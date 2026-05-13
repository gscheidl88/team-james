---
id: archon
type: research
title: "Archon — Deterministic AI Workflow Engine (coleam00)"
description: "Archon encodes dev processes as declarative YAML DAGs so AI fills intelligence at each node but the structure is deterministic — highest-relevance pattern: `.claude/rules/`, `handoff.md`, and `prime.md` commands."
tags: [agent-orchestration, workflows, harness, claude-code, memory-injection, session-management]
domain: meta

is_project: false
project:

status: active
is_valid: true
valid_from: 2026-04-10
valid_to:
expired_at:
superseded_by:

confidence: high
reviewed_by: James
review_date: 2026-04-10

created: 2026-04-10
created_by: James
last_modified: 2026-04-10
modified_by: James
source: "https://github.com/coleam00/Archon"
ingest_session: "[[log#2026-04-10-archon-research]]"

relates_to:
  - "[[claude-code-harness]]"
  - "[[github-copilot-sdk]]"
  - "[[agent-team-setup]]"
  - "[[research-synthesis-memory-systems]]"
depends_on: []
---

## Overview

Archon is a deterministic workflow engine for AI coding agents by Cole Medin (coleam00). Instead of letting the AI decide the execution flow, Archon encodes development processes as YAML DAGs — the AI fills intelligence at each node, but the structure (plan → implement → test → review → PR) is owned by the developer and always runs identically. The most immediately applicable patterns for our team are: the `.claude/rules/*.md` domain-rule split, the `handoff.md` session-closing command, and `prime*.md` context-injection commands — all directly solving gaps we've identified in our own harness.

---

## What Is Archon?

**Category:** Workflow engine / AI coding harness  
**Author:** Cole Medin (coleam00)  
**Tech stack:** TypeScript, Bun runtime, SQLite (default) / PostgreSQL, Claude Code SDK + Codex  
**Deployment:** Docker, VPS, CLI — multi-platform (Slack, Telegram, Discord, GitHub webhooks, Web UI)  
**Platforms supported:** Claude Code SDK, Codex (adapters pattern)

**Core idea:** Like Dockerfiles for infra or GitHub Actions for CI/CD — Archon does for AI workflows what those tools did for their domains. Every dev process gets a YAML spec; you commit it; the whole team runs the same deterministic flow.

```
User request
    ↓
Archon orchestrator reads workflow YAML
    ↓
Node 1 (AI): Plan the feature  →  AI fills in the plan
Node 2 (AI+loop): Implement  →  AI writes code, loop until tests pass
Node 3 (deterministic): Run tests  →  bash script, not AI
Node 4 (human gate): Approve  →  human approves or rejects
Node 5 (AI): Write PR description  →  AI fills in
Node 6 (deterministic): Create PR  →  git command
```

---

## Architecture Deep Dive

### Monorepo Structure (10 packages)

| Package | Role |
|---------|------|
| `core` | Central orchestration engine |
| `workflows` | DAG execution engine |
| `isolation` | Git worktree + sandbox isolation per run |
| `adapters` | AI model provider adapters (Claude/Codex) |
| `server` | API backend (port 3090) |
| `cli` | Command-line interface |
| `web` | React frontend (port 5173) |
| `git` | Git operations |
| `paths` | Path management utilities |
| `docs-web` | Documentation site |

### `.claude/` — Knowledge Injection System (⭐ Most Relevant)

This is Archon's own Claude Code agent configuration — and it is the most sophisticated `.claude/` setup available as open-source reference.

```
.claude/
├── settings.json          # Lifecycle hooks + env vars
├── agents/                # 13 named agent role definitions
├── skills/                # 14 reusable skill modules (with hooks!)
├── rules/                 # 11 domain-specific rule files
├── commands/              # 14+ executable workflow commands
├── docs/                  # 4 architecture reference guides
└── PRPs/                  # Prompt Response Patterns
```

#### settings.json — Lifecycle Hooks

```json
{
  "env": { "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1" },
  "hooks": {
    "SessionStart":    [...],   // restore context, prime memory
    "UserPromptSubmit":[...],   // update agent status, inject context
    "Stop":            [...],   // save state, run handoff
    "SubagentStop":    [...],   // callback notification
    "Notification":    [...]    // async event handling
  }
}
```

This maps 1:1 to the GitHub Copilot SDK hooks we're targeting in Phase 2.

#### agents/ — 13 Named Role Definitions

Each agent is a `.md` file defining: role, tools, rules to follow, memory access.

Examples: `code-reviewer.md`, `codebase-analyst.md`, `triage-agent.md`, `web-researcher.md`, `sdk-verifier.md`, `silent-failure-hunter.md`

Pattern: Each agent only has the **minimum tools it needs** for its role. No agent has global access.

