#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11,<3.14"
# dependencies = [
#   "kuzu>=0.6.0",
#   "pyyaml>=6.0",
#   "rich>=13.0",
# ]
# ///
"""
wiki_graph.py — Kuzu-powered knowledge graph for wiki pages.
Parses relates_to / depends_on frontmatter links, builds a property graph,
and enables Cypher traversal queries.

Usage:
  uv run tools/wiki/wiki_graph.py --build            # build/rebuild the graph
  uv run tools/wiki/wiki_graph.py --stats            # graph statistics
  uv run tools/wiki/wiki_graph.py --neighbors agent-team-setup   # direct neighbors
  uv run tools/wiki/wiki_graph.py --path karpathy-llm-wiki-pattern agent-team-setup  # shortest path
  uv run tools/wiki/wiki_graph.py --deps tooling-policy          # all dependencies
  uv run tools/wiki/wiki_graph.py --query "MATCH (a)-[r]->(b) RETURN a.id, label(r), b.id LIMIT 20"
"""

import argparse
import json
import logging
import re
import sys
import io
from pathlib import Path
from time import perf_counter

# Force UTF-8 output on Windows
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import kuzu
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from wiki_common import GRAPH_LOG, append_jsonl, now_iso

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

WIKI_DIR   = Path(__file__).parent.parent.parent / "wiki"
INDEX_DIR  = Path(__file__).parent.parent.parent / ".wiki_index"
GRAPH_FILE = INDEX_DIR / "wiki.kuzu"     # single-file DB (like SQLite)
SKIP_FILES = {"_schema.md", "index.md", "log.md"}
console    = Console()

_wikilink_re = re.compile(r"^\[\[(.+?)(?:\|.+?)?\]\]$")

def _strip_wikilink(s: str) -> str:
    """Strip Obsidian [[...]] or [[...|alias]] brackets to bare page-id."""
    m = _wikilink_re.match(s.strip())
    return m.group(1) if m else s.strip()


# ── Data loading ──────────────────────────────────────────────────────────────

def load_pages() -> list[dict]:
    pages = []
    for md in sorted(WIKI_DIR.glob("*.md")):
        if md.name in SKIP_FILES:
            continue
        text = md.read_text(encoding="utf-8")
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
        fm = {}
        if match:
            try:
                fm = yaml.safe_load(match.group(1)) or {}
            except yaml.YAMLError:
                pass
        pages.append({
            "id":           str(fm.get("id", md.stem)),
            "title":        str(fm.get("title", md.stem)),
            "type":         str(fm.get("type", "")),
            "domain":       str(fm.get("domain", "")),
            "status":       str(fm.get("status", "")),
            "is_valid":     bool(fm.get("is_valid", True)),
            "confidence":   str(fm.get("confidence", "")),
            "created_by":   str(fm.get("created_by", "")),
            "valid_from":   str(fm.get("valid_from", "")),
            "tags":         [str(t) for t in (fm.get("tags") or [])],
            "relates_to":   [_strip_wikilink(str(x)) for x in (fm.get("relates_to") or [])],
            "depends_on":   [_strip_wikilink(str(x)) for x in (fm.get("depends_on") or [])],
            "superseded_by":_strip_wikilink(str(fm.get("superseded_by", ""))),
        })
    return pages


# ── Graph build ───────────────────────────────────────────────────────────────

