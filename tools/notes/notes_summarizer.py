#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["python-dateutil"]
# ///
"""
notes_summarizer.py — Aggregate daily notes into weekly/monthly/annual summaries.

Usage:
    uv run tools/notes/notes_summarizer.py --weekly
    uv run tools/notes/notes_summarizer.py --monthly
    uv run tools/notes/notes_summarizer.py --annual
    uv run tools/notes/notes_summarizer.py --weekly --date 2026-04-07
"""

import argparse
import json
import random
import re
import shutil
import sys
from datetime import date, timedelta
from pathlib import Path

# ── Vault root = two levels up from this script ──────────────────────────────
VAULT = Path(__file__).resolve().parents[2]
DAILY_DIR   = VAULT / "PersonalNotes" / "Daily"
WEEKLY_DIR  = VAULT / "PersonalNotes" / "Weekly"
MONTHLY_DIR = VAULT / "PersonalNotes" / "Monthly"
ANNUAL_DIR  = VAULT / "PersonalNotes" / "Annual"
MEMORY_FILE = VAULT / "memory" / "MEMORY.md"
MEMORY_INDEX = VAULT / "memory" / "index.json"
REVIEWS_DIR = VAULT / "memory" / "reviews"

# ── Sections to extract from daily notes ─────────────────────────────────────
SECTIONS = {
    "achievements": re.compile(r"##\s+🏆\s+Achievements.*?(?=\n##|\Z)", re.S),
    "learnings":    re.compile(r"##\s+📚\s+Learnings.*?(?=\n##|\Z)", re.S),
    "tasks_done":   re.compile(r"##\s+📋\s+Tasks.*?(?=\n##|\Z)", re.S),
    "agent":        re.compile(r"##\s+🤖\s+Agent Sessions.*?(?=\n##|\Z)", re.S),
    "reflections":  re.compile(r"##\s+🔁\s+Reflections.*?(?=\n##|\Z)", re.S),
}


def extract_bullets(text: str) -> list[str]:
    """Pull non-empty bullet lines from a markdown block."""
    return [
        line.strip()
        for line in text.splitlines()
        if re.match(r"^\s*[-*]", line) and line.strip() not in ("-", "*", "- ", "* ")
    ]


def extract_checked_tasks(text: str) -> list[str]:
    """Pull completed tasks (- [x]) from a markdown block."""
    return [
        line.strip()
        for line in text.splitlines()
        if re.match(r"^\s*-\s+\[x\]", line, re.I)
    ]


def parse_daily_note(path: Path) -> dict[str, list[str]]:
    """Parse a daily note file and extract structured sections."""
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    result = {}
    for key, pattern in SECTIONS.items():
        match = pattern.search(text)
        if match:
            block = match.group(0)
            if key == "tasks_done":
                result[key] = extract_checked_tasks(block)
            else:
                result[key] = extract_bullets(block)
    return result


def get_week_dates(ref: date) -> list[date]:
    """Return Mon–Sun for the ISO week containing ref."""
    monday = ref - timedelta(days=ref.weekday())
    return [monday + timedelta(days=i) for i in range(7)]


def get_month_dates(ref: date) -> list[date]:
    """Return all dates in ref's month."""
    from dateutil.relativedelta import relativedelta
    start = ref.replace(day=1)
    end = (start + relativedelta(months=1)) - timedelta(days=1)
    days = (end - start).days + 1
    return [start + timedelta(days=i) for i in range(days)]


def get_year_dates_by_month(ref: date) -> dict[str, list[date]]:
    """Return dates grouped by month for ref's year."""
    from dateutil.relativedelta import relativedelta
    result = {}
    for m in range(1, 13):
        start = date(ref.year, m, 1)
        end = (start + relativedelta(months=1)) - timedelta(days=1)
        days = (end - start).days + 1
        label = start.strftime("%B")
        result[label] = [start + timedelta(days=i) for i in range(days)]
    return result


