---
id: agent-team-health
type: documentation
title: "Agent Team Health — Live Status"
description: "Live auto-refreshed summary of memory system health, knowledge graph state, and top compounding memories for the Gerhards Agent Team."
tags: [health, memory, knowledge, live, meta]
domain: meta

is_project: false
project:

status: active
is_valid: true
valid_from: 2026-05-10
valid_to:
expired_at:
superseded_by:

confidence: high
reviewed_by: James
review_date: 2026-05-10

created: 2026-05-10
created_by: James
last_modified: 2026-05-10
modified_by: James
source:
ingest_session:

relates_to: [memory-runtime-tooling, memory-session-lifecycle, knowledge-effectiveness-review, rowboat-patterns]
depends_on: []

live: true
refresh_tool: wiki_team_health_refresh
refresh_cadence: session
---
## Overview

Agent team health is a **live summary** of the memory and knowledge system state. It is auto-refreshed at each session close by `wiki_team_health_refresh.py`. Do not edit the body manually — changes will be overwritten. To fix issues, address the underlying artifacts in `memory/reviews/` or `wiki/reviews/`.

*Last refreshed: 2026-05-10 19:18*

---

## 🧠 Memory Health

| Metric | Value |
|--------|-------|
| Health score | **91.21** |
| Needs review | — |
| Archive candidates | — |
| Access log events | 6 |

### 🔥 Compounding Memories

🟡 No reinforcement data yet. Run `memory_retrieval.py --warmup` to seed the access log.

---

## 📚 Knowledge Graph Health

| Metric | Value |
|--------|-------|
| Status | 🟢 ok |
| Health score | **95.88** |
| Search index fresh | ✓ |
| Orphan pages | — |
| Search queries (30d) | 12 |

---

## 🔄 How to Fix Issues

| Problem | Command |
|---------|---------|
| Low compounding | `uv run tools/memory/memory_retrieval.py --warmup` |
| Stale search index | `uv run --python 3.12 tools/wiki/wiki_search.py --index` |
| Graph outdated | `uv run --python 3.12 tools/wiki/wiki_graph.py --build` |
| Memory needs review | Review `memory/reviews/memory-qa.md` |
| Archive candidates | Run `uv run tools/memory/memory_maintenance.py` |
