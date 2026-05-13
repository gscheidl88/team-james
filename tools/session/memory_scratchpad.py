#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""
memory_scratchpad.py - transient working-memory helper for Copilot session state.

Usage:
    uv run tools/session/memory_scratchpad.py init --session-root <path> [--task "text"]
    uv run tools/session/memory_scratchpad.py append --session-root <path> --section decisions --text "text"
    uv run tools/session/memory_scratchpad.py finalize --session-root <path> [--daily-note <path>]
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path

SECTIONS: dict[str, str] = {
    "current-task": "Current task",
    "changes": "Changes",
    "notes": "Notes",
    "hypotheses": "Hypotheses",
    "decisions": "Decisions",
    "conflicts": "Conflicts",
    "uncertainties": "Uncertainties",
    "lessons": "Lessons",
    "candidates": "Candidate durable updates",
}

SECTION_KEYS = tuple(SECTIONS.keys())
DIGEST_START = "<!-- memory-scratchpad-digest:start -->"
DIGEST_END = "<!-- memory-scratchpad-digest:end -->"


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(content, encoding="utf-8")
    temp.replace(path)


def session_files_dir(session_root: Path) -> Path:
    return session_root / "files"


def scratchpad_path(session_root: Path) -> Path:
    return session_files_dir(session_root) / "memory-scratchpad.md"


def candidates_path(session_root: Path) -> Path:
    return session_files_dir(session_root) / "memory-candidates.md"


def candidates_json_path(session_root: Path) -> Path:
    return session_files_dir(session_root) / "memory-candidates.json"


def scratchpad_template(task: str | None = None) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    task_line = task or ""
    blocks = [
        "---",
        f"created: {timestamp}",
        "status: active",
        "kind: transient-working-memory",
        "---",
        "",
        "# Session memory scratchpad",
        "",
        "Use this file for in-flight reasoning only. Promote stable insights during finalization.",
        "",
        "## Current task",
        "",
        f"- {task_line}" if task_line else "",
        "",
    ]
    for key, title in list(SECTIONS.items())[1:]:
        blocks.extend([f"## {title}", "", ""])
    return "\n".join(blocks).rstrip() + "\n"


def ensure_scratchpad(session_root: Path, task: str | None = None) -> Path:
    path = scratchpad_path(session_root)
    if not path.exists():
        atomic_write(path, scratchpad_template(task))
    return path


def parse_sections(text: str) -> dict[str, list[str]]:
    section_map: dict[str, list[str]] = {key: [] for key in SECTION_KEYS}
    pattern = re.compile(r"^## (?P<title>.+?)\n(?P<body>.*?)(?=^## |\Z)", re.M | re.S)
    title_to_key = {title: key for key, title in SECTIONS.items()}

    for match in pattern.finditer(text):
        title = match.group("title").strip()
        key = title_to_key.get(title)
        if not key:
            continue
        body = match.group("body")
        items = []
        for line in body.splitlines():
            stripped = line.strip()
            if re.match(r"^-\s+\S", stripped):
                items.append(re.sub(r"^-\s+", "", stripped).strip())
        section_map[key] = [item for item in items if item]
    return section_map


def insert_bullet_under_section(text: str, heading: str, bullet: str) -> str:
    pattern = re.compile(rf"(^## {re.escape(heading)}\n)(?P<body>.*?)(?=^## |\Z)", re.M | re.S)
    match = pattern.search(text)
    if not match:
        return text.rstrip() + f"\n\n## {heading}\n\n- {bullet}\n"

    body = match.group("body")
    lines = body.splitlines()
    lines = [line for line in lines if line.strip()]
    insert_at = len(lines)
    lines.insert(insert_at, f"- {bullet}")
    new_block = match.group(1) + ("\n".join(lines) + "\n" if lines else "")
    return text[: match.start()] + new_block + text[match.end() :]


def append_to_scratchpad(session_root: Path, section: str, text: str) -> Path:
    if section not in SECTIONS:
        raise ValueError(f"Unknown section: {section}")
    path = ensure_scratchpad(session_root)
    current = path.read_text(encoding="utf-8")
    updated = insert_bullet_under_section(current, SECTIONS[section], text.strip())
    atomic_write(path, updated)
    return path


def build_candidates_payload(sections: dict[str, list[str]]) -> dict[str, object]:
    created = datetime.now().strftime("%Y-%m-%d %H:%M")
    current_task = sections["current-task"][0] if sections["current-task"] else "(not specified)"

    def proposal_lines(items: list[str], target: str, action: str, confidence: str, source_kind: str) -> list[dict[str, str]]:
        result = []
        for item in items:
            result.append(
                {
                    "source_kind": source_kind,
                    "confidence": confidence,
                    "action": action,
                    "target": target,
                    "text": item,
                }
            )
        return result

    proposals = (
        proposal_lines(sections["decisions"], "MEMORY.md", "merge", "medium", "decision")
        + proposal_lines(sections["lessons"], "procedures.md", "merge", "medium", "lesson")
        + proposal_lines(sections["conflicts"], "review", "review", "low", "conflict")
        + proposal_lines(sections["uncertainties"], "review", "review", "uncertain", "uncertainty")
        + proposal_lines(sections["candidates"], "memory/wiki", "review", "medium", "candidate")
    )

    return {
        "created": created,
        "kind": "memory-candidates",
        "current_task": current_task,
        "sections": sections,
        "proposals": proposals,
        "counts": {key: len(value) for key, value in sections.items()},
    }