def format_section(title: str, items: list[str], emoji: str = "") -> str:
    if not items:
        return ""
    header = f"## {emoji} {title}".strip()
    bullets = "\n".join(f"- {item.lstrip('-* ').strip()}" for item in items if item.strip())
    return f"{header}\n\n{bullets}\n" if bullets else ""


def build_weekly_note(ref: date) -> str:
    week_dates = get_week_dates(ref)
    iso_year, iso_week, _ = ref.isocalendar()

    all_data: dict[str, list[str]] = {k: [] for k in SECTIONS}
    day_rows = []

    for d in week_dates:
        note_path = DAILY_DIR / f"{d.isoformat()}.md"
        data = parse_daily_note(note_path)
        exists = "✓" if note_path.exists() else "—"
        top_achievement = data.get("achievements", [""])[0] if data.get("achievements") else "—"
        day_rows.append(f"| {d.strftime('%a')} [[{d.isoformat()}]] | {top_achievement[:60]} | {exists} |")
        for key in all_data:
            all_data[key].extend(data.get(key, []))

    week_label = f"{iso_year}-W{iso_week:02d}"
    mon = week_dates[0].strftime("%d. %B")
    sun = week_dates[6].strftime("%d. %B %Y")

    lines = [
        f"---",
        f"created: {date.today().isoformat()}",
        f"week: {week_label}",
        f"period: weekly",
        f"tags: [weekly-note, {iso_year}]",
        f"generated: true",
        f"---",
        f"",
        f"# Week {iso_week:02d} · {iso_year}",
        f"",
        f"*{mon} – {sun}*",
        f"",
        f"---",
        f"",
        f"## 📅 Daily Overview",
        f"",
        f"| Day | Top Achievement | Note |",
        f"|-----|----------------|------|",
        *day_rows,
        f"",
    ]

    sections = [
        format_section("Achievements This Week", all_data["achievements"], "🏆"),
        format_section("Key Learnings", all_data["learnings"], "📚"),
        format_section("Completed Tasks", all_data["tasks_done"], "✅"),
        format_section("Agent Sessions Summary", all_data["agent"], "🤖"),
    ]

    lines += [s for s in sections if s]
    lines += [
        "---",
        "",
        "## 📊 Week in Review",
        "",
        "**What worked well:**",
        "",
        "**What to improve:**",
        "",
        "**Biggest win:**",
        "",
        "## 🎯 Focus for Next Week",
        "",
        "1. ",
        "2. ",
        "3. ",
        "",
    ]

    return "\n".join(lines)


def build_monthly_note(ref: date) -> str:
    month_dates = get_month_dates(ref)
    month_label = ref.strftime("%Y-%m")

    all_data: dict[str, list[str]] = {k: [] for k in SECTIONS}
    week_set: dict[str, list[str]] = {}

    for d in month_dates:
        note_path = DAILY_DIR / f"{d.isoformat()}.md"
        data = parse_daily_note(note_path)
        for key in all_data:
            all_data[key].extend(data.get(key, []))
        _, wn, _ = d.isocalendar()
        wk = f"{d.year}-W{wn:02d}"
        week_set.setdefault(wk, []).extend(data.get("achievements", []))

    week_rows = [
        f"| [[{wk}]] | {items[0][:60] if items else '—'} |"
        for wk, items in sorted(week_set.items())
    ]

    lines = [
        f"---",
        f"created: {date.today().isoformat()}",
        f"period: {month_label}",
        f"tags: [monthly-note, {ref.year}]",
        f"generated: true",
        f"---",
        f"",
        f"# {ref.strftime('%B %Y')}",
        f"",
        f"---",
        f"",
        f"## 📅 Weekly Highlights",
        f"",
        f"| Week | Top Achievement |",
        f"|------|----------------|",
        *week_rows,
        f"",
    ]

    sections = [
        format_section("Top Achievements", all_data["achievements"][:10], "🏆"),
        format_section("Major Learnings", all_data["learnings"][:10], "📚"),
        format_section("Completed Tasks", all_data["tasks_done"][:15], "✅"),
    ]

    lines += [s for s in sections if s]
    lines += [
        "---",
        "",
        "## 📊 Month in Review",
        "",
        "**Overall rating (1-10):**",
        "",
        "**Best decision:**",
        "",
        "**Biggest lesson:**",
        "",
        "## 🎯 Focus for Next Month",
        "",
        "1. ",
        "2. ",
        "3. ",
        "",
    ]

    return "\n".join(lines)


