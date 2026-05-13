#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""
memory_reconcile.py - review candidate durable updates against existing memory.

Usage:
    uv run tools/memory/memory_reconcile.py --candidate-file <path>
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from memory_common import REVIEWS_DIR, SourceHit, atomic_write, search_documents, tokenize, write_json

CANDIDATE_LINE_RE = re.compile(r"^-\s+\[(?P<confidence>[^\]]+)\]\s+\[(?P<action>[^\]]+)\]\s+\[(?P<target>[^\]]+)\]\s+(?P<text>.+)$")
NEGATION_TOKENS = {"not", "never", "no", "without", "avoid", "instead"}


@dataclass
class Candidate:
    source_kind: str
    confidence: str
    action: str
    target: str
    text: str


@dataclass
class ReviewItem:
    source_kind: str
    target: str
    action: str
    confidence: str
    text: str
    relation: str
    review_state: str
    top_hit_path: str | None
    top_hit_line: int | None
    top_hit_text: str | None
    related_hits: list[dict[str, object]]


def parse_candidates(path: Path) -> tuple[str, list[Candidate]]:
    if path.suffix.lower() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        task = str(payload.get("current_task", "(not specified)"))
        proposals = []
        for item in payload.get("proposals", []):
            proposals.append(
                Candidate(
                    source_kind=str(item.get("source_kind", "candidate")),
                    confidence=str(item.get("confidence", "medium")),
                    action=str(item.get("action", "review")),
                    target=str(item.get("target", "memory/wiki")),
                    text=str(item.get("text", "")).strip(),
                )
            )
        return task, [candidate for candidate in proposals if candidate.text]

    task = "(not specified)"
    candidates: list[Candidate] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("**Current task:**"):
            task = line.split(":", 1)[1].strip()
        match = CANDIDATE_LINE_RE.match(line.strip())
        if not match:
            continue
        candidates.append(
            Candidate(
                source_kind="candidate",
                confidence=match.group("confidence"),
                action=match.group("action"),
                target=match.group("target"),
                text=match.group("text").strip(),
            )
        )
    return task, candidates


def classify_candidate(candidate: Candidate, hits: list[SourceHit]) -> tuple[str, str]:
    if not hits:
        return "independent", "ready"

    top = hits[0]
    query_tokens = set(tokenize(candidate.text))
    hit_tokens = set(tokenize(top.text))
    overlap = len(query_tokens & hit_tokens) / max(len(query_tokens), 1)
    query_neg = bool(query_tokens & NEGATION_TOKENS)
    hit_neg = bool(hit_tokens & NEGATION_TOKENS)

    if overlap >= 0.4 and query_neg != hit_neg:
        relation = "contradictory"
    elif overlap >= 0.7 and len(candidate.text) > len(top.text) * 1.15:
        relation = "subsumes"
    elif overlap >= 0.45:
        relation = "compatible"
    elif overlap >= 0.2:
        relation = "independent"
    else:
        relation = "ignore" if candidate.action == "review" and candidate.confidence == "low" else "independent"

    review_state = "needs-review" if relation in {"contradictory", "ignore"} or candidate.confidence in {"low", "uncertain"} else "ready"
    return relation, review_state


def default_output_paths(candidate_path: Path) -> tuple[Path, Path]:
    if "session-state" in str(candidate_path).lower():
        base_dir = candidate_path.parent
        return base_dir / "memory-review.md", base_dir / "memory-review.json"
    return REVIEWS_DIR / "latest-memory-review.md", REVIEWS_DIR / "latest-memory-review.json"


def build_markdown(task: str, items: list[ReviewItem]) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    summary_rows = [
        f"| {item.source_kind} | {item.target} | {item.relation} | {item.review_state} | {item.top_hit_path or '—'} |"
        for item in items
    ]
    lines = [
        "---",
        f"created: {now}",
        "kind: memory-review",
        "---",
        "",
        "# Memory reconciliation review",
        "",
        f"**Current task:** {task}",
        "",
        "## Summary",
        "",
        "| Source | Target | Relation | Review state | Top related hit |",
        "|--------|--------|----------|--------------|------------------|",
        "",
    ]
    lines.extend(summary_rows if summary_rows else ["| — | — | — | — | — |"])
    lines.append("")

    for idx, item in enumerate(items, start=1):
        lines.extend(
            [
                f"## Item {idx}",
                "",
                f"- **Text:** {item.text}",
                f"- **Source kind:** {item.source_kind}",
                f"- **Target:** {item.target}",
                f"- **Action:** {item.action}",
                f"- **Confidence:** {item.confidence}",
                f"- **Relation:** {item.relation}",
                f"- **Review state:** {item.review_state}",
                "",
                "### Related hits",
                "",
            ]
        )
        if item.related_hits:
            for hit in item.related_hits:
                lines.append(
                    f"- [{hit['source_type']}] {hit['path']}:{hit['line_no']} (score {hit['score']}) — {hit['text']}"
                )
        else:
            lines.append("- No related hits.")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Review memory candidates against existing memory.")
    parser.add_argument("--candidate-file", required=True, help="Candidate markdown or JSON file")
    parser.add_argument("--limit", type=int, default=3, help="Maximum related hits per candidate")
    parser.add_argument("--markdown-out", help="Optional markdown output path")
    parser.add_argument("--json-out", help="Optional JSON output path")
    args = parser.parse_args()

    candidate_path = Path(args.candidate_file)
    task, candidates = parse_candidates(candidate_path)
    default_md, default_json = default_output_paths(candidate_path)
    markdown_out = Path(args.markdown_out) if args.markdown_out else default_md
    json_out = Path(args.json_out) if args.json_out else default_json

    items: list[ReviewItem] = []
    for candidate in candidates:
        hits = search_documents(candidate.text, limit=args.limit)
        relation, review_state = classify_candidate(candidate, hits)
        top_hit = hits[0] if hits else None
        items.append(
            ReviewItem(
                source_kind=candidate.source_kind,
                target=candidate.target,
                action=candidate.action,
                confidence=candidate.confidence,
                text=candidate.text,
                relation=relation,
                review_state=review_state,
                top_hit_path=top_hit.path if top_hit else None,
                top_hit_line=top_hit.line_no if top_hit else None,
                top_hit_text=top_hit.text if top_hit else None,
                related_hits=[hit.to_dict() for hit in hits],
            )
        )

    markdown = build_markdown(task, items)
    atomic_write(markdown_out, markdown)
    write_json(
        json_out,
        {
            "created": datetime.now().isoformat(timespec="seconds"),
            "kind": "memory-review",
            "current_task": task,
            "items": [asdict(item) for item in items],
        },
    )

    needs_review = sum(1 for item in items if item.review_state == "needs-review")
    contradictions = sum(1 for item in items if item.relation == "contradictory")
    print(f"MARKDOWN: {markdown_out}")
    print(f"JSON: {json_out}")
    print(f"ITEMS: {len(items)}")
    print(f"NEEDS_REVIEW: {needs_review}")
    print(f"CONTRADICTIONS: {contradictions}")


if __name__ == "__main__":
    main()