#### skills/ — 14 Composable Modules with Hooks

Skills can have **side effects via hooks** — not just passive knowledge:

```
.claude/skills/save-task-list/
├── index.md          # main skill definition
└── hooks/
    └── verify-task-list.sh   # runs at SessionStart
```

This is the "skills with lifecycle integration" pattern — our `skills/` directory currently has no hooks.

#### rules/ — 11 Domain Rule Files

Instead of one giant AGENTS.md, Archon splits rules by domain:

`adapters.md`, `cli.md`, `database.md`, `isolation.md`, `isolation-patterns.md`, `orchestrator.md`, `server-api.md`, `testing.md`, `web-frontend.md`, `workflows.md`, `dx-quirks.md`

Agents load **only the rules relevant to their task** — reduces noise, improves focus.

#### commands/ — Executable Workflow Prompts

These are agent-runnable `.md` files that define structured workflows:

| Command | What It Does |
|---------|-------------|
| `prime.md` | Context injection at session start (memory-bridge equivalent) |
| `prime-backend.md` | Backend-specific context injection |
| `prime-frontend.md` | Frontend-specific context injection |
| `handoff.md` | **Session closing + state handover** ← directly solves our harness gap |
| `plan-feature.md` | Structured feature planning workflow |
| `commit.md` | AI-assisted git commit |
| `validate.md` | Pre-PR validation checklist |
| `review-doc.md` | Documentation review workflow |
| `create-command.md` | Meta: create a new command |

**`handoff.md` is the single most actionable pattern for us.**

#### PRPs — Prompt Response Patterns

Structured templates for recurring prompt types — ensures consistent AI outputs across tasks. Similar to our skills but focused on prompt/output format rather than procedure.

### `.archon/` — Runtime State & Workflow Templates

```
.archon/
├── config.yaml           # baseBranch: dev, docs path, etc.
├── workflows/defaults/   # YAML workflow templates
└── commands/             # Runtime-specific commands
```

`.archon/config.yaml` equivalent for us: our `team-config.yaml`.

---

## Fit Analysis: What We Adopt

### Pattern Fit Table

| Pattern | Source | Verdict | Priority | Notes |
|---------|--------|---------|----------|-------|
| `handoff.md` command | `.claude/commands/` | **ADOPT NOW** | P0 | Directly solves our session-close harness gap |
| `prime.md` command | `.claude/commands/` | **ADOPT NOW** | P0 | Memory-bridge equivalent without SDK |
| Domain rule files (`.claude/rules/`) | `.claude/rules/*.md` | **ADOPT** | P1 | Split AGENTS.md → domain-specific files |
| PRPs (Prompt Response Patterns) | `.claude/PRPs/` | **ADOPT** | P1 | Add to `skills/` as structured prompt templates |
| Named agent definitions | `.claude/agents/*.md` | **ADOPT** | P1 | Currently inline in AGENTS.md; externalize |
| Skills with lifecycle hooks | `.claude/skills/*/hooks/` | **ADOPT** | P2 | Needs PowerShell hook infrastructure |
| Lifecycle hook settings.json | `.claude/settings.json` | **PHASE 2** | P2 | Requires Copilot SDK (mirrors exactly) |
| YAML workflow DAGs | `.archon/workflows/` | **PHASE 2** | P3 | Powerful for multi-step tasks, high complexity |
| `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` | settings.json env | **MONITOR** | — | Platform-specific; watch for Copilot equivalent |
| Git worktree isolation | `packages/isolation` | **SKIP** | — | Not relevant for personal assistant |
| Multi-platform adapters | `packages/adapters` | **SKIP** | — | Single platform (Copilot CLI) |
| Full deployment (Docker/Web UI) | `Dockerfile`, `packages/web` | **SKIP** | — | Personal tool, not infrastructure product |

### P0 Adoption: `handoff.md` + `prime.md` Commands

These two commands, translated to our environment, address the two biggest recurring gaps:

**Gap 1 — Session close:** James forgets/skips the closing checklist when Gerhard types `/exit`  
**Fix:** Create `tools/commands/handoff.md` — a structured prompt James executes before closing

**Gap 2 — Context loss:** After session compaction, James loses project context  
**Fix:** Create `tools/commands/prime.md` — a memory injection prompt James can run on demand

```markdown
# tools/commands/handoff.md
## Session Handoff Protocol

Execute these steps before closing:
1. Select-String "cc:WIP" <WORKSPACE_ROOT>\plans\*.md
2. Run wiki_lint.py — fix any issues before closing
3. Write Daily Note entry (agent, done, files changed)
4. Append MEMORY.md with new permanent facts
5. Run notes_summarizer.py --dream
6. Run wiki_graph.py --build (if wiki changed)
7. Confirm: "Session closed cleanly ✅"
```

