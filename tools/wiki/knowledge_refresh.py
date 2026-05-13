#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11,<3.14"
# dependencies = [
#   "lancedb>=0.6.0",
#   "sentence-transformers>=3.0",
#   "duckdb>=0.10.0",
#   "kuzu>=0.6.0",
#   "pyyaml>=6.0",
#   "rich>=13.0",
#   "rank_bm25>=0.2",
# ]
# ///
"""
knowledge_refresh.py - Repair and probe the wiki knowledge stack before rewriting the knowledge review.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from time import perf_counter
from typing import Any

import lancedb

from knowledge_review import build_review, render_markdown as render_review_markdown
from wiki_common import (
    GRAPH_LOG,
    REVIEW_HISTORY,
    REVIEW_JSON,
    REVIEW_MD,
    SEARCH_LOG,
    append_jsonl,
    count_recent_events,
    now_iso,
    read_json,
    write_json,
)
from wiki_graph import build_graph, get_graph_stats, open_graph
from wiki_search import (
    INDEX_DIR,
    MODEL_NAME,
    TABLE_NAME,
    SentenceTransformer,
    build_index,
    hybrid_search,
    index_status,
    load_pages,
    log_event,
)


DEFAULT_SEARCH_PROBES = [
    "working memory scratchpad",
    "agent orchestration policy",
    "memory lifecycle",
]
DEFAULT_GRAPH_QUERY = (
    "MATCH (a:Page)-[r:RELATES_TO|DEPENDS_ON]->(b:Page) "
    "RETURN a.id, label(r), b.id LIMIT 5"
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(content, encoding="utf-8")
    temp.replace(path)


def default_markdown_out() -> Path:
    return repo_root() / "wiki" / "reviews" / "knowledge-refresh.md"


def default_json_out() -> Path:
    return repo_root() / "wiki" / "reviews" / "knowledge-refresh.json"


def graph_is_available() -> bool:
    try:
        open_graph()
        return True
    except SystemExit:
        return False


def inspect_state() -> dict[str, Any]:
    pages = load_pages()
    db = lancedb.connect(str(INDEX_DIR / "lancedb"))
    index_info = index_status(db, pages)
    existing_review = read_json(REVIEW_JSON)
    search_queries = count_recent_events(SEARCH_LOG, days=30, event_type="query")
    graph_usage = (
        count_recent_events(GRAPH_LOG, days=30, action="stats")
        + count_recent_events(GRAPH_LOG, days=30, action="neighbors")
        + count_recent_events(GRAPH_LOG, days=30, action="deps")
        + count_recent_events(GRAPH_LOG, days=30, action="query")
    )
    return {
        "page_count": len(pages),
        "graph_available": graph_is_available(),
        "index_info": index_info,
        "review_status": str(existing_review.get("status") or "missing"),
        "review_reasons": list(existing_review.get("reasons") or []),
        "search_queries_last_30_days": search_queries,
        "graph_usage_last_30_days": graph_usage,
    }


def planned_actions(state: dict[str, Any], force_rebuild: bool, force_probe: bool) -> list[str]:
    actions: list[str] = []
    if force_rebuild or not state["graph_available"]:
        actions.append("rebuild_graph")
    if force_rebuild or not bool(state["index_info"].get("fresh")):
        actions.append("rebuild_search_index")
    if force_probe or int(state["search_queries_last_30_days"]) < 3:
        actions.append("run_search_probes")
    if force_probe or int(state["graph_usage_last_30_days"]) < 2:
        actions.append("run_graph_probes")
    actions.append("refresh_knowledge_review")
    return actions


def run_search_probes(pages: list[dict[str, Any]], top_n: int) -> list[dict[str, Any]]:
    db = lancedb.connect(str(INDEX_DIR / "lancedb"))
    table = db.open_table(TABLE_NAME)
    model = SentenceTransformer(MODEL_NAME)
    results: list[dict[str, Any]] = []
    for query in DEFAULT_SEARCH_PROBES:
        started = perf_counter()
        hits = hybrid_search(query, table, pages, model, top_n)
        duration_ms = round((perf_counter() - started) * 1000, 1)
        log_event(
            {
                "event_type": "query",
                "query_kind": "probe",
                "mode": "hybrid (RRF)",
                "query": query,
                "top_n": top_n,
                "result_count": len(hits),
                "duration_ms": duration_ms,
                "wiki_page_count": len(pages),
                "indexed_page_count": table.count_rows(),
                "index_fresh": True,
                "stale_reasons": [],
                "top_hit": hits[0]["file"] if hits else None,
            }
        )
        results.append(
            {
                "query": query,
                "duration_ms": duration_ms,
                "result_count": len(hits),
                "top_hit_file": hits[0]["file"] if hits else None,
                "top_hit_title": hits[0]["title"] if hits else None,
                "top_hit_score": hits[0]["score"] if hits else None,
            }
        )
    return results


def run_graph_probes() -> dict[str, Any]:
    conn = open_graph()
    started = perf_counter()
    stats = get_graph_stats(conn)
    stats_duration_ms = round((perf_counter() - started) * 1000, 1)
    append_jsonl(
        GRAPH_LOG,
        {
            "timestamp": now_iso(),
            "action": "stats",
            "probe": True,
            "duration_ms": stats_duration_ms,
            "page_count": stats.get("page_nodes", 0),
        },
    )

    started = perf_counter()
    query_result = conn.execute(DEFAULT_GRAPH_QUERY)
    rows: list[list[str]] = []
    while query_result.has_next():
        row = query_result.get_next()
        rows.append([str(item) for item in row])
    query_duration_ms = round((perf_counter() - started) * 1000, 1)
    append_jsonl(
        GRAPH_LOG,
        {
            "timestamp": now_iso(),
            "action": "query",
            "probe": True,
            "query": DEFAULT_GRAPH_QUERY,
            "duration_ms": query_duration_ms,
            "result_count": len(rows),
        },
    )
    return {
        "stats_duration_ms": stats_duration_ms,
        "query_duration_ms": query_duration_ms,
        "page_nodes": stats.get("page_nodes", 0),
        "total_edges": stats.get("total_edges", 0),
        "sample_rows": rows[:5],
    }


def write_knowledge_review() -> dict[str, Any]:
    payload = build_review()
    write_json(REVIEW_JSON, payload)
    atomic_write(REVIEW_MD, render_review_markdown(payload))
    append_jsonl(
        REVIEW_HISTORY,
        {
            "timestamp": payload["created"],
            "status": payload["status"],
            "health_score": payload["health_score"],
            "search_index_fresh": payload["search_index"]["fresh"],
            "search_queries_last_30_days": payload["usage"]["search_queries_last_30_days"],
            "graph_queries_last_30_days": payload["usage"]["graph_queries_last_30_days"],
            "orphans": payload["graph"]["orphans"],
            "reasons": payload["reasons"],
            "refresh_runtime": True,
        },
    )
    return payload


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "---",
        f"created: {payload['created']}",
        "kind: knowledge-refresh",
        "---",
        "",
        "# Knowledge refresh",
        "",
        f"- **Mode:** {payload['mode']}",
        f"- **Status:** {payload['status']}",
        f"- **Executed actions:** {', '.join(payload['executed_actions']) if payload['executed_actions'] else 'none'}",
        f"- **Knowledge review status:** {payload['knowledge_review']['status']}",
        f"- **Knowledge review score:** {payload['knowledge_review']['health_score']}",
        "",
        "## Before",
        "",
        f"- **Review status:** {payload['before']['review_status']}",
        f"- **Graph available:** {payload['before']['graph_available']}",
        f"- **Index fresh:** {payload['before']['index_info']['fresh']}",
        f"- **Search queries 30d:** {payload['before']['search_queries_last_30_days']}",
        f"- **Graph usage 30d:** {payload['before']['graph_usage_last_30_days']}",
        "",
        "## After",
        "",
        f"- **Review status:** {payload['after']['review_status']}",
        f"- **Graph available:** {payload['after']['graph_available']}",
        f"- **Index fresh:** {payload['after']['index_info']['fresh']}",
        f"- **Search queries 30d:** {payload['after']['search_queries_last_30_days']}",
        f"- **Graph usage 30d:** {payload['after']['graph_usage_last_30_days']}",
        "",
    ]
    if payload["search_probes"]:
        lines.extend(["## Search probes", ""])
        for item in payload["search_probes"]:
            lines.append(
                f"- **{item['query']}** — results {item['result_count']}, top hit `{item['top_hit_file'] or 'none'}`"
            )
        lines.append("")
    graph_probe = payload.get("graph_probe") or {}
    if graph_probe:
        lines.extend(
            [
                "## Graph probes",
                "",
                f"- **Page nodes:** {graph_probe.get('page_nodes', 0)}",
                f"- **Total edges:** {graph_probe.get('total_edges', 0)}",
                f"- **Sample rows:** {len(graph_probe.get('sample_rows') or [])}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Repair stale wiki knowledge state and refresh review artifacts.")
    parser.add_argument("--mode", choices=["preview", "apply"], default="preview")
    parser.add_argument("--force-rebuild", action="store_true", help="Force graph and search rebuild.")
    parser.add_argument("--force-probe", action="store_true", help="Force search and graph probes.")
    parser.add_argument("--top", type=int, default=5, help="Top results to keep for search probes.")
    parser.add_argument("--json-out", type=Path, default=default_json_out(), help="Refresh JSON artifact path.")
    parser.add_argument("--markdown-out", type=Path, default=default_markdown_out(), help="Refresh markdown artifact path.")
    parser.add_argument("--print", action="store_true", help="Print the markdown artifact.")
    args = parser.parse_args()

    started = perf_counter()
    before = inspect_state()
    actions = planned_actions(before, args.force_rebuild, args.force_probe)
    executed: list[str] = []
    search_probes: list[dict[str, Any]] = []
    graph_probe: dict[str, Any] | None = None

    if args.mode == "apply":
        pages = load_pages()
        if "rebuild_graph" in actions:
            build_graph(pages)
            executed.append("rebuild_graph")
        if "rebuild_search_index" in actions:
            model = SentenceTransformer(MODEL_NAME)
            build_index(pages, model)
            executed.append("rebuild_search_index")
        if "run_search_probes" in actions:
            search_probes = run_search_probes(pages, args.top)
            executed.append("run_search_probes")
        if "run_graph_probes" in actions:
            graph_probe = run_graph_probes()
            executed.append("run_graph_probes")

    if args.mode == "apply":
        review_payload = write_knowledge_review()
        executed.append("refresh_knowledge_review")
    else:
        review_payload = read_json(REVIEW_JSON)
        if not review_payload:
            review_payload = build_review()
    after = inspect_state()

    status = "ok" if review_payload["status"] == "ok" else "warn"
    payload = {
        "created": datetime.now().isoformat(timespec="seconds"),
        "mode": args.mode,
        "status": status,
        "planned_actions": actions,
        "executed_actions": executed,
        "duration_ms": round((perf_counter() - started) * 1000, 1),
        "before": before,
        "after": after,
        "search_probes": search_probes,
        "graph_probe": graph_probe,
        "knowledge_review": {
            "status": review_payload["status"],
            "health_score": review_payload["health_score"],
            "reasons": review_payload["reasons"],
        },
    }
    write_json(args.json_out, payload)
    atomic_write(args.markdown_out, render_markdown(payload))

    print(f"STATUS: {payload['status']}")
    print(f"KNOWLEDGE_STATUS: {review_payload['status']}")
    print(f"JSON: {args.json_out}")
    print(f"MARKDOWN: {args.markdown_out}")
    print(f"EXECUTED_ACTIONS: {len(executed)}")
    print(f"INDEX_FRESH: {after['index_info']['fresh']}")
    print(f"SEARCH_QUERIES_30D: {after['search_queries_last_30_days']}")
    print(f"GRAPH_USAGE_30D: {after['graph_usage_last_30_days']}")
    if args.print:
        print()
        print(render_markdown(payload), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
