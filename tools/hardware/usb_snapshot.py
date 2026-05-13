#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
usb_snapshot.py — Capture host-visible USB/PnP/storage state into structured JSON.

This tool only observes what the HOST PC can enumerate via Windows APIs.
It does NOT provide raw electrical USB-C diagnostics, firmware-level data,
or any information about the internal state of connected devices.

Data sources:
  - Get-PnpDevice    → all PnP-enumerated devices (USB subset highlighted)
  - Get-CimInstance Win32_USBControllerDevice → USB attachment tree
  - Get-Disk         → physical disk descriptors
  - Get-Volume       → volume/partition assignments

Usage:
    uv run tools/hardware/usb_snapshot.py
    uv run tools/hardware/usb_snapshot.py --out snapshots/before.json
    uv run tools/hardware/usb_snapshot.py --pretty
"""

import argparse
import datetime
import json
import socket
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SNAPSHOT_DIR = SCRIPT_DIR / "snapshots"


# ---------------------------------------------------------------------------
# PowerShell helpers
# ---------------------------------------------------------------------------

def _run_ps(script: str, label: str, required_commands: list[str]) -> dict:
    """Run a PowerShell fragment that produces JSON and return capture metadata."""
    # Force UTF-8 output so device names with non-ASCII chars survive the pipe.
    utf8_preamble = (
        "[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new();\n"
        "$OutputEncoding = [System.Text.UTF8Encoding]::new();\n"
        "$ErrorActionPreference = 'Stop';\n"
    )
    command_checks = "\n".join(
        f"if (-not (Get-Command {command} -ErrorAction SilentlyContinue)) "
        f"{{ throw 'Missing PowerShell command: {command}' }}"
        for command in required_commands
    )
    cmd = [
        "powershell.exe",
        "-NoProfile",
        "-NonInteractive",
        "-Command",
        utf8_preamble + command_checks + "\n" + script,
    ]
    result_meta = {
        "status": "ok",
        "records": [],
        "record_count": 0,
        "required_commands": required_commands,
        "error": "",
    }
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60,
        )
    except FileNotFoundError:
        error = "powershell.exe not found"
        print(f"[WARN] {error} — skipping {label}", file=sys.stderr)
        result_meta["status"] = "error"
        result_meta["error"] = error
        return result_meta
    except subprocess.TimeoutExpired:
        error = f"PowerShell timed out for {label}"
        print(f"[WARN] {error}", file=sys.stderr)
        result_meta["status"] = "error"
        result_meta["error"] = error
        return result_meta

    stdout_text = result.stdout.decode("utf-8", errors="replace")
    stderr_text = result.stderr.decode("utf-8", errors="replace")

    if result.returncode != 0:
        error = stderr_text.strip() or f"{label} exited with code {result.returncode}"
        print(f"[WARN] {label}: {error[:300]}", file=sys.stderr)
        result_meta["status"] = "error"
        result_meta["error"] = error[:1000]
        return result_meta

    raw = stdout_text.strip()
    if not raw:
        result_meta["status"] = "empty"
        return result_meta

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"[WARN] Could not parse JSON for {label}: {exc}", file=sys.stderr)
        result_meta["status"] = "error"
        result_meta["error"] = f"Could not parse JSON for {label}: {exc}"
        return result_meta

    records = data if isinstance(data, list) else [data]
    result_meta["records"] = records
    result_meta["record_count"] = len(records)
    return result_meta


# ---------------------------------------------------------------------------
# Individual collection functions
# ---------------------------------------------------------------------------

def collect_pnp_devices() -> list[dict]:
    """All PnP devices with class, status, and device ID."""
    script = r"""
$devs = @(Get-PnpDevice |
    Select-Object -Property FriendlyName, Class, Status,
                            DeviceID, Manufacturer, Present |
    Sort-Object Class, FriendlyName)
$devs | ConvertTo-Json -Depth 3 -Compress
"""
    return _run_ps(script, "PnpDevice", ["Get-PnpDevice"])


def collect_usb_tree() -> list[dict]:
    """USB controller → device attachment tree via Win32_USBControllerDevice."""
    script = r"""
$links = @(Get-CimInstance Win32_USBControllerDevice |
    Select-Object @{n='Controller';e={$_.Antecedent.DeviceID}},
                  @{n='Dependent';e={$_.Dependent.DeviceID}})
