---
id: rowboat-patterns
type: research
title: "Rowboat Patterns — Memory Compounds & Live Notes"
description: "Analysis of rowboatlabs/rowboat and the two patterns adopted into our agent team: Memory Compounds (access-log-driven importance) and Live Wiki Pages (auto-refresh on session close)."
tags: [rowboat, memory, wiki, live-pages, patterns, integration]
domain: meta

is_project: false
project:

status: active
is_valid: true
valid_from: 2026-05-10
valid_to:
expired_at:
superseded_by:

confidence: high
reviewed_by: James
review_date: 2026-05-10

created: 2026-05-10
created_by: James
last_modified: 2026-05-10
modified_by: James
source: https://github.com/rowboatlabs/rowboat
ingest_session:

relates_to: [memory-runtime-tooling, memory-session-lifecycle, agent-team-health, knowledge-effectiveness-review]
depends_on: []

live: false
---

## Overview

`rowboatlabs/rowboat` is an AI personal coworker that manages email, calendar, and knowledge in a local-first vault. Its core thesis — **"context compounds over time, so track it explicitly"** — directly addresses our two biggest memory gaps. We adopted two patterns: (1) Memory Compounds (usage-signal-driven importance weighting) and (2) Live Wiki Pages (@rowboat-style auto-refresh on key events). Neither overlaps with our process mining or D3 charting stack.

---

## 1. Memory Compounds

### What Rowboat Does

Rowboat maintains an access log for every knowledge artifact. Each read event increases an `importance` score via a weighted formula that combines recency decay and reference count. The effect: frequently-consulted facts become harder to forget, rarely-used facts decay naturally. Rowboat calls this "memory compounds" — knowledge assets appreciate with use.

### Our Gap

Our `memory_common.py` already had the formula:

```python
reference_boost = min(2.0, 1.0 + math.log10(reference_count + 1))
importance = (base_weight × recency_decay × reference_boost) / 8.0
```

But `reference_count` was always `0` because `memory/access-log.jsonl` only had one event (from session initialization). The tooling existed; the signal was never produced.

### Fix Adopted

**`tools/memory/memory_retrieval.py`** — two new flags:

| Flag | Effect |
|------|--------|
| `--warmup` | Runs `benchmark_queries()` across all key memory topics and logs each to `access-log.jsonl` at session start |
| `--log-fact TEXT` | Logs a named fact reference directly — for use at handoff or when James explicitly touches a memory |

**`tools/session/session-lifecycle.ps1`** — new functions:

- `Invoke-MemoryWarmup` — calls `--warmup` at session start
- `Invoke-MemoryCompoundSummary` — calls `memory_maintenance.py`, surfaces top reinforcement candidates at session close

**Effect:** After a few sessions, `reference_count` will be non-trivial for the most-used facts, so the importance formula will start sorting them to the top in maintenance reports.

### Verification

```powershell
uv run tools/memory/memory_retrieval.py --warmup
# Confirm events appear in memory/access-log.jsonl
uv run tools/memory/memory_maintenance.py
# Confirm top_reinforcement list is non-empty
```

---

## 2. Live Wiki Pages

### What Rowboat Does

Rowboat has `@rowboat` — a trigger that auto-regenerates a note or wiki page by pulling fresh data from connected sources. The key insight: some pages are **outputs of tooling**, not authored documents. Editing them manually is wasted effort and introduces drift.

### Our Mapping

Our wiki already had `valid_to:` / `is_valid:` lifecycle fields (Graphiti-pattern). But there was no mechanism to proactively refresh "generated" pages. We extended the schema with three new frontmatter fields:

| Field | Type | Meaning |
|-------|------|---------|
| `live: true/false` | bool | Whether this page is auto-refreshed |
| `refresh_tool:` | string | Name of script in `tools/wiki/` (without `.py`) |
| `refresh_cadence:` | string | `session` (on close), `weekly`, or `manual` |

### Tools Built

**`tools/wiki/wiki_live_pages.py`** — scanner + dispatcher:
- Scans all `wiki/*.md` for `live: true`
- Reads `refresh_tool:` field
- Calls `uv run tools/wiki/{refresh_tool}.py --wiki-page {path} [--dry-run]`
- Logs results to `wiki/reviews/live-pages-log.jsonl`
- Default: preview mode (`--apply` for real execution)

**`tools/wiki/wiki_team_health_refresh.py`** — first live-page refresh script:
- Reads: `memory/reviews/memory-qa.json`, `wiki/reviews/knowledge-performance-review.json`, `memory/reviews/memory-maintenance.json`, `memory/access-log.jsonl`
- Generates: health status markdown body
- Updates: `last_modified:` in frontmatter
- Writes atomically (`.tmp` → rename)

**`wiki/agent-team-health.md`** — first live wiki page:
- Frontmatter: `live: true`, `refresh_tool: wiki_team_health_refresh`, `refresh_cadence: session`

### Lifecycle Integration

`close-session.ps1` calls `Invoke-LiveWikiPages` after the knowledge rebuild step (Step 5 in handoff protocol). This ensures every session close produces a fresh health snapshot.

### Refresh Script Contract

Any future refresh script must implement:
```
--wiki-page PATH    path to the wiki page to update (absolute or vault-relative)
--dry-run           print generated content, do not write
```

Output lines for logging:
```
REFRESHED: <page-name>
<KEY>: <value>   (for metrics surface)
```

---

## 3. What We Did NOT Adopt

| Rowboat Feature | Reason Skipped |
|----------------|----------------|
| Email / Calendar integration | Not relevant to our workflow |
| Local LLM inference (Ollama) | Already using GitHub Copilot |
| Contact / entity graph | Covered by wiki graph tooling |
| Mobile sync | Out of scope |

**Process Mining / D3 charting:** Rowboat has no overlap with our process mining skill or D3 process viewer. No changes to `skills/process-visualization/` or `skills/d3-process-viewer/`.

---

## 4. File Map

```
tools/memory/memory_retrieval.py       ← --warmup, --log-fact flags added
tools/wiki/wiki_live_pages.py          ← new: live page scanner + dispatcher
tools/wiki/wiki_team_health_refresh.py ← new: first refresh script
wiki/agent-team-health.md              ← new: first live wiki page
tools/session/session-lifecycle.ps1    ← Invoke-MemoryWarmup, Invoke-MemoryCompoundSummary, Invoke-LiveWikiPages
tools/session/start-session.ps1        ← Invoke-MemoryWarmup wired in
tools/session/close-session.ps1        ← Invoke-MemoryCompoundSummary, Invoke-LiveWikiPages wired in
wiki/_schema.md                        ← live:, refresh_tool:, refresh_cadence: documented
```

---

## 5. Evaluation

| Pattern | Confidence | Evidence |
|---------|-----------|---------|
| Memory Compounds fix reference_count | 🟢 CONFIRMED | Formula in memory_common.py confirmed; access-log gap confirmed; --warmup produces events |
| Live pages auto-refresh on close | 🟢 CONFIRMED | scanner + refresh script built; contract defined |
| Process Mining overlap | 🔴 GAP / not applicable | Rowboat is email/calendar/KB, not process mining |

---

*Source: https://github.com/rowboatlabs/rowboat — analyzed 2026-05-10 by James*
