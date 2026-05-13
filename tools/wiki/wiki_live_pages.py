#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""
wiki_live_pages.py - Scan wiki for live pages and refresh them.

A "live page" has `live: true` in its frontmatter plus a `refresh_tool:` field
pointing to a script in tools/wiki/ that regenerates the page body.

Inspired by Rowboat's "Live Notes" pattern: wiki pages that stay current
automatically rather than requiring manual updates.

Usage:
    uv run tools/wiki/wiki_live_pages.py              # preview: show what would be refreshed
    uv run tools/wiki/wiki_live_pages.py --apply      # actually run refresh tools
    uv run tools/wiki/wiki_live_pages.py --apply --json  # JSON output for scripting
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path
from time import perf_counter

import yaml

VAULT = Path(__file__).resolve().parents[2]
WIKI_DIR = VAULT / "wiki"
TOOLS_WIKI_DIR = VAULT / "tools" / "wiki"
LIVE_PAGES_LOG = WIKI_DIR / "reviews" / "live-pages-log.jsonl"
UV_PATH = Path("C:/Users/User/.local/bin/uv.exe")


def get_uv() -> str:
    if UV_PATH.exists():
        return str(UV_PATH)
    return "uv"


def append_jsonl(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=False) + "\n")


def parse_frontmatter(path: Path) -> dict:
    """Extract YAML frontmatter from a markdown file. Returns {} on failure."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return {}
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    raw_yaml = text[3:end].strip()
    try:
        data = yaml.safe_load(raw_yaml)
        return data if isinstance(data, dict) else {}
    except yaml.YAMLError:
        return {}


def scan_live_pages() -> list[dict]:
    """Return metadata for all wiki pages with live: true."""
    pages = []
    for path in sorted(WIKI_DIR.glob("*.md")):
        if path.name.startswith("_"):
            continue
        fm = parse_frontmatter(path)
        if not fm.get("live"):
            continue
        refresh_tool = str(fm.get("refresh_tool") or "").strip()
        if not refresh_tool:
            continue
        pages.append({
            "path": path,
            "id": fm.get("id") or path.stem,
            "title": fm.get("title") or path.stem,
            "refresh_tool": refresh_tool,
            "refresh_cadence": str(fm.get("refresh_cadence") or "session").strip(),
            "last_modified": str(fm.get("last_modified") or ""),
        })
    return pages


def resolve_tool_script(refresh_tool: str) -> Path | None:
    """Resolve refresh_tool name to a .py path in tools/wiki/."""
    script = TOOLS_WIKI_DIR / f"{refresh_tool}.py"
    return script if script.exists() else None


def run_refresh(page: dict, *, apply: bool) -> dict:
    """Run the refresh tool for a single live page. Returns a result dict."""
    tool_script = resolve_tool_script(page["refresh_tool"])
    if tool_script is None:
        return {
            "page_id": page["id"],
            "status": "error",
            "error": f"refresh_tool script not found: {page['refresh_tool']}.py",
            "duration_ms": 0,
        }

    wiki_page_path = str(page["path"])
    cmd = [get_uv(), "run", str(tool_script), "--wiki-page", wiki_page_path]
    if not apply:
        cmd.append("--dry-run")

    started = perf_counter()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(VAULT),
        )
        duration_ms = round((perf_counter() - started) * 1000, 1)
        ok = result.returncode == 0
        return {
            "page_id": page["id"],
            "status": "ok" if ok else "error",
            "duration_ms": duration_ms,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip() if not ok else "",
        }
    except subprocess.TimeoutExpired:
        return {
            "page_id": page["id"],
            "status": "timeout",
            "error": "refresh tool timed out after 60s",
            "duration_ms": round((perf_counter() - started) * 1000, 1),
        }
    except Exception as exc:
        return {
            "page_id": page["id"],
            "status": "error",
            "error": str(exc),
            "duration_ms": round((perf_counter() - started) * 1000, 1),
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="Refresh live wiki pages.")
    parser.add_argument("--apply", action="store_true", help="Actually run refresh tools (default: preview)")
    parser.add_argument("--json", action="store_true", help="Emit JSON summary")
    args = parser.parse_args()

    pages = scan_live_pages()
    results: list[dict] = []

    for page in pages:
        result = run_refresh(page, apply=args.apply)
        results.append(result)

    ok_count = sum(1 for r in results if r["status"] == "ok")
    error_count = sum(1 for r in results if r["status"] not in {"ok"})
    overall_status = "ok" if error_count == 0 else "warn"

    summary = {
        "created": datetime.now().isoformat(timespec="seconds"),
        "mode": "apply" if args.apply else "preview",
        "live_pages_found": len(pages),
        "refreshed": ok_count if args.apply else 0,
        "errors": error_count,
        "status": overall_status,
        "results": results,
    }

    if args.apply:
        append_jsonl(LIVE_PAGES_LOG, {
            "timestamp": summary["created"],
            "mode": "apply",
            "live_pages": len(pages),
            "refreshed": ok_count,
            "errors": error_count,
            "status": overall_status,
        })

    if args.json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        return 0

    print(f"LIVE_PAGES: {len(pages)}")
    print(f"MODE: {'apply' if args.apply else 'preview'}")
    for r in results:
        status_char = "✓" if r["status"] == "ok" else "✗"
        print(f"  {status_char} {r['page_id']} ({r['status']}, {r['duration_ms']}ms)")
        if r.get("stdout"):
            for line in r["stdout"].splitlines():
                print(f"    {line}")
        if r.get("error"):
            print(f"    ERROR: {r['error']}")
        if r.get("stderr"):
            for line in r["stderr"].splitlines()[:5]:
                print(f"    STDERR: {line}")

    print(f"STATUS: {overall_status}")
    return 0 if overall_status == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
