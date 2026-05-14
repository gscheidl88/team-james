---
name: orchestration
description: "Standard delegation template, task metadata contract, checkpoint cadence, and model-routing rules for James when spawning sub-agents."
agent: James
tools_required: [task, read_agent, list_agents]
wiki_ref: "[[agent-team-setup]]"
version: "1.0"
---

# Skill: Orchestration

**Category:** Agent Management  
**Trigger:** Any task that James delegates to a sub-agent  
**Owner:** James (CAO)

---

## Purpose

This skill standardizes how James delegates work so sub-agents are traceable, reviewable, and easier to manage during execution.

---

## Delegation Contract

Every delegated task must include this metadata block:

```markdown
[TASK METADATA]
- task_id: <kebab-case-unique-id>
- goal: <one-sentence objective>
- dod: <measurable definition of done>
- verification_plan: <how the result will be checked>
- agent_role: <developer|analyst|researcher|qa|explore>
- requested_tools: <expected tool names for policy preflight>
- timeout_hint: <expected runtime or complexity hint>
- skill_context: injected below
- escalation_path: return to James
- model_override: <null or explicit model>
```

Use `model_override` only when the standard routing policy is intentionally bypassed.

---

## Delegation Template

```markdown
[ROLE]
You are the <specialist> leaf-agent for the owner's team. Do not spawn any sub-agents. Work directly and return the result to James.

[TASK METADATA]
- task_id: <kebab-case-unique-id>
- goal: <one-sentence objective>
- dod: <measurable definition of done>
- verification_plan: <how James will verify the result>
- agent_role: <delegated persona/role for policy preflight>
- requested_tools: <expected tool names for the delegated role>
- timeout_hint: <expected runtime or complexity hint>
- skill_context: injected below
- escalation_path: return to James
- model_override: <null or explicit model>

[ROUTING METADATA]
- complexity: <trivial|standard|complex|critical>
- task_type: <lookup|code|analysis|synthesis|decision>
- risk: <low|medium|high>
- cost_profile: <budget|normal|unlimited>
- verifiability: <high|medium|low>
- autonomy_level: <high|medium|low>
- primary_model: <recommended by model_router.py>
- verifier_model: <recommended by model_router.py or none>
- verification_need: <none|spot-check|full-review>

[PLAN STATE]
- plan_path: <plans/...md or n/a>
- assumptions: <short list or "see plan">
- validation_plan: <short list or "see plan">
- replan_rule: <when James should replan>
- handoff_state: <current state / next session start>

[HYPOTHESIS LEDGER]
- hypothesis: <current working hypothesis or n/a>
- confidence: <high|medium|low|uncertain>
- evidence: <best supporting evidence>
- contradiction: <best counter-signal or n/a>
- next_test: <most discriminating next check>

[FAILURE STATE]
- failure_class: <auth|tool|retrieval|logic|orchestration|none>
- fallback_action: <retry_once|fallback_path|escalate|absorb|n/a>
- escalate_when: <clear escalation trigger or n/a>

[SKILL CONTEXT]
<paste relevant SKILL.md content here>

[TASK]
<full task description with context, constraints, and expected output>

[RETURN FORMAT]
- concise conclusion
- files changed or recommended
- uncertainties / limitations
- explicit statement whether DoD was met
```

---

## Checkpoint Cadence

| Complexity | First check | Periodic check | Stall threshold |
|------------|-------------|----------------|-----------------|
| low | 15s | 45s | 90s without a new signal |
| medium | 30s | 90s | 180s without a new signal |
| high | 60s | 120s | 240s without a new signal |

James plans the first checkpoint before spawning. Delegation is never fire-and-forget.

For medium+ tasks, checkpoints should explicitly surface:

- `open_wip`
- `open_hypotheses`
- `blockers`
- `next_test`

---

## Stall Handling

If a sub-agent stops producing meaningful output:

1. Nudge once and request a concise status update.
2. If still stalled, decide one of:
   - retry with same settings
   - retry with a stronger model
   - stop and absorb the task directly
   - mark blocked with reason
3. Log the outcome in the plan and session artifacts.

---

## Model Routing Summary

Use `config/model-routing.yaml` as the source of truth.

Suggested helper:

```powershell
& "uv" run <WORKSPACE_ROOT>\tools\routing\model_router.py --complexity complex --task-type code --risk high
& "uv" run <WORKSPACE_ROOT>\tools\agents\cao_helper.py prepare --task-id example-task --goal "Implement the requested change." --dod "Tests pass and docs are updated." --verification-plan "Run workflow evals and inspect the diff." --agent-role developer --requested-tools view powershell --complexity complex --task-type code --risk high --skill-context-file <WORKSPACE_ROOT>\skills\orchestration\SKILL.md --json
```

- trivial tasks → economy model, no verifier
- standard tasks → standard model, verifier only if risk/uncertainty rises
- complex tasks → strong primary + spot-check verifier
- critical tasks → premium primary + mandatory verification or arbitration

For meaningful verification, prefer a cross-family verifier:

- Claude primary → GPT verifier
- GPT primary → Claude verifier

---

## Anti-patterns

- **Spawning sub-agents without task metadata** — no task_id, dod, or verification plan = untraceable, unacceptable.
- **Fire-and-forget delegation** — launching an agent without planning the first checkpoint; stall detection breaks.
- **Skipping skill injection** — spawning a leaf-agent without the relevant SKILL.md in the prompt; the agent makes assumptions.
- **Model override without logging** — using a non-routing-policy model without recording `model_override` in the task descriptor.
- **Merging multiple unrelated tasks into one spawn** — reduces traceability and makes DoD unclear.
- **Delegating to a sub-agent when a single tool call would suffice** — adds latency and complexity for no benefit.
- **Using context budget for a leaf-agent when an `explore` agent would do** — wastes premium model tokens on lookups.

---

## Checklist

Pre-completion checklist James runs before marking any delegated task done:

- [ ] Task descriptor includes `task_id`, `goal`, `dod`, `verification_plan`
- [ ] Relevant SKILL.md was injected into the sub-agent prompt
- [ ] Model was chosen per routing policy (or override is documented)
- [ ] First checkpoint was planned before spawn (not fire-and-forget)
- [ ] DoD verified: leaf-agent explicitly stated whether DoD was met
- [ ] Result checked by a cross-family verifier if risk ≥ medium
- [ ] Plan artifact updated (status → cc:完了 or blocked with reason)
- [ ] agent_trace.py used to log spawn/checkpoint/complete for medium+ tasks
