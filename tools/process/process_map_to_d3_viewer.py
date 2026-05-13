#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
process_map_to_d3_viewer.py - Render a mined process map JSON as a D3-powered HTML viewer.

Usage:
    uv run tools/process/process_map_to_d3_viewer.py PROCESS_MAP.json --out viewer.html
"""

from __future__ import annotations

import argparse
import json
from html import escape
from pathlib import Path


def build_html(process_map: dict) -> str:
    payload = json.dumps(process_map, ensure_ascii=False)
    title = escape(f"D3 process viewer — {process_map['meta'].get('source_path', 'event log')}")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #09111f;
      --panel: #10192b;
      --panel-soft: #172237;
      --text: #ecf2ff;
      --muted: #93a5c7;
      --accent: #6ee7ff;
      --accent-2: #84cc16;
      --warn: #f59e0b;
      --danger: #ef4444;
      --border: #293652;
      --lane-bg: rgba(255,255,255,0.025);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Inter, Segoe UI, Arial, sans-serif;
      background: linear-gradient(180deg, #09111f, #0f172a);
      color: var(--text);
    }}
    header {{
      padding: 22px 28px 16px;
      border-bottom: 1px solid var(--border);
      background: rgba(9, 17, 31, 0.92);
      position: sticky;
      top: 0;
      z-index: 10;
      backdrop-filter: blur(10px);
    }}
    h1 {{ margin: 0 0 8px; font-size: 28px; }}
    header p {{ margin: 0; color: var(--muted); }}
    main {{
      display: grid;
      gap: 18px;
      padding: 24px 28px 36px;
    }}
    .cards {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 14px;
    }}
    .card, .panel {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 16px;
      box-shadow: 0 10px 28px rgba(0,0,0,0.28);
    }}
    .card {{ padding: 16px 18px; }}
    .card .label {{
      color: var(--muted);
      font-size: 12px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }}
    .card .value {{
      margin-top: 8px;
      font-size: 30px;
      font-weight: 700;
    }}
    .layout {{
      display: grid;
      grid-template-columns: minmax(0, 2fr) minmax(340px, 1fr);
      gap: 18px;
      align-items: start;
    }}
    .panel {{ padding: 18px; }}
    .panel h2 {{ margin: 0 0 14px; font-size: 18px; }}
    .controls {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-bottom: 12px;
    }}
    select, button {{
      background: var(--panel-soft);
      border: 1px solid var(--border);
      color: var(--text);
      padding: 8px 10px;
      border-radius: 10px;
      font: inherit;
    }}
    button {{ cursor: pointer; }}
    .viewer {{
      position: relative;
      overflow: hidden;
      border-radius: 14px;
      background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0));
      min-height: 760px;
    }}
    svg {{
      width: 100%;
      height: 760px;
      display: block;
    }}
    .tooltip {{
      position: absolute;
      pointer-events: none;
      background: rgba(11, 17, 30, 0.96);
      border: 1px solid var(--border);
      color: var(--text);
      border-radius: 12px;
      padding: 10px 12px;
      font-size: 13px;
      line-height: 1.4;
      max-width: 300px;
      box-shadow: 0 16px 32px rgba(0,0,0,0.35);
      opacity: 0;
      transform: translateY(6px);
      transition: opacity 120ms ease, transform 120ms ease;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
    }}
    th, td {{
      text-align: left;
      padding: 10px 8px;
      border-bottom: 1px solid var(--border);
      vertical-align: top;
    }}
    th {{ color: var(--muted); font-weight: 600; }}
    .variant-row {{ cursor: pointer; }}
    .variant-row:hover {{ background: rgba(255,255,255,0.03); }}
    .hint {{
      color: var(--muted);
      font-size: 13px;
      margin-top: 12px;
    }}
    .pill {{
      display: inline-block;
      margin: 4px 6px 0 0;
      padding: 4px 8px;
      border-radius: 999px;
      background: var(--panel-soft);
      border: 1px solid var(--border);
      color: var(--muted);
      font-size: 12px;
    }}
    .path-step {{
      padding: 10px 12px;
      border: 1px solid var(--border);
      border-radius: 12px;
      background: rgba(255,255,255,0.02);
      margin-bottom: 10px;
    }}
    .path-step strong {{
      display: block;
      margin-bottom: 4px;
    }}
    code {{
      color: #c7d7f5;
      font-size: 12px;
    }}
    @media (max-width: 1100px) {{
      .layout {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>D3 process viewer</h1>
    <p>Interactive exploration layer for mined process data. Hierarchy metadata is real; Mermaid and BPMN remain flat/draft exports.</p>
  </header>
  <main>
    <section class="cards" id="cards"></section>
    <section class="layout">
      <div class="panel">
        <h2>Interactive process map</h2>
        <div class="controls">
          <select id="variantSelect"></select>
          <select id="groupSelect"></select>
          <button id="collapseGroup">Collapse group</button>
          <button id="resetCollapse">Reset collapse</button>
          <button id="resetVariant">Reset highlight</button>
          <button id="fitView">Fit view</button>
        </div>
        <div class="viewer">
          <svg id="graph" viewBox="0 0 1600 980" preserveAspectRatio="xMidYMid meet"></svg>
          <div class="tooltip" id="tooltip"></div>
        </div>
        <div class="hint">
          Node heat = activity count. Edge thickness = transition count. Variant highlighting uses stable node IDs. Collapse/expand is bounded to hierarchy path-prefix groups and resets exactly.
        </div>
      </div>
      <div class="panel">
        <h2>Variant explanation</h2>
        <div id="variantExplain" class="hint">Select a variant to inspect the exact step sequence, hierarchy context, and example case IDs.</div>
        <h2 style="margin-top:18px;">Hierarchy groups</h2>
        <div id="hierarchyGroups"></div>
      </div>
    </section>
    <section class="layout">
      <div class="panel">
        <h2>Variants</h2>
        <table>
          <thead><tr><th>Share</th><th>Path</th></tr></thead>
          <tbody id="variants"></tbody>
        </table>
      </div>
      <div class="panel">
        <h2>Current state</h2>
        <div id="stateSummary"></div>
      </div>
    </section>
  </main>

  <script src="https://d3js.org/d3.v7.min.js"></script>
  <script>
    const processMap = {payload};
    const hierarchy = processMap.hierarchy || {{ enabled: false, groups: [] }};
    const summary = processMap.summary;
    const cards = [
      ['Cases', summary.cases],
      ['Activities', summary.activities],
      ['Transitions', summary.transitions],
      ['Avg case length', summary.avg_case_length],
      ['Hierarchy groups', summary.hierarchy_groups ?? 0]
    ];

    document.getElementById('cards').innerHTML = cards.map(([label, value]) => `
      <article class="card">
        <div class="label">${{label}}</div>
        <div class="value">${{value}}</div>
      </article>
    `).join('');

    const collapseCandidates = (hierarchy.groups || []).filter(group => group.member_count > 1);
    document.getElementById('hierarchyGroups').innerHTML = hierarchy.enabled
      ? collapseCandidates.map(group => `<span class="pill">${{group.prefix}} · members=${{group.member_count}} · events=${{group.event_count}}</span>`).join('') || '<span class="hint">No collapsible hierarchy groups.</span>'
      : '<span class="hint">No hierarchy metadata in this process map.</span>';

    const variantSelect = document.getElementById('variantSelect');
    variantSelect.innerHTML = `<option value="">Highlight variant</option>` + processMap.variants.map((variant, index) =>
      `<option value="${{index}}">${{Math.round(variant.share * 100)}}% — ${{variant.path}}</option>`
    ).join('');

    const groupSelect = document.getElementById('groupSelect');
    groupSelect.innerHTML = `<option value="">Select hierarchy group</option>` + collapseCandidates.map(group =>
      `<option value="${{group.prefix}}">${{group.prefix}} (${{
        group.member_count
      }} nodes)</option>`
    ).join('');

    const variantsBody = document.getElementById('variants');
    variantsBody.innerHTML = processMap.variants.map((variant, index) => `
      <tr class="variant-row" data-index="${{index}}">
        <td>${{Math.round(variant.share * 100)}}%</td>
        <td>${{variant.path}}</td>
      </tr>
    `).join('');

    const svg = d3.select('#graph');
    const tooltip = d3.select('#tooltip');
    const width = 1600;
    const height = 980;
    const root = svg.append('g').attr('class', 'root');
    const laneLayer = root.append('g');
    const edgeLayer = root.append('g');
    const nodeLayer = root.append('g');

    const zoom = d3.zoom().scaleExtent([0.5, 2.2]).on('zoom', (event) => {{
      root.attr('transform', event.transform);
    }});
    svg.call(zoom);

    const rawActivities = processMap.activities.map(activity => ({{
      id: activity.id,
      label: activity.label,
      display: activity.label,
      count: activity.count,
      avg_position: activity.avg_position,
      lane: activity.suggested_lane || 'Unassigned',
      case_share: activity.case_share,
      actors: activity.actors,
      full_path: activity.full_path,
      hierarchy_parent: activity.hierarchy_parent,
      hierarchy_level: activity.hierarchy_level,
      type: 'activity'
    }}));
    const startNode = {{ id: '__START__', label: '__START__', display: 'Start', count: 0, avg_position: -1, lane: 'System', type: 'event' }};
    const endNode = {{ id: '__END__', label: '__END__', display: 'End', count: 0, avg_position: 99, lane: 'System', type: 'event' }};
    const rawLinks = processMap.transitions.map(transition => ({{
      ...transition,
      source_id: transition.source_id,
      target_id: transition.target_id
    }}));
    const state = {{
      selectedVariant: null,
      collapsedPrefix: '',
      currentGraph: null
    }};

    function mostCommonLane(nodes) {{
      const counts = new Map();
      for (const node of nodes) {{
        const lane = node.lane || 'Unassigned';
        counts.set(lane, (counts.get(lane) || 0) + node.count);
      }}
      let bestLane = 'Unassigned';
      let bestCount = -1;
      for (const [lane, count] of counts.entries()) {{
        if (count > bestCount) {{
          bestLane = lane;
          bestCount = count;
        }}
      }}
      return bestLane;
    }}

    function dedupeConsecutive(items) {{
      const out = [];
      for (const item of items) {{
        if (out.length === 0 || out[out.length - 1] !== item) {{
          out.push(item);
        }}
      }}
      return out;
    }}

    function computeDisplayGraph(collapsePrefix) {{
      const collapseMap = new Map();
      if (!collapsePrefix) {{
        return {{
          nodes: [startNode, ...rawActivities, endNode],
          links: rawLinks,
          collapseMap
        }};
      }}

      const group = collapseCandidates.find(candidate => candidate.prefix === collapsePrefix);
      if (!group) {{
        return {{
          nodes: [startNode, ...rawActivities, endNode],
          links: rawLinks,
          collapseMap
        }};
      }}

      const memberIds = new Set(group.member_ids);
      const memberNodes = rawActivities.filter(node => memberIds.has(node.id));
      const collapsedId = `__GROUP__:${{collapsePrefix}}`;
      for (const id of memberIds) {{
        collapseMap.set(id, collapsedId);
      }}

      const collapsedNode = {{
        id: collapsedId,
        label: group.label,
        display: `${{group.label}} (collapsed)`,
        count: memberNodes.reduce((sum, node) => sum + node.count, 0),
        avg_position: d3.mean(memberNodes, node => node.avg_position) || 0,
        lane: mostCommonLane(memberNodes),
        case_share: d3.mean(memberNodes, node => node.case_share) || 0,
        actors: [],
        full_path: group.prefix,
        hierarchy_parent: group.prefix.includes('::') ? group.prefix.split('::').slice(0, -1).join('::') : '',
        hierarchy_level: group.level,
        member_count: memberNodes.length,
        type: 'group'
      }};

      const visibleNodes = [startNode, ...rawActivities.filter(node => !memberIds.has(node.id)), collapsedNode, endNode];
      const nodeById = new Map(visibleNodes.map(node => [node.id, node]));
      const aggregated = new Map();

      for (const link of rawLinks) {{
        const mappedSource = collapseMap.get(link.source_id) || link.source_id;
        const mappedTarget = collapseMap.get(link.target_id) || link.target_id;
        if (mappedSource === mappedTarget) {{
          continue;
        }}
        const key = `${{mappedSource}}|||${{mappedTarget}}`;
        if (!aggregated.has(key)) {{
          aggregated.set(key, {{
            source_id: mappedSource,
            target_id: mappedTarget,
            source: nodeById.get(mappedSource)?.display || link.source,
            target: nodeById.get(mappedTarget)?.display || link.target,
            count: 0,
            case_share: 0,
            median_wait_seconds: null,
            mean_wait_seconds: null
          }});
        }}
        const entry = aggregated.get(key);
        entry.count += link.count;
        entry.case_share += link.case_share;
      }}

      return {{
        nodes: visibleNodes,
        links: [...aggregated.values()],
        collapseMap
      }};
    }}

    function renderVariantExplain(variant, mappedIds) {{
      const panel = document.getElementById('variantExplain');
      if (!variant) {{
        panel.innerHTML = '<span class="hint">Select a variant to inspect the exact step sequence, hierarchy context, and example case IDs.</span>';
        return;
      }}
      const collapsedNote = state.collapsedPrefix
        ? `<div class="pill">collapsed=${{state.collapsedPrefix}}</div><div class="pill">visible path=${{mappedIds.join(' → ')}}</div>`
        : '';
      panel.innerHTML = `
        <div class="pill">share=${{Math.round(variant.share * 100)}}%</div>
        <div class="pill">count=${{variant.count}}</div>
        <div class="pill">cases=${{variant.case_ids.join(', ') || 'n/a'}}</div>
        ${{collapsedNote}}
        <div style="margin-top:12px;">
          ${{
            variant.steps.map((step, index) => `
              <div class="path-step">
                <strong>${{index + 1}}. ${{step.label}}</strong>
                <div><code>${{step.full_path}}</code></div>
                <div class="hint">${{step.hierarchy_parent || 'flat activity'}}</div>
              </div>
            `).join('')
          }}
        </div>
      `;
    }}

    function renderStateSummary(graph) {{
      document.getElementById('stateSummary').innerHTML = `
        <div class="pill">collapsed=${{state.collapsedPrefix || 'none'}}</div>
        <div class="pill">visible nodes=${{graph.nodes.length}}</div>
        <div class="pill">visible edges=${{graph.links.length}}</div>
        <div class="pill">selected variant=${{state.selectedVariant === null ? 'none' : state.selectedVariant + 1}}</div>
      `;
    }}

    function showTooltip(event, html) {{
      tooltip.html(html)
        .style('opacity', 1)
        .style('transform', 'translateY(0)');
      const viewerRect = document.querySelector('.viewer').getBoundingClientRect();
      tooltip.style('left', (event.clientX - viewerRect.left + 16) + 'px')
        .style('top', (event.clientY - viewerRect.top + 16) + 'px');
    }}

    function hideTooltip() {{
      tooltip.style('opacity', 0).style('transform', 'translateY(6px)');
    }}

    function highlightVariant(index) {{
      state.selectedVariant = index;
      const edgeSelection = state.currentGraph.edgeSelection;
      const nodeSelection = state.currentGraph.nodeSelection;
      if (index === null) {{
        edgeSelection.attr('stroke', '#62789f').attr('opacity', 0.85);
        nodeSelection.attr('opacity', 1);
        renderVariantExplain(null, []);
        return;
      }}

      const variant = processMap.variants[index];
      if (!variant) {{
        return;
      }}
      const collapseMap = state.currentGraph.collapseMap;
      const mappedIds = dedupeConsecutive(variant.activity_ids.map(id => collapseMap.get(id) || id));
      const edgeSet = new Set();
      for (let i = 0; i < mappedIds.length - 1; i += 1) {{
        edgeSet.add(`${{mappedIds[i]}}|||${{mappedIds[i + 1]}}`);
      }}
      const nodeSet = new Set(mappedIds);

      edgeSelection
        .attr('stroke', d => edgeSet.has(`${{d.source_id}}|||${{d.target_id}}`) ? '#f59e0b' : '#384766')
        .attr('opacity', d => edgeSet.has(`${{d.source_id}}|||${{d.target_id}}`) ? 1 : 0.18);
      nodeSelection.attr('opacity', d => d.type === 'event' || nodeSet.has(d.id) ? 1 : 0.28);
      renderVariantExplain(variant, mappedIds);
    }}

    function renderGraph() {{
      const graph = computeDisplayGraph(state.collapsedPrefix);
      state.currentGraph = graph;
      renderStateSummary(graph);

      laneLayer.selectAll('*').remove();
      edgeLayer.selectAll('*').remove();
      nodeLayer.selectAll('*').remove();

      const laneOrder = ['System', ...new Set(graph.nodes.filter(node => node.type !== 'event').map(node => node.lane || 'Unassigned'))];
      const laneIndex = new Map(laneOrder.map((lane, index) => [lane, index]));
      const laneHeight = 170;
      const laneOffset = 60;
      const xScale = d3.scaleLinear()
        .domain([-1, d3.max(graph.nodes, d => d.avg_position) + 1])
        .range([110, width - 180]);
      const sizeScale = d3.scaleLinear()
        .domain([0, d3.max(graph.nodes.filter(node => node.type !== 'event'), d => d.count) || 1])
        .range([70, 140]);
      const heatScale = d3.scaleLinear()
        .domain([0, d3.max(graph.nodes.filter(node => node.type !== 'event'), d => d.count) || 1])
        .range(['#16304a', '#6ee7ff']);
      const edgeScale = d3.scaleLinear()
        .domain([0, d3.max(graph.links, d => d.count) || 1])
        .range([1.5, 8]);

      graph.nodes.forEach(node => {{
        node.x = xScale(node.avg_position);
        node.y = laneOffset + laneIndex.get(node.lane || 'System') * laneHeight + 46;
      }});

      laneLayer.selectAll('rect.lane')
        .data(laneOrder)
        .join('rect')
        .attr('class', 'lane')
        .attr('x', 42)
        .attr('y', lane => laneOffset - 10 + laneIndex.get(lane) * laneHeight)
        .attr('width', width - 84)
        .attr('height', laneHeight - 18)
        .attr('rx', 16)
        .attr('fill', (lane, index) => index % 2 === 0 ? 'rgba(255,255,255,0.02)' : 'rgba(255,255,255,0.035)')
        .attr('stroke', '#293652');

      laneLayer.selectAll('text.lane-label')
        .data(laneOrder)
        .join('text')
        .attr('class', 'lane-label')
        .attr('x', 62)
        .attr('y', lane => laneOffset + laneIndex.get(lane) * laneHeight + 18)
        .attr('fill', '#93a5c7')
        .attr('font-size', 14)
        .attr('font-weight', 600)
        .text(d => d);

      const nodesById = new Map(graph.nodes.map(node => [node.id, node]));
      graph.links = graph.links.map(link => ({{
        ...link,
        sourceNode: nodesById.get(link.source_id),
        targetNode: nodesById.get(link.target_id)
      }})).filter(link => link.sourceNode && link.targetNode);

      const edgeSelection = edgeLayer.selectAll('path.link')
        .data(graph.links)
        .join('path')
        .attr('class', 'link')
        .attr('fill', 'none')
        .attr('stroke', '#62789f')
        .attr('stroke-width', d => edgeScale(d.count))
        .attr('opacity', 0.85)
        .attr('d', d => {{
          const sourceWidth = d.source_id === '__START__' ? 36 : sizeScale(d.sourceNode.count);
          const targetWidth = d.target_id === '__END__' ? 36 : sizeScale(d.targetNode.count);
          const sx = d.sourceNode.x + (d.source_id === '__START__' ? 18 : sourceWidth / 2);
          const sy = d.sourceNode.y + (d.source_id === '__START__' ? 18 : 30);
          const tx = d.targetNode.x - (d.target_id === '__END__' ? -18 : targetWidth / 2);
          const ty = d.targetNode.y + (d.target_id === '__END__' ? 18 : 30);
          const mx = (sx + tx) / 2;
          return `M ${{sx}} ${{sy}} C ${{mx}} ${{sy}}, ${{mx}} ${{ty}}, ${{tx}} ${{ty}}`;
        }})
        .on('mousemove', (event, d) => showTooltip(event, `
          <strong>${{d.source}} → ${{d.target}}</strong><br>
          Count: ${{d.count}}<br>
          Case share: ${{Math.round((d.case_share || 0) * 100)}}%
        `))
        .on('mouseleave', hideTooltip);

      const nodeSelection = nodeLayer.selectAll('g.node')
        .data(graph.nodes)
        .join('g')
        .attr('class', 'node')
        .attr('transform', d => `translate(${{d.x}}, ${{d.y}})`)
        .on('mousemove', (event, d) => {{
          const html = d.type === 'activity' || d.type === 'group'
            ? `
                <strong>${{d.display}}</strong><br>
                Count: ${{d.count}}<br>
                Lane: ${{d.lane}}<br>
                Path: ${{d.full_path}}<br>
                ${{
                  d.type === 'group'
                    ? `Members: ${{d.member_count}}<br>`
                    : `Case share: ${{Math.round((d.case_share || 0) * 100)}}%<br>`
                }}
              `
            : `<strong>${{d.display}}</strong>`;
          showTooltip(event, html);
        }})
        .on('mouseleave', hideTooltip);

      nodeSelection.each(function(d) {{
        const group = d3.select(this);
        if (d.type === 'event') {{
          group.append('circle')
            .attr('r', 18)
            .attr('cx', 0)
            .attr('cy', 0)
            .attr('fill', d.id === '__START__' ? '#0f766e' : '#7c2d12')
            .attr('stroke', '#c7d7f5')
            .attr('stroke-width', 1.5);
          group.append('text')
            .attr('text-anchor', 'middle')
            .attr('y', 42)
            .attr('fill', '#ecf2ff')
            .attr('font-size', 12)
            .text(d.display);
        }} else {{
          const width = sizeScale(d.count);
          group.append('rect')
            .attr('x', -width / 2)
            .attr('y', -28)
            .attr('width', width)
            .attr('height', 58)
            .attr('rx', 14)
            .attr('fill', d.type === 'group' ? '#28435d' : heatScale(d.count))
            .attr('stroke', d.type === 'group' ? '#f59e0b' : '#d8f5ff')
            .attr('stroke-width', 1.1);
          group.append('text')
            .attr('text-anchor', 'middle')
            .attr('y', -6)
            .attr('fill', d.type === 'group' ? '#ecf2ff' : '#09111f')
            .attr('font-size', 12)
            .attr('font-weight', 700)
            .text(d.display.length > 24 ? d.display.slice(0, 24) + '…' : d.display);
          group.append('text')
            .attr('text-anchor', 'middle')
            .attr('y', 14)
            .attr('fill', d.type === 'group' ? '#dce8ff' : '#15324a')
            .attr('font-size', 11)
            .text(d.type === 'group' ? `members=${{d.member_count}} count=${{d.count}}` : `count=${{d.count}}`);
        }}
      }});

      state.currentGraph.edgeSelection = edgeSelection;
      state.currentGraph.nodeSelection = nodeSelection;
      highlightVariant(state.selectedVariant);
    }}

    function fitView() {{
      svg.transition().duration(250).call(
        zoom.transform,
        d3.zoomIdentity.translate(0, 0).scale(1)
      );
    }}

    document.getElementById('fitView').addEventListener('click', fitView);
    document.getElementById('resetVariant').addEventListener('click', () => {{
      variantSelect.value = '';
      highlightVariant(null);
    }});
    document.getElementById('collapseGroup').addEventListener('click', () => {{
      state.collapsedPrefix = groupSelect.value;
      renderGraph();
    }});
    document.getElementById('resetCollapse').addEventListener('click', () => {{
      state.collapsedPrefix = '';
      groupSelect.value = '';
      renderGraph();
    }});
    variantSelect.addEventListener('change', event => {{
      const value = event.target.value;
      highlightVariant(value === '' ? null : Number(value));
    }});
    variantsBody.querySelectorAll('.variant-row').forEach(row => {{
      row.addEventListener('click', () => {{
        variantSelect.value = row.dataset.index;
        highlightVariant(Number(row.dataset.index));
      }});
    }});

    renderGraph();
  </script>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a mined process map JSON as a D3-powered HTML viewer.")
    parser.add_argument("input", help="Process-map JSON file")
    parser.add_argument("--out", required=True, help="Output HTML path")
    args = parser.parse_args()

    process_map = json.loads(Path(args.input).read_text(encoding="utf-8"))
    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_html(process_map), encoding="utf-8")
    print(f"D3 viewer written → {output_path}")
    print(f"Cases: {process_map['summary']['cases']}")
    print(f"Activities: {process_map['summary']['activities']}")
    print(f"Transitions: {process_map['summary']['transitions']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
