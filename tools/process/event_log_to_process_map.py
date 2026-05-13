#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
event_log_to_process_map.py - Mine a simple event log into a structured process map.

Usage:
    uv run tools/process/event_log_to_process_map.py INPUT.csv --case-id case_id --activity activity
    uv run tools/process/event_log_to_process_map.py INPUT.csv --case-id case_id --activity activity --timestamp timestamp --actor actor --out-json out.json --out-mermaid out.mmd
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

START = "__START__"
END = "__END__"


def load_records(path: Path) -> list[dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))
    if suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError("JSON input must be a list of event objects.")
        return [dict(item) for item in data]
    raise ValueError(f"Unsupported input format: {path.suffix}")


def parse_timestamp(raw: str | None) -> dt.datetime | None:
    if not raw:
        return None
    text = raw.strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return dt.datetime.fromisoformat(text)
    except ValueError:
        return None


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


def make_node_id(key: str) -> str:
    digest = hashlib.sha1(key.encode("utf-8")).hexdigest()[:8]
    return f"node_{slugify(key.split('::')[-1])}_{digest}"


def split_hierarchy_path(raw: str | None) -> list[str]:
    text = str(raw or "").strip()
    if not text:
        return []
    parts = [part.strip() for part in re.split(r"\s*(?:::|>|/|\\)\s*", text) if part.strip()]
    return parts


def median_or_none(values: list[float]) -> float | None:
    if not values:
        return None
    return round(statistics.median(values), 2)


def mean_or_none(values: list[float]) -> float | None:
    if not values:
        return None
    return round(statistics.fmean(values), 2)


def parse_event_context(
    record: dict[str, Any],
    *,
    activity_field: str,
    activity_path_field: str | None,
    parent_activity_field: str | None,
) -> dict[str, Any] | None:
    activity = str(record.get(activity_field, "")).strip()
    if not activity:
        return None

    path_parts = split_hierarchy_path(record.get(activity_path_field)) if activity_path_field else []
    if path_parts:
        if path_parts[-1] != activity:
            path_parts.append(activity)
    else:
        parent_parts = split_hierarchy_path(record.get(parent_activity_field)) if parent_activity_field else []
        path_parts = parent_parts + [activity]

    hierarchy_key = "::".join(path_parts)
    parent_path = "::".join(path_parts[:-1]) if len(path_parts) > 1 else ""
    return {
        "label": activity,
        "path_parts": path_parts,
        "full_path": hierarchy_key,
        "parent_path": parent_path,
        "hierarchy_level": max(len(path_parts) - 1, 0),
        "hierarchy_group": path_parts[0] if len(path_parts) > 1 else "",
    }


