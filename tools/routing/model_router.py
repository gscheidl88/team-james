#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""
model_router.py - Recommend primary and verifier models from model-routing.yaml.

Usage:
    uv run tools/routing/model_router.py --complexity complex --task-type code --risk high
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

TIER_RANK = {"economy": 0, "standard": 1, "premium": 2}
VERIFICATION_RANK = {"none": 0, "spot-check": 1, "full-review": 2}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_config(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def model_tier(config: dict[str, Any], model: str) -> str | None:
    for tier_name, models in config["model_families"].items():
        if model in models:
            return tier_name
    return None


def model_family(model: str) -> str:
    lowered = model.lower()
    if lowered.startswith("claude-"):
        return "claude"
    if lowered.startswith("gpt-"):
        return "gpt"
    if lowered.startswith("gemini-"):
        return "gemini"
    return "unknown"


def choose_primary(
    config: dict[str, Any],
    complexity: str,
    task_type: str,
    cost_profile: str,
) -> tuple[str, list[str], str]:
    warnings: list[str] = []
    required_tier = config["complexity_rules"][complexity]["primary_tier"]
    cap_tier = config["cost_profiles"][cost_profile]["primary_cap"]
    preferred_models = config["task_type_overrides"][task_type]["preferred_primary"]

    allowed_models = [
        model
        for model in preferred_models
        if TIER_RANK[model_tier(config, model)] <= TIER_RANK[cap_tier]
        and TIER_RANK[model_tier(config, model)] >= TIER_RANK[required_tier]
    ]
    if allowed_models:
        return allowed_models[0], warnings, required_tier

    fallback_models = [
        model
        for model in preferred_models
        if TIER_RANK[model_tier(config, model)] >= TIER_RANK[required_tier]
    ]
    if fallback_models:
        warnings.append(
            f"Cost profile '{cost_profile}' does not satisfy required tier '{required_tier}'. "
            "Using stronger primary model."
        )
        return fallback_models[0], warnings, required_tier

    family_models = config["model_families"][required_tier]
    warnings.append(
        f"No preferred primary model matched task type '{task_type}'. Falling back to tier '{required_tier}'."
    )
    return family_models[0], warnings, required_tier


def resolve_verification_need(config: dict[str, Any], complexity: str, risk: str) -> str:
    base = config["complexity_rules"][complexity]["verification_need"]
    minimum = config["risk_rules"][risk]["minimum_verification"]
    return max(base, minimum, key=lambda item: VERIFICATION_RANK[item])


def choose_verifier(
    config: dict[str, Any],
    primary_model: str,
    verification_need: str,
    cost_profile: str,
) -> tuple[str | None, list[str]]:
    if verification_need == "none":
        return None, []

    warnings: list[str] = []
    primary_family = model_family(primary_model)
    routing_key = "claude_primary" if primary_family == "claude" else "gpt_primary"
    if routing_key not in config["verification_routing"]:
        warnings.append(f"No verifier routing configured for primary family '{primary_family}'.")
        return None, warnings

    verifier_candidates = config["verification_routing"][routing_key][verification_need.replace("-", "_")]
    cap_tier = config["cost_profiles"][cost_profile]["verifier_cap"]

    allowed = [
        model
        for model in verifier_candidates
        if TIER_RANK[model_tier(config, model)] <= TIER_RANK[cap_tier]
    ]
    if allowed:
        return allowed[0], warnings

    warnings.append(
        f"Cost profile '{cost_profile}' does not satisfy verifier requirement '{verification_need}'. "
        "Using stronger verifier model."
    )
    return verifier_candidates[0], warnings


def build_routing_metadata(
    complexity: str,
    task_type: str,
    risk: str,
    cost_profile: str,
    primary_model: str,
    verifier_model: str | None,
    verification_need: str,
) -> str:
    verifier_display = verifier_model if verifier_model else "none"
    return "\n".join(
        [
            "[ROUTING METADATA]",
            f"- complexity: {complexity}",
            f"- task_type: {task_type}",
            f"- risk: {risk}",
            f"- cost_profile: {cost_profile}",
            f"- primary_model: {primary_model}",
            f"- verifier_model: {verifier_display}",
            f"- verification_need: {verification_need}",
        ]
    )


def route_task(
    *,
    complexity: str,
    task_type: str,
    risk: str,
    cost_profile: str = "normal",
    config_path: Path | None = None,
) -> dict[str, Any]:
    config = load_config(config_path or (repo_root() / "config" / "model-routing.yaml"))
    primary_model, primary_warnings, required_tier = choose_primary(
        config=config,
        complexity=complexity,
        task_type=task_type,
        cost_profile=cost_profile,
    )
    verification_need = resolve_verification_need(config, complexity, risk)
    verifier_model, verifier_warnings = choose_verifier(
        config=config,
        primary_model=primary_model,
        verification_need=verification_need,
        cost_profile=cost_profile,
    )
    prompt = config["task_type_overrides"][task_type]["verifier_prompt"]
    return {
        "config_version": config["version"],
        "complexity": complexity,
        "task_type": task_type,
        "risk": risk,
        "cost_profile": cost_profile,
        "required_primary_tier": required_tier,
        "primary_model": primary_model,
        "primary_family": model_family(primary_model),
        "verification_need": verification_need,
        "verifier_model": verifier_model,
        "verifier_family": model_family(verifier_model) if verifier_model else None,
        "preferred_agent_type": config["task_type_overrides"][task_type]["preferred_agent_type"],
        "verifier_prompt": prompt,
        "routing_metadata": build_routing_metadata(
            complexity=complexity,
            task_type=task_type,
            risk=risk,
            cost_profile=cost_profile,
            primary_model=primary_model,
            verifier_model=verifier_model,
            verification_need=verification_need,
        ),
        "warnings": primary_warnings + verifier_warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Recommend primary/verifier models for delegated tasks.")
    parser.add_argument("--config", type=Path, default=repo_root() / "config" / "model-routing.yaml")
    parser.add_argument("--complexity", choices=["trivial", "standard", "complex", "critical"], required=True)
    parser.add_argument("--task-type", choices=["lookup", "code", "analysis", "synthesis", "decision"], required=True)
    parser.add_argument("--risk", choices=["low", "medium", "high"], required=True)
    parser.add_argument("--cost-profile", choices=["budget", "normal", "unlimited"], default="normal")
    parser.add_argument("--json", action="store_true", default=True)
    args = parser.parse_args()

    payload = route_task(
        complexity=args.complexity,
        task_type=args.task_type,
        risk=args.risk,
        cost_profile=args.cost_profile,
        config_path=args.config,
    )

    if args.json:
        print(json.dumps(payload, ensure_ascii=True))
    else:
        print(payload["routing_metadata"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
