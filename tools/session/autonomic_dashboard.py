#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""
autonomic_dashboard.py - Aggregate the current operational health of the workspace.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


STATUS_ORDER = {"ok": 0, "warn": 1, "degraded": 2, "blocked": 3, "unknown": 4}
WIP_RE = re.compile(r"cc:WIP", re.IGNORECASE)
BLOCKED_RE = re.compile(r"blocked\s*\(", re.IGNORECASE)


@dataclass
class Signal:
    name: str
    status: str
    source: str
    details: dict[str, object]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(content, encoding="utf-8")
    temp.replace(path)


def load_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def find_uv() -> str:
    return shutil.which("uv") or r"uv"


def run_refresh_commands(root: Path) -> list[str]:
    uv = find_uv()
    commands = [
        [uv, "run", str(root / "tools" / "agents" / "agent_review.py")],
        [uv, "run", str(root / "tools" / "memory" / "memory_guard.py")],
        [uv, "run", "--python", "3.12", str(root / "tools" / "wiki" / "knowledge_refresh.py"), "--mode", "apply"],
        [uv, "run", str(root / "tools" / "agents" / "skill_candidates.py")],
    ]
    failures: list[str] = []
    for command in commands:
        result = subprocess.run(command, cwd=root, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            failures.append(f"{Path(command[-1]).name}: {(result.stderr or result.stdout).strip()}")
    return failures


def worst_status(values: list[str]) -> str:
    known = [value for value in values if value in STATUS_ORDER]
    if not known:
        return "unknown"
    return max(known, key=lambda item: STATUS_ORDER[item])


def parse_plan_state(root: Path) -> dict[str, object]:
    plans_dir = root / "plans"
    wip_items: list[dict[str, object]] = []
    blocked_items: list[dict[str, object]] = []
    for path in sorted(plans_dir.glob("*.md")):
        for idx, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            text = line.strip()
            if WIP_RE.search(text):
                wip_items.append({"file": str(path.relative_to(root)), "line": idx, "text": text})
            if BLOCKED_RE.search(text):
                blocked_items.append({"file": str(path.relative_to(root)), "line": idx, "text": text})
    status = "ok"
    if wip_items or blocked_items:
        status = "warn"
    if blocked_items:
        status = "degraded"
    return {
        "status": status,
        "wip_count": len(wip_items),
        "blocked_count": len(blocked_items),
        "wip_items": wip_items[:10],
        "blocked_items": blocked_items[:10],
    }


def parse_issue_opportunities(root: Path) -> dict[str, object]:
    path = root / "sources" / "agent-ecosystem" / "2026-04-25-opportunities.json"
    payload = load_json(path)
    opportunities = list(payload.get("opportunities") or [])
    counts_by_status: dict[str, int] = {}
    ready_to_create: list[dict[str, object]] = []
    for item in opportunities:
        status = str(item.get("status") or "unknown")
        counts_by_status[status] = counts_by_status.get(status, 0) + 1
        issue = item.get("issue") or {}
        if status in {"selected", "planned"} and not issue.get("url"):
            ready_to_create.append(
                {
                    "id": item.get("id"),
                    "title": issue.get("title") or item.get("title"),
                    "status": status,
                    "priority": item.get("priority"),
                }
            )
    status = "ok" if not ready_to_create else "warn"
    return {
        "status": status,
        "source": str(path.relative_to(root)),
        "counts_by_status": counts_by_status,
        "ready_to_create_count": len(ready_to_create),
        "ready_to_create": ready_to_create[:10],
    }


def parse_skill_candidates(root: Path) -> dict[str, object]:
    path = root / "memory" / "reviews" / "skill-candidates.json"
    payload = load_json(path)
    candidates = list(payload.get("candidates") or [])
    status = "ok" if not candidates else "warn"
    return {
        "status": status,
        "source": str(path.relative_to(root)),
        "candidate_count": int(payload.get("candidate_count", len(candidates) or 0)),
        "top_candidates": [
            {
                "id": item.get("id"),
                "summary": item.get("summary"),
                "target_path": item.get("target_path"),
                "score": item.get("score"),
            }
            for item in candidates[:5]
        ],
    }


def parse_ecosystem_radar(root: Path) -> dict[str, object]:
    path = root / "memory" / "reviews" / "agent-ecosystem-refresh.json"
    if not path.exists():
        return {
            "status": "warn",
            "source": str(path.relative_to(root)),
            "reason": "missing_artifact",
            "source_count": 0,
            "changed_sources": 0,
            "failed_sources": 0,
            "baseline_missing_sources": 0,
            "attention": ["Ecosystem radar has not been run yet."],
        }
    payload = load_json(path)
    summary = payload.get("summary") or {}
    return {
        "status": str(payload.get("status") or "unknown"),
        "source": str(path.relative_to(root)),
        "reason": "artifact_present",
        "source_count": int(summary.get("source_count", 0) or 0),
        "changed_sources": int(summary.get("changed_sources", 0) or 0),
        "failed_sources": int(summary.get("failed_sources", 0) or 0),
        "baseline_missing_sources": int(summary.get("baseline_missing_sources", 0) or 0),
        "attention": list(payload.get("attention") or []),
    }


def build_payload(root: Path, refresh_failures: list[str]) -> dict[str, object]:
    memory_guard = load_json(root / "memory" / "reviews" / "memory-guard.json")
    knowledge_review = load_json(root / "wiki" / "reviews" / "knowledge-performance-review.json")
    agent_review = load_json(root / "memory" / "reviews" / "agent-performance-review.json")
    plan_state = parse_plan_state(root)
    skill_state = parse_skill_candidates(root)
    issue_state = parse_issue_opportunities(root)
    ecosystem_state = parse_ecosystem_radar(root)

    signals = [
        Signal(
            name="memory_guard",
            status=str(memory_guard.get("status") or "unknown"),
            source="memory/reviews/memory-guard.json",
            details={
                "health_score": memory_guard.get("health_score"),
                "needs_review": (memory_guard.get("review") or {}).get("needs_review", 0),
                "contradictions": (memory_guard.get("review") or {}).get("contradictions", 0),
            },
        ),
        Signal(
            name="knowledge_review",
            status=str(knowledge_review.get("status") or "unknown"),
            source="wiki/reviews/knowledge-performance-review.json",
            details={
                "health_score": knowledge_review.get("health_score"),
                "reasons": knowledge_review.get("reasons", []),
                "search_index_fresh": (knowledge_review.get("search_index") or {}).get("fresh"),
            },
        ),
        Signal(
            name="agent_review",
            status=str(agent_review.get("status") or "unknown"),
            source="memory/reviews/agent-performance-review.json",
            details={
                "open_tasks": (agent_review.get("summary") or {}).get("open_tasks", 0),
                "verification_tasks": (agent_review.get("summary") or {}).get("verification_tasks", 0),
                "coverage_verdict": agent_review.get("coverage_verdict"),
                "reasons": agent_review.get("reasons", []),
            },
        ),
        Signal(name="plan_state", status=str(plan_state["status"]), source="plans/*.md", details=plan_state),
        Signal(name="skill_candidates", status=str(skill_state["status"]), source=str(skill_state["source"]), details=skill_state),
        Signal(name="issue_opportunities", status=str(issue_state["status"]), source=str(issue_state["source"]), details=issue_state),
        Signal(name="ecosystem_radar", status=str(ecosystem_state["status"]), source=str(ecosystem_state["source"]), details=ecosystem_state),
    ]

    overall_status = worst_status([signal.status for signal in signals] + (["warn"] if refresh_failures else []))
    attention: list[str] = []
    if refresh_failures:
        attention.extend(f"Refresh failed for {item}" for item in refresh_failures)
    if plan_state["blocked_count"]:
        attention.append(f"{plan_state['blocked_count']} blocked plan items need review.")
    if plan_state["wip_count"]:
        attention.append(f"{plan_state['wip_count']} WIP plan items are still open.")
    if skill_state["candidate_count"]:
        attention.append(f"{skill_state['candidate_count']} skill candidates are waiting for review.")
    if issue_state["ready_to_create_count"]:
        attention.append(f"{issue_state['ready_to_create_count']} issue opportunities are ready to create.")
    if ecosystem_state["changed_sources"]:
        attention.append(f"{ecosystem_state['changed_sources']} ecosystem source changes need review.")
    if ecosystem_state["baseline_missing_sources"]:
        attention.append(f"{ecosystem_state['baseline_missing_sources']} ecosystem sources still need a stored radar baseline.")
    if ecosystem_state["failed_sources"]:
        attention.append(f"{ecosystem_state['failed_sources']} ecosystem sources failed to refresh.")
    if (agent_review.get("summary") or {}).get("open_tasks", 0):
        attention.append(f"{(agent_review.get('summary') or {}).get('open_tasks', 0)} delegated tasks are still open.")
    if agent_review.get("coverage_verdict") == "no_trace_file":
        attention.append("Agent trace file is missing — delegation activity in this session may be untracked.")
    if not attention:
        attention.append("Autonomic layer is healthy. No immediate operator intervention required.")

    return {
        "created": datetime.now().isoformat(timespec="seconds"),
        "status": overall_status,
        "refresh_failures": refresh_failures,
        "signals": [
            {
                "name": signal.name,
                "status": signal.status,
                "source": signal.source,
                "details": signal.details,
            }
            for signal in signals
        ],
        "summary": {
            "memory_guard_status": str(memory_guard.get("status") or "unknown"),
            "knowledge_review_status": str(knowledge_review.get("status") or "unknown"),
            "agent_review_status": str(agent_review.get("status") or "unknown"),
            "open_plan_wip": plan_state["wip_count"],
            "blocked_plan_items": plan_state["blocked_count"],
            "open_delegated_tasks": (agent_review.get("summary") or {}).get("open_tasks", 0),
            "pending_skill_candidates": skill_state["candidate_count"],
            "pending_issue_opportunities": issue_state["ready_to_create_count"],
            "ecosystem_changed_sources": ecosystem_state["changed_sources"],
        },
        "attention": attention,
        "plan_state": plan_state,
        "skill_candidates": skill_state,
        "issue_opportunities": issue_state,
        "ecosystem_radar": ecosystem_state,
    }


def render_markdown(payload: dict[str, object]) -> str:
    summary = payload["summary"]
    lines = [
        "---",
        f"created: {payload['created']}",
        "kind: autonomic-health-dashboard",
        "---",
        "",
        "# Autonomic health dashboard",
        "",
        f"- **Status:** {payload['status']}",
        f"- **Memory guard:** {summary['memory_guard_status']}",
        f"- **Knowledge review:** {summary['knowledge_review_status']}",
        f"- **Agent review:** {summary['agent_review_status']}",
        f"- **Open WIP:** {summary['open_plan_wip']}",
        f"- **Blocked plan items:** {summary['blocked_plan_items']}",
        f"- **Open delegated tasks:** {summary['open_delegated_tasks']}",
        f"- **Pending skill candidates:** {summary['pending_skill_candidates']}",
        f"- **Pending issue opportunities:** {summary['pending_issue_opportunities']}",
        f"- **Ecosystem changes:** {summary['ecosystem_changed_sources']}",
        "",
        "## Attention",
        "",
    ]
    lines.extend(f"- {item}" for item in payload["attention"])
    lines.extend(["", "## Signals", ""])
    for signal in payload["signals"]:
        lines.append(f"- **{signal['name']}:** {signal['status']} (`{signal['source']}`)")
    plan_state = payload["plan_state"]
    if plan_state["wip_items"] or plan_state["blocked_items"]:
        lines.extend(["", "## Plan state", ""])
        for item in plan_state["wip_items"]:
            lines.append(f"- **WIP:** `{item['file']}:{item['line']}` — {item['text']}")
        for item in plan_state["blocked_items"]:
            lines.append(f"- **Blocked:** `{item['file']}:{item['line']}` — {item['text']}")
    skill_candidates = payload["skill_candidates"]
    if skill_candidates["top_candidates"]:
        lines.extend(["", "## Skill candidates", ""])
        for item in skill_candidates["top_candidates"]:
            lines.append(f"- **{item['id']}** — score {item['score']}, target `{item['target_path']}`")
    issue_opportunities = payload["issue_opportunities"]
    if issue_opportunities["ready_to_create"]:
        lines.extend(["", "## Ready issue opportunities", ""])
        for item in issue_opportunities["ready_to_create"]:
            lines.append(f"- **{item['id']}** — {item['title']} ({item['status']}, {item['priority']})")
    ecosystem_radar = payload["ecosystem_radar"]
    if ecosystem_radar["changed_sources"] or ecosystem_radar["baseline_missing_sources"] or ecosystem_radar["failed_sources"]:
        lines.extend(["", "## Ecosystem radar", ""])
        for item in ecosystem_radar["attention"]:
            lines.append(f"- {item}")
    if payload["refresh_failures"]:
        lines.extend(["", "## Refresh failures", ""])
        lines.extend(f"- {item}" for item in payload["refresh_failures"])
    return "\n".join(lines).rstrip() + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Aggregate the current operational health of the workspace.")
    parser.add_argument("--refresh", action="store_true", help="Refresh core health artifacts before aggregating.")
    parser.add_argument(
        "--json-out",
        type=Path,
        default=repo_root() / "memory" / "reviews" / "autonomic-health-dashboard.json",
        help="Where to write the JSON output.",
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=repo_root() / "memory" / "reviews" / "autonomic-health-dashboard.md",
        help="Where to write the markdown output.",
    )
    parser.add_argument("--print", action="store_true", help="Print the markdown dashboard after writing.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    root = repo_root()
    refresh_failures = run_refresh_commands(root) if args.refresh else []
    payload = build_payload(root, refresh_failures)
    atomic_write(args.json_out, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    atomic_write(args.markdown_out, render_markdown(payload))
    print(f"STATUS: {payload['status']}")
    print(f"JSON: {args.json_out}")
    print(f"MARKDOWN: {args.markdown_out}")
    print(f"OPEN_WIP: {payload['summary']['open_plan_wip']}")
    print(f"OPEN_DELEGATED_TASKS: {payload['summary']['open_delegated_tasks']}")
    print(f"PENDING_SKILL_CANDIDATES: {payload['summary']['pending_skill_candidates']}")
    print(f"PENDING_ISSUE_OPPORTUNITIES: {payload['summary']['pending_issue_opportunities']}")
    print(f"ECOSYSTEM_CHANGED_SOURCES: {payload['summary']['ecosystem_changed_sources']}")
    if payload["refresh_failures"]:
        print(f"REFRESH_FAILURES: {len(payload['refresh_failures'])}")
    if args.print:
        print()
        print(render_markdown(payload), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
