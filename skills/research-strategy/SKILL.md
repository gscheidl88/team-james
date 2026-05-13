---
name: research-strategy
description: "Research workflow (FRAME→GATHER→SYNTHESIZE→RECOMMEND), ADR templates, SWOT/OKR frameworks, memory update protocol"
agent: Researcher
tools_required: []
wiki_ref: "[[karpathy-llm-wiki-pattern]]"
version: "1.0"
---

# Skill: Research & Strategy

**Category:** Knowledge & Strategy  
**Trigger:** Any research, strategic analysis, concept design, or documentation task  
**Owner:** Researcher Agent

---

## When to Use This Skill

- Market or technology research
- Competitive landscape analysis
- Strategic recommendations
- Writing proposals, concepts, or whitepapers
- Designing processes or frameworks
- Rapid domain learning and synthesis
- Decision documentation (Architecture Decision Records)

---

## Standard Research Workflow

```
1. FRAME       → Define the exact question (avoid scope creep)
2. GATHER      → Collect sources — web, docs, internal knowledge
3. SYNTHESIZE  → Find patterns, contradictions, gaps
4. EVALUATE    → Weight evidence, identify assumptions
5. RECOMMEND   → One clear recommendation + rationale
6. DOCUMENT    → Record the finding for the team's memory
```

---

## Research Brief Template

```markdown
## Research Brief: {Topic}

**Question:** {The specific question we need to answer}
**Requestor:** {Who needs this}
**Date:** {YYYY-MM-DD}

### Key Findings
1. {Finding with evidence}
2. {Finding with evidence}
3. {Finding with evidence}

### Recommendation
{Clear, actionable recommendation}

### Assumptions & Risks
- {Assumption 1}
- {Risk 1}

### Sources
- [{source title}]({url})
```

---

## Decision Record Template (ADR)

```markdown
## ADR-{number}: {Short title}

**Date:** {YYYY-MM-DD}
**Status:** Proposed | Accepted | Deprecated | Superseded by ADR-{n}

### Context
{What situation or problem forced this decision?}

### Options Considered
| Option | Pros | Cons |
|--------|------|------|
| A | ... | ... |
| B | ... | ... |

### Decision
{What was chosen and why}

### Consequences
{What becomes easier / harder as a result}
```

---

## Strategy Frameworks (Quick Reference)

### SWOT
```
Strengths    | Weaknesses
-------------|------------
Opportunities| Threats
```

### OKR
```
Objective: {Inspiring qualitative goal}
  KR1: {Measurable result by date}
  KR2: {Measurable result by date}
```

### Problem → Solution Map
```
Problem: {Precise problem statement}
Root Cause: {Why does it exist?}
Solution Options: [A] [B] [C]
Chosen: {Option} because {rationale}
Success Metric: {How do we know it worked?}
```

---

## Anti-patterns

- **Searching before framing** — starting data collection without a precise question leads to scope creep and wasted time.
- **Treating the first credible source as truth** — always cross-check claims across ≥2 independent sources.
- **Confirmation bias** — only gathering evidence that supports the initial hypothesis; actively seek contradictions.
- **Burying the conclusion** — leading with background and saving the recommendation for the end; use pyramid principle.
- **Claiming certainty without evidence** — every assertion must be tagged (🟢 CONFIRMED / 🟡 INFERRED / 🔴 GAP) for medium+ research tasks.
- **Skipping the memory update** — finishing research without updating `memory/MEMORY.md` or a wiki page means the knowledge is lost.
- **ADR without options considered** — recording only the chosen option; always document what was rejected and why.

---

## Checklist

- [ ] Research question was explicitly framed (FRAME step complete)
- [ ] ≥2 independent sources consulted for key claims
- [ ] Contradictions and gaps explicitly noted
- [ ] Lead with conclusion (pyramid principle applied)
- [ ] Every key claim tagged: 🟢 CONFIRMED / 🟡 INFERRED / 🔴 GAP
- [ ] Recommendation is actionable (who does what)
- [ ] Reusable knowledge added to `memory/MEMORY.md` or wiki page created

---

## After Research: Memory Update

If the research revealed reusable knowledge, add to `memory/MEMORY.md`:

```markdown
- [YYYY-MM-DD] {Key insight} — Source: {url or context}
```
