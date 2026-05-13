# Hardware Observability Tools

Host-side USB / PnP / storage enumeration for device maintenance and triage.

> **Scope:** These tools report what the **host PC can enumerate** via Windows APIs.
> They do NOT provide raw electrical USB-C diagnostics, firmware data, or
> information about the internal state of connected devices.

---

## Tools

| Tool | Purpose |
|------|---------|
| `usb_snapshot.py` | Capture current USB/PnP/storage state → JSON |
| `usb_diff.py` | Compare two snapshots, report added/removed/changed devices |

---

## Quick start

```powershell
# Take a snapshot (saved to tools\hardware\snapshots\<timestamp>.json)
uv run tools/hardware/usb_snapshot.py

# Take a snapshot with pretty-print JSON
uv run tools/hardware/usb_snapshot.py --pretty

# Specify output file
uv run tools/hardware/usb_snapshot.py --out snapshots/before.json

# Print summary only, no file written
uv run tools/hardware/usb_snapshot.py --no-save

# Diff two snapshots
uv run tools/hardware/usb_diff.py snapshots/before.json snapshots/after.json

# Self-diff smoke test (should report zero changes)
uv run tools/hardware/usb_diff.py snapshots/before.json snapshots/before.json

# Write diff to JSON as well
uv run tools/hardware/usb_diff.py before.json after.json --out diff.json

# JSON-only output (no human-readable text)
uv run tools/hardware/usb_diff.py before.json after.json --json-only
```

---

## Typical device-triage workflow

```
1. BEFORE connecting/disconnecting the device:
   uv run tools/hardware/usb_snapshot.py --out snapshots/before.json

2. Connect / disconnect / update the device

3. AFTER the change:
   uv run tools/hardware/usb_snapshot.py --out snapshots/after.json

4. Review what changed:
   uv run tools/hardware/usb_diff.py snapshots/before.json snapshots/after.json
```

The diff will show exactly which PnP device IDs appeared, disappeared, or had
their status updated — useful for confirming whether a USB-C cable is enumerating
correctly or whether a new drive was recognised.

---

## Data sources

| Section | Windows API | Notes |
|---------|------------|-------|
| `pnp_devices` | `Get-PnpDevice` | All PnP-enumerated devices; USB class highlighted |
| `usb_tree` | `Win32_USBControllerDevice` (CIM) | Controller→device attachment map |
| `disks` | `Get-Disk` | Physical disks: model, bus type, size, health |
| `volumes` | `Get-Volume` | Drive letters, labels, filesystem, free space |

---

## Snapshot JSON structure

```json
{
  "meta": {
    "timestamp": "2026-04-26T10:00:00+00:00",
    "host": "DESKTOP-XYZ",
    "tool": "usb_snapshot.py",
    "note": "Host-side enumeration only."
  },
  "pnp_devices": [ ... ],
  "usb_tree":    [ ... ],
  "disks":       [ ... ],
  "volumes":     [ ... ]
}
```

---

## Limitations

- **No raw USB-C electrical diagnostics** (speed negotiation, power delivery, Alt-Mode).
  For that, use `usbview.exe` (Windows SDK) or `USBTreeView`.
- **No SMART data.** Use `Get-StorageReliabilityCounter` or `CrystalDiskInfo` for drive health.
- **Bluetooth PAN / network adapters** appear as PnP devices but disk/volume data won't show.
- **Requires PowerShell** to be available on PATH (always true on modern Windows).
