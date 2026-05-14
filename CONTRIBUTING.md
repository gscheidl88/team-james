# Contributing to Team_James

## Principles

- Keep the repo local-first, markdown-first, and automation-light.
- Prefer clear operating contracts over hidden prompt behavior.
- Separate reusable framework assets from personal or runtime-only state.
- Use English for files, docs, and comments.
- Keep operator chat assumptions out of committed artifacts unless they become durable policy.

## Development workflow

1. Read `AGENTS.md`, `memory/MEMORY.md`, and `memory/USER.md` before major work.
2. For multi-step work, use a plan in `plans/`.
3. Update durable policy in the canonical source, not only in chat.
4. When behavior changes, update the matching docs or examples.
5. Keep changes surgical and avoid unrelated cleanup.

## Tooling

Use `uv run` for local scripts.

Common commands:

```powershell
uv run tools\wiki\wiki_lint.py --strict
uv run --python 3.12 tools\evals\run_workflow_evals.py
uv run --python 3.12 tools\evals\run_ablation_review.py
uv run --python 3.12 tools\evals\extract_backfill_cases.py --inputs plans\2026-04-15-agi-harness-epistemic-upgrades.md plans\2026-04-15-eval-backfill-and-repo-publish.md PersonalNotes\Daily\2026-04-15.md --output evals\backfill\generated-pilot.json
```

## Content conventions

- `agents/` defines agent roles and responsibilities.
- `config/` holds machine-readable policy and routing.
- `evals/` holds suites, fixtures, and normalized backfilled cases.
- `memory/` holds durable memory plus example templates for publishable setups.
- `plans/_template-*.md` files are reusable; session-specific plans stay local.
- `wiki/` pages require full frontmatter and an `## Overview` section.

## Before opening a change

- Run the relevant existing local scripts.
- Ensure generated outputs stay ignored.
- Do not add secrets, personal notes, or vault metadata.
- Preserve the distinction between capability evals and regression evals.

## Pull request expectations

- Explain the user-visible or operator-visible effect.
- Mention the canonical files changed.
- Call out any publish-surface or privacy impact.
- Use conventional commit style for PR titles when possible (`feat:`, `fix:`, `docs:`, `chore:`).
- Include the exact validation commands you ran.