def build_graph(pages: list[dict]) -> kuzu.Connection:
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    if GRAPH_FILE.exists():
        GRAPH_FILE.unlink()                                # remove old single-file DB
    db   = kuzu.Database(str(GRAPH_FILE))
    conn = kuzu.Connection(db)

    # ── Node tables ──────────────────────────────────────────────────────────
    conn.execute("""
        CREATE NODE TABLE Page (
            id STRING, title STRING, type STRING, domain STRING,
            status STRING, is_valid BOOLEAN, confidence STRING,
            created_by STRING, valid_from STRING,
            PRIMARY KEY (id)
        )
    """)
    conn.execute("CREATE NODE TABLE Tag   (name STRING, PRIMARY KEY (name))")
    conn.execute("CREATE NODE TABLE Agent (name STRING, PRIMARY KEY (name))")
    conn.execute("CREATE NODE TABLE Domain(name STRING, PRIMARY KEY (name))")

    # ── Relationship tables ───────────────────────────────────────────────────
    conn.execute("CREATE REL TABLE RELATES_TO   (FROM Page  TO Page)")
    conn.execute("CREATE REL TABLE DEPENDS_ON   (FROM Page  TO Page)")
    conn.execute("CREATE REL TABLE SUPERSEDED_BY(FROM Page  TO Page)")
    conn.execute("CREATE REL TABLE HAS_TAG      (FROM Page  TO Tag)")
    conn.execute("CREATE REL TABLE CREATED_BY   (FROM Page  TO Agent)")
    conn.execute("CREATE REL TABLE IN_DOMAIN    (FROM Page  TO Domain)")

    # ── Insert Page nodes ─────────────────────────────────────────────────────
    page_ids = {p["id"] for p in pages}
    for p in pages:
        conn.execute("""
            CREATE (:Page {
                id: $id, title: $title, type: $type, domain: $domain,
                status: $status, is_valid: $is_valid,
                confidence: $confidence, created_by: $created_by,
                valid_from: $valid_from
            })
        """, {"id": p["id"], "title": p["title"], "type": p["type"],
              "domain": p["domain"], "status": p["status"],
              "is_valid": p["is_valid"], "confidence": p["confidence"],
              "created_by": p["created_by"], "valid_from": p.get("valid_from","")})

    # ── Insert Tag / Agent / Domain nodes (deduplicated) ─────────────────────
    all_tags    = {t for p in pages for t in p["tags"]}
    all_agents  = {p["created_by"] for p in pages if p["created_by"]}
    all_domains = {p["domain"] for p in pages if p["domain"]}

    for tag    in all_tags:    conn.execute("CREATE (:Tag {name: $n})",    {"n": tag})
    for agent  in all_agents:  conn.execute("CREATE (:Agent {name: $n})",  {"n": agent})
    for domain in all_domains: conn.execute("CREATE (:Domain {name: $n})", {"n": domain})

    # ── Insert edges ──────────────────────────────────────────────────────────
    edges_added = 0

    def add_edge(src, tgt, rel, src_label="Page", tgt_label="Page",
                 src_key="id", tgt_key="id"):
        nonlocal edges_added
        try:
            conn.execute(
                f"MATCH (a:{src_label} {{{src_key}: $src}}), "
                f"(b:{tgt_label} {{{tgt_key}: $tgt}}) "
                f"CREATE (a)-[:{rel}]->(b)",
                {"src": src, "tgt": tgt}
            )
            edges_added += 1
        except Exception as e:
            log.debug(f"Edge skip {src}-[{rel}]->{tgt}: {e}")

    for p in pages:
        pid = p["id"]

        # Page → Page edges
        for tgt in p["relates_to"]:
            if tgt in page_ids: add_edge(pid, tgt, "RELATES_TO")
        for tgt in p["depends_on"]:
            if tgt in page_ids: add_edge(pid, tgt, "DEPENDS_ON")
        if p.get("superseded_by") and p["superseded_by"] in page_ids:
            add_edge(pid, p["superseded_by"], "SUPERSEDED_BY")

        # Page → Tag edges
        for tag in p["tags"]:
            add_edge(pid, tag, "HAS_TAG", tgt_label="Tag", tgt_key="name")

        # Page → Agent edge
        if p["created_by"]:
            add_edge(pid, p["created_by"], "CREATED_BY", tgt_label="Agent", tgt_key="name")

        # Page → Domain edge
        if p["domain"]:
            add_edge(pid, p["domain"], "IN_DOMAIN", tgt_label="Domain", tgt_key="name")

    console.print(f"[green]Graph built: {len(pages)} pages, {len(all_tags)} tags, "
                  f"{len(all_agents)} agents, {len(all_domains)} domains, "
                  f"{edges_added} edges → {GRAPH_FILE}[/green]")
    return conn


def open_graph() -> kuzu.Connection:
    if not GRAPH_FILE.exists():
        console.print("[red]No graph index found. Run --build first.[/red]")
        sys.exit(1)
    db   = kuzu.Database(str(GRAPH_FILE))
    conn = kuzu.Connection(db)
    return conn


