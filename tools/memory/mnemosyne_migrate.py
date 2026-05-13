#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
mnemosyne_migrate.py — One-time migration: MEMORY.md → Mnemosyne vector store.

Reads every meaningful bullet from MEMORY.md and stores it in Mnemosyne
so future semantic recall can find it. Deduplication is done by Mnemosyne.

Usage:
    uv run tools/memory/mnemosyne_migrate.py [--dry-run] [--limit N]
"""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

VAULT = Path(__file__).resolve().parents[2]
MEMORY_FILE = VAULT / "memory" / "MEMORY.md"
MNEMOSYNE_BIN = Path(r"~\.local\bin\mnemosyne.exe")
MNEMOSYNE_DATA_DIR = str(VAULT / ".mnemosyne")

_MEM_ID_RE = re.compile(r"`\[mem_\d+\]`\s+`\[\d{4}-\d{2}-\d{2}\]`\s+(.+)")
_BULLET_RE = re.compile(r"^[-*]\s+(.+)$")


def extract_entries(text: str) -> list[str]:
    """Extract meaningful content lines from MEMORY.md."""
    entries: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        # Prefer structured mem_NNN entries (preserve date context if possible)
        m = _MEM_ID_RE.search(s)
        if m:
            entries.append(m.group(1).strip())
            continue
        # Fall back to any bullet with enough content
        m = _BULLET_RE.match(s)
        if m:
            content = m.group(1).strip()
            if len(content) > 20 and not content.startswith("`["):
                entries.append(content)
    return entries


def store_entry(content: str, dry_run: bool) -> bool:
    if dry_run:
        short = content[:80] + "..." if len(content) > 80 else content
        print(f"  [DRY] {short}")
        return True
    env = {
        **os.environ,
        "MNEMOSYNE_DATA_DIR": MNEMOSYNE_DATA_DIR,
        "HF_HUB_DISABLE_SYMLINKS_WARNING": "1",
    }
    result = subprocess.run(
        [str(MNEMOSYNE_BIN), "store", content, "memory-md-import", "0.7"],
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )
    return result.returncode == 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate MEMORY.md entries to Mnemosyne")
    parser.add_argument("--dry-run", action="store_true", help="Print entries without storing")
    parser.add_argument("--limit", type=int, default=0, help="Max entries to process (0 = all)")
    args = parser.parse_args()

    if not MEMORY_FILE.exists():
        print(f"ERROR: {MEMORY_FILE} not found", file=sys.stderr)
        sys.exit(1)

    if not MNEMOSYNE_BIN.exists() and not args.dry_run:
        print(f"ERROR: mnemosyne binary not found at {MNEMOSYNE_BIN}", file=sys.stderr)
        sys.exit(1)

    text = MEMORY_FILE.read_text(encoding="utf-8")
    entries = extract_entries(text)

    if args.limit:
        entries = entries[: args.limit]

    print(f"Mnemosyne Migration -- MEMORY.md -> vector store")
    print(f"Found {len(entries)} entries")
    if args.dry_run:
        print("DRY RUN — nothing will be stored\n")

    ok, failed = 0, 0
    for i, entry in enumerate(entries, 1):
        success = store_entry(entry, args.dry_run)
        if success:
            ok += 1
            if not args.dry_run:
                print(f"  [{i}/{len(entries)}] ✓")
        else:
            failed += 1
            short = entry[:60]
            print(f"  [{i}/{len(entries)}] ✗ FAILED: {short}")

    print(f"\nDone — {ok} stored, {failed} failed")


if __name__ == "__main__":
    main()
