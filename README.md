[![CI](https://github.com/gscheidl88/team-james/actions/workflows/ci.yml/badge.svg)](https://github.com/gscheidl88/team-james/actions/workflows/ci.yml)
[![Lint](https://github.com/gscheidl88/team-james/actions/workflows/lint.yml/badge.svg)](https://github.com/gscheidl88/team-james/actions/workflows/lint.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.1.0--alpha-blue.svg)](CHANGELOG.md)

# Team_James — Personal AI Agent Framework

> A production-tested, local-first agent team for GitHub Copilot CLI.  
> Orchestration · Memory · Skills · Knowledge — all in your repo.

---

## What is This?

Team_James is a **personal agent framework** built on top of [GitHub Copilot CLI](https://docs.github.com/en/copilot/using-github-copilot/using-github-copilot-in-the-command-line).

Instead of a single AI assistant, you get a **team** of specialized agents that:

- Delegate work through a Chief Agent Officer (James)
- Share a layered memory system (facts, user profile, skills, wiki)
- Follow a proven orchestration policy (task metadata, model routing, verification)
- Build institutional knowledge in a structured wiki

Everything runs **locally** — no external services required.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  GitHub Copilot CLI                                                         │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  James — Chief Agent Officer (CAO)                                     │ │
│  │  • Reads: AGENTS.md · memory/MEMORY.md · memory/USER.md              │ │
│  │  • Orchestrates leaf agents via task tool                              │ │
│  │  • Enforces: skill injection · DoD · checkpoint cadence              │ │
│  └──────────┬───────────────────────────────────────────────────────────┘ │
│             │ delegates to                                                  │
│  ┌──────────▼──────────────────────────────────────────────────────────┐  │
│  │  Leaf Agents (never spawn sub-agents)                               │  │
│  │  Analyst · Developer · Researcher · QA · Domain Specialist         │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘

Memory Layers:
  memory/MEMORY.md     ← persistent facts (gitignored, yours only)
  memory/USER.md       ← your profile & preferences (gitignored)
  skills/*/SKILL.md    ← injectable procedure library
  wiki/*.md            ← deep knowledge base (Karpathy-pattern)
```

---

## Repository Structure

```
Team_James/
├── .github/
│   ├── ISSUE_TEMPLATE/           # Bug, feature, and setup-help templates
│   ├── workflows/                # GitHub Actions for lint and eval CI
│   ├── pull_request_template.md
│   └── copilot-instructions.md   # Copilot-specific system prompt
├── agents/                        # Agent persona definitions
│   ├── chief-agent.md             # James — CAO
│   ├── analyst-agent.md
│   ├── developer-agent.md
│   ├── researcher-agent.md
│   ├── qa-agent.md
│   └── investment-analyst-agent.md  # Domain specialist example
├── skills/                        # Injectable procedure library
│   ├── _contract.md               # Skill authoring standard
│   ├── orchestration/             # SKILL.md + skill.yaml
│   ├── data-analysis/
│   ├── research-strategy/
│   ├── software-development/
│   └── ...                        # 15 skills total
├── rules/                         # Condensed injectable rule files
│   ├── delegation.md
│   ├── memory.md
│   └── session.md
├── config/
│   └── model-routing.yaml         # Model selection policy
├── wiki/                          # Deep knowledge layer
│   ├── _schema.md                 # Frontmatter standard
│   ├── index.md                   # Content catalog
│   └── *.md                       # 40+ research & architecture pages
├── tools/                         # Python automation tools
│   ├── wiki/wiki_lint.py          # Wiki + skill lint
│   ├── notes/notes_summarizer.py  # Dream cycle / memory consolidation
│   ├── agents/skill_candidates.py # Auto-detect skill candidates
│   └── ...
├── memory/
│   ├── USER.example.md            # → copy to USER.md, personalize
│   └── MEMORY.example.md          # → copy to MEMORY.md
├── plans/
│   └── _template-complex-task.md  # Plan template with phase table
├── evals/                         # Evaluation suites for key workflows
├── AGENTS.md                      # Team constitution (read every session)
├── CHANGELOG.md
├── CODE_OF_CONDUCT.md
├── setup.ps1                      # Windows bootstrap for local path placeholders
├── setup.sh                       # POSIX bootstrap for local path placeholders
└── team-config.yaml               # Agent roster + skill registry
```

---

## Quick Start

### 1. Prerequisites

- [GitHub Copilot CLI](https://docs.github.com/en/copilot/using-github-copilot/using-github-copilot-in-the-command-line) installed and authenticated
- [uv](https://docs.astral.sh/uv/) for Python tooling

### 2. Clone and configure

```bash
git clone https://github.com/gscheidl88/team-james
cd team-james

# Create your personal memory files (gitignored)
cp memory/USER.example.md memory/USER.md
cp memory/MEMORY.example.md memory/MEMORY.md
# → Edit both files with your personal details
```

### 3. Run the setup script

The framework uses `<WORKSPACE_ROOT>` placeholders in several operational files. Run one setup command once after cloning:

```powershell
.\setup.ps1 -WorkspaceRoot "D:\your-workspace"
```

```bash
./setup.sh /your/workspace/path
```

The setup script:

- replaces `<WORKSPACE_ROOT>` placeholders in tracked framework files
- creates `memory/USER.md` and `memory/MEMORY.md` from the example templates if they do not exist
- keeps the public templates untouched in Git history

Your local working tree will contain personalized path changes after setup. That is expected for a local-first workspace fork.

### 4. Verify

```bash
uv run tools/wiki/wiki_lint.py
```

Should report: `Total issues: 0` (wiki) and skill sections status.

### 5. Start a session

Open GitHub Copilot CLI in your workspace. James reads `AGENTS.md`, `memory/MEMORY.md`, and `memory/USER.md` at startup. Tell him what you need.

---

## Key Concepts

### James — Chief Agent Officer

James is the always-active orchestrator. He:
- Reads team memory every session
- Delegates to specialist leaf agents
- Enforces task metadata, DoD, and verification
- Manages the skill library and wiki knowledge base

### Skill Library

Skills are injectable operating procedures stored in `skills/<id>/`:
- `SKILL.md` — human-readable procedure (injected into sub-agent prompts)
- `skill.yaml` — machine-readable manifest for routing and tooling

Every skill requires: `## When to Use`, `## Anti-patterns`, `## Checklist`.

### Wiki Knowledge Layer

Based on the [Karpathy wiki pattern](wiki/karpathy-llm-wiki-pattern.md) — a local knowledge base that compounds over time:
- Research briefs, ADRs, analysis results
- Validated by `wiki_lint.py` (dead links, missing sections, stale validity)
- Full frontmatter schema in `wiki/_schema.md`

### Memory System

Three persistent layers:
1. `memory/MEMORY.md` — factual knowledge (gitignored)
2. `memory/USER.md` — your profile and preferences (gitignored)
3. `skills/` — procedural knowledge (committed)

Optional: [Mnemosyne](wiki/mnemosyne-memory.md) for semantic vector recall on top of MEMORY.md.

### Model Routing

`config/model-routing.yaml` defines model selection policy:
- trivial lookups → economy model
- standard tasks → standard model
- complex/architecture → premium model

Cross-family verification: Claude primary → GPT verifier (and vice versa).

---

## Tooling

All tools use [uv](https://docs.astral.sh/uv/) with inline dependencies — no venv setup required.

| Tool | Command |
|------|---------|
| Wiki + skill lint | `uv run tools/wiki/wiki_lint.py` |
| Memory dream cycle | `uv run tools/notes/notes_summarizer.py --dream` |
| Skill candidate detection | `uv run tools/agents/skill_candidates.py --print` |
| Model router | `uv run tools/routing/model_router.py --complexity complex --task-type code` |
| CAO task helper | `uv run tools/agents/cao_helper.py prepare --help` |

---

## Customization

### Adding a domain specialist agent

1. Copy `agents/investment-analyst-agent.md` → `agents/<your-domain>-agent.md`
2. Adapt the persona, triggers, and capabilities
3. Add to `team-config.yaml` under `agents:`
4. Create a matching skill in `skills/<your-domain>/`

### Adding skills

1. Create `skills/<skill-id>/SKILL.md` and `skills/<skill-id>/skill.yaml`
2. Follow the contract in `skills/_contract.md`
3. Include `## Anti-patterns` and `## Checklist` (enforced by lint)
4. Add to `team-config.yaml` under `skills:`

### Adding wiki pages

1. Create `wiki/<slug>.md` with full frontmatter (see `wiki/_schema.md`)
2. Include `## Overview` section (L1 requirement)
3. Update `wiki/index.md` and `wiki/log.md`
4. Run `uv run tools/wiki/wiki_lint.py` to verify

---

## Inspirations & Attributions

This framework synthesizes ideas from many open-source projects and research:

| Source | What we learned |
|--------|-----------------|
| [affaan-m/everything-claude-code](https://github.com/affaan-m/everything-claude-code) | Skill anti-patterns/checklists · plan multi-phase format · rules/ injection |
| [Karpathy LLM Wiki Pattern](https://twitter.com/karpathy) | Wiki-as-memory: compound knowledge base with L0/L1/L2 depth |
| [Hermes Agent (NousResearch)](https://github.com/nousresearch/hermes-agent) | Memory architecture · skill lifecycle · Autonomous Curator pattern |
| [OpenViking Context DB](https://github.com/OpenViking) | Memory/Resource/Skill taxonomy · L0/L1/L2 depth axis |
| [OpenClaw Auto-Dream v4.0](https://github.com/OpenClaw) | 5-layer cognitive memory · dream cycle · priority markers (⚠️ PERMANENT / 🔥 HIGH / 📌 PIN) |
| [Rowboat Labs](https://github.com/rowboatlabs/rowboat) | Memory Compounds · access-log importance scoring · Live Wiki Pages |
| [Archon Workflow Engine](https://github.com/coleam00/ottomator-agents) | `.claude/rules/` domain split · `handoff.md` + `prime.md` session commands |
| [softaworks Agent Toolkit](https://github.com/softaworks) | Session-handoff skill · writing skill · Marp presentation integration |
| [Reversa Framework](https://github.com/reversa-ai) | Confidence markers (🟢 CONFIRMED / 🟡 INFERRED / 🔴 GAP) · reverse engineering workflow |
| [Mnemosyne Memory](https://github.com/ttztony/mnemosyne-memory) | Semantic vector recall layer · sleep consolidation · ONNX fastembed |
| [AGI Project Analysis Patterns](wiki/agi-project-analysis-patterns.md) | Hierarchical decomposition · uncertainty handling · evaluation discipline |
| [Zep/Graphiti](https://github.com/getzep/graphiti) | Temporal knowledge graphs · `valid_to` / `expired_at` validity model |

The orchestration policy, memory fence convention, model routing, and skill injection pattern were developed independently during operational use — but many converge with the above projects.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md), [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md), and [CHANGELOG.md](CHANGELOG.md).

This is a personal framework — contributions are welcome as improvements to the methodology, tooling, and skill library. Domain-specific agents (like the investment analyst) are provided as examples of the pattern, not as production content.

---

## License

[MIT](LICENSE) — use freely, attribute appreciated.

---

## Security

See [SECURITY.md](SECURITY.md).

**Key rule:** `memory/USER.md` and `memory/MEMORY.md` are gitignored. Never commit them.  
All secrets go in `.env` files (also gitignored). See `skills/secrets-management/` for the convention.
