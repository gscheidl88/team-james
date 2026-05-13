---
id: reversa-framework
type: research
title: "Reversa Framework"
tags: [reverse-engineering, tool-analysis, epistemics, skills, reversa]
domain: meta

is_project: false
project:

status: active
is_valid: true
valid_from: 2026-04-30
valid_to:
expired_at:
superseded_by:

confidence: high
reviewed_by:
review_date:

created: 2026-04-30
created_by: James
last_modified: 2026-04-30
modified_by: James
source: https://github.com/sandeco/reversa
ingest_session: "[[log#2026-04-30-research-reversa-framework]]"

relates_to:
  - "[[agent-orchestration-policy]]"
  - "[[tooling-policy]]"
  - "[[agent-ecosystem-upgrade-opportunities]]"
depends_on: []
---

## Overview

`sandeco/reversa` is a strong prompt-first reverse-engineering framework for legacy software projects, but it is not a good direct runtime fit for this workspace. The most valuable transferable pieces are its explicit evidence-marking convention and its phased reverse-engineering workflow. We therefore adapt the methodology into native skills and policy guidance while skipping the upstream installer and Node.js runtime.

# Reversa Framework

## What it is

`🟢 CONFIRMED` Reversa is a Node.js CLI plus prompt-only agent scaffold for reverse-engineering an existing software project into structured markdown specifications. The inspected upstream materials show a phase-based agent workflow, project-local state handling, and a large `_reversa_sdd/` documentation bundle as the primary output model.

`🟢 CONFIRMED` Its strongest operator value is methodological rather than technical-runtime depth: the repo organizes how an AI team should inspect a legacy codebase and report certainty, not how to perform hard static analysis automatically.

## Fit for this workspace

### Adopt

- `🟢 CONFIRMED` **Evidence markers** — `🟢 CONFIRMED`, `🟡 INFERRED`, and `🔴 GAP` are a clean operational upgrade for our epistemic-discipline standard.
- `🟢 CONFIRMED` **Scout / Detective / Architect workflow** — this maps well to our existing research + implementation flow and is now encoded as a native `reverse-engineering` skill.
- `🟢 CONFIRMED` **Git archaeology** as a first-class source of hidden rules and retroactive ADR clues.

### Adapt later if needed

- `🟡 INFERRED` **Traceability matrices** could become useful for larger codebase audits or migration work, but they are not necessary in the first adaptation slice.
- `🟡 INFERRED` **Tracer-style runtime evidence** may be worth exploring later if we build stronger tool-analytics or execution-observability workflows.

### Skip

- `🟢 CONFIRMED` **Upstream installer/runtime** — not worth adopting. It adds a Node.js workflow for a problem we can already solve natively.
- `🟢 CONFIRMED` **Large fixed document bundle generation** — too heavy for the usual scale of our repo/tool-fit investigations.
- `🟢 CONFIRMED` **State/resume model** — our `plans/`, handoff flow, and session lifecycle are already stronger.

## Why we adapt instead of install

- `🟢 CONFIRMED` Our workspace already has the stronger canonical layers: wiki, skills, plans, memory, evals, and reviewed agent orchestration.
- `🟢 CONFIRMED` Upstream `reversa` is very new and appears single-maintainer-driven, so borrowing the stable ideas is lower risk than depending on the runtime.
- `🟡 INFERRED` The full upstream pipeline is optimized for larger legacy-codebase reconstruction than the average tool-analysis task we run here.

## Native implementation slice

The current adaptation adds:

1. canonical evidence markers in `AGENTS.md` and `wiki/_schema.md`
2. `skills/reverse-engineering/` as a reusable workspace skill
3. this wiki page as the durable fit decision

## Recommendation

Use the native reverse-engineering skill whenever a tool, repo, or workflow is unfamiliar enough that we need explicit architecture reconstruction and evidence-tagged findings. Keep `reversa` itself as an external reference, not as a dependency.
