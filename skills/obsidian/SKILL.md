---
name: obsidian
description: "Obsidian CLI command reference for vault browsing and search — PRESENTATION ONLY, never use in automation scripts"
agent: Researcher
tools_required: [obsidian]
wiki_ref: "[[personal-notes-system]]"
version: "1.0"
note: "Obsidian = presentation, not plumbing. All file I/O in automation uses Add-Content or Python file writes."
---

# Skill: Obsidian CLI

**Category:** Knowledge Management  
**Trigger:** Any task involving Obsidian vault — creating notes, searching, tasks, daily notes, properties  
**Owner:** All agents (primarily Researcher + CAO)  
**Reference:** https://obsidian.md/help/cli

---

## Prerequisites

- Obsidian 1.12+ installed with installer version 1.12.7+
- CLI enabled: **Settings → General → Command line interface**
- Obsidian app must be running (first command will launch it if not)
- Vault: `<WORKSPACE_ROOT>` (default — CLI auto-detects when CWD is the vault)

---

## Vault Targeting

```shell
# When CWD is <WORKSPACE_ROOT> — vault is auto-detected, no flag needed
obsidian search query="meeting"

# Target by name explicitly
obsidian vault="<WORKSPACE_ROOT>" search query="meeting"
```

---

## Core Commands Reference

### Notes — Create, Read, Write

```shell
# Read the active file
obsidian read

# Read a specific file (by name or path)
obsidian read file=MyNote
obsidian read path="memory/MEMORY.md"

# Create a new note
obsidian create name="Note Title" content="# Title\n\nBody text"

# Create from template
obsidian create name="Project X" template=ProjectTemplate open

# Append to a note (adds a newline before content)
obsidian append file=MyNote content="New paragraph"

# Prepend content (after frontmatter)
obsidian prepend file=MyNote content="## Summary\n\nText here"

# Overwrite a file
obsidian create name=MyNote content="New content" overwrite

# Move / rename
obsidian move file=OldName to="archive/OldName"
obsidian rename file=OldName name="NewName"

# Delete (to trash by default)
obsidian delete file=MyNote
obsidian delete file=MyNote permanent
```

---

### Daily Notes

```shell
# Open today's daily note
obsidian daily

# Read today's daily note content
obsidian daily:read

# Append a task to today's daily note
obsidian daily:append content="- [ ] Review Q1 report"

# Prepend a note
obsidian daily:prepend content="## Morning Focus\n\n"
```

---

### Search

```shell
# Search vault — returns matching file paths
obsidian search query="revenue analysis"

# Search with line context (grep-style output)
obsidian search:context query="TODO"

# Search within a folder
obsidian search query="project" path="plans"

# Limit results
obsidian search query="report" limit=10

# Case-sensitive search
obsidian search query="KPI" case
```

---

### Tasks

```shell
# List all incomplete tasks in vault
obsidian tasks todo

# List tasks from today's daily note
obsidian tasks daily

# List tasks in a specific file
obsidian tasks file=MyNote

# List tasks with file paths and line numbers
obsidian tasks verbose

# Count all tasks
obsidian tasks total

# Toggle task completion (by file + line number)
obsidian task file=MyNote line=5 toggle

# Mark task done / todo
obsidian task file=MyNote line=5 done
obsidian task file=MyNote line=5 todo
```

---

### Properties (Frontmatter)

```shell
# Read a property from active file
obsidian property:read name=status

# Set a property
obsidian property:set name=status value=done
obsidian property:set name=tags value="analysis, q1" type=list
obsidian property:set name=priority value=1 type=number
obsidian property:set name=reviewed value=true type=checkbox

# Remove a property
obsidian property:remove name=draft

# List all properties in vault (with counts)
obsidian properties counts
```

---

### Tags

```shell
# List all tags with counts
obsidian tags counts

# Search files with a specific tag
obsidian tag name=analysis verbose
```

---

### Links & Graph

```shell
# List backlinks to a file
obsidian backlinks file=MyNote

# List outgoing links
obsidian links file=MyNote

# Find orphan notes (no incoming links)
obsidian orphans

# Find notes with no outgoing links
obsidian deadends

# Find unresolved links
obsidian unresolved
```

---

### Files & Vault Navigation

```shell
# List all files
obsidian files

# List files in a folder
obsidian files folder=plans

# List files by extension
obsidian files ext=md

# List all folders
obsidian folders

# Get file info
obsidian file file=MyNote

# Open a file in Obsidian
obsidian open file=MyNote
obsidian open file=MyNote newtab
```

---

### Output & Clipboard

```shell
# Copy any command output to clipboard
obsidian read file=MyNote --copy
obsidian search query="TODO" --copy

# Output as JSON (for scripting)
obsidian search query="meeting" format=json
obsidian tasks verbose format=json
obsidian tags counts format=json
```

---

## Agent Workflow Patterns

### Pattern 1: Log a finding to memory

```shell
# Append a new learning to MEMORY.md
obsidian append path="memory/MEMORY.md" content="\n- [2026-04-08] Key insight — context here"
```

### Pattern 2: Create a new plan note

```shell
obsidian create name="2026-04-08-analysis-plan" content="# Analysis Plan\n\n## Goal\n\n## Steps\n- [ ] Step 1" open
```

### Pattern 3: Daily standup — check today's tasks

```shell
obsidian tasks daily verbose
```

### Pattern 4: Search before creating (avoid duplicates)

```shell
obsidian search query="Q1 Revenue Report"
# If no result → create
obsidian create name="Q1 Revenue Report" open
```

### Pattern 5: Read + update a note in one workflow

```shell
# Read current state
obsidian read file="Project Status"

# Then append update
obsidian append file="Project Status" content="\n## 2026-04-08 Update\n\nAnalysis complete."
```

### Pattern 6: Tag-based knowledge retrieval

```shell
# Find all notes tagged with #analysis
obsidian tag name=analysis verbose

# Find notes tagged #todo
obsidian tag name=todo verbose
```

---

## Note Structure Convention (for this Vault)

All notes created by agents should follow this frontmatter template:

```markdown
---
created: 2026-04-08
agent: james | analyst | developer | researcher
tags: [tag1, tag2]
status: draft | active | archived
---

# Note Title

Content here.
```

---

## Multiline Content

Use `\n` for newlines and `\t` for tabs in content parameters:

```shell
obsidian create name=Note content="# Title\n\n## Section 1\n\nParagraph text.\n\n## Section 2\n\n- Item 1\n- Item 2"
```

---

## Output Checklist (after Obsidian operations)

- [ ] Note created/updated in correct folder
- [ ] Frontmatter properties set (created, agent, tags, status)
- [ ] Backlinks considered — did any existing note need updating?
- [ ] Important findings → also synced to `memory/MEMORY.md`

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