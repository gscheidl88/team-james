#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "duckdb>=0.10.0",
#   "pyyaml>=6.0",
#   "rich>=13.0",
# ]
# ///
"""
wiki_analytics.py — DuckDB-powered analytics & KPI dashboard for the wiki knowledge base.

Usage:
  uv run tools/wiki/wiki_analytics.py                  # full dashboard
  uv run tools/wiki/wiki_analytics.py --kpis           # KPI summary only
  uv run tools/wiki/wiki_analytics.py --compliance     # schema compliance check
  uv run tools/wiki/wiki_analytics.py --growth         # knowledge growth over time
  uv run tools/wiki/wiki_analytics.py --export kpis.json  # export KPIs as JSON
"""

import argparse
import json
import logging
import re
import sys
import io
from datetime import datetime

# Force UTF-8 output on Windows
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
from pathlib import Path

import duckdb
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

WIKI_DIR = Path(__file__).parent.parent.parent / "wiki"
SKIP_FILES = {"_schema.md", "index.md", "log.md"}
console = Console()


# ── Frontmatter parsing ──────────────────────────────────────────────────────

def parse_frontmatter(path: Path) -> dict:
    """Extract YAML frontmatter from a markdown file."""
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not match:
        return {"_file": path.name, "_has_frontmatter": False}
    try:
        data = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError as e:
        log.warning(f"YAML parse error in {path.name}: {e}")
        data = {}
    data["_file"] = path.name
    data["_has_frontmatter"] = True
    data["_word_count"] = len(text.split())
    data["_has_overview"] = bool(re.search(r"^## Overview", text, re.MULTILINE))
    data["_char_count"] = len(text)
    return data


def load_wiki(con: duckdb.DuckDBPyConnection) -> int:
    """Parse all wiki pages and load into DuckDB."""
    pages = []
    for md_file in sorted(WIKI_DIR.glob("*.md")):
        if md_file.name in SKIP_FILES:
            continue
        fm = parse_frontmatter(md_file)
        pages.append({
            "file":            fm.get("_file", md_file.name),
            "id":              str(fm.get("id", "")),
            "type":            str(fm.get("type", "")),
            "title":           str(fm.get("title", "")),
            "domain":          str(fm.get("domain", "")),
            "status":          str(fm.get("status", "")),
            "confidence":      str(fm.get("confidence", "")),
            "is_valid":        bool(fm.get("is_valid", True)),
            "is_project":      bool(fm.get("is_project", False)),
            "created_by":      str(fm.get("created_by", "")),
            "modified_by":     str(fm.get("modified_by", "")),
            "created":         str(fm.get("created", "")),
            "last_modified":   str(fm.get("last_modified", "")),
            "valid_from":      str(fm.get("valid_from", "")),
            "valid_to":        str(fm.get("valid_to", "")),
            "expired_at":      str(fm.get("expired_at", "")),
            "reviewed_by":     str(fm.get("reviewed_by", "")),
            "tags":            json.dumps(fm.get("tags", []) or []),
            "relates_to":      json.dumps(fm.get("relates_to", []) or []),
            "depends_on":      json.dumps(fm.get("depends_on", []) or []),
            "has_frontmatter": bool(fm.get("_has_frontmatter", False)),
            "has_overview":    bool(fm.get("_has_overview", False)),
            "word_count":      int(fm.get("_word_count", 0)),
            "char_count":      int(fm.get("_char_count", 0)),
        })

    con.execute("DROP TABLE IF EXISTS pages")
    con.execute("""
        CREATE TABLE pages (
            file VARCHAR, id VARCHAR, type VARCHAR, title VARCHAR,
            domain VARCHAR, status VARCHAR, confidence VARCHAR,
            is_valid BOOLEAN, is_project BOOLEAN,
            created_by VARCHAR, modified_by VARCHAR,
            created VARCHAR, last_modified VARCHAR,
            valid_from VARCHAR, valid_to VARCHAR, expired_at VARCHAR,
            reviewed_by VARCHAR,
            tags VARCHAR, relates_to VARCHAR, depends_on VARCHAR,
            has_frontmatter BOOLEAN, has_overview BOOLEAN,
            word_count INTEGER, char_count INTEGER
        )
    """)
    con.executemany("INSERT INTO pages VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    [list(p.values()) for p in pages])
    return len(pages)


# ── KPI Calculations ─────────────────────────────────────────────────────────

def compute_kpis(con: duckdb.DuckDBPyConnection) -> dict:
    def q(sql): return con.execute(sql).fetchone()[0]
    def qa(sql): return con.execute(sql).fetchall()

    total = q("SELECT COUNT(*) FROM pages")
    valid = q("SELECT COUNT(*) FROM pages WHERE is_valid = TRUE")
    archived = total - valid
    has_fm = q("SELECT COUNT(*) FROM pages WHERE has_frontmatter = TRUE")
    has_ov = q("SELECT COUNT(*) FROM pages WHERE has_overview = TRUE")

    # Confidence breakdown
    conf = {r[0]: r[1] for r in qa("SELECT confidence, COUNT(*) FROM pages GROUP BY confidence")}

    # By type
    by_type = {r[0]: r[1] for r in qa("SELECT type, COUNT(*) FROM pages GROUP BY type ORDER BY 2 DESC")}

    # By domain
    by_domain = {r[0]: r[1] for r in qa("SELECT domain, COUNT(*) FROM pages GROUP BY domain ORDER BY 2 DESC")}

    # Schema compliance score (5 checks)
    fm_score   = round(has_fm / total * 100) if total else 0
    ov_score   = round(has_ov / total * 100) if total else 0
    id_score   = round(q("SELECT COUNT(*) FROM pages WHERE id != ''") / total * 100) if total else 0
    conf_score = round(q("SELECT COUNT(*) FROM pages WHERE confidence != ''") / total * 100) if total else 0
    type_score = round(q("SELECT COUNT(*) FROM pages WHERE type != ''") / total * 100) if total else 0
    compliance = round((fm_score + ov_score + id_score + conf_score + type_score) / 5)

    # Connectivity
    avg_relates = con.execute("""
        SELECT AVG(json_array_length(relates_to)) FROM pages WHERE relates_to != '[]'
    """).fetchone()[0] or 0

    # Word count stats
    avg_words = q("SELECT AVG(word_count) FROM pages")
    total_words = q("SELECT SUM(word_count) FROM pages")

    # Human-reviewed
    reviewed = q("SELECT COUNT(*) FROM pages WHERE reviewed_by != '' AND reviewed_by IS NOT NULL")

    return {
        "total_pages": total,
        "valid_pages": valid,
        "archived_pages": archived,
        "frontmatter_coverage_pct": fm_score,
        "overview_section_pct": ov_score,
        "schema_compliance_score": compliance,
        "confidence": conf,
        "by_type": by_type,
        "by_domain": by_domain,
        "avg_relates_to": round(avg_relates, 1),
        "avg_word_count": round(avg_words or 0),
        "total_words": total_words or 0,
        "human_reviewed": reviewed,
        "generated_at": datetime.now().isoformat(),
    }


# ── Display functions ─────────────────────────────────────────────────────────

def print_dashboard(con: duckdb.DuckDBPyConnection, kpis: dict):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Header
    console.print(Panel(
        f"[bold cyan]📊 Wiki KPI Dashboard[/bold cyan]  ·  {now}\n"
        f"[dim]{WIKI_DIR}[/dim]",
        box=box.DOUBLE_EDGE
    ))

    # Core KPIs
    t = Table(show_header=False, box=box.SIMPLE, padding=(0,2))
    t.add_column("KPI", style="bold")
    t.add_column("Value")
    t.add_row("Total pages",            f"[cyan]{kpis['total_pages']}[/cyan]")
    t.add_row("Valid / Archived",       f"[green]{kpis['valid_pages']}[/green] / [dim]{kpis['archived_pages']}[/dim]")
    t.add_row("Schema compliance",      f"[{'green' if kpis['schema_compliance_score']>=80 else 'yellow' if kpis['schema_compliance_score']>=60 else 'red'}]{kpis['schema_compliance_score']}%[/]")
    t.add_row("Frontmatter coverage",   f"{kpis['frontmatter_coverage_pct']}%")
    t.add_row("## Overview present",   f"[{'green' if kpis['overview_section_pct']==100 else 'yellow'}]{kpis['overview_section_pct']}%[/]")
    t.add_row("Human reviewed",         f"{kpis['human_reviewed']} pages")
    t.add_row("Avg word count",         f"{kpis['avg_word_count']} words")
    t.add_row("Total words in wiki",    f"{kpis['total_words']:,} words")
    t.add_row("Avg relates_to links",   f"{kpis['avg_relates_to']} per page")
    console.print(t)

    # Confidence distribution
    console.print("\n[bold]Confidence Distribution[/bold]")
    ct = Table(box=box.SIMPLE, padding=(0,2))
    ct.add_column("Level"); ct.add_column("Pages", justify="right")
    for level, count in kpis["confidence"].items():
        colour = {"high": "green", "medium": "yellow", "low": "red"}.get(level, "white")
        ct.add_row(f"[{colour}]{level or '(unset)'}[/]", str(count))
    console.print(ct)

    # By type
    console.print("\n[bold]Pages by Type[/bold]")
    tt = Table(box=box.SIMPLE, padding=(0,2))
    tt.add_column("Type"); tt.add_column("Pages", justify="right")
    for t_, c in kpis["by_type"].items():
        tt.add_row(t_ or "(unset)", str(c))
    console.print(tt)

    # By domain
    console.print("\n[bold]Pages by Domain[/bold]")
    dt = Table(box=box.SIMPLE, padding=(0,2))
    dt.add_column("Domain"); dt.add_column("Pages", justify="right")
    for d, c in kpis["by_domain"].items():
        dt.add_row(d or "(unset)", str(c))
    console.print(dt)


def print_compliance(con: duckdb.DuckDBPyConnection):
    console.print(Panel("[bold yellow]🔍 Schema Compliance Report[/bold yellow]", box=box.SIMPLE))

    checks = [
        ("Frontmatter present",  "has_frontmatter = TRUE"),
        ("## Overview section",  "has_overview = TRUE"),
        ("id field set",         "id != ''"),
        ("type field set",       "type != ''"),
        ("confidence set",       "confidence != ''"),
        ("domain set",           "domain != ''"),
        ("created_by set",       "created_by != ''"),
        ("relates_to set",       "relates_to != '[]'"),
    ]

    t = Table(box=box.SIMPLE, padding=(0,2))
    t.add_column("Check"); t.add_column("Pass", justify="right"); t.add_column("Fail", justify="right")
    total = con.execute("SELECT COUNT(*) FROM pages").fetchone()[0]
    for label, condition in checks:
        passing = con.execute(f"SELECT COUNT(*) FROM pages WHERE {condition}").fetchone()[0]
        failing = total - passing
        colour = "green" if failing == 0 else "yellow" if failing <= 2 else "red"
        t.add_row(label, f"[green]{passing}[/green]", f"[{colour}]{failing}[/]")
    console.print(t)

    # Pages missing Overview
    missing_ov = con.execute(
        "SELECT file, title FROM pages WHERE has_overview = FALSE ORDER BY file"
    ).fetchall()
    if missing_ov:
        console.print("\n[yellow]Pages missing ## Overview section:[/yellow]")
        for f, title in missing_ov:
            console.print(f"  · [dim]{f}[/dim]  {title}")


def print_growth(con: duckdb.DuckDBPyConnection):
    console.print(Panel("[bold green]📈 Knowledge Growth[/bold green]", box=box.SIMPLE))

    rows = con.execute("""
        SELECT created, COUNT(*) as added, SUM(word_count) as words
        FROM pages
        WHERE created != ''
        GROUP BY created
        ORDER BY created
    """).fetchall()

    t = Table(box=box.SIMPLE, padding=(0,2))
    t.add_column("Date"); t.add_column("Pages added", justify="right"); t.add_column("Words added", justify="right")
    cumulative = 0
    for date, count, words in rows:
        cumulative += count
        t.add_row(date, str(count), f"{words:,}" if words else "—")
    t.add_row("[bold]Total[/bold]", f"[bold]{cumulative}[/bold]", "")
    console.print(t)

    # Most connected pages
    console.print("\n[bold]Most Connected Pages (by relates_to)[/bold]")
    mc = con.execute("""
        SELECT title, json_array_length(relates_to) as links
        FROM pages
        WHERE relates_to != '[]'
        ORDER BY links DESC
        LIMIT 5
    """).fetchall()
    mt = Table(box=box.SIMPLE, padding=(0,2))
    mt.add_column("Page"); mt.add_column("Links", justify="right")
    for title, links in mc:
        mt.add_row(title or "—", str(links))
    console.print(mt)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Wiki KPI Analytics Dashboard")
    parser.add_argument("--kpis",       action="store_true", help="KPI summary only")
    parser.add_argument("--compliance", action="store_true", help="Schema compliance report")
    parser.add_argument("--growth",     action="store_true", help="Knowledge growth report")
    parser.add_argument("--export",     metavar="FILE",      help="Export KPIs as JSON")
    args = parser.parse_args()

    con = duckdb.connect(":memory:")

    console.print("[dim]Loading wiki pages...[/dim]")
    count = load_wiki(con)
    console.print(f"[dim]Loaded {count} pages.[/dim]\n")

    kpis = compute_kpis(con)

    if args.export:
        out = Path(args.export)
        out.write_text(json.dumps(kpis, indent=2, ensure_ascii=False), encoding="utf-8")
        console.print(f"[green]✓ KPIs exported to {out}[/green]")
        return

    if args.compliance:
        print_compliance(con)
        return

    if args.growth:
        print_growth(con)
        return

    if args.kpis:
        print_dashboard(con, kpis)
        return

    # Full dashboard (default)
    print_dashboard(con, kpis)
    console.print()
    print_compliance(con)
    console.print()
    print_growth(con)


if __name__ == "__main__":
    main()
