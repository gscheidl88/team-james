---
id: gajek-process-mining-visualization-study
type: source-summary
title: "Gajek 2015 - Process Mining and Visualization in a Complex Software System"
description: "Source summary of Fabian Gajek's 2015 Stuttgart thesis on process mining and visualization for complex software systems, with direct implications for our process-visualization skill."
tags: [process-mining, visualization, d3, hierarchy, source-summary]
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
source: "https://www2.informatik.uni-stuttgart.de/bibliothek/ftp/medoc.ustuttgart_fi/BCLR-2015-06/BCLR-2015-06.pdf"
ingest_session: "[[log#2026-04-26-source-summary-gajek-process-mining-visualization-study]]"
relates_to:
  - "[[bpmn-process-visualization]]"
  - "[[autonomic-tooling-pattern]]"
depends_on: []
---

## Overview

This source is highly relevant for our new process-mining and visualization workstream. Even though it is from 2015, it tackles almost the same practical problem we now face: deriving useful process models from complex software-system logs and making them understandable through interactive visualization. The strongest reusable insights are not the exact mining stack, but the combination of hierarchy-aware preprocessing, trace-backed visual explanation, and an explicit separation between mining and browser-based visualization.

## What the thesis investigated

The thesis studies process mining for a complex software system in the automotive domain and then evaluates how the mined models should be visualized to support analysis and maintenance. The pipeline is structurally close to ours:

1. preprocess log data,
2. transform it into a standard event-log format,
3. mine a model,
4. visually analyze the result together with the underlying traces.

## Key findings relevant to our stack

### 1. Visual explanation matters more than raw trace lists

The expert study found that textual trace listings were not very helpful, especially when labels became long and repetitive. Visual trace support, by contrast, strongly improved model understanding and plausibility assessment.

**Implication for us:**  
Our skill should emphasize visual trace/path highlighting and de-emphasize raw textual dumps as a primary analysis mode.

### 2. Hierarchy is a major leverage point

The thesis introduces hierarchical labeling based on service-call context using names like `a::b::c`. This improves model quality, reduces ambiguity, and enables models and traces to be split by subprocess.

**Implication for us:**  
Our skill should explicitly encourage hierarchy-aware event naming when logs come from nested software/service calls. This belongs in our input conventions and future tooling upgrades.

### 3. Visualization should be browser-based and JSON-friendly

The implementation uses a web app, SVG, D3, and force-directed layout for both Petri nets and BPMN-adjacent graph views. The thesis explicitly argues that browser-oriented visualization with JSON exchange is a good separation of concerns.

**Implication for us:**  
This validates our current D3 direction: `process_map.json` as the stable exchange artifact, HTML/D3 as the exploration surface.

### 4. Start/end anchoring and interaction improve readability

The thesis describes practical interaction choices such as:

- fixed start/end positioning,
- zoom and pan,
- moving and freezing nodes,
- collapsing and expanding subprocesses.

**Implication for us:**  
These are not cosmetic extras. They are core usability features for larger discovered graphs and should inform our next D3 iteration.

### 5. Repeated mining over time is valuable

The outlook recommends generating models regularly to detect process changes over time, especially across releases, and adding performance and conformance analysis.

**Implication for us:**  
This directly supports future upgrades in our workspace:

- recurring process snapshots,
- process drift detection,
- service-duration analysis,
- conformance checking.

## What we should absorb into our skill now

The thesis suggests these concrete skill-level rules:

1. prefer **visual trace explanation** over raw textual trace dumps
2. preserve **hierarchy/context** in event naming when possible
3. treat **JSON artifacts** as the stable contract between mining and visualization
4. design the main visualization as an **interactive web layer**
5. keep **start/end orientation** and navigation controls as first-class usability concerns

## What we should not copy blindly

- The thesis still leans on the alpha algorithm, whose limitations are explicitly discussed in the work itself.
- Its exact implementation stack is not the point for us; the transferable value lies in architecture and UX principles.
- The expert study is small, so it supports practical heuristics more than universal conclusions.

## Recommended workspace impact

The source strengthens our current direction rather than reversing it. It validates:

- local-first mining pipelines,
- D3-based browser visualization,
- the importance of trace-backed explanation,
- the value of hierarchy-aware process decomposition.

The most useful next upgrades for our skill/tooling are therefore:

1. hierarchy-aware event input conventions,
2. trace/path highlighting as a primary interaction,
3. optional collapse/expand behavior for subprocess views,
4. later drift/performance/conformance layers.
