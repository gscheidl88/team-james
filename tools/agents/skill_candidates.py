#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""
skill_candidates.py - Build reviewable skill candidates from local workspace artifacts.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path


INTERESTING_RE = re.compile(
    r"\b(always|never|before|after|when|workflow|pattern|protocol|checklist|skill|handoff|review|verify|validation|recover|recovery|fallback|escalat(?:e|ion)|issue|backlog|radar|promot(?:e|ion)|trace|hypothesis|checkpoint|eval)\b",
    re.IGNORECASE,
)
DATE_RE = re.compile(r"\b20\d{2}-\d{2}-\d{2}\b")
PATH_RE = re.compile(r"[A-Za-z]:\\[^\s]+|(?:\.\.?\\)+[^\s]+")
URL_RE = re.compile(r"https?://\S+")
MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")
INLINE_CODE_RE = re.compile(r"`([^`]+)`")
MULTISPACE_RE = re.compile(r"\s+")


@dataclass(frozen=True)
class Theme:
    key: str
    title: str
    summary: str
    target_path: str
    reason: str
    keywords: tuple[str, ...]


THEMES = (
    Theme(
        key="skill-promotion",
        title="Skill promotion from repeated work",
        summary="Repeated local evidence suggests a reusable skill or procedure should be promoted from real work artifacts.",
        target_path="skills\\skill-promotion\\SKILL.md",
        reason="self-improvement-loop",
        keywords=("skill", "promote", "promotion", "pattern", "workflow", "procedure"),
    ),
    Theme(
        key="handoff-discipline",
        title="Handoff and checkpoint discipline",
        summary="The workspace repeatedly reinforces explicit plan state, checkpoint blocks, and clean agent handoff behavior.",
        target_path="skills\\session-handoff\\SKILL.md",
        reason="manager-operating-pattern",
        keywords=("handoff", "checkpoint", "validation", "next test", "blockers", "replan"),
    ),
    Theme(
        key="verification-and-evals",
        title="Verification and workflow-eval discipline",
        summary="Quality gates repeatedly rely on review, verification, and explicit eval passes rather than ad hoc confidence.",
        target_path="skills\\workflow-evaluation\\SKILL.md",
        reason="quality-assurance-pattern",
        keywords=("review", "verify", "validation", "eval", "regression", "capability"),
    ),
    Theme(
        key="reliability-and-recovery",
        title="Reliability, fallback, and recovery handling",
        summary="Operational reliability repeatedly depends on typed failures, fallback paths, recovery rules, and escalation signals.",
        target_path="memory\\procedures.md",
        reason="operational-reliability-pattern",
        keywords=("recover", "recovery", "fallback", "escalate", "escalation", "failure"),
    ),
    Theme(
        key="research-to-backlog",
        title="Research to backlog conversion",
        summary="Research findings should become explicit backlog items and issue-ready actions instead of staying as one-off analysis.",
        target_path="skills\\research-to-backlog\\SKILL.md",
        reason="execution-conversion-pattern",
        keywords=("issue", "backlog", "radar", "opportunity", "roadmap", "selected"),
    ),
    Theme(
        key="trace-aware-operations",
        title="Trace-aware delegated operations",
        summary="Delegated work is strongest when trace events, hypotheses, and next-test state remain visible during execution.",
        target_path="skills\\orchestration\\SKILL.md",
        reason="trace-governance-pattern",
        keywords=("trace", "hypothesis", "checkpoint", "next test", "open hypotheses", "task"),
    ),
)


@dataclass
class Evidence:
    source: str
    text: str


@dataclass
class Candidate:
    theme: Theme
    sources: set[str] = field(default_factory=set)
    evidence: list[Evidence] = field(default_factory=list)
    occurrences: int = 0

    def score(self) -> int:
        return self.occurrences + (len(self.sources) * 3)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(content, encoding="utf-8")
    temp.replace(path)


def normalize_text(value: str) -> str:
    text = value.strip()
    text = MARKDOWN_LINK_RE.sub(r"\1", text)
    text = INLINE_CODE_RE.sub(r"\1", text)
    text = URL_RE.sub("", text)
    text = PATH_RE.sub("", text)
    text = DATE_RE.sub("", text)
    text = text.replace("**", "").replace("*", "").replace("_", " ")
    text = re.sub(r"^\s*[-*]\s*", "", text)
    text = re.sub(r"^\s*\d+\.\s*", "", text)
    text = re.sub(r"^\s*\|\s*", "", text)
    text = re.sub(r"\s*\|\s*", " ", text)
    text = MULTISPACE_RE.sub(" ", text)
    return text.strip()


def keep_line(value: str) -> bool:
    stripped = value.strip()
    if len(stripped) < 25:
        return False
    if stripped.startswith("---"):
        return False
    if stripped.startswith("#"):
        return False
    if stripped.startswith("|-----"):
        return False
    if stripped.startswith("```"):
        return False
    lowered = stripped.lower()
    if lowered.startswith("files changed:"):
        return False
    if lowered.startswith("created skills/"):
        return False
    if lowered.count("\\") >= 2 or lowered.count("/") >= 3:
        return False
    return bool(INTERESTING_RE.search(stripped))


def collect_markdown_lines(path: Path) -> list[str]:
    lines: list[str] = []
    if not path.exists():
        return lines
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if keep_line(raw_line):
            lines.append(raw_line.strip())
    return lines


