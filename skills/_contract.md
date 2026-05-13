# Skill Packaging Contract

> Canonical definition for authoring, naming, and consuming skills in this workspace.
> Maintained by: James (CAO)
> See also: `CONTEXT.md` for the "skill" term definition.

---

## Overview

A skill is a reusable, self-contained operating procedure that James can inject into a sub-agent
prompt to provide domain expertise without requiring the sub-agent to read the file system itself.

Every skill lives in its own directory under `skills/` and ships as exactly **two files**:

| File | Format | Purpose |
|------|--------|---------|
| `SKILL.md` | Markdown | Human-readable procedure, templates, examples |
| `skill.yaml` | YAML | Machine-readable manifest for routing and tooling |

---

## Directory Layout

```
skills/
├── _contract.md               ← this file
├── <skill-id>/
│   ├── SKILL.md
│   └── skill.yaml
├── _drafts/                   ← promoted candidates (not yet active)
│   └── <candidate>/
│       ├── SKILL.md
│       └── skill.yaml
```

### Naming rules

- `<skill-id>` is kebab-case, lowercase, and unique across the `skills/` directory.
- `SKILL.md` is **always uppercase** (this matches the actual repo convention).
- `skill.yaml` is always lowercase.
- No other files in a skill directory (no README, no extra manifests).

---

## SKILL.md — Required Sections

```markdown
---
name: <skill-id>
description: "<one-sentence description>"
agent: <Agent | all>
tools_required: [<tool>, ...]
wiki_ref: "[[<wiki-slug>]]"   # optional — link to deep-dive wiki page
version: "<semver>"
---

# Skill: <Human Name>

**Category:** <category>
**Trigger:** <when to activate this skill>
**Owner:** <Agent>

## When to Use This Skill
...

## When to Use This Skill
...

## <Core Sections>
...

## Anti-patterns

List common misuses, edge cases where this skill does NOT apply, and failure modes to avoid.

## Checklist

A short pre-completion checklist the agent (or reviewer) runs before considering the skill output done.
Format: `- [ ] …` items.
```

All frontmatter fields listed above are required. `wiki_ref` is optional but encouraged when a
corresponding wiki page exists.

`## Anti-patterns` and `## Checklist` are **required** in every `SKILL.md`. Enforcement is automatic:
`uv run tools/wiki/wiki_lint.py` reports missing sections across all skills.

---

## skill.yaml — Required Fields

```yaml
id: <skill-id>          # matches directory name
name: <Human Name>
version: "<semver>"
owner: <Agent>
category: <category>
description: <one sentence>
triggers:               # list of lowercase keywords that activate this skill
  - keyword1
  - keyword2
inputs:
  - type: <spec|file|query|...>
    description: <what the skill expects>
outputs:
  - type: <report|python_script|diff|wiki_page|...>
    path: <optional expected output path>
    description: <optional>
tools_preferred:        # tools this skill's procedures rely on
  - <tool>
constraints: {}         # key: bool or string constraints
dependencies: []        # list of other skill IDs this skill depends on
```

---

## Pre-Injection Protocol (James → Sub-Agent)

Sub-agents do **not** read skill files themselves. James injects the relevant `SKILL.md` content
directly into the sub-agent's prompt under a `[SKILL CONTEXT]` header.

```python
# Canonical injection pattern (James applies this before every spawn)
skill_content = Path("skills/<skill-id>/SKILL.md").read_text(encoding="utf-8")
prompt = f"[SKILL CONTEXT]\n{skill_content}\n\n[TASK]\n{task_description}"
```

The `skill.yaml` manifest is used by tooling (e.g. `tools/agents/skill_candidates.py`,
`tools/agents/skill_stub_promotion.py`) for automated candidate detection and promotion reviews.
James reads `skill.yaml` for routing; sub-agents receive only the `SKILL.md` prose.

---

## Lifecycle: Draft → Active

1. New skill candidate? Create in `skills/_drafts/<skill-id>/` with both files.
2. Run `tools/agents/skill_candidates.py --print` to surface it for review.
3. After review, promote to `skills/<skill-id>/` and add to `team-config.yaml`.
4. Update `wiki/index.md` if a corresponding wiki page exists.

---

## Constraints

- **Do not** split a skill across multiple directories.
- **Do not** use `skill.md` (lowercase) — it will not be found by tooling that expects `SKILL.md`.
- **Do not** store runtime outputs in skill directories.
- **Do** update `team-config.yaml` when a new skill is promoted (see `skills` section).
