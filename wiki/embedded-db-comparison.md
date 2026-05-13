---
id: embedded-db-comparison
type: analysis
title: "Embedded Databases Compared — SQLite vs DuckDB vs LanceDB vs Kuzu"
tags: [database, sqlite, duckdb, lancedb, kuzu, embedded, technical]
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
relates_to: ["[[research-synthesis-memory-systems]]", "[[cognee-memory]]", "[[zep-graphiti-memory]]", "[[tooling-policy]]", "[[system-architecture-db-upgrade-analysis]]"]
depends_on: []
---

## Overview

A deep technical comparison of four embedded databases: SQLite (row-store OLTP), DuckDB (columnar OLAP), LanceDB (vector/ANN), and Kuzu (property graph). Each solves a fundamentally different problem and they are orthogonal — not competing alternatives. This page is the reference for deciding which database layer to use for which task.

# Embedded Databases Compared — SQLite vs DuckDB vs LanceDB vs Kuzu

## 1. Overview

This page provides a deep technical comparison of four embedded databases that are each genuinely different from one another: SQLite, DuckDB, LanceDB, and Kuzu. They were chosen not because they compete for the same use case, but because they represent four fundamentally different data models — row-relational, columnar-analytical, vector, and property graph — that are all relevant to AI-assisted knowledge systems. Understanding what each one *actually is* at the engine level will prevent misuse and inform sound architecture decisions. No installation recommendations are made here; this is purely a conceptual reference.

---

## 2. The Fundamental Distinction — Four Different Data Models

This is the most important section. Each database has a different answer to the question: *what is the unit of storage, and what is the primary operation?*

### SQLite — Row-Oriented Relational (OLTP)

SQLite thinks in **rows**. A table is a sequence of rows, each row stored together on a B-Tree page. When you read a row, you get every column — even the ones you didn't ask for.

```
Row 1: [id='agent-team-setup', title='...', body='...', domain='technical', confidence=0.9]
Row 2: [id='cognee-memory',     title='...', body='...', domain='ai',        confidence=0.75]
```

This is optimal when your access pattern is **row-level**: "give me everything about page X." It is poor when your access pattern is **column-level**: "give me the average confidence of all pages in the technical domain." To do that, SQLite reads every row in full — body, title, everything — just to extract two fields.

SQLite is built for **OLTP** (Online Transaction Processing): many small reads and writes, high concurrency on distinct rows, full ACID semantics, reliable durability. It is the most deployed database engine in the world for good reason — it does its job excellently.

**Core operation:** Point lookup, row insert/update/delete.

---

### DuckDB — Column-Oriented Relational (OLAP)

DuckDB thinks in **columns**. The same table is stored as separate column chunks. When you compute `AVG(confidence)`, DuckDB reads only the `confidence` and `domain` column chunks from disk — it never touches `title` or `body`.

```
Column: id         → ['agent-team-setup', 'cognee-memory', ...]
Column: domain     → ['technical', 'ai', ...]
Column: confidence → [0.9, 0.75, ...]
Column: body       → ['...', '...', ...]   ← not read for AVG(confidence)
```

This is the PAX (Partition Attributes Across) storage model. DuckDB also uses a **vectorized execution engine**: instead of processing one row at a time, it processes a chunk of 1024+ values at once using SIMD instructions. The result is dramatic throughput on analytical queries over large tables.

DuckDB is built for **OLAP** (Online Analytical Processing): aggregations, window functions, GROUP BY, joins over millions of rows. It can also query Parquet, CSV, and JSON files *directly* — no import step needed.

**Core operation:** Column-scan aggregation, analytical joins, batch read.

---

### LanceDB — Vector Database (ANN Search)

LanceDB thinks in **vectors**. Its primary storage unit is a high-dimensional float array — an **embedding** — plus associated metadata. An embedding is a numeric representation of meaning: a sentence like "graph memory system" gets encoded by a model (e.g. `text-embedding-3-small`) into a vector like `[0.021, -0.134, 0.087, ..., 0.003]` with 1536 dimensions.

The core operation is **Approximate Nearest Neighbour (ANN) search**: given a query vector, find the `k` stored vectors that are most similar (by cosine or L2 distance). "Most similar" is a proxy for "most semantically related."

LanceDB uses **HNSW** (Hierarchical Navigable Small World) or **IVF** (Inverted File) indexes to do this in sub-linear time. HNSW builds a layered graph where each node connects to its nearest neighbours at multiple granularity levels. Search starts at the top (coarse) layer and descends — it is approximate (may miss the true nearest neighbour) but extremely fast at scale.

