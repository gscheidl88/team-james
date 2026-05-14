---
id: openclaw-auto-dream
type: research
title: "OpenClaw Auto-Dream — Cognitive Memory Architecture & Dream Cycles"
tags: [memory, knowledge-management, automation, agent-memory, obsidian]
domain: agent-memory

is_project: false
project:

status: active
is_valid: true
valid_from: 2026-04-08
valid_to:
superseded_by:
expired_at:

confidence: high
reviewed_by:
review_date:

created: 2026-04-08
created_by: Researcher
last_modified: 2026-04-08
modified_by: Analyst
source: https://github.com/LeoYeAI/openclaw-auto-dream

relates_to:
  - "[[openclaw-ecosystem]]"
  - "[[research-synthesis-memory-systems]]"
  - "[[embedded-db-comparison]]"
  - "[[zep-graphiti-memory]]"
depends_on: []
---

## Overview

OpenClaw Auto-Dream (v4.0) is a cognitive memory architecture for AI agents that implements a nightly "dream cycle" — a scheduled consolidation process that extracts structured knowledge from daily logs into five persistent memory layers. It introduces importance scoring with forgetting curves, health metrics for the memory system, and UX patterns (streaks, milestones) that reinforce consistent usage. The system is OpenClaw-specific at the runtime level, but its algorithms and layer model are directly transferable to any workspace with daily notes and a long-term memory file.

---

## Core Architecture

### Five Memory Layers

| Layer | Storage | Purpose |
|-------|---------|---------|
| Working | LCM plugin | Real-time context compression during active session |
| Episodic | `memory/episodes/*.md` | Project narratives, event timelines, story arcs |
| Long-term | `MEMORY.md` | Facts, decisions, people, milestones |
| Procedural | `memory/procedures.md` | Workflows, preferences, tool patterns |
| Index | `memory/index.json` | Metadata, importance scores, relations |

### Dream Cycle — 3 Phases (cron at 4 AM)

**Phase 1 — Collect**
- Scan unconsolidated daily logs (last 7 days)
- Detect priority markers (`⚠️`, `🔥`, `📌`, `<!-- important -->`)
- Extract: decisions, facts, lessons, procedures, open threads

**Phase 2 — Consolidate**
- Route extracted items to correct memory layer
- Semantic deduplication across existing entries
- Assign addressable IDs (`mem_NNN`), link relations between entries

**Phase 3 — Evaluate**
- Score importance (formula below), apply forgetting curves
- Compute health score (5 metrics)
- Generate 1–3 insights from patterns in consolidated data
- Write dream report, send notification

---

## Key Algorithms

### Importance Scoring

```
importance = (base_weight × recency_factor × reference_boost) / 8.0

recency_factor = max(0.1, 1.0 - days_since_created / 180)   # 6-month linear decay
reference_boost = log₂(reference_count + 1)                  # logarithmic citation boost

Markers:
  🔥 HIGH     → base_weight × 2
  ⚠️ PERMANENT → always scores 1.0 (bypasses formula)
```

### Forgetting Curve

- Entry **>90 days unreferenced** AND **importance < 0.3** → archived to `memory/archive.md`
- Archive format: one-line summary, original ID preserved (`mem_NNN`)
- `⚠️ PERMANENT` and `📌 PIN` entries are **immune** — never archived

### Health Score

```
health = (freshness×0.25 + coverage×0.25 + coherence×0.20 + efficiency×0.15 + reachability×0.15) × 100
```

| Metric | Definition |
|--------|-----------|
| Freshness | % of entries referenced in the last 30 days |
| Coverage | % of knowledge categories updated in the last 14 days |
| Coherence | % of entries that have at least one relation link |
| Efficiency | How concise MEMORY.md stays (vs. redundancy/bloat) |
| Reachability | How well-connected the knowledge graph is (avg degree) |

---

## Priority Markers

Use in Daily Notes and any source text to signal memory importance to future consolidation agents.

| Marker | Meaning | Effect |
|--------|---------|--------|
| `⚠️ PERMANENT` | Critical decision or invariant rule | Always scores 1.0; never archived; immune to forgetting |
| `🔥 HIGH` | High-importance fact or finding | Doubles base_weight in importance formula |
| `📌 PIN` | Reference material, stable knowledge | Immune to forgetting curve; not affected by recency decay |
| `<!-- important -->` | Inline HTML marker (programmatic) | Treated as general high-priority signal by parsers |

