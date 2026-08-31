#!/usr/bin/env python3
"""Deterministically classify redacted Snowflake failover-readiness evidence."""

from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

MODES = {
    "PLAN_ONLY",
    "READ_ONLY_PREFLIGHT",
    "OPERATOR_EXECUTED_FAILOVER",
    "OPERATOR_EXECUTED_FAILOVER_AND_FAILBACK",
}
FAIL_CODES = {
    "EDITION_UNAVAILABLE",
    "GROUP_NOT_FAILOVER_CAPABLE",
    "SECONDARY_MISSING",
    "GROUP_SUSPENDED",
    "REFRESH_FAILED",
    "REFRESH_CANCELED",
    "RPO_BREACH",
    "RTO_BREACH",
    "DANGLING_REFERENCE",
    "TASK_OWNER_INVALID",
    "TARGET_VALIDATION_FAILED",
    "PRIVILEGE_GAP",
    "OPERATOR_APPROVAL_MISSING",
    "FAILOVER_UNVERIFIED",
    "FAILBACK_UNVERIFIED",
    "DRILL_RECEIPT_UNVERIFIABLE",
    "REPLICATION_RECEIPT_ERROR",
    "REPLICATION_RECEIPT_TRUNCATED",
    "REPLICATION_RECEIPT_UNVERIFIABLE",
}
INCONCLUSIVE_CODES = {
    "RPO_UNEVALUATED",
    "RTO_UNEVALUATED",
    "HISTORY_MISSING",
    "HISTORY_STALE",
    "TARGET_VALIDATION_MISSING",
    "VISIBILITY_GAP",
    "CURRENT_STATE_MISSING",
    "CURRENT_STATE_UNAVAILABLE",
    "CURRENT_STATE_UNVERIFIABLE",
    "CURRENT_STATE_STALE",
    "CURRENT_GROUP_STATE_MISSING",
    "GROUP_PROGRESS_MISSING",
    "GROUP_STATE_HISTORY_DRIFT",
    "GROUP_SCHEDULE_HISTORY_DRIFT",
}
SENSITIVE_KEY = re.compile(
    r"password|passphrase|secret|private.?key|credential|token|authorization|jwt|sql.?text|query.?text|raw.?row|pii",
    re.I,
)
PRESIGNED = re.compile(r"https?://\S+[?&](?:X-Amz-|X-Goog-|sig=|signature=)", re.I)
EMAIL = re.compile(r"(?i)(?<![\w.+-])[\w.+-]+@[a-z0-9.-]+\.[a-z]{2,}(?![\w.-])")
SSN = re.compile(r"(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)")
SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
REPLICATION_VIEW = "SNOWFLAKE.ACCOUNT_USAGE.REPLICATION_GROUP_REFRESH_HISTORY"
REPLICATION_DATASET = "replication_refresh_history"
REDACTIONS = (
    (re.compile(r"https?://\S+", re.IGNORECASE), "[REDACTED_URL]"),
    (re.compile(r"\bBearer\s+\S+", re.IGNORECASE), "[REDACTED_BEARER]"),
    (
        re.compile(
            r"(?i)\b[\w-]*(password|passphrase|token|secret|credential|private[_-]?key|authorization|jwt|api[_-]?key)[\w-]*\s*[=:]\s*\S+"
        ),
        "[REDACTED_CREDENTIAL]",
    ),
)


def stamp(value: Any, field: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a timezone-aware ISO 8601 timestamp")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} must be a timezone-aware ISO 8601 timestamp") from exc
    if result.tzinfo is None:
        raise ValueError(f"{field} must include a timezone")
    return result


