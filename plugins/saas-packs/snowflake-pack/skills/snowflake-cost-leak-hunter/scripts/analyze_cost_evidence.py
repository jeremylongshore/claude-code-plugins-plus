#!/usr/bin/env python3
"""Validate and summarize normalized, read-only Snowflake cost evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit


class EvidenceError(ValueError):
    """Raised when evidence cannot support a safe deterministic result."""


EXPECTED_COLLECTOR_SOURCES = [
    "SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY",
    "SNOWFLAKE.ACCOUNT_USAGE.QUERY_ATTRIBUTION_HISTORY",
    "SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_LOAD_HISTORY",
    "SNOWFLAKE.ACCOUNT_USAGE.METERING_HISTORY",
]
RECEIPT_DATASETS = ("warehouse_metering", "query_attribution", "warehouse_load", "serverless_usage")
BASELINE_RECEIPT_DATASETS = ("execution_context", *RECEIPT_DATASETS)
EXPECTED_COST_SURFACES = (
    "warehouse_metering",
    "query_attribution",
    "warehouse_load",
    "serverless_usage",
    "adaptive_usage",
    "storage_usage",
    "data_transfer_usage",
    "internal_transfer_usage",
    "ai_usage",
    "resource_monitors",
    "budgets",
)
EXPECTED_SURFACE_SOURCES = {
    "warehouse_metering": "SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY",
    "query_attribution": "SNOWFLAKE.ACCOUNT_USAGE.QUERY_ATTRIBUTION_HISTORY",
    "warehouse_load": "SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_LOAD_HISTORY",
    "serverless_usage": "SNOWFLAKE.ACCOUNT_USAGE.METERING_HISTORY",
    "adaptive_usage": "SNOWFLAKE.ACCOUNT_USAGE.QUERY_METERING_HISTORY",
    "storage_usage": "SNOWFLAKE.ACCOUNT_USAGE.STORAGE_USAGE",
    "data_transfer_usage": "SNOWFLAKE.ACCOUNT_USAGE.DATA_TRANSFER_HISTORY",
    "internal_transfer_usage": "SNOWFLAKE.ACCOUNT_USAGE.INTERNAL_DATA_TRANSFER_HISTORY",
    "ai_usage": "SNOWFLAKE.ACCOUNT_USAGE.CORTEX_AI_FUNCTIONS_USAGE_HISTORY",
    "resource_monitors": "SHOW RESOURCE MONITORS",
    "budgets": "SHOW SNOWFLAKE.CORE.BUDGET",
}
SUPPLEMENTAL_RECEIPT_SURFACES = {
    "adaptive_usage": ("cost-adaptive", "adaptive_usage"),
    "storage_usage": ("cost-storage", "storage_usage"),
    "data_transfer_usage": ("cost-transfer", "data_transfer_usage"),
    "internal_transfer_usage": ("cost-internal-transfer", "internal_transfer_usage"),
    "ai_usage": ("cost-ai-functions", "ai_usage"),
    "resource_monitors": ("cost-resource-monitors", "resource_monitors"),
    "budgets": ("cost-budgets", "budgets"),
}
SURFACE_ARRAYS = {
    "warehouse_metering": "warehouse_metering",
    "query_attribution": "query_attribution",
    "warehouse_load": "warehouse_load",
    "serverless_usage": "serverless_usage",
    "adaptive_usage": "adaptive_usage",
    "storage_usage": "storage_usage",
    "data_transfer_usage": "data_transfer_usage",
    "internal_transfer_usage": "internal_transfer_usage",
    "ai_usage": "ai_usage",
}
SURFACE_STATUSES = {"available", "unavailable", "region_unavailable", "privilege_error", "not_collected"}
LEDGER_ROLES = {"total", "attribution", "context", "estimate", "invoice-only"}
INVOICE_STATUSES = {"not_reconciled", "partially_reconciled", "reconciled", "invoice_only"}
COMPLETENESS_BLOCKING_CODES = {
    "COST_SURFACE_MISSING",
    "COST_SURFACE_STALE",
    "COST_SURFACE_TRUNCATED",
    "COST_DOUBLE_COUNT_RISK",
    "COST_ADAPTIVE_REGION_UNAVAILABLE",
    "COST_SURFACE_RECEIPT_INVALID",
    "COST_EVIDENCE_UNTRUSTED",
    "COST_AI_IN_PROGRESS",
    "COST_ADAPTIVE_IN_PROGRESS",
    "COST_INVOICE_UNVERIFIED",
    "COST_WINDOW_COVERAGE_GAP",
}
HASH_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
SURFACE_LATENCY_HOURS = {
    # Versioned from Snowflake's official Account Usage documentation.  Use the
    # slowest field carried by a surface, not a caller-provided optimistic value.
    "warehouse_metering": Decimal("6"),
    "query_attribution": Decimal("8"),
    "warehouse_load": Decimal("3"),
    "serverless_usage": Decimal("12"),
    "adaptive_usage": Decimal("1"),
    "storage_usage": Decimal("2"),
    "data_transfer_usage": Decimal("2"),
    "internal_transfer_usage": Decimal("3"),
    "ai_usage": Decimal("0.083334"),
    "resource_monitors": Decimal("0"),
    "budgets": Decimal("0"),
}
LATENCY_CONTRACT_VERSION = "snowflake-docs-2026-09-03"
WAREHOUSE_SIZES = (
    "X-SMALL",
    "SMALL",
    "MEDIUM",
    "LARGE",
    "X-LARGE",
    "2X-LARGE",
    "3X-LARGE",
    "4X-LARGE",
    "5X-LARGE",
    "6X-LARGE",
)
ROLLBACK_THRESHOLD_KEYS = {
    "max_p95_latency_regression_pct",
    "max_queue_regression_pct",
}
CONTEXT_FIELDS = {
    "observed_at",
    "account_identifier_sha256",
    "collector_user_sha256",
    "primary_role_sha256",
    "primary_role_type",
    "secondary_roles_sha256",
    "session_timezone",
}
CONTEXT_HASH_FIELDS = {
    "account_identifier_sha256",
    "collector_user_sha256",
    "primary_role_sha256",
    "secondary_roles_sha256",
}
CONTEXT_IDENTITY_FIELDS = CONTEXT_FIELDS - {"observed_at"}
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
MAX_RECEIPT_AGE_SECONDS = 3600
MAX_COLLECTION_INTERVAL_SECONDS = 120
MAX_COST_WINDOW = timedelta(days=7)
COST_HISTORY_COLLECTOR_SURFACES = {
    "cost",
    "cost-adaptive",
    "cost-ai-functions",
    "cost-internal-transfer",
    "cost-storage",
    "cost-transfer",
}
REVIEWED_INTRINSIC_ROW_LIMITS = {"cost-resource-monitors": 10000}
SQL_HASH_PREFIXES = {
    "SELECT",
    "WITH",
    "INSERT",
    "UPDATE",
    "DELETE",
    "MERGE",
    "DROP",
    "ALTER",
    "CREATE",
    "GRANT",
    "REVOKE",
    "CALL",
}


def validate_hash(value: Any, field: str) -> str:
    if not isinstance(value, str) or not HASH_RE.fullmatch(value):
        raise EvidenceError(f"{field} must be an opaque query hash, not SQL or free-form text")
    if value.split(".", 1)[0].upper() in SQL_HASH_PREFIXES:
        raise EvidenceError(f"{field} must be an opaque query hash, not SQL or free-form text")
    return value


def validate_sha256_hex(value: Any, field: str) -> str:
    if not isinstance(value, str) or not HEX64_RE.fullmatch(value):
        raise EvidenceError(f"{field} must be a 64-character lowercase SHA-256 hex digest")
    return value


def validate_tag_indicator(row: dict[str, Any], prefix: str) -> bool:
    present = row.get("query_tag_present")
    if not isinstance(present, bool):
        raise EvidenceError(f"{prefix}.query_tag_present is required and must be boolean")
    digest = row.get("query_tag_sha256")
    if digest is not None and (not isinstance(digest, str) or not HEX64_RE.fullmatch(digest)):
        raise EvidenceError(f"{prefix}.query_tag_sha256 must be a SHA-256 hex digest or null")
    if present != (digest is not None):
        raise EvidenceError(f"{prefix}.query_tag_present must be true exactly when query_tag_sha256 is present")
    return present


def warehouse_label(row: dict[str, Any], prefix: str) -> str:
    digest = row.get("warehouse_name_sha256")
    if digest is not None:
        if not isinstance(digest, str) or not HEX64_RE.fullmatch(digest):
            raise EvidenceError(f"{prefix}.warehouse_name_sha256 must be a SHA-256 hex digest")
        return digest
    warehouse_id = row.get("warehouse_id")
    if warehouse_id is not None:
        return safe_text(f"warehouse-id:{warehouse_id}", f"{prefix}.warehouse_id")
    return "<unknown>"


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def canonical_bundle_digest(data: dict[str, Any]) -> str:
    """Return the digest an operator records at a separate trusted boundary."""

    return f"sha256:{hashlib.sha256(_canonical_json(data)).hexdigest()}"


def assess_input_trust(data: dict[str, Any], trusted_input_sha256: str | None, warnings: list[str]) -> dict[str, Any]:
    actual = canonical_bundle_digest(data)
    non_claim = (
        "A matching digest is an operator assertion of byte identity at a separate trusted local boundary; "
        "it is not a signature, collector identity, or proof of Snowflake origin."
    )
    if trusted_input_sha256 is None:
        warnings.append("evidence provenance is untrusted; no out-of-band trusted-input digest was supplied")
        return {"status": "UNTRUSTED", "trusted": False, "actual_sha256": actual, "non_claim": non_claim}
    if not isinstance(trusted_input_sha256, str) or not DIGEST_RE.fullmatch(trusted_input_sha256):
        warnings.append("trusted input digest is malformed; evidence provenance remains untrusted")
        return {"status": "INVALID_TRUST_ANCHOR", "trusted": False, "actual_sha256": actual, "non_claim": non_claim}
    if trusted_input_sha256 != actual:
        warnings.append("trusted input digest does not match the supplied cost evidence bundle")
        return {"status": "DIGEST_MISMATCH", "trusted": False, "actual_sha256": actual, "non_claim": non_claim}
    return {
        "status": "DIGEST_MATCHED_OPERATOR_ASSERTED",
        "trusted": True,
        "actual_sha256": actual,
        "non_claim": non_claim,
    }


def _rows_match(left: Any, right: Any) -> bool:
    if not isinstance(left, list) or not isinstance(right, list) or len(left) != len(right):
        return False
    return sorted(_canonical_json(row) for row in left) == sorted(_canonical_json(row) for row in right)


def _reviewed_row_limit(template_name: str, collector_surface: str) -> int:
    """Derive the only accepted cap from the checked-in reviewed template."""

    template_path = Path(__file__).resolve().parent / "sql" / template_name
    try:
        template = template_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise EvidenceError(f"reviewed SQL template is unavailable: {template_name}") from exc
    limits = {int(value) for value in re.findall(r"\bLIMIT\s+(\d+)\b", template, flags=re.IGNORECASE)}
    intrinsic = REVIEWED_INTRINSIC_ROW_LIMITS.get(collector_surface)
    if intrinsic is not None:
        limits.add(intrinsic)
    if len(limits) != 1:
        raise EvidenceError(f"reviewed SQL template has no single enforceable row cap: {template_name}")
    return limits.pop()


def _receipt_settlement_observation(receipt: Any) -> datetime | None:
    if not isinstance(receipt, dict):
        return None
    datasets = receipt.get("datasets")
    contexts = datasets.get("execution_context") if isinstance(datasets, dict) else None
    if not isinstance(contexts, list) or len(contexts) != 1 or not isinstance(contexts[0], dict):
        return None
    value = contexts[0].get("observed_at")
    try:
        return parse_time(value, "receipt.execution_context.observed_at")
    except EvidenceError:
        return None


def _validate_live_receipt_envelope(
    receipt: dict[str, Any],
    collector_surface: str,
    template_name: str,
    data: dict[str, Any],
    issues: list[str],
) -> dict[str, Any] | None:
    if receipt.get("schema_version") != "2":
        issues.append("schema_version is not 2")
    if receipt.get("collection_mode") != "live-cli":
        issues.append("collection_mode is not live-cli")
    try:
        started = parse_time(receipt.get("collection_started_at"), "receipt.collection_started_at")
        completed = parse_time(receipt.get("collection_completed_at"), "receipt.collection_completed_at")
        collected = parse_time(receipt.get("collected_at"), "receipt.collected_at")
        if started > completed:
            issues.append("collection_started_at is after collection_completed_at")
        if (completed - started).total_seconds() > MAX_COLLECTION_INTERVAL_SECONDS:
            issues.append("collection interval exceeds the 120-second contract")
        if collected < started or collected > completed:
            issues.append("collected_at lies outside the collection interval")
        real_now = datetime.now(timezone.utc)
        if completed > real_now or (real_now - completed).total_seconds() > MAX_RECEIPT_AGE_SECONDS:
            issues.append("collection receipt is stale or from the future")
    except EvidenceError:
        started = completed = None
        issues.append("collection interval is invalid")

    datasets = receipt.get("datasets")
    contexts = datasets.get("execution_context") if isinstance(datasets, dict) else None
    context: dict[str, Any] | None = None
    if not isinstance(contexts, list) or len(contexts) != 1 or not isinstance(contexts[0], dict):
        issues.append("exactly one execution_context row is required")
    else:
        context = contexts[0]
        if set(context) != CONTEXT_FIELDS:
            issues.append("execution_context fields do not match the reviewed cost context")
        for field in CONTEXT_HASH_FIELDS:
            if not isinstance(context.get(field), str) or not HEX64_RE.fullmatch(context[field]):
                issues.append(f"execution_context.{field} is not a SHA-256 hex digest")
        if context.get("primary_role_type") not in {"ROLE", "APPLICATION_INSTANCE"}:
            issues.append("execution_context.primary_role_type is unsupported")
        if context.get("session_timezone") != "UTC":
            issues.append("execution_context.session_timezone is not UTC")
        try:
            observed = parse_time(context.get("observed_at"), "execution_context.observed_at")
            if started is None or completed is None or observed < started or observed > completed:
                issues.append("execution_context.observed_at lies outside the collection interval")
        except EvidenceError:
            issues.append("execution_context.observed_at is invalid")

    metadata = data.get("metadata", {})
    selector = (
        {
            "window_start": metadata.get("window_start"),
            "window_end": metadata.get("window_end"),
        }
        if collector_surface in COST_HISTORY_COLLECTOR_SURFACES
        else {}
    )
    source_metadata = receipt.get("source_metadata")
    if not isinstance(source_metadata, dict):
        issues.append("source_metadata is not an object")
        source_metadata = {}
    if source_metadata.get("template") != template_name:
        issues.append(f"source_metadata.template is not {template_name}")
    if source_metadata.get("selector") != {name: True for name in selector}:
        issues.append("source_metadata.selector does not match the required cost window")

    template_path = Path(__file__).resolve().parent / "sql" / template_name
    if not template_path.is_file():
        issues.append(f"reviewed SQL template is missing: {template_name}")
        return context
    template_bytes = template_path.read_bytes()
    template_hash = f"sha256:{hashlib.sha256(template_bytes).hexdigest()}"
    rendered = template_bytes.decode("utf-8")
    for name, value in selector.items():
        if not isinstance(value, str):
            issues.append(f"metadata.{name} is missing")
            continue
        rendered = rendered.replace(f"__{name.upper()}_UTC__", value)
    rendered_hash = f"sha256:{hashlib.sha256(rendered.encode('utf-8')).hexdigest()}"
    expected_selector_hash = f"sha256:{hashlib.sha256(_canonical_json(selector)).hexdigest()}" if selector else None
    if receipt.get("sql_sha256") != template_hash or receipt.get("template_sha256") != template_hash:
        issues.append("template hash does not match the reviewed cost SQL")
    if receipt.get("rendered_sql_sha256") != rendered_hash:
        issues.append("rendered_sql_sha256 does not match the bounded cost SQL")
    if receipt.get("selector_fingerprint") != expected_selector_hash:
        issues.append("selector_fingerprint does not match the requested cost window")
    return context


def validate_collector_receipt(
    data: dict[str, Any],
    warnings: list[str],
    evaluation_time: datetime,
    input_trusted: bool,
) -> dict[str, Any]:
    receipt = data.get("collector_receipt")
    if receipt is None:
        issue = "collector receipt not supplied; provenance and completeness are not verified"
        warnings.append(issue)
        return {"status": "not_supplied", "complete": False, "issues": [issue]}
    issues: list[str] = []
    if not isinstance(receipt, dict):
        issues.append("collector_receipt is not an object")
        receipt = {}
    context = _validate_live_receipt_envelope(receipt, "cost", "cost.sql", data, issues)
    if receipt.get("surface") != "cost":
        issues.append("surface is not cost")
    if receipt.get("status") != "collected":
        issues.append(f"status is {receipt.get('status')!r}")
    if receipt.get("errors"):
        issues.append("collector reported an error")
    if not isinstance(receipt.get("connection_profile_sha256"), str) or not DIGEST_RE.fullmatch(
        receipt["connection_profile_sha256"]
    ):
        issues.append("connection_profile_sha256 is missing or invalid")
    if receipt.get("connection_profile") is not None:
        issues.append("raw connection_profile is not accepted")
    try:
        receipt_time = parse_time(receipt.get("collected_at"), "collector_receipt.collected_at")
        if receipt_time > evaluation_time or receipt_time > datetime.now(timezone.utc):
            issues.append("collected_at is after the report evaluation time or in the future")
    except EvidenceError:
        issues.append("collected_at is invalid")
    if receipt.get("source_views") != EXPECTED_COLLECTOR_SOURCES:
        issues.append("source_views do not match the reviewed cost SQL")
    supplied_receipt_hash = receipt.get("receipt_sha256")
    body = dict(receipt)
    body.pop("receipt_sha256", None)
    expected_receipt_hash = f"sha256:{hashlib.sha256(_canonical_json(body)).hexdigest()}"
    if supplied_receipt_hash != expected_receipt_hash:
        issues.append("receipt_sha256 is missing or invalid")
    datasets = receipt.get("datasets")
    if not isinstance(datasets, dict):
        issues.append("datasets is not an object")
        datasets = {}
    if set(datasets) != set(BASELINE_RECEIPT_DATASETS):
        issues.append("datasets do not match the exact baseline cost contract")
    if receipt.get("expected_datasets") != list(BASELINE_RECEIPT_DATASETS):
        issues.append("expected_datasets do not match the exact baseline cost contract")
    expected_counts = {name: len(rows) for name, rows in datasets.items() if isinstance(rows, list)}
    if receipt.get("dataset_row_counts") != expected_counts:
        issues.append("dataset_row_counts do not match receipt datasets")
    expected_result_hash = f"sha256:{hashlib.sha256(_canonical_json(datasets)).hexdigest()}"
    if receipt.get("result_sha256") != expected_result_hash:
        issues.append("result_sha256 does not match normalized receipt datasets")
    if receipt.get("snowflake_query_id") is not None:
        issues.append("snowflake_query_id is not emitted by the reviewed Snow CLI transport")
    if receipt.get("snowflake_query_id_status") != "not_exposed_by_snow_cli_json_ext":
        issues.append("snowflake_query_id_status does not match the reviewed transport limitation")
    row_count = receipt.get("row_count")
    if not isinstance(row_count, int) or isinstance(row_count, bool) or row_count < 0:
        issues.append("row_count is invalid")
    elif row_count != sum(
        len(datasets.get(name, [])) for name in BASELINE_RECEIPT_DATASETS if isinstance(datasets.get(name, []), list)
    ):
        issues.append("row_count does not match receipt datasets")
    row_limit = receipt.get("row_limit")
    reviewed_row_limit = _reviewed_row_limit("cost.sql", "cost")
    if row_limit != reviewed_row_limit or isinstance(row_limit, bool):
        issues.append(f"row_limit does not match the reviewed SQL cap {reviewed_row_limit}")
    elif any(len(datasets.get(name, [])) >= row_limit for name in RECEIPT_DATASETS):
        issues.append("one or more baseline datasets is at the SQL cap")
    if receipt.get("cap_scope") != "per_dataset":
        issues.append("cap_scope is not per_dataset")
    if receipt.get("truncation_possible") is not False:
        issues.append("truncation_possible is not false")
    for name in RECEIPT_DATASETS:
        source_rows = data.get(name, [])
        receipt_rows = datasets.get(name, [])
        if not _rows_match(source_rows, receipt_rows):
            issues.append(f"{name} rows do not match collector receipt")
    for issue in issues:
        warnings.append(f"collector receipt unverifiable: {issue}")
    if not issues and not input_trusted:
        warnings.append(
            "collector receipt is self-consistent but the enclosing evidence bundle has no trusted local digest"
        )
    return {
        "status": (
            "trusted_local_boundary"
            if not issues and input_trusted
            else "self_consistent_untrusted"
            if not issues
            else "unverifiable"
        ),
        "complete": not issues and input_trusted,
        "issues": sorted(set(issues)),
        "surface": receipt.get("surface"),
        "collection_completed_at": receipt.get("collection_completed_at"),
        "template_sha256": receipt.get("template_sha256"),
        "rendered_sql_sha256": receipt.get("rendered_sql_sha256"),
        "result_sha256": receipt.get("result_sha256"),
        "snowflake_query_id": receipt.get("snowflake_query_id"),
        "snowflake_query_id_status": receipt.get("snowflake_query_id_status"),
        "row_count": receipt.get("row_count"),
        "row_limit": receipt.get("row_limit"),
        "cap_scope": receipt.get("cap_scope"),
        "truncation_possible": receipt.get("truncation_possible"),
        "context": context,
    }


def _supplemental_input_rows(data: dict[str, Any], surface: str) -> list[dict[str, Any]]:
    if surface in SURFACE_ARRAYS:
        value = data.get(SURFACE_ARRAYS[surface], [])
    else:
        controls = data.get("controls_inventory", {})
        if not isinstance(controls, dict):
            raise EvidenceError("controls_inventory must be an object")
        value = controls.get(surface, [])
    if not isinstance(value, list) or not all(isinstance(row, dict) for row in value):
        raise EvidenceError(f"{surface} evidence must be an array of objects")
    return value


def _rows_match_receipt_projection(supplied: list[dict[str, Any]], receipt_rows: Any) -> bool:
    if not isinstance(receipt_rows, list) or not all(isinstance(row, dict) for row in receipt_rows):
        return False
    # Analyzer-consumed evidence must be byte-equivalent to the receipted rows.
    # Projecting to only receipt keys allowed callers to inject control coverage
    # fields that had never been observed by the reviewed SQL.
    return _rows_match(supplied, receipt_rows)


def validate_supplemental_receipts(
    data: dict[str, Any],
    expected_surfaces: tuple[str, ...],
    evaluation_time: datetime,
    findings: list[dict[str, str]],
    warnings: list[str],
    input_trusted: bool,
) -> dict[str, dict[str, Any]]:
    supplied = data.get("supplemental_receipts", {})
    if not isinstance(supplied, dict):
        raise EvidenceError("supplemental_receipts must be an object keyed by cost surface")
    unknown = sorted(set(supplied) - set(SUPPLEMENTAL_RECEIPT_SURFACES))
    if unknown:
        raise EvidenceError(f"supplemental_receipts contains unsupported surfaces: {', '.join(unknown)}")

    assessments: dict[str, dict[str, Any]] = {}
    for surface in sorted(set(expected_surfaces) & set(SUPPLEMENTAL_RECEIPT_SURFACES)):
        receipt = supplied.get(surface)
        if receipt is None:
            issue = "supplemental collector receipt not supplied"
            assessments[surface] = {"status": "not_supplied", "complete": False, "issues": [issue]}
            warnings.append(f"{surface}: {issue}")
            add_finding(
                findings,
                "COST_SURFACE_RECEIPT_INVALID",
                "error",
                surface,
                "The surface inventory is not bound to an exact reviewed collector receipt.",
            )
            continue
        if not isinstance(receipt, dict):
            issues = ["receipt is not an object"]
            receipt = {}
        else:
            issues = []

        collector_surface, dataset = SUPPLEMENTAL_RECEIPT_SURFACES[surface]
        template_name = f"{collector_surface}.sql"
        context = _validate_live_receipt_envelope(receipt, collector_surface, template_name, data, issues)
        if receipt.get("surface") != collector_surface:
            issues.append(f"surface is not {collector_surface}")
        if receipt.get("status") != "collected":
            issues.append("status is not collected")
        if receipt.get("errors"):
            issues.append("collector reported an error")
        if not isinstance(receipt.get("connection_profile_sha256"), str) or not DIGEST_RE.fullmatch(
            receipt["connection_profile_sha256"]
        ):
            issues.append("connection_profile_sha256 is missing or invalid")
        if receipt.get("connection_profile") is not None:
            issues.append("raw connection_profile is not accepted")
        if receipt.get("truncation_possible") is not False:
            issues.append("truncation_possible is not false")
        if receipt.get("source_views") != [EXPECTED_SURFACE_SOURCES[surface]]:
            issues.append("source_views do not match the reviewed supplemental SQL")
        try:
            receipt_time = parse_time(receipt.get("collected_at"), f"supplemental_receipts.{surface}.collected_at")
            if receipt_time > evaluation_time or receipt_time > datetime.now(timezone.utc):
                issues.append("collected_at is after the report evaluation time or in the future")
        except EvidenceError:
            issues.append("collected_at is invalid")

        datasets = receipt.get("datasets")
        if not isinstance(datasets, dict):
            issues.append("datasets is not an object")
            datasets = {}
        if set(datasets) != {dataset, "execution_context"}:
            issues.append("datasets do not match the exact supplemental cost contract")
        expected_datasets = receipt.get("expected_datasets")
        if not isinstance(expected_datasets, list) or set(expected_datasets) != {dataset, "execution_context"}:
            issues.append("expected_datasets do not match the exact supplemental cost contract")
        expected_counts = {name: len(rows) for name, rows in datasets.items() if isinstance(rows, list)}
        if receipt.get("dataset_row_counts") != expected_counts:
            issues.append("dataset_row_counts do not match receipt datasets")
        expected_result_hash = f"sha256:{hashlib.sha256(_canonical_json(datasets)).hexdigest()}"
        if receipt.get("result_sha256") != expected_result_hash:
            issues.append("result_sha256 does not match normalized receipt datasets")
        if receipt.get("snowflake_query_id") is not None:
            issues.append("snowflake_query_id is not emitted by the reviewed Snow CLI transport")
        if receipt.get("snowflake_query_id_status") != "not_exposed_by_snow_cli_json_ext":
            issues.append("snowflake_query_id_status does not match the reviewed transport limitation")
        receipt_rows = datasets.get(dataset, [])
        if not _rows_match_receipt_projection(_supplemental_input_rows(data, surface), receipt_rows):
            issues.append(f"{dataset} rows do not match the supplemental receipt")
        row_count = receipt.get("row_count")
        if not isinstance(row_count, int) or isinstance(row_count, bool) or row_count < 0:
            issues.append("row_count is invalid")
        elif row_count != sum(expected_counts.values()):
            issues.append("row_count does not match receipt rows")
        row_limit = receipt.get("row_limit")
        reviewed_row_limit = _reviewed_row_limit(template_name, collector_surface)
        if row_limit != reviewed_row_limit or isinstance(row_limit, bool):
            issues.append(f"row_limit does not match the reviewed SQL cap {reviewed_row_limit}")
        elif len(receipt_rows) >= row_limit:
            issues.append("supplemental dataset is at or above the SQL cap")
        if receipt.get("cap_scope") != "single_dataset_or_result":
            issues.append("cap_scope is not single_dataset_or_result")

        body = dict(receipt)
        supplied_hash = body.pop("receipt_sha256", None)
        expected_receipt_hash = f"sha256:{hashlib.sha256(_canonical_json(body)).hexdigest()}"
        if supplied_hash != expected_receipt_hash:
            issues.append("receipt_sha256 is missing or invalid")

        if not issues and not input_trusted:
            warnings.append(
                f"{surface}: receipt is self-consistent but the enclosing bundle has no trusted local digest"
            )
        status = (
            "trusted_local_boundary"
            if not issues and input_trusted
            else "self_consistent_untrusted"
            if not issues
            else "unverifiable"
        )
        assessments[surface] = {
            "status": status,
            "complete": not issues and input_trusted,
            "issues": issues,
            "context": context,
            "surface": collector_surface,
            "collection_completed_at": receipt.get("collection_completed_at"),
            "template_sha256": receipt.get("template_sha256"),
            "rendered_sql_sha256": receipt.get("rendered_sql_sha256"),
            "result_sha256": receipt.get("result_sha256"),
            "snowflake_query_id": receipt.get("snowflake_query_id"),
            "snowflake_query_id_status": receipt.get("snowflake_query_id_status"),
            "row_count": receipt.get("row_count"),
            "row_limit": receipt.get("row_limit"),
            "cap_scope": receipt.get("cap_scope"),
            "truncation_possible": receipt.get("truncation_possible"),
        }
        if issues:
            warnings.extend(f"{surface} receipt unverifiable: {issue}" for issue in issues)
            add_finding(
                findings,
                "COST_SURFACE_RECEIPT_INVALID",
                "error",
                surface,
                "The supplemental collector receipt is missing, altered, stale, truncated, or mismatched.",
            )
    return assessments


def enforce_context_consistency(
    baseline: dict[str, Any],
    supplemental: dict[str, dict[str, Any]],
    findings: list[dict[str, str]],
    warnings: list[str],
) -> bool:
    expected = baseline.get("context")
    mismatch = not isinstance(expected, dict)
    expected_identity = (
        {field: expected.get(field) for field in CONTEXT_IDENTITY_FIELDS} if isinstance(expected, dict) else None
    )
    for surface, assessment in supplemental.items():
        context = assessment.get("context")
        identity = (
            {field: context.get(field) for field in CONTEXT_IDENTITY_FIELDS} if isinstance(context, dict) else None
        )
        if identity != expected_identity:
            assessment["complete"] = False
            assessment["status"] = "unverifiable"
            assessment.setdefault("issues", []).append(
                "execution_context identity differs from the baseline cost receipt"
            )
            warnings.append(f"{surface}: execution context identity differs from the baseline cost receipt")
            mismatch = True
    if mismatch:
        baseline["complete"] = False
        baseline["status"] = "unverifiable"
        baseline.setdefault("issues", []).append("cost receipt execution contexts are missing or inconsistent")
        add_finding(
            findings,
            "COST_SURFACE_RECEIPT_INVALID",
            "error",
            "execution_context",
            "All cost receipts must carry one identical account, user, role-set, and UTC context; "
            "each statement keeps its own independently validated observation time.",
        )
    return not mismatch


def reject_secret_fields(value: Any, path: str = "input") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = re.sub(r"[^a-z0-9]", "", str(key).casefold())
            if normalized in {
                "querytag",
                "username",
                "userid",
                "queryid",
                "warehousename",
                "computepoolname",
                "modelname",
            }:
                raise EvidenceError(
                    f"raw identity/tag field is not accepted: {path}.{key}; use an organization-and-account-scoped Snowflake-side hash"
                )
            if normalized in {"querytext", "sqltext", "rawrows", "presignedurl"}:
                raise EvidenceError(f"raw or sensitive evidence field is not accepted: {path}.{key}")
            if any(
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
                raise EvidenceError(f"credential-bearing field is not accepted: {path}.{key}")
            reject_secret_fields(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            reject_secret_fields(child, f"{path}[{index}]")
    elif isinstance(value, str):
        parsed = urlsplit(value.strip())
        if parsed.scheme in {"http", "https"} and (
            parsed.query or parsed.fragment or parsed.username or parsed.password
        ):
            raise EvidenceError(f"URL-bearing evidence is not accepted at {path}")


def safe_text(value: Any, field: str, *, required: bool = True) -> str:
    if not isinstance(value, str) or (required and not value.strip()):
        raise EvidenceError(f"{field} must be a non-empty string")
    text = value.strip()
    if len(text) > 256 or any(char in text for char in ("\n", "\r", "|", "`")):
        raise EvidenceError(f"{field} contains unsafe report text")
    parsed = urlsplit(text)
    if parsed.scheme and (parsed.username or parsed.password or parsed.query or parsed.fragment):
        raise EvidenceError(f"{field} URL must not contain userinfo, query, or fragment data")
    return text


def decimal_value(value: Any, field: str) -> Decimal:
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise EvidenceError(f"{field} must be a finite non-negative number") from exc
    if not number.is_finite() or number < 0:
        raise EvidenceError(f"{field} must be a finite non-negative number")
    return number


def parse_time(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise EvidenceError(f"{field} must be an ISO-8601 timestamp")
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise EvidenceError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise EvidenceError(f"{field} must include a timezone")
    return parsed.astimezone(timezone.utc)


def as_text(number: Decimal) -> str:
    normalized = number.quantize(Decimal("0.000001")).normalize()
    return format(normalized, "f")


def add_finding(
    findings: list[dict[str, str]],
    code: str,
    severity: str,
    surface: str,
    message: str,
) -> None:
    findings.append(
        {
            "code": code,
            "severity": severity,
            "surface": surface,
            "message": safe_text(message, f"finding.{code}.message"),
        }
    )


def ledger_entry(
    *,
    entry_id: str,
    domain: str,
    source: str,
    role: str,
    unit: str,
    amount: Decimal,
    parent_id: str | None,
    overlap_key: str,
    freshness_status: str,
    availability_status: str,
    invoice_status: str = "not_reconciled",
    finality_status: str = "settled",
) -> dict[str, Any]:
    if role not in LEDGER_ROLES:
        raise EvidenceError(f"unsupported ledger role: {role}")
    if invoice_status not in INVOICE_STATUSES:
        raise EvidenceError(f"unsupported invoice reconciliation status: {invoice_status}")
    return {
        "entry_id": safe_text(entry_id, "ledger.entry_id"),
        "domain": safe_text(domain, "ledger.domain"),
        "source": safe_text(source, "ledger.source"),
        "ledger_role": role,
        "unit": safe_text(unit, "ledger.unit"),
        "amount": as_text(amount),
        "parent_id": parent_id,
        "overlap_key": safe_text(overlap_key, "ledger.overlap_key"),
        "aggregation_eligible": role == "total" and finality_status == "settled",
        "freshness_status": safe_text(freshness_status, "ledger.freshness_status"),
        "availability_status": safe_text(availability_status, "ledger.availability_status"),
        "invoice_reconciliation": invoice_status,
        "finality_status": safe_text(finality_status, "ledger.finality_status"),
    }


def sum_field(rows: list[dict[str, Any]], field: str, prefix: str) -> Decimal:
    total = Decimal("0")
    for index, row in enumerate(rows):
        if field not in row or row[field] is None:
            raise EvidenceError(f"{prefix}[{index}].{field} is required")
        total += decimal_value(row[field], f"{prefix}[{index}].{field}")
    return total


def sum_nullable_zero(rows: list[dict[str, Any]], field: str, prefix: str) -> Decimal:
    """Sum a field whose provider contract defines NULL as zero, not missing."""

    total = Decimal("0")
    for index, row in enumerate(rows):
        if field not in row:
            raise EvidenceError(f"{prefix}[{index}].{field} is required")
        if row[field] is not None:
            total += decimal_value(row[field], f"{prefix}[{index}].{field}")
    return total


def validate_window(data: dict[str, Any]) -> tuple[datetime, datetime, datetime]:
    metadata = data.get("metadata")
    if not isinstance(metadata, dict):
        raise EvidenceError("metadata must be an object")
    start = parse_time(metadata.get("window_start"), "metadata.window_start")
    end = parse_time(metadata.get("window_end"), "metadata.window_end")
    generated = parse_time(metadata.get("generated_at"), "metadata.generated_at")
    if start >= end:
        raise EvidenceError("metadata.window_start must be before metadata.window_end")
    if end - start > MAX_COST_WINDOW:
        raise EvidenceError("cost analysis windows cannot exceed seven days; partition longer audits")
    if generated < end:
        raise EvidenceError("metadata.generated_at cannot precede metadata.window_end")
    if generated > datetime.now(timezone.utc):
        raise EvidenceError("metadata.generated_at cannot be in the future")
    disclosure_authorized = metadata.get("identity_disclosure_authorized")
    if not isinstance(disclosure_authorized, bool):
        raise EvidenceError("metadata.identity_disclosure_authorized must be explicitly true or false")
    identity_fields = ("account", "role", "review_owner", "approval_boundary")
    if disclosure_authorized:
        safe_text(
            metadata.get("identity_disclosure_authority"),
            "metadata.identity_disclosure_authority",
        )
        for field in identity_fields:
            safe_text(metadata.get(field), f"metadata.{field}")
    else:
        if metadata.get("identity_disclosure_authority") is not None:
            raise EvidenceError("metadata.identity_disclosure_authority is allowed only when disclosure is authorized")
        for field in identity_fields:
            validate_sha256_hex(metadata.get(field), f"metadata.{field}")
    return start, end, generated


def validate_rows(data: dict[str, Any], key: str) -> list[dict[str, Any]]:
    rows = data.get(key, [])
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise EvidenceError(f"{key} must be an array of objects")
    return rows


def validate_expected_surfaces(metadata: dict[str, Any]) -> tuple[str, ...]:
    supplied = metadata.get("expected_surfaces", list(EXPECTED_COST_SURFACES))
    if not isinstance(supplied, list) or not supplied or not all(isinstance(item, str) for item in supplied):
        raise EvidenceError("metadata.expected_surfaces must be a non-empty array of surface names")
    normalized = tuple(sorted(set(supplied)))
    unknown = sorted(set(normalized) - set(EXPECTED_COST_SURFACES))
    if unknown:
        raise EvidenceError(f"metadata.expected_surfaces contains unsupported surfaces: {', '.join(unknown)}")
    required = tuple(sorted(EXPECTED_COST_SURFACES))
    if normalized != required:
        missing = sorted(set(required) - set(normalized))
        raise EvidenceError(
            f"metadata.expected_surfaces cannot narrow the full cost-audit denominator; missing: {', '.join(missing)}"
        )
    return required


def assess_surface_inventory(
    data: dict[str, Any],
    generated: datetime,
    window_end: datetime,
    collection_times: dict[str, datetime],
    expected: tuple[str, ...],
    findings: list[dict[str, str]],
    warnings: list[str],
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    supplied = data.get("surface_inventory", [])
    if not isinstance(supplied, list) or not all(isinstance(row, dict) for row in supplied):
        raise EvidenceError("surface_inventory must be an array of objects")
    by_surface: dict[str, dict[str, Any]] = {}
    assessed: list[dict[str, Any]] = []
    for index, row in enumerate(supplied):
        prefix = f"surface_inventory[{index}]"
        surface = safe_text(row.get("surface"), f"{prefix}.surface")
        if surface not in EXPECTED_COST_SURFACES:
            raise EvidenceError(f"{prefix}.surface is unsupported: {surface}")
        if surface in by_surface:
            raise EvidenceError(f"duplicate surface_inventory entry: {surface}")
        status = safe_text(row.get("status"), f"{prefix}.status")
        if status not in SURFACE_STATUSES:
            raise EvidenceError(f"{prefix}.status is unsupported: {status}")
        privilege = safe_text(row.get("privilege_status", "unknown"), f"{prefix}.privilege_status")
        if privilege not in {"verified", "error", "unknown"}:
            raise EvidenceError(f"{prefix}.privilege_status is unsupported: {privilege}")
        source = safe_text(row.get("source", surface), f"{prefix}.source")
        if source != EXPECTED_SURFACE_SOURCES[surface]:
            raise EvidenceError(f"{prefix}.source does not match the reviewed source for {surface}")
        truncated = row.get("truncated", False)
        if not isinstance(truncated, bool):
            raise EvidenceError(f"{prefix}.truncated must be boolean")
        latest: datetime | None = None
        observed_age: Decimal | None = None
        documented_latency = SURFACE_LATENCY_HOURS[surface]
        freshness_status = "unknown"
        if row.get("documented_latency_hours") is not None:
            supplied_latency = decimal_value(row["documented_latency_hours"], f"{prefix}.documented_latency_hours")
            if supplied_latency != documented_latency:
                raise EvidenceError(
                    f"{prefix}.documented_latency_hours must match the code-owned "
                    f"{LATENCY_CONTRACT_VERSION} value {as_text(documented_latency)}"
                )
        if row.get("latest_timestamp") is not None:
            latest = parse_time(row["latest_timestamp"], f"{prefix}.latest_timestamp")
            if latest > generated:
                raise EvidenceError(f"{prefix}.latest_timestamp cannot be after metadata.generated_at")
            observed_age = Decimal(str((generated - latest).total_seconds())) / Decimal("3600")
        collection_time = collection_times.get(surface)
        settlement_lag = (
            Decimal(str((collection_time - window_end).total_seconds())) / Decimal("3600")
            if collection_time is not None
            else None
        )
        if status == "available":
            if collection_time is None:
                freshness_status = "unverified_collection_time"
                add_finding(
                    findings,
                    "COST_SURFACE_STALE",
                    "warning",
                    surface,
                    "No independently receipted collection time is available for the surface.",
                )
            elif surface in {"resource_monitors", "budgets"}:
                freshness_status = "current_role_scoped_observation"
            elif settlement_lag is not None and settlement_lag >= documented_latency:
                freshness_status = "settled_window"
            else:
                freshness_status = "unsettled_window"
                add_finding(
                    findings,
                    "COST_SURFACE_STALE",
                    "warning",
                    surface,
                    f"Collection occurred {as_text(settlement_lag or Decimal('0'))} hours after window end; "
                    f"the code-owned source delay is {as_text(documented_latency)} hours.",
                )
        if status != "available":
            code = (
                "COST_ADAPTIVE_REGION_UNAVAILABLE"
                if surface == "adaptive_usage" and status == "region_unavailable"
                else "COST_SURFACE_MISSING"
            )
            add_finding(
                findings, code, "warning", surface, f"Surface availability is {status}; absence is not zero usage."
            )
        if privilege == "error":
            add_finding(
                findings,
                "COST_SURFACE_MISSING",
                "warning",
                surface,
                "The approved role could not verify this surface; no privilege escalation was attempted.",
            )
        if truncated:
            add_finding(
                findings,
                "COST_SURFACE_TRUNCATED",
                "error",
                surface,
                "The surface reached its collection cap and cannot support completeness claims.",
            )
        settled_cutoff = (
            collection_time - timedelta(seconds=float(documented_latency * Decimal("3600")))
            if collection_time is not None
            else None
        )
        assessed_row = {
            "surface": surface,
            "source": source,
            "status": status,
            "privilege_status": privilege,
            "freshness_status": freshness_status,
            "latest_timestamp": latest.isoformat() if latest else None,
            "documented_latency_hours": as_text(documented_latency),
            "settled_cutoff": settled_cutoff.isoformat() if settled_cutoff else None,
            "window_end_precedes_settled_cutoff": (window_end <= settled_cutoff if settled_cutoff else None),
            "latency_contract_version": LATENCY_CONTRACT_VERSION,
            "observed_age_hours": as_text(observed_age) if observed_age is not None else None,
            "collection_time": collection_time.isoformat() if collection_time else None,
            "settlement_observed_at": collection_time.isoformat() if collection_time else None,
            "settlement_lag_hours": as_text(settlement_lag) if settlement_lag is not None else None,
            "truncated": truncated,
        }
        assessed.append(assessed_row)
        by_surface[surface] = assessed_row
    for surface in expected:
        if surface in by_surface:
            continue
        rows = data.get(SURFACE_ARRAYS.get(surface, ""), [])
        inferred = "available_unverified" if isinstance(rows, list) and rows else "not_supplied"
        assessed_row = {
            "surface": surface,
            "source": EXPECTED_SURFACE_SOURCES[surface],
            "status": inferred,
            "privilege_status": "unknown",
            "freshness_status": "unknown",
            "latest_timestamp": None,
            "documented_latency_hours": as_text(SURFACE_LATENCY_HOURS[surface]),
            "settled_cutoff": None,
            "window_end_precedes_settled_cutoff": None,
            "latency_contract_version": LATENCY_CONTRACT_VERSION,
            "observed_age_hours": None,
            "collection_time": None,
            "settlement_observed_at": None,
            "settlement_lag_hours": None,
            "truncated": False,
        }
        assessed.append(assessed_row)
        by_surface[surface] = assessed_row
        add_finding(
            findings,
            "COST_SURFACE_MISSING",
            "warning",
            surface,
            "No explicit availability and freshness receipt was supplied for this expected surface.",
        )
        warnings.append(f"{surface}: explicit surface inventory receipt not supplied")
    return sorted(assessed, key=lambda row: row["surface"]), by_surface


def surface_state(inventory: dict[str, dict[str, Any]], surface: str) -> tuple[str, str]:
    item = inventory.get(surface, {})
    return str(item.get("freshness_status", "unknown")), str(item.get("status", "not_supplied"))


def rows_in_window(
    rows: list[dict[str, Any]],
    key: str,
    window_start: datetime,
    window_end: datetime,
    warnings: list[str],
    findings: list[dict[str, str]],
) -> list[dict[str, Any]]:
    """Keep only complete source intervals inside the requested half-open window."""
    selected: list[dict[str, Any]] = []
    excluded = 0
    for index, row in enumerate(rows):
        prefix = f"{key}[{index}]"
        if row.get("start_time") is None or row.get("end_time") is None:
            raise EvidenceError(f"{prefix}.start_time and end_time are required for window filtering")
        row_start = parse_time(row["start_time"], f"{prefix}.start_time")
        row_end = parse_time(row["end_time"], f"{prefix}.end_time")
        if row_start >= row_end:
            raise EvidenceError(f"{prefix}.start_time must be before end_time")
        if row_start < window_start or row_end > window_end:
            excluded += 1
            continue
        selected.append(row)
    if excluded:
        message = f"{key}: excluded {excluded} row(s) not wholly contained in the requested half-open window"
        warnings.append(message)
        add_finding(
            findings,
            "COST_WINDOW_COVERAGE_GAP",
            "error",
            key,
            "One or more collected source intervals crossed or fell outside the requested window; "
            "totals are withheld because full-window coverage is not proven.",
        )
    return selected


def ensure_unique_rows(rows: list[dict[str, Any]], surface: str, key_fields: tuple[str, ...]) -> None:
    seen: set[bytes] = set()
    for index, row in enumerate(rows):
        encoded = _canonical_json({field: row.get(field) for field in key_fields})
        if encoded in seen:
            raise EvidenceError(f"{surface}[{index}] duplicates natural source key fields {', '.join(key_fields)}")
        seen.add(encoded)


def _optional_number(value: Any, field: str) -> Decimal | None:
    if value is None:
        return None
    return decimal_value(value, field)


def attribution_completeness(warehouses: list[dict[str, Any]], warnings: list[str]) -> list[dict[str, str]]:
    """Show how much metered compute can be reconciled to query attribution.

    A NULL attribution value is an unknown boundary (for example, an adaptive
    workload), not zero.  Grouping by warehouse ID when present avoids merging
    renamed warehouses that happen to share a display name.
    """
    grouped: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(warehouses):
        name = warehouse_label(row, f"warehouse_metering[{index}]")
        key = str(row.get("warehouse_id") or name)
        item = grouped.setdefault(
            key, {"warehouse_name": name, "compute": Decimal("0"), "attributed": Decimal("0"), "unknown": False}
        )
        item["compute"] += decimal_value(
            row.get("credits_used_compute", 0), f"warehouse_metering[{index}].credits_used_compute"
        )
        attributed = row.get("credits_attributed_compute_queries")
        if attributed is None:
            item["unknown"] = True
        else:
            item["attributed"] += decimal_value(
                attributed, f"warehouse_metering[{index}].credits_attributed_compute_queries"
            )
    result: list[dict[str, str]] = []
    for item in grouped.values():
        compute = item["compute"]
        attributed = item["attributed"]
        if item["unknown"]:
            result.append(
                {
                    "warehouse_name": item["warehouse_name"],
                    "status": "unknown",
                    "compute_credits": as_text(compute),
                    "attributed_query_credits": as_text(attributed),
                    "attribution_fraction": "unknown",
                    "unattributed_credits": "unknown",
                    "reason": "one or more metering rows has NULL query attribution",
                }
            )
            continue
        if attributed > compute:
            warnings.append(
                f"{item['warehouse_name']}: attributed credits exceed metered compute; completeness is inconclusive"
            )
            result.append(
                {
                    "warehouse_name": item["warehouse_name"],
                    "status": "inconclusive",
                    "compute_credits": as_text(compute),
                    "attributed_query_credits": as_text(attributed),
                    "attribution_fraction": "inconclusive",
                    "unattributed_credits": "inconclusive",
                    "reason": "attributed credits exceed aligned metering",
                }
            )
            continue
        fraction = attributed / compute if compute else Decimal("0")
        result.append(
            {
                "warehouse_name": item["warehouse_name"],
                "status": "measured",
                "compute_credits": as_text(compute),
                "attributed_query_credits": as_text(attributed),
                "attribution_fraction": as_text(fraction),
                "unattributed_credits": as_text(compute - attributed),
                "reason": "aligned WAREHOUSE_METERING_HISTORY rows",
            }
        )
    return sorted(result, key=lambda item: item["warehouse_name"])


def cost_latency_pareto(queries: list[dict[str, Any]], warnings: list[str]) -> list[dict[str, str | int | bool]]:
    """Return non-dominated query fingerprints for cost/latency review."""
    groups: dict[tuple[str, str], dict[str, Any]] = {}
    for index, row in enumerate(queries):
        fingerprint = row.get("query_parameterized_hash") or row.get("query_hash") or row.get("query_id_sha256")
        elapsed = _optional_number(
            row.get("total_elapsed_time_ms"), f"query_attribution[{index}].total_elapsed_time_ms"
        )
        credits = decimal_value(
            row.get("credits_attributed_compute", 0), f"query_attribution[{index}].credits_attributed_compute"
        )
        if fingerprint is None or elapsed is None:
            continue
        key = (
            warehouse_label(row, f"query_attribution[{index}]"),
            validate_hash(fingerprint, f"query_attribution[{index}].query_fingerprint"),
        )
        item = groups.setdefault(
            key,
            {
                "warehouse_name": key[0],
                "fingerprint": key[1],
                "credits": Decimal("0"),
                "elapsed": Decimal("0"),
                "count": 0,
            },
        )
        item["credits"] += credits
        item["elapsed"] += elapsed
        item["count"] += 1
    if not groups and queries:
        warnings.append(
            "cost/latency Pareto unavailable: query attribution rows lack a query fingerprint or elapsed time"
        )
    candidates = list(groups.values())
    result: list[dict[str, str | int | bool]] = []
    for candidate in candidates:
        average = candidate["elapsed"] / candidate["count"]
        dominated = any(
            other is not candidate
            and other["credits"] <= candidate["credits"]
            and other["elapsed"] / other["count"] <= average
            and (other["credits"] < candidate["credits"] or other["elapsed"] / other["count"] < average)
            for other in candidates
        )
        result.append(
            {
                "warehouse_name": candidate["warehouse_name"],
                "fingerprint": candidate["fingerprint"],
                "query_count": candidate["count"],
                "credits": as_text(candidate["credits"]),
                "average_elapsed_time_ms": as_text(average),
                "pareto_efficient": not dominated,
            }
        )
    return sorted(
        result,
        key=lambda item: (not bool(item["pareto_efficient"]), str(item["warehouse_name"]), str(item["fingerprint"])),
    )


def right_sizing_boundary(metadata: dict[str, Any], warnings: list[str]) -> dict[str, Any]:
    request = metadata.get("right_sizing")
    base = {
        "status": "not_requested",
        "warehouse": None,
        "current_size": None,
        "candidate_sizes": [],
        "max_size_steps": None,
        "success_criteria": None,
        "measurement_window": None,
        "rollback": None,
        "owner": metadata.get("review_owner"),
        "approval": metadata.get("approval_boundary"),
        "mutation_executed": False,
    }
    if request is None:
        return base
    if not isinstance(request, dict):
        raise EvidenceError("metadata.right_sizing must be an object")
    for field in ("warehouse", "current_size", "success_criteria", "measurement_window"):
        if field in request and request[field] is not None:
            base[field] = safe_text(request[field], f"metadata.right_sizing.{field}")
    candidates = request.get("candidate_sizes", [])
    if not isinstance(candidates, list) or not all(isinstance(value, str) and value.strip() for value in candidates):
        raise EvidenceError("metadata.right_sizing.candidate_sizes must be an array of names")
    base["candidate_sizes"] = [safe_text(value, "metadata.right_sizing.candidate_sizes") for value in candidates]
    if base["current_size"] and base["current_size"] not in WAREHOUSE_SIZES:
        raise EvidenceError("metadata.right_sizing.current_size is not a supported Snowflake warehouse size")
    if any(value not in WAREHOUSE_SIZES for value in base["candidate_sizes"]):
        raise EvidenceError("metadata.right_sizing.candidate_sizes contains an unsupported warehouse size")
    if base["current_size"] in base["candidate_sizes"]:
        raise EvidenceError("right-sizing candidates must differ from the current warehouse size")
    if request.get("max_size_steps") is not None:
        steps = decimal_value(request["max_size_steps"], "metadata.right_sizing.max_size_steps")
        if steps != steps.to_integral_value():
            raise EvidenceError("metadata.right_sizing.max_size_steps must be an integer")
        base["max_size_steps"] = int(steps)
        if base["max_size_steps"] <= 0:
            raise EvidenceError("metadata.right_sizing.max_size_steps must be positive")
    rollback = request.get("rollback")
    if rollback is not None:
        if not isinstance(rollback, dict):
            raise EvidenceError("metadata.right_sizing.rollback must be an object")
        rollback_size = safe_text(rollback.get("warehouse_size"), "metadata.right_sizing.rollback.warehouse_size")
        thresholds = rollback.get("thresholds")
        if not isinstance(thresholds, dict) or not thresholds:
            raise EvidenceError("metadata.right_sizing.rollback.thresholds must be a non-empty object")
        if set(thresholds) != ROLLBACK_THRESHOLD_KEYS:
            raise EvidenceError(
                "metadata.right_sizing.rollback.thresholds must contain exactly "
                "max_p95_latency_regression_pct and max_queue_regression_pct"
            )
        normalized_thresholds: dict[str, str] = {}
        for name, value in sorted(thresholds.items()):
            normalized_name = safe_text(name, "metadata.right_sizing.rollback.thresholds key")
            normalized_thresholds[normalized_name] = as_text(
                decimal_value(value, f"metadata.right_sizing.rollback.thresholds.{normalized_name}")
            )
        base["rollback"] = {
            "warehouse_size": rollback_size,
            "thresholds": normalized_thresholds,
            "automatic_execution": False,
        }
        if base["current_size"] and rollback_size != base["current_size"]:
            raise EvidenceError("rollback warehouse_size must restore the current warehouse size")
    if (
        not base["warehouse"]
        or not base["current_size"]
        or not base["candidate_sizes"]
        or not base["success_criteria"]
        or not base["measurement_window"]
        or base["rollback"] is None
    ):
        warnings.append(
            "right-sizing request is bounded only when warehouse, current size, candidates, measurement window, success criteria, and explicit rollback thresholds are supplied"
        )
        base["status"] = "incomplete"
    else:
        if base["max_size_steps"] is None:
            warnings.append(
                "right-sizing candidates supplied without max_size_steps; bounded review requires an explicit step limit"
            )
            base["status"] = "incomplete"
        else:
            current_index = WAREHOUSE_SIZES.index(str(base["current_size"]))
            if any(
                abs(WAREHOUSE_SIZES.index(candidate) - current_index) > base["max_size_steps"]
                for candidate in base["candidate_sizes"]
            ):
                raise EvidenceError("right-sizing candidate exceeds max_size_steps from current_size")
            base["status"] = "bounded_proposal"
    return base


def freshness(
    data: dict[str, Any], generated: datetime, window_end: datetime
) -> tuple[list[dict[str, str]], list[str]]:
    source_times = data.get("source_max_times", {})
    if not isinstance(source_times, dict):
        raise EvidenceError("source_max_times must be an object")
    results: list[dict[str, str]] = []
    warnings: list[str] = []
    for source in ("warehouse_metering", "query_attribution", "warehouse_load", "serverless_usage"):
        if source not in source_times:
            rows = data.get(source, [])
            if isinstance(rows, list) and rows:
                raise EvidenceError(f"source_max_times.{source} is required when {source} contains rows")
            warnings.append(f"{source}: maximum source timestamp not supplied; freshness unknown")
            continue
        maximum = parse_time(source_times[source], f"source_max_times.{source}")
        if maximum > generated:
            raise EvidenceError(f"source_max_times.{source} cannot be later than metadata.generated_at")
        if maximum < window_end:
            warnings.append(f"{source}: maximum source timestamp precedes window_end; coverage is partial")
        age_seconds = Decimal(str((generated - maximum).total_seconds()))
        results.append(
            {
                "source": source,
                "max_timestamp": maximum.isoformat(),
                "observed_age_seconds": as_text(age_seconds),
            }
        )
    return results, warnings


def rate_estimate(
    credits: Decimal,
    rate_key: str,
    rates: dict[str, Any],
    warnings: list[str],
) -> dict[str, str] | None:
    if credits == 0 or rate_key not in rates:
        return None
    rate = rates[rate_key]
    if not isinstance(rate, dict):
        raise EvidenceError(f"credit_rates.{rate_key} must be an object")
    unit_price = decimal_value(rate.get("unit_price"), f"credit_rates.{rate_key}.unit_price")
    currency = rate.get("currency")
    provenance = rate.get("provenance")
    currency = safe_text(currency, f"credit_rates.{rate_key}.currency")
    provenance = safe_text(provenance, f"credit_rates.{rate_key}.provenance")
    effective_period = (
        safe_text(
            rate.get("effective_period"),
            f"credit_rates.{rate_key}.effective_period",
        )
        if rate.get("effective_period") is not None
        else "not_supplied"
    )
    if "invoice_reconciled" in rate:
        raise EvidenceError(
            f"credit_rates.{rate_key}.invoice_reconciled is not accepted; a rate row cannot prove usage reconciliation"
        )
    warnings.append(f"{rate_key}: currency conversion is estimated and not reconciled to an invoice")
    return {
        "basis": rate_key,
        "credits": as_text(credits),
        "unit_price": as_text(unit_price),
        "currency": currency,
        "amount": as_text(credits * unit_price),
        "provenance": provenance,
        "classification": "estimated",
        "invoice_reconciliation": "not_reconciled",
        "effective_period": effective_period,
    }


def _sum_optional(rows: list[dict[str, Any]], field: str, prefix: str) -> Decimal:
    total = Decimal("0")
    for index, row in enumerate(rows):
        if row.get(field) is not None:
            total += decimal_value(row[field], f"{prefix}[{index}].{field}")
    return total


def validate_additional_rows(
    data: dict[str, Any],
    start: datetime,
    end: datetime,
    generated: datetime,
    warnings: list[str],
    findings: list[dict[str, str]],
) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for name in (
        "adaptive_usage",
        "storage_usage",
        "data_transfer_usage",
        "internal_transfer_usage",
        "ai_usage",
        "invoice_usage",
    ):
        rows = validate_rows(data, name)
        for index, row in enumerate(rows):
            if "unit" in row:
                raise EvidenceError(
                    f"{name}[{index}].unit is not accepted; ledger units are fixed by the reviewed source contract"
                )
            if name == "adaptive_usage":
                validate_tag_indicator(row, f"adaptive_usage[{index}]")
                validate_sha256_hex(
                    row.get("query_id_sha256"),
                    f"adaptive_usage[{index}].query_id_sha256",
                )
                warehouse_label(row, f"adaptive_usage[{index}]")
                if row.get("user_name_sha256") is not None:
                    validate_sha256_hex(
                        row["user_name_sha256"],
                        f"adaptive_usage[{index}].user_name_sha256",
                    )
                for field in ("query_hash", "query_parameterized_hash"):
                    if row.get(field) is not None:
                        validate_sha256_hex(row[field], f"adaptive_usage[{index}].{field}")
                query_start = parse_time(row.get("query_start_time"), f"adaptive_usage[{index}].query_start_time")
                query_end_value = row.get("query_end_time")
                if query_end_value is not None:
                    query_end = parse_time(query_end_value, f"adaptive_usage[{index}].query_end_time")
                    if query_end < query_start:
                        raise EvidenceError(f"adaptive_usage[{index}].query_end_time cannot precede query_start_time")
                    if query_end > generated:
                        raise EvidenceError(
                            f"adaptive_usage[{index}].query_end_time cannot be after metadata.generated_at"
                        )
            elif name == "internal_transfer_usage":
                if row.get("compute_pool_name_sha256") is not None:
                    validate_sha256_hex(
                        row["compute_pool_name_sha256"],
                        f"internal_transfer_usage[{index}].compute_pool_name_sha256",
                    )
            elif name == "ai_usage":
                validate_sha256_hex(row.get("query_id_sha256"), f"ai_usage[{index}].query_id_sha256")
                safe_text(row.get("function_name"), f"ai_usage[{index}].function_name")
                for field in (
                    "model_name_sha256",
                    "query_tag_sha256",
                    "user_id_sha256",
                ):
                    if row.get(field) is not None:
                        validate_sha256_hex(row[field], f"ai_usage[{index}].{field}")
                if not isinstance(row.get("is_completed"), bool):
                    raise EvidenceError(f"ai_usage[{index}].is_completed must be boolean")
        result[name] = rows_in_window(rows, name, start, end, warnings, findings)
    return result


def build_cost_ledger(
    warehouses: list[dict[str, Any]],
    queries: list[dict[str, Any]],
    serverless: list[dict[str, Any]],
    additional: dict[str, list[dict[str, Any]]],
    inventory: dict[str, dict[str, Any]],
    rates: dict[str, Any],
    findings: list[dict[str, str]],
    warnings: list[str],
) -> list[dict[str, Any]]:
    ledger: list[dict[str, Any]] = []

    def state(surface: str) -> tuple[str, str]:
        return surface_state(inventory, surface)

    warehouse_compute = sum_field(warehouses, "credits_used_compute", "warehouse_metering")
    warehouse_cloud = sum_field(warehouses, "credits_used_cloud_services", "warehouse_metering")
    if warehouses:
        fresh, available = state("warehouse_metering")
        ledger.append(
            ledger_entry(
                entry_id="warehouse-compute-total",
                domain="warehouse_compute",
                source="SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY",
                role="total",
                unit="credits",
                amount=warehouse_compute,
                parent_id=None,
                overlap_key="warehouse-compute",
                freshness_status=fresh,
                availability_status=available,
            )
        )
        ledger.append(
            ledger_entry(
                entry_id="warehouse-cloud-services-context",
                domain="warehouse_cloud_services",
                source="SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY",
                role="context",
                unit="credits",
                amount=warehouse_cloud,
                parent_id=None,
                overlap_key="warehouse-cloud-services-unadjusted",
                freshness_status=fresh,
                availability_status=available,
            )
        )
    if queries:
        fresh, available = state("query_attribution")
        ledger.append(
            ledger_entry(
                entry_id="query-attributed-compute",
                domain="query_attribution",
                source="SNOWFLAKE.ACCOUNT_USAGE.QUERY_ATTRIBUTION_HISTORY",
                role="attribution",
                unit="credits",
                amount=sum_field(queries, "credits_attributed_compute", "query_attribution"),
                parent_id="warehouse-compute-total",
                overlap_key="warehouse-compute",
                freshness_status=fresh,
                availability_status=available,
            )
        )
        qas = sum_nullable_zero(queries, "credits_used_query_acceleration", "query_attribution")
        ledger.append(
            ledger_entry(
                entry_id="query-acceleration-attribution",
                domain="query_acceleration",
                source="SNOWFLAKE.ACCOUNT_USAGE.QUERY_ATTRIBUTION_HISTORY",
                role="attribution",
                unit="credits",
                amount=qas,
                parent_id="metering-total:QUERY_ACCELERATION",
                overlap_key="service:QUERY_ACCELERATION",
                freshness_status=fresh,
                availability_status=available,
            )
        )
    serverless_totals: dict[str, Decimal] = {}
    for index, row in enumerate(serverless):
        service = safe_text(row.get("service_type"), f"serverless_usage[{index}].service_type")
        serverless_totals[service] = serverless_totals.get(service, Decimal("0")) + decimal_value(
            row.get("credits_used"), f"serverless_usage[{index}].credits_used"
        )
    fresh, available = state("serverless_usage")
    for service, amount in sorted(serverless_totals.items()):
        role = "context" if service in {"WAREHOUSE_METERING", "WAREHOUSE_METERING_READER"} else "total"
        ledger.append(
            ledger_entry(
                entry_id=f"metering-total:{service}",
                domain=f"metering:{service}",
                source="SNOWFLAKE.ACCOUNT_USAGE.METERING_HISTORY",
                role=role,
                unit="credits",
                amount=amount,
                parent_id=None,
                overlap_key="warehouse-compute" if role == "context" else f"service:{service}",
                freshness_status=fresh,
                availability_status=available,
            )
        )

    adaptive = additional["adaptive_usage"]
    if adaptive:
        fresh, available = state("adaptive_usage")
        mutable_adaptive = [row for row in adaptive if row.get("query_end_time") is None]
        settled_adaptive = [row for row in adaptive if row.get("query_end_time") is not None]
        for index, row in enumerate(adaptive):
            total = decimal_value(row.get("credits_used"), f"adaptive_usage[{index}].credits_used")
            compute = decimal_value(row.get("credits_used_compute"), f"adaptive_usage[{index}].credits_used_compute")
            cloud = decimal_value(
                row.get("credits_used_cloud_services"),
                f"adaptive_usage[{index}].credits_used_cloud_services",
            )
            if total != compute + cloud:
                raise EvidenceError(f"adaptive_usage[{index}] credits_used must equal compute plus cloud services")
        if mutable_adaptive:
            add_finding(
                findings,
                "COST_ADAPTIVE_IN_PROGRESS",
                "error",
                "adaptive_usage",
                "Adaptive rows without query_end_time remain mutable and cannot support settled attribution.",
            )
        if settled_adaptive:
            compute_credits = sum_field(settled_adaptive, "credits_used_compute", "adaptive_usage.settled")
            cloud_credits = sum_field(settled_adaptive, "credits_used_cloud_services", "adaptive_usage.settled")
            ledger.append(
                ledger_entry(
                    entry_id="adaptive-compute-attribution",
                    domain="adaptive_compute",
                    source="SNOWFLAKE.ACCOUNT_USAGE.QUERY_METERING_HISTORY",
                    role="attribution",
                    unit="credits",
                    amount=compute_credits,
                    parent_id="warehouse-compute-total",
                    overlap_key="warehouse-compute",
                    freshness_status=fresh,
                    availability_status=available,
                )
            )
            ledger.append(
                ledger_entry(
                    entry_id="adaptive-cloud-services-context",
                    domain="adaptive_cloud_services",
                    source="SNOWFLAKE.ACCOUNT_USAGE.QUERY_METERING_HISTORY",
                    role="context",
                    unit="credits",
                    amount=cloud_credits,
                    parent_id=None,
                    overlap_key="adaptive-cloud-services-unadjusted",
                    freshness_status=fresh,
                    availability_status=available,
                )
            )

    storage = additional["storage_usage"]
    if storage:
        fresh, available = state("storage_usage")
        storage_intervals: list[tuple[datetime, datetime, int, dict[str, Any]]] = []
        for index, row in enumerate(storage):
            interval_start = parse_time(row.get("start_time"), f"storage_usage[{index}].start_time")
            interval_end = parse_time(row.get("end_time"), f"storage_usage[{index}].end_time")
            storage_intervals.append((interval_start, interval_end, index, row))
        storage_intervals.sort(key=lambda item: (item[0], item[1]))
        for previous, current in zip(storage_intervals, storage_intervals[1:]):
            if current[0] < previous[1]:
                raise EvidenceError("storage_usage daily snapshot intervals must not overlap")
        for field, domain in (
            ("storage_bytes", "table_storage"),
            ("stage_bytes", "stage_storage"),
            ("failsafe_bytes", "failsafe_storage"),
            ("hybrid_table_storage_bytes", "hybrid_table_storage"),
            ("archive_storage_cool_bytes", "archive_storage_cool"),
            ("archive_storage_cold_bytes", "archive_storage_cold"),
            ("archive_storage_retrieval_temp_bytes", "archive_storage_retrieval_temp"),
        ):
            byte_days = Decimal("0")
            for interval_start, interval_end, index, row in storage_intervals:
                interval_days = Decimal(str((interval_end - interval_start).total_seconds())) / Decimal("86400")
                byte_days += decimal_value(row.get(field), f"storage_usage[{index}].{field}") * interval_days
            entry = ledger_entry(
                entry_id=f"storage-context:{domain}",
                domain=domain,
                source="SNOWFLAKE.ACCOUNT_USAGE.STORAGE_USAGE",
                role="context",
                unit="byte-days",
                amount=byte_days,
                parent_id=None,
                overlap_key=f"storage:{domain}",
                freshness_status=fresh,
                availability_status=available,
            )
            entry["measurement_basis"] = "average_daily_bytes_times_interval_days"
            ledger.append(entry)
        add_finding(
            findings,
            "COST_INVOICE_ONLY",
            "info",
            "storage_usage",
            "Storage usage is byte-day operational context and uses different measurement semantics from invoice storage.",
        )

    for surface, source in (
        ("data_transfer_usage", "SNOWFLAKE.ACCOUNT_USAGE.DATA_TRANSFER_HISTORY"),
        ("internal_transfer_usage", "SNOWFLAKE.ACCOUNT_USAGE.INTERNAL_DATA_TRANSFER_HISTORY"),
    ):
        rows = additional[surface]
        if rows:
            fresh, available = state(surface)
            ledger.append(
                ledger_entry(
                    entry_id=f"{surface}-context",
                    domain=surface,
                    source=source,
                    role="context",
                    unit="bytes",
                    amount=sum_field(rows, "bytes_transferred", surface),
                    parent_id=None,
                    overlap_key=f"transfer:{surface}",
                    freshness_status=fresh,
                    availability_status=available,
                )
            )

    ai = additional["ai_usage"]
    if ai:
        fresh, available = state("ai_usage")
        ai_calls: dict[str, list[dict[str, Any]]] = {}
        for row in ai:
            ai_calls.setdefault(row["query_id_sha256"], []).append(row)
        mutable_calls = [rows for rows in ai_calls.values() if not any(row["is_completed"] for row in rows)]
        settled_ai = [
            row for rows in ai_calls.values() if any(candidate["is_completed"] for candidate in rows) for row in rows
        ]
        if mutable_calls:
            add_finding(
                findings,
                "COST_AI_IN_PROGRESS",
                "error",
                "ai_usage",
                "AI Function calls without a completion-window row are billed observations but remain mutable and unsettled.",
            )
        if settled_ai and "AI_SERVICES" in serverless_totals:
            ledger.append(
                ledger_entry(
                    entry_id="ai-functions-attribution",
                    domain="cortex_ai_functions",
                    source="SNOWFLAKE.ACCOUNT_USAGE.CORTEX_AI_FUNCTIONS_USAGE_HISTORY",
                    role="attribution",
                    unit="credits",
                    amount=sum_field(settled_ai, "credits_used", "ai_usage.settled"),
                    parent_id="metering-total:AI_SERVICES",
                    overlap_key="service:AI_SERVICES",
                    freshness_status=fresh,
                    availability_status=available,
                )
            )
        if settled_ai and "AI_SERVICES" not in serverless_totals:
            add_finding(
                findings,
                "COST_SURFACE_MISSING",
                "warning",
                "serverless_usage",
                "Detailed AI attribution has no aligned METERING_HISTORY service total.",
            )
    elif serverless_totals.get("AI_SERVICES", Decimal("0")) > 0:
        add_finding(
            findings,
            "COST_AI_ATTRIBUTION_GAP",
            "warning",
            "ai_usage",
            "AI service credits are present without detailed AI function attribution.",
        )

    invoice_intervals: list[tuple[str, str, datetime, datetime, str]] = []
    for index, row in enumerate(additional["invoice_usage"]):
        domain = safe_text(row.get("domain"), f"invoice_usage[{index}].domain")
        currency = safe_text(row.get("currency"), f"invoice_usage[{index}].currency")
        statement_id = validate_hash(row.get("statement_id"), f"invoice_usage[{index}].statement_id")
        interval_start = parse_time(row["start_time"], f"invoice_usage[{index}].start_time")
        interval_end = parse_time(row["end_time"], f"invoice_usage[{index}].end_time")
        for prior_domain, prior_currency, prior_start, prior_end, prior_statement in invoice_intervals:
            if (
                domain == prior_domain
                and currency == prior_currency
                and interval_start < prior_end
                and prior_start < interval_end
            ):
                add_finding(
                    findings,
                    "COST_DOUBLE_COUNT_RISK",
                    "error",
                    "invoice_usage",
                    f"Invoice statements {prior_statement} and {statement_id} overlap for one domain and currency.",
                )
        invoice_intervals.append((domain, currency, interval_start, interval_end, statement_id))
        ledger.append(
            ledger_entry(
                entry_id=f"invoice:{statement_id}",
                domain=domain,
                source="customer-supplied billing statement",
                role="invoice-only",
                unit=currency,
                amount=decimal_value(row.get("amount"), f"invoice_usage[{index}].amount"),
                parent_id=None,
                overlap_key=f"invoice:{domain}:{currency}:{row['start_time']}:{row['end_time']}",
                freshness_status="not_applicable",
                availability_status="supplied",
                invoice_status="invoice_only",
            )
        )

    for entry in list(ledger):
        if entry["unit"] != "credits" or entry["ledger_role"] not in {"total", "invoice-only"}:
            continue
        rate_key = entry["domain"]
        if rate_key not in rates and rate_key == "warehouse_compute":
            rate_key = "warehouse"
        estimate = rate_estimate(Decimal(entry["amount"]), rate_key, rates, warnings)
        if not estimate:
            continue
        fresh = entry["freshness_status"]
        available = entry["availability_status"]
        estimate_entry = ledger_entry(
            entry_id=f"estimate:{entry['entry_id']}",
            domain=entry["domain"],
            source=estimate["provenance"],
            role="estimate",
            unit=estimate["currency"],
            amount=Decimal(estimate["amount"]),
            parent_id=entry["entry_id"],
            overlap_key=f"estimate:{entry['overlap_key']}",
            freshness_status=fresh,
            availability_status=available,
            invoice_status=estimate["invoice_reconciliation"],
        )
        estimate_entry["aggregation_eligible"] = False
        estimate_entry["unit_price"] = estimate["unit_price"]
        estimate_entry["rate_basis"] = estimate["basis"]
        estimate_entry["credits"] = estimate["credits"]
        estimate_entry["effective_period"] = estimate["effective_period"]
        ledger.append(estimate_entry)

    entry_ids = {entry["entry_id"] for entry in ledger}
    filtered_ledger: list[dict[str, Any]] = []
    for entry in ledger:
        parent_id = entry.get("parent_id")
        if parent_id is not None and parent_id not in entry_ids:
            add_finding(
                findings,
                "COST_SURFACE_MISSING",
                "warning",
                entry["domain"],
                f"Ledger entry {entry['entry_id']} was withheld because parent {parent_id} is absent.",
            )
            continue
        filtered_ledger.append(entry)
    ledger = filtered_ledger

    totals_by_overlap: dict[tuple[str, str], int] = {}
    for entry in ledger:
        if entry["aggregation_eligible"]:
            key = (entry["unit"], entry["overlap_key"])
            totals_by_overlap[key] = totals_by_overlap.get(key, 0) + 1
    for (unit, overlap), count in sorted(totals_by_overlap.items()):
        if count > 1:
            add_finding(
                findings,
                "COST_DOUBLE_COUNT_RISK",
                "error",
                "ledger",
                f"More than one additive {unit} total shares overlap key {overlap}.",
            )
    return sorted(ledger, key=lambda item: item["entry_id"])


def assess_controls(
    data: dict[str, Any],
    serverless: list[dict[str, Any]],
    adaptive: list[dict[str, Any]],
    ai: list[dict[str, Any]],
    findings: list[dict[str, str]],
) -> dict[str, Any]:
    controls = data.get("controls_inventory", {})
    if not isinstance(controls, dict):
        raise EvidenceError("controls_inventory must be an object")
    monitors = controls.get("resource_monitors", [])
    budgets = controls.get("budgets", [])
    if not isinstance(monitors, list) or not all(isinstance(row, dict) for row in monitors):
        raise EvidenceError("controls_inventory.resource_monitors must be an array of objects")
    if not isinstance(budgets, list) or not all(isinstance(row, dict) for row in budgets):
        raise EvidenceError("controls_inventory.budgets must be an array of objects")
    assigned_monitors = 0
    enforcing_monitors = 0
    for index, row in enumerate(monitors):
        validate_sha256_hex(
            row.get("name_sha256"),
            f"controls_inventory.resource_monitors[{index}].name_sha256",
        )
        if row.get("owner_sha256") is not None:
            validate_sha256_hex(
                row["owner_sha256"],
                f"controls_inventory.resource_monitors[{index}].owner_sha256",
            )
        level = safe_text(row.get("level", "UNASSIGNED"), f"controls_inventory.resource_monitors[{index}].level")
        if level in {"ACCOUNT", "WAREHOUSE"}:
            assigned_monitors += 1
        quota = _optional_number(row.get("credit_quota"), f"controls_inventory.resource_monitors[{index}].credit_quota")
        suspend = _optional_number(row.get("suspend"), f"controls_inventory.resource_monitors[{index}].suspend")
        suspend_immediate = _optional_number(
            row.get("suspend_immediate"),
            f"controls_inventory.resource_monitors[{index}].suspend_immediate",
        )
        if (
            level in {"ACCOUNT", "WAREHOUSE"}
            and quota is not None
            and (suspend is not None or suspend_immediate is not None)
        ):
            enforcing_monitors += 1
    for index, row in enumerate(budgets):
        validate_sha256_hex(
            row.get("name_sha256"),
            f"controls_inventory.budgets[{index}].name_sha256",
        )
        for field in ("database_name_sha256", "schema_name_sha256", "owner_sha256"):
            if row.get(field) is not None:
                validate_sha256_hex(
                    row[field],
                    f"controls_inventory.budgets[{index}].{field}",
                )
    if not monitors:
        add_finding(
            findings,
            "COST_RESOURCE_MONITOR_COVERAGE_GAP",
            "info",
            "resource_monitors",
            "No visible resource-monitor assignment was supplied; visibility may be role-scoped.",
        )
    non_warehouse_present = bool(
        adaptive
        or ai
        or any(
            str(row.get("service_type", "")) not in {"WAREHOUSE_METERING", "WAREHOUSE_METERING_READER"}
            for row in serverless
        )
    )
    if non_warehouse_present:
        add_finding(
            findings,
            "COST_SERVERLESS_MONITOR_GAP",
            "info",
            "budgets",
            "Resource-monitor inventory cannot enforce serverless or AI usage; visible budget instances do not prove linked-resource or action coverage.",
        )
    if not budgets:
        add_finding(
            findings,
            "COST_BUDGET_COVERAGE_GAP",
            "info",
            "budgets",
            "No visible budget inventory was supplied; this is an unknown control boundary, not proof that no budget exists.",
        )
    return {
        "visible_resource_monitors": len(monitors),
        "visible_assigned_monitors": assigned_monitors,
        "visible_enforcing_monitors": enforcing_monitors,
        "visible_budgets": len(budgets),
        "budget_coverage_status": "unknown_without_separately_receipted_budget_scope_and_actions",
        "visibility_is_complete": False,
        "visibility_scope": "current_role_only",
    }


def analyze(data: dict[str, Any], *, trusted_input_sha256: str | None = None) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise EvidenceError("input root must be an object")
    reject_secret_fields(data)
    start, end, generated = validate_window(data)
    expected_surfaces = validate_expected_surfaces(data["metadata"])
    raw_warehouses = validate_rows(data, "warehouse_metering")
    raw_queries = validate_rows(data, "query_attribution")
    raw_serverless = validate_rows(data, "serverless_usage")
    raw_warehouse_load = validate_rows(data, "warehouse_load")
    for dataset_name, rows in (
        ("warehouse_metering", raw_warehouses),
        ("query_attribution", raw_queries),
        ("serverless_usage", raw_serverless),
        ("warehouse_load", raw_warehouse_load),
    ):
        for index, row in enumerate(rows):
            if "unit" in row:
                raise EvidenceError(
                    f"{dataset_name}[{index}].unit is not accepted; ledger units are fixed by the reviewed source contract"
                )
    rates = data.get("credit_rates", {})
    if not isinstance(rates, dict):
        raise EvidenceError("credit_rates must be an object")

    warnings: list[str] = []
    findings: list[dict[str, str]] = []
    evidence_trust = assess_input_trust(data, trusted_input_sha256, warnings)
    if not evidence_trust["trusted"]:
        add_finding(
            findings,
            "COST_EVIDENCE_UNTRUSTED",
            "error",
            "evidence_bundle",
            "Positive cost claims are withheld until the canonical bundle matches a separately recorded trusted-input digest.",
        )
    collector_receipt = validate_collector_receipt(data, warnings, generated, evidence_trust["trusted"])
    raw_warehouses = rows_in_window(raw_warehouses, "warehouse_metering", start, end, warnings, findings)
    raw_queries = rows_in_window(raw_queries, "query_attribution", start, end, warnings, findings)
    raw_serverless = rows_in_window(raw_serverless, "serverless_usage", start, end, warnings, findings)
    raw_warehouse_load = rows_in_window(raw_warehouse_load, "warehouse_load", start, end, warnings, findings)
    raw_additional = validate_additional_rows(data, start, end, generated, warnings, findings)
    for index, row in enumerate(raw_queries):
        validate_sha256_hex(row.get("query_id_sha256"), f"query_attribution[{index}].query_id_sha256")
        warehouse_label(row, f"query_attribution[{index}]")
        validate_tag_indicator(row, f"query_attribution[{index}]")
        if row.get("user_name_sha256") is not None:
            validate_sha256_hex(row["user_name_sha256"], f"query_attribution[{index}].user_name_sha256")
        for field in ("query_hash", "query_parameterized_hash"):
            if row.get(field) is not None:
                validate_sha256_hex(row[field], f"query_attribution[{index}].{field}")
    for index, row in enumerate(raw_warehouses):
        warehouse_label(row, f"warehouse_metering[{index}]")
    for index, row in enumerate(raw_warehouse_load):
        warehouse_label(row, f"warehouse_load[{index}]")
    source_freshness, freshness_warnings = freshness(data, generated, end)
    warnings.extend(freshness_warnings)
    supplemental_receipts = validate_supplemental_receipts(
        data,
        expected_surfaces,
        generated,
        findings,
        warnings,
        evidence_trust["trusted"],
    )
    enforce_context_consistency(collector_receipt, supplemental_receipts, findings, warnings)
    baseline_time = (
        _receipt_settlement_observation(data.get("collector_receipt"))
        if collector_receipt.get("complete") is True
        else None
    )
    collection_times = {
        surface: baseline_time
        for surface in ("warehouse_metering", "query_attribution", "warehouse_load", "serverless_usage")
        if baseline_time is not None
    }
    supplied_supplemental = data.get("supplemental_receipts", {})
    if isinstance(supplied_supplemental, dict):
        for surface in SUPPLEMENTAL_RECEIPT_SURFACES:
            assessment = supplemental_receipts.get(surface, {})
            collection_time = (
                _receipt_settlement_observation(supplied_supplemental.get(surface))
                if assessment.get("complete") is True
                else None
            )
            if collection_time is not None:
                collection_times[surface] = collection_time
    surface_inventory, inventory_by_surface = assess_surface_inventory(
        data, generated, end, collection_times, expected_surfaces, findings, warnings
    )

    def surface_ready(surface: str) -> bool:
        item = inventory_by_surface.get(surface, {})
        if item.get("status") != "available" or item.get("truncated") is not False:
            return False
        if item.get("freshness_status") not in {"settled_window", "current_role_scoped_observation"}:
            return False
        if surface in {"warehouse_metering", "query_attribution", "warehouse_load", "serverless_usage"}:
            return bool(collector_receipt["complete"])
        return bool(supplemental_receipts.get(surface, {}).get("complete"))

    warehouses = raw_warehouses if surface_ready("warehouse_metering") else []
    queries = raw_queries if surface_ready("query_attribution") else []
    serverless = raw_serverless if surface_ready("serverless_usage") else []
    warehouse_load = raw_warehouse_load if surface_ready("warehouse_load") else []
    additional = {
        surface: rows if surface == "invoice_usage" or surface_ready(surface) else []
        for surface, rows in raw_additional.items()
    }
    ensure_unique_rows(
        warehouses,
        "warehouse_metering",
        ("warehouse_id", "start_time", "end_time"),
    )
    ensure_unique_rows(queries, "query_attribution", ("query_id_sha256", "start_time", "end_time"))
    ensure_unique_rows(
        warehouse_load,
        "warehouse_load",
        ("warehouse_id", "start_time", "end_time"),
    )
    ensure_unique_rows(serverless, "serverless_usage", ("service_type", "start_time", "end_time"))
    ensure_unique_rows(
        additional["adaptive_usage"],
        "adaptive_usage",
        ("query_id_sha256", "start_time", "end_time"),
    )
    ensure_unique_rows(additional["storage_usage"], "storage_usage", ("start_time", "end_time"))
    ensure_unique_rows(
        additional["data_transfer_usage"],
        "data_transfer_usage",
        ("transfer_type", "source_cloud", "source_region", "target_cloud", "target_region", "start_time", "end_time"),
    )
    ensure_unique_rows(
        additional["internal_transfer_usage"],
        "internal_transfer_usage",
        ("transfer_type", "compute_pool_name_sha256", "start_time", "end_time"),
    )
    ensure_unique_rows(
        additional["ai_usage"],
        "ai_usage",
        ("query_id_sha256", "function_name", "model_name_sha256", "start_time", "end_time"),
    )
    ensure_unique_rows(
        additional["invoice_usage"],
        "invoice_usage",
        ("statement_id", "domain", "currency", "start_time", "end_time"),
    )

    completeness = attribution_completeness(warehouses, warnings)
    pareto = cost_latency_pareto(queries, warnings)
    right_sizing = right_sizing_boundary(data["metadata"], warnings)
    if data["metadata"].get("right_sizing") is not None and right_sizing["status"] != "bounded_proposal":
        add_finding(
            findings,
            "COST_EXPERIMENT_ROLLBACK_UNBOUNDED",
            "error",
            "right_sizing",
            "The experiment lacks a complete measurement boundary and explicit rollback thresholds.",
        )

    warehouse_compute = sum_field(warehouses, "credits_used_compute", "warehouse_metering")
    warehouse_cloud = sum_field(warehouses, "credits_used_cloud_services", "warehouse_metering")
    idle_by_warehouse: list[dict[str, str]] = []
    review_owner = safe_text(data["metadata"]["review_owner"], "metadata.review_owner")
    approval_boundary = safe_text(data["metadata"]["approval_boundary"], "metadata.approval_boundary")
    for index, row in enumerate(warehouses):
        name = warehouse_label(row, f"warehouse_metering[{index}]")
        if row.get("credits_attributed_compute_queries") is None:
            warnings.append(
                f"warehouse_metering[{index}] {name}: attributed-query credits are NULL; "
                "idle/unattributed compute cannot be derived"
            )
            add_finding(
                findings,
                "COST_ADAPTIVE_ATTRIBUTION_GAP",
                "warning",
                "warehouse_metering",
                f"{name} has NULL attributed-query credits; unattributed compute is unknown.",
            )
            continue
        used = decimal_value(
            row.get("credits_used_compute", 0),
            f"warehouse_metering[{index}].credits_used_compute",
        )
        attributed = decimal_value(
            row.get("credits_attributed_compute_queries", 0),
            f"warehouse_metering[{index}].credits_attributed_compute_queries",
        )
        if attributed > used:
            warnings.append(
                f"warehouse_metering[{index}] {name}: attributed credits exceed compute "
                "credits; window alignment or source completeness requires review"
            )
            continue
        difference = used - attributed
        if difference > 0:
            add_finding(
                findings,
                "COST_UNATTRIBUTABLE",
                "warning",
                "warehouse_metering",
                f"{name} has metered compute not attributed to queries in the aligned window.",
            )
            idle_by_warehouse.append(
                {
                    "warehouse_name": name,
                    "credits": as_text(difference),
                    "classification": "at-risk",
                    "basis": "compute credits minus attributed query compute for the aligned window",
                    "decision": "review required; not asserted recoverable savings",
                    "competing_explanation": "intentional warm capacity, queue protection, or work outside query-attribution coverage",
                    "next_read_only_verification": "align warehouse load, query attribution, and workload schedule for the same half-open window",
                    "owner": review_owner,
                    "approval_boundary": approval_boundary,
                }
            )

    query_compute = sum_field(queries, "credits_attributed_compute", "query_attribution")
    query_acceleration = sum_nullable_zero(queries, "credits_used_query_acceleration", "query_attribution")
    untagged = Decimal("0")
    for index, row in enumerate(queries):
        credits = decimal_value(
            row.get("credits_attributed_compute", 0),
            f"query_attribution[{index}].credits_attributed_compute",
        )
        tag_present = validate_tag_indicator(row, f"query_attribution[{index}]")
        if not tag_present:
            untagged += credits

    serverless_by_service: dict[str, Decimal] = {}
    for index, row in enumerate(serverless):
        service = row.get("service_type")
        service = safe_text(service, f"serverless_usage[{index}].service_type")
        if "credits_used" not in row or row["credits_used"] is None:
            raise EvidenceError(f"serverless_usage[{index}].credits_used is required")
        credits = decimal_value(row["credits_used"], f"serverless_usage[{index}].credits_used")
        serverless_by_service[service] = serverless_by_service.get(service, Decimal("0")) + credits

    confirmed: list[dict[str, str]] = []
    if warehouses:
        confirmed.extend(
            [
                {
                    "metric": "warehouse_compute_credits",
                    "credits": as_text(warehouse_compute),
                    "classification": "confirmed",
                    "source": "WAREHOUSE_METERING_HISTORY evidence supplied",
                },
                {
                    "metric": "warehouse_cloud_services_credits_unadjusted",
                    "credits": as_text(warehouse_cloud),
                    "classification": "confirmed",
                    "source": "WAREHOUSE_METERING_HISTORY evidence supplied; not invoice-adjusted",
                },
            ]
        )
    if queries:
        confirmed.extend(
            [
                {
                    "metric": "query_attributed_compute_credits_excluding_idle",
                    "credits": as_text(query_compute),
                    "classification": "confirmed",
                    "source": "QUERY_ATTRIBUTION_HISTORY evidence supplied",
                },
                {
                    "metric": "query_acceleration_credits",
                    "credits": as_text(query_acceleration),
                    "classification": "confirmed",
                    "source": "QUERY_ATTRIBUTION_HISTORY evidence supplied",
                },
            ]
        )
    load_summary: list[dict[str, str]] = []
    for index, row in enumerate(warehouse_load):
        name = warehouse_label(row, f"warehouse_load[{index}]")
        running = decimal_value(row.get("avg_running", 0), f"warehouse_load[{index}].avg_running")
        queued = decimal_value(row.get("avg_queued_load", 0), f"warehouse_load[{index}].avg_queued_load")
        provisioning = decimal_value(
            row.get("avg_queued_provisioning", 0), f"warehouse_load[{index}].avg_queued_provisioning"
        )
        load_summary.append(
            {
                "warehouse_name": name,
                "avg_running": as_text(running),
                "avg_queued_load": as_text(queued),
                "avg_queued_provisioning": as_text(provisioning),
                "classification": "confirmed",
            }
        )
        if queued > 0 or provisioning > 0:
            warnings.append(
                f"{name}: warehouse load evidence shows queue pressure; correlate to query latency before resizing"
            )
    for service, credits in sorted(serverless_by_service.items()):
        confirmed.append(
            {
                "metric": f"metering:{service}",
                "credits": as_text(credits),
                "classification": "confirmed",
                "source": "METERING_HISTORY evidence supplied",
            }
        )

    at_risk = sorted(
        idle_by_warehouse,
        key=lambda item: Decimal(item["credits"]),
        reverse=True,
    )
    if untagged > 0:
        add_finding(
            findings,
            "COST_TAG_COVERAGE_GAP",
            "warning",
            "query_attribution",
            "Query-attributed compute includes usage without a non-empty query tag.",
        )
        at_risk.append(
            {
                "metric": "untagged_query_attributed_compute",
                "credits": as_text(untagged),
                "classification": "at-risk",
                "basis": "query-attributed compute with NULL or empty QUERY_TAG",
                "decision": "attribution gap; not asserted waste",
                "competing_explanation": "approved untagged system or interactive workload",
                "next_read_only_verification": "map query hashes and users to an authorized workload owner without exposing query text",
                "owner": review_owner,
                "approval_boundary": approval_boundary,
            }
        )

    if not warehouses:
        warnings.append("warehouse_metering evidence absent; warehouse usage is unknown, not zero")
    if not queries:
        warnings.append("query_attribution evidence absent; per-query usage is unknown, not zero")
    if not warehouse_load:
        warnings.append("warehouse_load evidence absent; cost/latency queue correlation is unknown")

    ledger = build_cost_ledger(
        warehouses,
        queries,
        serverless,
        additional,
        inventory_by_surface,
        rates,
        findings,
        warnings,
    )
    estimates = [
        {
            "basis": item["domain"],
            "credits": item["credits"],
            "unit_price": item["unit_price"],
            "currency": item["unit"],
            "amount": item["amount"],
            "provenance": item["source"],
            "classification": "estimated",
            "invoice_reconciliation": item["invoice_reconciliation"],
            "effective_period": item["effective_period"],
        }
        for item in ledger
        if item["ledger_role"] == "estimate"
    ]
    priced_parents = {item["parent_id"] for item in ledger if item["ledger_role"] == "estimate"}
    for item in ledger:
        if item["ledger_role"] == "total" and item["unit"] == "credits" and item["entry_id"] not in priced_parents:
            add_finding(
                findings,
                "COST_ESTIMATE_UNPRICED",
                "info",
                item["domain"],
                "No applicable customer-supplied rate was provided; the report remains in credits.",
            )
    trusted_controls_data = dict(data)
    raw_controls = data.get("controls_inventory", {})
    trusted_controls_data["controls_inventory"] = {
        "resource_monitors": raw_controls.get("resource_monitors", [])
        if isinstance(raw_controls, dict) and surface_ready("resource_monitors")
        else [],
        "budgets": raw_controls.get("budgets", [])
        if isinstance(raw_controls, dict) and surface_ready("budgets")
        else [],
    }
    controls_assessment = assess_controls(
        trusted_controls_data,
        serverless,
        additional["adaptive_usage"],
        additional["ai_usage"],
        findings,
    )
    if additional["invoice_usage"]:
        add_finding(
            findings,
            "COST_INVOICE_UNVERIFIED",
            "error",
            "invoice_usage",
            "Customer-supplied invoice rows are retained as non-additive evidence but are not a receipted usage reconciliation.",
        )
    if collector_receipt["status"] == "unverifiable":
        add_finding(
            findings,
            "COST_SURFACE_TRUNCATED" if collector_receipt.get("truncation_possible") else "COST_SURFACE_MISSING",
            "error",
            "collector_receipt",
            "The baseline collector receipt is unverifiable, so completeness claims remain blocked.",
        )
    if any(item["ledger_role"] == "total" and item["invoice_reconciliation"] != "reconciled" for item in ledger):
        add_finding(
            findings,
            "COST_INVOICE_ONLY",
            "info",
            "invoice",
            "Usage totals were not reconciled to an invoice or billing statement.",
        )

    approval_queue = [
        {
            "candidate": item.get("warehouse_name") or item.get("metric"),
            "status": "review_required",
            "owner": item["owner"],
            "approval_boundary": item["approval_boundary"],
            "impact": "unknown until the competing explanation is tested",
            "verification": item["next_read_only_verification"],
            "rollback": "no change is proposed by this analyzer; define reversal before approval",
        }
        for item in at_risk
    ]
    completeness_claim_blocked = not collector_receipt["complete"] or any(
        item["code"] in COMPLETENESS_BLOCKING_CODES for item in findings
    )
    if completeness_claim_blocked:
        confirmed = []
        estimates = []
        approval_queue = []
        for item in ledger:
            item["aggregation_eligible"] = False

    included_surfaces = sorted(surface for surface in expected_surfaces if surface_ready(surface))
    excluded_surfaces = sorted(set(expected_surfaces) - set(included_surfaces))
    total_entries = [item for item in ledger if item["ledger_role"] == "total"]
    invoice_reconciliation_status = (
        "reconciled"
        if total_entries and all(item["invoice_reconciliation"] == "reconciled" for item in total_entries)
        else "not_reconciled"
    )

    return {
        "schema_version": "2.0",
        "scope": {
            "account": safe_text(data["metadata"]["account"], "metadata.account"),
            "role": safe_text(data["metadata"]["role"], "metadata.role"),
            "window_start": start.isoformat(),
            "window_end": end.isoformat(),
            "generated_at": generated.isoformat(),
        },
        "identity_disclosure": {
            "authorized": data["metadata"]["identity_disclosure_authorized"],
            "authority": data["metadata"].get("identity_disclosure_authority"),
        },
        "source_freshness": source_freshness,
        "surface_inventory": surface_inventory,
        "included_surfaces": included_surfaces,
        "excluded_surfaces": excluded_surfaces,
        "invoice_reconciliation_status": invoice_reconciliation_status,
        "cost_ledger": ledger,
        "findings": sorted(findings, key=lambda item: (item["code"], item["surface"], item["message"])),
        "controls_assessment": controls_assessment,
        "confirmed_observations": confirmed,
        "estimated_amounts": estimates,
        "at_risk_opportunities": at_risk,
        "attribution_completeness": completeness,
        "warehouse_load_summary": load_summary,
        "cost_latency_pareto": pareto,
        "right_sizing_experiment": right_sizing,
        "approval_queue": approval_queue,
        "evidence_trust": evidence_trust,
        "coverage_status": "bounded_partial"
        if warnings or any(item["severity"] != "info" for item in findings)
        else "complete_for_required_surfaces",
        "collector_receipt_assessment": collector_receipt,
        "supplemental_receipt_assessments": supplemental_receipts,
        "collection_provenance": {
            "baseline": collector_receipt,
            "supplemental": supplemental_receipts,
        },
        "completeness_claim_blocked": completeness_claim_blocked,
        "warnings": sorted(set(warnings)),
        "non_claims": [
            "Credits are not reconciled invoice amounts.",
            "At-risk credits are not promised savings.",
            "No warehouse size, threshold, price, or SLA was inferred.",
            "The reviewed collector SQL contains no mutation and this analyzer executes no Snowflake commands.",
            "No claim is made about operations elsewhere in the surrounding session or workflow.",
        ],
    }


def render_markdown(result: dict[str, Any]) -> str:
    scope = result["scope"]
    baseline = result["collector_receipt_assessment"]
    source_maximums = (
        "; ".join(f"{item['source']}={item['max_timestamp']}" for item in result["source_freshness"]) or "none returned"
    )
    included = ", ".join(result["included_surfaces"]) or "none"
    excluded = ", ".join(result["excluded_surfaces"]) or "none"
    lines = [
        "# Snowflake cost evidence report",
        "",
        "## Evidence header",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| Account / locator | `{scope.get('account') or 'not supplied'}` |",
        f"| Role used for collection | `{scope.get('role') or 'not supplied'}` |",
        f"| Raw identity disclosure authorized | `{result['identity_disclosure']['authorized']}` |",
        f"| Identity disclosure authority | `{result['identity_disclosure']['authority'] or 'not applicable'}` |",
        f"| Session timezone | `{(baseline.get('context') or {}).get('session_timezone', 'unverified') if baseline.get('complete') else 'unverified'}` |",
        f"| UTC half-open window | `{scope['window_start']}` to `{scope['window_end']}` |",
        f"| Report generated | `{scope['generated_at']}` |",
        f"| Baseline collection completed | `{baseline.get('collection_completed_at') or 'unverified'}` |",
        f"| Maximum timestamp by source | {source_maximums} |",
        f"| Snowflake query ID | `{baseline.get('snowflake_query_id') or 'unavailable'}` ({baseline.get('snowflake_query_id_status') or 'unverified'}) |",
        f"| Reviewed / rendered SQL | `{baseline.get('template_sha256') or 'unverified'}` / `{baseline.get('rendered_sql_sha256') or 'unverified'}` |",
        f"| Normalized result hash | `{baseline.get('result_sha256') or 'unverified'}` |",
        f"| Row count / cap | `{baseline.get('row_count')}` / `{baseline.get('row_limit')}` ({baseline.get('cap_scope') or 'unverified'}; truncated={baseline.get('truncation_possible')}) |",
        f"| Included surfaces | {included} |",
        f"| Unavailable or excluded surfaces | {excluded} |",
        f"| Invoice reconciliation | `{result['invoice_reconciliation_status']}` |",
        f"| Receipt / completeness | `{baseline['status']}` / blocked=`{result['completeness_claim_blocked']}` |",
        "",
        "### Source-specific settled cutoffs",
        "",
        "| Surface | Settled cutoff | Window end within cutoff | Freshness |",
        "|---|---|---|---|",
    ]
    for item in result["surface_inventory"]:
        lines.append(
            f"| {item['surface']} | {item['settled_cutoff'] or 'unverified'} | "
            f"{item['window_end_precedes_settled_cutoff']} | {item['freshness_status']} |"
        )
    lines.extend(
        [
            "",
            "## Supplemental receipt assessments",
            "",
            "| Surface | Status | Collection | SQL / result | Rows / cap | Issues |",
            "|---|---|---|---|---|---|",
        ]
    )
    for surface, assessment in sorted(result["supplemental_receipt_assessments"].items()):
        issues = "; ".join(assessment["issues"]) or "none"
        lines.append(
            f"| {surface} | {assessment['status']} | {assessment.get('collection_completed_at') or 'unverified'} | "
            f"{assessment.get('template_sha256') or 'unverified'} / {assessment.get('result_sha256') or 'unverified'} | "
            f"{assessment.get('row_count')} / {assessment.get('row_limit')} ({assessment.get('cap_scope') or 'unverified'}) | {issues} |"
        )
    lines.extend(
        [
            "",
            "## Typed cost ledger",
            "",
            "| Entry | Domain | Source | Role | Amount | Measurement basis | Parent | Overlap key | Additive | Freshness | Availability | Invoice |",
            "|---|---|---|---|---:|---|---|---|---|---|---|---|",
        ]
    )
    for item in result["cost_ledger"]:
        lines.append(
            f"| {item['entry_id']} | {item['domain']} | {item['source']} | {item['ledger_role']} | "
            f"{item['amount']} {item['unit']} | {item.get('measurement_basis', 'not applicable')} | "
            f"{item['parent_id'] or 'none'} | {item['overlap_key']} | {item['aggregation_eligible']} | "
            f"{item['freshness_status']} | {item['availability_status']} | "
            f"{item['invoice_reconciliation']} |"
        )
    lines.extend(
        [
            "",
            "## Findings",
            "",
            "| Code | Severity | Surface | Evidence boundary |",
            "|---|---|---|---|",
        ]
    )
    for item in result["findings"]:
        lines.append(f"| {item['code']} | {item['severity']} | {item['surface']} | {item['message']} |")
    lines.extend(
        [
            "",
            "## Confirmed observations",
            "",
            "| Metric | Credits | Source boundary |",
            "|---|---:|---|",
        ]
    )
    for item in result["confirmed_observations"]:
        lines.append(f"| {item['metric']} | {item['credits']} | {item['source']} |")
    lines.extend(["", "## Estimated amounts", ""])
    if result["estimated_amounts"]:
        lines.extend(
            [
                "| Basis | Amount | Rate evidence | Effective period | Invoice status |",
                "|---|---:|---|---|---|",
            ]
        )
        for item in result["estimated_amounts"]:
            lines.append(
                f"| {item['basis']} | {item['amount']} {item['currency']} | "
                f"{item['unit_price']} per credit; {item['provenance']} | "
                f"{item['effective_period']} | {item['invoice_reconciliation']} |"
            )
    else:
        lines.append("No currency estimate: no applicable user-supplied rate was provided.")
    lines.extend(["", "## At-risk opportunities — review required", ""])
    if result["at_risk_opportunities"]:
        lines.extend(
            [
                "| Evidence | Credits | Why at risk | Competing explanation | Next verification | Owner / approval |",
                "|---|---:|---|---|---|---|",
            ]
        )
        for item in result["at_risk_opportunities"]:
            label = item.get("warehouse_name") or item.get("metric")
            lines.append(
                f"| {label} | {item['credits']} | {item['decision']} | "
                f"{item['competing_explanation']} | {item['next_read_only_verification']} | "
                f"{item['owner']} / {item['approval_boundary']} |"
            )
    else:
        lines.append("No at-risk opportunity was derivable from the supplied evidence.")
    lines.extend(
        [
            "",
            "## Attribution completeness",
            "",
            "| Warehouse | Status | Metered credits | Attributed credits | Fraction | Unattributed |",
            "|---|---|---:|---:|---:|---:|",
        ]
    )
    for item in result["attribution_completeness"]:
        lines.append(
            f"| {item['warehouse_name']} | {item['status']} | {item['compute_credits']} | {item['attributed_query_credits']} | {item['attribution_fraction']} | {item['unattributed_credits']} |"
        )
    lines.extend(["", "## Cost/latency Pareto", ""])
    if result["cost_latency_pareto"]:
        lines.extend(
            [
                "| Warehouse | Fingerprint | Queries | Credits | Avg elapsed ms | Pareto-efficient |",
                "|---|---|---:|---:|---:|---|",
            ]
        )
        for item in result["cost_latency_pareto"]:
            lines.append(
                f"| {item['warehouse_name']} | {item['fingerprint']} | {item['query_count']} | {item['credits']} | {item['average_elapsed_time_ms']} | {item['pareto_efficient']} |"
            )
    else:
        lines.append("No fingerprinted query rows had both cost and latency; Pareto position is unknown.")
    lines.extend(
        [
            "",
            "## Right-sizing experiment boundary",
            "",
            f"Status: `{result['right_sizing_experiment']['status']}`; no mutation executed.",
            "",
        ]
    )
    lines.append(
        "Supply an owner-approved bounded candidate set and success criteria before any resize experiment is considered."
    )
    lines.extend(["", "## Freshness and warnings", ""])
    for item in result["source_freshness"]:
        lines.append(
            f"- `{item['source']}` max timestamp `{item['max_timestamp']}`; "
            f"observed age {item['observed_age_seconds']} seconds."
        )
    for warning in result["warnings"]:
        lines.append(f"- Warning: {warning}")
    lines.extend(["", "## Approval queue", ""])
    if result["approval_queue"]:
        for item in result["approval_queue"]:
            lines.append(
                f"- `{item['candidate']}` — {item['status']}; owner `{item['owner']}`; "
                f"approval: {item['approval_boundary']}; verification: {item['verification']}; "
                f"rollback: {item['rollback']}."
            )
    else:
        lines.append("No configuration change is proposed from the supplied evidence.")
    lines.extend(["", "## Non-claims", ""])
    lines.extend(f"- {item}" for item in result["non_claims"])
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--markdown-out", type=Path)
    parser.add_argument(
        "--trusted-input-sha256",
        help="Out-of-band sha256:<hex> recorded when this canonical bundle crossed a trusted local boundary",
    )
    parser.add_argument(
        "--print-input-sha256",
        action="store_true",
        help="Print the canonical bundle digest for separate trusted-boundary recording, then exit",
    )
    args = parser.parse_args(argv)
    try:
        data = json.loads(args.input.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise EvidenceError("input root must be an object")
        if args.print_input_sha256:
            print(canonical_bundle_digest(data))
            return 0
        result = analyze(data, trusted_input_sha256=args.trusted_input_sha256)
    except (OSError, json.JSONDecodeError, EvidenceError) as exc:
        print(f"evidence error: {exc}", file=sys.stderr)
        return 2
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.json_out:
        args.json_out.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    if args.markdown_out:
        args.markdown_out.write_text(render_markdown(result), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
