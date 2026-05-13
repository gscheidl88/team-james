#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
process_map_to_html.py - Render a mined process map JSON as a self-contained HTML report.

Usage:
    uv run tools/process/process_map_to_html.py PROCESS_MAP.json --out report.html
"""

from __future__ import annotations

import argparse
import json
from html import escape
from pathlib import Path


def build_html(process_map: dict) -> str:
    payload = json.dumps(process_map, ensure_ascii=False)
    title = escape(f"Process report — {process_map['meta'].get('source_path', 'event log')}")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #0b1020;
      --panel: #131a2c;
      --panel-soft: #1a2338;
      --text: #ecf2ff;
      --muted: #9eb0d1;
      --accent: #6ee7ff;
      --accent-2: #84cc16;
      --warn: #f59e0b;
      --border: #2a3550;
      --edge: #5b709a;
      --edge-dim: #34435f;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Inter, Segoe UI, Arial, sans-serif;
      background: linear-gradient(180deg, #09101d 0%, #0f172a 100%);
      color: var(--text);
    }}
    header {{
      padding: 24px 28px 16px;
      border-bottom: 1px solid var(--border);
      background: rgba(11, 16, 32, 0.9);
      position: sticky;
      top: 0;
      backdrop-filter: blur(10px);
      z-index: 10;
    }}
    header h1 {{ margin: 0 0 6px; font-size: 28px; }}
    header p {{ margin: 0; color: var(--muted); }}
    main {{
      padding: 24px 28px 40px;
      display: grid;
      gap: 20px;
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
      box-shadow: 0 10px 30px rgba(0,0,0,0.25);
    }}
    .card {{ padding: 16px 18px; }}
    .card .label {{
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--muted);
    }}
    .card .value {{
      margin-top: 8px;
      font-size: 30px;
      font-weight: 700;
    }}
    .panel {{ padding: 18px; }}
    .panel h2 {{ margin: 0 0 14px; font-size: 18px; }}
    .layout {{
      display: grid;
      grid-template-columns: minmax(0, 2fr) minmax(320px, 1fr);
      gap: 20px;
      align-items: start;
    }}
    .controls {{
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
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
    svg {{
      width: 100%;
      min-height: 620px;
      display: block;
      background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0));
      border-radius: 14px;
    }}
    .legend {{
      display: flex;
      gap: 16px;
      flex-wrap: wrap;
      color: var(--muted);
      font-size: 13px;
      margin-top: 12px;
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
    .pill {{
      display: inline-block;
      border: 1px solid var(--border);
      background: var(--panel-soft);
      color: var(--muted);
      padding: 4px 8px;
      border-radius: 999px;
      font-size: 12px;
      margin-right: 6px;
      margin-bottom: 6px;
    }}
    .muted {{ color: var(--muted); }}
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
    .path-step code {{
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
    <h1>Process visualization report</h1>
    <p>Data-driven process view from mined event data. The JSON contract is hierarchy-aware; Mermaid and BPMN stay flat/draft exports for review.</p>
  </header>
  <main>
    <section class="cards" id="cards"></section>
    <section class="layout">
      <div class="panel">
        <h2>Process map</h2>
        <div class="controls">
          <select id="variantSelect"></select>
          <button id="resetVariant">Reset highlight</button>
        </div>
        <svg id="graph" viewBox="0 0 1400 820" preserveAspectRatio="xMidYMid meet"></svg>
        <div class="legend">
          <span><strong>Node size</strong> = activity frequency</span>
          <span><strong>Edge thickness</strong> = transition count</span>
          <span><strong>Highlight</strong> = selected variant path</span>
        </div>
      </div>
      <div class="panel">
        <h2>Variant explanation</h2>
        <div id="variantExplain" class="muted">Select a variant to see the exact step sequence, hierarchy context, and example case IDs.</div>
        <h2 style="margin-top:18px;">Hierarchy groups</h2>
        <div id="hierarchyGroups"></div>
      </div>
    </section>
    <section class="layout">
      <div class="panel">
        <h2>Activities</h2>
        <table>
          <thead><tr><th>Activity</th><th>Count</th><th>Lane</th><th>Hierarchy</th></tr></thead>
          <tbody id="activities"></tbody>
        </table>
      </div>
      <div class="panel">
        <h2>Transitions</h2>
        <table>
          <thead><tr><th>Transition</th><th>Count</th><th>Median wait</th></tr></thead>
          <tbody id="transitions"></tbody>
        </table>
      </div>
    </section>
    <section class="panel">
      <h2>Variants</h2>
      <table>
        <thead><tr><th>Share</th><th>Path</th><th>Examples</th></tr></thead>
        <tbody id="variants"></tbody>
      </table>
    </section>
  </main>
  <script>
    const processMap = {payload};
    const summary = processMap.summary;
    const hierarchy = processMap.hierarchy || {{ enabled: false, groups: [] }};
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

    document.getElementById('hierarchyGroups').innerHTML = hierarchy.enabled
      ? hierarchy.groups.map(group => `<span class="pill">${{group.prefix}} · members=${{group.member_count}} · events=${{group.event_count}}</span>`).join('')
      : '<span class="muted">No hierarchy metadata in this process map.</span>';

    document.getElementById('activities').innerHTML = processMap.activities.map(activity => `
      <tr>
        <td>
          <strong>${{activity.label}}</strong><br>
          <span class="muted">${{activity.full_path}}</span>
        </td>
        <td>${{activity.count}}</td>
        <td>${{activity.suggested_lane || '<span class="muted">n/a</span>'}}</td>
        <td>${{activity.hierarchy_parent ? `<code>${{activity.hierarchy_parent}}</code>` : '<span class="muted">flat</span>'}}</td>
      </tr>
    `).join('');

    document.getElementById('transitions').innerHTML = processMap.transitions.map(transition => `
      <tr>
        <td>${{transition.source}} → ${{transition.target}}<br><span class="muted">${{transition.source_path || 'START'}} → ${{transition.target_path || 'END'}}</span></td>
        <td>${{transition.count}}</td>
        <td>${{transition.median_wait_seconds ?? 'n/a'}}</td>
      </tr>
    `).join('');

    const variantsBody = document.getElementById('variants');
    variantsBody.innerHTML = processMap.variants.map((variant, index) => `
      <tr class="variant-row" data-index="${{index}}">
        <td>${{Math.round(variant.share * 100)}}%</td>
        <td>${{variant.path}}</td>
        <td>${{variant.case_ids.join(', ') || 'n/a'}}</td>
      </tr>
    `).join('');

    const variantSelect = document.getElementById('variantSelect');
    variantSelect.innerHTML = '<option value="">Highlight variant</option>' + processMap.variants.map((variant, index) =>
      `<option value="${{index}}">${{Math.round(variant.share * 100)}}% — ${{variant.path}}</option>`
    ).join('');

    const svg = document.getElementById('graph');
    const NS = 'http://www.w3.org/2000/svg';
    const activityById = new Map(processMap.activities.map(activity => [activity.id, activity]));
    const nodePositions = new Map();
    const nodeElements = new Map();
    const edgeElements = [];
    const laneOrder = [];
    const lanes = new Map();

    for (const activity of processMap.activities) {{
      const lane = activity.suggested_lane || 'Unassigned';
      if (!lanes.has(lane)) {{
        lanes.set(lane, []);
        laneOrder.push(lane);
      }}
      lanes.get(lane).push(activity);
    }}

    const append = (name, attrs, parent = svg) => {{
      const el = document.createElementNS(NS, name);
      for (const [key, value] of Object.entries(attrs || {{}})) {{
        el.setAttribute(key, String(value));
      }}
      parent.appendChild(el);
      return el;
    }};

    append('rect', {{ x: 0, y: 0, width: 1400, height: 820, fill: 'transparent' }});

    const laneHeight = 150;
    const colBase = 170;
    const colStep = 210;
    laneOrder.forEach((lane, laneIndex) => {{
      const top = 40 + laneIndex * laneHeight;
      append('rect', {{
        x: 50,
        y: top,
        width: 1280,
        height: laneHeight - 20,
        rx: 16,
        fill: laneIndex % 2 === 0 ? 'rgba(255,255,255,0.02)' : 'rgba(255,255,255,0.035)',
        stroke: '#2a3550'
      }});
      const label = append('text', {{
        x: 72,
        y: top + 28,
        fill: '#9eb0d1',
        'font-size': 14,
        'font-weight': 600
      }});
      label.textContent = lane;
    }});

    const startPos = {{ x: 80, y: 90 }};
    const endPos = {{ x: 1260, y: 90 }};
    nodePositions.set('__START__', startPos);
    nodePositions.set('__END__', endPos);

    for (const activity of processMap.activities) {{
      const lane = activity.suggested_lane || 'Unassigned';
      const laneIndex = laneOrder.indexOf(lane);
      const x = colBase + activity.avg_position * colStep;
      const y = 95 + laneIndex * laneHeight;
      nodePositions.set(activity.id, {{ x, y }});
    }}

    const maxEdge = Math.max(...processMap.transitions.map(t => t.count), 1);
    const maxNode = Math.max(...processMap.activities.map(a => a.count), 1);
    for (const transition of processMap.transitions) {{
      const source = nodePositions.get(transition.source_id);
      const target = nodePositions.get(transition.target_id);
      if (!source || !target) continue;
      const sourceActivity = activityById.get(transition.source_id);
      const targetActivity = activityById.get(transition.target_id);
      if (transition.source_id !== '__START__' && !sourceActivity) continue;
      if (transition.target_id !== '__END__' && !targetActivity) continue;
      const sourceWidth = transition.source_id === '__START__' ? 36 : 110 + Math.round((sourceActivity.count / maxNode) * 28);
      const targetWidth = transition.target_id === '__END__' ? 36 : 110 + Math.round((targetActivity.count / maxNode) * 28);
      const sourceX = transition.source_id === '__START__' ? source.x + 18 : source.x + sourceWidth;
      const sourceY = transition.source_id === '__START__' ? source.y + 18 : source.y + 29;
      const targetX = transition.target_id === '__END__' ? target.x + 18 : target.x;
      const targetY = transition.target_id === '__END__' ? target.y + 18 : target.y + 29;
      const midX = (sourceX + targetX) / 2;
      const curvature = Math.abs(targetY - sourceY) > 10 ? 30 : 0;
      const path = `M ${{sourceX}} ${{sourceY}} C ${{midX}} ${{sourceY + curvature}}, ${{midX}} ${{targetY - curvature}}, ${{targetX}} ${{targetY}}`;
      const edge = append('path', {{
        d: path,
        fill: 'none',
        stroke: '#5b709a',
        'stroke-width': 1 + (transition.count / maxEdge) * 5,
        opacity: 0.9
      }});
      const label = append('text', {{
        x: midX,
        y: (sourceY + targetY) / 2 - 8,
        fill: '#c7d7f5',
        'font-size': 12,
        'text-anchor': 'middle'
      }});
      label.textContent = transition.count;
      edgeElements.push({{ sourceId: transition.source_id, targetId: transition.target_id, edge, label }});
    }}

    const drawEvent = (position, label, color, id) => {{
      const circle = append('circle', {{ cx: position.x + 18, cy: position.y + 18, r: 18, fill: color, stroke: '#c7d7f5', 'stroke-width': 1.5 }});
      const text = append('text', {{
        x: position.x + 18,
        y: position.y + 48,
        fill: '#ecf2ff',
        'font-size': 12,
        'text-anchor': 'middle'
      }});
      text.textContent = label;
      nodeElements.set(id, [circle, text]);
    }};

    drawEvent(startPos, 'Start', '#0f766e', '__START__');
    drawEvent(endPos, 'End', '#7c2d12', '__END__');

    for (const activity of processMap.activities) {{
      const position = nodePositions.get(activity.id);
      const width = 110 + Math.round((activity.count / maxNode) * 28);
      const height = 58;
      const box = append('rect', {{
        x: position.x,
        y: position.y,
        width,
        height,
        rx: 14,
        fill: '#131a2c',
        stroke: '#6ee7ff',
        'stroke-width': 1.2
      }});
      const title = append('text', {{
        x: position.x + 12,
        y: position.y + 22,
        fill: '#ecf2ff',
        'font-size': 13,
        'font-weight': 600
      }});
      title.textContent = activity.label;
      const subtitle = append('text', {{
        x: position.x + 12,
        y: position.y + 42,
        fill: '#9eb0d1',
        'font-size': 11
      }});
      subtitle.textContent = activity.hierarchy_parent ? activity.hierarchy_parent : `count=${{activity.count}}`;
      nodeElements.set(activity.id, [box, title, subtitle]);
    }}

    function renderVariantExplain(variant) {{
      const panel = document.getElementById('variantExplain');
      if (!variant) {{
        panel.innerHTML = '<span class="muted">Select a variant to see the exact step sequence, hierarchy context, and example case IDs.</span>';
        return;
      }}
      panel.innerHTML = `
        <div class="pill">share=${{Math.round(variant.share * 100)}}%</div>
        <div class="pill">count=${{variant.count}}</div>
        <div class="pill">cases=${{variant.case_ids.join(', ') || 'n/a'}}</div>
        <div style="margin-top:12px;">
          ${{
            variant.steps.map((step, index) => `
              <div class="path-step">
                <strong>${{index + 1}}. ${{step.label}}</strong>
                <div><code>${{step.full_path}}</code></div>
                <div class="muted">${{step.hierarchy_parent || 'flat activity'}}</div>
              </div>
            `).join('')
          }}
        </div>
      `;
    }}

    function highlightVariant(index) {{
      const variant = index === null ? null : processMap.variants[index];
      if (!variant) {{
        for (const item of edgeElements) {{
          item.edge.setAttribute('stroke', '#5b709a');
          item.edge.setAttribute('opacity', '0.9');
          item.label.setAttribute('opacity', '1');
        }}
        for (const [id, elements] of nodeElements.entries()) {{
          const opacity = '1';
          elements.forEach(element => element.setAttribute('opacity', opacity));
        }}
        renderVariantExplain(null);
        return;
      }}

      const nodeSet = new Set(variant.activity_ids);
      const edgeSet = new Set();
      for (let i = 0; i < variant.activity_ids.length - 1; i += 1) {{
        edgeSet.add(`${{variant.activity_ids[i]}}|||${{variant.activity_ids[i + 1]}}`);
      }}

      for (const item of edgeElements) {{
        const active = edgeSet.has(`${{item.sourceId}}|||${{item.targetId}}`);
        item.edge.setAttribute('stroke', active ? '#f59e0b' : '#34435f');
        item.edge.setAttribute('opacity', active ? '1' : '0.18');
        item.label.setAttribute('opacity', active ? '1' : '0.18');
      }}
      for (const [id, elements] of nodeElements.entries()) {{
        const active = id === '__START__' || id === '__END__' || nodeSet.has(id);
        elements.forEach(element => element.setAttribute('opacity', active ? '1' : '0.28'));
      }}
      renderVariantExplain(variant);
    }}

    document.getElementById('resetVariant').addEventListener('click', () => {{
      variantSelect.value = '';
      highlightVariant(null);
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
  </script>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a process-map JSON as a self-contained HTML report.")
    parser.add_argument("input", help="Process-map JSON file")
    parser.add_argument("--out", required=True, help="Output HTML path")
    args = parser.parse_args()

    process_map = json.loads(Path(args.input).read_text(encoding="utf-8"))
    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_html(process_map), encoding="utf-8")
    print(f"HTML written → {output_path}")
    print(f"Cases: {process_map['summary']['cases']}")
    print(f"Activities: {process_map['summary']['activities']}")
    print(f"Transitions: {process_map['summary']['transitions']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
