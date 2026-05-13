---
name: daily-notes
description: "Session logging protocol — Add-Content file I/O to daily notes Markdown files; no Obsidian dependency in automation"
agent: James
tools_required: [powershell]
wiki_ref: "[[agent-team-setup]]"
version: "1.1"
---

# Skill: Daily Notes Session Logging

> **Purpose:** Defines exactly how James logs each work session into Obsidian daily notes.
> **Trigger:** Automatically at the end of every significant interaction with Gerhard.

---

## When to Log

Log a session entry when:
- A task was completed or substantially progressed
- A new tool, pattern, or insight was discovered
- Files were created or meaningfully modified
- A decision was made (architecture, tooling, approach)
- An error occurred and was resolved

Skip logging for: casual Q&A, brief lookups, quick clarifications.

---

## Session Log Format

Append under `## 🤖 Agent Sessions` in today's daily note.

```markdown
### [HH:MM] Session · <one-line summary>
- **Agent:** James (CAO) | Analyst | Developer | Researcher
- **Task:** <what was requested>
- **Done:**
  - <item 1>
  - <item 2>
- **Files changed:** `path/to/file.ext`, `path/to/other.ext`
- **Notes:** <anything worth remembering>
```

---

## How James Writes to Daily Notes

**Direct file I/O only — no Obsidian dependency.** Obsidian is presentation, not plumbing.

```powershell
# Today's note path
$today    = Get-Date -Format "yyyy-MM-dd"
$notePath = "<WORKSPACE_ROOT>\PersonalNotes\Daily\$today.md"

# Append a session entry
$entry = @"

### [$(Get-Date -Format 'HH:mm')] Session · <one-line summary>
- **Agent:** James (CAO)
- **Done:**
  - item 1
- **Files changed:** ``path/to/file``
"@
Add-Content -Path $notePath -Value $entry -Encoding UTF8
```

> **Rule:** James uses `Add-Content` to write directly to the `.md` file.  
> The note exists or is created by `start-session.ps1` / `close-session.ps1`. No external tool required.

---

## Achievements & Learnings Updates

```powershell
# Add achievement
Add-Content -Path $notePath -Value "`n- Achievement text here" -Encoding UTF8

# Add learning
Add-Content -Path $notePath -Value "`n- Learning text here" -Encoding UTF8
```

---

## End-of-Session Checklist

1. **Log session** in daily note (section `## 🤖 Agent Sessions`)
2. **Update achievements** if something was completed
3. **Update learnings** if something new was discovered
4. **Update `memory/MEMORY.md`** if a persistent fact was established
5. **Update `memory/USER.md`** if a new preference was expressed
6. **Update skill files** if a new pattern was documented

---

## Task Tracking in Daily Notes

Pending tasks go under `## 📋 Tasks`:
```markdown
- [ ] Task not yet done
- [x] Completed task
```

The summarizer picks up `- [x]` items automatically for weekly rollups.

---

## Automated Summaries Schedule

| Frequency | When | Script Flag | Task Scheduler Name |
|-----------|------|-------------|---------------------|
| Weekly | Every Sunday 20:00 | `--weekly` | `WeeklyNoteSummary` |
| Monthly | 1st of month 08:00 | `--monthly` | `MonthlyNoteSummary` |
| Annual | January 1st 09:00 | `--annual` | `AnnualNoteSummary` |

**Manual trigger:**
```shell
# From vault root (uv must be on PATH)
$env:PATH += ";~\.local\bin"
uv run tools\notes\notes_summarizer.py --weekly
uv run tools\notes\notes_summarizer.py --monthly --date 2026-04-01
```
