#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""
delegate.py - Protocol wrapper for James-managed sub-agent delegation.

Wraps the spawn → work → complete lifecycle so delegation telemetry is
written by default rather than by exception.  Because the external `task`
tool cannot be intercepted programmatically, this wrapper relies on James
calling it at the two natural boundaries of every delegation:

  1. BEFORE invoking the task tool:
       uv run tools/agents/delegate.py spawn \\
           --task-id  research-brief-001 \\
           --agent-type explore \\
           --model claude-haiku-4.5 \\
           --note "find agent orchestration patterns"

  2. AFTER the task tool returns (pick the right terminal event):
       uv run tools/agents/delegate.py complete --task-id research-brief-001 --dod-met true
       uv run tools/agents/delegate.py failed   --task-id research-brief-001 --note "timeout"
       uv run tools/agents/delegate.py blocked  --task-id research-brief-001 --note "missing creds"

  Declare expected delegation count at session start (creates a coverage denominator):
       uv run tools/agents/delegate.py session-expectation --expected-delegations 3

  Audit (detect unclosed delegation events — run before session close):
       uv run tools/agents/delegate.py audit

The wrapper writes to the same .agent-trace.jsonl file used by agent_trace.py
and agent_review.py so all tooling reads from one trace source.

Mandatory spawn fields
----------------------
--agent-type and --model are REQUIRED for `spawn`.  Omitting them causes
a validation error so that supervision routing is always auditable.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

# Reuse the single write path from agent_trace so there is no divergence.
_TOOLS_AGENTS = Path(__file__).resolve().parent
sys.path.insert(0, str(_TOOLS_AGENTS))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "routing"))

from agent_trace import (  # noqa: E402
    TERMINAL_EVENTS,
    TraceEntry,
    append_entry,
    default_trace_path,
    parse_metadata,
    read_entries,
    utc_now,
)
from preflight_guard import run_preflight  # noqa: E402

VALID_AGENT_TYPES = {"explore", "general-purpose", "code-review", "task"}
VALID_COMPLEXITIES = {"trivial", "standard", "complex", "critical"}
VALID_TASK_TYPES = {"lookup", "code", "analysis", "synthesis", "decision"}
VALID_RISKS = {"low", "medium", "high"}


def resolve_routed_contract(
    *,
    goal: str,
    dod_text: str,
    verification_plan: str,
    agent_role: str,
    requested_tools: list[str],
    complexity: str,
    task_type: str,
    risk: str,
    cost_profile: str = "normal",
    model: str | None = None,
    model_override_reason: str | None = None,
    permissions_config: Path | None = None,
    routing_config: Path | None = None,
    verifiability_config: Path | None = None,
) -> dict[str, Any]:
    """Resolve the routed delegation contract once for CLI and CAO helpers."""
    from model_router import route_task  # noqa: PLC0415
    from verifiability_profile import build_profile  # noqa: PLC0415

    preflight = run_preflight(
        agent_type=agent_role,
        requested_tools=requested_tools,
        config_path=permissions_config,
    )
    routing = route_task(
        complexity=complexity,
        task_type=task_type,
        risk=risk,
        cost_profile=cost_profile,
        config_path=routing_config,
    )
    profile = build_profile(
        task_type=task_type,
        complexity=complexity,
        risk=risk,
        config_path=verifiability_config,
    )
    selected_model = model or str(routing["primary_model"])
    blocking_errors: list[str] = []
    if int(preflight["exit_code"]) != 0:
        blocking_errors.append(f"routed delegation preflight failed for role '{agent_role}'")
    if selected_model != routing["primary_model"] and not model_override_reason:
        blocking_errors.append(
            "routed delegation uses a non-recommended primary model. "
            "Provide --model-override-reason so the deviation is auditable."
        )

    metadata = {
        "goal": goal,
        "dod": dod_text,
        "verification_plan": verification_plan,
        "agent_role": agent_role,
        "requested_tools": _format_csv(requested_tools),
        "complexity": complexity,
        "task_type": task_type,
        "risk": risk,
        "cost_profile": cost_profile,
        "preflight_status": "ok" if int(preflight["exit_code"]) == 0 else "denied",
        "preflight_allowed_tools": _format_csv(preflight["allowed"]),
        "preflight_denied_tools": _format_csv(preflight["denied"]),
        "verification_need": str(routing["verification_need"]),
        "verifier_model": str(routing["verifier_model"] or "none"),
        "primary_model": selected_model,
        "recommended_primary_model": str(routing["primary_model"]),
        "recommended_agent_type": str(routing["preferred_agent_type"]),
        "verifiability": str(profile["verifiability"]),
        "autonomy_level": str(profile["autonomy_level"]),
        "required_contract_fields": _format_csv(profile["required_contract_fields"]),
        "required_review_signals": _format_csv(profile["required_review_signals"]),
    }
    if model_override_reason:
        metadata["model_override_reason"] = model_override_reason

    return {
        "preflight": preflight,
        "routing": routing,
        "profile": profile,
        "selected_model": selected_model,
        "metadata": metadata,
        "blocking_errors": blocking_errors,
        "spawn_ready": not blocking_errors,
    }


