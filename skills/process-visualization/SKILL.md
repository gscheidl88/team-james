---
name: process-visualization
description: "Data-driven process visualization workflow: event log mining, Mermaid process maps, and BPMN draft export"
agent: James
tools_required: [uv, python]
wiki_ref: "[[bpmn-process-visualization]]"
version: "1.0"
---

# Skill: BPMN & Process Visualization

**Category:** Analysis + Engineering  
**Trigger:** Process discovery, BPMN drafting, workflow visualization, event-log analysis  
**Owner:** James / Analyst / Developer

---

## Purpose

Use this skill when James needs to turn event data into a structured process view.

The canonical first-line workflow is:

1. mine the event log into a process map,
2. inspect variants, transitions, and timing,
3. render Mermaid for fast review,
4. render HTML for interactive review and path explanation,
5. render D3 for deeper interactive exploration and bounded hierarchy collapse,
6. export BPMN draft XML for refinement.

---

## Inputs

Expected minimum columns:

- `case_id`
- `activity`

Recommended additional columns:

- `timestamp`
- `actor`
- `lane`
- `status`
- `lifecycle`
- `parent_activity` or a hierarchy/context field
- `activity_path` for stable hierarchy-aware node identity

Supported input formats for the first slice:

- CSV
- JSON list of event records

---

## Commands

```powershell
& "uv" run tools\process\event_log_to_process_map.py sources\process-visualization\sample-event-log.csv --case-id case_id --activity activity --timestamp timestamp --actor actor --out-json tools\process\outputs\sample-process-map.json --out-mermaid tools\process\outputs\sample-process-map.mmd

& "uv" run tools\process\process_map_to_html.py tools\process\outputs\sample-process-map.json --out tools\process\outputs\sample-process-map.html

& "uv" run tools\process\process_map_to_d3_viewer.py tools\process\outputs\sample-process-map.json --out tools\process\outputs\sample-process-map.d3.html

& "uv" run tools\process\process_map_to_bpmn.py tools\process\outputs\sample-process-map.json --out tools\process\outputs\sample-process-map.bpmn

& "uv" run tools\process\event_log_to_process_map.py sources\process-visualization\hierarchical-sample-event-log.csv --case-id case_id --activity activity --activity-path activity_path --parent-activity parent_activity --timestamp timestamp --actor actor --lifecycle lifecycle --out-json tools\process\outputs\hierarchical-process-map.json --out-mermaid tools\process\outputs\hierarchical-process-map.mmd
```

---

## What the workflow produces

- a process summary JSON
- transition frequencies
- variant analysis
- optional waiting-time metrics when timestamps exist
- Mermaid flowchart output
- self-contained HTML process report
- D3-powered HTML process viewer
- BPMN draft XML
- hierarchy-aware node IDs and group metadata when the log provides context fields

---

## Modeling boundaries

This workflow is **data-driven discovery first**, not full semantic modeling automation.

It is good for:

- as-is process discovery
- stakeholder review
- bottleneck spotting
- starting a BPMN modeling conversation

It is not sufficient on its own for:

- final BPMN governance
- exact business semantics
- exception modeling completeness
- full conformance checking
- true subprocess-faithful BPMN export from mined hierarchy

---

## Study-informed heuristics

The Stuttgart process-mining visualization study we ingested on 2026-04-26 adds four strong heuristics for this skill:

1. **Prefer visual trace explanation over raw trace dumps.**  
   When possible, use path highlighting, variant emphasis, or in-model trace overlays instead of relying on long text-only trace listings.

2. **Preserve hierarchy/context in event naming when the source system is nested.**  
   If events come from nested service calls, use contextual naming or fields that allow later decomposition into subprocess views. In this workspace, prefer `activity_path` for stable IDs and keep the visible activity label human-readable.

3. **Keep JSON as the stable handoff between mining and visualization.**  
   Mining tools should emit structured JSON first; Mermaid, D3, and BPMN exports should be downstream render layers.

4. **Treat interactive navigation as a core analysis feature.**  
   Zoom, pan, hot-path emphasis, and bounded hierarchy collapse/expand are not decoration; they are part of making mined models usable.

## Hierarchy-aware contract

- `process_map.json` keeps the existing top-level shape and adds hierarchy metadata.
- Activity identity is path-stable through `activity.id` and `activity.key`; viewers should not key nodes only by the visible label.
- Variants expose both human-readable `path` and stable `activity_ids`.
- Mermaid and BPMN remain draft/flat render layers even when hierarchy metadata exists.

---

## Recommended interpretation

Prefer language like:

- "The event log suggests these dominant paths."
- "This BPMN is a draft derived from observed transitions."
- "These variants should be reviewed with the process owner."

Avoid language like:

- "This is the final process definition."
- "The mined graph fully captures intent."

---

## Upgrade path

When the first slice proves useful, the next likely upgrades are:

1. PM4Py for stronger mining algorithms and conformance checks
2. richer HTML/D3 overlays for throughput, cost, and bottlenecks
3. richer BPMN XML/DI generation
4. optional workflow runtime integration via SpiffWorkflow

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