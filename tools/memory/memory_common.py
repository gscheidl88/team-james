from __future__ import annotations

import json
import math
import re
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

VAULT = Path(__file__).resolve().parents[2]
MEMORY_DIR = VAULT / "memory"
WIKI_DIR = VAULT / "wiki"
DAILY_DIR = VAULT / "PersonalNotes" / "Daily"
EPISODES_DIR = MEMORY_DIR / "episodes"
REVIEWS_DIR = MEMORY_DIR / "reviews"
MEMORY_FILE = MEMORY_DIR / "MEMORY.md"
PROCEDURES_FILE = MEMORY_DIR / "procedures.md"
USER_FILE = MEMORY_DIR / "USER.md"
ACCESS_LOG = MEMORY_DIR / "access-log.jsonl"

TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{1,}")
MEM_ENTRY_RE = re.compile(
    r"^-\s+(?:`\[(?P<mem_id>mem_\d+)\]`\s+)?(?:`\[(?P<entry_date>\d{4}-\d{2}-\d{2})\]`\s+)?(?P<text>.+)$"
)


@dataclass
class SourceHit:
    path: str
    line_no: int
    score: float
    source_type: str
    text: str

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["score"] = round(self.score, 4)
        return payload


@dataclass
class MemoryEntry:
    mem_id: str | None
    entry_date: date | None
    text: str
    line_no: int


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


