---
created: YYYY-MM-DD
owner: James
status: active
tags: [plan, complex-task]
---

# Complex task plan

## Problem

Briefly describe the problem, desired outcome, and why the task is non-trivial.

## Approach

1. Describe the execution strategy.
2. Describe how progress will be validated.
3. Describe what would trigger replanning.

## State and legibility

Canonical field names for automation and review:

- `assumptions`
- `validation_plan`
- `replan_rule`
- `handoff_state`

## Hypothesis Ledger

Use this section for medium+ research, analysis, and decision work.

| Hypothesis | Confidence | Evidence | Contradiction | Next test |
|------------|------------|----------|---------------|-----------|
| Example claim | medium | Supporting observation or source | Counter-signal or unresolved tension | Most discriminating next check |

### Assumptions

- Assumption:
- Assumption:

### Validation plan

- Deterministic checks:
- Review / verifier check:
- Runtime or behavioral check:

### Replan rule

- Replan when:
- Escalate when:
- Absorb directly when:

### Handoff state

- Current state:
- Open WIP:
- Blockers:
- Next session start:

## Tasks

| ID  | Task | DoD | Status |
|-----|------|-----|--------|
| 1.1 | Example task | measurable deliverable | cc:TODO |

---

## Phases (for multi-deliverable tasks)

Use this section when work is too large to deliver atomically. Each phase must be independently valuable.

| Phase | Name | Deliverable | DoD | Status |
|-------|------|-------------|-----|--------|
| MVP | Minimum viable | Smallest slice that provides value | Works end-to-end | cc:TODO |
| Core | Full feature set | All happy-path requirements met | Tested + documented | cc:TODO |
| Edge | Edge cases & hardening | Known failure modes handled | Regression covered | cc:TODO |
| Opt | Optimization | Performance / ergonomics improvements | Measurable gain | cc:TODO |

> **Rule:** Never start the next phase until the previous phase's DoD is met. Each phase is releasable.

## Checkpoint summary

Use this block during checkpoints and handoffs:

```markdown
### Checkpoint Summary
- Open WIP:
- Open hypotheses:
- Blockers:
- Next test:
```

## Notes

- Keep the plan concise and operational.
- Complex tasks should use this structure instead of relying on prompt-only context.
