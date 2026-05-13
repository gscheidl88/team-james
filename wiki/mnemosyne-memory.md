---
# ── Identity ──────────────────────────────────────────────
id: mnemosyne-memory
type: research
title: "Mnemosyne — Local AI Memory System Evaluation"
description: "Mnemosyne v2.3 evaluation and ADAPT integration: vector semantic recall layer alongside MEMORY.md; fastembed ONNX, SQLite-backed, MCP server, dual-write in dream cycle."
tags: [memory, vector-search, embeddings, mcp, agent-memory, integration]
domain: meta

# ── Project Context ───────────────────────────────────────
is_project: false
project:

# ── Lifecycle / Validity ──────────────────────────────────
status: active
is_valid: true
valid_from: 2026-05-10
valid_to:
expired_at:
superseded_by:

# ── Quality / Confidence ──────────────────────────────────
confidence: high
reviewed_by: James
review_date: 2026-05-10

# ── Provenance ────────────────────────────────────────────
created: 2026-05-10
created_by: James
last_modified: 2026-05-10
modified_by: James
source: https://github.com/rowboatlabs/mnemosyne
ingest_session:

# ── Knowledge Graph ───────────────────────────────────────
relates_to: [research-synthesis-memory-systems, hermes-v012-v013, openclaw-may2026]
depends_on: []

# ── Live Page ─────────────────────────────────────────────
live: false
refresh_tool:
refresh_cadence: manual
---

## Overview

Mnemosyne is a local AI memory system providing SQLite-backed episodic storage with fastembed ONNX vector embeddings (BAAI/bge-small-en-v1.5, 384-dim, CPU-only). Evaluated as v2.3 (PyPI), installed as a `uv tool`. Verdict: **ADAPT** — use as a semantic recall layer alongside MEMORY.md; do not replace MEMORY.md. Integrated via: (1) MCP server wired into Copilot CLI, (2) migration script for existing MEMORY.md entries, (3) dual-write in the dream cycle. Primary value: semantic similarity queries that FTS5-only keyword search cannot handle.

---

## Install & Configuration

```powershell
# Install (no pyproject.toml needed — uv tool)
uv tool install "mnemosyne-memory[embeddings]"

# Data dir — workspace-local, gitignored
$env:MNEMOSYNE_DATA_DIR = "<WORKSPACE_ROOT>\.mnemosyne"
$env:HF_HUB_DISABLE_SYMLINKS_WARNING = "1"   # required on Windows without Developer Mode

# First run downloads ONNX model (~130MB, one-time)
mnemosyne store "test entry"
```

🟢 CONFIRMED — installed v2.3, model downloads correctly, `store`/`recall`/`stats` work.

### Windows Gotchas

| Issue | Status | Workaround |
|-------|--------|-----------|
| `mnemosyne-install` fails (symlink error) | 🔴 Known | Skip — core works without it |
| ONNX model `.incomplete` on partial download | 🔴 Known | Clear `~/.hermes/cache/fastembed/` and re-run |
| `[mcp]` extra missing in v2.3 | 🟡 N/A | `mcp` subcommand still present, just no extra needed |

---

## CLI Reference (v2.3)

```
mnemosyne store <content> [source] [importance]   # store memory
mnemosyne recall <query> [top_k]                  # semantic search
mnemosyne sleep                                   # consolidation pass
mnemosyne stats                                   # show DB stats
mnemosyne diagnose                                # health check
mnemosyne export [file.json]                      # export all memories
mnemosyne import <file.json>                      # import memories
mnemosyne bank list|create|delete [name]          # named memory banks
mnemosyne mcp [--transport sse] [--port 8080]     # start MCP server
```

🟢 CONFIRMED — all commands present and functional.

---

## MCP Integration

Wired into `~/.copilot/mcp.json`:

```json
"mnemosyne": {
  "command": "~\.local\\bin\\mnemosyne.exe",
  "args": ["mcp"],
  "env": {
    "MNEMOSYNE_DATA_DIR": "<WORKSPACE_ROOT>\.mnemosyne",
    "HF_HUB_DISABLE_SYMLINKS_WARNING": "1"
  }
}
```

MCP transport: stdio (default). Fresh instance per call — safe, minor startup overhead.

---

## Integration Architecture

```
MEMORY.md  ←──────────── human-readable / Obsidian-readable (unchanged)
     │
     ├── dream cycle (notes_summarizer.py --dream)
     │     └── dual-write → mnemosyne store [entry]    # new entries only
     │
     └── migration (tools/memory/mnemosyne_migrate.py) # one-time bulk import

.mnemosyne/ (SQLite + fastembed index)
     └── mnemosyne recall "query" 5                    # semantic top-k
```

**Key decision:** MEMORY.md stays as the source of truth and Obsidian backlink anchor. Mnemosyne is the semantic recall layer — it receives every new dream entry via dual-write, and existing entries via the one-time migration script.

---

## Migration Script

```powershell
# Dry run first
uv run tools/memory/mnemosyne_migrate.py --dry-run

# Full migration
uv run tools/memory/mnemosyne_migrate.py
```

Script: `tools/memory/mnemosyne_migrate.py` — reads MEMORY.md bullets, calls `mnemosyne store` per entry with `source=memory-md-import`, `importance=0.7`.

🟡 INFERRED — Mnemosyne handles duplicates silently; safe to re-run.

---

## Verdict Summary

| Criterion | Assessment |
|-----------|-----------|
| Windows compatibility | ✅ Core works; installer fails (symlink) |
| Semantic recall quality | ✅ Score 0.724 on first real query |
| MEMORY.md replacement | ❌ Not needed; complementary |
| MCP integration | ✅ stdio, works with Copilot CLI |
| Dream cycle integration | ✅ Dual-write added |
| Obsidian compatibility | 🔴 None — SQLite silo; export-only bridge |

**Verdict: ADAPT** — Mnemosyne adds vector semantic recall; MEMORY.md stays for human readability and Obsidian graph links.

---

## Open Items

- 🔴 GAP: Migration not yet run against full MEMORY.md — run `mnemosyne_migrate.py` once
- 🔴 GAP: `mnemosyne sleep` (consolidation) not wired into session-close yet
- 🟡 INFERRED: v2.5 (from GitHub) may add `classify_memory()` and improved MCP tools; worth re-checking when published to PyPI
