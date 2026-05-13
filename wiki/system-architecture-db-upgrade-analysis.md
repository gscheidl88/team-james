---
id: system-architecture-db-upgrade-analysis
type: analysis
title: "Architecture Analysis — Upgrading the Agent KB System with Kuzu, LanceDB & DuckDB"
tags: [architecture, sqlite, duckdb, lancedb, kuzu, networkx, rag, knowledge-graph, analysis]
domain: technical
is_project: false
status: active
is_valid: true
valid_from: "2026-04-08"
confidence: high
created: "2026-04-08"
created_by: Analyst
last_modified: "2026-04-08"
modified_by: Analyst
source: "internal"
ingest_session: "2026-04-08"
relates_to: ["[[embedded-db-comparison]]", "[[research-synthesis-memory-systems]]", "[[zep-graphiti-memory]]", "[[tooling-policy]]"]
depends_on: ["[[embedded-db-comparison]]"]
---

## Overview

Architectural analysis of upgrading Gerhard's company knowledge base system, which currently uses SQLite for everything including graph storage (via NetworkX in-memory) and Azure OpenAI embeddings. The analysis identifies three structural pain points and maps each to a targeted database upgrade: Kuzu for graph traversal (replacing SQLite + NetworkX), LanceDB for vector storage (replacing Azure embedding blobs), and DuckDB as a new analytics layer. A phased migration plan (Phase 0–3) is included, each phase independently deployable.

# Architecture Analysis — Upgrading the Agent KB System with Kuzu, LanceDB & DuckDB

## 1. Overview

The current agent knowledge base system is a pragmatic, well-composed stack. It combines Markdown files as a Git-versioned source of truth, SQLite for relational session state and operational data, FTS5/BM25 for keyword search, Azure OpenAI embeddings for semantic retrieval, and a SQLite-backed entity graph traversed at runtime via NetworkX. For the scale it was built at, it holds together well.

This analysis is not a criticism of that design. It is a targeted examination of where the architecture starts to buckle under load, and a concrete map of how three purpose-built embedded databases — **Kuzu** (native graph), **LanceDB** (vector/columnar), and **DuckDB** (analytical SQL) — address each specific weakness without destabilising what already works. SQLite stays in several critical roles; the changes are additive and surgical.

---

## 2. What the Current System Does Well

Before diagnosing problems, honesty demands acknowledging what is correct.

**SQLite for session state is exactly right.** `agent_hub.db` stores todos, sessions, locks, facts, entities, and handover records. These are small, high-write, ACID-critical workloads. SQLite is battle-tested for exactly this pattern: single-writer, local, transactional, zero-config. There is no server to manage, no network round-trip, no deployment complexity. For an agent team operating on one machine or within one process, this is the ideal fit.

**FTS5/BM25 is best-in-class for keyword search.** SQLite's FTS5 extension implements BM25 ranking natively and performs extremely well on document corpora of the size a personal KB system handles. It handles stemming, prefix matching, and phrase queries. Replacing it with a dedicated search engine would add operational complexity for no meaningful gain at this scale.

**Markdown-as-source-of-truth with Git versioning is correct architecture.** The knowledge base lives in plaintext files under version control. This means the KB is diffable, auditable, recoverable, and human-readable without any tooling. The SQLite database (`kb.db`, `.private.db`) is a derived artefact built from Markdown — not the source. This separation is architecturally sound and should not be touched.

**NetworkX is flexible and well-understood.** For small graphs, NetworkX delivers fast prototyping. The Python ecosystem knows it well, the API is ergonomic, and it supports the full range of graph algorithms needed for early KB traversal work. It served its purpose.

---

## 3. Where the Pain Points Are

### Pain Point A — Embeddings in SQLite

Azure OpenAI embeddings are stored as binary blobs in a row-store table. This works, but it creates several structural problems:

**Token dependency.** Every new or modified document requires an API call to Azure OpenAI. There is no local fallback. If the Azure endpoint is unavailable, rate-limited, or the API key rotates, the entire semantic search pipeline is blocked. For an offline-capable agent system, this is a fragile dependency.

**Brute-force ANN.** Similarity search over SQLite embeddings means fetching all embedding rows into Python, computing cosine similarity in a loop or via NumPy, and sorting. This is O(n) across the full corpus. For a few hundred documents it is acceptable. At a few thousand, query latency degrades noticeably. At tens of thousands, it becomes a bottleneck.

**Row-store is the wrong layout.** SQLite stores data row by row. A float array embedding stored as a BLOB sits alongside every other column in the row. There is no way to vectorise across embeddings at the storage layer — every similarity computation requires deserialising individual BLOBs in Python. The storage format is architecturally opposed to the access pattern.

