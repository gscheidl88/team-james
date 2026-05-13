---
id: research-synthesis-memory-systems
type: decision
title: "Memory Systems Research Synthesis — OpenClaw, Zep/Graphiti, OpenViking, Cognee"
tags: [memory, synthesis, decision, knowledge-graph, agent-memory]
domain: agent-memory
is_project: false
status: active
is_valid: true
valid_from: "2026-04-08"
confidence: high
created: "2026-04-08"
created_by: Analyst
last_modified: "2026-04-14"
modified_by: James
source: "internal"
ingest_session: "2026-04-08"
relates_to: ["[[openclaw-ecosystem]]", "[[zep-graphiti-memory]]", "[[openviking-context-db]]", "[[cognee-memory]]", "[[agent-team-setup]]", "[[tooling-policy]]", "[[openclaw-auto-dream]]", "[[human-memory-inspired-agent-memory-gap-analysis]]", "[[mnemosyne-memory]]"]
depends_on: ["[[openclaw-ecosystem]]", "[[zep-graphiti-memory]]", "[[openviking-context-db]]", "[[cognee-memory]]"]
---

## Overview

Cross-system synthesis comparing four agent memory frameworks (OpenClaw, Zep/Graphiti, OpenViking, Cognee) across architecture, local-first viability, and adoptability. Contains a decision matrix, seven adopt-now items (zero new dependencies), five adopt-later items (Kuzu+LanceDB, wiki_tool etc.), and an explicit skip list. The central finding is that temporal validity, L0/L1/L2 depth, and hybrid vector+graph storage are universal patterns across all four systems.

# Memory Systems Research Synthesis — OpenClaw, Zep/Graphiti, OpenViking, Cognee

## 1. Executive Summary

- **We independently arrived at the right abstractions.** Our wiki frontmatter (`is_valid`, `valid_from`, `valid_to`, `depends_on`, `relates_to`) is a near-exact conceptual replica of Graphiti's `EntityEdge` temporal model — designed independently by two different teams solving the same problem. This is strong validation that our schema is correct.
- **None of the four systems is a drop-in adopt.** OpenClaw requires Node.js/WSL2; Graphiti and Cognee require LLM API calls on every write; OpenViking requires a VLM running persistently. All conflict with our zero-new-dependencies, local-first, token-free baseline. The value is in *patterns*, not installations.
- **Two data model concepts are universally worth stealing:** the L0/L1/L2 multi-resolution summary pattern (OpenViking) and the episode-provenance chain (Graphiti/Cognee). Both can be adopted as manual conventions right now without any tooling.
- **Kuzu + LanceDB is the correct local graph+vector pair** when we need those layers. Both are embedded (no server process), pip-installable, and used as local defaults in both Cognee and Graphiti. This convergence is evidence, not coincidence.
- **Our biggest gap is memory structure, not retrieval.** OpenViking's 8-category memory taxonomy exposes that our flat `USER.md` conflates facts with different lifecycles. Restructuring memory/ is high-value and zero-cost.

---

## 2. Comparison Matrix

| System | Architecture | Local-first | Python | Token-free writes | What to steal | Verdict |
|---|---|---|---|---|---|---|
| **OpenClaw** | Node.js gateway daemon + plugin ecosystem | Needs WSL2 on Windows | No (TypeScript) | Yes (no LLM for workflow execution) | Lobster YAML pipeline format; claims frontmatter; layered AGENTS.md; wiki digest pattern | Adopt patterns only — runtime incompatible |
| **Zep/Graphiti** | Temporal knowledge graph (episodes to edges with valid_at/invalid_at) | Yes via Kuzu (embedded) or FalkorDB (Docker) | Yes (`uv add graphiti-core`) | No — LLM required for entity extraction | `expired_at` field; context budget discipline; atomic FACT notation in MEMORY.md; episode provenance concept | Adopt schema concepts now; full stack only if LLM cost is justified |
| **OpenViking** | Virtual filesystem (Go binary) + L0/L1/L2 summaries + VLM-driven retrieval | Yes — pip installs bundled binaries | Yes (Python SDK) | No — VLM required for L0/L1 generation | L0/L1/L2 depth model; 8-category memory taxonomy; agent/user memory split | Adopt taxonomy and depth model as conventions — full stack requires always-on VLM |
| **Cognee** | `add -> cognify -> search` pipeline with pluggable graph/vector/relational backends | Yes — Kuzu + LanceDB + SQLite (all embedded) | Yes (`uv pip install cognee`) | No — LLM required for `cognify()` | Kuzu as local graph DB; LanceDB as local vector store; SearchType discriminator; pydantic-settings config | Adopt tool patterns; skip as full dependency at current scale |

---

## 3. Cross-cutting Themes

