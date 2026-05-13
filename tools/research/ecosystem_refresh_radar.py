#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""
ecosystem_refresh_radar.py - Refresh external agent ecosystem signals into review and delta artifacts.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
HEADING_RE = re.compile(r"<h[1-3][^>]*>(.*?)</h[1-3]>", re.IGNORECASE | re.DOTALL)
SCRIPT_STYLE_RE = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL)
COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
TAG_RE = re.compile(r"<[^>]+>")
MULTISPACE_RE = re.compile(r"\s+")
KEYWORD_RE = re.compile(
    r"\b(release|update|agent|copilot|model|tool|automation|memory|browser|voice|multimodal|context|planning|"
    r"coordination|skill|reasoning|recovery|workflow)\b",
    re.IGNORECASE,
)
NOISE_SUBSTRINGS = (
    "navigation menu",
    "search code, repositories, users, issues, pull requests",
    "saved searches",
    "provide feedback",
    "skip to content",
    "cookie",
    "privacy",
    "terms",
    "all reactions",
    "sign in",
    "appearance settings",
    "folders and files",
    "latest commit",
    "history",
    "choose a tag to compare",
    "uh oh!",
    "table of contents",
)


@dataclass
class FetchResult:
    url: str
    ok: bool
    status_code: int | None
    content_type: str
    fetched_at: str
    title: str
    snippets: list[str]
    signal_hash: str | None
    content_length: int
    error: str | None = None


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(content, encoding="utf-8")
    temp.replace(path)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def windows_rel(path: Path, root: Path) -> str:
    return str(path.relative_to(root)).replace("/", "\\")


def normalize_text(value: str) -> str:
    return MULTISPACE_RE.sub(" ", html.unescape(value or "").strip())


def unique_keep_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    items: list[str] = []
    for value in values:
        normalized = normalize_text(value)
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        items.append(normalized)
    return items


def clean_fragment(value: str) -> str:
    without_tags = TAG_RE.sub(" ", value)
    return normalize_text(without_tags)


def is_noise_line(value: str) -> bool:
    text = normalize_text(value).lower()
    if not text:
        return True
    return any(item in text for item in NOISE_SUBSTRINGS)


def strip_html(value: str) -> str:
    without_scripts = SCRIPT_STYLE_RE.sub(" ", value)
    without_comments = COMMENT_RE.sub(" ", without_scripts)
    without_tags = TAG_RE.sub("\n", without_comments)
    return html.unescape(without_tags)


def derive_signals(body: str, content_type: str) -> tuple[str, list[str], str]:
    looks_html = "html" in content_type.lower() or "<html" in body.lower()
    title = ""
    heading_lines: list[str] = []
    plain_text = body
    if looks_html:
        match = TITLE_RE.search(body)
        title = clean_fragment(match.group(1)) if match else ""
        heading_lines = [clean_fragment(item) for item in HEADING_RE.findall(body) if not is_noise_line(item)]
        plain_text = strip_html(body)

    raw_lines = [normalize_text(line) for line in plain_text.splitlines()]
    candidate_lines: list[str] = []
    for line in raw_lines:
        if len(line) < 20:
            continue
        if is_noise_line(line):
            continue
        candidate_lines.append(line)

    keyword_lines = [line for line in candidate_lines if KEYWORD_RE.search(line)]
    general_lines = [line for line in candidate_lines if line not in keyword_lines]
    snippets = unique_keep_order(([title] if title else []) + heading_lines[:8] + keyword_lines[:8] + general_lines[:4])[:10]
    if not title and snippets:
        title = snippets[0]
    signal_material = "\n".join(snippets).lower()
    signal_hash = hashlib.sha256(signal_material.encode("utf-8")).hexdigest()
    return title, snippets, signal_hash