def get_graph_stats(conn: kuzu.Connection) -> dict[str, object]:
    nodes  = conn.execute("MATCH (p:Page) RETURN COUNT(p)").get_next()[0]
    tags   = conn.execute("MATCH (t:Tag) RETURN COUNT(t)").get_next()[0]
    agents = conn.execute("MATCH (a:Agent) RETURN COUNT(a)").get_next()[0]
    domains= conn.execute("MATCH (d:Domain) RETURN COUNT(d)").get_next()[0]
    rel    = conn.execute("MATCH ()-[r:RELATES_TO]->() RETURN COUNT(r)").get_next()[0]
    dep    = conn.execute("MATCH ()-[r:DEPENDS_ON]->() RETURN COUNT(r)").get_next()[0]
    htag   = conn.execute("MATCH ()-[r:HAS_TAG]->() RETURN COUNT(r)").get_next()[0]
    cby    = conn.execute("MATCH ()-[r:CREATED_BY]->() RETURN COUNT(r)").get_next()[0]
    idom   = conn.execute("MATCH ()-[r:IN_DOMAIN]->() RETURN COUNT(r)").get_next()[0]
    result = conn.execute("""
        MATCH (a:Page)-[r:RELATES_TO|DEPENDS_ON]->(b:Page)
        RETURN a.id, a.title, COUNT(r) AS out_degree
        ORDER BY out_degree DESC
        LIMIT 8
    """)
    connected = []
    while result.has_next():
        row = result.get_next()
        connected.append({"id": str(row[0]), "title": str(row[1]), "out_degree": int(row[2])})
    tag_result = conn.execute("""
        MATCH (p:Page)-[:HAS_TAG]->(t:Tag)
        RETURN t.name, COUNT(p) AS pages
        ORDER BY pages DESC LIMIT 15
    """)
    tags_overview = []
    while tag_result.has_next():
        row = tag_result.get_next()
        tags_overview.append({"tag": str(row[0]), "pages": int(row[1])})
    orphans = conn.execute("""
        MATCH (p:Page)
        WHERE NOT (p)-[:RELATES_TO|DEPENDS_ON]->() AND NOT ()-[:RELATES_TO|DEPENDS_ON]->(p)
        RETURN p.id, p.title
    """)
    orphan_list: list[dict[str, str]] = []
    while orphans.has_next():
        row = orphans.get_next()
        orphan_list.append({"id": str(row[0]), "title": str(row[1])})
    return {
        "page_nodes": int(nodes),
        "tag_nodes": int(tags),
        "agent_nodes": int(agents),
        "domain_nodes": int(domains),
        "relates_to_edges": int(rel),
        "depends_on_edges": int(dep),
        "has_tag_edges": int(htag),
        "created_by_edges": int(cby),
        "in_domain_edges": int(idom),
        "total_edges": int(rel + dep + htag + cby + idom),
        "most_connected": connected,
        "top_tags": tags_overview,
        "orphans": orphan_list,
    }


# ── Queries ───────────────────────────────────────────────────────────────────

def print_stats(conn: kuzu.Connection):
    console.print(Panel("[bold cyan]Knowledge Graph Statistics[/bold cyan]", box=box.SIMPLE))
    stats = get_graph_stats(conn)

    t = Table(show_header=False, box=box.SIMPLE)
    t.add_column("Metric"); t.add_column("Value")
    t.add_row("Page nodes",        f"[cyan]{stats['page_nodes']}[/cyan]")
    t.add_row("Tag nodes",         str(stats["tag_nodes"]))
    t.add_row("Agent nodes",       str(stats["agent_nodes"]))
    t.add_row("Domain nodes",      str(stats["domain_nodes"]))
    t.add_row("RELATES_TO edges",  str(stats["relates_to_edges"]))
    t.add_row("DEPENDS_ON edges",  str(stats["depends_on_edges"]))
    t.add_row("HAS_TAG edges",     str(stats["has_tag_edges"]))
    t.add_row("CREATED_BY edges",  str(stats["created_by_edges"]))
    t.add_row("IN_DOMAIN edges",   str(stats["in_domain_edges"]))
    t.add_row("Total edges",       f"[bold]{stats['total_edges']}[/bold]")
    console.print(t)

    console.print("\n[bold]Most Connected Pages (Page-to-Page)[/bold]")
    mt = Table(box=box.SIMPLE, padding=(0,1))
    mt.add_column("Page ID"); mt.add_column("Title"); mt.add_column("Out", justify="right")
    for row in stats["most_connected"]:
        mt.add_row(str(row["id"]), str(row["title"])[:50], str(row["out_degree"]))
    console.print(mt)

    console.print("\n[bold]Tags in Graph[/bold]")
    tt = Table(box=box.SIMPLE, padding=(0,1))
    tt.add_column("Tag"); tt.add_column("Pages", justify="right")
    for row in stats["top_tags"]:
        tt.add_row(str(row["tag"]), str(row["pages"]))
    console.print(tt)

    orphan_list = stats["orphans"]
    if orphan_list:
        console.print(f"\n[yellow]Isolated pages (no Page-to-Page edges): {len(orphan_list)}[/yellow]")
        for row in orphan_list:
            console.print(f"  · [dim]{row['id']}[/dim]  {row['title']}")


