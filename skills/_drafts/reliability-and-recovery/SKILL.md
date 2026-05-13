---
name: reliability-and-recovery
description: "Operational reliability repeatedly depends on typed failures, fallback paths, recovery rules, and escalation signals."
agent: James
tools_required: [uv, powershell, review]
wiki_ref: "[[autonomic-tooling-pattern]]"
version: "0.1-draft"
status: draft
review_required: true
source_candidate: "reliability-and-recovery"
---

# Skill Draft: Reliability And Recovery

**Category:** Draft  
**Trigger:** Review required before canonical adoption  
**Owner:** James (CAO)

---

## Purpose

Operational reliability repeatedly depends on typed failures, fallback paths, recovery rules, and escalation signals.

---

## Why this draft exists

This stub was generated from `memory/reviews/skill-candidates.json` as a **reviewable draft**. It is not yet canonical and should not replace an existing skill without explicit review.

- **Candidate ID:** `reliability-and-recovery`
- **Reason:** `operational-reliability-pattern`
- **Suggested canonical target:** `memory\procedures.md`
- **Draft path:** `skills\_drafts\reliability-and-recovery`

---

## Proposed workflow

1. Review the evidence and decide whether this pattern deserves a canonical skill, an update to an existing skill, or only a procedure entry.
2. If promoted, merge the useful parts into the intended target instead of copying this draft blindly.
3. If rejected, keep or archive the draft as review history.

---

## Evidence

- `plans\2026-04-15-agent-management-and-model-routing.md` — if still stalled, stop/retry/escalate
- `plans\2026-04-15-agent-management-and-model-routing.md` — 4 Add arbitration/escalation path Disagreement between primary and verifier is resolved via explicit escalation rules cc:完了
- `plans\2026-04-15-agi-harness-epistemic-upgrades.md` — sandbox/fallback gaps for autonomous execution
- `plans\2026-04-15-agi-harness-epistemic-upgrades.md` — 2 Add fallback matrix Each failure class has retry/escalation/fallback rules integrated into runtime docs or tooling cc:完了
- `plans\2026-04-15-agi-harness-epistemic-upgrades.md` — 3 Extend trace and review Trace/review artifacts capture failure class and fallback path cc:完了

---

## Reviewer notes

- Decision:
- Target:
- Gaps:
- Next action:
