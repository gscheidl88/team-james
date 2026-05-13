#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
fix_backlinks.py — Standardise relates_to / depends_on to [[page-id]] Obsidian wikilink format.

Run once to normalise all 3 formats:
  1. [page-id, page-id]   (YAML inline list) → [[page-id]], [[page-id]]
  2. - bare-id            (plain dash-list)  → - "[[bare-id]]"
  3. - "[[page-id]]"      (already correct)  → unchanged

Also fixes wiki_graph.py parser which now strips [[...]] automatically.
"""
import re
import pathlib

WIKI_DIR = pathlib.Path(__file__).parent.parent.parent / "wiki"
SKIP     = {"_schema.md", "index.md", "log.md"}


def to_wikilink(val: str) -> str:
    """Wrap bare page-id in [[...]] if not already wrapped."""
    val = val.strip().strip('"')
    if val.startswith("[["):
        return val
    return f"[[{val}]]"


def process_file(md: pathlib.Path) -> bool:
    text  = md.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    new_lines     = []
    fm_count      = 0
    in_fm         = False
    in_rel_block  = False
    modified      = False

    for line in lines:
        stripped = line.rstrip()

        # Frontmatter boundary
        if stripped == "---":
            fm_count += 1
            in_fm        = (fm_count == 1)
            in_rel_block = False
            if fm_count == 2:
                in_fm = False
            new_lines.append(line)
            continue

        if not in_fm:
            new_lines.append(line)
            continue

        # relates_to / depends_on line
        if re.match(r"^(relates_to|depends_on)\s*:", stripped):
            # Case A: inline list  →  relates_to: [a, b, c]
            m = re.match(r"^(relates_to|depends_on)\s*:\s*\[(.+)\]", stripped)
            if m:
                key   = m.group(1)
                items = [x.strip() for x in m.group(2).split(",")]
                wl    = ", ".join(f'"{to_wikilink(i)}"' for i in items)
                new_line = f"{key}: [{wl}]\n"
                if new_line != line:
                    modified = True
                new_lines.append(new_line)
                in_rel_block = False
            else:
                # Case B: dash-list block starts on next lines
                in_rel_block = True
                new_lines.append(line)
            continue

        if in_rel_block:
            # Dash-list item
            m = re.match(r"^(\s*-\s+)(.*)", stripped)
            if m:
                prefix   = m.group(1)
                val      = m.group(2).strip('"')
                wl       = to_wikilink(val)
                new_line = f'{prefix}"{wl}"\n'
                if new_line != line:
                    modified = True
                new_lines.append(new_line)
            else:
                # End of block (empty line or new key)
                in_rel_block = False
                new_lines.append(line)
            continue

        new_lines.append(line)

    if modified:
        md.write_text("".join(new_lines), encoding="utf-8")
    return modified


def main():
    changed = []
    for md in sorted(WIKI_DIR.glob("*.md")):
        if md.name in SKIP:
            continue
        if process_file(md):
            changed.append(md.name)

    if changed:
        print(f"Standardised {len(changed)} files:")
        for f in changed:
            print(f"  · {f}")
    else:
        print("All files already in [[page-id]] format — no changes needed.")


if __name__ == "__main__":
    main()
