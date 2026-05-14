---
name: session-handoff
description: "Creates comprehensive handoff documents for seamless Copilot CLI session transfers. Triggered when: context approaches capacity, major task milestone completed, session ending, user says 'save state' / 'create handoff' / 'pause'. Enables fresh sessions to continue with zero ambiguity. Adapted from softaworks/agent-toolkit for owner team workflow."
agent: James
tools_required: [powershell, file-io]
wiki_ref: "[[session-handoff]]"
version: "1.0-gerhards"
source: "https://github.com/softaworks/agent-toolkit/tree/main/skills/session-handoff"
---

# Skill: Session Handoff

**Category:** Memory & Continuity  
**Trigger:** Context window near capacity, end of work session, milestone completed, user requests "save state"  
**Owner:** James (CAO) — can delegate to any agent

---

## The Problem This Solves

Copilot CLI has no persistent conversation log. When a session ends:
- All context (decisions made, files changed, next steps) is lost
- A fresh session has zero knowledge of what was done
- Work is duplicated, decisions are re-debated

A handoff document captures this context and lets a fresh session continue from exactly where the last one stopped.

---

## When to Create a Handoff

James creates a handoff **proactively** — not only when asked:

- After 5+ file edits in one session
- After an architecture decision
- After a complex debugging session  
- At the end of any non-trivial work session
- When context window is >70% full
- When the owner says "pause", "save state", "continue later"

**Proactive suggestion text:**
> "Wir haben erheblichen Fortschritt gemacht. Soll ich einen Handoff erstellen, damit die nächste Session nahtlos weiterarbeiten kann?"

---

## Workflow — Creating a Handoff

### Step 1: Generate the Handoff File

```powershell
# Filename convention: YYYY-MM-DD-HHMMSS-[slug].md
$timestamp = Get-Date -Format "yyyy-MM-dd-HHmmss"
$slug = "task-description"  # replace with actual task slug
$handoffPath = "<WORKSPACE_ROOT>\plans\handoffs\$timestamp-$slug.md"
New-Item -ItemType Directory -Path "<WORKSPACE_ROOT>\plans\handoffs" -Force | Out-Null
```

### Step 2: Fill the Handoff Template

Use the template below. Fill in ALL sections — no `[TODO]` placeholders in the final document.

### Step 3: Validate

Before finalizing, verify:
- [ ] No `[TODO]` placeholders remain
- [ ] All referenced file paths exist (check with `Test-Path`)
- [ ] No secrets, tokens, or credentials written into the file
- [ ] "Immediate Next Steps" are actionable, not vague
- [ ] Git status captured (branch, last commit)

### Step 4: Confirm to the owner

Report:
- Handoff file location
- Summary of captured context (2–3 sentences)
- First action item for next session

---

## Handoff Document Template

```markdown
---
created: YYYY-MM-DD HH:MM
session_end_reason: [context_full | milestone_reached | session_end | user_request]
git_branch: <branch>
git_last_commit: <SHA + message>
quality_score: [0-100]
---

# Session Handoff — [Task Title]

## Current State Summary

[1-3 sentences describing exactly where the work stands right now.]

## Handoff State

- Current execution state:
- Open WIP:
- Blockers:
- Next session start:

## Important Context — Fresh Agent MUST Know This

- [Critical decision made with rationale]
- [Non-obvious behavior discovered]
- [Constraint or limitation found]
- [the owner preference expressed]

## Immediate Next Steps

1. [Specific action — no ambiguity]
2. [Specific action]
3. [Specific action]

## Checkpoint Summary

- Open WIP:
- Open hypotheses:
- Blockers:
- Next test:

## Failure State

- Failure class:
- Fallback action:
- Escalate when:

## Hypothesis Ledger

| Hypothesis | Confidence | Evidence | Contradiction | Next test |
|------------|------------|----------|---------------|-----------|
| [claim] | [high/medium/low/uncertain] | [best support] | [main tension] | [next discriminating check] |

## Files Changed This Session

| File | Change Type | Notes |
|------|------------|-------|
| `path/to/file.py` | Modified | What changed and why |
| `path/to/new.md` | Created | Purpose |

## Decisions Made

| Decision | Rationale | Alternatives Rejected |
|----------|-----------|----------------------|
| Used X not Y | Because Z | Y requires token auth |

## Pending Work (not done yet)

- [ ] [Item 1]
- [ ] [Item 2]

## Key Patterns Discovered

- [Pattern or convention to follow in this project]

## Potential Gotchas

- [Known issue that will bite the next agent]
- [Thing that looks wrong but is intentional]

## Environment State

```powershell
# Run these to verify state at session start:
git status
git log --oneline -5
```

## Links & References

- Plan: `plans/[plan-file].md`
- Wiki: `wiki/[wiki-page].md`
- Continues from: [previous handoff if applicable]
```

---

## Workflow — Resuming from a Handoff

### Step 1: Find Available Handoffs

```powershell
Get-ChildItem "<WORKSPACE_ROOT>\plans\handoffs\" -Filter "*.md" |
  Sort-Object LastWriteTime -Descending |
  Select-Object Name, LastWriteTime |
  Format-Table -AutoSize
```

### Step 2: Assess Staleness

```powershell
# How many commits since handoff was created?
$handoffDate = "2026-04-10"  # adjust
git --no-pager log --oneline --since="$handoffDate" | Measure-Object -Line
```

Staleness thresholds:
- **0 commits, same day** → FRESH — resume directly
- **1–5 commits** → SLIGHTLY STALE — review changes first
- **6+ commits** → STALE — verify context carefully
- **>7 days** → VERY STALE — create fresh handoff instead

### Step 3: Load Context

1. Read the handoff document completely
2. Check "Potential Gotchas"
3. Run verification commands from "Environment State"
4. Start with "Immediate Next Steps" item #1

---

## Handoff Chaining (Long-Running Projects)

For multi-session projects, chain handoffs:

```
plans/handoffs/2026-04-10-120000-wiki-build.md   (initial)
    ↓ continues-from
plans/handoffs/2026-04-11-093000-wiki-build.md   (part 2)
    ↓ continues-from
plans/handoffs/2026-04-12-141500-wiki-build.md   (part 3)
```

Each handoff's front-matter includes:
```yaml
continues_from: "plans/handoffs/2026-04-11-093000-wiki-build.md"
```

---

## Storage Location

All handoffs: `<WORKSPACE_ROOT>\plans\handoffs\`

Naming: `YYYY-MM-DD-HHMMSS-[slug].md`

---

## Quality Checklist

- [ ] Summary clearly states "what's happening right now"
- [ ] Context includes all decisions with rationale (not just outcomes)
- [ ] Next steps are numbered and specific
- [ ] All modified files listed
- [ ] No secrets/tokens in document
- [ ] Gotchas section catches known surprises
- [ ] Verification commands copy-paste ready

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