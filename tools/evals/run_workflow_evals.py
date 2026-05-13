#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""
run_workflow_evals.py - repeatable private eval harness for recurring workflow quality.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from collections import OrderedDict
from datetime import datetime
from pathlib import Path
from typing import Any


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


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


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def find_uv() -> str:
    return shutil.which("uv") or r"uv"


def get_by_path(payload: dict[str, Any], path: str) -> Any:
    current: Any = payload
    for part in path.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
            continue
        raise KeyError(path)
    return current


def assert_equals(actual: Any, expected: Any) -> tuple[bool, str]:
    if actual == expected:
        return True, f"equals {expected!r}"
    return False, f"expected {expected!r}, got {actual!r}"


def assert_not_equals(actual: Any, expected: Any) -> tuple[bool, str]:
    if actual != expected:
        return True, f"not equals {expected!r} (got {actual!r})"
    return False, f"should not equal {expected!r}"


def assert_contains(actual: Any, expected: Any) -> tuple[bool, str]:
    if isinstance(actual, str):
        ok = str(expected) in actual
    elif isinstance(actual, list):
        ok = expected in actual
    elif isinstance(actual, dict):
        ok = str(expected) in actual
    else:
        ok = False
    if ok:
        return True, f"contains {expected!r}"
    return False, f"missing {expected!r} in {actual!r}"


def assert_not_contains(actual: Any, expected: Any) -> tuple[bool, str]:
    if isinstance(actual, str):
        ok = str(expected) not in actual
    elif isinstance(actual, list):
        ok = expected not in actual
    elif isinstance(actual, dict):
        ok = str(expected) not in actual
    else:
        ok = True
    if ok:
        return True, f"does not contain {expected!r}"
    return False, f"should not contain {expected!r} but found it in {actual!r}"


def assert_gte(actual: Any, expected: Any) -> tuple[bool, str]:
    try:
        actual_value = float(actual)
        expected_value = float(expected)
    except (TypeError, ValueError):
        return False, f"cannot compare {actual!r} >= {expected!r}"
    if actual_value >= expected_value:
        return True, f"{actual_value!r} >= {expected_value!r}"
    return False, f"expected >= {expected_value!r}, got {actual_value!r}"


def evaluate_assertions(payload: dict[str, Any], assertions: list[dict[str, Any]]) -> tuple[bool, list[dict[str, str]]]:
    results: list[dict[str, str]] = []
    passed = True
    for assertion in assertions:
        path = str(assertion["path"])
        actual = get_by_path(payload, path)
        if "equals" in assertion:
            ok, detail = assert_equals(actual, assertion["equals"])
        elif "not_equals" in assertion:
            ok, detail = assert_not_equals(actual, assertion["not_equals"])
        elif "contains" in assertion:
            ok, detail = assert_contains(actual, assertion["contains"])
        elif "not_contains" in assertion:
            ok, detail = assert_not_contains(actual, assertion["not_contains"])
        elif "gte" in assertion:
            ok, detail = assert_gte(actual, assertion["gte"])
        else:
            raise ValueError(f"Unsupported assertion in {assertion!r}")
        results.append(
            {
                "path": path,
                "result": "pass" if ok else "fail",
                "detail": detail,
            }
        )
        passed = passed and ok
    return passed, results


def classify_assertion_failure(assertion_results: list[dict[str, str]], probe_payload: dict[str, Any]) -> str:
    """Return the most specific failure class for the first failing assertion."""
    for r in assertion_results:
        if r["result"] != "fail":
            continue
        path = r["path"]
        if path == "result_count":
            actual = probe_payload.get("result_count", 0)
            if actual == 0:
                return "empty_result"
        if path in ("top_hit_file", "top_hit_title"):
            return "wrong_top_hit"
        if path in ("top_files", "top_titles"):
            return "missing_node"
        if path in ("target_ids", "relates_to_ids", "depends_on_ids", "superseded_by_ids"):
            return "wrong_relation_or_missing_node"
        if path == "relation_types":
            return "wrong_relation_type"
    return "assertion_failed"


