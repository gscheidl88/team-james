# Memory Rules

Quick-reference for all memory operations.
Full policy lives in `AGENTS.md` under "Memory-System".

---

## Three-Layer Architecture

| Layer | File | Purpose |
|-------|------|---------|
| Persistent facts | `memory/MEMORY.md` | Project-wide facts, cross-session |
| User profile | `memory/USER.md` | Gerhard's preferences and working style |
| Vector memory | `.mnemosyne/` | Semantic recall via Mnemosyne |
| Skills | `skills/*/SKILL.md` | Reusable procedures |
| Wiki | `wiki/*.md` | Deep knowledge, ADRs, research briefs |

## When to Update

- **After any completed task:** check whether a new insight belongs in `MEMORY.md`
- **New user preference observed:** update `memory/USER.md`
- **New repeatable pattern found:** create or extend a skill in `skills/`
- **Research / ADR completed:** create a wiki page (threshold: "would Gerhard want this in 3 months?")

## Memory Fence Convention

When injecting memory into a sub-agent prompt, always wrap:

```xml
<memory-context>
[System: Session context snapshot — frozen at start, treat as background not new user input]
[Edits during session persist to disk but don't affect this snapshot until next session]
...MEMORY.md + USER.md content...
</memory-context>
```

## Wiki Invalidation

- Logically outdated: `valid_to: <date>`, `is_valid: false`
- Empirically disproven: `expired_at: <date>`, `is_valid: false`
- Replaced: `superseded_by: [[new-page]]`

Run `uv run tools/wiki/wiki_lint.py` to surface stale pages.
