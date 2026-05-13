---
# ── Identity ──────────────────────────────────────────────
id: agent-orchestration-policy
type: documentation
title: "Agent Orchestration Policy and Model Routing"
tags: [agents, orchestration, model-routing, verification, governance]
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
confidence: high
reviewed_by: James
review_date: 2026-04-25

# ── Provenance ────────────────────────────────────────────
created: 2026-04-15
created_by: James
last_modified: 2026-04-25
modified_by: James
source: Local implementation in `AGENTS.md`, `skills/orchestration/`, `config/model-routing.yaml`, and `tools/agents/`
ingest_session: [[log#2026-04-15-documentation-agent-orchestration-policy]]

# ── Knowledge Graph ───────────────────────────────────────
relates_to:
  - "[[agent-team-setup]]"
  - "[[github-copilot-rubber-duck]]"
  - "[[github-copilot-sdk]]"
  - "[[agent-ecosystem-upgrade-opportunities]]"
  - "[[autonomic-tooling-pattern]]"
  - "[[memory-session-lifecycle]]"
  - "[[claude-code-harness]]"
  - "[[agi-project-analysis-patterns]]"
depends_on: []

description: "The workspace now has a fixed policy for sub-agent spawning, checkpointing, trace logging, and cross-family model verification, backed by local routing and review tooling."
---

## Overview

Gerhard's workspace now uses a concrete orchestration standard for delegated agent work. The policy combines three layers: a mandatory task descriptor for every sub-agent spawn, a declarative routing policy for primary and verifier models, and repeatable trace/review tooling so James can inspect delegated work operationally instead of relying on memory. The design is inspired by Rubber Duck's cross-family verification pattern, but implemented locally and deterministically through workspace files and scripts. The remaining limitation is that live sub-agent progress is still trace-driven rather than natively streamed through a manager console.

---

## Why this policy exists

Before this change, James could launch sub-agents but lacked a manager-grade operating loop:

- no mandatory spawn metadata
- no fixed checkpoint cadence
- no durable trace for delegated work
- no structural split between primary model and verifier model
- no repeatable KPI/review output for delegation quality

That made sub-agent work easy to start, but hard to supervise and hard to audit later.

---

## Operating policy

### Mandatory task descriptor

Every delegated task now includes:

- `task_id`
- `goal`
- `dod`
- `timeout_hint`
- `skill_context`
- `escalation_path`
- `model_override`

This makes every sub-agent call inspectable and reproducible.

### Checkpoint cadence

| Complexity | First check | Periodic check | Stall threshold |
|------------|-------------|----------------|-----------------|
| low | 15s | 45s | 90s without a new signal |
| medium | 30s | 90s | 180s without a new signal |
| high | 60s | 120s | 240s without a new signal |

James plans the first checkpoint before spawning the task. Delegation is not treated as fire-and-forget.

### Complex-task container standard

For medium+ tasks, James now uses an explicit host artifact instead of relying on prompt memory alone. The default host is a plan in `plans/` with these minimum fields:

- `assumptions`
- `validation_plan`
- `replan_rule`
- `handoff_state`

Checkpoint summaries must surface:

- `open_wip`
- `open_hypotheses`
- `blockers`
- `next_test`

This is the bridge between orchestration policy and epistemic upgrades: first make state visible, then make uncertainty richer.

### Stall escalation

If a delegated task stops producing meaningful progress:

1. James nudges once and requests a status update.
2. If the task is still stalled, James decides whether to retry, upgrade the model, absorb the task directly, or mark it blocked.
3. The decision is written into the trace and reflected in the plan or daily note.

---

## Model routing policy

The declarative source of truth is `config/model-routing.yaml`.

Routing is based on:

- `complexity`
- `task_type`
- `risk`
- `verification_need`
- `cost_profile`

### Primary model pattern

- trivial → economy
- standard → standard
- complex → strong standard
- critical → premium

### Verification pattern

- no verifier for trivial tasks
- spot-check verifier for medium-risk or complex work
- full review / arbitration for critical work

### Core verification rule

For meaningful review, verification is cross-family by default:

- Claude primary → GPT verifier
- GPT primary → Claude verifier

This is the durable local adoption of the Rubber Duck insight: second opinions are most useful when they are not produced by the same model family.

---

## Runtime components

### Prompt standard

`skills/orchestration/SKILL.md` provides the reusable delegation template, including:

- task metadata block
- routing metadata block
- plan-state block
- skill injection position
- expected return format

### Routing helper

`tools/routing/model_router.py` reads `config/model-routing.yaml` and returns:

- recommended primary model
- recommended verifier model
- verification need
- verifier prompt
- reusable routing metadata block

### Trace runtime

`tools/agents/agent_trace.py` records delegated work as JSONL events:

- `spawn`
- `checkpoint`
- `hypothesis_update`
- `failure_update`
- `stall`
- `complete`
- `failed`
- `cancelled`
- `blocked`
- `absorbed`

### Review runtime

`tools/agents/agent_review.py` turns trace history into repeatable operating metrics:

- completed vs open tasks
- failed / blocked / stalled tasks
- verification usage
- cross-family verification usage
- failure class counts
- fallback-action usage
- average completion time

It writes review artifacts to `memory/reviews/agent-performance-review.{json,md}` and appends history to `memory/reviews/agent-performance-history.jsonl`.

### Failure governance

Failure handling is now typed instead of ad hoc. `config/failure-taxonomy.yaml` is the source of truth for:

- `auth`
- `tool`
- `retrieval`
- `logic`
- `orchestration`

Each class defines a default retry, fallback path, and escalation trigger. Delegated-task traces and reviews can now carry:

- `failure_class`
- `fallback_action`
- `escalate_when`

This turns operational setbacks into inspectable recovery decisions instead of narrative-only notes.

### Private eval harness

The workspace now treats workflow quality as a local eval problem, not only a manual review problem. `tools/evals/run_workflow_evals.py` runs small private suites for recurring workflow classes and writes a repeatable review to `memory/reviews/workflow-eval-review.{json,md}`.

The active suite set is:

- `research-synthesis`
- `handoff`
- `trace-quality`
- `hypothesis-discipline`

Eval modes are explicit:

- `capability` checks whether the workflow contract exists and can produce the intended structure
- `regression` checks whether changes broke previously working workflow behavior

This gives the team a local measurement layer before any ablation or optimization work starts.

### Ablation review

Optimization is now gated by an explicit ablation review. `tools/evals/run_ablation_review.py` compares the current green workflow-eval baseline against the controls we might be tempted to relax:

- `verifier`
- `checkpoint`
- `ledger`
- `reconcile`

The rule is conservative by design:

- if a component has private-eval coverage, use that coverage to estimate what would be lost
- if a component is only backed by operational evidence, do not optimize it away yet

This keeps cost-optimization subordinate to measured workflow resilience.

---

## Session lifecycle integration

The session lifecycle scripts now include delegated-agent awareness:

- `start-session.ps1` checks the trace for unresolved delegated tasks before new work begins
- `checkpoint-session.ps1` surfaces open delegated tasks, runs the agent performance review, and prints a checkpoint summary block for open WIP, blockers, and next test
- `close-session.ps1` warns if delegated work is still open and writes a fresh review artifact

This does not provide real-time manager telemetry, but it does create an operational breadcrumb and review loop across sessions.

---

## Current limitation

The current Copilot CLI tool surface still does not expose a true built-in management console for sub-agents with rich progress state. James can inspect background tasks and read partial output during a session, but the persistent management layer is still local and trace-based.

In practice, that means:

- live progress remains checkpoint-driven
- unresolved delegated work is detected from trace state rather than native runtime hooks
- SDK-based lifecycle hooks remain the stronger future path for deeper orchestration

---

## Recommendation

Treat this policy as the new default operating model for delegated work:

1. route first
2. inject skill + metadata
3. trace spawn
4. inspect at cadence
5. review at checkpoint / close

This is strong enough for everyday team operations today, while still leaving room for a future SDK-based manager runtime.
