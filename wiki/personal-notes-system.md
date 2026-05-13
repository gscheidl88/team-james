---
id: personal-notes-system
type: documentation
title: "Personal Notes System — Daily/Weekly/Monthly/Annual Pipeline"
tags: [obsidian, notes, automation, personal-knowledge, task-scheduler]
domain: personal

is_project: false
project:

status: active
is_valid: true
valid_from: 2026-04-08
valid_to:
superseded_by:

confidence: high
reviewed_by: Gerhard
review_date: 2026-04-08

created: 2026-04-08
created_by: James
last_modified: 2026-04-08
modified_by: James
source:
ingest_session: "[[log#2026-04-08-init]]"

relates_to:
  - "[[agent-team-setup]]"
  - "[[tooling-policy]]"
depends_on:
  - "[[tooling-policy]]"
---

# Personal Notes System — Daily/Weekly/Monthly/Annual Pipeline

## Overview

A structured personal notes system built in Obsidian, with automated summarization via a uv Python script and Windows Task Scheduler. James logs every significant work session into the daily note.

---

## Folder Structure

```
PersonalNotes/
├── Daily/          YYYY-MM-DD.md     — created each day
├── Weekly/         YYYY-Www.md       — auto-generated every Sunday
├── Monthly/        YYYY-MM.md        — auto-generated 1st of month
├── Annual/         YYYY.md           — auto-generated Jan 1st
└── Templates/
    ├── Daily Note.md
    ├── Weekly Note.md
    ├── Monthly Note.md
    └── Annual Note.md
```

---

## Daily Note Structure

Key sections (emoji-headed, parsed by summarizer):

| Section | Emoji | Content |
|---------|-------|---------|
| Morning Focus | 🌅 | Main goal, top 3 priorities, energy level |
| Tasks | 📋 | Must Do / Should Do / Nice To Have |
| Achievements | 🏆 | What was accomplished |
| Learnings | 📚 | New insights, discoveries |
| Agent Sessions | 🤖 | James session logs |
| Evening Reflection | 🌙 | What went well, what to improve |
| Reflections | 🔁 | Longer reflection if needed |

Completed tasks: `- [x]` format — picked up automatically by summarizer.

---

## Automated Summarization

**Tool:** `tools/notes/notes_summarizer.py` (uv inline script, Python ≥ 3.11)

```powershell
# Manual run (from vault root)
uv run tools\notes\notes_summarizer.py --weekly
uv run tools\notes\notes_summarizer.py --monthly
uv run tools\notes\notes_summarizer.py --annual
uv run tools\notes\notes_summarizer.py --weekly --date 2026-04-07  # specific date
uv run tools\notes\notes_summarizer.py --weekly --overwrite         # replace existing
```

**Date guards:** Script checks the current date before running:
- `--weekly`: only runs on Sundays (unless `--date` specified)
- `--monthly`: only runs on the 1st (unless `--date` specified)
- `--annual`: only runs on Jan 1st (unless `--date` specified)

---

## Task Scheduler

Three tasks registered under `\GerhardsAgentTeam\`:

| Task | Trigger | Script Flag |
|------|---------|-------------|
| `WeeklyNoteSummary` | Every Sunday 20:00 | `--weekly` |
| `MonthlyNoteSummary` | Daily 08:00 (guard: 1st of month) | `--monthly` |
| `AnnualNoteSummary` | Daily 09:00 (guard: Jan 1st) | `--annual` |

Setup script: `tools/notes/setup_scheduler.ps1` (run as Administrator to re-register).

---

## James Session Logging Protocol

After every significant session, James appends under `## 🤖 Agent Sessions`:

```markdown
### [HH:MM] Session · <one-line summary>
- **Agent:** James (CAO) | Analyst | Developer | Researcher
- **Task:** <what was requested>
- **Done:**
  - <item 1>
- **Files changed:** `path/to/file.ext`
- **Notes:** <anything worth remembering>
```

Skill reference: `skills/daily-notes/skill.md`

---

## Obsidian Integration

- Templates use `{{date:FORMAT}}` syntax (Obsidian Templater plugin renders live)
- Dataview plugin can query Daily Notes frontmatter
- Graph view shows connections between notes
- Obsidian Web Clipper → clip articles → drop to `sources/` for wiki ingest

---

## Known Issues / Notes

- `New-ScheduledTaskTrigger -Monthly` not available in all PowerShell versions → workaround: daily trigger + date guard in Python script
- Obsidian must be running for CLI `obsidian append` commands to work
- uv must be on PATH: `$env:PATH += ";~\.local\bin"` (in PS profile)