def _open_delegations_from(task_entries: list[dict]) -> list[dict]:
    """Return entries for tasks that were spawned but have no terminal event yet."""
    spawned: set[str] = set()
    latest_by_task: dict[str, dict] = {}
    for entry in task_entries:
        tid = entry["task_id"]
        latest_by_task[tid] = entry
        if entry.get("event") == "spawn":
            spawned.add(tid)
    return [
        e for tid, e in latest_by_task.items()
        if tid in spawned and e.get("event") not in TERMINAL_EVENTS
    ]


def _coverage_gap_tasks(task_entries: list[dict]) -> list[dict]:
    """Return entries for tasks that have events but were never spawned.

    These are coverage gaps: activity was traced without a corresponding
    ``delegate.py spawn`` call.  The correct remediation is to ensure
    ``delegate.py spawn`` is called before every task tool invocation.
    """
    spawned: set[str] = set()
    latest_by_task: dict[str, dict] = {}
    for entry in task_entries:
        tid = entry["task_id"]
        latest_by_task[tid] = entry
        if entry.get("event") == "spawn":
            spawned.add(tid)
    return [e for tid, e in latest_by_task.items() if tid not in spawned]


def _validate_spawn(args: argparse.Namespace) -> list[str]:
    """Return validation errors for required spawn fields.

    Both ``--agent-type`` and ``--model`` are mandatory so that supervision
    routing is always auditable.  Returns a list of error strings (empty when
    valid).
    """
    errors: list[str] = []
    if not args.agent_type:
        errors.append("--agent-type is required for spawn (explore | general-purpose | code-review | task)")
    elif args.agent_type not in VALID_AGENT_TYPES:
        errors.append(
            f"--agent-type '{args.agent_type}' is not a recognised type "
            f"(valid: {', '.join(sorted(VALID_AGENT_TYPES))})"
        )
    if not args.model:
        errors.append("--model is required for spawn so model routing is auditable")
    routed_fields = [
        args.goal,
        args.dod_text,
        args.verification_plan,
        args.agent_role,
        args.requested_tools,
        args.complexity,
        args.task_type,
        args.risk,
        args.model_override_reason,
    ]
    routed_contract_requested = any(
        value not in (None, "", []) for value in routed_fields
    )
    routing_tuple = [args.complexity, args.task_type, args.risk]
    if any(value is not None for value in routing_tuple) and not all(value is not None for value in routing_tuple):
        errors.append("Provide --complexity, --task-type, and --risk together when using routed delegation.")
    if args.complexity and args.complexity not in VALID_COMPLEXITIES:
        errors.append(f"--complexity '{args.complexity}' is invalid")
    if args.task_type and args.task_type not in VALID_TASK_TYPES:
        errors.append(f"--task-type '{args.task_type}' is invalid")
    if args.risk and args.risk not in VALID_RISKS:
        errors.append(f"--risk '{args.risk}' is invalid")
    if routed_contract_requested:
        if not args.goal:
            errors.append("--goal is required for routed delegation so the task spec is traceable")
        if not args.dod_text:
            errors.append("--dod-text is required for routed delegation so completion can be reviewed")
        if not args.verification_plan:
            errors.append("--verification-plan is required for routed delegation")
        if not args.agent_role:
            errors.append("--agent-role is required for routed delegation preflight")
        if not args.requested_tools:
            errors.append("--requested-tools is required for routed delegation preflight")
    return errors


