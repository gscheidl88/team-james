---
title: "OpenClaw May 2026 — Skill Workshop, Standing Orders & Auto-Dream v4.0"
id: openclaw-may2026
type: research
status: active
created: 2026-05-25
updated: 2026-05-25
created_by: James (CAO)
confidence: high
is_valid: true
tags: [openclaw, agent-ecosystem, skills, standing-orders, auto-dream, dream]
relates_to: [hermes-v012-v013, rowboat-patterns, agent-team-health]
sources:
  - https://github.com/openclaw/openclaw
  - https://docs.openclaw.ai/automation/standing-orders.md
live: false
---

# OpenClaw May 2026 — Skill Workshop, Standing Orders & Auto-Dream v4.0

## Overview

OpenClaw shipped six major releases in May 2026. The most impactful additions for our harness are the **Skill Workshop** (automated heuristic-driven skill capture), **Standing Orders** (persistent declarative session programs), and **Auto-Dream v4.0** (which revealed three gaps in our existing dream implementation: stale thread detection, growth metrics, and skip-with-recall). All three have been analyzed and partially or fully adopted.

---

## Skill Workshop

An automated skill-capture plugin that monitors every agent turn for heuristic triggers and proposes new skills to `skills/<skill-name>/SKILL.md`.

**Heuristic triggers (per turn):**
- User phrases: "next time", "from now on", "always...use/check/verify"
- Pattern repetition (same tool sequence across turns)
- Instruction emphasis ("make sure you always...")

**Review pipeline:**
- Every 15 turns OR every 8 tool calls: LLM reviewer pass
- States: `pending` → `auto` (auto-approved low-risk) or `quarantined` (dangerous-code scanner flagged)
- Built-in dangerous-code scanner (prevents skills with `rm -rf`, `DROP TABLE`, etc.)
- Approved skills written to `skills/<name>/SKILL.md`

**Our adoption:**
- We capture skills manually today; the heuristic-trigger pattern is valuable for future automation
- No automated trigger pipeline built (Copilot CLI does not expose per-turn plugin hooks)
- **Gap:** Manual skill capture only — rely on James to identify patterns and write skills
- **Future:** If Copilot CLI exposes `before_agent_finalize` hook, Skill Workshop pattern becomes implementable

**Status:** 🟡 INFERRED — pattern adopted conceptually; automation deferred

---

## Standing Orders

Persistent declarative programs defined in `AGENTS.md` (or equivalent config), injected automatically into every session context.

**Program anatomy:**
```
scope: [session|weekly|monthly]
trigger: [condition]
approval: [none|manual|gated]
escalation: [rule when step fails]
execute: [ordered steps]
```

**Execute-Verify-Report discipline:**
- Each step must be verifiable (produces observable output)
- Report results to Daily Note / log artifact
- Escalation rules fire when steps fail

**OpenClaw usage:**
- Combined with cron jobs for time-based enforcement
- Approval gates for high-risk operations (e.g., archive a skill, delete a file)

**Our adoption:**
- ✅ **Fully adopted** — Standing Orders section added to `AGENTS.md`
- 4 Standing Orders defined: Session Close (SO-01), Weekly Wiki Review (SO-02), Skills Lifecycle (SO-03), Memory Warmup (SO-04)
- Follow Execute-Verify-Report discipline
- No cron integration (manual trigger for time-based orders)

**Status:** 🟢 CONFIRMED — fully adopted in `AGENTS.md`

---

## Auto-Dream v4.0 — Gap Analysis

OpenClaw's Auto-Dream v4.0 shipped three features our existing dream cycle was missing.

### Gap 1: Dream Streak Counter ✅ ADOPTED

Track consecutive days the dream cycle runs. Motivates consistent session closing.

**Implementation:**
- `memory/index.json` — `dream_streak` counter + `last_dream_date`
- `notes_summarizer.py --dream` now reads/writes streak, resets on gap
- Output: `Dream Cycle -- 2026-05-25 | Streak: 3 days | Memory: 127 -> 129 entries (+2 / +1.6%)`

### Gap 2: Growth Metrics ✅ ADOPTED

Show how many entries were added vs last run as `N → N+delta (+X%)`.

**Implementation:**
- `memory/index.json` — `entry_counts.last_run_count` + `baseline_count`
- `notes_summarizer.py --dream` counts memory entries before/after, prints growth line

### Gap 3: Skip-with-Recall ✅ ADOPTED (improved)

When the dream cycle finds no new entries (empty run), surface a random old memory instead of silently skipping.

**Our implementation (improved over OpenClaw):**
- Prefers `📌 PIN`-marked entries from memory pool (higher signal)
- Falls back to any `[mem_NNN]` entry at random
- Prior code used `candidates[-1]` (last entry = always the most recent, not random)

---

## `before_agent_finalize` Hook

OpenClaw's plugin system added a `before_agent_finalize` hook: a plugin can request one additional model pass before the agent commits its response. Used as a quality gate.

**Our situation:**
- Copilot CLI does not expose this hook
- Equivalent: James explicitly re-reviews critical outputs before sending (manual quality gate)
- **Deferred** — no implementation possible without CLI plugin support

**Status:** 🔴 GAP — not implementable without CLI hooks

---

## Integration Summary

| Feature | Adopted | Tool / File | Notes |
|---------|---------|-------------|-------|
| Standing Orders | ✅ | `AGENTS.md` (SO-01 – SO-04) | Execute-Verify-Report discipline |
| Dream streak counter | ✅ | `notes_summarizer.py`, `memory/index.json` | Resets on gap day |
| Dream growth metrics | ✅ | `notes_summarizer.py`, `memory/index.json` | N→N+delta format |
| Skip-with-Recall (random + PIN-biased) | ✅ | `notes_summarizer.py` | Improved over OpenClaw |
| Skill Workshop automation | ❌ deferred | — | No per-turn plugin hooks in CLI |
| `before_agent_finalize` hook | ❌ N/A | — | CLI does not expose |
