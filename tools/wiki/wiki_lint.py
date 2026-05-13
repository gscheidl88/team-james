#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pyyaml>=6.0",
#   "rich>=13.0",
# ]
# ///
"""
wiki_lint.py — Linter for the wiki knowledge base.

Checks:
  - Orphan pages (no inbound relates_to/depends_on links from other pages)
  - Dead backlinks (relates_to points to non-existent page id)
  - Stale validity (is_valid: true but valid_to date has passed)
  - Missing ## Overview section (L1 requirement)
  - Pages with no outbound relates_to links (isolated nodes)

Usage:
  uv run tools/wiki/wiki_lint.py
  uv run tools/wiki/wiki_lint.py --strict   # exit 1 if any issues found
  uv run tools/wiki/wiki_lint.py --fix      # auto-mark expired pages (valid_to passed)
"""

import argparse
import io
import re
import sys
from datetime import date
from pathlib import Path

import yaml
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# ── UTF-8 on Windows ─────────────────────────────────────────────────────────
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

WIKI_DIR = Path(__file__).parent.parent.parent / "wiki"
SKILLS_DIR = Path(__file__).parent.parent.parent / "skills"
SKIP_FILES = {"_schema.md", "index.md", "log.md"}

console = Console()

# ── Parsing ───────────────────────────────────────────────────────────────────

def _strip_wikilink(raw) -> str:
    """Strip [[page-id]] or [[page-id|alias]] → page-id."""
    s = str(raw).strip().strip('"').strip("'")
    m = re.match(r"^\[\[(.+?)(?:\|.+?)?\]\]$", s)
    return m.group(1).strip() if m else s


