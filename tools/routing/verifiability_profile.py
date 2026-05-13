#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""
verifiability_profile.py - Resolve verifiability and autonomy expectations for routed tasks.

Usage:
    uv run tools/routing/verifiability_profile.py --task-type code --complexity complex --risk high
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

AUTONOMY_RANK = {"low": 0, "medium": 1, "high": 2}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_config(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _merge_unique(*groups: list[str]) -> list[str]:
    merged: list[str] = []
    for group in groups:
        for item in group:
            if item not in merged:
                merged.append(item)
    return merged


def _cap_autonomy(current: str, cap: str | None) -> str:
    if not cap:
        return current
    return min((current, cap), key=lambda item: AUTONOMY_RANK[item])


def build_profile(
    *,
    task_type: str,
    complexity: str,
    risk: str,
    config_path: Path | None = None,
) -> dict[str, Any]:
    config = load_config(config_path or (repo_root() / "config" / "verifiability-map.yaml"))
    task_config = config["task_types"][task_type]
    complexity_config = config["complexity_overrides"].get(complexity, {})
    risk_config = config["risk_overrides"].get(risk, {})
    autonomy_level = str(task_config["default_autonomy_level"])
    autonomy_level = _cap_autonomy(autonomy_level, complexity_config.get("autonomy_cap"))
    autonomy_level = _cap_autonomy(autonomy_level, risk_config.get("autonomy_cap"))
    required_contract_fields = _merge_unique(
        list(config["defaults"].get("required_contract_fields", [])),
        list(task_config.get("required_contract_fields", [])),
        list(complexity_config.get("required_contract_fields", [])),
        list(risk_config.get("required_contract_fields", [])),
    )
    required_review_signals = _merge_unique(
        list(config["defaults"].get("required_review_signals", [])),
        list(task_config.get("required_review_signals", [])),
        list(complexity_config.get("required_review_signals", [])),
        list(risk_config.get("required_review_signals", [])),
    )
    rationale = [
        f"task_type={task_type} -> verifiability {task_config['verifiability']}",
        f"task_type={task_type} -> default autonomy {task_config['default_autonomy_level']}",
    ]
    if complexity_config.get("autonomy_cap"):
        rationale.append(f"complexity={complexity} caps autonomy to {complexity_config['autonomy_cap']}")
    if risk_config.get("autonomy_cap"):
        rationale.append(f"risk={risk} caps autonomy to {risk_config['autonomy_cap']}")
    return {
        "config_version": config["version"],
        "task_type": task_type,
        "complexity": complexity,
        "risk": risk,
        "verifiability": task_config["verifiability"],
        "autonomy_level": autonomy_level,
        "required_contract_fields": required_contract_fields,
        "required_review_signals": required_review_signals,
        "rationale": rationale,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve verifiability/autonomy metadata for routed tasks.")
    parser.add_argument("--config", type=Path, default=repo_root() / "config" / "verifiability-map.yaml")
    parser.add_argument("--task-type", choices=["lookup", "code", "analysis", "synthesis", "decision"], required=True)
    parser.add_argument("--complexity", choices=["trivial", "standard", "complex", "critical"], required=True)
    parser.add_argument("--risk", choices=["low", "medium", "high"], required=True)
    parser.add_argument("--json", action="store_true", default=True)
    args = parser.parse_args()

    payload = build_profile(
        task_type=args.task_type,
        complexity=args.complexity,
        risk=args.risk,
        config_path=args.config,
    )
    if args.json:
        print(json.dumps(payload, ensure_ascii=True))
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
