# Wiki Log

> **Append-only** chronological record of all wiki operations.
> Format: `## [YYYY-MM-DD] operation | title`
> Query tip: `Select-String "^\#\# \[" wiki\log.md | Select-Object -Last 5`

---

## [2026-04-08] init | Wiki system initialized

- **Operation:** init
- **Agent:** James (CAO)
- **Description:** Wiki layer established for the Team_James workspace. Based on Karpathy LLM Wiki pattern analysis. Schema defined in `_schema.md`. Index and log created.
- **Pages created:** `_schema.md`, `index.md`, `log.md`
- **Session ref:** Daily Note 2026-04-08

---

## [2026-04-08] research | Karpathy LLM Wiki Pattern — Fit Analysis

- **Operation:** ingest / research
- **Agent:** Researcher
- **Source:** https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
- **Description:** Evaluated Karpathy's LLM Wiki pattern against our existing setup. Produced fit analysis, gap analysis, and prioritized recommendations.
- **Pages created:** `karpathy-llm-wiki-pattern.md`
- **Key finding:** We have ~60% of the pattern; missing wiki layer, index, log, search tool.
- **Session ref:** Daily Note 2026-04-08

---

## [2026-04-08] seed | Agent Team Setup, Tooling Policy, Personal Notes System

- **Operation:** seed
- **Agent:** James (CAO)
- **Description:** Seeded wiki from existing workspace material. Three pages created covering team architecture, tooling decisions, and notes pipeline.
- **Pages created:** `agent-team-setup.md`, `tooling-policy.md`, `personal-notes-system.md`
- **Session ref:** Daily Note 2026-04-08

---

## [2026-04-08] research | Zep & Graphiti — Temporal Knowledge Graphs for Agent Memory

- **Operation:** research / ingest
- **Agent:** Researcher
- **Source:** https://github.com/getzep/graphiti + https://github.com/getzep/zep + https://github.com/getzep/context-engineering-contest
- **Description:** Deep-dive evaluation of the Zep/Graphiti ecosystem. Fetched actual source code (edges.py, nodes.py, graphiti.py) to extract exact data model. Key finding: our wiki frontmatter (valid_from, valid_to, is_valid) independently mirrors Graphiti's EntityEdge temporal model (valid_at, invalid_at). Produced fit analysis, infrastructure requirements, adoption recommendations.
- **Pages created:** `zep-graphiti-memory.md`
- **Key findings:**
  - Graphiti is fully local-capable (no Zep Cloud needed) via FalkorDB/Kuzu + LLM API
  - Our temporal frontmatter is a near-exact conceptual match to Graphiti's EntityEdge model
  - Zep Community Edition deprecated — all self-hosted paths go through Graphiti directly
  - Context engineering ≠ RAG: signal density and context ordering are the key disciplines
  - Recommend: `expired_at` field to wiki schema; atomic fact notation to MEMORY.md
