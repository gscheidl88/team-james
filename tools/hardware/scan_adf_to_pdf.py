#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=11.0.0"]
# ///
"""
scan_adf_to_pdf.py — Scan ADF pages via Windows WIA and build PDF output.

This tool uses the host-visible WIA device path that is already available on
this machine. It does not unlock vendor-only duplex features that the driver
does not expose.

Supported workflows:
1. Simplex ADF scan directly to a multi-page PDF.
2. Two-pass assembly from two feeder passes:
   - first pass: stack 1
   - second pass: stack 2
   - then interleave pages as either
     - stack1-1, stack2-1, stack1-2, stack2-2, ... (`--back-order same`)
     - stack1-1, stack2-last, stack1-2, stack2-last-1, ... (`--back-order reverse`)

Examples:
    uv run tools/hardware/scan_adf_to_pdf.py simplex out.pdf
    uv run tools/hardware/scan_adf_to_pdf.py scan-pass fronts/
    uv run tools/hardware/scan_adf_to_pdf.py scan-pass backs/
    uv run tools/hardware/scan_adf_to_pdf.py assemble-manual-duplex fronts/ backs/ out.pdf --back-order same
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

WIA_JPEG_FORMAT = "{B96B3CAE-0728-11D3-9D7B-0000F81EF32E}"
DEFAULT_DEVICE = "HP LJ M282M285 (USB)"
POWERSHELL = "powershell.exe"

SOURCE_TO_WIA_VALUE = {
    "feeder": 1,
    "flatbed": 2,
    "front-only": 33,
}


def _run_ps(script: str, *, env: dict[str, str]) -> str:
    utf8_preamble = (
        "[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new();\n"
        "$OutputEncoding = [System.Text.UTF8Encoding]::new();\n"
        "$ErrorActionPreference = 'Stop';\n"
    )
    result = subprocess.run(
        [POWERSHELL, "-NoProfile", "-NonInteractive", "-Command", utf8_preamble + script],
        env={**os.environ, **env},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=300,
    )
    stdout_text = result.stdout.decode("utf-8", errors="replace").strip()
    stderr_text = result.stderr.decode("utf-8", errors="replace").strip()
    if result.returncode != 0:
        detail = stderr_text or stdout_text or f"PowerShell exited with code {result.returncode}"
        raise RuntimeError(detail[:2000])
    return stdout_text


def scan_pass(
    output_dir: Path,
    *,
    device: str,
    source: str,
    resolution: int,
    page_limit: int,
) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    env = {
        "ADF_SCAN_DEVICE": device,
        "ADF_SCAN_OUTPUT_DIR": str(output_dir),
        "ADF_SCAN_SOURCE": str(SOURCE_TO_WIA_VALUE[source]),
        "ADF_SCAN_RESOLUTION": str(resolution),
        "ADF_SCAN_PAGE_LIMIT": str(page_limit),
        "ADF_SCAN_FORMAT": WIA_JPEG_FORMAT,
    }
    script = r"""
$deviceName = $env:ADF_SCAN_DEVICE
$outputDir = $env:ADF_SCAN_OUTPUT_DIR
$sourceSelect = [int]$env:ADF_SCAN_SOURCE
$resolution = [int]$env:ADF_SCAN_RESOLUTION
$pageLimit = [int]$env:ADF_SCAN_PAGE_LIMIT
$formatId = $env:ADF_SCAN_FORMAT

$dm = New-Object -ComObject WIA.DeviceManager
$deviceInfo = $null
foreach ($candidate in $dm.DeviceInfos) {
    if ($candidate.Type -eq 1 -and $candidate.Properties['Name'].Value -eq $deviceName) {
        $deviceInfo = $candidate
        break
    }
}
if (-not $deviceInfo) {
    throw "WIA device not found: $deviceName"
}

