#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""
memory_qa.py - repeatable QA and review metrics for the memory system.
"""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timedelta
from pathlib import Path

from memory_common import (
    ACCESS_LOG,
    DAILY_DIR,
    MEMORY_FILE,
    PROCEDURES_FILE,
    REVIEWS_DIR,
    USER_FILE,
    WIKI_DIR,
    append_jsonl,
    benchmark_queries,
    parse_memory_entries,
    read_jsonl,
    search_documents,
    summarize_access_log,
    write_json,
    atomic_write,
)
from memory_maintenance import build_reports


def recent_daily_count(days: int) -> int:
    cutoff = date.today() - timedelta(days=days)
    count = 0
    for path in DAILY_DIR.glob("*.md"):
        try:
            note_date = date.fromisoformat(path.stem)
        except ValueError:
            continue
        if note_date >= cutoff:
            count += 1
    return count


def procedures_rule_count() -> int:
    if not PROCEDURES_FILE.exists():
        return 0
    return sum(1 for line in PROCEDURES_FILE.read_text(encoding="utf-8").splitlines() if line.strip().startswith("- "))


def latest_review_metrics() -> dict[str, int]:
    review_path = REVIEWS_DIR / "latest-memory-review.json"
    if not review_path.exists():
        return {"items": 0, "needs_review": 0, "contradictions": 0}
    payload = json.loads(review_path.read_text(encoding="utf-8"))
    items = payload.get("items", [])
    return {
        "items": len(items),
        "needs_review": sum(1 for item in items if item.get("review_state") == "needs-review"),
        "contradictions": sum(1 for item in items if item.get("relation") == "contradictory"),
    }


def freshness_score(entries_count: int) -> float:
    if entries_count == 0:
        return 1.0
    recent_entries = sum(1 for entry in parse_memory_entries() if entry.entry_date and (date.today() - entry.entry_date).days <= 30)
    return round(recent_entries / entries_count, 4)


def coverage_score() -> float:
    files = [MEMORY_FILE, PROCEDURES_FILE, USER_FILE]
    existing = sum(1 for path in files if path.exists())
    daily_recent = 1 if recent_daily_count(14) > 0 else 0
    wiki_recent = 1 if any(path.exists() for path in WIKI_DIR.glob("*.md")) else 0
    reviews_recent = 1 if any(path.exists() for path in REVIEWS_DIR.glob("*.json")) else 0
    return round((existing + daily_recent + wiki_recent + reviews_recent) / 6.0, 4)


def coherence_score(entries_count: int, review: dict[str, int]) -> float:
    if entries_count == 0:
        return 1.0
    contradiction_penalty = review["contradictions"] / max(review["items"], 1) if review["items"] else 0.0
    return round(max(0.0, 1.0 - contradiction_penalty), 4)


def efficiency_score(entries_count: int) -> float:
    entries = parse_memory_entries()
    if not entries:
        return 1.0
    unique = len({entry.text.lower().strip() for entry in entries})
    avg_len = sum(len(entry.text) for entry in entries) / len(entries)
    redundancy = unique / len(entries)
    brevity = min(1.0, 160.0 / max(avg_len, 1.0))
    return round((redundancy + brevity) / 2.0, 4)


def reachability_score() -> tuple[float, list[dict[str, object]]]:
    query_results: list[dict[str, object]] = []
    success = 0
    for query in benchmark_queries():
        hits = search_documents(query, limit=3, daily_days=60)
        query_results.append(
            {
                "query": query,
                "hits": [hit.to_dict() for hit in hits],
            }
        )
        if hits:
            success += 1
    return round(success / max(len(query_results), 1), 4), query_results


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate repeatable QA metrics for the memory system.")
    parser.add_argument("--json-out", help="Optional JSON output path")
    parser.add_argument("--markdown-out", help="Optional markdown output path")
    args = parser.parse_args()

    entries_count = len(parse_memory_entries())
    review = latest_review_metrics()
    freshness = freshness_score(entries_count)
    coverage = coverage_score()
    coherence = coherence_score(entries_count, review)
    efficiency = efficiency_score(entries_count)
    reachability, query_results = reachability_score()
    usage = summarize_access_log(days=30)
    maintenance_summary, _ = build_reports()
    health_score = round(((freshness + coverage + coherence + efficiency + reachability) / 5.0) * 100.0, 2)

    payload = {
        "created": datetime.now().isoformat(timespec="seconds"),
        "health_score": health_score,
        "scores": {
            "freshness": freshness,
            "coverage": coverage,
            "coherence": coherence,
            "efficiency": efficiency,
            "reachability": reachability,
        },
        "counts": {
            "memory_entries": entries_count,
            "procedure_rules": procedures_rule_count(),
            "wiki_pages": len(list(WIKI_DIR.glob("*.md"))),
            "daily_notes_last_14_days": recent_daily_count(14),
            "daily_notes_last_30_days": recent_daily_count(30),
            "access_log_events": len(read_jsonl(ACCESS_LOG)),
            "access_log_events_last_30_days": usage["events_last_30_days"],
        },
        "review": review,
        "usage": usage,
        "maintenance": maintenance_summary,
        "benchmark_queries": query_results,
    }

    markdown = "\n".join(
        [
            "---",
            f"created: {payload['created']}",
            "kind: memory-qa",
            "---",
            "",
            "# Memory QA report",
            "",
            f"- **Health score:** {health_score}",
            f"- **Freshness:** {freshness}",
            f"- **Coverage:** {coverage}",
            f"- **Coherence:** {coherence}",
            f"- **Efficiency:** {efficiency}",
            f"- **Reachability:** {reachability}",
            "",
            "## Counts",
            "",
            *[f"- **{key}:** {value}" for key, value in payload["counts"].items()],
            "",
             "## Review",
             "",
             *[f"- **{key}:** {value}" for key, value in review.items()],
             "",
             "## Usage",
             "",
             f"- **Adoption score:** {usage['adoption_score']}",
             f"- **Access events (30d):** {usage['events_last_30_days']}",
             f"- **Distinct queries (30d):** {usage['distinct_queries_last_30_days']}",
             f"- **Zero-hit queries (30d):** {usage['zero_hit_queries_last_30_days']}",
             f"- **Hit rate (30d):** {usage['hit_rate_last_30_days']}",
             f"- **Source types touched (30d):** {usage['source_types_touched_last_30_days']}",
             f"- **Last access:** {usage['last_access_at'] or 'none'}",
             "",
             "## Maintenance",
             "",
             f"- **Reinforcement candidates:** {maintenance_summary['reinforcement_candidates']}",
            f"- **Archive candidates:** {maintenance_summary['archive_candidates']}",
            "",
        ]
    ).rstrip() + "\n"

    json_out = Path(args.json_out) if args.json_out else REVIEWS_DIR / "memory-qa.json"
    markdown_out = Path(args.markdown_out) if args.markdown_out else REVIEWS_DIR / "memory-qa.md"
    write_json(json_out, payload)
    atomic_write(markdown_out, markdown)
    append_jsonl(
        REVIEWS_DIR / "memory-qa-history.jsonl",
        {
            "timestamp": payload["created"],
            "health_score": health_score,
            "scores": payload["scores"],
            "review": review,
            "counts": payload["counts"],
            "usage": {
                "adoption_score": usage["adoption_score"],
                "events_last_30_days": usage["events_last_30_days"],
                "distinct_queries_last_30_days": usage["distinct_queries_last_30_days"],
                "hit_rate_last_30_days": usage["hit_rate_last_30_days"],
            },
        },
    )

    print(f"MARKDOWN: {markdown_out}")
    print(f"JSON: {json_out}")
    print(f"HEALTH_SCORE: {health_score}")
    print(f"REVIEW_NEEDS_REVIEW: {review['needs_review']}")
    print(f"ARCHIVE_CANDIDATES: {maintenance_summary['archive_candidates']}")


if __name__ == "__main__":
    main()
