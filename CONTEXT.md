# CONTEXT.md — Harness Glossary & Entry Point

> Pointer-style orientation guide for this workspace.
> This file defines shared vocabulary and links to canonical authorities.
> It does **not** reproduce or supersede `AGENTS.md`, `memory/MEMORY.md`, or any procedures file.

---

## Purpose

When a prompt, task descriptor, or skill doc uses harness-specific terms, this file is the first
reference. One definition here; no copies elsewhere.

---

## Shared Terms

| Term | Definition |
|------|-----------|
| **CAO** | Chief Agent Officer — James (GitHub Copilot). The only orchestrator that spawns sub-agents and owns quality sign-off. See `AGENTS.md` for the full role definition. |
| **leaf-agent** | A specialist sub-agent spawned by the CAO (Analyst, Developer, Researcher, QA). Leaf-agents are execution nodes only — they do not spawn further agents. |
| **delegation** | The act of the CAO handing a scoped task to a leaf-agent via the `task` tool. The full delegation protocol lives in `tools/agents/delegate.py`. |
| **permission boundary** | The set of tools and capabilities a given agent type may use. Declared in `config/agent-permissions.yaml`; enforced at runtime by `tools/agents/preflight_guard.py`. |
| **trace** | The append-only record of spawn/complete/failed/blocked events written to `.agent-trace.jsonl`. Tooling: `tools/agents/agent_trace.py` and `tools/agents/agent_review.py`. |
| **DoD** | Definition of Done — the measurable acceptance condition stated in a task descriptor. A task is not complete until DoD is verified and the result is persistent. |
| **skill** | A reusable, packaged operating procedure under `skills/`. Canonical packaging: `SKILL.md` (human-readable) + `skill.yaml` (machine manifest). Contract: `skills/_contract.md`. |
| **memory fence** | The `<memory-context>` XML wrapper James uses when injecting `MEMORY.md` or `USER.md` into a prompt to signal it is background, not new user input. |
| **model routing** | Policy for selecting which model tier to use per task complexity and type. Source of truth: `config/model-routing.yaml`. |
| **WIP marker** | `cc:WIP` in a plan file flags an in-progress task. James checks for open WIP markers before session close. |
| **hypothesis ledger** | Structured tracking of active hypotheses with confidence, evidence, contradiction, and next-test fields. Required for medium+ analysis tasks. |

---

## Canonical Authorities

| Topic | File |
|-------|------|
| Full operating contract and agent roles | `AGENTS.md` |
| Persistent facts and workspace decisions | `memory/MEMORY.md` |
| User profile and preferences | `memory/USER.md` |
| Model selection policy | `config/model-routing.yaml` |
| Agent permission policy | `config/agent-permissions.yaml` |
| Skill packaging contract | `skills/_contract.md` |
| Delegation protocol | `tools/agents/delegate.py` |
| Failure taxonomy | `config/failure-taxonomy.yaml` |
| Wiki schema | `wiki/_schema.md` |
| Session close and handoff | `tools/commands/handoff.md` |
| Session context recovery | `tools/commands/prime.md` |

---

## What Belongs Here vs. AGENTS.md

`AGENTS.md` is the **operating contract** — it governs behavior, workflow, and standards.
`CONTEXT.md` is the **glossary and pointer index** — it defines terms and routes readers to the right
canonical source. Do not add operating rules here; add them to `AGENTS.md` or the relevant config file.