def read_jsonl(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    items: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            items.append(json.loads(stripped))
        except json.JSONDecodeError:
            continue
    return items


def parse_iso_timestamp(value: object) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


def recent_jsonl_records(path: Path, *, days: int = 30) -> list[dict[str, object]]:
    cutoff = datetime.now() - timedelta(days=days)
    records: list[dict[str, object]] = []
    for record in read_jsonl(path):
        timestamp = parse_iso_timestamp(record.get("timestamp"))
        if timestamp is None or timestamp < cutoff:
            continue
        records.append(record)
    return records


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


def normalize_text(text: str) -> str:
    return " ".join(tokenize(text))


def fingerprint(text: str) -> str:
    return normalize_text(text)[:120]


def relpath(path: Path) -> str:
    try:
        return str(path.relative_to(VAULT)).replace("\\", "/")
    except ValueError:
        return str(path)


def source_type_for(path: Path) -> str:
    if path == MEMORY_FILE:
        return "memory"
    if path == PROCEDURES_FILE:
        return "procedures"
    if path == USER_FILE:
        return "user"
    if path.is_relative_to(WIKI_DIR):
        return "wiki"
    if path.is_relative_to(DAILY_DIR):
        return "daily"
    if path.is_relative_to(EPISODES_DIR):
        return "episode"
    if "session-state" in str(path).lower():
        return "session"
    return "other"


def _source_weight(kind: str) -> float:
    return {
        "memory": 0.55,
        "procedures": 0.5,
        "user": 0.45,
        "wiki": 0.4,
        "episode": 0.35,
        "daily": 0.25,
        "session": 0.2,
    }.get(kind, 0.1)


def _daily_recency_bonus(path: Path) -> float:
    try:
        days_old = (date.today() - date.fromisoformat(path.stem)).days
    except ValueError:
        return 0.0
    return max(0.0, 0.25 - (days_old / 120.0))


def collect_documents(daily_days: int = 30, extra_paths: list[Path] | None = None) -> list[Path]:
    docs: list[Path] = []
    docs.extend(path for path in (MEMORY_FILE, PROCEDURES_FILE, USER_FILE) if path.exists())
    docs.extend(sorted(path for path in EPISODES_DIR.glob("*.md") if path.is_file()))
    docs.extend(sorted(path for path in WIKI_DIR.glob("*.md") if path.is_file()))

    for path in sorted(DAILY_DIR.glob("*.md")):
        try:
            days_old = (date.today() - date.fromisoformat(path.stem)).days
        except ValueError:
            continue
        if 0 <= days_old <= daily_days:
            docs.append(path)

    if extra_paths:
        for path in extra_paths:
            if path.exists():
                docs.append(path)

    seen: set[Path] = set()
    deduped: list[Path] = []
    for path in docs:
        if path not in seen:
            seen.add(path)
            deduped.append(path)
    return deduped


def search_documents(
    query: str,
    *,
    limit: int = 10,
    daily_days: int = 30,
    extra_paths: list[Path] | None = None,
) -> list[SourceHit]:
    query_text = query.strip()
    query_tokens = set(tokenize(query_text))
    if not query_text or not query_tokens:
        return []

    hits: list[SourceHit] = []
    for path in collect_documents(daily_days=daily_days, extra_paths=extra_paths):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue

        kind = source_type_for(path)
        weight = _source_weight(kind)
        if kind == "daily":
            weight += _daily_recency_bonus(path)

        for line_no, raw_line in enumerate(lines, start=1):
            text = raw_line.strip()
            if len(text) < 4 or text in {"---", "***"}:
                continue
            line_tokens = set(tokenize(text))
            overlap = len(query_tokens & line_tokens)
            phrase_hit = query_text.lower() in text.lower()
            if overlap == 0 and not phrase_hit:
                continue
            score = weight + (overlap / max(len(query_tokens), 1))
            if phrase_hit:
                score += 0.75
            if text.startswith("#"):
                score -= 0.1
            hits.append(
                SourceHit(
                    path=relpath(path),
                    line_no=line_no,
                    score=score,
                    source_type=kind,
                    text=text,
                )
            )

    hits.sort(key=lambda item: (-item.score, item.path, item.line_no))
    return hits[:limit]


def log_access(query: str, hits: list[SourceHit]) -> None:
    append_jsonl(
        ACCESS_LOG,
        {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "query": query,
            "hits": [
                {
                    "path": hit.path,
                    "line_no": hit.line_no,
                    "source_type": hit.source_type,
                    "fingerprint": fingerprint(hit.text),
                    "score": round(hit.score, 4),
                }
                for hit in hits[:5]
            ],
        },
    )


def summarize_access_log(*, days: int = 30) -> dict[str, object]:
    all_records = read_jsonl(ACCESS_LOG)
    recent_records = recent_jsonl_records(ACCESS_LOG, days=days)
    distinct_queries: set[str] = set()
    hit_paths: Counter[str] = Counter()
    source_mix: Counter[str] = Counter()
    top_scores: list[float] = []
    active_days: set[str] = set()
    zero_hit_queries = 0
    hits_logged = 0
    latest_access: datetime | None = None

    for record in recent_records:
        query = normalize_text(str(record.get("query", "")).strip())
        if query:
            distinct_queries.add(query)
        timestamp = parse_iso_timestamp(record.get("timestamp"))
        if timestamp is not None:
            active_days.add(timestamp.date().isoformat())
            if latest_access is None or timestamp > latest_access:
                latest_access = timestamp

        hits = record.get("hits")
        if not isinstance(hits, list) or not hits:
            zero_hit_queries += 1
            continue

        hits_logged += len(hits)
        top_score = None
        for raw_hit in hits:
            if not isinstance(raw_hit, dict):
                continue
            path = str(raw_hit.get("path", "")).strip()
            if path:
                hit_paths[path] += 1
            source_type = str(raw_hit.get("source_type", "")).strip() or "unknown"
            source_mix[source_type] += 1
            try:
                score = float(raw_hit.get("score", 0.0))
            except (TypeError, ValueError):
                continue
            if top_score is None or score > top_score:
                top_score = score
        if top_score is not None:
            top_scores.append(top_score)

    event_count = len(recent_records)
    hit_rate = (event_count - zero_hit_queries) / event_count if event_count else 0.0
    avg_hits_per_query = hits_logged / event_count if event_count else 0.0
    avg_top_score = sum(top_scores) / len(top_scores) if top_scores else 0.0
    volume = min(1.0, event_count / 4.0)
    diversity = min(1.0, len(distinct_queries) / 4.0)
    source_reach = min(1.0, len(source_mix) / 4.0)
    recency = 0.0
    if latest_access is not None:
        days_since = max(0.0, (datetime.now() - latest_access).total_seconds() / 86400.0)
        recency = max(0.0, 1.0 - min(days_since, float(days)) / float(days))

    return {
        "events_total": len(all_records),
        f"events_last_{days}_days": event_count,
        f"distinct_queries_last_{days}_days": len(distinct_queries),
        f"zero_hit_queries_last_{days}_days": zero_hit_queries,
        f"hit_rate_last_{days}_days": round(hit_rate, 4),
        f"avg_hits_per_query_last_{days}_days": round(avg_hits_per_query, 2),
        f"avg_top_score_last_{days}_days": round(avg_top_score, 4),
        f"unique_hit_paths_last_{days}_days": len(hit_paths),
        f"source_types_touched_last_{days}_days": len(source_mix),
        f"source_mix_last_{days}_days": dict(sorted(source_mix.items())),
        f"active_days_last_{days}_days": len(active_days),
        "last_access_at": latest_access.isoformat(timespec="seconds") if latest_access else None,
        f"top_hit_paths_last_{days}_days": [
            {"path": path, "hits": count}
            for path, count in hit_paths.most_common(5)
        ],
        "adoption_score": round(((volume + diversity + hit_rate + source_reach + recency) / 5.0) * 100.0, 2),
    }


def parse_memory_entries() -> list[MemoryEntry]:
    if not MEMORY_FILE.exists():
        return []
    entries: list[MemoryEntry] = []
    for line_no, raw_line in enumerate(MEMORY_FILE.read_text(encoding="utf-8").splitlines(), start=1):
        match = MEM_ENTRY_RE.match(raw_line)
        if not match:
            continue
        entry_date = None
        if match.group("entry_date"):
            try:
                entry_date = date.fromisoformat(match.group("entry_date"))
            except ValueError:
                entry_date = None
        entries.append(
            MemoryEntry(
                mem_id=match.group("mem_id"),
                entry_date=entry_date,
                text=match.group("text").strip(),
                line_no=line_no,
            )
        )
    return entries


def marker_kind(text: str) -> str:
    if "⚠" in text and "PERMANENT" in text:
        return "permanent"
    if "📌" in text and "PIN" in text:
        return "pin"
    if "🔥" in text and "HIGH" in text:
        return "high"
    return "normal"


def compute_importance(days_since_reference: int, reference_count: int, marker: str) -> float:
    if marker == "permanent":
        return 1.0
    if marker == "pin":
        return 1.0

    base_weight = 6.0 if marker == "high" else 4.0
    recency_decay = max(0.15, 1.0 - (days_since_reference / 180.0))
    reference_boost = min(2.0, 1.0 + math.log10(reference_count + 1))
    return round(min(1.0, (base_weight * recency_decay * reference_boost) / 8.0), 4)


def recent_access_counts(days: int = 180) -> dict[str, int]:
    cutoff = datetime.now() - timedelta(days=days)
    counts: dict[str, int] = {}
    for record in read_jsonl(ACCESS_LOG):
        ts = str(record.get("timestamp", ""))
        try:
            timestamp = datetime.fromisoformat(ts)
        except ValueError:
            continue
        if timestamp < cutoff:
            continue
        for hit in record.get("hits", []):
            if not isinstance(hit, dict):
                continue
            key = f"{hit.get('path','')}::{hit.get('fingerprint','')}"
            counts[key] = counts.get(key, 0) + 1
    return counts


def benchmark_queries() -> list[str]:
    return [
        "uv instead of pip",
        "session closing checklist",
        "NotebookLM CDP auth",
        "working memory scratchpad",
        "wiki overview requirement",
    ]

