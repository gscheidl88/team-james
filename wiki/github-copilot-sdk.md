---
# ── Identity ──────────────────────────────────────────────
id: github-copilot-sdk
type: research
title: "GitHub Copilot SDK — Programmable Agent Runtime"
tags: [copilot, sdk, hooks, skills, harness, python, agent-runtime]
domain: meta

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
last_modified: 2026-04-15
modified_by: Researcher
source: https://github.com/github/copilot-sdk
ingest_session: [[log#2026-04-10-research-copilot-sdk]]

# ── Knowledge Graph ───────────────────────────────────────
relates_to:
  - "[[github-copilot-hooks]]"
  - "[[github-copilot-rubber-duck]]"
  - "[[agent-team-setup]]"
  - "[[tooling-policy]]"
  - "[[openclaw-ecosystem]]"
  - "[[notebooklm-mcp-cli]]"
depends_on: []

description: "GitHub Copilot SDK (Public Preview) exposes the Copilot CLI engine as a programmable Python/JS/Go/.NET/Java library with session lifecycle hooks, a skills system, and MCP integration — directly relevant for replacing the PowerShell harness wrapper."
---

## Overview

The GitHub Copilot SDK is a multi-language library (Python, Node.js, Go, .NET, Java) that wraps the same Copilot CLI engine behind a programmatic API. It is currently in Public Preview and communicates with the CLI via JSON-RPC in server mode. For our purposes, three features are directly relevant: (1) **Session lifecycle hooks** (`onSessionStart`, `onSessionEnd`, `onPreToolUse`, `onPostToolUse`) that cleanly replace the PowerShell `try/finally` wrapper; (2) the **Skills system** (`skill_directories` + `SKILL.md`) that is near-identical to our `skills/` directory structure; (3) **BYOK** support (own API keys) which decouples the harness from GitHub auth.

For the repository-scoped product hooks available in Copilot CLI and Copilot cloud agent, see [[github-copilot-hooks]]. Those hooks are operational shell extension points; the SDK hooks described here are the deeper programmable runtime layer.

---

## Architecture

```
Your Application (Python james.py)
       ↓
  SDK Client (github-copilot-sdk)
       ↓ JSON-RPC
  Copilot CLI (bundled, server mode)
```

The Python/Node.js/.NET SDKs bundle the CLI automatically — no separate installation required. The SDK manages the CLI process lifecycle. Current status: **Public Preview** — functional but not recommended for production yet.

---

## Features Relevant to Our Harness

### 1. Session Lifecycle Hooks

Hooks are callbacks registered at session creation. They are the official, clean equivalent of our `try/finally` PowerShell workaround:

| Hook | Trigger | Our Use Case |
|------|---------|--------------|
| `on_session_start` | Session initialised | Inject `MEMORY.md` + `USER.md` as `additional_context` |
| `on_session_end` | Session ends (any reason) | Run closing checklist: wiki lint → dream → graph rebuild |
| `on_pre_tool_use` | Before any tool call | Logging, permission gates |
| `on_post_tool_use` | After any tool call | Result transformation, audit log |
| `on_user_prompt_submitted` | User sends a message | Mid-session context injection |

**`on_session_end` receives a `reason` field:**
- `"complete"` — normal completion
- `"user_exit"` — user typed `\exit`
- `"error"` — unhandled exception
- `"abort"` — forceful termination
- `"timeout"` — session timed out

This means we can differentiate between a clean `\exit` and a crash — our current `try/finally` cannot.

**Python example skeleton:**
```python
from copilot import CopilotClient

async def on_session_start(event):
    memory = Path("memory/MEMORY.md").read_text()
    user = Path("memory/USER.md").read_text()
    return {"additional_context": f"{memory}\n\n{user}"}

async def on_session_end(event):
    reason = event.get("reason", "unknown")
    run_closing_checklist(reason)

session = await client.create_session(
    on_session_start=on_session_start,
    on_session_end=on_session_end,
    ...
)
```

### 2. Skills System

The SDK loads skills from directories at session creation:

```python
session = await client.create_session(
    skill_directories=["./skills"],  # parent dir
    disabled_skills=["experimental-skill"],
    ...
)
```

**`SKILL.md` format** (discovered via `skills/<name>/SKILL.md`):
```markdown
---
name: data-analysis
description: Data analysis procedures and SQL patterns
---

# Data Analysis Skill
Instructions injected into session context...
```

**Compatibility with our `skills/` structure:**
- Our directory layout (`skills/<name>/skill.md`) is **directly compatible**
- **Only change needed:** rename `skill.md` → `SKILL.md` in each skill directory
- Our `skill.yaml` manifests have no SDK equivalent — keep for our own tooling

### 3. BYOK (Bring Your Own Key)

Use own LLM API keys (OpenAI, Azure AI Foundry, Anthropic) without GitHub auth:
```python
client = CopilotClient(byok_config={"provider": "openai", "api_key": os.environ["OPENAI_API_KEY"]})
```
This decouples the harness entirely from GitHub subscription status.

### 4. Session Persistence

Resume sessions across restarts — relevant if we ever want persistent conversation context between James sessions.

### 5. MCP Integration

MCPs can be configured directly in `create_session()` — cleaner than the current `~/.copilot/mcp.json` global config. Could fix the NotebookLM MCP silent-startup issue.

---

## Fit Analysis: Replace PowerShell Harness?

| Component | Current (PS) | SDK Equivalent | Migration Effort |
|-----------|-------------|----------------|-----------------|
| Session start | `Invoke-James` alias | `on_session_start` hook | Medium |
| Session end cleanup | `try/finally` → `close-session.ps1` | `on_session_end` hook | Low (cleaner) |
| Memory injection | Manual ("read these files") | `additional_context` in `on_session_start` | Low (big win) |
| Skills loading | James reads files ad-hoc | `skill_directories` formal load | Low (rename only) |
| MCP config | `~/.copilot/mcp.json` global | Per-session `mcp_servers` dict | Low |
| Exit reason detection | Cannot distinguish | `reason` field in `on_session_end` | Free |

**Migration would yield:**
1. Automatic `MEMORY.md` + `USER.md` injection every session (no more "read these files")
2. Skills formally part of session context, not files James has to discover
3. Proper `user_exit` vs `error` differentiation in closing checklist
4. Per-session MCP config (potential fix for NotebookLM silent startup)

---

## Decision: Adopt When?

**Phase 1 (done 2026-04-10):** ✅ Renamed `skill.md` → `SKILL.md` — SDK-compatible, zero-risk.

**Phase 2 (deferred — SDK stable):** Build `tools/session/james.py` as Python SDK wrapper.

### Why not now?

The SDK is programmatic (`send_and_wait`), not interactive. To replace `copilot -i`, we'd need to build a full Python REPL:
- Subscribe to `assistant.message_delta` events for streaming output
- Handle `session.idle` for turn completion
- Implement readline/input history
- Replicate slash commands (`\exit`, `\clear`, etc.)
- Rebuild terminal output formatting (colors, tool rendering)

Estimated effort: ~150-200 lines of Python. Doable, but we'd temporarily lose CLI UX quality.

**Decided 2026-04-10:** Wait until SDK exits Public Preview. Current `try/finally` PS wrapper is stable enough.

**Trigger for Phase 2:** SDK exits Public Preview OR MCP loading issue persists AND becomes blocking.

---

## External / Automation Use Cases (Available TODAY)

The SDK is designed for programmatic use — these use cases work **now**, without building a REPL:

### Pattern: Copilot as LLM Backend for Scripts

```python
# tools/analyse_report.py
# /// script
# requires-python = ">=3.11"
# dependencies = ["github-copilot-sdk"]
# ///
import asyncio
from copilot import CopilotClient

async def main():
    client = CopilotClient()
    await client.start()
    
    session = await client.create_session(
        on_permission_request=lambda req, inv: {"kind": "approved"},
        skill_directories=["<WORKSPACE_ROOT>/skills"],
    )
    
    data = open("report.csv").read()
    result = await session.send_and_wait(
        f"Analysiere diese Daten und gib mir 3 Key Findings:\n\n{data}"
    )
    print(result.text)
    await client.stop()

asyncio.run(main())
```

Run: `uv run tools/analyse_report.py`

### Concrete Use Cases for the owner's Workflow

| Use Case | What it does | Trigger |
|----------|-------------|---------|
| **Nightly Report** | Liest neue Daten, lässt Copilot Key Findings extrahieren, schreibt in Daily Note | Task Scheduler |
| **NotebookLM → Summary** | `nlm notebook show` → Copilot schreibt Executive Summary | Manuell / scheduled |
| **Code Review Batch** | Git diff → Copilot gibt strukturiertes Review | Pre-commit / CI |
| **Wiki Gap Finder** | Scannt `wiki/` auf fehlende Seiten, lässt Copilot Lücken identifizieren | Wöchentlich |
| **Memory Digest** | MEMORY.md → Copilot schreibt kompaktes Briefing für neue Session | Session-Start |

### Key Difference vs. Phase 2

| | External Automation | Phase 2 (Interactive) |
|--|--------------------|-----------------------|
| **What** | Python scripts that call Copilot | James-Session läuft IN Python |
| **Hooks** | Per-call (send/receive) | Session-lifecycle (start/end) |
| **UX** | Non-interactive, output to file/stdout | Interaktiver Chat |
| **Ready** | ✅ NOW | ⏳ After SDK stable |

---

## Installation

```bash
# Python (our preferred language)
uv add github-copilot-sdk

# Verify
python -c "import copilot; print(copilot.__version__)"
```

Auth: uses stored `copilot` CLI credentials automatically (same OAuth flow).

---

## Related Links

- [SDK Docs](https://github.com/github/copilot-sdk/blob/main/docs/index.md)
- [Python README](https://github.com/github/copilot-sdk/blob/main/python/README.md)
- [Hooks Guide](https://github.com/github/copilot-sdk/blob/main/docs/features/hooks.md)
- [Skills Guide](https://github.com/github/copilot-sdk/blob/main/docs/features/skills.md)
- [BYOK Guide](https://github.com/github/copilot-sdk/blob/main/docs/auth/byok.md)
- [Cookbook](https://github.com/github/awesome-copilot/blob/main/cookbook/copilot-sdk/python/README.md)