def collect_trace_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    lines: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        payload = json.loads(raw)
        candidates = []
        note = str(payload.get("note") or "").strip()
        if note:
            candidates.append(note)
        metadata = payload.get("metadata") or {}
        for key in (
            "validation_plan",
            "replan_rule",
            "handoff_state",
            "hypothesis",
            "contradiction",
            "next_test",
            "fallback_action",
            "escalate_when",
        ):
            value = str(metadata.get(key) or "").strip()
            if value:
                candidates.append(value)
        for candidate in candidates:
            if keep_line(candidate):
                lines.append(candidate)
    return lines


def collect_evidence(args: argparse.Namespace) -> list[Evidence]:
    root = repo_root()
    evidence: list[Evidence] = []

    procedure_candidates = root / "memory" / "reviews" / "procedure-candidates.md"
    for line in collect_markdown_lines(procedure_candidates):
        evidence.append(Evidence("memory/reviews/procedure-candidates.md", line))

    for plan_path in sorted((root / "plans").glob("*.md")):
        for line in collect_markdown_lines(plan_path):
            evidence.append(Evidence(str(plan_path.relative_to(root)), line))

    daily_dir = root / "PersonalNotes" / "Daily"
    if daily_dir.exists():
        daily_paths = sorted(daily_dir.glob("*.md"))[-args.daily_limit :]
        for note_path in daily_paths:
            for line in collect_markdown_lines(note_path):
                evidence.append(Evidence(str(note_path.relative_to(root)), line))

    trace_path = root / ".agent-trace.jsonl"
    for line in collect_trace_lines(trace_path):
        evidence.append(Evidence(".agent-trace.jsonl", line))

    return evidence


def best_theme_for_line(text: str) -> Theme | None:
    lowered = normalize_text(text).lower()
    best_theme: Theme | None = None
    best_score = 0
    for theme in THEMES:
        score = 0
        for keyword in theme.keywords:
            if keyword in lowered:
                score += 1
        if score > best_score:
            best_score = score
            best_theme = theme
    return best_theme if best_score > 0 else None


def build_candidates(items: list[Evidence], limit: int) -> list[Candidate]:
    buckets: dict[str, Candidate] = {}
    for item in items:
        normalized = normalize_text(item.text)
        theme = best_theme_for_line(normalized)
        if theme is None:
            continue
        candidate = buckets.get(theme.key)
        if candidate is None:
            candidate = Candidate(theme=theme)
            buckets[theme.key] = candidate
        candidate.occurrences += 1
        candidate.sources.add(item.source.split("\\")[0].split("/")[0])
        if len(candidate.evidence) < 5:
            candidate.evidence.append(Evidence(item.source, normalized))

    ordered = sorted(
        (
            candidate
            for candidate in buckets.values()
            if candidate.occurrences >= 2 or len(candidate.sources) >= 2
        ),
        key=lambda item: (-item.score(), -item.occurrences, item.theme.title.lower()),
    )
    return ordered[:limit]


def render_json(candidates: list[Candidate]) -> str:
    payload = {
        "created_by": "James",
        "candidate_count": len(candidates),
        "candidates": [
            OrderedDict(
                id=candidate.theme.key,
                score=candidate.score(),
                occurrences=candidate.occurrences,
                source_count=len(candidate.sources),
                reason=candidate.theme.reason,
                target_path=candidate.theme.target_path,
                summary=candidate.theme.summary,
                evidence=[
                    OrderedDict(source=item.source, text=normalize_text(item.text))
                    for item in candidate.evidence
                ],
            )
            for candidate in candidates
        ],
    }
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def render_markdown(candidates: list[Candidate]) -> str:
    lines = [
        "---",
        'kind: skill-candidates',
        "created_by: James",
        "---",
        "",
        "# Skill candidates",
        "",
        "Review these candidates before promoting them into `skills/` or `memory/procedures.md`.",
        "",
    ]
    if not candidates:
        lines.append("- No candidates found.")
        return "\n".join(lines) + "\n"

    for candidate in candidates:
        lines.extend(
            [
                f"## {candidate.theme.title}",
                "",
                f"- **Score:** {candidate.score()}",
                f"- **Occurrences:** {candidate.occurrences}",
                f"- **Source count:** {len(candidate.sources)}",
                f"- **Reason:** {candidate.theme.reason}",
                f"- **Suggested target:** `{candidate.theme.target_path}`",
                f"- **Summary:** {candidate.theme.summary}",
                "",
                "### Evidence",
                "",
            ]
        )
        for item in candidate.evidence:
            lines.append(f"- `{item.source}` — {normalize_text(item.text)}")
        lines.extend(["", ""])
    return "\n".join(lines).rstrip() + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate reviewable skill candidates from local artifacts.")
    parser.add_argument("--daily-limit", type=int, default=14, help="How many daily notes to scan if present.")
    parser.add_argument("--limit", type=int, default=12, help="Maximum number of candidates to emit.")
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=repo_root() / "memory" / "reviews" / "skill-candidates.md",
        help="Where to write the markdown report.",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=repo_root() / "memory" / "reviews" / "skill-candidates.json",
        help="Where to write the JSON report.",
    )
    parser.add_argument("--print", action="store_true", help="Print markdown to stdout after writing.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    evidence = collect_evidence(args)
    candidates = build_candidates(evidence, args.limit)
    markdown = render_markdown(candidates)
    payload = render_json(candidates)
    atomic_write(args.markdown_out, markdown)
    atomic_write(args.json_out, payload)
    print(f"WROTE_MARKDOWN: {args.markdown_out}")
    print(f"WROTE_JSON: {args.json_out}")
    print(f"CANDIDATE_COUNT: {len(candidates)}")
    if args.print:
        print()
        print(markdown, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
