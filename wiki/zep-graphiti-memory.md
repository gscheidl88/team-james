---
id: zep-graphiti-memory
type: research
title: "Zep & Graphiti — Temporal Knowledge Graphs for Agent Memory"
tags: [memory, knowledge-graph, temporal, context-engineering, rag, graphiti]
domain: research

is_project: false
project:

status: active
is_valid: true
valid_from: 2026-04-08
valid_to:
superseded_by:

confidence: high
reviewed_by:
review_date:

created: 2026-04-08
created_by: Researcher
last_modified: 2026-04-08
modified_by: Analyst
source: https://github.com/getzep/zep
ingest_session: "[[log#2026-04-08-research-zep-graphiti]]"

relates_to:
  - "[[agent-team-setup]]"
  - "[[karpathy-llm-wiki-pattern]]"
  - "[[tooling-policy]]"
  - "[[research-synthesis-memory-systems]]"
  - "[[embedded-db-comparison]]"
depends_on: []
---

## Overview

Research brief on Zep (managed memory service) and Graphiti (open-source temporal knowledge graph framework). The key finding is that our wiki frontmatter schema (is_valid, valid_from, valid_to) was independently designed but is a near-exact conceptual match to Graphiti's EntityEdge model (valid_at, invalid_at, expired_at) — validating our schema design from first principles. Zep Cloud is skipped (token-dependent); Graphiti local with Kuzu is viable but requires an LLM API for entity extraction.

# Zep & Graphiti — Temporal Knowledge Graphs for Agent Memory

## 1. Executive Summary

Graphiti is an open-source Python framework (MIT, 24.6k ⭐) for building **temporal context graphs** — the same infrastructure that powers Zep Cloud. It is the most technically sophisticated approach to agent memory currently available in the open-source ecosystem, and it mirrors our wiki's temporal validity model almost exactly — but at the graph-database level rather than the markdown level.

**Key finding:** Our wiki frontmatter (`is_valid`, `valid_from`, `valid_to`, `depends_on`, `relates_to`) was designed independently but is a near-perfect conceptual replica of Graphiti's `EntityEdge` data model (`valid_at`, `invalid_at`, `expired_at`, `episodes`). This is validation that we independently arrived at the right abstraction. The practical question is not *whether* the model fits — it does — but *whether the infrastructure cost is justified* for our current scale.

**Bottom line:**
- **Graphiti** → Adopt selectively. The `graphiti-core` library with FalkorDB (Docker, no cloud) is viable but requires LLM API calls for ingestion (graph construction via entity extraction). Not token-free.
- **Zep Cloud** → Skip. Requires API token, managed service. Conflicts with tooling policy.
- **Graphiti's conceptual model** → Already adopted (our wiki frontmatter). Refine further by adding `episodes` provenance concept.
- **Context engineering patterns** → Adopt immediately: signal density, context ordering, character budgeting.

---

## 2. What Zep & Graphiti Are

### Zep (`getzep/zep`, 4.4k ⭐)
End-to-End Context Engineering Platform. A **managed cloud service** that wraps Graphiti for production deployments. Handles sub-200ms context retrieval, SOC2/HIPAA compliance, multi-user graph management, dashboards, and SDKs (Python/TypeScript/Go). Uses `uv` for Python package management.

> **Status:** Zep Community Edition (self-hosted) is **deprecated** and moved to `legacy/`. Only Zep Cloud remains active. **All self-hosted paths now go through Graphiti directly.**

### Graphiti (`getzep/graphiti`, 24.6k ⭐)
Open-source temporal context graph engine. MIT licensed. The actual framework Zep runs on. This is the relevant artifact for us.

Installs as: `uv add graphiti-core` or `pip install graphiti-core`

