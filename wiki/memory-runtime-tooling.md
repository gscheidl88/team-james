---
id: memory-runtime-tooling
type: documentation
title: "Memory Runtime Tooling"
description: "Runtime memory tooling for the owner's agent team: scratchpad finalization, local retrieval, reconciliation review, maintenance scoring, and repeatable QA."
tags: [memory, tooling, qa, retrieval, reconciliation]
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
source: "<WORKSPACE_ROOT>\tools\\memory\\"
ingest_session: [[log#2026-04-15-documentation-memory-runtime-tooling]]
relates_to:
  - "[[human-memory-inspired-agent-memory-gap-analysis]]"
  - "[[research-synthesis-memory-systems]]"
  - "[[agent-team-setup]]"
  - "[[personal-notes-system]]"
  - "[[openclaw-auto-dream]]"
  - "[[claude-code-harness]]"
  - "[[memory-session-lifecycle]]"
depends_on: []
---

## Overview

This page documents the runtime layer added on top of the markdown-first memory system. The goal is to make memory updates safer, more reviewable, and more measurable without replacing the existing local-first file stack. The implementation keeps retrieval ahead of reconsolidation, routes uncertain updates into review artifacts, and produces repeatable QA metrics after the flow runs.

## Components

### Session scratchpad and candidate finalization

- `tools/session/memory_scratchpad.py`
- Transient working memory lives in session state, not in repository memory files.
- Finalization writes:
  - `memory-candidates.md`
  - `memory-candidates.json`
  - daily note digest block

The scratchpad now carries explicit sections for:
- changes
- decisions
- conflicts
- uncertainties
- lessons
- candidate durable updates

### Retrieval

- `tools/memory/memory_retrieval.py`
- Searches `memory/`, `wiki/`, `memory/episodes/`, and recent `PersonalNotes/Daily/`
- Logs retrieval access to `memory/access-log.jsonl`

This is the first runtime implementation of the "retrieve before write" rule from the roadmap.

### Reconsolidation review

- `tools/memory/memory_reconcile.py`
- Reads candidate JSON or markdown
- Retrieves related memory automatically
- Classifies each candidate into:
  - `compatible`
  - `contradictory`
  - `subsumes`
  - `independent`
  - `ignore`
- Emits:
  - `memory/reviews/latest-memory-review.md`
  - `memory/reviews/latest-memory-review.json`

This creates an explicit review gate instead of allowing silent durable overwrites.

### Maintenance and advanced dynamics

- `tools/memory/memory_maintenance.py`
- Computes reinforcement and archive recommendations using:
  - priority markers
  - recency
  - retrieval access counts

Archive recommendations remain review-driven. The current implementation does **not** auto-archive durable memory.

### Repeatable QA metrics

- `tools/memory/memory_qa.py`
- Produces:
  - `memory/reviews/memory-qa.md`
  - `memory/reviews/memory-qa.json`
- Tracks:
  - freshness
  - coverage
  - coherence
  - efficiency
  - reachability
  - review backlog
  - maintenance candidates

Reachability is benchmarked with fixed retrieval queries, which makes the QA output repeatable across runs.

### Guard and unified lifecycle history

- `tools/memory/memory_guard.py`
- Produces:
  - `memory/reviews/memory-guard.md`
  - `memory/reviews/memory-guard.json`
- Appends history to:
  - `memory/reviews/memory-guard-history.jsonl`
  - `memory/reviews/memory-qa-history.jsonl`

`memory-guard-history.jsonl` now doubles as the lifecycle breadcrumb stream. Instead of creating a second `session-breadcrumbs.jsonl`, the system extends the existing guard history with:

- `event_type`
- `session_id`
- `session_root`
- `safe_handover`
- optional artifact metadata

This keeps observability in one place and avoids parallel logging overhead.

## Session lifecycle integration

The memory runtime now spans three scripts:

1. `tools/session/start-session.ps1`
2. `tools/session/checkpoint-session.ps1`
3. `tools/session/close-session.ps1`

This moves the system away from close-only safety and toward start + checkpoint + close resilience.

## Dream-cycle extension

`tools/notes/notes_summarizer.py --dream` now adds:

- procedure-candidate extraction into `memory/reviews/procedure-candidates.md`
- smart recall when no new memory entries are added

This is the first episodic-to-procedural promotion path in the current runtime.

## Operational commands

```powershell
uv run tools/memory/memory_retrieval.py --query "working memory scratchpad"
uv run tools/memory/memory_reconcile.py --candidate-file ~\.copilot\session-state\<session>\files\memory-candidates.json
uv run tools/memory/memory_maintenance.py
uv run tools/memory/memory_qa.py
```

## Current limitations

- Reconciliation is heuristic and still needs human review for meaningful contradictions.
- Retrieval logging only starts after this implementation; older memories have no historical access trail.
- Maintenance recommendations intentionally stop at review artifacts, not automatic mutation.
- Procedure candidate extraction is lightweight pattern mining, not full workflow induction.
