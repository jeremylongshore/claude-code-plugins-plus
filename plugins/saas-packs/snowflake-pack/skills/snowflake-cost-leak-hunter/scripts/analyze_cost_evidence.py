#!/usr/bin/env python3
"""Validate and summarize normalized, read-only Snowflake cost evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
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
}
HASH_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")
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


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _rows_match(left: Any, right: Any) -> bool:
    if not isinstance(left, list) or not isinstance(right, list) or len(left) != len(right):
        return False
    return sorted(_canonical_json(row) for row in left) == sorted(_canonical_json(row) for row in right)


def validate_collector_receipt(data: dict[str, Any], warnings: list[str], evaluation_time: datetime) -> dict[str, Any]:
    receipt = data.get("collector_receipt")
    if receipt is None:
        issue = "collector receipt not supplied; provenance and completeness are not verified"
        warnings.append(issue)
        return {"status": "not_supplied", "complete": False, "issues": [issue]}
    issues: list[str] = []
    if not isinstance(receipt, dict):
        issues.append("collector_receipt is not an object")
        receipt = {}
    if receipt.get("schema_version") != "1":
        issues.append("schema_version is not 1")
    if receipt.get("surface") != "cost":
        issues.append("surface is not cost")
    if receipt.get("status") != "collected":
        issues.append(f"status is {receipt.get('status')!r}")
    if receipt.get("errors"):
        issues.append("collector reported an error")
    if not isinstance(receipt.get("connection_profile"), str) or not receipt["connection_profile"].strip():
        issues.append("connection_profile is missing")
    try:
        receipt_time = parse_time(receipt.get("collected_at"), "collector_receipt.collected_at")
        if receipt_time > evaluation_time or receipt_time > datetime.now(timezone.utc):
            issues.append("collected_at is after the report evaluation time or in the future")
    except EvidenceError:
        issues.append("collected_at is invalid")
    if receipt.get("source_views") != EXPECTED_COLLECTOR_SOURCES:
        issues.append("source_views do not match the reviewed cost SQL")
    sql_path = Path(__file__).resolve().parent / "sql" / "cost.sql"
    expected_sql_hash = None
    if sql_path.is_file():
        expected_sql_hash = f"sha256:{hashlib.sha256(sql_path.read_bytes()).hexdigest()}"
    if receipt.get("sql_sha256") != expected_sql_hash:
        issues.append("sql_sha256 does not match the reviewed cost SQL")
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
    row_count = receipt.get("row_count")
    if not isinstance(row_count, int) or isinstance(row_count, bool) or row_count < 0:
        issues.append("row_count is invalid")
    elif row_count != sum(
        len(datasets.get(name, [])) for name in RECEIPT_DATASETS if isinstance(datasets.get(name, []), list)
    ):
        issues.append("row_count does not match receipt datasets")
    row_limit = receipt.get("row_limit")
    if not isinstance(row_limit, int) or isinstance(row_limit, bool) or row_limit <= 0:
        issues.append("row_limit is invalid")
    elif row_count >= row_limit:
        issues.append("row_count is at or above the SQL cap")
    if receipt.get("truncation_possible") is not False:
        issues.append("truncation_possible is not false")
    for name in RECEIPT_DATASETS:
        source_rows = data.get(name, [])
        receipt_rows = datasets.get(name, [])
        if not _rows_match(source_rows, receipt_rows):
            issues.append(f"{name} rows do not match collector receipt")
    for issue in issues:
        warnings.append(f"collector receipt unverifiable: {issue}")
    return {
        "status": "verified" if not issues else "unverifiable",
        "complete": not issues,
        "issues": sorted(set(issues)),
        "surface": receipt.get("surface"),
        "row_count": receipt.get("row_count"),
        "row_limit": receipt.get("row_limit"),
        "truncation_possible": receipt.get("truncation_possible"),
    }


def reject_secret_fields(value: Any, path: str = "input") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = re.sub(r"[^a-z0-9]", "", str(key).casefold())
            if normalized in {"querytag", "username"}:
                raise EvidenceError(f"raw identity/tag field is not accepted: {path}.{key}; use a Snowflake-side hash")
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
        if parsed.scheme in {"http", "https"} and (parsed.query or parsed.fragment or parsed.username or parsed.password):
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
        "aggregation_eligible": role in {"total", "invoice-only"},
        "freshness_status": safe_text(freshness_status, "ledger.freshness_status"),
        "availability_status": safe_text(availability_status, "ledger.availability_status"),
        "invoice_reconciliation": invoice_status,
    }


def sum_field(rows: list[dict[str, Any]], field: str, prefix: str) -> Decimal:
    total = Decimal("0")
    for index, row in enumerate(rows):
        if field not in row or row[field] is None:
            raise EvidenceError(f"{prefix}[{index}].{field} is required")
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
    if generated < end:
        raise EvidenceError("metadata.generated_at cannot precede metadata.window_end")
    if generated > datetime.now(timezone.utc):
        raise EvidenceError("metadata.generated_at cannot be in the future")
    for field in ("account", "role", "review_owner", "approval_boundary"):
        safe_text(metadata.get(field), f"metadata.{field}")
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
    return normalized


def assess_surface_inventory(
    data: dict[str, Any],
    generated: datetime,
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
        privilege = safe_text(row.get("privilege_status", "verified"), f"{prefix}.privilege_status")
        source = safe_text(row.get("source", surface), f"{prefix}.source")
        if source != EXPECTED_SURFACE_SOURCES[surface]:
            raise EvidenceError(
                f"{prefix}.source does not match the reviewed source for {surface}"
            )
        truncated = row.get("truncated", False)
        if not isinstance(truncated, bool):
            raise EvidenceError(f"{prefix}.truncated must be boolean")
        latest: datetime | None = None
        observed_age: Decimal | None = None
        documented_latency: Decimal | None = None
        freshness_status = "unknown"
        if row.get("documented_latency_hours") is not None:
            documented_latency = decimal_value(
                row["documented_latency_hours"], f"{prefix}.documented_latency_hours"
            )
        if row.get("latest_timestamp") is not None:
            latest = parse_time(row["latest_timestamp"], f"{prefix}.latest_timestamp")
            if latest > generated:
                raise EvidenceError(f"{prefix}.latest_timestamp cannot be after metadata.generated_at")
            observed_age = Decimal(str((generated - latest).total_seconds())) / Decimal("3600")
            if documented_latency is None:
                freshness_status = "unknown"
            elif observed_age > documented_latency:
                freshness_status = "stale"
                add_finding(
                    findings,
                    "COST_SURFACE_STALE",
                    "warning",
                    surface,
                    f"Observed age {as_text(observed_age)} hours exceeds the supplied documented latency boundary.",
                )
            else:
                freshness_status = "within_boundary"
        elif status == "available" and surface in SURFACE_ARRAYS:
            add_finding(
                findings,
                "COST_SURFACE_STALE",
                "warning",
                surface,
                "The surface is marked available but has no latest source timestamp; freshness is unverifiable.",
            )
        if status != "available":
            code = "COST_ADAPTIVE_REGION_UNAVAILABLE" if surface == "adaptive_usage" and status == "region_unavailable" else "COST_SURFACE_MISSING"
            add_finding(findings, code, "warning", surface, f"Surface availability is {status}; absence is not zero usage.")
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
        assessed_row = {
            "surface": surface,
            "source": source,
            "status": status,
            "privilege_status": privilege,
            "freshness_status": freshness_status,
            "latest_timestamp": latest.isoformat() if latest else None,
            "documented_latency_hours": as_text(documented_latency) if documented_latency is not None else None,
            "observed_age_hours": as_text(observed_age) if observed_age is not None else None,
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
            "source": surface,
            "status": inferred,
            "privilege_status": "unknown",
            "freshness_status": "unknown",
            "latest_timestamp": None,
            "documented_latency_hours": None,
            "observed_age_hours": None,
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
        warnings.append(f"{key}: excluded {excluded} row(s) outside the requested half-open window")
    return selected


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
        name = safe_text(row.get("warehouse_name") or "<unknown>", f"warehouse_metering[{index}].warehouse_name")
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
        fingerprint = row.get("query_parameterized_hash") or row.get("query_hash") or row.get("query_id")
        elapsed = _optional_number(
            row.get("total_elapsed_time_ms"), f"query_attribution[{index}].total_elapsed_time_ms"
        )
        credits = decimal_value(
            row.get("credits_attributed_compute", 0), f"query_attribution[{index}].credits_attributed_compute"
        )
        if fingerprint is None or elapsed is None:
            continue
        key = (
            safe_text(row.get("warehouse_name") or "<unknown>", f"query_attribution[{index}].warehouse_name"),
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
    if request.get("max_size_steps") is not None:
        steps = decimal_value(request["max_size_steps"], "metadata.right_sizing.max_size_steps")
        if steps != steps.to_integral_value():
            raise EvidenceError("metadata.right_sizing.max_size_steps must be an integer")
        base["max_size_steps"] = int(steps)
    rollback = request.get("rollback")
    if rollback is not None:
        if not isinstance(rollback, dict):
            raise EvidenceError("metadata.right_sizing.rollback must be an object")
        rollback_size = safe_text(rollback.get("warehouse_size"), "metadata.right_sizing.rollback.warehouse_size")
        thresholds = rollback.get("thresholds")
        if not isinstance(thresholds, dict) or not thresholds:
            raise EvidenceError("metadata.right_sizing.rollback.thresholds must be a non-empty object")
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
    if rate.get("invoice_reconciled") is not True:
        warnings.append(f"{rate_key}: currency conversion is estimated and not reconciled to an invoice")
    return {
        "basis": rate_key,
        "credits": as_text(credits),
        "unit_price": as_text(unit_price),
        "currency": currency,
        "amount": as_text(credits * unit_price),
        "provenance": provenance,
        "classification": "estimated",
        "invoice_reconciliation": "reconciled" if rate.get("invoice_reconciled") is True else "not_reconciled",
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
    warnings: list[str],
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
        result[name] = rows_in_window(rows, name, start, end, warnings)
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
        qas = sum_field(queries, "credits_used_query_acceleration", "query_attribution")
        ledger.append(
            ledger_entry(
                entry_id="query-acceleration-attribution",
                domain="query_acceleration",
                source="SNOWFLAKE.ACCOUNT_USAGE.QUERY_ATTRIBUTION_HISTORY",
                role="attribution",
                unit="credits",
                amount=qas,
                parent_id="serverless-total:QUERY_ACCELERATION",
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
                entry_id=f"serverless-total:{service}",
                domain=f"serverless:{service}",
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
        ledger.append(
            ledger_entry(
                entry_id="adaptive-compute-attribution",
                domain="adaptive_compute",
                source="SNOWFLAKE.ACCOUNT_USAGE.QUERY_METERING_HISTORY",
                role="attribution",
                unit="credits",
                amount=sum_field(adaptive, "credits_used", "adaptive_usage"),
                parent_id="warehouse-compute-total",
                overlap_key="warehouse-compute",
                freshness_status=fresh,
                availability_status=available,
            )
        )

    storage = additional["storage_usage"]
    if storage:
        fresh, available = state("storage_usage")
        for field, domain in (
            ("storage_bytes", "table_storage"),
            ("stage_bytes", "stage_storage"),
            ("failsafe_bytes", "failsafe_storage"),
        ):
            ledger.append(
                ledger_entry(
                    entry_id=f"storage-context:{domain}",
                    domain=domain,
                    source="SNOWFLAKE.ACCOUNT_USAGE.STORAGE_USAGE",
                    role="context",
                    unit="bytes",
                    amount=_sum_optional(storage, field, "storage_usage"),
                    parent_id=None,
                    overlap_key=f"storage:{domain}",
                    freshness_status=fresh,
                    availability_status=available,
                )
            )
        add_finding(
            findings,
            "COST_INVOICE_ONLY",
            "info",
            "storage_usage",
            "Storage usage is operational context and uses different measurement semantics from invoice storage.",
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
        credits = sum_field(ai, "credits_used", "ai_usage")
        ledger.append(
            ledger_entry(
                entry_id="ai-functions-attribution",
                domain="cortex_ai_functions",
                source="SNOWFLAKE.ACCOUNT_USAGE.CORTEX_AI_FUNCTIONS_USAGE_HISTORY",
                role="attribution",
                unit="credits",
                amount=credits,
                parent_id="serverless-total:AI_SERVICES",
                overlap_key="service:AI_SERVICES",
                freshness_status=fresh,
                availability_status=available,
            )
        )
        if "AI_SERVICES" not in serverless_totals:
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

    for index, row in enumerate(additional["invoice_usage"]):
        domain = safe_text(row.get("domain"), f"invoice_usage[{index}].domain")
        currency = safe_text(row.get("currency"), f"invoice_usage[{index}].currency")
        statement_id = validate_hash(row.get("statement_id"), f"invoice_usage[{index}].statement_id")
        ledger.append(
            ledger_entry(
                entry_id=f"invoice:{statement_id}",
                domain=domain,
                source="customer-supplied billing statement",
                role="invoice-only",
                unit=currency,
                amount=decimal_value(row.get("amount"), f"invoice_usage[{index}].amount"),
                parent_id=None,
                overlap_key=f"invoice:{domain}:{currency}:{statement_id}",
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
        ledger.append(estimate_entry)

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
    active_monitors = 0
    for index, row in enumerate(monitors):
        validate_hash(row.get("name_sha256"), f"controls_inventory.resource_monitors[{index}].name_sha256")
        level = safe_text(row.get("level", "UNASSIGNED"), f"controls_inventory.resource_monitors[{index}].level")
        if level in {"ACCOUNT", "WAREHOUSE"}:
            active_monitors += 1
    covered_domains: set[str] = set()
    for index, row in enumerate(budgets):
        validate_hash(row.get("name_sha256"), f"controls_inventory.budgets[{index}].name_sha256")
        domains = row.get("covered_domains", [])
        if not isinstance(domains, list) or not all(isinstance(value, str) for value in domains):
            raise EvidenceError(f"controls_inventory.budgets[{index}].covered_domains must be an array")
        covered_domains.update(safe_text(value, "budget covered domain") for value in domains)
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
    if non_warehouse_present and not ({"serverless", "adaptive", "ai"} & covered_domains):
        add_finding(
            findings,
            "COST_SERVERLESS_MONITOR_GAP",
            "warning",
            "budgets",
            "Observed non-warehouse usage is outside resource-monitor coverage and no matching budget coverage was supplied.",
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
        "active_resource_monitors": active_monitors,
        "visible_budgets": len(budgets),
        "budget_covered_domains": sorted(covered_domains),
        "visibility_is_complete": controls.get("visibility_is_complete") is True,
    }


def analyze(data: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise EvidenceError("input root must be an object")
    reject_secret_fields(data)
    start, end, generated = validate_window(data)
    expected_surfaces = validate_expected_surfaces(data["metadata"])
    warehouses = validate_rows(data, "warehouse_metering")
    queries = validate_rows(data, "query_attribution")
    serverless = validate_rows(data, "serverless_usage")
    warehouse_load = validate_rows(data, "warehouse_load")
    rates = data.get("credit_rates", {})
    if not isinstance(rates, dict):
        raise EvidenceError("credit_rates must be an object")

    warnings: list[str] = []
    findings: list[dict[str, str]] = []
    collector_receipt = validate_collector_receipt(data, warnings, generated)
    warehouses = rows_in_window(warehouses, "warehouse_metering", start, end, warnings)
    queries = rows_in_window(queries, "query_attribution", start, end, warnings)
    serverless = rows_in_window(serverless, "serverless_usage", start, end, warnings)
    warehouse_load = rows_in_window(warehouse_load, "warehouse_load", start, end, warnings)
    additional = validate_additional_rows(data, start, end, warnings)
    for index, row in enumerate(queries):
        for field in ("query_hash", "query_parameterized_hash"):
            if row.get(field) is not None:
                validate_hash(row[field], f"query_attribution[{index}].{field}")
    source_freshness, freshness_warnings = freshness(data, generated, end)
    warnings.extend(freshness_warnings)
    surface_inventory, inventory_by_surface = assess_surface_inventory(
        data, generated, expected_surfaces, findings, warnings
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
        name = safe_text(
            row.get("warehouse_name") or "<unknown>",
            f"warehouse_metering[{index}].warehouse_name",
        )
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
    query_acceleration = sum_field(queries, "credits_used_query_acceleration", "query_attribution")
    untagged = Decimal("0")
    for index, row in enumerate(queries):
        credits = decimal_value(
            row.get("credits_attributed_compute", 0),
            f"query_attribution[{index}].credits_attributed_compute",
        )
        tag_present = row.get("query_tag_present")
        if not isinstance(tag_present, bool):
            raise EvidenceError(f"query_attribution[{index}].query_tag_present is required and must be boolean")
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
        name = safe_text(row.get("warehouse_name") or "<unknown>", f"warehouse_load[{index}].warehouse_name")
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
                "metric": f"serverless:{service}",
                "credits": as_text(credits),
                "classification": "confirmed",
                "source": "serverless usage evidence supplied",
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

    estimates: list[dict[str, str]] = []
    for credits, rate_key in (
        (warehouse_compute, "warehouse"),
        (query_acceleration, "query_acceleration"),
    ):
        estimate = rate_estimate(credits, rate_key, rates, warnings)
        if estimate:
            estimates.append(estimate)
    for service, credits in sorted(serverless_by_service.items()):
        estimate = rate_estimate(credits, f"serverless:{service}", rates, warnings)
        if estimate:
            estimates.append(estimate)

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
    controls_assessment = assess_controls(
        data,
        serverless,
        additional["adaptive_usage"],
        additional["ai_usage"],
        findings,
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
    return {
        "schema_version": "2.0",
        "scope": {
            "account": safe_text(data["metadata"]["account"], "metadata.account"),
            "role": safe_text(data["metadata"]["role"], "metadata.role"),
            "window_start": start.isoformat(),
            "window_end": end.isoformat(),
            "generated_at": generated.isoformat(),
        },
        "source_freshness": source_freshness,
        "surface_inventory": surface_inventory,
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
        "coverage_status": "bounded_partial"
        if warnings or any(item["severity"] != "info" for item in findings)
        else "complete_for_supplied_surfaces",
        "collector_receipt_assessment": collector_receipt,
        "completeness_claim_blocked": not collector_receipt["complete"]
        or any(item["code"] in COMPLETENESS_BLOCKING_CODES for item in findings),
        "warnings": sorted(set(warnings)),
        "non_claims": [
            "Credits are not reconciled invoice amounts.",
            "At-risk credits are not promised savings.",
            "No warehouse size, threshold, price, or SLA was inferred.",
            "No Snowflake object or configuration was mutated.",
        ],
    }


def render_markdown(result: dict[str, Any]) -> str:
    scope = result["scope"]
    lines = [
        "# Snowflake cost evidence report",
        "",
        f"Window: `{scope['window_start']}` to `{scope['window_end']}` (half-open, UTC)",
        f"Account: `{scope.get('account') or 'not supplied'}` · Role: `{scope.get('role') or 'not supplied'}`",
        f"Collector receipt: `{result['collector_receipt_assessment']['status']}`; completeness claim blocked: `{result['completeness_claim_blocked']}`",
        "",
        "## Typed cost ledger",
        "",
        "| Entry | Domain | Role | Amount | Additive | Freshness | Availability | Invoice |",
        "|---|---|---|---:|---|---|---|---|",
    ]
    for item in result["cost_ledger"]:
        lines.append(
            f"| {item['entry_id']} | {item['domain']} | {item['ledger_role']} | "
            f"{item['amount']} {item['unit']} | {item['aggregation_eligible']} | "
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
    lines.extend([
        "",
        "## Confirmed observations",
        "",
        "| Metric | Credits | Source boundary |",
        "|---|---:|---|",
    ])
    for item in result["confirmed_observations"]:
        lines.append(f"| {item['metric']} | {item['credits']} | {item['source']} |")
    lines.extend(["", "## Estimated amounts", ""])
    if result["estimated_amounts"]:
        lines.extend(["| Basis | Amount | Rate evidence |", "|---|---:|---|"])
        for item in result["estimated_amounts"]:
            lines.append(
                f"| {item['basis']} | {item['amount']} {item['currency']} | "
                f"{item['unit_price']} per credit; {item['provenance']} |"
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
    args = parser.parse_args(argv)
    try:
        data = json.loads(args.input.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise EvidenceError("input root must be an object")
        result = analyze(data)
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
