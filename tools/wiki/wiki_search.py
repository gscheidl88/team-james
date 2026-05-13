#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "lancedb>=0.6.0",
#   "sentence-transformers>=3.0",
#   "pyyaml>=6.0",
#   "rich>=13.0",
#   "rank_bm25>=0.2",
# ]
# ///
"""
wiki_search.py — Semantic + BM25 hybrid search over the wiki knowledge base.
Uses sentence-transformers (local, no API token) + LanceDB (embedded vector store).

Usage:
  uv run tools/wiki/wiki_search.py --index           # build/rebuild the index
  uv run tools/wiki/wiki_search.py "query text"      # hybrid search (default)
  uv run tools/wiki/wiki_search.py "query" --semantic  # semantic only
  uv run tools/wiki/wiki_search.py "query" --bm25     # BM25 only
  uv run tools/wiki/wiki_search.py "query" --top 10  # return top N results
"""

import argparse
import json
import logging
import re
import sys
import io
import warnings
from time import perf_counter

# Force UTF-8 output on Windows
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
from pathlib import Path

import lancedb
import numpy as np
import yaml
from rank_bm25 import BM25Okapi
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from sentence_transformers import SentenceTransformer

from wiki_common import (
    SEARCH_LOG,
    SEARCH_METADATA,
    append_jsonl,
    current_wiki_manifest,
    now_iso,
    read_json,
    write_json,
)

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

WIKI_DIR   = Path(__file__).parent.parent.parent / "wiki"
INDEX_DIR  = Path(__file__).parent.parent.parent / ".wiki_index"
SKIP_FILES = {"_schema.md", "index.md", "log.md"}
MODEL_NAME = "all-MiniLM-L6-v2"   # 80MB, runs locally, no token needed
TABLE_NAME = "wiki_pages"
console    = Console()


def table_names(db) -> set[str]:
    if hasattr(db, "table_names"):
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                return {str(name) for name in db.table_names()}
        except Exception:
            pass
    names: set[str] = set()
    for item in db.list_tables():
        if isinstance(item, (list, tuple)):
            if item:
                names.add(str(item[0]))
        else:
            names.add(str(item))
    return names


# ── Text extraction ───────────────────────────────────────────────────────────

def extract_content(path: Path) -> tuple[dict, str]:
    """Return (frontmatter_dict, plain_text_body)."""
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    fm = {}
    body = text
    if match:
        try:
            fm = yaml.safe_load(match.group(1)) or {}
        except yaml.YAMLError:
            pass
        body = text[match.end():]
    # Strip markdown syntax for cleaner embeddings
    body = re.sub(r"#{1,6}\s", "", body)
    body = re.sub(r"\*{1,2}(.+?)\*{1,2}", r"\1", body)
    body = re.sub(r"`{1,3}.*?`{1,3}", "", body, flags=re.DOTALL)
    body = re.sub(r"\[\[(.+?)\]\]", r"\1", body)
    body = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", body)
    return fm, body.strip()


def load_pages() -> list[dict]:
    pages = []
    for md in sorted(WIKI_DIR.glob("*.md")):
        if md.name in SKIP_FILES:
            continue
        fm, body = extract_content(md)
        pages.append({
            "file":    md.name,
            "id":      str(fm.get("id", md.stem)),
            "title":   str(fm.get("title", md.stem)),
            "type":    str(fm.get("type", "")),
            "domain":  str(fm.get("domain", "")),
            "tags":    ", ".join(fm.get("tags", []) or []),
            "is_valid": bool(fm.get("is_valid", True)),
            "confidence": str(fm.get("confidence", "")),
            "body":    body,
            "text":    f"{fm.get('title', '')} {fm.get('tags', '')} {body}",
        })
    return pages


# ── Index build ───────────────────────────────────────────────────────────────

