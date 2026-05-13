---
# ── Identity ──────────────────────────────────────────────
id: github-copilot-hooks
type: research
title: "GitHub Copilot Hooks"
tags: [copilot, hooks, cli, cloud-agent, policy, automation]
domain: meta

# ── Project Context ───────────────────────────────────────
is_project: false
project:

# ── Lifecycle / Validity ──────────────────────────────────
status: active
is_valid: true
valid_from: 2026-04-15
valid_to:
expired_at:
superseded_by:

# ── Quality / Confidence ──────────────────────────────────
confidence: high
reviewed_by: Researcher
review_date: 2026-04-15

# ── Provenance ────────────────────────────────────────────
created: 2026-04-15
created_by: Researcher
last_modified: 2026-04-15
modified_by: Researcher
source: https://docs.github.com/en/copilot/reference/hooks-configuration
ingest_session: [[log#2026-04-15-research-github-copilot-hooks]]

# ── Knowledge Graph ───────────────────────────────────────
relates_to:
  - "[[github-copilot-sdk]]"
  - "[[github-copilot-rubber-duck]]"
  - "[[memory-session-lifecycle]]"
  - "[[agent-team-setup]]"
  - "[[claude-code-harness]]"
depends_on: []

description: "GitHub Copilot Hooks are repository-scoped, JSON-configured shell command hooks for Copilot CLI and Copilot cloud agent; they are strong for deterministic policy and audit automation but materially narrower than SDK callbacks."
---

## Overview

GitHub Copilot Hooks are currently a **repository-scoped shell automation layer** for Copilot CLI and Copilot cloud agent. They are configured in `.github/hooks/*.json`, execute synchronously at fixed lifecycle points, and are best suited for deterministic controls such as policy enforcement, audit logging, lightweight cleanup, and simple workflow automation. They are **not** equivalent to the GitHub Copilot SDK hooks: product hooks are external shell commands with very limited writable outputs, while SDK hooks are in-process callbacks that can inject context and reshape session behavior much more deeply.

---

## What Copilot Hooks are today

Official GitHub documentation describes hooks as custom shell commands that run at strategic points in an agent workflow. The core model is:

1. Copilot hits a lifecycle event.
2. It sends structured JSON to the hook over `stdin`.
3. The hook script runs locally or in the agent environment.
4. Copilot optionally consumes a small JSON response.

For CLI and cloud agent, hooks are configured per repository, not per prompt. This makes them good for **repeatable operational policy** and poor for ad-hoc conversational steering.

---

## Where hooks run

### Copilot CLI

- Hooks are loaded from `.github/hooks/*.json` in the **current working directory**.
- They run on the **user's local machine**.
- On Windows, the relevant command key is usually `powershell`.

### Copilot cloud agent

- Hooks must exist in `.github/hooks/` on the repository's **default branch**.
- They run inside the cloud agent's **GitHub Actions-powered ephemeral development environment**.
- This makes them suitable for repository policy and automation that should travel with the repo.

### VS Code (related but not identical)

VS Code also documents hooks in Preview, but it exposes a broader and slightly different surface, including extra events such as `PreCompact`, `SubagentStart`, `SubagentStop`, and `Stop`. Treat VS Code hooks as the **same idea, but not the same contract** as CLI/cloud-agent hooks.

---

## Configuration model

CLI and cloud-agent hooks use repository JSON files in `.github/hooks/`:

```json
{
  "version": 1,
  "hooks": {
    "sessionStart": [
      {
        "type": "command",
        "bash": "./scripts/session-start.sh",
        "powershell": "./scripts/session-start.ps1",
        "cwd": ".github/hooks",
        "env": {
          "LOG_LEVEL": "INFO"
        },
        "timeoutSec": 10
      }
    ]
  }
}
```

Important properties:

- `version: 1` is required.
- Each event maps to an **array** of hook commands.
- Each command uses `type: "command"`.
- Commands can be platform-specific via `bash` and `powershell`.
- `cwd` is relative to the repository root.
- `env` merges additional environment variables into the process environment.
- `timeoutSec` defaults to `30`.

Multiple hooks of the same type execute **in order**. Because hooks are synchronous, slow scripts directly slow down the agent.

---

## Hook and event model

### Core CLI / cloud-agent events

| Event | Confirmed input highlights | What the hook can really do today |
|------|-----------------------------|-----------------------------------|
| `sessionStart` | `source`, `initialPrompt` | Initialize or log; output ignored |
| `sessionEnd` | `reason` = `complete \| error \| abort \| timeout \| user_exit` | Cleanup or log; output ignored |
| `userPromptSubmitted` | `prompt` | Audit/log only; prompt rewriting is **not** supported in customer hooks |
| `preToolUse` | `toolName`, `toolArgs` JSON string | Main control point; can deny a tool call |
| `postToolUse` | `toolResult` with `success \| failure \| denied` | Log or trigger side effects; result rewriting not supported |
| `errorOccurred` | `error.message`, `error.name`, `error.stack` | Log or notify; output ignored |

### Important nuance

`preToolUse` is the only documented hook where customer output meaningfully changes runtime behavior today. Even there, the official reference says `permissionDecision` supports `allow`, `deny`, and `ask`, but **only `deny` is currently processed**. That makes hooks more useful for **blocking** than for rich interactive approval flows.

### Documentation ambiguity

The concept page for cloud-agent hooks also lists `agentStop` and `subagentStop`, while the reference and tutorial material focus on the six events above. VS Code Preview documents yet another event set with different casing. The safest reading is:

- the six-event model above is the stable baseline for CLI/cloud-agent work today
- extra events are surface-specific or less mature
- do not assume event names or capabilities transfer 1:1 across Copilot surfaces

---

## Common usage patterns

Official docs and tutorials consistently point to these patterns:

1. **Policy enforcement**
   - deny dangerous shell commands in `preToolUse`
   - constrain where edits may happen
   - require human escalation for risky operations

2. **Audit logging**
   - log session starts and ends
   - log prompts or prompt metadata
   - log attempted tool calls and deny decisions

3. **Lightweight workflow automation**
   - show a repository policy banner on session start
   - append JSONL audit entries
   - run follow-up scripts after tool completion

4. **Notifications / integrations**
   - send alerts when a tool fails
   - forward events to a centralized logging or observability system

5. **Quality and compliance gates**
   - block obviously unsafe commands
   - redact secrets before writing logs
   - ensure repository-local governance follows the codebase

---

## Security and operational considerations

The official docs are clear on the main risks:

- hooks run on **untrusted input** and must validate/sanitize it
- shell escaping matters; badly written hooks can introduce command injection
- hooks must **not log secrets**
- external network calls add latency and may expose data
- hooks are synchronous and therefore on the critical path
- timeouts and file permissions need to be set deliberately

Operationally, GitHub recommends keeping hooks fast; the concept docs explicitly say to keep execution under roughly **5 seconds when possible**. Long-running hooks degrade the agent experience because they block forward progress.

There is also **no built-in secret redaction** in the CLI tutorial examples. GitHub shows redaction as user-authored script logic, not as a platform guarantee.

---

## Limitations

The current hooks model is useful, but narrower than it first appears:

1. **Mostly side effects, not deep control**
   - `sessionStart`, `sessionEnd`, `userPromptSubmitted`, `postToolUse`, and `errorOccurred` are effectively side-effect hooks.
   - They are good for logging and cleanup, not for reshaping the conversation.

2. **No true memory/context injection path in product hooks**
   - The official CLI/cloud-agent docs do not show a supported way to inject additional session context or rewrite prompts/results via customer hooks.

3. **No native equivalent to our checkpoint lifecycle**
   - Hooks cover start/end and tool boundaries, but not our `checkpoint-session.ps1` pattern for mid-session durable persistence.

4. **Surface inconsistency**
   - CLI/cloud-agent docs and VS Code Preview docs do not expose the exact same events or naming.

5. **Shell-first ergonomics**
   - Powerful for ops teams, but less expressive than an in-process SDK callback model.

---

## Comparison with our current local lifecycle

Current workspace state:

- we have **no** `.github/hooks/` configuration in this repository today
- our lifecycle is currently **tool-driven**
- key entry points are `tools/session/start-session.ps1`, `tools/session/checkpoint-session.ps1`, and `tools/session/close-session.ps1`

### Fit analysis

| Need in this workspace | Current approach | Copilot Hooks fit |
|------|------------------|-------------------|
| Start-of-session guardrails | `start-session.ps1` | **Partial fit** — `sessionStart` can automate lightweight repo-scoped startup actions |
| Mid-session persistence | `checkpoint-session.ps1` | **No native fit** in current CLI/cloud-agent hooks |
| End-of-session cleanup | `close-session.ps1` | **Good fit** for lightweight cleanup/logging, but not for our full close routine |
| Tool safety gates | Manual discipline + instructions | **Strong fit** via `preToolUse` deny rules |
| Audit trail | Ad-hoc / file-based | **Strong fit** via session/prompt/tool hooks |
| Memory injection | Manual file reading | **Poor fit** in product hooks today |

### Practical conclusion

Copilot Hooks could reduce some manual glue in our local setup, especially for:

- startup banners
- prompt/tool audit logs
- hard deny rules for dangerous tool usage
- small session-end cleanup tasks

They would **not** replace our current lifecycle architecture for:

- memory preflight
- checkpoint-based crash resistance
- durable memory reconciliation
- knowledge review orchestration

---

## Comparison with the GitHub Copilot SDK page

The existing `[[github-copilot-sdk]]` page describes **SDK hooks**, which are a different class of mechanism.

| Dimension | Product hooks (`.github/hooks/*.json`) | SDK hooks |
|----------|-----------------------------------------|-----------|
| Runtime model | External shell commands | In-process callbacks |
| Main target | CLI and cloud-agent repository automation | Programmable Copilot app/session runtime |
| Config style | JSON + shell scripts | Language API (Python/JS/Go/.NET/Java) |
| Best at | Policy, audit, cleanup, notifications | Context injection, prompt rewriting, tool/result shaping |
| Output power | Mostly ignored; `preToolUse` denial is the key writable path | Richer mutation of session behavior |
| Fit for our memory bridge | Weak | Strong |

This distinction matters for planning:

- **Use product hooks** if we want deterministic repository governance now.
- **Use the SDK** if we want a future James runtime with automatic `MEMORY.md` / `USER.md` injection and deeper lifecycle control.

---

## Recommendation

Adopt Copilot Hooks only for **narrow, deterministic controls**:

1. repository-local policy banners
2. prompt/tool/session audit logging with redaction
3. `preToolUse` deny rules for obviously unsafe commands
4. lightweight session-end housekeeping

Do **not** treat product hooks as a replacement for our memory lifecycle or as a substitute for the SDK. For this workspace, the right split is:

- **Hooks** = repo policy and audit
- **Current session scripts** = start/checkpoint/close durability
- **SDK (future)** = real memory/context bridge

---

## Sources

- https://docs.github.com/en/copilot/concepts/agents/cloud-agent/about-hooks
- https://docs.github.com/en/copilot/reference/hooks-configuration
- https://docs.github.com/copilot/how-tos/copilot-cli/use-hooks
- https://docs.github.com/copilot/tutorials/copilot-cli-hooks
- https://docs.github.com/en/copilot/concepts/agents/cloud-agent/about-cloud-agent
- https://github.com/github/copilot-sdk/blob/main/docs/features/hooks.md
- https://code.visualstudio.com/docs/copilot/customization/hooks
