---
name: d3-process-viewer
description: "Generate D3-based local HTML viewers from mined process-map JSON for interactive process exploration"
agent: James
tools_required: [uv, python, browser]
wiki_ref: "[[bpmn-process-visualization]]"
version: "1.0"
---

# Skill: D3 Process Viewer

**Category:** Visualization  
**Trigger:** Interactive process-map exploration, hot-path analysis, variant inspection  
**Owner:** James / Developer

---

## Purpose

Use this skill when Mermaid is no longer enough for process analysis.

The D3 viewer is the next visualization layer after process-map JSON:

1. mine event data into `process_map.json`
2. generate a D3 HTML viewer
3. inspect hot paths, lane ownership, and variants interactively

---

## Command

```powershell
& "uv" run tools\process\process_map_to_d3_viewer.py tools\process\outputs\sample-process-map.json --out tools\process\outputs\sample-process-map.d3.html
```

---

## What it adds over Mermaid

- edge-width encoding for transition frequency
- node heat for activity counts
- tooltips with process metrics
- zoom and pan
- variant highlighting

---

## Boundaries

- local static HTML only
- D3 is loaded from CDN in the current first slice
- this is an analysis viewer, not a final BPMN renderer
- no separate visualization agent role is required at current scope

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