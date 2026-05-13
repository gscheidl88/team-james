#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
process_map_to_bpmn.py - Convert a mined process map JSON into a BPMN draft XML file.

Usage:
    uv run tools/process/process_map_to_bpmn.py PROCESS_MAP.json --out draft.bpmn
"""

from __future__ import annotations

import argparse
import json
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

START = "__START__"
END = "__END__"

NS = {
    "bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL",
    "bpmndi": "http://www.omg.org/spec/BPMN/20100524/DI",
    "dc": "http://www.omg.org/spec/DD/20100524/DC",
    "di": "http://www.omg.org/spec/DD/20100524/DI",
}

for prefix, uri in NS.items():
    ET.register_namespace(prefix, uri)


def qname(prefix: str, tag: str) -> str:
    return f"{{{NS[prefix]}}}{tag}"


def slugify(value: str) -> str:
    out = []
    for char in value.lower():
        if char.isalnum():
            out.append(char)
        else:
            out.append("_")
    slug = "".join(out).strip("_")
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug or "node"


def add_bounds(parent: ET.Element, x: float, y: float, width: float, height: float) -> None:
    ET.SubElement(
        parent,
        qname("dc", "Bounds"),
        {"x": str(x), "y": str(y), "width": str(width), "height": str(height)},
    )


def center(bounds: tuple[float, float, float, float]) -> tuple[float, float]:
    x, y, width, height = bounds
    return x + width / 2, y + height / 2


def build_bpmn(process_map: dict) -> ET.ElementTree:
    activities = process_map["activities"]
    transitions = process_map["transitions"]
    activity_by_id = {activity["id"]: activity for activity in activities}

    indegree: Counter[str] = Counter()
    outdegree: Counter[str] = Counter()
    for transition in transitions:
        indegree[transition["target_id"]] += 1
        outdegree[transition["source_id"]] += 1

    definitions = ET.Element(
        qname("bpmn", "definitions"),
        {
            "id": "Definitions_ProcessVisualization",
            "targetNamespace": "https://gerhard.local/process-visualization",
        },
    )
    process = ET.SubElement(
        definitions,
        qname("bpmn", "process"),
        {"id": "Process_1", "name": "Generated Process Draft", "isExecutable": "false"},
    )

    flow_ids: dict[str, str] = {START: "StartEvent_1", END: "EndEvent_1"}
    ET.SubElement(process, qname("bpmn", "startEvent"), {"id": flow_ids[START], "name": "Start"})
    ET.SubElement(process, qname("bpmn", "endEvent"), {"id": flow_ids[END], "name": "End"})

    activity_order = sorted(activities, key=lambda item: item["avg_position"])
    for activity in activity_order:
        task_id = f"Task_{activity['id']}"
        flow_ids[activity["id"]] = task_id
        task_name = activity["full_path"] if process_map.get("hierarchy", {}).get("enabled") else activity["label"]
        ET.SubElement(process, qname("bpmn", "task"), {"id": task_id, "name": task_name})

    join_gateways: dict[str, str] = {}
    split_gateways: dict[str, str] = {}
    for node, count in indegree.items():
        if node not in (START,) and count > 1:
            gateway_id = f"GatewayJoin_{slugify(node)}"
            join_gateways[node] = gateway_id
            gateway_name = activity_by_id.get(node, {}).get("full_path", node)
            ET.SubElement(process, qname("bpmn", "exclusiveGateway"), {"id": gateway_id, "name": f"Join {gateway_name}"})
    for node, count in outdegree.items():
        if node not in (END,) and count > 1:
            gateway_id = f"GatewaySplit_{slugify(node)}"
            split_gateways[node] = gateway_id
            gateway_name = activity_by_id.get(node, {}).get("full_path", node)
            ET.SubElement(process, qname("bpmn", "exclusiveGateway"), {"id": gateway_id, "name": f"Split {gateway_name}"})

    connector_flows: list[tuple[str, str, str]] = []
    connector_index = 1
    for node, gateway_id in join_gateways.items():
        connector_flows.append((f"Flow_{connector_index}", gateway_id, flow_ids[node]))
        connector_index += 1
    for node, gateway_id in split_gateways.items():
        connector_flows.append((f"Flow_{connector_index}", flow_ids[node], gateway_id))
        connector_index += 1

    sequence_flows: list[tuple[str, str, str, int]] = []
    for transition in transitions:
        source = transition["source_id"]
        target = transition["target_id"]
        source_ref = split_gateways.get(source, flow_ids[source])
        target_ref = join_gateways.get(target, flow_ids[target])
        sequence_flows.append((f"Flow_{connector_index}", source_ref, target_ref, transition["count"]))
        connector_index += 1

    for flow_id, source_ref, target_ref in connector_flows:
        ET.SubElement(process, qname("bpmn", "sequenceFlow"), {"id": flow_id, "sourceRef": source_ref, "targetRef": target_ref})
    for flow_id, source_ref, target_ref, count in sequence_flows:
        ET.SubElement(
            process,
            qname("bpmn", "sequenceFlow"),
            {"id": flow_id, "name": str(count), "sourceRef": source_ref, "targetRef": target_ref},
        )

    diagram = ET.SubElement(definitions, qname("bpmndi", "BPMNDiagram"), {"id": "BPMNDiagram_1"})
    plane = ET.SubElement(diagram, qname("bpmndi", "BPMNPlane"), {"id": "BPMNPlane_1", "bpmnElement": "Process_1"})

    bounds_by_id: dict[str, tuple[float, float, float, float]] = {}
    x = 80.0
    y = 120.0

    def add_shape(element_id: str, width: float, height: float) -> None:
        nonlocal x
        shape = ET.SubElement(
            plane,
            qname("bpmndi", "BPMNShape"),
            {"id": f"{element_id}_di", "bpmnElement": element_id},
        )
        add_bounds(shape, x, y, width, height)
        bounds_by_id[element_id] = (x, y, width, height)
        x += 180.0

    add_shape("StartEvent_1", 36.0, 36.0)
    for activity in activity_order:
        task_id = flow_ids[activity["id"]]
        if activity["id"] in join_gateways:
            add_shape(join_gateways[activity["id"]], 50.0, 50.0)
        add_shape(task_id, 110.0, 70.0)
        if activity["id"] in split_gateways:
            add_shape(split_gateways[activity["id"]], 50.0, 50.0)
    add_shape("EndEvent_1", 36.0, 36.0)

    for flow_id, source_ref, target_ref in connector_flows:
        edge = ET.SubElement(
            plane,
            qname("bpmndi", "BPMNEdge"),
            {"id": f"{flow_id}_di", "bpmnElement": flow_id},
        )
        sx, sy = center(bounds_by_id[source_ref])
        tx, ty = center(bounds_by_id[target_ref])
        ET.SubElement(edge, qname("di", "waypoint"), {"x": str(sx), "y": str(sy)})
        ET.SubElement(edge, qname("di", "waypoint"), {"x": str(tx), "y": str(ty)})
    for flow_id, source_ref, target_ref, _count in sequence_flows:
        edge = ET.SubElement(
            plane,
            qname("bpmndi", "BPMNEdge"),
            {"id": f"{flow_id}_di", "bpmnElement": flow_id},
        )
        sx, sy = center(bounds_by_id[source_ref])
        tx, ty = center(bounds_by_id[target_ref])
        ET.SubElement(edge, qname("di", "waypoint"), {"x": str(sx), "y": str(sy)})
        ET.SubElement(edge, qname("di", "waypoint"), {"x": str(tx), "y": str(ty)})

    return ET.ElementTree(definitions)


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert a mined process-map JSON into BPMN draft XML.")
    parser.add_argument("input", help="Process-map JSON file")
    parser.add_argument("--out", required=True, help="Output BPMN file path")
    args = parser.parse_args()

    process_map = json.loads(Path(args.input).read_text(encoding="utf-8"))
    tree = build_bpmn(process_map)
    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)
    print(f"BPMN written → {output_path}")
    print(f"Activities: {len(process_map['activities'])}")
    print(f"Transitions: {len(process_map['transitions'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