- **Session ref:** [[log#2026-04-08-research-zep-graphiti]]

---

## [2026-04-08] research | OpenClaw Ecosystem — Analysis & Fit Assessment

- **Operation:** research
- **Agent:** Researcher
- **Source:** https://github.com/openclaw/openclaw
- **Description:** Deep-dive analysis of OpenClaw ecosystem (main repo, ClaWHub, Lobster, acpx, Windows companion, Ansible installer, memory-wiki plugin, plugin SDK). Evaluated architecture, skill system, ACP protocol, Windows maturity, and fit with our Copilot-CLI-centric setup.
- **Pages created:** `openclaw-ecosystem.md`
- **Key findings:** (1) Lobster workflow YAML format is direct inspiration for our `tools/` layer. (2) memory-wiki plugin validates our `wiki/` design and adds structured claims pattern. (3) OpenClaw itself is not a fit for direct adoption — wrong runtime, wrong interface paradigm. (4) ACP is an open standard worth monitoring.
- **Repos analyzed:** openclaw/openclaw, openclaw/clawhub, openclaw/skills, openclaw/lobster, openclaw/acpx, openclaw/openclaw-windows-node, openclaw/openclaw-ansible
- **Session ref:** log#2026-04-08-research-openclaw

---

## [2026-04-25] research | Agent Ecosystem Upgrade Opportunities

- **Operation:** research / synthesis
- **Agent:** James (CAO)
- **Source:** https://github.com/NousResearch/hermes-agent ; https://docs.z.ai/release-notes/new-released ; https://github.com/openclaw/openclaw/releases ; https://github.blog/changelog/2026-01-14-github-copilot-cli-enhanced-agents-context-management-and-new-ways-to-install/
- **Description:** Synthesized current external agent-platform developments from Hermes, Z.AI, OpenClaw, and GitHub Copilot into concrete workspace upgrades. Selected immediate improvements: a skill-candidate promotion runtime and a GitHub issue batch runtime; kept an ecosystem refresh radar as the next follow-up item.
- **Pages created:** `agent-ecosystem-upgrade-opportunities.md`
- **Session ref:** Daily Note 2026-04-25

---

## [2026-04-25] concept | Autonomic Tooling Pattern

- **Operation:** concept / synthesis
- **Agent:** James (CAO)
- **Description:** Classified current workspace work into pure autonomic loops, guarded autonomic loops, and human judgment loops. Documented which tasks already belong in tools, which should move next into tooling, and the assurance model for keeping future automation checked and integrated.
- **Pages created:** `autonomic-tooling-pattern.md`
- **Session ref:** Daily Note 2026-04-25

---

## [2026-04-25] update | Autonomic Tooling Pattern

- **Operation:** update / implementation-sync
- **Agent:** James (CAO)
- **Description:** Updated the autonomic tooling concept after shipping the recurring ecosystem refresh radar. The page now records the radar as an encoded guarded loop and advances the next follow-up priorities to issue-label synchronization and lifecycle-level dashboard integration.
- **Pages updated:** `autonomic-tooling-pattern.md`
- **Session ref:** Daily Note 2026-04-25

---

## [2026-04-26] update | Autonomic Tooling Pattern

- **Operation:** update / implementation-sync
- **Agent:** James (CAO)
- **Description:** Updated the autonomic tooling concept after shipping the self-healing knowledge refresh runtime. The page now records knowledge refresh as an encoded loop and advances the next follow-up priorities to delegated trace automation and retrieval eval hardening.
- **Pages updated:** `autonomic-tooling-pattern.md`
- **Session ref:** Daily Note 2026-04-26

---

## [2026-04-26] update | Delegation and Retrieval Hardening

- **Operation:** update / implementation-sync
- **Agent:** James (CAO)
- **Description:** Finished issue #4 delegated trace automation and issue #5 knowledge retrieval eval hardening. Added a QA agent persona, wrapper-governed delegation with coverage-denominator review, strict retrieval probes with explicit failure classes, and expanded workflow eval coverage to 28 green cases.
- **Pages updated:** `agent-orchestration-policy.md`, `autonomic-tooling-pattern.md`
- **Session ref:** Daily Note 2026-04-26

---

## [2026-04-26] documentation | Windows Hardware Triage

- **Operation:** documentation / implementation-sync
- **Agent:** James (CAO)
- **Description:** Anchored the new hardware-observability slice as durable workspace knowledge. Documented the Windows host-side USB/PnP/disk/volume snapshot workflow, the before/after diff pattern, explicit partial-capture semantics, and the boundary between host-visible enumeration and unsupported USB-C/cable/firmware diagnostics.
- **Pages created:** `windows-hardware-triage.md`
- **Session ref:** Daily Note 2026-04-26

---

## [2026-04-26] documentation | BPMN and Process Visualization

- **Operation:** documentation / research-sync
- **Agent:** James (CAO)
- **Description:** Anchored the new BPMN and process-visualization workstream as durable repo knowledge. Documented the local-first architecture: event log mining first, Mermaid review second, BPMN draft export third, with PM4Py and SpiffWorkflow kept as explicit future upgrade paths.
- **Pages created:** `bpmn-process-visualization.md`
- **Session ref:** Daily Note 2026-04-26

---

## [2026-04-26] source-summary | Gajek 2015 - Process Mining and Visualization in a Complex Software System

- **Operation:** source-summary / research-ingest
- **Agent:** James (CAO)
- **Source:** https://www2.informatik.uni-stuttgart.de/bibliothek/ftp/medoc.ustuttgart_fi/BCLR-2015-06/BCLR-2015-06.pdf
- **Description:** Ingested Fabian Gajek's 2015 Stuttgart thesis on process mining and visualization for complex software systems. Captured its strongest transferable lessons for our workspace: hierarchy-aware preprocessing, trace-backed visual explanation, JSON between mining and browser visualization, and browser-based D3 interaction as a strong fit for process analysis.
- **Pages created:** `gajek-process-mining-visualization-study.md`
- **Session ref:** Daily Note 2026-04-26

---

## [2026-04-26] update | BPMN and Process Visualization

- **Operation:** update / implementation-sync
- **Agent:** James (CAO)
- **Description:** Upgraded the process-visualization stack from flat discovery to a hierarchy-aware first pass. The miner now emits additive hierarchy metadata and path-stable node IDs, the HTML report now explains selected variants directly, and the D3 viewer can collapse path-prefix hierarchy groups with deterministic reset while Mermaid/BPMN stay explicitly flat/draft exports.
- **Pages updated:** `bpmn-process-visualization.md`
- **Session ref:** Daily Note 2026-04-26

---

## [2026-04-30] research | Reversa Framework — Fit Assessment

- **Operation:** research / implementation-sync
- **Agent:** James (CAO)
- **Source:** https://github.com/sandeco/reversa
- **Description:** Evaluated `sandeco/reversa` for reverse-engineering and tool-analytics fit. Decided to adapt the confidence-marker convention and the Scout/Detective/Architect methodology into native workspace assets, while explicitly skipping the upstream Node.js installer/runtime.
- **Pages created:** `reversa-framework.md`
- **Key findings:**
  - Reversa is best treated as a methodology donor, not an install target
  - `🟢 CONFIRMED / 🟡 INFERRED / 🔴 GAP` is the most portable epistemic upgrade
  - Git archaeology plus bounded reverse-engineering phases fit the current harness well
- **Session ref:** Daily Note 2026-04-30

---

## [2026-04-30] update | Agent Ecosystem Upgrade Opportunities

- **Operation:** update / cross-reference-sync
- **Agent:** James (CAO)
- **Description:** Added a backlink from the broader ecosystem-upgrade synthesis to `reversa-framework` so the new fit decision is discoverable from the existing external-pattern landscape.
- **Pages updated:** `agent-ecosystem-upgrade-opportunities.md`
- **Session ref:** Daily Note 2026-04-30

---

## [2026-04-30] documentation | Investment Research Foundations

- **Operation:** documentation / implementation-sync
- **Agent:** James (CAO)
- **Description:** Added the first finance-domain reference layer for Magnus, the investment research analyst. Created a PRIIP/KID reading guide and an Austrian fund landscape page to support later the investment research pattern.
- **Pages created:** `priip-kid-structure.md`, `austrian-fund-landscape.md`
- **Session ref:** Daily Note 2026-04-30

---

## [2026-04-09] tooling | wiki_lint.py — Wiki Linter (orphans, dead links, stale validity)

- **Operation:** implementation
- **Agent:** Developer (James)
- **Description:** Built `tools/wiki/wiki_lint.py` — 5-check linter for the wiki. Checks: missing ## Overview, orphan pages (no inbound links), dead backlinks (links to non-existent pages), stale validity (is_valid=true but valid_to passed), isolated pages (no outbound links). Flags: --strict (exit 1 on issues), --fix (auto-mark expired pages). First run found 3 orphans → fixed by adding backlinks. Final result: 0 issues.
- **Files created:** tools/wiki/wiki_lint.py
- **Orphans fixed:** ai-git-commit (← karpathy-llm-wiki-pattern), openclaw-auto-dream (← research-synthesis), system-architecture-db-upgrade-analysis (← embedded-db-comparison)
- **Graph after fix:** 13 pages, 159 edges
- **Session ref:** Daily Note 2026-04-09
## [2026-04-08] research | OpenClaw Ecosystem — Analysis & Fit Assessment

- **Operation:** research
- **Agent:** Researcher
- **Source:** https://github.com/openclaw/openclaw
- **Description:** Full ecosystem analysis of OpenClaw (352k ⭐). Don't adopt directly (Node.js/WSL2). Key patterns to steal: Lobster YAML workflow shell, memory-wiki claims system, skill.yaml manifests. ACP protocol worth monitoring.
- **Pages created:** openclaw-ecosystem.md
- **Session ref:** Daily Note 2026-04-08

---

## [2026-04-08] research | Zep & Graphiti — Temporal Knowledge Graphs for Agent Memory

- **Operation:** research
- **Agent:** Researcher
- **Source:** https://github.com/getzep/zep + https://github.com/getzep/graphiti
- **Description:** Deep analysis of Zep/Graphiti temporal knowledge graph architecture. Key finding: our wiki frontmatter (is_valid/valid_from/valid_to) independently mirrors Graphiti's EntityEdge model. Zep Cloud skipped (token-dependent). Graphiti local viable with Kuzu but needs LLM API. Context engineering patterns adopted.
- **Pages created:** zep-graphiti-memory.md
- **Session ref:** Daily Note 2026-04-08

---

## [2026-04-08] research | OpenViking — Context DB & Three-Layer Memory Architecture

- **Operation:** research
- **Agent:** Researcher
- **Source:** https://github.com/volcengine/OpenViking
- **Description:** Deep analysis of OpenViking context DB. Key finding: their Memory/Resource/Skill taxonomy maps to our memory/skills/wiki stack. L0/L1/L2 is a depth-of-detail axis (not a tier axis) — L0=abstract/frontmatter description, L1=overview (missing in our system), L2=full content. Windows supported via pip. Ollama embeddings viable. VLM optional (llava 4-8GB).
- **Pages created:** openviking-context-db.md
- **Session ref:** Daily Note 2026-04-08

---

## [2026-04-08] research | Cognee — Python Knowledge Engine & Hybrid Memory Pipeline

- **Operation:** research
- **Agent:** Researcher
- **Source:** https://github.com/topoteretes/cognee
- **Description:** Analysis of Cognee knowledge engine (add→cognify→search pipeline). Local-first viable with Kuzu (graph) + LanceDB (vector) + SQLite. Always needs LLM for cognify(). Cognee integrated Graphiti in 2025. Don't adopt as dependency — our hand-authored frontmatter beats LLM-extracted entities. Steal: Kuzu, LanceDB, SearchType pattern, env-var adapter pattern.
- **Pages created:** cognee-memory.md
- **Session ref:** Daily Note 2026-04-08

---

## [2026-04-08] decision | Memory Systems Research Synthesis

- **Operation:** analysis + decision
- **Agent:** Analyst
- **Sources:** openclaw-ecosystem, zep-graphiti-memory, openviking-context-db, cognee-memory
- **Description:** Cross-system synthesis of 4 researched memory frameworks. 7 adopt-now items (zero new deps), 5 adopt-later items (Kuzu+LanceDB wiki_tool etc.), explicit skip list. Key themes: temporal validity universal, L0/L1/L2 depth axis, hybrid vector+graph convergence, LLM ingestion bottleneck, agent/user memory split.
- **Pages created:** esearch-synthesis-memory-systems.md
- **Session ref:** Daily Note 2026-04-08

---

## [2026-04-08] analysis | Embedded DB Comparison — SQLite vs DuckDB vs LanceDB vs Kuzu

- **Operation:** analysis
- **Agent:** Analyst
- **Sources:** internal + official docs
- **Description:** Deep technical comparison of 4 embedded databases. Data models, storage formats, query models, Python integration, honest weaknesses, decision triggers, and co-existence architecture. ~1900 words.
- **Pages created:** mbedded-db-comparison.md
- **Session ref:** Daily Note 2026-04-08

---

## [2026-04-08] analysis | Architecture Upgrade Analysis — Agent KB System with Kuzu/LanceDB/DuckDB

- **Operation:** analysis
- **Agent:** Analyst
- **Sources:** internal (Gerhard's company system description + embedded-db-comparison)
- **Description:** Full architectural analysis of upgrading current SQLite+NetworkX+Azure OpenAI KB system. Phase 0-3 migration plan. Biggest win: Kuzu replaces SQLite entity_relations + NetworkX in-memory graph. LanceDB replaces Azure embedding blobs. DuckDB adds analytics layer via ATTACH bridge (zero migration).
- **Pages created:** system-architecture-db-upgrade-analysis.md
- **Session ref:** Daily Note 2026-04-08

---

## [2026-04-08] tooling | Wiki DB Stack (Phase 1-3) — DuckDB + LanceDB + Kuzu

- **Operation:** implementation
- **Agent:** Developer (James)
- **Description:** Built 3-tool wiki stack. Phase 1: DuckDB KPI dashboard (frontmatter -> analytics). Phase 2: LanceDB hybrid search (RRF semantic+BM25, all-MiniLM-L6-v2 local). Phase 3: Kuzu knowledge graph (11 nodes, 17 edges initially).
- **Files created:** tools/wiki/wiki_analytics.py, tools/wiki/wiki_search.py, tools/wiki/wiki_graph.py
- **Session ref:** Daily Note 2026-04-08

---

## [2026-04-08] enrichment | Overview sections + frontmatter for all 9 wiki pages

- **Operation:** enrichment
- **Agent:** Analyst (wiki-enricher background agent)
- **Description:** Added Overview (L1) to all 9 wiki pages missing it. Populated relates_to links on 5 pages. Added depends_on to 3 pages. Result: 100% schema compliance, 100% Overview coverage.
- **Pages touched:** cognee, embedded-db-comparison, karpathy, openclaw, openviking, research-synthesis, system-architecture, tooling-policy, zep
- **Session ref:** Daily Note 2026-04-08

---

## [2026-04-08] research | OpenClaw Auto-Dream — Cognitive Memory Architecture

- **Operation:** research
- **Agent:** Researcher
- **Source:** https://github.com/LeoYeAI/openclaw-auto-dream
- **Description:** Analysis of Auto-Dream v4.0 — a cognitive memory architecture with 5 layers (working/episodic/long-term/procedural/index), importance scoring with forgetting curves, health score (5 metrics), and daily dream cycles. Adopted: priority markers convention, memory/procedures.md layer. Deferred: dream consolidation in notes_summarizer.py, episode files.
- **Pages created:** openclaw-auto-dream.md
- **Adopted immediately:** priority markers in AGENTS.md + template, memory/procedures.md created
- **Session ref:** Daily Note 2026-04-08

---

- **Operation:** improvement
- **Agent:** Developer (James)
- **Description:** Extended Kuzu graph from 2 node types to 4 (Page, Tag, Agent, Domain) with 6 edge types (RELATES_TO, DEPENDS_ON, SUPERSEDED_BY, HAS_TAG, CREATED_BY, IN_DOMAIN). Graph grew from 17 to 109 edges. Final: 11 pages, 43 tags, 3 agents, 5 domains, 100% KPI compliance.
- **Session ref:** Daily Note 2026-04-08

---

## [2026-04-08] research | AI Git Commit — Karpathy gcm Pattern Analysis

- **Operation:** research
- **Agent:** Researcher
- **Source:** https://gist.github.com/karpathy/1dd0294ef9567971c1e4348a90d69285
- **Description:** Analysis of Karpathy's gcm shell function for AI-generated git commit messages. Adapted for Windows/PowerShell using `llm` CLI (uv tool install llm). Also updated karpathy-llm-wiki-pattern.md with new insights from today's updated gist (Dataview, Lint, Query→file protocol).
- **Pages created:** ai-git-commit.md
- **Pages updated:** karpathy-llm-wiki-pattern.md
- **Session ref:** Daily Note 2026-04-08

---

## [2026-04-09] tooling | Dream Consolidation + memory/episodes/ Layer

- **Operation:** implementation
- **Agent:** Developer (James)
- **Description:** Extended `notes_summarizer.py` with `--dream` flag (Auto-Dream pattern). Scans last 7 days of daily notes, extracts priority-marked entries (⚠️/🔥/📌), achievements, learnings, agent session bullets. Deduplicates against MEMORY.md, assigns `mem_NNN` IDs, backs up on >5 new entries. Stale thread detection for `- [ ]` items >14 days old. First dream run: 10 new entries extracted (mem_001-mem_010). Created `memory/episodes/` layer with README + first episode `agent-team-setup.md`.
- **Files created:** memory/episodes/README.md, memory/episodes/agent-team-setup.md
- **Files updated:** tools/notes/notes_summarizer.py, memory/MEMORY.md
- **Session ref:** Daily Note 2026-04-09
## [2026-04-10] ingest | NotebookLM MCP CLI

- **Operation:** ingest / research
- **Agent:** James (CAO)
- **Source:** https://github.com/jacob-bd/notebooklm-mcp-cli

---

## [2026-04-15] update | Agent Orchestration Policy — Failure Governance

- **Operation:** update
- **Agent:** James (CAO)
- **Description:** Extended the orchestration policy with typed failure governance. Added a reusable failure taxonomy and fallback order, plus runtime support for `failure_class`, `fallback_action`, and `escalate_when` in delegated-task trace and review artifacts.
- **Pages updated:** `agent-orchestration-policy.md`
- **Files changed:** `config/failure-taxonomy.yaml`, `AGENTS.md`, `memory/procedures.md`, `skills/orchestration/SKILL.md`, `skills/session-handoff/SKILL.md`, `tools/agents/agent_trace.py`, `tools/agents/agent_review.py`, `tools/session/session-lifecycle.ps1`
- **Session ref:** Daily Note 2026-04-15

---

## [2026-04-15] update | Agent Orchestration Policy — Workflow Eval Harness

- **Operation:** update
- **Agent:** James (CAO)
- **Description:** Added a private workflow eval harness and documented the distinction between capability evals and regression evals. The workspace now has four seeded local suites plus repeatable workflow-eval review artifacts in `memory/reviews/`.
- **Pages updated:** `agent-orchestration-policy.md`
- **Files changed:** `tools/evals/run_workflow_evals.py`, `evals/research-synthesis/suite.json`, `evals/handoff/suite.json`, `evals/trace-quality/suite.json`, `evals/hypothesis-discipline/suite.json`, `AGENTS.md`, `memory/procedures.md`
- **Session ref:** Daily Note 2026-04-15

---

## [2026-04-15] update | Agent Orchestration Policy — Ablation Review

- **Operation:** update
- **Agent:** James (CAO)
- **Description:** Added a baseline ablation review for workflow controls. The first run keeps `verifier`, `checkpoint`, and `ledger` as high-risk controls to remove, and explicitly blocks reconciliation optimization until a private eval exists for it.
- **Pages updated:** `agent-orchestration-policy.md`
- **Files changed:** `tools/evals/run_ablation_review.py`, `memory/reviews/ablation-review-template.md`, `memory/reviews/ablation-review.json`, `memory/reviews/ablation-review.md`, `memory/reviews/ablation-review-history.jsonl`, `AGENTS.md`, `memory/procedures.md`, `evals/research-synthesis/suite.json`, `evals/handoff/suite.json`, `evals/trace-quality/suite.json`, `evals/hypothesis-discipline/suite.json`
- **Session ref:** Daily Note 2026-04-15
- **Description:** Repo analysis. Installed via uv tool install. Auth valid (73 notebooks). MCP in ~/.copilot/mcp.json. Known issue: tools not loading in Copilot CLI. nlm CLI works as fallback.
- **Pages created:** notebooklm-mcp-cli.md
- **Session ref:** Daily Note 2026-04-10

---

## [2026-04-15] research | GitHub Copilot Rubber Duck

- **Operation:** research
- **Agent:** Researcher
- **Sources:** https://github.blog/ai-and-ml/github-copilot/github-copilot-cli-combines-model-families-for-a-second-opinion/ + https://github.com/github/copilot-cli + https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference + https://docs.github.com/en/get-started/using-github/exploring-early-access-releases-with-feature-preview
- **Description:** Researched GitHub Copilot's Rubber Duck feature before enabling experimental mode. Key finding: Rubber Duck is an official but experimental Copilot CLI review agent that adds a cross-model second opinion at selected checkpoints. Documentation is real but still sparse and CLI-scoped; there is no dedicated product reference page yet.
- **Pages created:** `github-copilot-rubber-duck.md`
- **Key findings:**
  - Rubber Duck is officially announced by GitHub, but the only clearly documented first-class surface is Copilot CLI.
  - Experimental mode is both an access flag and a maturity boundary: the feature is still in development and should be treated as non-GA.
  - The feature is most valuable as a selective sparring partner for complex plans/refactors, not as a default workflow primitive for stable and reproducible work.
- **Session ref:** Daily Note 2026-04-15

---

## [2026-04-10] research | GitHub Copilot SDK — Hooks, Skills, Harness Migration Assessment

- **Operation:** research
- **Agent:** James (CAO)
- **Source:** https://github.com/github/copilot-sdk
- **Description:** Full evaluation of GitHub Copilot SDK (Public Preview). Key findings: (1) `on_session_end` hook with `reason` field cleanly replaces PS `try/finally`; (2) `skill_directories` + `SKILL.md` format is directly compatible with our `skills/` dir (just rename `skill.md`); (3) `additional_context` in `on_session_start` = automatic MEMORY.md injection; (4) BYOK decouples from GitHub auth. Decision: adopt-later (Phase 2), rename `skill.md` → `SKILL.md` now as Phase 1.
- **Pages created:** github-copilot-sdk.md
- **Session ref:** Daily Note 2026-04-10

---

- **Operation:** implementation
- **Agent:** Developer (James)
- **Description:** (1) Invoke-James wraps copilot in try/finally, close-session.ps1 runs on every exit. (2) All obsidian CLI references removed from automation layer, replaced with Add-Content file I/O.
- **Files created:** tools/session/close-session.ps1
- **Files updated:** profile.ps1, skills/daily-notes/skill.md, AGENTS.md
- **Session ref:** Daily Note 2026-04-10

---

## [2026-04-10] research | Claude Code Harness — Pattern Analysis & Fit Assessment

- **Operation:** research + create
- **Agent:** James (CAO) + 3 parallel research agents (wiki-knowledge-reader, hermes-researcher, harness-deep-reader)
- **Description:** Deep analysis of Chachamaru127/claude-code-harness. Cross-referenced against Hermes patterns, OpenClaw ecosystem, Copilot SDK, and our agent-team-setup. 7 patterns directly adoptable today identified. Memory-bridge pattern (per-prompt injection) confirmed as critical missing piece for Phase 2.
- **Pages created:** claude-code-harness.md
- **Pages updated:** index.md, gent-team-setup.md (backlink)
- **Session ref:** Daily Note 2026-04-10

## [2026-04-10] research | Archon — Deterministic AI Workflow Engine

- **Operation:** research + ingest
- **Agent:** James (CAO) + 2 parallel explore agents
- **Source:** https://github.com/coleam00/Archon
- **Pages created:** `archon.md`
- **Pages updated:** `index.md`, `agent-team-setup.md` (backlink added)
- **Key findings:** .claude/rules/ domain split, handoff.md + prime.md commands (P0), YAML DAG workflows (Phase 3); Archon is the production reference for our Copilot SDK Phase 2 target

## [2026-04-10] documentation | Marp — Markdown Presentation Ecosystem

- **Operation:** research / documentation
- **Agent:** Researcher
- **Source:** https://marp.app/ + https://github.com/marp-team/marp-cli + https://github.com/marp-team/marp-core + https://marketplace.visualstudio.com/items?itemName=marp-team.marp-vscode
- **Description:** Full research and documentation of the Marp ecosystem. Covers Marp Core, Marp CLI, Marp for VS Code, slide syntax, directives, built-in themes (default/gaia/uncover), custom CSS themes, background images, two-column layout, math typesetting, CLI flags, VS Code workflow, and use cases for Gerhard's team. Created wiki page and skills/presentations/ skill with complete working analyst presentation example.
- **Pages created:** marp.md
- **Skills created:** skills/presentations/SKILL.md, skills/presentations/skill.yaml
- **Session ref:** Daily Note 2026-04-10

---

## [2026-04-11] documentation | Marp Advanced — McKinsey Design Patterns
 
- **Operation:** research / documentation
- **Agent:** Researcher
- **Description:** Researched and documented advanced Marp presentation patterns at McKinsey/BCG consultant level. Six topics covered: (1) McKinsey slide structure — action titles, SCQA, Pyramid Principle, 3-box Exec Summary; (2) KPI metric blocks — big number cards, traffic light status, 4-card grid; (3) Professional color & typography — McKinsey/BCG palettes, Windows font stack, slide sizing; (4) Image best practices — external URLs, split layouts, overlay text, attribution; (5) Advanced layout patterns — 3-column grid, icon cards, quote slide, process timeline, financial table; (6) Complete production CSS theme.
- **Pages created:** marp-advanced.md
- **Skills created:** skills/presentations/corp-theme.css
- **Skills updated:** skills/presentations/SKILL.md (McKinsey-Style Deck Patterns section added)
- **Pages updated:** marp.md (relates_to), index.md (new entry)
- **Session ref:** Daily Note 2026-04-11

---

## [2026-04-14] research | Softaworks Agent Toolkit — Skill Library Fit Assessment

- **Operation:** recovery + research documentation
- **Agent:** James (CAO)
- **Source:** https://github.com/softaworks/agent-toolkit
- **Description:** Retroactively documented the 2026-04-12 analysis that had reached the daily note but not the wiki layer. Core result: use the repo as a pattern source, not a bulk dependency. Highest-value imports were `session-handoff` for session continuity and `writing-clearly-and-concisely` for prose quality; `marp-slide` patterns were merged into our existing presentations skill.
- **Pages created:** softaworks-agent-toolkit.md
- **Pages updated:** agent-team-setup.md, index.md
- **Session ref:** Daily Note 2026-04-14

---

## [2026-04-14] analysis | Human-Memory-Inspired Agent Memory — Gap Analysis

- **Operation:** analysis
- **Agent:** James (CAO)
- **Source:** NotebookLM notebook `Mimicking Human Memory for Advanced AI Agents`
- **Description:** Compared our current markdown-first memory system against brain-inspired agent memory research. Confirmed strong coverage of structural memory layers and consolidation. Identified the main remaining gaps as active working memory management, conflict-aware reconsolidation, metacognitive confidence gating, adaptive forgetting, and stronger processed episodic learning.
- **Pages created:** human-memory-inspired-agent-memory-gap-analysis.md
- **Pages updated:** index.md
- **Session ref:** Daily Note 2026-04-14

---

## [2026-04-19] research | GitHub Copilot CLI Remote Access and Rubber Duck

- **Operation:** research / refresh
- **Agent:** James (CAO)
- **Sources:** https://docs.github.com/en/copilot/concepts/agents/copilot-cli/about-remote-access + https://docs.github.com/en/copilot/how-tos/copilot-cli/steer-remotely + https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference + https://github.blog/ai-and-ml/github-copilot/github-copilot-cli-combines-model-families-for-a-second-opinion/
- **Description:** Produced a precise operating analysis of `/remote` and refreshed the current Rubber Duck assessment. Key result: `/remote` is GitHub.com/GitHub-Mobile steering for a still-local CLI session, while Rubber Duck remains an official but experimental CLI-only review layer with sparse documentation. Added explicit implications for Telegram, remote continuation, and checkpoint-based use.
- **Pages created:** `github-copilot-cli-remote-access.md`
- **Pages updated:** `github-copilot-rubber-duck.md`, `index.md`
- **Session ref:** Daily Note 2026-04-19

---

## [2026-04-25] maintenance | Wiki backlink repair for AGI analysis page

- **Operation:** maintenance
- **Agent:** James (CAO)
- **Description:** Repaired an orphan-page issue from wiki lint by linking `agi-project-analysis-patterns.md` back into `agent-orchestration-policy.md`. This restores inbound reachability for the AGI analysis page without changing its substantive content.
- **Pages updated:** `agent-orchestration-policy.md`
- **Session ref:** Daily Note 2026-04-25

---

## [2026-04-15] documentation | Memory Runtime Tooling

- **Operation:** implementation documentation
- **Agent:** James (CAO)
- **Source:** Local implementation in `tools/memory/`, `tools/session/`, and `tools/notes/`
- **Description:** Documented the runtime implementation of the memory roadmap: session scratchpad finalization, local retrieval, reconciliation review, maintenance scoring, and repeatable QA metrics integrated into the close-session flow.
- **Pages created:** memory-runtime-tooling.md
- **Pages updated:** index.md
- **Session ref:** Daily Note 2026-04-15

---

## [2026-04-15] documentation | Memory Session Lifecycle

- **Operation:** lifecycle hardening documentation
- **Agent:** James (CAO)
- **Source:** Local implementation in `tools/session/` and `tools/memory/`
- **Description:** Documented the crash-resistant memory lifecycle with start preflight, mid-session checkpoints, close finalization, and guard reactions. This formalizes the move away from close-only persistence.
- **Pages created:** memory-session-lifecycle.md
- **Pages updated:** memory-runtime-tooling.md, index.md
- **Session ref:** Daily Note 2026-04-15

---

## [2026-04-15] documentation | Unified Lifecycle History

- **Operation:** observability refinement
- **Agent:** James (CAO)
- **Source:** Local implementation in `tools/session/session-lifecycle.ps1` and `tools/memory/memory_guard.py`
- **Description:** Refined the logging model so `memory-guard-history.jsonl` now serves as both guard history and session breadcrumb timeline. Added lifecycle events with session IDs and safe-handover markers instead of introducing a second parallel breadcrumbs file.
- **Pages updated:** memory-session-lifecycle.md, memory-runtime-tooling.md
- **Session ref:** Daily Note 2026-04-15

---

## [2026-04-15] documentation | Agent Orchestration Policy and Model Routing

- **Operation:** implementation + documentation
- **Agent:** James (CAO)
- **Source:** Local implementation in `AGENTS.md`, `skills/orchestration/`, `config/model-routing.yaml`, `tools/agents/`, and `tools/session/`
- **Description:** Formalized the delegated-agent operating model with mandatory task metadata, fixed checkpoint cadence, cross-family model routing, JSONL trace logging, and repeatable agent performance reviews integrated into checkpoint and close routines.
- **Pages created:** `agent-orchestration-policy.md`
- **Pages updated:** `agent-team-setup.md`, `index.md`
- **Session ref:** Daily Note 2026-04-15

---

## [2026-04-15] documentation | Knowledge Effectiveness Review

- **Operation:** knowledge observability and routine hardening
- **Agent:** James (CAO)
- **Source:** Local implementation in `tools/wiki/` and `tools/session/`
- **Description:** Added telemetry for wiki search and graph usage, repaired wiki KPI analytics, introduced a repeatable knowledge performance review, and integrated graph rebuild + search reindex + review into the session routines.
- **Pages created:** knowledge-effectiveness-review.md
- **Pages updated:** index.md, memory-session-lifecycle.md, agent-team-setup.md
- **Session ref:** Daily Note 2026-04-15

---

## [2026-04-15] documentation | NotebookLM Auth Recovery Pattern

- **Operation:** operational documentation update
- **Agent:** James (CAO)
- **Source:** Live diagnosis of `nlm login`, Chrome process command lines, and CDP-based re-authentication
- **Description:** Documented the stable NotebookLM re-authentication rule for this workspace: first inspect whether an existing local Chrome debug session is already running and reuse it through CDP; only launch a fresh login browser when no reusable debug session exists.
- **Pages updated:** `notebooklm-mcp-cli.md`
- **Session ref:** Daily Note 2026-04-15

---

## [2026-04-15] research | GitHub Copilot Hooks

- **Operation:** research
- **Agent:** Researcher
- **Source:** Official GitHub Docs for hooks, Copilot CLI, Copilot cloud agent, and the Copilot SDK hooks guide
- **Description:** Researched GitHub Copilot Hooks as they exist today. Confirmed that product hooks are repository-scoped JSON shell commands for Copilot CLI and Copilot cloud agent, best suited for deterministic policy, logging, and cleanup. Also confirmed that they are materially narrower than SDK hooks: customer outputs are mostly ignored, `preToolUse` denial is the main effective control point, and there is no native equivalent to our checkpoint-based lifecycle.
- **Pages created:** github-copilot-hooks.md
- **Pages updated:** index.md, github-copilot-sdk.md
- **Session ref:** Daily Note 2026-04-15

---

## [2026-04-15] analysis | AGI Project Analysis Patterns

- **Operation:** research synthesis
- **Agent:** James (CAO) with Researcher + Developer input
- **Source:** NotebookLM notebook `The Future of AGI: Intelligence, Alignment, and Economic Impact`, plus local workspace policy and memory pages
- **Description:** Synthesized the notebook's main lessons for sustainable complex-project work into concrete team patterns. Main conclusions: harness-first design beats monolithic prompting, uncertainty must be tracked explicitly, evaluation should behave like a private regression discipline, and long-running work needs typed handoffs plus stronger plan artifacts.
- **Pages created:** `agi-project-analysis-patterns.md`
- **Pages updated:** `index.md`
- **Session ref:** Daily Note 2026-04-15

---

## [2026-04-15] implementation | AGI Harness Phase 1

- **Operation:** container-first rollout
- **Agent:** James (CAO)
- **Source:** Local implementation in `AGENTS.md`, `memory/procedures.md`, `skills/orchestration/`, `skills/session-handoff/`, `tools/session/`, and `plans/`
- **Description:** Implemented phase 1 of the AGI rollout plan. Medium+ tasks now have a canonical plan container with assumptions, validation plan, replan rule, and handoff state; checkpoints now print a standard summary block for open WIP, open hypotheses, blockers, and next test.
- **Pages updated:** `agent-orchestration-policy.md`
- **Session ref:** Daily Note 2026-04-15

---

## [2026-04-15] implementation | AGI Harness Phase 2

- **Operation:** epistemic-discipline rollout
- **Agent:** James (CAO)
- **Source:** Local implementation in `AGENTS.md`, `memory/procedures.md`, `skills/orchestration/`, `skills/session-handoff/`, `tools/agents/`, `tools/session/`, and `plans/`
- **Description:** Implemented phase 2 of the AGI rollout plan. Medium+ analysis tasks now use a Hypothesis Ledger schema, and runtime artifacts can surface hypothesis updates, open hypothesis counts, contradiction signals, and next-test state through trace, review, and checkpoint outputs.
- **Pages updated:** `agent-orchestration-policy.md`
- **Session ref:** Daily Note 2026-04-15

## [2026-05-10] created | rowboat-patterns

- **Operation:** created
- **Agent:** James (CAO)
- **Description:** Research page documenting Memory Compounds and Live Wiki Pages patterns adopted from rowboatlabs/rowboat analysis.
- **Pages created:** wiki/rowboat-patterns.md
- **Session ref:** Rowboat integration session

---

## [2026-05-10] created | agent-team-health

- **Operation:** created
- **Agent:** James (CAO)
- **Description:** First live wiki page — auto-refreshed by wiki_team_health_refresh.py at each session close. Documents memory and knowledge graph health.
- **Pages created:** wiki/agent-team-health.md
- **Session ref:** Rowboat integration session

---

## [2026-05-10] updated | _schema

- **Operation:** updated
- **Agent:** James (CAO)
- **Description:** Added live page fields: live:, refresh_tool:, refresh_cadence:. Added agent rule 9 for live pages.
- **Pages updated:** wiki/_schema.md
- **Session ref:** Rowboat integration session

---

---

## [2026-05-10] research | Hermes Agent v0.12.0 + v0.13.0 — Curator & Tenacity Releases

- **Operation:** create
- **Agent:** James (CAO)
- **Pages created:** `hermes-v012-v013.md`
- **Summary:** Autonomous Curator pattern (skill lifecycle), FTS5 Session Search, Ralph Goal Loop. Curator + Dream Streak adopted; Goal Loop deferred.

---

## [2026-05-10] research | OpenClaw May 2026 — Skill Workshop, Standing Orders, Auto-Dream v4.0

- **Operation:** create
- **Agent:** James (CAO)
- **Pages created:** `openclaw-may2026.md`
- **Summary:** Standing Orders fully adopted in AGENTS.md. Auto-Dream v4.0 gaps (streak, growth, skip-with-recall) all adopted in notes_summarizer.py. Skill Workshop deferred.

---

## [2026-05-10] create | skills_curator.py + usage.json — Hermes Curator Pattern Adoption

- **Operation:** create
- **Agent:** James (CAO)
- **Files created:** `tools/skills/skills_curator.py`, `skills/usage.json`, `memory/index.json`
- **Summary:** Full skill lifecycle manager with check/apply modes. Wired into close-session.ps1.

---

## [2026-05-10] research | Mnemosyne — Local AI Memory System Evaluation + Integration

- **Operation:** research / implementation-sync
- **Agent:** James (CAO)
- **Source:** https://github.com/rowboatlabs/mnemosyne
- **Description:** Evaluated Mnemosyne v2.3 as a semantic recall upgrade. Installed as `uv tool`, wired MCP into Copilot CLI config, added dual-write bridge in dream cycle, built migration script for existing MEMORY.md entries. Verdict: ADAPT — Mnemosyne adds vector search; MEMORY.md stays for human readability and Obsidian graph links.
- **Pages created:** `mnemosyne-memory.md`
- **Files created/modified:** `tools/memory/mnemosyne_migrate.py`, `tools/notes/notes_summarizer.py` (dual-write), `~/.copilot/mcp.json` (MCP wiring), `.gitignore` (.mnemosyne/)
- **Session ref:** Daily Note 2026-05-10



## [2026-05-13] created | ecc-patterns-adopted

Created wiki page documenting ECC (everything-claude-code) pattern adoption: Anti-patterns/Checklist skill sections, rules/ directory, plan template phases, skill lint enforcement. Rubber Duck reviewed (GPT-5.4-mini), 4 patterns implemented.