**No indexing primitives.** SQLite has no concept of an approximate nearest neighbour (ANN) index. Implementing HNSW or IVF on top of SQLite would require writing it from scratch in Python.

### Pain Point B — Graph in SQLite + NetworkX (the biggest architectural mismatch)

This is the most structurally misaligned component in the system, and understanding why requires following the full execution path of a graph query.

The `entity_relations` table in SQLite is a flat relational table: `(source, target, relation_type)`. A structured question like "How does SF relate to SailPoint?" follows this path:

1. `SELECT * FROM entity_relations` — fetches the entire edge table into Python memory.
2. A `nx.DiGraph()` is constructed, iterating every row to call `G.add_edge(src, tgt, relation=rel)`.
3. NetworkX path-finding (`nx.shortest_path`, `nx.all_simple_paths`) is called in Python.
4. The graph object is discarded at the end of the call — nothing persists.

Every single query rebuilds the entire graph from scratch. For a KB with hundreds of entities this is fast enough to be invisible. For a KB with thousands — or when the system is handling multiple concurrent agent queries — the cost compounds.

More critically, **variable-length path queries are expensive Python loops.** Finding everything connected to an entity within 3 hops requires either implementing BFS manually or calling `nx.ego_graph`, neither of which benefits from any indexing. The graph has no persistent index; it is reconstructed from rows every time.

The entire graph must fit in RAM. If the entity and relations tables grow substantially — or if the agent system begins ingesting enterprise-scale data — this becomes a hard ceiling.

This is not a shortcoming of NetworkX. NetworkX is a correct tool for in-memory graph computation. The problem is that it is being used as a *database*, a role it was never designed to fill.

### Pain Point C — No Analytical Layer

There is currently no easy path to answer cross-KB aggregate questions:

- "How many entities of each type exist in the KB?"
- "Which entities have the highest relationship degree?"
- "What knowledge was added in the last 30 days?"
- "What is the distribution of confidence scores across all facts?"

These questions require aggregation over the full relational tables. Writing them in SQLite is possible, but the row-store layout makes column scans slow, and there is no columnar compression or vectorised execution. More practically: there is no good place to put these analytical queries in the current architecture. They do not belong in `kb.py`, they do not belong in the agent runtime, and they are not session operations. The analytical layer simply does not exist.

---

## 4. The Upgrade Map — What Replaces or Augments What

| Layer | Current | Upgraded | Change Type |
|---|---|---|---|
| Session state | SQLite `agent_hub.db` | SQLite `agent_hub.db` | ✅ Keep — perfect fit |
| BM25 search | SQLite FTS5 | SQLite FTS5 | ✅ Keep — best-in-class |
| Embeddings storage | SQLite (binary BLOBs) | LanceDB | 🔄 Replace |
| Embedding model | Azure OpenAI | Local Ollama (`nomic-embed-text`) | 🔄 Optional replace |
| ANN search | Brute-force O(n) in Python | LanceDB HNSW index | 🔄 Replace |
| Graph storage | SQLite `entity_relations` | Kuzu | 🔄 Replace |
| Graph traversal | NetworkX (in-memory, rebuilt per call) | Kuzu Cypher queries | 🔄 Replace |
| Analytics | Ad-hoc SQLite queries | DuckDB | ➕ New layer |
| Source of truth | Markdown + Git | Markdown + Git | ✅ Keep — unchanged |

---

## 5. Deep Dive: SQLite `entity_relations` → Kuzu

This is the highest-impact change in the upgrade map. The mismatch between a relational row-store and a graph traversal workload is fundamental, and Kuzu is purpose-built to resolve it.

**Current pattern — Python + SQLite + NetworkX:**

```python
import sqlite3
import networkx as nx

conn = sqlite3.connect(".kb.db")

# Step 1: fetch the entire edge table — no filtering possible yet
rows = conn.execute(
    "SELECT source, target, relation_type FROM entity_relations"
).fetchall()

# Step 2: build the graph in Python memory — O(n) construction
G = nx.DiGraph()
for src, tgt, rel in rows:
    G.add_edge(src, tgt, relation=rel)

# Step 3: traverse — stays in Python, no DB involvement
paths = nx.all_simple_paths(G, source="SF", target="SailPoint", cutoff=3)
for path in paths:
    print(path)

# Graph is discarded here — next call starts from scratch
```

**Kuzu equivalent — traversal stays in the database:**

