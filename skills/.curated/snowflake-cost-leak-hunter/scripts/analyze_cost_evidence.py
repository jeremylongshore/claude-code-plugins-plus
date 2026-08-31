#!/usr/bin/env python3
"""Validate and summarize normalized, read-only Snowflake cost evidence."""

from __future__ import annotations

import argparse
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


def reject_secret_fields(value: Any, path: str = "input") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = re.sub(r"[^a-z0-9]", "", str(key).casefold())
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


def freshness(
    data: dict[str, Any], generated: datetime, window_end: datetime
) -> tuple[list[dict[str, str]], list[str]]:
    source_times = data.get("source_max_times", {})
    if not isinstance(source_times, dict):
        raise EvidenceError("source_max_times must be an object")
    results: list[dict[str, str]] = []
    warnings: list[str] = []
    for source in ("warehouse_metering", "query_attribution", "serverless_usage"):
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
    rates = data.get("credit_rates", {})
    if not isinstance(rates, dict):
        raise EvidenceError("credit_rates must be an object")

    warnings: list[str] = []
    source_freshness, freshness_warnings = freshness(data, generated, end)
    warnings.extend(freshness_warnings)

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
        tag = row.get("query_tag")
        if tag is None or (isinstance(tag, str) and not tag.strip()):
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
        "approval_queue": approval_queue,
        "coverage_status": "bounded_partial" if warnings else "complete_for_supplied_surfaces",
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
