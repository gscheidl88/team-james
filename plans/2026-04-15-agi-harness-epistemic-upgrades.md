# AGI harness epistemic upgrades — synthetic eval fixture

> This file is a committed fixture for the public workflow eval harness.
> It preserves representative plan structure without depending on private session artifacts.

## Overview

This plan captures the structure of the AGI harness rollout and keeps the evaluation discipline visible in a portable form.

### Phase 4 — Eval harness

Build private workflow eval suites that can be rerun locally and in CI.
Do not mix capability evals and regression evals.

### Validation plan

- Run the private workflow eval suites after every meaningful orchestration change.
- Record failures in review artifacts rather than hiding them in chat.

### Replan rule

If a control cannot be validated by the eval harness, keep it in place until new evidence exists.

### Handoff state

- Current focus: eval harness structure and evidence discipline
- Next checkpoint: verify capability vs regression separation in repeatable artifacts

## Hypothesis Ledger

- Hypothesis: Hierarchical orchestration needs explicit eval discipline to stay stable.
  - Confidence: medium
  - Evidence: prior workflow drift without fixed review artifacts
  - Contradiction: none observed in this fixture
  - Next test: confirm repeatable suite execution on a fresh clone

## Checkpoint summary

- Open WIP: finish the public eval fixture set
- Open hypotheses: eval coverage is still narrower than runtime behavior
- Next test: re-run the public workflow harness

private workflow eval suites
typed handoffs
