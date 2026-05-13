---
name: reverse-engineering
description: "Structured workflow for understanding unfamiliar tools or codebases through scouting, git archaeology, architecture synthesis, and evidence-tagged findings"
agent: James
tools_required: [view, rg, powershell, git]
wiki_ref: "[[reversa-framework]]"
version: "1.0"
---

# Skill: Reverse Engineering

**Category:** Research + Engineering  
**Trigger:** Unfamiliar codebase analysis, tool onboarding, legacy workflow reconstruction, implementation archaeology  
**Owner:** James / Researcher / Developer

---

## Purpose

Use this skill when James needs to understand how an unfamiliar tool, repository, or workflow
actually works without pretending certainty too early.

The first-pass workflow is:

1. **Scout** the structure and operator surfaces,
2. **Detective** the hidden rules, assumptions, and git history,
3. **Architect** the component model and traceability,
4. capture findings with explicit evidence markers.

This skill adapts the strongest parts of the Reversa methodology into this workspace's native
plan/wiki/skill structure. It does **not** require installing Reversa itself.

---

## When to Use This Skill

- onboarding to an unfamiliar repository
- understanding a third-party tool before adoption
- reconstructing undocumented workflows or decision paths
- tool analytics for "what does this actually do and where are the seams?"
- preparing a bounded implementation or migration plan from an existing codebase

---

## Phase 1 — Scout

Goal: map the visible surface quickly before diving into details.

Look for:

- entry points (`README`, CLI entry files, package metadata, config roots)
- directory layout and major modules
- install/runtime assumptions
- inputs, outputs, and generated artifacts
- obvious user workflows

Typical actions:

- `glob` / `rg` for entry files and command names
- `view` for README, manifests, and main modules
- short directory scans before deep file reads

Deliverables:

- one-paragraph system summary
- list of core surfaces
- first hypothesis ledger entries

---

## Phase 2 — Detective

Goal: surface the implicit rules that are not obvious from the README alone.

Focus on:

- git archaeology (`git log`, reverts, hotfix commits, issue-linked commits)
- constraints encoded in config or validation logic
- failure modes and boundaries
- places where behavior is inferred rather than directly evidenced

Evidence notation:

- `🟢 CONFIRMED` — directly supported by source, code, or tool output
- `🟡 INFERRED` — best-supported interpretation, not directly confirmed
- `🔴 GAP` — meaningful unknown, unresolved ambiguity, or missing evidence

Deliverables:

- explicit assumptions and contradictions
- non-obvious rules or gotchas
- evidence-tagged findings instead of one-tone certainty

---

## Phase 3 — Architect

Goal: turn the evidence into a usable model for decisions.

Preferred outputs:

- component map (Mermaid or structured bullets)
- data/input/output flow
- operator workflow summary
- traceability matrix from source files/modules to behavioral claims
- adopt / adapt / skip recommendation if this is a tool-fit analysis

When useful, prefer language like:

- "The inspected repo suggests..."
- "This behavior is `🟡 INFERRED` from..."
- "The current evidence leaves a `🔴 GAP` around..."

Avoid language like:

- "The system definitely guarantees..."
- "This is fully understood" when major seams were not inspected

---

## Git Archaeology Heuristics

Git history often exposes design truth faster than polished docs.

Prioritize:

1. reverts — often reveal failed assumptions or unstable directions
2. hotfixes — often reveal the real expected behavior
3. commits touching validation, permissions, migrations, or schema files
4. repeated edits in the same area — often signal a brittle seam

Use history to extract:

- retroactive ADR clues
- hidden business rules
- operational constraints
- likely regression hotspots

---

## Recommended Outputs in This Workspace

- a plan in `plans/` for medium+ investigations
- a durable wiki page if the result should be findable in 3 months
- memory update if the finding becomes a durable workspace rule
- optional skill proposal if the same investigation pattern repeats

---

## Boundaries

This skill is strong for:

- codebase reconnaissance
- third-party tool fit analysis
- architecture reconstruction
- explicit uncertainty handling

This skill is **not** by itself:

- full static analysis
- binary reverse engineering
- security audit completeness
- proof that undocumented behavior is correct

---

## Minimal Checklist

- [ ] visible surfaces mapped
- [ ] hidden rules or constraints investigated
- [ ] evidence markers used where certainty varies
- [ ] output distinguishes fact vs inference vs gap
- [ ] recommendation ends in a concrete next step
