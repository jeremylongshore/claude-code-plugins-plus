#!/usr/bin/env python3
"""Analyze a read-only snapshot of a Snowflake pipeline.

The input is deliberately a small, connector-neutral JSON contract.  A caller
can collect rows from TASK_HISTORY, stream metadata, dynamic-table refresh
history, and SYSTEM$PIPE_STATUS, then pass the redacted result here.  This
module contains no Snowflake client and never executes SQL, resumes an object,
recreates a stream, or changes data.  Keeping diagnosis pure makes the same
classification usable in CI fixtures and incident response.

Input (JSON file or stdin)::

  {"observed_at":"2026-08-30T12:00:00Z", "nodes":[
    {"id":"raw", "kind":"TABLE", "status":"OK",
     "change_tracking":true, "duplicate_rows":0},
    {"id":"s", "kind":"STREAM", "status":"STALE", "source":"raw",
     "stale":true, "stale_reason":"offset beyond retention"},
    {"id":"t", "kind":"TASK", "status":"SUSPENDED", "upstream":["s"]}
  ], "edges":[{"from":"raw","to":"s"},{"from":"s","to":"t"}]}

Exit codes: 0 for a valid report (findings are data), 2 for bad usage/input.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Any


SCHEMA_VERSION = "1"
KIND_ORDER = {"TABLE": 0, "STREAM": 1, "TASK": 2, "DYNAMIC_TABLE": 3, "PIPE": 4}
REDACTIONS = (
    (re.compile(r"https?://\S+", re.IGNORECASE), "[REDACTED_URL]"),
    (re.compile(r"\b[a-z][a-z0-9+.-]*://[^/\s:@]+:[^@\s/]+@\S+", re.IGNORECASE), "[REDACTED_CONNECTION_URL]"),
    (re.compile(r"\bBearer\s+\S+", re.IGNORECASE), "[REDACTED_BEARER]"),
    (re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b"), "[REDACTED_EMAIL]"),
    (
        re.compile(
            r"(?i)\b[\w-]*(password|passphrase|token|secret|credential|private[_-]?key|authorization|jwt|api[_-]?key)[\w-]*\s*[=:]\s*\S+"
        ),
        "[REDACTED_CREDENTIAL]",
    ),
)
SENSITIVE_KEYS = {
    "password",
    "passphrase",
    "token",
    "oauthtoken",
    "sessiontoken",
    "apikey",
    "awsaccesskeyid",
    "secretaccesskey",
    "secret",
    "credential",
    "credentials",
    "privatekey",
    "authorization",
    "jwt",
}


def _safe(value: Any) -> str:
    text = str(value)
    for pattern, replacement in REDACTIONS:
        text = pattern.sub(replacement, text)
    return text


def _reject_secret_fields(value: Any, path: str = "snapshot") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = re.sub(r"[^a-z0-9]", "", str(key).casefold())
            if normalized in SENSITIVE_KEYS or any(
                fragment in normalized
                for fragment in (
                    "password",
                    "passphrase",
                    "secret",
                    "privatekey",
                    "credential",
                    "token",
                    "apikey",
                    "authorization",
                    "jwt",
                )
            ):
                raise ValueError(f"credential-bearing field is not accepted: {path}.{key}")
            _reject_secret_fields(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_secret_fields(child, f"{path}[{index}]")


def _parse_observed_at(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    parsed = parsed.astimezone(timezone.utc)
    return parsed if parsed <= datetime.now(timezone.utc) else None


def _text(node: dict[str, Any]) -> str:
    fields = (
        node.get("status"),
        node.get("state"),
        node.get("last_error"),
        node.get("error"),
        node.get("state_message"),
        node.get("stale_reason"),
        node.get("refresh_mode_reason"),
        node.get("scheduling_state"),
    )
    return " ".join(str(value) for value in fields if value is not None).lower()


def _number(node: dict[str, Any], *names: str) -> float | None:
    for name in names:
        value = node.get(name)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)
    return None


def _kind(node: dict[str, Any]) -> str:
    return str(node.get("kind", "UNKNOWN")).upper().replace("-", "_")


def normalize_snapshot(snapshot: Any) -> tuple[dict[str, dict[str, Any]], list[tuple[str, str]], list[dict[str, str]]]:
    if not isinstance(snapshot, dict):
        raise ValueError("snapshot must be a JSON object")
    _reject_secret_fields(snapshot)
    raw_nodes = snapshot.get("nodes")
    if not isinstance(raw_nodes, list) or not raw_nodes:
        raise ValueError("snapshot.nodes must be a non-empty array")
    nodes: dict[str, dict[str, Any]] = {}
    for raw in raw_nodes:
        if not isinstance(raw, dict) or not raw.get("id"):
            raise ValueError("each node must be an object with a non-empty id")
        node = dict(raw)
        node["id"] = str(node["id"])
        node["kind"] = _kind(node)
        if node["id"] in nodes:
            raise ValueError(f"duplicate node id: {node['id']}")
        nodes[node["id"]] = node

    edges: list[tuple[str, str]] = []
    dangling: list[dict[str, str]] = []
    for edge in snapshot.get("edges", []):
        if not isinstance(edge, dict) or not edge.get("from") or not edge.get("to"):
            continue
        source, target = str(edge["from"]), str(edge["to"])
        if source in nodes and target in nodes:
            edges.append((source, target))
        else:
            dangling.append({"from": _safe(source), "to": _safe(target), "source": "edges"})
    # A source/upstream field is convenient when a connector cannot emit edges.
    for target, node in nodes.items():
        upstream = node.get("upstream", node.get("sources", []))
        if isinstance(upstream, str):
            upstream = [upstream]
        for source in upstream or []:
            if str(source) in nodes:
                edges.append((str(source), target))
            else:
                dangling.append({"from": _safe(source), "to": _safe(target), "source": "upstream"})
        source = node.get("source")
        if source is not None and str(source) in nodes:
            edges.append((str(source), target))
        elif source is not None:
            dangling.append({"from": _safe(source), "to": _safe(target), "source": "source"})
    unique_dangling = {(item["from"], item["to"], item["source"]): item for item in dangling}
    return nodes, sorted(set(edges)), [unique_dangling[key] for key in sorted(unique_dangling)]


def _finding(code: str, node: dict[str, Any], severity: str, evidence: str, action: str, rank: int) -> dict[str, Any]:
    return {
        "code": code,
        "node_id": _safe(node["id"]),
        "kind": node["kind"],
        "severity": severity,
        "evidence": _safe(evidence),
        "recovery_rank": rank,
        "read_only_action": action,
    }


def classify_node(node: dict[str, Any]) -> list[dict[str, Any]]:
    """Return deterministic findings for one node; does not infer missing data."""
    kind = _kind(node)
    text = _text(node)
    findings: list[dict[str, Any]] = []
    status = str(node.get("status", node.get("state", ""))).upper()

    stale = node.get("stale") is True or status == "STALE"
    if kind == "STREAM" and stale:
        reason = node.get("stale_reason") or node.get("last_error") or "stream reports stale"
        findings.append(
            _finding(
                "STREAM_STALE",
                node,
                "critical",
                str(reason),
                "Preserve the evidence, verify retention/change history, then plan a new stream plus an idempotent backfill; do not silently reset offsets.",
                10,
            )
        )

    change_tracking = node.get("change_tracking")
    change_tracking_error = any(
        term in text
        for term in (
            "change tracking is not enabled",
            "change tracking not enabled",
            "change tracking disabled",
            "change tracking missing",
            "requires change tracking",
        )
    )
    if kind == "DYNAMIC_TABLE" and (change_tracking is False or change_tracking_error):
        findings.append(
            _finding(
                "CHANGE_TRACKING_MISSING",
                node,
                "critical",
                node.get("last_error")
                or node.get("state_message")
                or "incremental refresh lacks source change tracking",
                "Confirm the original source object and retention window; capture GET_DDL, repair history, and budget a full reinitialization if incremental history is unavailable.",
                20,
            )
        )

    schema_signal = any(
        term in text
        for term in (
            "schema mismatch",
            "schema change",
            "column not found",
            "invalid column",
            "type mismatch",
            "base table dropped",
            "cannot read from stream",
        )
    )
    if (
        schema_signal
        and status in {"FAILED", "FAILURE", "ERROR"}
        and kind in {"STREAM", "TASK", "DYNAMIC_TABLE", "PIPE"}
    ):
        findings.append(
            _finding(
                "SCHEMA_DRIFT",
                node,
                "high",
                node.get("last_error") or node.get("state_message") or "schema-change signal",
                "Compare the producer schema and consumer definition, preserve the failing query id, and choose an additive or explicit migration; do not CREATE OR REPLACE blindly.",
                30,
            )
        )

    current_lag = _number(node, "current_lag_minutes", "lag_minutes", "actual_lag_minutes")
    target_lag = _number(node, "target_lag_minutes", "target_lag")
    if current_lag is not None and target_lag is not None and current_lag > target_lag:
        findings.append(
            _finding(
                "LAG_BREACH",
                node,
                "high",
                f"actual lag {current_lag:g} minutes exceeds target {target_lag:g} minutes",
                "Check refresh duration, queueing, warehouse capacity, pipeline depth, and upstream failures; treat TARGET_LAG as a freshness goal, not a fixed schedule.",
                40,
            )
        )

    duplicate_count = _number(node, "duplicate_rows", "duplicate_count")
    duplicate_rate = _number(node, "duplicate_rate")
    if (duplicate_count is not None and duplicate_count > 0) or (duplicate_rate is not None and duplicate_rate > 0):
        detail = (
            f"duplicate_rows={duplicate_count:g}"
            if duplicate_count is not None
            else f"duplicate_rate={duplicate_rate:g}"
        )
        findings.append(
            _finding(
                "DUPLICATE_DELIVERY",
                node,
                "high",
                detail,
                "Identify the delivery key and retry boundary, then prove idempotence with a key-level duplicate query before replaying files or task runs.",
                50,
            )
        )

    if kind == "TASK":
        if status == "SUSPENDED":
            findings.append(
                _finding(
                    "TASK_SUSPENDED",
                    node,
                    "high",
                    node.get("last_error") or "task graph/task is suspended",
                    "Inspect TASK_HISTORY and predecessor completion; suspend/resume changes require explicit operator approval and are not performed by this skill.",
                    15,
                )
            )
        elif status in {"FAILED", "FAILURE", "ERROR"}:
            findings.append(
                _finding(
                    "TASK_FAILED",
                    node,
                    "high",
                    node.get("last_error") or node.get("state_message") or "task reports failure",
                    "Pin the failing run and query id, walk predecessors, and retry only after the first causal failure is understood; no blind retry loop.",
                    25,
                )
            )

    if kind == "DYNAMIC_TABLE" and status in {"FAILED", "FAILURE", "ERROR"}:
        findings.append(
            _finding(
                "DYNAMIC_REFRESH_FAILED",
                node,
                "high",
                node.get("last_error") or node.get("state_message") or "refresh failed",
                "Read DYNAMIC_TABLE_REFRESH_HISTORY and graph history, distinguish source failure from refresh-mode/schema failure, and preserve the data timestamp.",
                25,
            )
        )

    if kind == "PIPE":
        no_message = node.get("notification_gap") is True or any(
            term in text
            for term in (
                "no message received",
                "no notification received",
                "not forwarded",
                "path mismatch",
            )
        )
        load_error = node.get("load_failed") is True or any(
            term in text
            for term in (
                "load failed",
                "load error",
                "copy error",
                "file format error",
                "permission denied",
            )
        )
        if no_message:
            findings.append(
                _finding(
                    "PIPE_NOTIFICATION_GAP",
                    node,
                    "high",
                    node.get("last_error") or "pipe status indicates an event/message gap",
                    "Compare stage/path, cloud notification routing, and SYSTEM$PIPE_STATUS timestamps; do not resubmit files until duplicate-load behavior is understood.",
                    18,
                )
            )
        elif load_error or status in {"FAILED", "ERROR"}:
            findings.append(
                _finding(
                    "PIPE_LOAD_FAILURE",
                    node,
                    "high",
                    node.get("last_error") or node.get("state_message") or "pipe reports load failure",
                    "Inspect COPY_HISTORY and the pipe error notification, isolate the file and preserve its load metadata before replaying.",
                    28,
                )
            )

    return findings


def _reverse_graph(nodes: dict[str, dict[str, Any]], edges: list[tuple[str, str]]) -> dict[str, list[str]]:
    upstream: dict[str, list[str]] = defaultdict(list)
    for source, target in edges:
        upstream[target].append(source)
    for node_id in nodes:
        upstream[node_id] = sorted(set(upstream[node_id]))
    return upstream


def _connected_components(nodes: dict[str, dict[str, Any]], edges: list[tuple[str, str]]) -> list[list[str]]:
    neighbors: dict[str, set[str]] = {node_id: set() for node_id in nodes}
    for source, target in edges:
        neighbors[source].add(target)
        neighbors[target].add(source)
    remaining = set(nodes)
    components: list[list[str]] = []
    while remaining:
        start = min(remaining)
        queue = deque([start])
        component: set[str] = set()
        while queue:
            current = queue.popleft()
            if current in component:
                continue
            component.add(current)
            queue.extend(sorted(neighbors[current] - component))
        remaining -= component
        components.append(sorted(component))
    return components


def _dependency_chains(
    nodes: dict[str, dict[str, Any]],
    edges: list[tuple[str, str]],
    findings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_node: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for finding in findings:
        by_node[finding["node_id"]].append(finding)
    upstream = _reverse_graph(nodes, edges)
    endpoints = sorted(
        {f["node_id"] for f in findings},
        key=lambda node_id: (0 if _kind(nodes[node_id]) in {"TASK", "DYNAMIC_TABLE", "PIPE"} else 1, node_id),
    )
    chains: list[dict[str, Any]] = []
    for endpoint in endpoints:
        queue: deque[tuple[str, list[str]]] = deque([(endpoint, [endpoint])])
        endpoint_paths: list[list[str]] = []
        while queue:
            current, current_path = queue.popleft()
            parents = [parent for parent in upstream.get(current, []) if parent not in current_path]
            if not parents:
                endpoint_paths.append(list(reversed(current_path)))
                continue
            for parent in parents:
                queue.append((parent, current_path + [parent]))
        for path in endpoint_paths or [[endpoint]]:
            chains.append(
                {
                    "endpoint": _safe(endpoint),
                    "classification": "dependency_order_not_proven_causality",
                    "nodes": [
                        {
                            "node_id": _safe(node_id),
                            "kind": _kind(nodes[node_id]),
                            "findings": [f["code"] for f in sorted(by_node.get(node_id, []), key=lambda f: f["code"])],
                        }
                        for node_id in path
                    ],
                }
            )
    unique = {(item["endpoint"], tuple(node["node_id"] for node in item["nodes"])): item for item in chains}
    return [unique[key] for key in sorted(unique)]


def analyze(snapshot: Any) -> dict[str, Any]:
    nodes, edges, dangling_edges = normalize_snapshot(snapshot)
    components = _connected_components(nodes, edges)
    observed_at = _parse_observed_at(snapshot.get("observed_at"))
    evidence_source = snapshot.get("evidence_source")
    evidence_gaps: list[str] = []
    if observed_at is None:
        evidence_gaps.append("observed_at must be a valid, non-future timezone timestamp")
    if not isinstance(evidence_source, str) or not evidence_source.strip():
        evidence_gaps.append("evidence_source is required")
    if dangling_edges:
        evidence_gaps.append("one or more dependency edges reference missing nodes")
    if len(components) > 1:
        evidence_gaps.append("node inventory contains disconnected components")
    findings = [finding for node_id in sorted(nodes) for finding in classify_node(nodes[node_id])]
    findings.sort(key=lambda f: (f["recovery_rank"], f["node_id"], f["code"]))
    recovery = []
    seen_actions: set[str] = set()
    for finding in findings:
        action = finding["read_only_action"]
        if action not in seen_actions:
            seen_actions.add(action)
            recovery.append({"order": len(recovery) + 1, "for": finding["code"], "action": action})
    invariants = [
        "No stream is stale and every recreated stream has a documented backfill boundary.",
        "Every incremental dynamic table retains source change history for its recovery window.",
        "Actual freshness is within the stated target lag, or the breach is acknowledged with capacity evidence.",
        "Task graphs have a successful predecessor chain and are not silently suspended.",
        "Snowpipe message, load, and COPY history agree; replay keys are idempotent and duplicates are zero.",
    ]
    limitations = [
        "This report classifies supplied evidence only; missing fields are not proof of health.",
        "It does not connect to Snowflake or execute ALTER, RESUME, REFRESH, CREATE, DROP, INSERT, or COPY statements.",
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "observed_at": observed_at.isoformat() if observed_at else None,
        "evidence_source": _safe(evidence_source) if isinstance(evidence_source, str) else None,
        "evidence_complete": not evidence_gaps,
        "evidence_gaps": evidence_gaps,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "causal_chains": _dependency_chains(nodes, edges, findings),
        "dangling_edges": dangling_edges,
        "graph_complete": not dangling_edges and len(components) == 1,
        "connected_components": [[_safe(node_id) for node_id in group] for group in components],
        "findings": findings,
        "ordered_recovery": recovery,
        "post_fix_invariants": invariants,
        "limitations": limitations,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Classify a read-only Snowflake pipeline evidence snapshot")
    parser.add_argument("--input", "-i", help="JSON input path; default is stdin")
    args = parser.parse_args()
    try:
        raw = open(args.input, encoding="utf-8").read() if args.input else sys.stdin.read()
        report = analyze(json.loads(raw))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
