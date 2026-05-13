#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""
agent_review.py - Repeatable review for delegated agent activity.
"""

from __future__ import annotations

import argparse
import json
from collections import OrderedDict
from datetime import datetime
from pathlib import Path
from typing import Any

TERMINAL_EVENTS = {"complete", "failed", "cancelled", "blocked", "absorbed"}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


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


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rows.append(json.loads(line))
    return rows


def trace_coverage_verdict(trace_path: Path) -> str:
    """Classify the trace file state so reviewers can distinguish real gaps.

    Returns:
        "no_trace_file"          — file does not exist (likely a coverage gap)
        "empty_trace"            — file exists but has no entries (unverifiable;
                                   use ``delegate.py session-expectation`` to
                                   make this auditable)
        "declared_no_delegation" — session_expectation event with
                                   expected_delegations=0 and no task events
                                   (explicitly declared delegation-free session)
        "has_events_no_spawn"    — file has task events but none are spawn events
                                   (coverage gap: activity without tracing)
        "has_delegation"         — at least one spawn event is present
    """
    if not trace_path.exists():
        return "no_trace_file"
    entries = read_jsonl(trace_path)
    if not entries:
        return "empty_trace"

    task_events = [e for e in entries if e.get("event") != "session_expectation"]
    session_events = [e for e in entries if e.get("event") == "session_expectation"]

    if not task_events:
        # Only session-level metadata — check for explicit zero declaration
        if session_events:
            raw = session_events[-1].get("metadata", {}).get("expected_delegations")
            try:
                expected = int(str(raw)) if raw is not None else -1
            except (ValueError, TypeError):
                expected = -1
            if expected == 0:
                return "declared_no_delegation"
        return "empty_trace"

    if any(e.get("event") == "spawn" for e in task_events):
        return "has_delegation"
    return "has_events_no_spawn"


def model_family(model: str | None) -> str | None:
    if not model:
        return None
    lowered = model.lower()
    if lowered.startswith("claude-"):
        return "claude"
    if lowered.startswith("gpt-"):
        return "gpt"
    if lowered.startswith("gemini-"):
        return "gemini"
    return "unknown"


def parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def build_review(trace_path: Path) -> dict[str, Any]:
    coverage_verdict = trace_coverage_verdict(trace_path)
    entries = read_jsonl(trace_path)

    # Separate session-level events (not task events) from task events.
    session_events = [e for e in entries if e.get("event") == "session_expectation"]
    task_entries = [e for e in entries if e.get("event") != "session_expectation"]

    # Resolve expected_delegations from the latest session_expectation event.
    expected_delegations: int | None = None
    if session_events:
        raw = session_events[-1].get("metadata", {}).get("expected_delegations")
        if raw is not None:
            try:
                expected_delegations = int(str(raw))
            except (ValueError, TypeError):
                pass

    by_task: dict[str, list[dict[str, Any]]] = OrderedDict()
    for entry in task_entries:
        by_task.setdefault(str(entry.get("task_id")), []).append(entry)

    total_tasks = len(by_task)
    completed = 0
    failed = 0
    blocked = 0
    open_tasks = 0
    stalled = 0
    dod_met = 0
    verification_tasks = 0
    cross_family_tasks = 0
    contract_v2_tasks = 0
    contract_complete_tasks = 0
    preflight_checked_tasks = 0
    verifiability_profiled_tasks = 0
    model_override_tasks = 0
    hypothesis_tasks = 0
    open_hypotheses = 0
    contradiction_tasks = 0
    failure_class_counts: dict[str, int] = OrderedDict()
    fallback_actions_used = 0
    completion_durations: list[float] = []

    open_task_details: list[dict[str, Any]] = []

    for task_id, task_entries in by_task.items():
        latest = task_entries[-1]
        latest_event = str(latest.get("event"))
        latest_metadata: dict[str, Any] = {}
        for item in task_entries:
            latest_metadata.update(item.get("metadata") or {})

        if latest_event == "complete":
            completed += 1
        elif latest_event == "failed":
            failed += 1
        elif latest_event == "blocked":
            blocked += 1
        elif latest_event == "stall":
            stalled += 1
            open_tasks += 1
        elif latest_event not in TERMINAL_EVENTS:
            open_tasks += 1

        if latest.get("dod_met") is True:
            dod_met += 1

        verification_need = latest_metadata.get("verification_need")
        verifier_model = latest_metadata.get("verifier_model")
        primary_model = latest_metadata.get("primary_model") or latest.get("model")
        if verification_need and verification_need != "none":
            verification_tasks += 1
            if model_family(primary_model) and model_family(verifier_model) and model_family(primary_model) != model_family(verifier_model):
                cross_family_tasks += 1
        contract_keys = ("goal", "dod", "verification_plan", "agent_role", "requested_tools")
        contract_signal_keys = contract_keys + ("complexity", "task_type", "risk", "verifiability")
        has_contract_signal = any(
            str(latest_metadata.get(key) or "").strip()
            for key in contract_signal_keys
        )
        if has_contract_signal:
            contract_v2_tasks += 1
            if all(str(latest_metadata.get(key) or "").strip() for key in contract_keys):
                contract_complete_tasks += 1
            if str(latest_metadata.get("preflight_status") or "").strip().lower() == "ok":
                preflight_checked_tasks += 1
            if str(latest_metadata.get("verifiability") or "").strip():
                verifiability_profiled_tasks += 1
            if str(latest_metadata.get("model_override_reason") or "").strip():
                model_override_tasks += 1

        task_open_hypotheses = int(str(latest_metadata.get("open_hypotheses", "0")) or "0")
        if task_open_hypotheses > 0:
            hypothesis_tasks += 1
            open_hypotheses += task_open_hypotheses
        if latest_metadata.get("contradiction") and str(latest_metadata.get("contradiction")).lower() not in {"", "none", "n/a"}:
            contradiction_tasks += 1
        failure_class = str(latest_metadata.get("failure_class") or "").strip()
        if failure_class:
            failure_class_counts[failure_class] = failure_class_counts.get(failure_class, 0) + 1
        fallback_action = str(latest_metadata.get("fallback_action") or "").strip().lower()
        if fallback_action and fallback_action not in {"", "none", "n/a"}:
            fallback_actions_used += 1

        spawn_entry = next((item for item in task_entries if item.get("event") == "spawn"), None)
        terminal_entry = next((item for item in reversed(task_entries) if item.get("event") in TERMINAL_EVENTS), None)
        spawn_at = parse_timestamp(spawn_entry.get("timestamp") if spawn_entry else None)
        done_at = parse_timestamp(terminal_entry.get("timestamp") if terminal_entry else None)
        if spawn_at and done_at:
            completion_durations.append((done_at - spawn_at).total_seconds())

        if latest_event not in TERMINAL_EVENTS:
            open_task_details.append(
                {
                    "task_id": task_id,
                    "latest_event": latest_event,
                    "agent_id": latest.get("agent_id"),
                    "model": latest.get("model") or latest_metadata.get("primary_model"),
                    "note": latest.get("note"),
                    "failure_class": failure_class or None,
                    "fallback_action": fallback_action or None,
                }
            )

    avg_duration = round(sum(completion_durations) / len(completion_durations), 2) if completion_durations else None

    spawn_count = sum(1 for task_entries_list in by_task.values() for e in task_entries_list if e.get("event") == "spawn")
    delegation_gap = max(0, expected_delegations - spawn_count) if expected_delegations is not None else 0

    reasons: list[str] = []
    actions: list[str] = []
    status = "ok"

    if coverage_verdict == "no_trace_file":
        status = "warn"
        reasons.append("no-trace-file")
        actions.append(
            "The agent trace file is missing. Run `delegate.py spawn` before the next task tool invocation "
            "and `delegate.py complete/failed` after it returns so delegation activity is captured."
        )
    if coverage_verdict == "has_events_no_spawn":
        status = "warn" if status == "ok" else status
        reasons.append("has-events-no-spawn")
        actions.append(
            "Trace has task events but no spawn events. This indicates a coverage gap: agent activity "
            "happened but was not logged via `delegate.py spawn`. Run `delegate.py spawn` before every "
            "task tool invocation."
        )
    if coverage_verdict == "empty_trace" and expected_delegations is None:
        # Cannot verify: trace exists but is empty and no expectation was declared.
        status = "warn" if status == "ok" else status
        reasons.append("unverified-empty-trace")
        actions.append(
            "Trace file exists but is empty and no session expectation was declared. "
            "Use `delegate.py session-expectation --expected-delegations 0` to explicitly confirm "
            "delegation-free sessions, or `delegate.py spawn` if delegation did occur."
        )
    if expected_delegations is not None and delegation_gap > 0:
        status = "warn" if status == "ok" else status
        reasons.append("delegation-below-expectation")
        actions.append(
            f"Expected {expected_delegations} delegation(s) but trace records {spawn_count} spawn(s). "
            f"Delegation gap: {delegation_gap}. Check if `delegate.py spawn` was called for all task "
            "tool invocations this session."
        )
    if open_tasks > 0:
        status = "warn"
        reasons.append("open-delegated-tasks-present")
        actions.append("Resolve or explicitly close open delegated tasks before ending the workstream.")
    if stalled > 0:
        status = "warn" if status == "ok" else status
        reasons.append("stalled-agents-detected")
        actions.append("Review stalled tasks and decide retry, escalation, or absorption.")
    if total_tasks > 0 and verification_tasks == 0:
        status = "warn" if status == "ok" else status
        reasons.append("verification-not-used")
        actions.append("Use verifier routing on medium/high-risk delegated tasks so quality impact can be measured.")
    if contract_v2_tasks > 0 and contract_complete_tasks < contract_v2_tasks:
        status = "warn" if status == "ok" else status
        reasons.append("routed-contract-incomplete")
        actions.append(
            "Routed delegated tasks should record goal, dod, verification_plan, agent_role, and requested_tools."
        )
    if contract_v2_tasks > 0 and preflight_checked_tasks < contract_v2_tasks:
        status = "warn" if status == "ok" else status
        reasons.append("preflight-not-used-on-routed-tasks")
        actions.append("Run persona-aware preflight for routed delegated tasks before spawning the task tool.")
    if contract_v2_tasks > 0 and verifiability_profiled_tasks < contract_v2_tasks:
        status = "warn" if status == "ok" else status
        reasons.append("verifiability-not-profiled")
        actions.append("Resolve verifiability metadata for routed tasks so autonomy and review depth are auditable.")
    if total_tasks > 0 and hypothesis_tasks == 0:
        status = "warn" if status == "ok" else status
        reasons.append("hypothesis-discipline-not-used")
        actions.append("Use the hypothesis ledger on medium/high-uncertainty analysis tasks so uncertainty is explicit.")
    if failed + blocked > 2:
        status = "degraded"
        reasons.append("agent-failures-high")
        actions.append("Review delegation prompts and routing rules; failure volume is too high.")
    if (failed + blocked) > 0 and not failure_class_counts:
        status = "warn" if status == "ok" else status
        reasons.append("failure-classes-not-used")
        actions.append("Classify failures explicitly so fallback and recovery quality can be reviewed.")

    if not actions:
        actions.append("Delegated agent activity is healthy. Continue using trace logging and verification selectively.")

    payload = {
        "created": now_iso(),
        "status": status,
        "trace_path": str(trace_path),
        "coverage_verdict": coverage_verdict,
        "summary": {
            "total_tasks": total_tasks,
            "completed_tasks": completed,
            "failed_tasks": failed,
            "blocked_tasks": blocked,
            "open_tasks": open_tasks,
            "stalled_tasks": stalled,
            "dod_met_tasks": dod_met,
            "expected_delegations": expected_delegations,
            "delegation_gap": delegation_gap,
            "verification_tasks": verification_tasks,
            "cross_family_verification_tasks": cross_family_tasks,
            "contract_v2_tasks": contract_v2_tasks,
            "contract_complete_tasks": contract_complete_tasks,
            "preflight_checked_tasks": preflight_checked_tasks,
            "verifiability_profiled_tasks": verifiability_profiled_tasks,
            "model_override_tasks": model_override_tasks,
            "hypothesis_tasks": hypothesis_tasks,
            "open_hypotheses": open_hypotheses,
            "contradiction_tasks": contradiction_tasks,
            "failure_class_counts": failure_class_counts,
            "fallback_actions_used": fallback_actions_used,
            "average_completion_seconds": avg_duration,
        },
        "open_tasks": open_task_details,
        "reasons": reasons,
        "actions": actions,
    }
    return payload


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "---",
        f"created: {payload['created']}",
        "kind: agent-performance-review",
        "---",
        "",
        "# Agent performance review",
        "",
        f"- **Status:** {payload['status']}",
        f"- **Coverage verdict:** {payload['coverage_verdict']}",
        f"- **Trace path:** `{payload['trace_path']}`",
        "",
        "## Summary",
        "",
        f"- **Total tasks:** {summary['total_tasks']}",
        f"- **Completed:** {summary['completed_tasks']}",
        f"- **Failed:** {summary['failed_tasks']}",
        f"- **Blocked:** {summary['blocked_tasks']}",
        f"- **Open:** {summary['open_tasks']}",
        f"- **Stalled:** {summary['stalled_tasks']}",
        f"- **DoD met:** {summary['dod_met_tasks']}",
        f"- **Expected delegations:** {summary['expected_delegations'] if summary['expected_delegations'] is not None else 'undeclared'}",
        f"- **Delegation gap:** {summary['delegation_gap']}",
        f"- **Verification tasks:** {summary['verification_tasks']}",
        f"- **Cross-family verification tasks:** {summary['cross_family_verification_tasks']}",
        f"- **Contract v2 tasks:** {summary['contract_v2_tasks']}",
        f"- **Contract-complete tasks:** {summary['contract_complete_tasks']}",
        f"- **Preflight-checked tasks:** {summary['preflight_checked_tasks']}",
        f"- **Verifiability-profiled tasks:** {summary['verifiability_profiled_tasks']}",
        f"- **Model override tasks:** {summary['model_override_tasks']}",
        f"- **Hypothesis tasks:** {summary['hypothesis_tasks']}",
        f"- **Open hypotheses:** {summary['open_hypotheses']}",
        f"- **Contradiction tasks:** {summary['contradiction_tasks']}",
        f"- **Fallback actions used:** {summary['fallback_actions_used']}",
        f"- **Average completion seconds:** {summary['average_completion_seconds'] if summary['average_completion_seconds'] is not None else 'n/a'}",
        "",
        "## Actions",
        "",
    ]
    lines.extend(f"- {action}" for action in payload["actions"])
    if summary["failure_class_counts"]:
        lines.extend(["", "## Failure classes", ""])
        for key, value in summary["failure_class_counts"].items():
            lines.append(f"- **{key}:** {value}")
    if payload["open_tasks"]:
        lines.extend(["", "## Open tasks", ""])
        for task in payload["open_tasks"]:
            lines.append(
                f"- **{task['task_id']}** — event `{task['latest_event']}`, model `{task['model']}`, failure `{task['failure_class'] or 'n/a'}`, fallback `{task['fallback_action'] or 'n/a'}`, note: {task['note'] or 'n/a'}"
            )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    vault = repo_root()
    review_dir = vault / "memory" / "reviews"
    parser = argparse.ArgumentParser(description="Review delegated agent activity and verification usage.")
    parser.add_argument("--trace-path", type=Path, default=vault / ".agent-trace.jsonl")
    parser.add_argument("--json-out", type=Path, default=review_dir / "agent-performance-review.json")
    parser.add_argument("--markdown-out", type=Path, default=review_dir / "agent-performance-review.md")
    parser.add_argument("--history-out", type=Path, default=review_dir / "agent-performance-history.jsonl")
    args = parser.parse_args()

    payload = build_review(args.trace_path)
    write_json(args.json_out, payload)
    atomic_write(args.markdown_out, render_markdown(payload))
    append_jsonl(
        args.history_out,
        {
            "timestamp": payload["created"],
            "status": payload["status"],
            **payload["summary"],
            "reasons": payload["reasons"],
        },
    )

    print(f"STATUS: {payload['status']}")
    print(f"JSON: {args.json_out}")
    print(f"MARKDOWN: {args.markdown_out}")
    print(f"TOTAL_TASKS: {payload['summary']['total_tasks']}")
    print(f"OPEN_TASKS: {payload['summary']['open_tasks']}")
    print(f"VERIFICATION_TASKS: {payload['summary']['verification_tasks']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