Backed by an arXiv paper: [Zep: A Temporal Knowledge Graph Architecture for Agent Memory (2501.13956)](https://arxiv.org/abs/2501.13956)

---

## 3. Graphiti Technical Architecture

### The Four-Layer Data Model

| Layer | Class | What it stores |
|-------|-------|----------------|
| **Episodes** | `EpisodicNode` | Raw ingested data — conversations, JSON, text. The ground-truth provenance stream. Every derived fact traces back here. |
| **Entities** | `EntityNode` | People, tools, concepts, products. Each has a `summary` field that evolves over time as new episodes arrive. Embeddings on `name`. |
| **Facts / Relationships** | `EntityEdge` | Triplets: `(EntityNode → fact_string → EntityNode)`. The primary carrier of temporal state. |
| **Communities** | `CommunityNode` | Automatically detected clusters of related entities. Higher-level summaries. |

### The Critical Data Structure: `EntityEdge`

```python
class EntityEdge(Edge):
    name: str                          # relation type, e.g. "USES_FRAMEWORK"
    fact: str                          # natural-language statement: "Marcus uses React for frontend"
    fact_embedding: list[float] | None # semantic search vector
    episodes: list[str]                # provenance: which EpisodicNode UUIDs produced this fact
    
    # ── TEMPORAL VALIDITY ──────────────────────────────────
    valid_at:    datetime | None       # when this fact BECAME true
    invalid_at:  datetime | None       # when this fact STOPPED being true (null = still true)
    expired_at:  datetime | None       # when Graphiti DETECTED the invalidation
    reference_time: datetime | None    # timestamp from the source episode
    
    attributes:  dict[str, Any]        # custom typed attributes (ontology)
```

### Temporal Mechanics — How Invalidation Works

1. New episode arrives (conversation turn, JSON event, document)
2. LLM extracts entities and facts (structured output, Pydantic models)
3. Graph is queried: does a conflicting fact already exist?
4. If yes → existing `EntityEdge` gets `invalid_at` set to the new episode's `reference_time`; new edge created with `valid_at` = same timestamp
5. Facts are **never deleted** — only invalidated. Full temporal history preserved.
6. Query time: `WHERE e.invalid_at IS NULL` retrieves current facts; point-in-time queries use `WHERE e.valid_at <= $t AND (e.invalid_at IS NULL OR e.invalid_at > $t)`

### EpisodicNode — Provenance Anchor

```python
class EpisodicNode(Node):
    source: EpisodeType               # message | json | text
    source_description: str           # e.g. "chat session 2026-04-08"
    content: str                      # raw data as ingested
    valid_at: datetime                # when the episode occurred (set by caller)
    entity_edges: list[str]           # UUIDs of edges derived from this episode
```

`EpisodeType` supports three input modalities: `message` (chat), `json` (structured data), `text` (documents). This is how Marcus Chen's `vscode_settings.json`, `pyproject.json`, and conversations all land in the same graph.

### Hybrid Retrieval Stack

Graphiti queries combine three retrieval methods simultaneously:
1. **Semantic search** — cosine similarity on `fact_embedding` (entity edges) and `name_embedding` (entity nodes)
2. **BM25 keyword search** — full-text search on fact strings
3. **Graph traversal** — shortest path, community membership, node distance reranking

Results are re-ranked by a cross-encoder (default: OpenAI). The search recipe `COMBINED_HYBRID_SEARCH_CROSS_ENCODER` is the default production config.

### Ontology — Prescribed vs. Learned

- **Learned (default):** LLM autonomously extracts entity types and relationship names from raw data. No schema needed to start.
- **Prescribed:** Developer defines `EntityNode` and `EntityEdge` subclasses via Pydantic. These become typed graph nodes with custom attributes. Example: `class ToolPreference(EntityEdge): version: str; confidence: float`.

---

## 4. Local vs. Cloud — Infrastructure Requirements

### Can Graphiti run fully without Zep Cloud?

**Yes, completely.** Graphiti is standalone. It connects directly to a graph database you control. Zep Cloud is a separate, optional managed layer on top.

### Graph Database Options

| Backend | Deployment | Notes |
|---------|-----------|-------|
| **Neo4j** | Docker or Desktop | Default backend. Most features. Requires Java runtime. |
| **FalkorDB** | Docker (single line) | Redis-compatible wire protocol. Fastest local startup. **Recommended for us.** |
| **Kuzu** | Embedded (file-based) | No server needed. Pure Python. Limited scale. Potentially simplest. |
| **Amazon Neptune** | AWS managed | Cloud-only. Not relevant to us. |

**FalkorDB quickstart:**
```bash
docker run -p 6379:6379 -p 3000:3000 -it --rm falkordb/falkordb:latest
```

**Kuzu (fully embedded, no Docker):**
```python
from graphiti_core.driver.kuzu_driver import KuzuDriver
driver = KuzuDriver(db="<WORKSPACE_ROOT>/graphiti.kuzu")
```

### LLM Requirements

**This is the critical constraint.** Graphiti requires an LLM API for:
- Entity and fact extraction during ingestion (structured output required)
- Embedding generation for semantic search
- Cross-encoder reranking

Default: OpenAI (`OPENAI_API_KEY`). Alternatives: Anthropic, Gemini, Groq, Azure OpenAI.

> **Tooling policy implication:** Graphiti is NOT token-free. Every episode ingested makes LLM API calls. This is a fundamental architectural requirement, not an optional feature — the entity extraction is what makes the graph intelligent. Local LLMs (Ollama etc.) are community-supported but the README explicitly warns: *"Using other services may result in incorrect output schemas and ingestion failures. This is particularly problematic when using smaller models."*

### Minimal Local Setup

```bash
# 1. Start FalkorDB
docker run -p 6379:6379 -it --rm falkordb/falkordb:latest

# 2. Install
uv add "graphiti-core[falkordb]"

# 3. Set env vars
OPENAI_API_KEY=...  # or ANTHROPIC_API_KEY with [anthropic] extra

# 4. Run
uv run python my_graphiti_script.py
```

---

## 5. Connection to Our Wiki Schema

### The Parallel Discovery

Our wiki frontmatter was designed independently by looking at Karpathy's wiki pattern and adding temporal validity. Graphiti's `EntityEdge` was designed by a team building production agent memory infrastructure. **They converge on the same abstractions:**

| Our Wiki Frontmatter | Graphiti `EntityEdge` | Semantic match |
|---------------------|----------------------|----------------|
| `is_valid: true/false` | `invalid_at IS NULL` | ✅ Exact — "is this fact currently true?" |
| `valid_from: 2026-04-08` | `valid_at: datetime` | ✅ Exact — "when did this become true?" |
| `valid_to: <date or null>` | `invalid_at: datetime \| None` | ✅ Exact — "when did it stop being true?" |
| `superseded_by: [[link]]` | New edge created with `valid_at` pointing back | ⚠️ We use explicit links; Graphiti uses temporal continuity |
| `relates_to: [...]` | Graph edges (RELATES_TO relationships) | ✅ Structural match — both express relationships |
| `depends_on: [...]` | No direct equivalent | 🔴 Gap — Graphiti doesn't model prerequisite dependencies |
| `confidence: high/medium/low` | Cross-encoder rerank score (implicit) | ⚠️ Partial — Graphiti has confidence as query-time score, not stored metadata |
| `source: <url>` | `episodes: [uuid, ...]` → `EpisodicNode.content` | ⚠️ We store URL; Graphiti stores full raw content with provenance chain |
| `ingest_session: [[log#...]]` | `EpisodicNode.uuid` + `reference_time` | ✅ Concept match — both track provenance to the ingestion event |

### What We're Missing That Graphiti Has

1. **Episode provenance chain:** We record `source:` as a URL, but we have no equivalent of Graphiti's `EpisodicNode` — a first-class record of *when and how* each fact was ingested. Our `log.md` partially fills this role but doesn't link at the field level.

2. **`expired_at` vs `valid_to`:** We only have `valid_to` (when the fact stopped being true). Graphiti separately tracks `invalid_at` (when the fact stopped being true in the world) and `expired_at` (when the system detected this). This distinction matters: a fact can become false before the system knows about it.

3. **Automatic conflict resolution:** When a new wiki page supersedes an old one, we manually set `superseded_by`. Graphiti automates this: new facts trigger LLM-assisted conflict detection and automatic `invalid_at` stamping on contradicting edges.

4. **Relationship embedding:** Our `relates_to` links are untyped strings. Graphiti's edges have typed names (`USES_FRAMEWORK`, `PREFERS_TOOL`) with embedded facts — semantically searchable.

### What We Have That Graphiti Lacks

1. **`depends_on`:** Explicit prerequisite dependency tracking. Graphiti has no equivalent — it models relationships but not logical dependencies.
2. **`confidence` as stored metadata:** We can flag a page as `confidence: low` with a note. Graphiti confidence is implicit in retrieval scores.
3. **Human prose:** Our wiki pages are full markdown documents readable by Gerhard. Graphiti stores structured triples and summaries, not human-readable pages.
4. **Zero infrastructure cost:** Markdown files in Obsidian need no server, no database, no embeddings. Graphiti needs a graph DB + LLM API.

---

## 6. Context Engineering Patterns Worth Adopting

The `getzep/context-engineering-contest` repository reveals the practical discipline of context engineering. Key patterns:

### Signal Density Over Document Retrieval
The contest enforces a **2000-character context budget** with a 2-second latency limit. This forces a shift from "retrieve documents" to "retrieve facts." The metric that matters is *signal per character*, not coverage.

> **Adopt:** When our agents retrieve context from `MEMORY.md` or wiki pages, they should extract and compact the *specific facts* relevant to the query, not pass whole documents. A pre-formatted fact: `"Marcus uses uv for Python (confirmed 2026-03-15)"` is higher signal than a paragraph.

### Context Ordering Matters
From the contest docs: *"structure your context so that the highest-signal information appears in the first 2000 characters."* LLMs weight earlier context more heavily. The contest explicitly found that completeness scores (context contains the answer) often exceeded accuracy scores (agent used it correctly) — pointing to ordering as the bottleneck, not retrieval.

> **Adopt:** In agent system prompts, order memory context: (1) current-session facts, (2) recent relevant facts from MEMORY.md, (3) background wiki pages. Most critical context first.

### Context Engineering ≠ RAG
RAG: retrieve documents → stuff into context. Context Engineering: *deliberately assemble a pre-formatted context block that maximizes agent accuracy within constraints.* Key differences:
- RAG is retrieval-first; CE is constraint-first (latency, token count, relevance)
- RAG returns chunks; CE returns structured facts
- RAG is stateless; CE accounts for the agent's current task and history

> **Adopt:** Think of `MEMORY.md` retrieval as context assembly, not search. The `START-SESSION.md` bootstrap is already doing this — it's context engineering in YAML form.

### Temporal Recency Bias
Graphiti weights recent facts higher in retrieval. Older facts with `invalid_at` set are excluded by default. For our MEMORY.md append-only log, this means recency should be an explicit filter — newer entries for the same entity should shadow older ones.

---

## 7. Memory Architecture Comparison

### Zep/Graphiti Architecture
```
Raw inputs (chat, JSON, docs)
        ↓ [LLM: entity extraction, structured output]
EpisodicNodes (provenance)
        ↓ [LLM: conflict detection, temporal reasoning]
EntityNodes + EntityEdges (with valid_at / invalid_at)
        ↓ [hybrid retrieval: BM25 + semantic + graph traversal]
Context block (pre-formatted, 2000 chars, <200ms)
        ↓
Agent
```

### Our Architecture
```
Agent interactions / Gerhard's decisions
        ↓ [manual or agent-written]
MEMORY.md (append-only, timestamped entries)
wiki/*.md (structured pages, temporal frontmatter)
        ↓ [grep / BM25 search / manual lookup]
START-SESSION.md (curated bootstrap context)
        ↓
Agent
```

### Head-to-Head Comparison

| Dimension | Zep/Graphiti | Our MEMORY.md + Wiki | Winner |
|-----------|-------------|---------------------|--------|
| **Temporal tracking** | Automatic, per-fact, bi-temporal | Manual, per-page, single-window | Graphiti |
| **Conflict resolution** | Automatic (LLM-assisted) | Manual (human updates superseded_by) | Graphiti |
| **Relationship modeling** | Rich graph with typed edges | Untyped `relates_to` links | Graphiti |
| **Provenance** | Full chain (episode → edge) | URL + session log | Roughly equal |
| **Retrieval quality** | Hybrid: semantic + BM25 + graph | BM25 (planned), currently grep | Graphiti |
| **Infrastructure cost** | Graph DB + LLM API every write | Zero (markdown files) | Ours |
| **Human readability** | Machine-structured triples | Full markdown prose | Ours |
| **Dependency tracking** | None | `depends_on` field | Ours |
| **Token cost** | High (LLM on every ingestion) | Zero (no LLM needed for writes) | Ours |
| **Setup complexity** | High (Docker + API keys) | Zero | Ours |
| **Portability** | Vendor risk (graph DB format) | None (plain text files) | Ours |
| **Scale ceiling** | Millions of facts | ~Thousands of pages (practical) | Graphiti |

**Assessment:** For our current scale (one user, hundreds of memory facts, dozens of wiki pages), the infrastructure overhead of Graphiti is not justified. Our architecture wins on simplicity, cost, and portability. However, Graphiti wins decisively on *automated* temporal reasoning at scale.

---

## 8. Fit Analysis

| Zep/Graphiti Concept | Our Equivalent | Gap / Opportunity |
|---------------------|---------------|-------------------|
| `EntityEdge.valid_at` | `wiki.valid_from` | ✅ Covered — same concept |
| `EntityEdge.invalid_at` | `wiki.valid_to` | ✅ Covered — same concept |
| `EntityEdge.expired_at` | — | 🔶 Gap: we don't track "when did we discover this was wrong?" |
| `EntityEdge.fact` (NL string) | Wiki body / MEMORY.md entries | ⚠️ Ours are prose pages; Graphiti uses atomic triples |
| `EntityEdge.episodes` provenance | `wiki.ingest_session` + `wiki.source` | ⚠️ Partial — we link to session but don't chain at field level |
| `EntityNode.summary` (evolving) | Wiki page body (static until edited) | 🔶 Gap: our summaries don't auto-update; manual refresh needed |
| `EpisodicNode` (raw input archive) | `memory/MEMORY.md` append log | ✅ Conceptual match — both preserve raw history |
| Automatic conflict detection | Manual `superseded_by` | 🔴 Gap: we have no automated contradiction detection |
| Hybrid retrieval (semantic + BM25) | grep (current), BM25 (planned) | 🔶 Gap: no semantic search yet |
| Custom ontology (Pydantic types) | `_schema.md` + frontmatter fields | ✅ Same intent: defined schema for structured knowledge |
| `group_id` (graph partitioning) | Subdirectories / `domain:` field | ✅ Covered conceptually |
| Community detection (clusters) | Wiki `tags` + `relates_to` graph | ⚠️ Manual clustering vs. automatic |
| Context block assembly | `START-SESSION.md` bootstrap | ✅ Same pattern — curated context for agent |
| 2000-char signal budget | No explicit budget | 🔶 Opportunity: add context budget discipline to session bootstrap |

---

## 9. Recommendations — What to Adopt / Adapt / Skip

### ✅ Adopt Now (zero infrastructure cost)

**A. Add `expired_at` field to wiki schema**
We have `valid_to` (when fact stopped being true) but no field for "when we discovered this." Add `expired_at:` to `_schema.md`. Distinction: a tooling policy could become invalid in November but we might not discover this until January.

**B. Adopt context budget discipline**
From the context engineering contest: explicitly constrain session bootstrap context to a character/token budget. Structure `START-SESSION.md` so highest-signal facts appear first. Document the budget in `tooling-policy.md`.

**C. Atomic fact notation in MEMORY.md**
Graphiti stores facts as atomic triples: `"(Gerhard, PREFERS_TOOL, uv) [valid_at: 2026-01-15]"`. Our MEMORY.md entries are prose paragraphs. **Adopt a hybrid:** keep prose for narrative, but for preference/decision facts, add a structured summary line at the end of each entry:
```
## 2026-04-08 — Tooling decision
[narrative prose...]
> FACT: (Gerhard, USES_FOR_PYTHON, uv) | valid_from: 2026-01-15
```

**D. Provenance at the fact level**
Add `episodes: []` or `derived_from: []` to wiki pages that summarize multiple sources. This mirrors Graphiti's episode provenance chain without needing a database.

### 🔶 Adapt Later (when BM25 search is implemented)

**E. Temporal recency filter in retrieval**
When we implement BM25/semantic search over the wiki, add a `valid_at` range filter as a default. Return only `is_valid: true` facts by default; allow `include_historical: true` for point-in-time queries. This mirrors Graphiti's default retrieval behavior.

**F. Relationship indexing**
Build a lightweight index of `relates_to` and `depends_on` links (e.g., a JSON adjacency list) so agents can traverse the wiki graph without grepping every file. This is a small Graphiti-inspired graph layer on top of our markdown.

### ⚠️ Evaluate Carefully (significant cost)

**G. Graphiti with Kuzu (fully embedded)**
Kuzu is an embedded graph database (file-based, no server) that Graphiti supports. This is the lowest-cost path to actual graph-backed memory. **Prerequisite:** an LLM API for ingestion (cannot avoid). Consider for a specific high-value use case (e.g., ingesting all past Gerhard sessions into a persistent fact graph). Cost: ~$0.01-0.05 per session ingested at gpt-4o-mini rates.

**H. Graphiti MCP server**
Graphiti ships an MCP server (`mcp_server/` directory) that integrates with Claude, Cursor, etc. This would give Claude Code access to a real temporal knowledge graph. **Requires:** Docker + graph DB + LLM API. High setup cost; high potential value.

### ❌ Skip

**I. Zep Cloud**
Requires API token, SOC2/HIPAA managed service. Conflicts with tooling policy (prefer token-free). No self-hosted path. Community Edition deprecated. Skip entirely.

**J. Full Graphiti ingestion of wiki**
Ingesting our existing wiki pages through Graphiti's LLM entity extraction pipeline would cost tokens and require ongoing maintenance of a graph database. The pages are already structured with our frontmatter — we've done the hard work manually. Redundant at current scale.

---

## 10. Open Questions for Gerhard

1. **Kuzu evaluation:** Kuzu is a file-based embedded graph DB (no Docker, no server) that Graphiti can use as a backend. Worth a spike to see if `graphiti-core[kuzu]` is feasible on Windows without major friction. Would you like the Analyst to prototype this?

2. **LLM cost tolerance for ingestion:** Graphiti's core value proposition requires LLM API calls for every ingestion event. At ~$0.001-0.005 per session (gpt-4o-mini), it's cheap but not free. Is there a specific memory use case (e.g., tracking tool preferences, project decisions) where this cost is worth the automated temporal reasoning?

3. **`expired_at` field:** Should we add this to the wiki schema now? It distinguishes "when did this fact stop being true in the world" from "when did we discover that it stopped being true" — a subtle but useful distinction for research notes where information lag matters.

4. **Atomic fact notation in MEMORY.md:** The `FACT:` structured line proposal (Section 9C) would require all agents to follow a new convention when writing to MEMORY.md. Is this worth the consistency overhead? Or should MEMORY.md stay pure prose?

5. **Graphiti MCP server:** There is a fully-built MCP server for Graphiti in the repo. If we ever move to a Docker-based local dev setup, this would be a high-value integration — giving all MCP clients (Claude, Cursor) access to a persistent temporal knowledge graph. Worth flagging for future architecture review.

---

*Research conducted by Researcher Agent on 2026-04-08. Sources: getzep/graphiti README (raw), graphiti_core/edges.py, graphiti_core/nodes.py, graphiti_core/graphiti.py (actual source code), getzep/context-engineering-contest README, getzep/zep README. arXiv:2501.13956.*
