#!/usr/bin/env python3
"""Verify receipted Snowflake access evidence and run scoped graph analysis."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
SQL_DIR = HERE / "sql"
ANALYZER_PATH = HERE / "analyze_access.py"
ANALYZER_SPEC = importlib.util.spec_from_file_location("snowflake_access_graph", ANALYZER_PATH)
if ANALYZER_SPEC is None or ANALYZER_SPEC.loader is None:  # pragma: no cover - package corruption
    raise RuntimeError(f"cannot load bundled analyzer: {ANALYZER_PATH}")
ANALYZER = importlib.util.module_from_spec(ANALYZER_SPEC)
ANALYZER_SPEC.loader.exec_module(ANALYZER)

DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_$]{0,254}$")
QUALIFIED_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_$]{0,254}\.[A-Za-z_][A-Za-z0-9_$]{0,254}$")
OBJECT_IDENTIFIER_RE = re.compile(
    r"^[A-Za-z_][A-Za-z0-9_$]{0,254}\.[A-Za-z_][A-Za-z0-9_$]{0,254}\.[A-Za-z_][A-Za-z0-9_$]{0,254}$"
)
SURFACE_CONTRACTS: dict[str, tuple[str, list[str], str | None, tuple[str, ...]]] = {
    "access": (
        "access.sql",
        [
            "SNOWFLAKE.ACCOUNT_USAGE.GRANTS_TO_ROLES",
            "SNOWFLAKE.ACCOUNT_USAGE.GRANTS_TO_USERS",
            "SNOWFLAKE.ACCOUNT_USAGE.ROLES",
        ],
        None,
        ("grants_to_roles", "grants_to_users", "roles"),
    ),
    "access-database-role-current": (
        "access-database-role-current.sql",
        ["SHOW GRANTS TO DATABASE ROLE"],
        "database_role",
        ("execution_context", "rows"),
    ),
    "access-future-database": (
        "access-future-database.sql",
        ["SHOW FUTURE GRANTS IN DATABASE"],
        "database",
        ("execution_context", "rows"),
    ),
    "access-future-schema": (
        "access-future-schema.sql",
        ["SHOW FUTURE GRANTS IN SCHEMA"],
        "schema",
        ("execution_context", "rows"),
    ),
    "access-role-current": (
        "access-role-current.sql",
        ["SHOW GRANTS TO ROLE"],
        "role",
        ("execution_context", "rows"),
    ),
    "access-role-parents": (
        "access-role-parents.sql",
        ["SHOW GRANTS OF ROLE"],
        "role",
        ("execution_context", "rows"),
    ),
    "access-session": (
        "access-session.sql",
        ["Snowflake current-session context functions"],
        None,
        ("session_context",),
    ),
    "access-user-current": (
        "access-user-current.sql",
        ["SHOW GRANTS TO USER"],
        "user",
        ("execution_context", "rows"),
    ),
}
MARKERS = {
    "database": "__DATABASE_IDENTIFIER__",
    "database_role": "__DATABASE_ROLE_IDENTIFIER__",
    "role": "__ROLE_IDENTIFIER__",
    "schema": "__SCHEMA_IDENTIFIER__",
    "user": "__USER_IDENTIFIER__",
}
COLLECTION_KEYS = {
    "database_role_current": "access-database-role-current",
    "future_database": "access-future-database",
    "future_schema": "access-future-schema",
    "role_current": "access-role-current",
    "role_parents": "access-role-parents",
    "user_current": "access-user-current",
}
COVERAGE_KEYS = {
    "database_role_current": "database_roles",
    "future_database": "future_databases",
    "future_schema": "future_schemas",
    "role_current": "roles",
    "role_parents": "roles",
    "user_current": "users",
}


class AccessEvidenceError(ValueError):
    """Raised when access evidence is malformed or unsafe to interpret."""


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def input_sha256(value: dict[str, Any]) -> str:
    return f"sha256:{hashlib.sha256(canonical_json(value)).hexdigest()}"


def parse_time(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise AccessEvidenceError(f"{field} must be a timezone-aware timestamp")
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError as exc:
        raise AccessEvidenceError(f"{field} must be a timezone-aware timestamp") from exc
    if parsed.tzinfo is None:
        raise AccessEvidenceError(f"{field} must be a timezone-aware timestamp")
    return parsed.astimezone(timezone.utc)


def _folded(row: dict[str, Any]) -> dict[str, Any]:
    return {str(key).casefold(): value for key, value in row.items()}


def _value(row: dict[str, Any], *names: str) -> Any:
    folded = _folded(row)
    for name in names:
        if name.casefold() in folded:
            return folded[name.casefold()]
    return None


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _upper(value: Any) -> str:
    return _text(value).upper()


def _principal_type(value: Any) -> str:
    normalized = _upper(value).replace("_", " ")
    if normalized == "ACCOUNT ROLE":
        return "ROLE"
    if normalized == "DATABASE ROLE":
        return "DATABASE_ROLE"
    return normalized.replace(" ", "_")


def _selector_value(selector_name: str, selector: dict[str, Any]) -> str:
    if set(selector) != {selector_name}:
        raise AccessEvidenceError(f"selector must contain only {selector_name}")
    value = selector[selector_name]
    pattern = QUALIFIED_IDENTIFIER_RE if selector_name in {"database_role", "schema"} else IDENTIFIER_RE
    if not isinstance(value, str) or not pattern.fullmatch(value):
        raise AccessEvidenceError(f"selector.{selector_name} is not a supported unquoted identifier")
    return value


def _receipt_hash_is_valid(receipt: dict[str, Any]) -> bool:
    body = dict(receipt)
    supplied = body.pop("receipt_sha256", None)
    expected = f"sha256:{hashlib.sha256(canonical_json(body)).hexdigest()}"
    return supplied == expected


def _expected_sql(surface: str, selector: dict[str, Any]) -> tuple[bytes, bytes, str, list[str], tuple[str, ...]]:
    filename, sources, selector_name, datasets = SURFACE_CONTRACTS[surface]
    path = SQL_DIR / filename
    if path.is_symlink() or not path.is_file():
        raise AccessEvidenceError(f"reviewed SQL is missing or not a regular file: {filename}")
    template = path.read_bytes()
    rendered = template.decode("utf-8")
    if selector_name is None:
        if selector:
            raise AccessEvidenceError(f"{surface} does not accept a selector")
    else:
        value = _selector_value(selector_name, selector)
        rendered = rendered.replace(MARKERS[selector_name], value)
    if "__" in rendered:
        raise AccessEvidenceError(f"{surface} has an unresolved reviewed selector marker")
    return template, rendered.encode("utf-8"), filename, sources, datasets


ROW_FIELDS = {
    "access-database-role-current": {
        "created_on",
        "privilege",
        "granted_on",
        "name",
        "granted_to",
        "grantee_name",
        "grant_option",
        "granted_by",
    },
    "access-future-database": {
        "created_on",
        "privilege",
        "grant_on",
        "name",
        "grant_to",
        "grantee_name",
        "grant_option",
    },
    "access-future-schema": {
        "created_on",
        "privilege",
        "grant_on",
        "name",
        "grant_to",
        "grantee_name",
        "grant_option",
    },
    "access-role-current": {
        "created_on",
        "privilege",
        "granted_on",
        "name",
        "granted_to",
        "grantee_name",
        "grant_option",
        "granted_by",
    },
    "access-role-parents": {"created_on", "role", "granted_to", "grantee_name", "granted_by"},
    "access-user-current": {
        "created_on",
        "privilege",
        "granted_on",
        "name",
        "role",
        "granted_to",
        "grantee_name",
        "grant_option",
        "granted_by",
    },
}
EXECUTION_CONTEXT_FIELDS = {
    "observed_at",
    "session_id",
    "account_locator",
    "current_user_name",
    "primary_role",
    "primary_role_type",
    "secondary_roles",
}


def _surface_row_issues(surface: str, selector: dict[str, Any], datasets: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if surface not in ROW_FIELDS:
        return issues
    contexts = datasets.get("execution_context", [])
    if not isinstance(contexts, list) or len(contexts) != 1:
        issues.append("execution_context must contain exactly one same-statement row")
    elif set(contexts[0]) != EXECUTION_CONTEXT_FIELDS:
        issues.append("execution_context fields do not match the reviewed projection")
    else:
        try:
            _secondary_context(contexts[0])
        except AccessEvidenceError as exc:
            issues.append(str(exc))
    expected_fields = ROW_FIELDS[surface]
    rows = datasets.get("rows", [])
    if isinstance(rows, list):
        for index, row in enumerate(rows):
            if set(row) != expected_fields:
                issues.append(f"rows[{index}] fields do not match the reviewed projection")
                continue
            selector_name = SURFACE_CONTRACTS[surface][2]
            selector_value = _upper(selector.get(selector_name)) if selector_name else ""
            if surface in {"access-role-current", "access-database-role-current", "access-user-current"}:
                if _upper(row.get("grantee_name")) != selector_value:
                    issues.append(f"rows[{index}] grantee_name does not match the bound selector")
            elif surface == "access-role-parents" and _upper(row.get("role")) != selector_value:
                issues.append(f"rows[{index}] role does not match the bound selector")
            if surface == "access-role-parents":
                required = ("role", "granted_to", "grantee_name")
            elif surface == "access-user-current" and _text(row.get("role")):
                required = ("role", "granted_to", "grantee_name")
            else:
                required = (
                    "privilege",
                    "name",
                    "grantee_name",
                    "grant_option",
                    "grant_on" if surface.startswith("access-future-") else "granted_on",
                    "grant_to" if surface.startswith("access-future-") else "granted_to",
                )
            if any(not _text(row.get(field)) for field in required):
                issues.append(f"rows[{index}] is missing a required projected value")
            if surface.startswith("access-future-"):
                if _principal_type(row.get("grant_to")) == "USER":
                    issues.append(f"rows[{index}] is an impossible future grant directly to USER")
                if not _upper(row.get("name")).startswith(f"{selector_value}."):
                    issues.append(f"rows[{index}] future object template is outside the bound selector")
    return issues


def validate_receipt(
    wrapper: Any,
    surface: str,
    evaluation_time: datetime,
    max_age_seconds: int,
    input_trusted: bool,
) -> tuple[dict[str, Any], dict[str, Any]]:
    issues: list[str] = []
    if not isinstance(wrapper, dict):
        wrapper = {}
        issues.append("receipt wrapper is not an object")
    selector = wrapper.get("selector", {})
    if not isinstance(selector, dict):
        selector = {}
        issues.append("selector is not an object")
    receipt = wrapper.get("receipt")
    if not isinstance(receipt, dict):
        receipt = {}
        issues.append("receipt is not an object")
    try:
        template, rendered, filename, sources, expected_datasets = _expected_sql(surface, selector)
    except AccessEvidenceError as exc:
        template, rendered, filename, sources, expected_datasets = b"", b"", "", [], ()
        issues.append(str(exc))

    if receipt.get("schema_version") != "2":
        issues.append("schema_version is not 2")
    if receipt.get("surface") != surface:
        issues.append(f"surface is not {surface}")
    if receipt.get("status") != "collected":
        issues.append("status is not collected")
    if receipt.get("errors"):
        issues.append("collector reported an error")
    if not isinstance(receipt.get("connection_profile"), str) or not receipt["connection_profile"].strip():
        issues.append("connection_profile is missing")
    if receipt.get("collection_mode") != "live-cli":
        issues.append("collection_mode is not live-cli")

    receipt_time: datetime | None = None
    collection_started: datetime | None = None
    collection_completed: datetime | None = None
    try:
        receipt_time = parse_time(receipt.get("collected_at"), "receipt.collected_at")
        if receipt_time > evaluation_time or receipt_time > datetime.now(timezone.utc):
            issues.append("collected_at is after evaluation time or in the future")
        elif (evaluation_time - receipt_time).total_seconds() > max_age_seconds:
            issues.append("receipt exceeds metadata.max_age_seconds")
    except AccessEvidenceError as exc:
        issues.append(str(exc))
    try:
        collection_started = parse_time(receipt.get("collection_started_at"), "receipt.collection_started_at")
        collection_completed = parse_time(receipt.get("collection_completed_at"), "receipt.collection_completed_at")
        if collection_started > collection_completed:
            issues.append("collection_started_at is after collection_completed_at")
        if collection_completed > evaluation_time or collection_completed > datetime.now(timezone.utc):
            issues.append("collection_completed_at is after evaluation time or in the future")
        elif (evaluation_time - collection_completed).total_seconds() > max_age_seconds:
            issues.append("live collection exceeds metadata.max_age_seconds")
        if receipt_time is not None and receipt_time < collection_started:
            issues.append("collected_at predates collection_started_at")
    except AccessEvidenceError as exc:
        issues.append(str(exc))

    template_hash = f"sha256:{hashlib.sha256(template).hexdigest()}" if template else None
    rendered_hash = f"sha256:{hashlib.sha256(rendered).hexdigest()}" if rendered else None
    selector_fingerprint = f"sha256:{hashlib.sha256(canonical_json(selector)).hexdigest()}" if selector else None
    if receipt.get("sql_sha256") != template_hash:
        issues.append("sql_sha256 does not match the reviewed template")
    if receipt.get("template_sha256") != template_hash:
        issues.append("template_sha256 does not match the reviewed template")
    if receipt.get("rendered_sql_sha256") != rendered_hash:
        issues.append("rendered_sql_sha256 does not match the bound selector")
    if receipt.get("selector_fingerprint") != selector_fingerprint:
        issues.append("selector_fingerprint does not match the bound selector")
    if receipt.get("source_views") != sources:
        issues.append("source_views do not match the reviewed surface")
    expected_source_metadata = {
        "template": filename,
        "source_views": sources,
        "selector": {name: True for name in selector},
    }
    if receipt.get("source_metadata") != expected_source_metadata:
        issues.append("source_metadata does not match the reviewed surface and selector")
    if not _receipt_hash_is_valid(receipt):
        issues.append("receipt_sha256 is missing or invalid")

    datasets = receipt.get("datasets")
    if not isinstance(datasets, dict):
        datasets = {}
        issues.append("datasets is not an object")
    if receipt.get("expected_datasets") != list(expected_datasets):
        issues.append("expected_datasets does not match the reviewed surface")
    if set(datasets) != set(expected_datasets):
        issues.append("datasets do not match the reviewed surface")
    row_total = 0
    dataset_counts: dict[str, int] = {}
    for name, rows in datasets.items():
        if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
            issues.append(f"datasets.{name} is not an array of objects")
            continue
        dataset_counts[name] = len(rows)
        row_total += len(rows)
    issues.extend(_surface_row_issues(surface, selector, datasets))
    row_count = receipt.get("row_count")
    if not isinstance(row_count, int) or isinstance(row_count, bool) or row_count < 0:
        issues.append("row_count is invalid")
    elif row_count != row_total:
        issues.append("row_count does not match datasets")
    if receipt.get("dataset_row_counts") != dataset_counts:
        issues.append("dataset_row_counts do not match datasets")
    limits = re.findall(rb"\bLIMIT\s+(\d+)\b", rendered, flags=re.IGNORECASE)
    expected_limit = int(limits[-1]) if limits else None
    if surface != "access-session" and expected_limit is None:
        issues.append("reviewed SQL has no enforceable row cap")
    if receipt.get("row_limit") != expected_limit:
        issues.append("row_limit does not match the reviewed SQL")
    capped_row_count = len(datasets.get("rows", [])) if surface != "access" else row_count
    expected_truncation = (
        expected_limit is not None
        and isinstance(capped_row_count, int)
        and not isinstance(capped_row_count, bool)
        and capped_row_count >= expected_limit
    )
    if receipt.get("truncation_possible") is not expected_truncation:
        issues.append("truncation_possible is inconsistent with the reviewed cap")
    if expected_truncation:
        issues.append("receipt reached the reviewed row cap")

    unique_issues = sorted(set(issues))
    if unique_issues:
        status = "INVALID"
    elif input_trusted:
        status = "DIGEST_MATCHED_OPERATOR_ASSERTED"
    else:
        status = "SELF_CONSISTENT_UNTRUSTED"
    return (
        {
            "surface": surface,
            "selector": selector,
            "status": status,
            "complete": not unique_issues and input_trusted,
            "issues": unique_issues,
            "collected_at": receipt_time.isoformat() if receipt_time else None,
            "row_count": row_count,
            "truncation_possible": receipt.get("truncation_possible"),
            "connection_profile": receipt.get("connection_profile"),
            "collection_started_at": collection_started.isoformat() if collection_started else None,
            "collection_completed_at": collection_completed.isoformat() if collection_completed else None,
        },
        datasets if not unique_issues and input_trusted else {name: [] for name in expected_datasets},
    )


def _grant_key(row: dict[str, Any]) -> tuple[str, ...]:
    return (
        _upper(_value(row, "grantee", "grantee_name")),
        _principal_type(_value(row, "grantee_type", "granted_to", "grant_to")),
        _upper(_value(row, "privilege")),
        _upper(_value(row, "object", "object_name", "name")),
        _upper(_value(row, "object_type", "granted_on", "grant_on")),
        _upper(_value(row, "grant_option")),
        _upper(_value(row, "granted_by")),
    )


def _is_unqualified_database_role_edge(row: dict[str, Any]) -> bool:
    """Identify imported/system database-role links that cannot be scoped locally.

    SHOW GRANTS can expose Snowflake-provided database roles (for example,
    ALERT_VIEWER) without a database qualifier. Account Usage can omit these
    shared/imported relationships. Treating the short name as a local database
    role would create an impossible evidence denominator and could also let an
    unresolved edge participate in a proof.
    """

    granted_on = _upper(_value(row, "granted_on", "grant_on", "object_type"))
    child = _upper(_value(row, "name", "object_name"))
    return granted_on == "DATABASE_ROLE" and bool(child) and "." not in child


def _reconcile(current: list[dict[str, Any]], historical: list[dict[str, Any]]) -> dict[str, Any]:
    current_keys = {_grant_key(row) for row in current}
    historical_keys = {_grant_key(row) for row in historical}
    malformed = sorted(key for key in current_keys | historical_keys if not key[0] or not key[2])
    current_only = sorted(current_keys - historical_keys)
    historical_only = sorted(historical_keys - current_keys)
    if malformed:
        status = "INVALID_ROWS"
    elif current_only or historical_only:
        status = "DRIFT_REQUIRES_REVIEW"
    else:
        status = "MATCHED_WITHIN_SCOPE"
    return {
        "status": status,
        "current_count": len(current_keys),
        "historical_count": len(historical_keys),
        "current_only": [list(item) for item in current_only[:100]],
        "historical_only": [list(item) for item in historical_only[:100]],
        "difference_truncated": len(current_only) > 100 or len(historical_only) > 100,
        "malformed_rows": [list(item) for item in malformed[:20]],
    }


def _assignment_key(row: dict[str, Any]) -> tuple[str, ...]:
    return (
        _upper(_value(row, "grantee_name", "user")),
        _upper(_value(row, "role", "name")),
        _upper(_value(row, "granted_by")),
    )


def _reconcile_assignments(current: list[dict[str, Any]], historical: list[dict[str, Any]]) -> dict[str, Any]:
    current_keys = {_assignment_key(row) for row in current}
    historical_keys = {_assignment_key(row) for row in historical}
    malformed = sorted(key for key in current_keys | historical_keys if not key[0] or not key[1])
    current_only = sorted(current_keys - historical_keys)
    historical_only = sorted(historical_keys - current_keys)
    if malformed:
        status = "INVALID_ROWS"
    elif current_only or historical_only:
        status = "DRIFT_REQUIRES_REVIEW"
    else:
        status = "MATCHED_WITHIN_SCOPE"
    return {
        "status": status,
        "current_count": len(current_keys),
        "historical_count": len(historical_keys),
        "current_only": [list(item) for item in current_only[:100]],
        "historical_only": [list(item) for item in historical_only[:100]],
        "difference_truncated": len(current_only) > 100 or len(historical_only) > 100,
        "malformed_rows": [list(item) for item in malformed[:20]],
    }


def _role_edge_key(row: dict[str, Any], inherited_role: str) -> tuple[str, ...]:
    return (
        _upper(inherited_role),
        _upper(_value(row, "grantee_name", "grantee")),
        _principal_type(_value(row, "granted_to", "grant_to", "grantee_type")),
        _upper(_value(row, "granted_by")),
    )


def _reconcile_role_edges(
    current: list[dict[str, Any]], historical: list[dict[str, Any]], inherited_role: str
) -> dict[str, Any]:
    current_keys = {_role_edge_key(row, inherited_role) for row in current}
    historical_keys = {_role_edge_key(row, inherited_role) for row in historical}
    malformed = sorted(key for key in current_keys | historical_keys if not key[0] or not key[1] or not key[2])
    current_only = sorted(current_keys - historical_keys)
    historical_only = sorted(historical_keys - current_keys)
    if malformed:
        status = "INVALID_ROWS"
    elif current_only or historical_only:
        status = "DRIFT_REQUIRES_REVIEW"
    else:
        status = "MATCHED_WITHIN_SCOPE"
    return {
        "status": status,
        "current_count": len(current_keys),
        "historical_count": len(historical_keys),
        "current_only": [list(item) for item in current_only[:100]],
        "historical_only": [list(item) for item in historical_only[:100]],
        "difference_truncated": len(current_only) > 100 or len(historical_only) > 100,
        "malformed_rows": [list(item) for item in malformed[:20]],
    }


def _normalize_grant(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "grantee": _upper(_value(row, "grantee", "grantee_name")),
        "grantee_type": _principal_type(_value(row, "grantee_type", "granted_to", "grant_to")),
        "privilege": _upper(_value(row, "privilege")),
        "object": _text(_value(row, "object", "object_name", "name")),
        "object_type": _upper(_value(row, "object_type", "granted_on", "grant_on")),
        "grantor": _upper(_value(row, "grantor", "granted_by")),
        "grant_option": _upper(_value(row, "grant_option")),
    }


def _normalize_future(row: dict[str, Any], scope: str) -> dict[str, Any]:
    normalized = _normalize_grant(row)
    normalized["scope"] = scope
    normalized["scope_type"] = "SCHEMA" if "." in scope else "DATABASE"
    return normalized


def _role_list(value: Any, field: str) -> list[str]:
    if isinstance(value, str):
        values = [] if not value.strip() else [item.strip() for item in value.split(",")]
    elif isinstance(value, list) and all(isinstance(item, str) for item in value):
        values = [item.strip() for item in value]
    else:
        raise AccessEvidenceError(f"secondary_roles.{field} has an unsupported shape")
    if any(not IDENTIFIER_RE.fullmatch(item) for item in values if item):
        raise AccessEvidenceError(f"secondary_roles.{field} contains an unsupported identifier")
    return sorted({_upper(item) for item in values if item})


def _secondary_context(row: dict[str, Any]) -> tuple[str, list[str], list[str]]:
    raw = _value(row, "secondary_roles")
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise AccessEvidenceError("secondary_roles is not valid JSON") from exc
    if not isinstance(raw, dict) or set(raw) != {"roles", "value"}:
        raise AccessEvidenceError("secondary_roles must use Snowflake's roles/value object")
    activated = _role_list(raw["roles"], "roles")
    requested_raw = raw["value"]
    if isinstance(requested_raw, str) and requested_raw.strip().upper() in {"ALL", "NONE"}:
        mode = requested_raw.strip().upper()
        requested = []
    else:
        requested = _role_list(requested_raw, "value")
        mode = "EXPLICIT" if requested else "NONE"
    return mode, activated, requested


def _context_signature(row: dict[str, Any]) -> tuple[str, ...]:
    mode, activated, requested = _secondary_context(row)
    account = _upper(_value(row, "account_locator", "account_name"))
    principal = _upper(_value(row, "current_user_name"))
    primary_role = _upper(_value(row, "primary_role"))
    primary_role_type = _upper(_value(row, "primary_role_type"))
    session_id = _text(_value(row, "session_id"))
    if not account or not principal or not primary_role or not primary_role_type:
        raise AccessEvidenceError("execution context is missing account, principal, or primary-role identity")
    if "session_id" in row and not session_id:
        raise AccessEvidenceError("execution context session_id is empty")
    return (
        account,
        principal,
        primary_role,
        primary_role_type,
        mode,
        ",".join(activated),
        ",".join(requested),
    )


def _scope_values(coverage: dict[str, Any], key: str) -> list[str]:
    values = coverage.get(key)
    if not isinstance(values, list) or any(not isinstance(value, str) for value in values):
        raise AccessEvidenceError(f"metadata.coverage.{key} must be an array of identifiers")
    pattern = QUALIFIED_IDENTIFIER_RE if key in {"database_roles", "future_schemas"} else IDENTIFIER_RE
    if any(not pattern.fullmatch(value) for value in values):
        raise AccessEvidenceError(f"metadata.coverage.{key} contains an unsupported unquoted identifier")
    normalized = [_upper(value) for value in values]
    if len(normalized) != len(set(normalized)):
        raise AccessEvidenceError(f"metadata.coverage.{key} contains duplicates")
    return sorted(normalized)


def analyze_bundle(data: dict[str, Any], *, trusted_input_sha256: str | None = None) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise AccessEvidenceError("input must be a JSON object")
    if data.get("schema_version") != "2.0":
        raise AccessEvidenceError("schema_version must be 2.0")
    try:
        ANALYZER.reject_secrets(data)
    except ValueError as exc:
        raise AccessEvidenceError(str(exc)) from exc
    metadata = data.get("metadata")
    if not isinstance(metadata, dict):
        raise AccessEvidenceError("metadata must be an object")
    evaluation_time = parse_time(metadata.get("evaluated_at"), "metadata.evaluated_at")
    if evaluation_time > datetime.now(timezone.utc):
        raise AccessEvidenceError("metadata.evaluated_at must not be in the future")
    max_age_seconds = metadata.get("max_age_seconds")
    if not isinstance(max_age_seconds, int) or isinstance(max_age_seconds, bool) or max_age_seconds <= 0:
        raise AccessEvidenceError("metadata.max_age_seconds must be a positive integer")
    connection_profile = metadata.get("connection_profile")
    if not isinstance(connection_profile, str) or not connection_profile.strip():
        raise AccessEvidenceError("metadata.connection_profile must be a non-empty string")
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

    request = data.get("request")
    if not isinstance(request, dict):
        raise AccessEvidenceError("request must be an object")
    principal = _text(request.get("principal"))
    object_name = _text(request.get("object"))
    privilege = _text(request.get("privilege"))
    if not IDENTIFIER_RE.fullmatch(principal):
        raise AccessEvidenceError("request.principal must be one supported unquoted user identifier")
    if not OBJECT_IDENTIFIER_RE.fullmatch(object_name):
        raise AccessEvidenceError("request.object must be one supported three-part unquoted object identifier")
    if not IDENTIFIER_RE.fullmatch(privilege):
        raise AccessEvidenceError("request.privilege must be one supported privilege identifier")

    coverage = metadata.get("coverage")
    if not isinstance(coverage, dict):
        raise AccessEvidenceError("metadata.coverage must be an object")
    expected_coverage = {
        key: _scope_values(coverage, key)
        for key in ("roles", "users", "database_roles", "future_databases", "future_schemas")
    }
    collections = data.get("collections")
    if not isinstance(collections, dict):
        raise AccessEvidenceError("collections must be an object")

    assessments: list[dict[str, Any]] = []
    receipt_datasets: dict[str, list[tuple[dict[str, Any], dict[str, Any]]]] = {}
    for key, surface in (("historical", "access"), ("session", "access-session")):
        wrapper = collections.get(key)
        assessment, datasets = validate_receipt(wrapper, surface, evaluation_time, max_age_seconds, input_trusted)
        assessment["collection"] = key
        assessments.append(assessment)
        safe_selector = wrapper.get("selector", {}) if isinstance(wrapper, dict) else {}
        receipt_datasets[key] = [(safe_selector if isinstance(safe_selector, dict) else {}, datasets)]

    coverage_issues: list[str] = []
    for database in expected_coverage["future_databases"]:
        if not any(schema.split(".", 1)[0] == database for schema in expected_coverage["future_schemas"]):
            coverage_issues.append(f"future database {database!r} has no declared schema receipt for precedence review")
    for key, surface in COLLECTION_KEYS.items():
        wrappers = collections.get(key, [])
        if not isinstance(wrappers, list):
            wrappers = []
            coverage_issues.append(f"collections.{key} must be an array")
        receipt_datasets[key] = []
        observed: list[str] = []
        selector_name = SURFACE_CONTRACTS[surface][2]
        assert selector_name is not None
        for index, wrapper in enumerate(wrappers):
            assessment, datasets = validate_receipt(wrapper, surface, evaluation_time, max_age_seconds, input_trusted)
            assessment["collection"] = f"{key}[{index}]"
            assessments.append(assessment)
            selector = wrapper.get("selector", {}) if isinstance(wrapper, dict) else {}
            receipt_datasets[key].append((selector, datasets))
            if isinstance(selector, dict) and selector_name in selector and isinstance(selector[selector_name], str):
                observed.append(_upper(selector[selector_name]))
        expected = expected_coverage[COVERAGE_KEYS[key]]
        if key == "role_parents":
            expected = [value for value in expected if value != "PUBLIC"]
        if sorted(observed) != expected:
            coverage_issues.append(
                f"collections.{key} selectors {sorted(observed)!r} do not match declared coverage {expected!r}"
            )
    if any(item.get("connection_profile") != connection_profile for item in assessments):
        coverage_issues.append("every receipt must use metadata.connection_profile")

    historical = receipt_datasets["historical"][0][1]
    historical_grants = historical.get("grants_to_roles", [])
    historical_user_grants = historical.get("grants_to_users", [])
    historical_roles = historical.get("roles", [])

    imported_database_role_edges: list[dict[str, Any]] = []
    for key, selector_name in (("role_current", "role"), ("database_role_current", "database_role")):
        for selector, datasets in receipt_datasets[key]:
            parent = _upper(selector.get(selector_name))
            for row in datasets.get("rows", []):
                if not _is_unqualified_database_role_edge(row):
                    continue
                imported_database_role_edges.append(
                    {
                        "source": f"{key}:{parent}",
                        "parent": parent,
                        "database_role": _upper(_value(row, "name", "object_name")),
                        "status": "UNRESOLVED_IMPORTED_SYSTEM_BOUNDARY",
                        "used_for_access_proof": False,
                        "reason": (
                            "Unqualified database-role links can be Snowflake-provided or imported and are "
                            "not reliably represented in Account Usage."
                        ),
                    }
                )
    imported_database_role_edges = sorted(
        {canonical_json(row): row for row in imported_database_role_edges}.values(),
        key=canonical_json,
    )

    reconciliation: dict[str, Any] = {}
    for key in ("role_current", "database_role_current"):
        for selector, datasets in receipt_datasets[key]:
            selector_value = next(iter(selector.values()), "")
            current_rows = [row for row in datasets.get("rows", []) if not _is_unqualified_database_role_edge(row)]
            historical_rows = [
                row
                for row in historical_grants
                if _upper(_value(row, "grantee_name", "grantee")) == _upper(selector_value)
                and not _is_unqualified_database_role_edge(row)
            ]
            reconciliation[f"{key}:{selector_value}"] = _reconcile(current_rows, historical_rows)
    for selector, datasets in receipt_datasets["user_current"]:
        selector_value = next(iter(selector.values()), "")
        current_rows = datasets.get("rows", [])
        historical_rows = [
            row
            for row in historical_user_grants
            if _upper(_value(row, "grantee_name", "user")) == _upper(selector_value)
        ]
        current_assignments = [row for row in current_rows if _upper(_value(row, "role"))]
        historical_assignments = [row for row in historical_rows if _upper(_value(row, "role"))]
        current_direct = [row for row in current_rows if _upper(_value(row, "privilege"))]
        historical_direct = [
            row
            for row in historical_grants
            if _upper(_value(row, "grantee_name", "user")) == _upper(selector_value)
            and _upper(_value(row, "granted_to", "grantee_type")) == "USER"
            and _upper(_value(row, "privilege"))
        ]
        reconciliation[f"user_current:{selector_value}:roles"] = _reconcile_assignments(
            current_assignments, historical_assignments
        )
        reconciliation[f"user_current:{selector_value}:direct"] = _reconcile(current_direct, historical_direct)
    for selector, datasets in receipt_datasets["role_parents"]:
        selector_value = next(iter(selector.values()), "")
        current_rows = datasets.get("rows", [])
        historical_rows = [
            row
            for row in historical_grants
            if _upper(_value(row, "name", "role")) == _upper(selector_value)
            and _upper(_value(row, "granted_on", "object_type")) == "ROLE"
        ]
        reconciliation[f"role_parents:{selector_value}"] = _reconcile_role_edges(
            current_rows, historical_rows, selector_value
        )

    current_grants: list[dict[str, Any]] = []
    for key in ("role_current", "database_role_current"):
        for _, datasets in receipt_datasets[key]:
            current_grants.extend(
                _normalize_grant(row)
                for row in datasets.get("rows", [])
                if _upper(_value(row, "granted_on", "grant_on", "object_type")) not in {"ROLE", "DATABASE_ROLE"}
            )
    for _, datasets in receipt_datasets["user_current"]:
        current_grants.extend(
            _normalize_grant(row)
            for row in datasets.get("rows", [])
            if _upper(_value(row, "granted_on", "grant_on", "object_type")) not in {"", "ROLE", "DATABASE_ROLE"}
        )
    inherited_by_parent: dict[str, set[str]] = {}
    for key, selector_name in (("role_current", "role"), ("database_role_current", "database_role")):
        for selector, datasets in receipt_datasets[key]:
            parent = _upper(selector.get(selector_name))
            for row in datasets.get("rows", []):
                if _is_unqualified_database_role_edge(row):
                    continue
                if _upper(_value(row, "granted_on", "grant_on", "object_type")) not in {
                    "ROLE",
                    "DATABASE_ROLE",
                }:
                    continue
                child = _upper(_value(row, "name", "object_name"))
                if parent and child:
                    inherited_by_parent.setdefault(parent, set()).add(child)
    for selector, datasets in receipt_datasets["role_parents"]:
        inherited_role = _upper(selector.get("role"))
        for row in datasets.get("rows", []):
            if _upper(_value(row, "granted_to", "grant_to", "grantee_type")) != "ROLE":
                continue
            parent = _upper(_value(row, "grantee_name", "grantee"))
            if parent and inherited_role:
                inherited_by_parent.setdefault(parent, set()).add(inherited_role)
    role_grants = [
        {"name": parent, "inherits": sorted(children)} for parent, children in sorted(inherited_by_parent.items())
    ]

    users: dict[str, dict[str, Any]] = {}
    for selector, datasets in receipt_datasets["user_current"]:
        name = _upper(selector.get("user"))
        roles = sorted({_upper(_value(row, "role")) for row in datasets.get("rows", []) if _upper(_value(row, "role"))})
        users[name] = {"name": name, "roles": roles}
    session_rows = receipt_datasets["session"][0][1].get("session_context", [])
    baseline_context: tuple[str, ...] | None = None
    secondary_roles: list[str] = []
    if len(session_rows) == 1:
        session = session_rows[0]
        name = _upper(_value(session, "current_user_name"))
        session_account = _upper(_value(session, "account_locator", "account_name"))
        if session_account != _upper(metadata.get("account")):
            coverage_issues.append("session account does not match metadata.account")
        if _upper(_value(session, "primary_role")) != _upper(metadata.get("collector_role")):
            coverage_issues.append("session primary role does not match metadata.collector_role")
        try:
            baseline_context = _context_signature(session)
            mode, secondary_roles, _ = _secondary_context(session)
        except AccessEvidenceError as exc:
            coverage_issues.append(str(exc))
            mode = "UNVERIFIED"
        session_assessment = next(item for item in assessments if item["collection"] == "session")
        try:
            observed = parse_time(_value(session, "observed_at"), "session_context.observed_at")
            started = parse_time(session_assessment.get("collection_started_at"), "session.collection_started_at")
            completed = parse_time(session_assessment.get("collection_completed_at"), "session.collection_completed_at")
            if not (started <= observed <= completed):
                coverage_issues.append("session_context.observed_at is outside its live collection interval")
            if (evaluation_time - observed).total_seconds() > max_age_seconds:
                coverage_issues.append("session_context.observed_at exceeds metadata.max_age_seconds")
        except AccessEvidenceError as exc:
            coverage_issues.append(str(exc))
        if name:
            row = users.setdefault(name, {"name": name, "roles": []})
            row["primary_role"] = _upper(_value(session, "primary_role"))
            row["secondary_roles_mode"] = mode
            row["secondary_roles"] = secondary_roles
            row["roles"] = sorted(
                role for role in set(row.get("roles", [])) | set(secondary_roles) | {row["primary_role"]} if role
            )
    else:
        coverage_issues.append("session receipt must contain exactly one session_context row")

    assessment_by_collection = {item["collection"]: item for item in assessments}
    for key in COLLECTION_KEYS:
        for index, (_, datasets) in enumerate(receipt_datasets[key]):
            collection_name = f"{key}[{index}]"
            context_rows = datasets.get("execution_context", [])
            if len(context_rows) != 1:
                if assessment_by_collection[collection_name]["complete"]:
                    coverage_issues.append(f"{collection_name} has no same-statement execution context")
                continue
            context = context_rows[0]
            try:
                signature = _context_signature(context)
                observed = parse_time(_value(context, "observed_at"), f"{collection_name}.observed_at")
                started = parse_time(
                    assessment_by_collection[collection_name].get("collection_started_at"),
                    f"{collection_name}.collection_started_at",
                )
                completed = parse_time(
                    assessment_by_collection[collection_name].get("collection_completed_at"),
                    f"{collection_name}.collection_completed_at",
                )
                if not (started <= observed <= completed):
                    coverage_issues.append(f"{collection_name} observed_at is outside its live collection interval")
                if (evaluation_time - observed).total_seconds() > max_age_seconds:
                    coverage_issues.append(f"{collection_name} observed_at exceeds metadata.max_age_seconds")
                if baseline_context is None or signature != baseline_context:
                    coverage_issues.append(f"{collection_name} authorization context does not match session")
            except AccessEvidenceError as exc:
                coverage_issues.append(f"{collection_name}: {exc}")

    request_database, request_schema, _ = (_upper(part) for part in object_name.split("."))
    required_users = {_upper(principal)}
    required_roles = {
        "PUBLIC",
        _upper(_value(session_rows[0], "primary_role")) if len(session_rows) == 1 else "",
        *secondary_roles,
    }
    required_roles.discard("")
    required_database_roles: set[str] = set()
    for _, datasets in receipt_datasets["user_current"]:
        for row in datasets.get("rows", []):
            role_name = _upper(row.get("role"))
            if role_name:
                (required_database_roles if "." in role_name else required_roles).add(role_name)
    for selector, datasets in receipt_datasets["role_current"]:
        required_roles.add(_upper(selector.get("role")))
        for row in datasets.get("rows", []):
            granted_on = _upper(row.get("granted_on"))
            child = _upper(row.get("name"))
            if granted_on == "ROLE" and child:
                required_roles.add(child)
            elif granted_on == "DATABASE_ROLE" and child:
                if not _is_unqualified_database_role_edge(row):
                    required_database_roles.add(child)
    for selector, datasets in receipt_datasets["role_parents"]:
        required_roles.add(_upper(selector.get("role")))
        for row in datasets.get("rows", []):
            parent = _upper(row.get("grantee_name"))
            if _upper(row.get("granted_to")) == "ROLE" and parent:
                required_roles.add(parent)
    for selector, datasets in receipt_datasets["database_role_current"]:
        required_database_roles.add(_upper(selector.get("database_role")))
        for row in datasets.get("rows", []):
            child = _upper(row.get("name"))
            if _upper(row.get("granted_on")) == "DATABASE_ROLE" and child:
                if not _is_unqualified_database_role_edge(row):
                    required_database_roles.add(child)

    derived_requirements = {
        "users": sorted(required_users),
        "roles": sorted(required_roles),
        "database_roles": sorted(required_database_roles),
        "future_databases": [request_database],
        "future_schemas": [f"{request_database}.{request_schema}"],
    }
    for key, required in derived_requirements.items():
        missing = sorted(set(required) - set(expected_coverage[key]))
        if missing:
            coverage_issues.append(f"metadata.coverage.{key} omits request-derived selectors {missing!r}")

    future_grants: list[dict[str, Any]] = []
    for key in ("future_database", "future_schema"):
        for selector, datasets in receipt_datasets[key]:
            scope = next(iter(selector.values()), "")
            future_grants.extend(_normalize_future(row, scope) for row in datasets.get("rows", []))

    roles: list[dict[str, Any]] = []
    for row in historical_roles:
        role_name = _upper(_value(row, "name", "role_name"))
        role_type = _upper(_value(row, "role_type"))
        role_database = _upper(_value(row, "role_database_name"))
        if role_type == "DATABASE_ROLE" and role_database and "." not in role_name:
            role_name = f"{role_database}.{role_name}"
        if role_name:
            roles.append(
                {
                    "name": role_name,
                    "role_type": role_type,
                    "role_database_name": role_database,
                }
            )
    known_role_names = {row["name"] for row in roles}
    for role_name in expected_coverage["roles"]:
        if _upper(role_name) not in known_role_names:
            roles.append({"name": _upper(role_name), "role_type": "ACCOUNT_ROLE"})

    graph_input = {
        "metadata": {
            "account": metadata.get("account"),
            "role": metadata.get("collector_role"),
            "collected_at": metadata.get("evaluated_at"),
            "window_start": metadata.get("window_start"),
            "window_end": metadata.get("window_end"),
            "freshness": {
                "status": "FRESH" if all(item["complete"] for item in assessments) else "UNVERIFIED",
                "checked_at": metadata.get("evaluated_at"),
                "max_age_seconds": max_age_seconds,
            },
        },
        "roles": roles,
        "role_grants": role_grants,
        "users": sorted(users.values(), key=lambda row: row["name"]),
        "grants": current_grants,
        "future_grants": future_grants,
        "managed_access_schemas": data.get("managed_access_schemas", []),
        "verification": data.get("verification", {}),
    }
    if principal and len(session_rows) == 1:
        session_principal = _upper(_value(session_rows[0], "current_user_name"))
        if session_principal != _upper(principal):
            coverage_issues.append("request principal does not match the receipted current session")
    graph = ANALYZER.analyze(graph_input, principal, object_name, privilege)
    if isinstance(graph.get("evidence_scope"), dict) and isinstance(graph["evidence_scope"].get("freshness"), dict):
        graph["evidence_scope"]["freshness"]["status"] = "RECEIPTS_RECENT_ACCOUNT_USAGE_LAG_POSSIBLE"

    drift_issues = [name for name, result in reconciliation.items() if result["status"] != "MATCHED_WITHIN_SCOPE"]
    external = metadata.get("external_boundaries", {})
    if not isinstance(external, dict):
        external = {}
    missing_external = [
        name
        for name in ("object_policies", "shares", "inherited_grants_capability")
        if external.get(name) != "REVIEWED"
    ]
    all_receipts_complete = all(item["complete"] for item in assessments)
    scoped_complete = all_receipts_complete and not coverage_issues and not drift_issues
    if not scoped_complete:
        graph = {
            "status": "UNVERIFIED_EVIDENCE",
            "effective_access": {
                "status": "UNVERIFIED_EVIDENCE",
                "paths": [],
                "reason": "No authorization path is reported unless the digest, every receipt, request-derived scope, context binding, and reconciliation all pass.",
            },
            "findings": [],
            "verification": {"status": "NOT_EVALUATED"},
        }
    non_claims = [
        "A receipt self-checksum is not provenance; completeness requires a separately recorded matching bundle digest.",
        "A matching digest is an operator assertion of byte identity, not proof of origin or authenticity.",
        "Current SHOW results are scoped to equivalent authorization contexts across independent sessions and do not prove account-wide absence.",
        "Account Usage can lag by up to 120 minutes and omits documented shared/imported role cases.",
        "No GRANT, REVOKE, ownership transfer, USE ROLE, or USE SECONDARY ROLES statement was executed.",
        "Database roles cannot be activated directly; their privileges require a current account-role linkage.",
        "Identifiers are necessary security metadata and remain sensitive even though credential and free-form text fields are excluded.",
    ]
    return {
        "schema_version": "2.0",
        "input_sha256": actual_digest,
        "evidence_trust": {
            "status": trust_status,
            "trusted": input_trusted,
            "non_claim": non_claims[0],
        },
        "receipt_assessments": assessments,
        "scope_coverage": {
            "status": "COMPLETE" if not coverage_issues else "INCOMPLETE",
            "declared": expected_coverage,
            "request_derived_required": derived_requirements,
            "issues": sorted(coverage_issues),
        },
        "authorization_context": {
            "status": "AUTHORIZATION_CONTEXT_MATCHED" if scoped_complete else "UNVERIFIED",
            "fingerprint": input_sha256({"context": list(baseline_context)})
            if baseline_context is not None and scoped_complete
            else None,
            "physical_session_claim": "NOT_CLAIMED_INDEPENDENT_INVOCATIONS",
        },
        "historical_current_reconciliation": reconciliation,
        "drift_requiring_review": sorted(drift_issues),
        "unresolved_imported_database_role_edges": imported_database_role_edges,
        "missing_external_boundaries": missing_external,
        "freshness_assessment": {
            "receipt_recency": "WITHIN_DECLARED_BOUND"
            if all(item["complete"] for item in assessments)
            else "UNVERIFIED",
            "account_usage_source": "DELAYED_UP_TO_120_MINUTES_AND_DOCUMENTED_OMISSIONS_APPLY",
            "claim": "Receipt recency is not source-state freshness.",
        },
        "grant_graph_scope_complete": scoped_complete,
        "object_privilege_path_supported": scoped_complete
        and graph.get("effective_access", {}).get("status") == "OBJECT_PRIVILEGE_PATH_PROVEN",
        "positive_access_claim_supported": scoped_complete
        and graph.get("effective_access", {}).get("status") == "OBJECT_PRIVILEGE_PATH_PROVEN"
        and graph.get("verification", {}).get("positive_proof", {}).get("status") == "PROVEN",
        "absence_claim_blocked": True,
        # Policy/share/inherited-grant declarations are operator reminders, not
        # receipted evidence in this bounded collector. Never promote them into
        # a machine-certified complete authorization graph.
        "completeness_claim_blocked": True,
        "normalized_graph_input_sha256": input_sha256(graph_input),
        "analysis": graph,
        "non_claims": non_claims,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="Normalized receipted access-evidence bundle")
    parser.add_argument("--out", type=Path, help="Write JSON report; stdout when omitted")
    parser.add_argument(
        "--trusted-input-sha256",
        help="Out-of-band sha256:<hex> recorded when the bundle crossed a trusted local boundary",
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
            raise AccessEvidenceError("input must be a JSON object")
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
    except (AccessEvidenceError, OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
