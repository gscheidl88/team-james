#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""
wiki_team_health_refresh.py - Generate team health status for wiki/agent-team-health.md.

Reads existing JSON artifacts from memory and wiki review tooling, then writes
a fresh body into the live wiki page.

Usage (called by wiki_live_pages.py):
    uv run tools/wiki/wiki_team_health_refresh.py --wiki-page wiki/agent-team-health.md
    uv run tools/wiki/wiki_team_health_refresh.py --wiki-page wiki/agent-team-health.md --dry-run
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

# Force UTF-8 output on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

VAULT = Path(__file__).resolve().parents[2]
REVIEWS_DIR = VAULT / "memory" / "reviews"
WIKI_REVIEWS_DIR = VAULT / "wiki" / "reviews"
ACCESS_LOG = VAULT / "memory" / "access-log.jsonl"


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def read_jsonl_count(path: Path) -> int:
    if not path.exists():
        return 0
    count = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            count += 1
    return count


def parse_frontmatter_raw(text: str) -> tuple[str, str]:
    """Split a markdown file into (frontmatter_block, body). Returns ('', text) if no frontmatter."""
    if not text.startswith("---"):
        return "", text
    end = text.find("\n---", 3)
    if end == -1:
        return "", text
    fm = text[: end + 4]
    body = text[end + 4:].lstrip("\n")
    return fm, body


def update_last_modified(frontmatter: str, today: str) -> str:
    """Replace last_modified: value in frontmatter block."""
    updated = re.sub(
        r"^last_modified:.*$",
        f"last_modified: {today}",
        frontmatter,
        flags=re.MULTILINE,
    )
    if "last_modified:" not in updated:
        updated = updated.rstrip() + f"\nlast_modified: {today}\n"
    return updated


def render_body(
    memory_qa: dict,
    knowledge_review: dict,
    memory_maintenance: dict,
    access_count: int,
    today: str,
) -> str:
    """Generate the markdown body for the team health wiki page."""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Memory QA metrics
    health_score = memory_qa.get("health_score") or memory_qa.get("score") or "—"
    needs_review = memory_qa.get("needs_review", "—")
    archive_candidates = memory_qa.get("archive_candidates", "—")

    # Knowledge review metrics
    kr_status = knowledge_review.get("status") or "—"
    kr_score = knowledge_review.get("health_score") or "—"
    kr_search_fresh = knowledge_review.get("search_index", {}).get("fresh")
    kr_orphans = knowledge_review.get("graph", {}).get("orphans") or "—"
    kr_search_queries = knowledge_review.get("usage", {}).get("search_queries_last_30_days") or "—"
    kr_reasons = knowledge_review.get("reasons") or []

    # Memory maintenance — top compounding memories
    top_reinforcement = memory_maintenance.get("top_reinforcement") or []

    status_icon = {
        "ok": "🟢",
        "warn": "🟡",
        "degraded": "🔴",
        "blocked": "🔴",
    }

    lines = [
        f"## Overview",
        "",
        "Agent team health is a **live summary** of the memory and knowledge system state. "
        "It is auto-refreshed at each session close by `wiki_team_health_refresh.py`. "
        "Do not edit the body manually — changes will be overwritten. "
        "To fix issues, address the underlying artifacts in `memory/reviews/` or `wiki/reviews/`.",
        "",
        f"*Last refreshed: {now_str}*",
        "",
        "---",
        "",
        "## 🧠 Memory Health",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Health score | **{health_score}** |",
        f"| Needs review | {needs_review} |",
        f"| Archive candidates | {archive_candidates} |",
        f"| Access log events | {access_count} |",
        "",
    ]

    if top_reinforcement:
        lines += [
            "### 🔥 Top Compounding Memories",
            "",
            "These facts are referenced most — reinforcement priority:",
            "",
        ]
        for item in top_reinforcement[:5]:
            refs = item.get("references", 0)
            importance = item.get("importance", 0)
            text = str(item.get("text") or "")[:100]
            lines.append(f"- `refs={refs}` `importance={importance}` — {text}")
        lines.append("")
    else:
        lines += [
            "### 🔥 Compounding Memories",
            "",
            "🟡 No reinforcement data yet. Run `memory_retrieval.py --warmup` to seed the access log.",
            "",
        ]

    lines += [
        "---",
        "",
        "## 📚 Knowledge Graph Health",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Status | {status_icon.get(kr_status, '⚪')} {kr_status} |",
        f"| Health score | **{kr_score}** |",
        f"| Search index fresh | {'✓' if kr_search_fresh else '✗' if kr_search_fresh is not None else '—'} |",
        f"| Orphan pages | {kr_orphans} |",
        f"| Search queries (30d) | {kr_search_queries} |",
        "",
    ]

    if kr_reasons:
        lines += ["**Issues:**", ""]
        for reason in kr_reasons:
            lines.append(f"- {reason}")
        lines.append("")

    lines += [
        "---",
        "",
        "## 🔄 How to Fix Issues",
        "",
        "| Problem | Command |",
        "|---------|---------|",
        "| Low compounding | `uv run tools/memory/memory_retrieval.py --warmup` |",
        "| Stale search index | `uv run --python 3.12 tools/wiki/wiki_search.py --index` |",
        "| Graph outdated | `uv run --python 3.12 tools/wiki/wiki_graph.py --build` |",
        "| Memory needs review | Review `memory/reviews/memory-qa.md` |",
        "| Archive candidates | Run `uv run tools/memory/memory_maintenance.py` |",
        "",
    ]

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Refresh wiki/agent-team-health.md body from system artifacts.")
    parser.add_argument("--wiki-page", required=True, type=Path, help="Path to the wiki page to refresh")
    parser.add_argument("--dry-run", action="store_true", help="Print generated content, do not write")
    args = parser.parse_args()

    wiki_page: Path = args.wiki_page
    if not wiki_page.is_absolute():
        wiki_page = VAULT / wiki_page
    if not wiki_page.exists():
        print(f"ERROR: wiki page not found: {wiki_page}")
        return 1

    memory_qa = read_json(REVIEWS_DIR / "memory-qa.json")
    knowledge_review = read_json(WIKI_REVIEWS_DIR / "knowledge-performance-review.json")
    memory_maintenance = read_json(REVIEWS_DIR / "memory-maintenance.json")
    access_count = read_jsonl_count(ACCESS_LOG)
    today = date.today().isoformat()

    existing_text = wiki_page.read_text(encoding="utf-8")
    frontmatter, _ = parse_frontmatter_raw(existing_text)
    if not frontmatter:
        print(f"ERROR: no frontmatter found in {wiki_page}")
        return 1

    updated_fm = update_last_modified(frontmatter, today)
    new_body = render_body(memory_qa, knowledge_review, memory_maintenance, access_count, today)
    new_content = updated_fm + "\n" + new_body

    if args.dry_run:
        print(new_content)
        print("DRY_RUN: no file written")
        return 0

    temp = wiki_page.with_suffix(".md.tmp")
    temp.write_text(new_content, encoding="utf-8")
    temp.replace(wiki_page)

    print(f"REFRESHED: {wiki_page.name}")
    print(f"MEMORY_HEALTH: {memory_qa.get('health_score', '—')}")
    print(f"KNOWLEDGE_STATUS: {knowledge_review.get('status', '—')}")
    print(f"ACCESS_LOG_EVENTS: {access_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
