#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11,<3.14"
# dependencies = [
#   "duckdb>=0.10.0",
#   "kuzu>=0.6.0",
#   "pyyaml>=6.0",
#   "rich>=13.0",
# ]
# ///
"""
knowledge_review.py - repeatable performance review for the wiki RAG + graph stack.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

import duckdb

from wiki_analytics import compute_kpis, load_wiki
from wiki_common import (
    GRAPH_LOG,
    REVIEW_HISTORY,
    REVIEW_JSON,
    REVIEW_MD,
    SEARCH_LOG,
    SEARCH_METADATA,
    append_jsonl,
    count_recent_events,
    current_wiki_manifest,
    latest_event_timestamp,
    read_json,
    summarize_graph_usage,
    summarize_search_usage,
    write_json,
)
from wiki_graph import get_graph_stats, open_graph


def load_graph_stats() -> tuple[dict[str, object], str | None]:
    try:
        conn = open_graph()
    except SystemExit:
        return {}, "graph-index-missing"
    return get_graph_stats(conn), None


def index_summary() -> dict[str, object]:
    page_count, manifest = current_wiki_manifest()
    metadata = read_json(SEARCH_METADATA)
    indexed_count = int(metadata.get("page_count", 0) or 0) if metadata else 0
    reasons: list[str] = []
    if not metadata:
        reasons.append("missing-metadata")
    if indexed_count != page_count:
        reasons.append("page-count-mismatch")
    if metadata and str(metadata.get("manifest", "")) != manifest:
        reasons.append("manifest-mismatch")
    return {
        "wiki_page_count": page_count,
        "indexed_page_count": indexed_count,
        "fresh": len(reasons) == 0,
        "reasons": reasons,
        "built_at": metadata.get("built_at") if metadata else None,
    }


def evaluate_review(
    kpis: dict[str, object],
    graph_stats: dict[str, object],
    index_info: dict[str, object],
    search_usage: dict[str, object],
    graph_usage: dict[str, object],
) -> tuple[str, dict[str, float], list[str], list[str]]:
    compliance = float(kpis.get("schema_compliance_score", 0))
    orphan_count = len(graph_stats.get("orphans", []))
    page_count = max(int(graph_stats.get("page_nodes", 0) or 0), 1)
    orphan_ratio = orphan_count / page_count
    graph_score = max(0.0, 100.0 - (orphan_ratio * 100.0))
    freshness_score = 100.0 if bool(index_info.get("fresh")) else 55.0
    search_human_queries = int(search_usage.get("human_queries_last_30_days", 0) or 0)
    search_zero_result_rate = 1.0 - float(search_usage.get("hit_rate_last_30_days", 0.0) or 0.0)
    graph_human_actions = int(graph_usage.get("human_actions_last_30_days", 0) or 0)
    graph_action_mix = graph_usage.get("action_mix_last_30_days", {})
    graph_action_diversity = len([name for name, count in (graph_action_mix.items() if isinstance(graph_action_mix, dict) else []) if count])
    adoption_score = round(
        (float(search_usage.get("usage_score", 0.0) or 0.0) * 0.55)
        + (float(graph_usage.get("usage_score", 0.0) or 0.0) * 0.45),
        2,
    )
    health_score = round((compliance * 0.35) + (graph_score * 0.25) + (freshness_score * 0.25) + (adoption_score * 0.15), 2)

    status = "ok"
    reasons: list[str] = []
    actions: list[str] = []

    if not bool(index_info.get("fresh")):
        status = "warn"
        reasons.append("wiki-search-index-stale")
        actions.append("Rebuild the wiki search index so hybrid retrieval stays aligned with current wiki pages.")

    if compliance < 80:
        status = "degraded"
        reasons.append("wiki-schema-compliance-below-80")
        actions.append("Repair wiki metadata compliance before relying on the graph and RAG outputs.")
    elif compliance < 90:
        status = "warn" if status == "ok" else status
        reasons.append("wiki-schema-compliance-below-90")

    if orphan_ratio > 0.25:
        status = "warn" if status == "ok" else status
        reasons.append("graph-orphan-ratio-high")
        actions.append("Link isolated wiki pages with relates_to or depends_on edges.")

    if search_human_queries < 3:
        status = "warn" if status == "ok" else status
        reasons.append("wiki-search-adoption-low")
        actions.append("Use wiki search in real retrieval flows so effectiveness can be measured, not just assumed.")

    if search_human_queries >= 3 and search_zero_result_rate > 0.35:
        status = "warn" if status == "ok" else status
        reasons.append("wiki-search-zero-result-rate-high")
        actions.append("Review common search terms and index coverage so repeated wiki searches do not end in zero-result queries.")

    if graph_human_actions < 2:
        status = "warn" if status == "ok" else status
        reasons.append("wiki-graph-adoption-low")
        actions.append("Use graph stats, neighbors, or dependency queries during research and architecture work.")

    if graph_human_actions >= 2 and graph_action_diversity < 2:
        status = "warn" if status == "ok" else status
        reasons.append("wiki-graph-usage-too-narrow")
        actions.append("Exercise more than one graph workflow (stats, neighbors, deps, query) so graph usage reflects real operational breadth.")

    if not actions:
        actions.append("Knowledge setup is healthy. Continue using search and graph tools in normal workflows.")

    component_scores = {
        "compliance": round(compliance, 2),
        "graph_connectivity": round(graph_score, 2),
        "index_freshness": round(freshness_score, 2),
        "adoption": round(adoption_score, 2),
    }
    return status, component_scores, reasons, actions


def build_review() -> dict[str, object]:
    con = duckdb.connect(":memory:")
    load_wiki(con)
    kpis = compute_kpis(con)
    graph_stats, graph_error = load_graph_stats()
    index_info = index_summary()
    search_usage = summarize_search_usage(days=30)
    graph_usage = summarize_graph_usage(days=30)
    status, scores, reasons, actions = evaluate_review(kpis, graph_stats, index_info, search_usage, graph_usage)

    payload = {
        "created": datetime.now().isoformat(timespec="seconds"),
        "status": status,
        "health_score": round(sum(scores.values()) / len(scores), 2),
        "scores": scores,
        "reasons": reasons,
        "actions": actions,
        "wiki_kpis": kpis,
        "graph": {
            "error": graph_error,
            "page_nodes": graph_stats.get("page_nodes", 0),
            "relates_to_edges": graph_stats.get("relates_to_edges", 0),
            "depends_on_edges": graph_stats.get("depends_on_edges", 0),
            "total_edges": graph_stats.get("total_edges", 0),
            "orphans": len(graph_stats.get("orphans", [])),
        },
        "search_index": index_info,
        "usage": {
            "search_queries_last_30_days": count_recent_events(SEARCH_LOG, days=30, event_type="query"),
            "search_rebuilds_last_30_days": count_recent_events(SEARCH_LOG, days=30, event_type="index_build"),
            "graph_stats_last_30_days": count_recent_events(GRAPH_LOG, days=30, action="stats"),
            "graph_neighbors_last_30_days": count_recent_events(GRAPH_LOG, days=30, action="neighbors"),
            "graph_deps_last_30_days": count_recent_events(GRAPH_LOG, days=30, action="deps"),
            "graph_queries_last_30_days": count_recent_events(GRAPH_LOG, days=30, action="query"),
            "last_search_query_at": latest_event_timestamp(SEARCH_LOG, event_type="query"),
            "last_graph_query_at": latest_event_timestamp(GRAPH_LOG, action="query"),
            "search": search_usage,
            "graph": graph_usage,
        },
    }
    return payload


def render_markdown(payload: dict[str, object]) -> str:
    lines = [
        "---",
        f"created: {payload['created']}",
        "kind: knowledge-performance-review",
        "---",
        "",
        "# Knowledge performance review",
        "",
        f"- **Status:** {payload['status']}",
        f"- **Health score:** {payload['health_score']}",
        f"- **Reasons:** {', '.join(payload['reasons']) if payload['reasons'] else 'none'}",
        "",
        "## Component scores",
        "",
    ]
    for key, value in payload["scores"].items():
        lines.append(f"- **{key.replace('_', ' ').title()}:** {value}")
    lines.extend(
        [
            "",
            "## Search index",
            "",
            f"- **Fresh:** {payload['search_index']['fresh']}",
            f"- **Wiki pages:** {payload['search_index']['wiki_page_count']}",
            f"- **Indexed pages:** {payload['search_index']['indexed_page_count']}",
            f"- **Reasons:** {', '.join(payload['search_index']['reasons']) if payload['search_index']['reasons'] else 'none'}",
            "",
            "## Graph",
            "",
            f"- **Page nodes:** {payload['graph']['page_nodes']}",
            f"- **RELATES_TO edges:** {payload['graph']['relates_to_edges']}",
            f"- **DEPENDS_ON edges:** {payload['graph']['depends_on_edges']}",
            f"- **Orphans:** {payload['graph']['orphans']}",
            "",
            "## Usage (last 30 days)",
            "",
            f"- **Search queries:** {payload['usage']['search_queries_last_30_days']}",
            f"- **Search rebuilds:** {payload['usage']['search_rebuilds_last_30_days']}",
            f"- **Graph stats:** {payload['usage']['graph_stats_last_30_days']}",
            f"- **Graph neighbors:** {payload['usage']['graph_neighbors_last_30_days']}",
            f"- **Graph deps:** {payload['usage']['graph_deps_last_30_days']}",
             f"- **Graph queries:** {payload['usage']['graph_queries_last_30_days']}",
             "",
             "## Search usage KPIs",
             "",
             f"- **Usage score:** {payload['usage']['search']['usage_score']}",
             f"- **Human queries:** {payload['usage']['search']['human_queries_last_30_days']}",
             f"- **Distinct queries:** {payload['usage']['search']['distinct_queries_last_30_days']}",
             f"- **Zero-result queries:** {payload['usage']['search']['zero_result_queries_last_30_days']}",
             f"- **Hit rate:** {payload['usage']['search']['hit_rate_last_30_days']}",
             f"- **Unique top hits:** {payload['usage']['search']['unique_top_hits_last_30_days']}",
             f"- **Last query:** {payload['usage']['search']['last_query_at'] or 'none'}",
             "",
             "## Graph usage KPIs",
             "",
             f"- **Usage score:** {payload['usage']['graph']['usage_score']}",
             f"- **Human actions:** {payload['usage']['graph']['human_actions_last_30_days']}",
             f"- **Action mix:** {payload['usage']['graph']['action_mix_last_30_days']}",
             f"- **Distinct page targets:** {payload['usage']['graph']['distinct_page_targets_last_30_days']}",
             f"- **Distinct queries:** {payload['usage']['graph']['distinct_queries_last_30_days']}",
             f"- **Query success rate:** {payload['usage']['graph']['query_success_rate_last_30_days'] if payload['usage']['graph']['query_success_rate_last_30_days'] is not None else 'n/a'}",
             f"- **Last usage:** {payload['usage']['graph']['last_usage_at'] or 'none'}",
             "",
             "## Actions",
             "",
         ]
    )
    lines.extend(f"- {action}" for action in payload["actions"])
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Review wiki RAG + graph effectiveness.")
    parser.add_argument("--json-out", help="Optional JSON output path")
    parser.add_argument("--markdown-out", help="Optional Markdown output path")
    args = parser.parse_args()

    payload = build_review()
    json_out = Path(args.json_out) if args.json_out else REVIEW_JSON
    md_out = Path(args.markdown_out) if args.markdown_out else REVIEW_MD

    write_json(json_out, payload)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.write_text(render_markdown(payload), encoding="utf-8")

    append_jsonl(
        REVIEW_HISTORY,
        {
            "timestamp": payload["created"],
            "status": payload["status"],
            "health_score": payload["health_score"],
            "search_index_fresh": payload["search_index"]["fresh"],
            "search_queries_last_30_days": payload["usage"]["search_queries_last_30_days"],
            "graph_queries_last_30_days": payload["usage"]["graph_queries_last_30_days"],
            "search_usage_score": payload["usage"]["search"]["usage_score"],
            "graph_usage_score": payload["usage"]["graph"]["usage_score"],
            "search_human_queries_last_30_days": payload["usage"]["search"]["human_queries_last_30_days"],
            "graph_human_actions_last_30_days": payload["usage"]["graph"]["human_actions_last_30_days"],
            "orphans": payload["graph"]["orphans"],
            "reasons": payload["reasons"],
        },
    )

    print(f"STATUS: {payload['status']}")
    print(f"JSON: {json_out}")
    print(f"MARKDOWN: {md_out}")
    print(f"HEALTH_SCORE: {payload['health_score']}")
    print(f"SEARCH_INDEX_FRESH: {payload['search_index']['fresh']}")
    print(f"SEARCH_QUERIES_30D: {payload['usage']['search_queries_last_30_days']}")
    print(f"GRAPH_QUERIES_30D: {payload['usage']['graph_queries_last_30_days']}")


if __name__ == "__main__":
    main()
