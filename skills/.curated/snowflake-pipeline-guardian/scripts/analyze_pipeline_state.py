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
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "2"
KIND_ORDER = {"TABLE": 0, "COPY_LOAD": 1, "STREAM": 2, "TASK": 3, "DYNAMIC_TABLE": 4, "PIPE": 5}
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
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
UTC_SELECTOR_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$")
PIPELINE_RECEIPT_CONTRACTS = {
    "pipeline": {
        "template": "pipeline.sql",
        "sources": [
            "SNOWFLAKE.ACCOUNT_USAGE.TASK_HISTORY",
            "SNOWFLAKE.ACCOUNT_USAGE.DYNAMIC_TABLE_REFRESH_HISTORY",
            "SNOWFLAKE.ACCOUNT_USAGE.COPY_HISTORY",
        ],
        "datasets": {"task_history", "dynamic_table_refresh_history", "copy_history", "execution_context"},
        "cap_datasets": {"task_history", "dynamic_table_refresh_history", "copy_history"},
        "max_age_seconds": 900,
        "row_limit": 5000,
        "selector": {"window_start": True, "window_end": True},
    },
    "pipeline-task-current": {
        "template": "pipeline-task-current.sql",
        "sources": ["SHOW TASKS IN ACCOUNT"],
        "datasets": {"current_tasks", "execution_context"},
        "cap_datasets": {"current_tasks"},
        "max_age_seconds": 900,
        "row_limit": 10000,
        "selector": {},
    },
    "pipeline-stream-current": {
        "template": "pipeline-stream-current.sql",
        "sources": ["SHOW STREAMS IN ACCOUNT"],
        "datasets": {"current_streams", "execution_context"},
        "cap_datasets": {"current_streams"},
        "max_age_seconds": 900,
        "row_limit": 10000,
        "selector": {},
    },
    "pipeline-dynamic-table-current": {
        "template": "pipeline-dynamic-table-current.sql",
        "sources": ["SHOW DYNAMIC TABLES IN ACCOUNT"],
        "datasets": {"current_dynamic_tables", "execution_context"},
        "cap_datasets": {"current_dynamic_tables"},
        "max_age_seconds": 900,
        "row_limit": 10000,
        "selector": {},
    },
    "pipeline-pipe-current": {
        "template": "pipeline-pipe-current.sql",
        "sources": ["SHOW PIPES IN ACCOUNT"],
        "datasets": {"current_pipes", "execution_context"},
        "cap_datasets": {"current_pipes"},
        "max_age_seconds": 900,
        "row_limit": 10000,
        "selector": {},
    },
    "pipeline-pipe-status": {
        "template": "pipeline-pipe-status.sql",
        "sources": ["SYSTEM$PIPE_STATUS"],
        "datasets": {"pipe_status", "execution_context"},
        "cap_datasets": set(),
        "max_age_seconds": 900,
        "row_limit": 1,
        "selector": {"pipe": True},
    },
}
REQUIRED_PIPELINE_SURFACES = frozenset(PIPELINE_RECEIPT_CONTRACTS)
EXPECTED_PIPELINE_SOURCES = PIPELINE_RECEIPT_CONTRACTS["pipeline"]["sources"]
EXPECTED_PIPELINE_DATASETS = PIPELINE_RECEIPT_CONTRACTS["pipeline"]["datasets"]

