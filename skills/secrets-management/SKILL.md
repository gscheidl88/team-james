---
name: secrets-management
description: "All secrets in ~/.gerhards-analyst/secrets/ — never in workspace; per-service env files; load via python-dotenv or PowerShell"
agent: James
tools_required: [powershell, python-dotenv]
wiki_ref: "[[tooling-policy]]"
version: "1.0"
---

# Skill: Secrets Management

All secrets (API keys, tokens, cookies, passwords) are stored in the **user-level secrets store** at `~\.gerhards-analyst\secrets\` — never in the workspace or any project directory.

This follows the same principle as `.ssh\`, `.aws\credentials`, and `.notebooklm-mcp-cli\` — OS-scoped, git-unreachable, user-only access.

## Overview

```
~\.gerhards-analyst\
└── secrets\
    ├── README.txt          ← index of what's stored here
    ├── <service>.env       ← per-service env file
    └── <service>.json      ← per-service JSON credentials
```

**Never** create `.env` files in `<WORKSPACE_ROOT>\` or any subdirectory.

---

## Convention: Per-Service Files

Each external service gets its own file:

| Service | File | Format |
|---------|------|--------|
| NotebookLM | `~/.notebooklm-mcp-cli/profiles/default/` | managed by `nlm` |
| OpenAI / Anthropic | `~/.gerhards-analyst/secrets/llm-keys.env` | KEY=VALUE |
| GitHub PAT | `~/.gerhards-analyst/secrets/github.env` | KEY=VALUE |
| Custom tools | `~/.gerhards-analyst/secrets/<name>.env` | KEY=VALUE |

---

## How to Load Secrets in Python (uv scripts)

```python
from dotenv import load_dotenv
from pathlib import Path
import os

secrets_path = Path.home() / ".gerhards-analyst" / "secrets" / "llm-keys.env"
load_dotenv(secrets_path)

api_key = os.getenv("OPENAI_API_KEY")
```

## How to Load Secrets in PowerShell

```powershell
$secrets = Get-Content "~\.gerhards-analyst\secrets\llm-keys.env" |
    Where-Object { $_ -match "=" } |
    ForEach-Object {
        $key, $val = $_ -split "=", 2
        [System.Environment]::SetEnvironmentVariable($key.Trim(), $val.Trim(), "Process")
    }
```

---

## Rules

1. **Never commit secrets** — not even with `.gitignore` protection
2. **One file per service** — easier rotation and auditing
3. **Prefix env vars** by service: `OPENAI_`, `GITHUB_`, `ANTHROPIC_`
4. **Document in README.txt** what's stored (keys only, no values)
5. **Rotate** when in doubt — NotebookLM cookies expire every 2-4 weeks

---

## Adding a New Secret

```powershell
# 1. Create the file
$secretsDir = "~\.gerhards-analyst\secrets"
Add-Content "$secretsDir\llm-keys.env" "OPENAI_API_KEY=sk-..."

# 2. Update the README index
Add-Content "$secretsDir\README.txt" "llm-keys.env: OpenAI API key (added 2026-04-10)"
```

## Anti-patterns

- Do not activate this skill when a simpler direct answer or a different specialist skill is a better fit.
- Do not hide assumptions, uncertainty, or missing inputs behind confident-sounding prose.
- Do not skip the required validation, evidence, or operator handoff that makes the output usable.
- Do not turn examples into universal rules without checking whether the current task actually matches them.
## Checklist

- [ ] The skill matches the actual task trigger.
- [ ] Assumptions, limits, or unknowns are stated explicitly.
- [ ] Output format matches the operator need.
- [ ] Validation, evidence, or next-step guidance is included where relevant.