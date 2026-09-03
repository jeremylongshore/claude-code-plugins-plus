#!/usr/bin/env python3
"""Validate receipted Snowflake auth evidence and emit a read-only migration packet."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
SQL_DIR = HERE / "sql"
LEGACY_ANALYZER_PATH = HERE / "analyze_auth.py"
COLLECTOR_PATH = HERE / "collect_snowflake_evidence.py"
LEGACY_SPEC = importlib.util.spec_from_file_location("snowflake_auth_planner", LEGACY_ANALYZER_PATH)
if LEGACY_SPEC is None or LEGACY_SPEC.loader is None:  # pragma: no cover - corrupt package
    raise RuntimeError(f"cannot load bundled analyzer: {LEGACY_ANALYZER_PATH}")
LEGACY = importlib.util.module_from_spec(LEGACY_SPEC)
LEGACY_SPEC.loader.exec_module(LEGACY)
COLLECTOR_SPEC = importlib.util.spec_from_file_location("snowflake_auth_collector", COLLECTOR_PATH)
if COLLECTOR_SPEC is None or COLLECTOR_SPEC.loader is None:  # pragma: no cover - corrupt package
    raise RuntimeError(f"cannot load bundled collector: {COLLECTOR_PATH}")
COLLECTOR = importlib.util.module_from_spec(COLLECTOR_SPEC)
COLLECTOR_SPEC.loader.exec_module(COLLECTOR)

DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
HEX_RE = re.compile(r"^[0-9a-f]{64}$")
SAFE_OBSERVATION_RE = re.compile(r"^[A-Z][A-Z0-9_ -]{0,63}$")
LOGIN_HISTORY_LATENCY_SECONDS = 7200
LOGIN_HISTORY_WINDOW_SECONDS = 7 * 24 * 60 * 60
MAX_EVALUATION_CLOCK_AGE_SECONDS = 300
MAX_RECEIPT_AGE_SECONDS = 3600
SURFACE_CONTRACTS: dict[str, tuple[str, list[str], tuple[str, ...], str]] = {
    "auth-current": (
        "auth-current.sql",
        ["SHOW USERS"],
        ("current_users", "execution_context"),
        "current_users",
    ),
    "auth": (
        "auth.sql",
        ["SNOWFLAKE.ACCOUNT_USAGE.USERS"],
        ("execution_context", "historical_users"),
        "historical_users",
    ),
    "auth-login-history": (
        "auth-login-history.sql",
        ["SNOWFLAKE.ACCOUNT_USAGE.LOGIN_HISTORY"],
        ("execution_context", "login_history"),
        "login_history",
    ),
}
CONTEXT_FIELDS = {
    "observed_at",
    "account_identifier_sha256",
    "collector_user_sha256",
    "primary_role_sha256",
    "primary_role_type",
    "secondary_roles_sha256",
}
AUTHORIZATION_CONTEXT_FIELDS = CONTEXT_FIELDS - {"observed_at"}
SUPPORTED_ROLE_TYPES = {"APPLICATION_INSTANCE", "ROLE"}
BUNDLE_REQUIRED_FIELDS = {
    "schema_version",
    "metadata",
    "collections",
    "users",
    "workloads",
    "integrations",
    "enforcement_windows",
}
BUNDLE_OPTIONAL_FIELDS: set[str] = set()
METADATA_FIELDS = {
    "evaluated_at",
    "max_age_seconds",
    "connection_profile",
    "login_history_latency_seconds",
    "coverage",
    "authorization_context",
}
AUTH_RECEIPT_FIELDS = {
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
    "dataset_row_counts",
    "expected_datasets",
    "datasets",
    "errors",
    "non_claims",
    "collection_mode",
    "collection_started_at",
    "collection_completed_at",
    "receipt_sha256",
}
COMMON_USER_FIELDS = {
    "user_name_sha256",
    "created_on",
    "disabled",
    "type",
    "principal_scope",
    "has_password",
    "has_rsa_public_key",
    "has_mfa",
    "has_pat",
    "has_workload_identity",
}
USER_FIELDS = {
    "current_users": COMMON_USER_FIELDS | {"metadata_visible"},
    "historical_users": COMMON_USER_FIELDS,
}
LOGIN_FIELDS = {
    "auth_event_sha256",
    "user_name_sha256",
    "event_timestamp",
    "event_type",
    "first_authentication_factor",
    "second_authentication_factor",
    "is_success",
    "error_code",
}
POSTURE_FIELDS = (
    "disabled",
    "type",
    "has_password",
    "has_rsa_public_key",
    "has_mfa",
    "has_pat",
    "has_workload_identity",
)


class AuthEvidenceError(ValueError):
    """Raised when the bundle envelope is malformed or unsafe to interpret."""


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def input_sha256(value: dict[str, Any]) -> str:
    return f"sha256:{hashlib.sha256(canonical_json(value)).hexdigest()}"


def parse_time(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise AuthEvidenceError(f"{field} must be a timezone-aware timestamp")
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError as exc:
        raise AuthEvidenceError(f"{field} must be a timezone-aware timestamp") from exc
    if parsed.tzinfo is None:
        raise AuthEvidenceError(f"{field} must be a timezone-aware timestamp")
    return parsed.astimezone(timezone.utc)


def _receipt_hash_valid(receipt: dict[str, Any]) -> bool:
    body = dict(receipt)
    supplied = body.pop("receipt_sha256", None)
    expected = f"sha256:{hashlib.sha256(canonical_json(body)).hexdigest()}"
    return supplied == expected


def _safe_observation(value: Any, *, nullable: bool = True) -> bool:
    if value is None and nullable:
        return True
    return isinstance(value, str) and bool(SAFE_OBSERVATION_RE.fullmatch(value))


def _hash_valid(value: Any, *, nullable: bool = False) -> bool:
    return (value is None and nullable) or (isinstance(value, str) and bool(HEX_RE.fullmatch(value)))


def _expected_sql(surface: str) -> tuple[bytes, str, list[str], tuple[str, ...], str]:
    filename, sources, datasets, cap_dataset = SURFACE_CONTRACTS[surface]
    path = SQL_DIR / filename
    if path.is_symlink() or not path.is_file():
        raise AuthEvidenceError(f"reviewed SQL is missing or not a regular file: {filename}")
    return path.read_bytes(), filename, sources, datasets, cap_dataset


def _context_issues(row: dict[str, Any], path: str) -> tuple[list[str], tuple[str, ...] | None, datetime | None]:
    issues: list[str] = []
    if set(row) != CONTEXT_FIELDS:
        return [f"{path} fields do not match the reviewed privacy projection"], None, None
    for field in (
        "account_identifier_sha256",
        "collector_user_sha256",
        "primary_role_sha256",
        "secondary_roles_sha256",
    ):
        if not _hash_valid(row.get(field)):
            issues.append(f"{path}.{field} is not a lowercase SHA-256 digest")
    if row.get("primary_role_type") not in SUPPORTED_ROLE_TYPES:
        issues.append(f"{path}.primary_role_type is not a supported role type")
    observed: datetime | None = None
    try:
        observed = parse_time(row.get("observed_at"), f"{path}.observed_at")
    except AuthEvidenceError as exc:
        issues.append(str(exc))
    signature = None
    if not issues:
        signature = tuple(
            str(row[field])
            for field in (
                "account_identifier_sha256",
                "collector_user_sha256",
                "primary_role_sha256",
                "primary_role_type",
                "secondary_roles_sha256",
            )
        )
    return issues, signature, observed


def _authorization_context_signature(value: Any) -> tuple[str, ...]:
    if not isinstance(value, dict) or set(value) != AUTHORIZATION_CONTEXT_FIELDS:
        raise AuthEvidenceError(
            "metadata.authorization_context must contain exactly the reviewed hashed context fields"
        )
    for field in (
        "account_identifier_sha256",
        "collector_user_sha256",
        "primary_role_sha256",
        "secondary_roles_sha256",
    ):
        if not _hash_valid(value.get(field)):
            raise AuthEvidenceError(f"metadata.authorization_context.{field} must be a lowercase SHA-256 digest")
    if value.get("primary_role_type") not in SUPPORTED_ROLE_TYPES:
        raise AuthEvidenceError("metadata.authorization_context.primary_role_type is not a supported role type")
    return tuple(str(value[field]) for field in sorted(AUTHORIZATION_CONTEXT_FIELDS))


def _user_issues(dataset: str, values: Any) -> list[str]:
    issues: list[str] = []
    if not isinstance(values, list):
        return [f"datasets.{dataset} is not an array"]
    seen: set[str] = set()
    for index, row in enumerate(values):
        path = f"datasets.{dataset}[{index}]"
        if not isinstance(row, dict):
            issues.append(f"{path} is not an object")
            continue
        if set(row) != USER_FIELDS[dataset]:
            issues.append(f"{path} fields do not match the reviewed privacy projection")
            continue
        digest = row.get("user_name_sha256")
        if not _hash_valid(digest):
            issues.append(f"{path}.user_name_sha256 is invalid")
        elif digest in seen:
            issues.append(f"{path}.user_name_sha256 is duplicated")
        else:
            seen.add(digest)
        try:
            parse_time(row.get("created_on"), f"{path}.created_on")
        except AuthEvidenceError as exc:
            issues.append(str(exc))
        user_type = str(row.get("type") or "").upper()
        if user_type not in {
            "PERSON",
            "SERVICE",
            "LEGACY_SERVICE",
            "SERVICE_AGENT",
            "SNOWFLAKE_SERVICE",
        }:
            issues.append(f"{path}.type is not a supported Snowflake user type")
        expected_scope = "SNOWFLAKE_MANAGED_EXCLUDED" if user_type == "SNOWFLAKE_SERVICE" else "OPERATOR_OWNED"
        if row.get("principal_scope") != expected_scope:
            issues.append(f"{path}.principal_scope does not match the reviewed user classification")
        for field in (
            "disabled",
            "has_password",
            "has_rsa_public_key",
            "has_mfa",
            "has_pat",
            "has_workload_identity",
        ):
            value = row.get(field)
            service_non_applicable = user_type in {"SERVICE", "SERVICE_AGENT"} and field in {
                "has_password",
                "has_mfa",
            }
            if user_type == "SNOWFLAKE_SERVICE":
                if value is not None and type(value) is not bool:
                    issues.append(f"{path}.{field} must be boolean or null for an excluded managed principal")
            elif service_non_applicable:
                if value is not None and value is not False:
                    issues.append(f"{path}.{field} must be false or null when not applicable to {user_type}")
            elif type(value) is not bool:
                issues.append(f"{path}.{field} must be boolean")
        if dataset == "current_users" and type(row.get("metadata_visible")) is not bool:
            issues.append(f"{path}.metadata_visible must be boolean")
        elif (
            dataset == "current_users" and user_type != "SNOWFLAKE_SERVICE" and row.get("metadata_visible") is not True
        ):
            issues.append(f"{path} is privilege-filtered; SHOW USERS metadata is incomplete")
    if not values:
        issues.append(f"datasets.{dataset} is empty and cannot establish a user denominator")
    return issues


def _login_issues(values: Any, observed_at: datetime | None) -> list[str]:
    issues: list[str] = []
    if not isinstance(values, list):
        return ["datasets.login_history is not an array"]
    seen: set[str] = set()
    for index, row in enumerate(values):
        path = f"datasets.login_history[{index}]"
        if not isinstance(row, dict):
            issues.append(f"{path} is not an object")
            continue
        if set(row) != LOGIN_FIELDS:
            issues.append(f"{path} fields do not match the reviewed privacy projection")
            continue
        event_digest = row.get("auth_event_sha256")
        if not _hash_valid(event_digest):
            issues.append(f"{path}.auth_event_sha256 is invalid")
        elif event_digest in seen:
            issues.append(f"{path}.auth_event_sha256 is duplicated")
        else:
            seen.add(event_digest)
        if not _hash_valid(row.get("user_name_sha256"), nullable=True):
            issues.append(f"{path}.user_name_sha256 is invalid")
        if row.get("is_success") is True and row.get("user_name_sha256") is None:
            issues.append(f"{path} has a successful event without a resolved user digest")
        if row.get("event_type") != "LOGIN":
            issues.append(f"{path}.event_type is not LOGIN")
        for field in (
            "first_authentication_factor",
            "second_authentication_factor",
        ):
            if not _safe_observation(row.get(field)):
                issues.append(f"{path}.{field} is not a bounded observation label")
        if row.get("is_success") is not None and type(row.get("is_success")) is not bool:
            issues.append(f"{path}.is_success must be boolean or null")
        if row.get("error_code") is not None and (type(row.get("error_code")) is not int or row.get("error_code") < 0):
            issues.append(f"{path}.error_code must be a non-negative integer or null")
        try:
            event_time = parse_time(row.get("event_timestamp"), f"{path}.event_timestamp")
            if observed_at is not None and event_time >= observed_at - timedelta(seconds=LOGIN_HISTORY_LATENCY_SECONDS):
                issues.append(f"{path}.event_timestamp is inside the unsettled Account Usage latency window")
            if observed_at is not None and event_time < observed_at - timedelta(seconds=LOGIN_HISTORY_WINDOW_SECONDS):
                issues.append(f"{path}.event_timestamp is outside the reviewed seven-day SQL window")
        except AuthEvidenceError as exc:
            issues.append(str(exc))
    return issues


def validate_receipt(
    wrapper: Any,
    surface: str,
    evaluation_time: datetime,
    max_age_seconds: int,
    input_trusted: bool,
    expected_context: tuple[str, ...],
) -> tuple[dict[str, Any], dict[str, list[dict[str, Any]]], tuple[str, ...] | None]:
    issues: list[str] = []
    if not isinstance(wrapper, dict):
        wrapper = {}
        issues.append("receipt wrapper is not an object")
    if set(wrapper) - {"receipt"}:
        issues.append("receipt wrapper contains unsupported fields")
    receipt = wrapper.get("receipt")
    if not isinstance(receipt, dict):
        receipt = {}
        issues.append("receipt is not an object")
    if set(receipt) != AUTH_RECEIPT_FIELDS:
        issues.append("receipt fields do not match the exact reviewed envelope")
    sql, filename, sources, expected_datasets, cap_dataset = _expected_sql(surface)
    expected_hash = f"sha256:{hashlib.sha256(sql).hexdigest()}"
    if receipt.get("schema_version") != "2":
        issues.append("schema_version is not 2")
    if receipt.get("surface") != surface:
        issues.append(f"surface is not {surface}")
    if receipt.get("status") != "collected":
        issues.append("status is not collected")
    if receipt.get("errors") != []:
        issues.append("errors must be exactly an empty array for a collected receipt")
    if receipt.get("non_claims") != list(COLLECTOR.RECEIPT_NON_CLAIMS):
        issues.append("non_claims do not match the canonical collector boundary")
    if receipt.get("collection_mode") != "live-cli":
        issues.append("collection_mode is not live-cli")
    receipt_profile = receipt.get("connection_profile")
    profile_safe = isinstance(receipt_profile, str) and bool(COLLECTOR.PROFILE_RE.fullmatch(receipt_profile))
    if not profile_safe:
        issues.append("connection_profile does not match the safe profile-name grammar")
    collected = started = completed = None
    try:
        collected = parse_time(receipt.get("collected_at"), "receipt.collected_at")
        started = parse_time(receipt.get("collection_started_at"), "receipt.collection_started_at")
        completed = parse_time(receipt.get("collection_completed_at"), "receipt.collection_completed_at")
        if not started <= completed <= collected <= evaluation_time:
            issues.append("receipt collection timestamps are not ordered through evaluation time")
        if collected > datetime.now(timezone.utc):
            issues.append("receipt.collected_at is in the future")
        if (evaluation_time - completed).total_seconds() > max_age_seconds:
            issues.append("receipt exceeds metadata.max_age_seconds")
        if (completed - started).total_seconds() > max_age_seconds:
            issues.append("receipt collection interval exceeds metadata.max_age_seconds")
    except AuthEvidenceError as exc:
        issues.append(str(exc))
    if receipt.get("sql_sha256") != expected_hash:
        issues.append("sql_sha256 does not match the reviewed SQL")
    if receipt.get("template_sha256") != expected_hash:
        issues.append("template_sha256 does not match the reviewed SQL")
    if receipt.get("rendered_sql_sha256") != expected_hash:
        issues.append("rendered_sql_sha256 does not match the reviewed SQL")
    if receipt.get("selector_fingerprint") is not None:
        issues.append("selector_fingerprint must be null for this surface")
    if receipt.get("source_views") != sources:
        issues.append("source_views do not match the reviewed surface")
    if receipt.get("source_metadata") != {"template": filename, "source_views": sources, "selector": {}}:
        issues.append("source_metadata does not match the reviewed surface")
    if not _receipt_hash_valid(receipt):
        issues.append("receipt_sha256 is missing or invalid")
    datasets = receipt.get("datasets")
    if not isinstance(datasets, dict):
        datasets = {}
        issues.append("datasets is not an object")
    if receipt.get("expected_datasets") != list(expected_datasets):
        issues.append("expected_datasets do not match the reviewed surface")
    if set(datasets) != set(expected_datasets):
        issues.append("datasets do not match the reviewed surface")
    counts: dict[str, int] = {}
    for name, values in datasets.items():
        if isinstance(values, list) and all(isinstance(row, dict) for row in values):
            counts[name] = len(values)
        else:
            issues.append(f"datasets.{name} is not an array of objects")
    if receipt.get("dataset_row_counts") != counts:
        issues.append("dataset_row_counts do not match datasets")
    row_total = sum(counts.values())
    if type(receipt.get("row_count")) is not int or receipt.get("row_count") != row_total:
        issues.append("row_count does not match datasets")
    limits = re.findall(rb"\bLIMIT\s+(\d+)\b", sql, flags=re.IGNORECASE)
    expected_limit = int(limits[-1]) if limits else None
    if expected_limit is None or receipt.get("row_limit") != expected_limit:
        issues.append("row_limit does not match the reviewed SQL cap")
    cap_count = counts.get(cap_dataset, 0)
    expected_truncation = expected_limit is not None and cap_count >= expected_limit
    if receipt.get("truncation_possible") is not expected_truncation:
        issues.append("truncation_possible is inconsistent with the reviewed cap")
    if expected_truncation:
        issues.append("receipt reached the reviewed row cap")
    contexts = datasets.get("execution_context", [])
    context_signature = None
    context_observed = None
    if not isinstance(contexts, list) or len(contexts) != 1 or not isinstance(contexts[0], dict):
        issues.append("execution_context must contain exactly one same-statement row")
    else:
        context_findings, context_signature, context_observed = _context_issues(
            contexts[0], "datasets.execution_context[0]"
        )
        issues.extend(context_findings)
        if context_signature is not None and context_signature != expected_context:
            issues.append("execution_context does not match metadata.authorization_context")
        if context_observed is not None and started is not None and completed is not None:
            if not started <= context_observed <= completed:
                issues.append("execution_context.observed_at is outside the collection interval")
            elif (evaluation_time - context_observed).total_seconds() > max_age_seconds:
                issues.append("execution_context.observed_at exceeds metadata.max_age_seconds")
    if surface == "auth-current":
        issues.extend(_user_issues("current_users", datasets.get("current_users")))
    elif surface == "auth":
        issues.extend(_user_issues("historical_users", datasets.get("historical_users")))
    else:
        issues.extend(_login_issues(datasets.get("login_history"), context_observed))
    unique_issues = sorted(set(issues))
    if unique_issues:
        status = "INVALID"
    elif input_trusted:
        status = "DIGEST_MATCHED_OPERATOR_ASSERTED"
    else:
        status = "SELF_CONSISTENT_UNTRUSTED"
    complete = not unique_issues and input_trusted
    safe_datasets = datasets if complete else {name: [] for name in expected_datasets}
    return (
        {
            "surface": surface,
            "status": status,
            "complete": complete,
            "issues": unique_issues,
            "connection_profile": receipt_profile if profile_safe else None,
            "collected_at": collected.isoformat() if collected else None,
            "collection_started_at": started.isoformat() if started else None,
            "collection_completed_at": completed.isoformat() if completed else None,
            "row_count": receipt.get("row_count"),
            "truncation_possible": receipt.get("truncation_possible"),
        },
        safe_datasets,
        context_signature if complete else None,
    )


def _user_map(values: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row["user_name_sha256"]): row for row in values}


def _reconcile_users(current: list[dict[str, Any]], historical: list[dict[str, Any]]) -> dict[str, Any]:
    current_map = _user_map(current)
    historical_map = _user_map(historical)
    current_only = sorted(set(current_map) - set(historical_map))
    historical_only = sorted(set(historical_map) - set(current_map))
    drift: list[dict[str, str]] = []
    for digest in sorted(set(current_map) & set(historical_map)):
        current_type = current_map[digest].get("type")
        historical_type = historical_map[digest].get("type")
        for field in ("created_on", *POSTURE_FIELDS):
            current_value = current_map[digest].get(field)
            historical_value = historical_map[digest].get(field)
            if field == "created_on":
                current_value = (
                    parse_time(current_value, "current_users.created_on").isoformat()
                    if current_value is not None
                    else None
                )
                historical_value = (
                    parse_time(historical_value, "historical_users.created_on").isoformat()
                    if historical_value is not None
                    else None
                )
            elif (
                field in {"has_password", "has_mfa"}
                and current_type == historical_type
                and current_type in {"SERVICE", "SERVICE_AGENT"}
            ):
                # Snowflake can expose a non-applicable service field as FALSE in
                # SHOW USERS and NULL in Account Usage. Both mean "not present";
                # neither is a positive posture claim.
                current_value = current_value is True
                historical_value = historical_value is True
            if current_value != historical_value:
                drift.append({"user_name_sha256": digest, "field": field})
    status = (
        "MATCHED_WITHIN_SCOPE" if not current_only and not historical_only and not drift else "DRIFT_REQUIRES_REVIEW"
    )
    return {
        "status": status,
        "current_count": len(current_map),
        "historical_count": len(historical_map),
        "current_only": current_only,
        "historical_only": historical_only,
        "field_drift": drift,
    }


def _operator_scope(
    data: dict[str, Any], coverage: list[str], current_users: list[dict[str, Any]]
) -> tuple[list[str], dict[str, str]]:
    issues: list[str] = []
    name_to_hash: dict[str, str] = {}
    methods_by_hash: dict[str, set[str]] = {}
    current_by_hash = _user_map(current_users)
    method_fields = {
        "KEY_PAIR": "has_rsa_public_key",
        "PAT": "has_pat",
        "WIF": "has_workload_identity",
    }
    users = data.get("users", [])
    workloads = data.get("workloads", [])
    if not isinstance(users, list) or any(not isinstance(row, dict) for row in users):
        raise AuthEvidenceError("users must be an array of objects")
    if not isinstance(workloads, list) or any(not isinstance(row, dict) for row in workloads):
        raise AuthEvidenceError("workloads must be an array of objects")
    for index, row in enumerate(users):
        name = str(row.get("name", "")).strip().upper()
        digest = row.get("user_name_sha256")
        if not name or not _hash_valid(digest):
            issues.append(f"users[{index}] lacks a name and matching Snowflake-side user digest")
            continue
        if name in name_to_hash or digest in name_to_hash.values():
            issues.append(f"users[{index}] duplicates an identity or digest")
        name_to_hash[name] = digest
        if not str(row.get("owner", "")).strip():
            issues.append(f"users[{index}] has no owner")
        current = current_by_hash.get(str(digest), {})
        declared_type = str(row.get("type") or "").strip().upper()
        if declared_type != current.get("type"):
            issues.append(f"users[{index}].type does not match receipted current posture")
        try:
            methods = set(LEGACY.list_upper(row.get("auth_methods"), f"users[{index}].auth_methods"))
        except ValueError as exc:
            issues.append(str(exc))
            methods = set()
        if not methods or not methods <= LEGACY.METHODS:
            issues.append(f"users[{index}].auth_methods is empty or contains unsupported methods")
        password_methods = methods & {"PASSWORD", "BASIC"}
        if bool(password_methods) is not (current.get("has_password") is True):
            issues.append(f"users[{index}].auth_methods does not match receipted password posture")
        for method, field in method_fields.items():
            if (method in methods) is not (current.get(field) is True):
                issues.append(f"users[{index}].auth_methods does not match receipted {method} posture")
        if methods & {"OAUTH", "SAML"}:
            issues.append(f"users[{index}].auth_methods includes methods not provable from user posture receipts")
        methods_by_hash[str(digest)] = methods
    workload_names: set[str] = set()
    for index, row in enumerate(workloads):
        name = str(row.get("name", "")).strip()
        normalized_name = name.upper()
        if normalized_name in workload_names:
            issues.append(f"workloads[{index}].name duplicates another workload")
        elif normalized_name:
            workload_names.add(normalized_name)
        identity = str(row.get("identity") or row.get("user") or row.get("service_user") or "").strip().upper()
        digest = row.get("identity_sha256")
        if not name or identity not in name_to_hash or digest != name_to_hash.get(identity):
            issues.append(f"workloads[{index}] is not one-to-one bound to a declared identity digest")
        if not str(row.get("owner", "")).strip():
            issues.append(f"workloads[{index}] has no owner")
        current_auth = str(row.get("current_auth") or "").strip().upper()
        if current_auth not in methods_by_hash.get(str(digest), set()):
            issues.append(f"workloads[{index}].current_auth does not match receipted operator auth methods")
    if sorted(name_to_hash.values()) != coverage:
        issues.append("declared operator users do not exactly match metadata.coverage.user_name_sha256")
    return sorted(set(issues)), name_to_hash


def _login_identity_issues(
    login_rows: list[dict[str, Any]], current_users: list[dict[str, Any]]
) -> tuple[list[str], set[str]]:
    issues: list[str] = []
    quarantined_events: set[str] = set()
    current_by_hash = _user_map(current_users)
    for index, row in enumerate(login_rows):
        digest = row.get("user_name_sha256")
        current = current_by_hash.get(str(digest))
        if current is None:
            continue
        try:
            event_time = parse_time(row.get("event_timestamp"), f"datasets.login_history[{index}].event_timestamp")
            created_on = parse_time(current.get("created_on"), f"current_users[{digest}].created_on")
            if event_time < created_on:
                issues.append(
                    f"datasets.login_history[{index}] predates the reconciled current principal creation time"
                )
                event_digest = row.get("auth_event_sha256")
                if isinstance(event_digest, str):
                    quarantined_events.add(event_digest)
        except AuthEvidenceError as exc:
            issues.append(str(exc))
    return sorted(set(issues)), quarantined_events


def _window_assessment(
    data: dict[str, Any],
    evaluation_time: datetime,
    settled_through: datetime | None,
    name_to_hash: dict[str, str],
) -> dict[str, Any]:
    windows = data.get("enforcement_windows", [])
    workloads = data.get("workloads", [])
    issues: list[str] = []
    assessed: list[dict[str, Any]] = []
    if not isinstance(windows, list) or any(not isinstance(row, dict) for row in windows):
        return {"status": "INVALID", "issues": ["enforcement_windows must be an array of objects"], "windows": []}
    workload_names = [str(row.get("name", "")).strip().upper() for row in workloads if isinstance(row, dict)]
    if len(workload_names) != len(set(workload_names)):
        issues.append("duplicate workload names cannot define an enforcement-window denominator")
    workload_map = {str(row.get("name", "")).strip().upper(): row for row in workloads if isinstance(row, dict)}
    observed_workloads: list[str] = []
    for index, row in enumerate(windows):
        path = f"enforcement_windows[{index}]"
        workload = str(row.get("workload", "")).strip().upper()
        observed_workloads.append(workload)
        start = end = None
        try:
            start = parse_time(row.get("start"), f"{path}.start")
            end = parse_time(row.get("end"), f"{path}.end")
            if not start < end <= evaluation_time:
                issues.append(f"{path} is not an ordered completed window")
        except AuthEvidenceError as exc:
            issues.append(str(exc))
        identity = str(workload_map.get(workload, {}).get("identity", "")).strip().upper()
        if workload not in workload_map or row.get("identity_sha256") != name_to_hash.get(identity):
            issues.append(f"{path} does not match the workload identity digest")
        if not all(str(row.get(field, "")).strip() for field in ("name", "owner", "approved_by", "change_id")):
            issues.append(f"{path} lacks name, owner, approver, or change identifier")
        selected = (
            LEGACY.choose_target(
                LEGACY.list_upper(
                    workload_map.get(workload, {}).get("supported_auth")
                    or workload_map.get(workload, {}).get("target_auth_options")
                    or workload_map.get(workload, {}).get("allowed_auth_methods"),
                    f"{path}.target_options",
                )
            )
            if workload in workload_map
            else "MANUAL_REVIEW"
        )
        if str(row.get("target_auth", "")).strip().upper() != selected:
            issues.append(f"{path}.target_auth does not match the deterministic plan")
        settled = end is not None and settled_through is not None and end <= settled_through
        if not settled:
            issues.append(f"{path} is inside the unsettled Account Usage latency boundary")
        assessed.append(
            {
                "name": str(row.get("name", "")),
                "workload": workload,
                "target_auth": selected,
                "start": start.isoformat() if start else None,
                "end": end.isoformat() if end else None,
                "account_usage_settled": settled,
            }
        )
    expected = sorted(workload_map)
    if sorted(observed_workloads) != expected:
        issues.append("enforcement windows do not cover each declared workload exactly once")
    return {
        "status": "VALID" if not issues else "INVALID",
        "issues": sorted(set(issues)),
        "windows": assessed,
        "settled_through": settled_through.isoformat() if settled_through else None,
    }


def _target_capability_assessment(
    data: dict[str, Any],
    name_to_hash: dict[str, str],
    current_users: list[dict[str, Any]],
) -> dict[str, Any]:
    current_by_hash = _user_map(current_users)
    posture_field = {
        "KEY_PAIR": "has_rsa_public_key",
        "PASSWORD": "has_password",
        "PAT": "has_pat",
        "WIF": "has_workload_identity",
    }
    workloads: list[dict[str, Any]] = []
    for row in data.get("workloads", []):
        if not isinstance(row, dict):
            continue
        options = LEGACY.list_upper(
            row.get("supported_auth") or row.get("target_auth_options") or row.get("allowed_auth_methods"),
            "workloads.target_options",
        )
        target = LEGACY.choose_target(options)
        identity = str(row.get("identity") or row.get("user") or row.get("service_user") or "").strip().upper()
        digest = name_to_hash.get(identity)
        field = posture_field.get(target)
        configured = current_by_hash.get(str(digest), {}).get(field) if field else None
        workloads.append(
            {
                "workload": str(row.get("name", "")).strip().upper(),
                "selected_target": target,
                "operator_declared_option": target != "MANUAL_REVIEW" and target in options,
                "current_configuration_field": field,
                "current_configuration_observation": configured,
                "capability_status": "OPERATOR_DECLARED_NOT_INDEPENDENTLY_VERIFIED",
            }
        )
    return {
        "status": "OPERATOR_DECLARED_NOT_INDEPENDENTLY_VERIFIED",
        "workloads": workloads,
        "non_claim": (
            "supported_auth is operator input. Current posture flags describe configuration, not runtime, "
            "driver, connector, integration, or target-login capability."
        ),
    }


def analyze_bundle(data: dict[str, Any], *, trusted_input_sha256: str | None = None) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise AuthEvidenceError("input must be a JSON object")
    if not BUNDLE_REQUIRED_FIELDS <= set(data) or set(data) - BUNDLE_REQUIRED_FIELDS - BUNDLE_OPTIONAL_FIELDS:
        raise AuthEvidenceError("input fields do not match the exact schema-2 bundle envelope")
    if data.get("schema_version") != "2.0":
        raise AuthEvidenceError("schema_version must be 2.0")
    metadata = data.get("metadata")
    if not isinstance(metadata, dict) or set(metadata) != METADATA_FIELDS:
        raise AuthEvidenceError("metadata fields do not match the exact schema-2 contract")
    evaluation_time = parse_time(metadata.get("evaluated_at"), "metadata.evaluated_at")
    current_time = datetime.now(timezone.utc)
    if evaluation_time > current_time:
        raise AuthEvidenceError("metadata.evaluated_at must not be in the future")
    if (current_time - evaluation_time).total_seconds() > MAX_EVALUATION_CLOCK_AGE_SECONDS:
        raise AuthEvidenceError("metadata.evaluated_at exceeds the five-minute analysis clock boundary")
    max_age_seconds = metadata.get("max_age_seconds")
    if type(max_age_seconds) is not int or not 0 < max_age_seconds <= MAX_RECEIPT_AGE_SECONDS:
        raise AuthEvidenceError("metadata.max_age_seconds must be an integer from 1 through 3600")
    connection_profile = metadata.get("connection_profile")
    if not isinstance(connection_profile, str) or not COLLECTOR.PROFILE_RE.fullmatch(connection_profile):
        raise AuthEvidenceError("metadata.connection_profile does not match the safe profile-name grammar")
    if metadata.get("login_history_latency_seconds") != LOGIN_HISTORY_LATENCY_SECONDS:
        raise AuthEvidenceError("metadata.login_history_latency_seconds must be 7200")
    expected_context = _authorization_context_signature(metadata.get("authorization_context"))
    coverage_obj = metadata.get("coverage")
    if not isinstance(coverage_obj, dict) or set(coverage_obj) != {"user_name_sha256"}:
        raise AuthEvidenceError("metadata.coverage must contain only user_name_sha256")
    coverage = coverage_obj.get("user_name_sha256")
    if not isinstance(coverage, list) or not coverage or any(not _hash_valid(value) for value in coverage):
        raise AuthEvidenceError("metadata.coverage.user_name_sha256 must be a non-empty digest array")
    if len(coverage) != len(set(coverage)):
        raise AuthEvidenceError("metadata.coverage.user_name_sha256 contains duplicates")
    coverage = sorted(coverage)
    actual_digest = input_sha256(data)
    digest_well_formed = isinstance(trusted_input_sha256, str) and bool(DIGEST_RE.fullmatch(trusted_input_sha256))
    input_trusted = digest_well_formed and trusted_input_sha256 == actual_digest
    if trusted_input_sha256 is None:
        trust_status = "UNTRUSTED"
    elif not digest_well_formed:
        trust_status = "INVALID_TRUST_ANCHOR"
    elif not input_trusted:
        trust_status = "DIGEST_MISMATCH"
    else:
        trust_status = "DIGEST_MATCHED_OPERATOR_ASSERTED"
    collections = data.get("collections")
    if not isinstance(collections, dict):
        collections = {}
    expected_collection_keys = {"current", "historical", "login_history"}
    collection_issues = []
    if set(collections) != expected_collection_keys:
        collection_issues.append("collections must contain exactly current, historical, and login_history")
    assessments: list[dict[str, Any]] = []
    trusted_datasets: dict[str, dict[str, list[dict[str, Any]]]] = {}
    contexts: list[tuple[str, ...]] = []
    for key, surface in (
        ("current", "auth-current"),
        ("historical", "auth"),
        ("login_history", "auth-login-history"),
    ):
        assessment, datasets, context = validate_receipt(
            collections.get(key), surface, evaluation_time, max_age_seconds, input_trusted, expected_context
        )
        assessment["collection"] = key
        assessments.append(assessment)
        trusted_datasets[key] = datasets
        if context is not None:
            contexts.append(context)
    if any(item.get("connection_profile") != connection_profile for item in assessments):
        collection_issues.append("every receipt must use metadata.connection_profile")
    if len(contexts) != 3 or len(set(contexts)) != 1 or any(context != expected_context for context in contexts):
        collection_issues.append("receipt authorization contexts do not match the declared expected context")
    current_user_rows = trusted_datasets["current"].get("current_users", [])
    historical_user_rows = trusted_datasets["historical"].get("historical_users", [])
    current_users = [row for row in current_user_rows if row.get("principal_scope") == "OPERATOR_OWNED"]
    historical_users = [row for row in historical_user_rows if row.get("principal_scope") == "OPERATOR_OWNED"]
    login_rows = trusted_datasets["login_history"].get("login_history", [])
    reconciliation = _reconcile_users(current_users, historical_users)
    current_hashes = sorted(row["user_name_sha256"] for row in current_users)
    if current_hashes != coverage:
        collection_issues.append("trusted current users do not exactly match declared digest coverage")
    operator_issues, name_to_hash = _operator_scope(data, coverage, current_users)
    login_identity_issues, quarantined_login_events = _login_identity_issues(login_rows, current_users)
    collection_issues.extend(login_identity_issues)
    try:
        LEGACY.reject_credentials(
            {
                "users": data.get("users", []),
                "workloads": data.get("workloads", []),
                "integrations": data.get("integrations", []),
                "enforcement_windows": data.get("enforcement_windows", []),
            }
        )
    except ValueError as exc:
        raise AuthEvidenceError(str(exc)) from exc
    login_context_rows = trusted_datasets["login_history"].get("execution_context", [])
    login_observed = (
        parse_time(login_context_rows[0].get("observed_at"), "login execution_context.observed_at")
        if len(login_context_rows) == 1
        else None
    )
    settled_through = login_observed - timedelta(seconds=LOGIN_HISTORY_LATENCY_SECONDS) if login_observed else None
    windows = _window_assessment(data, evaluation_time, settled_through, name_to_hash)
    receipt_complete = all(item["complete"] for item in assessments)
    evidence_scope_complete = (
        receipt_complete
        and not collection_issues
        and not operator_issues
        and reconciliation["status"] == "MATCHED_WITHIN_SCOPE"
        and windows["status"] == "VALID"
    )
    login_by_user: dict[str, dict[str, int]] = {}
    for row in login_rows:
        digest = row.get("user_name_sha256")
        if (
            not isinstance(digest, str)
            or digest not in coverage
            or row.get("auth_event_sha256") in quarantined_login_events
        ):
            continue
        counts = login_by_user.setdefault(digest, {"successful": 0, "failed": 0, "unknown": 0})
        if row.get("is_success") is True:
            counts["successful"] += 1
        elif row.get("is_success") is False:
            counts["failed"] += 1
        else:
            counts["unknown"] += 1
    planner_input = {
        "metadata": {
            "collected_at": metadata.get("evaluated_at"),
            "window_start": min(
                (
                    row.get("start")
                    for row in data.get("enforcement_windows", [])
                    if isinstance(row, dict) and row.get("start")
                ),
                default=metadata.get("evaluated_at"),
            ),
            "window_end": max(
                (
                    row.get("end")
                    for row in data.get("enforcement_windows", [])
                    if isinstance(row, dict) and row.get("end")
                ),
                default=metadata.get("evaluated_at"),
            ),
            "freshness": {
                "status": "FRESH" if evidence_scope_complete else "UNVERIFIED",
                "checked_at": metadata.get("evaluated_at"),
                "max_age_seconds": max_age_seconds,
            },
        },
        "users": data.get("users", []) if not operator_issues else [],
        "workloads": data.get("workloads", []) if not operator_issues else [],
        "integrations": data.get("integrations", []),
        "break_glass": {},
        "canary": {},
    }
    plan = LEGACY.analyze(planner_input)
    target_capability = _target_capability_assessment(data, name_to_hash, current_users)
    return {
        "schema_version": "2.0",
        "input_sha256": actual_digest,
        "evidence_trust": {
            "status": trust_status,
            "trusted": input_trusted,
            "non_claim": "A matching digest is an operator assertion of byte identity, not a signature or proof of origin.",
        },
        "receipt_assessments": assessments,
        "evidence_issues": sorted(set(collection_issues + operator_issues)),
        "authorization_context": {
            "status": "MATCHED_DECLARED_EQUIVALENT_CONTEXT"
            if len(contexts) == 3
            and len(set(contexts)) == 1
            and all(context == expected_context for context in contexts)
            else "UNVERIFIED",
            "physical_session_claim": "NOT_CLAIMED_INDEPENDENT_INVOCATIONS",
        },
        "current_historical_reconciliation": reconciliation,
        "managed_principal_exclusions": {
            "current": sum(row.get("principal_scope") == "SNOWFLAKE_MANAGED_EXCLUDED" for row in current_user_rows),
            "historical": sum(
                row.get("principal_scope") == "SNOWFLAKE_MANAGED_EXCLUDED" for row in historical_user_rows
            ),
            "non_claim": "Snowflake-managed principals remain in cap accounting but are excluded from the operator migration denominator.",
        },
        "enforcement_window_assessment": windows,
        "target_capability_assessment": target_capability,
        "login_history_observation": {
            "status": (
                "UNRESOLVED_PREDECESSOR_OBSERVATION"
                if quarantined_login_events
                else "OBSERVED"
                if login_by_user
                else "NOT_OBSERVED"
                if receipt_complete
                else "UNTRUSTED"
            ),
            "by_user_name_sha256": dict(sorted(login_by_user.items())),
            "non_claim": "LOGIN_HISTORY is delayed observation and does not by itself prove canary causality, policy enforcement, or absence.",
        },
        "claims": {
            "current_posture_supported": evidence_scope_complete,
            "history_reconciliation_supported": evidence_scope_complete,
            "declared_workload_coverage_supported": evidence_scope_complete,
            "login_history_surface_supported": receipt_complete and not collection_issues,
            "target_capability_supported": False,
            "canary_operational_proof_supported": False,
            "recovery_proof_supported": False,
            "cutover_ready": False,
            "account_wide_absence_claim_blocked": True,
        },
        "evidence_scope_complete": evidence_scope_complete,
        "completeness_claim_blocked": not evidence_scope_complete,
        "cutover_approval": {
            "eligible": False,
            "status": "OPERATOR_REVIEW_REQUIRED"
            if evidence_scope_complete and windows["status"] == "VALID"
            else "UNVERIFIED_EVIDENCE",
            "reason": "The packet is read-only guidance. Bound positive, negative, and independently tested recovery receipts remain an operator approval gate.",
        },
        "migration_plan_status": (
            "POSTURE_EVIDENCE_BOUND_TARGET_CAPABILITY_UNVERIFIED" if evidence_scope_complete else "UNVERIFIED_PLAN"
        ),
        "migration_plan": plan,
        "safety": {
            "edit_authority": False,
            "analyzer_snowflake_operations_executed": False,
            "reviewed_collector_sql_mutating": False,
            "external_mutation_attestation": "NOT_CLAIMED",
            "credential_values_accepted": False,
        },
        "non_claims": [
            "SHOW USERS alone does not prove historical completeness, authentication use, or policy enforcement.",
            "Account Usage USERS and LOGIN_HISTORY can lag by up to 120 minutes.",
            "An empty or non-matching LOGIN_HISTORY window does not prove that no authentication occurred.",
            "Pseudonymous SHA-256 identity values remain sensitive and can be dictionary-tested.",
            "The analyzer performed no Snowflake operation; reviewed collector statements are read-only; surrounding session and workflow operations are not attested.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="Receipted authentication-evidence bundle")
    parser.add_argument("--out", type=Path, help="Write JSON report; stdout when omitted")
    parser.add_argument(
        "--trusted-input-sha256",
        help="Out-of-band sha256:<hex> recorded when the final bundle crossed a controlled local boundary",
    )
    parser.add_argument(
        "--print-input-sha256",
        action="store_true",
        help="Print the canonical bundle digest for separate trusted-boundary recording",
    )
    args = parser.parse_args(argv)
    try:
        data = json.loads(args.input.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise AuthEvidenceError("input must be a JSON object")
        if args.print_input_sha256:
            print(input_sha256(data))
            return 0
        report = analyze_bundle(data, trusted_input_sha256=args.trusted_input_sha256)
        rendered = json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            temporary = args.out.with_name(f".{args.out.name}.tmp")
            temporary.write_text(rendered, encoding="utf-8")
            temporary.replace(args.out)
        else:
            sys.stdout.write(rendered)
        return 0
    except (AuthEvidenceError, OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"error: {COLLECTOR.sanitize_text(exc)}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