**Usage rules:**
- Place marker at the start of the line/sentence it applies to
- `⚠️ PERMANENT` is for things that should never be overridden without explicit revision (e.g., tooling choices, communication rules)
- `🔥 HIGH` is for the most important insight of a session — use sparingly
- `📌 PIN` is for reference facts you'll want to look up repeatedly (specs, URLs, formulas)
- Example: `⚠️ PERMANENT: We always use uv, never pip.`

---

## UX Patterns Worth Stealing

### Smart Skip + Recall
When no new content exists in the notes window, the dream cycle does **not** skip silently. Instead, it surfaces an old memory: *"N days ago, you decided…"* and shows the current dream streak count. This prevents habit interruption and provides value even on empty days.

### Stale Thread Detection
The cycle scans all "Open Threads" sections for `- [ ]` items older than 14 days. The top 3 most-stale items are surfaced in the notification. This prevents open loops from disappearing silently into the past.

### Dream Streak Counter
Tracks consecutive days with a completed dream cycle. Displayed in each notification. Psychological habit-formation mechanism.

### Milestone Celebrations
Triggered at: 1st dream, 7th dream, 30th dream, 100 entries, 200 entries, 500 entries. Each milestone emits a distinct notification with a short summary of system growth since last milestone.

### Weekly Sunday Summary
Every Sunday, the dream report includes a week-over-week growth diff: new entries added, entries archived, health score delta, entries referenced this week. Gives the owner a cadence-based mental model of memory growth.

---

## Fit Analysis

### Alignment with Our System

| Auto-Dream Concept | Our Equivalent | Status |
|-------------------|---------------|--------|
| `MEMORY.md` long-term layer | `memory/MEMORY.md` | ✅ Already have |
| Daily Notes as source logs | `PersonalNotes/Daily/` | ✅ Already have |
| Scheduled consolidation | `notes_summarizer.py` + Task Scheduler | ⚠️ Partial — summarizes only, no extract→file |
| Knowledge base beyond MEMORY.md | `wiki/` | ✅ Already have |
| `is_valid`/`expired_at` validity | Frontmatter fields | ✅ Already have |

### What We're Missing (High Value)

| Gap | Value | Complexity |
|-----|-------|-----------|
| Priority markers in Daily Notes | High | Zero — just a convention |
| `memory/procedures.md` procedural layer | High | Low — extract from AGENTS.md |
| `memory/episodes/` project narratives | Medium | Medium — requires synthesis |
| Dream consolidation in `notes_summarizer.py` | High | High — needs extract→MEMORY.md logic |
| Stale thread detection (open `- [ ]` > 14 days) | Medium | Medium |
| MEMORY.md entry IDs (`mem_NNN`) | Medium | Low — add IDs to new entries |
| Health score for `memory/` | Medium | Medium — different from wiki health |

### What to Skip

| Concept | Reason |
|---------|--------|
| `<!-- consolidated -->` HTML markers | OpenClaw-specific workflow markers |
| `memory/index.json` rigid format | We have Kuzu graph — strictly better |
| LCM working memory plugin | OpenClaw runtime, not applicable |
| Cross-instance migration | Single user/instance setup |
| MyClaw.ai cloud platform | Token-dependent, external |

---

## Adopted Patterns

### Implemented Now (this session)
- **Priority markers convention** — `⚠️ PERMANENT` / `🔥 HIGH` / `📌 PIN` added to `AGENTS.md` Daily Note Logging section and Daily Note template
- **`memory/procedures.md`** — Procedural memory layer created, extracted from AGENTS.md + USER.md

### Deferred (adopt later)
- **Dream consolidation step** in `notes_summarizer.py` — extract facts → `MEMORY.md` automatically; requires significant logic
- **`memory/episodes/`** — project narrative synthesis files; requires a synthesis agent pass
- **Stale thread detection** — scan open `- [ ]` items older than 14 days; can be added to summarizer
- **MEMORY.md entry IDs** (`mem_NNN`) — addressable entries; adopt when entries grow beyond ~50
- **Health score for `memory/`** — parallel to wiki health score; adopt after dream consolidation is running