Data is stored in columnar **Lance format**, built on Apache Arrow — which means metadata columns can be efficiently filtered alongside vector search (hybrid search).

**Core operation:** Approximate vector similarity search (semantic lookup).

---

### Kuzu — Embedded Property Graph Database

Kuzu thinks in **graphs**. Data is modelled as **nodes** (entities) and **edges** (relationships), each carrying typed properties. A wiki page is a node; a `RELATES_TO` link between two pages is a directed edge.

```
(Page {id: 'synthesis'}) -[:RELATES_TO]-> (Page {id: 'agent-team-setup'})
(Page {id: 'synthesis'}) -[:DEPENDS_ON]->  (Page {id: 'cognee-memory'})
```

The core operation is **graph traversal**: follow edges from a starting node, expanding relationships to arbitrary depth. This is expressed in **Cypher** (or Kuzu's own variant), a declarative pattern-matching query language.

Graph traversal is what makes Kuzu different from everything else here. No SQL join can express "give me all pages that `synthesis` depends on, and all pages those pages relate to, and their tags" as naturally or as efficiently as a multi-hop Cypher query. Relational joins on adjacency tables degrade badly at depth ≥ 3; Kuzu's native graph storage keeps this fast.

**Core operation:** Pattern matching and multi-hop traversal over node-edge graphs.

---

## 3. Storage Format & Architecture

| Database | On-Disk Layout | Index Type | Journal/WAL |
|----------|---------------|------------|-------------|
| SQLite   | Single `.db` file | B-Tree per table/index | WAL (Write-Ahead Log) or rollback journal |
| DuckDB   | Single `.duckdb` file | Zonemap + ART (Adaptive Radix Tree) | Checkpointing with WAL |
| LanceDB  | Directory of `.lance` fragment files | HNSW or IVF (separate index files) | Manifest-based versioning (immutable fragments) |
| Kuzu     | Directory of binary files per node/edge table | CSR (Compressed Sparse Row) for edges | Shadow paging with WAL |

**SQLite**: One file, all pages 4KB by default, each page is either a B-Tree interior node, a B-Tree leaf, or overflow. The WAL journal enables concurrent readers while one writer proceeds. The entire database — schema, data, indexes — lives in that single file. Extremely portable.

**DuckDB**: One file, internally structured as columnar blocks. Zonemaps (min/max per block) enable block-skipping — if you `WHERE confidence > 0.8`, DuckDB skips entire column blocks where `max < 0.8` without reading them. Parquet files on disk can be queried with `SELECT * FROM 'wiki/*.parquet'` using the same engine with no schema declaration.

**LanceDB**: A directory, not a file. Each "fragment" is an immutable Arrow IPC file. New writes append new fragments; deletes write a deletion bitmap. Versions are tracked via a manifest. The HNSW index is a separate file structure built on demand (`table.create_index()`). This immutable-append model makes LanceDB naturally suited to data versioning and avoids locking issues.

**Kuzu**: A directory containing separate binary files per node table and edge table. Edges are stored in **CSR format** (Compressed Sparse Row) — a graph-native layout that makes forward-traversal (follow outgoing edges from node X) extremely cache-efficient. The buffer pool manager handles page eviction for large graphs that don't fit in memory.

---

## 4. Query Model

### SQLite — SQL, Row Lookup

```sql
-- Point lookup: reads one B-Tree path
SELECT * FROM pages WHERE id = 'agent-team-setup';

-- Aggregation: full table scan (reads every row entirely)
SELECT domain, COUNT(*) FROM pages GROUP BY domain;
```

Standard ANSI SQL. Mature, portable, well-understood.

---

### DuckDB — SQL, Column-Scan + Direct File Query

```sql
-- Only reads 'domain' and 'confidence_score' columns from disk
SELECT domain, AVG(confidence_score) FROM pages GROUP BY domain;

-- Query Parquet directly — no table creation needed
SELECT title, confidence_score
FROM read_parquet('<WORKSPACE_ROOT>/exports/wiki_dump.parquet')
WHERE domain = 'technical';

-- Query a folder of JSON files
SELECT * FROM read_json_auto('<WORKSPACE_ROOT>/memory/*.json');
```

DuckDB supports the full SQL standard including window functions, CTEs, LATERAL joins, and UNNEST for arrays.

---

### LanceDB — Python API, Vector Search

```python
import lancedb
import numpy as np

db = lancedb.connect("./lancedb_store")
table = db.open_table("wiki_embeddings")

# query_embedding: a 1536-dim float array from your embedding model
query_embedding = embed_text("graph memory system")  # → np.array([...])

results = (
    table.search(query_embedding)
         .limit(5)
         .where("domain = 'technical'")   # metadata pre-filter
         .to_pandas()
)
```

The `.search()` call triggers an HNSW traversal: starting from entry-point nodes at the top graph layer, the algorithm greedily navigates toward the query vector, descending layers until it reaches the bottom. It returns the `k` closest vectors *approximately* — there is a configurable `ef` parameter trading recall accuracy against speed.

Hybrid search (combining vector similarity with scalar filters) is natively supported.

---

### Kuzu — Cypher, Graph Traversal

```cypher
-- All pages that 'synthesis' relates to
MATCH (a:Page)-[:RELATES_TO]->(b:Page)
WHERE a.id = 'synthesis'
RETURN b.id, b.title;

-- Two-hop: pages that synthesis depends on, and what those pages relate to
MATCH (a:Page)-[:DEPENDS_ON]->(b:Page)-[:RELATES_TO]->(c:Page)
WHERE a.id = 'synthesis'
RETURN a.id, b.id, c.id;

-- Variable-length path: all ancestors of 'synthesis' up to depth 5
MATCH (a:Page)-[:DEPENDS_ON*1..5]->(b:Page)
WHERE a.id = 'synthesis'
RETURN b.id;
```

Cypher patterns are declarative: you describe the *shape* of the graph you want to find, not the traversal procedure. Kuzu compiles these to physical plans over its CSR-backed edge tables.

---

## 5. Concurrency & Transactions

| Database | ACID | Multi-Reader | Multi-Writer | Isolation Level |
|----------|------|-------------|-------------|----------------|
| SQLite   | Full | Yes (WAL mode) | No (serialised) | Serializable |
| DuckDB   | Full | Yes | No (one writer at a time) | Snapshot isolation |
| LanceDB  | Partial (fragment-level) | Yes | Append-only concurrent | No cross-fragment transactions |
| Kuzu     | Full | Yes | No (single writer) | Serializable |

**SQLite** in WAL mode allows multiple concurrent readers while a single writer proceeds without blocking reads. Writes are serialised. For most single-process workloads this is invisible.

**DuckDB** offers snapshot isolation: each transaction sees a consistent snapshot of the database at the start of the transaction. Only one writer at a time; not designed for high-concurrency write workloads.

**LanceDB** uses an optimistic concurrency model on fragment manifests. Concurrent appends to different fragments can succeed; conflicting manifest updates (e.g. two concurrent index rebuilds) are detected and one is retried. There are no multi-table transactions. It is not a general-purpose ACID database.

**Kuzu** provides full ACID with serializable isolation, important when building graph structures where consistency between node and edge insertions matters. Like the others, it supports one writer at a time.

---

## 6. Python Integration

```python
# ── SQLite ──────────────────────────────────────────────────────────────────
import sqlite3

conn = sqlite3.connect("wiki.db")
cur = conn.cursor()
cur.execute("SELECT id, title FROM pages WHERE domain = 'technical'")
rows = cur.fetchall()
conn.close()

# ── DuckDB ───────────────────────────────────────────────────────────────────
import duckdb

con = duckdb.connect("wiki.duckdb")
df = con.execute(
    "SELECT domain, AVG(confidence_score) AS avg_conf FROM pages GROUP BY domain"
).df()
con.close()

# DuckDB can also run against Parquet with no persistent DB:
df2 = duckdb.sql("SELECT * FROM 'exports/wiki_dump.parquet' WHERE domain='ai'").df()

# ── LanceDB ───────────────────────────────────────────────────────────────────
import lancedb

db = lancedb.connect("./lancedb_store")
table = db.open_table("wiki_embeddings")
results = table.search([0.021, -0.134, 0.087, ...]).limit(5).to_pandas()

# ── Kuzu ─────────────────────────────────────────────────────────────────────
import kuzu

db = kuzu.Database("./kuzu_store")
conn = kuzu.Connection(db)
result = conn.execute(
    "MATCH (a:Page)-[:RELATES_TO]->(b:Page) WHERE a.id = $id RETURN b.id",
    parameters={"id": "synthesis"}
)
while result.has_next():
    print(result.get_next())
```

All four are available via `pip` / `uv add` with no external server process. They run in-process.

---

## 7. Honest Weaknesses

**SQLite**
- Column-scan analytics are slow on large tables — it reads every column even when only one is needed.
- No native support for arrays, vectors, or graph traversal.
- The single-writer constraint becomes a bottleneck in high-write-concurrency scenarios.
- Full-text search is an add-on (FTS5 extension), not a first-class citizen.

**DuckDB**
- Not designed for frequent small writes or OLTP row-level updates — it performs poorly as a session state store or event log with many tiny inserts.
- Only one writer at a time; not suitable for concurrent write workloads.
- No native vector index; embedding search requires extensions or external tooling.
- In-process only — there is no built-in server mode (though `duckdb-server` wrappers exist).

**LanceDB**
- Not a general-purpose relational database. SQL joins across tables are limited.
- No ACID transactions spanning multiple operations.
- Index build time for HNSW on large datasets can be significant.
- The Python API is the primary interface; SQL support is partial and secondary.
- ANN search is approximate — results are not guaranteed to be the true nearest neighbours.

**Kuzu**
- No column-scan analytics; aggregate queries over millions of nodes are slow compared to DuckDB.
- No native vector search.
- Cypher is less universally known than SQL; steeper initial learning curve.
- Single writer only; not suited to high-throughput concurrent writes.
- Relatively young project — some edge cases in production workloads are still being ironed out.

---

## 8. When Each Shines — Decision Triggers

**Use SQLite when:**
- You need reliable row-level CRUD with ACID transactions.
- The access pattern is mostly point lookups: "get this specific record by ID."
- You want zero-infrastructure persistence for application state, user sessions, or configuration.
- The dataset is small-to-medium and query patterns are mixed reads/writes.
- Portability (single-file database) is important.

**Use DuckDB when:**
- Your queries are analytical: GROUP BY, window functions, aggregations over many rows.
- You want to query Parquet, CSV, or JSON files without importing them.
- You're building a local analytics pipeline or data exploration tool.
- You need SQL expressiveness on columnar data — CTEs, lateral joins, unnest.
- Read performance on large tables matters more than write throughput.

**Use LanceDB when:**
- Your core operation is semantic similarity search: "find the most relevant documents to this query."
- You are storing and searching embeddings produced by an ML model.
- You need hybrid search: combine vector similarity with metadata filters.
- You are building RAG (Retrieval-Augmented Generation) pipelines, semantic memory, or recommendation systems.
- Approximate results are acceptable in exchange for speed at scale.

**Use Kuzu when:**
- Your data is fundamentally relational *in the graph sense*: entities connected by named, typed relationships.
- You need multi-hop traversal: "find all things connected to X, transitively."
- Relationship structure is a first-class concern, not a derived view.
- You are modelling knowledge graphs, dependency trees, social graphs, or citation networks.
- You want Cypher as your query language — a powerful, expressive graph DSL.

---

## 9. Can They Be Combined?

Yes — and this is the key architectural insight. These four databases are **not alternatives**; they are **orthogonal tools** solving different problems. A single application can and should use more than one:

```
┌─────────────────────────────────────────────────────────────────┐
│  Application Layer                                              │
│                                                                 │
│  SQLite          DuckDB           LanceDB          Kuzu         │
│  ──────────      ──────────       ──────────       ──────────   │
│  Session state   Analytics over   Semantic search  Relationship │
│  Agent config    wiki exports     over embeddings  traversal    │
│  Task queue      Log aggregation  RAG retrieval    Graph memory │
└─────────────────────────────────────────────────────────────────┘
```

**Concrete example:**
- **SQLite** tracks agent session state, task queue, and ingest metadata (row-level CRUD, ACID).
- **DuckDB** runs weekly analytics over exported Parquet snapshots of the wiki (how many pages per domain, confidence distributions, tag frequency).
- **LanceDB** stores embeddings of all wiki pages and enables "find pages semantically similar to this query" for RAG workflows.
- **Kuzu** stores the explicit `RELATES_TO` and `DEPENDS_ON` graph between pages for structured dependency traversal and knowledge graph reasoning.

Each database holds a projection of the same underlying knowledge — formatted for the operation it does best. Synchronisation between them is a design concern, but the duplication is intentional and justified by the performance characteristics of each engine.
