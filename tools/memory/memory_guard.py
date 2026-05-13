#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""
memory_guard.py - evaluate memory health thresholds and unfinished session artifacts.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from memory_common import REVIEWS_DIR, append_jsonl, read_jsonl, write_json

STATUS_ORDER = {"ok": 0, "warn": 1, "degraded": 2, "blocked": 3}
HISTORY_PATH = REVIEWS_DIR / "memory-guard-history.jsonl"


def worsen(current: str, new: str) -> str:
    return new if STATUS_ORDER[new] > STATUS_ORDER[current] else current


def load_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _session_id_from_root(session_root: Path | None) -> str | None:
    if not session_root:
        return None
    return session_root.name


def find_unfinished_sessions(session_state_base: Path, current_session_root: Path | None) -> list[dict[str, object]]:
    unfinished: list[dict[str, object]] = []
    if not session_state_base.exists():
        return unfinished

    current_resolved = current_session_root.resolve() if current_session_root and current_session_root.exists() else None
    for session_root in sorted(path for path in session_state_base.iterdir() if path.is_dir()):
        if current_resolved and session_root.resolve() == current_resolved:
            continue

        scratchpad = session_root / "files" / "memory-scratchpad.md"
        candidates = session_root / "files" / "memory-candidates.json"
        if not scratchpad.exists():
            continue

        reason = None
        if not candidates.exists():
            reason = "scratchpad-exists-without-candidates"
        elif scratchpad.stat().st_mtime > candidates.stat().st_mtime:
            reason = "scratchpad-newer-than-candidates"

        if reason:
            unfinished.append(
                {
                    "session_root": str(session_root),
                    "reason": reason,
                    "scratchpad_modified": datetime.fromtimestamp(scratchpad.stat().st_mtime).isoformat(timespec="seconds"),
                    "candidates_modified": datetime.fromtimestamp(candidates.stat().st_mtime).isoformat(timespec="seconds")
                    if candidates.exists()
                    else None,
                }
            )
    return unfinished


def find_unresolved_lifecycle_sessions(
    history_records: list[dict[str, object]],
    current_session_root: Path | None,
) -> list[dict[str, object]]:
    current_session_id = _session_id_from_root(current_session_root)
    latest_per_session: dict[str, dict[str, object]] = {}

    for record in history_records:
        event_type = str(record.get("event_type") or "guard_eval")
        if event_type == "guard_eval":
            continue
        session_id = str(record.get("session_id") or "").strip()
        if not session_id or session_id == current_session_id:
            continue
        latest_per_session[session_id] = record

    unresolved: list[dict[str, object]] = []
    for session_id, record in latest_per_session.items():
        if bool(record.get("safe_handover", False)):
            continue
        unresolved.append(
            {
                "session_id": session_id,
                "session_root": record.get("session_root"),
                "event_type": record.get("event_type"),
                "timestamp": record.get("timestamp"),
                "note": record.get("note"),
            }
        )

    unresolved.sort(key=lambda item: str(item.get("timestamp", "")))
    return unresolved


