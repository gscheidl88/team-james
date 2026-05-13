---
name: verification-and-evals
description: "Quality gates repeatedly rely on review, verification, and explicit eval passes rather than ad hoc confidence."
agent: James
tools_required: [uv, powershell, review]
wiki_ref: "[[autonomic-tooling-pattern]]"
version: "0.1-draft"
status: draft
review_required: true
source_candidate: "verification-and-evals"
---

# Skill Draft: Verification And Evals

**Category:** Draft  
**Trigger:** Review required before canonical adoption  
**Owner:** James (CAO)

---

## Purpose

Quality gates repeatedly rely on review, verification, and explicit eval passes rather than ad hoc confidence.

---

## Why this draft exists

This stub was generated from `memory/reviews/skill-candidates.json` as a **reviewable draft**. It is not yet canonical and should not replace an existing skill without explicit review.

- **Candidate ID:** `verification-and-evals`
- **Reason:** `quality-assurance-pattern`
- **Suggested canonical target:** `skills\workflow-evaluation\SKILL.md`
- **Draft path:** `skills\_drafts\verification-and-evals`

---

## Proposed workflow

1. Review the evidence and decide whether this pattern deserves a canonical skill, an update to an existing skill, or only a procedure entry.
2. If promoted, merge the useful parts into the intended target instead of copying this draft blindly.
3. If rejected, keep or archive the draft as review history.

---

## Evidence

- `plans\2026-04-14-memory-roadmap-implementation.md` — 2 Candidate reconciliation review cc:完了
- `plans\2026-04-14-memory-roadmap-implementation.md` — 4 Session-close review + machine-readable candidate metadata cc:完了
- `plans\2026-04-15-agent-management-and-model-routing.md` — complex/critical: full review or arbitration path
- `plans\2026-04-15-agent-management-and-model-routing.md` — 5 Add review metrics Repeated metrics capture when verification was used, what it caught, and cost/latency impact cc:完了
- `plans\2026-04-15-agi-harness-epistemic-upgrades.md` — Our AGI notebook synthesis shows that the next maturity step for the workspace is not more raw memory, but more explicit epistemic and operational structure. The current harness is already strong on orchestration, lifecycle, review, and durable knowledge. The main remaining gap is that complex work still lacks first-class treatment of assumptions, uncertainty, validation plans, failure classes, and eval baselines.

---

## Reviewer notes

- Decision:
- Target:
- Gaps:
- Next action:
