#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""
memory_retrieval.py - local retrieval over memory, wiki, episodes, and recent daily notes.

Usage:
    uv run tools/memory/memory_retrieval.py --query "working memory scratchpad"
"""

from __future__ import annotations

import argparse
import json

from memory_common import benchmark_queries, log_access, search_documents


def _warmup() -> int:
    """Run all benchmark queries and log each — seeds the access log for memory compounding."""
    queries = benchmark_queries()
    for query in queries:
        hits = search_documents(query, limit=5)
        log_access(query, hits)
    return len(queries)


def _log_fact(fact_text: str) -> None:
    """Directly log a named memory fact reference without performing a search.

    Used by James at session handoff to mark which MEMORY.md entries were
    actually referenced during the session, ensuring reference_count compounds.
    """
    from memory_common import ACCESS_LOG, fingerprint, append_jsonl
    from datetime import datetime

    append_jsonl(
        ACCESS_LOG,
        {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "query": "__direct_fact_reference__",
            "hits": [
                {
                    "path": "memory/MEMORY.md",
                    "line_no": -1,
                    "source_type": "memory",
                    "fingerprint": fingerprint(fact_text),
                    "score": 1.0,
                }
            ],
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Search local memory artifacts for related context.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--query", help="Search query")
    mode.add_argument("--warmup", action="store_true", help="Run all benchmark queries and log them (seeds memory compounding)")
    mode.add_argument("--log-fact", metavar="TEXT", dest="log_fact", help="Directly log a named memory fact reference to the access log")
    parser.add_argument("--limit", type=int, default=8, help="Maximum results (search mode only)")
    parser.add_argument("--daily-days", type=int, default=30, help="Daily note lookback window")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    parser.add_argument("--no-log", action="store_true", help="Skip retrieval access logging")
    args = parser.parse_args()

    if args.warmup:
        count = _warmup()
        print(f"WARMUP: {count} benchmark queries logged")
        return

    if args.log_fact:
        _log_fact(args.log_fact)
        print(f"LOGGED: direct fact reference — {args.log_fact[:80]}")
        return

    if not args.query:
        parser.error("One of --query, --warmup, or --log-fact is required")

    hits = search_documents(args.query, limit=args.limit, daily_days=args.daily_days)
    if not args.no_log:
        log_access(args.query, hits)

    if args.json:
        print(json.dumps([hit.to_dict() for hit in hits], indent=2, ensure_ascii=False))
        return

    print(f"QUERY: {args.query}")
    print(f"HITS: {len(hits)}")
    for idx, hit in enumerate(hits, start=1):
        print(f"{idx}. [{hit.source_type}] score={hit.score:.3f} {hit.path}:{hit.line_no}")
        print(f"   {hit.text}")


if __name__ == "__main__":
    main()