COMMON_CONTEXT_FIELDS = {
    "observed_at",
    "organization_name_sha256",
    "account_identifier_sha256",
    "collector_user_sha256",
    "primary_role_sha256",
    "primary_role_type",
    "secondary_roles_sha256",
    "timezone",
}
CURRENT_CONTEXT_FIELDS = COMMON_CONTEXT_FIELDS | {
    "source_row_count",
    "source_row_limit",
    "truncation_possible",
}
HISTORY_CONTEXT_FIELDS = COMMON_CONTEXT_FIELDS | {
    "window_start_utc",
    "window_end_utc",
    "window_semantics",
    "task_history_settled_through_utc",
    "dynamic_table_refresh_history_settled_through_utc",
    "copy_history_settled_through_utc",
    "per_dataset_row_limit",
}
DATASET_FIELDS = {
    "task_history": {
        "object_key_sha256",
        "state",
        "scheduled_time",
        "completed_time",
        "query_start_time",
        "root_task_id_sha256",
        "run_id_sha256",
        "graph_run_group_id_sha256",
        "attempt_number",
        "graph_version",
        "query_id_sha256",
    },
    "dynamic_table_refresh_history": {
        "object_key_sha256",
        "state",
        "refresh_start_time",
        "refresh_end_time",
        "data_timestamp",
        "completion_target",
        "refresh_action",
        "refresh_trigger",
        "target_lag_sec",
        "query_id_sha256",
    },
    "copy_history": {
        "file_identifier_sha256",
        "stage_identifier_sha256",
        "object_key_sha256",
        "pipe_identifier_sha256",
        "last_load_time",
        "pipe_received_time",
        "first_commit_time",
        "status",
        "row_count",
        "row_parsed",
        "file_size",
        "error_count",
    },
    "current_tasks": {
        "object_key_sha256",
        "task_id_sha256",
        "created_on",
        "scheduling_mode",
        "predecessor_count",
        "state",
        "allow_overlapping_execution",
        "last_committed_on",
        "last_suspended_on",
    },
    "current_streams": {
        "object_key_sha256",
        "source_identifier_sha256",
        "created_on",
        "source_type",
        "stream_type",
        "mode",
        "stale",
        "stale_after",
    },
    "current_dynamic_tables": {
        "object_key_sha256",
        "created_on",
        "rows",
        "bytes",
        "scheduler",
        "refresh_mode",
        "automatic_clustering",
        "scheduling_state",
        "last_suspended_on",
        "is_clone",
        "is_replica",
        "is_iceberg",
        "data_timestamp",
    },
    "current_pipes": {"object_key_sha256", "created_on", "kind"},
    "pipe_status": {
        "object_key_sha256",
        "execution_state",
        "oldest_file_timestamp",
        "pending_file_count",
        "last_pipe_error_timestamp",
        "last_pipe_fault_timestamp",
        "last_ingested_timestamp",
        "outstanding_message_count",
        "last_received_message_timestamp",
        "last_forwarded_message_timestamp",
        "last_pulled_from_channel_timestamp",
        "load_history_remaining_entries_to_sync",
        "oldest_pending_history_refresh_job_creation_time",
        "pending_history_refresh_jobs_count",
    },
}
REQUIRED_DATASET_FIELDS = {
    "task_history": {"object_key_sha256", "state", "completed_time"},
    "dynamic_table_refresh_history": {"object_key_sha256", "state", "refresh_end_time"},
    "copy_history": {"object_key_sha256", "file_identifier_sha256", "last_load_time", "status", "error_count"},
    "current_tasks": {"object_key_sha256", "state"},
    "current_streams": {"object_key_sha256", "stale"},
    "current_dynamic_tables": {"object_key_sha256", "scheduling_state"},
    "current_pipes": {"object_key_sha256", "kind"},
    "pipe_status": {"object_key_sha256", "execution_state"},
}
RECEIPT_NON_CLAIMS = [
    "No Snowflake mutation was executed by the reviewed collector SQL.",
    "Missing rows or permission-blocked views do not prove health.",
    "Account Usage evidence can lag and must not be treated as real-time state.",
    "The selected domain skill must evaluate freshness and completeness.",
    "A row count at the reviewed SQL limit may indicate truncated evidence.",
    "The embedded receipt SHA-256 is a self-checksum, not proof of origin or authenticity.",
    "The collector does not attest to operations performed elsewhere in the surrounding session or workflow.",
]
ENUM_FIELDS = {
    "task_history": {
        "state": {"SUCCEEDED", "FAILED", "FAILED_AND_AUTO_SUSPENDED", "CANCELLED", "SKIPPED"},
    },
    "dynamic_table_refresh_history": {
        "state": {"SUCCEEDED", "FAILED", "CANCELLED", "UPSTREAM_FAILED"},
        "refresh_action": {"NO_DATA", "REINITIALIZE", "FULL", "INCREMENTAL", "CUSTOM_INCREMENTAL"},
        "refresh_trigger": {"SCHEDULED", "MANUAL", "CREATION"},
    },
    "copy_history": {
        "status": {"LOADED", "LOAD FAILED", "PARTIALLY LOADED", "LOAD SKIPPED"},
    },
    "current_tasks": {
        "scheduling_mode": {"FIXED", "FLEXIBLE"},
        "state": {"STARTED", "SUSPENDED"},
    },
    "current_streams": {
        "source_type": {"TABLE", "VIEW", "DIRECTORY TABLE", "EXTERNAL TABLE", "DYNAMIC TABLE"},
        "stream_type": {"DELTA"},
        "mode": {"APPEND_ONLY", "INSERT_ONLY", "DEFAULT"},
    },
    "current_dynamic_tables": {
        "scheduler": {"ENABLE", "DISABLE"},
        "refresh_mode": {"INCREMENTAL", "FULL", "AUTO", "ADAPTIVE", "CUSTOM_INCREMENTAL"},
        "scheduling_state": {"RUNNING", "SUSPENDED"},
    },
    "current_pipes": {"kind": {"STAGE"}},
    "pipe_status": {
        "execution_state": {
            "FAILING_OVER",
            "PAUSED",
            "READ_ONLY",
            "RUNNING",
            "STOPPED_BY_SNOWFLAKE_ADMIN",
            "STOPPED_CLONED",
            "STOPPED_FEATURE_DISABLED",
            "STOPPED_STAGE_ALTERED",
            "STOPPED_STAGE_DROPPED",
            "STOPPED_FILE_FORMAT_DROPPED",
            "STOPPED_NOTIFICATION_INTEGRATION_DROPPED",
            "STOPPED_MISSING_PIPE",
            "STOPPED_MISSING_TABLE",
            "STALLED_COMPILATION_ERROR",
            "STALLED_INITIALIZATION_ERROR",
            "STALLED_EXECUTION_ERROR",
            "STALLED_INTERNAL_ERROR",
            "STALLED_STAGE_PERMISSION_ERROR",
        }
    },
}
UNIQUE_KEY_FIELDS = {
    "current_tasks": ("object_key_sha256",),
    "current_streams": ("object_key_sha256",),
    "current_dynamic_tables": ("object_key_sha256",),
    "current_pipes": ("object_key_sha256",),
    "pipe_status": ("object_key_sha256",),
}
TIMESTAMP_FIELDS = {
    "scheduled_time",
    "completed_time",
    "query_start_time",
    "refresh_start_time",
    "refresh_end_time",
    "data_timestamp",
    "completion_target",
    "last_load_time",
    "pipe_received_time",
    "first_commit_time",
    "created_on",
    "last_committed_on",
    "last_suspended_on",
    "stale_after",
    "oldest_file_timestamp",
    "last_pipe_error_timestamp",
    "last_pipe_fault_timestamp",
    "last_ingested_timestamp",
    "last_received_message_timestamp",
    "last_forwarded_message_timestamp",
    "last_pulled_from_channel_timestamp",
    "oldest_pending_history_refresh_job_creation_time",
}
BOOLEAN_FIELDS = {
    "allow_overlapping_execution",
    "stale",
    "automatic_clustering",
    "is_clone",
    "is_replica",
    "is_iceberg",
}
NUMBER_FIELDS = {
    "attempt_number",
    "graph_version",
    "target_lag_sec",
    "row_count",
    "row_parsed",
    "file_size",
    "error_count",
    "predecessor_count",
    "rows",
    "bytes",
    "pending_file_count",
    "outstanding_message_count",
    "load_history_remaining_entries_to_sync",
    "pending_history_refresh_jobs_count",
}
RECEIPT_FIELDS = {
    "schema_version",
    "surface",
    "status",
    "collected_at",
    "sql_sha256",
    "template_sha256",
    "rendered_sql_sha256",
    "selector_fingerprint",
    "source_metadata",
    "source_views",
    "row_count",
    "row_limit",
    "cap_scope",
    "truncation_possible",
    "dataset_row_counts",
    "expected_datasets",
    "datasets",
    "errors",
    "non_claims",
    "result_sha256",
    "connection_profile_sha256",
    "snowflake_query_id",
    "snowflake_query_id_status",
    "collection_mode",
    "collection_started_at",
    "collection_completed_at",
    "receipt_sha256",
}


def canonical_bundle_digest(data: dict[str, Any]) -> str:
    """Return the digest recorded when a bundle crosses a trusted boundary."""

    return f"sha256:{hashlib.sha256(_canonical_json(data)).hexdigest()}"


def _dataset_row_issues(surface: str, dataset_name: str, row: dict[str, Any], index: int) -> list[str]:
    prefix = f"{surface}: {dataset_name}[{index}]"
    allowed = DATASET_FIELDS.get(dataset_name)
    if allowed is None:
        return [f"{prefix} has no reviewed projection schema"]
    issues: list[str] = []
    unexpected = sorted(set(row) - allowed)
    missing_projection_fields = sorted(allowed - set(row))
    if unexpected:
        issues.append(f"{prefix} contains fields outside the reviewed projection")
    if missing_projection_fields:
        issues.append(f"{prefix} is missing projected fields: {', '.join(missing_projection_fields)}")
    missing = sorted(
        field for field in REQUIRED_DATASET_FIELDS[dataset_name] if row.get(field) is None or row.get(field) == ""
    )
    if missing:
        issues.append(f"{prefix} is missing required evidence: {', '.join(missing)}")
    for field, value in row.items():
        if field not in allowed:
            continue
        if field.endswith("_sha256"):
            if value is not None and (not isinstance(value, str) or not HEX64_RE.fullmatch(value)):
                issues.append(f"{prefix}.{field} must be a lowercase SHA-256 digest or null")
        elif field in TIMESTAMP_FIELDS:
            if value is not None and _parse_node_time(value) is None:
                issues.append(f"{prefix}.{field} must be a timezone-aware timestamp or null")
        elif field in BOOLEAN_FIELDS:
            if value is not None and type(value) is not bool:
                issues.append(f"{prefix}.{field} must be a boolean or null")
        elif field in NUMBER_FIELDS:
            if value is not None and (not isinstance(value, (int, float)) or isinstance(value, bool)):
                issues.append(f"{prefix}.{field} must be numeric or null")
        elif value is not None and not isinstance(value, str):
            issues.append(f"{prefix}.{field} must be a string or null")
        elif value is not None:
            allowed_values = ENUM_FIELDS.get(dataset_name, {}).get(field)
            if allowed_values is None:
                issues.append(f"{prefix}.{field} is an unreviewed free-text field")
            elif value.upper() not in allowed_values:
                issues.append(f"{prefix}.{field} is outside the reviewed Snowflake value domain")
    if dataset_name == "dynamic_table_refresh_history" and str(row.get("state", "")).upper() == "EXECUTING":
        issues.append(f"{prefix} is mutable EXECUTING history, not settled evidence")
    return issues


