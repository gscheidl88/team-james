# Delegation Rules

Quick-reference injection for James when orchestrating sub-agents.
Full policy lives in `AGENTS.md` under "Sub-Agent Orchestration Rules".

---

## Core Rules

1. **Only James spawns agents.** Sub-agents (Analyst, Developer, Researcher, QA, Magnus) are leaf-nodes — they never spawn further agents. If a sub-agent needs another agent, it returns the request to James.

2. **Every spawn has a task descriptor** with: `task_id`, `goal`, `dod`, `verification_plan`, `agent_role`, `requested_tools`, `timeout_hint`, `skill_context`, `escalation_path`.

3. **Skill injection is mandatory.** Read `skills/<id>/SKILL.md` and paste under `[SKILL CONTEXT]` in the prompt before spawning. Sub-agents do not read skill files themselves.

4. **First checkpoint is planned before spawn** — never fire-and-forget.

## Model Routing

| Complexity | agent_type | model |
|------------|-----------|-------|
| Lookup / simple research | `explore` | haiku |
| Code / multi-file analysis | `general-purpose` | sonnet |
| Code review | `code-review` | sonnet |
| Architecture / synthesis | `general-purpose` | `claude-opus-4.5` |

## Checkpoint Cadence

| Complexity | First check | Stall threshold |
|------------|-------------|-----------------|
| low | 15 s | 90 s |
| medium | 30 s | 180 s |
| high | 60 s | 240 s |

## Escalation Path

1. Nudge once, request status.
2. If still stalled: retry, retry with stronger model, or absorb directly.
3. Document outcome in plan (`cc:完了` or `blocked (reason)`).
