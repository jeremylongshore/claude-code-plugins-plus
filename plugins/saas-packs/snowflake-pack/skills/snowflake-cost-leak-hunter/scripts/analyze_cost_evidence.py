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
HASH_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")
SQL_HASH_PREFIXES = {"SELECT", "WITH", "INSERT", "UPDATE", "DELETE", "MERGE", "DROP", "ALTER", "CREATE", "GRANT", "REVOKE", "CALL"}


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


def validate_collector_receipt(
    data: dict[str, Any], warnings: list[str], evaluation_time: datetime
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
    sql_path = Path(__file__).resolve().parents[3] / "shared" / "evidence" / "sql" / "cost.sql"
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
    elif row_count != sum(len(datasets.get(name, [])) for name in RECEIPT_DATASETS if isinstance(datasets.get(name, []), list)):
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


def attribution_completeness(
    warehouses: list[dict[str, Any]], warnings: list[str]
) -> list[dict[str, str]]:
    """Show how much metered compute can be reconciled to query attribution.

    A NULL attribution value is an unknown boundary (for example, an adaptive
    workload), not zero.  Grouping by warehouse ID when present avoids merging
    renamed warehouses that happen to share a display name.
    """
    grouped: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(warehouses):
        name = safe_text(row.get("warehouse_name") or "<unknown>", f"warehouse_metering[{index}].warehouse_name")
        key = str(row.get("warehouse_id") or name)
        item = grouped.setdefault(key, {"warehouse_name": name, "compute": Decimal("0"), "attributed": Decimal("0"), "unknown": False})
        item["compute"] += decimal_value(row.get("credits_used_compute", 0), f"warehouse_metering[{index}].credits_used_compute")
        attributed = row.get("credits_attributed_compute_queries")
        if attributed is None:
            item["unknown"] = True
        else:
            item["attributed"] += decimal_value(attributed, f"warehouse_metering[{index}].credits_attributed_compute_queries")
    result: list[dict[str, str]] = []
    for item in grouped.values():
        compute = item["compute"]
        attributed = item["attributed"]
        if item["unknown"]:
            result.append({
                "warehouse_name": item["warehouse_name"],
                "status": "unknown",
                "compute_credits": as_text(compute),
                "attributed_query_credits": as_text(attributed),
                "attribution_fraction": "unknown",
                "unattributed_credits": "unknown",
                "reason": "one or more metering rows has NULL query attribution",
            })
            continue
        if attributed > compute:
            warnings.append(f"{item['warehouse_name']}: attributed credits exceed metered compute; completeness is inconclusive")
            result.append({
                "warehouse_name": item["warehouse_name"], "status": "inconclusive",
                "compute_credits": as_text(compute), "attributed_query_credits": as_text(attributed),
                "attribution_fraction": "inconclusive", "unattributed_credits": "inconclusive",
                "reason": "attributed credits exceed aligned metering",
            })
            continue
        fraction = attributed / compute if compute else Decimal("0")
        result.append({
            "warehouse_name": item["warehouse_name"], "status": "measured",
            "compute_credits": as_text(compute), "attributed_query_credits": as_text(attributed),
            "attribution_fraction": as_text(fraction), "unattributed_credits": as_text(compute - attributed),
            "reason": "aligned WAREHOUSE_METERING_HISTORY rows",
        })
    return sorted(result, key=lambda item: item["warehouse_name"])


def cost_latency_pareto(queries: list[dict[str, Any]], warnings: list[str]) -> list[dict[str, str | int | bool]]:
    """Return non-dominated query fingerprints for cost/latency review."""
    groups: dict[tuple[str, str], dict[str, Any]] = {}
    for index, row in enumerate(queries):
        fingerprint = row.get("query_parameterized_hash") or row.get("query_hash") or row.get("query_id")
        elapsed = _optional_number(row.get("total_elapsed_time_ms"), f"query_attribution[{index}].total_elapsed_time_ms")
        credits = decimal_value(row.get("credits_attributed_compute", 0), f"query_attribution[{index}].credits_attributed_compute")
        if fingerprint is None or elapsed is None:
            continue
        key = (
            safe_text(row.get("warehouse_name") or "<unknown>", f"query_attribution[{index}].warehouse_name"),
            validate_hash(fingerprint, f"query_attribution[{index}].query_fingerprint"),
        )
        item = groups.setdefault(key, {"warehouse_name": key[0], "fingerprint": key[1], "credits": Decimal("0"), "elapsed": Decimal("0"), "count": 0})
        item["credits"] += credits
        item["elapsed"] += elapsed
        item["count"] += 1
    if not groups and queries:
        warnings.append("cost/latency Pareto unavailable: query attribution rows lack a query fingerprint or elapsed time")
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
        result.append({
            "warehouse_name": candidate["warehouse_name"], "fingerprint": candidate["fingerprint"],
            "query_count": candidate["count"], "credits": as_text(candidate["credits"]),
            "average_elapsed_time_ms": as_text(average), "pareto_efficient": not dominated,
        })
    return sorted(result, key=lambda item: (not bool(item["pareto_efficient"]), str(item["warehouse_name"]), str(item["fingerprint"])))


def right_sizing_boundary(metadata: dict[str, Any], warnings: list[str]) -> dict[str, Any]:
    request = metadata.get("right_sizing")
    base = {
        "status": "not_requested", "warehouse": None, "current_size": None,
        "candidate_sizes": [], "max_size_steps": None, "success_criteria": None,
        "measurement_window": None, "owner": metadata.get("review_owner"),
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
    if not base["warehouse"] or not base["current_size"] or not base["candidate_sizes"] or not base["success_criteria"]:
        warnings.append("right-sizing request is bounded only when warehouse, current size, candidate sizes, and success criteria are supplied")
        base["status"] = "incomplete"
    else:
        if base["max_size_steps"] is None:
            warnings.append("right-sizing candidates supplied without max_size_steps; bounded review requires an explicit step limit")
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
    }


def analyze(data: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise EvidenceError("input root must be an object")
    reject_secret_fields(data)
    start, end, generated = validate_window(data)
    warehouses = validate_rows(data, "warehouse_metering")
    queries = validate_rows(data, "query_attribution")
    serverless = validate_rows(data, "serverless_usage")
    warehouse_load = validate_rows(data, "warehouse_load")
    rates = data.get("credit_rates", {})
    if not isinstance(rates, dict):
        raise EvidenceError("credit_rates must be an object")

    warnings: list[str] = []
    collector_receipt = validate_collector_receipt(data, warnings, generated)
    warehouses = rows_in_window(warehouses, "warehouse_metering", start, end, warnings)
    queries = rows_in_window(queries, "query_attribution", start, end, warnings)
    serverless = rows_in_window(serverless, "serverless_usage", start, end, warnings)
    warehouse_load = rows_in_window(warehouse_load, "warehouse_load", start, end, warnings)
    for index, row in enumerate(queries):
        for field in ("query_hash", "query_parameterized_hash"):
            if row.get(field) is not None:
                validate_hash(row[field], f"query_attribution[{index}].{field}")
    source_freshness, freshness_warnings = freshness(data, generated, end)
    warnings.extend(freshness_warnings)

    completeness = attribution_completeness(warehouses, warnings)
    pareto = cost_latency_pareto(queries, warnings)
    right_sizing = right_sizing_boundary(data["metadata"], warnings)

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
        provisioning = decimal_value(row.get("avg_queued_provisioning", 0), f"warehouse_load[{index}].avg_queued_provisioning")
        load_summary.append({
            "warehouse_name": name,
            "avg_running": as_text(running),
            "avg_queued_load": as_text(queued),
            "avg_queued_provisioning": as_text(provisioning),
            "classification": "confirmed",
        })
        if queued > 0 or provisioning > 0:
            warnings.append(f"{name}: warehouse load evidence shows queue pressure; correlate to query latency before resizing")
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
        "schema_version": "1.0",
        "scope": {
            "account": safe_text(data["metadata"]["account"], "metadata.account"),
            "role": safe_text(data["metadata"]["role"], "metadata.role"),
            "window_start": start.isoformat(),
            "window_end": end.isoformat(),
            "generated_at": generated.isoformat(),
        },
        "source_freshness": source_freshness,
        "confirmed_observations": confirmed,
        "estimated_amounts": estimates,
        "at_risk_opportunities": at_risk,
        "attribution_completeness": completeness,
        "warehouse_load_summary": load_summary,
        "cost_latency_pareto": pareto,
        "right_sizing_experiment": right_sizing,
        "approval_queue": approval_queue,
        "coverage_status": "bounded_partial" if warnings else "complete_for_supplied_surfaces",
        "collector_receipt_assessment": collector_receipt,
        "completeness_claim_blocked": not collector_receipt["complete"],
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
        "## Confirmed observations",
        "",
        "| Metric | Credits | Source boundary |",
        "|---|---:|---|",
    ]
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
    lines.extend(["", "## Attribution completeness", "", "| Warehouse | Status | Metered credits | Attributed credits | Fraction | Unattributed |", "|---|---|---:|---:|---:|---:|"])
    for item in result["attribution_completeness"]:
        lines.append(f"| {item['warehouse_name']} | {item['status']} | {item['compute_credits']} | {item['attributed_query_credits']} | {item['attribution_fraction']} | {item['unattributed_credits']} |")
    lines.extend(["", "## Cost/latency Pareto", ""])
    if result["cost_latency_pareto"]:
        lines.extend(["| Warehouse | Fingerprint | Queries | Credits | Avg elapsed ms | Pareto-efficient |", "|---|---|---:|---:|---:|---|"])
        for item in result["cost_latency_pareto"]:
            lines.append(f"| {item['warehouse_name']} | {item['fingerprint']} | {item['query_count']} | {item['credits']} | {item['average_elapsed_time_ms']} | {item['pareto_efficient']} |")
    else:
        lines.append("No fingerprinted query rows had both cost and latency; Pareto position is unknown.")
    lines.extend(["", "## Right-sizing experiment boundary", "", f"Status: `{result['right_sizing_experiment']['status']}`; no mutation executed.", ""])
    lines.append("Supply an owner-approved bounded candidate set and success criteria before any resize experiment is considered.")
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
