---
name: investment-research
description: "Educational workflow for factsheet and KID analysis, market-context synthesis, and structured investment-product comparison"
agent: Investment Analyst
tools_required: [view, web_fetch, web_search, powershell]
wiki_ref: ""
version: "1.0"
---

# Skill: Investment Research

**Category:** Research + Analysis  
**Trigger:** Fund analysis, factsheet review, KID/PRIIP interpretation, market-context comparison  
**Owner:** Investment Analyst / James / Researcher / Analyst

---

## Purpose

Use this skill when James or Investment Analyst needs to turn investment-product documents and market context
into a structured research brief without crossing into personalized financial advice.

The first-line workflow is:

1. ingest the factsheet or KID,
2. extract product facts and explicit risks,
3. interpret costs, risk class, and stated objective,
4. add market context relevant to the theme,
5. produce a comparison-ready summary with open questions.

---

## Inputs

Common inputs:

- PDF factsheet (`FS`)
- Key Information Document / PRIIP basis information sheet (`KID`, `BIB`)
- fund landing page or product description
- optional market-context query (rates, inflation, theme momentum, sector backdrop)

---

## Core Workflow

### 1. Document ingest

Prefer the local parser first:

```powershell
& "uv" run tools\investment\factsheet_parser.py "path\to\factsheet.pdf" --out-json tools\investment\outputs\factsheet.json
```

Capture at minimum:

- fund name
- ISIN
- document type
- data / factsheet date
- risk indicator if present
- cost fields if present
- missing-field warnings

### 2. Product structure

From the source documents, extract:

- stated objective and theme
- asset class and geography
- concentration signals
- fee / cost items
- risk indicator
- performance-scenario caveats

Use evidence markers:

- `🟢 CONFIRMED` for document-backed facts
- `🟡 INFERRED` for interpretation
- `🔴 GAP` for missing or unclear fields

### 3. Market-context synthesis

Add only the context needed to interpret the product:

- rates / inflation environment
- sector or theme momentum
- commodity / defense / AI / healthcare / water / mining context as applicable
- regulatory or geographic context where material

Keep market context separate from product facts.

### 4. Comparison output

When comparing products, prefer a matrix with:

- product / ISIN
- theme
- structure
- risk
- cost
- data freshness
- red flags
- open diligence questions

### 5. Due-diligence questions

Always end with questions such as:

- What exactly drives this fund's exposure?
- Are the costs justified relative to passive alternatives?
- How concentrated is the theme or manager risk?
- How current is the document set?
- What remains unverified from the provided documents?

---

## Required Response Shape

1. **Conclusion**
2. **Product facts**
3. **Market context**
4. **Risks and red flags**
5. **Open questions**
6. **Research-only footer**

---

## Boundaries

This skill is strong for:

- educational product analysis
- fund comparisons
- factsheet/KID interpretation
- market-context research
- advisor-prep question generation

This skill is **not** for:

- personalized buy/sell advice
- portfolio allocation
- tax or legal guidance
- guaranteed return claims

If the task drifts into suitability or personal recommendation, reframe it to:

- comparison
- clarification of trade-offs
- questions for a licensed advisor

---

## Minimal Checklist

- [ ] document-backed facts separated from interpretation
- [ ] data freshness noted
- [ ] risk and cost language explained plainly
- [ ] open questions listed
- [ ] research-only boundary stated

## Anti-patterns

- Do not activate this skill when a simpler direct answer or a different specialist skill is a better fit.
- Do not hide assumptions, uncertainty, or missing inputs behind confident-sounding prose.
- Do not skip the required validation, evidence, or operator handoff that makes the output usable.
- Do not turn examples into universal rules without checking whether the current task actually matches them.
## Checklist

- [ ] The skill matches the actual task trigger.
- [ ] Assumptions, limits, or unknowns are stated explicitly.
- [ ] Output format matches the operator need.
- [ ] Validation, evidence, or next-step guidance is included where relevant.