def _expected_context_fields(surface: str) -> set[str]:
    if surface == "pipeline":
        return HISTORY_CONTEXT_FIELDS
    if surface == "pipeline-pipe-status":
        return COMMON_CONTEXT_FIELDS
    return CURRENT_CONTEXT_FIELDS


def _collector_receipt_issues(receipt: Any, wall_clock: datetime | None = None) -> list[str]:
    """Validate one schema-2 receipt; its self-hash is never a trust anchor."""

    if not isinstance(receipt, dict):
        return ["collector receipt must be an object"]
    surface = receipt.get("surface")
    contract = PIPELINE_RECEIPT_CONTRACTS.get(surface)
    if contract is None:
        return ["collector receipt surface is not a reviewed pipeline surface"]
    issues: list[str] = []
    prefix = str(surface)
    unexpected_receipt_fields = sorted(set(receipt) - RECEIPT_FIELDS)
    missing_receipt_fields = sorted(RECEIPT_FIELDS - set(receipt))
    if unexpected_receipt_fields:
        issues.append(f"{prefix}: receipt has fields outside the reviewed schema")
    if missing_receipt_fields:
        issues.append(f"{prefix}: receipt is missing fields: {', '.join(missing_receipt_fields)}")
    if receipt.get("schema_version") != "2":
        issues.append(f"{prefix}: collector receipt schema_version must be 2")
    if receipt.get("status") != "collected":
        issues.append(f"{prefix}: collector receipt status must be collected")
    errors = receipt.get("errors")
    if not isinstance(errors, list):
        issues.append(f"{prefix}: collector receipt errors must be an array")
    elif errors:
        issues.append(f"{prefix}: collected receipt contains errors")
    if "connection_profile" in receipt:
        issues.append(f"{prefix}: raw connection_profile is forbidden")
    if not isinstance(receipt.get("connection_profile_sha256"), str) or not SHA256_RE.fullmatch(
        receipt["connection_profile_sha256"]
    ):
        issues.append(f"{prefix}: connection_profile_sha256 is invalid")
    if receipt.get("collection_mode") != "live-cli":
        issues.append(f"{prefix}: only live-cli collection is accepted")
    if receipt.get("snowflake_query_id") is not None:
        issues.append(f"{prefix}: snowflake_query_id must remain redacted")
    if receipt.get("snowflake_query_id_status") != "not_exposed_by_snow_cli_json_ext":
        issues.append(f"{prefix}: snowflake_query_id_status does not match the reviewed collector")
    if receipt.get("non_claims") != RECEIPT_NON_CLAIMS:
        issues.append(f"{prefix}: non_claims must match the reviewed fixed statements")

    started = _parse_observed_at(receipt.get("collection_started_at"))
    completed = _parse_observed_at(receipt.get("collection_completed_at"))
    collected = _parse_observed_at(receipt.get("collected_at"))
    if started is None or completed is None or collected is None:
        issues.append(f"{prefix}: collection timestamps must be valid non-future timezone timestamps")
    elif not (started <= collected <= completed):
        issues.append(f"{prefix}: collected_at must fall within the collection interval")
    else:
        if collected != completed:
            issues.append(f"{prefix}: collected_at must equal collection_completed_at")
        if completed - started > timedelta(seconds=130):
            issues.append(f"{prefix}: collection interval exceeds the reviewed transport bound")
        if wall_clock is not None and completed > wall_clock:
            issues.append(f"{prefix}: collection_completed_at is after evaluation time")

    source_views = receipt.get("source_views")
    if source_views != contract["sources"]:
        issues.append(f"{prefix}: source_views do not match the reviewed SQL")
    metadata = receipt.get("source_metadata")
    if not isinstance(metadata, dict):
        issues.append(f"{prefix}: source_metadata must be an object")
    else:
        allowed_metadata = {"template", "source_views", "selector"}
        if surface == "pipeline":
            allowed_metadata.add("selector_values")
        elif surface == "pipeline-pipe-status":
            allowed_metadata.add("selector_binding")
            allowed_metadata.add("rendered_sql_contract")
        unexpected_metadata = sorted(set(metadata) - allowed_metadata)
        if unexpected_metadata:
            issues.append(f"{prefix}: source_metadata has unexpected fields")
        if metadata.get("template") != contract["template"]:
            issues.append(f"{prefix}: source template does not match the reviewed SQL")
        if metadata.get("source_views") != contract["sources"]:
            issues.append(f"{prefix}: source metadata views do not match the reviewed SQL")
        if metadata.get("selector") != contract["selector"]:
            issues.append(f"{prefix}: source selector shape does not match the reviewed SQL")
    selector_fingerprint = receipt.get("selector_fingerprint")
    if contract["selector"]:
        if not isinstance(selector_fingerprint, str) or not SHA256_RE.fullmatch(selector_fingerprint):
            issues.append(f"{prefix}: selector_fingerprint is invalid")
    elif selector_fingerprint is not None:
        issues.append(f"{prefix}: selector_fingerprint must be null for an unselected surface")

    sql_path = Path(__file__).resolve().parent / "sql" / str(contract["template"])
    expected_sql_hash = f"sha256:{hashlib.sha256(sql_path.read_bytes()).hexdigest()}" if sql_path.is_file() else None
    for field in ("sql_sha256", "template_sha256", "rendered_sql_sha256", "result_sha256", "receipt_sha256"):
        if not isinstance(receipt.get(field), str) or not SHA256_RE.fullmatch(receipt[field]):
            issues.append(f"{prefix}: {field} is invalid")
    if expected_sql_hash is None or receipt.get("sql_sha256") != expected_sql_hash:
        issues.append(f"{prefix}: sql_sha256 does not match the reviewed pipeline SQL")
    if receipt.get("template_sha256") != expected_sql_hash:
        issues.append(f"{prefix}: template_sha256 does not match the reviewed pipeline SQL")
    if (
        expected_sql_hash is not None
        and surface
        in {
            "pipeline-task-current",
            "pipeline-stream-current",
            "pipeline-dynamic-table-current",
            "pipeline-pipe-current",
        }
        and receipt.get("rendered_sql_sha256") != expected_sql_hash
    ):
        issues.append(f"{prefix}: rendered_sql_sha256 must equal the unselected reviewed template")

    datasets = receipt.get("datasets")
    expected_datasets = set(contract["datasets"])
    if not isinstance(datasets, dict):
        issues.append(f"{prefix}: datasets must be an object")
        datasets = {}
    elif set(datasets) != expected_datasets:
        for missing_dataset in sorted(expected_datasets - set(datasets)):
            issues.append(f"{prefix}: missing required dataset: {missing_dataset}")
        if set(datasets) - expected_datasets:
            issues.append(f"{prefix}: datasets contain entries outside the reviewed set")
    if any(not isinstance(rows, list) for rows in datasets.values()):
        issues.append(f"{prefix}: dataset values must be arrays")
    for dataset_name, rows in datasets.items():
        if dataset_name not in expected_datasets or dataset_name == "execution_context" or not isinstance(rows, list):
            continue
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                issues.append(f"{prefix}: {dataset_name}[{index}] must be an object")
                continue
            issues.extend(_dataset_row_issues(prefix, dataset_name, row, index))
        unique_fields = UNIQUE_KEY_FIELDS.get(dataset_name)
        if unique_fields:
            keys = [tuple(row.get(field) for field in unique_fields) for row in rows if isinstance(row, dict)]
            if len(keys) != len(set(keys)):
                issues.append(f"{prefix}: {dataset_name} contains duplicate natural keys")
    dataset_count = sum(len(rows) for rows in datasets.values() if isinstance(rows, list))
    if type(receipt.get("row_count")) is not int or receipt["row_count"] != dataset_count:
        issues.append(f"{prefix}: row_count does not match datasets")
    expected_counts = {name: len(rows) for name, rows in datasets.items() if isinstance(rows, list)}
    if receipt.get("dataset_row_counts") != expected_counts:
        issues.append(f"{prefix}: dataset_row_counts do not match datasets")
    if receipt.get("expected_datasets") != sorted(expected_datasets):
        issues.append(f"{prefix}: expected_datasets do not match the reviewed dataset set")
    expected_result_hash = f"sha256:{hashlib.sha256(_canonical_json(datasets)).hexdigest()}"
    if receipt.get("result_sha256") != expected_result_hash:
        issues.append(f"{prefix}: result_sha256 does not match datasets")

    row_limit = receipt.get("row_limit")
    if row_limit != contract["row_limit"]:
        issues.append(f"{prefix}: row_limit does not match the reviewed SQL cap")
    cap_rows = [len(datasets.get(name, [])) for name in contract["cap_datasets"]]
    expected_truncation = type(row_limit) is int and row_limit > 0 and any(count >= row_limit for count in cap_rows)
    if receipt.get("truncation_possible") is not expected_truncation:
        issues.append(f"{prefix}: truncation_possible disagrees with per-dataset caps")
    if expected_truncation:
        issues.append(f"{prefix}: collector receipt is truncated")
    expected_cap_scope = "per_dataset" if len(contract["cap_datasets"]) > 1 else "single_dataset_or_result"
    if receipt.get("cap_scope") != expected_cap_scope:
        issues.append(f"{prefix}: cap_scope does not match the reviewed surface")

    contexts = datasets.get("execution_context")
    context = (
        contexts[0] if isinstance(contexts, list) and len(contexts) == 1 and isinstance(contexts[0], dict) else None
    )
    if context is None:
        issues.append(f"{prefix}: exactly one execution_context row is required")
    else:
        unexpected_context = sorted(set(context) - _expected_context_fields(str(surface)))
        missing_context = sorted(_expected_context_fields(str(surface)) - set(context))
        if unexpected_context:
            issues.append(f"{prefix}: execution_context has unexpected fields")
        if missing_context:
            issues.append(f"{prefix}: execution_context is missing fields: {', '.join(missing_context)}")
        required_hashes = (
            "organization_name_sha256",
            "account_identifier_sha256",
            "collector_user_sha256",
            "primary_role_sha256",
            "secondary_roles_sha256",
        )
        for field in required_hashes:
            if not isinstance(context.get(field), str) or not HEX64_RE.fullmatch(context[field]):
                issues.append(f"{prefix}: execution_context.{field} must be a lowercase SHA-256 digest")
        if context.get("timezone") != "UTC":
            issues.append(f"{prefix}: execution_context timezone must be UTC")
        if context.get("primary_role_type") not in {"ROLE", "APPLICATION_INSTANCE"}:
            issues.append(f"{prefix}: execution_context.primary_role_type is outside the reviewed value domain")
        observed = _parse_observed_at(context.get("observed_at"))
        if observed is None:
            issues.append(f"{prefix}: execution_context.observed_at is invalid")
        else:
            if wall_clock is not None and observed > wall_clock:
                issues.append(f"{prefix}: execution_context observation is after evaluation time")
            elif wall_clock is not None and wall_clock - observed > timedelta(seconds=int(contract["max_age_seconds"])):
                issues.append(f"{prefix}: execution_context is stale")
            if started is not None and completed is not None and not (started <= observed <= completed):
                issues.append(f"{prefix}: execution_context observation falls outside collection interval")
        if surface == "pipeline":
            window_start = _parse_node_time(context.get("window_start_utc"))
            window_end = _parse_node_time(context.get("window_end_utc"))
            if window_start is None or window_end is None or not window_start < window_end:
                issues.append("pipeline: execution_context has an invalid history window")
            elif window_end - window_start > timedelta(days=7):
                issues.append("pipeline: execution_context history window exceeds seven days")
            if context.get("window_semantics") != "HALF_OPEN_UTC":
                issues.append("pipeline: execution_context window semantics must be HALF_OPEN_UTC")
            if context.get("per_dataset_row_limit") != contract["row_limit"]:
                issues.append("pipeline: execution_context.per_dataset_row_limit does not match the reviewed cap")
            settled_fields = {
                "task_history": ("task_history_settled_through_utc", timedelta(minutes=45), "completed_time"),
                "dynamic_table_refresh_history": (
                    "dynamic_table_refresh_history_settled_through_utc",
                    timedelta(hours=3),
                    "refresh_end_time",
                ),
                "copy_history": ("copy_history_settled_through_utc", timedelta(hours=48), "last_load_time"),
            }
            for dataset_name, (field, latency, time_field) in settled_fields.items():
                settled = _parse_node_time(context.get(field))
                if settled is None or (window_end is not None and settled > window_end):
                    issues.append(f"pipeline: execution_context.{field} is invalid")
                elif observed is not None and window_end is not None and settled != min(window_end, observed - latency):
                    issues.append(f"pipeline: execution_context.{field} does not match the reviewed settlement cutoff")
                if window_start is not None and window_end is not None and settled is not None:
                    if settled <= window_start:
                        issues.append(f"pipeline: {dataset_name} has no settled coverage in the requested window")
                    if settled < window_end:
                        issues.append(f"pipeline: {dataset_name} has an unsettled tail in the requested window")
                    for index, row in enumerate(datasets.get(dataset_name, [])):
                        if not isinstance(row, dict):
                            continue
                        event_time = _parse_node_time(row.get(time_field))
                        if event_time is None or not (window_start <= event_time < settled):
                            issues.append(
                                f"pipeline: {dataset_name}[{index}].{time_field} falls outside settled coverage"
                            )
            selector_values = metadata.get("selector_values") if isinstance(metadata, dict) else None
            if not isinstance(selector_values, dict) or set(selector_values) != {"window_start", "window_end"}:
                issues.append("pipeline: source_metadata.selector_values must bind the exact history window")
            elif any(
                not isinstance(value, str) or not UTC_SELECTOR_RE.fullmatch(value) for value in selector_values.values()
            ):
                issues.append("pipeline: selector values must be canonical UTC timestamps ending in Z")
            elif (
                _parse_node_time(selector_values.get("window_start")) != window_start
                or _parse_node_time(selector_values.get("window_end")) != window_end
            ):
                issues.append("pipeline: selector values do not match the execution_context history window")
            else:
                expected_selector = f"sha256:{hashlib.sha256(_canonical_json(selector_values)).hexdigest()}"
                if receipt.get("selector_fingerprint") != expected_selector:
                    issues.append("pipeline: selector_fingerprint does not match the bound history window")
                if sql_path.is_file():
                    rendered = sql_path.read_text(encoding="utf-8")
                    rendered = rendered.replace("__WINDOW_START_UTC__", selector_values["window_start"])
                    rendered = rendered.replace("__WINDOW_END_UTC__", selector_values["window_end"])
                    expected_rendered = f"sha256:{hashlib.sha256(rendered.encode('utf-8')).hexdigest()}"
                    if receipt.get("rendered_sql_sha256") != expected_rendered:
                        issues.append("pipeline: rendered_sql_sha256 does not match the bound reviewed SQL")
        elif surface == "pipeline-pipe-status":
            binding = metadata.get("selector_binding") if isinstance(metadata, dict) else None
            rows = datasets.get("pipe_status", [])
            object_key = rows[0].get("object_key_sha256") if len(rows) == 1 and isinstance(rows[0], dict) else None
            expected_binding = {"pipe_object_key_sha256": object_key}
            if binding != expected_binding or not isinstance(object_key, str) or not HEX64_RE.fullmatch(object_key):
                issues.append("pipeline-pipe-status: selector binding must match its one scoped pipe object hash")
            else:
                expected_selector = f"sha256:{hashlib.sha256(_canonical_json(expected_binding)).hexdigest()}"
                if receipt.get("selector_fingerprint") != expected_selector:
                    issues.append("pipeline-pipe-status: selector_fingerprint does not match its scoped pipe binding")
                if metadata.get("rendered_sql_contract") != "privacy-bound-selector-v1":
                    issues.append("pipeline-pipe-status: rendered SQL contract is not the reviewed privacy-bound form")
                if sql_path.is_file():
                    privacy_bound_sql = sql_path.read_text(encoding="utf-8").replace(
                        "__PIPE_IDENTIFIER__", f"__PIPE_OBJECT_KEY_SHA256_{object_key}__"
                    )
                    expected_rendered = f"sha256:{hashlib.sha256(privacy_bound_sql.encode('utf-8')).hexdigest()}"
                    if receipt.get("rendered_sql_sha256") != expected_rendered:
                        issues.append(
                            "pipeline-pipe-status: rendered_sql_sha256 does not match the privacy-bound selector projection"
                        )
        else:
            dataset_name = next(name for name in expected_datasets if name != "execution_context")
            source_rows = datasets.get(dataset_name, [])
            if context.get("source_row_count") != len(source_rows):
                issues.append(f"{prefix}: execution_context.source_row_count does not match projected rows")
            if context.get("source_row_limit") != contract["row_limit"]:
                issues.append(f"{prefix}: execution_context.source_row_limit does not match the reviewed cap")
            source_truncated = len(source_rows) >= contract["row_limit"]
            if context.get("truncation_possible") is not source_truncated:
                issues.append(f"{prefix}: execution_context.truncation_possible disagrees with SHOW output")

    unsigned = dict(receipt)
    unsigned.pop("receipt_sha256", None)
    expected_receipt_hash = f"sha256:{hashlib.sha256(_canonical_json(unsigned)).hexdigest()}"
    if receipt.get("receipt_sha256") != expected_receipt_hash:
        issues.append(f"{prefix}: receipt_sha256 does not match its contents")
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
                raise ValueError("credential-bearing field is not accepted")
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
    return parsed.astimezone(timezone.utc)


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


