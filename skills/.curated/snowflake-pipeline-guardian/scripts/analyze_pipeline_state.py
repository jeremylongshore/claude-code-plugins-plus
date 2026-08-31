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
import hashlib
import json
import re
import sys
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
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


def _safe_value(value: Any) -> Any:
    """Sanitize arbitrary receipt values before they cross the report boundary."""
    if isinstance(value, dict):
        return {str(key): _safe_value(child) for key, child in value.items()}
    if isinstance(value, list):
        return [_safe_value(child) for child in value]
    if isinstance(value, str):
        return _safe(value)
    return value


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
EXPECTED_PIPELINE_SOURCES = [
    "SNOWFLAKE.ACCOUNT_USAGE.TASK_HISTORY",
    "SNOWFLAKE.ACCOUNT_USAGE.DYNAMIC_TABLE_REFRESH_HISTORY",
    "SNOWFLAKE.ACCOUNT_USAGE.COPY_HISTORY",
]
EXPECTED_PIPELINE_DATASETS = {"task_history", "dynamic_table_refresh_history", "copy_history"}


def _collector_receipt_issues(receipt: Any, observed_at: datetime | None) -> list[str]:
    """Validate the shared collector envelope without trusting its claims."""
    if not isinstance(receipt, dict):
        return ["collector receipt must be an object"]
    issues: list[str] = []
    if receipt.get("schema_version") != "1":
        issues.append("collector receipt schema_version must be 1")
    if receipt.get("surface") != "pipeline":
        issues.append("collector receipt surface must be pipeline")
    if receipt.get("status") not in {"collected", "error"}:
        issues.append("collector receipt status must be collected or error")
    if receipt.get("status") == "error":
        issues.append("collector receipt status is error")
    errors = receipt.get("errors")
    if not isinstance(errors, list):
        issues.append("collector receipt errors must be an array")
    elif receipt.get("status") == "collected" and errors:
        issues.append("collected receipt contains errors")
    elif receipt.get("status") == "error" and not errors:
        issues.append("error receipt has no error details")

    collected_at = _parse_observed_at(receipt.get("collected_at"))
    if collected_at is None:
        issues.append("collector receipt collected_at must be a valid, non-future timezone timestamp")
    elif observed_at is not None and collected_at > observed_at:
        issues.append("collector receipt collected_at cannot be after observed_at")
    if not isinstance(receipt.get("connection_profile"), str) or not receipt["connection_profile"].strip():
        issues.append("collector receipt connection_profile is required")
    source_views = receipt.get("source_views")
    if source_views != EXPECTED_PIPELINE_SOURCES:
        issues.append("collector receipt source_views do not match the reviewed pipeline SQL")
    if not isinstance(receipt.get("sql_sha256"), str) or not SHA256_RE.fullmatch(receipt["sql_sha256"]):
        issues.append("collector receipt sql_sha256 is invalid")
    else:
        sql_path = Path(__file__).resolve().parent / "sql" / "pipeline.sql"
        expected_sql_hash = f"sha256:{hashlib.sha256(sql_path.read_bytes()).hexdigest()}"
        if receipt["sql_sha256"] != expected_sql_hash:
            issues.append("collector receipt sql_sha256 does not match the reviewed pipeline SQL")
    if not isinstance(receipt.get("receipt_sha256"), str) or not SHA256_RE.fullmatch(receipt["receipt_sha256"]):
        issues.append("collector receipt receipt_sha256 is invalid")
    else:
        unsigned = dict(receipt)
        unsigned.pop("receipt_sha256", None)
        expected = f"sha256:{hashlib.sha256(_canonical_json(unsigned)).hexdigest()}"
        if receipt["receipt_sha256"] != expected:
            issues.append("collector receipt receipt_sha256 does not match its contents")

    row_count = receipt.get("row_count")
    if type(row_count) is not int or row_count < 0:
        issues.append("collector receipt row_count must be a non-negative integer")
    row_limit = receipt.get("row_limit")
    if row_limit is None:
        issues.append("collector receipt row_limit is required")
    elif type(row_limit) is not int or row_limit <= 0:
        issues.append("collector receipt row_limit must be a positive integer")
    truncation = receipt.get("truncation_possible")
    if not isinstance(truncation, bool):
        issues.append("collector receipt truncation_possible must be boolean")
    elif (
        type(row_count) is int
        and row_limit is not None
        and type(row_limit) is int
        and truncation != row_count >= row_limit
    ):
        issues.append("collector receipt truncation_possible disagrees with row_count and row_limit")
    if truncation is True:
        issues.append("collector receipt is truncated")
    datasets = receipt.get("datasets")
    if not isinstance(datasets, dict):
        issues.append("collector receipt datasets must be an object")
    else:
        unexpected = set(datasets) - EXPECTED_PIPELINE_DATASETS
        if unexpected:
            issues.append("collector receipt contains unexpected datasets")
        dataset_count = sum(len(rows) for rows in datasets.values() if isinstance(rows, list))
        if any(not isinstance(rows, list) for rows in datasets.values()):
            issues.append("collector receipt dataset values must be arrays")
        elif type(row_count) is int and row_count != dataset_count:
            issues.append("collector receipt row_count does not match its datasets")
    return issues


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


