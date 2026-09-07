#!/usr/bin/env python3
"""Evaluate trusted Snowflake failover evidence without executing control-plane changes."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

VERSION = "3.0.0"
SQL_DIR = Path(__file__).resolve().parent / "sql"
SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$")
ERROR_CODE_RE = re.compile(r"^\d{1,10}$")

RECEIPT_NON_CLAIMS = [
    "No Snowflake mutation was executed by the reviewed collector SQL.",
    "Missing rows or permission-blocked views do not prove health.",
    "Account Usage evidence can lag and must not be treated as real-time state.",
    "The selected domain skill must evaluate freshness and completeness.",
    "A row count at the reviewed SQL limit may indicate truncated evidence.",
    "The embedded receipt SHA-256 is a self-checksum, not proof of origin or authenticity.",
    "The collector does not attest to operations performed elsewhere in the surrounding session or workflow.",
]
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
WINDOW_CONTEXT_FIELDS = COMMON_CONTEXT_FIELDS | {
    "window_start_utc",
    "window_end_utc",
    "window_semantics",
    "source_row_count",
    "source_row_limit",
    "truncation_possible",
    "provider_retention_days",
}
CURRENT_CONTEXT_FIELDS = COMMON_CONTEXT_FIELDS | {
    "source_row_count",
    "source_row_limit",
    "truncation_possible",
}
DANGLING_CONTEXT_FIELDS = CURRENT_CONTEXT_FIELDS | {
    "selected_group_key_sha256",
    "evaluation_scope",
}
CONTRACTS = {
    "replication": {
        "template": "replication.sql",
        "sources": ["INFORMATION_SCHEMA.REPLICATION_GROUP_REFRESH_HISTORY_ALL"],
        "datasets": {"execution_context", "replication_refresh_history"},
        "data": "replication_refresh_history",
        "selector": {"window_start": True, "window_end": True},
        "context": WINDOW_CONTEXT_FIELDS,
    },
    "replication-current": {
        "template": "replication-current.sql",
        "sources": ["SHOW FAILOVER GROUPS"],
        "datasets": {"execution_context", "current_groups"},
        "data": "current_groups",
        "selector": {},
        "context": CURRENT_CONTEXT_FIELDS,
    },
    "replication-progress": {
        "template": "replication-progress.sql",
        "sources": ["INFORMATION_SCHEMA.REPLICATION_GROUP_REFRESH_PROGRESS_ALL"],
        "datasets": {"execution_context", "replication_progress"},
        "data": "replication_progress",
        "selector": {"window_start": True, "window_end": True},
        "context": WINDOW_CONTEXT_FIELDS,
    },
    "replication-dangling": {
        "template": "replication-dangling.sql",
        "sources": ["INFORMATION_SCHEMA.REPLICATION_GROUP_DANGLING_REFERENCES"],
        "datasets": {"execution_context", "dangling_references"},
        "data": "dangling_references",
        "selector": {"replication_group": True},
        "context": DANGLING_CONTEXT_FIELDS,
    },
}
DATASET_FIELDS = {
    "replication_refresh_history": {
        "group_key_sha256",
        "group_type",
        "phase_name",
        "start_time",
        "end_time",
        "job_key_sha256",
        "primary_snapshot_timestamp",
        "error_code",
    },
    "current_groups": {
        "local_account_key_sha256",
        "local_group_key_sha256",
        "lineage_group_key_sha256",
        "group_type",
        "is_primary",
        "object_types_sha256",
        "allowed_accounts_sha256",
        "allowed_integration_types_sha256",
        "replication_schedule_sha256",
        "schedule_status",
        "next_scheduled_refresh",
    },
    "replication_progress": {
        "group_key_sha256",
        "group_type",
        "phase_name",
        "start_time",
        "end_time",
        "progress",
        "primary_snapshot_epoch",
        "error_code",
    },
    "dangling_references": {
        "selected_group_key_sha256",
        "referenced_entity_domain",
        "referenced_entity_key_sha256",
        "referencing_entity_domain",
        "referencing_entity_key_sha256",
        "referencing_entity_groups_sha256",
        "is_blocking_refresh",
    },
}
PHASES = {
    "SECONDARY_SYNCHRONIZING_MEMBERSHIP",
    "SECONDARY_UPLOADING_INVENTORY",
    "PRIMARY_UPLOADING_METADATA",
    "PRIMARY_UPLOADING_DATA",
    "SECONDARY_DOWNLOADING_METADATA",
    "SECONDARY_DOWNLOADING_DATA",
    "SECONDARY_COMMITTING",
    "COMPLETED",
    "FAILED",
    "CANCELED",
    "PROVIDER_OTHER",
}
POLICY_FIELDS = {
    "schema_version",
    "analysis_as_of_utc",
    "mode",
    "expected_group_count",
    "groups",
    "expected_dependency_count",
    "dependencies",
    "expected_validation_count",
    "validation_max_age_seconds",
    "validations",
}
GROUP_FIELDS = {
    "lineage_group_key_sha256",
    "source_account_key_sha256",
    "source_group_key_sha256",
    "target_account_key_sha256",
    "target_group_key_sha256",
    "expected_object_types_sha256",
    "expected_allowed_accounts_sha256",
    "expected_allowed_integration_types_sha256",
    "expected_replication_schedule_sha256",
    "rpo_seconds",
    "rto_seconds",
}
DEPENDENCY_FIELDS = {
    "dependency_key_sha256",
    "lineage_group_key_sha256",
    "ordering_proof_sha256",
}
VALIDATION_POLICY_FIELDS = {"validation_key_sha256", "lineage_group_key_sha256", "stage"}
VALIDATION_RECEIPT_FIELDS = {
    "schema_version",
    "validation_key_sha256",
    "lineage_group_key_sha256",
    "stage",
    "observed_at",
    "status",
    "receipt_sha256",
}
OPERATOR_RECEIPT_FIELDS = {
    "schema_version",
    "event_key_sha256",
    "lineage_group_key_sha256",
    "event",
    "source_account_key_sha256",
    "target_account_key_sha256",
    "change_record_sha256",
    "operator_key_sha256",
    "started_at",
    "completed_at",
    "outcome",
    "receipt_sha256",
}
MODES = {"PREFLIGHT", "FAILOVER_ATTESTATION", "FULL_DRILL_ATTESTATION"}


class EvidenceError(ValueError):
    """Raised when the strict wrapper, policy, or receipt contract is invalid."""


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def digest(value: Any) -> str:
    return f"sha256:{hashlib.sha256(canonical_json(value)).hexdigest()}"


def valid_hex(value: Any) -> bool:
    return isinstance(value, str) and bool(HEX64_RE.fullmatch(value))


def parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not UTC_RE.fullmatch(value):
        return None
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return None
    return parsed.astimezone(timezone.utc)


def format_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def temporal_qualification(
    data: dict[str, Any], valid_receipts: list[dict[str, Any]], evaluated_at: datetime
) -> dict[str, str | None]:
    observations = [
        parsed
        for receipt in valid_receipts
        for parsed in [parse_time(receipt["datasets"]["execution_context"][0]["observed_at"])]
        if parsed is not None
    ]
    observations.extend(
        parsed
        for row in data["validation_receipts"]
        if isinstance(row, dict)
        for parsed in [parse_time(row.get("observed_at"))]
        if parsed is not None
    )
    observations.extend(
        parsed
        for row in data["operator_receipts"]
        if isinstance(row, dict)
        for field in ("started_at", "completed_at")
        for parsed in [parse_time(row.get(field))]
        if parsed is not None
    )
    return {
        "basis": "AS_OF_ONLY",
        "analysis_as_of_utc": format_utc(evaluated_at),
        "evidence_observed_from_utc": format_utc(min(observations)) if observations else None,
        "evidence_observed_through_utc": format_utc(max(observations)) if observations else None,
        # This deterministic analyzer has no independently trusted live clock or
        # refresh service, so it makes no forward-validity claim.
        "valid_until_utc": format_utc(evaluated_at),
    }


def self_hash_valid(value: dict[str, Any]) -> bool:
    body = dict(value)
    supplied = body.pop("receipt_sha256", None)
    return isinstance(supplied, str) and supplied == digest(body)


def canonical_input_digest(data: dict[str, Any]) -> str:
    return digest({"schema_version": data.get("schema_version"), "collector_receipts": data.get("collector_receipts")})


def canonical_policy_digest(data: dict[str, Any]) -> str:
    return digest(data.get("policy"))


def canonical_operator_digest(data: dict[str, Any]) -> str:
    return digest(
        {
            "operator_receipts": data.get("operator_receipts"),
            "validation_receipts": data.get("validation_receipts"),
        }
    )


def validate_policy(policy: Any, evaluated_at: datetime) -> list[str]:
    if not isinstance(policy, dict) or set(policy) != POLICY_FIELDS or policy.get("schema_version") != "1":
        return ["policy_schema"]
    issues: list[str] = []
    if parse_time(policy.get("analysis_as_of_utc")) != evaluated_at:
        issues.append("policy_time")
    mode = policy.get("mode")
    if not isinstance(mode, str) or mode not in MODES:
        issues.append("policy_mode")
    if (
        type(policy.get("validation_max_age_seconds")) is not int
        or not 1 <= policy["validation_max_age_seconds"] <= 604800
    ):
        issues.append("policy_validation_age")
    groups = policy.get("groups")
    if not isinstance(groups, list) or not groups:
        return issues + ["policy_groups"]
    if type(policy.get("expected_group_count")) is not int or policy["expected_group_count"] != len(groups):
        issues.append("policy_group_count")
    group_keys: set[str] = set()
    pair_keys: set[tuple[str, str, str, str]] = set()
    for row in groups:
        if not isinstance(row, dict) or set(row) != GROUP_FIELDS:
            issues.append("policy_group_schema")
            continue
        hashes = [row.get(name) for name in GROUP_FIELDS if name.endswith("_sha256")]
        if any(not valid_hex(value) for value in hashes):
            issues.append("policy_group_hash")
        lineage = row.get("lineage_group_key_sha256")
        pair = (
            str(row.get("source_account_key_sha256")),
            str(row.get("source_group_key_sha256")),
            str(row.get("target_account_key_sha256")),
            str(row.get("target_group_key_sha256")),
        )
        if isinstance(lineage, str) and (lineage in group_keys or pair in pair_keys):
            issues.append("policy_group_duplicate")
        if row.get("source_account_key_sha256") == row.get("target_account_key_sha256"):
            issues.append("policy_group_direction")
        if isinstance(lineage, str):
            group_keys.add(lineage)
        pair_keys.add(pair)
        for field in ("rpo_seconds", "rto_seconds"):
            if type(row.get(field)) is not int or not 1 <= row[field] <= 604800:
                issues.append("policy_objective")
    dependencies = policy.get("dependencies")
    if not isinstance(dependencies, list):
        issues.append("policy_dependencies")
        dependencies = []
    if type(policy.get("expected_dependency_count")) is not int or policy["expected_dependency_count"] != len(
        dependencies
    ):
        issues.append("policy_dependency_count")
    dependency_keys: set[str] = set()
    for row in dependencies:
        if not isinstance(row, dict) or set(row) != DEPENDENCY_FIELDS:
            issues.append("policy_dependency_schema")
            continue
        if not valid_hex(row.get("dependency_key_sha256")) or not valid_hex(row.get("lineage_group_key_sha256")):
            issues.append("policy_dependency_hash")
        if row.get("ordering_proof_sha256") is not None and not valid_hex(row.get("ordering_proof_sha256")):
            issues.append("policy_dependency_hash")
        dependency_lineage = row.get("lineage_group_key_sha256")
        dependency_key = row.get("dependency_key_sha256")
        if not isinstance(dependency_lineage, str) or dependency_lineage not in group_keys:
            issues.append("policy_dependency_scope")
        if isinstance(dependency_key, str) and dependency_key in dependency_keys:
            issues.append("policy_dependency_duplicate")
        if isinstance(dependency_key, str):
            dependency_keys.add(dependency_key)
    validations = policy.get("validations")
    if not isinstance(validations, list) or not validations:
        issues.append("policy_validations")
        validations = []
    if type(policy.get("expected_validation_count")) is not int or policy["expected_validation_count"] != len(
        validations
    ):
        issues.append("policy_validation_count")
    validation_keys: set[str] = set()
    for row in validations:
        if not isinstance(row, dict) or set(row) != VALIDATION_POLICY_FIELDS:
            issues.append("policy_validation_schema")
            continue
        if not valid_hex(row.get("validation_key_sha256")) or not valid_hex(row.get("lineage_group_key_sha256")):
            issues.append("policy_validation_hash")
        validation_lineage = row.get("lineage_group_key_sha256")
        validation_key = row.get("validation_key_sha256")
        stage = row.get("stage")
        if (
            not isinstance(validation_lineage, str)
            or validation_lineage not in group_keys
            or not isinstance(stage, str)
            or stage
            not in {
                "PRE_FAILOVER",
                "POST_FAILOVER",
                "POST_FAILBACK",
            }
        ):
            issues.append("policy_validation_scope")
        if isinstance(validation_key, str) and validation_key in validation_keys:
            issues.append("policy_validation_duplicate")
        if isinstance(validation_key, str):
            validation_keys.add(validation_key)
    required_stages = {
        "PREFLIGHT": {"PRE_FAILOVER"},
        "FAILOVER_ATTESTATION": {"PRE_FAILOVER", "POST_FAILOVER"},
        "FULL_DRILL_ATTESTATION": {"PRE_FAILOVER", "POST_FAILOVER", "POST_FAILBACK"},
    }.get(mode if isinstance(mode, str) else "", set())
    for group_key in group_keys:
        stages = {
            row.get("stage")
            for row in validations
            if isinstance(row, dict)
            and row.get("lineage_group_key_sha256") == group_key
            and isinstance(row.get("stage"), str)
        }
        if not required_stages <= stages:
            issues.append("policy_validation_stage_coverage")
    return issues


def row_issues(dataset: str, row: Any) -> list[str]:
    if not isinstance(row, dict) or set(row) != DATASET_FIELDS[dataset]:
        return ["row_schema"]
    issues: list[str] = []
    if dataset == "replication_refresh_history" and not valid_hex(row.get("job_key_sha256")):
        issues.append("row_hash")
    if (
        dataset == "replication_progress"
        and row.get("phase_name") in {"COMPLETED", "FAILED", "CANCELED"}
        and row.get("end_time") is not None
    ):
        issues.append("row_terminal_end")
    for key, value in row.items():
        if key.endswith("_sha256"):
            if value is not None and not valid_hex(value):
                issues.append("row_hash")
        elif key in {"start_time", "end_time", "primary_snapshot_timestamp", "next_scheduled_refresh"}:
            if value is not None and parse_time(value) is None:
                issues.append("row_time")
        elif key == "primary_snapshot_epoch":
            if value is not None and (type(value) not in (int, float) or value < 0):
                issues.append("row_number")
        elif key == "group_type" and value not in {"FAILOVER", "REPLICATION", "PROVIDER_OTHER"}:
            issues.append("row_enum")
        elif key == "phase_name" and value not in PHASES:
            issues.append("row_enum")
        elif key == "schedule_status" and value not in {"STARTED", "SUSPENDED", "NOT_CONFIGURED", "PROVIDER_OTHER"}:
            issues.append("row_enum")
        elif key in {"is_primary", "is_blocking_refresh"} and type(value) is not bool:
            issues.append("row_boolean")
        elif key in {"referenced_entity_domain", "referencing_entity_domain"}:
            if not isinstance(value, str) or not re.fullmatch(r"[A-Z_]{1,64}", value):
                issues.append("row_enum")
        elif key == "progress":
            if value not in (None, "") and (
                not isinstance(value, str) or not re.fullmatch(r"(?:100|\d{1,2})(?:\.\d+)?", value)
            ):
                issues.append("row_progress")
        elif key == "error_code":
            if value is not None and (not isinstance(value, str) or not ERROR_CODE_RE.fullmatch(value)):
                issues.append("row_error_code")
    return issues


def receipt_issues(receipt: Any, evaluated_at: datetime) -> list[str]:
    if not isinstance(receipt, dict):
        return ["receipt_schema"]
    surface = receipt.get("surface")
    contract = CONTRACTS.get(surface)
    if contract is None:
        return ["receipt_surface"]
    issues: list[str] = []
    if set(receipt) != RECEIPT_FIELDS or receipt.get("schema_version") != "2":
        issues.append("receipt_schema")
    if (
        receipt.get("status") != "collected"
        or receipt.get("errors") != []
        or receipt.get("collection_mode") != "live-cli"
    ):
        issues.append("receipt_status")
    if not SHA256_RE.fullmatch(str(receipt.get("connection_profile_sha256", ""))):
        issues.append("receipt_connection")
    if (
        receipt.get("snowflake_query_id") is not None
        or receipt.get("snowflake_query_id_status") != "not_exposed_by_snow_cli_json_ext"
    ):
        issues.append("receipt_query")
    if receipt.get("non_claims") != RECEIPT_NON_CLAIMS:
        issues.append("receipt_non_claims")
    started = parse_time(receipt.get("collection_started_at"))
    completed = parse_time(receipt.get("collection_completed_at"))
    collected = parse_time(receipt.get("collected_at"))
    if not started or not completed or not collected or not (started <= collected == completed <= evaluated_at):
        issues.append("receipt_time")
    elif completed - started > timedelta(seconds=130) or evaluated_at - completed > timedelta(minutes=15):
        issues.append("receipt_stale")
    metadata = receipt.get("source_metadata")
    allowed_metadata = {"template", "source_views", "selector"}
    if surface in {"replication", "replication-progress"}:
        allowed_metadata.add("selector_values")
    if surface == "replication-dangling":
        allowed_metadata |= {"selector_binding", "rendered_sql_contract"}
    if not isinstance(metadata, dict) or set(metadata) != allowed_metadata:
        issues.append("receipt_metadata")
        metadata = {}
    selector = metadata.get("selector")
    if not isinstance(selector, dict) or selector != contract["selector"]:
        issues.append("receipt_selector")
    if (
        receipt.get("source_views") != contract["sources"]
        or metadata.get("source_views") != contract["sources"]
        or metadata.get("template") != contract["template"]
    ):
        issues.append("receipt_source")
    sql_path = SQL_DIR / contract["template"]
    template_hash = f"sha256:{hashlib.sha256(sql_path.read_bytes()).hexdigest()}" if sql_path.is_file() else None
    if receipt.get("sql_sha256") != template_hash or receipt.get("template_sha256") != template_hash:
        issues.append("receipt_template_hash")
    datasets = receipt.get("datasets")
    if (
        not isinstance(datasets, dict)
        or set(datasets) != contract["datasets"]
        or any(not isinstance(rows, list) for rows in datasets.values())
    ):
        issues.append("receipt_datasets")
        datasets = {}
    if receipt.get("expected_datasets") != sorted(contract["datasets"]):
        issues.append("receipt_expected_datasets")
    counts = {name: len(rows) for name, rows in datasets.items()}
    if (
        receipt.get("dataset_row_counts") != counts
        or type(receipt.get("row_count")) is not int
        or receipt.get("row_count") != sum(counts.values())
    ):
        issues.append("receipt_counts")
    if receipt.get("result_sha256") != digest(datasets) or not self_hash_valid(receipt):
        issues.append("receipt_hash")
    if receipt.get("row_limit") != 5000 or receipt.get("cap_scope") != "per_dataset":
        issues.append("receipt_cap")
    context_rows = datasets.get("execution_context", [])
    context = context_rows[0] if len(context_rows) == 1 and isinstance(context_rows[0], dict) else {}
    if set(context) != contract["context"]:
        issues.append("context_schema")
    for field in (
        "organization_name_sha256",
        "account_identifier_sha256",
        "collector_user_sha256",
        "primary_role_sha256",
        "secondary_roles_sha256",
    ):
        if not valid_hex(context.get(field)):
            issues.append("context_hash")
    observed = parse_time(context.get("observed_at"))
    if context.get("timezone") != "UTC" or context.get("primary_role_type") not in {"ROLE", "APPLICATION_INSTANCE"}:
        issues.append("context_enum")
    if (
        not observed
        or observed > evaluated_at
        or evaluated_at - observed > timedelta(minutes=15)
        or (started and completed and not started <= observed <= completed)
    ):
        issues.append("context_time")
    data_rows = datasets.get(contract["data"], [])
    source_count = context.get("source_row_count")
    capped = type(source_count) is int and source_count >= 5000
    if (
        type(source_count) is not int
        or source_count < len(data_rows)
        or (source_count < 5000 and source_count != len(data_rows))
    ):
        issues.append("context_count")
    if (
        context.get("source_row_limit") != 5000
        or type(context.get("truncation_possible")) is not bool
        or context.get("truncation_possible") is not capped
    ):
        issues.append("context_cap")
    if (
        type(receipt.get("truncation_possible")) is not bool
        or receipt.get("truncation_possible") is not capped
        or capped
    ):
        issues.append("receipt_truncated")
    if surface in {"replication", "replication-progress"}:
        window_start = parse_time(context.get("window_start_utc"))
        window_end = parse_time(context.get("window_end_utc"))
        values = metadata.get("selector_values")
        if (
            not window_start
            or not window_end
            or not window_start < window_end
            or window_end - window_start > timedelta(days=7)
            or not observed
            or not started
            or window_end > started
            or started - window_end > timedelta(seconds=60)
            or window_end > observed
            or evaluated_at - window_end > timedelta(minutes=15)
            or context.get("window_semantics") != "HALF_OPEN_UTC"
            or context.get("provider_retention_days") != 14
        ):
            issues.append("window_context")
        if (
            not isinstance(values, dict)
            or set(values) != {"window_start", "window_end"}
            or parse_time(values.get("window_start")) != window_start
            or parse_time(values.get("window_end")) != window_end
        ):
            issues.append("window_selector")
        elif receipt.get("selector_fingerprint") != digest(values):
            issues.append("window_fingerprint")
        elif sql_path.is_file():
            rendered = (
                sql_path.read_text(encoding="utf-8")
                .replace("__WINDOW_START_UTC__", values["window_start"])
                .replace("__WINDOW_END_UTC__", values["window_end"])
            )
            if receipt.get("rendered_sql_sha256") != f"sha256:{hashlib.sha256(rendered.encode()).hexdigest()}":
                issues.append("window_rendered_hash")
        for row in data_rows:
            if not isinstance(row, dict):
                continue
            started_at = parse_time(row.get("start_time"))
            ended_at = parse_time(row.get("end_time")) if row.get("end_time") is not None else None
            snapshot_at = (
                parse_time(row.get("primary_snapshot_timestamp"))
                if row.get("primary_snapshot_timestamp") is not None
                else None
            )
            if not started_at or not window_start or not window_end or not window_start <= started_at < window_end:
                issues.append("window_row_time")
            if ended_at is not None and (started_at is None or ended_at < started_at or ended_at > evaluated_at):
                issues.append("window_row_time")
            if snapshot_at is not None and snapshot_at > evaluated_at:
                issues.append("window_row_time")
    elif surface == "replication-dangling":
        selected = context.get("selected_group_key_sha256")
        binding = {"selected_group_key_sha256": selected}
        if (
            not valid_hex(selected)
            or context.get("evaluation_scope") != "CALLING_ACCOUNT_ONLY"
            or metadata.get("selector_binding") != binding
            or receipt.get("selector_fingerprint") != digest(binding)
            or metadata.get("rendered_sql_contract") != "privacy-bound-selector-v1"
        ):
            issues.append("selector_binding")
        elif sql_path.is_file():
            rendered = sql_path.read_text(encoding="utf-8").replace(
                "__REPLICATION_GROUP_IDENTIFIER__", f"__REPLICATION_GROUP_KEY_SHA256_{selected}__"
            )
            if receipt.get("rendered_sql_sha256") != f"sha256:{hashlib.sha256(rendered.encode()).hexdigest()}":
                issues.append("selector_rendered_hash")
        if any(isinstance(row, dict) and row.get("selected_group_key_sha256") != selected for row in data_rows):
            issues.append("selector_scope")
    elif receipt.get("selector_fingerprint") is not None or receipt.get("rendered_sql_sha256") != template_hash:
        issues.append("unscoped_rendered_hash")
    seen: set[bytes] = set()
    natural_keys: set[tuple[Any, ...]] = set()
    for row in data_rows:
        issues.extend(row_issues(contract["data"], row))
        if isinstance(row, dict):
            encoded = canonical_json(row)
            if encoded in seen:
                issues.append("row_duplicate")
            seen.add(encoded)
            if surface == "replication-current":
                natural_key = (row.get("local_account_key_sha256"), row.get("local_group_key_sha256"))
                if row.get("local_account_key_sha256") != context.get("account_identifier_sha256"):
                    issues.append("row_account_context")
            elif surface == "replication":
                # REPLICATION_GROUP_REFRESH_HISTORY returns one current-status
                # row per JOB_UUID, so a second row for the same job is
                # contradictory evidence rather than another phase record.
                natural_key = (row.get("job_key_sha256"),)
            elif surface == "replication-progress":
                natural_key = (row.get("group_key_sha256"), row.get("start_time"))
            else:
                natural_key = (
                    row.get("selected_group_key_sha256"),
                    row.get("referenced_entity_key_sha256"),
                    row.get("referencing_entity_key_sha256"),
                )
            try:
                duplicate_natural_key = natural_key in natural_keys
            except TypeError:
                issues.append("row_natural_key")
            else:
                if duplicate_natural_key:
                    issues.append("row_natural_key_duplicate")
                natural_keys.add(natural_key)
    return sorted(set(issues))


def validate_attestations(data: dict[str, Any], policy: dict[str, Any], evaluated_at: datetime) -> list[str]:
    issues: list[str] = []
    expected = {
        (row["validation_key_sha256"], row["lineage_group_key_sha256"], row["stage"]) for row in policy["validations"]
    }
    observed: set[tuple[str, str, str]] = set()
    for row in data["validation_receipts"]:
        if (
            not isinstance(row, dict)
            or set(row) != VALIDATION_RECEIPT_FIELDS
            or row.get("schema_version") != "1"
            or not self_hash_valid(row)
        ):
            issues.append("validation_receipt_schema")
            continue
        key = (row.get("validation_key_sha256"), row.get("lineage_group_key_sha256"), row.get("stage"))
        when = parse_time(row.get("observed_at"))
        key_is_hashable = all(isinstance(value, str) for value in key)
        if (
            not key_is_hashable
            or key not in expected
            or key in observed
            or row.get("status") not in {"PASS", "FAIL"}
            or not when
            or when > evaluated_at
            or evaluated_at - when > timedelta(seconds=policy["validation_max_age_seconds"])
        ):
            issues.append("validation_receipt_scope")
        if key_is_hashable:
            observed.add(key)
    if observed != expected:
        issues.append("validation_receipt_coverage")
    group_keys = {row["lineage_group_key_sha256"] for row in policy["groups"]}
    event_keys: set[str] = set()
    for row in data["operator_receipts"]:
        if (
            not isinstance(row, dict)
            or set(row) != OPERATOR_RECEIPT_FIELDS
            or row.get("schema_version") != "1"
            or not self_hash_valid(row)
        ):
            issues.append("operator_receipt_schema")
            continue
        for field in (
            "event_key_sha256",
            "lineage_group_key_sha256",
            "source_account_key_sha256",
            "target_account_key_sha256",
            "change_record_sha256",
            "operator_key_sha256",
        ):
            if not valid_hex(row.get(field)):
                issues.append("operator_receipt_hash")
        event_lineage = row.get("lineage_group_key_sha256")
        event_key = row.get("event_key_sha256")
        if (
            not isinstance(event_lineage, str)
            or event_lineage not in group_keys
            or not isinstance(event_key, str)
            or event_key in event_keys
        ):
            issues.append("operator_receipt_scope")
        if isinstance(event_key, str):
            event_keys.add(event_key)
        started, completed = parse_time(row.get("started_at")), parse_time(row.get("completed_at"))
        if (
            not started
            or not completed
            or not started < completed <= evaluated_at
            or row.get("event") not in {"FAILOVER", "FAILBACK"}
            or row.get("outcome") not in {"SUCCEEDED", "FAILED", "PARTIAL", "CANCELED"}
        ):
            issues.append("operator_receipt_event")
    if policy["mode"] == "PREFLIGHT" and data["operator_receipts"]:
        issues.append("operator_receipt_unexpected")
    return sorted(set(issues))


def add_finding(findings: list[dict[str, Any]], code: str, severity: str, scope: str | None) -> None:
    findings.append({"code": code, "severity": severity, "scope_sha256": scope})


def current_row(
    receipts: list[dict[str, Any]],
    account: str,
    group: str,
    *,
    before: datetime | None = None,
    after: datetime | None = None,
) -> dict[str, Any] | None:
    candidates: list[tuple[datetime, dict[str, Any]]] = []
    for receipt in receipts:
        context = receipt["datasets"]["execution_context"][0]
        # The SQL statement observation is the state boundary. Collection
        # completion can occur later and must not move evidence across an event.
        when = parse_time(context["observed_at"])
        if context["account_identifier_sha256"] != account or when is None:
            continue
        if before is not None and when >= before:
            continue
        if after is not None and when <= after:
            continue
        for row in receipt["datasets"]["current_groups"]:
            if row["local_account_key_sha256"] == account and row["local_group_key_sha256"] == group:
                candidates.append((when, row))
    return sorted(candidates, key=lambda item: item[0])[-1][1] if candidates else None


def evaluate_replication_leg(
    *,
    findings: list[dict[str, Any]],
    rpo_results: list[dict[str, Any]],
    history_receipts: list[dict[str, Any]],
    progress_receipts: list[dict[str, Any]],
    account: str,
    group_key: str,
    lineage: str,
    leg: str,
    anchor: datetime,
    objective_seconds: int,
) -> datetime | None:
    history_rows = [
        row
        for receipt in history_receipts
        if receipt["datasets"]["execution_context"][0]["account_identifier_sha256"] == account
        for row in receipt["datasets"]["replication_refresh_history"]
        if row.get("group_key_sha256") == group_key
    ]
    if any(row.get("group_type") != "FAILOVER" for row in history_rows):
        add_finding(findings, "GROUP_TYPE_MISMATCH", "critical", lineage)
    jobs: dict[str, list[dict[str, Any]]] = {}
    for row in history_rows:
        started = parse_time(row.get("start_time"))
        if row.get("group_type") == "FAILOVER" and started and started <= anchor:
            jobs.setdefault(row["job_key_sha256"], []).append(row)
    latest_job: list[dict[str, Any]] = []
    if jobs:
        job_times = {
            key: max(parse_time(row["start_time"]) or datetime.min.replace(tzinfo=timezone.utc) for row in rows)
            for key, rows in jobs.items()
        }
        latest_time = max(job_times.values())
        latest_keys = [key for key, value in job_times.items() if value == latest_time]
        if len(latest_keys) == 1:
            latest_job = jobs[latest_keys[0]]
    terminal = [row for row in latest_job if row["phase_name"] in {"COMPLETED", "FAILED", "CANCELED"}]
    snapshots = {
        parsed
        for row in latest_job
        if row["primary_snapshot_timestamp"] is not None
        for parsed in [parse_time(row["primary_snapshot_timestamp"])]
        if parsed is not None
    }
    completed_at = parse_time(terminal[0]["end_time"]) if len(terminal) == 1 else None
    snapshot = next(iter(snapshots)) if len(snapshots) == 1 else None
    if (
        len(terminal) != 1
        or terminal[0]["phase_name"] != "COMPLETED"
        or completed_at is None
        or completed_at > anchor
        or snapshot is None
        or snapshot > anchor
    ):
        add_finding(findings, "LATEST_REFRESH_NOT_PROVEN_COMPLETE", "critical", lineage)
        rpo_results.append(
            {
                "lineage_group_key_sha256": lineage,
                "leg": leg,
                "status": "UNPROVEN",
                "age_seconds": None,
                "objective_seconds": objective_seconds,
            }
        )
        snapshot = None
    else:
        age_seconds = int((anchor - snapshot).total_seconds())
        if age_seconds > objective_seconds:
            add_finding(findings, "RPO_BREACH", "critical", lineage)
        rpo_results.append(
            {
                "lineage_group_key_sha256": lineage,
                "leg": leg,
                "status": "PASS" if age_seconds <= objective_seconds else "FAIL",
                "age_seconds": age_seconds,
                "objective_seconds": objective_seconds,
            }
        )

    progress_rows = [
        row
        for receipt in progress_receipts
        if receipt["datasets"]["execution_context"][0]["account_identifier_sha256"] == account
        for row in receipt["datasets"]["replication_progress"]
        if row.get("group_key_sha256") == group_key
    ]
    if any(row.get("group_type") != "FAILOVER" for row in progress_rows):
        add_finding(findings, "GROUP_TYPE_MISMATCH", "critical", lineage)
    eligible_progress = [
        row
        for row in progress_rows
        if row.get("group_type") == "FAILOVER"
        and (started := parse_time(row.get("start_time"))) is not None
        and started <= anchor
    ]
    if not eligible_progress:
        add_finding(findings, "REFRESH_PROGRESS_MISSING", "critical", lineage)
    else:
        latest_progress = max(eligible_progress, key=lambda row: parse_time(row["start_time"]))
        progress_ended = parse_time(latest_progress["end_time"]) if latest_progress["end_time"] else None
        # Snowflake leaves PROGRESS empty for terminal phases. PHASE_NAME is the
        # provider's completion signal; percentages apply only to active phases.
        if latest_progress["phase_name"] != "COMPLETED" or (progress_ended is not None and progress_ended > anchor):
            add_finding(findings, "REFRESH_PROGRESS_NOT_COMPLETE", "critical", lineage)
    return snapshot


def check_secondary_schedule(
    findings: list[dict[str, Any]], row: dict[str, Any] | None, group: dict[str, Any], anchor: datetime
) -> None:
    lineage = group["lineage_group_key_sha256"]
    next_refresh = parse_time(row.get("next_scheduled_refresh")) if row else None
    if (
        row is None
        or row.get("is_primary") is not False
        or row.get("replication_schedule_sha256") != group["expected_replication_schedule_sha256"]
        or row.get("schedule_status") != "STARTED"
        or next_refresh is None
        or next_refresh <= anchor
        or next_refresh > anchor + timedelta(seconds=group["rpo_seconds"])
    ):
        add_finding(findings, "SCHEDULE_NOT_RUNNING", "critical", lineage)


def analyze(
    data: Any, *, evaluated_at: str, trusted_input_sha256: str, trusted_policy_sha256: str, trusted_operator_sha256: str
) -> dict[str, Any]:
    evaluated = parse_time(evaluated_at)
    if evaluated is None:
        raise EvidenceError("evaluated_at must be canonical UTC")
    if (
        not isinstance(data, dict)
        or set(data) != {"schema_version", "policy", "collector_receipts", "operator_receipts", "validation_receipts"}
        or data.get("schema_version") != "2"
        or not all(
            isinstance(data.get(name), list)
            for name in ("collector_receipts", "operator_receipts", "validation_receipts")
        )
    ):
        raise EvidenceError("input must match the exact schema-2 failover wrapper")
    input_digest = canonical_input_digest(data)
    policy_digest = canonical_policy_digest(data)
    operator_digest = canonical_operator_digest(data)
    policy = data["policy"]
    integrity_issues = validate_policy(policy, evaluated)
    if trusted_input_sha256 != input_digest:
        integrity_issues.append("trusted_input_mismatch")
    if trusted_policy_sha256 != policy_digest:
        integrity_issues.append("trusted_policy_mismatch")
    if trusted_operator_sha256 != operator_digest:
        integrity_issues.append("trusted_operator_mismatch")
    valid_receipts: list[dict[str, Any]] = []
    for receipt in data["collector_receipts"]:
        found = receipt_issues(receipt, evaluated)
        integrity_issues.extend(found)
        if not found:
            valid_receipts.append(receipt)
    if not integrity_issues and isinstance(policy, dict):
        integrity_issues.extend(validate_attestations(data, policy, evaluated))
    receipt_hashes = sorted(receipt["receipt_sha256"] for receipt in valid_receipts)
    temporal = temporal_qualification(data, valid_receipts, evaluated)
    if integrity_issues:
        report = {
            "schema_version": "2",
            "analyzer_version": VERSION,
            "overall_status": "INCONCLUSIVE",
            "evidence_integrity_status": "INVALID",
            "coverage_status": "UNPROVEN",
            "temporal_qualification": temporal,
            "findings": [{"code": "EVIDENCE_INTEGRITY_INVALID", "severity": "critical", "scope_sha256": None}],
            "integrity_issue_codes": sorted(set(integrity_issues)),
            "evidence": {
                "input_sha256": input_digest,
                "policy_sha256": policy_digest,
                "operator_sha256": operator_digest,
                "receipt_sha256s": receipt_hashes,
            },
            "non_claims": [
                "No failover, failback, refresh, resume, cancellation, redirect, or session change was executed.",
                "Embedded receipt hashes are self-checks; the three trusted digests are independent inputs.",
            ],
        }
        report["report_sha256"] = digest(report)
        return report

    by_surface = {name: [row for row in valid_receipts if row["surface"] == name] for name in CONTRACTS}
    findings: list[dict[str, Any]] = []
    groups = policy["groups"]
    mode = policy["mode"]
    current_receipts = by_surface["replication-current"]
    history_receipts = by_surface["replication"]
    progress_receipts = by_surface["replication-progress"]
    dangling_receipts = by_surface["replication-dangling"]
    expected_accounts = {
        row[side] for row in groups for side in ("source_account_key_sha256", "target_account_key_sha256")
    }
    current_account_values = [
        r["datasets"]["execution_context"][0]["account_identifier_sha256"] for r in current_receipts
    ]
    current_accounts = set(current_account_values)
    expected_snapshot_count = {"PREFLIGHT": 1, "FAILOVER_ATTESTATION": 2, "FULL_DRILL_ATTESTATION": 3}[mode]
    if current_accounts != expected_accounts or any(
        current_account_values.count(account) != expected_snapshot_count for account in expected_accounts
    ):
        add_finding(findings, "CURRENT_ACCOUNT_COVERAGE_INCOMPLETE", "critical", None)
    for account in expected_accounts:
        snapshot_times = [
            receipt["datasets"]["execution_context"][0]["observed_at"]
            for receipt in current_receipts
            if receipt["datasets"]["execution_context"][0]["account_identifier_sha256"] == account
        ]
        if len(snapshot_times) != len(set(snapshot_times)):
            add_finding(findings, "CURRENT_SNAPSHOT_ORDER_INVALID", "critical", account)
    organization_hashes = {
        receipt["datasets"]["execution_context"][0]["organization_name_sha256"] for receipt in valid_receipts
    }
    if len(organization_hashes) != 1:
        add_finding(findings, "ORGANIZATION_CONTEXT_MISMATCH", "critical", None)
    target_accounts = {row["target_account_key_sha256"] for row in groups}
    replication_accounts = set(target_accounts)
    if mode == "FULL_DRILL_ATTESTATION":
        replication_accounts |= {row["source_account_key_sha256"] for row in groups}
    history_accounts = [r["datasets"]["execution_context"][0]["account_identifier_sha256"] for r in history_receipts]
    if set(history_accounts) != replication_accounts or any(
        history_accounts.count(account) != 1 for account in replication_accounts
    ):
        add_finding(findings, "HISTORY_ACCOUNT_COVERAGE_INCOMPLETE", "critical", None)
    progress_accounts = [r["datasets"]["execution_context"][0]["account_identifier_sha256"] for r in progress_receipts]
    if set(progress_accounts) != replication_accounts or any(
        progress_accounts.count(account) != 1 for account in replication_accounts
    ):
        add_finding(findings, "PROGRESS_ACCOUNT_COVERAGE_INCOMPLETE", "critical", None)
    for account in expected_accounts:
        account_receipts = [
            receipt
            for receipt in valid_receipts
            if receipt["datasets"]["execution_context"][0]["account_identifier_sha256"] == account
        ]
        fingerprints = {
            tuple(
                context[field]
                for field in (
                    "organization_name_sha256",
                    "collector_user_sha256",
                    "primary_role_sha256",
                    "primary_role_type",
                    "secondary_roles_sha256",
                )
            )
            for receipt in account_receipts
            for context in [receipt["datasets"]["execution_context"][0]]
        }
        if len(fingerprints) != 1:
            add_finding(findings, "AUTHORIZATION_CONTEXT_MISMATCH", "critical", account)
    for account in replication_accounts:
        windows = {
            (context["window_start_utc"], context["window_end_utc"])
            for receipt in history_receipts + progress_receipts
            for context in [receipt["datasets"]["execution_context"][0]]
            if context["account_identifier_sha256"] == account
        }
        if len(windows) != 1:
            add_finding(findings, "HISTORY_PROGRESS_WINDOW_MISMATCH", "critical", account)
    expected_dangling = {
        (row[side_account], row[side_group])
        for row in groups
        for side_account, side_group in (
            ("source_account_key_sha256", "source_group_key_sha256"),
            ("target_account_key_sha256", "target_group_key_sha256"),
        )
    }
    observed_dangling_values = [
        (
            r["datasets"]["execution_context"][0]["account_identifier_sha256"],
            r["datasets"]["execution_context"][0]["selected_group_key_sha256"],
        )
        for r in dangling_receipts
    ]
    observed_dangling = set(observed_dangling_values)
    if observed_dangling != expected_dangling or any(
        observed_dangling_values.count(scope) != 1 for scope in expected_dangling
    ):
        add_finding(findings, "DANGLING_SCOPE_COVERAGE_INCOMPLETE", "critical", None)

    rpo_results: list[dict[str, Any]] = []
    operator_by_group: dict[str, list[dict[str, Any]]] = {}
    for receipt in data["operator_receipts"]:
        operator_by_group.setdefault(receipt["lineage_group_key_sha256"], []).append(receipt)
    validation_by_key = {
        (r["validation_key_sha256"], r["lineage_group_key_sha256"], r["stage"]): r for r in data["validation_receipts"]
    }
    for group in groups:
        lineage = group["lineage_group_key_sha256"]
        group_events = sorted(
            operator_by_group.get(lineage, []),
            key=lambda row: parse_time(row["started_at"]) or evaluated,
        )
        source_current = current_row(
            current_receipts, group["source_account_key_sha256"], group["source_group_key_sha256"]
        )
        target_current = current_row(
            current_receipts, group["target_account_key_sha256"], group["target_group_key_sha256"]
        )
        source_expected_primary = mode != "FAILOVER_ATTESTATION"
        for row, expected_primary, code in (
            (source_current, source_expected_primary, "SOURCE_CURRENT_STATE_INVALID"),
            (target_current, not source_expected_primary, "TARGET_CURRENT_STATE_INVALID"),
        ):
            if (
                row is None
                or row.get("lineage_group_key_sha256") != lineage
                or row.get("group_type") != "FAILOVER"
                or row.get("is_primary") is not expected_primary
            ):
                add_finding(findings, code, "critical", lineage)
        policy_current = source_current
        forward_secondary = target_current
        if group_events:
            policy_current = current_row(
                current_receipts,
                group["source_account_key_sha256"],
                group["source_group_key_sha256"],
                before=parse_time(group_events[0]["started_at"]),
            )
            forward_secondary = current_row(
                current_receipts,
                group["target_account_key_sha256"],
                group["target_group_key_sha256"],
                before=parse_time(group_events[0]["started_at"]),
            )
        if policy_current:
            if (
                policy_current.get("object_types_sha256") != group["expected_object_types_sha256"]
                or policy_current.get("allowed_accounts_sha256") != group["expected_allowed_accounts_sha256"]
                or policy_current.get("allowed_integration_types_sha256")
                != group["expected_allowed_integration_types_sha256"]
            ):
                add_finding(findings, "GROUP_POLICY_DRIFT", "critical", lineage)
            if policy_current.get("replication_schedule_sha256") != group["expected_replication_schedule_sha256"]:
                add_finding(findings, "SCHEDULE_NOT_RUNNING", "critical", lineage)
        failover_anchor = parse_time(group_events[0]["started_at"]) if group_events else evaluated
        check_secondary_schedule(findings, forward_secondary, group, failover_anchor)
        evaluate_replication_leg(
            findings=findings,
            rpo_results=rpo_results,
            history_receipts=history_receipts,
            progress_receipts=progress_receipts,
            account=group["target_account_key_sha256"],
            group_key=group["target_group_key_sha256"],
            lineage=lineage,
            leg="FORWARD_FAILOVER",
            anchor=failover_anchor,
            objective_seconds=group["rpo_seconds"],
        )
        if len(group_events) == 2:
            failback_anchor = parse_time(group_events[1]["started_at"])
            reverse_secondary = current_row(
                current_receipts,
                group["source_account_key_sha256"],
                group["source_group_key_sha256"],
                after=parse_time(group_events[0]["completed_at"]),
                before=failback_anchor,
            )
            check_secondary_schedule(findings, reverse_secondary, group, failback_anchor)
            evaluate_replication_leg(
                findings=findings,
                rpo_results=rpo_results,
                history_receipts=history_receipts,
                progress_receipts=progress_receipts,
                account=group["source_account_key_sha256"],
                group_key=group["source_group_key_sha256"],
                lineage=lineage,
                leg="REVERSE_FAILBACK",
                anchor=failback_anchor,
                objective_seconds=group["rpo_seconds"],
            )
        for receipt in dangling_receipts:
            context = receipt["datasets"]["execution_context"][0]
            if (context["account_identifier_sha256"], context["selected_group_key_sha256"]) in {
                (group["source_account_key_sha256"], group["source_group_key_sha256"]),
                (group["target_account_key_sha256"], group["target_group_key_sha256"]),
            }:
                for row in receipt["datasets"]["dangling_references"]:
                    add_finding(
                        findings,
                        "BLOCKING_DANGLING_REFERENCE"
                        if row["is_blocking_refresh"]
                        else "NONBLOCKING_DANGLING_REFERENCE",
                        "critical" if row["is_blocking_refresh"] else "warning",
                        lineage,
                    )
        expected_events = (
            [] if mode == "PREFLIGHT" else ["FAILOVER"] if mode == "FAILOVER_ATTESTATION" else ["FAILOVER", "FAILBACK"]
        )
        if [row["event"] for row in group_events] != expected_events or any(
            row["outcome"] != "SUCCEEDED" for row in group_events
        ):
            if expected_events:
                add_finding(findings, "OPERATOR_EVENT_COVERAGE_INVALID", "critical", lineage)
        if group_events:
            failover = group_events[0]
            if (
                failover["source_account_key_sha256"] != group["source_account_key_sha256"]
                or failover["target_account_key_sha256"] != group["target_account_key_sha256"]
            ):
                add_finding(findings, "FAILOVER_SCOPE_MISMATCH", "critical", lineage)
            duration = (parse_time(failover["completed_at"]) - parse_time(failover["started_at"])).total_seconds()
            if duration > group["rto_seconds"]:
                add_finding(findings, "RTO_BREACH", "critical", lineage)
            before_source = current_row(
                current_receipts,
                group["source_account_key_sha256"],
                group["source_group_key_sha256"],
                before=parse_time(failover["started_at"]),
            )
            transition_upper = parse_time(group_events[1]["started_at"]) if len(group_events) == 2 else None
            after_source = current_row(
                current_receipts,
                group["source_account_key_sha256"],
                group["source_group_key_sha256"],
                after=parse_time(failover["completed_at"]),
                before=transition_upper,
            )
            after_target = current_row(
                current_receipts,
                group["target_account_key_sha256"],
                group["target_group_key_sha256"],
                after=parse_time(failover["completed_at"]),
                before=transition_upper,
            )
            if (
                not before_source
                or before_source["is_primary"] is not True
                or not after_source
                or after_source["is_primary"] is not False
                or not after_target
                or after_target["is_primary"] is not True
            ):
                add_finding(findings, "FAILOVER_TRANSITION_UNPROVEN", "critical", lineage)
        if len(group_events) == 2:
            failback = group_events[1]
            if (
                parse_time(group_events[0]["completed_at"]) >= parse_time(failback["started_at"])
                or failback["source_account_key_sha256"] != group["target_account_key_sha256"]
                or failback["target_account_key_sha256"] != group["source_account_key_sha256"]
            ):
                add_finding(findings, "FAILBACK_ORDER_OR_SCOPE_INVALID", "critical", lineage)
            final_source = current_row(
                current_receipts,
                group["source_account_key_sha256"],
                group["source_group_key_sha256"],
                after=parse_time(failback["completed_at"]),
            )
            final_target = current_row(
                current_receipts,
                group["target_account_key_sha256"],
                group["target_group_key_sha256"],
                after=parse_time(failback["completed_at"]),
            )
            if (
                not final_source
                or final_source["is_primary"] is not True
                or not final_target
                or final_target["is_primary"] is not False
            ):
                add_finding(findings, "FAILBACK_TRANSITION_UNPROVEN", "critical", lineage)
            failback_duration = (
                parse_time(failback["completed_at"]) - parse_time(failback["started_at"])
            ).total_seconds()
            if failback_duration > group["rto_seconds"]:
                add_finding(findings, "FAILBACK_RTO_BREACH", "critical", lineage)
        if group_events:
            final_secondary = source_current if len(group_events) == 1 else target_current
            check_secondary_schedule(findings, final_secondary, group, evaluated)
        for expected in policy["validations"]:
            if expected["lineage_group_key_sha256"] == lineage:
                receipt = validation_by_key.get((expected["validation_key_sha256"], lineage, expected["stage"]))
                if receipt is None or receipt["status"] != "PASS":
                    add_finding(findings, "VALIDATION_NOT_PASSING", "critical", lineage)
                    continue
                observed_at = parse_time(receipt["observed_at"])
                if (
                    group_events
                    and expected["stage"] == "PRE_FAILOVER"
                    and observed_at >= parse_time(group_events[0]["started_at"])
                ):
                    add_finding(findings, "VALIDATION_EVENT_ORDER_INVALID", "critical", lineage)
                if group_events and expected["stage"] == "POST_FAILOVER":
                    upper = parse_time(group_events[1]["started_at"]) if len(group_events) == 2 else evaluated
                    if not parse_time(group_events[0]["completed_at"]) < observed_at < upper:
                        add_finding(findings, "VALIDATION_EVENT_ORDER_INVALID", "critical", lineage)
                if (
                    len(group_events) == 2
                    and expected["stage"] == "POST_FAILBACK"
                    and observed_at <= parse_time(group_events[1]["completed_at"])
                ):
                    add_finding(findings, "VALIDATION_EVENT_ORDER_INVALID", "critical", lineage)
    for dependency in policy["dependencies"]:
        if dependency["ordering_proof_sha256"] is None:
            add_finding(findings, "DEPENDENCY_ORDERING_UNPROVEN", "critical", dependency["lineage_group_key_sha256"])
    findings.sort(key=lambda row: (row["severity"], row["code"], row["scope_sha256"] or ""))
    critical = any(row["severity"] == "critical" for row in findings)
    if critical:
        status = "NOT_READY"
    elif findings:
        status = "AT_RISK"
    elif mode == "PREFLIGHT":
        status = "READY_FOR_OPERATOR_DRILL_AS_OF"
    elif mode == "FAILOVER_ATTESTATION":
        status = "FAILOVER_ATTESTED_AS_OF"
    else:
        status = "FULL_DRILL_ATTESTED_AS_OF"
    report = {
        "schema_version": "2",
        "analyzer_version": VERSION,
        "overall_status": status,
        "evidence_integrity_status": "VALID",
        "coverage_status": "COMPLETE",
        "temporal_qualification": temporal,
        "findings": findings,
        "integrity_issue_codes": [],
        "rpo_results": sorted(rpo_results, key=lambda row: (row["lineage_group_key_sha256"], row["leg"])),
        "evidence": {
            "input_sha256": input_digest,
            "policy_sha256": policy_digest,
            "operator_sha256": operator_digest,
            "receipt_sha256s": receipt_hashes,
        },
        "non_claims": [
            "No failover, failback, refresh, resume, cancellation, redirect, or session change was executed.",
            "RPO is derived only from a completed refresh primary snapshot; it does not prove application currency.",
            "Attested means independently trusted evidence matched the policy; it is not authorization to execute another transition.",
            "Positive verdicts are historical as-of statements and must not be used after valid_until_utc.",
        ],
    }
    report["report_sha256"] = digest(report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--evaluated-at", required=True)
    parser.add_argument("--trusted-input-sha256", required=True)
    parser.add_argument("--trusted-policy-sha256", required=True)
    parser.add_argument("--trusted-operator-sha256", required=True)
    args = parser.parse_args(argv)
    try:
        data = json.loads(args.input.read_text(encoding="utf-8"))
        report = analyze(
            data,
            evaluated_at=args.evaluated_at,
            trusted_input_sha256=args.trusted_input_sha256,
            trusted_policy_sha256=args.trusted_policy_sha256,
            trusted_operator_sha256=args.trusted_operator_sha256,
        )
    except (OSError, json.JSONDecodeError, EvidenceError, TypeError, ValueError) as exc:
        print(f"error: {type(exc).__name__}", file=sys.stderr)
        return 2
    sys.stdout.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0 if report["overall_status"] not in {"INCONCLUSIVE", "NOT_READY"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
