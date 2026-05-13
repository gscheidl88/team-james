#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
usb_diff.py — Compare two USB/PnP/storage snapshots produced by usb_snapshot.py.

Shows:
  - Added / removed / changed PnP devices
  - Added / removed / changed disks
  - Added / removed / changed volumes
  - Added / removed USB tree links

Usage:
    uv run tools/hardware/usb_diff.py BEFORE.json AFTER.json
    uv run tools/hardware/usb_diff.py BEFORE.json AFTER.json --out diff.json
    uv run tools/hardware/usb_diff.py BEFORE.json AFTER.json --json-only

    # Self-diff smoke test (should show zero changes):
    uv run tools/hardware/usb_diff.py snap.json snap.json
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Generic keyed-list differ
# ---------------------------------------------------------------------------

def _diff_records(
    before: list[dict],
    after: list[dict],
    key_field: str,
    ignore_fields: set[str] | None = None,
) -> dict:
    """
    Diff two lists of dicts by key_field.
    Returns {'added': [...], 'removed': [...], 'changed': [...], 'unchanged_count': int}
    """
    ignore_fields = ignore_fields or set()

    before_map = {r[key_field]: r for r in before if r.get(key_field)}
    after_map  = {r[key_field]: r for r in after  if r.get(key_field)}

    added_keys   = set(after_map) - set(before_map)
    removed_keys = set(before_map) - set(after_map)
    common_keys  = set(before_map) & set(after_map)

    added   = [after_map[k]  for k in sorted(added_keys)]
    removed = [before_map[k] for k in sorted(removed_keys)]

    changed = []
    unchanged = 0
    for k in sorted(common_keys):
        b = {f: v for f, v in before_map[k].items() if f not in ignore_fields}
        a = {f: v for f, v in after_map[k].items()  if f not in ignore_fields}
        if b != a:
            diffs = {}
            all_fields = set(b) | set(a)
            for f in sorted(all_fields):
                bv, av = b.get(f), a.get(f)
                if bv != av:
                    diffs[f] = {"before": bv, "after": av}
            changed.append({key_field: k, "changes": diffs})
        else:
            unchanged += 1

    return {
        "added": added,
        "removed": removed,
        "changed": changed,
        "unchanged_count": unchanged,
    }


# ---------------------------------------------------------------------------
# USB tree differ (set of (controller, dependent) tuples)
# ---------------------------------------------------------------------------

def _diff_usb_tree(before: list[dict], after: list[dict]) -> dict:
    def to_set(records: list[dict]) -> set[tuple]:
        return {(r.get("controller", ""), r.get("dependent", "")) for r in records}

    b_set = to_set(before)
    a_set = to_set(after)

    return {
        "added":   [{"controller": c, "dependent": d} for c, d in sorted(a_set - b_set)],
        "removed": [{"controller": c, "dependent": d} for c, d in sorted(b_set - a_set)],
        "unchanged_count": len(b_set & a_set),
    }


# ---------------------------------------------------------------------------
# Pretty printer
# ---------------------------------------------------------------------------

_RESET  = "\033[0m"
_GREEN  = "\033[32m"
_RED    = "\033[31m"
_YELLOW = "\033[33m"
_BOLD   = "\033[1m"
_DIM    = "\033[2m"

def _c(text: str, code: str) -> str:
    """Wrap text in ANSI colour if stdout is a TTY."""
    if sys.stdout.isatty():
        return f"{code}{text}{_RESET}"
    return text


def _section(title: str) -> None:
    print(f"\n{_c(title, _BOLD)}")
    print(_c("─" * 60, _DIM))


def _print_record(record: dict, prefix: str = "", color: str = "") -> None:
    line = "  " + prefix + "  "
    line += "  ".join(
        f"{k}={v!r}"
        for k, v in record.items()
        if v not in (None, "", False, 0)
    )
    print(_c(line, color))


def _print_changes(item: dict, key_field: str) -> None:
    key_val = item.get(key_field, "?")
    print(f"  {_c('~', _YELLOW)}  {key_field}={key_val!r}")
    for field, delta in item.get("changes", {}).items():
        bv = repr(delta["before"])
        av = repr(delta["after"])
        print(f"       {field}: {_c(bv, _RED)} → {_c(av, _GREEN)}")


def print_diff_section(
    title: str,
    diff: dict,
    key_field: str,
    summary_fields: list[str] | None = None,
) -> None:
    added   = diff["added"]
    removed = diff["removed"]
    changed = diff.get("changed", [])
    unch    = diff.get("unchanged_count", 0)

    total_delta = len(added) + len(removed) + len(changed)
    status = _c(f"  +{len(added)}  -{len(removed)}  ~{len(changed)}  ={unch}", _DIM)
    _section(f"{title}  {status}")

    if total_delta == 0:
        print(_c("  ✓ No changes", _DIM))
        return

    for r in added:
        label = " | ".join(str(r.get(f, "")) for f in (summary_fields or [key_field]))
        print(_c(f"  +  {label}", _GREEN))

    for r in removed:
        label = " | ".join(str(r.get(f, "")) for f in (summary_fields or [key_field]))
        print(_c(f"  -  {label}", _RED))

    for item in changed:
        _print_changes(item, key_field)