def build_process_map(
    records: list[dict[str, Any]],
    *,
    case_id_field: str,
    activity_field: str,
    timestamp_field: str | None,
    actor_field: str | None,
    lane_field: str | None,
    lifecycle_field: str | None,
    activity_path_field: str | None,
    parent_activity_field: str | None,
    top_variants: int,
) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for index, record in enumerate(records):
        case_id = str(record.get(case_id_field, "")).strip()
        if not case_id:
            continue
        context = parse_event_context(
            record,
            activity_field=activity_field,
            activity_path_field=activity_path_field,
            parent_activity_field=parent_activity_field,
        )
        if context is None:
            continue
        lane = str(record.get(lane_field, "")).strip() if lane_field else ""
        actor = str(record.get(actor_field, "")).strip() if actor_field else ""
        enriched = {
            "case_id": case_id,
            "activity": context["label"],
            "activity_key": context["full_path"],
            "activity_id": make_node_id(context["full_path"]),
            "full_path": context["full_path"],
            "path_parts": context["path_parts"],
            "parent_path": context["parent_path"],
            "hierarchy_level": context["hierarchy_level"],
            "hierarchy_group": context["hierarchy_group"],
            "timestamp": parse_timestamp(str(record.get(timestamp_field, "")).strip()) if timestamp_field else None,
            "actor": actor,
            "lane": lane,
            "effective_lane": lane or actor,
            "lifecycle": str(record.get(lifecycle_field, "")).strip() if lifecycle_field else "",
            "row_order": index,
        }
        grouped[case_id].append(enriched)

    activity_counts: Counter[str] = Counter()
    position_sums: defaultdict[str, list[int]] = defaultdict(list)
    activity_actors: defaultdict[str, Counter[str]] = defaultdict(Counter)
    activity_lanes: defaultdict[str, Counter[str]] = defaultdict(Counter)
    activity_meta: dict[str, dict[str, Any]] = {}
    transition_counts: Counter[tuple[str, str]] = Counter()
    transition_waits: defaultdict[tuple[str, str], list[float]] = defaultdict(list)
    variants: Counter[tuple[str, ...]] = Counter()
    variant_examples: defaultdict[tuple[str, ...], list[str]] = defaultdict(list)
    case_durations: list[float] = []
    case_lengths: list[int] = []
    hierarchy_prefix_members: defaultdict[str, set[str]] = defaultdict(set)

    for case_id, events in grouped.items():
        events.sort(key=lambda item: (item["timestamp"] is None, item["timestamp"] or dt.datetime.min, item["row_order"]))
        sequence_keys = [event["activity_key"] for event in events]
        variants[tuple(sequence_keys)] += 1
        if len(variant_examples[tuple(sequence_keys)]) < 5:
            variant_examples[tuple(sequence_keys)].append(case_id)
        case_lengths.append(len(sequence_keys))

        timestamps = [event["timestamp"] for event in events if event["timestamp"] is not None]
        if len(timestamps) >= 2:
            case_durations.append((max(timestamps) - min(timestamps)).total_seconds())

        for idx, event in enumerate(events):
            key = event["activity_key"]
            activity_counts[key] += 1
            position_sums[key].append(idx)
            if event["actor"]:
                activity_actors[key][event["actor"]] += 1
            if event["effective_lane"]:
                activity_lanes[key][event["effective_lane"]] += 1
            if key not in activity_meta:
                activity_meta[key] = {
                    "id": event["activity_id"],
                    "label": event["activity"],
                    "full_path": event["full_path"],
                    "path_parts": list(event["path_parts"]),
                    "parent_path": event["parent_path"],
                    "hierarchy_level": event["hierarchy_level"],
                    "hierarchy_group": event["hierarchy_group"],
                }
            parts = event["path_parts"]
            for depth in range(1, len(parts)):
                prefix = "::".join(parts[:depth])
                hierarchy_prefix_members[prefix].add(key)

        chain = [START] + sequence_keys + [END]
        for idx in range(len(chain) - 1):
            edge = (chain[idx], chain[idx + 1])
            transition_counts[edge] += 1

        if timestamp_field:
            for left, right in zip(events, events[1:]):
                if left["timestamp"] is None or right["timestamp"] is None:
                    continue
                edge = (left["activity_key"], right["activity_key"])
                wait_seconds = (right["timestamp"] - left["timestamp"]).total_seconds()
                transition_waits[edge].append(wait_seconds)

    activities = []
    total_cases = max(len(grouped), 1)
    for key, count in sorted(activity_counts.items(), key=lambda item: (-item[1], item[0])):
        meta = activity_meta[key]
        actors = activity_actors[key]
        lanes = activity_lanes[key]
        activities.append(
            {
                "id": meta["id"],
                "key": key,
                "label": meta["label"],
                "full_path": meta["full_path"],
                "hierarchy_path": meta["full_path"] if meta["hierarchy_level"] > 0 else "",
                "hierarchy_parent": meta["parent_path"],
                "hierarchy_parts": meta["path_parts"],
                "hierarchy_level": meta["hierarchy_level"],
                "hierarchy_group": meta["hierarchy_group"],
                "count": count,
                "case_share": round(count / total_cases, 4),
                "avg_position": round(statistics.fmean(position_sums[key]), 2),
                "suggested_lane": lanes.most_common(1)[0][0] if lanes else "",
                "actors": [{"name": name, "count": actor_count} for name, actor_count in actors.most_common()],
            }
        )

    activity_by_key = {activity["key"]: activity for activity in activities}

    transitions = []
    for (source_key, target_key), count in sorted(transition_counts.items(), key=lambda item: (-item[1], item[0])):
        waits = transition_waits.get((source_key, target_key), [])
        source_activity = activity_by_key.get(source_key)
        target_activity = activity_by_key.get(target_key)
        transitions.append(
            {
                "source": START if source_key == START else source_activity["label"],
                "target": END if target_key == END else target_activity["label"],
                "source_id": START if source_key == START else source_activity["id"],
                "target_id": END if target_key == END else target_activity["id"],
                "source_key": source_key,
                "target_key": target_key,
                "source_path": "" if source_key == START else source_activity["full_path"],
                "target_path": "" if target_key == END else target_activity["full_path"],
                "count": count,
                "case_share": round(count / total_cases, 4),
                "median_wait_seconds": median_or_none(waits),
                "mean_wait_seconds": mean_or_none(waits),
            }
        )

    variant_rows = []
    for key_sequence, count in variants.most_common(top_variants):
        steps = []
        for key in key_sequence:
            activity = activity_by_key[key]
            steps.append(
                {
                    "id": activity["id"],
                    "key": activity["key"],
                    "label": activity["label"],
                    "full_path": activity["full_path"],
                    "hierarchy_parent": activity["hierarchy_parent"],
                    "hierarchy_level": activity["hierarchy_level"],
                }
            )
        variant_rows.append(
            {
                "path": " > ".join(step["label"] for step in steps),
                "count": count,
                "share": round(count / total_cases, 4),
                "activity_ids": [step["id"] for step in steps],
                "activity_keys": [step["key"] for step in steps],
                "activity_paths": [step["full_path"] for step in steps],
                "steps": steps,
                "case_ids": list(variant_examples[key_sequence]),
            }
        )

    groups = []
    for prefix, members in sorted(hierarchy_prefix_members.items(), key=lambda item: (item[0].count("::"), item[0])):
        member_rows = [activity_by_key[key] for key in members]
        groups.append(
            {
                "prefix": prefix,
                "label": prefix.split("::")[-1],
                "level": prefix.count("::"),
                "member_count": len(member_rows),
                "event_count": sum(row["count"] for row in member_rows),
                "member_ids": [row["id"] for row in sorted(member_rows, key=lambda item: item["full_path"])],
            }
        )

    hierarchy_enabled = any(activity["hierarchy_level"] > 0 for activity in activities)
    max_depth = max((len(activity["hierarchy_parts"]) for activity in activities), default=1)

    return {
        "meta": {
            "tool": "event_log_to_process_map.py",
            "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "source_records": len(records),
            "retained_records": sum(activity_counts.values()),
            "cases": len(grouped),
            "top_variants": top_variants,
            "hierarchy_enabled": hierarchy_enabled,
            "max_hierarchy_depth": max_depth,
        },
        "input": {
            "case_id_field": case_id_field,
            "activity_field": activity_field,
            "timestamp_field": timestamp_field or "",
            "actor_field": actor_field or "",
            "lane_field": lane_field or "",
            "lifecycle_field": lifecycle_field or "",
            "activity_path_field": activity_path_field or "",
            "parent_activity_field": parent_activity_field or "",
        },
        "summary": {
            "cases": len(grouped),
            "activities": len(activity_counts),
            "transitions": len(transition_counts),
            "avg_case_length": round(statistics.fmean(case_lengths), 2) if case_lengths else 0,
            "median_case_duration_seconds": median_or_none(case_durations),
            "hierarchy_groups": len(groups),
        },
        "hierarchy": {
            "enabled": hierarchy_enabled,
            "max_depth": max_depth,
            "groups": groups,
        },
        "activities": activities,
        "transitions": transitions,
        "variants": variant_rows,
    }