def fetch_url(url: str, timeout: int) -> FetchResult:
    fetched_at = datetime.now().isoformat(timespec="seconds")
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "KortexxEcosystemRadar/1.0 (+https://github.com/<YOUR_GITHUB_USERNAME>/Agent_James)",
            "Accept": "text/html, text/markdown, text/plain;q=0.9, */*;q=0.1",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
            charset = response.headers.get_content_charset() or "utf-8"
            body = raw.decode(charset, errors="replace")
            content_type = response.headers.get_content_type() or "text/plain"
            title, snippets, signal_hash = derive_signals(body, content_type)
            return FetchResult(
                url=url,
                ok=True,
                status_code=response.status,
                content_type=content_type,
                fetched_at=fetched_at,
                title=title,
                snippets=snippets,
                signal_hash=signal_hash,
                content_length=len(body),
            )
    except urllib.error.HTTPError as exc:
        return FetchResult(
            url=url,
            ok=False,
            status_code=exc.code,
            content_type="",
            fetched_at=fetched_at,
            title="",
            snippets=[],
            signal_hash=None,
            content_length=0,
            error=f"HTTP {exc.code}: {exc.reason}",
        )
    except urllib.error.URLError as exc:
        return FetchResult(
            url=url,
            ok=False,
            status_code=None,
            content_type="",
            fetched_at=fetched_at,
            title="",
            snippets=[],
            signal_hash=None,
            content_length=0,
            error=f"URL error: {exc.reason}",
        )


def combine_hash(results: list[FetchResult]) -> str | None:
    ok_hashes = [item.signal_hash for item in results if item.ok and item.signal_hash]
    if not ok_hashes:
        return None
    material = "\n".join(ok_hashes)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def build_source_status(previous_hash: str | None, current_hash: str | None, mode: str, success_count: int, total_count: int) -> tuple[str, bool]:
    if success_count == 0:
        return "fetch_failed", False
    if success_count < total_count:
        if previous_hash and current_hash and previous_hash != current_hash:
            return "changed_partial", True
        return "partial", False
    if not previous_hash:
        return ("baseline_written", False) if mode == "apply" else ("baseline_missing", False)
    if previous_hash == current_hash:
        return "unchanged", False
    return "changed", True


def summarize_source(source: dict[str, Any], mode: str, timeout: int) -> dict[str, Any]:
    previous = dict(source.get("radar") or {})
    urls = [str(url) for url in source.get("urls") or []]
    fetches = [fetch_url(url, timeout) for url in urls]
    current_hash = combine_hash(fetches)
    success_count = sum(1 for item in fetches if item.ok)
    status, changed = build_source_status(previous.get("content_hash"), current_hash, mode, success_count, len(fetches))
    ok_fetches = [item for item in fetches if item.ok]
    latest_title = ok_fetches[0].title if ok_fetches else str(previous.get("title") or "")
    latest_snippets = unique_keep_order([snippet for item in ok_fetches for snippet in item.snippets])[:10]
    summary = {
        "id": source.get("id"),
        "name": source.get("name"),
        "status": status,
        "changed": changed,
        "last_checked": datetime.now().isoformat(timespec="seconds"),
        "previous_hash": previous.get("content_hash"),
        "content_hash": current_hash,
        "title": latest_title,
        "snippets": latest_snippets,
        "previous_title": previous.get("title"),
        "previous_snippets": list(previous.get("snippets") or []),
        "fetches": [
            {
                "url": item.url,
                "ok": item.ok,
                "status_code": item.status_code,
                "content_type": item.content_type,
                "fetched_at": item.fetched_at,
                "title": item.title,
                "snippets": item.snippets,
                "signal_hash": item.signal_hash,
                "content_length": item.content_length,
                "error": item.error,
            }
            for item in fetches
        ],
    }
    return summary


def source_radar_metadata(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "last_checked": summary["last_checked"],
        "status": summary["status"],
        "content_hash": summary["content_hash"],
        "title": summary["title"],
        "snippets": summary["snippets"],
        "previous_hash": summary["previous_hash"],
    }


