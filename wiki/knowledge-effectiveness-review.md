---
id: knowledge-effectiveness-review
type: documentation
title: "Knowledge Effectiveness Review"
description: "Operational review model for the wiki RAG and knowledge-graph stack: telemetry, freshness checks, performance review artifacts, and routine integration."
tags: [knowledge, rag, knowledge-graph, observability, performance, review]
domain: meta
is_project: false
project:
status: active
is_valid: true
valid_from: 2026-04-15
valid_to:
expired_at:
superseded_by:
confidence: high
reviewed_by: James
review_date: 2026-04-15
created: 2026-04-15
created_by: James
last_modified: 2026-04-15
modified_by: James
source: "<WORKSPACE_ROOT>\tools\\wiki\\"
ingest_session: [[log#2026-04-15-documentation-knowledge-effectiveness-review]]
relates_to:
  - "[[agent-team-setup]]"
  - "[[memory-session-lifecycle]]"
  - "[[memory-runtime-tooling]]"
  - "[[karpathy-llm-wiki-pattern]]"
  - "[[embedded-db-comparison]]"
depends_on: []
---

## Overview

The knowledge stack now has an explicit operational review loop instead of relying on ad hoc spot checks. The key addition is a repeatable **knowledge performance review** that measures wiki quality, search-index freshness, graph connectivity, and actual tool usage. This makes the RAG and graph setup inspectable as a system, not just a collection of scripts.

## Problem that triggered the review layer

The wiki graph was structurally healthy, but the search layer could silently drift stale from current wiki content. In practice, this meant the graph could be up to date while LanceDB search still answered from an older index. We also lacked usage telemetry for `wiki_search.py` and `wiki_graph.py`, so effectiveness was mostly assumed rather than measured.

## Runtime components

### Telemetry

- `wiki/reviews/wiki-search-log.jsonl`
- `wiki/reviews/wiki-graph-log.jsonl`

Search logs record:

- `event_type` (`query`, `index_build`)
- query mode
- result count
- top hit
- duration
- index freshness metadata

Graph logs record:

- `action` (`build`, `stats`, `neighbors`, `deps`, `query`)
- page id or query when relevant
- duration

### Freshness control

`tools/wiki/wiki_search.py` now writes `<WORKSPACE_ROOT>\.wiki_index\wiki-search-metadata.json` with:

- build timestamp
- page count
- manifest hash
- embedding model name

This makes search-index freshness explicit and reviewable rather than implicit.

### Repeatable review artifact

`tools/wiki/knowledge_review.py` produces:

- `wiki/reviews/knowledge-performance-review.json`
- `wiki/reviews/knowledge-performance-review.md`
- `wiki/reviews/knowledge-performance-history.jsonl`

The review combines:

- wiki schema compliance from `wiki_analytics.py`
- graph structure from `wiki_graph.py`
- search-index freshness from metadata
- usage signals from search/graph logs

## Current scoring model

The review currently scores four components:

1. compliance
2. graph connectivity
3. index freshness
4. adoption

It emits a `status` of:

- `ok` — knowledge stack is operationally healthy
- `warn` — usable, but freshness or adoption follow-up is needed
- `degraded` — do not trust the stack without repair

## Routine integration

### Start preflight

`tools/session/start-session.ps1` now runs the knowledge performance review after the memory guard so James sees search/graph issues at session start.

### Mid-session checkpoint

`tools/session/checkpoint-session.ps1` also runs the review. This keeps long sessions aware of knowledge drift instead of deferring all checks to close.

### Close handover

`tools/session/close-session.ps1` now:

1. rebuilds the wiki graph
2. rebuilds the LanceDB search index
3. runs the knowledge performance review

This means the next session should inherit a fresh graph and fresh search index by default.

## Current limitations

- The search script currently rebuilds the vector index when explicitly requested, which is correct but not cheap.
- Adoption metrics are still young; low counts today mean low observed usage, not necessarily low long-term value.
- The graph review currently treats structural usage separately from graph rebuilds, so a healthy build pipeline does not by itself count as graph exploration.
