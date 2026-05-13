---
id: ecc-patterns-adopted
title: "ECC Patterns Adopted — everything-claude-code Integration"
type: research
created: 2026-05-13
updated: 2026-05-13
created_by: James
confidence: high
is_valid: true
tags: [agent-team, skill-contract, patterns, ecc]
relates_to:
  - "[[agent-team-setup]]"
  - "[[agent-orchestration-policy]]"
  - "[[claude-code-harness]]"
  - "[[archon]]"
  - "[[softaworks-agent-toolkit]]"
---

# ECC Patterns Adopted — everything-claude-code Integration

## Overview

Evaluated `affaan-m/everything-claude-code` (ECC) — a battle-tested Claude Code playbook with 25 agents, 108 skills, 57 commands, 18+ hooks, and 27 MCPs. ECC validates our existing agent/skill/memory architecture as sound. Five patterns were extracted for adoption; the hook system, InsAIts, devfleet, and slash commands were explicitly rejected as incompatible with Copilot CLI on Windows.

---

## Adopted Patterns

### 1. SKILL.md Required Sections: `## Anti-patterns` + `## Checklist`

**Source:** ECC skill format (all 108 skills carry structured anti-pattern and completion checklist sections)

**What we did:**
- Extended `skills/_contract.md` to require both sections as mandatory
- Updated 3 reference skills: `orchestration`, `data-analysis`, `research-strategy`
- Extended `tools/wiki/wiki_lint.py` to validate all `skills/*/SKILL.md` files for the required sections

**Value:** Prevents skill misuse drift; provides a pre-completion verification step that agents can run without reading the full skill documentation.

**Status:** 🟢 CONFIRMED implemented. 12 remaining skills flagged by lint — backlog.

---

### 2. `rules/` Directory (Injectable Quick-Reference Files)

**Source:** ECC `.claude/rules/` directory — domain-split rule files for context injection

**What we did:**
- Created `rules/delegation.md`, `rules/memory.md`, `rules/session.md`
- These are **supplementary**, not extracted from AGENTS.md (avoids bootstrap risk)
- AGENTS.md header now references `rules/` as quick-reference injection targets
- James can inject a specific rules file into a sub-agent prompt for targeted policy delivery

**Value:** Condensed, injectable rule references for sub-agent prompts — reduces prompt size vs. injecting all of AGENTS.md.

**Status:** 🟢 CONFIRMED implemented.

---

### 3. Plan Template Multi-Phase Format

**Source:** ECC multi-phase planning pattern (MVP → Core → Edge → Optimization, each independently deliverable)

**What we did:**
- Extended `plans/_template-complex-task.md` with a `## Phases` section
- Each phase has: Name, Deliverable, DoD, Status
- Rule: never start next phase until previous DoD is met

**Value:** Forces decomposition of large tasks into independently releasable slices; clearer handoff points.

**Status:** 🟢 CONFIRMED implemented.

---

### 4. Skill Lint Enforcement (wiki_lint.py extension)

**Source:** ECC pattern: structural contracts must be enforced by tooling, not just documentation.

**What we did:**
- Extended `tools/wiki/wiki_lint.py` with a full skill lint section
- New functions: `load_skills()`, `check_skill_sections()`, `print_skill_report()`
- New CLI flags: `--skills-only`, `--wiki-only`
- Reports missing `## Anti-patterns` and `## Checklist` per skill

**Value:** Skill contract drift is now automatically surfaced in the CI/session-close lint step — no manual audit needed.

**Status:** 🟢 CONFIRMED implemented. Lint correctly identifies 12 non-updated skills.

---

## Rejected Patterns and Why

| ECC Feature | Reason Rejected |
|-------------|-----------------|
| Hook system (PreToolUse/PostToolUse/SessionEnd) | Claude Code–specific API; Copilot CLI has no equivalent hook mechanism |
| InsAIts security monitoring | Node.js runtime dependency; Claude Code–specific |
| devfleet multi-agent | External SaaS; not local-first |
| 57 slash commands | Claude Code–specific format; incompatible with Copilot CLI |
| TDD enforcement rules | Not our primary workflow; would add overhead without benefit |
| Agent YAML frontmatter (`tools:`, `model:`, `scope:`) | Dead weight — nothing in the workspace reads it; deferred until a parser/router consumer is built |
| Language-specific rules (Go/Java/TypeScript) | Not a software dev shop primary use case |
| Claude marketplace / plugin system | Claude Code–specific install mechanism |

---

## Deferred Items

| Item | Reason Deferred |
|------|-----------------|
| Agent YAML frontmatter | Needs a consumer first (model_router.py, team-config.yaml) before it has value |
| skill_candidates.py git log source | Extend existing pipeline rather than new script — backlog |
| Update remaining 12 skills | Lint now enforces it; incremental updates as skills are next touched |

---

## Key Insight: ECC as Architecture Validation

ECC independently arrived at the same three-layer architecture (Agent / Skill / Memory) we use. Its 108 skills use the same trigger-based injection pattern we formalized in `_contract.md`. This provides strong external validation that our architecture is sound — the main gap was structural completeness (anti-patterns, checklists) rather than fundamental design.

---

## References

- Source repo: `affaan-m/everything-claude-code`
- Plan: `plans/2026-05-13-ecc-integration.md` (session plan folder)
- Rubber Duck review: GPT-5.4-mini cross-family verifier, 2026-05-13