def build_index(pages: list[dict], model: SentenceTransformer) -> lancedb.table.Table:
    console.print("[dim]Encoding pages with sentence-transformers...[/dim]")
    texts   = [p["text"] for p in pages]
    vectors = model.encode(texts, show_progress_bar=True, normalize_embeddings=True)

    INDEX_DIR.mkdir(exist_ok=True)
    db    = lancedb.connect(str(INDEX_DIR / "lancedb"))

    records = []
    for page, vec in zip(pages, vectors):
        records.append({
            "vector":     vec.tolist(),
            "file":       page["file"],
            "id":         page["id"],
            "title":      page["title"],
            "type":       page["type"],
            "domain":     page["domain"],
            "tags":       page["tags"],
            "is_valid":   page["is_valid"],
            "confidence": page["confidence"],
            "body":       page["body"][:2000],   # store first 2000 chars
        })

    table = db.create_table(TABLE_NAME, records, mode="overwrite")
    page_count, manifest = current_wiki_manifest()
    write_json(
        SEARCH_METADATA,
        {
            "built_at": now_iso(),
            "page_count": page_count,
            "manifest": manifest,
            "model_name": MODEL_NAME,
            "table_name": TABLE_NAME,
        },
    )
    console.print(f"[green]✓ Indexed {len(records)} pages → {INDEX_DIR / 'lancedb'}[/green]")
    return table


def log_event(payload: dict[str, object]) -> None:
    append_jsonl(SEARCH_LOG, {"timestamp": now_iso(), **payload})


def index_status(db: lancedb.DBConnection, pages: list[dict]) -> dict[str, object]:
    page_count, manifest = current_wiki_manifest()
    metadata = read_json(SEARCH_METADATA)
    table_exists = TABLE_NAME in table_names(db)
    indexed_count = 0
    if table_exists:
        indexed_count = int(db.open_table(TABLE_NAME).count_rows())

    reasons: list[str] = []
    if not table_exists:
        reasons.append("missing-table")
    if not metadata:
        reasons.append("missing-metadata")
    if indexed_count and indexed_count != page_count:
        reasons.append("page-count-mismatch")
    if metadata and int(metadata.get("page_count", 0) or 0) != page_count:
        reasons.append("metadata-page-count-mismatch")
    if metadata and str(metadata.get("manifest", "")) != manifest:
        reasons.append("manifest-mismatch")

    return {
        "wiki_page_count": page_count,
        "indexed_page_count": indexed_count,
        "manifest": manifest,
        "metadata": metadata,
        "fresh": len(reasons) == 0,
        "reasons": reasons,
        "table_exists": table_exists,
    }


# ── Search ────────────────────────────────────────────────────────────────────

def semantic_search(query: str, table, model: SentenceTransformer, top_n: int) -> list[dict]:
    q_vec = model.encode([query], normalize_embeddings=True)[0].tolist()
    results = table.search(q_vec).limit(top_n).to_list()
    return [{"file": r["file"], "title": r["title"], "score": float(r["_distance"]),
             "type": r["type"], "domain": r["domain"], "body": r["body"][:200]}
            for r in results]


def bm25_search(query: str, pages: list[dict], top_n: int) -> list[dict]:
    tokenized = [p["text"].lower().split() for p in pages]
    bm25  = BM25Okapi(tokenized)
    scores = bm25.get_scores(query.lower().split())
    ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:top_n]
    return [{"file": pages[i]["file"], "title": pages[i]["title"],
             "score": float(s), "type": pages[i]["type"],
             "domain": pages[i]["domain"], "body": pages[i]["body"][:200]}
            for i, s in ranked if s > 0]


def hybrid_search(query: str, table, pages: list[dict], model: SentenceTransformer, top_n: int) -> list[dict]:
    """Reciprocal Rank Fusion of semantic + BM25 results."""
    sem   = semantic_search(query, table, model, top_n * 2)
    bm    = bm25_search(query, pages, top_n * 2)
    k     = 60  # RRF constant

    scores: dict[str, float] = {}
    for rank, r in enumerate(sem):
        scores[r["file"]] = scores.get(r["file"], 0) + 1 / (k + rank + 1)
    for rank, r in enumerate(bm):
        scores[r["file"]] = scores.get(r["file"], 0) + 1 / (k + rank + 1)

    # Merge metadata
    meta = {p["file"]: p for p in pages}
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
    return [{"file": f, "title": meta[f]["title"], "score": round(s, 4),
             "type": meta[f]["type"], "domain": meta[f]["domain"],
             "body": meta[f]["body"][:200]}
            for f, s in ranked if f in meta]


# ── Display ───────────────────────────────────────────────────────────────────

def print_results(results: list[dict], query: str, mode: str):
    console.print(Panel(
        f"[bold cyan]🔍 Wiki Search[/bold cyan]  ·  \"{query}\"  ·  mode=[yellow]{mode}[/yellow]",
        box=box.SIMPLE
    ))
    if not results:
        console.print("[red]No results found.[/red]")
        return

    t = Table(box=box.SIMPLE, padding=(0,1))
    t.add_column("#",      style="dim", width=3)
    t.add_column("Score",  justify="right", width=8)
    t.add_column("Title",  style="bold")
    t.add_column("Type",   width=12)
    t.add_column("Domain", width=12)

    for i, r in enumerate(results, 1):
        t.add_row(str(i), f"{r['score']:.4f}", r["title"],
                  r.get("type", ""), r.get("domain", ""))
    console.print(t)

    # Show snippet for top result
    if results:
        top = results[0]
        console.print(f"\n[bold]Top result snippet:[/bold] [dim]{top['file']}[/dim]")
        console.print(f"[dim]{top['body'][:300]}...[/dim]")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Wiki Hybrid Search")
    parser.add_argument("query",     nargs="?",        help="Search query")
    parser.add_argument("--index",   action="store_true", help="Build/rebuild the search index")
    parser.add_argument("--semantic",action="store_true", help="Semantic search only")
    parser.add_argument("--bm25",    action="store_true", help="BM25 search only")
    parser.add_argument("--top",     type=int, default=5, help="Number of results (default: 5)")
    parser.add_argument("--no-refresh", action="store_true", help="Do not auto-rebuild a stale index")
    parser.add_argument("--no-log", action="store_true", help="Skip usage logging")
    args = parser.parse_args()

    started = perf_counter()
    pages = load_pages()
    console.print(f"[dim]Loaded {len(pages)} wiki pages.[/dim]")
    db_path = INDEX_DIR / "lancedb"
    db = lancedb.connect(str(db_path))
    mode = "hybrid (RRF)"
    if args.semantic:
        mode = "semantic"
    elif args.bm25:
        mode = "bm25"

    status = index_status(db, pages)
    needs_vector = mode != "bm25" or args.index
    needs_rebuild = args.index or (needs_vector and not status["fresh"] and not args.no_refresh)

    model = None
    table = None
    if needs_rebuild:
        console.print("[dim]Loading embedding model (first run downloads ~80MB)...[/dim]")
        model = SentenceTransformer(MODEL_NAME)
        table = build_index(pages, model)
        db = lancedb.connect(str(db_path))
        status = index_status(db, pages)
        if not args.no_log:
            log_event(
                {
                    "event_type": "index_build",
                    "mode": mode,
                    "wiki_page_count": status["wiki_page_count"],
                    "indexed_page_count": status["indexed_page_count"],
                    "index_fresh": status["fresh"],
                    "stale_reasons": status["reasons"],
                }
            )
    elif needs_vector:
        table = db.open_table(TABLE_NAME)
        console.print(f"[dim]Using existing index ({table.count_rows()} entries).[/dim]")

    if not args.query:
        if not args.index:
            console.print("[yellow]No query provided. Use --index to build index or provide a search query.[/yellow]")
        return

    if args.semantic:
        if model is None:
            console.print("[dim]Loading embedding model (first run downloads ~80MB)...[/dim]")
            model = SentenceTransformer(MODEL_NAME)
        results = semantic_search(args.query, table, model, args.top)
    elif args.bm25:
        results = bm25_search(args.query, pages, args.top)
    else:
        if model is None:
            console.print("[dim]Loading embedding model (first run downloads ~80MB)...[/dim]")
            model = SentenceTransformer(MODEL_NAME)
        results = hybrid_search(args.query, table, pages, model, args.top)

    print_results(results, args.query, mode)
    duration_ms = round((perf_counter() - started) * 1000, 1)
    if not args.no_log:
        log_event(
            {
                "event_type": "query",
                "mode": mode,
                "query": args.query,
                "top_n": args.top,
                "result_count": len(results),
                "duration_ms": duration_ms,
                "wiki_page_count": status["wiki_page_count"],
                "indexed_page_count": status["indexed_page_count"],
                "index_fresh": status["fresh"],
                "stale_reasons": status["reasons"],
                "top_hit": results[0]["file"] if results else None,
            }
        )


if __name__ == "__main__":
    main()