def _uses_routed_contract(args: argparse.Namespace) -> bool:
    return any(
        value not in (None, "", [])
        for value in (
            args.goal,
            args.dod_text,
            args.verification_plan,
            args.agent_role,
            args.requested_tools,
            args.complexity,
            args.task_type,
            args.risk,
            args.model_override_reason,
        )
    )


def _format_csv(values: list[str]) -> str:
    return ",".join(values)


def _open_delegations(trace_path: Path) -> list[dict]:
    """Return trace entries for tasks that have no terminal event yet."""
    entries = read_entries(trace_path)
    by_task: dict[str, dict] = {}
    for entry in entries:
        by_task[entry["task_id"]] = entry
    return [e for e in by_task.values() if e.get("event") not in TERMINAL_EVENTS]


def command_spawn(args: argparse.Namespace) -> int:
    errors = _validate_spawn(args)
    if errors:
        for err in errors:
            print(f"ERROR: {err}", file=sys.stderr)
        print(
            "HINT: provide all required fields so delegation can be audited "
            "(--agent-type, --model, --task-id)",
            file=sys.stderr,
        )
        return 2
    metadata = parse_metadata(args.metadata or [])
    if _uses_routed_contract(args):
        contract = resolve_routed_contract(
            goal=args.goal,
            dod_text=args.dod_text,
            verification_plan=args.verification_plan,
            agent_role=args.agent_role,
            requested_tools=args.requested_tools,
            complexity=args.complexity,
            task_type=args.task_type,
            risk=args.risk,
            cost_profile=args.cost_profile,
            model=args.model,
            model_override_reason=args.model_override_reason,
            permissions_config=args.permissions_config,
            routing_config=args.routing_config,
            verifiability_config=args.verifiability_config,
        )
        preflight = contract["preflight"]
        if int(preflight["exit_code"]) != 0:
            print(f"ERROR: routed delegation preflight failed for role '{args.agent_role}'", file=sys.stderr)
            print(f"ALLOWED: {', '.join(preflight['allowed']) or 'none'}", file=sys.stderr)
            print(f"DENIED: {', '.join(preflight['denied']) or 'none'}", file=sys.stderr)
            if preflight.get("notes"):
                print(f"POLICY NOTE: {preflight['notes']}", file=sys.stderr)
            print("ACTION: remove denied tools, change persona, or escalate to James.", file=sys.stderr)
            return 1
        if not contract["spawn_ready"]:
            print(
                "ERROR: routed delegation uses a non-recommended primary model. "
                "Provide --model-override-reason so the deviation is auditable.",
                file=sys.stderr,
            )
            return 2
        for key, value in contract["metadata"].items():
            metadata.setdefault(key, value)

    entry = TraceEntry(
        timestamp=utc_now(),
        event="spawn",
        task_id=args.task_id,
        agent_id=args.agent_id,
        agent_name=args.agent_name,
        agent_type=args.agent_type,
        model=args.model,
        status=None,
        dod_met=None,
        note=args.note,
        metadata=metadata,
    )
    append_entry(args.trace_path, entry)
    print(f"SPAWN: {args.task_id}")
    print(f"TRACE_PATH: {args.trace_path}")
    if _uses_routed_contract(args):
        print(f"PREFLIGHT: ok ({_format_csv(args.requested_tools)})")
        print(f"VERIFIABILITY: {metadata.get('verifiability')}")
        print(f"AUTONOMY_LEVEL: {metadata.get('autonomy_level')}")
        print(f"VERIFICATION_NEED: {metadata.get('verification_need')}")
    print("NEXT: invoke the task tool, then run `delegate.py complete --task-id <id>` when it returns")
    return 0