def build_annual_note(ref: date) -> str:
    months = get_year_dates_by_month(ref)
    all_data: dict[str, list[str]] = {k: [] for k in SECTIONS}
    month_rows = []

    for month_name, dates in months.items():
        month_data: dict[str, list[str]] = {k: [] for k in SECTIONS}
        for d in dates:
            note_path = DAILY_DIR / f"{d.isoformat()}.md"
            data = parse_daily_note(note_path)
            for key in month_data:
                month_data[key].extend(data.get(key, []))
        top = month_data["achievements"][0][:60] if month_data["achievements"] else "—"
        m_label = dates[0].strftime("%Y-%m")
        month_rows.append(f"| {month_name} [[{m_label}]] | {top} |")
        for key in all_data:
            all_data[key].extend(month_data.get(key, []))

    lines = [
        f"---",
        f"created: {date.today().isoformat()}",
        f"period: {ref.year}",
        f"tags: [annual-note, {ref.year}]",
        f"generated: true",
        f"---",
        f"",
        f"# Year in Review · {ref.year}",
        f"",
        f"---",
        f"",
        f"## 📅 Monthly Highlights",
        f"",
        f"| Month | Top Achievement |",
        f"|-------|----------------|",
        *month_rows,
        f"",
    ]

    sections = [
        format_section(f"Top Achievements of {ref.year}", all_data["achievements"][:10], "🏆"),
        format_section("Most Important Learnings", all_data["learnings"][:10], "📚"),
    ]

    lines += [s for s in sections if s]
    lines += [
        "---",
        "",
        "## 📊 Year in Review",
        "",
        "**Overall rating (1-10):**",
        "",
        "**The year in one sentence:**",
        "",
        "**Proudest moment:**",
        "",
        "**Biggest lesson:**",
        "",
        "## 🎯 Vision for Next Year",
        "",
        "1. ",
        "2. ",
        "3. ",
        "",
    ]

    return "\n".join(lines)


def write_note(path: Path, content: str, overwrite: bool = False) -> None:
    if path.exists() and not overwrite:
        print(f"  EXISTS (skipped): {path.name} — use --overwrite to replace")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"  WRITTEN: {path}")


# ── Dream consolidation ───────────────────────────────────────────────────────

_MEM_ID_RE    = re.compile(r'\[mem_(\d+)\]')
_UNCHECKED_RE = re.compile(r'^-\s+\[ \]\s+\S')
_AGENT_SEC_RE = re.compile(r'##[^\n]*[Aa]gent\s+[Ss]essions?.*?(?=\n##|\Z)', re.S)
_PROCEDURAL_HINT_RE = re.compile(r"\b(always|never|must|should|use|before|after|when|if|check|run|update|create|avoid|prefer)\b", re.I)


def _has_priority_marker(line: str) -> bool:
    """Return True if line contains ⚠️ PERMANENT, 🔥 HIGH, or 📌 PIN."""
    return (("⚠" in line) and "PERMANENT" in line) or \
           ("🔥" in line and "HIGH" in line) or \
           ("📌" in line and "PIN" in line)


def _is_placeholder(line: str) -> bool:
    """Return True for template filler lines with no real content."""
    s = line.strip()
    if not s:
        return True
    if s in ("-", "*", "- ", "* ", "- [ ]", "- [ ] ", "- [x]", "- [X]"):
        return True
    # Italic-only template hints like *(Quick thoughts...)*
    if s.startswith("*(") and s.endswith(")*"):
        return True
    return False


