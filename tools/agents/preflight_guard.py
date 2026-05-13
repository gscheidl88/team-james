#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""
preflight_guard.py — Agent permission preflight check.

Reads config/agent-permissions.yaml and checks whether the requested tools
are permitted for the given agent type.

Exit codes:
  0  — all requested tools are allowed
  1  — one or more tools are policy-denied for this agent type
  2  — invalid invocation (bad args) or missing / unreadable config

Usage:
    uv run tools/agents/preflight_guard.py --agent-type developer --requested-tools view edit powershell
    uv run tools/agents/preflight_guard.py --agent-type researcher --requested-tools shell
    uv run tools/agents/preflight_guard.py --agent-type analyst --requested-tools agent_spawn

This is the canonical preflight check for delegated personas. Routed `delegate.py spawn`
invocations call it before the task tool is launched, and it can still be run
manually or in CI to surface policy violations early.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any


# ── Config resolution ─────────────────────────────────────────────────────────

def _find_repo_root() -> Path:
    """Walk up from this file to find the repo root (contains AGENTS.md)."""
    here = Path(__file__).resolve().parent
    for candidate in [here, *here.parents]:
        if (candidate / "AGENTS.md").exists():
            return candidate
    # Fallback: treat cwd as root
    return Path.cwd()


def _load_permissions(config_path: Path) -> dict:
    try:
        import yaml  # type: ignore[import-untyped]
    except ImportError:
        print("ERROR: pyyaml is not available — install with: uv add pyyaml", file=sys.stderr)
        sys.exit(2)

    if not config_path.exists():
        print(f"ERROR: permissions config not found: {config_path}", file=sys.stderr)
        print("HINT: expected config/agent-permissions.yaml in the repo root", file=sys.stderr)
        sys.exit(2)

    try:
        with config_path.open(encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except Exception as exc:
        print(f"ERROR: failed to parse {config_path}: {exc}", file=sys.stderr)
        sys.exit(2)

    if not isinstance(data, dict) or "agents" not in data:
        print(f"ERROR: {config_path} is missing the top-level 'agents' key", file=sys.stderr)
        sys.exit(2)

    return data


def run_preflight(
    agent_type: str,
    requested_tools: list[str],
    config_path: Path | None = None,
) -> dict[str, Any]:
    """Resolve a preflight check once so CLI and runtime callers share one path."""
    resolved_config = config_path or (_find_repo_root() / "config" / "agent-permissions.yaml")
    permissions = _load_permissions(resolved_config)
    exit_code, allowed, denied = _check_agent(
        permissions=permissions,
        agent_type=agent_type,
        requested_tools=requested_tools,
    )
    agent_entry = next((a for a in permissions["agents"] if a.get("id") == agent_type), None)
    return {
        "exit_code": exit_code,
        "allowed": allowed,
        "denied": denied,
        "config_path": resolved_config,
        "agent_label": (agent_entry or {}).get("label", agent_type),
        "notes": (agent_entry or {}).get("notes"),
        "permissions": permissions,
    }


# ── Permission resolution ─────────────────────────────────────────────────────

def _resolve_tools(tool_categories: dict[str, list[str]], category_names: list[str]) -> set[str]:
    """Expand a list of category names into individual tool names."""
    resolved: set[str] = set()
    for name in category_names:
        if name in tool_categories:
            resolved.update(tool_categories[name])
        else:
            # Treat unknown names as literal tool names
            resolved.add(name)
    return resolved


def _check_agent(
    permissions: dict,
    agent_type: str,
    requested_tools: list[str],
) -> tuple[int, list[str], list[str]]:
    """Return (exit_code, allowed_tools, denied_tools).

    exit_code: 0 = all allowed, 1 = some denied, 2 = agent_type not found
    """
    tool_categories: dict[str, list[str]] = permissions.get("tool_categories", {})
    agents: list[dict] = permissions.get("agents", [])

    agent_entry = next((a for a in agents if a.get("id") == agent_type), None)
    if agent_entry is None:
        known = [a.get("id") for a in agents]
        print(
            f"ERROR: agent type '{agent_type}' is not defined in agent-permissions.yaml",
            file=sys.stderr,
        )
        print(f"HINT: known agent types: {', '.join(str(k) for k in known)}", file=sys.stderr)
        return 2, [], []

    permitted_categories: list[str] = agent_entry.get("permitted_tools", [])
    denied_categories: list[str] = agent_entry.get("denied_tools", [])

    permitted_set = _resolve_tools(tool_categories, permitted_categories)
    denied_set = _resolve_tools(tool_categories, denied_categories)

    allowed: list[str] = []
    denied: list[str] = []

    for tool in requested_tools:
        # A tool is denied if it appears in the denied set OR is not in the permitted set.
        if tool in denied_set or tool not in permitted_set:
            denied.append(tool)
        else:
            allowed.append(tool)

    exit_code = 0 if not denied else 1
    return exit_code, allowed, denied


# ── CLI ───────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Preflight permission check for agent tool requests.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--agent-type",
        required=True,
        help="Agent type to check (e.g. developer, analyst, researcher, qa, cao, explore).",
    )
    parser.add_argument(
        "--requested-tools",
        nargs="+",
        required=True,
        metavar="TOOL",
        help="One or more tool names to check (e.g. view edit powershell agent_spawn).",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to agent-permissions.yaml (default: auto-detect from repo root).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print the full agent policy entry.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        return 2

    args = parser.parse_args()

    # Resolve config path
    config_path: Path
    if args.config:
        config_path = args.config
    else:
        repo_root = _find_repo_root()
        config_path = repo_root / "config" / "agent-permissions.yaml"

    result = run_preflight(
        agent_type=args.agent_type,
        requested_tools=args.requested_tools,
        config_path=config_path,
    )
    permissions = result["permissions"]
    exit_code = int(result["exit_code"])
    allowed = list(result["allowed"])
    denied = list(result["denied"])

    if exit_code == 2:
        return 2

    agent_label = str(result["agent_label"])

    print(f"AGENT:     {agent_label}")
    print(f"CONFIG:    {config_path}")
    print(f"REQUESTED: {', '.join(args.requested_tools)}")
    print()

    if allowed:
        print(f"ALLOWED ({len(allowed)}): {', '.join(allowed)}")
    if denied:
        print(f"DENIED  ({len(denied)}): {', '.join(denied)}")

    if exit_code == 0:
        print("\nRESULT: OK — all requested tools are permitted for this agent type.")
    else:
        print(
            f"\nRESULT: POLICY DENIED — {len(denied)} tool(s) not permitted for '{args.agent_type}'."
        )
        notes = result.get("notes")
        if notes:
            print(f"POLICY NOTE: {notes}")
        print("ACTION: Remove denied tools from the task or escalate to James (CAO).")

    if args.verbose:
        import json
        entry = next(a for a in permissions["agents"] if a.get("id") == args.agent_type)
        print("\nFULL POLICY ENTRY:")
        print(json.dumps(entry, indent=2))

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
