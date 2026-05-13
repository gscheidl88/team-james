---
id: karpathy-llm-wiki-pattern
type: research
title: "Karpathy LLM Wiki Pattern — Fit Analysis"
tags: [knowledge-management, llm, wiki, architecture, obsidian]
domain: meta

is_project: false
project:

status: active
is_valid: true
valid_from: 2026-04-08
valid_to:
superseded_by:

confidence: high
reviewed_by: Gerhard
review_date: 2026-04-08

created: 2026-04-08
created_by: Researcher
last_modified: 2026-04-08
modified_by: Analyst
gist_last_updated: 2026-04-08
source: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
ingest_session: "[[log#2026-04-08-research-karpathy-llm-wiki-pattern]]"

relates_to:
  - "[[agent-team-setup]]"
  - "[[tooling-policy]]"
  - "[[personal-notes-system]]"
  - "[[research-synthesis-memory-systems]]"
  - "[[ai-git-commit]]"
depends_on: []
---

## Overview

Analysis of Andrej Karpathy's LLM Wiki pattern — a three-layer knowledge architecture (index, log, content pages) for AI agents. This pattern directly inspired our wiki/ knowledge layer. The page documents our gap analysis (we had ~60% of the pattern before) and the implementation decisions we made to adopt it.

# Karpathy LLM Wiki Pattern — Fit Analysis

## Executive Summary

The Karpathy LLM Wiki pattern formalizes a persistent, LLM-maintained knowledge base that compounds over time. Our workspace already has the Schema layer (`AGENTS.md`), a partial wiki (`MEMORY.md`), the IDE (Obsidian), and the LLM writer (James). What we lacked was the actual wiki layer — structured entity/concept pages, a content catalog, an ingest log, and a search tool. This page documents that gap and the response.

---

## The Pattern

Three layers:

1. **Raw Sources** (`sources/`) — immutable inputs. LLM reads, never modifies.
2. **Wiki** (`wiki/`) — LLM-maintained markdown pages. Incrementally updated as sources are ingested or questions are answered.
3. **Schema** (`AGENTS.md`) — governs agent behavior, page conventions, workflows.

Operations:
- **Ingest**: new source → LLM writes/updates wiki pages → appends to `log.md`
- **Query**: question → LLM reads wiki → answers → optionally files answer as new page
- **Lint**: health-check for orphans, contradictions, stale content

Key insight: **good answers become wiki pages** — explorations compound in the knowledge base.

---

## Fit Analysis

| Karpathy Element | Our Equivalent | Gap |
|---|---|---|
| Schema (AGENTS.md) | `AGENTS.md` — full team constitution, auto-loaded | None |
| Wiki IDE | Obsidian Vault = `<WORKSPACE_ROOT>` | None |
| LLM writer | James (CAO) | None |
| Wiki pages | `memory/MEMORY.md` (flat facts only) | Critical — flat ≠ structured pages |
| `index.md` catalog | Nothing | Missing |
| `log.md` | Nothing formal | Missing |
| Raw sources dir | Nothing | Missing |
| Ingest workflow | Nothing | Missing |
| Lint operation | Nothing | Missing |
| Search tool | Nothing | Missing |
| Procedural knowledge | `skills/` library (5 skills) | Strong — exceeds Karpathy |

---

## Key Decisions Made

- **MEMORY.md stays separate** — fast agent-bootstrap register; wiki is deeper structured knowledge
- **Daily Notes pipeline is independent** — covers session logging; `log.md` covers knowledge-layer ingest
- **No qmd MCP** — custom Python BM25 (`tools/wiki/wiki_tool.py`) fits tooling policy, sufficient at our scale
- **Wiki scope expanded** — not just external sources; all research, analysis, and documentation we produce together goes in the wiki

---

## New Findings (2026-04-08 Update)

The gist was updated on **2026-04-08** (today) — it is actively maintained by Karpathy. Key additions:

### Dataview Plugin
[Dataview](https://github.com/blacksmithgu/obsidian-dataview) is an Obsidian plugin that runs SQL-like queries over page frontmatter and renders dynamic tables directly in the editor. Our wiki already has rich, consistent frontmatter (`status`, `domain`, `confidence`, `tags`, `is_valid`, etc.) — this makes us an immediate fit for Dataview queries without any schema changes. Example use: a live table of all `status: active` research pages, or all pages with `confidence: low` flagged for review. **Gap: Dataview plugin not yet installed.**

### Lint Operation
Karpathy explicitly describes a periodic **lint pass**: ask the LLM to health-check the wiki. Checks include:
- Contradictions between pages
- Stale claims superseded by newer sources
- Orphan pages with no inbound links
- Important concepts mentioned but lacking their own page
- Missing cross-references and data gaps

We have `tools/wiki/wiki_analytics.py` (KPI dashboard) but it does not perform a lint pass. This is a distinct operation. **Gap: `wiki_lint.py` does not exist.**

### Query → File Back Protocol
Karpathy's pattern: "good answers can be filed back into the wiki as new pages. A comparison you asked for, an analysis, a connection you discovered — these are valuable and shouldn't disappear into chat history."

We do this informally (e.g., research sessions produce wiki pages). It should be formalized as a protocol in `AGENTS.md`: any answer James produces that meets a quality threshold (novel insight, synthesis, decision rationale) should be proposed as a new wiki page. **Gap: not in AGENTS.md as an explicit rule.**

### Obsidian Web Clipper
The [Obsidian Web Clipper](https://obsidian.md/clipper) is a browser extension that converts web articles to markdown and saves them directly to the vault's `sources/` directory. Practical for ingesting blog posts, documentation pages, and gists without copy-paste. Integrates with our existing sources/ convention.

---

## Implementation Status

- [x] `wiki/` directory created
- [x] `wiki/_schema.md` — frontmatter standard with knowledge-graph fields
- [x] `wiki/index.md` — content catalog
- [x] `wiki/log.md` — append-only log
- [x] This page filed
- [x] `tools/wiki/wiki_analytics.py` — KPI dashboard (DuckDB)
- [x] `tools/wiki/wiki_search.py` — hybrid BM25+vector search (LanceDB)
- [x] `tools/wiki/wiki_graph.py` — knowledge graph (Kuzu)
- [x] Wiki seeded with existing material (9 pages)
- [ ] `sources/` directory
- [ ] Wiki protocol added to `AGENTS.md`
- [ ] `wiki_lint.py` — lint operation (orphans, stale claims, missing cross-refs)
- [ ] Dataview plugin + frontmatter queries in Obsidian
- [ ] Formal Query→Wiki protocol in AGENTS.md
- [ ] Obsidian Web Clipper installed

---

## Recommended Next Steps

1. `sources/` directory + ingestion convention
2. Wiki protocol in `AGENTS.md` (behavioral rule for James)
3. `tools/wiki/wiki_tool.py` with lint + BM25 search
4. Seed wiki with: agent team setup, tooling policy, obsidian setup

---

## References

- Source: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
- Related: Vannevar Bush's Memex (1945)
- Tool mentioned: [qmd](https://github.com/tobi/qmd) — not adopted (see tooling policy)