def _section_bullets_all(text: str, section_re: re.Pattern) -> list[str]:
    """Extract non-placeholder bullet content from ALL occurrences of a section."""
    results: list[str] = []
    for m in section_re.finditer(text):
        for line in m.group(0).splitlines():
            s = line.strip()
            if re.match(r'^[-*]\s', s) and not _is_placeholder(s):
                # Strip leading bullet + optional checkbox
                content = re.sub(r'^[-*]\s+(\[.\]\s+)?', '', s).strip()
                if len(content) > 5:
                    results.append(content)
    return results


def _agent_first_bullets(text: str) -> list[str]:
    """Return the first real bullet from each Agent Sessions block."""
    results: list[str] = []
    for m in _AGENT_SEC_RE.finditer(text):
        for line in m.group(0).splitlines():
            s = line.strip()
            if re.match(r'^[-*]\s', s) and not _is_placeholder(s):
                content = re.sub(r'^[-*]\s+(\[.\]\s+)?', '', s).strip()
                if len(content) > 5:
                    results.append(content)
                    break
    return results


def _next_mem_id(memory_text: str) -> int:
    """Return the next available mem_NNN number."""
    ids = [int(n) for n in _MEM_ID_RE.findall(memory_text)]
    return (max(ids) + 1) if ids else 1


