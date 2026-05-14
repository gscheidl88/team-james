# Wiki Index

> **Content catalog** — all pages in `wiki/`, one-line summary per entry.
> Updated by James after every ingest or new page creation.
> Agents: read this first when answering queries to find relevant pages.

---

## Meta

| Page | Type | Summary | Status | Valid |
|------|------|---------|--------|-------|
| [[_schema]] | reference | Frontmatter schema standard for all wiki pages | active | ✅ |
| [[log]] | reference | Append-only log of all wiki operations | active | ✅ |

## Research

| Page | Type | Summary | Domain | Valid |
|------|------|---------|--------|-------|
| [[karpathy-llm-wiki-pattern]] | research | Karpathy LLM Wiki pattern fit analysis + our implementation decisions | meta | ✅ |
| [[openclaw-ecosystem]] | research | OpenClaw personal assistant ecosystem — don't adopt directly, steal Lobster/claims/skill-manifest patterns | research | ✅ |
| [[zep-graphiti-memory]] | research | Zep/Graphiti temporal knowledge graphs — our wiki frontmatter independently mirrors Graphiti's EntityEdge model | research | ✅ |
| [[openviking-context-db]] | research | OpenViking context DB — 3-type taxonomy (Memory/Resource/Skill) maps to our stack; L0/L1/L2 depth axis worth adopting | research | ✅ |
| [[cognee-memory]] | research | Cognee knowledge engine — hybrid vector+graph pipeline; steal Kuzu+LanceDB backends; skip full lib | research | ✅ |
| [[research-synthesis-memory-systems]] | decision | Synthesis of 4 memory systems (OpenClaw/Graphiti/OpenViking/Cognee) — decision matrix, adopt-now/later/skip | decision | ✅ |
| [[embedded-db-comparison]] | analysis | Deep technical comparison: SQLite vs DuckDB vs LanceDB vs Kuzu — data models, storage, queries, weaknesses | technical | ✅ |
| [[system-architecture-db-upgrade-analysis]] | analysis | Architecture upgrade analysis: how Kuzu/LanceDB/DuckDB improve the owner's company KB system (SQLite+NetworkX+Azure) | technical | ✅ |
| [[zep-graphiti-memory]] | research | Zep & Graphiti temporal knowledge graphs — deep-dive, data model, fit analysis vs our wiki | research | ✅ |
| [[openclaw-ecosystem]] | research | OpenClaw ecosystem deep-dive — architecture, Lobster, ACP, Windows, fit analysis | research | ✅ |
| [[openclaw-auto-dream]] | research | Auto-Dream v4.0 — 5-layer cognitive memory architecture, importance scoring, forgetting curves, dream cycles; adopted: priority markers + procedures.md | agent-memory | ✅ |
| [[agent-ecosystem-upgrade-opportunities]] | research | Current Hermes, Z.AI, OpenClaw, and Copilot signals mapped to the next local team upgrades | meta | ✅ |
| [[reversa-framework]] | research | Reversa fit assessment — adapt confidence markers and reverse-engineering workflow, skip the upstream installer/runtime | meta | ✅ |

| [[rowboat-patterns]] | research | Rowboat patterns adopted: Memory Compounds (access-log importance) + Live Wiki Pages (auto-refresh); no process mining overlap | meta | ✅ |
| [[hermes-v012-v013]] | research | Hermes v0.12.0 + v0.13.0 — Autonomous Curator (skill lifecycle), FTS5 Session Search, Ralph Goal Loop; adoption status per feature | agent-ecosystem | ✅ |
| [[openclaw-may2026]] | research | OpenClaw May 2026 — Skill Workshop, Standing Orders, Auto-Dream v4.0 gaps (streak, growth metrics, skip-with-recall); all three adopted | agent-ecosystem | ✅ |
| [[mnemosyne-memory]] | research | Mnemosyne v2.3 evaluation — ADAPT verdict; vector semantic recall layer; fastembed ONNX, MCP server, dual-write in dream cycle | agent-memory | ✅ |


## Harness & Infrastructure

