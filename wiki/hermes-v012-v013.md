---
title: "Hermes Agent v0.12.0 + v0.13.0 — Curator & Tenacity Releases"
id: hermes-v012-v013
type: research
status: active
created: 2026-05-25
updated: 2026-05-25
created_by: James (CAO)
confidence: high
is_valid: true
tags: [hermes, agent-ecosystem, memory, skills, goal-loop, session-search]
relates_to: [rowboat-patterns, agent-team-health, openclaw-may2026]
sources:
  - https://github.com/NousResearch/hermes-agent
live: false
---

# Hermes Agent v0.12.0 + v0.13.0 — Curator & Tenacity Releases

## Overview

Hermes Agent shipped two major releases in April–May 2026: v0.12.0 "The Curator Release" and v0.13.0 "The Tenacity Release". The key additions are the **Autonomous Curator** (background skill lifecycle manager), **FTS5 Session Search** (cross-session recall via SQLite), and the **Ralph Goal Loop** (`/goal` command with LLM judge). All three address gaps in our existing harness and have been partially adopted or directly inspire new tools.

---

## Autonomous Curator (v0.12.0)

The Curator is a background maintenance agent that manages the lifecycle of skills automatically.

**Sidecar file:** `skills/.usage.json`
- Fields per skill: `use_count`, `view_count`, `patch_count`, `last_used_at`, `state`, `pinned`
- States: `active` → `stale` (30d unused) → `archived` (90d unused)
- Pinned skills never transition.

**Lifecycle run:**
- Scans skills directory, loads usage sidecar
- Applies state transitions (check or apply mode)
- Optional LLM consolidation pass for near-duplicates (max 8 iterations)
- Backup before each run
- Produces `REPORT.md` + `run.json` per run
- Uses `auxiliary.curator` model slot (can use cheap model)

**Our adoption:**
- `skills/usage.json` — telemetry sidecar created
- `tools/skills/skills_curator.py` — lifecycle manager (check/apply modes)
- Wired into `close-session.ps1` via `Invoke-SkillsCurator`

**Gap vs Hermes:**
- LLM consolidation pass not yet implemented (deferred — low ROI without large skill library)
- No per-run `REPORT.md` artifact (using `memory/reviews/skills-curator.json` instead)

---

## FTS5 Session Search (v0.12.0)

All Hermes sessions are stored in a SQLite database with FTS5 full-text indexing. The agent can query across all prior sessions using a `session_search` tool — returning excerpts plus an LLM-generated summary.

**Key distinction from MEMORY.md:**
- MEMORY.md: always in context, hard 1300-token cap, high-signal curated facts
- Session Search: unlimited but requires explicit retrieval, low-signal raw history

**Our situation:**
- Copilot CLI already exposes `session_store` with FTS5 (the SQL tool in this session)
- No separate build needed — existing `session_store` database covers this pattern
- `memory_retrieval.py --warmup` provides a lighter warm-path recall

**Status:** 🟢 CONFIRMED — covered by existing Copilot CLI session_store

---

## Ralph Goal Loop — `/goal` command (v0.13.0)

The Goal Loop allows a user to declare a multi-turn goal once; an LLM judge then evaluates after each agent turn whether the goal is complete.

**Architecture:**
- `GoalManager` + `judge_goal` + `GoalState` in `hermes_cli/goals.py`
- Judge model: `auxiliary.judge` (separate model slot)
- Real user input always preempts the goal loop
- Judge failure mode: OPEN (never wedges agent)
- Goal state persisted in `SessionDB.state_meta`
- Default 20-turn budget

**Our situation:**
- Copilot CLI's autopilot mode partially covers this
- Ralph Goal Loop is architecturally interesting but requires native CLI integration we cannot add
- **Deferred** — revisit if Copilot CLI exposes plugin points for this

**Status:** 🟡 INFERRED — partially covered, not fully adoptable

---

## Checkpoints v2 (v0.12.0)

- Single bare git repo at `~/.hermes/checkpoints/store/`
- Per-project refs
- Real pruning with `max_total_size_mb: 500`
- Cleaner than prior multi-folder approach

**Our situation:** Copilot CLI manages session checkpoints natively. Not applicable.

---

## Self-Improvement Loop Upgrades (v0.13.0)

- Rubric-based (class-first) evaluation
- Active-update biased (always produces improvement if possible)
- Restricted toolset during self-improvement (no external calls)
- Clean context: prior-turn tool messages excluded during self-eval

**Our situation:** No self-improvement loop in our harness currently. Interesting pattern for future eval harness work (→ see `_drafts/verification-and-evals`).

---

## Integration Summary

| Feature | Adopted | Tool / File | Notes |
|---------|---------|-------------|-------|
| Skill usage telemetry | ✅ | `skills/usage.json` | Sidecar file, all skills seeded |
| Skill lifecycle manager | ✅ | `tools/skills/skills_curator.py` | check + apply modes |
| Session lifecycle wiring | ✅ | `close-session.ps1` + `session-lifecycle.ps1` | `Invoke-SkillsCurator` |
| FTS5 Session Search | ✅ (native) | Copilot CLI `session_store` | No additional build needed |
| LLM consolidation pass | ❌ deferred | — | Low ROI without large skill library |
| Ralph Goal Loop | ❌ deferred | — | No CLI plugin point |
| Self-improvement loop | ❌ deferred | — | Future eval harness work |