def build_mermaid(process_map: dict[str, Any], direction: str) -> str:
    activity_ids = {activity["id"]: activity for activity in process_map["activities"]}
    lines = [f"flowchart {direction}", "    start((Start))", "    end((End))"]

    for activity in sorted(process_map["activities"], key=lambda item: item["avg_position"]):
        label_parts = [activity["label"], f"count={activity['count']}"]
        if activity["suggested_lane"]:
            label_parts.append(f"lane={activity['suggested_lane']}")
        if activity["hierarchy_parent"]:
            label_parts.append(f"path={activity['hierarchy_parent']}")
        label = "\\n".join(label_parts)
        lines.append(f'    {activity["id"]}["{label}"]')

    for transition in process_map["transitions"]:
        source = "start" if transition["source_id"] == START else transition["source_id"]
        target = "end" if transition["target_id"] == END else transition["target_id"]
        label = str(transition["count"])
        lines.append(f"    {source} -->|{label}| {target}")

    return "\n".join(lines) + "\n"


def print_summary(process_map: dict[str, Any]) -> None:
    summary = process_map["summary"]
    print(f"Cases: {summary['cases']}")
    print(f"Activities: {summary['activities']}")
    print(f"Transitions: {summary['transitions']}")
    print(f"Avg case length: {summary['avg_case_length']}")
    if summary["median_case_duration_seconds"] is not None:
        print(f"Median case duration (s): {summary['median_case_duration_seconds']}")
    if process_map["hierarchy"]["enabled"]:
        print(f"Hierarchy groups: {summary['hierarchy_groups']}")
        print(f"Max hierarchy depth: {process_map['hierarchy']['max_depth']}")
    print("Top variants:")
    for variant in process_map["variants"][:5]:
        print(f"- {variant['count']}x ({variant['share']:.0%}) {variant['path']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Mine a simple event log into a process map JSON + Mermaid flowchart.")
    parser.add_argument("input", help="CSV or JSON event log file")
    parser.add_argument("--case-id", default="case_id", help="Case ID column name")
    parser.add_argument("--activity", default="activity", help="Activity column name")
    parser.add_argument("--timestamp", help="Timestamp column name")
    parser.add_argument("--actor", help="Actor/role column name")
    parser.add_argument("--lane", help="Lane/owner column name")
    parser.add_argument("--lifecycle", help="Lifecycle/status column name")
    parser.add_argument("--activity-path", help="Hierarchy path column name, e.g. api::service::activity")
    parser.add_argument("--parent-activity", help="Parent activity/path column name when no explicit path exists")
    parser.add_argument("--top-variants", type=int, default=10, help="How many variants to keep in the summary")
    parser.add_argument("--direction", default="LR", choices=["LR", "TD"], help="Mermaid layout direction")
    parser.add_argument("--out-json", help="Write process map JSON to file")
    parser.add_argument("--out-mermaid", help="Write Mermaid flowchart to file")
    args = parser.parse_args()

    input_path = Path(args.input)
    records = load_records(input_path)
    process_map = build_process_map(
        records,
        case_id_field=args.case_id,
        activity_field=args.activity,
        timestamp_field=args.timestamp,
        actor_field=args.actor,
        lane_field=args.lane,
        lifecycle_field=args.lifecycle,
        activity_path_field=args.activity_path,
        parent_activity_field=args.parent_activity,
        top_variants=args.top_variants,
    )
    process_map["meta"]["source_path"] = str(input_path)
    process_map["meta"]["direction"] = args.direction

    mermaid = build_mermaid(process_map, args.direction)
    print_summary(process_map)

    if args.out_json:
        out_json = Path(args.out_json)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(process_map, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"JSON written → {out_json}")

    if args.out_mermaid:
        out_mmd = Path(args.out_mermaid)
        out_mmd.parent.mkdir(parents=True, exist_ok=True)
        out_mmd.write_text(mermaid, encoding="utf-8")
        print(f"Mermaid written → {out_mmd}")
    else:
        print()
        print(mermaid)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
