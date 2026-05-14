---
id: autonomic-tooling-pattern
type: concept
title: "Autonomic Tooling Pattern"
description: "Classifies which workspace tasks should become autonomic tool-driven routines, which need guarded automation, and which should remain human-led."
tags: [automation, autonomic-system, operations, governance]
domain: meta
is_project: false
project:
status: active
is_valid: true
valid_from: 2026-04-25
valid_to:
expired_at:
superseded_by:
confidence: high
reviewed_by:
review_date:
created: 2026-04-25
created_by: James
last_modified: 2026-04-26
modified_by: James
source: Local synthesis from `tools/session/*.ps1`, `tools/wiki/*.py`, `tools/memory/*.py`, `tools/agents/*.py`, and `tools/github/issue_batch.py`
ingest_session: "[[log#2026-04-25-concept-autonomic-tooling-pattern]]"
relates_to:
  - "[[agent-orchestration-policy]]"
  - "[[memory-session-lifecycle]]"
  - "[[memory-runtime-tooling]]"
  - "[[knowledge-effectiveness-review]]"
  - "[[agent-ecosystem-upgrade-opportunities]]"
  - "[[windows-hardware-triage]]"
  - "[[bpmn-process-visualization]]"
depends_on: []
---

## Overview

The workspace should treat repeatable operational work like an autonomic nervous system: local tools handle the routine loops, while James watches health, exceptions, and priorities. The right split is not "automate everything," but "automate everything deterministic, repetitive, and inspectable." The governing rule is simple: if a task can be executed repeatedly from explicit inputs and judged by explicit checks, it belongs in `tools/`; if it needs trade-off judgment or changing intent, it stays human-led.

# Autonomic Tooling Pattern

## The three layers

### 1. Pure autonomic loops

These should run with little or no thinking once triggered:

- session preflight
- mid-session checkpoint flush
- session close finalization
- wiki lint
- wiki graph rebuild + search reindex
- memory QA
- memory guard
- knowledge performance review
- agent trace status + agent review
- dream consolidation
- issue preview generation
- skill candidate generation

**Why these belong in the autonomic layer:**  
They are deterministic, repetitive, checkable, and already mostly encoded as scripts.

### 2. Guarded autonomic loops

These should still be tool-driven, but only behind health checks, thresholds, or explicit review artifacts:

- promoting daily-note candidates into durable memory
- promoting repeated patterns into actual new `skills/`
- creating GitHub issues from opportunity seeds
- rebuilding knowledge indexes after content mutations
- delegation review and verifier usage
- scheduled ecosystem refresh scans

**Why these are guarded instead of fully automatic:**  
They mutate durable state or create external side effects. They need explicit guardrails, but not full human micromanagement every time.

### 3. Human judgment loops

These should remain led by James and the owner:

- setting priorities
- defining what "important" means
- making architectural trade-offs
- deciding when a candidate becomes canonical policy
- changing model-routing philosophy
- deciding whether a new pattern deserves a real skill or only a procedure

**Why these stay human-led:**  
They depend on intent, trade-offs, and strategic context rather than simple pass/fail checks.

## What is already in the vegetative nervous system

### Session lifecycle

Already encoded:

- `tools/session/start-session.ps1`
- `tools/session/checkpoint-session.ps1`
- `tools/session/close-session.ps1`

These already cover preflight, checkpointing, scratchpad finalization, memory review, QA, guard evaluation, knowledge review, and git sync.
They now also make wiki graph/search rebuilds and knowledge-review reruns depend on detected changed paths instead of operator memory alone.

### Memory and knowledge hygiene

Already encoded:

- `tools/memory/memory_guard.py`
- `tools/memory/memory_qa.py`
- `tools/memory/memory_reconcile.py`
- `tools/wiki/wiki_lint.py`
- `tools/wiki/wiki_graph.py`
- `tools/wiki/wiki_search.py`
- `tools/wiki/knowledge_review.py`
- `tools/notes/notes_summarizer.py`

This is the current heartbeat-breathing-digestion layer for memory and knowledge quality.

### Orchestration telemetry

Already encoded:

- `tools/agents/agent_trace.py`
- `tools/agents/agent_review.py`

This is the reflex arc: delegated work leaves machine-readable traces and gets reviewed instead of being remembered informally.

### Unified autonomic health surface

Already encoded:

- `tools/session/autonomic_dashboard.py`

This is the operator-visible dashboard for the whole autonomic layer: one place to see pulse, respiration, and backlog pressure.

### Research-to-backlog conversion

Already encoded:

- `tools/github/issue_batch.py`
- `sources/agent-ecosystem/2026-04-25-opportunities.json`

This is the first autonomic bridge from external signals to execution.

### Skill detection

Already encoded:

- `tools/agents/skill_candidates.py`

This is the first autonomic bridge from repeated local work to reusable operating patterns.

### Guarded skill-stub promotion

Already encoded:

