# Wiki Frontmatter Schema

> **Purpose:** Standard frontmatter for all wiki pages.
> Enables knowledge graph queries via Obsidian Dataview and `tools/wiki/wiki_tool.py`.
> All agents must follow this schema when creating or updating wiki pages.

---

## Full Schema

```yaml
---
# ── Identity ──────────────────────────────────────────────
id: unique-slug-for-this-page          # kebab-case, unique across wiki/
type: research                          # see Types below
title: "Human readable title"
tags: [tag1, tag2]
domain: technical                       # see Domains below

# ── Project Context ───────────────────────────────────────
is_project: false                       # true if part of an active project
project:                                # project slug if is_project: true

# ── Lifecycle / Validity ──────────────────────────────────
status: active                          # see Status values below
is_valid: true                          # false = archived/superseded, keep for reference
valid_from: 2026-04-08                  # when this knowledge became current
valid_to:                               # null = still valid; set when superseded
expired_at:                             # date knowledge was *empirically* invalidated (Graphiti pattern)
superseded_by:                          # [[link-to-newer-page]] if replaced

# ── Quality / Confidence ──────────────────────────────────
confidence: high                        # high | medium | low
reviewed_by:                            # Gerhard | James | agent name
review_date:                            # date of last human review

# ── Provenance ────────────────────────────────────────────
created: 2026-04-08
created_by: James                       # James | Analyst | Developer | Researcher | Gerhard
last_modified: 2026-04-08
modified_by: James
source:                                 # URL or file path (for source-summary pages)
ingest_session:                         # [[log#entry-id]] link to log.md entry

# ── Knowledge Graph ───────────────────────────────────────
relates_to: []                          # [[page-slug]] links to related wiki pages
depends_on: []                          # knowledge that must be valid for this to hold

# ── Live Page (auto-refresh) ──────────────────────────────
live: false                             # true = body is auto-generated; do not edit manually
refresh_tool:                           # script name in tools/wiki/ (without .py), e.g. wiki_team_health_refresh
refresh_cadence: session                # session | weekly | manual
---
```

---

## Field Reference

### Types
| Value | Use |
|-------|-----|
| `research` | Research briefs, topic deep-dives, literature reviews |
| `analysis` | Data analysis, system evaluation, comparison studies |
| `documentation` | Setup docs, how-to guides, reference pages |
| `decision` | Architecture Decision Records (ADRs), strategic choices |
| `concept` | Definitions, mental models, frameworks |
| `source-summary` | Summary of a specific external document/article/paper |
| `reference` | Checklists, templates, lookup tables |

### Domains
| Value | Use |
|-------|-----|
| `personal` | Personal knowledge, self-improvement, goals |
| `technical` | Engineering, tooling, architecture, code |
| `research` | Research methodology, literature, academic |
| `business` | Strategy, analysis, competitive intelligence |
| `meta` | Agent team, workflow, memory system itself |

### Status Values
| Value | Meaning |
|-------|---------|
| `active` | Current, in use, being updated |
| `draft` | Work in progress, not yet reliable |
| `archived` | No longer active but kept for reference |
| `superseded` | Replaced by a newer page (set `superseded_by`) |

### `is_valid` vs `status`
- `status: archived` = the page is no longer being maintained
- `is_valid: false` = the *knowledge itself* is no longer accurate (e.g. a tool was deprecated, a decision was reversed)
- `expired_at` = the *date* the knowledge was empirically invalidated (distinct from `valid_to` which is a planned end-date). From Graphiti's temporal model.
- A page can be `status: active` but `is_valid: false` if it's actively documenting something that was disproven

### Evidence notation inside page body
- `🟢 CONFIRMED` = directly supported by inspected source, code, tool output, or artifact
- `🟡 INFERRED` = best-supported interpretation, but not directly evidenced
- `🔴 GAP` = missing evidence, unresolved ambiguity, or known unknown
- These markers complement frontmatter `confidence`; they do not replace it

---

## Dataview Query Examples

```dataview
TABLE title, status, confidence, last_modified
FROM "wiki"
WHERE is_valid = true
SORT last_modified DESC
```

```dataview
TABLE title, valid_from, superseded_by
FROM "wiki"
WHERE is_valid = false
```

```dataview
TABLE title, project, domain
FROM "wiki"
WHERE is_project = true AND status = "active"
```

---

## Agent Rules

1. Every wiki page **must** have complete frontmatter following this schema
2. Every wiki page **must** start with an `## Overview` section (L1, 2–5 sentences) immediately after the frontmatter — the frontmatter `description:` field is the L0 abstract (one line). This mirrors OpenViking's L0/L1/L2 depth model.
3. When updating a page: always update `last_modified` and `modified_by`
4. When superseding a page: set `is_valid: false`, `status: superseded`, `superseded_by: [[new-page]]`
5. When a fact is empirically disproven: set `expired_at:` to today's date, `is_valid: false`
6. When filing a new page: add an entry to `wiki/log.md` and update `wiki/index.md`
7. `confidence: low` pages must include a note explaining why confidence is low
8. Use `🟢 CONFIRMED`, `🟡 INFERRED`, and `🔴 GAP` markers in the page body when the distinction between direct evidence and inference matters
9. Pages with `live: true` are auto-generated — **do not edit the body manually**. To change content, modify the refresh script listed in `refresh_tool:`. Add sections to the page only in the frontmatter or Overview (which the script preserves).