These patterns appear in 2 or more of the four systems — convergent evidence that they solve real problems.

### Temporal validity is a first-class concern
Graphiti, our wiki frontmatter, and OpenViking's memory decay all independently model that facts have a lifespan. Graphiti separates `invalid_at` (when the fact stopped being true) from `expired_at` (when the system *detected* this). Our schema has `valid_to` but lacks `expired_at`. The distinction matters: a decision can become outdated in November but get discovered in January.

### Multi-resolution depth (L0 / L1 / L2)
OpenViking formalises this as `.abstract.md` (~100 tokens), `.overview.md` (~2k tokens), and full content. Cognee implements it as chunked embeddings, entity summaries, and raw documents. Graphiti implements it as CommunityNode summaries -> EntityNode summaries -> EntityEdge facts -> EpisodicNode raw content. The core principle: agents should filter at low resolution before loading full content. Our `description:` frontmatter field is a manual L0; we have no L1 equivalent.

### Hybrid vector + graph retrieval
Three of the four systems (Graphiti, Cognee, OpenViking) combine semantic vector search with structured graph or directory traversal. Flat RAG loses document topology. The winning architecture: vector search narrows candidates, then graph/directory structure re-ranks by coherence. Kuzu + LanceDB is the local implementation target if we ever build this layer.

### LLM as the ingestion bottleneck
All four systems that do automatic knowledge extraction require an LLM for ingestion — there is no token-free path to automated graph/entity construction. This is not a design flaw; it is the fundamental trade-off. Automated extraction costs tokens; manual frontmatter costs human time. At our scale, human time wins. The crossover point is when corpus volume or churn makes manual maintenance impractical.

### Agent/user memory split
OpenViking explicitly partitions memory into `user/` (profile, preferences, entities, events — facts *about* Gerhard) and `agent/` (cases, patterns, tools, skills — things the *agent* learned). Cognee mirrors this with user vs. agent ontologies. Our `USER.md` and `MEMORY.md` implicitly conflate these two streams. Separating them clarifies lifecycles: user facts are updated in-place; agent-learned cases are immutable append entries.

### Claims vs. pages
OpenClaw's `memory-wiki` plugin tracks `claims:` as first-class objects with `{ id, text, confidence, evidence[] }` — separate from the page they live in. Graphiti tracks `EntityEdge.fact` as an atomic NL string with its own temporal envelope. Both point away from page-level confidence toward claim-level confidence. Our current model operates at page granularity.

---

## 4. Adopt Now

Zero new dependencies. Implement as conventions or lightweight scripts today.

**A. Add `expired_at:` to wiki schema**
Add to `_schema.md` alongside `valid_to`. `valid_to` = when the fact stopped being true in the world. `expired_at` = when we discovered this. For time-sensitive research pages (tooling decisions, vendor assessments), this distinction is real and cheap to track.

**B. Restructure `memory/` with the 8-category taxonomy**
No tooling required — just reorganise files. Split `USER.md` into `memory/user/profile.md`, `memory/user/preferences.md`, `memory/user/entities.md`, `memory/user/events.md`. Add `memory/agent/cases.md`, `memory/agent/patterns.md`, `memory/agent/tools.md`. Events and cases are immutable (append-only); others are mergeable (in-place update).

**C. Enforce L0 `description:` on every wiki page and skill**
One sentence, 100 tokens max. This is a manual L0 — enough for an agent to decide relevance before loading the full document. Already partially done; make it a required schema field.

**D. Adopt context budget discipline in `START-SESSION.md`**
From Graphiti's context engineering research: structure session bootstrap so highest-signal facts appear in the first ~2000 characters. Order: current-session facts first, then MEMORY.md extracts, then background wiki links. Document the budget ceiling in `tooling-policy.md`.

**E. Add `claims:` frontmatter array to fact-heavy wiki pages**
For pages making multiple distinct factual assertions (tooling-policy, agent-team-setup, any decision page), add: `claims: [{ id, text, confidence, evidence }]`. Start with 2-3 pages as a pilot. No new tooling — just structured YAML.

**F. Add layered AGENTS.md to key subdirectories**
One-paragraph files in `skills/`, `tools/`, `wiki/`, `memory/` describing what each directory owns, what agents may change, and naming conventions. Inspired by OpenClaw's progressive-disclosure AGENTS.md discipline.

**G. Atomic FACT notation in MEMORY.md**
For preference and decision entries, add a structured summary line:
```
> FACT: (Gerhard, PREFERS_TOOL, uv) | valid_from: 2026-01-15
```
Keeps MEMORY.md human-readable prose while making key facts machine-parseable without an LLM.

---

## 5. Adopt Later

Worth building when the time is right — requires new tooling or infrastructure investment.

**H. `wiki_tool` with Kuzu + LanceDB backend**
When we want semantic search over the wiki, the correct local stack is: Kuzu (embedded graph, file-based) for `relates_to` / `depends_on` traversal, and LanceDB (embedded vector store) with `nomic-embed-text` via Ollama for semantic search. Both are `pip install`, no Docker, no server. Cognee and Graphiti both validate this pair independently.

**I. `wiki_digest.py` — compiled machine-readable snapshot**
A Python script (using `uv run`) that parses all frontmatter from `wiki/*.md` and emits `wiki/_digest.json`: a flat index of all pages with their `id`, `tags`, `domain`, `confidence`, `is_valid`, `relates_to`, and `description`. Enables agents to reason about the wiki without reading every file. Inspired by OpenClaw's `memory-wiki` agent-digest pattern.

**J. Wiki dashboard reports**
Auto-generated from frontmatter queries on `_digest.json`: `wiki/reports/low-confidence.md` (all pages with `confidence: low`), `wiki/reports/open-questions.md`, `wiki/reports/contradictions.md` (pages where `superseded_by` is set but `is_valid: true`). Inspired by OpenClaw's `memory-wiki` dashboard layer.

**K. L1 directory overview files**
Add a `_overview.md` to `wiki/`, `memory/`, and `skills/` providing a ~500-token structured navigation guide for that directory. An agent can load this before deciding which files to open. Manually written (no LLM required), reviewed quarterly.

**L. Graphiti with Kuzu for high-value session ingestion (conditional)**
If a specific use case emerges where automated temporal reasoning over past sessions is worth the token cost (~$0.001-0.005 per session at gpt-4o-mini), `graphiti-core[kuzu]` is the lowest-friction path. The Graphiti MCP server would then give Claude/Cursor access to a persistent fact graph. Prerequisite: validate Kuzu works on Windows without friction.

---

## 6. Skip

Explicitly decided against — not just deferred.

| What | Why |
|---|---|
| **OpenClaw runtime** (gateway daemon, npm, WSL2) | Our stack is Copilot CLI + Python + Windows-native. A Node.js daemon adds operational overhead with no benefit we can't get from pattern-stealing alone. |
| **Zep Cloud** | Managed service, requires API token. Conflicts with tooling policy. Community Edition deprecated. |
| **OpenViking full stack** (AGFS + VLM) | Alpha software requiring an always-on vision model. Most value can be extracted as conventions without installation. Alpha churn risk is real. |
| **Cognee as a full dependency** | 50+ transitive dependencies. The `cognify()` pipeline is LLM-call-per-chunk — overkill for structured Markdown pages where we already have hand-authored frontmatter. We've done the hard work manually. |
| **Full Graphiti ingestion of existing wiki** | Redundant: our frontmatter already encodes what Graphiti would auto-extract. Running LLM entity extraction over structured Markdown we authored would produce lower-quality output than what we already have. |
| **Cognee Cloud / Zep Cloud / any SaaS memory layer** | Conflicts with local-first policy. Data sovereignty matters. |
| **ACP / acpx CLI** (monitor, not skip) | The *protocol* is worth watching; `acpx` is alpha. Revisit when stable. |
| **OpenClaw messaging channels** (WhatsApp, Telegram, etc.) | Not our interface paradigm. We are terminal / VS Code users. |

---

## 7. Open Questions

1. **Memory restructure scope:** Should the 8-category taxonomy restructure happen immediately or after a session to validate the categories fit Gerhard's actual usage patterns? Risk of over-engineering a structure that doesn't match reality.

2. **`expired_at` vs. `valid_to` in practice:** For most wiki pages, `valid_to` and `expired_at` will be the same date. Is the distinction worth the extra field? Only clearly valuable for pages covering external facts (vendor status, library support) where there is a real information-lag gap.

3. **Kuzu Windows validation:** Kuzu is listed as a supported backend by both Cognee and Graphiti, but neither explicitly tests on Windows in their CI. A quick `uv pip install kuzu` spike on this machine would confirm whether it works before we commit to it as our graph layer target.

4. **Claims granularity threshold:** Which wiki pages warrant claim-level tracking vs. page-level confidence? A rule of thumb is needed — otherwise claims arrays will be added inconsistently. Proposal: any page with 3+ distinct factual assertions that could independently be wrong.

5. **`wiki_digest.py` trigger:** Should `_digest.json` be generated on-demand (agent calls tool), on git commit (via hook), or periodically (scheduled task)? On-demand is simplest; commit hook ensures freshness; scheduled is most robust for a long-lived vault.

6. **Graphiti MCP server evaluation:** If we ever move to a Docker-based local dev environment, the Graphiti MCP server is a high-value integration — giving all MCP clients access to a persistent temporal knowledge graph over our session history. Worth scheduling a formal evaluation at that inflection point.
