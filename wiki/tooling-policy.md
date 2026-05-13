---
id: tooling-policy
type: decision
title: "Tooling Policy — uv Python Tools vs MCPs"
tags: [tooling, python, uv, mcp, policy, decision]
domain: meta

is_project: false
project:

status: active
is_valid: true
valid_from: 2026-04-08
valid_to:
superseded_by:

confidence: high
reviewed_by: Gerhard
review_date: 2026-04-08

created: 2026-04-08
created_by: James
last_modified: 2026-04-08
modified_by: Analyst
source:
ingest_session: "[[log#2026-04-08-init]]"

relates_to:
  - "[[agent-team-setup]]"
  - "[[karpathy-llm-wiki-pattern]]"
  - "[[personal-notes-system]]"
depends_on: []
---

## Overview

The team's tooling policy establishing `uv` Python scripts as the primary tool standard, with MCPs as an acceptable fallback only when no practical alternative exists. The policy covers the decision criteria (token-free, local-first, reproducible), the uv inline script format, and the MCP evaluation process. James acts as sparring partner — both options are weighed before Gerhard decides.

# Tooling Policy — uv Python Tools vs MCPs

## Decision

**Prefer direct Python tools via `uv run` over MCPs whenever a token-free, flexible alternative exists.**

MCPs are acceptable when there is no practical alternative. James acts as sparring partner — weighing both options, giving a recommendation, Gerhard decides.

---

## Rationale

| Criterion | uv Python Tool | MCP |
|-----------|---------------|-----|
| Token dependency | None | Often required |
| Auth overhead | None | Depends on MCP |
| Control & transparency | Full — we own the code | Limited — black box |
| Logging | Custom, clean, structured | Varies |
| Collaboration fit | High — James and Gerhard work through it together | Lower |
| Maintenance | We own it | External dependency |
| Fit with workflow | Perfect — same pattern as existing tools | Separate runtime |

---

## Decision Criteria (in order)

1. **Can it run without external API tokens / auth overhead?** → uv Python tool
2. **Is there no practical alternative?** → MCP acceptable
3. **Gray area?** → James presents both options with tradeoff analysis; Gerhard decides

---

## Script Standard

All Python tools follow the uv inline script format:

```python
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["dependency1", "dependency2"]
# ///
"""
tool_name.py — Short description.

Usage:
    uv run tools/<name>.py --flag value
"""
```

- No `pyproject.toml` or separate venv needed
- `uv run script.py` handles dependency installation automatically
- Every script must have structured, readable log output (not silent, not verbose noise)
- Location: `tools/<domain>/script_name.py`

---

## uv Binary

- Path: `uv`
- Added to PATH via `D:\OneDrive\Documents\PowerShell\profile.ps1`
- Verify: `uv --version`

---

## Existing Tools

| Tool | Location | Purpose |
|------|----------|---------|
| `notes_summarizer.py` | `tools/notes/` | Aggregates Daily Notes → Weekly/Monthly/Annual |
| `wiki_tool.py` | `tools/wiki/` | Wiki ingest / lint / BM25 search *(planned)* |

---

## MCP Exceptions

If an MCP is chosen, document it here with justification:

*(none yet)*
