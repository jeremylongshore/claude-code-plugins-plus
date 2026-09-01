#!/usr/bin/env python3
"""Deterministic, read-only Snowflake authorization graph analyzer.

The input is a sanitized JSON export.  This program never connects to
Snowflake and never emits SQL that changes state.  It turns role edges, users,
object grants, and future grants into a reviewable report so an operator can
decide what to change under an approved change process.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path


SENSITIVE_KEY_NAMES = {
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
    "sessiontoken",
    "token",
}
SENSITIVE_KEY_FRAGMENTS = (
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
SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
SENSITIVE_VALUE_PATTERNS = (
    re.compile(
        r"(?i)\b(?:password|passwd|pwd|passphrase|secret|token|api[_ -]?key|authorization|credential|private[_ -]?key)\b\s*[:=]\s*\S+"
    ),
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{8,}"),
    re.compile(r"-----BEGIN(?: [A-Z0-9]+)? PRIVATE KEY-----"),
)


def _norm(value: object) -> str:
    return str(value or "").strip()


def _upper(value: object) -> str:
    return _norm(value).upper()


def reject_secrets(value: object, path: str = "input") -> None:
    """Fail closed if a caller tries to provide credential material."""
    if isinstance(value, dict):
        for key, child in value.items():
            key_l = "".join(char for char in str(key).casefold() if char.isalnum())
            if key_l in SENSITIVE_KEY_NAMES or any(fragment in key_l for fragment in SENSITIVE_KEY_FRAGMENTS):
                raise ValueError(f"credential-bearing field is not accepted: {path}.{key}")
            reject_secrets(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            reject_secrets(child, f"{path}[{index}]")
    elif isinstance(value, str) and any(pattern.search(value) for pattern in SENSITIVE_VALUE_PATTERNS):
        raise ValueError(f"credential-shaped value is not accepted: {path}")


def _rows(doc: dict, field: str) -> list[dict]:
    value = doc.get(field, [])
    if not isinstance(value, list):
        raise ValueError(f"{field} must be an array")
    for index, row in enumerate(value):
        if not isinstance(row, dict):
            raise ValueError(f"{field}[{index}] must be an object")
    return value


def _strings(value: object, path: str, *, allow_scalar: bool = False) -> list[str]:
    if value is None:
        return []
    if allow_scalar and isinstance(value, str):
        values = [value]
    elif isinstance(value, list):
        values = value
    else:
        raise ValueError(f"{path} must be an array of strings")
    if any(not isinstance(item, str) for item in values):
        raise ValueError(f"{path} must be an array of strings")
    return values


def _timestamp(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def _verification_receipts(value: object, path: str) -> list[dict]:
    if not isinstance(value, list):
        raise ValueError(f"{path} must be an array")
    for index, row in enumerate(value):
        if not isinstance(row, dict):
            raise ValueError(f"{path}[{index}] must be an object")
    return value


def _optional_rows(doc: dict, names: tuple[str, ...], path: str) -> tuple[list[dict] | None, str | None]:
    """Return an explicitly supplied snapshot without treating omission as empty."""
    for name in names:
        if name in doc:
            return _rows(doc, name), name
    return None, None


def _access_row_key(row: dict, *, future: bool = False, role: bool = False) -> tuple[str, ...]:
    if role:
        return (_upper(row.get("name") or row.get("role_name")), _upper(row.get("role_type")))
    if future:
        return (
            _upper(row.get("grantee")),
            _upper(row.get("privilege")),
            _upper(row.get("scope_type")),
            _upper(row.get("scope") or row.get("container")),
            _upper(row.get("object_type")),
        )
    return (
        _upper(row.get("grantee")),
        _upper(row.get("grantee_type")),
        _upper(row.get("privilege")),
        _upper(row.get("object") or row.get("object_name")),
        _upper(row.get("object_type")),
    )


def _reconcile_access_rows(
    current: list[dict] | None, historical: list[dict] | None, *, future: bool = False, role: bool = False
) -> dict:
    current_keys = {_access_row_key(row, future=future, role=role) for row in current or []}
    historical_keys = {_access_row_key(row, future=future, role=role) for row in historical or []}
    current_only = sorted(current_keys - historical_keys)
    historical_only = sorted(historical_keys - current_keys)
    if current is None or historical is None:
        status = "NOT_SUPPLIED"
    elif not current_only and not historical_only:
        status = "MATCHED"
    else:
        status = "MISMATCH"
    return {
        "status": status,
        "current_count": len(current_keys) if current is not None else None,
        "historical_count": len(historical_keys) if historical is not None else None,
        "current_only": [list(item) for item in current_only[:100]],
        "historical_only": [list(item) for item in historical_only[:100]],
        "difference_truncated": len(current_only) > 100 or len(historical_only) > 100,
    }


def _receipt_assessment(value: object, label: str) -> dict:
    if value is None:
        return {"status": "NOT_SUPPLIED", "complete": False, "issues": [f"{label} receipt not supplied"]}
    if not isinstance(value, dict):
        return {"status": "UNVERIFIABLE", "complete": False, "issues": [f"{label} receipt is not an object"]}
    issues = []
    expected_surface = {"current access": "access-current", "future access": "access-future"}.get(label)
    if value.get("schema_version") != "1":
        issues.append("schema_version is not 1")
    if expected_surface and value.get("surface") != expected_surface:
        issues.append(f"surface is not {expected_surface}")
    if value.get("status") != "collected":
        issues.append("status is not collected")
    if value.get("errors"):
        issues.append("collector reported an error")
    if value.get("truncation_possible") is not False:
        issues.append("truncation_possible is not false")
    if not isinstance(value.get("source_views"), list) or not value.get("source_views"):
        issues.append("source_views are missing")
    selector = (
        value.get("source_metadata", {}).get("selector") if isinstance(value.get("source_metadata"), dict) else None
    )
    expected_selector = {"database": True} if label == "future access" else {}
    if selector != expected_selector:
        issues.append("source_metadata.selector is not the expected privacy-safe binding")
    if label == "future access":
        if not isinstance(value.get("selector_fingerprint"), str) or not re.fullmatch(
            r"sha256:[0-9a-f]{64}", value["selector_fingerprint"]
        ):
            issues.append("selector_fingerprint is missing or malformed")
    elif value.get("selector_fingerprint") is not None:
        issues.append("unexpected selector_fingerprint on unscoped receipt")
    for field in ("sql_sha256", "template_sha256", "rendered_sql_sha256"):
        if not isinstance(value.get(field), str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", value[field]):
            issues.append(f"{field} is missing or malformed")
    body = dict(value)
    supplied_hash = body.pop("receipt_sha256", None)
    canonical_body = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    expected_hash = f"sha256:{hashlib.sha256(canonical_body).hexdigest()}"
    if supplied_hash != expected_hash:
        issues.append("receipt_sha256 is missing or invalid")
    collected = _timestamp(value.get("collected_at"))
    if collected is None or collected > datetime.now(timezone.utc):
        issues.append("collected_at is invalid or in the future")
    return {"status": "VERIFIED" if not issues else "UNVERIFIABLE", "complete": not issues, "issues": issues}


def object_schema(object_name: str) -> str:
    parts = [part for part in _norm(object_name).split(".") if part]
    return ".".join(parts[:-1]) if len(parts) >= 2 else ""


def role_paths(role: str, parents: dict[str, list[str]]) -> dict[str, list[str]]:
    """Return role -> all inheritance paths from the starting role."""
    result: dict[str, list[str]] = {role: [role]}
    queue: deque[tuple[str, list[str]]] = deque([(role, [role])])
    while queue:
        current, path = queue.popleft()
        for parent in sorted(parents.get(current, [])):
            if parent in path:
                continue
            next_path = path + [parent]
            result.setdefault(parent, next_path)
            queue.append((parent, next_path))
    return result


def _finding(fid: str, severity: str, category: str, subject: str, detail: str, **extra: str) -> dict:
    item = {
        "id": fid,
        "severity": severity,
        "category": category,
        "subject": subject,
        "detail": detail,
    }
    item.update({key: value for key, value in extra.items() if value != ""})
    return item


def analyze(doc: dict, principal: str = "", object_name: str = "", privilege: str = "") -> dict:
    if not isinstance(doc, dict):
        raise ValueError("input must be a JSON object")
    reject_secrets(doc)
    role_rows = _rows(doc, "roles")
    role_grants = _rows(doc, "role_grants") if "role_grants" in doc else role_rows
    user_rows = _rows(doc, "users")
    grants = _rows(doc, "grants")
    future = _rows(doc, "future_grants")
    current_roles, _ = _optional_rows(doc, ("current_roles", "current_show_roles"), "current_roles")
    historical_roles, _ = _optional_rows(doc, ("historical_roles", "account_usage_roles"), "historical_roles")
    historical_roles = (
        role_rows
        if historical_roles is None and "historical_roles" not in doc and "account_usage_roles" not in doc
        else historical_roles
    )
    current_grants, current_grants_field = _optional_rows(
        doc, ("current_grants", "current_show_grants", "current_snapshot_grants"), "current_grants"
    )
    historical_grants, historical_grants_field = _optional_rows(
        doc, ("historical_grants", "account_usage_grants"), "historical_grants"
    )
    current_future, _ = _optional_rows(
        doc, ("current_future_grants", "current_show_future_grants"), "current_future_grants"
    )
    historical_future, _ = _optional_rows(
        doc, ("historical_future_grants", "account_usage_future_grants"), "historical_future_grants"
    )
    # The legacy `grants` and `future_grants` fields are the historical side of
    # the contract. Explicit aliases take precedence when provided.
    historical_grants = (
        grants
        if historical_grants is None and "historical_grants" not in doc and "account_usage_grants" not in doc
        else historical_grants
    )
    historical_future = (
        future
        if historical_future is None
        and "historical_future_grants" not in doc
        and "account_usage_future_grants" not in doc
        else historical_future
    )
    reconciliation = {
        "roles": _reconcile_access_rows(current_roles, historical_roles, role=True),
        "grants": _reconcile_access_rows(current_grants, historical_grants),
        "future_grants": _reconcile_access_rows(current_future, historical_future, future=True),
    }
    completeness_blocked = any(item["status"] != "MATCHED" for item in reconciliation.values())
    receipt = _receipt_assessment(doc.get("current_receipt", doc.get("access_current_receipt")), "current access")
    future_receipt = _receipt_assessment(doc.get("future_receipt", doc.get("access_future_receipt")), "future access")
    if not receipt["complete"] or (current_future is not None and not future_receipt["complete"]):
        completeness_blocked = True
    metadata = doc.get("metadata", {})
    if not isinstance(metadata, dict):
        raise ValueError("metadata must be an object")
    report_collected_at = _timestamp(metadata.get("collected_at"))
    for label, item, raw in (
        ("current", receipt, doc.get("current_receipt", doc.get("access_current_receipt"))),
        ("future", future_receipt, doc.get("future_receipt", doc.get("access_future_receipt"))),
    ):
        receipt_at = _timestamp(raw.get("collected_at")) if isinstance(raw, dict) else None
        if report_collected_at is not None and receipt_at is not None and receipt_at > report_collected_at:
            item["status"] = "UNVERIFIABLE"
            item["complete"] = False
            item["issues"].append("collected_at is later than report collection")
            completeness_blocked = True
    supplied_verification = doc.get("verification", {})
    if not isinstance(supplied_verification, dict):
        raise ValueError("verification must be an object")
    positive_receipts = _verification_receipts(supplied_verification.get("positive", []), "verification.positive")
    negative_receipts = _verification_receipts(supplied_verification.get("negative", []), "verification.negative")
    managed_access_schemas = _strings(doc.get("managed_access_schemas"), "managed_access_schemas")
    roles = {_upper(row.get("name")): row for row in role_rows if _norm(row.get("name"))}
    role_parents: dict[str, list[str]] = defaultdict(list)
    for index, row in enumerate(role_grants):
        child = _upper(row.get("role") or row.get("child") or row.get("name"))
        parent_field = "inherits" if "inherits" in row else "parents"
        parents = _strings(row.get(parent_field), f"role_grants[{index}].{parent_field}")
        for parent in parents:
            parent_n = _upper(parent)
            if child and parent_n:
                role_parents[child].append(parent_n)
                roles.setdefault(parent_n, {"name": parent_n})

    users: dict[str, dict] = {}
    user_roles: dict[str, list[str]] = defaultdict(list)
    for index, row in enumerate(user_rows):
        name = _upper(row.get("name"))
        if not name:
            continue
        users[name] = row
        declared = _strings(row.get("roles"), f"users[{index}].roles")
        primary = _upper(row.get("primary_role") or row.get("default_role"))
        for role in declared:
            role_n = _upper(role)
            if role_n and role_n not in user_roles[name]:
                user_roles[name].append(role_n)
        if primary and primary not in user_roles[name]:
            user_roles[name].insert(0, primary)

    known_grantees = set(roles) | set(users) | {"PUBLIC"}
    findings: list[dict] = []
    effective_paths: dict[str, list[dict]] = defaultdict(list)
    direct_user_paths: list[dict] = []
    ownership_paths: list[dict] = []

    for index, grant in enumerate(grants):
        grantee = _upper(grant.get("grantee"))
        obj = _norm(grant.get("object") or grant.get("object_name"))
        priv = _upper(grant.get("privilege"))
        grant_type = _upper(grant.get("grantee_type"))
        if not grantee or not obj:
            continue
        if not priv:
            findings.append(
                _finding(
                    f"incomplete-grant-{index}",
                    "high",
                    "incomplete-grant",
                    grantee,
                    "Grant evidence has no privilege and cannot support an effective-access decision.",
                    object=obj,
                )
            )
            continue
        if grantee not in known_grantees:
            findings.append(
                _finding(
                    f"orphan-grant-{index}",
                    "high",
                    "orphan-grantee",
                    grantee,
                    "Grant targets a principal absent from the supplied role/user inventory; verify whether the grant is stale before any cleanup.",
                    object=obj,
                    privilege=priv,
                )
            )
        if grantee == "PUBLIC":
            findings.append(
                _finding(
                    f"public-grant-{index}",
                    "high",
                    "public-grant",
                    grantee,
                    "PUBLIC receives an object privilege available to every Snowflake user. Confirm that account-wide authenticated access is intentional; do not replace it automatically.",
                    object=obj,
                    privilege=priv,
                )
            )
        elif grantee in users or grant_type == "USER":
            direct_user_paths.append(
                {
                    "grantee": grantee,
                    "object": obj,
                    "privilege": priv,
                    "path": f"{grantee} (direct grant)",
                    "observed": True,
                }
            )
            findings.append(
                _finding(
                    f"direct-user-grant-{index}",
                    "high",
                    "direct-user-grant",
                    grantee,
                    "Privilege is granted directly to a user instead of a reviewable access role.",
                    object=obj,
                    privilege=priv,
                )
            )
        if priv == "OWNERSHIP":
            ownership_paths.append(
                {
                    "grantee": grantee,
                    "object": obj,
                    "path": f"{grantee} -> OWNERSHIP",
                    "via": "direct grant edge",
                }
            )
            findings.append(
                _finding(
                    f"ownership-{index}",
                    "medium",
                    "ownership-control",
                    grantee,
                    "OWNERSHIP is a control-plane capability, not routine read/write access; capture dependencies and an approved transfer/reversal before changing it.",
                    object=obj,
                )
            )

        schema = object_schema(obj)
        managed = {_upper(item) for item in managed_access_schemas}
        if schema and schema.upper() in managed and not _norm(grant.get("grantor")):
            findings.append(
                _finding(
                    f"managed-access-grantor-{index}",
                    "medium",
                    "managed-access",
                    grantee,
                    "Grant is in a managed access schema but its grantor evidence is absent; verify MANAGE GRANTS authority and centralized ownership before execution.",
                    object=obj,
                    privilege=priv,
                )
            )

    by_scope: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for index, grant in enumerate(future):
        scope = _norm(grant.get("scope") or grant.get("container"))
        scope_type = _upper(grant.get("scope_type"))
        obj_type = _upper(grant.get("object_type"))
        grantee = _upper(grant.get("grantee"))
        priv = _upper(grant.get("privilege"))
        if not scope or not grantee:
            continue
        by_scope[(grantee, obj_type, priv)].append(
            {**grant, "_index": index, "_scope": scope, "_scope_type": scope_type}
        )
        if priv == "OWNERSHIP":
            findings.append(
                _finding(
                    f"future-ownership-{index}",
                    "high",
                    "future-ownership",
                    grantee,
                    "Future OWNERSHIP grant transfers control of newly created objects; require explicit design approval and creator/rollback testing.",
                    scope=scope,
                    object_type=obj_type,
                )
            )
    for key, entries in by_scope.items():
        db_scopes = [row for row in entries if row["_scope_type"] in {"DATABASE", "DATABASES"}]
        schema_scopes = [row for row in entries if row["_scope_type"] in {"SCHEMA", "SCHEMAS"}]
        if db_scopes and schema_scopes:
            findings.append(
                _finding(
                    f"future-conflict-{key[0]}-{key[1]}-{key[2]}",
                    "medium",
                    "future-grant-conflict",
                    key[0],
                    "Database- and schema-level future grants target the same grantee/object type/privilege. Schema-level precedence can make the effective policy differ from the database-level intent; reconcile explicitly.",
                    privilege=key[2],
                    object_type=key[1],
                )
            )

    future_precedence: list[dict] = []
    for key, entries in sorted(by_scope.items()):
        db_scopes = [row for row in entries if row["_scope_type"] in {"DATABASE", "DATABASES"}]
        schema_scopes = [row for row in entries if row["_scope_type"] in {"SCHEMA", "SCHEMAS"}]
        if db_scopes and schema_scopes:
            future_precedence.append(
                {
                    "grantee": key[0],
                    "object_type": key[1],
                    "privilege": key[2],
                    "database_scopes": sorted(row["_scope"] for row in db_scopes),
                    "schema_scopes": sorted(row["_scope"] for row in schema_scopes),
                    "effective_precedence": "SCHEMA",
                    "rule": "When database- and schema-level future grants overlap for the same grantee/object type, schema-level intent takes precedence; verify each schema explicitly.",
                }
            )

    for user, row in sorted(users.items()):
        primary = _upper(row.get("primary_role") or row.get("default_role"))
        mode = _upper(row.get("secondary_roles_mode") or row.get("secondary_role_mode"))
        declared_secondary = _strings(row.get("secondary_roles"), f"users.{user}.secondary_roles")
        all_roles = list(user_roles.get(user, []))
        active: list[str] = []
        if primary:
            active.append(primary)
        if mode == "ALL":
            active.extend(all_roles)
        elif mode in {"LIST", "EXPLICIT"}:
            active.extend(_upper(item) for item in declared_secondary)
        active = sorted(set(item for item in active if item))
        role_closure: set[str] = set()
        active_paths: list[tuple[str, str, list[str]]] = []
        for active_role in active:
            for inherited_role, path in role_paths(active_role, role_parents).items():
                role_closure.add(inherited_role)
                active_paths.append((active_role, inherited_role, path))
        user_roles[user] = sorted(set(user_roles[user]) | role_closure)
        if any(role != primary for role in active) and mode != "ALL":
            findings.append(
                _finding(
                    f"secondary-role-context-{user}",
                    "info",
                    "secondary-role-context",
                    user,
                    "Effective access depends on explicitly activated secondary roles; replay verification with the same USE SECONDARY ROLES context.",
                    primary_role=primary,
                )
            )
        for active_role, role, path in sorted(active_paths):
            chain = " -> ".join([user] + path)
            for grant in grants:
                if _upper(grant.get("grantee")) != role:
                    continue
                key = f"{_norm(grant.get('object') or grant.get('object_name'))}|{_upper(grant.get('privilege'))}"
                effective_paths[key].append(
                    {
                        "path": chain,
                        "active_role": active_role,
                        "via_secondary_role": active_role != primary,
                    }
                )
                if _upper(grant.get("privilege")) == "OWNERSHIP":
                    ownership_paths.append(
                        {
                            "grantee": role,
                            "object": _norm(grant.get("object") or grant.get("object_name")),
                            "path": chain,
                            "via": "role inheritance",
                        }
                    )
        for grant in grants:
            if _upper(grant.get("grantee")) == "PUBLIC":
                key = f"{_norm(grant.get('object') or grant.get('object_name'))}|{_upper(grant.get('privilege'))}"
                effective_paths[key].append({"path": f"{user} -> PUBLIC", "via_secondary_role": False})
                if _upper(grant.get("privilege")) == "OWNERSHIP":
                    ownership_paths.append(
                        {
                            "grantee": "PUBLIC",
                            "object": _norm(grant.get("object") or grant.get("object_name")),
                            "path": f"{user} -> PUBLIC",
                            "via": "PUBLIC grant",
                        }
                    )
        for grant in grants:
            # Direct user grants are effective independently of secondary-role
            # activation; secondary-role mode controls roles, not grants to USER.
            if _upper(grant.get("grantee")) == user:
                key = f"{_norm(grant.get('object') or grant.get('object_name'))}|{_upper(grant.get('privilege'))}"
                effective_paths[key].append({"path": f"{user} (direct grant)", "via_secondary_role": False})

    requested = None
    if principal or object_name or privilege:
        p = _upper(principal)
        o = _norm(object_name)
        v = _upper(privilege)
        complete_request = bool(p and o and v)
        paths = list(effective_paths.get(f"{o}|{v}", [])) if complete_request and p in users else []
        if complete_request and p in users:
            paths = [item for item in paths if item["path"].startswith(f"{p} ")]
        requested = {
            "principal": p,
            "object": o,
            "privilege": v,
            "status": "INCOMPLETE_REQUEST"
            if not complete_request
            else ("OBJECT_PRIVILEGE_PATH_PROVEN" if paths else "NOT_PROVEN"),
            "paths": sorted(paths, key=lambda item: item["path"]),
            "note": "OBJECT_PRIVILEGE_PATH_PROVEN proves only the supplied object-grant path, not complete access; database/schema USAGE, policies, shares, and live authorization remain separate. INCOMPLETE_REQUEST requires principal, object, and privilege. NOT_PROVEN is not proof of denial.",
        }

    # Timestamp/freshness is explicit evidence, not inferred from the current
    # clock or from a row's CREATED_ON value.  This keeps Account Usage lag and
    # SHOW GRANTS current-state checks visible to the operator.
    freshness = metadata.get("freshness", {})
    freshness_missing: list[str] = []
    collected_at = _timestamp(metadata.get("collected_at"))
    window_start = _timestamp(metadata.get("window_start"))
    window_end = _timestamp(metadata.get("window_end"))
    if collected_at is None:
        freshness_missing.append("metadata.collected_at(valid timezone timestamp)")
    elif collected_at > datetime.now(timezone.utc):
        freshness_missing.append("metadata.collected_at(not in future)")
    if window_start is None:
        freshness_missing.append("metadata.window_start(valid timezone timestamp)")
    if window_end is None:
        freshness_missing.append("metadata.window_end(valid timezone timestamp)")
    if window_start is not None and window_end is not None and window_start > window_end:
        freshness_missing.append("metadata.observation_window(ordered)")
    if window_end is not None and collected_at is not None and window_end > collected_at:
        freshness_missing.append("metadata.window_end(no later than collection)")
    if not isinstance(freshness, dict):
        freshness_missing.append("metadata.freshness(object)")
    else:
        if str(freshness.get("status", "")).upper() != "FRESH":
            freshness_missing.append("metadata.freshness.status(FRESH)")
        freshness_checked = _timestamp(freshness.get("checked_at"))
        if freshness_checked is None:
            freshness_missing.append("metadata.freshness.checked_at(valid timezone timestamp)")
        elif collected_at is not None and freshness_checked > collected_at:
            freshness_missing.append("metadata.freshness.checked_at(no later than collection)")
        if type(freshness.get("max_age_seconds")) is not int or freshness.get("max_age_seconds") <= 0:
            freshness_missing.append("metadata.freshness.max_age_seconds(positive integer)")
        elif (
            freshness_checked is not None
            and collected_at is not None
            and (collected_at - freshness_checked).total_seconds() > freshness["max_age_seconds"]
        ):
            freshness_missing.append("metadata.freshness.checked_at(within max_age_seconds)")
    if freshness_missing:
        findings.append(
            _finding(
                "evidence-freshness-missing",
                "high",
                "evidence-freshness",
                "inventory",
                "Missing or invalid: "
                + ", ".join(freshness_missing)
                + ". Recollect current SHOW GRANTS/FUTURE GRANTS evidence with UTC timestamps, an explicit freshness bound, and the observation window; Account Usage lag is not proof of denial.",
            )
        )

    requested_user = users.get(_upper(principal), {})
    expected_primary = _upper(requested_user.get("primary_role") or requested_user.get("default_role"))
    expected_mode = _upper(requested_user.get("secondary_roles_mode") or "NONE")
    if expected_mode == "ALL":
        expected_secondary = sorted(role for role in user_roles.get(_upper(principal), []) if role != expected_primary)
    elif expected_mode == "EXPLICIT":
        expected_secondary = sorted(
            _upper(role)
            for role in _strings(requested_user.get("secondary_roles"), "users[].secondary_roles")
            if _upper(role)
        )
    else:
        expected_secondary = []
    expected_context = {
        "account": _upper(metadata.get("account")),
        "principal": _upper(principal),
        "object": _upper(object_name),
        "privilege": _upper(privilege),
        "primary_role": expected_primary,
        "secondary_roles_mode": expected_mode,
        "secondary_roles": expected_secondary,
    }
    request_is_bound = bool(
        expected_context["account"]
        and expected_context["principal"]
        and expected_context["object"]
        and expected_context["privilege"]
        and requested_user
    )
    proof_start = window_start
    proof_end = collected_at

    def proof_status(receipts: list[dict], expected: str, path: str) -> str:
        if not request_is_bound:
            return "NOT_PROVEN"
        valid = []
        for index, receipt in enumerate(receipts):
            observed_at = _timestamp(receipt.get("observed_at"))
            if (
                observed_at is None
                or proof_start is None
                or proof_end is None
                or not (proof_start <= observed_at <= proof_end)
            ):
                findings.append(
                    _finding(
                        f"{path}-timestamp-{index}",
                        "high",
                        "access-proof-timestamp",
                        path,
                        f"{path}[{index}] has no valid observed_at timestamp. Repeat the access proof and record a UTC timestamp tied to the same account, principal, object, and role context.",
                    )
                )
                continue
            actual_context = {
                "account": _upper(receipt.get("account")),
                "principal": _upper(receipt.get("principal")),
                "object": _upper(receipt.get("object")),
                "privilege": _upper(receipt.get("privilege")),
                "primary_role": _upper(receipt.get("primary_role")),
                "secondary_roles_mode": _upper(receipt.get("secondary_roles_mode")),
                "secondary_roles": sorted(
                    _upper(role)
                    for role in _strings(receipt.get("secondary_roles"), f"{path}[{index}].secondary_roles")
                    if _upper(role)
                ),
            }
            if actual_context != expected_context:
                findings.append(
                    _finding(
                        f"{path}-context-{index}",
                        "high",
                        "access-proof-context",
                        path,
                        f"{path}[{index}] is not bound to the requested account, principal, object, privilege, and primary/secondary-role context. Repeat the proof under the exact requested context.",
                    )
                )
                continue
            if str(receipt.get("status", "")).upper() == expected:
                valid.append(receipt)
        return "PROVEN" if valid else "NOT_PROVEN"

    positive_status = proof_status(positive_receipts, "PASS", "positive-proof")
    negative_status = proof_status(negative_receipts, "DENIED", "negative-proof")
    if positive_status != "PROVEN":
        findings.append(
            _finding(
                "positive-access-proof-missing",
                "high",
                "access-proof-missing",
                "positive",
                "No timestamped positive allowed-action receipt. Run a representative allowed operation under the requested primary/secondary-role context and attach a sanitized PASS receipt.",
            )
        )
    if negative_status != "PROVEN":
        findings.append(
            _finding(
                "negative-access-proof-missing",
                "high",
                "access-proof-missing",
                "negative",
                "No timestamped negative denied-action receipt. Run a representative prohibited operation and attach a sanitized DENIED receipt; do not infer denial from absent grants.",
            )
        )

    for label, item in reconciliation.items():
        if item["status"] == "NOT_SUPPLIED":
            findings.append(
                _finding(
                    f"{label}-reconciliation-missing",
                    "high",
                    "access-reconciliation-missing",
                    label,
                    "Current SHOW evidence and historical Account Usage evidence were not both supplied; completeness and absence claims are blocked.",
                )
            )
        elif item["status"] == "MISMATCH":
            findings.append(
                _finding(
                    f"{label}-reconciliation-mismatch",
                    "high",
                    "access-reconciliation-mismatch",
                    label,
                    "Current and historical access snapshots differ. Investigate timing, revocation, future-grant precedence, and role context before making an access decision.",
                )
            )
    for label, item in (("current", receipt), ("future", future_receipt)):
        if not item["complete"] and (label == "current" or current_future is not None):
            findings.append(
                _finding(
                    f"{label}-collector-receipt-unverifiable",
                    "high",
                    "collector-receipt-unverifiable",
                    label,
                    "The evidence collector receipt is missing, errored, stale, or potentially truncated; do not report a complete access graph.",
                )
            )

    findings.sort(key=lambda item: (SEVERITY_ORDER[item["severity"]], item["id"]))
    payload = json.dumps(doc, sort_keys=True, separators=(",", ":")).encode()
    return {
        "schema_version": "1.0",
        "input_sha256": hashlib.sha256(payload).hexdigest(),
        "summary": {
            "roles": len(roles),
            "users": len(users),
            "grants": len(grants),
            "future_grants": len(future),
            "findings": len(findings),
            "high_or_critical": sum(item["severity"] in {"high", "critical"} for item in findings),
        },
        "boundaries": {
            "read_only": True,
            "authorization_source": "sanitized inventory only; Account Usage is historical and live SHOW/INFORMATION_SCHEMA checks remain required",
            "secondary_roles": "primary role is always included; secondary roles are included only when mode is ALL or EXPLICIT/LIST",
            "managed_access_schemas": sorted({_norm(item) for item in managed_access_schemas}),
        },
        "evidence_scope": {
            "account": metadata.get("account"),
            "role": metadata.get("role"),
            "collected_at": metadata.get("collected_at"),
            "observation_window": {"start": metadata.get("window_start"), "end": metadata.get("window_end")},
            "freshness": freshness,
        },
        "findings": findings,
        "direct_user_paths": sorted(
            direct_user_paths, key=lambda item: (item["grantee"], item["object"], item["privilege"])
        ),
        "ownership_paths": sorted(ownership_paths, key=lambda item: (item["object"], item["path"])),
        "future_grant_precedence": future_precedence,
        "effective_access": requested,
        "access_evidence_reconciliation": {
            **reconciliation,
            "current_grants_field": current_grants_field,
            "historical_grants_field": historical_grants_field,
            "current_receipt": receipt,
            "future_receipt": future_receipt,
        },
        "completeness_claim_blocked": completeness_blocked,
        "verification": {
            "positive": [
                "Run SHOW GRANTS and a representative allowed query under the workload's primary/secondary-role context."
            ],
            "negative": [
                "Run a representative prohibited query and confirm it remains denied; test PUBLIC/direct paths separately."
            ],
            "change_packet": "No GRANT, REVOKE, GRANT OWNERSHIP, or ALTER statement is executed by this analyzer.",
            "positive_proof": {"status": positive_status, "receipts": positive_receipts},
            "negative_proof": {"status": negative_status, "receipts": negative_receipts},
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze a sanitized Snowflake authorization graph")
    parser.add_argument("--input", required=True, help="sanitized JSON inventory")
    parser.add_argument("--out", help="write JSON report here; otherwise stdout")
    parser.add_argument("--principal")
    parser.add_argument("--object")
    parser.add_argument("--privilege")
    args = parser.parse_args()
    try:
        doc = json.loads(Path(args.input).read_text(encoding="utf-8"))
        if not isinstance(doc, dict):
            raise ValueError("input must be a JSON object")
        report = analyze(doc, args.principal or "", args.object or "", args.privilege or "")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    output = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        Path(args.out).write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
