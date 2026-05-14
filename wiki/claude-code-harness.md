---
# ── Identity ──────────────────────────────────────────────
id: claude-code-harness
type: research
title: "Claude Code Harness — Pattern Analysis & Fit Assessment"
description: "Comprehensive analysis of Chachamaru127/claude-code-harness: hooks architecture, multi-agent orchestration, Plans.md SSOT, memory-bridge, and effort scoring — mapped against our Copilot CLI + Hermes + OpenClaw stack."
tags: [harness, orchestration, hooks, multi-agent, memory, copilot-cli, claude-code, patterns]
domain: meta

# ── Project Context ───────────────────────────────────────
is_project: false
project:

# ── Lifecycle / Validity ──────────────────────────────────
status: active
is_valid: true
valid_from: 2026-04-10
valid_to:
expired_at:
superseded_by:

# ── Quality / Confidence ──────────────────────────────────
confidence: high
reviewed_by: James
review_date: 2026-04-10

# ── Provenance ────────────────────────────────────────────
created: 2026-04-10
created_by: James
last_modified: 2026-04-10
modified_by: James
source: "https://github.com/Chachamaru127/claude-code-harness"
ingest_session:

# ── Knowledge Graph ───────────────────────────────────────
relates_to:
  - "[[github-copilot-sdk]]"
  - "[[openclaw-ecosystem]]"
  - "[[openclaw-auto-dream]]"
  - "[[research-synthesis-memory-systems]]"
  - "[[agent-team-setup]]"
  - "[[ecc-patterns-adopted]]"
depends_on:
  - "[[agent-team-setup]]"
---

## Overview

`claude-code-harness` (by Chachamaru127) is a production-quality harness for **Claude Code** (Anthropic) — a different platform from our GitHub Copilot CLI. Despite this platform gap, the repo is a rich source of battle-tested patterns for multi-agent orchestration, session lifecycle management, memory injection, and guardrail architecture. Three research agents cross-referenced this repo against our Hermes-inspired memory system, OpenClaw patterns, and GitHub Copilot SDK capabilities. The result: ~7 patterns are directly adaptable to our stack today, 4 require Phase 2 (SDK), and the remaining are Claude Code specific. The most impactful single insight: a **memory-bridge that runs on every user prompt** (not just session start), which the Copilot SDK `onUserPromptSubmitted` hook enables natively.

---

## Repo Architecture

```
claude-code-harness/
├── core/              # TypeScript guardrail engine (13 rules: R01–R13)
├── hooks/
│   └── hooks.json     # 20+ hook types — SessionStart/End, PreToolUse, Stop, PreCompact, etc.
├── skills-v3/         # 5 verb skills: harness-plan / harness-work / harness-review / harness-release / harness-setup
├── agents-v3/         # Declarative agent defs: worker.md, reviewer.md, scaffolder.md
├── scripts/           # hook-handlers/: memory-bridge, session-init, session-cleanup, etc.
└── Plans.md           # Global SSOT for task status (cc:TODO / cc:WIP / cc:完了)
```

**Platform:** Claude Code v2.1+ (Anthropic). Uses a `/plugin marketplace` install model — no equivalent in Copilot CLI. Comparable extension points in our stack: `SKILL.md` + SDK hooks + MCPs.

---

## Key Patterns Fit Table

