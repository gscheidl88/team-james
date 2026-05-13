---
name: handoff-discipline
description: "The workspace repeatedly reinforces explicit plan state, checkpoint blocks, and clean agent handoff behavior."
agent: James
tools_required: [uv, powershell, review]
wiki_ref: "[[autonomic-tooling-pattern]]"
version: "0.1-draft"
status: draft
review_required: true
source_candidate: "handoff-discipline"
---

# Skill Draft: Handoff Discipline

**Category:** Draft  
**Trigger:** Review required before canonical adoption  
**Owner:** James (CAO)

---

## Purpose

The workspace repeatedly reinforces explicit plan state, checkpoint blocks, and clean agent handoff behavior.

---

## Why this draft exists

This stub was generated from `memory/reviews/skill-candidates.json` as a **reviewable draft**. It is not yet canonical and should not replace an existing skill without explicit review.

- **Candidate ID:** `handoff-discipline`
- **Reason:** `manager-operating-pattern`
- **Suggested canonical target:** `skills\session-handoff\SKILL.md`
- **Draft path:** `skills\_drafts\handoff-discipline`

---

## Proposed workflow

1. Review the evidence and decide whether this pattern deserves a canonical skill, an update to an existing skill, or only a procedure entry.
2. If promoted, merge the useful parts into the intended target instead of copying this draft blindly.
3. If rejected, keep or archive the draft as review history.

---

## Evidence

- `plans\2026-04-15-agent-management-and-model-routing.md` — James can spawn sub-agents, but the operating model is still too implicit. We lack a fixed lifecycle policy for spawn/checkpoint/escalation, and our model selection is still coarse instead of structurally encoding primary-model choice, cross-family verification, and cost-aware routing.
- `plans\2026-04-15-agent-management-and-model-routing.md` — James follows a fixed checkpoint cadence:
- `plans\2026-04-15-agent-management-and-model-routing.md` — 1 Document sub-agent lifecycle policy AGENTS.md or dedicated policy doc defines spawn metadata, checkpoint cadence, and escalation cc:完了
- `plans\2026-04-15-agent-management-and-model-routing.md` — tools/session/checkpoint-session.ps1
- `plans\2026-04-15-agi-harness-epistemic-upgrades.md` — checkpoint summary discipline

---

## Reviewer notes

- Decision:
- Target:
- Gaps:
- Next action:
