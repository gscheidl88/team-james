# Session Rules

Quick-reference for session lifecycle management.
Full protocol lives in `tools/commands/prime.md` (open) and `tools/commands/handoff.md` (close).

---

## Session Open (Prime)

When James starts a fresh session or has lost context:

1. Read `memory/MEMORY.md` + `memory/USER.md`
2. Read `AGENTS.md` (team constitution)
3. Read active plan in `plans/` if a task is in-flight
4. Check for open `cc:WIP` items: `Select-String "cc:WIP" plans\*.md`

Full protocol: `tools/commands/prime.md`

## Session Close Checklist (short form)

```powershell
# 0. Check for open WIP
Select-String "cc:WIP" <WORKSPACE_ROOT>\plans\*.md 2>$null
# 1. Wiki lint
uv run tools/wiki/wiki_lint.py
# 2. Write Daily Note (agent, done, files, wiki backlinks)
# 3. Update MEMORY.md + USER.md
# 4. Dream (memory consolidation)
uv run tools/notes/notes_summarizer.py --dream
# 5. Graph rebuild (if wiki changed)
uv run --python 3.12 tools/wiki/wiki_graph.py --build
# 6. Telegram push
uv run tools/telegram/telegram_notify.py "✅ Session closed [HH:MM]"
```

Full protocol: `tools/commands/handoff.md`

## Daily Note Logging

Write **during** the session (not at end). After every completed task:

```powershell
$today = Get-Date -Format "yyyy-MM-dd"
$notePath = "<WORKSPACE_ROOT>\PersonalNotes\Daily\$today.md"
Add-Content -Path $notePath -Value "`n### [HH:MM] Session · summary`n- **Agent:** James`n- **Done:** ..." -Encoding UTF8
```

Include: what was done, which agent, files created/changed (with links), open wiki backlinks.

## Task Status Markers

| Marker | Meaning |
|--------|---------|
| `cc:TODO` | Accepted, not started |
| `cc:WIP` | In progress |
| `cc:完了` | Done, DoD met |
| `blocked (reason)` | Blocked — reason required |
