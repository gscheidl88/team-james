#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11,<3.14"
# dependencies = [
#   "lancedb>=0.6.0",
#   "sentence-transformers>=3.0",
#   "kuzu>=0.6.0",
#   "pyyaml>=6.0",
#   "rich>=13.0",
#   "rank_bm25>=0.2",
# ]
# ///
"""
retrieval_probe.py - JSON probes for wiki search and graph retrieval behavior.

Failure classes emitted in probe_ok=False payloads:
  stale_index            -- search index is stale and --strict prevented auto-rebuild
  stale_graph            -- graph DB is missing or older than wiki sources; --strict blocked rebuild
  missing_source_node    -- page_id not found in the graph (node does not exist)
  probe_setup_error      -- unexpected error during setup (not stale-related)
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import lancedb

import wiki_graph as _wiki_graph
from wiki_graph import build_graph, load_pages as load_graph_pages, open_graph
from wiki_search import (
    INDEX_DIR,
    MODEL_NAME,
    TABLE_NAME,
    SentenceTransformer,
    build_index,
    hybrid_search,
    index_status,
    load_pages,
)


class _StaleError(Exception):
    """Raised in strict mode when the index/graph is not fresh."""

    def __init__(self, failure_class: str, reasons: list[str]) -> None:
        self.failure_class = failure_class
        self.reasons = reasons
        super().__init__(f"{failure_class}: {reasons}")


def ensure_search_ready(
    strict: bool = False,
    index_dir: Path | None = None,
) -> tuple[list[dict[str, Any]], Any]:
    """Return (pages, table).  In strict mode raises _StaleError instead of rebuilding.

    Parameters
    ----------
    index_dir:
        Override the lancedb directory.  Defaults to the module-level INDEX_DIR from
        wiki_search.  Pass a non-existent path to exercise strict stale-index detection
        without relying on the real index being current.
    """
    effective_index_dir = index_dir if index_dir is not None else INDEX_DIR
    pages = load_pages()
    db = lancedb.connect(str(effective_index_dir / "lancedb"))
    status = index_status(db, pages)
    if not status["fresh"]:
        if strict:
            raise _StaleError("stale_index", status.get("reasons", []))
        model = SentenceTransformer(MODEL_NAME)
        build_index(pages, model)
        db = lancedb.connect(str(effective_index_dir / "lancedb"))
    return pages, db.open_table(TABLE_NAME)


def run_search(query: str, top: int, strict: bool = False, index_dir: Path | None = None) -> dict[str, Any]:
    try:
        pages, table = ensure_search_ready(strict=strict, index_dir=index_dir)
    except _StaleError as exc:
        return {
            "probe_kind": "search",
            "probe_ok": False,
            "failure_class": exc.failure_class,
            "stale_reasons": exc.reasons,
            "query": query,
            "top": top,
        }
    model = SentenceTransformer(MODEL_NAME)
    results = hybrid_search(query, table, pages, model, top)
    return {
        "probe_kind": "search",
        "probe_ok": True,
        "query": query,
        "top": top,
        "result_count": len(results),
        "top_hit_file": results[0]["file"] if results else None,
        "top_hit_title": results[0]["title"] if results else None,
        "top_hit_score": results[0]["score"] if results else None,
        "top_files": [item["file"] for item in results],
        "top_titles": [item["title"] for item in results],
    }


def _check_graph_staleness() -> list[str]:
    """Return staleness reasons if the graph DB is missing or older than any wiki source file."""
    graph_file: Path = _wiki_graph.GRAPH_FILE
    if not graph_file.exists():
        return ["graph-db-missing"]
    graph_mtime = graph_file.stat().st_mtime
    stale_files = [
        md.name
        for md in _wiki_graph.WIKI_DIR.glob("*.md")
        if md.name not in _wiki_graph.SKIP_FILES and md.stat().st_mtime > graph_mtime
    ]
    if stale_files:
        return [f"graph-older-than-wiki: {stale_files[:5]}"]
    return []


def ensure_graph_ready(strict: bool = False):
    """Return an open kuzu.Connection.

    In strict mode: raises _StaleError if graph is missing OR any wiki file is newer
    than the graph DB.  In non-strict mode: rebuilds silently when stale.
    """
    reasons = _check_graph_staleness()
    if reasons:
        if strict:
            raise _StaleError("stale_graph", reasons)
        build_graph(load_graph_pages())
    # Guard against edge-cases where the file disappeared between the check and open.
    try:
        return open_graph()
    except SystemExit:
        if strict:
            raise _StaleError("stale_graph", ["graph-db-open-failed"])
        build_graph(load_graph_pages())
        return open_graph()


def run_neighbors(page_id: str, strict: bool = False) -> dict[str, Any]:
    try:
        conn = ensure_graph_ready(strict=strict)
    except _StaleError as exc:
        return {
            "probe_kind": "neighbors",
            "probe_ok": False,
            "failure_class": exc.failure_class,
            "stale_reasons": exc.reasons,
            "page_id": page_id,
        }
    result = conn.execute(
        """
        MATCH (a:Page {id: $id})-[r]->(b:Page)
        RETURN label(r), b.id, b.title
        ORDER BY label(r), b.id
        """,
        {"id": page_id},
    )
    rows: list[dict[str, str]] = []
    while result.has_next():
        row = result.get_next()
        rows.append({"relation": str(row[0]), "id": str(row[1]), "title": str(row[2])})

    # A zero-row result is ambiguous: either the page has no outgoing edges, or it does
    # not exist at all.  Check node existence explicitly to distinguish the two cases.
    if not rows:
        exists_result = conn.execute(
            "MATCH (a:Page {id: $id}) RETURN count(a)",
            {"id": page_id},
        )
        if exists_result.get_next()[0] == 0:
            return {
                "probe_kind": "neighbors",
                "probe_ok": False,
                "failure_class": "missing_source_node",
                "page_id": page_id,
                "stale_reasons": [],
            }

    # Break down by relation type so assertions can check direction+type, not just IDs.
    relates_to_ids = [r["id"] for r in rows if r["relation"] == "RELATES_TO"]
    depends_on_ids = [r["id"] for r in rows if r["relation"] == "DEPENDS_ON"]
    superseded_by_ids = [r["id"] for r in rows if r["relation"] == "SUPERSEDED_BY"]
    relation_types = sorted({r["relation"] for r in rows})

    return {
        "probe_kind": "neighbors",
        "probe_ok": True,
        "page_id": page_id,
        "result_count": len(rows),
        "target_ids": [item["id"] for item in rows],
        "targets": rows,
        # Per-relation-type ID lists for stricter assertions:
        "relates_to_ids": relates_to_ids,
        "depends_on_ids": depends_on_ids,
        "superseded_by_ids": superseded_by_ids,
        "relation_types": relation_types,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run JSON retrieval probes against the wiki search/graph stack.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help=(
            "Fail with failure_class=stale_index/stale_graph instead of auto-rebuilding. "
            "Use this to detect regressions caused by index drift."
        ),
    )
    parser.add_argument(
        "--index-dir",
        type=Path,
        default=None,
        help=(
            "Override the wiki index directory (default: .wiki_index next to repo root). "
            "Useful for testing strict-stale behavior against a fixture or absent directory."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    search = subparsers.add_parser("search")
    search.add_argument("--query", required=True)
    search.add_argument("--top", type=int, default=5)

    neighbors = subparsers.add_parser("neighbors")
    neighbors.add_argument("--page-id", required=True)

    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    # Patch module-level graph path so ensure_graph_ready / open_graph use the override.
    if args.index_dir is not None:
        _wiki_graph.INDEX_DIR = args.index_dir
        _wiki_graph.GRAPH_FILE = args.index_dir / "wiki.kuzu"

    if args.command == "search":
        payload = run_search(args.query, args.top, strict=args.strict, index_dir=args.index_dir)
    else:
        payload = run_neighbors(args.page_id, strict=args.strict)

    content = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(content, encoding="utf-8")
    print(content, end="")
    # Exit 2 if probe itself reported a failure (stale index/graph, setup error).
    if not payload.get("probe_ok", True):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