def command_session_expectation(args: argparse.Namespace) -> int:
    """Log an expected delegation count so the review has an explicit denominator.

    Writing this event at the start of a session lets ``agent_review.py``
    distinguish "no delegation was expected" from "delegation happened but the
    trace is missing".  Use ``--expected-delegations 0`` to explicitly declare
    a delegation-free session.
    """
    entry = TraceEntry(
        timestamp=utc_now(),
        event="session_expectation",
        task_id="__session__",
        agent_id=None,
        agent_name=None,
        agent_type=None,
        model=None,
        status=None,
        dod_met=None,
        note=args.note,
        metadata={"expected_delegations": str(args.expected_delegations)},
    )
    append_entry(args.trace_path, entry)
    print(f"SESSION_EXPECTATION: expected_delegations={args.expected_delegations}")
    print(f"TRACE_PATH: {args.trace_path}")
    print(
        "NOTE: run `delegate.py spawn` before each task tool call so the denominator is met"
        if args.expected_delegations > 0
        else "NOTE: session declared delegation-free; review will accept an empty trace as ok"
    )
    return 0


def command_terminal(args: argparse.Namespace, event: str) -> int:
    entry = TraceEntry(
        timestamp=utc_now(),
        event=event,
        task_id=args.task_id,
        agent_id=args.agent_id,
        agent_name=args.agent_name,
        agent_type=None,
        model=None,
        status=args.status,
        dod_met=args.dod_met,
        note=args.note,
        metadata=parse_metadata(args.metadata or []),
    )
    append_entry(args.trace_path, entry)
    print(f"LOGGED: {event}")
    print(f"TASK_ID: {args.task_id}")
    print(f"TRACE_PATH: {args.trace_path}")
    return 0


