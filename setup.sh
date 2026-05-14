#!/usr/bin/env sh
set -eu

if [ "$#" -ne 1 ]; then
  echo "Usage: ./setup.sh /absolute/workspace/path" >&2
  exit 1
fi

REPO_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
WORKSPACE_ROOT=$1

if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN=python3
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN=python
elif command -v uv >/dev/null 2>&1; then
  PYTHON_BIN="uv run python"
else
  echo "Python 3 or uv is required to run setup.sh" >&2
  exit 1
fi

if [ "$PYTHON_BIN" = "uv run python" ]; then
  uv run python - "$REPO_ROOT" "$WORKSPACE_ROOT" <<'PY'
from pathlib import Path
import shutil
import sys

repo_root = Path(sys.argv[1])
workspace_root = sys.argv[2]
updated = 0

for path in repo_root.rglob("*"):
    if not path.is_file() or ".git" in path.parts:
        continue
    if path.suffix not in {".md", ".yaml", ".yml", ".py", ".ps1", ".sh"}:
        continue
    text = path.read_text(encoding="utf-8")
    if "<WORKSPACE_ROOT>" not in text:
        continue
    path.write_text(text.replace("<WORKSPACE_ROOT>", workspace_root), encoding="utf-8")
    updated += 1
    print(f"Updated {path.relative_to(repo_root)}")

for source_name, target_name in (
    ("memory/USER.example.md", "memory/USER.md"),
    ("memory/MEMORY.example.md", "memory/MEMORY.md"),
):
    source = repo_root / source_name
    target = repo_root / target_name
    if not target.exists():
        shutil.copyfile(source, target)
        print(f"Created {target.relative_to(repo_root)}")

print(f"Setup complete. Updated {updated} files.")
PY
else
  "$PYTHON_BIN" - "$REPO_ROOT" "$WORKSPACE_ROOT" <<'PY'
from pathlib import Path
import shutil
import sys

repo_root = Path(sys.argv[1])
workspace_root = sys.argv[2]
updated = 0

for path in repo_root.rglob("*"):
    if not path.is_file() or ".git" in path.parts:
        continue
    if path.suffix not in {".md", ".yaml", ".yml", ".py", ".ps1", ".sh"}:
        continue
    text = path.read_text(encoding="utf-8")
    if "<WORKSPACE_ROOT>" not in text:
        continue
    path.write_text(text.replace("<WORKSPACE_ROOT>", workspace_root), encoding="utf-8")
    updated += 1
    print(f"Updated {path.relative_to(repo_root)}")

for source_name, target_name in (
    ("memory/USER.example.md", "memory/USER.md"),
    ("memory/MEMORY.example.md", "memory/MEMORY.md"),
):
    source = repo_root / source_name
    target = repo_root / target_name
    if not target.exists():
        shutil.copyfile(source, target)
        print(f"Created {target.relative_to(repo_root)}")

print(f"Setup complete. Updated {updated} files.")
PY
fi
