---
name: trace-aware-operations
description: "Delegated work is strongest when trace events, hypotheses, and next-test state remain visible during execution."
agent: James
tools_required: [uv, powershell, review]
wiki_ref: "[[autonomic-tooling-pattern]]"
version: "0.1-draft"
status: draft
review_required: true
source_candidate: "trace-aware-operations"
---

# Skill Draft: Trace Aware Operations

**Category:** Draft  
**Trigger:** Review required before canonical adoption  
**Owner:** James (CAO)

---

## Purpose

Delegated work is strongest when trace events, hypotheses, and next-test state remain visible during execution.

---

## Why this draft exists

This stub was generated from `memory/reviews/skill-candidates.json` as a **reviewable draft**. It is not yet canonical and should not replace an existing skill without explicit review.

- **Candidate ID:** `trace-aware-operations`
- **Reason:** `trace-governance-pattern`
- **Suggested canonical target:** `skills\orchestration\SKILL.md`
- **Draft path:** `skills\_drafts\trace-aware-operations`

---

## Proposed workflow

1. Review the evidence and decide whether this pattern deserves a canonical skill, an update to an existing skill, or only a procedure entry.
2. If promoted, merge the useful parts into the intended target instead of copying this draft blindly.
3. If rejected, keep or archive the draft as review history.

---

## Evidence

- `plans\2026-04-15-agent-management-and-model-routing.md` — 3 Add agent trace logging Spawn/complete/stall events are persisted to a machine-readable log cc:完了
- `plans\2026-04-15-agent-management-and-model-routing.md` — 4 Add agent monitor/checkpoint integration Existing lifecycle scripts capture trace-derived delegated task state and review signals cc:完了
- `plans\2026-04-15-agent-management-and-model-routing.md` — 3 Add verification protocol Task prompts include routing metadata and verifier role requirements cc:完了
- `plans\2026-04-15-agent-management-and-model-routing.md` — Add agent trace logging
- `plans\2026-04-15-agi-harness-epistemic-upgrades.md` — Container first: richer plan artifacts and checkpoint summaries should come before the Hypothesis Ledger.

---

## Reviewer notes

- Decision:
- Target:
- Gaps:
- Next action:
