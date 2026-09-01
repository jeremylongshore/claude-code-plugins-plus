#!/usr/bin/env python3
"""Deterministically assess normalized Snowflake data-quality evidence.

The analyzer is connector- and model-neutral. It consumes metadata only, never
connects to Snowflake, and treats findings as data rather than process failures.
Exit code 2 is reserved for invalid or unsafe input.
"""

from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "1.1.0"
STATUS_ORDER = {
    "FAIL": 0,
    "DEGRADED": 1,
    "INCONCLUSIVE": 2,
    "PASS": 3,
    "NO_REQUIRED_CHECKS": 4,
}
SUPPORTED_OBJECT_TYPES = {"TABLE", "VIEW"}
TOP_LEVEL_KEYS = {
    "metadata",
    "requirements",
    "associations",
    "measurements",
    "source_metadata",
    "current_state",
    "current_state_receipt",
}
REQUIRED_TOP_LEVEL_KEYS = TOP_LEVEL_KEYS - {"current_state", "current_state_receipt"}
PROHIBITED_KEY_FRAGMENTS = (
    "password",
    "passphrase",
    "privatekey",
    "secret",
    "token",
    "apikey",
    "authorization",
    "credential",
    "querytext",
    "sqltext",
    "sqlstatement",
    "presignedurl",
    "rawfailedrow",
    "failedrow",
    "rejectedrow",
    "rawpayload",
    "rawgroup",
    "groupvalues",
    "groupbyvalues",
    "withingroup",
    "filter",
    "endpoint",
    "rowdata",
    "firstname",
    "lastname",
    "email",
    "phone",
    "socialsecurity",
    "dateofbirth",
    "clientip",
    "ipaddress",
)
EMAIL_RE = re.compile(r"(?i)(?<![\w.+-])[\w.+-]+@[a-z0-9.-]+\.[a-z]{2,}(?![\w.-])")
SSN_RE = re.compile(r"(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)")
BEARER_RE = re.compile(r"(?i)\bbearer\s+[a-z0-9._~+/=-]{8,}")
PRIVATE_KEY_RE = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")
SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9_$.-]{1,255}$")
CURRENT_RECEIPT_SOURCE = "SNOWFLAKE.ACCOUNT_USAGE.DATA_METRIC_FUNCTION_REFERENCES"
CURRENT_RECEIPT_DATASET = "data_quality_current"
CURRENT_RECEIPT_TEMPLATE = "data-quality-current.sql"
CURRENT_RECEIPT_KEYS = {
    "schema_version",
    "surface",
    "status",
    "collected_at",
    "connection_profile",
    "sql_sha256",
    "template_sha256",
    "rendered_sql_sha256",
    "selector_fingerprint",
    "source_metadata",
    "source_views",
    "row_count",
    "row_limit",
    "truncation_possible",
    "dataset_row_limits",
    "dataset_truncation_possible",
    "datasets",
    "errors",
    "non_claims",
    "receipt_sha256",
}
CURRENT_RECEIPT_ROW_KEYS = {
    "metric_database_name",
    "metric_schema_name",
    "metric_name",
    "ref_database_name",
    "ref_schema_name",
    "ref_entity_name",
    "ref_entity_domain",
    "reference_id",
    "schedule",
    "schedule_status",
    "notification_status",
    "anomaly_detection_status",
    "execution_role",
}
CURRENT_RECEIPT_NON_CLAIMS = [
    "No Snowflake mutation was executed.",
    "Missing rows or permission-blocked views do not prove health.",
    "Account Usage evidence can lag and must not be treated as real-time state.",
    "The selected domain skill must evaluate freshness and completeness.",
    "A row count at the reviewed SQL limit may indicate truncated evidence.",
]


class EvidenceError(ValueError):
    """Raised when evidence cannot be assessed safely."""


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _normalized_key(value: object) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value).casefold())


def _looks_like_ip(value: str) -> bool:
    try:
        ipaddress.ip_address(value.strip())
    except ValueError:
        return False
    return True


def reject_sensitive_data(value: Any, path: str = "input") -> None:
    """Reject secrets, PII, SQL text, row payloads, and signed URLs."""
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = _normalized_key(key)
            if any(fragment in normalized for fragment in PROHIBITED_KEY_FRAGMENTS):
                raise EvidenceError(f"prohibited field is not accepted: {path}.{key}")
            reject_sensitive_data(child, f"{path}.{key}")
        return
    if isinstance(value, list):
        for index, child in enumerate(value):
            reject_sensitive_data(child, f"{path}[{index}]")
        return
    if not isinstance(value, str):
        return
    if len(value) > 4096:
        raise EvidenceError(f"string exceeds 4096 characters: {path}")
    if EMAIL_RE.search(value) or SSN_RE.search(value) or _looks_like_ip(value):
        raise EvidenceError(f"PII-like value is not accepted: {path}")
    if BEARER_RE.search(value) or PRIVATE_KEY_RE.search(value):
        raise EvidenceError(f"credential-like value is not accepted: {path}")
    stripped = value.strip()
    lowered = stripped.casefold()
    if lowered.startswith(("http://", "https://")):
        if (
            re.search(r"://[^/@\s]+@", stripped)
            or "?" in stripped
            or "#" in stripped
            or any(
                marker in value.casefold() for marker in ("x-amz-signature", "x-goog-signature", "sig=", "signature=")
            )
        ):
            raise EvidenceError(f"presigned or credential-bearing URL is not accepted: {path}")


