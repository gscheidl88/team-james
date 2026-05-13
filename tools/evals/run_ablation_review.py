#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""
run_ablation_review.py - baseline ablation review for workflow components.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any


ABLATION_COMPONENTS = ("verifier", "checkpoint", "ledger", "reconcile")


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


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_workflow_eval_review(root: Path) -> dict[str, Any]:
    runner = root / "tools" / "evals" / "run_workflow_evals.py"
    with tempfile.TemporaryDirectory(prefix="ablation-review-") as temp_dir:
        temp = Path(temp_dir)
        json_out = temp / "workflow-eval-review.json"
        markdown_out = temp / "workflow-eval-review.md"
        history_out = temp / "workflow-eval-history.jsonl"
        completed = subprocess.run(
            [
                sys.executable,
                str(runner),
                "--json-out",
                str(json_out),
                "--markdown-out",
                str(markdown_out),
                "--history-out",
                str(history_out),
            ],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(f"Workflow eval runner failed:\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}")
        return read_json(json_out)


def load_suite_definitions(root: Path) -> dict[str, dict[str, Any]]:
    suites: dict[str, dict[str, Any]] = {}
    for suite_path in sorted((root / "evals").glob("*/suite.json")):
        payload = read_json(suite_path)
        suites[str(payload["name"])] = payload
    return suites


def build_case_result_map(workflow_review: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    case_map: dict[tuple[str, str], dict[str, Any]] = {}
    for suite in workflow_review.get("suites", []):
        suite_name = str(suite["name"])
        for case in suite.get("cases", []):
            case_map[(suite_name, str(case["id"]))] = case
    return case_map


def risk_level(overall_delta_percent: float, includes_regression: bool, component: str, measurement_mode: str) -> str:
    if measurement_mode != "private-eval":
        return "medium"
    if includes_regression or overall_delta_percent >= 30.0:
        return "high"
    if overall_delta_percent >= 15.0:
        return "medium"
    return "low"


def recommendation_for(component: str, measurement_mode: str, includes_regression: bool) -> str:
    if component == "verifier":
        return "Keep cross-family verifier routing active on complex and critical delegated work."
    if component == "checkpoint":
        return "Keep first-check planning and checkpoint-summary requirements mandatory for long-running work."
    if component == "ledger":
        return "Keep the Hypothesis Ledger on medium+ analysis, research, and decision workflows."
    if component == "reconcile":
        if measurement_mode != "private-eval":
            return "Do not optimize away reconciliation yet; first add private eval coverage for reconcile-specific workflows."
        return "Keep retrieval-before-write reconciliation in durable-memory flows."
    return "Preserve the current control until stronger evidence exists."


def analyze_eval_backed_component(
    component: str,
    workflow_review: dict[str, Any],
    suite_definitions: dict[str, dict[str, Any]],
    case_results: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, Any]:
    impacted: list[dict[str, Any]] = []
    regression_count = 0
    total_cases = int(workflow_review["summary"]["overall"]["case_count"])
    for suite_name, suite in suite_definitions.items():
        for case in suite.get("cases", []):
            components = [str(item) for item in case.get("components", [])]
            if component not in components:
                continue
            result = case_results[(suite_name, str(case["id"]))]
            impacted.append(
                {
                    "suite": suite_name,
                    "case_id": case["id"],
                    "mode": suite["mode"],
                    "passed_in_baseline": bool(result["passed"]),
                    "detail": result["detail"],
                }
            )
            if suite["mode"] == "regression":
                regression_count += 1

    passed_in_baseline = sum(1 for item in impacted if item["passed_in_baseline"])
    overall_delta_percent = round((passed_in_baseline / max(total_cases, 1)) * 100.0, 2)
    measurement_mode = "private-eval"
    return {
        "component": component,
        "measurement_mode": measurement_mode,
        "coverage_count": len(impacted),
        "baseline_passed_coverage": passed_in_baseline,
        "overall_case_delta_percent": overall_delta_percent,
        "includes_regression": regression_count > 0,
        "risk": risk_level(overall_delta_percent, regression_count > 0, component, measurement_mode),
        "recommendation": recommendation_for(component, measurement_mode, regression_count > 0),
        "impacted_cases": impacted,
    }


def analyze_reconcile_component(root: Path) -> dict[str, Any]:
    procedures_text = (root / "memory" / "procedures.md").read_text(encoding="utf-8")
    latest_review_path = root / "memory" / "reviews" / "latest-memory-review.json"
    memory_reconcile_path = root / "tools" / "memory" / "memory_reconcile.py"

    latest_review = read_json(latest_review_path) if latest_review_path.exists() else {"items": []}
    items = latest_review.get("items", [])
    evidence = [
        {
            "signal": "procedure-rules-present",
            "present": "Reconsolidation states" in procedures_text and "Retrieve-before-write checklist" in procedures_text,
        },
        {
            "signal": "reconcile-tool-present",
            "present": memory_reconcile_path.exists(),
        },
        {
            "signal": "review-artifact-present",
            "present": latest_review_path.exists() and len(items) > 0,
        },
    ]
    evidence_count = sum(1 for item in evidence if item["present"])
    measurement_mode = "operational-evidence"
    return {
        "component": "reconcile",
        "measurement_mode": measurement_mode,
        "coverage_count": evidence_count,
        "baseline_passed_coverage": evidence_count,
        "overall_case_delta_percent": None,
        "includes_regression": False,
        "risk": risk_level(0.0, False, "reconcile", measurement_mode),
        "recommendation": recommendation_for("reconcile", measurement_mode, False),
        "impacted_cases": evidence,
    }


def build_review_payload(root: Path) -> dict[str, Any]:
    workflow_review = run_workflow_eval_review(root)
    suite_definitions = load_suite_definitions(root)
    case_results = build_case_result_map(workflow_review)

    component_reviews = [
        analyze_eval_backed_component("verifier", workflow_review, suite_definitions, case_results),
        analyze_eval_backed_component("checkpoint", workflow_review, suite_definitions, case_results),
        analyze_eval_backed_component("ledger", workflow_review, suite_definitions, case_results),
        analyze_reconcile_component(root),
    ]

    reasons: list[str] = []
    actions: list[str] = []
    status = "ok"

    if workflow_review["status"] != "ok":
        status = "warn"
        reasons.append("workflow-eval-baseline-not-green")
        actions.append("Stabilize the workflow eval baseline before trusting ablation guidance.")

    reconcile_review = next(item for item in component_reviews if item["component"] == "reconcile")
    if reconcile_review["measurement_mode"] != "private-eval":
        status = "warn" if status == "ok" else status
        reasons.append("reconcile-ablation-not-eval-backed")
        actions.append("Add a private reconcile workflow eval before relaxing memory reconciliation controls.")

    high_risk_components = [item["component"] for item in component_reviews if item["risk"] == "high"]
    if high_risk_components:
        actions.append(
            "Do not relax these controls without replacement evidence: " + ", ".join(high_risk_components) + "."
        )

    if not actions:
        actions.append("Ablation baseline is healthy. Preserve current controls unless a targeted replacement is measured.")

    return {
        "created": now_iso(),
        "status": status,
        "baseline_workflow_eval": {
            "status": workflow_review["status"],
            "summary": workflow_review["summary"],
        },
        "components": component_reviews,
        "reasons": reasons,
        "actions": actions,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    baseline = payload["baseline_workflow_eval"]
    lines = [
        "---",
        f"created: {payload['created']}",
        "kind: ablation-review",
        "---",
        "",
        "# Ablation review",
        "",
        f"- **Status:** {payload['status']}",
        f"- **Reasons:** {', '.join(payload['reasons']) if payload['reasons'] else 'none'}",
        "",
        "## Baseline",
        "",
        f"- **Workflow eval status:** {baseline['status']}",
        f"- **Suites:** {baseline['summary']['overall']['suite_count']}",
        f"- **Cases:** {baseline['summary']['overall']['case_count']}",
        f"- **Passed cases:** {baseline['summary']['overall']['passed_cases']}",
        f"- **Failed cases:** {baseline['summary']['overall']['failed_cases']}",
        "",
        "## Component ablations",
        "",
        "| Component | Measurement mode | Coverage | Delta if removed | Risk | Recommendation |",
        "|-----------|------------------|----------|------------------|------|----------------|",
    ]
    for component in payload["components"]:
        delta = (
            f"{component['overall_case_delta_percent']}% of workflow cases"
            if component["overall_case_delta_percent"] is not None
            else "not directly measured"
        )
        lines.append(
            f"| {component['component']} | {component['measurement_mode']} | "
            f"{component['baseline_passed_coverage']}/{component['coverage_count']} | {delta} | "
            f"{component['risk']} | {component['recommendation']} |"
        )

    lines.extend(["", "## Actions", ""])
    lines.extend(f"- {action}" for action in payload["actions"])

    for component in payload["components"]:
        lines.extend(
            [
                "",
                f"## {component['component'].title()}",
                "",
                f"- **Measurement mode:** {component['measurement_mode']}",
                f"- **Coverage:** {component['baseline_passed_coverage']}/{component['coverage_count']}",
                f"- **Risk:** {component['risk']}",
                f"- **Recommendation:** {component['recommendation']}",
                "",
            ]
        )
        for item in component["impacted_cases"]:
            if component["measurement_mode"] == "private-eval":
                lines.append(
                    f"- **{item['suite']} / {item['case_id']}** ({item['mode']}) — "
                    f"baseline passed: {item['passed_in_baseline']}"
                )
            else:
                lines.append(f"- **{item['signal']}** — present: {item['present']}")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    root = repo_root()
    reviews_dir = root / "memory" / "reviews"
    parser = argparse.ArgumentParser(description="Run a baseline ablation review over workflow controls.")
    parser.add_argument("--json-out", type=Path, default=reviews_dir / "ablation-review.json")
    parser.add_argument("--markdown-out", type=Path, default=reviews_dir / "ablation-review.md")
    parser.add_argument("--history-out", type=Path, default=reviews_dir / "ablation-review-history.jsonl")
    args = parser.parse_args()

    payload = build_review_payload(root)
    write_json(args.json_out, payload)
    atomic_write(args.markdown_out, render_markdown(payload))
    append_jsonl(
        args.history_out,
        {
            "timestamp": payload["created"],
            "status": payload["status"],
            "baseline_workflow_eval_status": payload["baseline_workflow_eval"]["status"],
            "reasons": payload["reasons"],
            "component_risks": {item["component"]: item["risk"] for item in payload["components"]},
        },
    )

    print(f"STATUS: {payload['status']}")
    print(f"JSON: {args.json_out}")
    print(f"MARKDOWN: {args.markdown_out}")
    print(f"BASELINE_WORKFLOW_STATUS: {payload['baseline_workflow_eval']['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