def print_usb_tree_section(diff: dict) -> None:
    added   = diff["added"]
    removed = diff["removed"]
    unch    = diff["unchanged_count"]
    status  = _c(f"  +{len(added)}  -{len(removed)}  ={unch}", _DIM)
    _section(f"USB tree links  {status}")

    if not added and not removed:
        print(_c("  ✓ No changes", _DIM))
        return

    for r in added:
        print(_c(f"  +  {r['controller']} → {r['dependent']}", _GREEN))
    for r in removed:
        print(_c(f"  -  {r['controller']} → {r['dependent']}", _RED))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def load_snapshot(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"[ERROR] File not found: {path}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as exc:
        print(f"[ERROR] Invalid JSON in {path}: {exc}", file=sys.stderr)
        sys.exit(1)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Diff two usb_snapshot.py JSON files."
    )
    parser.add_argument("before", metavar="BEFORE.json")
    parser.add_argument("after",  metavar="AFTER.json")
    parser.add_argument(
        "--out", metavar="FILE",
        help="Write structured diff to JSON file",
    )
    parser.add_argument(
        "--json-only", action="store_true",
        help="Suppress human-readable output, print raw diff JSON to stdout",
    )
    args = parser.parse_args()

    before = load_snapshot(Path(args.before))
    after  = load_snapshot(Path(args.after))

    b_meta = before.get("meta", {})
    a_meta = after.get("meta", {})

    diff = {
        "meta": {
            "before_file": args.before,
            "after_file":  args.after,
            "before_time": b_meta.get("timestamp"),
            "after_time":  a_meta.get("timestamp"),
            "before_host": b_meta.get("host"),
            "after_host":  a_meta.get("host"),
        },
        "pnp_devices": _diff_records(
            before.get("pnp_devices", []),
            after.get("pnp_devices", []),
            key_field="device_id",
        ),
        "usb_tree": _diff_usb_tree(
            before.get("usb_tree", []),
            after.get("usb_tree", []),
        ),
        "disks": _diff_records(
            before.get("disks", []),
            after.get("disks", []),
            key_field="disk_key",
        ),
        "volumes": _diff_records(
            before.get("volumes", []),
            after.get("volumes", []),
            key_field="volume_key",
            ignore_fields={"free_bytes", "free_gb"},
        ),
    }

    if args.json_only:
        print(json.dumps(diff, indent=2, ensure_ascii=False))
        return 0

    # Human-readable output
    meta = diff["meta"]
    print(f"\n{'='*60}")
    print(f"  USB/PnP Snapshot Diff")
    print(f"{'='*60}")
    print(f"  Before: {meta['before_time']}  ({meta['before_host']})")
    print(f"  After:  {meta['after_time']}  ({meta['after_host']})")
    print(f"  Files:  {Path(args.before).name}  →  {Path(args.after).name}")
    before_status = before.get("meta", {}).get("capture_status", "unknown")
    after_status = after.get("meta", {}).get("capture_status", "unknown")
    print(f"  Capture: {before_status}  →  {after_status}")

    for side_name, snapshot in (("before", before), ("after", after)):
        section_errors = snapshot.get("meta", {}).get("section_errors", {})
        if section_errors:
            print(f"  Warning: {side_name} snapshot is partial")
            for section, error in section_errors.items():
                print(f"           {section}: {error}")

    print_diff_section(
        "PnP Devices",
        diff["pnp_devices"],
        key_field="device_id",
        summary_fields=["friendly_name", "class", "status", "device_id"],
    )
    print_usb_tree_section(diff["usb_tree"])
    print_diff_section(
        "Physical Disks",
        diff["disks"],
        key_field="disk_key",
        summary_fields=["model", "bus_type", "size_gb", "health_status", "serial_number"],
    )
    print_diff_section(
        "Volumes",
        diff["volumes"],
        key_field="volume_key",
        summary_fields=["drive_letter", "label", "filesystem", "size_gb", "path"],
    )

    # Overall verdict
    total_changes = sum(
        len(diff[sec].get("added", [])) +
        len(diff[sec].get("removed", [])) +
        len(diff[sec].get("changed", []))
        for sec in ("pnp_devices", "disks", "volumes")
    ) + len(diff["usb_tree"]["added"]) + len(diff["usb_tree"]["removed"])

    print(f"\n{'─'*60}")
    if total_changes == 0:
        print(_c("  ✓ Snapshots are identical — no hardware changes detected.", _GREEN))
    else:
        print(_c(f"  ⚠  {total_changes} change(s) detected across all categories.", _YELLOW))
    print()

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(diff, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"Diff written → {out_path}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
