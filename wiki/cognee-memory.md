---
id: cognee-memory
type: research
title: "Cognee — Knowledge Graph Memory for AI Agents"
tags: [memory, knowledge-graph, python, research]
domain: agent-memory
is_project: false
status: active
is_valid: true
valid_from: "2026-04-08"
confidence: high
created: "2026-04-08"
created_by: Researcher
last_modified: "2026-04-08"
modified_by: Analyst
source: "https://github.com/topoteretes/cognee"
ingest_session: "2026-04-08"
relates_to: ["[[zep-graphiti-memory]]", "[[openclaw-ecosystem]]", "[[agent-team-setup]]"]
depends_on: ["[[embedded-db-comparison]]"]
---

## Overview

Cognee is a Python knowledge engine using a three-step pipeline (add → cognify → search) with local-first backends (Kuzu + LanceDB + SQLite) and optional Graphiti integration for temporal reasoning. It requires an LLM for the cognify step and is therefore not a zero-dependency adopt for our team. The value here lies in what we steal: Kuzu as an embedded graph store, LanceDB as an embedded vector store, and the SearchType discriminator pattern for multi-mode retrieval — all adoptable as standalone choices without pulling in the full cognee package.

# Cognee — Knowledge Graph Memory for AI Agents

## Executive Summary

- **What it is**: Open-source Python knowledge engine that converts raw documents into a hybrid vector + graph knowledge store, queryable by AI agents. Core pipeline: `add()` → `cognify()` → `search()`.
- **Local-first viable** with the right config: defaults to Kuzu (embedded graph, no server) + LanceDB (local vector) + SQLite (relational). Runs 100% offline when paired with Ollama for LLM/embeddings.
- **LLM required for ingestion**: The `cognify()` step uses an LLM to extract entities and relationships from documents—no token-free ingestion path exists. This is a hard dependency.
- **Cognee recently integrated Graphiti** for temporal awareness, but temporal tracking is an add-on, not native. Graphiti's `valid_from/valid_to` model is still architecturally stronger for our wiki frontmatter pattern.
- **Key steal**: The `add → cognify → search` pipeline design and the pluggable database adapter pattern (swap graph/vector/relational backends via env vars) are excellent patterns to emulate.

---

## Core Architecture & How It Works

### The Three-Step Pipeline

Cognee exposes a deceptively simple public API:

```python
import cognee
import asyncio

async def main():
    await cognee.add("Any text, file path, or URL")   # Ingest
    await cognee.cognify()                              # Process → graph + vectors
    results = await cognee.search("What does X do?")  # Hybrid retrieval
```

Under the hood, each step is a full pipeline:

1. **`add()`** — Ingests content into a staging dataset. Supports raw text, PDFs, URLs, images, audio, Notion, Slack, and 30+ connectors. Content is stored in the relational DB (SQLite by default).

2. **`cognify()`** — The heavy-lift step. Calls an LLM to:
   - Chunk documents
   - Extract named entities (people, concepts, places, events)
   - Infer typed relationships between entities
   - Store entities/edges in the graph DB (Kuzu by default)
   - Generate embeddings and store in vector DB (LanceDB by default)
   This step is LLM-bound and cannot run without a model configured.

3. **`search(type, query)`** — Hybrid retrieval combining:
   - Vector similarity (semantic search)
   - Graph traversal (relationship hops, entity lookups)
   - Structured SQL (metadata filters)
   The `SearchType` enum selects the retrieval strategy.

### Module Structure

```
cognee/
├── api/v1/            # Public surface: add, cognify, search, delete, config
├── infrastructure/
│   ├── databases/
│   │   ├── graph/     # Adapters: Kuzu (local), Neo4j, Neptune
│   │   ├── vector/    # Adapters: LanceDB (local), ChromaDB, pgvector
│   │   ├── relational/# SQLite (default), PostgreSQL
│   │   └── hybrid/    # Combined graph+vector queries
│   ├── llm/           # LLM adapters (OpenAI, Ollama, Anthropic, Gemini…)
│   └── loaders/       # Document loaders
├── modules/
│   ├── cognify/       # Entity extraction pipeline
│   ├── graph/         # Graph operations
│   ├── retrieval/     # Retrieval strategies
│   ├── ontology/      # Schema/ontology grounding
│   ├── pipelines/     # Custom pipeline runner
│   └── observability/ # OTEL tracing, Langfuse
└── tasks/             # Atomic pipeline tasks (composable)
```

### Database Backends

| Layer    | Default (local)   | Cloud/Remote options              |
|----------|-------------------|-----------------------------------|
| Graph    | **Kuzu** (embedded file) | Neo4j, AWS Neptune, FalkorDB |
| Vector   | **LanceDB** (local dir)  | ChromaDB, pgvector, Qdrant   |
| Relational | **SQLite** (file)      | PostgreSQL                   |

All backends are swapped via environment variables — no code changes needed.

### Ontology & Knowledge Grounding

Cognee supports user-defined ontologies: you can supply a schema that guides entity extraction, ensuring LLM-extracted concepts align with your domain vocabulary. This is relevant for our agent team where we want consistent entity types across sessions.

---

## Local-First Viability Assessment

### ✅ Fully local path exists

```env
# .env — 100% local, zero cloud
LLM_PROVIDER=ollama
LLM_MODEL=ollama/mistral
LLM_ENDPOINT=http://localhost:11434

EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=ollama/nomic-embed-text
EMBEDDING_ENDPOINT=http://localhost:11434

GRAPH_DATABASE_PROVIDER=kuzu
VECTOR_DB_PROVIDER=lancedb
DB_PROVIDER=sqlite
```

Install with: `uv pip install cognee[ollama]`

### ⚠️ Caveats

| Constraint | Detail |
|-----------|--------|
| **Ollama required** | `cognify()` always calls an LLM. No token-free path. |
| **Async-native** | All core functions are `async`. Needs `asyncio.run()` wrapper in scripts. |
| **First-run migrations** | Alembic runs SQLite migrations on startup—need write access to `.cognee_system/`. |
| **Heavy cold start** | `cognify()` on a large corpus is slow even with a local LLM—entity extraction is LLM call per chunk. |
| **Storage paths** | Defaults to `~/.cognee/` for logs, `.data_storage/` and `.cognee_system/` relative to CWD. Configurable via env vars. |

### uv compatibility

Cognee explicitly supports `uv pip install cognee`. Provider extras: `cognee[ollama]`, `cognee[gemini]`, `cognee[anthropic]`. Clean fit with our stack.

---

## Comparison Table: Cognee vs Graphiti

| Dimension | **Cognee** | **Graphiti (Zep)** |
|-----------|-----------|-------------------|
| **Primary focus** | Broad-corpus knowledge engine | Temporal conversation memory |
| **Temporal support** | Added via Graphiti integration (plugin) | Native — every edge has `valid_from`/`valid_to`/`invalid_at` |
| **Fact invalidation** | Not native; no `is_valid` concept in core | Core concept — facts never deleted, only invalidated |
| **Ingestion model** | Batch pipeline (`cognify()`) | Streaming episodes (add → immediate graph update) |
| **LLM dependency** | Required for `cognify()` (entity extraction) | Required for episode processing |
| **Local-first** | ✅ via Ollama + Kuzu + LanceDB | ✅ via Ollama + Kuzu/FalkorDB |
| **Graph backend** | Kuzu (default local), Neo4j | Neo4j, FalkorDB, Kuzu |
| **Vector backend** | LanceDB (default local), ChromaDB, pgvector | Integrated with graph (no separate vector store) |
| **Python API** | `add / cognify / search` (async) | `add_episode / search` (async) |
| **Multimodal** | ✅ PDFs, images, audio, 30+ connectors | ✗ Text/JSON focused |
| **Custom pipelines** | ✅ `run_custom_pipeline()` | ✗ Fixed pipeline |
| **Our wiki frontmatter** | Requires manual integration | Directly mirrors `EntityEdge` temporal model |
| **Benchmarks** | Wins on multi-hop semantic QA | Wins on temporal/historical queries |
| **Maintenance** | Active (getzep integration announced 2025) | Active (getzep team) |

**Key insight**: Cognee recently integrated Graphiti to gain temporal capabilities. The two projects are converging. For *our* use case (static wiki + session notes, not real-time chat history), Cognee's document-ingestion pipeline is actually closer to what we need than Graphiti's episode-streaming model.

---

## Patterns & APIs to Adopt

### 1. The `add → process → search` Pipeline Pattern

Cognee's clean separation of ingestion (add), processing (cognify), and retrieval (search) is worth emulating in our own tooling. Our wiki ingest flow could follow:

```
add(wiki_page.md) → extract_entities() → index_vector() → search()
```

### 2. Pluggable Backend Adapters via Env Vars

Cognee's factory pattern (`get_graph_engine()`, `create_vector_engine()`) selects backends at runtime from env vars. We should apply the same to our tools: configure storage backends via `.env` rather than hardcoded paths.

### 3. Kuzu as the Local Graph Database

Kuzu is an **embedded** graph DB (like SQLite for graphs). No server process, stores to a local directory, fast Cypher-like queries. This is the best local graph option we've seen. If we ever want graph-backed memory (beyond the flat MEMORY.md), Kuzu is the implementation path.

```python
# Example: Kuzu is embedded - just point to a directory
from cognee.infrastructure.databases.graph.kuzu.adapter import KuzuAdapter
db = KuzuAdapter(db_path="./.cognee_graph")
```

### 4. LanceDB as the Local Vector Store

LanceDB is another embedded option (no server). Stores to local directory, supports hybrid search. Already used by Cognee as the default vector backend. Pair with `nomic-embed-text` via Ollama for a fully local embedding pipeline.

### 5. `SearchType` Enum for Multi-Mode Retrieval

```python
from cognee import SearchType, search

# Different retrieval modes:
await search(SearchType.GRAPH_COMPLETION, "What is X related to?")
await search(SearchType.CHUNKS, "Find passages about Y")
await search(SearchType.SUMMARIES, "Summary of Z")
```

This pattern — a single `search()` with a type discriminator — is cleaner than having multiple functions. Consider adopting for our wiki query tool.

### 6. Custom Pipeline Composition

```python
from cognee.modules.pipelines import run_tasks

pipeline = run_tasks([
    chunk_documents,
    extract_entities,
    add_to_graph,
    index_vectors,
])
```

Composable, async-native task pipeline. Similar to our `skills/` layer concept but for data processing.

### 7. Pydantic-settings Config Pattern

```python
from pydantic_settings import BaseSettings

class BaseConfig(BaseSettings):
    data_root_directory: str = get_absolute_path(".data_storage")
    model_config = SettingsConfigDict(env_file=".env", extra="allow")
```

Cognee uses `pydantic-settings` throughout for config loading from `.env` with defaults. Clean, type-safe, already our pattern — validates our approach.

---

## What to Skip

| Feature | Reason to skip |
|---------|---------------|
| **Cognee Cloud** | Cloud SaaS — conflicts with local-first policy |
| **Full `cognee` as a dependency** | 50+ transitive deps, heavyweight for our use case |
| **`cognify()` for wiki pages** | LLM call per page chunk is expensive; our wiki is structured Markdown, not unstructured docs |
| **OTEL / Langfuse observability** | Overkill for a personal team; adds env var complexity |
| **User/tenant isolation** (`modules/users/`) | Multi-tenant feature — irrelevant for single-user setup |
| **Distributed deploy** (Modal, Railway, Fly.io) | We're local-first |
| **cognee-openclaw plugin** | OpenClaw is Node.js/WSL2 — already ruled out |
| **Alembic migrations** | Only needed if using the full cognee stack |

---

## Recommended Next Steps

### Immediate (low effort, high value)
1. **File a note** in `memory/MEMORY.md` that Kuzu + LanceDB are our go-to local graph/vector pair if we need those layers.
2. **Extract the SearchType pattern** — create a `search_type` discriminator in our wiki query tool (when built).

### Medium-term (if we need graph memory)
3. **Prototype Kuzu standalone** — `uv pip install kuzu` and test graph queries on a subset of our wiki pages. No need to pull in full cognee.
4. **Evaluate Ollama + nomic-embed-text** — test embedding our wiki pages locally for semantic search. LanceDB as the store.

### Conditional (only if ingestion automation is wanted)
5. **Pilot `cognee[ollama]`** — run `add()` + `cognify()` on a handful of wiki pages with local Ollama (requires `mistral` or similar running). Evaluate quality of extracted entities vs. our hand-crafted frontmatter.
6. **Map cognee's entity types to our wiki schema** — `relates_to`, `domain`, `tags` in our frontmatter already encode relationships. A cognee ontology file could mirror this.

### Decision gate
> **Do NOT adopt cognee as a full dependency** unless we decide to automate ingestion of unstructured sources (PDFs, meeting notes, web pages). For structured Markdown wiki pages with rich frontmatter, our current approach (hand-authored + frontmatter claims) produces higher-quality knowledge than LLM-extracted entities.

---

## References

- GitHub: https://github.com/topoteretes/cognee
- Docs: https://docs.cognee.ai
- Cognee + Graphiti integration blog: https://www.cognee.ai/blog/deep-dives/cognee-graphiti-integrating-temporal-aware-graphs
- Benchmarks vs Mem0/Graphiti: https://www.cognee.ai/blog/deep-dives/ai-memory-evals-0825
- Research paper (2025): https://arxiv.org/abs/2505.24478
- Vectorize.io comparison: https://vectorize.io/articles/zep-vs-cognee
