---
created: 2026-04-15
owner: James
status: active
tags: [evals, backfill, schema, extraction]
---

# Workflow eval extraction rules

## Overview

These rules define how real workflow eval cases are mined from existing workspace artifacts. The goal is to grow the current seeded eval harness into a production-like local corpus without inventing synthetic fluff. A valid case must be traceable to a dated artifact, executable through the current eval runner primitives, and mapped to at least one ablation-relevant control.

## Case acceptance rules

Accept a candidate case only if all of the following are true:

1. The source artifact exists in the workspace and is stable enough to reference by path.
2. The case can be expressed with the current runner primitives:
   - `file_contains`
   - `trace_review`
3. The case describes a non-trivial workflow guarantee, not only file existence.
4. The case maps to at least one of:
   - `verifier`
   - `checkpoint`
   - `ledger`
   - `reconcile`
5. The case record can be encoded using `evals/case-schema.json`.

Reject a candidate if it is purely synthetic, requires human judgment to score, or depends on a personal/private artifact that should never become canonical framework evidence.

## Source priority

1. `plans/*.md`
2. `PersonalNotes/Daily/*.md`
3. `memory/reviews/*`
4. `memory/reviews/*.jsonl`
5. `wiki/*.md`

## Extraction rules by source family

### 1. Plans

Use plans first because they are the richest structured source for real workflow intent and expected behavior.

Accept a plan-derived case when the file contains:

- a clear workflow structure or phase boundary
- explicit validation or review intent
- a stable textual invariant that can be asserted later

Preferred suite mapping:

- `handoff`
- `research-synthesis`
- `hypothesis-discipline`

Example patterns:

- `validation_plan`
- `handoff_state`
- `### Checkpoint Summary`
- `## Hypothesis Ledger`

Suggested case type:

- `plan-validation`

### 2. Daily notes

Use daily notes to backfill real operating episodes and visible outcomes.

Accept a daily-note-derived case when the note contains:

- an `## 🤖 Agent Sessions` section
- a session with a concrete outcome or blocker
- a stable workflow signal that should remain true across similar sessions

Preferred suite mapping:

- `hypothesis-discipline`
- `handoff`
- `trace-quality`

Suggested case type:

- `daily-session`

Important constraint:

- Daily notes may reference personal context. Only extract workflow mechanics, not private content.

### 3. Review artifacts

Use review artifacts to backfill measurable signals already produced by the harness.

Accept a review-derived case when the review contains:

- a deterministic summary field
- a stable recommendation or guardrail
- a measurable status transition (`ok`, `warn`, `degraded`)

Preferred suite mapping:

- `trace-quality`
- `hypothesis-discipline`
- `reconcile`

Suggested case types:

- `review-signal`
- `reconcile-review`

### 4. Review history streams

Use JSONL histories to derive repeated transition-style regression cases.

Accept a history-derived case when an event stream shows:

- repeated status changes
- stable metric names
- a signal worth preserving after future changes

Preferred suite mapping:

- `trace-quality`
- `reconcile`

Suggested case type:

- `history-transition`

### 5. Wiki pages

Use wiki pages only after plans, daily notes, and reviews have been mined. Wiki pages are valuable for structural capability coverage but are weaker evidence for real operating episodes.

Accept a wiki-derived case when the page contains:

- a durable workflow principle
- a stable structural requirement
- explicit decomposition, uncertainty, or handoff guidance

Preferred suite mapping:

- `research-synthesis`
- `handoff`

Suggested case type:

- `plan-validation`

## Suite-specific targets

### research-synthesis

Target artifacts:

- AGI analysis pages
- strategy/research plans
- wiki pages with decomposition and eval guidance

What to preserve:

- hierarchical decomposition
- eval discipline
- typed handoffs

### handoff

Target artifacts:

- session-handoff skill
- complex plans
- daily notes showing cross-session continuity

What to preserve:

- explicit handoff state
- checkpoint summary visibility
- failure and hypothesis state carried across boundaries

### trace-quality

Target artifacts:

- agent review artifacts
- agent-performance history
- future richer trace files

What to preserve:

- verification visibility
- failure classification visibility
- fallback action visibility

### hypothesis-discipline

Target artifacts:

- plans with hypothesis ledger
- review artifacts with contradiction and open-hypothesis counts
- daily notes that describe uncertainty and next tests

What to preserve:

- contradiction visibility
- open hypothesis visibility
- confidence-bearing workflow structure

### reconcile

Target artifacts:

- memory reconciliation reviews
- memory procedures
- memory review histories

What to preserve:

- retrieval-before-write discipline
- typed reconciliation states
- review gating on contradictory or uncertain updates

## Pilot extraction target

The first pilot should produce **five real cases**:

1. Three from `plans/*.md`
2. Two from `PersonalNotes/Daily/*.md`

The pilot passes when:

- all five cases validate against `evals/case-schema.json`
- all five can be expressed with current runner primitives
- all five pass the workflow eval harness after integration

## Notes

- Prefer backfilled real artifacts over newly invented fixtures whenever possible.
- Keep capability and regression balanced, but do not force symmetry in the pilot.
- Do not mine private content into public-facing framework assets; only extract reusable workflow patterns.