def _receipt_sequence(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    raw = snapshot.get("collector_receipts")
    if "collector_receipts" in snapshot and "collector_receipt" in snapshot:
        raise ValueError("supply collector_receipts or collector_receipt, not both")
    if isinstance(raw, dict):
        values = list(raw.values())
    elif isinstance(raw, list):
        values = raw
    elif raw is not None:
        raise ValueError("collector_receipts must be an array or object of receipts")
    elif isinstance(snapshot.get("collector_receipt"), dict):
        values = [snapshot["collector_receipt"]]
    elif "collector_receipt" in snapshot:
        raise ValueError("collector_receipt must be an object")
    elif isinstance(snapshot.get("datasets"), dict):
        values = [snapshot]
    else:
        values = []
    if any(not isinstance(value, dict) for value in values):
        raise ValueError("every collector receipt member must be an object")
    return values


def _collector_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Convert a shared collector receipt into the connector-neutral snapshot.

    The collector deliberately emits datasets rather than pretending it knows
    graph edges. This adapter keeps those rows useful while marking the resulting
    graph incomplete until an operator supplies object dependencies.
    """
    receipts = _receipt_sequence(snapshot)
    if not receipts:
        return snapshot
    wrapper_keys = {"collector_receipt", "collector_receipts"}
    if wrapper_keys & set(snapshot):
        overlays = sorted(set(snapshot) - wrapper_keys)
        if overlays:
            raise ValueError("collector receipt bundles cannot include analyzer overlays")
    nodes: list[dict[str, Any]] = []
    datasets_by_surface = {
        str(receipt.get("surface")): receipt.get("datasets", {})
        for receipt in receipts
        if isinstance(receipt.get("datasets"), dict)
    }
    history = datasets_by_surface.get("pipeline", {})
    for row in datasets_by_surface.get("pipeline-stream-current", {}).get("current_streams", []):
        if not isinstance(row, dict):
            continue
        node = dict(row)
        node["id"] = str(row.get("object_key_sha256") or "stream")
        node["kind"] = "STREAM"
        node["status"] = "MAY_BE_STALE" if row.get("stale") is True else "OK"
        node["_evidence_plane"] = "current"
        node["_source_surface"] = "pipeline-stream-current"
        nodes.append(node)
    for row in datasets_by_surface.get("pipeline-task-current", {}).get("current_tasks", []):
        if not isinstance(row, dict):
            continue
        node = dict(row)
        node["id"] = str(row.get("object_key_sha256") or "task")
        node["kind"] = "TASK"
        node["status"] = row.get("state", "UNKNOWN")
        node["_evidence_plane"] = "current"
        node["_source_surface"] = "pipeline-task-current"
        nodes.append(node)
    for row in datasets_by_surface.get("pipeline-dynamic-table-current", {}).get("current_dynamic_tables", []):
        if not isinstance(row, dict):
            continue
        node = dict(row)
        node["id"] = str(row.get("object_key_sha256") or "dynamic_table")
        node["kind"] = "DYNAMIC_TABLE"
        node["status"] = row.get("scheduling_state", "UNKNOWN")
        node["_evidence_plane"] = "current"
        node["_source_surface"] = "pipeline-dynamic-table-current"
        nodes.append(node)
    pipe_nodes: dict[str, dict[str, Any]] = {}
    for row in datasets_by_surface.get("pipeline-pipe-current", {}).get("current_pipes", []):
        if not isinstance(row, dict):
            continue
        node = dict(row)
        node["id"] = str(row.get("object_key_sha256") or "pipe")
        node["kind"] = "PIPE"
        node["status"] = "UNKNOWN"
        node["_evidence_plane"] = "current"
        node["_source_surface"] = "pipeline-pipe-current"
        pipe_nodes[node["id"]] = node
    for receipt in receipts:
        if receipt.get("surface") != "pipeline-pipe-status":
            continue
        rows = receipt.get("datasets", {}).get("pipe_status", []) if isinstance(receipt.get("datasets"), dict) else []
        for row in rows:
            if not isinstance(row, dict):
                continue
            object_key = str(row.get("object_key_sha256") or "pipe")
            node = pipe_nodes.setdefault(object_key, {"id": object_key, "kind": "PIPE"})
            node.update(row)
            node["status"] = row.get("execution_state", "UNKNOWN")
            node["_source_surface"] = "pipeline-pipe-status"
    nodes.extend(pipe_nodes.values())
    for row_index, row in enumerate(history.get("task_history", [])):
        if not isinstance(row, dict):
            continue
        node = dict(row)
        node["id"] = _history_node_id(
            row,
            ("object_key_sha256",),
            ("run_id_sha256", "graph_run_group_id_sha256", "attempt_number", "scheduled_time", "query_id_sha256"),
            "task",
            row_index,
        )
        node["kind"] = "TASK"
        node["status"] = row.get("state", "UNKNOWN")
        node["_evidence_plane"] = "settled_history"
        node["_source_surface"] = "pipeline"
        node["_source_dataset"] = "task_history"
        nodes.append(node)
    for row_index, row in enumerate(history.get("dynamic_table_refresh_history", [])):
        if not isinstance(row, dict):
            continue
        node = dict(row)
        node["id"] = _history_node_id(
            row,
            ("object_key_sha256",),
            ("refresh_end_time", "refresh_start_time", "query_id_sha256", "data_timestamp"),
            "dynamic_table",
            row_index,
        )
        node["kind"] = "DYNAMIC_TABLE"
        node["status"] = row.get("state", "UNKNOWN")
        node["_evidence_plane"] = "settled_history"
        node["_source_surface"] = "pipeline"
        node["_source_dataset"] = "dynamic_table_refresh_history"
        nodes.append(node)
    for row_index, row in enumerate(history.get("copy_history", [])):
        if not isinstance(row, dict):
            continue
        node = dict(row)
        pipe_key = row.get("pipe_identifier_sha256")
        object_fields = ("pipe_identifier_sha256",) if pipe_key else ("object_key_sha256",)
        node["id"] = _history_node_id(
            row,
            object_fields,
            ("last_load_time", "file_identifier_sha256", "stage_identifier_sha256"),
            "copy_target",
            row_index,
        )
        node["kind"] = "PIPE" if pipe_key else "COPY_LOAD"
        copy_status = str(row.get("status", "")).upper()
        error_count = _number(row, "error_count") or 0
        if copy_status == "PARTIALLY LOADED":
            node["status"] = "PARTIAL"
        elif copy_status == "LOAD SKIPPED":
            node["status"] = "SKIPPED"
        elif copy_status == "LOADED" and error_count == 0:
            node["status"] = "OK"
        else:
            node["status"] = "FAILED"
        node["_evidence_plane"] = "settled_history"
        node["_source_surface"] = "pipeline"
        node["_source_dataset"] = "copy_history"
        nodes.append(node)
    if not nodes:
        nodes = [{"id": "bounded-empty-inventory", "kind": "UNKNOWN", "status": "UNKNOWN"}]
    observed_values = []
    for receipt in receipts:
        datasets = receipt.get("datasets")
        contexts = datasets.get("execution_context") if isinstance(datasets, dict) else None
        if isinstance(contexts, list) and len(contexts) == 1 and isinstance(contexts[0], dict):
            observed_values.append(contexts[0].get("observed_at"))
    return {
        "observed_at": max((value for value in observed_values if isinstance(value, str)), default=None),
        "evidence_source": "shared Snowflake evidence collector",
        "nodes": nodes,
        "edges": snapshot.get("edges", []),
        "collector_receipts": receipts,
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
            raise ValueError("duplicate node id is not accepted")
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
    finding = {
        "code": code,
        "node_id": _safe(node["id"]),
        "kind": node["kind"],
        "severity": severity,
        "evidence": _safe(evidence),
        "recovery_rank": rank,
        "read_only_action": action,
    }
    if node.get("_evidence_plane"):
        finding["evidence_plane"] = node["_evidence_plane"]
    if node.get("_source_surface"):
        finding["source_surface"] = node["_source_surface"]
    if node.get("_source_dataset"):
        finding["source_dataset"] = node["_source_dataset"]
    return finding


def classify_node(node: dict[str, Any]) -> list[dict[str, Any]]:
    """Return deterministic findings for one node; does not infer missing data."""
    kind = _kind(node)
    text = _text(node)
    findings: list[dict[str, Any]] = []
    status = str(node.get("status", node.get("state", ""))).upper()

    confirmed_stale = status == "STALE" or node.get("stale_confirmed") is True
    may_be_stale = status == "MAY_BE_STALE" or (node.get("stale") is True and not confirmed_stale)
    if kind == "STREAM" and confirmed_stale:
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
    elif kind == "STREAM" and may_be_stale:
        findings.append(
            _finding(
                "STREAM_MAY_BE_STALE",
                node,
                "high",
                "SHOW STREAMS reports stale=TRUE, which Snowflake defines as may be stale",
                "Preserve the evidence and verify the retention/readability boundary with an authorized operator; do not reset, recreate, consume, or call SYSTEM$STREAM_HAS_DATA automatically.",
                11,
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

    if node.get("_source_dataset") == "copy_history":
        if status == "PARTIAL":
            findings.append(
                _finding(
                    "COPY_PARTIALLY_LOADED",
                    node,
                    "high",
                    f"COPY_HISTORY reports a partial load with error_count={int(_number(node, 'error_count') or 0)}",
                    "Preserve the file and load hashes, reconcile rejected versus committed rows, and prove target idempotence before any replay.",
                    27,
                )
            )
        elif status == "SKIPPED":
            findings.append(
                _finding(
                    "COPY_LOAD_SKIPPED",
                    node,
                    "high",
                    "COPY_HISTORY reports a skipped load",
                    "Reconcile the file hash against prior load history and target state before deciding whether a bounded replay is safe.",
                    27,
                )
            )
        elif status == "FAILED":
            findings.append(
                _finding(
                    "COPY_LOAD_FAILURE",
                    node,
                    "high",
                    "COPY_HISTORY reports a failed load",
                    "Preserve the hashed file/load evidence, diagnose the failure outside this redacted bundle, and prove idempotence before replay.",
                    28,
                )
            )

    if kind == "PIPE" and node.get("_source_dataset") != "copy_history":
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
        elif status in {"FAILED", "FAILED_AND_AUTO_SUSPENDED", "FAILURE", "ERROR"}:
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

    if kind == "DYNAMIC_TABLE":
        if status in {"FAILED", "UPSTREAM_FAILED", "FAILURE", "ERROR"}:
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
        elif status == "CANCELLED":
            findings.append(
                _finding(
                    "DYNAMIC_REFRESH_CANCELLED",
                    node,
                    "medium",
                    "dynamic table refresh was cancelled",
                    "Confirm whether cancellation was operator-intended; bound the missed refresh interval before changing scheduling state.",
                    24,
                )
            )
        elif status == "SUSPENDED":
            findings.append(
                _finding(
                    "DYNAMIC_TABLE_SUSPENDED",
                    node,
                    "high",
                    "current scheduling state is SUSPENDED",
                    "Measure the suspension against source retention and change-history horizons before proposing resume or reinitialization; this skill does not mutate the table.",
                    16,
                )
            )

    if kind == "PIPE" and node.get("_source_dataset") != "copy_history":
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
        elif status not in {"", "UNKNOWN", "RUNNING", "OK"}:
            findings.append(
                _finding(
                    "PIPE_NOT_RUNNING",
                    node,
                    "high",
                    f"current pipe execution state is {status}",
                    "Inspect the minimized pipe-status timestamps and current pipe configuration; any resume or refresh requires explicit operator approval.",
                    19,
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


def _receipt_privacy_issues(receipt: dict[str, Any]) -> list[str]:
    forbidden = {
        "connection_profile",
        "name",
        "database_name",
        "schema_name",
        "table_name",
        "query_id",
        "run_id",
        "root_task_id",
        "graph_run_group_id",
        "file_name",
        "stage_location",
        "definition",
        "comment",
        "owner",
        "warehouse",
        "notification_channel",
        "notification_channel_name",
        "error_message",
        "state_message",
        "predecessors",
        "task_relations",
        "integration",
        "error_integration",
        "success_integration",
        "pattern",
        "path",
        "oldest_pending_file_path",
        "last_ingested_file_path",
        "config",
        "condition",
        "text",
        "execute_as_user",
        "refresh_mode_reason",
        "invalid_reason",
        "error",
        "fault",
        "role_name",
        "user_name",
    }
    issues: list[str] = []
    safe_surface = (
        str(receipt.get("surface")) if receipt.get("surface") in PIPELINE_RECEIPT_CONTRACTS else "collector receipt"
    )

    def walk(value: Any, path: str) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if str(key).casefold() in forbidden:
                    issues.append(f"{safe_surface}: a raw field is forbidden in the evidence projection")
                if (
                    str(key).endswith("_sha256")
                    and child is not None
                    and (not isinstance(child, str) or not HEX64_RE.fullmatch(child))
                ):
                    issues.append(f"{safe_surface}: an invalid scoped digest is present")
                walk(child, f"{path}.{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, f"{path}[{index}]")

    walk(receipt.get("datasets"), "datasets")
    return issues


def _evidence_coverage(receipts: list[dict[str, Any]]) -> dict[str, Any]:
    history: dict[str, Any] | None = None
    current: list[dict[str, Any]] = []
    settlement_fields = {
        "task_history": ("task_history_settled_through_utc", "completed_time"),
        "dynamic_table_refresh_history": (
            "dynamic_table_refresh_history_settled_through_utc",
            "refresh_end_time",
        ),
        "copy_history": ("copy_history_settled_through_utc", "last_load_time"),
    }
    for receipt in receipts:
        datasets = receipt.get("datasets")
        contexts = datasets.get("execution_context") if isinstance(datasets, dict) else None
        context = (
            contexts[0] if isinstance(contexts, list) and len(contexts) == 1 and isinstance(contexts[0], dict) else None
        )
        if context is None:
            continue
        if receipt.get("surface") not in PIPELINE_RECEIPT_CONTRACTS:
            continue
        surface = str(receipt.get("surface"))
        if surface == "pipeline":
            start = _parse_node_time(context.get("window_start_utc"))
            end = _parse_node_time(context.get("window_end_utc"))
            dataset_coverage: dict[str, Any] = {}
            for dataset_name, (settled_field, basis) in settlement_fields.items():
                settled = _parse_node_time(context.get(settled_field))
                covered_end = max(start, min(end, settled)) if start and end and settled else None
                tail = None
                if covered_end and end and covered_end < end:
                    tail = {
                        "start": covered_end.isoformat(),
                        "end": end.isoformat(),
                        "classification": "unknown",
                    }
                dataset_coverage[dataset_name] = {
                    "event_time_basis": basis,
                    "covered_interval": {
                        "start": start.isoformat() if start else None,
                        "end": covered_end.isoformat() if covered_end else None,
                        "semantics": "half_open_utc",
                    },
                    "unsettled_tail": tail,
                    "row_limit": PIPELINE_RECEIPT_CONTRACTS["pipeline"]["row_limit"],
                }
            history = {
                "requested_window": {
                    "start": start.isoformat() if start else None,
                    "end": end.isoformat() if end else None,
                    "semantics": "half_open_utc",
                },
                "datasets": dataset_coverage,
            }
        else:
            observed = _parse_node_time(context.get("observed_at"))
            current.append(
                {
                    "surface": surface,
                    "observed_at": observed.isoformat() if observed else None,
                    "scope": "current_role_visible",
                    "row_limit": PIPELINE_RECEIPT_CONTRACTS[surface]["row_limit"],
                }
            )
    return {
        "history": history,
        "current": sorted(current, key=lambda item: (item["surface"], str(item["observed_at"]))),
    }


def analyze(
    snapshot: Any,
    *,
    trusted_input_sha256: str | None = None,
    evaluated_at: str | datetime | None = None,
) -> dict[str, Any]:
    original = snapshot
    input_trust = {
        "status": "NOT_APPLICABLE",
        "trusted": False,
        "actual_sha256": None,
        "non_claim": "A matching digest is an operator assertion of byte identity, not a signature or proof of Snowflake origin.",
    }
    evaluation_time = evaluated_at if isinstance(evaluated_at, datetime) else _parse_node_time(evaluated_at)
    if isinstance(evaluation_time, datetime):
        if evaluation_time.tzinfo is None:
            evaluation_time = None
        else:
            evaluation_time = evaluation_time.astimezone(timezone.utc)
    collector_receipts = _receipt_sequence(original) if isinstance(original, dict) else []
    receipt_issues: list[str] = []
    unsafe_receipt_issues: list[str] = []
    for receipt in collector_receipts:
        validation_issues = [
            *_collector_receipt_issues(receipt, evaluation_time),
            *_receipt_privacy_issues(receipt),
        ]
        receipt_issues.extend(validation_issues)
        unsafe_receipt_issues.extend(validation_issues)
    if isinstance(original, dict):
        actual_digest = canonical_bundle_digest(original)
        input_trust["actual_sha256"] = actual_digest
        if trusted_input_sha256 is None:
            input_trust["status"] = "UNTRUSTED"
        elif not isinstance(trusted_input_sha256, str) or not SHA256_RE.fullmatch(trusted_input_sha256):
            input_trust["status"] = "INVALID_TRUST_ANCHOR"
        elif trusted_input_sha256 != actual_digest:
            input_trust["status"] = "DIGEST_MISMATCH"
        else:
            input_trust["status"] = "DIGEST_MATCHED_OPERATOR_ASSERTED"
            input_trust["trusted"] = True
        if collector_receipts and unsafe_receipt_issues:
            # Never adapt invalid receipt fields into graph identifiers or
            # findings. That would let rejected values escape through normal
            # output or exception text before validation had taken effect.
            snapshot = {
                "observed_at": None,
                "evidence_source": "shared Snowflake evidence collector",
                "nodes": [{"id": "invalid-collector-evidence", "kind": "UNKNOWN", "status": "UNKNOWN"}],
                "edges": [],
            }
        else:
            snapshot = _collector_snapshot(original)
    nodes, edges, dangling_edges = normalize_snapshot(snapshot)
    components = _connected_components(nodes, edges)
    observed_at = _parse_observed_at(snapshot.get("observed_at"))
    evidence_source = snapshot.get("evidence_source")
    evidence_gaps: list[str] = []
    collector_mode = bool(collector_receipts)
    if collector_mode:
        if evaluation_time is None:
            receipt_issues.append(
                "an explicit timezone-aware evaluation timestamp is required for deterministic freshness"
            )
        surface_counts: dict[str, int] = defaultdict(int)
        for receipt in collector_receipts:
            surface_counts[str(receipt.get("surface"))] += 1
        required_once = REQUIRED_PIPELINE_SURFACES - {"pipeline-pipe-status"}
        missing = sorted(surface for surface in required_once if surface_counts.get(surface) != 1)
        if missing:
            receipt_issues.append(f"missing or duplicate required pipeline surfaces: {', '.join(missing)}")
        contexts: list[dict[str, Any]] = []
        for receipt in collector_receipts:
            datasets = receipt.get("datasets")
            rows = datasets.get("execution_context") if isinstance(datasets, dict) else None
            if isinstance(rows, list) and len(rows) == 1 and isinstance(rows[0], dict):
                contexts.append(rows[0])
        if contexts:
            binding_fields = (
                "organization_name_sha256",
                "account_identifier_sha256",
                "collector_user_sha256",
                "primary_role_sha256",
                "primary_role_type",
                "secondary_roles_sha256",
                "timezone",
            )
            anchor = contexts[0]
            for field in binding_fields:
                if any(context.get(field) != anchor.get(field) for context in contexts[1:]):
                    receipt_issues.append(f"execution_context mismatch across receipts: {field}")
            context_times = [_parse_observed_at(context.get("observed_at")) for context in contexts]
            valid_times = [value for value in context_times if value is not None]
            if len(valid_times) == len(contexts) and max(valid_times) - min(valid_times) > timedelta(minutes=15):
                receipt_issues.append("execution_context observations span more than 15 minutes")
        pipe_inventory: set[str] = set()
        pipe_statuses: list[str] = []
        for receipt in collector_receipts:
            datasets = receipt.get("datasets") if isinstance(receipt.get("datasets"), dict) else {}
            if receipt.get("surface") == "pipeline-pipe-current":
                pipe_inventory.update(
                    str(row.get("object_key_sha256"))
                    for row in datasets.get("current_pipes", [])
                    if isinstance(row, dict) and row.get("object_key_sha256")
                )
            elif receipt.get("surface") == "pipeline-pipe-status":
                pipe_statuses.extend(
                    str(row.get("object_key_sha256"))
                    for row in datasets.get("pipe_status", [])
                    if isinstance(row, dict) and row.get("object_key_sha256")
                )
        if set(pipe_statuses) != pipe_inventory or len(pipe_statuses) != len(pipe_inventory):
            receipt_issues.append("pipe status receipts do not exactly cover the current pipe inventory")
    else:
        receipt_issues.append("connector-neutral input is advisory and cannot establish evidence completeness")
    if not input_trust["trusted"]:
        receipt_issues.append("evidence bundle lacks a matching out-of-band trusted-input digest")
    evidence_gaps.extend(receipt_issues)
    if observed_at is None:
        evidence_gaps.append("observed_at must be a valid, non-future timezone timestamp")
    elif evaluation_time is not None and observed_at > evaluation_time:
        evidence_gaps.append("observed_at is after the explicit evaluation timestamp")
    if not isinstance(evidence_source, str) or not evidence_source.strip():
        evidence_gaps.append("evidence_source is required")
    if dangling_edges:
        evidence_gaps.append("one or more dependency edges reference missing nodes")
    if len(components) > 1 and not collector_mode:
        evidence_gaps.append("node inventory contains disconnected components")
    collector_safe_for_classification = not collector_mode or (not unsafe_receipt_issues and input_trust["trusted"])
    findings = (
        [finding for node_id in sorted(nodes) for finding in classify_node(nodes[node_id])]
        if collector_safe_for_classification
        else []
    )
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
        "evaluated_at": evaluation_time.isoformat() if evaluation_time else None,
        "observed_at": observed_at.isoformat() if observed_at else None,
        "evidence_source": _safe(evidence_source) if isinstance(evidence_source, str) else None,
        "evidence_complete": not evidence_gaps,
        "evidence_gaps": evidence_gaps,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "causal_chains": _dependency_chains(nodes, edges, findings),
        "dangling_edges": dangling_edges,
        "graph_complete": not dangling_edges and len(components) == 1 and not collector_mode and not receipt_issues,
        "connected_components": [[_safe(node_id) for node_id in group] for group in components],
        "findings": findings,
        "ordered_recovery": recovery,
        "post_fix_invariants": invariants,
        "limitations": limitations,
        "evidence_coverage": (
            _evidence_coverage(collector_receipts) if collector_mode else {"history": None, "current": []}
        ),
        "evidence_trust": input_trust,
        "collector_ingestion": {
            "status": "validated" if not receipt_issues else "insufficient_evidence",
            "surfaces": sorted(
                {
                    str(receipt.get("surface"))
                    for receipt in collector_receipts
                    if receipt.get("surface") in PIPELINE_RECEIPT_CONTRACTS
                }
            ),
            "receipt_count": len(collector_receipts),
        }
        if collector_mode
        else {
            "status": "not_used",
            "datasets": [],
            "message": "connector-neutral nodes were supplied directly",
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Classify a read-only Snowflake pipeline evidence snapshot")
    parser.add_argument("--input", "-i", help="JSON input path; default is stdin")
    parser.add_argument(
        "--trusted-input-sha256",
        help="Out-of-band sha256:<hex> recorded when the canonical bundle crossed a trusted local boundary",
    )
    parser.add_argument(
        "--evaluated-at",
        help="Explicit timezone-aware evaluation timestamp used for deterministic receipt freshness",
    )
    parser.add_argument(
        "--print-input-sha256",
        action="store_true",
        help="Print the canonical input digest for separate recording, then exit",
    )
    args = parser.parse_args(argv)
    try:
        raw = open(args.input, encoding="utf-8").read() if args.input else sys.stdin.read()
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("input root must be an object")
        if args.print_input_sha256:
            print(canonical_bundle_digest(data))
            return 0
        report = analyze(
            data,
            trusted_input_sha256=args.trusted_input_sha256,
            evaluated_at=args.evaluated_at,
        )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
