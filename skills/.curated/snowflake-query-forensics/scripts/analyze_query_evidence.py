#!/usr/bin/env python3
"""Validate and classify normalized Snowflake query evidence without mutation."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


class EvidenceError(ValueError):
    """Raised when query evidence is malformed or unsafe to interpret."""


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


def analyze(data: dict[str, Any]) -> dict[str, Any]:
    reject_secret_fields(data)
    metadata = data.get("metadata")
    history = data.get("query_history")
    if not isinstance(metadata, dict):
        raise EvidenceError("metadata must be an object")
    if not isinstance(history, dict):
        raise EvidenceError("query_history must be an object")
    query_id = metadata.get("query_id")
    if not isinstance(query_id, str) or not query_id.strip():
        raise EvidenceError("metadata.query_id is required")
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
    experiment_owner = str(metadata["experiment_owner"])

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
    if not insights:
        warnings.append("no Query Insights supplied; absence is not proof that no performance condition exists")

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
