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
import sys
from collections import defaultdict, deque
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
        for grant in grants:
            if _upper(grant.get("grantee")) == "PUBLIC":
                key = f"{_norm(grant.get('object') or grant.get('object_name'))}|{_upper(grant.get('privilege'))}"
                effective_paths[key].append({"path": f"{user} -> PUBLIC", "via_secondary_role": False})
        for grant in grants:
            if _upper(grant.get("grantee")) == user and mode == "ALL":
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
        "findings": findings,
        "effective_access": requested,
        "verification": {
            "positive": [
                "Run SHOW GRANTS and a representative allowed query under the workload's primary/secondary-role context."
            ],
            "negative": [
                "Run a representative prohibited query and confirm it remains denied; test PUBLIC/direct paths separately."
            ],
            "change_packet": "No GRANT, REVOKE, GRANT OWNERSHIP, or ALTER statement is executed by this analyzer.",
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
