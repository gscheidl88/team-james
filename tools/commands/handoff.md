# Session Handoff Protocol

> James executes this checklist at the end of EVERY session — without exception.
> Run each step in order. Fix issues before proceeding. Do NOT skip.

For long or risky sessions, also run:

```powershell
& "<WORKSPACE_ROOT>\tools\session\checkpoint-session.ps1"
```

This is the crash-resistance checkpoint. Do not rely on session close alone.

## Step 1 — Check for WIP

```powershell
Select-String "cc:WIP" <WORKSPACE_ROOT>\plans\*.md 2>$null
```

If any WIP found: summarize open items in Daily Note before closing.

## Step 2 — Wiki Lint (must be 0 issues)

```powershell
& "uv" run tools/wiki/wiki_lint.py
```

If issues found: fix orphans, dead links, missing frontmatter — then re-run until clean.

## Step 3 — Daily Note (write NOW, not later)

```powershell
$today = Get-Date -Format "yyyy-MM-dd"
$notePath = "<WORKSPACE_ROOT>\PersonalNotes\Daily\$today.md"
```

Write under `## 🤖 Agent Sessions`:
- What was done (1–2 sentences)
- Which agent was active
- Files created/changed
- Links to plans if any

Write under `## 📖 Wiki Pages Today`:
- Every wiki page created/updated/discussed today as `[[page-id]]`

## Step 4 — Persist new facts to MEMORY.md

Review this session: any new decisions, standards, preferences, or permanent facts?
If yes → append to `memory/MEMORY.md` with `[DATE]` prefix and correct priority marker:
- `⚠️ PERMANENT` — critical, never archive
- `🔥 HIGH` — important, doubled weight
- `📌 PIN` — reference material

If the owner showed a new preference → also update `memory/USER.md`.

## Step 5 — Dream Consolidation

```powershell
& "uv" run tools/notes/notes_summarizer.py --dream
```

0 new entries = correct (dedup active). Not an error.

## Step 6 — Knowledge Index Refresh (only if wiki changed)

```powershell
& "uv" run --python 3.12 tools/wiki/wiki_graph.py --build
& "uv" run --python 3.12 tools/wiki/wiki_search.py --index
```

## Step 7 — Knowledge Performance Review

```powershell
& "uv" run --python 3.12 tools/wiki/knowledge_review.py
```

If status is `warn` or `degraded`: review `wiki/reviews/knowledge-performance-review.md` before ending the handoff.

## Step 8 — Telegram Push

```powershell
& "uv" run tools/telegram/telegram_notify.py "✅ Session closed [DATE HH:MM] — Wiki: OK | Dream: done | WIP: none"
```

Replace `[DATE HH:MM]` with actual timestamp. Replace `none` with open WIP items if any.

## Step 9 — Confirm

Respond to the owner:

```
Session geschlossen ✅
- Wiki Lint: X issues (0 = clean)
- Dream: X neue Einträge
- Daily Note: geschrieben
- MEMORY: X neue Einträge
- Knowledge review: ok|warn|degraded
- Telegram: Push gesendet
```