def command_audit(args: argparse.Namespace) -> int:
    """Check for unclosed delegation events and coverage gaps.  Exit 1 if any gap is found."""
    if not args.trace_path.exists():
        print("AUDIT: no_trace_file")
        print(f"TRACE_PATH: {args.trace_path}")
        print("ACTION: run `delegate.py spawn` before the next task tool invocation")
        return 1

    all_entries = read_entries(args.trace_path)
    task_entries = [e for e in all_entries if e.get("event") != "session_expectation"]
    session_events = [e for e in all_entries if e.get("event") == "session_expectation"]

    open_tasks = _open_delegations_from(task_entries)
    coverage_gaps = _coverage_gap_tasks(task_entries)

    # Compute expected vs actual delegation gap
    expected: int | None = None
    if session_events:
        raw = session_events[-1].get("metadata", {}).get("expected_delegations")
        if raw is not None:
            try:
                expected = int(str(raw))
            except (ValueError, TypeError):
                pass

    spawn_count = sum(1 for e in task_entries if e.get("event") == "spawn")
    gap = max(0, (expected or 0) - spawn_count) if expected is not None else 0

    exit_code = 0

    if coverage_gaps:
        print(f"AUDIT: warn — coverage_gap: {len(coverage_gaps)} task(s) have events but were never spawned")
        for task in coverage_gaps:
            print(
                f"  COVERAGE_GAP: {task['task_id']} | last_event={task['event']} | note={task.get('note')}"
            )
        print(
            "ACTION: ensure `delegate.py spawn` is called before every task tool invocation; "
            "activity was traced without spawn registration — delegation may have been missed"
        )
        exit_code = 1

    if open_tasks:
        print(f"AUDIT: warn — {len(open_tasks)} unclosed delegation(s)")
        for task in open_tasks:
            print(
                f"  OPEN: {task['task_id']} | event={task['event']} | note={task.get('note')}"
            )
        print("ACTION: close open tasks with `delegate.py complete --task-id <id>` or `delegate.py failed`")
        exit_code = 1

    if not coverage_gaps and not open_tasks:
        if gap > 0:
            print(f"AUDIT: warn — expected {expected} delegation(s) but only {spawn_count} spawn(s) logged")
            print(f"  DELEGATION_GAP: {gap}")
            print("ACTION: check if delegate.py spawn was called for all task tool invocations")
            exit_code = 1
        elif not task_entries and expected is None:
            print("AUDIT: ok — no task events; use `session-expectation` to make this auditable")
        else:
            print("AUDIT: ok")

    if expected is not None:
        print(f"  EXPECTED_DELEGATIONS: {expected}")
        print(f"  SPAWN_COUNT: {spawn_count}")
        print(f"  DELEGATION_GAP: {gap}")

    print(f"TRACE_PATH: {args.trace_path}")
    return exit_code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Protocol wrapper for James-managed sub-agent delegation.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    def _add_common(sub: argparse.ArgumentParser, task_required: bool = True) -> None:
        sub.add_argument(
            "--trace-path", type=Path, default=default_trace_path(),
            help="Path to the JSONL trace file (default: .agent-trace.jsonl in repo root).",
        )
        sub.add_argument("--task-id", required=task_required, help="Unique kebab-case task identifier.")
        sub.add_argument("--agent-id", help="Identifier for the spawned agent instance.")
        sub.add_argument("--agent-name", help="Human-readable agent name.")
        sub.add_argument("--note", help="Free-text note for this event.")
        sub.add_argument(
            "--metadata", action="append", default=[],
            help="Extra key=value pairs to include (e.g. verification_need=full-review).  May be repeated.",
        )

    # spawn — agent-type and model are enforced in command_spawn for clean error messages
    spawn_p = subparsers.add_parser("spawn", help="Log a spawn event before invoking the task tool.")
    _add_common(spawn_p)
    spawn_p.add_argument(
        "--agent-type",
        help="REQUIRED. Agent type: explore | general-purpose | code-review | task.",
    )
    spawn_p.add_argument(
        "--model",
        help="REQUIRED. Model identifier, e.g. claude-haiku-4.5.",
    )
    spawn_p.add_argument("--goal", help="One-sentence objective for routed delegation.")
    spawn_p.add_argument("--dod-text", help="Measurable definition of done for routed delegation.")
    spawn_p.add_argument("--verification-plan", help="How the delegated result will be verified.")
    spawn_p.add_argument("--agent-role", help="Delegated persona/role for policy preflight (e.g. developer).")
    spawn_p.add_argument(
        "--requested-tools",
        nargs="+",
        help="Tool names the delegated persona is expected to use (e.g. view powershell).",
    )
    spawn_p.add_argument("--complexity", help="Routing complexity: trivial | standard | complex | critical.")
    spawn_p.add_argument("--task-type", help="Routing task type: lookup | code | analysis | synthesis | decision.")
    spawn_p.add_argument("--risk", help="Routing risk: low | medium | high.")
    spawn_p.add_argument("--cost-profile", default="normal", help="Routing cost profile (default: normal).")
    spawn_p.add_argument(
        "--model-override-reason",
        help="Required when routed delegation intentionally uses a non-recommended primary model.",
    )
    spawn_p.add_argument(
        "--permissions-config",
        type=Path,
        default=None,
        help="Optional path to agent-permissions.yaml.",
    )
    spawn_p.add_argument(
        "--routing-config",
        type=Path,
        default=None,
        help="Optional path to model-routing.yaml.",
    )
    spawn_p.add_argument(
        "--verifiability-config",
        type=Path,
        default=None,
        help="Optional path to verifiability-map.yaml.",
    )

    # session-expectation — coverage denominator
    ses_p = subparsers.add_parser(
        "session-expectation",
        help="Declare the expected number of delegations for this session (creates a coverage denominator).",
    )
    ses_p.add_argument(
        "--trace-path", type=Path, default=default_trace_path(),
        help="Path to the JSONL trace file.",
    )
    ses_p.add_argument(
        "--expected-delegations", type=int, required=True,
        help="How many task tool invocations are expected this session. Use 0 to explicitly declare delegation-free.",
    )
    ses_p.add_argument("--note", help="Free-text note.")

    # terminal events
    for evt in ("complete", "failed", "blocked", "absorbed", "cancelled"):
        term_p = subparsers.add_parser(evt, help=f"Log a '{evt}' event after the task tool returns.")
        _add_common(term_p)
        term_p.add_argument("--status", help="Optional status string.")
        term_p.add_argument(
            "--dod-met", type=lambda v: v.lower() == "true",
            metavar="true|false", help="Whether the Definition of Done was met.",
        )

    # audit
    audit_p = subparsers.add_parser("audit", help="Check for unclosed delegation events and expectation gaps.")
    audit_p.add_argument(
        "--trace-path", type=Path, default=default_trace_path(),
        help="Path to the JSONL trace file.",
    )

    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "spawn":
        return command_spawn(args)
    if args.command == "session-expectation":
        return command_session_expectation(args)
    if args.command == "audit":
        return command_audit(args)
    return command_terminal(args, args.command)


if __name__ == "__main__":
    raise SystemExit(main())