def build_delta_opportunities(root: Path, source_summaries: list[dict[str, Any]], output_path: Path) -> dict[str, Any]:
    changed_sources = [item for item in source_summaries if item.get("changed")]
    opportunities: list[dict[str, Any]] = []
    for item in changed_sources:
        current_hash = str(item.get("content_hash") or "unknown")[:8]
        previous_hash = str(item.get("previous_hash") or "none")[:8]
        title = str(item.get("title") or item.get("name") or item.get("id"))
        snippets = list(item.get("snippets") or [])[:4]
        opportunities.append(
            {
                "id": f"ecosystem-refresh-{item.get('id')}-{current_hash}",
                "status": "planned",
                "priority": "medium",
                "title": f"Review {item.get('name')} ecosystem update ({current_hash})",
                "summary": f"{item.get('name')} changed since the last recorded radar baseline and should be reviewed for local workflow impact.",
                "why_now": f"The recurring ecosystem radar detected a source fingerprint change for {item.get('name')} ({previous_hash} -> {current_hash}).",
                "external_signals": [f"Latest title: {title}"] + [f"Observed signal: {snippet}" for snippet in snippets],
                "repo_gap": [
                    "External ecosystem changes can become stale before they are translated into local improvements.",
                    "The existing opportunity file needs recurring delta reviews instead of one-off research pulls.",
                ],
                "proposed_changes": [
                    "Review the changed source against current local tooling and policy.",
                    "Either update the canonical opportunity seed file or close the delta as not actionable.",
                    "If actionable, preview or create an issue with `tools\\github\\issue_batch.py --input sources\\agent-ecosystem\\refresh-deltas.json`.",
                ],
                "definition_of_done": [
                    "The changed source has been reviewed against local roadmap and tooling.",
                    "Any actionable local improvement is reflected in seed data or a tracked issue.",
                    "The radar delta is either resolved or explicitly marked not actionable.",
                ],
                "issue": {
                    "title": f"Review {item.get('name')} ecosystem update",
                    "labels": ["enhancement", "research", "ops"],
                },
            }
        )
    return {
        "created": datetime.now().isoformat(timespec="seconds"),
        "created_by": "James",
        "topic": "agent-ecosystem-refresh-deltas",
        "source_file": windows_rel(output_path, root),
        "opportunities": opportunities,
    }


