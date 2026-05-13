#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""
cao_helper.py - Higher-level routed delegation helper for James.

Prepares routed task-tool metadata, renders a paste-ready prompt block, and can
log the routed spawn through delegate.py without manually assembling every flag.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_TOOLS_AGENTS = Path(__file__).resolve().parent
sys.path.insert(0, str(_TOOLS_AGENTS))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "routing"))

from agent_trace import default_trace_path  # noqa: E402
from delegate import VALID_AGENT_TYPES, command_spawn, resolve_routed_contract  # noqa: E402

ROLE_LABELS = {
    "analyst": "Analyst",
    "developer": "Developer",
    "researcher": "Researcher",
    "qa": "QA",
    "explore": "Explore",
}

COMPLEXITY_TIMEOUT_HINTS = {
    "trivial": "low complexity",
    "standard": "medium complexity",
    "complex": "medium-high complexity",
    "critical": "high complexity",
}


def _quote_ps(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _joined(values: list[str]) -> str:
    return ", ".join(values)


def _safe_console_text(value: str) -> str:
    encoding = sys.stdout.encoding or "utf-8"
    return value.encode(encoding, errors="replace").decode(encoding, errors="replace")


def _clean_text(value: str | None, fallback: str = "n/a") -> str:
    cleaned = (value or "").strip()
    return cleaned or fallback


def _load_skill_context(paths: list[Path]) -> str:
    blocks: list[str] = []
    for path in paths:
        content = path.read_text(encoding="utf-8").strip()
        blocks.append(f"[SKILL CONTEXT — {path.stem}]\n{content}")
    return "\n\n".join(blocks)


def _role_line(agent_role: str) -> str:
    label = ROLE_LABELS.get(agent_role, agent_role.replace("-", " ").title())
    return (
        f"You are the {label} leaf-agent for Gerhard's team. "
        "Do not spawn any sub-agents. Work directly in the workspace and return the result to James."
    )


def _build_trace_metadata(args: argparse.Namespace) -> list[str]:
    entries = list(args.metadata or [])
    derived = {
        "timeout_hint": args.timeout_hint,
        "plan_path": args.plan_path,
        "assumptions": args.assumptions,
        "validation_plan": args.validation_plan,
        "replan_rule": args.replan_rule,
        "handoff_state": args.handoff_state,
        "failure_class": args.failure_class,
        "fallback_action": args.fallback_action,
        "escalate_when": args.escalate_when,
    }
    for key, value in derived.items():
        cleaned = _clean_text(value, fallback="")
        if cleaned and cleaned.lower() not in {"none", "n/a"}:
            entries.append(f"{key}={cleaned}")
    has_hypothesis_context = any(
        _clean_text(value, fallback="")
        for value in (args.hypothesis, args.evidence, args.contradiction, args.next_test)
    ) or args.open_hypotheses is not None
    if has_hypothesis_context:
        hypothesis_fields = {
            "hypothesis": args.hypothesis,
            "confidence": args.confidence,
            "evidence": args.evidence,
            "contradiction": args.contradiction,
            "next_test": args.next_test,
        }
        for key, value in hypothesis_fields.items():
            cleaned = _clean_text(value, fallback="")
            if cleaned and cleaned.lower() not in {"none", "n/a"}:
                entries.append(f"{key}={cleaned}")
    if args.open_hypotheses is not None:
        entries.append(f"open_hypotheses={args.open_hypotheses}")
    if args.task_agent_type:
        entries.append(f"selected_agent_type={args.task_agent_type}")
    return entries


def _build_prompt_block(args: argparse.Namespace, resolved: dict[str, Any], skill_context: str) -> str:
    routing = resolved["routing"]
    profile = resolved["profile"]
    lines = [
        "[ROLE]",
        _role_line(args.agent_role),
        "",
        "[TASK METADATA]",
        f"- task_id: {args.task_id}",
        f"- goal: {args.goal}",
        f"- dod: {args.dod}",
        f"- verification_plan: {args.verification_plan}",
        f"- agent_role: {args.agent_role}",
        f"- requested_tools: {_joined(args.requested_tools)}",
        f"- timeout_hint: {args.timeout_hint}",
        f"- skill_context: {'injected below' if skill_context else 'n/a'}",
        "- escalation_path: return to James",
        f"- model_override: {args.model_override or 'null'}",
        "",
        "[ROUTING METADATA]",
        f"- complexity: {args.complexity}",
        f"- task_type: {args.task_type}",
        f"- risk: {args.risk}",
        f"- cost_profile: {args.cost_profile}",
        f"- verifiability: {profile['verifiability']}",
        f"- autonomy_level: {profile['autonomy_level']}",
        f"- primary_model: {resolved['selected_model']}",
        f"- verifier_model: {routing['verifier_model'] or 'none'}",
        f"- verification_need: {routing['verification_need']}",
        "",
        "[PLAN STATE]",
        f"- plan_path: {_clean_text(args.plan_path)}",
        f"- assumptions: {_clean_text(args.assumptions)}",
        f"- validation_plan: {_clean_text(args.validation_plan)}",
        f"- replan_rule: {_clean_text(args.replan_rule)}",
        f"- handoff_state: {_clean_text(args.handoff_state)}",
        "",
        "[HYPOTHESIS LEDGER]",
        f"- hypothesis: {_clean_text(args.hypothesis)}",
        f"- confidence: {_clean_text(args.confidence, 'uncertain')}",
        f"- evidence: {_clean_text(args.evidence)}",
        f"- contradiction: {_clean_text(args.contradiction)}",
        f"- next_test: {_clean_text(args.next_test)}",
        "",
        "[FAILURE STATE]",
        f"- failure_class: {_clean_text(args.failure_class, 'none')}",
        f"- fallback_action: {_clean_text(args.fallback_action)}",
        f"- escalate_when: {_clean_text(args.escalate_when)}",
    ]
    if skill_context:
        lines.extend(["", skill_context])
    if args.task_body:
        lines.extend(["", "[TASK]", args.task_body.strip()])
    return "\n".join(lines)


def _build_delegate_spawn_command(
    args: argparse.Namespace,
    resolved: dict[str, Any],
    trace_metadata: list[str],
) -> str:
    repo_root = Path(__file__).resolve().parents[2]
    delegate_script = repo_root / "tools" / "agents" / "delegate.py"
    selected_agent_type = args.task_agent_type or str(resolved["routing"]["preferred_agent_type"])
    tokens = [
        "&",
        _quote_ps(r"uv"),
        "run",
        _quote_ps(str(delegate_script)),
        "spawn",
        "--task-id",
        _quote_ps(args.task_id),
        "--agent-type",
        _quote_ps(selected_agent_type),
        "--model",
        _quote_ps(str(resolved["selected_model"])),
        "--goal",
        _quote_ps(args.goal),
        "--dod-text",
        _quote_ps(args.dod),
        "--verification-plan",
        _quote_ps(args.verification_plan),
        "--agent-role",
        _quote_ps(args.agent_role),
        "--requested-tools",
    ]
    tokens.extend(_quote_ps(tool) for tool in args.requested_tools)
    tokens.extend(
        [
            "--complexity",
            _quote_ps(args.complexity),
            "--task-type",
            _quote_ps(args.task_type),
            "--risk",
            _quote_ps(args.risk),
            "--cost-profile",
            _quote_ps(args.cost_profile),
        ]
    )
    if args.note:
        tokens.extend(["--note", _quote_ps(args.note)])
    if args.agent_id:
        tokens.extend(["--agent-id", _quote_ps(args.agent_id)])
    if args.agent_name:
        tokens.extend(["--agent-name", _quote_ps(args.agent_name)])
    if args.trace_path:
        tokens.extend(["--trace-path", _quote_ps(str(args.trace_path))])
    if args.model_override:
        tokens.extend(["--model-override-reason", _quote_ps(args.model_override_reason or "")])
    for entry in trace_metadata:
        tokens.extend(["--metadata", _quote_ps(entry)])
    return " ".join(tokens)


def _resolve_bundle(args: argparse.Namespace) -> dict[str, Any]:
    skill_context = _load_skill_context(args.skill_context_file)
    resolved = resolve_routed_contract(
        goal=args.goal,
        dod_text=args.dod,
        verification_plan=args.verification_plan,
        agent_role=args.agent_role,
        requested_tools=args.requested_tools,
        complexity=args.complexity,
        task_type=args.task_type,
        risk=args.risk,
        cost_profile=args.cost_profile,
        model=args.model_override,
        model_override_reason=args.model_override_reason,
        permissions_config=args.permissions_config,
        routing_config=args.routing_config,
        verifiability_config=args.verifiability_config,
    )
    trace_metadata = _build_trace_metadata(args)
    preflight = resolved["preflight"]
    payload = {
        "task_id": args.task_id,
        "recommended_agent_type": resolved["routing"]["preferred_agent_type"],
        "selected_agent_type": args.task_agent_type or str(resolved["routing"]["preferred_agent_type"]),
        "recommended_primary_model": resolved["routing"]["primary_model"],
        "selected_model": resolved["selected_model"],
        "spawn_ready": resolved["spawn_ready"],
        "blocking_errors": resolved["blocking_errors"],
        "preflight": {
            "status": "ok" if int(preflight["exit_code"]) == 0 else "denied",
            "agent_label": preflight["agent_label"],
            "allowed": preflight["allowed"],
            "denied": preflight["denied"],
            "notes": preflight["notes"],
        },
        "routing": {
            "complexity": resolved["routing"]["complexity"],
            "task_type": resolved["routing"]["task_type"],
            "risk": resolved["routing"]["risk"],
            "cost_profile": resolved["routing"]["cost_profile"],
            "primary_model": resolved["routing"]["primary_model"],
            "verifier_model": resolved["routing"]["verifier_model"],
            "verification_need": resolved["routing"]["verification_need"],
            "warnings": resolved["routing"]["warnings"],
        },
        "verifiability_profile": {
            "verifiability": resolved["profile"]["verifiability"],
            "autonomy_level": resolved["profile"]["autonomy_level"],
            "required_contract_fields": resolved["profile"]["required_contract_fields"],
            "required_review_signals": resolved["profile"]["required_review_signals"],
            "rationale": resolved["profile"]["rationale"],
        },
        "trace_metadata": trace_metadata,
        "delegate_spawn_command": _build_delegate_spawn_command(args, resolved, trace_metadata),
        "task_prompt_block": _build_prompt_block(args, resolved, skill_context),
    }
    return payload


def command_prepare(args: argparse.Namespace) -> int:
    payload = _resolve_bundle(args)
    if args.json:
        print(json.dumps(payload, ensure_ascii=True))
    else:
        print(f"RECOMMENDED_AGENT_TYPE: {payload['recommended_agent_type']}")
        print(f"SELECTED_AGENT_TYPE: {payload['selected_agent_type']}")
        print(f"SELECTED_MODEL: {payload['selected_model']}")
        print(f"VERIFIER_MODEL: {payload['routing']['verifier_model'] or 'none'}")
        print(f"VERIFICATION_NEED: {payload['routing']['verification_need']}")
        print(f"PREFLIGHT: {payload['preflight']['status']}")
        if payload["blocking_errors"]:
            print(f"BLOCKING_ERRORS: {json.dumps(payload['blocking_errors'], ensure_ascii=True)}")
        print(f"DELEGATE_COMMAND: {payload['delegate_spawn_command']}")
        print("\n[TASK PROMPT BLOCK]\n")
        print(_safe_console_text(payload["task_prompt_block"]))
    return 0 if payload["spawn_ready"] else 1


def command_spawn_helper(args: argparse.Namespace) -> int:
    payload = _resolve_bundle(args)
    if not payload["spawn_ready"]:
        if args.json:
            print(json.dumps(payload, ensure_ascii=True))
        else:
            print(f"PREFLIGHT: {payload['preflight']['status']}")
            print(f"BLOCKING_ERRORS: {json.dumps(payload['blocking_errors'], ensure_ascii=True)}")
        return 1

    delegate_args = argparse.Namespace(
        command="spawn",
        trace_path=args.trace_path,
        task_id=args.task_id,
        agent_id=args.agent_id,
        agent_name=args.agent_name,
        note=args.note,
        metadata=payload["trace_metadata"],
        agent_type=payload["selected_agent_type"],
        model=payload["selected_model"],
        goal=args.goal,
        dod_text=args.dod,
        verification_plan=args.verification_plan,
        agent_role=args.agent_role,
        requested_tools=args.requested_tools,
        complexity=args.complexity,
        task_type=args.task_type,
        risk=args.risk,
        cost_profile=args.cost_profile,
        model_override_reason=args.model_override_reason,
        permissions_config=args.permissions_config,
        routing_config=args.routing_config,
        verifiability_config=args.verifiability_config,
    )
    exit_code = command_spawn(delegate_args)
    if exit_code != 0:
        return exit_code
    print(f"SELECTED_AGENT_TYPE: {payload['selected_agent_type']}")
    print(f"SELECTED_MODEL: {payload['selected_model']}")
    print("\n[TASK PROMPT BLOCK]\n")
    print(_safe_console_text(payload["task_prompt_block"]))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare or log routed delegation metadata for James.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_common(subparser: argparse.ArgumentParser) -> None:
        subparser.add_argument("--task-id", required=True, help="Unique kebab-case task identifier.")
        subparser.add_argument("--goal", required=True, help="One-sentence objective.")
        subparser.add_argument("--dod", required=True, help="Measurable definition of done.")
        subparser.add_argument("--verification-plan", required=True, help="How the result will be verified.")
        subparser.add_argument("--agent-role", required=True, help="Delegated persona (developer, analyst, researcher, qa, explore).")
        subparser.add_argument("--requested-tools", nargs="+", required=True, help="Expected tool names for policy preflight.")
        subparser.add_argument("--complexity", choices=["trivial", "standard", "complex", "critical"], required=True)
        subparser.add_argument("--task-type", choices=["lookup", "code", "analysis", "synthesis", "decision"], required=True)
        subparser.add_argument("--risk", choices=["low", "medium", "high"], required=True)
        subparser.add_argument("--cost-profile", choices=["budget", "normal", "unlimited"], default="normal")
        subparser.add_argument("--task-agent-type", choices=sorted(VALID_AGENT_TYPES), help="Optional override for the task-tool agent type.")
        subparser.add_argument("--model-override", help="Optional override for the recommended primary model.")
        subparser.add_argument("--model-override-reason", help="Reason for overriding the recommended primary model.")
        subparser.add_argument("--timeout-hint", help="Prompt timeout/runtime hint.")
        subparser.add_argument("--plan-path", help="Plan artifact path.")
        subparser.add_argument("--assumptions", help="Current assumptions or short pointer.")
        subparser.add_argument("--validation-plan", help="Validation summary or pointer.")
        subparser.add_argument("--replan-rule", help="Condition for replanning.")
        subparser.add_argument("--handoff-state", help="Current handoff summary.")
        subparser.add_argument("--hypothesis", help="Current working hypothesis.")
        subparser.add_argument("--confidence", help="Hypothesis confidence.")
        subparser.add_argument("--evidence", help="Best supporting evidence.")
        subparser.add_argument("--contradiction", help="Best contradiction or gap.")
        subparser.add_argument("--next-test", help="Most discriminating next test.")
        subparser.add_argument("--open-hypotheses", type=int, help="Open hypothesis count to carry into trace metadata.")
        subparser.add_argument("--failure-class", help="Failure class or none.")
        subparser.add_argument("--fallback-action", help="Fallback action or n/a.")
        subparser.add_argument("--escalate-when", help="Escalation trigger or n/a.")
        subparser.add_argument("--task-body", help="Optional full task description for the prompt block.")
        subparser.add_argument(
            "--skill-context-file",
            action="append",
            type=Path,
            default=[],
            help="Optional SKILL.md path to inject into the prompt block. May be repeated.",
        )
        subparser.add_argument("--metadata", action="append", default=[], help="Additional trace metadata as key=value.")
        subparser.add_argument("--json", action="store_true", help="Print JSON output.")
        subparser.add_argument("--permissions-config", type=Path, default=None, help="Optional path to agent-permissions.yaml.")
        subparser.add_argument("--routing-config", type=Path, default=None, help="Optional path to model-routing.yaml.")
        subparser.add_argument("--verifiability-config", type=Path, default=None, help="Optional path to verifiability-map.yaml.")

    prepare_p = subparsers.add_parser("prepare", help="Resolve routed delegation metadata and print a prompt bundle.")
    add_common(prepare_p)

    spawn_p = subparsers.add_parser("spawn", help="Resolve routed metadata and log the spawn through delegate.py.")
    add_common(spawn_p)
    spawn_p.add_argument("--trace-path", type=Path, default=default_trace_path(), help="Path to the JSONL trace file.")
    spawn_p.add_argument("--agent-id", help="Identifier for the spawned agent instance.")
    spawn_p.add_argument("--agent-name", help="Human-readable agent name.")
    spawn_p.add_argument("--note", help="Free-text note for the spawn event.")
    return parser


def _apply_defaults(args: argparse.Namespace) -> argparse.Namespace:
    if not args.timeout_hint:
        args.timeout_hint = COMPLEXITY_TIMEOUT_HINTS[args.complexity]
    if not getattr(args, "confidence", None):
        args.confidence = "uncertain"
    if not getattr(args, "failure_class", None):
        args.failure_class = "none"
    if not getattr(args, "fallback_action", None):
        args.fallback_action = "n/a"
    if not getattr(args, "escalate_when", None):
        args.escalate_when = "n/a"
    if args.model_override and not args.model_override_reason:
        args.model_override_reason = "manual CAO override"
    if not hasattr(args, "trace_path"):
        args.trace_path = default_trace_path()
    if not hasattr(args, "agent_id"):
        args.agent_id = None
    if not hasattr(args, "agent_name"):
        args.agent_name = None
    if not hasattr(args, "note"):
        args.note = None
    return args


def main() -> int:
    args = _apply_defaults(build_parser().parse_args())
    if args.command == "prepare":
        return command_prepare(args)
    return command_spawn_helper(args)


if __name__ == "__main__":
    raise SystemExit(main())
