from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

VAULT = Path(__file__).resolve().parents[2]
WIKI_DIR = VAULT / "wiki"
INDEX_DIR = VAULT / ".wiki_index"
REVIEWS_DIR = WIKI_DIR / "reviews"
SKIP_FILES = {"_schema.md", "index.md", "log.md"}
SEARCH_LOG = REVIEWS_DIR / "wiki-search-log.jsonl"
GRAPH_LOG = REVIEWS_DIR / "wiki-graph-log.jsonl"
REVIEW_JSON = REVIEWS_DIR / "knowledge-performance-review.json"
REVIEW_MD = REVIEWS_DIR / "knowledge-performance-review.md"
REVIEW_HISTORY = REVIEWS_DIR / "knowledge-performance-history.jsonl"
SEARCH_METADATA = INDEX_DIR / "wiki-search-metadata.json"


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(content, encoding="utf-8")
    temp.replace(path)


def write_json(path: Path, payload: object) -> None:
    atomic_write(path, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def append_jsonl(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def read_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def read_jsonl(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    rows: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def wiki_markdown_files() -> list[Path]:
    return sorted(path for path in WIKI_DIR.glob("*.md") if path.name not in SKIP_FILES)


def compute_manifest(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def current_wiki_manifest() -> tuple[int, str]:
    paths = wiki_markdown_files()
    return len(paths), compute_manifest(paths)


def parse_iso_timestamp(value: object) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


def recent_records(
    path: Path,
    *,
    days: int = 30,
    event_type: str | None = None,
    action: str | None = None,
) -> list[dict[str, object]]:
    cutoff = datetime.now() - timedelta(days=days)
    items: list[dict[str, object]] = []
    for record in read_jsonl(path):
        timestamp = parse_iso_timestamp(record.get("timestamp"))
        if timestamp is None or timestamp < cutoff:
            continue
        if event_type and str(record.get("event_type", "")) != event_type:
            continue
        if action and str(record.get("action", "")) != action:
            continue
        items.append(record)
    return items


def _normalize_value(value: object) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _recency_score(records: list[dict[str, object]], *, days: int) -> float:
    latest: datetime | None = None
    for record in records:
        timestamp = parse_iso_timestamp(record.get("timestamp"))
        if timestamp is None:
            continue
        if latest is None or timestamp > latest:
            latest = timestamp
    if latest is None:
        return 0.0
    days_since = max(0.0, (datetime.now() - latest).total_seconds() / 86400.0)
    return max(0.0, 1.0 - min(days_since, float(days)) / float(days))


def summarize_search_usage(*, days: int = 30) -> dict[str, object]:
    query_records = recent_records(SEARCH_LOG, days=days, event_type="query")
    human_queries = [record for record in query_records if str(record.get("query_kind", "")).strip().lower() != "probe"]
    probe_queries = [record for record in query_records if str(record.get("query_kind", "")).strip().lower() == "probe"]
    distinct_queries = {
        _normalize_value(record.get("query"))
        for record in query_records
        if _normalize_value(record.get("query"))
    }
    zero_result_queries = sum(1 for record in query_records if int(record.get("result_count", 0) or 0) <= 0)
    successful_queries = sum(1 for record in query_records if int(record.get("result_count", 0) or 0) > 0)
    unique_top_hits = {
        str(record.get("top_hit", "")).strip()
        for record in query_records
        if str(record.get("top_hit", "")).strip()
    }
    modes = Counter(str(record.get("mode", "")).strip() or "unknown" for record in query_records)
    active_days = {
        timestamp.date().isoformat()
        for timestamp in (parse_iso_timestamp(record.get("timestamp")) for record in query_records)
        if timestamp is not None
    }
    durations = [
        float(record.get("duration_ms", 0.0) or 0.0)
        for record in query_records
        if isinstance(record.get("duration_ms"), (int, float))
    ]
    hit_rate = successful_queries / len(query_records) if query_records else 0.0
    weighted_volume = min(1.0, (len(human_queries) + (0.5 * len(probe_queries))) / 6.0)
    diversity = min(1.0, len(distinct_queries) / 6.0)
    hit_diversity = min(1.0, len(unique_top_hits) / 6.0)
    recency = _recency_score(query_records, days=days)
    usage_score = round(((weighted_volume + diversity + hit_rate + hit_diversity + recency) / 5.0) * 100.0, 2)

    return {
        f"queries_last_{days}_days": len(query_records),
        f"human_queries_last_{days}_days": len(human_queries),
        f"probe_queries_last_{days}_days": len(probe_queries),
        f"distinct_queries_last_{days}_days": len(distinct_queries),
        f"zero_result_queries_last_{days}_days": zero_result_queries,
        f"hit_rate_last_{days}_days": round(hit_rate, 4),
        f"unique_top_hits_last_{days}_days": len(unique_top_hits),
        f"mode_mix_last_{days}_days": dict(sorted(modes.items())),
        f"active_days_last_{days}_days": len(active_days),
        f"avg_duration_ms_last_{days}_days": round(sum(durations) / len(durations), 1) if durations else 0.0,
        "last_query_at": latest_event_timestamp(SEARCH_LOG, event_type="query"),
        "usage_score": usage_score,
    }


def summarize_graph_usage(*, days: int = 30) -> dict[str, object]:
    all_recent = recent_records(GRAPH_LOG, days=days)
    usage_records = [
        record for record in all_recent if str(record.get("action", "")).strip() in {"stats", "neighbors", "deps", "query"}
    ]
    human_usage = [record for record in usage_records if not bool(record.get("probe"))]
    probe_usage = [record for record in usage_records if bool(record.get("probe"))]
    action_mix = Counter(str(record.get("action", "")).strip() for record in usage_records)
    distinct_targets = {
        str(record.get("page_id", "")).strip()
        for record in usage_records
        if str(record.get("page_id", "")).strip()
    }
    distinct_queries = {
        _normalize_value(record.get("query"))
        for record in usage_records
        if str(record.get("action", "")).strip() == "query" and _normalize_value(record.get("query"))
    }
    active_days = {
        timestamp.date().isoformat()
        for timestamp in (parse_iso_timestamp(record.get("timestamp")) for record in usage_records)
        if timestamp is not None
    }
    durations = [
        float(record.get("duration_ms", 0.0) or 0.0)
        for record in usage_records
        if isinstance(record.get("duration_ms"), (int, float))
    ]
    query_records = [record for record in usage_records if str(record.get("action", "")).strip() == "query"]
    query_result_samples = [
        int(record.get("result_count", 0) or 0)
        for record in query_records
        if isinstance(record.get("result_count"), (int, float))
    ]
    query_success_rate = (
        sum(1 for count in query_result_samples if count > 0) / len(query_result_samples)
        if query_result_samples
        else 0.0
    )
    weighted_volume = min(1.0, (len(human_usage) + (0.5 * len(probe_usage))) / 4.0)
    action_diversity = sum(1 for count in action_mix.values() if count > 0) / 4.0 if usage_records else 0.0
    target_diversity = min(1.0, (len(distinct_targets) + len(distinct_queries)) / 4.0)
    query_success_component = query_success_rate if query_result_samples else 0.5
    recency = _recency_score(usage_records, days=days)
    usage_score = round(
        ((weighted_volume + action_diversity + target_diversity + query_success_component + recency) / 5.0) * 100.0,
        2,
    )

    return {
        f"actions_last_{days}_days": len(usage_records),
        f"human_actions_last_{days}_days": len(human_usage),
        f"probe_actions_last_{days}_days": len(probe_usage),
        f"builds_last_{days}_days": sum(1 for record in all_recent if str(record.get('action', '')).strip() == 'build'),
        f"action_mix_last_{days}_days": dict(sorted(action_mix.items())),
        f"distinct_page_targets_last_{days}_days": len(distinct_targets),
        f"distinct_queries_last_{days}_days": len(distinct_queries),
        f"query_success_rate_last_{days}_days": round(query_success_rate, 4) if query_result_samples else None,
        f"active_days_last_{days}_days": len(active_days),
        f"avg_duration_ms_last_{days}_days": round(sum(durations) / len(durations), 1) if durations else 0.0,
        "last_usage_at": latest_event_timestamp(GRAPH_LOG),
        "last_query_at": latest_event_timestamp(GRAPH_LOG, action="query"),
        "usage_score": usage_score,
    }


def count_recent_events(path: Path, *, days: int = 30, event_type: str | None = None, action: str | None = None) -> int:
    return len(recent_records(path, days=days, event_type=event_type, action=action))


def latest_event_timestamp(path: Path, *, event_type: str | None = None, action: str | None = None) -> str | None:
    latest: str | None = None
    for record in read_jsonl(path):
        if event_type and str(record.get("event_type", "")) != event_type:
            continue
        if action and str(record.get("action", "")) != action:
            continue
        timestamp = str(record.get("timestamp", "")).strip()
        if not timestamp:
            continue
        if latest is None or timestamp > latest:
            latest = timestamp
    return latest