$links | ConvertTo-Json -Depth 3 -Compress
"""
    return _run_ps(script, "USBTree", ["Get-CimInstance"])


def collect_disks() -> list[dict]:
    """Physical disks: number, model, size, bus type, health."""
    script = r"""
$disks = @(Get-Disk |
    Select-Object Number, FriendlyName, Manufacturer, Model,
                  Size, BusType, HealthStatus, OperationalStatus,
                  PartitionStyle, IsReadOnly, SerialNumber)
$disks | ConvertTo-Json -Depth 3 -Compress
"""
    return _run_ps(script, "Disk", ["Get-Disk"])


def collect_volumes() -> list[dict]:
    """Volumes/partitions: drive letter, label, FS, size, free space."""
    script = r"""
$vols = @(Get-Volume |
    Select-Object DriveLetter, FileSystemLabel, FileSystem,
                  DriveType, HealthStatus, OperationalStatus,
                  Size, SizeRemaining, Path)
$vols | ConvertTo-Json -Depth 3 -Compress
"""
    return _run_ps(script, "Volume", ["Get-Volume"])


# ---------------------------------------------------------------------------
# Normalisation helpers
# ---------------------------------------------------------------------------

def _str(v) -> str:
    return str(v).strip() if v is not None else ""


def normalise_pnp(raw: list[dict], *, include_nonpresent: bool = False) -> list[dict]:
    out = []
    for d in raw:
        present = bool(d.get("Present"))
        if not include_nonpresent and not present:
            continue
        out.append({
            "friendly_name": _str(d.get("FriendlyName")),
            "class": _str(d.get("Class")),
            "status": _str(d.get("Status")),
            "device_id": _str(d.get("DeviceID")),
            "manufacturer": _str(d.get("Manufacturer")),
            "present": present,
        })
    return out


def normalise_usb_tree(raw: list[dict]) -> list[dict]:
    out = []
    for d in raw:
        out.append({
            "controller": _str(d.get("Controller")),
            "dependent": _str(d.get("Dependent")),
        })
    return out


def normalise_disks(raw: list[dict]) -> list[dict]:
    out = []
    for d in raw:
        size_bytes = d.get("Size")
        try:
            size_gb = round(int(size_bytes) / (1024 ** 3), 2) if size_bytes else None
        except (TypeError, ValueError):
            size_gb = None
        serial_number = _str(d.get("SerialNumber"))
        disk_key = serial_number or "|".join([
            _str(d.get("BusType")),
            _str(d.get("Model")),
            _str(d.get("FriendlyName")),
            _str(size_bytes),
        ])
        out.append({
            "disk_key": disk_key,
            "number": d.get("Number"),
            "friendly_name": _str(d.get("FriendlyName")),
            "model": _str(d.get("Model")),
            "manufacturer": _str(d.get("Manufacturer")),
            "size_bytes": size_bytes,
            "size_gb": size_gb,
            "bus_type": _str(d.get("BusType")),
            "health_status": _str(d.get("HealthStatus")),
            "operational_status": _str(d.get("OperationalStatus")),
            "partition_style": _str(d.get("PartitionStyle")),
            "is_readonly": bool(d.get("IsReadOnly")),
            "serial_number": serial_number,
        })
    return out


def normalise_volumes(raw: list[dict]) -> list[dict]:
    out = []
    for d in raw:
        size = d.get("Size")
        remaining = d.get("SizeRemaining")
        try:
            size_gb = round(int(size) / (1024 ** 3), 2) if size else None
        except (TypeError, ValueError):
            size_gb = None
        try:
            free_gb = round(int(remaining) / (1024 ** 3), 2) if remaining else None
        except (TypeError, ValueError):
            free_gb = None
        path = _str(d.get("Path"))
        volume_key = path or "|".join([
            _str(d.get("DriveLetter")),
            _str(d.get("FileSystemLabel")),
            _str(size),
        ])
        out.append({
            "volume_key": volume_key,
            "drive_letter": _str(d.get("DriveLetter")),
            "label": _str(d.get("FileSystemLabel")),
            "filesystem": _str(d.get("FileSystem")),
            "drive_type": _str(d.get("DriveType")),
            "health_status": _str(d.get("HealthStatus")),
            "operational_status": _str(d.get("OperationalStatus")),
            "size_bytes": size,
            "size_gb": size_gb,
            "free_bytes": remaining,
            "free_gb": free_gb,
            "path": path,
        })
    return out


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def build_snapshot() -> dict:
    print("Collecting PnP devices …", file=sys.stderr)
    pnp_capture = collect_pnp_devices()

    print("Collecting USB tree …", file=sys.stderr)
    usb_capture = collect_usb_tree()

    print("Collecting disks …", file=sys.stderr)
    disk_capture = collect_disks()

    print("Collecting volumes …", file=sys.stderr)
    volume_capture = collect_volumes()

    sections = {
        "pnp_devices": pnp_capture,
        "usb_tree": usb_capture,
        "disks": disk_capture,
        "volumes": volume_capture,
    }
    section_status = {
        name: {
            "status": result["status"],
            "record_count": result["record_count"],
            "required_commands": result["required_commands"],
            "error": result["error"],
        }
        for name, result in sections.items()
    }
    section_errors = {
        name: result["error"]
        for name, result in sections.items()
        if result["error"]
    }
    capture_status = "ok" if not section_errors else "partial"

    return {
        "meta": {
            "schema_version": 1,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "host": socket.gethostname(),
            "tool": "usb_snapshot.py",
            "note": (
                "Host-side enumeration only. "
                "No raw electrical or firmware diagnostics."
            ),
            "capture_status": capture_status,
            "section_status": section_status,
            "section_errors": section_errors,
            "filters": {
                "include_nonpresent_pnp": False,
            },
        },
        "pnp_devices": normalise_pnp(pnp_capture["records"]),
        "usb_tree": normalise_usb_tree(usb_capture["records"]),
        "disks": normalise_disks(disk_capture["records"]),
        "volumes": normalise_volumes(volume_capture["records"]),
    }


def print_summary(snapshot: dict) -> None:
    meta = snapshot["meta"]
    pnp = snapshot["pnp_devices"]
    disks = snapshot["disks"]
    vols = snapshot["volumes"]

    usb_devices = [d for d in pnp if "USB" in d.get("class", "").upper()
                   or "USB" in d.get("device_id", "").upper()]

    print(f"\n{'='*60}")
    print(f"  Snapshot — {meta['host']}  @  {meta['timestamp']}")
    print(f"{'='*60}")
    print(f"  Capture status    : {meta['capture_status']}")
    print(f"  PnP devices total : {len(pnp)}")
    print(f"  USB-class devices : {len(usb_devices)}")
    print(f"  Physical disks    : {len(disks)}")
    print(f"  Volumes           : {len(vols)}")

    if meta["section_errors"]:
        print("\n  Section errors:")
        for name, error in meta["section_errors"].items():
            print(f"    {name}: {error}")

    if disks:
        print("\n  Disks:")
        for d in disks:
            gb = f"{d['size_gb']} GB" if d["size_gb"] else "?"
            print(f"    [{d['number']}] {d['model'] or d['friendly_name']} "
                  f"({d['bus_type']}, {gb}, {d['health_status']})")

    if vols:
        print("\n  Volumes:")
        for v in vols:
            letter = v["drive_letter"] or "-"
            label = v["label"] or "(no label)"
            free = f"{v['free_gb']} GB free" if v["free_gb"] is not None else "?"
            size = f"{v['size_gb']} GB" if v["size_gb"] else "?"
            print(f"    {letter}:  {label}  {v['filesystem']}  {size}  [{free}]")

    print()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Capture host-visible USB/PnP/storage state into JSON."
    )
    parser.add_argument(
        "--out", metavar="FILE",
        help="Output JSON file path (default: snapshots/YYYY-MM-DDTHH-MM-SS.json)",
    )
    parser.add_argument(
        "--pretty", action="store_true",
        help="Write indented JSON (default: compact)",
    )
    parser.add_argument(
        "--no-save", action="store_true",
        help="Print summary only, do not write file",
    )
    args = parser.parse_args()

    snapshot = build_snapshot()
    print_summary(snapshot)

    if args.no_save:
        return 0

    if args.out:
        out_path = Path(args.out)
    else:
        SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        out_path = SNAPSHOT_DIR / f"{ts}.json"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    indent = 2 if args.pretty else None
    out_path.write_text(
        json.dumps(snapshot, indent=indent, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Snapshot written → {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
