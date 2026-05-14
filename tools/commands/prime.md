# Prime — Context Recovery After Compaction

> Run this when context was lost (compaction, new session, or James seems to have forgotten project state).
> James reads each file and confirms understanding before continuing.

## Step 1 — Identity & Role

Read `AGENTS.md` — confirm: who am I, what are my responsibilities, what protocols do I follow?

## Step 2 — Persistent Memory

Read `memory/MEMORY.md` — load all permanent facts, standards, and decisions.

Pay special attention to entries marked:
- `⚠️ PERMANENT` — critical rules, always active
- `🔥 HIGH` — high-weight facts
- `📌 PIN` — reference material

## Step 3 — User Profile

Read `memory/USER.md` — load the owner's preferences, working style, and goals.

## Step 4 — Current Plans

```powershell
Get-ChildItem <WORKSPACE_ROOT>\plans\ -Filter "*.md" | Sort-Object LastWriteTime -Descending | Select-Object -First 5
```

Read the most recent plan file. Check for `cc:WIP` markers.

## Step 5 — Wiki Index

Read `wiki/index.md` — understand what knowledge exists and where.

## Step 6 — Today's Daily Note

```powershell
$today = Get-Date -Format "yyyy-MM-dd"
Get-Content "<WORKSPACE_ROOT>\PersonalNotes\Daily\$today.md" -ErrorAction SilentlyContinue
```

If it exists: what happened today so far?

## Step 7 — Confirm Prime Complete

Run the preflight when possible:

```powershell
& "<WORKSPACE_ROOT>\tools\session\start-session.ps1"
```

Then respond with a brief status:

```
Prime complete ✅
- Role: James, CAO — [key responsibilities recalled]
- Memory: X permanent facts loaded
- Active plan: [plan title or "none"]
- Today: [summary of today's work or "no daily note yet"]
- Guard: [ok | warn | degraded | blocked]
- Ready to continue.
```
