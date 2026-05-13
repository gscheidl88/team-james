---
name: hardware-triage
description: "Host-side USB, PnP, disk, and volume observability workflow for before/after device triage on Windows"
agent: James
tools_required: [uv, powershell]
wiki_ref: "[[autonomic-tooling-pattern]]"
version: "1.0"
---

# Skill: Hardware Triage

**Category:** Operations  
**Trigger:** Device maintenance, USB troubleshooting, storage visibility checks, before/after host comparisons  
**Owner:** James / Developer

---

## Purpose

Use this skill when James needs a reliable, host-visible picture of USB, PnP, disk, and volume state on Windows.

This is an **observability aid**, not a firmware or cable diagnostics tool.

---

## What This Skill Can Confirm

- whether Windows currently enumerates a USB/PnP device
- whether disks or volumes appeared, disappeared, or changed
- whether a snapshot was only partially captured because a PowerShell/CIM source failed

## What This Skill Cannot Confirm

- raw USB-C electrical health
- cable quality
- firmware-level recovery state of a broken device
- direct access to a device that never enumerates on the host

---

## Standard Workflow

1. Capture a **before** snapshot.
2. Connect, disconnect, or reboot the target device.
3. Capture an **after** snapshot.
4. Run the diff and review added, removed, and changed records.
5. Check `meta.capture_status` and `meta.section_errors` before trusting the result.

---

## Commands

```powershell
& "uv" run tools\hardware\usb_snapshot.py --out tools\hardware\snapshots\before.json
& "uv" run tools\hardware\usb_snapshot.py --out tools\hardware\snapshots\after.json
& "uv" run tools\hardware\usb_diff.py tools\hardware\snapshots\before.json tools\hardware\snapshots\after.json
```

Optional smoke test:

```powershell
& "uv" run tools\hardware\usb_diff.py tools\hardware\snapshots\before.json tools\hardware\snapshots\before.json
```

---

## Interpretation Rules

- `capture_status = ok` means every configured section returned cleanly.
- `capture_status = partial` means at least one section failed and the result must be treated as incomplete.
- Stable no-change runs should normally produce zero diffs across PnP, USB tree, disks, and volumes.
- Volume free-space churn is intentionally ignored so normal background activity does not look like hardware change.

---

## Recommended Operator Language

Use wording like:

- "Windows enumerates the device."
- "The host does not currently expose a new disk or volume."
- "The snapshot is partial, so this result is not complete."

Avoid wording like:

- "The USB-C port is electrically fine."
- "The cable is definitely broken."
- "The device storage is readable over USB-C."
