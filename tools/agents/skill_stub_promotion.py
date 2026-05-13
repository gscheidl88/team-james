#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""
skill_stub_promotion.py - Generate reviewable draft skill stubs from skill candidates.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Candidate:
    candidate_id: str
    score: int
    reason: str
    target_path: str
    summary: str
    evidence: list[dict[str, str]]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(content, encoding="utf-8")
    temp.replace(path)


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def windows_path(path: Path) -> str:
    return str(path).replace("/", "\\")


def load_candidates(path: Path) -> list[Candidate]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = []
    for item in payload.get("candidates") or []:
        rows.append(
            Candidate(
                candidate_id=str(item["id"]),
                score=int(item.get("score", 0)),
                reason=str(item.get("reason") or ""),
                target_path=str(item.get("target_path") or ""),
                summary=str(item.get("summary") or ""),
                evidence=list(item.get("evidence") or []),
            )
        )
    return rows


def select_candidates(
    candidates: list[Candidate],
    min_score: int,
    candidate_ids: set[str],
    select_all: bool,
) -> list[Candidate]:
    selected = [item for item in candidates if item.score >= min_score]
    if candidate_ids:
        selected = [item for item in selected if item.candidate_id in candidate_ids]
    elif not select_all:
        selected = selected[:3]
    return selected


def draft_slug(candidate: Candidate) -> str:
    return slugify(candidate.candidate_id)


def draft_dir(root: Path, draft_root: Path, candidate: Candidate) -> Path:
    return root / draft_root / draft_slug(candidate)


def render_skill_markdown(candidate: Candidate, draft_path: Path) -> str:
    title = candidate.candidate_id.replace("-", " ").title()
    evidence_lines = "\n".join(
        f"- `{item.get('source', 'unknown')}` — {item.get('text', '').strip()}"
        for item in candidate.evidence[:5]
    )
    return f"""---
name: {draft_slug(candidate)}
description: "{candidate.summary}"
agent: James
tools_required: [uv, powershell, review]
wiki_ref: "[[autonomic-tooling-pattern]]"
version: "0.1-draft"
status: draft
review_required: true
source_candidate: "{candidate.candidate_id}"
---

# Skill Draft: {title}

**Category:** Draft  
**Trigger:** Review required before canonical adoption  
**Owner:** James (CAO)

---

## Purpose

{candidate.summary}

---

## Why this draft exists

This stub was generated from `memory/reviews/skill-candidates.json` as a **reviewable draft**. It is not yet canonical and should not replace an existing skill without explicit review.

- **Candidate ID:** `{candidate.candidate_id}`
- **Reason:** `{candidate.reason}`
- **Suggested canonical target:** `{candidate.target_path}`
- **Draft path:** `{draft_path}`

---

## Proposed workflow

1. Review the evidence and decide whether this pattern deserves a canonical skill, an update to an existing skill, or only a procedure entry.
2. If promoted, merge the useful parts into the intended target instead of copying this draft blindly.
3. If rejected, keep or archive the draft as review history.

---

## Evidence

{evidence_lines if evidence_lines else "- No evidence captured."}

---

## Reviewer notes

- Decision:
- Target:
- Gaps:
- Next action:
"""


def render_skill_yaml(candidate: Candidate, draft_path: Path) -> str:
    return f"""id: {draft_slug(candidate)}
name: {candidate.candidate_id.replace("-", " ").title()}
version: "0.1-draft"
owner: James
category: draft
description: {candidate.summary}
status: draft
review_required: true
source_candidate: {candidate.candidate_id}
suggested_target: {candidate.target_path}
draft_path: {windows_path(draft_path)}
triggers:
  - review
  - promotion
inputs:
  - type: skill_candidate
    description: Candidate payload from skill-candidates.json
outputs:
  - type: draft_skill
    path: {windows_path(draft_path)}
tools_preferred:
  - uv
  - powershell
  - view
constraints:
  - canonical_merge_required: true
  - no_auto_canonization: true
dependencies: []
"""