def parse_page(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    fm: dict = {}
    if m:
        try:
            fm = yaml.safe_load(m.group(1)) or {}
        except yaml.YAMLError:
            fm = {}
    fm["_file"] = path.name
    fm["_path"] = path
    fm["_has_overview"] = bool(re.search(r"^## Overview", text, re.MULTILINE))

    # Normalise list fields → plain id strings
    for field in ("relates_to", "depends_on"):
        raw = fm.get(field) or []
        if isinstance(raw, str):
            raw = [raw]
        fm[field] = [_strip_wikilink(x) for x in raw if x]

    return fm


def load_pages() -> list[dict]:
    pages = []
    for md in sorted(WIKI_DIR.glob("*.md")):
        if md.name in SKIP_FILES:
            continue
        pages.append(parse_page(md))
    return pages


# ── Lint checks ───────────────────────────────────────────────────────────────

def check_missing_overview(pages: list[dict]) -> list[dict]:
    return [p for p in pages if not p.get("_has_overview")]


def check_orphans(pages: list[dict]) -> list[dict]:
    """Pages that no other page links to (no inbound relates_to or depends_on)."""
    page_ids = {str(p.get("id", "")).strip() for p in pages if p.get("id")}
    inbound: dict[str, int] = {pid: 0 for pid in page_ids}
    for p in pages:
        for target in p.get("relates_to", []) + p.get("depends_on", []):
            if target in inbound:
                inbound[target] += 1
    return [p for p in pages if str(p.get("id", "")).strip() in inbound
            and inbound[str(p.get("id", "")).strip()] == 0]


def check_dead_links(pages: list[dict]) -> list[tuple[dict, str]]:
    """relates_to / depends_on entries pointing to non-existent page ids."""
    page_ids = {str(p.get("id", "")).strip() for p in pages if p.get("id")}
    dead = []
    for p in pages:
        for target in p.get("relates_to", []) + p.get("depends_on", []):
            if target and target not in page_ids:
                dead.append((p, target))
    return dead


def check_stale_validity(pages: list[dict]) -> list[dict]:
    """Pages with is_valid=True but valid_to date has passed."""
    today = date.today()
    stale = []
    for p in pages:
        if not p.get("is_valid", True):
            continue
        valid_to = p.get("valid_to")
        if not valid_to:
            continue
        try:
            vt = date.fromisoformat(str(valid_to))
            if vt < today:
                stale.append(p)
        except ValueError:
            pass
    return stale


def check_no_outbound(pages: list[dict]) -> list[dict]:
    """Pages with no relates_to and no depends_on links (isolated nodes)."""
    return [
        p for p in pages
        if not p.get("relates_to") and not p.get("depends_on")
    ]


# ── Auto-fix: mark expired pages ─────────────────────────────────────────────

def fix_expired(pages: list[dict]) -> int:
    """Set is_valid: false for pages whose valid_to has passed."""
    fixed = 0
    for p in check_stale_validity(pages):
        path: Path = p["_path"]
        text = path.read_text(encoding="utf-8")
        new_text = re.sub(r"(^is_valid:\s*)true", r"\1false", text, flags=re.MULTILINE)
        if new_text != text:
            path.write_text(new_text, encoding="utf-8")
            fixed += 1
    return fixed


# ── Display ───────────────────────────────────────────────────────────────────

def section(title: str, colour: str = "yellow"):
    console.print(f"\n[bold {colour}]{title}[/bold {colour}]")


def print_report(pages: list[dict], args) -> int:
    """Print full lint report. Returns total issue count."""
    total_issues = 0

    missing_ov = check_missing_overview(pages)
    orphans     = check_orphans(pages)
    dead        = check_dead_links(pages)
    stale       = check_stale_validity(pages)
    isolated    = check_no_outbound(pages)

    console.print(Panel(
        f"[bold cyan]🔍 Wiki Lint Report[/bold cyan]\n"
        f"[dim]{WIKI_DIR}  ·  {len(pages)} pages checked[/dim]",
        box=box.DOUBLE_EDGE
    ))

    # ── Missing ## Overview ──────────────────────────────────────────────────
    section(f"Missing ## Overview  ({len(missing_ov)} pages)", "red" if missing_ov else "green")
    if missing_ov:
        t = Table(box=box.SIMPLE, padding=(0, 2))
        t.add_column("File"); t.add_column("Title")
        for p in missing_ov:
            t.add_row(f"[dim]{p['_file']}[/dim]", str(p.get("title", "—")))
        console.print(t)
        total_issues += len(missing_ov)
    else:
        console.print("  [green]✓ All pages have ## Overview[/green]")

    # ── Orphan pages ────────────────────────────────────────────────────────
    section(f"Orphan Pages (no inbound links)  ({len(orphans)} pages)",
            "yellow" if orphans else "green")
    if orphans:
        t = Table(box=box.SIMPLE, padding=(0, 2))
        t.add_column("id"); t.add_column("Title")
        for p in orphans:
            t.add_row(str(p.get("id", "?")), str(p.get("title", "—")))
        console.print(t)
        total_issues += len(orphans)
    else:
        console.print("  [green]✓ No orphan pages[/green]")

    # ── Dead backlinks ───────────────────────────────────────────────────────
    section(f"Dead Backlinks  ({len(dead)} broken)",
            "red" if dead else "green")
    if dead:
        t = Table(box=box.SIMPLE, padding=(0, 2))
        t.add_column("Source page"); t.add_column("Missing target")
        for p, target in dead:
            t.add_row(f"[dim]{p['_file']}[/dim]", f"[red]{target}[/red]")
        console.print(t)
        total_issues += len(dead)
    else:
        console.print("  [green]✓ All backlinks resolve[/green]")

    # ── Stale validity ───────────────────────────────────────────────────────
    section(f"Stale Validity (is_valid=true but valid_to passed)  ({len(stale)} pages)",
            "yellow" if stale else "green")
    if stale:
        t = Table(box=box.SIMPLE, padding=(0, 2))
        t.add_column("File"); t.add_column("valid_to"); t.add_column("Title")
        for p in stale:
            t.add_row(
                f"[dim]{p['_file']}[/dim]",
                f"[yellow]{p.get('valid_to')}[/yellow]",
                str(p.get("title", "—"))
            )
        console.print(t)
        if args.fix:
            fixed = fix_expired(pages)
            console.print(f"  [green]✓ Fixed {fixed} pages (set is_valid: false)[/green]")
        else:
            console.print("  [dim]Run with --fix to auto-update is_valid → false[/dim]")
        total_issues += len(stale)
    else:
        console.print("  [green]✓ No stale validity entries[/green]")

    # ── Isolated nodes (no outbound links) ───────────────────────────────────
    section(f"Isolated Pages (no outbound relates_to/depends_on)  ({len(isolated)} pages)",
            "yellow" if isolated else "green")
    if isolated:
        t = Table(box=box.SIMPLE, padding=(0, 2))
        t.add_column("id"); t.add_column("Title")
        for p in isolated:
            t.add_row(str(p.get("id", "?")), str(p.get("title", "—")))
        console.print(t)
        total_issues += len(isolated)
    else:
        console.print("  [green]✓ All pages have outbound links[/green]")

    # ── Summary ──────────────────────────────────────────────────────────────
    colour = "green" if total_issues == 0 else "yellow" if total_issues <= 5 else "red"
    console.print(f"\n[bold {colour}]Total issues: {total_issues}[/bold {colour}]")

    return total_issues


# ── Skill lint ────────────────────────────────────────────────────────────────

SKILL_REQUIRED_SECTIONS = ["## Anti-patterns", "## Checklist"]
SKILL_SKIP_DIRS = {"_drafts", "_contract.md"}


def load_skills() -> list[dict]:
    """Scan skills/ for all active SKILL.md files (excludes _drafts/)."""
    skills = []
    for skill_md in sorted(SKILLS_DIR.glob("*/SKILL.md")):
        if any(skip in skill_md.parts for skip in SKILL_SKIP_DIRS):
            continue
        text = skill_md.read_text(encoding="utf-8")
        skills.append({"_path": skill_md, "_skill_id": skill_md.parent.name, "_text": text})
    return skills


def check_skill_sections(skills: list[dict]) -> list[dict]:
    """Skills missing required ## Anti-patterns or ## Checklist sections."""
    issues = []
    for s in skills:
        missing = [sec for sec in SKILL_REQUIRED_SECTIONS
                   if not re.search(rf"^{re.escape(sec)}", s["_text"], re.MULTILINE)]
        if missing:
            issues.append({**s, "_missing_sections": missing})
    return issues


def print_skill_report(skills: list[dict]) -> int:
    """Print skill lint report. Returns issue count."""
    total = 0
    section_issues = check_skill_sections(skills)

    console.print(Panel(
        f"[bold cyan]🔧 Skill Lint Report[/bold cyan]\n"
        f"[dim]{SKILLS_DIR}  ·  {len(skills)} skills checked[/dim]",
        box=box.DOUBLE_EDGE
    ))

    section(
        f"Missing Required Sections  ({len(section_issues)} skills)",
        "red" if section_issues else "green"
    )
    if section_issues:
        t = Table(box=box.SIMPLE, padding=(0, 2))
        t.add_column("Skill ID")
        t.add_column("Missing sections")
        for s in section_issues:
            t.add_row(
                f"[dim]{s['_skill_id']}[/dim]",
                f"[red]{', '.join(s['_missing_sections'])}[/red]"
            )
        console.print(t)
        total += len(section_issues)
    else:
        console.print("  [green]✓ All skills have required sections[/green]")

    colour = "green" if total == 0 else "red"
    console.print(f"\n[bold {colour}]Skill issues: {total}[/bold {colour}]")
    return total


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Wiki + Skill lint — check for structural issues")
    parser.add_argument("--strict", action="store_true",
                        help="Exit with code 1 if any issues found")
    parser.add_argument("--fix",    action="store_true",
                        help="Auto-fix: set is_valid=false for expired pages")
    parser.add_argument("--skills-only", action="store_true",
                        help="Only run skill lint, skip wiki lint")
    parser.add_argument("--wiki-only",   action="store_true",
                        help="Only run wiki lint, skip skill lint")
    args = parser.parse_args()

    total_issues = 0

    if not args.skills_only:
        pages = load_pages()
        total_issues += print_report(pages, args)

    if not args.wiki_only:
        skills = load_skills()
        total_issues += print_skill_report(skills)

    if args.strict and total_issues > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
