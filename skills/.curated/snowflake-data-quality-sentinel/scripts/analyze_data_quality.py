#!/usr/bin/env python3
"""Evaluate trusted schema-2 Snowflake data-quality evidence without mutation."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

VERSION = "2.1.0"
SQL_DIR = Path(__file__).resolve().parent / "sql"
SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
UTC_SELECTOR_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$")

RECEIPT_NON_CLAIMS = [
    "No Snowflake mutation was executed by the reviewed collector SQL.",
    "Missing rows or permission-blocked views do not prove health.",
    "Account Usage evidence can lag and must not be treated as real-time state.",
    "The selected domain skill must evaluate freshness and completeness.",
    "A row count at the reviewed SQL limit may indicate truncated evidence.",
    "The embedded receipt SHA-256 is a self-checksum, not proof of origin or authenticity.",
    "The collector does not attest to operations performed elsewhere in the surrounding session or workflow.",
]

RECEIPT_CONTRACTS = {
    "data-quality": {
        "template": "data-quality.sql",
        "sources": ["SNOWFLAKE.LOCAL.DATA_QUALITY_MONITORING_EXPECTATION_STATUS"],
        "datasets": {"execution_context", "expectation_history"},
        "cap_datasets": {"expectation_history"},
        "row_limit": 5000,
        "selector": {"window_start": True, "window_end": True},
    },
    "data-quality-associations-current": {
        "template": "data-quality-associations-current.sql",
        "sources": ["INFORMATION_SCHEMA.DATA_METRIC_FUNCTION_REFERENCES"],
        "datasets": {"execution_context", "current_associations"},
        "cap_datasets": {"current_associations"},
        "row_limit": 5000,
        "selector": {"data_quality_object": True, "data_quality_domain": True},
    },
    "data-quality-expectations-current": {
        "template": "data-quality-expectations-current.sql",
        "sources": ["INFORMATION_SCHEMA.DATA_METRIC_FUNCTION_EXPECTATIONS"],
        "datasets": {"execution_context", "current_expectations"},
        "cap_datasets": {"current_expectations"},
        "row_limit": 5000,
        "selector": {"data_quality_object": True, "data_quality_domain": True},
    },
    "data-quality-notification-current": {
        "template": "data-quality-notification-current.sql",
        "sources": ["INFORMATION_SCHEMA.DATA_METRIC_FUNCTION_REFERENCES"],
        "datasets": {"execution_context", "notification_associations"},
        "cap_datasets": {"notification_associations"},
        "row_limit": 5000,
        "selector": {"data_quality_object": True, "data_quality_domain": True},
    },
}
REQUIRED_SINGLETON_SURFACES = {
    "data-quality",
}
SELECTOR_BOUND_SURFACES = {
    "data-quality-associations-current",
    "data-quality-expectations-current",
    "data-quality-notification-current",
}
POLICY_FIELDS = {
    "schema_version",
    "expected_requirement_count",
    "analysis_as_of_utc",
    "history_assumption_delay_seconds",
    "history_assumption_status",
    "requirements",
}
REQUIREMENT_FIELDS = {
    "requirement_key_sha256",
    "object_key_sha256",
    "association_key_sha256",
    "metric_key_sha256",
    "expectation_key_sha256",
    "definition_sha256",
    "schedule_sha256",
    "expected_execution_role_sha256",
    "group_definition_sha256",
    "schedule_mode",
    "max_result_age_seconds",
    "notification_required",
    "objective_mode",
    "object_domain",
    "filter_sha256",
    "expected_group_limit",
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
HISTORY_CONTEXT_FIELDS = COMMON_CONTEXT_FIELDS | {
    "window_start_utc",
    "window_end_utc",
    "window_semantics",
    "per_dataset_row_limit",
    "provider_latency_documented",
    "settlement_policy_status",
}
SELECTOR_CONTEXT_FIELDS = COMMON_CONTEXT_FIELDS | {
    "source_row_count",
    "source_row_limit",
    "truncation_possible",
    "selected_object_key_sha256",
    "selected_object_domain",
}
DATASET_FIELDS = {
    "expectation_history": {
        "object_key_sha256",
        "association_key_sha256",
        "metric_key_sha256",
        "expectation_key_sha256",
        "definition_sha256",
        "scheduled_time",
        "change_commit_time",
        "measurement_time",
        "expectation_violated",
    },
    "current_associations": {
        "object_key_sha256",
        "association_key_sha256",
        "metric_key_sha256",
        "object_domain",
        "schedule_sha256",
        "schedule_status",
        "execution_role_sha256",
        "association_level",
        "filter_sha256",
        "group_definition_sha256",
        "group_limit",
        "anomaly_status",
        "anomaly_sensitivity",
    },
    "current_expectations": {
        "object_key_sha256",
        "association_key_sha256",
        "metric_key_sha256",
        "expectation_key_sha256",
        "definition_sha256",
    },
    "notification_associations": {
        "object_key_sha256",
        "association_key_sha256",
        "metric_key_sha256",
        "object_domain",
        "notification_status",
    },
}
NULLABLE_HASH_FIELDS = {"execution_role_sha256", "filter_sha256", "group_definition_sha256"}
TIMESTAMP_FIELDS = {"scheduled_time", "change_commit_time", "measurement_time"}
ENUM_FIELDS = {
    "object_domain": {"TABLE", "VIEW", "PROVIDER_OTHER"},
    "schedule_status": {
        "STARTED",
        "STARTED_AND_PENDING_SCHEDULE_UPDATE",
        "SUSPENDED",
        "SUSPENDED_TABLE_DOES_NOT_EXIST_OR_NOT_AUTHORIZED",
        "SUSPENDED_DATA_METRIC_FUNCTION_DOES_NOT_EXIST_OR_NOT_AUTHORIZED",
        "SUSPENDED_TABLE_COLUMN_DOES_NOT_EXIST_OR_NOT_AUTHORIZED",
        "SUSPENDED_INSUFFICIENT_PRIVILEGE_TO_EXECUTE_DATA_METRIC_FUNCTION",
        "SUSPENDED_ACTIVE_EVENT_TABLE_DOES_NOT_EXIST_OR_NOT_AUTHORIZED",
        "PROVIDER_OTHER",
    },
    "association_level": {"TABLE", "SCHEMA", "PROVIDER_OTHER"},
    "anomaly_status": {"NOT_CONFIGURED", "TRAINING_IN_PROGRESS", "PROVIDER_OTHER"},
    "anomaly_sensitivity": {"LOW", "MEDIUM", "HIGH", "NOT_CONFIGURED", "PROVIDER_OTHER"},
    "notification_status": {"ENABLED", "DISABLED", "ERROR_INSUFFICIENT_PRIVILEGE", "NOT_CONFIGURED", "PROVIDER_OTHER"},
}
UNIQUE_KEYS = {
    "expectation_history": ("association_key_sha256", "expectation_key_sha256", "measurement_time"),
    "current_associations": ("association_key_sha256",),
    "current_expectations": ("association_key_sha256", "expectation_key_sha256"),
    "notification_associations": ("association_key_sha256",),
}


class EvidenceError(ValueError):
    """Raised for an invalid trusted wrapper or policy."""


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def digest(value: Any) -> str:
    return f"sha256:{hashlib.sha256(canonical_json(value)).hexdigest()}"


def canonical_input_digest(data: dict[str, Any]) -> str:
    if not isinstance(data, dict):
        raise EvidenceError("invalid input")
    return digest({"schema_version": data.get("schema_version"), "collector_receipts": data.get("collector_receipts")})


def canonical_policy_digest(data: dict[str, Any]) -> str:
    if not isinstance(data, dict) or not isinstance(data.get("policy"), dict):
        raise EvidenceError("invalid policy")
    return canonical_policy_document_digest(data["policy"])


def canonical_policy_document_digest(policy: Any) -> str:
    validate_policy(policy)
    return digest(policy)


def parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def valid_hex(value: Any, *, nullable: bool = False) -> bool:
    return (value is None and nullable) or (isinstance(value, str) and HEX64_RE.fullmatch(value) is not None)


def validate_policy(policy: Any) -> list[dict[str, Any]]:
    if not isinstance(policy, dict) or set(policy) != POLICY_FIELDS or policy.get("schema_version") != "1":
        raise EvidenceError("invalid policy")
    requirements = policy.get("requirements")
    count = policy.get("expected_requirement_count")
    assumption_delay = policy.get("history_assumption_delay_seconds")
    if not isinstance(requirements, list) or type(count) is not int or count < 0 or count != len(requirements):
        raise EvidenceError("invalid policy")
    if parse_time(policy.get("analysis_as_of_utc")) is None:
        raise EvidenceError("invalid policy")
    if policy.get("history_assumption_status") != "OWNER_DECLARED_NOT_PROVIDER_GUARANTEED":
        raise EvidenceError("invalid policy")
    if assumption_delay is not None and (type(assumption_delay) is not int or not 0 <= assumption_delay <= 604800):
        raise EvidenceError("invalid policy")
    seen_requirements: set[str] = set()
    seen_expectations: set[tuple[str, str]] = set()
    association_identities: dict[str, tuple[Any, ...]] = {}
    normalized: list[dict[str, Any]] = []
    for row in requirements:
        if not isinstance(row, dict) or set(row) != REQUIREMENT_FIELDS:
            raise EvidenceError("invalid policy")
        for field in (
            "requirement_key_sha256",
            "object_key_sha256",
            "association_key_sha256",
            "metric_key_sha256",
            "expectation_key_sha256",
            "definition_sha256",
            "schedule_sha256",
        ):
            if not valid_hex(row.get(field)):
                raise EvidenceError("invalid policy")
        for field in ("expected_execution_role_sha256", "group_definition_sha256", "filter_sha256"):
            if not valid_hex(row.get(field), nullable=True):
                raise EvidenceError("invalid policy")
        if row.get("schedule_mode") not in {"INTERVAL", "CRON", "TRIGGER_ON_CHANGES"}:
            raise EvidenceError("invalid policy")
        if row.get("objective_mode") not in {"EXPECTATION", "ANOMALY"}:
            raise EvidenceError("invalid policy")
        if row.get("object_domain") not in {"TABLE", "VIEW"}:
            raise EvidenceError("invalid policy")
        group_limit = row.get("expected_group_limit")
        if group_limit is not None and (type(group_limit) is not int or not 1 <= group_limit <= 1000):
            raise EvidenceError("invalid policy")
        age = row.get("max_result_age_seconds")
        if type(age) is not int or not 1 <= age <= 31_536_000 or type(row.get("notification_required")) is not bool:
            raise EvidenceError("invalid policy")
        expectation_key = (row["association_key_sha256"], row["expectation_key_sha256"])
        if row["requirement_key_sha256"] in seen_requirements or expectation_key in seen_expectations:
            raise EvidenceError("invalid policy")
        association_identity = (
            row["object_key_sha256"],
            row["metric_key_sha256"],
            row["schedule_sha256"],
            row["expected_execution_role_sha256"],
            row["group_definition_sha256"],
            row["object_domain"],
            row["filter_sha256"],
            row["expected_group_limit"],
        )
        prior_identity = association_identities.setdefault(row["association_key_sha256"], association_identity)
        if prior_identity != association_identity:
            raise EvidenceError("invalid policy")
        seen_requirements.add(row["requirement_key_sha256"])
        seen_expectations.add(expectation_key)
        normalized.append(dict(row))
    return sorted(normalized, key=lambda item: item["requirement_key_sha256"])


def context_fields(surface: str) -> set[str]:
    if surface == "data-quality":
        return HISTORY_CONTEXT_FIELDS
    return SELECTOR_CONTEXT_FIELDS


def row_issues(dataset: str, row: Any) -> list[str]:
    if not isinstance(row, dict) or set(row) != DATASET_FIELDS[dataset]:
        return ["row_schema"]
    issues: list[str] = []
    for field, value in row.items():
        if field.endswith("_sha256"):
            if not valid_hex(value, nullable=field in NULLABLE_HASH_FIELDS):
                issues.append("row_hash")
        elif field in TIMESTAMP_FIELDS:
            if value is not None and parse_time(value) is None:
                issues.append("row_timestamp")
        elif field == "expectation_violated":
            if value is not None and type(value) is not bool:
                issues.append("row_boolean")
        elif field == "group_limit":
            if value is not None and (type(value) is not int or not 1 <= value <= 1000):
                issues.append("row_number")
        elif field in ENUM_FIELDS:
            if value not in ENUM_FIELDS[field]:
                issues.append("row_enum")
        elif value is not None:
            issues.append("row_unreviewed_text")
    return issues


def receipt_issues(receipt: Any, evaluated_at: datetime) -> list[str]:
    if not isinstance(receipt, dict):
        return ["receipt_schema"]
    surface = receipt.get("surface")
    contract = RECEIPT_CONTRACTS.get(surface)
    if contract is None:
        return ["receipt_surface"]
    issues: list[str] = []
    if set(receipt) != RECEIPT_FIELDS or receipt.get("schema_version") != "2":
        issues.append("receipt_schema")
    if receipt.get("status") != "collected" or receipt.get("errors") != []:
        issues.append("receipt_status")
    if receipt.get("collection_mode") != "live-cli":
        issues.append("receipt_mode")
    if not isinstance(receipt.get("connection_profile_sha256"), str) or not SHA256_RE.fullmatch(
        receipt["connection_profile_sha256"]
    ):
        issues.append("receipt_connection")
    if (
        receipt.get("snowflake_query_id") is not None
        or receipt.get("snowflake_query_id_status") != "not_exposed_by_snow_cli_json_ext"
    ):
        issues.append("receipt_query_id")
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
    if surface == "data-quality":
        allowed_metadata.add("selector_values")
    if surface in SELECTOR_BOUND_SURFACES:
        allowed_metadata |= {"selector_binding", "rendered_sql_contract"}
    if not isinstance(metadata, dict) or set(metadata) != allowed_metadata:
        issues.append("receipt_source_metadata")
        metadata = {}
    selector_contract = metadata.get("selector")
    selector_contract_valid = (
        isinstance(selector_contract, dict)
        and set(selector_contract) == set(contract["selector"])
        and all(type(value) is bool and value is True for value in selector_contract.values())
    )
    if (
        receipt.get("source_views") != contract["sources"]
        or metadata.get("source_views") != contract["sources"]
        or metadata.get("template") != contract["template"]
        or not selector_contract_valid
    ):
        issues.append("receipt_source_contract")

    sql_path = SQL_DIR / contract["template"]
    expected_template_hash = (
        f"sha256:{hashlib.sha256(sql_path.read_bytes()).hexdigest()}" if sql_path.is_file() else None
    )
    for field in ("sql_sha256", "template_sha256", "rendered_sql_sha256", "result_sha256", "receipt_sha256"):
        if not isinstance(receipt.get(field), str) or not SHA256_RE.fullmatch(receipt[field]):
            issues.append("receipt_hash")
    if (
        expected_template_hash is None
        or receipt.get("sql_sha256") != expected_template_hash
        or receipt.get("template_sha256") != expected_template_hash
    ):
        issues.append("receipt_template_hash")

    datasets = receipt.get("datasets")
    expected_datasets = contract["datasets"]
    if (
        not isinstance(datasets, dict)
        or set(datasets) != expected_datasets
        or any(not isinstance(rows, list) for rows in datasets.values())
    ):
        issues.append("receipt_datasets")
        datasets = {}
    if receipt.get("expected_datasets") != sorted(expected_datasets):
        issues.append("receipt_expected_datasets")
    expected_counts = {name: len(rows) for name, rows in datasets.items()}
    reported_counts = receipt.get("dataset_row_counts")
    counts_typed = isinstance(reported_counts, dict) and all(
        type(value) is int and value >= 0 for value in reported_counts.values()
    )
    if (
        not counts_typed
        or reported_counts != expected_counts
        or type(receipt.get("row_count")) is not int
        or receipt.get("row_count") != sum(expected_counts.values())
    ):
        issues.append("receipt_counts")
    if receipt.get("result_sha256") != digest(datasets):
        issues.append("receipt_result_hash")
    body = dict(receipt)
    body.pop("receipt_sha256", None)
    if receipt.get("receipt_sha256") != digest(body):
        issues.append("receipt_self_hash")
    if (
        type(receipt.get("row_limit")) is not int
        or receipt.get("row_limit") != contract["row_limit"]
        or receipt.get("cap_scope") != "per_dataset"
    ):
        issues.append("receipt_cap")
    emitted_count = sum(len(datasets.get(name, [])) for name in contract["cap_datasets"])
    context_rows = datasets.get("execution_context", [])
    cap_context = context_rows[0] if len(context_rows) == 1 and isinstance(context_rows[0], dict) else {}
    source_count = cap_context.get("source_row_count")
    if surface == "data-quality":
        capped = emitted_count >= contract["row_limit"]
    else:
        capped = type(source_count) is int and source_count >= contract["row_limit"]
    if (
        type(receipt.get("truncation_possible")) is not bool
        or receipt.get("truncation_possible") is not capped
        or capped
    ):
        issues.append("receipt_truncated")

    contexts = datasets.get("execution_context", [])
    context = contexts[0] if len(contexts) == 1 and isinstance(contexts[0], dict) else None
    if context is None or set(context) != context_fields(surface):
        issues.append("context_schema")
        context = {}
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
        or evaluated_at - observed > timedelta(seconds=900)
        or (started and completed and not started <= observed <= completed)
    ):
        issues.append("context_time")

    if surface == "data-quality":
        window_start = parse_time(context.get("window_start_utc"))
        window_end = parse_time(context.get("window_end_utc"))
        if (
            not window_start
            or not window_end
            or not window_start < window_end
            or window_end - window_start > timedelta(days=7)
            or context.get("window_semantics") != "HALF_OPEN_UTC"
            or type(context.get("per_dataset_row_limit")) is not int
            or context.get("per_dataset_row_limit") != 5000
            or type(context.get("provider_latency_documented")) is not bool
            or context.get("provider_latency_documented") is not False
            or context.get("settlement_policy_status") != "NOT_DECLARED"
        ):
            issues.append("history_context")
        selector_values = metadata.get("selector_values")
        if (
            not isinstance(selector_values, dict)
            or set(selector_values) != {"window_start", "window_end"}
            or any(
                not isinstance(value, str) or not UTC_SELECTOR_RE.fullmatch(value) for value in selector_values.values()
            )
            or parse_time(selector_values.get("window_start")) != window_start
            or parse_time(selector_values.get("window_end")) != window_end
        ):
            issues.append("history_selector")
        else:
            if receipt.get("selector_fingerprint") != digest(selector_values):
                issues.append("history_selector_hash")
            if sql_path.is_file():
                rendered = (
                    sql_path.read_text(encoding="utf-8")
                    .replace("__WINDOW_START_UTC__", selector_values["window_start"])
                    .replace("__WINDOW_END_UTC__", selector_values["window_end"])
                )
                if receipt.get("rendered_sql_sha256") != f"sha256:{hashlib.sha256(rendered.encode()).hexdigest()}":
                    issues.append("history_rendered_hash")
        for row in datasets.get("expectation_history", []):
            if isinstance(row, dict):
                measured = parse_time(row.get("measurement_time"))
                if not measured or not window_start or not window_end or not window_start <= measured < window_end:
                    issues.append("history_event_time")
    else:
        selected = context.get("selected_object_key_sha256")
        domain = context.get("selected_object_domain")
        binding = {"selected_object_key_sha256": selected, "selected_object_domain": domain}
        if not valid_hex(selected) or domain not in {"TABLE", "VIEW"} or metadata.get("selector_binding") != binding:
            issues.append("selector_binding")
        elif (
            receipt.get("selector_fingerprint") != digest(binding)
            or metadata.get("rendered_sql_contract") != "privacy-bound-selector-v1"
        ):
            issues.append("selector_hash")
        elif sql_path.is_file():
            rendered = sql_path.read_text(encoding="utf-8")
            rendered = rendered.replace(
                "__DATA_QUALITY_DATABASE_IDENTIFIER__",
                f"__DATA_QUALITY_DATABASE_BOUND_TO_OBJECT_KEY_SHA256_{selected}__",
            )
            rendered = rendered.replace(
                "__DATA_QUALITY_OBJECT_IDENTIFIER__",
                f"__DATA_QUALITY_OBJECT_KEY_SHA256_{selected}__",
            )
            rendered = rendered.replace("__DATA_QUALITY_DOMAIN__", f"__DATA_QUALITY_DOMAIN_{domain}__")
            expected_rendered = f"sha256:{hashlib.sha256(rendered.encode()).hexdigest()}"
            if receipt.get("rendered_sql_sha256") != expected_rendered:
                issues.append("selector_rendered_hash")
        data_name = next(iter(contract["cap_datasets"]))
        for row in datasets.get(data_name, []):
            if isinstance(row, dict):
                row_domain_mismatch = (
                    "object_domain" in DATASET_FIELDS[data_name] and row.get("object_domain") != domain
                )
                if row.get("object_key_sha256") != selected or row_domain_mismatch:
                    issues.append("selector_scope")
        if (
            type(context.get("source_row_limit")) is not int
            or context.get("source_row_limit") != 5000
            or type(context.get("source_row_count")) is not int
            or context.get("source_row_count") < len(datasets.get(data_name, []))
            or (
                context.get("source_row_count") < 5000
                and context.get("source_row_count") != len(datasets.get(data_name, []))
            )
            or type(context.get("truncation_possible")) is not bool
            or context.get("truncation_possible") is not capped
        ):
            issues.append("selector_context")

    for dataset, rows in datasets.items():
        if dataset == "execution_context":
            continue
        keys: list[tuple[Any, ...]] = []
        for row in rows:
            issues.extend(row_issues(dataset, row))
            if isinstance(row, dict):
                keys.append(tuple(row.get(field) for field in UNIQUE_KEYS[dataset]))
        if len(keys) != len(set(keys)):
            issues.append("duplicate_natural_key")
    return sorted(set(issues))


def finding(
    code: str, scope: str, detail: str, action: str, *, quality: str | None = None, monitoring: str | None = None
) -> dict[str, Any]:
    return {
        "code": code,
        "scope": scope,
        "detail": detail,
        "action": action,
        "quality_impact": quality,
        "monitoring_impact": monitoring,
    }


def analyze(data: Any, *, evaluated_at: str, trusted_input_sha256: str, trusted_policy_sha256: str) -> dict[str, Any]:
    if (
        not isinstance(data, dict)
        or set(data) != {"schema_version", "policy", "collector_receipts"}
        or data.get("schema_version") != "2"
        or not isinstance(data.get("collector_receipts"), list)
    ):
        raise EvidenceError("invalid input")
    evaluated = parse_time(evaluated_at)
    if evaluated is None:
        raise EvidenceError("invalid evaluation time")
    requirements = validate_policy(data["policy"])
    if parse_time(data["policy"]["analysis_as_of_utc"]) != evaluated:
        raise EvidenceError("invalid policy")
    input_digest = canonical_input_digest(data)
    policy_digest = canonical_policy_digest(data)
    input_trusted = isinstance(trusted_input_sha256, str) and trusted_input_sha256 == input_digest
    policy_trusted = isinstance(trusted_policy_sha256, str) and trusted_policy_sha256 == policy_digest

    receipts = data["collector_receipts"]
    receipt_errors: list[str] = []
    valid_receipts: list[dict[str, Any]] = []
    for receipt in receipts:
        issues = receipt_issues(receipt, evaluated)
        if issues:
            receipt_errors.extend(issues)
        elif isinstance(receipt, dict):
            valid_receipts.append(receipt)
    surfaces = [receipt["surface"] for receipt in valid_receipts]
    for surface in REQUIRED_SINGLETON_SURFACES:
        if surfaces.count(surface) != 1:
            receipt_errors.append("required_surface_count")
    governed_objects = {(row["object_key_sha256"], row["object_domain"]) for row in requirements}
    required_notification_objects = {
        (row["object_key_sha256"], row["object_domain"]) for row in requirements if row["notification_required"]
    }
    selected_receipts: dict[str, list[dict[str, Any]]] = {}
    for surface in SELECTOR_BOUND_SURFACES:
        surface_receipts = [receipt for receipt in valid_receipts if receipt["surface"] == surface]
        selected_receipts[surface] = surface_receipts
        selected_objects = [
            (
                receipt["datasets"]["execution_context"][0]["selected_object_key_sha256"],
                receipt["datasets"]["execution_context"][0]["selected_object_domain"],
            )
            for receipt in surface_receipts
        ]
        if len(selected_objects) != len(set(selected_objects)):
            receipt_errors.append("duplicate_object_selector")
        expected_objects = (
            required_notification_objects if surface == "data-quality-notification-current" else governed_objects
        )
        if set(selected_objects) != expected_objects:
            receipt_errors.append("governed_object_coverage")

    contexts = [receipt["datasets"]["execution_context"][0] for receipt in valid_receipts]
    identity_fields = (
        "organization_name_sha256",
        "account_identifier_sha256",
        "collector_user_sha256",
        "primary_role_sha256",
        "primary_role_type",
        "secondary_roles_sha256",
        "timezone",
    )
    if contexts and any(
        tuple(context.get(field) for field in identity_fields)
        != tuple(contexts[0].get(field) for field in identity_fields)
        for context in contexts[1:]
    ):
        receipt_errors.append("mixed_execution_context")

    evidence_valid = input_trusted and policy_trusted and not receipt_errors
    findings: list[dict[str, Any]] = []
    history_observations: list[str] = []
    out_of_scope_observation_count = 0
    if not evidence_valid:
        for requirement in requirements:
            findings.append(
                finding(
                    "DQ_EVIDENCE_INCOMPLETE",
                    requirement["requirement_key_sha256"],
                    "Required trusted collector evidence is incomplete or invalid.",
                    "Recollect every required surface and verify both independent trusted digests.",
                    quality="INCONCLUSIVE",
                    monitoring="INCONCLUSIVE",
                )
            )
    else:
        by_surface = {surface: [r for r in valid_receipts if r["surface"] == surface] for surface in RECEIPT_CONTRACTS}
        history_receipt = by_surface["data-quality"][0]
        history = history_receipt["datasets"]["expectation_history"]
        governed_history_keys = {
            (
                row["object_key_sha256"],
                row["association_key_sha256"],
                row["metric_key_sha256"],
                row["expectation_key_sha256"],
                row["definition_sha256"],
            )
            for row in requirements
        }
        out_of_scope_observation_count = sum(
            (
                row["object_key_sha256"],
                row["association_key_sha256"],
                row["metric_key_sha256"],
                row["expectation_key_sha256"],
                row["definition_sha256"],
            )
            not in governed_history_keys
            for row in history
        )
        associations = [
            row
            for receipt in selected_receipts["data-quality-associations-current"]
            for row in receipt["datasets"]["current_associations"]
        ]
        expectations = [
            row
            for receipt in selected_receipts["data-quality-expectations-current"]
            for row in receipt["datasets"]["current_expectations"]
        ]
        notification_receipts = selected_receipts["data-quality-notification-current"]
        notifications = [
            row for receipt in notification_receipts for row in receipt["datasets"]["notification_associations"]
        ]
        association_by_key = {
            (row["object_key_sha256"], row["association_key_sha256"], row["metric_key_sha256"]): row
            for row in associations
        }
        expectation_by_key = {
            (
                row["object_key_sha256"],
                row["association_key_sha256"],
                row["metric_key_sha256"],
                row["expectation_key_sha256"],
            ): row
            for row in expectations
        }
        notification_by_key = {
            (row["object_key_sha256"], row["association_key_sha256"], row["metric_key_sha256"]): row
            for row in notifications
        }

        for requirement in requirements:
            scope = requirement["requirement_key_sha256"]
            expected_identity = (
                requirement["object_key_sha256"],
                requirement["association_key_sha256"],
                requirement["metric_key_sha256"],
            )
            association = association_by_key.get(expected_identity)
            if association is None:
                findings.append(
                    finding(
                        "DQ_ASSOCIATION_MISSING",
                        scope,
                        "The governed association is absent from current evidence.",
                        "Restore the governed association and recollect.",
                        quality="INCONCLUSIVE",
                        monitoring="FAIL",
                    )
                )
            else:
                observed_identity = (
                    association["object_key_sha256"],
                    association["association_key_sha256"],
                    association["metric_key_sha256"],
                )
                if observed_identity != expected_identity:
                    findings.append(
                        finding(
                            "DQ_ASSOCIATION_IDENTITY_DRIFT",
                            scope,
                            "The current association does not match the governed identity.",
                            "Reconcile the association against approved policy.",
                            quality="INCONCLUSIVE",
                            monitoring="FAIL",
                        )
                    )
                if association["schedule_sha256"] != requirement["schedule_sha256"]:
                    findings.append(
                        finding(
                            "DQ_SCHEDULE_DRIFT",
                            scope,
                            "The current schedule fingerprint differs from policy.",
                            "Restore the approved schedule.",
                            quality="INCONCLUSIVE",
                            monitoring="FAIL",
                        )
                    )
                if association["schedule_status"] == "STARTED_AND_PENDING_SCHEDULE_UPDATE":
                    findings.append(
                        finding(
                            "DQ_SCHEDULE_UPDATE_PENDING",
                            scope,
                            "The governed association is running with a schedule update still pending.",
                            "Wait for Snowflake to apply the approved schedule update, then recollect.",
                            quality="INCONCLUSIVE",
                            monitoring="INCONCLUSIVE",
                        )
                    )
                elif association["schedule_status"] == "PROVIDER_OTHER":
                    findings.append(
                        finding(
                            "DQ_SCHEDULE_STATE_UNREVIEWED",
                            scope,
                            "The provider returned an unrecognized schedule state.",
                            "Review the provider state before relying on this association.",
                            quality="INCONCLUSIVE",
                            monitoring="FAIL",
                        )
                    )
                elif association["schedule_status"] != "STARTED":
                    findings.append(
                        finding(
                            "DQ_ASSOCIATION_SUSPENDED",
                            scope,
                            "The governed association is not started.",
                            "Resume the association after approval.",
                            quality="INCONCLUSIVE",
                            monitoring="FAIL",
                        )
                    )
                if association["association_level"] == "PROVIDER_OTHER":
                    findings.append(
                        finding(
                            "DQ_ASSOCIATION_LEVEL_UNREVIEWED",
                            scope,
                            "The provider returned an unrecognized association level.",
                            "Review the association scope before relying on this evidence.",
                            quality="INCONCLUSIVE",
                            monitoring="FAIL",
                        )
                    )
                if association["execution_role_sha256"] != requirement["expected_execution_role_sha256"]:
                    findings.append(
                        finding(
                            "DQ_EXECUTION_ROLE_DRIFT",
                            scope,
                            "The execution-role fingerprint differs from policy.",
                            "Restore the approved execution role.",
                            quality="INCONCLUSIVE",
                            monitoring="FAIL",
                        )
                    )
                if association["group_definition_sha256"] != requirement["group_definition_sha256"]:
                    findings.append(
                        finding(
                            "DQ_GROUP_DEFINITION_DRIFT",
                            scope,
                            "The group-definition fingerprint differs from policy.",
                            "Restore the approved grouping definition.",
                            quality="INCONCLUSIVE",
                            monitoring="FAIL",
                        )
                    )
                if association["object_domain"] != requirement["object_domain"]:
                    findings.append(
                        finding(
                            "DQ_OBJECT_DOMAIN_DRIFT",
                            scope,
                            "The current object domain differs from policy.",
                            "Restore the approved object domain.",
                            quality="INCONCLUSIVE",
                            monitoring="FAIL",
                        )
                    )
                if association["filter_sha256"] != requirement["filter_sha256"]:
                    findings.append(
                        finding(
                            "DQ_FILTER_DRIFT",
                            scope,
                            "The current filter fingerprint differs from policy.",
                            "Restore the approved filter.",
                            quality="INCONCLUSIVE",
                            monitoring="FAIL",
                        )
                    )
                if association["group_limit"] != requirement["expected_group_limit"]:
                    findings.append(
                        finding(
                            "DQ_GROUP_LIMIT_DRIFT",
                            scope,
                            "The current group limit differs from policy.",
                            "Restore the approved group limit.",
                            quality="INCONCLUSIVE",
                            monitoring="FAIL",
                        )
                    )

            expectation = expectation_by_key.get(
                (
                    requirement["object_key_sha256"],
                    requirement["association_key_sha256"],
                    requirement["metric_key_sha256"],
                    requirement["expectation_key_sha256"],
                )
            )
            if expectation is None:
                findings.append(
                    finding(
                        "DQ_EXPECTATION_MISSING",
                        scope,
                        "The governed expectation is absent from current evidence.",
                        "Restore the approved expectation and recollect.",
                        quality="INCONCLUSIVE",
                        monitoring="FAIL",
                    )
                )
            elif (
                expectation["object_key_sha256"] != requirement["object_key_sha256"]
                or expectation["metric_key_sha256"] != requirement["metric_key_sha256"]
                or expectation["definition_sha256"] != requirement["definition_sha256"]
            ):
                findings.append(
                    finding(
                        "DQ_DEFINITION_DRIFT",
                        scope,
                        "The current expectation definition differs from policy.",
                        "Reconcile the expectation definition before classifying results.",
                        quality="INCONCLUSIVE",
                        monitoring="FAIL",
                    )
                )

            if requirement["schedule_mode"] == "TRIGGER_ON_CHANGES":
                findings.append(
                    finding(
                        "DQ_TRIGGER_FRESHNESS_UNPROVEN",
                        scope,
                        "Trigger-on-change freshness cannot be proven from these surfaces.",
                        "Provide a separately reviewed trigger-change evidence surface.",
                        quality="INCONCLUSIVE",
                        monitoring="INCONCLUSIVE",
                    )
                )
            if requirement["group_definition_sha256"] is not None:
                findings.append(
                    finding(
                        "DQ_GROUP_EVIDENCE_UNAVAILABLE",
                        scope,
                        "Grouped-result completeness is not proven by the reviewed result projection.",
                        "Provide separately trusted group-result evidence.",
                        quality="INCONCLUSIVE",
                        monitoring="INCONCLUSIVE",
                    )
                )
            if requirement["objective_mode"] == "ANOMALY":
                findings.append(
                    finding(
                        "DQ_ANOMALY_EVIDENCE_UNAVAILABLE",
                        scope,
                        "Anomaly classification is not present in the reviewed expectation surface.",
                        "Collect a separately reviewed trusted anomaly surface.",
                        quality="INCONCLUSIVE",
                        monitoring="INCONCLUSIVE",
                    )
                )
            else:
                matching_results = [
                    row
                    for row in history
                    if (
                        row["object_key_sha256"],
                        row["association_key_sha256"],
                        row["metric_key_sha256"],
                        row["expectation_key_sha256"],
                        row["definition_sha256"],
                    )
                    == (
                        requirement["object_key_sha256"],
                        requirement["association_key_sha256"],
                        requirement["metric_key_sha256"],
                        requirement["expectation_key_sha256"],
                        requirement["definition_sha256"],
                    )
                ]
                mismatched_definition = any(
                    row["object_key_sha256"] == requirement["object_key_sha256"]
                    and row["association_key_sha256"] == requirement["association_key_sha256"]
                    and row["metric_key_sha256"] == requirement["metric_key_sha256"]
                    and row["expectation_key_sha256"] == requirement["expectation_key_sha256"]
                    and row["definition_sha256"] != requirement["definition_sha256"]
                    for row in history
                )
                if mismatched_definition:
                    findings.append(
                        finding(
                            "DQ_RESULT_DEFINITION_MISMATCH",
                            scope,
                            "Observed result history is bound to a different definition fingerprint.",
                            "Obtain a result for the exact current governed definition.",
                            quality="INCONCLUSIVE",
                            monitoring="INCONCLUSIVE",
                        )
                    )
                if not matching_results:
                    findings.append(
                        finding(
                            "DQ_NO_EVALUATION",
                            scope,
                            "No matching governed expectation evaluation was observed.",
                            "Run or await a governed evaluation and recollect.",
                            quality="INCONCLUSIVE",
                            monitoring="INCONCLUSIVE",
                        )
                    )
                else:
                    latest = max(
                        matching_results,
                        key=lambda row: (
                            parse_time(row["measurement_time"]) or datetime.min.replace(tzinfo=timezone.utc)
                        ),
                    )
                    measured = parse_time(latest["measurement_time"])
                    if (
                        measured is None
                        or measured > evaluated
                        or evaluated - measured > timedelta(seconds=requirement["max_result_age_seconds"])
                    ):
                        findings.append(
                            finding(
                                "DQ_RESULT_STALE",
                                scope,
                                "The newest matching evaluation is outside the governed freshness bound.",
                                "Obtain a fresh evaluation before classification.",
                                quality="INCONCLUSIVE",
                                monitoring="INCONCLUSIVE",
                            )
                        )
                    elif latest["expectation_violated"] is None:
                        history_observations.append("EVALUATION_FAILED_OBSERVED")
                        findings.append(
                            finding(
                                "DQ_EXPECTATION_EVALUATION_FAILED",
                                scope,
                                "The evaluation did not produce a Boolean expectation result.",
                                "Fix evaluation execution and recollect.",
                                quality="INCONCLUSIVE",
                                monitoring="DEGRADED",
                            )
                        )
                    elif latest["expectation_violated"] is True:
                        history_observations.append("VIOLATION_OBSERVED")
                        findings.append(
                            finding(
                                "DQ_EXPECTATION_VIOLATED",
                                scope,
                                "The newest exact governed expectation result is violated.",
                                "Investigate through the governed data-owner workflow without collecting raw rows.",
                                quality="FAIL",
                            )
                        )
                    else:
                        history_observations.append("SATISFIED_OBSERVATION")

            if requirement["notification_required"]:
                notification = notification_by_key.get(expected_identity)
                if notification is None:
                    findings.append(
                        finding(
                            "DQ_NOTIFICATION_VISIBILITY_GAP",
                            scope,
                            "Current notification configuration is not visible for the governed association.",
                            "Restore least-privilege visibility and recollect.",
                            monitoring="INCONCLUSIVE",
                        )
                    )
                elif (
                    notification["object_key_sha256"],
                    notification["association_key_sha256"],
                    notification["metric_key_sha256"],
                ) != expected_identity:
                    findings.append(
                        finding(
                            "DQ_NOTIFICATION_IDENTITY_DRIFT",
                            scope,
                            "Notification configuration is bound to a different association identity.",
                            "Reconcile notification configuration with policy.",
                            monitoring="FAIL",
                        )
                    )
                elif notification["notification_status"] == "DISABLED":
                    findings.append(
                        finding(
                            "DQ_NOTIFICATION_DISABLED",
                            scope,
                            "Required notification configuration is disabled.",
                            "Enable the approved notification configuration.",
                            monitoring="FAIL",
                        )
                    )
                elif notification["notification_status"] == "ERROR_INSUFFICIENT_PRIVILEGE":
                    findings.append(
                        finding(
                            "DQ_NOTIFICATION_PRIVILEGE_ERROR",
                            scope,
                            "Notification configuration reports insufficient privilege.",
                            "Restore least-privilege notification execution rights.",
                            monitoring="FAIL",
                        )
                    )
                elif notification["notification_status"] == "NOT_CONFIGURED":
                    findings.append(
                        finding(
                            "DQ_NOTIFICATION_NOT_CONFIGURED",
                            scope,
                            "Required notification configuration is not configured.",
                            "Configure the approved notification integration.",
                            monitoring="FAIL",
                        )
                    )
                elif notification["notification_status"] == "PROVIDER_OTHER":
                    findings.append(
                        finding(
                            "DQ_NOTIFICATION_STATE_UNREVIEWED",
                            scope,
                            "Notification configuration is outside the reviewed state domain.",
                            "Review the provider state before classifying notification readiness.",
                            monitoring="INCONCLUSIVE",
                        )
                    )

    def configuration_status() -> str:
        if not requirements:
            return "INCONCLUSIVE"
        impacts = [item["monitoring_impact"] for item in findings if item["monitoring_impact"] is not None]
        if "FAIL" in impacts:
            return "FAIL"
        if "INCONCLUSIVE" in impacts or "DEGRADED" in impacts:
            return "INCONCLUSIVE"
        return "PASS"

    if "VIOLATION_OBSERVED" in history_observations:
        history_observation_status = "VIOLATION_OBSERVED"
    elif "EVALUATION_FAILED_OBSERVED" in history_observations:
        history_observation_status = "EVALUATION_FAILED_OBSERVED"
    elif "SATISFIED_OBSERVATION" in history_observations:
        history_observation_status = "SATISFIED_OBSERVATION"
    else:
        history_observation_status = "NOT_OBSERVED"

    quality_status = "FAIL" if history_observation_status == "VIOLATION_OBSERVED" else "INCONCLUSIVE"

    report = {
        "schema_version": "2",
        "analyzer": {"name": "snowflake-data-quality-sentinel", "version": VERSION},
        "quality_status": quality_status,
        "configuration_status": configuration_status(),
        "history_observation_status": history_observation_status,
        "history_completeness_status": "UNPROVEN_NO_PROVIDER_SLA",
        "pass_supported": False,
        "settled_through_utc": None,
        "structural_evidence_valid": evidence_valid,
        "evidence_integrity_status": "VALID" if evidence_valid else "INVALID",
        "governed_coverage_status": (
            "INCOMPLETE"
            if {
                "duplicate_object_selector",
                "governed_object_coverage",
                "required_surface_count",
            }.intersection(receipt_errors)
            else "COMPLETE"
        ),
        "evidence_complete": False,
        "out_of_scope_observation_count": out_of_scope_observation_count,
        "denominator": {
            "expected_requirements": len(requirements),
            "evaluated_requirements": len(requirements) if evidence_valid else 0,
        },
        "findings": sorted(findings, key=lambda item: (item["code"], item["scope"])),
        "notification_delivery_status": "NOT_OBSERVED",
        "provenance": {
            "evaluated_at": evaluated.isoformat().replace("+00:00", "Z"),
            "input_sha256": input_digest,
            "policy_sha256": policy_digest,
            "trusted_input": input_trusted,
            "trusted_policy": policy_trusted,
            "history_assumption_status": data["policy"]["history_assumption_status"],
            "history_assumption_delay_seconds": data["policy"]["history_assumption_delay_seconds"],
            "receipt_sha256s": sorted(receipt["receipt_sha256"] for receipt in valid_receipts),
        },
        "evidence_gap_codes": sorted(
            set(receipt_errors + ([] if input_trusted and policy_trusted else ["external_trust_mismatch"]))
        ),
        "non_claims": [
            "No Snowflake mutation was executed.",
            "Notification configuration does not prove notification delivery; delivery remains NOT_OBSERVED.",
            "Missing, stale, truncated, invalid, mixed-context, or untrusted evidence cannot prove health.",
            "Anomaly and grouped-result health require separately reviewed trusted evidence.",
            "Snowflake publishes no finality SLA for this history surface.",
            "A satisfied observation is not a present-tense quality PASS.",
            "The owner-declared history delay is an assumption, not a provider guarantee.",
        ],
    }
    report["report_sha256"] = digest(report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", help="schema-2 evidence JSON; omit to read stdin")
    parser.add_argument("--evaluated-at")
    parser.add_argument("--trusted-input-sha256")
    parser.add_argument("--trusted-policy-sha256")
    parser.add_argument("--policy-file", help="separately owner-approved policy JSON")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--print-input-sha256", action="store_true")
    modes.add_argument("--print-policy-sha256", action="store_true")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.print_policy_sha256:
            if not args.policy_file:
                raise EvidenceError("missing policy file")
            policy = json.loads(Path(args.policy_file).read_text(encoding="utf-8"))
            print(canonical_policy_document_digest(policy))
            return 0
        raw = Path(args.input).read_text(encoding="utf-8") if args.input else sys.stdin.read()
        data = json.loads(raw)
        if args.print_input_sha256:
            print(canonical_input_digest(data))
            return 0
        if (
            not args.evaluated_at
            or not args.trusted_input_sha256
            or not args.trusted_policy_sha256
            or not args.policy_file
        ):
            raise EvidenceError("missing trust arguments")
        policy = json.loads(Path(args.policy_file).read_text(encoding="utf-8"))
        validate_policy(policy)
        if data.get("policy") != policy:
            raise EvidenceError("invalid policy")
        report = analyze(
            data,
            evaluated_at=args.evaluated_at,
            trusted_input_sha256=args.trusted_input_sha256,
            trusted_policy_sha256=args.trusted_policy_sha256,
        )
    except (OSError, json.JSONDecodeError, EvidenceError, TypeError, ValueError):
        print("error: evidence input is invalid", file=sys.stderr)
        return 2
    json.dump(report, sys.stdout, sort_keys=True, indent=2 if args.pretty else None, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