### P1 Adoption: Domain Rule Files

Archon's insight: one big rules file creates noise. Domain-specific files let agents load only what's relevant.

**Proposed split of our AGENTS.md:**
```
<WORKSPACE_ROOT>\.claude\rules\
├── orchestration.md    # CAO rules: delegation, recursive prevention, effort routing
├── memory.md           # Memory system: MEMORY.md, USER.md, wiki, fences
├── wiki.md             # Wiki protocol: schema, creation, lint, backlinks
├── daily-notes.md      # Daily note logging rules
└── session-lifecycle.md # Opening/closing checklist
```

AGENTS.md becomes a lightweight index that references these files.

---

## CLAUDE.md Engineering Principles Worth Noting

Archon's CLAUDE.md encodes engineering principles that Gerhard's team can adopt:

| Principle | Archon's Formulation | Relevance |
|-----------|---------------------|-----------|
| **KISS** | No unnecessary abstraction | James should prefer simple PowerShell over complex Python when both work |
| **Fail Fast** | Explicit errors, no silent failures | Our tools should throw, not swallow errors |
| **Determinism** | Same input → same output | Wiki creation should follow schema exactly every time |
| **Reversibility** | Rollback-first thinking | Before modifying MEMORY.md, consider reversibility |
| **Type Safety** | Zod schema validation | Our wiki frontmatter schema (`_schema.md`) mirrors this |

---

## Cross-Reference: Archon vs Previous Research

### vs. claude-code-harness

| Aspect | claude-code-harness | Archon |
|--------|---------------------|--------|
| **Focus** | Session hooks + memory bridge | Full workflow orchestration platform |
| **Complexity** | Minimal harness | Full product (10 packages) |
| **Memory** | Shell script re-injection | `.claude/rules/` + `prime.md` command |
| **Session close** | WIP-check hook (planned) | `handoff.md` command (implemented) |
| **Agent defs** | Inline YAML frontmatter | Separate `.md` per agent |
| **Platform** | Claude Code | Claude Code (but patterns are universal) |

**Verdict:** Archon's `.claude/` structure is the **production-quality version** of what claude-code-harness starts. Both are for Claude Code, but Archon shows the mature end state.

### vs. GitHub Copilot SDK

| Aspect | Archon (`.claude/settings.json`) | Copilot SDK |
|--------|----------------------------------|-------------|
| `SessionStart` hook | ✅ | ✅ `on_session_start` |
| `UserPromptSubmit` hook | ✅ | ✅ `onUserPromptSubmitted` |
| `Stop` hook | ✅ | ✅ `on_session_end` |
| Named agents | ✅ `.claude/agents/` | ✅ `customAgents[]` |
| Skills | ✅ `.claude/skills/` | ✅ SDK Skills |

**Archon is the reference implementation showing what Copilot SDK Phase 2 integration should look like.**

---

## Adoption Roadmap

### Phase 0 — Immediate (no infrastructure needed)

- [ ] Create `tools/commands/handoff.md` — session close protocol as a prompt James reads
- [ ] Create `tools/commands/prime.md` — memory injection prompt for post-compaction recovery
- [ ] Add both to Session Closing Checklist in AGENTS.md as Step 0 reference

### Phase 1 — Domain Rules Split

- [ ] Create `.claude/rules/` directory with 5 domain rule files
- [ ] Refactor AGENTS.md to be lightweight index referencing rule files
- [ ] Extract PRPs for recurring task types (wiki creation, research synthesis, code review)

### Phase 2 — Skills with Hooks (requires SDK)

- [ ] `skills/daily-notes/hooks/session-end.ps1` — auto-runs on Stop hook
- [ ] `skills/wiki/hooks/session-start.ps1` — re-injects wiki index at start
- [ ] Map Archon's `settings.json` → Copilot SDK config when SDK is stable

### Phase 3 — YAML Workflows (long-term)

- [ ] Define recurring complex tasks as workflow YAMLs (e.g., "research + wiki + daily note" pipeline)
- [ ] Use Archon's workflow templates as reference for structure

---

## Source Files (Key)

| File | Size | Relevance |
|------|------|-----------|
| `CLAUDE.md` | 40KB | Engineering bible — principles + commands |
| `.claude/settings.json` | — | Lifecycle hooks configuration |
| `.claude/agents/` | 13 files | Named agent role definitions |
| `.claude/skills/` | 14 modules | Composable skill modules with hooks |
| `.claude/rules/` | 11 files | Domain-specific rule files |
| `.claude/commands/handoff.md` | — | Session close workflow |
| `.claude/commands/prime*.md` | 5 files | Context injection commands |
| `.archon/workflows/defaults/` | 17 files | YAML workflow templates |