def build_review_payload(root: Path, source_path: Path, source_payload: dict[str, Any], source_summaries: list[dict[str, Any]], delta_path: Path) -> dict[str, Any]:
    counts: dict[str, int] = {}
    failures = 0
    changed = 0
    baseline_missing = 0
    for item in source_summaries:
        status = str(item.get("status") or "unknown")
        counts[status] = counts.get(status, 0) + 1
        if status == "fetch_failed":
            failures += 1
        if item.get("changed"):
            changed += 1
        if status == "baseline_missing":
            baseline_missing += 1
    overall_status = "ok"
    if failures == len(source_summaries):
        overall_status = "degraded"
    elif failures or changed or baseline_missing:
        overall_status = "warn"

    attention: list[str] = []
    if changed:
        attention.append(f"{changed} external source(s) changed and produced review deltas.")
    if baseline_missing:
        attention.append(f"{baseline_missing} source(s) still need an applied baseline before change detection becomes active.")
    if failures:
        attention.append(f"{failures} source(s) failed to fetch during the latest radar run.")
    if not attention:
        attention.append("No external source changes were detected.")

    return {
        "created": datetime.now().isoformat(timespec="seconds"),
        "status": overall_status,
        "source_file": windows_rel(source_path, root),
        "delta_file": windows_rel(delta_path, root),
        "counts": counts,
        "summary": {
            "source_count": len(source_summaries),
            "changed_sources": changed,
            "baseline_missing_sources": baseline_missing,
            "failed_sources": failures,
        },
        "attention": attention,
        "sources": source_summaries,
        "existing_topic": source_payload.get("topic"),
    }


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "---",
        f"created: {payload['created']}",
        "kind: ecosystem-refresh-radar",
        "---",
        "",
        "# Ecosystem refresh radar",
        "",
        f"- **Status:** {payload['status']}",
        f"- **Sources checked:** {summary['source_count']}",
        f"- **Changed sources:** {summary['changed_sources']}",
        f"- **Baseline missing:** {summary['baseline_missing_sources']}",
        f"- **Failed sources:** {summary['failed_sources']}",
        f"- **Delta file:** `{payload['delta_file']}`",
        "",
        "## Attention",
        "",
    ]
    for item in payload.get("attention") or []:
        lines.append(f"- {item}")
    lines.extend(["", "## Sources", ""])
    for source in payload.get("sources") or []:
        lines.extend(
            [
                f"### {source.get('name')}",
                "",
                f"- **Status:** {source.get('status')}",
                f"- **Last checked:** {source.get('last_checked')}",
                f"- **Title:** {source.get('title') or 'n/a'}",
                f"- **Previous title:** {source.get('previous_title') or 'n/a'}",
            ]
        )
        if source.get("content_hash"):
            lines.append(f"- **Hash:** `{str(source.get('content_hash'))[:12]}`")
        if source.get("previous_hash"):
            lines.append(f"- **Previous hash:** `{str(source.get('previous_hash'))[:12]}`")
        fetch_errors = [item for item in source.get("fetches") or [] if item.get("error")]
        if fetch_errors:
            for item in fetch_errors:
                lines.append(f"- **Fetch error:** `{item.get('url')}` -> {item.get('error')}")
        snippets = list(source.get("snippets") or [])[:5]
        if snippets:
            lines.append("")
            lines.append("**Observed signals**")
            lines.append("")
            for snippet in snippets:
                lines.append(f"- {snippet}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def update_source_payload(source_payload: dict[str, Any], source_summaries: list[dict[str, Any]], review_json_path: Path, delta_path: Path, root: Path) -> dict[str, Any]:
    updated = dict(source_payload)
    summary_by_id = {str(item["id"]): item for item in source_summaries}
    updated_sources: list[dict[str, Any]] = []
    for source in source_payload.get("sources") or []:
        copy = dict(source)
        summary = summary_by_id.get(str(source.get("id")))
        if summary:
            copy["radar"] = source_radar_metadata(summary)
        updated_sources.append(copy)
    updated["sources"] = updated_sources
    updated["radar"] = {
        "last_refreshed": datetime.now().isoformat(timespec="seconds"),
        "review_json": windows_rel(review_json_path, root),
        "delta_file": windows_rel(delta_path, root),
        "status_counts": {
            str(item.get("status")): sum(1 for row in source_summaries if row.get("status") == item.get("status"))
            for item in source_summaries
        },
    }
    return updated


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Refresh external ecosystem sources into review and delta artifacts.")
    parser.add_argument(
        "--input",
        type=Path,
        default=repo_root() / "sources" / "agent-ecosystem" / "2026-04-25-opportunities.json",
        help="Canonical ecosystem opportunity seed file.",
    )
    parser.add_argument(
        "--mode",
        choices=["preview", "apply"],
        default="preview",
        help="Preview the radar run or apply updated radar metadata back into the source seed file.",
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=repo_root() / "memory" / "reviews" / "agent-ecosystem-refresh.md",
        help="Markdown review artifact path.",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=repo_root() / "memory" / "reviews" / "agent-ecosystem-refresh.json",
        help="JSON review artifact path.",
    )
    parser.add_argument(
        "--delta-out",
        type=Path,
        default=repo_root() / "sources" / "agent-ecosystem" / "refresh-deltas.json",
        help="Issue-ready delta seed file.",
    )
    parser.add_argument("--timeout", type=int, default=20, help="Per-request timeout in seconds.")
    parser.add_argument("--print", action="store_true", help="Print the markdown review artifact.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    root = repo_root()
    source_path = args.input
    source_payload = load_json(source_path)
    source_summaries = [summarize_source(source, args.mode, args.timeout) for source in source_payload.get("sources") or []]
    delta_payload = build_delta_opportunities(root, source_summaries, args.delta_out)
    review_payload = build_review_payload(root, source_path, source_payload, source_summaries, args.delta_out)
    review_markdown = render_markdown(review_payload)

    atomic_write(args.markdown_out, review_markdown)
    atomic_write(args.json_out, json.dumps(review_payload, indent=2, ensure_ascii=False) + "\n")
    atomic_write(args.delta_out, json.dumps(delta_payload, indent=2, ensure_ascii=False) + "\n")

    if args.mode == "apply":
        updated_source = update_source_payload(source_payload, source_summaries, args.json_out, args.delta_out, root)
        atomic_write(source_path, json.dumps(updated_source, indent=2, ensure_ascii=False) + "\n")

    print(f"WROTE_MARKDOWN: {args.markdown_out}")
    print(f"WROTE_JSON: {args.json_out}")
    print(f"WROTE_DELTAS: {args.delta_out}")
    print(f"SOURCE_COUNT: {review_payload['summary']['source_count']}")
    print(f"CHANGED_SOURCES: {review_payload['summary']['changed_sources']}")
    print(f"FAILED_SOURCES: {review_payload['summary']['failed_sources']}")
    print(f"BASELINE_MISSING: {review_payload['summary']['baseline_missing_sources']}")
    if args.mode == "apply":
        print(f"UPDATED_SOURCE: {source_path}")
    if args.print:
        print()
        print(review_markdown, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