def parse_time(value: Any, path: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise EvidenceError(f"{path} must be an ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise EvidenceError(f"{path} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise EvidenceError(f"{path} must include a timezone")
    return parsed.astimezone(timezone.utc)


def text(value: Any, path: str, *, required: bool = True) -> str:
    if value is None and not required:
        return ""
    if not isinstance(value, str) or (required and not value.strip()):
        raise EvidenceError(f"{path} must be a non-empty string")
    result = value.strip()
    if len(result) > 255 or "\n" in result or "\r" in result:
        raise EvidenceError(f"{path} contains unsafe text")
    return result


def identifier(value: Any, path: str) -> str:
    result = text(value, path)
    if not IDENTIFIER_RE.fullmatch(result):
        raise EvidenceError(f"{path} must be a bounded Snowflake identifier")
    return result.upper()


def boolean(value: Any, path: str, *, default: bool | None = None) -> bool | None:
    if value is None and default is not None:
        return default
    if value is None:
        return None
    if type(value) is not bool:
        raise EvidenceError(f"{path} must be a boolean or null")
    return value


def positive_integer(value: Any, path: str, *, default: int | None = None) -> int:
    if value is None and default is not None:
        return default
    if type(value) is not int or value <= 0 or value > 31_536_000:
        raise EvidenceError(f"{path} must be an integer from 1 to 31536000")
    return value


def string_list(value: Any, path: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise EvidenceError(f"{path} must be an array of strings")
    result = [text(item, f"{path}[]").upper() for item in value]
    if len(result) > 500:
        raise EvidenceError(f"{path} exceeds 500 entries")
    return sorted(set(result))


def object_identity(value: Any, path: str) -> dict[str, str]:
    if not isinstance(value, dict):
        raise EvidenceError(f"{path} must be an object")
    required = {"database", "schema", "name", "type"}
    if set(value) != required:
        raise EvidenceError(f"{path} must contain exactly {sorted(required)}")
    return {
        "database": identifier(value["database"], f"{path}.database"),
        "schema": identifier(value["schema"], f"{path}.schema"),
        "name": identifier(value["name"], f"{path}.name"),
        "type": identifier(value["type"], f"{path}.type"),
    }


def metric_identity(value: Any, path: str) -> dict[str, str]:
    if not isinstance(value, dict):
        raise EvidenceError(f"{path} must be an object")
    required = {"database", "schema", "name"}
    if set(value) != required:
        raise EvidenceError(f"{path} must contain exactly {sorted(required)}")
    return {key: identifier(value[key], f"{path}.{key}") for key in sorted(required)}


def _reviewed_current_sql() -> tuple[str, int]:
    path = Path(__file__).resolve().parent / "sql" / CURRENT_RECEIPT_TEMPLATE
    try:
        sql = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise EvidenceError("bundled data-quality-current SQL is unavailable") from exc
    limits = re.findall(r"\bLIMIT\s+(\d+)\b", sql, flags=re.IGNORECASE)
    if len(limits) != 1:
        raise EvidenceError("bundled data-quality-current SQL must declare exactly one row cap")
    return f"sha256:{hashlib.sha256(sql.encode('utf-8')).hexdigest()}", int(limits[0])


def validate_current_state_receipt(
    value: Any,
    *,
    envelope_collected_at: datetime,
    current_observed_at: datetime | None,
    requirements: list[dict[str, Any]],
    current_associations: list[dict[str, str]],
    current_notifications: list[dict[str, Any]],
) -> dict[str, Any]:
    """Verify an exact data-quality-current collector receipt and row binding."""

    if value is None:
        return {
            "status": "not_supplied",
            "complete": False,
            "issues": ["current_state_receipt not supplied"],
            "receipt_sha256": None,
        }
    if not isinstance(value, dict):
        return {
            "status": "unverifiable",
            "complete": False,
            "issues": ["current_state_receipt is not an object"],
            "receipt_sha256": None,
        }

    issues: list[str] = []
    if set(value) != CURRENT_RECEIPT_KEYS:
        issues.append(f"receipt keys must be exactly {sorted(CURRENT_RECEIPT_KEYS)}")
    if value.get("schema_version") != "1":
        issues.append("schema_version is not 1")
    if value.get("surface") != "data-quality-current":
        issues.append("surface is not data-quality-current")
    if value.get("status") != "collected":
        issues.append("status is not collected")
    if value.get("errors") != []:
        issues.append("errors is not an empty array")
    profile = value.get("connection_profile")
    if not isinstance(profile, str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", profile):
        issues.append("connection_profile is invalid")

    receipt_time: datetime | None = None
    try:
        receipt_time = parse_time(value.get("collected_at"), "current_state_receipt.collected_at")
        if receipt_time > envelope_collected_at or receipt_time > datetime.now(timezone.utc):
            issues.append("collected_at is after the evidence envelope or in the future")
        if current_observed_at is None or receipt_time != current_observed_at:
            issues.append("collected_at does not exactly match current_state.observed_at")
    except EvidenceError:
        issues.append("collected_at is invalid")

    expected_hash, expected_limit = _reviewed_current_sql()
    for field in ("sql_sha256", "template_sha256", "rendered_sql_sha256"):
        if value.get(field) != expected_hash:
            issues.append(f"{field} does not match the bundled data-quality-current SQL")
    if value.get("selector_fingerprint") is not None:
        issues.append("selector_fingerprint is unexpected")
    expected_views = [CURRENT_RECEIPT_SOURCE]
    if value.get("source_views") != expected_views:
        issues.append("source_views do not match the reviewed current-state SQL")
    expected_source_metadata = {
        "template": CURRENT_RECEIPT_TEMPLATE,
        "source_views": expected_views,
        "selector": {},
    }
    if value.get("source_metadata") != expected_source_metadata:
        issues.append("source_metadata does not exactly describe the bundled current-state SQL")

    datasets = value.get("datasets")
    if not isinstance(datasets, dict) or set(datasets) != {CURRENT_RECEIPT_DATASET}:
        issues.append(f"datasets must contain exactly {CURRENT_RECEIPT_DATASET}")
        receipt_rows: Any = []
    else:
        receipt_rows = datasets[CURRENT_RECEIPT_DATASET]
    if not isinstance(receipt_rows, list) or any(not isinstance(row, dict) for row in receipt_rows):
        issues.append(f"datasets.{CURRENT_RECEIPT_DATASET} must be an array of objects")
        receipt_rows = []

    normalized_receipt_rows: list[dict[str, str]] = []
    seen_reference_ids: set[str] = set()
    for index, row in enumerate(receipt_rows):
        path = f"current_state_receipt.datasets.{CURRENT_RECEIPT_DATASET}[{index}]"
        if set(row) != CURRENT_RECEIPT_ROW_KEYS:
            issues.append(f"{path} keys do not match the reviewed SQL projection")
            continue
        try:
            normalized_row = {
                "metric_database_name": identifier(row["metric_database_name"], f"{path}.metric_database_name"),
                "metric_schema_name": identifier(row["metric_schema_name"], f"{path}.metric_schema_name"),
                "metric_name": identifier(row["metric_name"], f"{path}.metric_name"),
                "ref_database_name": identifier(row["ref_database_name"], f"{path}.ref_database_name"),
                "ref_schema_name": identifier(row["ref_schema_name"], f"{path}.ref_schema_name"),
                "ref_entity_name": identifier(row["ref_entity_name"], f"{path}.ref_entity_name"),
                "ref_entity_domain": identifier(row["ref_entity_domain"], f"{path}.ref_entity_domain"),
                "reference_id": text(row["reference_id"], f"{path}.reference_id"),
                "schedule": text(row["schedule"], f"{path}.schedule").upper(),
                "schedule_status": text(row["schedule_status"], f"{path}.schedule_status").upper(),
                "notification_status": text(row["notification_status"], f"{path}.notification_status").upper(),
                "anomaly_detection_status": text(
                    row["anomaly_detection_status"], f"{path}.anomaly_detection_status"
                ).upper(),
                "execution_role": text(row["execution_role"], f"{path}.execution_role").upper(),
            }
        except EvidenceError as exc:
            issues.append(str(exc))
            continue
        if normalized_row["reference_id"] in seen_reference_ids:
            issues.append(f"duplicate receipt reference_id: {normalized_row['reference_id']}")
        seen_reference_ids.add(normalized_row["reference_id"])
        normalized_receipt_rows.append(normalized_row)

    row_count = value.get("row_count")
    if type(row_count) is not int or row_count < 0:
        issues.append("row_count is invalid")
    elif row_count != len(receipt_rows):
        issues.append("row_count does not match the current-state dataset")
    if value.get("row_limit") != expected_limit:
        issues.append(f"row_limit is not the reviewed SQL cap of {expected_limit}")
    if type(row_count) is int and row_count >= expected_limit:
        issues.append("row_count is at or above the reviewed SQL cap")
    if value.get("truncation_possible") is not False:
        issues.append("truncation_possible is not false")
    if value.get("dataset_row_limits") != {CURRENT_RECEIPT_DATASET: expected_limit}:
        issues.append("dataset_row_limits does not match the reviewed SQL cap")
    if value.get("dataset_truncation_possible") != {CURRENT_RECEIPT_DATASET: False}:
        issues.append("dataset_truncation_possible is not exactly false for data_quality_current")
    if value.get("non_claims") != CURRENT_RECEIPT_NON_CLAIMS:
        issues.append("non_claims do not match the collector contract")

    body = dict(value)
    supplied_receipt_hash = body.pop("receipt_sha256", None)
    expected_receipt_hash = f"sha256:{hashlib.sha256(canonical_json(body)).hexdigest()}"
    if supplied_receipt_hash != expected_receipt_hash:
        issues.append("receipt_sha256 is missing or invalid")

    requirements_by_id = {row["id"]: row for row in requirements}
    receipt_by_reference = {row["reference_id"]: row for row in normalized_receipt_rows}
    association_by_requirement = {row["requirement_id"]: row for row in current_associations}
    for association in current_associations:
        requirement_id = association["requirement_id"]
        requirement = requirements_by_id.get(requirement_id)
        row = receipt_by_reference.get(association["reference_id"])
        if requirement is None:
            issues.append(f"current association {requirement_id} is outside the requirement denominator")
            continue
        if row is None:
            issues.append(f"current association {requirement_id} has no matching receipt row")
            continue
        expected_projection = {
            "metric_database_name": requirement["metric"]["database"],
            "metric_schema_name": requirement["metric"]["schema"],
            "metric_name": requirement["metric"]["name"],
            "ref_database_name": requirement["object"]["database"],
            "ref_schema_name": requirement["object"]["schema"],
            "ref_entity_name": requirement["object"]["name"],
            "ref_entity_domain": requirement["object"]["type"],
            "schedule_status": association["schedule_status"],
            "notification_status": association["notification_status"],
            "execution_role": association["execution_role"],
        }
        for field, expected in expected_projection.items():
            if row[field] != expected:
                issues.append(f"current association {requirement_id} does not match receipt field {field}")

    for notification in current_notifications:
        association = association_by_requirement.get(notification["requirement_id"])
        row = receipt_by_reference.get(association["reference_id"]) if association else None
        if row is None or row["notification_status"] != notification["status"]:
            issues.append(
                f"current notification {notification['requirement_id']} does not match a receipt association row"
            )

    unique_issues = sorted(set(issues))
    return {
        "status": "verified" if not unique_issues else "unverifiable",
        "complete": not unique_issues,
        "issues": unique_issues,
        "receipt_sha256": supplied_receipt_hash if isinstance(supplied_receipt_hash, str) else None,
        "collected_at": receipt_time.isoformat().replace("+00:00", "Z") if receipt_time else None,
        "row_count": row_count,
        "row_limit": value.get("row_limit"),
    }


def normalize_document(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise EvidenceError("input must be an object")
    reject_sensitive_data(data)
    unknown = set(data) - TOP_LEVEL_KEYS
    missing = REQUIRED_TOP_LEVEL_KEYS - set(data)
    if unknown or missing:
        raise EvidenceError(f"top-level keys must be exactly {sorted(TOP_LEVEL_KEYS)}")

    metadata = data["metadata"]
    if not isinstance(metadata, dict):
        raise EvidenceError("metadata must be an object")
    expected_metadata = {
        "schema_version",
        "surface",
        "collected_at",
        "window_start",
        "window_end",
        "collector_receipt_sha256",
    }
    if set(metadata) != expected_metadata:
        raise EvidenceError(f"metadata keys must be exactly {sorted(expected_metadata)}")
    collected_at = parse_time(metadata["collected_at"], "metadata.collected_at")
    window_start = parse_time(metadata["window_start"], "metadata.window_start")
    window_end = parse_time(metadata["window_end"], "metadata.window_end")
    if collected_at > datetime.now(timezone.utc):
        raise EvidenceError("metadata.collected_at cannot be in the future")
    if window_start >= window_end or window_end > collected_at:
        raise EvidenceError("metadata window must end after start and not after collected_at")
    receipt_hash = text(metadata["collector_receipt_sha256"], "metadata.collector_receipt_sha256")
    if not SHA256_RE.fullmatch(receipt_hash):
        raise EvidenceError("metadata.collector_receipt_sha256 must be sha256:<64 lowercase hex>")
    normalized_metadata = {
        "schema_version": text(metadata["schema_version"], "metadata.schema_version"),
        "surface": text(metadata["surface"], "metadata.surface"),
        "collected_at": collected_at.isoformat().replace("+00:00", "Z"),
        "window_start": window_start.isoformat().replace("+00:00", "Z"),
        "window_end": window_end.isoformat().replace("+00:00", "Z"),
        "collector_receipt_sha256": receipt_hash,
    }
    if normalized_metadata["surface"] != "data-quality":
        raise EvidenceError("metadata.surface must be data-quality")

    requirements = data["requirements"]
    associations = data["associations"]
    measurements = data["measurements"]
    sources = data["source_metadata"]
    for name, rows in (
        ("requirements", requirements),
        ("associations", associations),
        ("measurements", measurements),
        ("source_metadata", sources),
    ):
        if not isinstance(rows, list) or len(rows) > 10_000:
            raise EvidenceError(f"{name} must be an array with at most 10000 entries")
        if any(not isinstance(row, dict) for row in rows):
            raise EvidenceError(f"{name} entries must be objects")

    normalized_requirements: list[dict[str, Any]] = []
    seen_requirement_ids: set[str] = set()
    requirement_keys = {
        "id",
        "object",
        "metric",
        "objective",
        "max_result_age_seconds",
        "expected_schedule",
        "notification_required",
        "expected_execution_role",
        "required_groups",
    }
    for index, row in enumerate(requirements):
        if set(row) != requirement_keys:
            raise EvidenceError(f"requirements[{index}] keys must be exactly {sorted(requirement_keys)}")
        requirement_id = text(row["id"], f"requirements[{index}].id")
        if requirement_id in seen_requirement_ids:
            raise EvidenceError(f"duplicate requirement id: {requirement_id}")
        seen_requirement_ids.add(requirement_id)
        objective = row["objective"]
        if objective is not None:
            if not isinstance(objective, dict) or set(objective) != {"mode", "name"}:
                raise EvidenceError(f"requirements[{index}].objective must be null or mode/name")
            mode = text(objective["mode"], f"requirements[{index}].objective.mode").lower()
            if mode not in {"expectation", "anomaly"}:
                raise EvidenceError(f"requirements[{index}].objective.mode is unsupported")
            objective = {
                "mode": mode,
                "name": text(objective["name"], f"requirements[{index}].objective.name"),
            }
        expected_role = text(
            row["expected_execution_role"],
            f"requirements[{index}].expected_execution_role",
            required=False,
        )
        normalized_requirements.append(
            {
                "id": requirement_id,
                "object": object_identity(row["object"], f"requirements[{index}].object"),
                "metric": metric_identity(row["metric"], f"requirements[{index}].metric"),
                "objective": objective,
                "max_result_age_seconds": positive_integer(
                    row["max_result_age_seconds"],
                    f"requirements[{index}].max_result_age_seconds",
                ),
                "expected_schedule": text(
                    row["expected_schedule"],
                    f"requirements[{index}].expected_schedule",
                ).upper(),
                "notification_required": boolean(
                    row["notification_required"],
                    f"requirements[{index}].notification_required",
                    default=False,
                ),
                "expected_execution_role": expected_role.upper(),
                "required_groups": string_list(row["required_groups"], f"requirements[{index}].required_groups"),
            }
        )

    association_keys = {
        "requirement_id",
        "reference_id",
        "schedule",
        "schedule_status",
        "schedule_update_pending",
        "notification_status",
        "anomaly_status",
        "execution_role",
        "observed_groups",
    }
    normalized_associations: list[dict[str, Any]] = []
    seen_association_requirements: set[str] = set()
    seen_reference_ids: set[str] = set()
    for index, row in enumerate(associations):
        if set(row) != association_keys:
            raise EvidenceError(f"associations[{index}] keys must be exactly {sorted(association_keys)}")
        requirement_id = text(row["requirement_id"], f"associations[{index}].requirement_id")
        reference_id = text(row["reference_id"], f"associations[{index}].reference_id")
        if requirement_id in seen_association_requirements or reference_id in seen_reference_ids:
            raise EvidenceError("association requirement_id and reference_id must be unique")
        seen_association_requirements.add(requirement_id)
        seen_reference_ids.add(reference_id)
        normalized_associations.append(
            {
                "requirement_id": requirement_id,
                "reference_id": reference_id,
                "schedule": text(row["schedule"], f"associations[{index}].schedule").upper(),
                "schedule_status": text(row["schedule_status"], f"associations[{index}].schedule_status").upper(),
                "schedule_update_pending": boolean(
                    row["schedule_update_pending"],
                    f"associations[{index}].schedule_update_pending",
                    default=False,
                ),
                "notification_status": text(
                    row["notification_status"],
                    f"associations[{index}].notification_status",
                ).upper(),
                "anomaly_status": text(row["anomaly_status"], f"associations[{index}].anomaly_status").upper(),
                "execution_role": text(row["execution_role"], f"associations[{index}].execution_role").upper(),
                "observed_groups": string_list(row["observed_groups"], f"associations[{index}].observed_groups"),
            }
        )

    measurement_keys = {
        "requirement_id",
        "reference_id",
        "measured_at",
        "evaluation_status",
        "expectation_name",
        "expectation_violated",
        "anomaly_detected",
        "observed_value",
        "observed_groups",
    }
    normalized_measurements: list[dict[str, Any]] = []
    for index, row in enumerate(measurements):
        if set(row) != measurement_keys:
            raise EvidenceError(f"measurements[{index}] keys must be exactly {sorted(measurement_keys)}")
        observed_value = row["observed_value"]
        if isinstance(observed_value, (dict, list)):
            raise EvidenceError(f"measurements[{index}].observed_value must be scalar")
        measured_at = parse_time(row["measured_at"], f"measurements[{index}].measured_at")
        normalized_measurements.append(
            {
                "requirement_id": text(row["requirement_id"], f"measurements[{index}].requirement_id"),
                "reference_id": text(row["reference_id"], f"measurements[{index}].reference_id"),
                "measured_at": measured_at.isoformat().replace("+00:00", "Z"),
                "evaluation_status": text(
                    row["evaluation_status"],
                    f"measurements[{index}].evaluation_status",
                ).upper(),
                "expectation_name": text(
                    row["expectation_name"],
                    f"measurements[{index}].expectation_name",
                    required=False,
                ),
                "expectation_violated": boolean(
                    row["expectation_violated"],
                    f"measurements[{index}].expectation_violated",
                ),
                "anomaly_detected": boolean(
                    row["anomaly_detected"],
                    f"measurements[{index}].anomaly_detected",
                ),
                "observed_value": observed_value,
                "observed_groups": string_list(row["observed_groups"], f"measurements[{index}].observed_groups"),
            }
        )

        if measured_at < window_start or measured_at > window_end:
            raise EvidenceError(f"measurements[{index}].measured_at must fall within metadata.window_start/window_end")

    source_keys = {
        "source",
        "kind",
        "status",
        "collected_at",
        "latest_record_at",
        "max_latency_seconds",
        "row_count",
        "error_code",
    }
    normalized_sources: list[dict[str, Any]] = []
    seen_sources: set[str] = set()
    for index, row in enumerate(sources):
        if set(row) != source_keys:
            raise EvidenceError(f"source_metadata[{index}] keys must be exactly {sorted(source_keys)}")
        source = text(row["source"], f"source_metadata[{index}].source")
        if source in seen_sources:
            raise EvidenceError(f"duplicate source metadata: {source}")
        seen_sources.add(source)
        latest = row["latest_record_at"]
        normalized_sources.append(
            {
                "source": source,
                "kind": text(row["kind"], f"source_metadata[{index}].kind").lower(),
                "status": text(row["status"], f"source_metadata[{index}].status").lower(),
                "collected_at": parse_time(
                    row["collected_at"],
                    f"source_metadata[{index}].collected_at",
                )
                .isoformat()
                .replace("+00:00", "Z"),
                "latest_record_at": (
                    parse_time(latest, f"source_metadata[{index}].latest_record_at").isoformat().replace("+00:00", "Z")
                    if latest is not None
                    else None
                ),
                "max_latency_seconds": positive_integer(
                    row["max_latency_seconds"],
                    f"source_metadata[{index}].max_latency_seconds",
                ),
                "row_count": row["row_count"],
                "error_code": text(row["error_code"], f"source_metadata[{index}].error_code", required=False).upper(),
            }
        )
        source_collected_at = parse_time(row["collected_at"], f"source_metadata[{index}].collected_at")
        if source_collected_at < window_start:
            raise EvidenceError(f"source_metadata[{index}].collected_at cannot precede metadata.window_start")
        if source_collected_at > collected_at:
            raise EvidenceError(f"source_metadata[{index}].collected_at cannot be after metadata.collected_at")
        source_latest = normalized_sources[-1]["latest_record_at"]
        if source_latest is not None:
            source_latest_at = parse_time(source_latest, f"source_metadata[{index}].latest_record_at")
            if source_latest_at < window_start or source_latest_at > window_end:
                raise EvidenceError(
                    f"source_metadata[{index}].latest_record_at must fall within metadata.window_start/window_end"
                )
        if type(row["row_count"]) is not int or row["row_count"] < 0:
            raise EvidenceError(f"source_metadata[{index}].row_count must be a non-negative integer")

    current_state = data.get("current_state")
    if current_state is None:
        normalized_current_state = {
            "status": "not_supplied",
            "observed_at": None,
            "max_age_seconds": None,
            "associations": [],
            "notifications": [],
        }
    else:
        if not isinstance(current_state, dict):
            raise EvidenceError("current_state must be an object")
        current_keys = {"status", "observed_at", "max_age_seconds", "associations", "notifications"}
        if set(current_state) != current_keys:
            raise EvidenceError(f"current_state keys must be exactly {sorted(current_keys)}")
        current_status = text(current_state["status"], "current_state.status").lower()
        current_observed = parse_time(current_state["observed_at"], "current_state.observed_at")
        max_age = positive_integer(current_state["max_age_seconds"], "current_state.max_age_seconds")
        if current_observed > collected_at:
            raise EvidenceError("current_state.observed_at cannot be after metadata.collected_at")
        current_associations = current_state["associations"]
        current_notifications = current_state["notifications"]
        if not isinstance(current_associations, list) or any(
            not isinstance(row, dict) for row in current_associations
        ):
            raise EvidenceError("current_state.associations must be an array of objects")
        if not isinstance(current_notifications, list) or any(
            not isinstance(row, dict) for row in current_notifications
        ):
            raise EvidenceError("current_state.notifications must be an array of objects")
        current_association_keys = {
            "requirement_id",
            "reference_id",
            "status",
            "schedule_status",
            "notification_status",
            "execution_role",
        }
        normalized_associations_current: list[dict[str, str]] = []
        seen_current_requirements: set[str] = set()
        for index, row in enumerate(current_associations):
            if set(row) != current_association_keys:
                raise EvidenceError(
                    f"current_state.associations[{index}] keys must be exactly {sorted(current_association_keys)}"
                )
            requirement_id = text(row["requirement_id"], f"current_state.associations[{index}].requirement_id")
            if requirement_id in seen_current_requirements:
                raise EvidenceError(f"duplicate current association requirement id: {requirement_id}")
            seen_current_requirements.add(requirement_id)
            normalized_associations_current.append(
                {
                    "requirement_id": requirement_id,
                    "reference_id": text(row["reference_id"], f"current_state.associations[{index}].reference_id"),
                    "status": text(row["status"], f"current_state.associations[{index}].status").upper(),
                    "schedule_status": text(
                        row["schedule_status"], f"current_state.associations[{index}].schedule_status"
                    ).upper(),
                    "notification_status": text(
                        row["notification_status"], f"current_state.associations[{index}].notification_status"
                    ).upper(),
                    "execution_role": text(
                        row["execution_role"], f"current_state.associations[{index}].execution_role"
                    ).upper(),
                }
            )
        notification_keys = {"requirement_id", "status", "last_delivery_at"}
        normalized_notifications: list[dict[str, Any]] = []
        seen_notification_requirements: set[str] = set()
        for index, row in enumerate(current_notifications):
            if set(row) != notification_keys:
                raise EvidenceError(
                    f"current_state.notifications[{index}] keys must be exactly {sorted(notification_keys)}"
                )
            requirement_id = text(row["requirement_id"], f"current_state.notifications[{index}].requirement_id")
            if requirement_id in seen_notification_requirements:
                raise EvidenceError(f"duplicate current notification requirement id: {requirement_id}")
            seen_notification_requirements.add(requirement_id)
            last_delivery = row["last_delivery_at"]
            normalized_notifications.append(
                {
                    "requirement_id": requirement_id,
                    "status": text(row["status"], f"current_state.notifications[{index}].status").upper(),
                    "last_delivery_at": (
                        parse_time(
                            last_delivery,
                            f"current_state.notifications[{index}].last_delivery_at",
                        )
                        .isoformat()
                        .replace("+00:00", "Z")
                        if last_delivery is not None
                        else None
                    ),
                }
            )
        normalized_current_state = {
            "status": current_status,
            "observed_at": current_observed.isoformat().replace("+00:00", "Z"),
            "max_age_seconds": max_age,
            "associations": sorted(normalized_associations_current, key=lambda item: item["requirement_id"]),
            "notifications": sorted(normalized_notifications, key=lambda item: item["requirement_id"]),
        }

    current_observed_at = (
        parse_time(normalized_current_state["observed_at"], "current_state.observed_at")
        if normalized_current_state["observed_at"] is not None
        else None
    )
    current_state_receipt = validate_current_state_receipt(
        data.get("current_state_receipt"),
        envelope_collected_at=collected_at,
        current_observed_at=current_observed_at,
        requirements=normalized_requirements,
        current_associations=normalized_current_state["associations"],
        current_notifications=normalized_current_state["notifications"],
    )

    return {
        "metadata": normalized_metadata,
        "requirements": sorted(normalized_requirements, key=lambda item: item["id"]),
        "associations": sorted(normalized_associations, key=lambda item: item["requirement_id"]),
        "measurements": sorted(
            normalized_measurements,
            key=lambda item: (item["requirement_id"], item["measured_at"], item["reference_id"]),
        ),
        "source_metadata": sorted(normalized_sources, key=lambda item: item["source"]),
        "current_state": normalized_current_state,
        "current_state_receipt": current_state_receipt,
    }


def finding(
    code: str,
    scope: str,
    evidence: str,
    action: str,
    *,
    quality_impact: str = "PASS",
    monitoring_impact: str = "PASS",
) -> dict[str, str]:
    return {
        "code": code,
        "scope": scope,
        "evidence": evidence,
        "action": action,
        "quality_impact": quality_impact,
        "monitoring_impact": monitoring_impact,
    }


def _status(findings: list[dict[str, str]], field: str) -> str:
    impacts = [item[field] for item in findings if item[field] != "PASS"]
    return min(impacts, key=lambda status: STATUS_ORDER[status]) if impacts else "PASS"


def analyze(data: Any) -> dict[str, Any]:
    normalized = normalize_document(data)
    requirements = normalized["requirements"]
    associations_by_requirement = {row["requirement_id"]: row for row in normalized["associations"]}
    measurements_by_requirement: dict[str, list[dict[str, Any]]] = {}
    for row in normalized["measurements"]:
        measurements_by_requirement.setdefault(row["requirement_id"], []).append(row)
    collected_at = parse_time(normalized["metadata"]["collected_at"], "metadata.collected_at")
    findings: list[dict[str, str]] = []
    current_state = normalized["current_state"]
    current_state_receipt = normalized["current_state_receipt"]
    current_associations = {row["requirement_id"]: row for row in current_state["associations"]}
    current_notifications = {row["requirement_id"]: row for row in current_state["notifications"]}
    if not current_state_receipt["complete"]:
        findings.append(
            finding(
                "DQ_CURRENT_STATE_RECEIPT_INVALID",
                "data-quality-current-state",
                "; ".join(current_state_receipt["issues"]),
                "Recollect with the bundled data-quality-current surface and preserve its exact canonical receipt.",
                quality_impact="INCONCLUSIVE",
                monitoring_impact="INCONCLUSIVE",
            )
        )
    if current_state["status"] != "collected":
        findings.append(
            finding(
                "DQ_CURRENT_STATE_UNAVAILABLE",
                "data-quality-current-state",
                f"current association state status is {current_state['status']}",
                "Collect current association and notification metadata before claiming monitoring health.",
                quality_impact="INCONCLUSIVE",
                monitoring_impact="INCONCLUSIVE",
            )
        )
    elif current_state["observed_at"] is not None:
        current_age = int((collected_at - parse_time(current_state["observed_at"], "current_state.observed_at")).total_seconds())
        if current_age > current_state["max_age_seconds"]:
            findings.append(
                finding(
                    "DQ_CURRENT_STATE_STALE",
                    "data-quality-current-state",
                    f"current association state is {current_age}s old; limit is {current_state['max_age_seconds']}s",
                    "Recollect current association and notification metadata before making a monitoring claim.",
                    quality_impact="INCONCLUSIVE",
                    monitoring_impact="INCONCLUSIVE",
                )
            )

    edition_unavailable = any(
        source["error_code"] in {"DQ_EDITION_UNAVAILABLE", "ENTERPRISE_EDITION_REQUIRED", "FEATURE_NOT_AVAILABLE"}
        or source["status"] == "edition_unavailable"
        for source in normalized["source_metadata"]
    )
    if edition_unavailable:
        findings.append(
            finding(
                "DQ_EDITION_UNAVAILABLE",
                "data-quality-surface",
                "Enterprise data-quality evidence is unavailable for the selected account or role.",
                "Record the edition boundary; do not infer health or escalate privileges automatically.",
                quality_impact="INCONCLUSIVE",
                monitoring_impact="INCONCLUSIVE",
            )
        )

    usage_sources = [source for source in normalized["source_metadata"] if source["kind"] == "usage"]
    if not usage_sources or any(source["status"] != "collected" for source in usage_sources):
        findings.append(
            finding(
                "DQ_USAGE_VISIBILITY_GAP",
                "data-quality-usage",
                "No complete collected usage source proves monitoring visibility.",
                "Restore read-only usage visibility before making coverage or cost claims.",
                quality_impact="INCONCLUSIVE",
                monitoring_impact="INCONCLUSIVE",
            )
        )

    notification_privilege_error = any(
        source["error_code"] in {"DQ_NOTIFICATION_PRIVILEGE_ERROR", "INSUFFICIENT_PRIVILEGES", "NOT_AUTHORIZED"}
        and source["kind"] == "notification"
        for source in normalized["source_metadata"]
    )
    if notification_privilege_error:
        findings.append(
            finding(
                "DQ_NOTIFICATION_PRIVILEGE_ERROR",
                "notification-evidence",
                "Notification evidence collection failed with a privilege error.",
                "Grant only the documented read/monitor privilege and recollect; do not switch to ACCOUNTADMIN.",
                quality_impact="INCONCLUSIVE",
                monitoring_impact="FAIL",
            )
        )

    if not edition_unavailable:
        for requirement in requirements:
            requirement_id = requirement["id"]
            scope = requirement_id
            objective = requirement["objective"]
            if requirement["object"]["type"] not in SUPPORTED_OBJECT_TYPES:
                findings.append(
                    finding(
                        "DQ_UNSUPPORTED_OBJECT",
                        scope,
                        f"Object type {requirement['object']['type']} is outside this analyzer's TABLE/VIEW contract.",
                        "Use a supported object or document a separate monitoring control.",
                        quality_impact="INCONCLUSIVE",
                        monitoring_impact="FAIL",
                    )
                )
            if objective is None:
                findings.append(
                    finding(
                        "DQ_OBJECTIVE_MISSING",
                        scope,
                        "The required metric has no expectation or anomaly objective.",
                        "Define a bounded objective before interpreting the metric value.",
                        quality_impact="INCONCLUSIVE",
                        monitoring_impact="DEGRADED",
                    )
                )

            association = associations_by_requirement.get(requirement_id)
            if association is None:
                findings.append(
                    finding(
                        "DQ_ASSOCIATION_MISSING",
                        scope,
                        "No observed DMF association matches the required check.",
                        "Create or restore the association through the approved change process.",
                        quality_impact="INCONCLUSIVE",
                        monitoring_impact="FAIL",
                    )
                )
            else:
                if association["schedule_status"].startswith("SUSPENDED"):
                    findings.append(
                        finding(
                            "DQ_ASSOCIATION_SUSPENDED",
                            scope,
                            f"Association status is {association['schedule_status']}.",
                            "Resolve the documented suspension cause before resuming evaluation.",
                            quality_impact="INCONCLUSIVE",
                            monitoring_impact="FAIL",
                        )
                    )
                if (
                    association["schedule_update_pending"]
                    or association["schedule"] != requirement["expected_schedule"]
                ):
                    findings.append(
                        finding(
                            "DQ_SCHEDULE_UPDATE_PENDING",
                            scope,
                            f"Observed schedule {association['schedule']} differs from required {requirement['expected_schedule']}.",
                            "Wait for metadata propagation or complete the approved schedule update, then recollect.",
                            quality_impact="INCONCLUSIVE",
                            monitoring_impact="DEGRADED",
                        )
                    )
                if requirement["notification_required"] and association["notification_status"] not in {
                    "ENABLED",
                    "STARTED",
                }:
                    findings.append(
                        finding(
                            "DQ_NOTIFICATION_DISABLED",
                            scope,
                            f"Required notification status is {association['notification_status']}.",
                            "Enable the approved notification path and verify delivery with a safe test.",
                            monitoring_impact="DEGRADED",
                        )
                    )
                if (
                    requirement["expected_execution_role"]
                    and association["execution_role"] != requirement["expected_execution_role"]
                ):
                    findings.append(
                        finding(
                            "DQ_EXECUTION_ROLE_DRIFT",
                            scope,
                            f"Observed role {association['execution_role']} differs from required {requirement['expected_execution_role']}.",
                            "Restore the least-privilege execution role and verify object visibility.",
                            quality_impact="INCONCLUSIVE",
                            monitoring_impact="FAIL",
                        )
                    )
                if association["anomaly_status"] == "TRAINING_IN_PROGRESS":
                    findings.append(
                        finding(
                            "DQ_ANOMALY_TRAINING",
                            scope,
                            "Anomaly detection is still training; this is not a health result.",
                            "Wait for training completion and require a post-training measurement.",
                            quality_impact="INCONCLUSIVE",
                            monitoring_impact="DEGRADED",
                        )
                    )

            current_association = current_associations.get(requirement_id)
            if current_state["status"] == "collected" and current_association is None:
                findings.append(
                    finding(
                        "DQ_CURRENT_ASSOCIATION_MISSING",
                        scope,
                        "No current association metadata matches the required check.",
                        "Collect current DATA_METRIC_FUNCTION_REFERENCES metadata; historical association rows cannot prove present coverage.",
                        quality_impact="INCONCLUSIVE",
                        monitoring_impact="FAIL",
                    )
                )
            elif current_association is not None:
                if current_association["status"] != "ACTIVE" or current_association["schedule_status"] != "STARTED":
                    findings.append(
                        finding(
                            "DQ_CURRENT_ASSOCIATION_NOT_ACTIVE",
                            scope,
                            f"current status={current_association['status']} schedule_status={current_association['schedule_status']}",
                            "Restore the association through approved change control, then recollect current metadata.",
                            quality_impact="INCONCLUSIVE",
                            monitoring_impact="FAIL",
                        )
                    )
                if requirement["notification_required"] and current_association["notification_status"] not in {
                    "ENABLED",
                    "STARTED",
                }:
                    findings.append(
                        finding(
                            "DQ_CURRENT_NOTIFICATION_DISABLED",
                            scope,
                            f"current notification status={current_association['notification_status']}",
                            "Restore the approved notification integration and verify delivery without collecting payloads.",
                            quality_impact="INCONCLUSIVE",
                            monitoring_impact="FAIL",
                        )
                    )
            current_notification = current_notifications.get(requirement_id)
            if requirement["notification_required"] and current_state["status"] == "collected":
                if current_notification is None or current_notification["status"] not in {"ENABLED", "STARTED"}:
                    findings.append(
                        finding(
                            "DQ_NOTIFICATION_STATE_MISSING",
                            scope,
                            "Current notification delivery state is missing or not enabled.",
                            "Collect notification state and a safe delivery receipt; do not infer delivery from an expectation result.",
                            quality_impact="INCONCLUSIVE",
                            monitoring_impact="FAIL",
                        )
                    )

            measurements = measurements_by_requirement.get(requirement_id, [])
            if not measurements:
                findings.append(
                    finding(
                        "DQ_RESULT_MISSING",
                        scope,
                        "No measurement exists in the declared evidence window.",
                        "Verify scheduling, permissions, and event-table visibility; do not infer pass.",
                        quality_impact="INCONCLUSIVE",
                        monitoring_impact="DEGRADED",
                    )
                )
                continue
            latest = max(measurements, key=lambda item: item["measured_at"])
            measured_at = parse_time(latest["measured_at"], f"measurements[{scope}].measured_at")
            age_seconds = max(0, int((collected_at - measured_at).total_seconds()))
            if age_seconds > requirement["max_result_age_seconds"]:
                findings.append(
                    finding(
                        "DQ_RESULT_STALE",
                        scope,
                        f"Newest result is {age_seconds}s old; limit is {requirement['max_result_age_seconds']}s.",
                        "Recollect after the next successful evaluation before making a health claim.",
                        quality_impact="INCONCLUSIVE",
                        monitoring_impact="DEGRADED",
                    )
                )

            if objective is None and latest["observed_value"] is not None:
                findings.append(
                    finding(
                        "DQ_METRIC_OBSERVED_NO_OBJECTIVE",
                        scope,
                        "A raw metric value was observed without a decision objective.",
                        "Treat the value as observation only; define an objective before classifying quality.",
                        quality_impact="INCONCLUSIVE",
                        monitoring_impact="DEGRADED",
                    )
                )
            elif objective and objective["mode"] == "expectation":
                if latest["evaluation_status"] in {"FAILED", "ERROR"} or latest["expectation_violated"] is None:
                    findings.append(
                        finding(
                            "DQ_EXPECTATION_EVALUATION_FAILED",
                            scope,
                            f"Expectation evaluation status is {latest['evaluation_status']}.",
                            "Fix evaluation execution and obtain a valid Boolean result before classifying quality.",
                            quality_impact="INCONCLUSIVE",
                            monitoring_impact="DEGRADED",
                        )
                    )
                elif latest["expectation_violated"] is True:
                    findings.append(
                        finding(
                            "DQ_EXPECTATION_VIOLATED",
                            scope,
                            f"Expectation {objective['name']} was violated by the newest valid result.",
                            "Investigate the governed data owner workflow; never include raw failed rows in evidence.",
                            quality_impact="FAIL",
                        )
                    )
            elif objective and objective["mode"] == "anomaly" and latest["anomaly_detected"] is True:
                findings.append(
                    finding(
                        "DQ_ANOMALY_DETECTED",
                        scope,
                        f"Anomaly objective {objective['name']} detected an anomaly in the newest result.",
                        "Triage the anomaly with aggregate metadata only and record the disposition.",
                        quality_impact="FAIL",
                    )
                )

            observed_groups = set(latest["observed_groups"])
            if association is not None:
                observed_groups.update(association["observed_groups"])
            missing_groups = sorted(set(requirement["required_groups"]) - observed_groups)
            if missing_groups:
                findings.append(
                    finding(
                        "DQ_GROUP_COVERAGE_GAP",
                        scope,
                        f"Required groups lack evidence: {', '.join(missing_groups)}.",
                        "Restore grouped evaluation coverage and verify each required group emits a result.",
                        quality_impact="INCONCLUSIVE",
                        monitoring_impact="DEGRADED",
                    )
                )

        known_requirement_ids = {item["id"] for item in requirements}
        for measurement in normalized["measurements"]:
            if measurement["requirement_id"] not in known_requirement_ids and measurement["observed_value"] is not None:
                findings.append(
                    finding(
                        "DQ_METRIC_OBSERVED_NO_OBJECTIVE",
                        measurement["requirement_id"],
                        "A measurement is outside the governed requirement denominator.",
                        "Add an owner-approved requirement and objective or retire the orphan measurement.",
                        quality_impact="INCONCLUSIVE",
                        monitoring_impact="DEGRADED",
                    )
                )

    findings.sort(key=lambda item: (item["code"], item["scope"], item["evidence"]))
    if requirements:
        quality_status = _status(findings, "quality_impact")
        monitoring_status = _status(findings, "monitoring_impact")
    else:
        quality_status = "NO_REQUIRED_CHECKS"
        monitoring_status = "NO_REQUIRED_CHECKS"

    input_hash = f"sha256:{hashlib.sha256(canonical_json(normalized)).hexdigest()}"
    report = {
        "schema_version": "1",
        "analyzer": {"name": "snowflake-data-quality-sentinel", "version": VERSION},
        "quality_status": quality_status,
        "monitoring_status": monitoring_status,
        "denominator": {
            "requirements": len(requirements),
            "associations": len(normalized["associations"]),
            "measurements": len(normalized["measurements"]),
            "sources": len(normalized["source_metadata"]),
        },
        "finding_counts": dict(sorted(Counter(item["code"] for item in findings).items())),
        "findings": findings,
        "provenance": {
            "input_sha256": input_hash,
            "collector_receipt_sha256": normalized["metadata"]["collector_receipt_sha256"],
            "surface": normalized["metadata"]["surface"],
            "collected_at": normalized["metadata"]["collected_at"],
            "window_start": normalized["metadata"]["window_start"],
            "window_end": normalized["metadata"]["window_end"],
            "sources": normalized["source_metadata"],
            "current_state_receipt": current_state_receipt,
        },
        "non_claims": [
            "No Snowflake mutation was executed.",
            "Raw metric values without objectives are not violations or passes.",
            "Anomaly training is not a health result.",
            "Missing, stale, unavailable, or privilege-blocked evidence cannot prove health.",
        ],
    }
    report["receipt_sha256"] = f"sha256:{hashlib.sha256(canonical_json(report)).hexdigest()}"
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", help="normalized evidence JSON; omit to read stdin")
    parser.add_argument("--pretty", action="store_true", help="indent JSON output")
    args = parser.parse_args(argv)
    try:
        if args.input:
            raw = Path(args.input).read_text(encoding="utf-8")
        else:
            raw = sys.stdin.read()
        data = json.loads(raw)
        report = analyze(data)
    except (OSError, json.JSONDecodeError, EvidenceError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    json.dump(report, sys.stdout, indent=2 if args.pretty else None, sort_keys=True, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
