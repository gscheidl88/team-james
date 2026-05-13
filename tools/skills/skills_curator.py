#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""
skills_curator.py — Autonomous lifecycle manager for the skills/ directory.

Inspired by Hermes Agent v0.12.0 "The Curator Release" (NousResearch/hermes-agent).

Lifecycle:
    active  → stale   (after stale_after_days days unused)
    stale   → archived (after archive_after_days days unused)
    pinned skills are NEVER transitioned, even if unused.

Usage:
    uv run tools/skills/skills_curator.py --mode check     # Preview transitions only
    uv run tools/skills/skills_curator.py --mode apply     # Apply transitions to usage.json
    uv run tools/skills/skills_curator.py --mode check --json
    uv run tools/skills/skills_curator.py --pin daily-notes
    uv run tools/skills/skills_curator.py --unpin some-skill
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

VAULT = Path(__file__).resolve().parents[2]
SKILLS_DIR = VAULT / "skills"
USAGE_FILE = SKILLS_DIR / "usage.json"
REPORTS_DIR = VAULT / "memory" / "reviews"

STALE_AFTER_DAYS = 30
ARCHIVE_AFTER_DAYS = 90


def _load_usage() -> dict:
    if not USAGE_FILE.exists():
        return {"_meta": {}, "skills": {}}
    return json.loads(USAGE_FILE.read_text(encoding="utf-8"))


def _save_usage(data: dict) -> None:
    USAGE_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _today_iso() -> str:
    return date.today().isoformat()


def _days_since(iso_date: str | None) -> int | None:
    if not iso_date:
        return None
    try:
        last = date.fromisoformat(iso_date[:10])
        return (date.today() - last).days
    except ValueError:
        return None


def _discover_skills() -> list[str]:
    """Return sorted list of skill slugs (relative to SKILLS_DIR) that have a SKILL.md."""
    slugs = []
    for skill_md in sorted(SKILLS_DIR.rglob("SKILL.md")):
        rel = skill_md.parent.relative_to(SKILLS_DIR)
        slugs.append(str(rel).replace("\\", "/"))
    return slugs


def _sync_skills(data: dict) -> tuple[dict, list[str], list[str]]:
    """Add discovered skills missing from usage.json; return (updated_data, added, removed)."""
    known = set(data["skills"].keys())
    discovered = set(_discover_skills())

    added = []
    for slug in sorted(discovered - known):
        data["skills"][slug] = {
            "use_count": 0,
            "view_count": 0,
            "last_used_at": _today_iso(),  # bootstrap: treat newly discovered skills as used today
            "state": "active",
            "pinned": False,
        }
        added.append(slug)

    removed = sorted(known - discovered)
    return data, added, removed


def run_check(data: dict, apply: bool) -> dict:
    """Evaluate all skills, transition stale/archived if apply=True. Returns report dict."""
    transitions = []
    pinned_protected = []

    for slug, info in data["skills"].items():
        state = info.get("state", "active")
        pinned = info.get("pinned", False)
        last_used = info.get("last_used_at")
        days = _days_since(last_used)

        if pinned and state != "active":
            if apply:
                info["state"] = "active"
            pinned_protected.append(slug)
            continue

        if pinned:
            continue

        if state == "active":
            if days is None or days >= STALE_AFTER_DAYS:
                transitions.append({
                    "slug": slug,
                    "from": "active",
                    "to": "stale",
                    "reason": f"unused for {days if days is not None else 'never'} days (threshold: {STALE_AFTER_DAYS})",
                })
                if apply:
                    info["state"] = "stale"

        elif state == "stale":
            if days is None or days >= ARCHIVE_AFTER_DAYS:
                transitions.append({
                    "slug": slug,
                    "from": "stale",
                    "to": "archived",
                    "reason": f"unused for {days if days is not None else 'never'} days (threshold: {ARCHIVE_AFTER_DAYS})",
                })
                if apply:
                    info["state"] = "archived"

    state_counts = {"active": 0, "stale": 0, "archived": 0}
    for info in data["skills"].values():
        s = info.get("state", "active")
        state_counts[s] = state_counts.get(s, 0) + 1

    pinned_count = sum(1 for info in data["skills"].values() if info.get("pinned"))

    report = {
        "date": _today_iso(),
        "mode": "apply" if apply else "check",
        "total_skills": len(data["skills"]),
        "state_counts": state_counts,
        "pinned_count": pinned_count,
        "transitions": transitions,
        "pinned_protected": pinned_protected,
    }
    return report


def cmd_pin(slug: str, data: dict, unpin: bool) -> None:
    if slug not in data["skills"]:
        print(f"ERROR: skill '{slug}' not in usage.json. Run --mode apply to sync first.")
        sys.exit(1)
    data["skills"][slug]["pinned"] = not unpin
    if not unpin and data["skills"][slug].get("state") != "active":
        data["skills"][slug]["state"] = "active"
    _save_usage(data)
    action = "UNPINNED" if unpin else "PINNED"
    print(f"{action}: {slug}")


def print_report(report: dict, data: dict) -> None:
    mode_label = "APPLIED" if report["mode"] == "apply" else "PREVIEW"
    print(f"Skill Curator -- {report['date']} [{mode_label}]")
    print(f"  Total: {report['total_skills']}  |  "
          f"Active: {report['state_counts'].get('active', 0)}  |  "
          f"Stale: {report['state_counts'].get('stale', 0)}  |  "
          f"Archived: {report['state_counts'].get('archived', 0)}  |  "
          f"Pinned: {report['pinned_count']}")

    if report["transitions"]:
        print(f"\n  Transitions ({len(report['transitions'])}):")
        for t in report["transitions"]:
            arrow = f"{t['from']} -> {t['to']}"
            marker = "OK" if report["mode"] == "apply" else "WARN"
            print(f"    [{marker}] {t['slug']:<40} {arrow}  ({t['reason']})")
    else:
        print("\n  OK No transitions needed -- all skills within lifecycle thresholds.")

    if report["pinned_protected"]:
        print(f"\n  Pinned/protected: {', '.join(report['pinned_protected'])}")

    stale_slugs = [slug for slug, info in data["skills"].items() if info.get("state") == "stale"]
    if stale_slugs:
        print(f"\n  HINT Stale skills (consider using or pinning): {', '.join(stale_slugs[:5])}")


def write_report_artifact(report: dict) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORTS_DIR / "skills-curator.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Autonomous skill lifecycle manager (Hermes Curator pattern).")
    parser.add_argument("--mode", choices=["check", "apply"], default="check",
                        help="check=preview only, apply=write transitions to usage.json")
    parser.add_argument("--json", action="store_true", dest="json_out", help="Output report as JSON")
    parser.add_argument("--pin", metavar="SLUG", help="Pin a skill (protect from lifecycle transitions)")
    parser.add_argument("--unpin", metavar="SLUG", help="Unpin a skill")
    args = parser.parse_args()

    data = _load_usage()
    data, added, _removed = _sync_skills(data)

    if added:
        print(f"  SYNC: {len(added)} new skill(s) added to usage.json: {', '.join(added)}")

    if args.pin:
        cmd_pin(args.pin, data, unpin=False)
        return 0

    if args.unpin:
        cmd_pin(args.unpin, data, unpin=True)
        return 0

    apply_mode = args.mode == "apply"
    report = run_check(data, apply=apply_mode)

    if apply_mode:
        _save_usage(data)

    write_report_artifact(report)

    if args.json_out:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print_report(report, data)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