def render_preview(selected: list[Candidate], root: Path, draft_root: Path) -> str:
    lines = [
        "---",
        "kind: skill-stub-promotion-preview",
        "---",
        "",
        "# Skill stub promotion preview",
        "",
        "These drafts are reviewable stubs only. They are not canonical skills.",
        "",
    ]
    if not selected:
        lines.append("- No candidates matched the current selection.")
        return "\n".join(lines) + "\n"
    for item in selected:
        skill_dir = draft_dir(root, draft_root, item)
        lines.extend(
            [
                f"## {item.candidate_id}",
                "",
                f"- **Score:** {item.score}",
                f"- **Reason:** {item.reason}",
                f"- **Suggested canonical target:** `{item.target_path}`",
                f"- **Draft directory:** `{skill_dir.relative_to(root)}`",
                f"- **Summary:** {item.summary}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def write_drafts(selected: list[Candidate], root: Path, draft_root: Path) -> list[str]:
    created: list[str] = []
    for item in selected:
        skill_dir = draft_dir(root, draft_root, item)
        skill_md = skill_dir / "SKILL.md"
        skill_yaml = skill_dir / "skill.yaml"
        atomic_write(skill_md, render_skill_markdown(item, skill_dir.relative_to(root)))
        atomic_write(skill_yaml, render_skill_yaml(item, skill_dir.relative_to(root)))
        created.append(str(skill_dir.relative_to(root)))
    return created


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate reviewable draft skill stubs from skill candidates.")
    parser.add_argument(
        "--input",
        type=Path,
        default=repo_root() / "memory" / "reviews" / "skill-candidates.json",
        help="Path to the skill candidates JSON file.",
    )
    parser.add_argument(
        "--mode",
        choices=["preview", "apply"],
        default="preview",
        help="Preview draft generation or write draft stubs.",
    )
    parser.add_argument(
        "--draft-root",
        type=Path,
        default=Path("skills") / "_drafts",
        help="Relative path from repo root where draft skills should be written.",
    )
    parser.add_argument(
        "--candidate-id",
        action="append",
        default=[],
        help="Specific candidate id to include. Can be repeated.",
    )
    parser.add_argument("--all", action="store_true", help="Select all candidates above the score threshold.")
    parser.add_argument("--min-score", type=int, default=25, help="Minimum candidate score to include.")
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=repo_root() / "memory" / "reviews" / "skill-stub-promotion.md",
        help="Where to write the preview markdown.",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=repo_root() / "memory" / "reviews" / "skill-stub-promotion.json",
        help="Where to write the JSON selection artifact.",
    )
    parser.add_argument("--print", action="store_true", help="Print the preview markdown after writing.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    root = repo_root()
    candidates = load_candidates(args.input)
    selected = select_candidates(candidates, args.min_score, set(args.candidate_id), args.all)
    preview = render_preview(selected, root, args.draft_root)
    selection_payload = {
        "created": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
        "mode": args.mode,
        "draft_root": str(args.draft_root).replace("/", "\\"),
        "selected_count": len(selected),
        "candidates": [
            {
                "id": item.candidate_id,
                "score": item.score,
                "reason": item.reason,
                "target_path": item.target_path,
                "summary": item.summary,
                "draft_dir": str(draft_dir(root, args.draft_root, item).relative_to(root)),
            }
            for item in selected
        ],
    }
    atomic_write(args.markdown_out, preview)
    atomic_write(args.json_out, json.dumps(selection_payload, indent=2, ensure_ascii=False) + "\n")
    created: list[str] = []
    if args.mode == "apply":
        created = write_drafts(selected, root, args.draft_root)
    print(f"WROTE_MARKDOWN: {args.markdown_out}")
    print(f"WROTE_JSON: {args.json_out}")
    print(f"SELECTED_COUNT: {len(selected)}")
    if created:
        print(f"CREATED_DRAFTS: {len(created)}")
        for item in created:
            print(f"CREATED: {item}")
    if args.print:
        print()
        print(preview, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