def run_file_contains_case(case: dict[str, Any], root: Path) -> dict[str, Any]:
    target = root / str(case["path"])
    content = target.read_text(encoding="utf-8")
    missing = [needle for needle in case.get("contains", []) if needle not in content]
    passed = len(missing) == 0
    return {
        "id": case["id"],
        "type": case["type"],
        "passed": passed,
        "target": str(target),
        "missing": missing,
        "detail": "all required strings present" if passed else f"missing strings: {missing}",
    }


def run_trace_review_case(case: dict[str, Any], suite_dir: Path, root: Path) -> dict[str, Any]:
    trace_path = suite_dir / str(case["trace_fixture"])
    review_script = root / "tools" / "agents" / "agent_review.py"
    with tempfile.TemporaryDirectory(prefix="workflow-evals-") as temp_dir:
        temp = Path(temp_dir)
        json_out = temp / "review.json"
        markdown_out = temp / "review.md"
        history_out = temp / "review-history.jsonl"
        completed = subprocess.run(
            [
                sys.executable,
                str(review_script),
                "--trace-path",
                str(trace_path),
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
            return {
                "id": case["id"],
                "type": case["type"],
                "passed": False,
                "detail": "agent_review.py execution failed",
                "stdout": completed.stdout,
                "stderr": completed.stderr,
            }
        payload = read_json(json_out)
        passed, assertion_results = evaluate_assertions(payload, case.get("assertions", []))
        return {
            "id": case["id"],
            "type": case["type"],
            "passed": passed,
            "trace_path": str(trace_path),
            "detail": "all assertions passed" if passed else "one or more assertions failed",
            "assertions": assertion_results,
            "review_status": payload.get("status"),
        }


def run_runtime_delegate_case(case: dict[str, Any], suite_dir: Path, root: Path) -> dict[str, Any]:
    """Run a real delegate.py spawn → complete → audit roundtrip to prove the runtime path works.

    This goes beyond fixture-only regression: it exercises the actual CLI tool
    so changes to delegate.py that silently break the protocol surface here.
    """
    delegate_script = root / "tools" / "agents" / "delegate.py"
    uv = find_uv()

    with tempfile.TemporaryDirectory(prefix="delegate-eval-") as temp_dir:
        temp = Path(temp_dir)
        trace_path = temp / "runtime-test-trace.jsonl"
        task_id = str(case.get("task_id", "runtime-eval-task"))

        def run_step(step_args: list[str], step_name: str) -> dict[str, Any] | None:
            result = subprocess.run(
                [uv, "run", "--python", "3.12", str(delegate_script)] + step_args,
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode not in (0, 1):  # 1 is acceptable for audit with open tasks
                return {
                    "id": case["id"],
                    "type": case["type"],
                    "passed": False,
                    "detail": f"{step_name} exited {result.returncode}",
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                }
            return None

        common = ["--trace-path", str(trace_path)]

        # Step 1: declare session expectation (denominator = 1)
        err = run_step(["session-expectation"] + common + ["--expected-delegations", "1"], "session-expectation")
        if err:
            return err

        # Step 2: spawn
        spawn_args = case.get("spawn_args") or [
            "--task-id", task_id,
            "--agent-type", "explore",
            "--model", "claude-haiku-4.5",
            "--note", "runtime eval roundtrip",
        ]
        err = run_step(["spawn"] + common + spawn_args, "spawn")
        if err:
            return err

        # Step 3: complete
        complete_args = case.get("complete_args") or ["--task-id", task_id, "--dod-met", "true"]
        err = run_step(["complete"] + common + complete_args, "complete")
        if err:
            return err

        # Step 4: audit — must exit 0 (no open tasks, gap = 0)
        audit_result = subprocess.run(
            [uv, "run", "--python", "3.12", str(delegate_script), "audit"] + common,
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        audit_ok = audit_result.returncode == 0

        # Step 5: run agent_review and check coverage verdict
        review_script = root / "tools" / "agents" / "agent_review.py"
        json_out = temp / "review.json"
        markdown_out = temp / "review.md"
        history_out = temp / "review-history.jsonl"
        review_result = subprocess.run(
            [
                sys.executable, str(review_script),
                "--trace-path", str(trace_path),
                "--json-out", str(json_out),
                "--markdown-out", str(markdown_out),
                "--history-out", str(history_out),
            ],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        if review_result.returncode != 0:
            return {
                "id": case["id"],
                "type": case["type"],
                "passed": False,
                "detail": "agent_review.py failed during runtime eval",
                "stdout": review_result.stdout,
                "stderr": review_result.stderr,
            }

        review_payload = read_json(json_out)
        passed, assertion_results = evaluate_assertions(review_payload, case.get("assertions", []))
        all_passed = passed and audit_ok

        return {
            "id": case["id"],
            "type": case["type"],
            "passed": all_passed,
            "detail": "runtime roundtrip passed" if all_passed else (
                f"audit_exit={audit_result.returncode}, review_status={review_payload.get('status')}, "
                f"coverage={review_payload.get('coverage_verdict')}"
            ),
            "assertions": assertion_results,
            "audit_exit": audit_result.returncode,
            "review_status": review_payload.get("status"),
            "coverage_verdict": review_payload.get("coverage_verdict"),
        }


def run_runtime_cao_helper_case(case: dict[str, Any], suite_dir: Path, root: Path) -> dict[str, Any]:
    helper_script = root / "tools" / "agents" / "cao_helper.py"
    delegate_script = root / "tools" / "agents" / "delegate.py"
    review_script = root / "tools" / "agents" / "agent_review.py"
    uv = find_uv()

    with tempfile.TemporaryDirectory(prefix="cao-helper-eval-") as temp_dir:
        temp = Path(temp_dir)
        trace_path = temp / "cao-helper-trace.jsonl"
        prepare_args = list(case.get("prepare_args", []))
        if "--json" not in prepare_args:
            prepare_args.append("--json")
        prepare_result = subprocess.run(
            [uv, "run", "--python", "3.12", str(helper_script), "prepare"] + prepare_args,
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        expected_prepare_exit = int(case.get("prepare_exit_code", 0))
        if prepare_result.returncode != expected_prepare_exit:
            return {
                "id": case["id"],
                "type": case["type"],
                "passed": False,
                "detail": f"prepare exited {prepare_result.returncode}, expected {expected_prepare_exit}",
                "stdout": prepare_result.stdout,
                "stderr": prepare_result.stderr,
            }
        try:
            prepare_payload = json.loads(prepare_result.stdout)
        except json.JSONDecodeError as exc:
            return {
                "id": case["id"],
                "type": case["type"],
                "passed": False,
                "detail": f"prepare did not return JSON: {exc}",
                "stdout": prepare_result.stdout,
                "stderr": prepare_result.stderr,
            }
        prepare_passed, prepare_assertions = evaluate_assertions(
            prepare_payload,
            case.get("prepare_assertions", []),
        )
        if not case.get("spawn_after_prepare"):
            return {
                "id": case["id"],
                "type": case["type"],
                "passed": prepare_passed,
                "detail": "prepare assertions passed" if prepare_passed else "prepare assertions failed",
                "assertions": prepare_assertions,
            }

        expectation = subprocess.run(
            [
                uv,
                "run",
                "--python",
                "3.12",
                str(delegate_script),
                "session-expectation",
                "--trace-path",
                str(trace_path),
                "--expected-delegations",
                "1",
            ],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        if expectation.returncode != 0:
            return {
                "id": case["id"],
                "type": case["type"],
                "passed": False,
                "detail": "session expectation failed",
                "stdout": expectation.stdout,
                "stderr": expectation.stderr,
            }

        spawn_args = list(case.get("spawn_args", case.get("prepare_args", [])))
        spawn_result = subprocess.run(
            [
                uv,
                "run",
                "--python",
                "3.12",
                str(helper_script),
                "spawn",
                "--trace-path",
                str(trace_path),
            ] + spawn_args,
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        if spawn_result.returncode != 0:
            return {
                "id": case["id"],
                "type": case["type"],
                "passed": False,
                "detail": f"spawn exited {spawn_result.returncode}",
                "stdout": spawn_result.stdout,
                "stderr": spawn_result.stderr,
            }

        task_id = str(case["task_id"])
        complete_result = subprocess.run(
            [
                uv,
                "run",
                "--python",
                "3.12",
                str(delegate_script),
                "complete",
                "--trace-path",
                str(trace_path),
                "--task-id",
                task_id,
                "--dod-met",
                "true",
            ],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        if complete_result.returncode != 0:
            return {
                "id": case["id"],
                "type": case["type"],
                "passed": False,
                "detail": "complete step failed",
                "stdout": complete_result.stdout,
                "stderr": complete_result.stderr,
            }

        audit_result = subprocess.run(
            [uv, "run", "--python", "3.12", str(delegate_script), "audit", "--trace-path", str(trace_path)],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        if audit_result.returncode != 0:
            return {
                "id": case["id"],
                "type": case["type"],
                "passed": False,
                "detail": f"audit exited {audit_result.returncode}",
                "stdout": audit_result.stdout,
                "stderr": audit_result.stderr,
            }

        json_out = temp / "review.json"
        markdown_out = temp / "review.md"
        history_out = temp / "review-history.jsonl"
        review_result = subprocess.run(
            [
                sys.executable,
                str(review_script),
                "--trace-path",
                str(trace_path),
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
        if review_result.returncode != 0:
            return {
                "id": case["id"],
                "type": case["type"],
                "passed": False,
                "detail": "agent review failed",
                "stdout": review_result.stdout,
                "stderr": review_result.stderr,
            }
        review_payload = read_json(json_out)
        review_passed, review_assertions = evaluate_assertions(
            review_payload,
            case.get("review_assertions", []),
        )
        passed = prepare_passed and review_passed
        return {
            "id": case["id"],
            "type": case["type"],
            "passed": passed,
            "detail": "cao helper runtime passed" if passed else "cao helper runtime assertions failed",
            "prepare_assertions": prepare_assertions,
            "review_assertions": review_assertions,
            "review_status": review_payload.get("status"),
            "coverage_verdict": review_payload.get("coverage_verdict"),
        }


def find_powershell() -> str:
    return (
        shutil.which("pwsh")
        or shutil.which("powershell")
        or r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
    )


def run_runtime_session_delegation_case(case: dict[str, Any], suite_dir: Path, root: Path) -> dict[str, Any]:
    request_script = root / "tools" / "session" / "request-delegation.ps1"
    delegate_script = root / "tools" / "agents" / "delegate.py"
    review_script = root / "tools" / "agents" / "agent_review.py"
    powershell = find_powershell()
    uv = find_uv()

    with tempfile.TemporaryDirectory(prefix="session-delegation-eval-") as temp_dir:
        temp = Path(temp_dir)
        trace_path = temp / "session-delegation-trace.jsonl"
        request_args = list(case.get("request_args", []))
        request_result = subprocess.run(
            [
                powershell,
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(request_script),
                "-VaultRoot",
                str(root),
                "-TracePath",
                str(trace_path),
                "-SkipLifecycleHistory",
            ] + request_args,
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        if request_result.returncode != 0:
            return {
                "id": case["id"],
                "type": case["type"],
                "passed": False,
                "detail": f"request-delegation exited {request_result.returncode}",
                "stdout": request_result.stdout,
                "stderr": request_result.stderr,
            }

        task_id = str(case["task_id"])
        complete_result = subprocess.run(
            [
                uv,
                "run",
                "--python",
                "3.12",
                str(delegate_script),
                "complete",
                "--trace-path",
                str(trace_path),
                "--task-id",
                task_id,
                "--dod-met",
                "true",
            ],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        if complete_result.returncode != 0:
            return {
                "id": case["id"],
                "type": case["type"],
                "passed": False,
                "detail": "complete step failed",
                "stdout": complete_result.stdout,
                "stderr": complete_result.stderr,
            }

        audit_result = subprocess.run(
            [uv, "run", "--python", "3.12", str(delegate_script), "audit", "--trace-path", str(trace_path)],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        if audit_result.returncode != 0:
            return {
                "id": case["id"],
                "type": case["type"],
                "passed": False,
                "detail": f"audit exited {audit_result.returncode}",
                "stdout": audit_result.stdout,
                "stderr": audit_result.stderr,
            }

        json_out = temp / "review.json"
        markdown_out = temp / "review.md"
        history_out = temp / "review-history.jsonl"
        review_result = subprocess.run(
            [
                sys.executable,
                str(review_script),
                "--trace-path",
                str(trace_path),
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
        if review_result.returncode != 0:
            return {
                "id": case["id"],
                "type": case["type"],
                "passed": False,
                "detail": "agent review failed",
                "stdout": review_result.stdout,
                "stderr": review_result.stderr,
            }

        review_payload = read_json(json_out)
        passed, assertion_results = evaluate_assertions(
            review_payload,
            case.get("assertions", []),
        )
        return {
            "id": case["id"],
            "type": case["type"],
            "passed": passed,
            "detail": "session delegation runtime passed" if passed else "session delegation assertions failed",
            "assertions": assertion_results,
            "review_status": review_payload.get("status"),
            "coverage_verdict": review_payload.get("coverage_verdict"),
            "request_stdout": request_result.stdout.strip(),
        }


def run_retrieval_probe_case(case: dict[str, Any], suite_dir: Path, root: Path) -> dict[str, Any]:
    probe_script = root / "tools" / "wiki" / "retrieval_probe.py"
    uv = find_uv()
    # Persist artifact alongside the suite for reviewability — no temp-dir discard.
    artifact_dir = suite_dir / "artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    json_out = artifact_dir / f"{case['id']}-latest.json"

    # --json-out must come before the subcommand; retrieval_probe.py defines it on the main parser
    command = [uv, "run", "--python", "3.12", str(probe_script), "--json-out", str(json_out)]
    if case.get("strict"):
        command.append("--strict")
    if case.get("index_dir"):
        # Resolve relative to repo root so suite.json can use repo-relative paths.
        command.extend(["--index-dir", str(root / case["index_dir"])])
    command.append(case["probe_kind"])
    if case["probe_kind"] == "search":
        command.extend(["--query", str(case["query"]), "--top", str(int(case.get("top", 5)))])
    elif case["probe_kind"] == "neighbors":
        command.extend(["--page-id", str(case["page_id"])])
    else:
        raise ValueError(f"Unsupported probe kind: {case['probe_kind']}")
    completed = subprocess.run(
        command,
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    # Exit code 2 means the probe ran but reported probe_ok=False (stale index/graph).
    # Exit code != 0 and != 2 means the subprocess crashed before producing output.
    if completed.returncode not in (0, 2):
        return {
            "id": case["id"],
            "type": case["type"],
            "passed": False,
            "failure_class": "probe_execution_failed",
            "detail": "retrieval probe execution failed",
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
    if not json_out.exists():
        return {
            "id": case["id"],
            "type": case["type"],
            "passed": False,
            "failure_class": "probe_execution_failed",
            "detail": "retrieval probe produced no output file",
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
    payload = read_json(json_out)

    # Probe reported a structural failure (stale index/graph, missing node, setup error).
    # If the case declared expected_failure_class, a matching failure is the correct outcome.
    if not payload.get("probe_ok", True):
        actual_fc = str(payload.get("failure_class", "probe_reported_failure"))
        expected_fc = case.get("expected_failure_class")
        if expected_fc and actual_fc == expected_fc:
            return {
                "id": case["id"],
                "type": case["type"],
                "passed": True,
                "detail": f"probe correctly reported failure_class={actual_fc}",
                "failure_class": actual_fc,
                "probe_kind": payload.get("probe_kind"),
                "artifact_path": str(json_out),
            }
        detail = f"probe reported failure: {actual_fc}"
        if expected_fc:
            detail += f" (expected {expected_fc})"
        return {
            "id": case["id"],
            "type": case["type"],
            "passed": False,
            "failure_class": actual_fc,
            "detail": detail,
            "stale_reasons": payload.get("stale_reasons", []),
            "probe_kind": payload.get("probe_kind"),
            "artifact_path": str(json_out),
        }

    # probe_ok=True but the case expected a specific failure — that is itself a failure.
    expected_fc = case.get("expected_failure_class")
    if expected_fc:
        return {
            "id": case["id"],
            "type": case["type"],
            "passed": False,
            "failure_class": "unexpected_probe_success",
            "detail": f"expected probe failure_class={expected_fc} but probe succeeded",
            "probe_kind": payload.get("probe_kind"),
            "result_count": payload.get("result_count"),
            "artifact_path": str(json_out),
        }

    passed, assertion_results = evaluate_assertions(payload, case.get("assertions", []))
    failure_class = classify_assertion_failure(assertion_results, payload) if not passed else None
    result: dict[str, Any] = {
        "id": case["id"],
        "type": case["type"],
        "passed": passed,
        "detail": "all assertions passed" if passed else f"assertion failed: {failure_class}",
        "assertions": assertion_results,
        "probe_kind": payload.get("probe_kind"),
        "top_hit_file": payload.get("top_hit_file"),
        "result_count": payload.get("result_count"),
        "artifact_path": str(json_out),
    }
    if failure_class:
        result["failure_class"] = failure_class
    return result


def run_trace_audit_case(case: dict[str, Any], suite_dir: Path, root: Path) -> dict[str, Any]:
    """Run `delegate.py audit --trace-path <fixture>` and check exit code + stdout."""
    trace_path = suite_dir / str(case["trace_fixture"])
    delegate_script = root / "tools" / "agents" / "delegate.py"
    uv = find_uv()
    completed = subprocess.run(
        [uv, "run", "--python", "3.12", str(delegate_script), "audit", "--trace-path", str(trace_path)],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    payload: dict[str, Any] = {
        "exit_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }
    passed, assertion_results = evaluate_assertions(payload, case.get("assertions", []))
    return {
        "id": case["id"],
        "type": case["type"],
        "passed": passed,
        "trace_path": str(trace_path),
        "detail": "all assertions passed" if passed else "one or more assertions failed",
        "assertions": assertion_results,
        "exit_code": completed.returncode,
        "stdout": completed.stdout.strip(),
    }


def run_runtime_delegate_spawn_validation_case(case: dict[str, Any], suite_dir: Path, root: Path) -> dict[str, Any]:
    """Run delegate.py spawn with intentionally incomplete args; assert exit code and stderr content.

    Each entry in ``scenarios`` is exercised independently.  The case passes only
    when every scenario passes.  This ensures that removing the ``_validate_spawn``
    guard in delegate.py would be caught immediately.
    """
    delegate_script = root / "tools" / "agents" / "delegate.py"
    uv = find_uv()
    scenario_results: list[dict[str, Any]] = []
    all_passed = True

    with tempfile.TemporaryDirectory(prefix="spawn-val-eval-") as temp_dir:
        trace_path = Path(temp_dir) / "validation-test-trace.jsonl"

        for scenario in case.get("scenarios", []):
            label = scenario.get("label", "unnamed")
            extra_args: list[str] = scenario.get("spawn_args", [])
            completed = subprocess.run(
                [uv, "run", "--python", "3.12", str(delegate_script), "spawn",
                 "--trace-path", str(trace_path)] + extra_args,
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )
            payload: dict[str, Any] = {
                "exit_code": completed.returncode,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
            }
            passed, assertion_results = evaluate_assertions(payload, scenario.get("assertions", []))
            all_passed = all_passed and passed
            scenario_results.append({
                "label": label,
                "passed": passed,
                "exit_code": completed.returncode,
                "assertions": assertion_results,
                "stderr_snippet": completed.stderr.strip()[:300],
            })

    return {
        "id": case["id"],
        "type": case["type"],
        "passed": all_passed,
        "detail": "all scenarios passed" if all_passed else "one or more scenarios failed",
        "scenarios": scenario_results,
    }


def run_case(case: dict[str, Any], suite_dir: Path, root: Path) -> dict[str, Any]:
    case_type = str(case["type"])
    if case_type == "file_contains":
        return run_file_contains_case(case, root)
    if case_type == "trace_review":
        return run_trace_review_case(case, suite_dir, root)
    if case_type == "retrieval_probe":
        return run_retrieval_probe_case(case, suite_dir, root)
    if case_type == "runtime_delegate_audit":
        return run_runtime_delegate_case(case, suite_dir, root)
    if case_type == "runtime_cao_helper":
        return run_runtime_cao_helper_case(case, suite_dir, root)
    if case_type == "runtime_session_delegation":
        return run_runtime_session_delegation_case(case, suite_dir, root)
    if case_type == "trace_audit":
        return run_trace_audit_case(case, suite_dir, root)
    if case_type == "runtime_delegate_spawn_validation":
        return run_runtime_delegate_spawn_validation_case(case, suite_dir, root)
    raise ValueError(f"Unsupported case type: {case_type}")


def load_suites(root: Path) -> list[tuple[Path, dict[str, Any]]]:
    suites: list[tuple[Path, dict[str, Any]]] = []
    for suite_path in sorted((root / "evals").glob("*/suite.json")):
        suites.append((suite_path.parent, read_json(suite_path)))
    return suites


def suite_summary(results: list[dict[str, Any]]) -> dict[str, int]:
    total_cases = sum(len(suite["cases"]) for suite in results)
    passed_cases = sum(1 for suite in results for case in suite["cases"] if case["passed"])
    failed_cases = total_cases - passed_cases
    passed_suites = sum(1 for suite in results if suite["passed"])
    failed_suites = len(results) - passed_suites
    return {
        "suite_count": len(results),
        "case_count": total_cases,
        "passed_suites": passed_suites,
        "failed_suites": failed_suites,
        "passed_cases": passed_cases,
        "failed_cases": failed_cases,
    }


def build_review_payload(suites: list[dict[str, Any]]) -> dict[str, Any]:
    capability = [suite for suite in suites if suite["mode"] == "capability"]
    regression = [suite for suite in suites if suite["mode"] == "regression"]
    capability_summary = suite_summary(capability)
    regression_summary = suite_summary(regression)
    overall_summary = suite_summary(suites)
    failing_cases = [
        {
            "suite": suite["name"],
            "case": case["id"],
            "detail": case["detail"],
            "failure_class": case.get("failure_class"),
        }
        for suite in suites
        for case in suite["cases"]
        if not case["passed"]
    ]

    status = "ok"
    reasons: list[str] = []
    actions: list[str] = []

    if regression_summary["failed_cases"] > 0:
        status = "degraded"
        reasons.append("regression-evals-failed")
        actions.append("Fix failing regression suites before trusting workflow changes or moving to ablation.")
    elif capability_summary["failed_cases"] > 0:
        status = "warn"
        reasons.append("capability-evals-failed")
        actions.append("Review capability coverage gaps before expanding workflow scope.")

    if overall_summary["suite_count"] < 4:
        status = "warn" if status == "ok" else status
        reasons.append("workflow-eval-suite-count-below-four")
        actions.append("Keep at least four private workflow suites active: research synthesis, handoff, trace quality, and hypothesis discipline.")

    if not actions:
        actions.append("Workflow eval harness is healthy. Keep running capability and regression suites before optimization work.")

    return {
        "created": now_iso(),
        "status": status,
        "summary": {
            "overall": overall_summary,
            "capability": capability_summary,
            "regression": regression_summary,
        },
        "reasons": reasons,
        "actions": actions,
        "failing_cases": failing_cases,
        "suites": suites,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    overall = payload["summary"]["overall"]
    capability = payload["summary"]["capability"]
    regression = payload["summary"]["regression"]
    lines = [
        "---",
        f"created: {payload['created']}",
        "kind: workflow-eval-review",
        "---",
        "",
        "# Workflow eval review",
        "",
        f"- **Status:** {payload['status']}",
        f"- **Reasons:** {', '.join(payload['reasons']) if payload['reasons'] else 'none'}",
        "",
        "## Summary",
        "",
        f"- **Suites:** {overall['suite_count']}",
        f"- **Cases:** {overall['case_count']}",
        f"- **Passed suites:** {overall['passed_suites']}",
        f"- **Failed suites:** {overall['failed_suites']}",
        f"- **Passed cases:** {overall['passed_cases']}",
        f"- **Failed cases:** {overall['failed_cases']}",
        "",
        "## Eval modes",
        "",
        f"- **Capability suites:** {capability['suite_count']} ({capability['passed_cases']}/{capability['case_count']} cases passed)",
        f"- **Regression suites:** {regression['suite_count']} ({regression['passed_cases']}/{regression['case_count']} cases passed)",
        "",
        "## Actions",
        "",
    ]
    lines.extend(f"- {action}" for action in payload["actions"])
    lines.extend(["", "## Suite results", ""])
    for suite in payload["suites"]:
        lines.append(f"### {suite['name']} ({suite['mode']})")
        lines.append("")
        lines.append(f"- **Status:** {'pass' if suite['passed'] else 'fail'}")
        lines.append(f"- **Description:** {suite['description']}")
        for case in suite["cases"]:
            lines.append(f"- **{case['id']}:** {'pass' if case['passed'] else 'fail'} — {case['detail']}")
        lines.append("")
    if payload["failing_cases"]:
        lines.extend(["## Failing cases", ""])
        for item in payload["failing_cases"]:
            fc = f" [{item['failure_class']}]" if item.get("failure_class") else ""
            lines.append(f"- **{item['suite']} / {item['case']}:{fc}** {item['detail']}")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    root = repo_root()
    reviews_dir = root / "memory" / "reviews"
    parser = argparse.ArgumentParser(description="Run private workflow eval suites and write a repeatable review.")
    parser.add_argument("--mode", choices=("all", "capability", "regression"), default="all")
    parser.add_argument("--suite", help="Optional suite name filter")
    parser.add_argument("--json-out", type=Path, default=reviews_dir / "workflow-eval-review.json")
    parser.add_argument("--markdown-out", type=Path, default=reviews_dir / "workflow-eval-review.md")
    parser.add_argument("--history-out", type=Path, default=reviews_dir / "workflow-eval-history.jsonl")
    args = parser.parse_args()

    suites: list[dict[str, Any]] = []
    for suite_dir, suite in load_suites(root):
        if args.mode != "all" and suite["mode"] != args.mode:
            continue
        if args.suite and suite["name"] != args.suite:
            continue
        case_results = [run_case(case, suite_dir, root) for case in suite.get("cases", [])]
        suites.append(
            {
                "name": suite["name"],
                "mode": suite["mode"],
                "description": suite["description"],
                "passed": all(case["passed"] for case in case_results),
                "cases": case_results,
            }
        )

    payload = build_review_payload(suites)
    write_json(args.json_out, payload)
    atomic_write(args.markdown_out, render_markdown(payload))
    append_jsonl(
        args.history_out,
        {
            "timestamp": payload["created"],
            "status": payload["status"],
            "overall": payload["summary"]["overall"],
            "capability": payload["summary"]["capability"],
            "regression": payload["summary"]["regression"],
            "reasons": payload["reasons"],
        },
    )

    print(f"STATUS: {payload['status']}")
    print(f"JSON: {args.json_out}")
    print(f"MARKDOWN: {args.markdown_out}")
    print(f"SUITES: {payload['summary']['overall']['suite_count']}")
    print(f"CASES: {payload['summary']['overall']['case_count']}")
    print(f"FAILED_CASES: {payload['summary']['overall']['failed_cases']}")
    return 0 if payload["status"] != "degraded" else 1


if __name__ == "__main__":
    raise SystemExit(main())
