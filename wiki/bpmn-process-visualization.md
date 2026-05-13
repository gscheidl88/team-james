---
id: bpmn-process-visualization
type: documentation
title: "BPMN and Process Visualization"
description: "Local-first approach for BPMN-oriented, data-driven process visualization: mine event logs, visualize process maps, and export BPMN drafts."
tags: [bpmn, process-mining, visualization, process-analysis, workflow]
domain: technical
is_project: false
project:
status: active
is_valid: true
valid_from: 2026-04-26
valid_to:
expired_at:
superseded_by:
confidence: high
reviewed_by: James
review_date: 2026-04-26
created: 2026-04-26
created_by: James
last_modified: 2026-04-26
modified_by: James
source: "OMG BPMN 2.0 spec + PM4Py + SpiffWorkflow + bpmn-visualization research synthesized for local workspace use"
ingest_session: "[[log#2026-04-26-documentation-bpmn-process-visualization]]"
relates_to:
  - "[[tooling-policy]]"
  - "[[autonomic-tooling-pattern]]"
  - "[[windows-hardware-triage]]"
  - "[[gajek-process-mining-visualization-study]]"
depends_on: []
---

## Overview

This page defines the first local-first BPMN and process-visualization strategy for the workspace. The guiding pattern is simple: start from event data, mine the as-is process into an inspectable process map, render a lightweight reviewable visualization, and only then export BPMN as a draft artifact for refinement. That keeps the first slice token-free, reproducible, and useful even before adopting heavier process-mining runtimes.

## Research conclusion

The research converges on three layers:

1. **BPMN 2.0** as the canonical interchange and communication format
2. **Process mining** as the data-driven discovery layer
3. **Visualization overlays** as the operational analysis layer

For this workspace, the best first-line local stack is:

- local CSV/JSON event logs
- a local mining step
- Mermaid for rapid review
- HTML for interactive review and explicit path explanation
- D3 viewer for exploratory analysis and bounded hierarchy collapse/expand
- BPMN draft export for stakeholder-facing refinement

## Core BPMN elements worth encoding

The first local slice should work with the BPMN concepts that matter most operationally:

- start and end events
- tasks / activities
- sequence flows
- exclusive branching / merging
- pools and lanes as future enrichment
- data overlays as metrics rather than as primary modeling objects

## Recommended workspace architecture

### Phase 1 - local-first discovery

- `tools\process\event_log_to_process_map.py`
- `tools\process\process_map_to_html.py`
- `tools\process\process_map_to_d3_viewer.py`
- `tools\process\process_map_to_bpmn.py`
- `skills\process-visualization\`
- `skills\d3-process-viewer\`

This phase is optimized for inspectability, version control, and quick review.

The current implementation now also supports **hierarchy-aware discovery**:

- optional `activity_path` / `parent_activity` fields for nested service/process context
- stable node IDs in `process_map.json` so repeated leaf labels under different parents do not collide
- explicit hierarchy group metadata for viewer-side path-prefix collapse/expand
- visual variant/path explanation in both HTML and D3 outputs

### Phase 2 - stronger mining

Recommended future upgrade:

- PM4Py for richer discovery, conformance, and enhancement

This should only become default once the first slice proves useful enough to justify the extra dependency and AGPL implications. D3 is now the lighter-weight step before that: it adds interactive process exploration without forcing a new Python mining dependency.

### Phase 3 - runtime / execution

Recommended future upgrade:

- SpiffWorkflow when BPMN execution or workflow runtime behavior matters

This is a different concern from process discovery and should stay separate until the workspace actually needs execution semantics.

## Why not jump directly to heavy BPMN tooling

The first need is not enterprise BPM governance. It is a reliable, inspectable way for James to turn event data into a process view and communicate that view cleanly. Heavy BPM suites solve more than the current problem and would add runtime weight before the local workflow has proven its value.

## What the current tooling is for

The current process-visualization slice is good for:

- as-is process discovery
- variant and transition analysis
- reviewable process diagrams
- self-contained interactive process reports
- D3-based hot-path and variant exploration
- a draft BPMN starting point

It is not yet the right layer for:

- final BPMN semantics
- full conformance checking
- enterprise approval workflows
- live execution dashboards

## Additional guidance from the Stuttgart study

The 2015 Stuttgart thesis on process mining and visualization in a complex software system strongly reinforces our current direction:

- visual trace/path support matters more than raw textual trace dumps
- hierarchy-aware naming is useful when software events come from nested service calls
- JSON as the interchange layer between mining and browser visualization is a good architectural split
- D3-style interactive web visualization is the right place for zoom, pan, path emphasis, and later subtree expansion

That guidance is now implemented in a bounded first pass:

1. hierarchy-aware node identity is additive in the miner,
2. path explanation is visible in HTML and D3,
3. D3 collapse/expand is limited to path-prefix groups with deterministic reset,
4. Mermaid and BPMN remain explicitly flat/draft exports instead of pretending to be faithful subprocess models.

This means our skill should continue to optimize for:

1. data-first discovery,
2. visual explanation of why the model looks the way it does,
3. hierarchy-aware process decomposition when the source logs support it.

## Canonical commands

```powershell
& "uv" run tools\process\event_log_to_process_map.py sources\process-visualization\sample-event-log.csv --case-id case_id --activity activity --timestamp timestamp --actor actor --out-json tools\process\outputs\sample-process-map.json --out-mermaid tools\process\outputs\sample-process-map.mmd

& "uv" run tools\process\process_map_to_html.py tools\process\outputs\sample-process-map.json --out tools\process\outputs\sample-process-map.html

& "uv" run tools\process\process_map_to_d3_viewer.py tools\process\outputs\sample-process-map.json --out tools\process\outputs\sample-process-map.d3.html

& "uv" run tools\process\process_map_to_bpmn.py tools\process\outputs\sample-process-map.json --out tools\process\outputs\sample-process-map.bpmn

& "uv" run tools\process\event_log_to_process_map.py sources\process-visualization\hierarchical-sample-event-log.csv --case-id case_id --activity activity --activity-path activity_path --parent-activity parent_activity --timestamp timestamp --actor actor --lifecycle lifecycle --out-json tools\process\outputs\hierarchical-process-map.json --out-mermaid tools\process\outputs\hierarchical-process-map.mmd
```

## Sources

- BPMN 2.0 specification and XML schema at OMG
- PM4Py as the strongest local Python process-mining path
- SpiffWorkflow as the strongest Python BPMN runtime path
- bpmn-visualization as the visualization-overlay reference pattern