def _safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _safe(child) for key, child in value.items()}
    if isinstance(value, list):
        return [_safe(child) for child in value]
    if isinstance(value, str):
        for pattern, replacement in REDACTIONS:
            value = pattern.sub(replacement, value)
    return value


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _replication_receipt_findings(receipt: Any, as_of: datetime) -> list[tuple[str, str]]:
    """Return blocking findings for an untrusted shared replication receipt."""
    if not isinstance(receipt, dict):
        return [("REPLICATION_RECEIPT_UNVERIFIABLE", "collector receipt is missing or not an object")]
    findings: list[tuple[str, str]] = []
    if receipt.get("schema_version") != "1":
        findings.append(("REPLICATION_RECEIPT_UNVERIFIABLE", "collector receipt schema_version must be 1"))
    if receipt.get("surface") != "replication":
        findings.append(("REPLICATION_RECEIPT_UNVERIFIABLE", "collector receipt surface must be replication"))
    status = receipt.get("status")
    if status != "collected":
        findings.append(("REPLICATION_RECEIPT_ERROR", f"collector receipt status={status!r}"))
    errors = receipt.get("errors")
    if not isinstance(errors, list) or errors:
        findings.append(("REPLICATION_RECEIPT_ERROR", "collector receipt contains collection errors"))
    try:
        collected = stamp(receipt.get("collected_at"), "collector_receipt.collected_at")
        if collected > datetime.now(collected.tzinfo) or collected > as_of:
            findings.append(
                ("REPLICATION_RECEIPT_UNVERIFIABLE", "collector receipt collected_at is future-dated or after as_of")
            )
    except ValueError:
        findings.append(("REPLICATION_RECEIPT_UNVERIFIABLE", "collector receipt collected_at is invalid"))
    if not isinstance(receipt.get("connection_profile"), str) or not receipt["connection_profile"].strip():
        findings.append(("REPLICATION_RECEIPT_UNVERIFIABLE", "collector receipt connection_profile is required"))
    source_views = receipt.get("source_views")
    if source_views != [REPLICATION_VIEW]:
        findings.append(
            (
                "REPLICATION_RECEIPT_UNVERIFIABLE",
                f"collector receipt source_views must exactly match {REPLICATION_VIEW}",
            )
        )
    if not isinstance(receipt.get("sql_sha256"), str) or not SHA256_RE.fullmatch(receipt["sql_sha256"]):
        findings.append(("REPLICATION_RECEIPT_UNVERIFIABLE", "collector receipt sql_sha256 is invalid"))
    else:
        sql_path = Path(__file__).resolve().parent / "sql" / "replication.sql"
        expected_sql_hash = f"sha256:{hashlib.sha256(sql_path.read_bytes()).hexdigest()}"
        if receipt["sql_sha256"] != expected_sql_hash:
            findings.append(
                (
                    "REPLICATION_RECEIPT_UNVERIFIABLE",
                    "collector receipt sql_sha256 does not match the reviewed replication SQL",
                )
            )
    if not isinstance(receipt.get("receipt_sha256"), str) or not SHA256_RE.fullmatch(receipt["receipt_sha256"]):
        findings.append(("REPLICATION_RECEIPT_UNVERIFIABLE", "collector receipt receipt_sha256 is invalid"))
    if isinstance(receipt.get("receipt_sha256"), str) and SHA256_RE.fullmatch(receipt["receipt_sha256"]):
        unsigned = dict(receipt)
        unsigned.pop("receipt_sha256", None)
        expected = f"sha256:{hashlib.sha256(_canonical_json(unsigned)).hexdigest()}"
        if receipt["receipt_sha256"] != expected:
            findings.append(
                ("REPLICATION_RECEIPT_UNVERIFIABLE", "collector receipt receipt_sha256 does not match its contents")
            )
    row_count = receipt.get("row_count")
    if type(row_count) is not int or row_count < 0:
        findings.append(
            ("REPLICATION_RECEIPT_UNVERIFIABLE", "collector receipt row_count must be a non-negative integer")
        )
    row_limit = receipt.get("row_limit")
    if row_limit is None or type(row_limit) is not int or row_limit <= 0:
        findings.append(("REPLICATION_RECEIPT_UNVERIFIABLE", "collector receipt row_limit must be a positive integer"))
    truncation = receipt.get("truncation_possible")
    if not isinstance(truncation, bool):
        findings.append(("REPLICATION_RECEIPT_UNVERIFIABLE", "collector receipt truncation_possible must be boolean"))
    elif type(row_count) is int and type(row_limit) is int and truncation != row_count >= row_limit:
        findings.append(
            (
                "REPLICATION_RECEIPT_UNVERIFIABLE",
                "collector receipt truncation_possible disagrees with row_count and row_limit",
            )
        )
    if truncation is True:
        findings.append(("REPLICATION_RECEIPT_TRUNCATED", "collector receipt is truncated at its SQL row limit"))
    datasets = receipt.get("datasets")
    if not isinstance(datasets, dict):
        findings.append(("REPLICATION_RECEIPT_UNVERIFIABLE", "collector receipt datasets must be an object"))
    else:
        rows = datasets.get(REPLICATION_DATASET, [])
        if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
            findings.append(
                ("REPLICATION_RECEIPT_UNVERIFIABLE", "replication_refresh_history must be an array of objects")
            )
        elif type(row_count) is int and row_count != len(rows):
            findings.append(
                (
                    "REPLICATION_RECEIPT_UNVERIFIABLE",
                    "collector receipt row_count does not match replication history rows",
                )
            )
        if set(datasets) - {REPLICATION_DATASET}:
            findings.append(("REPLICATION_RECEIPT_UNVERIFIABLE", "collector receipt contains unexpected datasets"))
    return findings


