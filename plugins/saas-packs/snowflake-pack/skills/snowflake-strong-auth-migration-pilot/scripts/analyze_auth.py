#!/usr/bin/env python3
"""Deterministic Snowflake authentication inventory and migration planner.

Input is sanitized metadata only.  The script does not contact Snowflake, mint
or inspect tokens, rotate keys, disable users, or alter integrations.  It emits
a bounded dry-run packet and verification checklist for an authorized operator.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


SENSITIVE_KEY_NAMES = {
    "apikey",
    "authorization",
    "credential",
    "credentials",
    "password",
    "passphrase",
    "passwordvalue",
    "privatekey",
    "jwt",
    "oauthcode",
    "oauthtoken",
    "secret",
    "secretvalue",
    "token",
    "tokenvalue",
    "sessiontoken",
}
METHODS = {"WIF", "PAT", "OAUTH", "KEY_PAIR", "PASSWORD", "SAML", "BASIC"}
TARGET_PRIORITY = ("WIF", "KEY_PAIR", "OAUTH", "PAT")
HIGH_RISK_CURRENT = {"PASSWORD", "BASIC"}
SENSITIVE_VALUE_PATTERNS = (
    re.compile(
        r"(?i)\b(?:password|passwd|pwd|passphrase|secret|token|api[_ -]?key|authorization|credential|private[_ -]?key)\b\s*[:=]\s*\S+"
    ),
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{8,}"),
    re.compile(r"-----BEGIN(?: [A-Z0-9]+)? PRIVATE KEY-----"),
)


def norm(value: object) -> str:
    return str(value or "").strip()


def upper(value: object) -> str:
    return norm(value).upper().replace("-", "_").replace(" ", "_")


def sensitive_key(key: object) -> bool:
    """Recognize credential-bearing keys across snake/camel/kebab casing."""
    normalized = re.sub(r"[^a-z0-9]", "", str(key).casefold())
    fragments = (
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
    return normalized in SENSITIVE_KEY_NAMES or any(fragment in normalized for fragment in fragments)


def reject_credentials(value: object, path: str = "input") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if sensitive_key(key):
                raise ValueError(f"credential-bearing field is not accepted: {path}.{key}")
            reject_credentials(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            reject_credentials(child, f"{path}[{index}]")
    elif isinstance(value, str) and any(pattern.search(value) for pattern in SENSITIVE_VALUE_PATTERNS):
        raise ValueError(f"credential-shaped value is not accepted: {path}")


def rows(doc: dict, field: str) -> list[dict]:
    value = doc.get(field, [])
    if not isinstance(value, list):
        raise ValueError(f"{field} must be an array")
    for index, row in enumerate(value):
        if not isinstance(row, dict):
            raise ValueError(f"{field}[{index}] must be an object")
    return value


def string_list(value: object, path: str, *, allow_scalar: bool = False) -> list[str]:
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


def list_upper(value: object, path: str, *, allow_scalar: bool = False) -> list[str]:
    return sorted({upper(item) for item in string_list(value, path, allow_scalar=allow_scalar) if norm(item)})


def timestamp(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def finding(fid: str, severity: str, category: str, subject: str, detail: str, **extra: object) -> dict:
    result: dict[str, object] = {
        "id": fid,
        "severity": severity,
        "category": category,
        "subject": subject,
        "detail": detail,
    }
    result.update({key: val for key, val in extra.items() if val not in (None, "", [], {})})
    return result


def choose_target(options: list[str]) -> str:
    for candidate in TARGET_PRIORITY:
        if candidate in options:
            return candidate
    return "MANUAL_REVIEW"


def analyze(doc: dict) -> dict:
    if not isinstance(doc, dict):
        raise ValueError("input must be a JSON object")
    reject_credentials(doc)
    users = [row for row in rows(doc, "users") if norm(row.get("name"))]
    workloads = [row for row in rows(doc, "workloads") if norm(row.get("name"))]
    integrations = [row for row in rows(doc, "integrations") if norm(row.get("name"))]
    metadata = doc.get("metadata", {})
    if not isinstance(metadata, dict):
        raise ValueError("metadata must be an object")
    break_glass = doc.get("break_glass", doc.get("break_glass_identity", {}))
    if not isinstance(break_glass, dict):
        raise ValueError("break_glass must be an object")
    canary = doc.get("canary", doc.get("canary_receipt", {}))
    if not isinstance(canary, dict):
        raise ValueError("canary must be an object")
    user_map = {upper(row["name"]): row for row in users}
    findings: list[dict] = []
    plans: list[dict] = []

    freshness = metadata.get("freshness", {})
    freshness_missing: list[str] = []
    now = datetime.now(timezone.utc)
    parsed_metadata: dict[str, datetime | None] = {}
    for field in ("collected_at", "window_start", "window_end"):
        parsed_metadata[field] = timestamp(metadata.get(field))
        if parsed_metadata[field] is None:
            freshness_missing.append(f"metadata.{field}(valid timezone timestamp)")
    collected_at = parsed_metadata["collected_at"]
    window_start = parsed_metadata["window_start"]
    window_end = parsed_metadata["window_end"]
    if collected_at is not None and collected_at > now:
        freshness_missing.append("metadata.collected_at(not in future)")
    if window_start is not None and window_end is not None and window_start > window_end:
        freshness_missing.append("metadata.observation_window(ordered)")
    if window_end is not None and collected_at is not None and window_end > collected_at:
        freshness_missing.append("metadata.window_end(no later than collection)")
    if not isinstance(freshness, dict):
        freshness_missing.append("metadata.freshness(object)")
    else:
        if str(freshness.get("status", "")).upper() != "FRESH":
            freshness_missing.append("metadata.freshness.status(FRESH)")
        checked_at = timestamp(freshness.get("checked_at"))
        if checked_at is None:
            freshness_missing.append("metadata.freshness.checked_at(valid timezone timestamp)")
        elif collected_at is not None and checked_at > collected_at:
            freshness_missing.append("metadata.freshness.checked_at(no later than collection)")
        if type(freshness.get("max_age_seconds")) is not int or freshness.get("max_age_seconds") <= 0:
            freshness_missing.append("metadata.freshness.max_age_seconds(positive integer)")
        elif (
            checked_at is not None
            and collected_at is not None
            and (collected_at - checked_at).total_seconds() > freshness["max_age_seconds"]
        ):
            freshness_missing.append("metadata.freshness.checked_at(within max_age_seconds)")
    if freshness_missing:
        findings.append(
            finding(
                "inventory-freshness-missing",
                "high",
                "inventory-freshness",
                "identity-estate",
                "Missing or invalid: "
                + ", ".join(freshness_missing)
                + ". Recollect the read-only identity/workload inventory with a bounded observation window.",
            )
        )

    if (
        break_glass.get("verified") is not True
        or not norm(break_glass.get("identity"))
        or not norm(break_glass.get("owner"))
        or timestamp(break_glass.get("tested_at")) is None
        or (
            window_start is not None
            and timestamp(break_glass.get("tested_at")) is not None
            and timestamp(break_glass.get("tested_at")) < window_start
        )
        or (
            collected_at is not None
            and timestamp(break_glass.get("tested_at")) is not None
            and timestamp(break_glass.get("tested_at")) > collected_at
        )
        or not norm(break_glass.get("auth_method"))
    ):
        findings.append(
            finding(
                "break-glass-unverified",
                "critical",
                "break-glass-unverified",
                "recovery-identity",
                "A separately owned, tested recovery identity is not proven. Do not retire a password/basic path or start a cutover without break-glass recovery evidence.",
            )
        )
    canary_positive = (
        canary.get("positive") is True
        if "positive" in canary
        else str(canary.get("positive_status", "")).upper() in {"PASS", "PASSED"}
    )
    canary_negative = (
        canary.get("negative") is True
        if "negative" in canary
        else str(canary.get("negative_status", "")).upper() in {"PASS", "PASSED", "DENIED"}
    )
    if (
        canary.get("verified") is not True
        or not norm(canary.get("workload"))
        or not norm(canary.get("target_auth"))
        or timestamp(canary.get("tested_at")) is None
        or (
            window_start is not None
            and timestamp(canary.get("tested_at")) is not None
            and timestamp(canary.get("tested_at")) < window_start
        )
        or (
            collected_at is not None
            and timestamp(canary.get("tested_at")) is not None
            and timestamp(canary.get("tested_at")) > collected_at
        )
        or not canary_positive
        or not canary_negative
    ):
        findings.append(
            finding(
                "canary-unverified",
                "high",
                "canary-unverified",
                norm(canary.get("workload")) or "pilot",
                "A target-auth canary lacks verified positive and negative outcomes. Keep the current path and stage the target only after the canary and rollback identity are proven.",
            )
        )

    for index, user in enumerate(users):
        name = upper(user["name"])
        user_type = upper(user.get("type") or user.get("user_type") or "UNKNOWN")
        method_field = "auth_methods" if "auth_methods" in user else "authentication_methods"
        methods = list_upper(user.get(method_field), f"users[{index}].{method_field}")
        unknown = sorted(set(methods) - METHODS)
        if unknown:
            findings.append(
                finding(
                    f"unknown-method-{index}",
                    "medium",
                    "unknown-auth-method",
                    name,
                    "Authentication method is not in the planner vocabulary; verify the live Snowflake user/integration inventory.",
                    methods=unknown,
                )
            )
        if user_type not in {"PERSON", "SERVICE", "LEGACY_SERVICE"}:
            findings.append(
                finding(
                    f"unknown-user-type-{index}",
                    "medium",
                    "unknown-user-type",
                    name,
                    "Classify this principal as PERSON, SERVICE, or LEGACY_SERVICE before choosing a migration target.",
                )
            )
        if user_type == "PERSON":
            if "PASSWORD" in methods and not ({"SAML", "OAUTH"} & set(methods)):
                findings.append(
                    finding(
                        f"person-password-{index}",
                        "high",
                        "person-password-review",
                        name,
                        "Interactive principal has password authentication without an observed SSO/OAuth path; verify IdP coverage before changing anything.",
                    )
                )
        elif user_type in {"SERVICE", "LEGACY_SERVICE"}:
            if "PASSWORD" in methods or "BASIC" in methods:
                findings.append(
                    finding(
                        f"service-password-{index}",
                        "high",
                        "service-password",
                        name,
                        "Non-human identity uses password/basic authentication; map its workload to WIF, key pair, or approved OAuth before retirement.",
                    )
                )
        bound = [
            row for row in workloads if upper(row.get("identity") or row.get("user") or row.get("service_user")) == name
        ]
        if user_type in {"SERVICE", "LEGACY_SERVICE"} and not bound:
            findings.append(
                finding(
                    f"unbound-service-{index}",
                    "medium",
                    "unbound-service",
                    name,
                    "Service identity has no workload binding in the supplied inventory; do not disable or migrate it until an owner and workload are identified.",
                )
            )
        for workload in bound:
            wname = upper(workload["name"])
            option_field = next(
                (
                    field
                    for field in ("supported_auth", "target_auth_options", "allowed_auth_methods")
                    if field in workload
                ),
                "supported_auth",
            )
            options = list_upper(
                workload.get("supported_auth")
                or workload.get("target_auth_options")
                or workload.get("allowed_auth_methods"),
                f"workloads.{wname}.{option_field}",
            )
            current = upper(workload.get("current_auth") or (methods[0] if methods else "UNKNOWN"))
            selected = choose_target(options)
            if selected == "MANUAL_REVIEW":
                findings.append(
                    finding(
                        f"no-target-{wname}",
                        "high",
                        "no-supported-target",
                        wname,
                        "No supported WIF/key-pair/OAuth/PAT target is declared; obtain driver/runtime capability evidence instead of guessing.",
                    )
                )
            if current in HIGH_RISK_CURRENT:
                findings.append(
                    finding(
                        f"legacy-workload-auth-{wname}",
                        "high",
                        "legacy-workload-auth",
                        wname,
                        "Workload currently authenticates with a password/basic method; stage a parallel non-password path and prove rollback before cutover.",
                    )
                )
            if selected == "PAT":
                findings.append(
                    finding(
                        f"pat-boundary-{wname}",
                        "medium",
                        "pat-boundary",
                        wname,
                        "PAT is selected only as an explicitly approved bounded fallback; record owner, audience, TTL/revocation process, and why WIF/key-pair/OAuth is unavailable.",
                    )
                )
            if selected == "WIF":
                detail = "Workload identity federation is the preferred target when the cloud runtime, Snowflake integration, and driver support it; verify issuer, audience, subject mapping, and role scope live."
            elif selected == "KEY_PAIR":
                detail = "Key-pair authentication is the selected non-password target; verify public-key registration, storage/rotation ownership, and a second key/recovery path without exposing private material."
            elif selected == "OAUTH":
                detail = "OAuth is the selected target; verify integration, audience/scopes, token acquisition path, and role mapping without handling token values in this packet."
            elif selected == "PAT":
                detail = "PAT is the selected bounded fallback; it must not be treated as a universal service-account replacement."
            else:
                detail = "No target selected."
            plans.append(
                {
                    "subject": name,
                    "workload": wname,
                    "user_type": user_type,
                    "current_auth": current,
                    "target_auth": selected,
                    "target_rationale": detail,
                    "owner": norm(workload.get("owner")) or norm(user.get("owner")),
                    "canary": {
                        "verified": canary.get("verified") is True and upper(canary.get("workload")) == wname,
                        "tested_at": canary.get("tested_at"),
                    },
                    "roles": list_upper(
                        workload.get("roles") if "roles" in workload else workload.get("role"),
                        f"workloads.{wname}.roles",
                        allow_scalar="roles" not in workload,
                    ),
                    "dry_run": [
                        "Verify workload owner, runtime, driver, integration, role scope, and rollback identity.",
                        f"Stage {selected} alongside the current path in a non-production or canary context; do not disable the current path yet.",
                        "Prepare (but do not execute) the user/integration change and an explicit reversal packet.",
                    ],
                }
            )

    for index, workload in enumerate(workloads):
        name = upper(workload["name"])
        identity = upper(workload.get("identity") or workload.get("user") or workload.get("service_user"))
        if identity not in user_map:
            findings.append(
                finding(
                    f"workload-unknown-identity-{index}",
                    "high",
                    "unknown-workload-identity",
                    name,
                    "Workload points at a principal absent from the user inventory; stop before cutover.",
                )
            )
        option_field = next(
            (field for field in ("supported_auth", "target_auth_options", "allowed_auth_methods") if field in workload),
            "supported_auth",
        )
        if not list_upper(
            workload.get("supported_auth")
            or workload.get("target_auth_options")
            or workload.get("allowed_auth_methods"),
            f"workloads.{name}.{option_field}",
        ):
            findings.append(
                finding(
                    f"workload-capability-gap-{index}",
                    "medium",
                    "capability-evidence-gap",
                    name,
                    "Runtime/driver capability list is missing; do not assume WIF support.",
                )
            )

    oauth_controls_by_integration: dict[str, dict[str, object]] = {}
    for index, integration in enumerate(integrations):
        name = upper(integration["name"])
        itype = upper(integration.get("type"))
        managed_mcp = "MCP" in itype
        if managed_mcp:
            control_type = upper(integration.get("source_control_type"))
            scopes = [
                norm(item)
                for item in string_list(
                    integration.get("oauth_scopes_supported"),
                    f"integrations.{name}.oauth_scopes_supported",
                )
                if norm(item)
            ]
            named_scope_roles = sorted(
                {
                    upper(item.split(":", 2)[2])
                    for item in scopes
                    if item.lower().startswith("session:role:")
                    and item.lower() not in {"session:role:all", "session:role-any"}
                }
            )
            allowed_roles = list_upper(integration.get("allowed_roles"), f"integrations.{name}.allowed_roles")
            blocked_roles = list_upper(integration.get("blocked_roles"), f"integrations.{name}.blocked_roles")
            scope_location = upper(integration.get("scope_location"))
            scope_object = norm(integration.get("scope_object"))
            secondary = upper(integration.get("oauth_use_secondary_roles") or "UNKNOWN")
            client_behavior = upper(integration.get("client_scope_behavior") or "UNKNOWN")
            oauth_controls_by_integration[name] = {
                "control_type": control_type,
                "named_scope_roles": named_scope_roles,
                "allowed_roles": allowed_roles,
                "blocked_roles": blocked_roles,
                "secondary": secondary,
                "client_behavior": client_behavior,
                "scope_location": scope_location,
                "scope_object": scope_object,
            }
            missing = []
            if control_type not in {"SNOWFLAKE_OAUTH", "EXTERNAL_OAUTH"}:
                missing.append("source_control_type")
            if not scopes:
                missing.append("oauth_scopes_supported")
            if not allowed_roles:
                missing.append("allowed_roles")
            if "blocked_roles" not in integration:
                missing.append("blocked_roles(explicit array, empty is allowed)")
            if scope_location not in {"ACCOUNT", "DATABASE", "SCHEMA"}:
                missing.append("scope_location(ACCOUNT|DATABASE|SCHEMA)")
            if scope_location in {"DATABASE", "SCHEMA"} and not scope_object:
                missing.append("scope_object")
            if secondary not in {"NONE", "IMPLICIT"}:
                missing.append("oauth_use_secondary_roles")
            if client_behavior not in {"NAMED_ROLE", "SESSION_ROLE_ALL", "SESSION_ROLE_ANY"}:
                missing.append("client_scope_behavior")
            if missing:
                findings.append(
                    finding(
                        f"mcp-controls-missing-{index}",
                        "high",
                        "managed-mcp-controls-missing",
                        name,
                        "Managed MCP authorization evidence is incomplete; do not infer a safe session role from an arbitrary role list.",
                        missing=missing,
                    )
                )
            powerful = {"ACCOUNTADMIN", "SECURITYADMIN", "ORGADMIN", "GLOBALORGADMIN"}
            advertised = set(named_scope_roles) | set(allowed_roles)
            if "*" in advertised or powerful & advertised:
                findings.append(
                    finding(
                        f"mcp-scope-broad-{index}",
                        "critical",
                        "managed-mcp-scope-broad",
                        name,
                        "Managed MCP OAuth controls advertise or allow a wildcard or powerful account role; narrow the primary-role controls and re-verify.",
                    )
                )
            if secondary == "IMPLICIT":
                findings.append(
                    finding(
                        f"mcp-secondary-implicit-{index}",
                        "critical",
                        "managed-mcp-secondary-roles",
                        name,
                        "OAUTH_USE_SECONDARY_ROLES is IMPLICIT. Secondary roles are separate from advertised primary-role scopes and can expand the session; use NONE for the bounded MCP pilot.",
                    )
                )
        if "OAUTH" in itype and not integration.get("enabled", True):
            findings.append(
                finding(
                    f"oauth-disabled-{index}",
                    "info",
                    "oauth-disabled",
                    name,
                    "OAuth integration is disabled in the supplied inventory; target plans using it cannot be considered ready.",
                )
            )

    for index, workload in enumerate(workloads):
        integration = upper(workload.get("integration") or workload.get("oauth_integration"))
        if integration and integration in oauth_controls_by_integration:
            workload_roles = set(
                list_upper(
                    workload.get("roles") if "roles" in workload else workload.get("role"),
                    f"workloads.{upper(workload['name'])}.roles",
                    allow_scalar="roles" not in workload,
                )
            )
            controls = oauth_controls_by_integration[integration]
            allowed = set(controls["allowed_roles"])
            blocked = set(controls["blocked_roles"])
            client_behavior = str(controls["client_behavior"])
            identity = user_map.get(upper(workload.get("identity")), {})
            default_role = upper(identity.get("default_role"))
            default_warehouse = norm(identity.get("default_warehouse"))
            if client_behavior == "SESSION_ROLE_ALL":
                effective_roles = {default_role} if default_role else set()
                if not default_role or not default_warehouse:
                    findings.append(
                        finding(
                            f"mcp-default-context-{index}",
                            "high",
                            "managed-mcp-default-context-missing",
                            upper(workload["name"]),
                            "This client requests session:role:all, so the user DEFAULT_ROLE is primary and DEFAULT_WAREHOUSE is required; one or both are absent.",
                        )
                    )
            else:
                effective_roles = set(controls["named_scope_roles"])
            permitted = {role for role in effective_roles if (not allowed or role in allowed) and role not in blocked}
            if workload_roles and not workload_roles <= permitted:
                findings.append(
                    finding(
                        f"mcp-role-mismatch-{index}",
                        "high",
                        "managed-mcp-role-mismatch",
                        upper(workload["name"]),
                        "Required workload roles are not proven as usable after client scope behavior, default-role selection, allowlist, blocklist, and secondary-role controls are applied; reconcile without broadening automatically.",
                        required_roles=sorted(workload_roles),
                        permitted_primary_roles=sorted(permitted),
                        client_scope_behavior=client_behavior,
                    )
                )

    findings.sort(
        key=lambda row: ({"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}[row["severity"]], row["id"])
    )
    payload = json.dumps(doc, sort_keys=True, separators=(",", ":")).encode()
    return {
        "schema_version": "1.0",
        "input_sha256": hashlib.sha256(payload).hexdigest(),
        "summary": {
            "persons": sum(upper(row.get("type") or row.get("user_type")) == "PERSON" for row in users),
            "services": sum(upper(row.get("type") or row.get("user_type")) == "SERVICE" for row in users),
            "legacy_services": sum(upper(row.get("type") or row.get("user_type")) == "LEGACY_SERVICE" for row in users),
            "workloads": len(workloads),
            "integrations": len(integrations),
            "findings": len(findings),
            "high_or_critical": sum(row["severity"] in {"high", "critical"} for row in findings),
        },
        "boundaries": {
            "read_only": True,
            "edit_authority": False,
            "snowflake_mutation_authority": False,
            "credential_handling": "No password, token, private-key, or secret values are accepted or emitted.",
            "dates": "No universal retirement date is assumed; use the account's approved change window and live feature support.",
            "managed_mcp_oauth": "Primary-role scopes, client behavior, DEFAULT_ROLE, allowed/blocked roles, and OAUTH_USE_SECONDARY_ROLES are separate evidence; the analyzer does not broaden or enable them.",
        },
        "inventory_receipt": {
            "read_only": True,
            "source": metadata.get("source") or "operator-supplied sanitized inventory",
            "account": metadata.get("account"),
            "role": metadata.get("role"),
            "collected_at": metadata.get("collected_at"),
            "observation_window": {"start": metadata.get("window_start"), "end": metadata.get("window_end")},
            "freshness": freshness,
            "counts": {"users": len(users), "workloads": len(workloads), "integrations": len(integrations)},
            "non_claims": [
                "No identity, integration, policy, password, key, token, or role was changed by this analyzer."
            ],
        },
        "recovery_receipt": {
            "break_glass": break_glass,
            "canary": canary,
        },
        "plans": plans,
        "managed_mcp_controls": [
            {
                "integration": name,
                **controls,
                "default_contexts": sorted(
                    {
                        (
                            upper(user_map.get(upper(workload.get("identity")), {}).get("default_role")),
                            norm(user_map.get(upper(workload.get("identity")), {}).get("default_warehouse")),
                        )
                        for workload in workloads
                        if upper(workload.get("integration") or workload.get("oauth_integration")) == name
                    }
                ),
            }
            for name, controls in sorted(oauth_controls_by_integration.items())
        ],
        "findings": findings,
        "cutover_packet": {
            "preconditions": [
                "Named workload owner, security approver, executor, recovery identity, runtime/driver compatibility, and Snowflake integration evidence.",
                "Current role and authentication inventory captured without credential values.",
                "For managed MCP/OAuth, source control type, advertised scopes, client behavior, DEFAULT_ROLE/warehouse, allowed/blocked roles, and secondary-role setting are approved.",
            ],
            "positive_verification": [
                "Canary workload authenticates through the selected target and reaches only its approved role/object path.",
                "Person can complete the approved interactive path where applicable.",
                "Managed MCP/OAuth request is accepted with an in-scope role and produces an auditable session.",
            ],
            "negative_verification": [
                "Old password/basic path is rejected only after the replacement and recovery path are proven.",
                "Out-of-scope role/object request is denied, including a managed MCP/OAuth scope outside the approved role.",
                "Unknown or unbound service identity is not disabled as a side effect of the pilot.",
            ],
            "rollback": "Keep the current authentication path and a separately verified recovery identity until positive and negative receipts are accepted; this report does not alter users or integrations.",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan a Snowflake non-password authentication pilot")
    parser.add_argument("--input", required=True, help="sanitized JSON identity/workload inventory")
    parser.add_argument("--out", help="write JSON report here; otherwise stdout")
    args = parser.parse_args()
    try:
        doc = json.loads(Path(args.input).read_text(encoding="utf-8"))
        if not isinstance(doc, dict):
            raise ValueError("input must be a JSON object")
        report = analyze(doc)
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
