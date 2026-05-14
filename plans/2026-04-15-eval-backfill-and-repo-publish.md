# Eval backfill and repo publish — synthetic eval fixture

> This file is a committed fixture for the public workflow eval harness.
> It keeps the original structure-based assertions while removing private operator context.

## Overview

Pilot-extract 5 real cases and validate quality before broadening the published eval corpus.

### Source priority

1. reusable plans
2. public-safe daily note fixtures
3. committed wiki pages

### Validation plan

- confirm that the extracted cases are schema-valid
- keep handoff state visible in the plan itself
- ensure the fixture still demonstrates the public publish review path

### Replan rule

If the extracted cases depend on local-only notes or plans, replace them with committed synthetic fixtures first.

### Handoff state

- Current phase: converting private backfill evidence into public-safe fixtures
- Remaining gap: preserve structure without leaking local-only context

## Hypothesis Ledger

- Hypothesis: A small committed fixture set can preserve the same review signals as private artifacts.
  - Confidence: medium
  - Evidence: the eval harness only needs stable text anchors, not sensitive history
  - Contradiction: fixture drift can hide real regressions if not maintained
  - Next test: re-run workflow evals after fixture migration

## Checkpoint summary

- Open WIP: fixture migration
- Open hypotheses: synthetic fixtures may miss nuance from the private originals
- Next test: compare workflow eval output before and after migration
