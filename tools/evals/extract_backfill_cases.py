#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""
extract_backfill_cases.py - extract normalized workflow eval cases from plans and daily notes.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(content, encoding="utf-8")
    temp.replace(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def detect_source_family(path: Path, root: Path) -> str:
    relative = path.relative_to(root).as_posix()
    if relative.startswith("plans/"):
        return "plans"
    if relative.startswith("PersonalNotes/Daily/"):
        return "daily-notes"
    raise ValueError(f"Unsupported source family for {relative}")


def build_case(
    *,
    relative_path: str,
    created: str,
    suite: str,
    mode: str,
    case_type: str,
    source_family: str,
    title: str,
    description: str,
    contains: list[str],
    components: list[str],
) -> dict[str, Any]:
    path_obj = Path(relative_path)
    case_id = f"{suite}-{slugify(path_obj.stem)}-{slugify(title)}"
    return {
        "id": case_id,
        "created": created,
        "suite": suite,
        "mode": mode,
        "case_type": case_type,
        "source_family": source_family,
        "source_path": relative_path.replace("\\", "/"),
        "title": title,
        "description": description,
        "test_type": "file_contains",
        "test_payload": {
            "path": relative_path.replace("/", "\\"),
            "contains": contains,
        },
        "expected_outcome": "pass",
        "confidence": "high",
        "components_covered": components,
        "evidence": contains,
        "contradiction": None,
        "next_test": "Expand this pattern to an additional independent artifact.",
    }


def plan_patterns(relative_path: str) -> list[dict[str, Any]]:
    patterns: list[dict[str, Any]] = []
    if relative_path == "plans/2026-04-15-agi-harness-epistemic-upgrades.md":
        patterns.append(
            {
                "suite": "research-synthesis",
                "mode": "capability",
                "case_type": "plan-validation",
                "title": "AGI rollout eval discipline",
                "description": "Verify that the rollout plan keeps explicit eval structure and capability-vs-regression discipline.",
                "contains": [
                    "### Phase 4 — Eval harness",
                    "private workflow eval suites",
                    "Do not mix capability evals and regression evals.",
                ],
                "components": ["checkpoint", "ledger"],
            }
        )
    if relative_path == "plans/2026-04-15-eval-backfill-and-repo-publish.md":
        patterns.extend(
            [
                {
                    "suite": "handoff",
                    "mode": "capability",
                    "case_type": "plan-validation",
                    "title": "Backfill plan handoff state",
                    "description": "Verify that validation, replanning, handoff, and checkpoint sections remain visible.",
                    "contains": [
                        "### Validation plan",
                        "### Replan rule",
                        "### Handoff state",
                        "## Checkpoint summary",
                    ],
                    "components": ["checkpoint", "ledger"],
                },
                {
                    "suite": "hypothesis-discipline",
                    "mode": "capability",
                    "case_type": "plan-validation",
                    "title": "Backfill plan hypothesis ledger",
                    "description": "Verify that the plan keeps a visible hypothesis ledger and explicit next test.",
                    "contains": [
                        "## Hypothesis Ledger",
                        "Pilot-extract 5 real cases and validate quality",
                        "### Source priority",
                    ],
                    "components": ["ledger"],
                },
            ]
        )
    return patterns


def daily_patterns(relative_path: str) -> list[dict[str, Any]]:
    patterns: list[dict[str, Any]] = []
    if relative_path == "PersonalNotes/Daily/2026-04-15.md":
        patterns.extend(
            [
                {
                    "suite": "trace-quality",
                    "mode": "regression",
                    "case_type": "daily-session",
                    "title": "Phase 4 green baseline recorded",
                    "description": "Verify that the daily note preserves the green workflow-eval baseline.",
                    "contains": [
                        "### [15:39] Session · AGI Harness Phase 4",
                        "workflow eval status `ok`; suites `4`; cases `6`; failed cases `0`",
                    ],
                    "components": ["verifier", "checkpoint"],
                },
                {
                    "suite": "hypothesis-discipline",
                    "mode": "regression",
                    "case_type": "daily-session",
                    "title": "Phase 5 warning recorded",
                    "description": "Verify that the daily note preserves the conservative ablation warning.",
                    "contains": [
                        "### [15:44] Session · AGI Harness Phase 5",
                        "reconcile-ablation-not-eval-backed",
                        "baseline workflow eval `ok`",
                    ],
                    "components": ["verifier", "ledger"],
                },
            ]
        )
    return patterns


def validate_case(case: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in schema["required_fields"]:
        if field not in case:
            errors.append(f"{case.get('id', '<missing-id>')}: missing field '{field}'")
    for field, allowed in schema["enums"].items():
        if field not in case:
            continue
        value = case[field]
        if isinstance(value, list):
            invalid = [item for item in value if item not in allowed]
            if invalid:
                errors.append(f"{case['id']}: invalid {field} values {invalid}")
        elif value not in allowed:
            errors.append(f"{case['id']}: invalid {field} value {value!r}")
    payload = case.get("test_payload", {})
    if case.get("test_type") == "file_contains":
        if "path" not in payload or "contains" not in payload:
            errors.append(f"{case['id']}: invalid file_contains payload")
    return errors


def extract_cases(input_paths: list[Path], root: Path, created: str) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for path in input_paths:
        relative = path.relative_to(root).as_posix()
        source_family = detect_source_family(path, root)
        patterns = plan_patterns(relative) if source_family == "plans" else daily_patterns(relative)
        for pattern in patterns:
            content = path.read_text(encoding="utf-8")
            if all(needle in content for needle in pattern["contains"]):
                cases.append(
                    build_case(
                        relative_path=relative,
                        created=created,
                        suite=pattern["suite"],
                        mode=pattern["mode"],
                        case_type=pattern["case_type"],
                        source_family=source_family,
                        title=pattern["title"],
                        description=pattern["description"],
                        contains=pattern["contains"],
                        components=pattern["components"],
                    )
                )
    return cases


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract normalized backfill cases from plans and daily notes.")
    parser.add_argument("--inputs", nargs="+", required=True, help="Workspace-relative input files to inspect.")
    parser.add_argument("--output", required=True, help="Workspace-relative JSON output path.")
    parser.add_argument("--description", default="Generated real-case extraction batch.", help="Description for the output bundle.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root()
    created = now_iso()
    schema = read_json(root / "evals" / "case-schema.json")
    input_paths = [root / item for item in args.inputs]
    cases = extract_cases(input_paths, root, created)

    errors: list[str] = []
    for case in cases:
        errors.extend(validate_case(case, schema))
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    payload = {
        "version": 1,
        "created": created,
        "description": args.description,
        "cases": cases,
    }
    output_path = root / args.output
    atomic_write(output_path, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    print(f"OUTPUT: {output_path}")
    print(f"CASES: {len(cases)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
