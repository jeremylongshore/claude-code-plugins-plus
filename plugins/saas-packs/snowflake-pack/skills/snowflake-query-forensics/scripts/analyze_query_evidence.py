#!/usr/bin/env python3
"""Validate and classify normalized Snowflake query evidence without mutation."""

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


class EvidenceError(ValueError):
    """Raised when query evidence is malformed or unsafe to interpret."""


EXPECTED_COLLECTOR_SOURCES = [
    "SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY",
    "SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_LOAD_HISTORY",
]
HASH_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")
QUERY_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,255}$")
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


def validate_query_id(value: Any, field: str) -> str:
    if not isinstance(value, str) or not QUERY_ID_RE.fullmatch(value):
        raise EvidenceError(f"{field} must be an opaque Snowflake query ID")
    if any(token in value.upper() for token in ("SELECT", "UNION", "DROP", "--", "/*", "*/", ";", "'")):
        raise EvidenceError(f"{field} must be an opaque Snowflake query ID, not SQL")
    return value


def validate_subsurface_receipt(
    value: Any, label: str, surface: str, query_id: str, evaluation_time: datetime
) -> dict[str, Any]:
    if value is None:
        return {"status": "not_supplied", "complete": False, "issues": [f"{label} receipt not supplied"]}
    if not isinstance(value, dict):
        return {"status": "unverifiable", "complete": False, "issues": [f"{label} receipt is not an object"]}
    issues: list[str] = []
    if value.get("schema_version") != "1":
        issues.append("schema_version is not 1")
    if value.get("surface") != surface:
        issues.append(f"surface is not {surface}")
    if value.get("status") != "collected":
        issues.append("status is not collected")
    if value.get("errors"):
        issues.append("collector reported an error")
    if value.get("truncation_possible") is not False:
        issues.append("truncation_possible is not false")
    metadata = value.get("source_metadata")
    if not isinstance(metadata, dict) or metadata.get("selector") != {"query_id": True}:
        issues.append("source_metadata.selector is not the privacy-safe query_id binding")
    if not isinstance(metadata, dict) or metadata.get("template") != f"{surface}.sql":
        issues.append(f"source_metadata.template is not {surface}.sql")
    selector_body = {"query_id": query_id}
    expected_fingerprint = f"sha256:{hashlib.sha256(_canonical_json(selector_body)).hexdigest()}"
    if value.get("selector_fingerprint") != expected_fingerprint:
        issues.append("selector_fingerprint does not match metadata.query_id")
    for field in ("sql_sha256", "template_sha256", "rendered_sql_sha256"):
        if not isinstance(value.get(field), str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", value[field]):
            issues.append(f"{field} is missing or malformed")
    if value.get("sql_sha256") != value.get("template_sha256"):
        issues.append("sql_sha256 does not match template_sha256")
    try:
        if parse_time(value.get("collected_at"), f"{label}.collected_at") > evaluation_time:
            issues.append("collected_at is after evaluation time")
    except EvidenceError:
        issues.append("collected_at is invalid")
    supplied_receipt_hash = value.get("receipt_sha256")
    body = dict(value)
    body.pop("receipt_sha256", None)
    expected_receipt_hash = f"sha256:{hashlib.sha256(_canonical_json(body)).hexdigest()}"
    if supplied_receipt_hash != expected_receipt_hash:
        issues.append("receipt_sha256 is missing or invalid")
    return {"status": "verified" if not issues else "unverifiable", "complete": not issues, "issues": issues}


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
    if receipt.get("surface") != "query":
        issues.append("surface is not query")
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
        issues.append("source_views do not match the reviewed query SQL")
    sql_path = Path(__file__).resolve().parent / "sql" / "query.sql"
    expected_sql_hash = None
    if sql_path.is_file():
        expected_sql_hash = f"sha256:{hashlib.sha256(sql_path.read_bytes()).hexdigest()}"
    if receipt.get("sql_sha256") != expected_sql_hash:
        issues.append("sql_sha256 does not match the reviewed query SQL")
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
    elif row_count != sum(len(value) for value in datasets.values() if isinstance(value, list)):
        issues.append("row_count does not match receipt datasets")
    row_limit = receipt.get("row_limit")
    if not isinstance(row_limit, int) or isinstance(row_limit, bool) or row_limit <= 0:
        issues.append("row_limit is invalid")
    elif row_count >= row_limit:
        issues.append("row_count is at or above the SQL cap")
    if receipt.get("truncation_possible") is not False:
        issues.append("truncation_possible is not false")
    for name in ("query_history", "warehouse_load"):
        supplied = data.get(name, [])
        supplied_rows = [supplied] if name == "query_history" and isinstance(supplied, dict) else supplied
        if not _rows_match(supplied_rows, datasets.get(name, [])):
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


SENSITIVE_KEYS = {
    "apikey",
    "authorization",
    "credential",
    "credentials",
    "jwt",
    "oauthcode",
    "oauthtoken",
    "passphrase",
    "password",
    "privatekey",
    "secret",
    "secretaccesskey",
    "sessiontoken",
    "token",
}
REDACTIONS = (
    (re.compile(r"https?://\S+", re.IGNORECASE), "[REDACTED_URL]"),
    (re.compile(r"\bBearer\s+\S+", re.IGNORECASE), "[REDACTED_BEARER]"),
    (re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b"), "[REDACTED_EMAIL]"),
    (
        re.compile(
            r"(?i)\b[\w-]*(password|passphrase|token|secret|credential|private[_-]?key|authorization|jwt|api[_-]?key)[\w-]*\s*[=:]\s*\S+"
        ),
        "[REDACTED_CREDENTIAL]",
    ),
)


def reject_secret_fields(value: Any, path: str = "input") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = re.sub(r"[^a-z0-9]", "", str(key).casefold())
            if normalized in {"querytag", "username"}:
                raise EvidenceError(f"raw identity/tag field is not accepted: {path}.{key}; use a Snowflake-side hash")
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
                raise EvidenceError(f"credential-bearing field is not accepted: {path}.{key}")
            reject_secret_fields(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            reject_secret_fields(child, f"{path}[{index}]")


def safe_text(value: Any) -> str:
    text = str(value)
    for pattern, replacement in REDACTIONS:
        text = pattern.sub(replacement, text)
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
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise EvidenceError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise EvidenceError(f"{field} must include a timezone")
    return parsed.astimezone(timezone.utc)


def as_text(number: Decimal) -> str:
    return format(number.quantize(Decimal("0.000001")).normalize(), "f")


def nested_number(container: dict[str, Any], path: tuple[str, ...], field: str) -> Decimal:
    current: Any = container
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return Decimal("0")
        current = current[key]
    return decimal_value(current, field)


def load_summary(
    rows: Any,
    warnings: list[str],
    query_start: datetime,
    query_end: datetime,
    query_warehouse: str,
) -> list[dict[str, str]]:
    if rows is None:
        return []
    if not isinstance(rows, list) or not all(isinstance(item, dict) for item in rows):
        raise EvidenceError("warehouse_load must be an array of objects")
    grouped: dict[str, dict[str, Decimal]] = {}
    excluded = 0
    for index, row in enumerate(rows):
        prefix = f"warehouse_load[{index}]"
        if row.get("start_time") is None or row.get("end_time") is None:
            raise EvidenceError(f"{prefix}.start_time and end_time are required for query alignment")
        row_start = parse_time(row["start_time"], f"{prefix}.start_time")
        row_end = parse_time(row["end_time"], f"{prefix}.end_time")
        if row_start >= row_end:
            raise EvidenceError(f"{prefix}.start_time must be before end_time")
        name = str(row.get("warehouse_name") or "<unknown>")
        if name != query_warehouse or row_end <= query_start or row_start >= query_end:
            excluded += 1
            continue
        item = grouped.setdefault(
            name,
            {
                "running": Decimal("0"),
                "queued": Decimal("0"),
                "provisioning": Decimal("0"),
                "blocked": Decimal("0"),
                "rows": Decimal("0"),
            },
        )
        for source, target in (
            ("avg_running", "running"),
            ("avg_queued_load", "queued"),
            ("avg_queued_provisioning", "provisioning"),
            ("avg_blocked", "blocked"),
        ):
            if row.get(source) is not None:
                item[target] += decimal_value(row[source], f"warehouse_load[{index}].{source}")
        item["rows"] += 1
    if excluded:
        warnings.append(f"warehouse_load: excluded {excluded} row(s) outside the query interval or warehouse")
    result = []
    for name, values in grouped.items():
        result.append(
            {
                "warehouse_name": name,
                "interval_count": as_text(values["rows"]),
                "avg_running_load_sum": as_text(values["running"]),
                "avg_queued_load_sum": as_text(values["queued"]),
                "avg_queued_provisioning_sum": as_text(values["provisioning"]),
                "avg_blocked_sum": as_text(values["blocked"]),
                "classification": "confirmed",
            }
        )
        if values["queued"] > 0 or values["provisioning"] > 0:
            warnings.append(
                f"{name}: warehouse load shows queue/provisioning pressure; align it with this query's wait timeline"
            )
    return sorted(result, key=lambda item: item["warehouse_name"])


def hash_comparison(data: dict[str, Any], warnings: list[str]) -> list[dict[str, Any]]:
    supplied = data.get("query_runs")
    if supplied is None:
        supplied = [data["query_history"]]
    if not isinstance(supplied, list) or not all(isinstance(item, dict) for item in supplied):
        raise EvidenceError("query_runs must be an array of objects")
    if len(supplied) > 1:
        alignment = data.get("comparison_alignment")
        required = ("warehouse_name", "data_scope", "parameters", "cache_state", "session_parameters")
        if not isinstance(alignment, dict) or alignment.get("status") != "aligned":
            warnings.append("query hash comparison unavailable: explicit aligned comparison receipt is missing")
            return []
        missing = [field for field in required if field not in alignment or alignment[field] is None]
        if missing:
            warnings.append(
                "query hash comparison unavailable: aligned comparison receipt is missing " + ", ".join(missing)
            )
            return []
        if any(not isinstance(alignment[field], (str, dict, list, bool, int, float)) for field in required):
            warnings.append("query hash comparison unavailable: aligned comparison receipt contains invalid fields")
            return []
    else:
        alignment = None
    groups: dict[str, list[tuple[Decimal, str | None]]] = {}
    invalid = False
    for index, row in enumerate(supplied):
        fingerprint = row.get("query_parameterized_hash") or row.get("query_hash")
        elapsed = row.get("total_elapsed_time_ms")
        if fingerprint is None or elapsed is None or not row.get("query_id"):
            warnings.append(f"query_runs[{index}]: fingerprint, elapsed time, and query_id are required for comparison")
            invalid = True
            continue
        fingerprint = validate_hash(fingerprint, f"query_runs[{index}].query_fingerprint")
        run_id = validate_query_id(row.get("query_id"), f"query_runs[{index}].query_id")
        if alignment is not None and row.get("warehouse_name") != alignment.get("warehouse_name"):
            warnings.append(f"query_runs[{index}]: warehouse does not match aligned comparison receipt")
            invalid = True
            continue
        value = decimal_value(elapsed, f"query_runs[{index}].total_elapsed_time_ms")
        group_key = str(fingerprint)
        groups.setdefault(group_key, []).append((value, run_id))
    if invalid:
        return []
    if not groups:
        warnings.append("query hash comparison unavailable: no fingerprinted runs with elapsed time")
    result = []
    for fingerprint, runs in groups.items():
        values = [value for value, _ in runs]
        result.append(
            {
                "fingerprint": safe_text(fingerprint),
                "sample_count": len(values),
                "average_elapsed_time_ms": as_text(sum(values, Decimal("0")) / len(values)),
                "min_elapsed_time_ms": as_text(min(values)),
                "max_elapsed_time_ms": as_text(max(values)),
                "query_ids": [safe_text(str(query_id)) for _, query_id in runs if query_id is not None],
                "classification": "derived",
            }
        )
    return sorted(result, key=lambda item: str(item["fingerprint"]))


def search_optimization_roi(data: dict[str, Any], warnings: list[str]) -> list[dict[str, str]]:
    supplied = data.get("search_optimization")
    if supplied is None:
        return []
    if isinstance(supplied, dict):
        supplied = [supplied]
    if not isinstance(supplied, list) or not all(isinstance(item, dict) for item in supplied):
        raise EvidenceError("search_optimization must be an object or array of objects")
    result: list[dict[str, str]] = []
    for index, row in enumerate(supplied):
        for field in (
            "credits_used",
            "query_count",
            "latency_before_ms",
            "latency_after_ms",
            "bytes_scanned_before",
            "bytes_scanned_after",
        ):
            if field in row and row[field] is not None:
                decimal_value(row[field], f"search_optimization[{index}].{field}")
        credits = decimal_value(row.get("credits_used", 0), f"search_optimization[{index}].credits_used")
        before_latency = row.get("latency_before_ms")
        after_latency = row.get("latency_after_ms")
        before_bytes = row.get("bytes_scanned_before")
        after_bytes = row.get("bytes_scanned_after")
        item: dict[str, str] = {"classification": "derived", "credits_used": as_text(credits)}
        if before_latency is not None and after_latency is not None:
            latency_delta = decimal_value(
                before_latency, f"search_optimization[{index}].latency_before_ms"
            ) - decimal_value(after_latency, f"search_optimization[{index}].latency_after_ms")
            item["latency_reduction_ms"] = as_text(latency_delta)
        if before_bytes is not None and after_bytes is not None:
            bytes_delta = decimal_value(
                before_bytes, f"search_optimization[{index}].bytes_scanned_before"
            ) - decimal_value(after_bytes, f"search_optimization[{index}].bytes_scanned_after")
            item["bytes_scanned_reduction"] = as_text(bytes_delta)
        if credits > 0 and "latency_reduction_ms" not in item and "bytes_scanned_reduction" not in item:
            warnings.append(
                "search optimization credits supplied without a measured latency or scan baseline; ROI is unknown"
            )
        item["decision"] = "review measured benefit against maintenance credits; no SOS change proposed"
        result.append(item)
    return result


def analyze(data: dict[str, Any]) -> dict[str, Any]:
    reject_secret_fields(data)
    metadata = data.get("metadata")
    history = data.get("query_history")
    if not isinstance(metadata, dict):
        raise EvidenceError("metadata must be an object")
    if not isinstance(history, dict):
        raise EvidenceError("query_history must be an object")
    query_id = metadata.get("query_id")
    query_id = validate_query_id(query_id, "metadata.query_id")
    history_query_id = history.get("query_id")
    history_query_id = validate_query_id(history_query_id, "query_history.query_id")
    if history_query_id != query_id:
        raise EvidenceError("metadata.query_id must match query_history.query_id")
    for field in ("query_hash", "query_parameterized_hash"):
        if history.get(field) is not None:
            validate_hash(history[field], f"query_history.{field}")
    for field in ("account", "role", "history_source", "experiment_owner"):
        if not isinstance(metadata.get(field), str) or not metadata[field].strip():
            raise EvidenceError(f"metadata.{field} is required")
    if not isinstance(history.get("warehouse_name"), str) or not history["warehouse_name"].strip():
        raise EvidenceError("query_history.warehouse_name is required")
    collected_at = parse_time(metadata.get("collected_at"), "metadata.collected_at")
    source_max_time = parse_time(metadata.get("history_source_max_time"), "metadata.history_source_max_time")
    if source_max_time > collected_at:
        raise EvidenceError("metadata.history_source_max_time cannot be later than metadata.collected_at")
    if collected_at > datetime.now(timezone.utc):
        raise EvidenceError("metadata.collected_at cannot be in the future")
    observed_age = Decimal(str((collected_at - source_max_time).total_seconds()))

    operators = data.get("operators", [])
    insights = data.get("query_insights", [])
    if not isinstance(operators, list) or not all(isinstance(item, dict) for item in operators):
        raise EvidenceError("operators must be an array of objects")
    if not isinstance(insights, list) or not all(isinstance(item, dict) for item in insights):
        raise EvidenceError("query_insights must be an array of objects")

    confirmed: list[dict[str, str]] = []
    derived: list[dict[str, str]] = []
    hypotheses: list[dict[str, str]] = []
    warnings: list[str] = []
    collector_receipt = validate_collector_receipt(data, warnings, collected_at)
    operator_receipt = validate_subsurface_receipt(
        data.get("operator_stats_receipt", data.get("operator_collection_receipt")),
        "operator statistics",
        "query-operator-stats",
        query_id,
        collected_at,
    )
    insights_receipt = validate_subsurface_receipt(
        data.get("query_insights_receipt", data.get("insights_collection_receipt")),
        "Query Insights",
        "query-insights",
        query_id,
        collected_at,
    )
    source_max_age = metadata.get("source_max_age_seconds", 2700)
    if type(source_max_age) is not int or source_max_age <= 0:
        raise EvidenceError("metadata.source_max_age_seconds must be a positive integer")
    source_freshness_ok = observed_age <= source_max_age
    if not source_freshness_ok:
        warnings.append("query history source exceeds the declared freshness bound")
    experiment_owner = str(metadata["experiment_owner"])
    query_start = query_end = None
    if data.get("warehouse_load"):
        query_start = parse_time(history.get("start_time"), "query_history.start_time")
        query_end = parse_time(history.get("end_time"), "query_history.end_time")
        if query_start >= query_end:
            raise EvidenceError("query_history.start_time must be before end_time")
    warehouse_load = load_summary(
        data.get("warehouse_load", []),
        warnings,
        query_start or datetime.min.replace(tzinfo=timezone.utc),
        query_end or datetime.max.replace(tzinfo=timezone.utc),
        history["warehouse_name"],
    )
    hash_comparison_rows = hash_comparison(data, warnings)
    sos_roi = search_optimization_roi(data, warnings)

    status = str(history.get("execution_status") or "unknown").lower()
    operator_evidence_eligible = status in {"success", "fail", "incident"}
    if not operator_evidence_eligible:
        operators = []
        insights = []
    timing_fields = (
        ("compilation_time_ms", "compilation"),
        ("execution_time_ms", "execution"),
        ("queued_overload_time_ms", "warehouse queue overload"),
        ("queued_provisioning_time_ms", "warehouse provisioning wait"),
        ("queued_repair_time_ms", "warehouse repair wait"),
        ("transaction_blocked_time_ms", "transaction blocked wait"),
    )
    timeline: dict[str, str | None] = {}
    supplied_component_total = Decimal("0")
    for field, label in timing_fields:
        if field not in history or history[field] is None:
            timeline[field] = None
            continue
        value = decimal_value(history[field], f"query_history.{field}")
        timeline[field] = as_text(value)
        supplied_component_total += value
        if value > 0:
            confirmed.append(
                {
                    "kind": "timing",
                    "metric": field,
                    "value": as_text(value),
                    "unit": "milliseconds",
                    "classification": "confirmed",
                    "observation": label,
                }
            )
            if field == "queued_overload_time_ms":
                hypotheses.append(
                    {
                        "hypothesis": "concurrency or workload-placement pressure",
                        "classification": "at-risk",
                        "evidence": f"{as_text(value)} ms queued for overload",
                        "competing_explanation": "temporary burst or intentionally bounded capacity",
                        "next_read_only_check": "correlate warehouse load over the same interval",
                    }
                )
            if field == "transaction_blocked_time_ms":
                hypotheses.append(
                    {
                        "hypothesis": "transaction lock contention",
                        "classification": "at-risk",
                        "evidence": f"{as_text(value)} ms transaction-blocked time",
                        "competing_explanation": "expected serialization for the workload",
                        "next_read_only_check": "identify blocker and waiter transactions without terminating either",
                    }
                )

    if history.get("total_elapsed_time_ms") is not None:
        total_elapsed = decimal_value(history["total_elapsed_time_ms"], "query_history.total_elapsed_time_ms")
        timeline["total_elapsed_time_ms"] = as_text(total_elapsed)
        difference = total_elapsed - supplied_component_total
        if difference >= 0:
            timeline["other_or_unexplained_time_ms"] = as_text(difference)
        else:
            timeline["other_or_unexplained_time_ms"] = None
            warnings.append("supplied timing components exceed total elapsed time; verify source semantics and overlap")
    else:
        timeline["total_elapsed_time_ms"] = None
        timeline["other_or_unexplained_time_ms"] = None
        warnings.append("total elapsed time absent; supplied timing fields cannot be reconciled")

    for field, unit in (
        ("bytes_scanned", "bytes"),
        ("partitions_scanned", "partitions"),
        ("partitions_total", "partitions"),
        ("bytes_spilled_to_local_storage", "bytes"),
        ("bytes_spilled_to_remote_storage", "bytes"),
    ):
        if history.get(field) is None:
            continue
        value = decimal_value(history[field], f"query_history.{field}")
        confirmed.append(
            {
                "kind": "query_history",
                "metric": field,
                "value": as_text(value),
                "unit": unit,
                "classification": "confirmed",
                "observation": "QUERY_HISTORY counter supplied",
            }
        )
    top_operators: list[dict[str, str]] = []
    for index, operator in enumerate(operators):
        if (
            operator.get("query_id") is not None
            and validate_query_id(operator["query_id"], f"operators[{index}].query_id") != query_id
        ):
            raise EvidenceError(f"operators[{index}].query_id must match metadata.query_id")
        operator_id = str(operator.get("operator_id", index))
        operator_type = str(operator.get("operator_type") or "unknown")
        statistics = operator.get("operator_statistics") or {}
        breakdown = operator.get("execution_time_breakdown") or {}
        if not isinstance(statistics, dict) or not isinstance(breakdown, dict):
            raise EvidenceError(f"operators[{index}] statistics and breakdown must be objects")

        overall = decimal_value(
            breakdown.get("overall_percentage", 0),
            f"operators[{index}].execution_time_breakdown.overall_percentage",
        )
        if overall > 100:
            raise EvidenceError(f"operators[{index}].execution_time_breakdown.overall_percentage cannot exceed 100")
        top_operators.append(
            {
                "operator_id": operator_id,
                "operator_type": operator_type,
                "overall_percentage": as_text(overall),
            }
        )

        remote_spill = nested_number(
            statistics,
            ("spilling", "bytes_spilled_remote_storage"),
            f"operators[{index}].operator_statistics.spilling.bytes_spilled_remote_storage",
        )
        local_spill = nested_number(
            statistics,
            ("spilling", "bytes_spilled_local_storage"),
            f"operators[{index}].operator_statistics.spilling.bytes_spilled_local_storage",
        )
        for metric, value in (
            ("bytes_spilled_remote_storage", remote_spill),
            ("bytes_spilled_local_storage", local_spill),
        ):
            if value > 0:
                confirmed.append(
                    {
                        "kind": "operator",
                        "metric": metric,
                        "value": as_text(value),
                        "unit": "bytes",
                        "operator_id": operator_id,
                        "operator_type": operator_type,
                        "classification": "confirmed",
                        "observation": "spill recorded by operator statistics",
                    }
                )
        if remote_spill > 0:
            hypotheses.append(
                {
                    "hypothesis": "query shape or warehouse capacity contributed to remote spill",
                    "classification": "at-risk",
                    "evidence": f"operator {operator_id} recorded {as_text(remote_spill)} remote-spill bytes",
                    "competing_explanation": "data-volume change or intentional batch shape",
                    "next_read_only_check": "compare the same parameterized hash and aligned data volume",
                }
            )

        input_rows = statistics.get("input_rows")
        output_rows = statistics.get("output_rows")
        if input_rows is not None and output_rows is not None:
            input_value = decimal_value(input_rows, f"operators[{index}].operator_statistics.input_rows")
            output_value = decimal_value(output_rows, f"operators[{index}].operator_statistics.output_rows")
            if input_value > 0:
                multiple = output_value / input_value
                derived.append(
                    {
                        "metric": "output_to_input_row_multiple",
                        "value": as_text(multiple),
                        "operator_id": operator_id,
                        "operator_type": operator_type,
                        "classification": "estimated",
                        "basis": "output_rows / input_rows",
                    }
                )
                if operator_type.lower() in {"join", "cartesianjoin"} and multiple > 1:
                    hypotheses.append(
                        {
                            "hypothesis": "join expansion requires semantic review",
                            "classification": "at-risk",
                            "evidence": f"operator {operator_id} output/input multiple {as_text(multiple)}",
                            "competing_explanation": "valid many-to-many join semantics",
                            "next_read_only_check": "review approved redacted join predicates and baseline cardinality",
                        }
                    )

        scanned = nested_number(
            statistics,
            ("pruning", "partitions_scanned"),
            f"operators[{index}].operator_statistics.pruning.partitions_scanned",
        )
        total = nested_number(
            statistics,
            ("pruning", "partitions_total"),
            f"operators[{index}].operator_statistics.pruning.partitions_total",
        )
        if total > 0:
            if scanned > total:
                raise EvidenceError(f"operators[{index}] partitions_scanned cannot exceed partitions_total")
            ratio = scanned / total
            derived.append(
                {
                    "metric": "partitions_scanned_fraction",
                    "value": as_text(ratio),
                    "operator_id": operator_id,
                    "operator_type": operator_type,
                    "classification": "estimated",
                    "basis": "partitions_scanned / partitions_total",
                }
            )
            if scanned == total:
                hypotheses.append(
                    {
                        "hypothesis": "no partition pruning observed for this scan",
                        "classification": "at-risk",
                        "evidence": f"operator {operator_id} scanned {as_text(scanned)} of {as_text(total)} partitions",
                        "competing_explanation": "the query may intentionally require the full table",
                        "next_read_only_check": "compare predicates and data layout for the same query hash",
                    }
                )

    top_operators.sort(key=lambda item: Decimal(item["overall_percentage"]), reverse=True)

    for index, insight in enumerate(insights):
        if (
            insight.get("query_id") is not None
            and validate_query_id(insight["query_id"], f"query_insights[{index}].query_id") != query_id
        ):
            raise EvidenceError(f"query_insights[{index}].query_id must match metadata.query_id")
        type_id = insight.get("type_id")
        if not isinstance(type_id, str) or not type_id.strip():
            raise EvidenceError(f"query_insights[{index}].type_id is required")
        confirmed.append(
            {
                "kind": "query_insight",
                "metric": type_id,
                "value": safe_text(insight.get("message") or "platform insight returned"),
                "unit": "message",
                "classification": "confirmed",
                "observation": "Snowflake Query Insight supplied",
            }
        )

    if not operator_evidence_eligible:
        warnings.append(f"execution status is {status}; operator statistics may be unavailable until completion")
    if not operators:
        warnings.append("operator statistics absent; operator-level conditions are unknown, not zero")
    insight_status = data.get("query_insights_status")
    if insight_status is not None:
        if not isinstance(insight_status, dict):
            raise EvidenceError("query_insights_status must be an object")
        status_value = str(insight_status.get("status") or "unknown")
        if status_value not in {"available", "unavailable", "excluded", "unknown"}:
            raise EvidenceError("query_insights_status.status must be available, unavailable, excluded, or unknown")
        insight_coverage = {"status": status_value, "reason": safe_text(insight_status.get("reason") or "not supplied")}
    else:
        insight_coverage = {
            "status": "available" if insights else "unknown",
            "reason": "rows supplied"
            if insights
            else "no row supplied; exclusion, latency, or no signal are all possible",
        }
    if not insights:
        warnings.append(f"no Query Insights supplied; absence is not proof; {insight_coverage['reason']}")

    for hypothesis in hypotheses:
        hypothesis["falsification_evidence"] = (
            "an aligned repeat with the same parameterized hash and fixed inputs does not reproduce the condition"
        )
        hypothesis["experiment_owner"] = experiment_owner

    return {
        "schema_version": "1.0",
        "query": {
            "query_id": query_id,
            "execution_status": status,
            "account": metadata.get("account"),
            "role": metadata.get("role"),
            "warehouse_name": history.get("warehouse_name"),
            "query_hash": history.get("query_hash"),
            "query_parameterized_hash": history.get("query_parameterized_hash"),
        },
        "history_source": metadata.get("history_source"),
        "history_source_max_time": source_max_time.isoformat(),
        "collected_at": collected_at.isoformat(),
        "observed_history_age_seconds": as_text(observed_age),
        "timeline_ms": timeline,
        "confirmed_observations": confirmed,
        "estimated_or_derived_metrics": derived,
        "at_risk_hypotheses": hypotheses,
        "top_operators_by_observed_percentage": top_operators,
        "warehouse_load_summary": warehouse_load,
        "query_hash_comparison": hash_comparison_rows,
        "collector_receipt_assessment": collector_receipt,
        "operator_stats_receipt_assessment": operator_receipt,
        "query_insights_receipt_assessment": insights_receipt,
        "source_freshness": {
            "observed_age_seconds": as_text(observed_age),
            "max_age_seconds": source_max_age,
            "status": "FRESH" if source_freshness_ok else "STALE",
            "documented_latency": "QUERY_HISTORY up to 45 minutes; Query Insights up to 90 minutes",
        },
        "completeness_claim_blocked": (
            not collector_receipt["complete"]
            or not source_freshness_ok
            or ("operator_stats_receipt" in data and not operator_receipt["complete"])
            or ("operator_collection_receipt" in data and not operator_receipt["complete"])
            or ("query_insights_receipt" in data and not insights_receipt["complete"])
            or ("insights_collection_receipt" in data and not insights_receipt["complete"])
        ),
        "search_optimization_roi": sos_roi,
        "query_insights_coverage": insight_coverage,
        "one_variable_experiment": {
            "status": "not_proposed",
            "owner": experiment_owner,
            "baseline": "use this packet only after timing/source reconciliation",
            "change": None,
            "fixed_inputs": "same parameterized hash, aligned data window, role, warehouse, and session context",
            "measurement_window": None,
            "success_criteria": None,
            "impact": "unknown until an operator supplies one proposed variable",
            "approval": "explicit workload owner and Snowflake change approver required",
            "rollback": "define reversal for the single selected variable before execution",
        },
        "warnings": sorted(set(warnings)),
        "non_claims": [
            "No single metric was treated as a proven root cause.",
            "No universal performance threshold or SLA was applied.",
            "No SQL, warehouse, clustering, session, or query state was mutated.",
            "Raw query text was not required by this evidence contract.",
        ],
    }


def render_markdown(result: dict[str, Any]) -> str:
    query = result["query"]
    lines = [
        "# Snowflake query forensics packet",
        "",
        f"Query: `{query['query_id']}` · Status: `{query['execution_status']}`",
        f"Account: `{query.get('account') or 'not supplied'}` · Role: `{query.get('role') or 'not supplied'}`",
        f"History source: `{result.get('history_source') or 'not supplied'}`; observed age {result['observed_history_age_seconds']} seconds",
        f"Collector receipt: `{result['collector_receipt_assessment']['status']}`; completeness claim blocked: `{result['completeness_claim_blocked']}`",
        "",
        "## Timeline (milliseconds)",
        "",
        "| Field | Supplied/reconciled value |",
        "|---|---:|",
    ]
    for field, value in result["timeline_ms"].items():
        lines.append(f"| {field} | {value if value is not None else 'not supplied'} |")
    lines.extend(
        [
            "",
            "## Confirmed observations",
            "",
        ]
    )
    if result["confirmed_observations"]:
        lines.extend(["| Evidence | Value | Context |", "|---|---:|---|"])
        for item in result["confirmed_observations"]:
            lines.append(f"| {item['metric']} | {item['value']} {item['unit']} | {item['observation']} |")
    else:
        lines.append("No positive confirmed condition was present in the supplied fields.")
    lines.extend(["", "## Estimated or derived metrics", ""])
    if result["estimated_or_derived_metrics"]:
        lines.extend(["| Metric | Value | Basis |", "|---|---:|---|"])
        for item in result["estimated_or_derived_metrics"]:
            lines.append(f"| {item['metric']} | {item['value']} | {item['basis']} |")
    else:
        lines.append("No derived metric was computable from the supplied evidence.")
    lines.extend(["", "## At-risk hypotheses — corroboration required", ""])
    if result["at_risk_hypotheses"]:
        for item in result["at_risk_hypotheses"]:
            lines.extend(
                [
                    f"### {item['hypothesis']}",
                    "",
                    f"- Evidence: {item['evidence']}",
                    f"- Competing explanation: {item['competing_explanation']}",
                    f"- Next read-only check: {item['next_read_only_check']}",
                    f"- Falsification evidence: {item['falsification_evidence']}",
                    f"- Experiment owner: {item['experiment_owner']}",
                    "",
                ]
            )
    else:
        lines.append("No hypothesis was generated from the supplied evidence.")
    lines.extend(["", "## Warehouse load correlation", ""])
    lines.append(
        f"Query Insights coverage: `{result['query_insights_coverage']['status']}` — {result['query_insights_coverage']['reason']}"
    )
    if result["warehouse_load_summary"]:
        lines.extend(
            [
                "",
                "| Warehouse | Intervals | Running load | Queued load | Provisioning load | Blocked load |",
                "|---|---:|---:|---:|---:|---:|",
            ]
        )
        for item in result["warehouse_load_summary"]:
            lines.append(
                f"| {item['warehouse_name']} | {item['interval_count']} | {item['avg_running_load_sum']} | {item['avg_queued_load_sum']} | {item['avg_queued_provisioning_sum']} | {item['avg_blocked_sum']} |"
            )
    else:
        lines.append("No warehouse load rows supplied; queue cause remains unknown.")
    lines.extend(["", "## Query-hash comparison", ""])
    for item in result["query_hash_comparison"]:
        lines.append(
            f"- `{item['fingerprint']}` — {item['sample_count']} run(s), average {item['average_elapsed_time_ms']} ms, range {item['min_elapsed_time_ms']}–{item['max_elapsed_time_ms']} ms."
        )
    if not result["query_hash_comparison"]:
        lines.append("No comparable query fingerprint was supplied.")
    lines.extend(["", "## Search Optimization Service ROI", ""])
    if result["search_optimization_roi"]:
        for item in result["search_optimization_roi"]:
            lines.append(
                f"- Credits used: {item['credits_used']}; latency reduction: {item.get('latency_reduction_ms', 'unknown')} ms; bytes reduction: {item.get('bytes_scanned_reduction', 'unknown')}; {item['decision']}."
            )
    else:
        lines.append("No Search Optimization Service ROI evidence supplied; benefit and maintenance cost are unknown.")
    experiment = result["one_variable_experiment"]
    lines.extend(
        [
            "## One-variable experiment boundary",
            "",
            f"- Status: {experiment['status']}",
            f"- Owner: {experiment['owner']}",
            f"- Fixed inputs: {experiment['fixed_inputs']}",
            f"- Approval: {experiment['approval']}",
            f"- Rollback: {experiment['rollback']}",
            "",
            "## Warnings",
            "",
        ]
    )
    lines.extend(f"- {warning}" for warning in result["warnings"])
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
