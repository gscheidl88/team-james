#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""
memory_maintenance.py - compute reinforcement and archive recommendations for MEMORY.md.
"""

from __future__ import annotations

import argparse
from datetime import date, datetime
from pathlib import Path

from memory_common import (
    REVIEWS_DIR,
    compute_importance,
    fingerprint,
    marker_kind,
    parse_memory_entries,
    recent_access_counts,
    relpath,
    write_json,
    atomic_write,
    MEMORY_FILE,
)


def build_reports() -> tuple[dict[str, object], str]:
    entries = parse_memory_entries()
    counts = recent_access_counts(days=180)
    today = date.today()

    reinforcement: list[dict[str, object]] = []
    archive_candidates: list[dict[str, object]] = []

    for entry in entries:
        marker = marker_kind(entry.text)
        age_days = (today - entry.entry_date).days if entry.entry_date else 365
        key = f"{relpath(MEMORY_FILE)}::{fingerprint(entry.text)}"
        reference_count = counts.get(key, 0)
        last_reference_days = 0 if reference_count > 0 else age_days
        importance = compute_importance(last_reference_days, reference_count, marker)
        payload = {
            "mem_id": entry.mem_id,
            "line_no": entry.line_no,
            "entry_date": entry.entry_date.isoformat() if entry.entry_date else None,
            "marker": marker,
            "references": reference_count,
            "importance": importance,
            "text": entry.text,
        }

        if reference_count >= 2 or (marker in {"high", "pin", "permanent"} and reference_count >= 1):
            reinforcement.append(payload)
        if entry.entry_date and marker not in {"pin", "permanent"} and age_days > 90 and importance < 0.3:
            archive_candidates.append(payload)

    reinforcement.sort(key=lambda item: (-int(item["references"]), -float(item["importance"])))
    archive_candidates.sort(key=lambda item: (float(item["importance"]), -int(item["references"])))

    summary = {
        "created": datetime.now().isoformat(timespec="seconds"),
        "memory_entries": len(entries),
        "reinforcement_candidates": len(reinforcement),
        "archive_candidates": len(archive_candidates),
        "top_reinforcement": reinforcement[:10],
        "top_archive_candidates": archive_candidates[:10],
    }

    lines = [
        "---",
        f"created: {summary['created']}",
        "kind: memory-maintenance",
        "---",
        "",
        "# Memory maintenance recommendations",
        "",
        f"- **Memory entries:** {len(entries)}",
        f"- **Reinforcement candidates:** {len(reinforcement)}",
        f"- **Archive candidates:** {len(archive_candidates)}",
        "",
        "## Reinforcement candidates",
        "",
    ]
    if reinforcement:
        for item in reinforcement[:10]:
            lines.append(
                f"- [{item['importance']}] refs={item['references']} line={item['line_no']} — {item['text']}"
            )
    else:
        lines.append("- No reinforcement candidates.")

    lines.extend(["", "## Archive candidates", ""])
    if archive_candidates:
        for item in archive_candidates[:10]:
            lines.append(
                f"- [{item['importance']}] refs={item['references']} line={item['line_no']} — {item['text']}"
            )
    else:
        lines.append("- No archive candidates.")

    return summary, "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute reinforcement and archive recommendations for memory.")
    parser.add_argument("--markdown-out", help="Optional markdown output path")
    parser.add_argument("--json-out", help="Optional JSON output path")
    args = parser.parse_args()

    summary, markdown = build_reports()
    markdown_out = Path(args.markdown_out) if args.markdown_out else REVIEWS_DIR / "memory-maintenance.md"
    json_out = Path(args.json_out) if args.json_out else REVIEWS_DIR / "memory-maintenance.json"
    atomic_write(markdown_out, markdown)
    write_json(json_out, summary)

    print(f"MARKDOWN: {markdown_out}")
    print(f"JSON: {json_out}")
    print(f"REINFORCEMENT: {summary['reinforcement_candidates']}")
    print(f"ARCHIVE: {summary['archive_candidates']}")


if __name__ == "__main__":
    main()
