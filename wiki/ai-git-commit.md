---
id: ai-git-commit
type: documentation
title: "AI Git Commit — Automated Commit Message Generation"
tags: [git, developer-workflow, automation, llm]
domain: technical

is_project: false
project:

status: active
is_valid: true
valid_from: 2026-04-08
valid_to:
superseded_by:
expired_at:

confidence: high
reviewed_by:
review_date:

created: 2026-04-08
created_by: Researcher
last_modified: 2026-04-08
modified_by: Analyst
source: https://gist.github.com/karpathy/1dd0294ef9567971c1e4348a90d69285

relates_to:
  - "[[karpathy-llm-wiki-pattern]]"
  - "[[tooling-policy]]"
depends_on: []
---

## Overview

The AI Git Commit pattern (`gcm`) is a shell function by Andrej Karpathy that pipes `git diff --cached` into an LLM CLI to generate a one-line commit message, then offers an interactive accept/edit/regenerate/cancel loop. This page documents the original Bash pattern and our Windows/PowerShell adaptation using the `llm` CLI (installable via `uv tool install llm`). James (GitHub Copilot CLI) can also serve this role interactively in any session.

---

## Original Pattern (Bash / macOS)

Source: https://gist.github.com/karpathy/1dd0294ef9567971c1e4348a90d69285

```bash
gcm() {
  local diff commit
  diff=$(git diff --cached)
  if [[ -z "$diff" ]]; then
    echo "No staged changes. Stage changes with git add first."
    return 1
  fi
  while true; do
    commit=$(echo "$diff" | llm "Below is a code diff. Generate a short, single-line git commit message (max 72 chars) that describes the change. Output the commit message only, no extra text.")
    echo "Proposed commit message:"
    echo "  $commit"
    echo ""
    echo "(a)ccept  (e)dit  (r)egenerate  (c)ancel"
    read -r choice
    case "$choice" in
      a) git commit -m "$commit"; break ;;
      e) read -rp "Edit: " commit; git commit -m "$commit"; break ;;
      r) echo "Regenerating..."; continue ;;
      c) echo "Cancelled."; break ;;
      *) echo "Invalid choice." ;;
    esac
  done
}
```

The `llm` CLI tool (from [llm.datasette.io](https://llm.datasette.io/en/stable/)) handles model routing. It supports OpenAI, Anthropic, local Ollama models, and many others via plugins.

---

## Windows / PowerShell Adaptation

### Installation

Install `llm` with `uv` (consistent with our tooling policy — never `pip`):

```powershell
uv tool install llm
```

Configure a backend. For OpenAI:

```powershell
$env:OPENAI_API_KEY = "sk-..."
llm keys set openai   # or use the env var directly
```

For local models via Ollama:

```powershell
llm install llm-ollama
llm models   # lists available Ollama models
```

### PowerShell `gcm` Function

Add to your PowerShell profile (`$PROFILE`):

```powershell
function Invoke-AiCommit {
    $diff = git diff --cached
    if (-not $diff) {
        Write-Host "No staged changes. Stage changes with git add first."
        return
    }

    $prompt = "Below is a code diff. Generate a short, single-line git commit message (max 72 chars) describing the change. Output only the commit message, no extra text."

    while ($true) {
        $commit = $diff | llm $prompt
        Write-Host ""
        Write-Host "Proposed commit message:"
        Write-Host "  $commit"
        Write-Host ""
        Write-Host "(a)ccept  (e)dit  (r)egenerate  (c)ancel"
        $choice = Read-Host

        switch ($choice.ToLower()) {
            'a' { git commit -m $commit; return }
            'e' {
                $commit = Read-Host "Edit"
                git commit -m $commit
                return
            }
            'r' { Write-Host "Regenerating..."; continue }
            'c' { Write-Host "Cancelled."; return }
            default { Write-Host "Invalid choice. Enter a, e, r, or c." }
        }
    }
}

Set-Alias gcm Invoke-AiCommit
```

> **Note:** PowerShell already has a built-in `gcm` alias for `Get-Command`. Use a different alias name if this conflicts, e.g. `aigcm` or `aicommit`.

---

## Backend Notes

| Backend | Setup | Notes |
|---------|-------|-------|
| OpenAI GPT-4o-mini | `$env:OPENAI_API_KEY` | Fast, cheap, excellent for commit messages |
| Anthropic Claude | `llm install llm-claude-3` | Higher quality, higher cost |
| Ollama (local) | `llm install llm-ollama` | Zero cost, needs Ollama running, ~3-7B model sufficient |
| Default model | `llm models default <model>` | Sets the model used when no `-m` flag given |

---

## Alternative: James (GitHub Copilot CLI)

In any session, James can generate a commit message directly without the `llm` CLI:

```
# Ask James interactively
"Here's my git diff --cached output: [paste]. Write a commit message."
```

James then produces the message. This is useful for one-off commits or when `llm` is not configured. For a repeatable automated workflow, the `llm`-based PowerShell function above is preferred.

---

## References

- Original gist: https://gist.github.com/karpathy/1dd0294ef9567971c1e4348a90d69285
- `llm` CLI docs: https://llm.datasette.io/en/stable/
- `llm-ollama` plugin: https://github.com/taketwo/llm-ollama
- Related: [[karpathy-llm-wiki-pattern]], [[tooling-policy]]