$device = $deviceInfo.Connect()
$handling = $device.Properties['Document Handling Select']
$allowed = @()
try {
    $allowed = @($handling.SubTypeValues)
} catch {
    $allowed = @()
}
if ($allowed.Count -gt 0 -and -not ($allowed -contains $sourceSelect)) {
    throw "Requested WIA source value $sourceSelect is not allowed for $deviceName. Allowed: $($allowed -join ', ')"
}
$handling.Value = $sourceSelect
$pagesRequested = [Math]::Min($pageLimit, 99)
try {
    $device.Properties['Pages'].Value = $pagesRequested
} catch {}

$item = $device.Items.Item(1)
try {
    $item.Properties['Horizontal Resolution'].Value = $resolution
} catch {}

$saved = @()
for ($i = 1; $i -le $pageLimit; $i++) {
    try {
        $image = $item.Transfer($formatId)
        $name = ('page-{0:D4}.jpg' -f $i)
        $path = Join-Path $outputDir $name
        $image.SaveFile($path)
        $saved += $path
        Start-Sleep -Milliseconds 150
    } catch {
        if ($saved.Count -gt 0) {
            break
        }
        throw
    }
}

if ($saved.Count -eq 0) {
    throw "No pages scanned."
}

[pscustomobject]@{
    device = $deviceName
    source = $sourceSelect
    resolution = $resolution
    pages_requested = $pagesRequested
    page_count = $saved.Count
    pages = @($saved | ForEach-Object { Split-Path $_ -Leaf })
} | ConvertTo-Json -Compress
"""
    raw = _run_ps(script, env=env)
    payload = json.loads(raw)
    return [output_dir / name for name in payload["pages"]]


def _load_pdf_image(path: Path) -> Image.Image:
    image = Image.open(path)
    if image.mode != "RGB":
        image = image.convert("RGB")
    return image


def write_pdf(image_paths: list[Path], output_path: Path) -> None:
    if not image_paths:
        raise ValueError("No input images provided for PDF generation.")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    images = [_load_pdf_image(path) for path in image_paths]
    first, rest = images[0], images[1:]
    try:
        first.save(output_path, save_all=True, append_images=rest, resolution=300.0)
    finally:
        for image in images:
            image.close()


def natural_paths(directory: Path) -> list[Path]:
    return sorted([path for path in directory.iterdir() if path.is_file()], key=lambda p: p.name.lower())


def interleave_manual_duplex(fronts: list[Path], backs: list[Path], *, back_order: str) -> list[Path]:
    if not fronts:
        raise ValueError("Front-pass directory is empty.")
    if len(backs) > len(fronts):
        raise ValueError("Back-pass page count exceeds front-pass page count.")
    if len(fronts) - len(backs) > 1:
        raise ValueError("Back-pass is missing too many pages for manual duplex assembly.")

    ordered_backs = backs if back_order == "same" else list(reversed(backs))
    merged: list[Path] = []
    for idx, front in enumerate(fronts):
        merged.append(front)
        if idx < len(ordered_backs):
            merged.append(ordered_backs[idx])
    return merged


def command_scan_pass(args: argparse.Namespace) -> int:
    pages = scan_pass(
        Path(args.output_dir),
        device=args.device,
        source=args.source,
        resolution=args.resolution,
        page_limit=args.page_limit,
    )
    payload = {
        "status": "ok",
        "mode": "scan-pass",
        "device": args.device,
        "source": args.source,
        "resolution": args.resolution,
        "pages_requested": min(args.page_limit, 99),
        "page_count": len(pages),
        "output_dir": str(Path(args.output_dir).resolve()),
        "pages": [path.name for path in pages],
    }
    print(json.dumps(payload, indent=2))
    return 0


def command_simplex(args: argparse.Namespace) -> int:
    output_path = Path(args.output_pdf).resolve()
    if args.keep_images_dir:
        work_dir = Path(args.keep_images_dir).resolve()
        work_dir.mkdir(parents=True, exist_ok=True)
        pages = scan_pass(
            work_dir,
            device=args.device,
            source=args.source,
            resolution=args.resolution,
            page_limit=args.page_limit,
        )
    else:
        with tempfile.TemporaryDirectory(prefix="scan-adf-") as tmp:
            work_dir = Path(tmp)
            pages = scan_pass(
                work_dir,
                device=args.device,
                source=args.source,
                resolution=args.resolution,
                page_limit=args.page_limit,
            )
            write_pdf(pages, output_path)
            payload = {
                "status": "ok",
                "mode": "simplex",
                "device": args.device,
                "source": args.source,
                "resolution": args.resolution,
                "pages_requested": min(args.page_limit, 99),
                "page_count": len(pages),
                "output_pdf": str(output_path),
            }
            print(json.dumps(payload, indent=2))
            return 0

    write_pdf(pages, output_path)
    payload = {
        "status": "ok",
        "mode": "simplex",
        "device": args.device,
        "source": args.source,
        "resolution": args.resolution,
        "pages_requested": min(args.page_limit, 99),
        "page_count": len(pages),
        "output_pdf": str(output_path),
        "images_dir": str(work_dir),
    }
    print(json.dumps(payload, indent=2))
    return 0


def command_assemble_manual_duplex(args: argparse.Namespace) -> int:
    front_dir = Path(args.front_dir).resolve()
    back_dir = Path(args.back_dir).resolve()
    output_path = Path(args.output_pdf).resolve()
    fronts = natural_paths(front_dir)
    backs = natural_paths(back_dir)
    merged = interleave_manual_duplex(fronts, backs, back_order=args.back_order)
    write_pdf(merged, output_path)
    payload = {
        "status": "ok",
        "mode": "assemble-manual-duplex",
        "back_order": args.back_order,
        "front_pages": len(fronts),
        "back_pages": len(backs),
        "output_pdf": str(output_path),
        "merged_pages": [path.name for path in merged],
    }
    print(json.dumps(payload, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Scan ADF pages via WIA and build PDF output."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_scan_options(sub: argparse.ArgumentParser) -> None:
        sub.add_argument("--device", default=DEFAULT_DEVICE, help=f"WIA device name (default: {DEFAULT_DEVICE})")
        sub.add_argument(
            "--source",
            choices=sorted(SOURCE_TO_WIA_VALUE),
            default="feeder",
            help="WIA document source selection.",
        )
        sub.add_argument("--resolution", type=int, default=200, help="Horizontal scan resolution in DPI.")
        sub.add_argument("--page-limit", type=int, default=100, help="Safety cap for scanned pages in one pass.")

    scan_pass_p = subparsers.add_parser("scan-pass", help="Scan one feeder pass into JPEG pages.")
    scan_pass_p.add_argument("output_dir", help="Directory that will receive page-0001.jpg, ...")
    add_scan_options(scan_pass_p)
    scan_pass_p.set_defaults(func=command_scan_pass)

    simplex_p = subparsers.add_parser("simplex", help="Scan one feeder pass and write a multi-page PDF.")
    simplex_p.add_argument("output_pdf", help="Target PDF file path.")
    simplex_p.add_argument(
        "--keep-images-dir",
        help="Optional directory to keep the intermediate JPEG pages instead of using a temp directory.",
    )
    add_scan_options(simplex_p)
    simplex_p.set_defaults(func=command_simplex)

    duplex_p = subparsers.add_parser(
        "assemble-manual-duplex",
        help="Interleave two scan passes into one PDF.",
    )
    duplex_p.add_argument("front_dir", help="Directory with front-side page JPEGs in natural order.")
    duplex_p.add_argument("back_dir", help="Directory with back-side page JPEGs in scan order before reversing.")
    duplex_p.add_argument("output_pdf", help="Target PDF file path.")
    duplex_p.add_argument(
        "--back-order",
        choices=("same", "reverse"),
        default="same",
        help="How to consume the second pass while interleaving (default: same).",
    )
    duplex_p.set_defaults(func=command_assemble_manual_duplex)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