```python
import kuzu

db = kuzu.Database("kb.kuzu")
conn = kuzu.Connection(db)

# Schema defined once at KB build time
conn.execute("CREATE NODE TABLE Entity(id STRING, type STRING, PRIMARY KEY(id))")
conn.execute("CREATE REL TABLE RELATES_TO(FROM Entity TO Entity, relation_type STRING)")

# Query: variable-length path, 1–3 hops, no Python graph construction
result = conn.execute("""
    MATCH path = (a:Entity {id: 'SF'})-[:RELATES_TO*1..3]->(b:Entity {id: 'SailPoint'})
    RETURN path, [r IN relationships(path) | r.relation_type] AS rel_types
""")
for row in result:
    print(row)
```

**Key improvements:**

- **No full graph load into RAM.** Kuzu pages nodes and edges from disk on demand. A 50,000-node graph does not require 50,000 objects in Python memory.
- **Variable-length paths are native.** The `*1..3` syntax compiles to an optimised internal traversal — not a Python loop.
- **The graph persists.** Kuzu writes to a directory on disk. There is no rebuild cost per query. The first call after startup is as fast as subsequent ones.
- **Edge types become first-class.** `integrates_with`, `depends_on`, and `owned_by` can be modelled as separate relationship tables in Kuzu, not as a `relation_type` string column. This enables type-safe traversal: `MATCH (a)-[:DEPENDS_ON]->(b)` rather than filtering a string field post-fetch.
- **Kuzu is fully embedded.** No server process, no TCP port, installs via `pip install kuzu`. The migration adds one dependency and one new directory — it does not change the deployment model.

The migration itself is straightforward: `kb.py` currently builds `entity_relations` rows during ingestion. Redirect that write path to Kuzu's `CREATE` statements instead. Both can run in parallel during a transition period.

---

## 6. Deep Dive: Azure Embeddings → LanceDB + Local Model

LanceDB stores data in the Lance columnar format, which is Arrow-native. Embeddings are stored as contiguous float arrays in column-major order — the storage layout matches the access pattern for ANN queries directly.

**HNSW index eliminates the O(n) problem.** LanceDB builds a Hierarchical Navigable Small World index over the embedding vectors. ANN queries run in O(log n) rather than O(n). The difference between scanning 10,000 embeddings and index-navigating to the 10 nearest is the difference between 200ms and 2ms at modest scale.

**Metadata filtering before ANN.** LanceDB supports pre-filter conditions before the vector search:

```python
import lancedb

db = lancedb.connect("kb.lance")
table = db.open_table("documents")

# Only search within 'system' entity type documents
results = (
    table.search(query_embedding)
    .where("entity_type = 'system'", prefilter=True)
    .limit(10)
    .to_pandas()
)
```

This is not possible with the current SQLite approach without fetching filtered rows first, then running similarity in Python.

**Local embedding model via Ollama.** `nomic-embed-text` produces 768-dimensional embeddings via Ollama and runs entirely locally. No Azure token, no API rate limit, no latency from an HTTP round-trip. For a personal agent system, offline capability is a significant operational improvement.

```python
import ollama
import numpy as np

def embed(text: str) -> list[float]:
    response = ollama.embed(model="nomic-embed-text", input=text)
    return response["embeddings"][0]
```

**Hybrid search: LanceDB + FTS5.** The FTS5 layer stays intact. The recommended pattern is Reciprocal Rank Fusion (RRF): run the BM25 query against SQLite FTS5 and the ANN query against LanceDB independently, then merge ranked lists by `1 / (rank + k)` weighting. This consistently outperforms either retrieval method alone on mixed keyword/semantic queries.

**Migration path.** Run `kb.py` once with the Ollama embed function instead of the Azure call. Write output to LanceDB instead of SQLite BLOBs. The Markdown source of truth does not change. A full re-embed of a typical personal KB completes in minutes locally.

---

## 7. Deep Dive: DuckDB as Analytics Layer

DuckDB slots into the architecture as a read-only analytical lens over existing data — no migration required for Phase 1. Its most useful feature in this context is direct attachment to SQLite files:

```python
import duckdb

con = duckdb.connect()
con.execute("ATTACH 'agent_hub.db' AS hub (TYPE sqlite)")
con.execute("ATTACH '.kb.db' AS kb (TYPE sqlite)")
```

From here, full analytical SQL runs over existing SQLite tables with columnar execution and vectorised aggregation:

```sql
-- Entity type distribution in the KB
SELECT entity_type, COUNT(*) AS count
FROM kb.entities
GROUP BY entity_type
ORDER BY count DESC;

-- Most connected entities by outgoing relationship degree
SELECT source, COUNT(*) AS degree
FROM kb.entity_relations
GROUP BY source
ORDER BY degree DESC
LIMIT 10;

-- KB growth over time — new entities per week
SELECT DATE_TRUNC('week', created_at) AS week, COUNT(*) AS new_entities
FROM kb.entities
GROUP BY week
ORDER BY week;

-- Cross-system: which sessions referenced the highest-degree entities?
SELECT s.session_id, e.id AS entity, er.degree
FROM hub.sessions s
JOIN (
    SELECT source AS id, COUNT(*) AS degree
    FROM kb.entity_relations
    GROUP BY source
) er ON s.context LIKE '%' || er.id || '%'
ORDER BY er.degree DESC;
```

DuckDB can also query Parquet files, JSON, and CSV directly without import:

```sql
-- Query knowledge base JSON exports without loading them
SELECT id, confidence, entity_type
FROM read_json_auto('knowledge/**/*.json')
WHERE confidence > 0.8
ORDER BY confidence DESC;
```

The value here is not replacing SQLite — it is giving Gerhard a proper analytical interface over data that was previously only accessible via bespoke Python scripts or hand-crafted SQLite aggregations.

---

## 8. Migration Strategy

Phases are independent and reversible. Each can be deployed without affecting the others.

**Phase 0 — Document (now).** Keep all systems as-is. This document is the artefact of Phase 0. Baseline the current architecture so regressions are detectable.

**Phase 1 — Add DuckDB (low risk, immediate value).** Install `duckdb` via `uv add duckdb`. Write a small analytics module that attaches to existing SQLite files and exposes canned queries. Zero changes to `kb.py`, zero changes to agent runtime. Fully reversible: remove the module, nothing else changes.

**Phase 2 — Migrate embeddings to LanceDB + Ollama (medium risk).** Add `lancedb` and `ollama` Python packages. Modify `kb.py`'s embedding write path to target LanceDB. Add HNSW index build step after ingestion. Update retrieval functions to query LanceDB instead of SQLite BLOBs. Run a full re-embed. Keep FTS5 unchanged. Implement RRF hybrid fusion. Risk: the re-embed must complete cleanly; run against a copy of the KB first.

**Phase 3 — Migrate entity graph to Kuzu (higher risk, highest payoff).** Add `kuzu` package. Modify `kb.py`'s relation write path to issue Kuzu `CREATE` statements in addition to (then instead of) SQLite inserts. Update graph query functions to use Cypher. Retire the NetworkX construction block. Retire the `entity_relations` SQLite table after validation. Risk: Cypher queries must be validated to return equivalent results to the NetworkX paths they replace. Run both systems in parallel for one ingestion cycle before cutover.

---

## 9. What Stays Exactly the Same

This is worth stating explicitly to prevent scope creep and unnecessary risk:

- **Markdown source of truth** — unchanged. Every document still lives in `knowledge/` and `memory/` as Markdown. `kb.py` still reads from there. Git still versions it.
- **Git versioning** — unchanged. The KB is still auditable, diffable, and recoverable.
- **SQLite for session/OLTP** — `agent_hub.db` stays. Todos, sessions, locks, facts, handovers — all remain in SQLite. This is the right tool for this workload and nothing in the upgrade touches it.
- **FTS5/BM25** — unchanged. The keyword search layer in `.kb.db` stays as-is. It participates in hybrid search as the BM25 half of RRF.
- **`kb.py` as the ingestion pipeline** — the file remains the central build script. The upgrade changes *where it writes* embeddings and relations, not the ingestion logic itself.

The total surface area of change across all three phases is: one new database directory (Kuzu), one new Lance directory (LanceDB), one optional Ollama model pull, and roughly 200–300 lines of modified Python across `kb.py` and retrieval utilities. The Markdown files, the Git history, the SQLite session database, and the FTS5 index are untouched.

---

## Summary

| Component | Current Weakness | Upgrade | Complexity |
|---|---|---|---|
| Embedding storage | BLOBs in row-store, brute-force ANN | LanceDB + HNSW | Low–Medium |
| Graph traversal | Full in-memory rebuild per call, no path indexing | Kuzu + Cypher | Medium |
| Analytics | No analytical layer exists | DuckDB (read-only attachment) | Low |
| Session state | None — correct fit | No change | — |
| BM25 search | None — correct fit | No change | — |

The architecture after these upgrades is still a fully embedded, single-machine, no-server system. It adds three new embedded databases to replace three components that were using the wrong tool for their workload. The source of truth, the operational database, and the search index are unchanged. The risk is manageable when phased correctly, and each phase delivers independent value.
