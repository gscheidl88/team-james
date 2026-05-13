---
id: windows-hardware-triage
type: documentation
title: "Windows Hardware Triage"
description: "Host-side USB, PnP, disk, and volume observability workflow for device maintenance and before/after troubleshooting on Windows."
tags: [hardware, usb, pnp, storage, diagnostics, windows]
domain: technical
is_project: false
project:
status: active
is_valid: true
valid_from: 2026-04-26
valid_to:
expired_at:
superseded_by:
confidence: high
reviewed_by: James
review_date: 2026-04-26
created: 2026-04-26
created_by: James
last_modified: 2026-04-26
modified_by: James
source: "<WORKSPACE_ROOT>\tools\\hardware\\"
ingest_session: "[[log#2026-04-26-documentation-windows-hardware-triage]]"
relates_to:
  - "[[tooling-policy]]"
  - "[[autonomic-tooling-pattern]]"
  - "[[agent-orchestration-policy]]"
depends_on: []
---

## Overview

This page documents the first durable hardware-observability slice for the workspace. The workflow is intentionally host-side: James can inspect what Windows currently enumerates via USB, PnP, disk, and volume APIs, compare before/after snapshots, and expose partial-capture failures instead of silently assuming the machine is healthy. It is useful for device maintenance and troubleshooting, but it is not a raw USB-C, cable, firmware, or target-disk diagnostic surface.

## What James can monitor now

The current tooling can show:

- whether Windows enumerates a device at all
- whether a USB, PnP, disk, or volume record appeared or disappeared
- whether a previously known record changed
- whether one of the capture sections failed and made the snapshot partial

The current tooling cannot show:

- raw USB-C electrical health
- cable quality
- firmware-level device state
- direct storage access to a broken Windows device that never enumerates on the host

## Tooling

The first-line tools live under `tools\hardware\`:

- `usb_snapshot.py`
- `usb_diff.py`

They are local `uv run` tools and do not require MCPs or external APIs.

## Commands

```powershell
& "uv" run tools\hardware\usb_snapshot.py --out tools\hardware\snapshots\before.json
& "uv" run tools\hardware\usb_snapshot.py --out tools\hardware\snapshots\after.json
& "uv" run tools\hardware\usb_diff.py tools\hardware\snapshots\before.json tools\hardware\snapshots\after.json
```

Self-diff smoke test:

```powershell
& "uv" run tools\hardware\usb_diff.py tools\hardware\snapshots\before.json tools\hardware\snapshots\before.json
```

## Snapshot semantics

Each snapshot records:

- `meta.capture_status`
- `meta.section_status`
- `meta.section_errors`

This makes partial failures explicit. A snapshot with `capture_status = partial` is still useful evidence, but it must not be treated as a complete picture.

## Diff semantics

The diff tool compares:

- `pnp_devices`
- `usb_tree`
- `disks`
- `volumes`

The first hardening pass established these rules:

- non-present PnP devices are filtered by default
- disks use a stable `disk_key`
- volumes use a stable `volume_key`
- free-space churn is ignored so background activity does not look like a hardware event

## Recommended interpretation language

Prefer statements like:

- "Windows currently enumerates the device."
- "No new storage device became visible on the host."
- "The snapshot is partial, so this result is incomplete."

Avoid statements like:

- "The USB-C port is electrically healthy."
- "The cable is definitely broken."
- "The device can be read directly over USB-C."

## Why this matters

This closes the practical gap between "James can reason about hardware" and "James can actually see host-visible device state." For maintenance sessions, the first question is now operational and testable: what did Windows enumerate before and after the event?