def evaluate_guard(
    qa_payload: dict[str, object],
    review_payload: dict[str, object],
    unfinished_sessions: list[dict[str, object]],
    unresolved_lifecycle_sessions: list[dict[str, object]],
) -> tuple[str, list[str], list[str]]:
    status = "ok"
    reasons: list[str] = []
    actions: list[str] = []

    if not qa_payload:
        return (
            "degraded",
            ["memory-qa-missing"],
            [
                "Run `uv run tools/memory/memory_qa.py` before relying on durable memory state.",
                "Rebuild memory health artifacts, then re-check guard status.",
            ],
        )

    health_score = float(qa_payload.get("health_score", 0.0))
    scores = qa_payload.get("scores", {})
    review = qa_payload.get("review", {})

    freshness = float(scores.get("freshness", 0.0))
    coverage = float(scores.get("coverage", 0.0))
    coherence = float(scores.get("coherence", 0.0))
    reachability = float(scores.get("reachability", 0.0))
    needs_review = int(review.get("needs_review", 0))
    contradictions = int(review.get("contradictions", 0))

    if health_score < 70:
        status = worsen(status, "blocked")
        reasons.append("health-score-below-70")
        actions.append("Stop durable memory updates until QA recovers above 70.")
    elif health_score < 80:
        status = worsen(status, "degraded")
        reasons.append("health-score-below-80")
        actions.append("Reduce memory writes and inspect review backlog before continuing.")
    elif health_score < 90:
        status = worsen(status, "warn")
        reasons.append("health-score-below-90")

    if freshness < 0.5:
        status = worsen(status, "degraded")
        reasons.append("freshness-below-0.5")
        actions.append("Refresh retrieval targets and promote missing recent learnings.")
    elif freshness < 0.7:
        status = worsen(status, "warn")
        reasons.append("freshness-below-0.7")

    if coverage < 0.75 or coherence < 0.8 or reachability < 0.75:
        status = worsen(status, "degraded")
        reasons.append("core-memory-scores-degraded")
        actions.append("Run retrieval, review, and wiki checks before further memory promotion.")
    elif coverage < 0.9 or coherence < 0.95 or reachability < 0.9:
        status = worsen(status, "warn")
        reasons.append("core-memory-scores-warning")

    if contradictions >= 3:
        status = worsen(status, "blocked")
        reasons.append("review-contradictions-3-plus")
        actions.append("Resolve contradictory memory candidates before any further durable writes.")
    elif contradictions > 0:
        status = worsen(status, "warn")
        reasons.append("review-contradictions-present")

    if needs_review >= 6:
        status = worsen(status, "degraded")
        reasons.append("review-backlog-6-plus")
        actions.append("Clear review backlog before trusting autonomous memory promotion.")
    elif needs_review >= 3:
        status = worsen(status, "warn")
        reasons.append("review-backlog-3-plus")

    if unfinished_sessions:
        status = worsen(status, "warn")
        reasons.append("unfinished-session-artifacts")
        actions.append("Recover unfinished scratchpads or candidate files from prior crashed sessions.")

    if unresolved_lifecycle_sessions:
        status = worsen(status, "warn")
        reasons.append("unresolved-lifecycle-sessions")
        actions.append("Inspect lifecycle history for sessions that started but never reached a safe handover event.")

    if not actions:
        actions.append("Memory guard is healthy. Proceed with normal retrieval → work → review → persist flow.")

    return status, reasons, actions


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate memory guard thresholds and crash-recovery signals.")
    parser.add_argument("--session-state-base", help="Optional session-state base directory to scan")
    parser.add_argument("--current-session-root", help="Optional current session root to exclude from unfinished scan")
    parser.add_argument("--session-id", help="Optional session id for guard history entry")
    parser.add_argument("--json-out", help="Optional JSON output path")
    parser.add_argument("--markdown-out", help="Optional Markdown output path")
    args = parser.parse_args()

    qa_path = REVIEWS_DIR / "memory-qa.json"
    review_path = REVIEWS_DIR / "latest-memory-review.json"
    qa_payload = load_json(qa_path)
    review_payload = load_json(review_path)

    session_state_base = Path(args.session_state_base) if args.session_state_base else Path.home() / ".copilot" / "session-state"
    current_session_root = Path(args.current_session_root) if args.current_session_root else None
    unfinished = find_unfinished_sessions(session_state_base, current_session_root)
    history_records = read_jsonl(HISTORY_PATH)
    unresolved_lifecycle_sessions = find_unresolved_lifecycle_sessions(history_records, current_session_root)

    status, reasons, actions = evaluate_guard(qa_payload, review_payload, unfinished, unresolved_lifecycle_sessions)
    session_id = args.session_id or _session_id_from_root(current_session_root)
    payload = {
        "created": datetime.now().isoformat(timespec="seconds"),
        "status": status,
        "reasons": reasons,
        "actions": actions,
        "unfinished_sessions": unfinished,
        "unresolved_lifecycle_sessions": unresolved_lifecycle_sessions,
        "health_score": qa_payload.get("health_score"),
        "review": qa_payload.get("review", {}),
        "scores": qa_payload.get("scores", {}),
    }

    json_out = Path(args.json_out) if args.json_out else REVIEWS_DIR / "memory-guard.json"
    markdown_out = Path(args.markdown_out) if args.markdown_out else REVIEWS_DIR / "memory-guard.md"
    write_json(json_out, payload)

    lines = [
        "---",
        f"created: {payload['created']}",
        "kind: memory-guard",
        "---",
        "",
        "# Memory guard report",
        "",
        f"- **Status:** {status}",
        f"- **Health score:** {payload['health_score']}",
        f"- **Reasons:** {', '.join(reasons) if reasons else 'none'}",
        f"- **Unfinished sessions:** {len(unfinished)}",
        f"- **Unresolved lifecycle sessions:** {len(unresolved_lifecycle_sessions)}",
        "",
        "## Actions",
        "",
        *[f"- {action}" for action in actions],
        "",
    ]
    if unfinished:
        lines.extend(["## Unfinished session artifacts", ""])
        for item in unfinished:
            lines.append(f"- `{item['session_root']}` — {item['reason']}")
        lines.append("")
    if unresolved_lifecycle_sessions:
        lines.extend(["## Unresolved lifecycle sessions", ""])
        for item in unresolved_lifecycle_sessions:
            lines.append(
                f"- `{item['session_id']}` @ {item['timestamp']} — {item['event_type']} ({item.get('note') or 'no note'})"
            )
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    append_jsonl(
        HISTORY_PATH,
        {
            "timestamp": payload["created"],
            "event_type": "guard_eval",
            "session_id": session_id,
            "status": status,
            "health_score": payload["health_score"],
            "reasons": reasons,
            "unfinished_sessions": len(unfinished),
            "unresolved_lifecycle_sessions": len(unresolved_lifecycle_sessions),
        },
    )

    print(f"STATUS: {status}")
    print(f"JSON: {json_out}")
    print(f"MARKDOWN: {markdown_out}")
    print(f"UNFINISHED_SESSIONS: {len(unfinished)}")
    print(f"UNRESOLVED_LIFECYCLE_SESSIONS: {len(unresolved_lifecycle_sessions)}")
    print(f"REASONS: {len(reasons)}")


if __name__ == "__main__":
    main()