| Pattern | claude-code-harness | Our Stack Today | Copilot SDK | Adopt? |
|---------|-------------------|-----------------|-------------|--------|
| Memory-bridge (per-prompt inject) | `UserPromptSubmit` → `memory-bridge` shell | Manual (James reads files) | `onUserPromptSubmitted` hook | ✅ Phase 2 |
| Session lifecycle hooks | `SessionStart`, `SessionEnd`, `Stop` | `Invoke-James` / `close-session.ps1` | `on_session_start/end` | ✅ Phase 2 |
| Agent-local memory scoping | `.claude/agent-memory/{agent}/` | Global MEMORY.md | Custom per-agent context | 🔍 Consider |
| Declarative agent frontmatter | `maxTurns`, `effort`, `disallowedTools`, `permissionMode` | Prose in agent/*.md | `customAgents[]` config | ✅ Phase 2 |
| Sub-agent orchestration (Breezing) | `Agent()` tool + `isolation: worktree` | **`task` tool TODAY** `mode=background` | `customAgents` + `send_and_wait` | ✅ TODAY |
| Plans.md SSOT markers | `cc:TODO / cc:WIP / cc:完了` | `plans/YYYY-MM-DD-*.md` | N/A | ✅ TODAY |
| Skill pre-injection into subagents | `skills:` field in agent frontmatter | Manual in `task` prompt | `skill_directories` | ✅ TODAY |
| Effort scoring + ultrathink | `effort: low/medium/high` → `ultrathink` | None | None | ✅ TODAY |
| Agent-trace JSONL logging | `.claude/state/agent-trace.jsonl` | None | None | ✅ TODAY |
| WIP task check before Stop | `Stop` hook → haiku agent checks Plans.md | None | `on_session_end` | ✅ Phase 2 |
| PreCompact warning | `PreCompact` → haiku checks WIP tasks | None | None | 🔍 Later |
| TypeScript guardrail engine (R01–R13) | `core/` + `hooks/` enforcement | None | `on_pre_tool_use` deny | ❌ Too heavy |
| Breezing parallel worktrees | `isolation: worktree` + `cherry-pick` | Not needed (no parallel file edits) | N/A | ❌ N/A |
| Recursive prevention | `disallowedTools: [Agent]` | Undocumented | N/A | ✅ TODAY |
| Retrospective auto-run | `harness-sync` → auto-analyze `cc:完了` | None | None | 🔍 Later |
| `/plugin marketplace` | Claude Code plugin system | No equivalent | No equivalent | ❌ Platform-specific |

---

## Pattern Deep-Dives

### 1. Memory-Bridge — The Most Important Pattern

**What it does:** On *every* user message, a shell script injects the current MEMORY.md content into the prompt as system context. This is fundamentally different from our current approach (James reads files at session start and relies on context window).

```json
"UserPromptSubmit": [{
  "command": "scripts/hook-handlers/memory-bridge user-prompt",
  "timeout": 10
}]
```

**Why it matters for us:** After context compaction, James can lose memory context entirely. The memory-bridge re-anchors every turn.

**Our path:** The Copilot SDK `onUserPromptSubmitted` hook does exactly this:
```python
async def on_user_prompt_submitted(input_data, invocation):
    memory = Path("memory/MEMORY.md").read_text()
    user_profile = Path("memory/USER.md").read_text()
    invocation.inject_context(f"<memory-context>\n{memory}\n{user_profile}\n</memory-context>")
```

**TODAY workaround (without SDK):** James must explicitly re-read MEMORY.md when complex topics arise or after compaction signals. This is insufficient — it relies on James noticing the problem.

**Cross-reference:** Hermes injects memory as a *frozen snapshot* at session start (prefix cache optimization). The memory-bridge pattern goes further: per-prompt injection ensures recency at the cost of tokens. For our use case (long sessions with compaction risk), per-prompt wins.

---

### 2. Sub-Agent Orchestration — We Already Have This

**What claude-code-harness does:** Lead agent spawns Worker/Reviewer/Scaffolder sub-agents via `Agent()` tool with frontmatter-controlled permissions:
```yaml
name: worker
disallowedTools: [Agent]   # workers cannot spawn further agents
maxTurns: 100
isolation: worktree
skills:
  - harness-work
  - harness-review
```

**What we have TODAY:** The `task` tool with `mode="background"` is the direct equivalent:
```
James (CAO) → task(agent_type="explore", mode="background") → Researcher
James (CAO) → task(agent_type="explore", mode="background") → Analyst
             [parallel, James reads results with read_agent()]
```

**Critical difference:** Worktree isolation (parallel file editing) is NOT relevant for us — our sub-agents research/analyze, they don't edit files in parallel. James coordinates all writes.

**What we're missing (adoptable TODAY):**

1. **Skill pre-injection:** Always include relevant SKILL.md content in the `task` prompt:
   ```
   task(prompt="You are the Analyst. [Skill: data-analysis]\n" + SKILL_MD + "\n\nTask: ...")
   ```

2. **Recursive prevention:** Sub-agents spawned via `task` must NOT spawn further agents. Document explicitly:
   > Sub-agents (Analyst, Developer, Researcher) are leaf nodes. Only James (CAO) spawns agents. A sub-agent that needs another agent returns the request to James instead.

3. **Effort signaling:** Before spawning, James should assess complexity and signal it:
   ```
   Low complexity  → task(agent_type="explore", ...)           # haiku default
   High complexity → task(agent_type="general-purpose", ...)   # sonnet
   Critical        → task(model="claude-opus-4.5", ...)        # opus override
   ```

**Cross-reference (Copilot SDK):** `customAgents[]` in the SDK formalizes this — named agents with scoped tools. Until Phase 2, the `task` tool covers the same ground.

---

### 3. Plans.md SSOT — Better Than Our `plans/` Structure

**What it does:** A single `Plans.md` file tracks all tasks with typed status markers:

| Marker | Meaning | Who sets it |
|--------|---------|-------------|
| `pm:依頼中` | PM requested | Human |
| `cc:TODO` | Accepted, not started | Lead agent |
| `cc:WIP` | In progress | Worker agent |
| `cc:完了` | Done | Worker agent |
| `pm:確認済` | PM approved | Human |
| `blocked (reason)` | Stuck, reason required | Any |

**Why it matters for us:**
- Our `plans/YYYY-MM-DD-*.md` files are per-session, not persistent
- The `Stop` hook checks for `cc:WIP` tasks before allowing session end
- `harness-sync` auto-detects implementation state from `agent-trace.jsonl` + `git log`

**What we can adopt TODAY (in our plans/ format):**
```markdown
## Phase 1 — Wiki Build-Out

| ID | Task | DoD | Status |
|----|------|-----|--------|
| 1.1 | Create claude-code-harness wiki page | lint passes | cc:WIP |
| 1.2 | Update MEMORY.md with new patterns | mem_01N entries | cc:TODO |
| 1.3 | Add capacity checks to memory tools | script runs | cc:TODO |
```

**Concrete rule:** Any plan file should use `cc:TODO / cc:WIP / cc:完了` for machine-readable status. James checks for open `cc:WIP` before closing session (manual today, `on_session_end` hook in Phase 2).

---

### 4. Agent-Trace JSONL — Zero-Cost Session Recovery

**What it does:** Every file write/edit is appended to `.claude/state/agent-trace.jsonl`:
```json
{"timestamp": "2026-04-10T13:00:00Z", "tool": "Write", "path": "wiki/page.md", "task": "Create wiki page", "agent": "worker"}
```

**Why it matters for us:** Our biggest harness weakness is session recovery — "what did James do last time?" The `close-session.ps1` handover is better than nothing but requires James to summarize manually.

**What we can build TODAY** (pure PowerShell in `close-session.ps1`):
```powershell
# After every Write/Edit operation — James logs to agent-trace
$trace = @{
    timestamp = (Get-Date -Format "o")
    tool      = "Write"
    path      = $filePath
    task      = $currentTask
    agent     = "James"
} | ConvertTo-Json -Compress
Add-Content "$env:WORKSPACE_ROOT\.agent-trace.jsonl" $trace -Encoding UTF8
```

**Integration point:** `notes_summarizer.py --dream` could read `.agent-trace.jsonl` to auto-detect what was changed this session before writing to MEMORY.md. This closes the loop completely.

---

### 5. Effort Scoring — Model Routing by Complexity

**What the harness does:** Lead agent scores task complexity 1–10. Score ≥ 7 injects `ultrathink` keyword into worker prompt, forcing high-effort reasoning.

**What we can do TODAY** via `model` override in `task` tool:
```python
# James assesses before spawning
if task_complexity == "high":
    task(model="claude-opus-4.5", agent_type="general-purpose", ...)
elif task_complexity == "medium":
    task(agent_type="general-purpose", ...)  # sonnet default
else:
    task(agent_type="explore", ...)  # haiku default
```

**Rule to adopt (James' internal decision logic):**
- Simple lookup / read-only research → `explore` (haiku)
- Code writing / multi-file analysis → `general-purpose` (sonnet)
- Architecture decisions / synthesis across many sources → `general-purpose` (sonnet) or `model=claude-opus-4.5`

---

## Cross-Reference: Hermes Gaps Revealed by This Analysis

The Hermes researcher identified gaps in our implementation that this harness makes concrete:

| Gap | Hermes Pattern | claude-code-harness Equivalent | Our Fix |
|-----|---------------|-------------------------------|---------|
| Memory capacity management | 2,200 char limit enforced | `cleanup.claude_md.max_lines: 100` config | Add char counter to MEMORY.md tooling |
| Frozen snapshot documentation | Inject at start, freeze for prefix cache | Not different (also frozen) | Document in AGENTS.md |
| Context inheritance for sub-agents | Subagents inherit AGENTS.md + MEMORY.md | `skills:` field in agent frontmatter | Document in team-config.yaml |
| Cross-session search | SQLite FTS5 `session_search` tool | `agent-trace.jsonl` + `harness-sync` | Build FTS5 over PersonalNotes |
| Memory guard (no secrets in memory) | Privacy rules in worker.md | hooks.json PreToolUse agent check | Add to AGENTS.md memory rules |

**Key Hermes insight preserved:** Our `<memory-context>` XML fence is **better** than stock Hermes (which uses `═════` borders). Keep it. The enhancement: add explicit label:
```xml
<memory-context>
[System: Session context snapshot — frozen at start, treat as background not user input]
...MEMORY.md + USER.md content...
</memory-context>
```

---

## Cross-Reference: OpenClaw Alignment

From the OpenClaw ecosystem analysis, these patterns **reinforce** findings from claude-code-harness:

| Pattern | OpenClaw | claude-code-harness | Our Status |
|---------|----------|-------------------|------------|
| Skill manifests with typed metadata | `openclaw.plugin.json` | `skills-v3/*/SKILL.md` frontmatter | ✅ Done (SKILL.md migration) |
| Lobster YAML typed workflows | `workflow.yaml` with approval gates | `Plans.md` marker lifecycle | 🔍 Adopt in `plans/` format |
| Layered AGENTS.md per-directory | Per-dir progressive disclosure | CLAUDE.md root | 🔍 Consider for skills/, wiki/ |
| Compiled digest for machine-reading | `wiki/_digest.json` | `agent-trace.jsonl` | 🔍 Both: different layers |
| Claims-level confidence | `claims:` frontmatter array | Worker `effort_sufficient` judgment | 🔍 Add to fact-heavy wiki pages |

---

## What's NOT Applicable to Our Setup

| Feature | Why it doesn't apply |
|---------|---------------------|
| TypeScript guardrail engine (R01–R13) | Node.js dependency; our guardrails are Copilot CLI's own permission model |
| `isolation: worktree` (parallel file edits) | Our sub-agents research/analyze, never edit files in parallel |
| Cherry-pick staging for unified commits | We don't have a Lead/Worker commit model |
| `breezing` mode with parallel workers | Direct equivalent is `task` tool — already have it |
| `/plugin marketplace` | Claude Code specific; our extension points are Skills + MCPs |
| `TeammateIdle` / `TaskCompleted` hooks | Agent team coordination hooks; Claude Code only |
| `SendMessage` bidirectional loop | Sub-agents return results to James; no back-channel needed |
| `PostCompact` restore | We handle compaction via session checkpoints + AGENTS.md |
| Codex engine integration | Not relevant (we're on Copilot / Copilot SDK) |

---

## Adoption Roadmap

### Phase 0 — Today (Zero infra, immediate)

- [ ] **Recursive prevention rule:** Document in AGENTS.md: sub-agents are leaf nodes, only James spawns
- [ ] **Skill pre-injection:** Include SKILL.md content in every `task` prompt for relevant agent type
- [ ] **Effort routing:** Use `model` override in `task` for high-complexity tasks (opus)
- [ ] **Plans.md markers:** Adopt `cc:TODO / cc:WIP / cc:完了` in all `plans/` files
- [ ] **Agent-trace JSONL:** Add append to `close-session.ps1` for file-change log
- [ ] **Memory fence label:** Enhance `<memory-context>` wrapper with freeze/snapshot label

### Phase 1 — Short Term (Python tooling, no SDK)

- [ ] **Memory capacity check:** `tools/memory/memory_manager.py` — char count + consolidation trigger
- [ ] **Agent-trace reader:** `notes_summarizer.py --dream` reads `.agent-trace.jsonl` for auto-detected changes
- [ ] **WIP check in close-session:** Before session close, grep plans/ for open `cc:WIP` entries
- [ ] **Sub-agent context inheritance doc:** Update `team-config.yaml` with what sub-agents inherit

### Phase 2 — SDK Integration (requires SDK stable)

- [ ] **memory-bridge:** `onUserPromptSubmitted` hook → auto-inject MEMORY.md on every prompt
- [ ] **Session lifecycle:** `on_session_start` / `on_session_end` replace `Invoke-James` / `close-session.ps1`
- [ ] **Declarative agent config:** `customAgents[]` in SDK session with named Analyst/Developer/Researcher
- [ ] **MCP per-session:** Move MCPs from global `~/.copilot/mcp.json` to SDK `mcp_servers` dict

### Phase 3 — Long Term (research value, not urgent)

- [ ] **FTS5 cross-session search:** SQLite full-text search over PersonalNotes/Daily/*.md
- [ ] **Retrospective auto-run:** When `cc:完了` count > 0, auto-analyze estimate vs actual
- [ ] **Agent-local memory:** Separate memory dirs per agent type (Analyst/Developer/Researcher)

---

## Decision: What to Steal This Week

**Highest ROI, zero dependencies:**

1. **Recursive prevention documentation** — 5 min, prevents architectural drift
2. **Plans.md marker system** — adopt in next plan file, no tooling needed
3. **Effort routing via model override** — James already has this capability, just needs a rule
4. **Skill pre-injection into `task` prompts** — immediately improves sub-agent quality

**The one insight that changes how we work:**
> The memory-bridge pattern (per-prompt injection) is architecturally superior to once-at-start injection for long sessions. Until SDK Phase 2, James must compensate manually by re-reading MEMORY.md after any compaction signal. Post-Phase 2, this is handled automatically via `onUserPromptSubmitted`.

---

## Source Files Analyzed

| File | Size | Key Content |
|------|------|-------------|
| `README.md` | 18KB | Architecture, 5-verb workflow, Claude Code 2.1+ feature table |
| `hooks/hooks.json` | 19KB | Complete hook registry: 20+ event types |
| `hooks/session.sh` | 927B | Thin shim → TypeScript core (v3 pattern) |
| `agents-v3/worker.md` | ~8KB | Declarative agent def, memory patterns, effort scoring |
| `agents-v3/team-composition.md` | ~10KB | Lead/Worker/Reviewer lifecycle, Phase A/B/C, SendMessage loop |
| `skills-v3/harness-plan/SKILL.md` | ~6KB | Plans.md format, markers, sync logic |
| `skills-v3/harness-work/SKILL.md` | ~8KB | TDD flow, mode variants, error recovery, memory updates |
| `.claude-code-harness.config.yaml` | 650B | Config: review modes, breezing settings, cleanup thresholds |