def build_candidates_markdown(payload: dict[str, object]) -> str:
    sections = payload["sections"]
    proposals = payload["proposals"]
    body = [
        "---",
        f"created: {payload['created']}",
        "kind: memory-candidates",
        "---",
        "",
        "# Memory candidates",
        "",
        f"**Current task:** {payload['current_task']}",
        "",
        "## Daily note digest",
        "",
    ]

    digest_items = (
        [f"Change: {item}" for item in sections["changes"]]
        + [f"Decision: {item}" for item in sections["decisions"]]
        + [f"Conflict: {item}" for item in sections["conflicts"]]
        + [f"Uncertainty: {item}" for item in sections["uncertainties"]]
        + [f"Lesson: {item}" for item in sections["lessons"]]
        + [f"Candidate: {item}" for item in sections["candidates"]]
    )
    if digest_items:
        body.extend(f"- {item}" for item in digest_items)
    else:
        body.append("- No stable memory candidates captured.")

    body.extend(
        [
            "",
            "## Durable memory proposals",
            "",
        ]
    )

    if proposals:
        body.extend(
            f"- [{item['confidence']}] [{item['action']}] [{item['target']}] {item['text']}"
            for item in proposals
        )
    else:
        body.append("- No proposals.")

    body.extend(
        [
            "",
            "## Review checklist",
            "",
            "1. Retrieve related memory/wiki entries before durable write.",
            "2. Classify relation: compatible, contradictory, subsumes, independent, ignore.",
            "3. Downgrade or pause on stale, uncertain, or conflicting evidence.",
            "4. Promote only stable insights; leave temporary reasoning in the scratchpad history.",
            "",
        ]
    )

    return "\n".join(body)


def build_daily_digest_block(sections: dict[str, list[str]]) -> str:
    task = sections["current-task"][0] if sections["current-task"] else "(not specified)"
    lines = [
        DIGEST_START,
        "### Session scratchpad digest (auto)",
        "",
        f"- **Task:** {task}",
    ]
    for label, key in (
        ("Changes", "changes"),
        ("Decisions", "decisions"),
        ("Conflicts", "conflicts"),
        ("Uncertainties", "uncertainties"),
        ("Lessons", "lessons"),
        ("Candidates", "candidates"),
    ):
        for item in sections[key]:
            lines.append(f"- **{label}:** {item}")
    if lines[-1] == f"- **Task:** {task}":
        lines.append("- No durable candidates captured.")
    lines.extend(["", DIGEST_END])
    return "\n".join(lines)


def upsert_daily_digest(daily_note: Path, digest_block: str) -> None:
    if not daily_note.exists():
        return
    text = daily_note.read_text(encoding="utf-8")
    replacement = digest_block
    block_re = re.compile(
        rf"{re.escape(DIGEST_START)}.*?{re.escape(DIGEST_END)}",
        re.S,
    )
    if block_re.search(text):
        updated = block_re.sub(replacement, text)
        atomic_write(daily_note, updated)
        return

    section_re = re.compile(r"(^## 💬 Notes & Captures\s*$)", re.M)
    match = section_re.search(text)
    if not match:
        atomic_write(daily_note, text.rstrip() + "\n\n" + replacement + "\n")
        return

    insert_pos = text.find("\n", match.end())
    if insert_pos == -1:
        insert_pos = len(text)
    updated = text[: insert_pos + 1] + "\n" + replacement + "\n" + text[insert_pos + 1 :]
    atomic_write(daily_note, updated)


def finalize_scratchpad(session_root: Path, daily_note: Path | None = None) -> tuple[Path, Path, list[str]]:
    path = scratchpad_path(session_root)
    if not path.exists():
        raise FileNotFoundError(f"Scratchpad not found: {path}")
    sections = parse_sections(path.read_text(encoding="utf-8"))
    payload = build_candidates_payload(sections)
    candidates = build_candidates_markdown(payload)
    output = candidates_path(session_root)
    json_output = candidates_json_path(session_root)
    atomic_write(output, candidates)
    atomic_write(json_output, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    if daily_note:
        upsert_daily_digest(daily_note, build_daily_digest_block(sections))

    summary = []
    for key in ("changes", "decisions", "conflicts", "uncertainties", "lessons", "candidates"):
        summary.extend(sections[key])
    return output, json_output, summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage transient session memory scratchpads.")
    sub = parser.add_subparsers(dest="command", required=True)

    init_cmd = sub.add_parser("init", help="Initialize a scratchpad for a session")
    init_cmd.add_argument("--session-root", required=True, help="Session root path")
    init_cmd.add_argument("--task", help="Initial task description")

    append_cmd = sub.add_parser("append", help="Append an item to a scratchpad section")
    append_cmd.add_argument("--session-root", required=True, help="Session root path")
    append_cmd.add_argument("--section", required=True, choices=SECTION_KEYS)
    append_cmd.add_argument("--text", required=True, help="Bullet content")

    final_cmd = sub.add_parser("finalize", help="Finalize scratchpad into memory candidates")
    final_cmd.add_argument("--session-root", required=True, help="Session root path")
    final_cmd.add_argument("--daily-note", help="Optional daily note path for digest insertion")

    args = parser.parse_args()
    session_root = Path(args.session_root)

    if args.command == "init":
        path = ensure_scratchpad(session_root, args.task)
        print(f"INITIALIZED: {path}")
        return

    if args.command == "append":
        path = append_to_scratchpad(session_root, args.section, args.text)
        print(f"UPDATED: {path}")
        return

    if args.command == "finalize":
        daily_note = Path(args.daily_note) if args.daily_note else None
        output, json_output, summary = finalize_scratchpad(session_root, daily_note)
        print(f"CANDIDATES: {output}")
        print(f"CANDIDATES_JSON: {json_output}")
        print(f"SUMMARY_COUNT: {len(summary)}")
        return


if __name__ == "__main__":
    main()
