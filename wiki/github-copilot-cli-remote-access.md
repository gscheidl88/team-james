---
# ── Identity ──────────────────────────────────────────────
id: github-copilot-cli-remote-access
type: research
title: "GitHub Copilot CLI Remote Access"
tags: [copilot, cli, remote, github-mobile, github-com, preview]
domain: meta

# ── Project Context ───────────────────────────────────────
is_project: false
project:

# ── Lifecycle / Validity ──────────────────────────────────
status: active
is_valid: true
valid_from: 2026-04-19
valid_to:
expired_at:
superseded_by:

# ── Quality / Confidence ──────────────────────────────────
confidence: high
reviewed_by: James
review_date: 2026-04-19

# ── Provenance ────────────────────────────────────────────
created: 2026-04-19
created_by: James
last_modified: 2026-04-19
modified_by: James
source: https://docs.github.com/en/copilot/concepts/agents/copilot-cli/about-remote-access
ingest_session: [[log#2026-04-19-research-github-copilot-cli-remote-access-and-rubber-duck]]

# ── Knowledge Graph ───────────────────────────────────────
relates_to:
  - "[[github-copilot-rubber-duck]]"
  - "[[agent-orchestration-policy]]"
  - "[[github-copilot-sdk]]"
depends_on: []

description: "GitHub Copilot CLI `/remote` enables preview-stage steering of a running local CLI session from GitHub.com and GitHub Mobile; execution stays local, capabilities are narrow, and it is not a general-purpose messaging bridge."
---

## Overview

`/remote` in GitHub Copilot CLI is a **session steering feature**, not a remote execution feature. It lets you view and steer a running local CLI session from **GitHub.com** or **GitHub Mobile**, while the actual tools, shell commands, file changes, and agent execution remain on the original machine. For our harness, this is useful as a lightweight control plane for long-running sessions, but it is not a native chat-bot transport and does not turn Copilot CLI into a generic Telegram-style bidirectional worker.

---

## What `/remote` is

GitHub documents `/remote` as a way to:

- monitor a running Copilot CLI session
- reply to permission requests
- answer agent questions
- approve or reject plans
- submit additional prompts
- switch modes remotely
- cancel the current operation

The slash command itself is:

```text
/remote
```

Remote access can also be enabled:

- at startup with `copilot --remote`
- permanently for interactive sessions with:

```json
{
  "remoteSessions": true
}
```

Remote access is disabled by default and can be suppressed with `--no-remote`.

---

## Core operating model

The most important design fact is this:

**The session continues to run locally.**

GitHub's own docs say that when remote access is enabled:

- session events are sent from the local machine to GitHub
- remote commands are polled by Copilot CLI from GitHub
- those commands are injected into the local session
- the CLI, tools, shell, file access, and execution all remain on the original machine

That gives `/remote` a clear architecture:

### Control plane

GitHub.com / GitHub Mobile

- shows the session timeline
- displays permission requests
- accepts replies and follow-up prompts
- lets you steer the session

### Execution plane

Your local machine

- runs the Copilot CLI process
- executes tools and shell commands
- reads and writes files
- holds the actual working directory and local environment

### Practical interpretation

`/remote` is closer to **remote steering of a local agent** than to "move my session into the cloud."

---

## Exact prerequisites and boundaries

GitHub currently documents these requirements:

1. **Interactive session only**  
   `/remote` does not work for programmatic `--prompt` usage.

2. **GitHub-hosted repository required**  
   If the working directory is not a Git repo hosted on GitHub.com, the CLI shows:  
   `Remote session disabled: not in a GitHub repository`

3. **Machine must stay online**  
   If the machine sleeps or loses connectivity, remote steering becomes unavailable until it reconnects.

4. **Same GitHub account only**  
   The remote session is user-specific. Other users cannot access it.

5. **Preview status**  
   The feature is in public preview and subject to change.

6. **Mobile availability is limited**  
   GitHub documents mobile access through the latest beta release of GitHub Mobile.

---

## What you can and cannot do remotely

### Supported remotely

- approve or deny tool/path/URL permission requests
- answer clarifying questions
- approve or reject plans
- send additional prompts
- switch between session modes
- cancel the current operation

### Not supported remotely

GitHub explicitly notes that **slash commands are not currently available from the remote interface**.

That means you cannot rely on the remote surface for commands such as:

- `/allow-all`
- `/remote`
- `/experimental`
- `/mcp`
- `/agent`
- `/skills`

### Important implication

If your workflow depends on local configuration changes or feature flags, those must already be set on the local CLI side before remote steering becomes useful.

---

## Session lifecycle details

### How a remote session is accessed

When remote access is enabled, the CLI prints a GitHub URL in the form:

```text
https://github.com/OWNER/REPO/tasks/TASK_ID
```

The session also appears under recent agent sessions on:

- GitHub.com
- GitHub Mobile

### Resume behavior

If you shut down a remotely enabled session and later resume it:

- you must re-enable remote access
- or use `--remote` while resuming
- unless `remoteSessions` is enabled globally in config

### Keeping the machine awake

GitHub documents `/keep-alive` as the companion command for `/remote`:

- `on`
- `off`
- `busy`
- timed durations like `30m`, `8h`, `1d`

This is operationally important because `/remote` is useless if the local machine sleeps.

---

## Performance and operational limits

GitHub documents one especially important limit:

- the remote interface has a **60 MB session output limit**

If a long-running session emits too much output:

- the local terminal is unaffected
- the remote interface may become slower or less useful

### What that means for us

`/remote` is strongest for:

- review/approval checkpoints
- medium-duration long-running tasks
- "check in from phone" use

It is weaker for:

- extremely verbose sessions
- huge tool-output streams
- workflows that depend on raw terminal fidelity

---

## Security and trust model

GitHub's model is intentionally narrow:

- remote access does **not** grant direct shell access to the machine
- all agent actions still run through the local CLI session
- only the signed-in user with the same GitHub account can steer the session

This is a meaningful safety distinction:

- `/remote` is **not** remote desktop
- `/remote` is **not** SSH
- `/remote` is **not** a public bot API

It is a GitHub-mediated steering channel into an already-running local agent session.

---

## Fit for our team setup

### Strong fit

`/remote` is useful for our harness when:

- a long-running CLI task needs occasional approvals
- James is executing locally but Gerhard wants mobile continuity
- we want a clean split between local execution and remote steering
- a session runs into plan approvals or decision checkpoints while away from the desk

### Weak fit

`/remote` is a poor fit when we need:

- a general-purpose external messaging interface
- deterministic, scriptable remote orchestration
- multi-user shared steering of one CLI session
- slash-command-heavy control from the remote side

### Team interpretation

For us, `/remote` should be treated as a **continuity feature**, not as an orchestration backbone.

---

## Telegram implications

This is the key boundary for Gerhard's earlier question:

### What `/remote` does **not** mean

It does **not** mean Copilot CLI has a native remote bot protocol for arbitrary messaging platforms.

GitHub documents remote steering only for:

- GitHub.com
- GitHub Mobile

By contrast, GitHub documents **Slack**, **Teams**, **Linear**, **Azure Boards**, and **Jira** as official integrations for **Copilot cloud agent**, not Copilot CLI remote steering.

### Why Telegram is not a native fit

`/remote` depends on GitHub's own remote session transport:

- GitHub receives session events
- GitHub stores and presents them in its own UI
- Copilot CLI polls GitHub for replies

Telegram is not part of that documented control path.

### Practical consequence

A bidirectional Telegram workflow would require a **custom bridge**:

1. Telegram bot receives message
2. local service translates it to Copilot CLI / SDK input
3. local service captures session output
4. local service pushes summary or interaction back to Telegram

That is a custom transport layer, not an official `/remote` extension.

---

## Recommendation

### Recommended use

Use `/remote` for:

- mobile steering of active local sessions
- plan approvals on the go
- permission handling while away from the machine
- light monitoring of long-running tasks

### Do not use it as

- a Telegram replacement
- a shared team console
- a durable automation bus

### Best internal framing

Treat `/remote` as:

**local execution + GitHub-hosted steering**

not as:

**remote execution + arbitrary chat integration**

---

## Sources

1. GitHub Docs — *About remote access to GitHub Copilot CLI sessions*  
   https://docs.github.com/en/copilot/concepts/agents/copilot-cli/about-remote-access

2. GitHub Docs — *Steering a GitHub Copilot CLI session from another device*  
   https://docs.github.com/en/copilot/how-tos/copilot-cli/steer-remotely

3. GitHub Docs — *GitHub Copilot CLI command reference*  
   https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference

4. GitHub Docs — *About Copilot integrations*  
   https://docs.github.com/en/copilot/concepts/tools/about-copilot-integrations
