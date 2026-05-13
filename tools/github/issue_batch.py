#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""
issue_batch.py - Preview or create GitHub issues from machine-readable opportunity data.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class IssueDraft:
    opportunity_id: str
    title: str
    labels: list[str]
    body: str


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(content, encoding="utf-8")
    temp.replace(path)


def run_command(command: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd or repo_root(),
        capture_output=True,
        text=True,
        check=False,
    )


def default_input_path() -> Path:
    return repo_root() / "sources" / "agent-ecosystem" / "2026-04-25-opportunities.json"


def load_payload(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_labels(raw_labels: list[str]) -> list[str]:
    labels = [label.strip() for label in raw_labels if label.strip()]
    return sorted(dict.fromkeys(labels))


def build_issue_body(item: dict[str, Any], source_path: Path) -> str:
    lines = [
        "## Summary",
        "",
        str(item.get("summary") or "").strip(),
        "",
        "## Why now",
        "",
        str(item.get("why_now") or "").strip(),
        "",
        "## External signals",
        "",
    ]
    for signal in item.get("external_signals") or []:
        lines.append(f"- {signal}")
    lines.extend(["", "## Repo gap", ""])
    for gap in item.get("repo_gap") or []:
        lines.append(f"- {gap}")
    lines.extend(["", "## Proposed changes", ""])
    for change in item.get("proposed_changes") or []:
        lines.append(f"- {change}")
    lines.extend(["", "## Definition of Done", ""])
    for dod_item in item.get("definition_of_done") or []:
        lines.append(f"- {dod_item}")
    lines.extend(
        [
            "",
            "## Source data",
            "",
            f"- Opportunity ID: `{item.get('id')}`",
            f"- Source file: `{source_path.relative_to(repo_root())}`",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def build_drafts(payload: dict[str, Any], source_path: Path, status_filter: set[str]) -> list[IssueDraft]:
    drafts: list[IssueDraft] = []
    for item in payload.get("opportunities") or []:
        status = str(item.get("status") or "").strip()
        if status_filter and status not in status_filter:
            continue
        issue = item.get("issue") or {}
        drafts.append(
            IssueDraft(
                opportunity_id=str(item["id"]),
                title=str(issue.get("title") or item.get("title") or item["id"]),
                labels=parse_labels(issue.get("labels") or []),
                body=build_issue_body(item, source_path),
            )
        )
    return drafts


def render_preview(drafts: list[IssueDraft]) -> str:
    lines = [
        "# GitHub issue batch preview",
        "",
    ]
    if not drafts:
        lines.append("- No issue drafts matched the requested filter.")
        return "\n".join(lines) + "\n"
    for draft in drafts:
        lines.extend(
            [
                f"## {draft.title}",
                "",
                f"- **Opportunity ID:** `{draft.opportunity_id}`",
                f"- **Labels:** {', '.join(draft.labels) if draft.labels else 'none'}",
                "",
                draft.body,
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def detect_repo_slug() -> str | None:
    result = run_command(["git", "config", "--get", "remote.origin.url"])
    if result.returncode != 0:
        return None
    raw = (result.stdout or "").strip()
    if raw.endswith(".git"):
        raw = raw[:-4]
    if raw.startswith("https://github.com/"):
        return raw.removeprefix("https://github.com/")
    if raw.startswith("git@github.com:"):
        return raw.removeprefix("git@github.com:")
    return None


def gh_authenticated() -> tuple[bool, str]:
    result = run_command(["gh", "api", "user", "--jq", ".login"])
    if result.returncode == 0:
        return True, (result.stdout or result.stderr).strip()
    message = (result.stderr or result.stdout).strip()
    return False, message


def load_repo_labels(repo: str | None) -> set[str]:
    if not repo:
        return set()
    result = run_command(["gh", "label", "list", "--repo", repo, "--limit", "200", "--json", "name"])
    if result.returncode != 0:
        return set()
    try:
        payload = json.loads(result.stdout or "[]")
    except json.JSONDecodeError:
        return set()
    return {str(item.get("name")) for item in payload if item.get("name")}


def create_issues(drafts: list[IssueDraft], repo: str | None) -> tuple[list[str], list[str], list[str]]:
    created: list[str] = []
    failures: list[str] = []
    notes: list[str] = []
    known_labels = load_repo_labels(repo)
    for draft in drafts:
        command = ["gh", "issue", "create", "--title", draft.title, "--body", draft.body]
        if repo:
            command.extend(["--repo", repo])
        labels_to_apply = draft.labels if not known_labels else [label for label in draft.labels if label in known_labels]
        skipped_labels = [label for label in draft.labels if label not in labels_to_apply]
        for label in labels_to_apply:
            command.extend(["--label", label])
        result = run_command(command)
        if result.returncode == 0:
            created.append((result.stdout or result.stderr).strip())
            if skipped_labels:
                notes.append(f"{draft.title}: skipped missing labels [{', '.join(skipped_labels)}]")
        else:
            error = (result.stderr or result.stdout).strip()
            failures.append(f"{draft.title}: {error}")
    return created, failures, notes


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Preview or create GitHub issues from opportunity seed data.")
    parser.add_argument(
        "--input",
        type=Path,
        default=default_input_path(),
        help="JSON file containing opportunity seed data.",
    )
    parser.add_argument(
        "--mode",
        choices=["preview", "create"],
        default="preview",
        help="Preview issues or create them via gh.",
    )
    parser.add_argument(
        "--status",
        action="append",
        default=[],
        help="Opportunity status filter. Can be repeated. Defaults to selected and planned.",
    )
    parser.add_argument(
        "--repo",
        help="Optional owner/repo override for gh issue create.",
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=repo_root() / "plans" / "issue-batch-preview.md",
        help="Where to write the preview markdown.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    status_filter = set(args.status or ["selected", "planned"])
    input_path = args.input if args.input.is_absolute() else (repo_root() / args.input)
    payload = load_payload(input_path)
    drafts = build_drafts(payload, input_path, status_filter)
    preview = render_preview(drafts)
    atomic_write(args.markdown_out, preview)
    print(f"WROTE_PREVIEW: {args.markdown_out}")
    print(f"DRAFT_COUNT: {len(drafts)}")

    if args.mode == "preview":
        return 0

    repo = args.repo or detect_repo_slug()
    if repo:
        print(f"TARGET_REPO: {repo}")

    authenticated, message = gh_authenticated()
    if not authenticated:
        print("GH_AUTH: unavailable")
        print(message)
        return 2

    print(f"GH_AUTH: ok ({message})")
    created, failures, notes = create_issues(drafts, repo)
    print(f"CREATED_COUNT: {len(created)}")
    for item in created:
        print(f"CREATED: {item}")
    for item in notes:
        print(f"NOTE: {item}")
    if failures:
        for item in failures:
            print(f"FAILED: {item}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
