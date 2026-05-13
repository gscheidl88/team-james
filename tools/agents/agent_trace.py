#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""
agent_trace.py - Track sub-agent lifecycle events in a local JSONL file.

Usage:
    uv run tools/agents/agent_trace.py spawn --task-id example --agent-id worker-1 --agent-type general-purpose
    uv run tools/agents/agent_trace.py checkpoint --task-id example --note "first review"
    uv run tools/agents/agent_trace.py complete --task-id example --dod-met true
    uv run tools/agents/agent_trace.py status
"""

from __future__ import annotations

import argparse
import json
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TERMINAL_EVENTS = {"complete", "failed", "cancelled", "blocked", "absorbed"}


@dataclass
class TraceEntry:
    timestamp: str
    event: str
    task_id: str
    agent_id: str | None
    agent_name: str | None
    agent_type: str | None
    model: str | None
    status: str | None
    dod_met: bool | None
    note: str | None
    metadata: dict[str, Any]

    def to_json(self) -> str:
        payload = OrderedDict(
            timestamp=self.timestamp,
            event=self.event,
            task_id=self.task_id,
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            agent_type=self.agent_type,
            model=self.model,
            status=self.status,
            dod_met=self.dod_met,
            note=self.note,
            metadata=self.metadata,
        )
        return json.dumps(payload, ensure_ascii=True)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def default_trace_path() -> Path:
    return Path(__file__).resolve().parents[2] / ".agent-trace.jsonl"


def append_entry(path: Path, entry: TraceEntry) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(entry.to_json())
        handle.write("\n")


def parse_metadata(values: list[str]) -> dict[str, Any]:
    metadata: dict[str, Any] = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"Metadata must use key=value format: {value}")
        key, raw = value.split("=", 1)
        metadata[key] = raw
    return metadata


def coerce_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def read_entries(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    entries: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            entries.append(json.loads(line))
    return entries


def latest_by_task(entries: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for entry in entries:
        latest[entry["task_id"]] = entry
    return latest


def command_log(args: argparse.Namespace, event: str) -> int:
    entry = TraceEntry(
        timestamp=utc_now(),
        event=event,
        task_id=args.task_id,
        agent_id=args.agent_id,
        agent_name=args.agent_name,
        agent_type=args.agent_type,
        model=args.model,
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


def command_status(args: argparse.Namespace) -> int:
    entries = read_entries(args.trace_path)
    latest = latest_by_task(entries)
    open_tasks = [
        entry
        for entry in latest.values()
        if entry.get("event") not in TERMINAL_EVENTS
    ]
    open_hypothesis_count = 0
    hypothesis_update_count = 0
    open_failure_classes: dict[str, int] = {}
    failure_update_count = 0
    for entry in entries:
        if entry.get("event") == "hypothesis_update":
            hypothesis_update_count += 1
        if entry.get("event") == "failure_update":
            failure_update_count += 1
    for entry in open_tasks:
        metadata = entry.get("metadata") or {}
        open_hypothesis_count += coerce_int(metadata.get("open_hypotheses"))
        failure_class = str(metadata.get("failure_class") or "").strip()
        if failure_class:
            open_failure_classes[failure_class] = open_failure_classes.get(failure_class, 0) + 1

    status = "ok" if not open_tasks else "warn"
    payload = {
        "status": status,
        "trace_path": str(args.trace_path),
        "entry_count": len(entries),
        "open_task_count": len(open_tasks),
        "open_hypothesis_count": open_hypothesis_count,
        "hypothesis_update_count": hypothesis_update_count,
        "failure_update_count": failure_update_count,
        "open_failure_classes": open_failure_classes,
        "open_tasks": open_tasks,
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=True))
        return 0

    print(f"STATUS: {status}")
    print(f"TRACE_PATH: {args.trace_path}")
    print(f"ENTRY_COUNT: {len(entries)}")
    print(f"OPEN_TASKS: {len(open_tasks)}")
    print(f"OPEN_HYPOTHESES: {open_hypothesis_count}")
    print(f"HYPOTHESIS_UPDATES: {hypothesis_update_count}")
    print(f"FAILURE_UPDATES: {failure_update_count}")
    if open_failure_classes:
        print(f"OPEN_FAILURE_CLASSES: {json.dumps(open_failure_classes, ensure_ascii=True)}")
    for task in open_tasks:
        task_metadata = task.get("metadata") or {}
        task_model = task.get("model") or task_metadata.get("primary_model")
        print(
            "OPEN_TASK: "
            f"{task.get('task_id')} | event={task.get('event')} | "
            f"agent_id={task.get('agent_id')} | model={task_model} | "
            f"note={task.get('note')}"
        )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Track and inspect sub-agent lifecycle events.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_log_parser(name: str) -> argparse.ArgumentParser:
        subparser = subparsers.add_parser(name)
        subparser.add_argument(
            "--trace-path",
            type=Path,
            default=default_trace_path(),
            help="Path to the JSONL trace file.",
        )
        subparser.add_argument("--task-id", required=True)
        subparser.add_argument("--agent-id")
        subparser.add_argument("--agent-name")
        subparser.add_argument("--agent-type")
        subparser.add_argument("--model")
        subparser.add_argument("--status")
        subparser.add_argument("--dod-met", type=lambda value: value.lower() == "true")
        subparser.add_argument("--note")
        subparser.add_argument("--metadata", action="append", default=[])
        return subparser

    for event_name in ("spawn", "checkpoint", "hypothesis_update", "failure_update", "complete", "stall", "failed", "cancelled", "blocked", "absorbed"):
        add_log_parser(event_name)

    status_parser = subparsers.add_parser("status")
    status_parser.add_argument(
        "--trace-path",
        type=Path,
        default=default_trace_path(),
        help="Path to the JSONL trace file.",
    )
    status_parser.add_argument("--json", action="store_true")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "status":
        return command_status(args)

    return command_log(args, args.command)


if __name__ == "__main__":
    raise SystemExit(main())