def print_neighbors(conn: kuzu.Connection, page_id: str):
    console.print(Panel(f"[bold]🔗 Neighbors of:[/bold] [cyan]{page_id}[/cyan]", box=box.SIMPLE))

    result = conn.execute("""
        MATCH (a:Page {id: $id})-[r]->(b:Page)
        RETURN label(r) AS rel, b.id, b.title, b.type
        ORDER BY rel, b.id
    """, {"id": page_id})

    t = Table(box=box.SIMPLE, padding=(0,1))
    t.add_column("Relation"); t.add_column("Target ID"); t.add_column("Title"); t.add_column("Type")
    count = 0
    while result.has_next():
        row = result.get_next()
        t.add_row(str(row[0]), str(row[1]), str(row[2])[:50], str(row[3]))
        count += 1

    if count == 0:
        console.print("[yellow]No outgoing edges found for this page.[/yellow]")
    else:
        console.print(t)

    # Incoming edges
    incoming = conn.execute("""
        MATCH (a:Page)-[r]->(b:Page {id: $id})
        RETURN label(r) AS rel, a.id, a.title
        ORDER BY rel, a.id
    """, {"id": page_id})

    inc_rows = []
    while incoming.has_next():
        inc_rows.append(incoming.get_next())

    if inc_rows:
        console.print(f"\n[bold]Incoming links ({len(inc_rows)}):[/bold]")
        it = Table(box=box.SIMPLE, padding=(0,1))
        it.add_column("Relation"); it.add_column("Source ID"); it.add_column("Title")
        for row in inc_rows:
            it.add_row(str(row[0]), str(row[1]), str(row[2])[:50])
        console.print(it)


def print_deps(conn: kuzu.Connection, page_id: str):
    console.print(Panel(f"[bold]🧩 Dependency chain for:[/bold] [cyan]{page_id}[/cyan]", box=box.SIMPLE))
    result = conn.execute("""
        MATCH path = (a:Page {id: $id})-[:DEPENDS_ON*1..5]->(b:Page)
        RETURN b.id, b.title, LENGTH(path) AS depth
        ORDER BY depth, b.id
    """, {"id": page_id})

    t = Table(box=box.SIMPLE, padding=(0,1))
    t.add_column("Depth", justify="right"); t.add_column("Page ID"); t.add_column("Title")
    count = 0
    while result.has_next():
        row = result.get_next()
        t.add_row(str(row[2]), str(row[0]), str(row[1])[:60])
        count += 1
    if count == 0:
        console.print("[dim]No DEPENDS_ON edges found.[/dim]")
    else:
        console.print(t)


def run_custom_query(conn: kuzu.Connection, cypher: str):
    console.print(Panel(f"[bold]🔎 Cypher Query[/bold]\n[dim]{cypher}[/dim]", box=box.SIMPLE))
    try:
        result = conn.execute(cypher)
        t = Table(box=box.SIMPLE)
        rows = []
        while result.has_next():
            rows.append([str(x) for x in result.get_next()])
        if rows:
            for i in range(len(rows[0])):
                t.add_column(f"col{i}")
            for row in rows:
                t.add_row(*row)
            console.print(t)
            console.print(f"[dim]{len(rows)} row(s)[/dim]")
        else:
            console.print("[dim]No results.[/dim]")
    except Exception as e:
        console.print(f"[red]Query error: {e}[/red]")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Wiki Knowledge Graph (Kuzu)")
    parser.add_argument("--build",     action="store_true", help="Build/rebuild the graph")
    parser.add_argument("--stats",     action="store_true", help="Graph statistics")
    parser.add_argument("--neighbors", metavar="PAGE_ID",   help="Show neighbors of a page")
    parser.add_argument("--deps",      metavar="PAGE_ID",   help="Show dependency chain")
    parser.add_argument("--query",     metavar="CYPHER",    help="Run a custom Cypher query")
    args = parser.parse_args()

    started = perf_counter()
    pages = load_pages()
    console.print(f"[dim]Loaded {len(pages)} wiki pages.[/dim]")

    if args.build:
        conn = build_graph(pages)
        append_jsonl(
            GRAPH_LOG,
            {
                "timestamp": now_iso(),
                "action": "build",
                "page_count": len(pages),
                "duration_ms": round((perf_counter() - started) * 1000, 1),
            },
        )
    else:
        conn = open_graph()

    if args.stats or (not any([args.neighbors, args.deps, args.query, args.build])):
        print_stats(conn)
        append_jsonl(
            GRAPH_LOG,
            {
                "timestamp": now_iso(),
                "action": "stats",
                "duration_ms": round((perf_counter() - started) * 1000, 1),
                "page_count": len(pages),
            },
        )

    if args.neighbors:
        print_neighbors(conn, args.neighbors)
        append_jsonl(
            GRAPH_LOG,
            {
                "timestamp": now_iso(),
                "action": "neighbors",
                "page_id": args.neighbors,
                "duration_ms": round((perf_counter() - started) * 1000, 1),
            },
        )

    if args.deps:
        print_deps(conn, args.deps)
        append_jsonl(
            GRAPH_LOG,
            {
                "timestamp": now_iso(),
                "action": "deps",
                "page_id": args.deps,
                "duration_ms": round((perf_counter() - started) * 1000, 1),
            },
        )

    if args.query:
        run_custom_query(conn, args.query)
        append_jsonl(
            GRAPH_LOG,
            {
                "timestamp": now_iso(),
                "action": "query",
                "query": args.query,
                "duration_ms": round((perf_counter() - started) * 1000, 1),
            },
        )


if __name__ == "__main__":
    main()
