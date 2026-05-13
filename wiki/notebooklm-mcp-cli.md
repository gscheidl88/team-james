---
# ── Identity ──────────────────────────────────────────────
id: notebooklm-mcp-cli
type: research
title: "NotebookLM MCP CLI — Programmatic Access to Google NotebookLM"
description: "Unified CLI + MCP server for Google NotebookLM — 35 tools, 73 notebooks, browser-cookie auth, uv-installable."
tags: [notebooklm, mcp, google, cli, tool, installed]
domain: technical

# ── Project Context ───────────────────────────────────────
is_project: false
project:

# ── Lifecycle / Validity ──────────────────────────────────
status: active
is_valid: true
valid_from: 2026-04-10
valid_to:
expired_at:
superseded_by:

# ── Quality / Confidence ──────────────────────────────────
confidence: high
reviewed_by: James
review_date: 2026-04-10

# ── Provenance ────────────────────────────────────────────
created: 2026-04-10
created_by: James
last_modified: 2026-04-10
modified_by: James
source: https://github.com/jacob-bd/notebooklm-mcp-cli
ingest_session:

# ── Knowledge Graph ───────────────────────────────────────
relates_to:
  - "[[tooling-policy]]"
depends_on: []
---

## Overview

`notebooklm-mcp-cli` is a unified Python package that provides both a CLI (`nlm`) and an MCP server (`notebooklm-mcp`) for programmatic access to Google NotebookLM. It uses browser-extracted cookies for authentication (no official API). The package was installed on 2026-04-10 via `uv tool install notebooklm-mcp-cli`, authenticated successfully, and gives access to Gerhard's 73 NotebookLM notebooks. The MCP server is configured in `~/.copilot/mcp.json` but may not be loaded in all Copilot CLI sessions — use `nlm` CLI as a reliable fallback.

---

## Installation & Setup

```powershell
# Install (already done)
uv tool install notebooklm-mcp-cli

# Authenticate (already done — valid)
nlm login

# Check auth status
nlm login --check
# Output: ✓ Authentication valid! | Notebooks found: 73

# Upgrade when needed
uv tool install --force notebooklm-mcp-cli
```

**Binaries installed:**
- `~\.local\bin\nlm.exe` — CLI
- `~\.local\bin\notebooklm-mcp.exe` — MCP server

---

## MCP Configuration (Copilot CLI)

Config file: `~\.copilot\mcp.json`

```json
{
  "mcpServers": {
    "notebooklm-mcp": {
      "command": "~\.local\\bin\\notebooklm-mcp.exe"
    }
  }
}
```

**Known issue:** MCP tools not visible in Copilot CLI sessions — likely silent startup failure. Root cause unclear (Playwright/Chrome dependency? Auth timing?). Use `nlm` CLI directly as fallback until resolved.

---

## Key CLI Commands

```powershell
# Notebooks
nlm notebook list                              # List all notebooks (JSON)
nlm notebook create "Title"                    # Create notebook
nlm notebook query <id> "question"             # Query a notebook (AI answer)

# Sources
nlm source add <notebook-id> --url "https://..."
nlm source add <notebook-id> --text "content"

# Studio content generation
nlm studio create <notebook-id> --type audio   # Generate podcast
nlm download audio <notebook-id> <artifact-id>

# Research
nlm research start "topic"                     # Web research + import

# Batch & pipeline
nlm batch query ...
nlm pipeline run ...

# Diagnostics
nlm doctor
nlm login --check
```

---

## MCP Tools (35 available when loaded)

Key tools: `notebook_list`, `notebook_create`, `notebook_query`, `source_add`, `studio_create`, `download_artifact`, `research_start`, `notebook_share_*`, `batch`, `cross_notebook_query`, `pipeline`

Full reference: `nlm --ai` for AI-optimized docs, or official [MCP Guide](https://github.com/jacob-bd/notebooklm-mcp-cli/blob/main/docs/MCP_GUIDE.md)

---

## Authentication Lifecycle

| Component | Duration | Refresh |
|-----------|----------|---------|
| Cookies | ~2–4 weeks | Auto-refresh via headless browser |
| CSRF Token | ~minutes | Auto-refreshed on failure |
| Session ID | Per MCP session | Auto-extracted on start |

When auto-refresh fails: `nlm login` (re-authenticates via browser).

**Rate limits:** Free tier ~50 queries/day.

### Browser auth recovery pattern

For Gerhard's workspace, `nlm login` should not blindly launch a new browser every time auth expires. The stable recovery order is:

1. check whether a local Chrome debug session for NotebookLM auth is already running
2. inspect active debug ports and Chrome command lines
3. reuse the existing debug browser through CDP if available
4. only start a new auth browser if no reusable debug session exists
5. validate with `nlm login --check`

Observed working pattern on 2026-04-15:

```powershell
# 1. Check existing debug ports
Get-NetTCPConnection -State Listen | Where-Object { $_.LocalPort -in 9222, 9223, 18800 }

# 2. Inspect Chrome command lines
Get-CimInstance Win32_Process -Filter "name='chrome.exe'" |
  Select-Object ProcessId, CommandLine

# 3. Reuse existing debug browser
nlm login --provider openclaw --cdp-url http://127.0.0.1:9222

# 4. Validate
nlm login --check
```

Important nuance:

- A normal open Chrome window is **not enough**
- `nlm` needs a reachable debug/CDP browser session or a saved headless profile
- On 2026-04-15 the reusable local login browser was open, but the default `nlm login` path failed because it tried a different connection path and could not attach automatically

So the correct operational rule is: **reuse existing debug browser first, spawn a new one only when no usable debug session exists**.

---

## Architecture Notes

- Uses **internal, undocumented Google APIs** — may break without warning
- Cookie-based auth (no OAuth token, no official API key)
- January 2026: unified package (`notebooklm-mcp-cli`) replaced two separate packages (`notebooklm-cli` + `notebooklm-mcp-server`)
- "Vibe-coded" by non-developer with AI assistants — community-maintained

---

## Gerhard's Usage Context

- **73 notebooks** available as of 2026-04-10
- Primary use: access notebooks from Copilot CLI sessions, query content, add sources programmatically
- Fallback path: `nlm notebook list` + `nlm notebook query` when MCP not loaded