- `tools/agents/skill_stub_promotion.py`
- `skills\_drafts\`

This closes the next step after candidate detection: repeated patterns can now become reviewable draft skills without silently becoming canonical policy.

### Recurring ecosystem refresh radar

Already encoded:

- `tools\research\ecosystem_refresh_radar.py`
- `memory\reviews\agent-ecosystem-refresh.json`
- `sources\agent-ecosystem\refresh-deltas.json`

This turns one-off external ecosystem analysis into a recurring loop: sources are re-fetched, compared against the stored baseline, written into review artifacts, and translated into issue-ready deltas when something materially changes.

### Knowledge refresh and retrieval probes

Already encoded:

- `tools\wiki\knowledge_refresh.py`
- `wiki\reviews\knowledge-refresh.json`
- `wiki\reviews\knowledge-performance-review.json`

This closes the repair gap in the knowledge layer: stale graph/search state can now be rebuilt, probe queries can populate retrieval telemetry, and the knowledge review is rewritten from fresh evidence instead of only surfacing drift.

### Hardware observability

Already encoded:

- `tools\hardware\usb_snapshot.py`
- `tools\hardware\usb_diff.py`
- `skills\hardware-triage\`
- `[[windows-hardware-triage]]`

This adds a first host-side hardware reflex loop: James can now compare before/after Windows-visible USB, PnP, disk, and volume state, surface partial capture instead of silently failing open, and support device-maintenance sessions with inspectable evidence rather than only general advice.

### Process visualization and BPMN drafting

Already encoded:

- `tools\process\event_log_to_process_map.py`
- `tools\process\process_map_to_bpmn.py`
- `skills\process-visualization\`
- [[bpmn-process-visualization]]

This adds a first data-driven process reflex loop: James can now turn local event data into mined transitions, variants, Mermaid process maps, and BPMN draft XML. The workflow is intentionally discovery-first and keeps heavier BPM suites as explicit future upgrades rather than default infrastructure.

## What should move next into the autonomic layer

### 1. Automatic label synchronization for GitHub issues

Current state: issue creation works, but missing labels are skipped with a note.  
Next step: add a repo-label sync or manifest so issue creation is fully consistent.

### 2. Autonomic health dashboard integration

Current state: the dashboard exists as a standalone command.  
Next step: integrate it into the session lifecycle and use it as the default operator status surface.

## What was just promoted into the autonomic layer

### Delegated agent trace automation

This is now encoded as a guarded operational loop:

- `tools\agents\delegate.py`
- `tools\agents\agent_review.py`
- `tools\session\autonomic_dashboard.py`
- `evals\trace-quality\suite.json`

The loop is intentionally wrapper-governed rather than pretending the external `task` tool can be intercepted. It now has an explicit delegation denominator, coverage verdicts, audit separation between missing spawn coverage and unclosed delegations, and regression coverage for both paths.

### Knowledge retrieval eval suite

This is now encoded as a repeatable regression surface:

- `tools\wiki\retrieval_probe.py`
- `evals\knowledge-retrieval\suite.json`
- `evals\knowledge-retrieval\artifacts\`

The loop now distinguishes operational self-healing from strict regression measurement. Retrieval probes can fail closed on `stale_index`, `stale_graph`, and `missing_source_node`, and the suite persists raw probe artifacts so future drift stays reviewable.

## Rule for deciding if a task belongs in tools

Put a task into `tools/` when all four are true:

1. **Repeatable** — it happens often enough to justify encoding
2. **Deterministic** — inputs and outputs can be described clearly
3. **Inspectable** — success/failure can be checked with artifacts or exit codes
4. **Low-judgment** — it does not require fresh strategic trade-offs every run

If one of these is false, keep the task human-led or move only part of it into tooling.

## How to keep future checks and integration safe

### A. Every autonomic loop needs a health signal

No hidden automation. Every loop should emit at least one of:

- exit code
- JSON artifact
- markdown review artifact
- trace line
- guard status

### B. Every autonomic loop needs an integration point

No orphan scripts. Every loop should be anchored in one of:

- session start
- session checkpoint
- session close
- scheduled task
- issue creation flow
- research ingest flow

### C. Every state-mutating loop needs a guard

If a tool changes durable memory, wiki knowledge, or external systems, it should run behind:

- retrieve-before-write
- review artifact generation
- health threshold
- explicit create/apply mode split

`issue_batch.py` already follows this pattern with preview vs create. More tools should do the same.

### D. Every important loop needs eval or lint coverage

The future standard should be:

- lint for structure
- review for operational quality
- eval for regression or capability

If a loop is important enough to rely on, it is important enough to measure.

## Recommended operating model

Think of James as the **cortex** and `tools/` as the **vegetative nervous system**:

- `tools/` maintains routine regulation
- James notices anomalies, sets goals, and chooses interventions
- the owner decides priorities and strategic direction

That is the stable split: tools regulate, James orchestrates, the owner decides.
