---
id: memory-session-lifecycle
type: documentation
title: "Memory Session Lifecycle"
description: "Crash-resistant session lifecycle for the memory system: start preflight, mid-session checkpoints, close finalization, and memory guard reactions."
tags: [memory, lifecycle, preflight, checkpoint, guard, recovery]
domain: meta
is_project: true
project: memory-roadmap
status: active
is_valid: true
valid_from: 2026-04-15
valid_to:
expired_at:
superseded_by:
confidence: high
reviewed_by: James
review_date: 2026-04-15
created: 2026-04-15
created_by: James
last_modified: 2026-04-15
modified_by: James
source: "<WORKSPACE_ROOT>\tools\\session\\"
ingest_session: [[log#2026-04-15-documentation-memory-session-lifecycle]]
relates_to:
  - "[[memory-runtime-tooling]]"
  - "[[human-memory-inspired-agent-memory-gap-analysis]]"
  - "[[agent-team-setup]]"
  - "[[personal-notes-system]]"
  - "[[claude-code-harness]]"
depends_on: []
---

## Overview

The memory system now uses a crash-resistant lifecycle instead of relying on session close alone. The core idea is to split memory safety into three stages: **start preflight**, **mid-session checkpoints**, and **close finalization**. This reduces the risk that a crash or abrupt session stop leaves scratchpad state, review work, or QA checks behind.

## Lifecycle model

### 1. Start preflight

Run:

```powershell
& "<WORKSPACE_ROOT>\tools\session\start-session.ps1"
```

What it does:

- ensures today's daily note exists
- initializes the session scratchpad if session state is available
- runs `memory_qa.py`
- runs `memory_guard.py`
- runs `tools/wiki/knowledge_review.py`
- checks for unfinished scratchpads from prior sessions

This is the first recovery checkpoint, before substantive work starts.

### 2. Mid-session checkpoint

Run during longer or riskier sessions:

```powershell
& "<WORKSPACE_ROOT>\tools\session\checkpoint-session.ps1"
```

What it does:

- finalizes the current scratchpad into candidate artifacts
- reconciles candidates against durable memory
- refreshes QA
- refreshes guard status
- refreshes the knowledge performance review

This is the primary crash-resistance mechanism. It makes memory persistence incremental instead of purely end-of-session.

### 3. Close finalization

Run on session exit:

```powershell
& "<WORKSPACE_ROOT>\tools\session\close-session.ps1"
```

What it does:

- wiki lint
- dream consolidation
- scratchpad finalization
- candidate reconciliation
- QA
- guard evaluation
- optional graph rebuild
- wiki search reindex
- knowledge performance review

Close-session remains important, but it is no longer the only durable safety point.

## Guard statuses

`tools/memory/memory_guard.py` emits one of:

- `ok`
- `warn`
- `degraded`
- `blocked`

Inputs:

- `memory/reviews/memory-qa.json`
- `memory/reviews/latest-memory-review.json`
- unfinished scratchpad scan in `~\.copilot\session-state\`

Typical triggers:

- low health score
- weak freshness / coherence / reachability
- large review backlog
- contradictions
- unfinished session artifacts from prior crashes

## Guard reaction model

- `ok` — proceed normally
- `warn` — continue, but prefer retrieval + checkpoint discipline
- `degraded` — reduce durable writes until review/QA issues are checked
- `blocked` — stop durable memory mutation until contradictions or severe health issues are resolved

## Logging and history

The lifecycle now writes machine-readable history:

- `memory/access-log.jsonl`
- `memory/reviews/memory-qa-history.jsonl`
- `memory/reviews/memory-guard-history.jsonl`

`memory-guard-history.jsonl` is now a **unified lifecycle history**, not just a guard-status stream. It includes:

- lifecycle breadcrumbs such as `preflight_complete`, `checkpoint_complete`, and `close_complete`
- intermediate events such as `scratchpad_init` and `scratchpad_finalize`
- guard evaluations as `event_type=guard_eval`
- `session_id`, `session_root`, and `safe_handover`

This means one file now answers two questions:

1. **Health:** was the memory layer healthy?
2. **Continuity:** did a session reach a safe handover point before stopping?

This gives us trendable memory-health signals **and** a breadcrumb trail without introducing a second parallel log file.

## Operational policy

- start every new work session with preflight when possible
- checkpoint during long sessions or before risky work
- do not rely on close-session as the sole persistence path
- treat `degraded` or `blocked` guard states as operational incidents for the memory layer

## Current limitation

The current lifecycle is tool-driven, not hook-driven. It is robust if James runs the scripts, but it is not yet wired into a native `on_session_start` / `on_session_checkpoint` platform hook.