def reject_sensitive(value: Any, path: str = "input") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if SENSITIVE_KEY.search(str(key)):
                raise ValueError(f"sensitive field is not accepted: {path}.{key}")
            reject_sensitive(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            reject_sensitive(child, f"{path}[{index}]")
    elif isinstance(value, str):
        if PRESIGNED.search(value):
            raise ValueError(f"presigned URL is not accepted: {path}")
        try:
            is_ip = bool(ipaddress.ip_address(value.strip()))
        except ValueError:
            is_ip = False
        if EMAIL.search(value) or SSN.search(value) or is_ip:
            raise ValueError(f"PII-like value is not accepted: {path}")


def finding(code: str, severity: str, evidence: str, action: str) -> dict[str, str]:
    return {"code": code, "severity": severity, "evidence": evidence, "read_only_action": action}


def _current_state_findings(data: dict[str, Any], as_of: datetime, groups: list[dict[str, Any]]) -> list[tuple[str, str]]:
    """Validate near-live group/progress/schedule state against the history view."""
    current = data.get("current_state")
    if not isinstance(current, dict):
        return [("CURRENT_STATE_MISSING", "near-live failover-group state is absent")]
    findings: list[tuple[str, str]] = []
    if current.get("status") != "collected":
        findings.append(("CURRENT_STATE_UNAVAILABLE", f"current-state status={current.get('status')!r}"))
    try:
        observed = stamp(current.get("observed_at"), "current_state.observed_at")
    except ValueError:
        findings.append(("CURRENT_STATE_UNVERIFIABLE", "current_state.observed_at is invalid"))
        observed = None
    max_age = current.get("max_age_minutes")
    if type(max_age) is not int or max_age <= 0:
        findings.append(("CURRENT_STATE_UNVERIFIABLE", "current_state.max_age_minutes must be positive"))
    elif observed is not None and (as_of - observed).total_seconds() > max_age * 60:
        findings.append(("CURRENT_STATE_STALE", f"current group state age exceeds {max_age} minutes"))
    current_groups = current.get("groups")
    if not isinstance(current_groups, list) or any(not isinstance(row, dict) for row in current_groups):
        findings.append(("CURRENT_STATE_UNVERIFIABLE", "current_state.groups must be an array of objects"))
        return findings
    current_by_name: dict[str, dict[str, Any]] = {}
    for row in current_groups:
        name = row.get("name")
        if not isinstance(name, str) or not name:
            findings.append(("CURRENT_STATE_UNVERIFIABLE", "current group is missing a name"))
            continue
        if name in current_by_name:
            findings.append(("CURRENT_STATE_UNVERIFIABLE", f"duplicate current group {name}"))
        current_by_name[name] = row
        if str(row.get("progress_status", "")).upper() in {"", "UNKNOWN", "MISSING"}:
            findings.append(("GROUP_PROGRESS_MISSING", name))
    for group in groups:
        name = str(group.get("name", "unnamed"))
        current_group = current_by_name.get(name)
        if current_group is None:
            findings.append(("CURRENT_GROUP_STATE_MISSING", name))
            continue
        if str(current_group.get("refresh_status", "")).upper() != str(group.get("refresh_status", "")).upper():
            findings.append(("GROUP_STATE_HISTORY_DRIFT", name))
        if "scheduled_interval_minutes" in current_group and current_group.get("scheduled_interval_minutes") != group.get(
            "scheduled_interval_minutes"
        ):
            findings.append(("GROUP_SCHEDULE_HISTORY_DRIFT", name))
    return findings


def _drill_receipt_issue(event: Any, name: str) -> str | None:
    if not isinstance(event, dict):
        return f"{name} event is not an object"
    receipt = event.get("receipt_sha256")
    if not isinstance(receipt, str) or not SHA256_RE.fullmatch(receipt):
        return f"{name} receipt_sha256 is missing or invalid"
    unsigned = dict(event)
    unsigned.pop("receipt_sha256", None)
    expected = f"sha256:{hashlib.sha256(_canonical_json(unsigned)).hexdigest()}"
    return None if receipt == expected else f"{name} receipt_sha256 does not match event contents"


def analyze(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError("evidence must be a JSON object")
    reject_sensitive(data)
    mode = data.get("mode")
    if mode not in MODES:
        raise ValueError(f"mode must be one of: {', '.join(sorted(MODES))}")
    as_of = stamp(data.get("as_of"), "as_of")
    if as_of > datetime.now(as_of.tzinfo):
        raise ValueError("as_of cannot be in the future")
    collector_receipt = data.get("collector_receipt")
    for name in ("groups", "dependencies", "object_checks", "target_validations", "drill_events"):
        if not isinstance(data.get(name, []), list) or any(not isinstance(row, dict) for row in data.get(name, [])):
            raise ValueError(f"{name} must be an array of objects")
    objectives = data.get("objectives", {})
    if not isinstance(objectives, dict):
        raise ValueError("objectives must be an object")
    rpo = objectives.get("rpo_minutes")
    rto = objectives.get("rto_minutes")
    if rpo is not None and (type(rpo) not in (int, float) or rpo <= 0):
        raise ValueError("objectives.rpo_minutes must be positive")
    if rto is not None and (type(rto) not in (int, float) or rto <= 0):
        raise ValueError("objectives.rto_minutes must be positive")

    out: list[dict[str, str]] = []

    def add(code: str, severity: str, evidence: str, action: str) -> None:
        out.append(finding(code, severity, evidence, action))

    for code, evidence in _replication_receipt_findings(collector_receipt, as_of):
        add(
            code,
            "critical",
            evidence,
            "Recollect a complete, hash-verifiable replication receipt through the approved read-only collector before making a readiness decision.",
        )
    edition = str(data.get("edition", "UNKNOWN")).upper().replace(" ", "_")
    if edition not in {"BUSINESS_CRITICAL", "VIRTUAL_PRIVATE_SNOWFLAKE"}:
        add(
            "EDITION_UNAVAILABLE",
            "critical",
            f"edition={edition}",
            "Confirm edition and limit the plan to supported replication capability; do not claim account failover readiness.",
        )

    for code, evidence in _current_state_findings(data, as_of, data.get("groups", [])):
        add(
            code,
            "critical" if code.endswith("UNVERIFIABLE") else "unknown",
            evidence,
            "Collect a fresh, hash-verifiable near-live group state receipt before making a readiness decision.",
        )

    groups = data.get("groups", [])
    names = {str(row.get("name")) for row in groups if row.get("name")}
    if not groups:
        add(
            "HISTORY_MISSING",
            "unknown",
            "no in-scope groups",
            "Declare the complete in-scope failover-group denominator and collect group evidence.",
        )
    receipt_rows = (
        collector_receipt.get("datasets", {}).get(REPLICATION_DATASET, [])
        if isinstance(collector_receipt, dict) and isinstance(collector_receipt.get("datasets"), dict)
        else []
    )
    receipt_group_names = {
        str(row.get("replication_group_name"))
        for row in receipt_rows
        if isinstance(row, dict) and row.get("replication_group_name")
    }
    missing_history = sorted(name for name in names if name not in receipt_group_names)
    if missing_history:
        add(
            "HISTORY_MISSING",
            "unknown",
            f"no collector history for groups={','.join(missing_history)}",
            "Collect a complete historical refresh receipt for every in-scope group; absence is not evidence of health.",
        )
    for group in groups:
        name = str(group.get("name", "unnamed"))
        if str(group.get("kind", "")).upper() != "FAILOVER":
            add(
                "GROUP_NOT_FAILOVER_CAPABLE",
                "critical",
                name,
                "Verify that the recovery scope uses a failover group rather than assuming replication-only capability.",
            )
        if group.get("secondary_present") is not True:
            add("SECONDARY_MISSING", "critical", name, "Confirm a matching secondary group in the target account.")
        if group.get("suspended") is True:
            add(
                "GROUP_SUSPENDED",
                "critical",
                name,
                "Review suspension state and require an authorized operator decision outside this skill.",
            )
        refresh = str(group.get("refresh_status", "UNKNOWN")).upper()
        if refresh == "IN_PROGRESS":
            add(
                "REFRESH_IN_PROGRESS",
                "warning",
                name,
                "Wait for the current refresh to finish and collect a new near-live receipt.",
            )
        elif refresh == "FAILED":
            add(
                "REFRESH_FAILED",
                "critical",
                name,
                "Inspect the sanitized refresh error and repair the refresh path before a drill.",
            )
        elif refresh == "CANCELED":
            add(
                "REFRESH_CANCELED",
                "critical",
                name,
                "Establish why the refresh was canceled and collect a successful replacement receipt.",
            )
        last = group.get("last_successful_refresh_at")
        if rpo is None or not last:
            add("RPO_UNEVALUATED", "unknown", name, "Declare RPO and collect the last successful refresh timestamp.")
        else:
            last_at = stamp(last, f"groups[{name}].last_successful_refresh_at")
            if last_at > datetime.now(last_at.tzinfo):
                raise ValueError(f"groups[{name}].last_successful_refresh_at cannot be in the future")
            age = (as_of - last_at).total_seconds() / 60
            if age < 0:
                raise ValueError(f"groups[{name}].last_successful_refresh_at cannot be after as_of")
            if age > float(rpo):
                add(
                    "RPO_BREACH",
                    "critical",
                    f"{name}: age={age:.1f}m objective={rpo}m",
                    "Repair refresh cadence and verify a new near-live refresh before a drill.",
                )
        interval = group.get("scheduled_interval_minutes")
        if rpo is not None and type(interval) in (int, float) and interval > rpo:
            add(
                "SCHEDULE_OVERRUN",
                "warning",
                f"{name}: interval={interval}m objective={rpo}m",
                "Review the schedule; its nominal interval already exceeds the RPO.",
            )

    for dep in data.get("dependencies", []):
        left, right = str(dep.get("from_group", "")), str(dep.get("to_group", ""))
        if left not in names or right not in names or str(dep.get("status", "KNOWN")).upper() == "DANGLING":
            add(
                "DANGLING_REFERENCE",
                "critical",
                f"{left}->{right}",
                "Resolve or explicitly exclude the dangling dependency before a drill.",
            )
        elif left != right:
            add(
                "CROSS_GROUP_DEPENDENCY",
                "warning",
                f"{left}->{right}",
                "Prove ordering and target consistency across both groups.",
            )

    for check in data.get("object_checks", []):
        obj = str(check.get("object", "unknown"))
        if check.get("task_stream_split") is True:
            add(
                "TASK_STREAM_SPLIT",
                "warning",
                obj,
                "Keep dependent tasks and streams in a proven promotion unit or document ordering and replay controls.",
            )
        if check.get("task_owner_valid") is False:
            add(
                "TASK_OWNER_INVALID",
                "critical",
                obj,
                "Verify target task ownership and execution role before promotion.",
            )
        stream = str(check.get("stream_state", "CURRENT")).upper()
        if stream in {"STALE", "DUPLICATE_RISK", "TIME_TRAVEL_RISK"}:
            add(
                f"STREAM_{stream}",
                "warning",
                obj,
                "Validate stream offsets, retention, and replay/idempotency behavior on the target.",
            )
        if check.get("dynamic_table_reinitialize") is True:
            add(
                "DYNAMIC_TABLE_REINITIALIZATION",
                "warning",
                obj,
                "Budget and validate target reinitialization before counting it inside RTO.",
            )

    validations = data.get("target_validations", [])
    if not validations:
        add(
            "TARGET_VALIDATION_MISSING",
            "unknown",
            "no target invariants",
            "Define and execute target-side data and application invariants.",
        )
    for row in validations:
        if str(row.get("status", "MISSING")).upper() != "PASS":
            add(
                "TARGET_VALIDATION_FAILED",
                "critical",
                str(row.get("name", "unnamed")),
                "Repair the target invariant and collect a passing receipt.",
            )
    redirect = data.get("client_redirect", {})
    if not isinstance(redirect, dict) or redirect.get("tested") is not True:
        add(
            "CLIENT_REDIRECT_UNVERIFIED",
            "warning",
            "client redirect not proven",
            "Test the approved client redirection path and application reconnect behavior.",
        )
    privileges = data.get("privileges", {})
    if not isinstance(privileges, dict) or privileges.get("observable") is not True:
        add(
            "VISIBILITY_GAP",
            "unknown",
            "privilege evidence unavailable",
            "Collect least-privilege source and target visibility evidence.",
        )
    elif privileges.get("missing"):
        add(
            "PRIVILEGE_GAP",
            "critical",
            ", ".join(map(str, privileges["missing"])),
            "Resolve the named runtime/validation privilege gaps through approved change control.",
        )

    history = data.get("history", {})
    if not isinstance(history, dict) or not history.get("account_usage_collected_at"):
        add(
            "HISTORY_MISSING",
            "unknown",
            "Account Usage receipt absent",
            "Collect a timestamped historical receipt and near-live state.",
        )
    else:
        history_at = stamp(history["account_usage_collected_at"], "history.account_usage_collected_at")
        if history_at > datetime.now(history_at.tzinfo):
            raise ValueError("history.account_usage_collected_at cannot be in the future")
        age = (as_of - history_at).total_seconds() / 60
        if age < 0:
            raise ValueError("history.account_usage_collected_at cannot be after as_of")
        if age > 180:
            add(
                "HISTORY_STALE",
                "unknown",
                f"Account Usage receipt age={age:.1f}m",
                "Collect near-live Information Schema state before an operator decision.",
            )
    if history.get("detailed_window_days", 0) > 14:
        add(
            "HISTORY_RETENTION_EXCEEDED",
            "warning",
            f"requested {history['detailed_window_days']} days",
            "Use a retained external receipt for older detail; do not assume Snowflake still exposes it.",
        )

    events = {str(row.get("event", "")).upper(): row for row in data.get("drill_events", [])}
    execution = mode.startswith("OPERATOR_EXECUTED")
    if execution:
        failover = events.get("FAILOVER")
        if (issue := _drill_receipt_issue(failover, "FAILOVER")) is not None:
            add(
                "DRILL_RECEIPT_UNVERIFIABLE",
                "critical",
                issue,
                "Attach a canonical hash over the approved operator event and recollect the drill receipt.",
            )
        failover_observed = (
            stamp(failover.get("observed_at"), "drill_events.FAILOVER.observed_at") if failover else None
        )
        if failover_observed is not None and (
            failover_observed > as_of or failover_observed > datetime.now(failover_observed.tzinfo)
        ):
            raise ValueError("drill_events.FAILOVER.observed_at cannot be in the future or after as_of")
        if not failover or failover.get("status") != "SUCCEEDED":
            add(
                "FAILOVER_UNVERIFIED",
                "critical",
                "successful failover event absent",
                "Attach the authorized operator event and post-failover validation receipt.",
            )
        elif failover.get("operator_approved") is not True:
            add(
                "OPERATOR_APPROVAL_MISSING",
                "critical",
                "failover approval absent",
                "Attach explicit operator/change approval; analyzer execution is never authorization.",
            )
        duration = failover.get("duration_minutes") if failover else None
        if rto is None or type(duration) not in (int, float):
            add(
                "RTO_UNEVALUATED",
                "unknown",
                "RTO objective or measured duration absent",
                "Declare RTO and attach measured operator duration.",
            )
        elif duration > rto:
            add(
                "RTO_BREACH",
                "critical",
                f"duration={duration}m objective={rto}m",
                "Update the recovery plan or reduce measured recovery time before verification.",
            )
    elif rto is None:
        add("RTO_UNEVALUATED", "unknown", "RTO objective absent", "Declare a target RTO before scheduling an exercise.")
    if mode == "OPERATOR_EXECUTED_FAILOVER_AND_FAILBACK":
        failback = events.get("FAILBACK")
        if (issue := _drill_receipt_issue(failback, "FAILBACK")) is not None:
            add(
                "DRILL_RECEIPT_UNVERIFIABLE",
                "critical",
                issue,
                "Attach a canonical hash over the approved operator event and recollect the drill receipt.",
            )
        failback_observed = (
            stamp(failback.get("observed_at"), "drill_events.FAILBACK.observed_at") if failback else None
        )
        if failback_observed is not None and (
            failback_observed > as_of or failback_observed > datetime.now(failback_observed.tzinfo)
        ):
            raise ValueError("drill_events.FAILBACK.observed_at cannot be in the future or after as_of")
        if not failback or failback.get("status") != "SUCCEEDED" or failback.get("operator_approved") is not True:
            add(
                "FAILBACK_UNVERIFIED",
                "critical",
                "approved successful failback event absent",
                "Attach the authorized failback and post-failback validation receipt.",
            )

    out.sort(key=lambda row: (row["code"], row["evidence"]))
    codes = {row["code"] for row in out}
    if codes & FAIL_CODES:
        status = "NOT_READY"
    elif codes & INCONCLUSIVE_CODES:
        status = "INCONCLUSIVE"
    elif out:
        status = "AT_RISK"
    elif mode == "OPERATOR_EXECUTED_FAILOVER_AND_FAILBACK":
        status = "DRILL_VERIFIED"
    elif mode == "OPERATOR_EXECUTED_FAILOVER":
        status = "FAILOVER_VERIFIED"
    else:
        status = "READY_FOR_OPERATOR_DRILL"
    report = {
        "schema_version": "1",
        "status": status,
        "mode": mode,
        "objectives": {"rpo_minutes": rpo, "rto_minutes": rto},
        "findings": out,
        "collector_ingestion": _safe(collector_receipt)
        if isinstance(collector_receipt, dict)
        else {"status": "not_supplied"},
        "non_claims": [
            "No Snowflake refresh, promotion, redirect, failover, or failback was executed.",
            "Historical success and successful login do not prove current application readiness.",
            "A positive verdict is bounded to the supplied denominator and timestamps.",
        ],
    }
    encoded = json.dumps(report, sort_keys=True, separators=(",", ":")).encode()
    report["receipt_sha256"] = f"sha256:{hashlib.sha256(encoded).hexdigest()}"
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        report = analyze(json.loads(args.input.read_text(encoding="utf-8")))
        rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            temporary = args.output.with_name(f".{args.output.name}.tmp")
            temporary.write_text(rendered, encoding="utf-8")
            temporary.replace(args.output)
        else:
            sys.stdout.write(rendered)
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