def _parse_node_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def _history_node_id(
    row: dict[str, Any],
    object_fields: tuple[str, ...],
    run_fields: tuple[str, ...],
    fallback: str,
    row_index: int,
) -> str:
    """Build a stable, unique ID for one historical observation.

    Account Usage history has one row per run/refresh/file, so object name alone
    is not a node identity. A malformed row without a stable run key is rejected;
    an input-order ordinal would make replay and overlap analysis unstable.
    """
    object_name = ".".join(str(row.get(field)) for field in object_fields if row.get(field)) or fallback
    run_parts = [str(row[field]) for field in run_fields if row.get(field) is not None]
    run_key = "|".join(run_parts)
    if not run_key:
        raise ValueError(f"{fallback} history row lacks stable identity fields")
    return f"{object_name}@{run_key}"


def _collector_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Convert a shared collector receipt into the connector-neutral snapshot.

    The collector deliberately emits datasets rather than pretending it knows
    graph edges. This adapter keeps those rows useful while marking the resulting
    graph incomplete until an operator supplies object dependencies.
    """
    receipt = snapshot.get("collector_receipt") if isinstance(snapshot.get("collector_receipt"), dict) else snapshot
    datasets = receipt.get("datasets") if isinstance(receipt, dict) else None
    if not isinstance(datasets, dict) or "nodes" in snapshot:
        return snapshot
    nodes: list[dict[str, Any]] = []
    for row in datasets.get("stream_metadata", []):
        if not isinstance(row, dict):
            continue
        node = dict(row)
        node["id"] = ".".join(
            str(row.get(field)) for field in ("database_name", "schema_name", "name") if row.get(field)
        ) or str(row.get("name") or "stream")
        node["kind"] = "STREAM"
        node["status"] = "STALE" if row.get("stale") is True else "OK"
        nodes.append(node)
    for row_index, row in enumerate(datasets.get("task_history", [])):
        if not isinstance(row, dict):
            continue
        node = dict(row)
        node["id"] = _history_node_id(
            row,
            ("database_name", "schema_name", "name"),
            ("run_id", "graph_run_group_id", "attempt_number", "scheduled_time", "query_id"),
            "task",
            row_index,
        )
        node["kind"] = "TASK"
        node["status"] = row.get("state", "UNKNOWN")
        nodes.append(node)
    for row_index, row in enumerate(datasets.get("dynamic_table_refresh_history", [])):
        if not isinstance(row, dict):
            continue
        node = dict(row)
        node["id"] = _history_node_id(
            row,
            ("database_name", "schema_name", "name"),
            ("refresh_start_time", "query_id", "data_timestamp"),
            "dynamic_table",
            row_index,
        )
        node["kind"] = "DYNAMIC_TABLE"
        node["status"] = row.get("state", "UNKNOWN")
        nodes.append(node)
    for row_index, row in enumerate(datasets.get("copy_history", [])):
        if not isinstance(row, dict):
            continue
        node = dict(row)
        node["id"] = _history_node_id(
            row,
            ("table_name",),
            ("last_load_time", "file_name_sha256", "stage_location_sha256"),
            "copy_target",
            row_index,
        )
        node["kind"] = "PIPE"
        node["status"] = (
            "FAILED" if str(row.get("status", "")).upper() not in {"LOADED", "PARTIALLY LOADED", ""} else "OK"
        )
        nodes.append(node)
    if not nodes:
        return snapshot
    return {
        "observed_at": receipt.get("collected_at"),
        "evidence_source": "shared Snowflake evidence collector",
        "nodes": nodes,
        "edges": snapshot.get("edges", []),
        "collector_receipt": _safe_value(receipt),
    }


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

    idempotency = node.get("idempotency")
    idempotency_status = node.get("idempotency_status")
    if isinstance(idempotency, dict):
        idempotency_status = idempotency.get("status", idempotency_status)
        if node.get("delivery_key") is None:
            node["delivery_key"] = idempotency.get("delivery_key") or idempotency.get("business_key")
        if node.get("dedup_checked") is None:
            node["dedup_checked"] = idempotency.get("dedup_checked")
    status_text = str(idempotency_status or "").upper()
    has_key = any(
        node.get(field) for field in ("delivery_key", "business_key", "dedupe_key", "event_id", "file_identity")
    )
    if status_text in {"FAILED", "FALSE", "UNPROVEN", "UNKNOWN"} or (
        idempotency_status is None and (node.get("idempotency") is not None or node.get("replay_requested") is True)
    ):
        findings.append(
            _finding(
                "IDEMPOTENCY_UNPROVEN",
                node,
                "high",
                f"idempotency status={idempotency_status or 'not supplied'}; delivery key={'present' if has_key else 'absent'}",
                "Inspect the business/event/file key, target uniqueness or MERGE semantics, and partial-commit boundary before retry or replay; do not claim exactly-once from task or pipe success.",
                45,
            )
        )
    if node.get("replay_requested") is True or node.get("replay_window") is not None or node.get("replay_risk") is True:
        findings.append(
            _finding(
                "REPLAY_RISK",
                node,
                "high",
                f"replay boundary={node.get('replay_window') or 'not bounded'}",
                "Freeze replay scope, reconcile source identities to target keys, and prove idempotence with a bounded dry-run/count check before any replay.",
                47,
            )
        )

    if node.get("dedup_checked") is False or node.get("deduplication_status") in {"FAILED", "UNKNOWN"}:
        findings.append(
            _finding(
                "DEDUPLICATION_UNVERIFIED",
                node,
                "high",
                f"deduplication status={node.get('deduplication_status', node.get('dedup_checked'))}",
                "Run a read-only key-level duplicate and source-file/event reconciliation; hold replay until the duplicate budget and correction boundary are approved.",
                48,
            )
        )

    runs = node.get("run_history")
    skipped_count = _number(node, "skipped_runs", "skipped_count")
    if skipped_count is not None and skipped_count > 0:
        findings.append(
            _finding(
                "TASK_SKIPPED",
                node,
                "high",
                f"skipped_runs={skipped_count:g}",
                "Align skipped runs to predecessor return/state and WHEN-condition evidence; bound the missed interval before replaying downstream work.",
                22,
            )
        )
    overlap_count = _number(node, "overlapping_runs", "overlap_count")
    if overlap_count is not None and overlap_count > 0:
        findings.append(
            _finding(
                "TASK_OVERLAP",
                node,
                "high",
                f"overlapping_runs={overlap_count:g}",
                "Compare run IDs, attempt numbers, target keys, and transaction boundaries; prove whether concurrent runs can commit the same business interval before changing schedule or replaying.",
                23,
            )
        )
    if isinstance(runs, list):
        normalized_runs = [run for run in runs if isinstance(run, dict)]
        skipped = [run for run in normalized_runs if str(run.get("state", run.get("status", ""))).upper() == "SKIPPED"]
        if skipped:
            findings.append(
                _finding(
                    "TASK_SKIPPED",
                    node,
                    "high",
                    f"{len(skipped)} scheduled run(s) were SKIPPED",
                    "Align skipped runs to predecessor return/state and WHEN-condition evidence; bound the missed interval before replaying downstream work.",
                    22,
                )
            )
        parsed_runs = sorted(
            (
                (run, _parse_node_time(run.get("scheduled_time")), _parse_node_time(run.get("completed_time")))
                for run in normalized_runs
                if _parse_node_time(run.get("scheduled_time"))
            ),
            key=lambda item: item[1],
        )
        overlaps = []
        for current, (_, scheduled, completed) in zip(parsed_runs, parsed_runs[1:]):
            previous_run, previous_scheduled, previous_completed = current
            if previous_completed and scheduled and previous_completed > scheduled:
                overlaps.append((previous_run, scheduled))
        if overlaps:
            findings.append(
                _finding(
                    "TASK_OVERLAP",
                    node,
                    "high",
                    f"{len(overlaps)} scheduled interval(s) overlap a prior completion",
                    "Compare run IDs, attempt numbers, target keys, and transaction boundaries; prove whether concurrent runs can commit the same business interval before changing schedule or replaying.",
                    23,
                )
            )

    if kind == "PIPE":
        notification_duplicates = _number(node, "duplicate_notifications", "notification_duplicates")
        if notification_duplicates is not None and notification_duplicates > 0:
            findings.append(
                _finding(
                    "PIPE_NOTIFICATION_DUPLICATE",
                    node,
                    "high",
                    f"duplicate notification count={notification_duplicates:g}",
                    "Reconcile notification IDs to file identities and COPY_HISTORY; suppress blind replay until duplicate delivery is bounded.",
                    46,
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
        elif status == "SKIPPED":
            findings.append(
                _finding(
                    "TASK_SKIPPED",
                    node,
                    "high",
                    node.get("last_error") or "task run reports SKIPPED",
                    "Align the skipped run to predecessor return/state and WHEN-condition evidence; bound the missed interval before replaying downstream work.",
                    22,
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
    if isinstance(snapshot, dict):
        snapshot = _collector_snapshot(snapshot)
    nodes, edges, dangling_edges = normalize_snapshot(snapshot)
    components = _connected_components(nodes, edges)
    observed_at = _parse_observed_at(snapshot.get("observed_at"))
    evidence_source = snapshot.get("evidence_source")
    evidence_gaps: list[str] = []
    collector_receipt = snapshot.get("collector_receipt") if isinstance(snapshot, dict) else None
    receipt_issues = _collector_receipt_issues(collector_receipt, observed_at) if collector_receipt is not None else []
    evidence_gaps.extend(receipt_issues)
    if observed_at is None:
        evidence_gaps.append("observed_at must be a valid, non-future timezone timestamp")
    if not isinstance(evidence_source, str) or not evidence_source.strip():
        evidence_gaps.append("evidence_source is required")
    if dangling_edges:
        evidence_gaps.append("one or more dependency edges reference missing nodes")
    if collector_receipt and not edges:
        evidence_gaps.append("shared collector receipt did not include dependency edges")
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
        "Task run history has no unexplained overlap or SKIPPED interval; retries carry an attempt/run-group boundary.",
        "Snowpipe message, load, and COPY history agree; notification/file identities are deduplicated.",
        "Replay keys and target merge/uniqueness semantics are proven idempotent; duplicate count is zero or explicitly reconciled.",
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
        "graph_complete": not dangling_edges
        and len(components) == 1
        and not (collector_receipt and not edges)
        and not receipt_issues,
        "connected_components": [[_safe(node_id) for node_id in group] for group in components],
        "findings": findings,
        "ordered_recovery": recovery,
        "post_fix_invariants": invariants,
        "limitations": limitations,
        "collector_ingestion": _safe_value(collector_receipt)
        if collector_receipt
        else {
            "status": "not_used",
            "datasets": [],
            "message": "connector-neutral nodes were supplied directly",
        },
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