def _normalize_entry(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", " ", text.lower())).strip()


def _recall_existing_memory(memory_text: str) -> str | None:
    # Prefer PIN-marked entries; fall back to any mem entry picked at random.
    lines = [
        line.strip()
        for line in memory_text.splitlines()
        if line.strip().startswith("- ") and "`[mem_" in line
    ]
    if not lines:
        return None
    pin_lines = [l for l in lines if "\U0001f4cc" in l and "PIN" in l]
    pool = pin_lines if pin_lines else lines
    return random.choice(pool)


def _extract_procedure_candidates(raw_entries: list[tuple[str, str]]) -> list[tuple[str, int, str]]:
    counts: dict[str, dict[str, object]] = {}
    for _, entry in raw_entries:
        normalized = _normalize_entry(entry)
        if len(normalized) < 12:
            continue
        bucket = counts.setdefault(
            normalized,
            {
                "count": 0,
                "text": entry,
                "procedural": bool(_PROCEDURAL_HINT_RE.search(entry)),
            },
        )
        bucket["count"] = int(bucket["count"]) + 1

    candidates: list[tuple[str, int, str]] = []
    for payload in counts.values():
        text = str(payload["text"])
        count = int(payload["count"])
        procedural = bool(payload["procedural"])
        if procedural or count >= 2:
            reason = "procedural-pattern" if procedural else "repeated-pattern"
            candidates.append((text, count, reason))

    candidates.sort(key=lambda item: (-item[1], item[0].lower()))
    return candidates[:12]


def _write_procedure_candidates(ref: date, candidates: list[tuple[str, int, str]]) -> None:
    if not candidates:
        return
    REVIEWS_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        f"created: {ref.isoformat()}",
        "kind: procedure-candidates",
        "---",
        "",
        "# Procedure candidates",
        "",
        "These items were extracted from recent daily notes and should be reviewed before promotion into procedures or skills.",
        "",
    ]
    for text, count, reason in candidates:
        target = "skills/" if "skill" in text.lower() else "memory/procedures.md"
        lines.append(f"- [{reason}] occurrences={count} target={target} {text}")
    (REVIEWS_DIR / "procedure-candidates.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _push_to_mnemosyne(entries: list[tuple[str, str]]) -> int:
    """Push new dream entries into Mnemosyne vector store (best-effort, silent on failure)."""
    import os
    import subprocess

    bin_path = Path(r"~\.local\bin\mnemosyne.exe")
    if not bin_path.exists():
        return 0
    env = {
        **os.environ,
        "MNEMOSYNE_DATA_DIR": str(VAULT / ".mnemosyne"),
        "HF_HUB_DISABLE_SYMLINKS_WARNING": "1",
    }
    pushed = 0
    for _dstr, entry in entries:
        try:
            r = subprocess.run(
                [str(bin_path), "store", entry, "dream-cycle", "0.8"],
                capture_output=True,
                text=True,
                env=env,
                timeout=15,
            )
            if r.returncode == 0:
                pushed += 1
        except Exception:
            pass
    return pushed


def run_dream(ref: date) -> None:
    """Dream consolidation: extract key entries from last 7 days → append to MEMORY.md."""
    scan_dates = [ref - timedelta(days=i) for i in range(7)]
    raw_entries: list[tuple[str, str]] = []
    notes_scanned = 0

    for d in scan_dates:
        note_path = DAILY_DIR / f"{d.isoformat()}.md"
        if not note_path.exists():
            continue
        notes_scanned += 1
        text = note_path.read_text(encoding="utf-8")
        dstr = d.isoformat()

        # Priority-marked lines (scan entire note)
        for line in text.splitlines():
            s = line.strip()
            if _has_priority_marker(s) and not _is_placeholder(s) and len(s) > 10:
                raw_entries.append((dstr, s.lstrip("-* ").strip()))

        # Achievements + Learnings bullets (all occurrences)
        for bullet in _section_bullets_all(text, SECTIONS["achievements"]):
            raw_entries.append((dstr, bullet))
        for bullet in _section_bullets_all(text, SECTIONS["learnings"]):
            raw_entries.append((dstr, bullet))

        # First bullet from each Agent Sessions block
        for bullet in _agent_first_bullets(text):
            raw_entries.append((dstr, bullet))

    procedure_candidates = _extract_procedure_candidates(raw_entries)
    _write_procedure_candidates(ref, procedure_candidates)

    # Load MEMORY.md
    mem_text = MEMORY_FILE.read_text(encoding="utf-8") if MEMORY_FILE.exists() else ""

    # Deduplicate against existing content and within batch
    seen: set[str] = set()
    new_entries: list[tuple[str, str]] = []
    for dstr, entry in raw_entries:
        fp = entry[:50].strip()
        if not fp or fp in mem_text or fp in seen:
            continue
        seen.add(fp)
        new_entries.append((dstr, entry))

    # Stale thread detection: unchecked tasks in notes 15–30 days old
    stale: list[tuple[str, str]] = []
    for i in range(15, 31):
        d = ref - timedelta(days=i)
        note_path = DAILY_DIR / f"{d.isoformat()}.md"
        if not note_path.exists():
            continue
        for line in note_path.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if _UNCHECKED_RE.match(s):
                stale.append((d.isoformat(), s))

    # Compute next ID before any writes so report IDs match written IDs
    next_id = _next_mem_id(mem_text)

    # Backup MEMORY.md if adding many entries
    if len(new_entries) > 5 and MEMORY_FILE.exists():
        shutil.copy2(MEMORY_FILE, MEMORY_FILE.parent / "MEMORY.md.bak")
        print(f"  BACKUP: MEMORY.md.bak created ({len(new_entries)} new entries)")

    # Append new entries to MEMORY.md
    if new_entries:
        section_lines = [f"\n## Dream Cycle — {ref.isoformat()} (auto-consolidated)\n"]
        for i, (dstr, entry) in enumerate(new_entries):
            mem_id = f"mem_{next_id + i:03d}"
            section_lines.append(f"- `[{mem_id}]` `[{dstr}]` {entry}")
        section_lines.append("")
        with MEMORY_FILE.open("a", encoding="utf-8") as f:
            f.write("\n".join(section_lines) + "\n")
        # Mnemosyne dual-write: mirror new entries into vector store
        _push_to_mnemosyne(new_entries)

    # ── Dream streak + growth metrics ────────────────────────────────────────
    index_data: dict = {}
    if MEMORY_INDEX.exists():
        try:
            index_data = json.loads(MEMORY_INDEX.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            index_data = {}

    last_dream = index_data.get("last_dream_date")
    yesterday = (ref - timedelta(days=1)).isoformat()
    streak = int(index_data.get("dream_streak", 0))
    if last_dream == yesterday or last_dream == ref.isoformat():
        streak += 1
    else:
        streak = 1  # reset

    # Current memory entry count
    mem_lines = MEMORY_FILE.read_text(encoding="utf-8").splitlines() if MEMORY_FILE.exists() else []
    current_count = sum(1 for l in mem_lines if l.strip().startswith("- "))
    last_count = int(index_data.get("entry_counts", {}).get("last_run_count", current_count))
    delta = current_count - last_count
    pct = (delta / last_count * 100) if last_count > 0 else 0

    # Update index
    index_data["dream_streak"] = streak
    index_data["last_dream_date"] = ref.isoformat()
    index_data.setdefault("entry_counts", {})
    index_data["entry_counts"]["last_run_count"] = current_count
    index_data["entry_counts"].setdefault("baseline_count", last_count)
    try:
        MEMORY_INDEX.write_text(json.dumps(index_data, indent=2, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass

    # ── Report ────────────────────────────────────────────────────────────────
    growth_str = f"{last_count} -> {current_count} entries (+{delta} / +{pct:.1f}%)" if delta > 0 else f"{current_count} entries (no change)"
    print(f"Dream Cycle -- {ref.isoformat()} | Streak: {streak} days | Memory: {growth_str}")
    print(f"  Scanned: {notes_scanned} daily notes | New: {len(new_entries)} entries | Stale threads: {len(stale)}")

    if new_entries:
        print("\n  New entries:")
        for i, (dstr, entry) in enumerate(new_entries):
            mem_id = f"mem_{next_id + i:03d}"
            display = entry[:80] + "..." if len(entry) > 80 else entry
            print(f"    [{mem_id}] {display}")
    else:
        recall = _recall_existing_memory(mem_text)
        if recall:
            print("\n  Smart recall:")
            print(f"    {recall[:120]}")

    if stale:
        print("\n  Stale threads (>14 days):")
        for dstr, task in stale:
            print(f"    {dstr}: {task}")

    if procedure_candidates:
        print(f"\n  Procedure candidates: {len(procedure_candidates)} -> memory\\reviews\\procedure-candidates.md")




def main() -> None:
    parser = argparse.ArgumentParser(description="Generate periodic summary notes")
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument("--weekly",  action="store_true", help="Generate weekly summary")
    group.add_argument("--monthly", action="store_true", help="Generate monthly summary")
    group.add_argument("--annual",  action="store_true", help="Generate annual summary")
    parser.add_argument("--dream",     action="store_true", help="Run dream consolidation cycle")
    parser.add_argument("--date",      default=None, help="Reference date YYYY-MM-DD (default: today)")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing note")
    args = parser.parse_args()

    if not any([args.weekly, args.monthly, args.annual, args.dream]):
        parser.error("One of --weekly, --monthly, --annual, or --dream is required.")

    ref = date.fromisoformat(args.date) if args.date else date.today()

    if args.dream:
        run_dream(ref)

    if args.weekly:
        if ref.weekday() != 6:  # 6 = Sunday; skip if not triggered on Sunday
            # Allow forced run via --date
            if not args.date:
                print(f"  SKIPPED: --weekly runs automatically on Sundays (today is {ref.strftime('%A')}). Use --date to force.")
                return
        _, iso_week, _ = ref.isocalendar()
        filename = f"{ref.year}-W{iso_week:02d}.md"
        content  = build_weekly_note(ref)
        write_note(WEEKLY_DIR / filename, content, args.overwrite)

    elif args.monthly:
        if ref.day != 1:
            if not args.date:
                print(f"  SKIPPED: --monthly runs automatically on the 1st (today is {ref.day}). Use --date to force.")
                return
        filename = f"{ref.strftime('%Y-%m')}.md"
        content  = build_monthly_note(ref)
        write_note(MONTHLY_DIR / filename, content, args.overwrite)

    elif args.annual:
        if not (ref.month == 1 and ref.day == 1):
            if not args.date:
                print(f"  SKIPPED: --annual runs automatically on Jan 1 (today is {ref.strftime('%b %d')}). Use --date to force.")
                return
        filename = f"{ref.year}.md"
        content  = build_annual_note(ref)
        write_note(ANNUAL_DIR / filename, content, args.overwrite)


if __name__ == "__main__":
    main()
