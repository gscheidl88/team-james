---
# ── Identity ──────────────────────────────────────────────
id: agi-project-analysis-patterns
type: analysis
title: "AGI Project Analysis Patterns for Team Processes and Harness Design"
tags: [agi, analysis, harness, evaluation, uncertainty, planning]
domain: meta

# ── Project Context ───────────────────────────────────────
is_project: false
project:

# ── Lifecycle / Validity ──────────────────────────────────
status: active
is_valid: true
valid_from: 2026-04-15
valid_to:
expired_at:
superseded_by:

# ── Quality / Confidence ──────────────────────────────────
confidence: medium
reviewed_by: James
review_date: 2026-04-15

# ── Provenance ────────────────────────────────────────────
created: 2026-04-15
created_by: James
last_modified: 2026-04-15
modified_by: James
source: "NotebookLM notebook: The Future of AGI: Intelligence, Alignment, and Economic Impact"
ingest_session: [[log#2026-04-15-analysis-agi-project-analysis-patterns]]

# ── Knowledge Graph ───────────────────────────────────────
relates_to:
  - "[[agent-orchestration-policy]]"
  - "[[human-memory-inspired-agent-memory-gap-analysis]]"
  - "[[knowledge-effectiveness-review]]"
  - "[[github-copilot-rubber-duck]]"
  - "[[agent-team-setup]]"
depends_on: []

description: "The strongest lessons from AGI/alignment/economic-impact research for our team are hierarchical decomposition, explicit uncertainty management, regression-style evaluation, typed handoffs, and harness-first design."
---

## Overview

The AGI notebook reinforces that sustainable progress on complex topics comes less from a stronger single model and more from a stronger operating system around the models. The recurring patterns are hierarchical decomposition, explicit uncertainty handling, continuous feedback loops, role specialization, and evaluation discipline grounded in real tasks rather than leaderboard metrics. For Gerhard's workspace, the conclusion is that the biggest next step is not more memory, but more epistemic structure: hypotheses, confidence, validation plans, and typed handoffs across long-running work.

## Core lessons from the notebook

### 1. Decomposition must be hierarchical

Complex work should not be handled as one large undifferentiated task. The strongest pattern is a split between:

- planning
- execution
- review
- testing / validation

This matches long-horizon agent research and also maps well to our existing planner / executor / verifier direction. The missing piece is a stronger plan artifact that survives replanning and handoffs.

### 2. Harness quality matters more than prompt cleverness

The notebook repeatedly points toward harness engineering: humans increasingly contribute by shaping the environment around the model rather than manually doing every step. That means:

- better context delivery
- better tool boundaries
- better memory and handoff state
- better review and fallback rules

This validates our current direction strongly.

### 3. Uncertainty must be explicit

The research repeatedly highlights epistemic humility. Good systems do not only produce an answer; they track:

- current hypothesis
- competing explanations
- confidence
- discriminating next test
- when to defer

This is the clearest gap in our current setup.

### 4. Evaluation must behave like an operating discipline

Static public benchmarks are not enough. Sustainable teams need:

- private regression sets
- rotated evaluation cases
- component-level reviews
- adversarial checks for unsafe or misleading behavior

For our workspace, that means turning key workflows into repeatable evals rather than relying only on spot judgment.

### 5. Specialized roles beat monolithic agency

The notebook's direction is strongly role-based:

- strategist / planner
- executor
- reviewer / verifier
- domain specialist

This supports our current sub-agent policy and argues for stronger role boundaries and clearer replan rights.

## What we already cover well

Our current workspace already has several good foundations:

- fixed sub-agent task descriptors
- checkpoint cadence and stall escalation
- cross-family verification
- scratchpad + retrieval + reconciliation memory model
- start / checkpoint / close lifecycle
- trace logging and review artifacts

So the notebook does not invalidate our design. It mainly shows where to deepen it.

## What still appears missing

### Hypothesis discipline

We do not yet have a standard artifact for assumptions, alternatives, confidence, and next tests. That makes analyses look more coherent than they really are.

### Stronger plan artifacts

We have plans, but not yet a standard structure for:

- decomposition
- validation strategy
- replan rules
- open hypotheses
- handoff state

### Eval harnesses for recurring workflows

We review memory and knowledge quality, but we do not yet have equivalent proprietary eval sets for:

- research synthesis
- long-running handoffs
- agent trace quality
- hypothesis handling

### Failure taxonomy

We still need a cleaner separation between:

- auth failures
- tool failures
- retrieval failures
- logic failures
- orchestration failures

Each class should have a known retry and fallback rule.

## Recommended upgrades

### Quick wins

1. Add a **Hypothesis Ledger** to medium+ research and analysis work:
   - hypothesis
   - confidence
   - evidence
   - contradiction
   - next test

2. Extend plan artifacts with:
   - assumptions
   - validation plan
   - escalation rule
   - next-session start state

3. Add a mandatory checkpoint summary block:
   - open WIP
   - open hypotheses
   - blockers
   - next test

### Structural upgrades

1. Move toward a **four-artifact harness**:
   - Plan
   - Implement / Execute
   - Review
   - Handoff

2. Add a **failure taxonomy + fallback matrix** for operational issues.

3. Build small **private eval suites** for recurring workflows instead of trusting ad hoc judgment.

4. Introduce periodic **ablation reviews**:
   - what changes if verifier is removed?
   - what changes if checkpointing is skipped?
   - what changes if reconciliation is bypassed?

## Suggested review KPIs

- `% medium+ tasks with explicit assumptions and validation plan`
- `% analysis tasks with at least one explicit hypothesis + confidence`
- `% critical tasks with deterministic check + verifier pass`
- `% open WIP sessions with visible handoff state`
- `% durable writes with typed reconsolidation state`
- `escaped regression count across sessions`

## Bottom line

The strongest lesson is simple: our next maturity step is not “more AI,” but **more disciplined thinking around AI**. We already have a solid harness and memory base. The next gains will come from making uncertainty, evaluation, and handoff state as explicit and reviewable as planning and execution already are.
