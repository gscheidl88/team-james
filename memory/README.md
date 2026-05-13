# memory/

This directory holds the persistent memory layers for your agent team.

## Files

| File | Purpose |
|------|---------|
| `USER.example.md` | Template — copy to `USER.md` and personalize |
| `MEMORY.example.md` | Template — copy to `MEMORY.md` and start adding facts |
| `USER.md` | **Your personal profile** — gitignored, never commit |
| `MEMORY.md` | **Persistent facts** — gitignored, never commit |

## Setup

```bash
cp memory/USER.example.md memory/USER.md
cp memory/MEMORY.example.md memory/MEMORY.md
```

Then edit both files with your personal details and initial facts.

## Why gitignored?

`USER.md` and `MEMORY.md` contain personal operating preferences and project-specific facts
that should not be shared publicly. The `.example.md` templates are the public-safe versions.