| Page | Type | Summary | Domain | Valid |
|------|------|---------|--------|-------|
| [[github-copilot-sdk]] | research | GitHub Copilot SDK (Public Preview) — hooks, skills, BYOK; adopt-later to replace PowerShell harness | meta | ✅ |
| [[github-copilot-hooks]] | research | GitHub Copilot Hooks today are repo-scoped JSON shell hooks for CLI/cloud agent; strong for policy and audit, weaker than SDK callbacks for memory injection | meta | ✅ |
| [[github-copilot-cli-remote-access]] | research | `/remote` steers a running local Copilot CLI session from GitHub.com or GitHub Mobile; execution remains local, the feature is preview-stage, and it is not a general messaging bridge | meta | ✅ |
| [[github-copilot-rubber-duck]] | research | Official but experimental Copilot CLI review agent; useful as a second-opinion sparring partner, but docs are sparse and the feature is not yet stable enough for default workflow use | meta | ✅ |
| [[claude-code-harness]] | research | claude-code-harness pattern analysis — memory-bridge, sub-agent orchestration, Plans.md SSOT, effort scoring; 7 patterns adoptable today | meta | ✅ |
| [[archon]] | research | Archon workflow engine — YAML DAG orchestration, `.claude/rules/` domain split, `handoff.md` + `prime.md` commands directly adoptable; P0: fix session-close gap | meta | ✅ |
| [[softaworks-agent-toolkit]] | research | softaworks agent-toolkit — selective import source; adopted session-handoff and writing-clearly-and-concisely, merged Marp patterns locally | meta | ✅ |
| [[ecc-patterns-adopted]] | research | ECC (everything-claude-code) patterns adopted: Anti-patterns/Checklist sections, rules/ directory, plan template phases, skill lint enforcement | meta | ✅ |

## Analysis

| Page | Type | Summary | Domain | Valid |
|------|------|---------|--------|-------|
| [[human-memory-inspired-agent-memory-gap-analysis]] | analysis | Gap analysis of our markdown-first memory system against human-memory-inspired agent memory research; strong on layering and consolidation, weaker on runtime governance | meta | ✅ |
| [[agi-project-analysis-patterns]] | analysis | AGI notebook synthesis for sustainable complex-project work: hierarchical decomposition, explicit uncertainty handling, evaluation discipline, typed handoffs, and harness-first design | meta | ✅ |

## Decisions

| Page | Type | Summary | Domain | Valid |
|------|------|---------|--------|-------|
| [[tooling-policy]] | decision | uv Python tools vs MCPs — criteria, script standard, exceptions | meta | ✅ |

## Concepts

| Page | Type | Summary | Domain | Valid |
|------|------|---------|--------|-------|
| [[autonomic-tooling-pattern]] | concept | Defines which recurring workspace tasks belong in autonomic tooling, which need guarded automation, and which stay human-led | meta | ✅ |

## Documentation

| Page | Type | Summary | Domain | Valid |
|------|------|---------|--------|-------|
| [[agent-team-health]] | documentation | Live auto-refreshed summary of memory health, knowledge graph state, and top compounding memories | meta | ✅ |
| [[agent-team-setup]] | documentation | Architecture, agents, memory system, key files | meta | ✅ |
| [[agent-orchestration-policy]] | documentation | Standard policy for delegated agents: task descriptors, checkpoint cadence, trace logging, model routing, and cross-family verification | meta | ✅ |
| [[personal-notes-system]] | documentation | Daily/Weekly/Monthly/Annual pipeline, summarizer, scheduler | personal | ✅ |
| [[memory-runtime-tooling]] | documentation | Runtime memory stack: scratchpad finalization, retrieval, reconciliation, maintenance, and repeatable QA metrics | meta | ✅ |
| [[memory-session-lifecycle]] | documentation | Crash-resistant lifecycle for memory operations: start preflight, checkpoints, close finalization, and guard reactions | meta | ✅ |
| [[knowledge-effectiveness-review]] | documentation | Operational review loop for wiki RAG + graph effectiveness: telemetry, freshness checks, and routine-integrated performance review | meta | ✅ |
| [[ai-git-commit]] | documentation | AI-generated git commit messages — Karpathy gcm pattern + Windows/PowerShell adaptation using `llm` CLI | technical | ✅ |
| [[marp]] | documentation | Marp — Markdown Presentation Ecosystem; install, syntax, themes, CLI, VS Code workflow | technical | ✅ |
| [[marp-advanced]] | documentation | Marp Advanced — McKinsey/BCG design patterns: action titles, SCQA, KPI cards, CSS layout, corp-theme.css | technical | ✅ |
| [[windows-hardware-triage]] | documentation | Host-side USB, PnP, disk, and volume observability workflow for device maintenance and before/after troubleshooting on Windows | technical | ✅ |
| [[bpmn-process-visualization]] | documentation | Local-first approach for BPMN-oriented, data-driven process visualization: mine event logs, visualize process maps, and export BPMN drafts | technical | ✅ |
| [[gajek-process-mining-visualization-study]] | source-summary | Stuttgart 2015 source summary: hierarchy-aware process mining, D3/web visualization, and trace-backed model understanding for complex software systems | technical | ✅ |

## Source Summaries

*(no entries yet)*

---

*Last updated: 2026-05-13 by James*
*Total pages: 43 (excl. index + log + schema)*
