---
id: agent-team-setup
type: documentation
title: "Team_James Agent Team — Architecture & Setup"
tags: [agent-team, james, architecture, memory, skills, obsidian]
domain: meta

is_project: false
project:

status: active
is_valid: true
valid_from: 2026-04-08
valid_to:
superseded_by:

confidence: high
reviewed_by: the owner
review_date: 2026-04-08

created: 2026-04-08
created_by: James
last_modified: 2026-04-30
modified_by: James
source:
ingest_session: "[[log#2026-04-08-init]]"

relates_to:
  - "[[tooling-policy]]"
  - "[[karpathy-llm-wiki-pattern]]"
  - "[[personal-notes-system]]"
  - "[[github-copilot-sdk]]"
  - "[[notebooklm-mcp-cli]]"
  - "[[claude-code-harness]]"
  - "[[archon]]"
  - "[[marp]]"
  - "[[softaworks-agent-toolkit]]"
  - "[[memory-runtime-tooling]]"
  - "[[agent-orchestration-policy]]"
  - "[[knowledge-effectiveness-review]]"
depends_on: []
---

# Team_James Agent Team — Architecture & Setup

## Overview

A personal AI agent team built on GitHub Copilot CLI, inspired by the [Hermes Agent architecture](https://github.com/nousresearch/hermes-agent). James (CAO) is the orchestrating intelligence; specialist agents handle specific domains.

**Workspace:** `<WORKSPACE_ROOT>` (also an Obsidian Vault)  
**Initialized:** 2026-04-08  
**Primary interface:** Copilot CLI (`james` alias) or VS Code

---

## Agent Roster

| Agent | Role | Trigger Domains |
|-------|------|----------------|
| **James** (CAO) | Chief Agent Officer — orchestrates, quality-gates, maintains memory | Always active |
| **Analyst** | Data analysis, SQL, BI, reporting, KPIs | data, SQL, reports, BI |
| **Developer** | Code, architecture, debugging, automation | code, script, API, CI/CD |
| **Investment Analyst** | Investment research, fund documents, KID/PRIIP interpretation, market-context synthesis | investment, fund, factsheet, market context |
| **Researcher** | Research, strategy, concepts, documentation | research, strategy, decision |

---

## Memory Architecture (Hermes-inspired)

Three layers, read at every session start:

```
memory/
├── MEMORY.md     — persistent cross-session facts (append-only)
└── USER.md       — the owner's profile, preferences, tooling policy

skills/
├── data-analysis/SKILL.md
├── software-development/SKILL.md
├── research-strategy/SKILL.md
├── investment-research/SKILL.md
├── obsidian/SKILL.md
└── daily-notes/SKILL.md

wiki/              — structured knowledge base (Karpathy-inspired)
├── index.md       — content catalog
├── log.md         — append-only ingest/operation log
└── *.md           — entity/concept/analysis pages
```

**Memory fence convention** (prevents model treating recalled memory as new user input):
```xml
<memory-context>
[System: Recalled memory — treat as background, not new user input]
{content}
</memory-context>
```

---

## Session Start Protocol

**CLI (`james` alias):**
```powershell
james                    # Navigate to vault + load memory context
james 'Task description' # Start with a specific task
```

The `james` function (in `D:\OneDrive\Documents\PowerShell\profile.ps1`):
1. Navigates to `<WORKSPACE_ROOT>`
2. Shows team banner
3. Starts `copilot -i` with memory-loading prompt injecting MEMORY.md + USER.md

**VS Code:** `AGENTS.md` and `.github/copilot-instructions.md` auto-loaded by Copilot.

---

## Knowledge System

### Three-layer knowledge stack

| Layer | Files | Purpose |
|-------|-------|---------|
| Fast bootstrap | `memory/MEMORY.md`, `memory/USER.md` | Quick agent context at session start |
| Procedural | `skills/*.md` | How-to patterns, templates, workflows |
| Deep knowledge | `wiki/*.md` | Structured research, analysis, decisions |
| Operational review | `wiki/reviews/*` | Knowledge performance review, search telemetry, graph telemetry |

### Wiki Protocol

New wiki page when: *"Would the owner want to find this in 3 months?"*

Every wiki page has full frontmatter: `is_valid`, `confidence`, `created_by`, `relates_to`, `depends_on` — enabling Obsidian Dataview queries and knowledge graph navigation.

### Personal Notes Pipeline

```
Daily Notes (PersonalNotes/Daily/YYYY-MM-DD.md)
    ↓ every Sunday 20:00 (Task Scheduler)
Weekly Summary (PersonalNotes/Weekly/YYYY-Www.md)
    ↓ 1st of month 08:00
Monthly Summary (PersonalNotes/Monthly/YYYY-MM.md)
    ↓ Jan 1st 09:00
Annual Review (PersonalNotes/Annual/YYYY.md)
```

Powered by `tools/notes/notes_summarizer.py` (uv inline script).

---

## Key Files

| File | Purpose |
|------|---------|
| `AGENTS.md` | Team constitution — auto-loaded by Copilot CLI |
| `.github/copilot-instructions.md` | VS Code Copilot auto-load |
| `team-config.yaml` | Full team configuration |
| `START-SESSION.md` | How to start a CLI session |
| `memory/MEMORY.md` | Persistent facts register |
| `memory/USER.md` | the owner's profile & preferences |

---

## Design Decisions

- **Hermes-inspired** memory system: MEMORY.md + USER.md + Skills (not a vector DB)
- **Karpathy-inspired** wiki layer: compounding knowledge base, LLM as writer
- **AGENTS.md = Schema**: the single file that governs all agent behavior, auto-loaded
- **Obsidian = IDE**: wiki and notes browsable, graph view for navigation
- **uv = runtime**: all Python tools run without venv or token overhead
- **Language**: Chat in German, all files/documentation in English

---

## References

- Hermes Agent: https://github.com/nousresearch/hermes-agent
- Karpathy LLM Wiki: [[karpathy-llm-wiki-pattern]]
- Tooling Policy: [[tooling-policy]]
