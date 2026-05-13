#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
contrast_check.py - Check text/background contrast ratios for presentation colors.

Usage:
    uv run tools/presentations/contrast_check.py --fg FFFFFF --bg 003366
    uv run tools/presentations/contrast_check.py --fg 1A1A2E --bg F5F7FA --large-text
"""

from __future__ import annotations

import argparse


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check WCAG contrast between two colors.")
    parser.add_argument("--fg", required=True, help="Foreground/text color hex, e.g. FFFFFF or #FFFFFF")
    parser.add_argument("--bg", required=True, help="Background color hex, e.g. 003366 or #003366")
    parser.add_argument(
        "--large-text",
        action="store_true",
        help="Use the WCAG threshold for large text (3.0) instead of normal text (4.5).",
    )
    return parser.parse_args()


def normalize_hex(value: str) -> str:
    text = value.strip().lstrip("#")
    if len(text) == 3:
        text = "".join(ch * 2 for ch in text)
    if len(text) != 6 or any(ch not in "0123456789abcdefABCDEF" for ch in text):
        raise ValueError(f"Invalid hex color: {value}")
    return text.upper()


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def channel_to_linear(channel: int) -> float:
    srgb = channel / 255
    if srgb <= 0.04045:
        return srgb / 12.92
    return ((srgb + 0.055) / 1.055) ** 2.4


def relative_luminance(rgb: tuple[int, int, int]) -> float:
    r, g, b = (channel_to_linear(channel) for channel in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(fg: tuple[int, int, int], bg: tuple[int, int, int]) -> float:
    l1 = relative_luminance(fg)
    l2 = relative_luminance(bg)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def best_polar_text(bg: tuple[int, int, int]) -> tuple[str, float]:
    white_ratio = contrast_ratio((255, 255, 255), bg)
    black_ratio = contrast_ratio((0, 0, 0), bg)
    if white_ratio >= black_ratio:
        return "#FFFFFF", white_ratio
    return "#000000", black_ratio


def main() -> int:
    args = parse_args()
    fg_hex = normalize_hex(args.fg)
    bg_hex = normalize_hex(args.bg)
    ratio = contrast_ratio(hex_to_rgb(fg_hex), hex_to_rgb(bg_hex))
    threshold = 3.0 if args.large_text else 4.5
    passes = ratio >= threshold
    suggested, suggested_ratio = best_polar_text(hex_to_rgb(bg_hex))
    print(f"foreground: #{fg_hex}")
    print(f"background: #{bg_hex}")
    print(f"contrast_ratio: {ratio:.2f}:1")
    print(f"threshold: {threshold:.1f}:1")
    print(f"status: {'PASS' if passes else 'FAIL'}")
    print(f"best_simple_text_for_background: {suggested} ({suggested_ratio:.2f}:1)")
    return 0 if passes else 1


if __name__ == "__main__":
    raise SystemExit(main())
