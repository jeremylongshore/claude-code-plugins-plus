#!/usr/bin/env python3
"""Audit a metadata-only Grammarly OAuth plan without network or credential access."""

from __future__ import annotations

import json
import re
import sys
from typing import Any


OPERATIONS = {
    "writing-score": frozenset(("scores-api:read", "scores-api:write")),
    "ai-detection": frozenset(("ai-detection-api:read", "ai-detection-api:write")),
    "plagiarism": frozenset(("plagiarism-api:read", "plagiarism-api:write")),
    "analytics-read": frozenset(("analytics-api:read",)),
    "license-read": frozenset(("users-api:read",)),
}
OFFICIAL_OAUTH_CATALOG_SCOPES = frozenset(
    ("scores-api:read", "scores-api:write", "analytics-api:read", "users-api:read", "users-api:write")
)
KNOWN_ENDPOINT_SCOPES = frozenset().union(*OPERATIONS.values())
BETA_OPERATIONS = frozenset(("ai-detection", "plagiarism"))
ROOT_KEYS = frozenset(
    (
        "schema_version",
        "access_tier",
        "oauth_client_configured",
        "configuration_source",
        "operations",
        "granted_scopes",
        "beta_scope_exception_approved",
    )
)
ACCESS_TIERS = frozenset(("enterprise", "education-institution-wide", "unknown"))
CONFIGURATION_SOURCES = frozenset(("environment-injected", "secret-manager-reference", "unknown"))
SECRET_KEY_RE = re.compile(
    r"(?:secret|token|password|passwd|credential|api[_-]?key|access[_-]?key|private[_-]?key|authorization|bearer)",
    re.IGNORECASE,
)
SECRET_VALUE_RES = (
    re.compile(r"-----BEGIN [^-]*PRIVATE KEY-----"),
    re.compile(r"\bBearer\s+\S+", re.IGNORECASE),
    re.compile(r"(?:access[_-]?token|client[_-]?secret|refresh[_-]?token)\s*[:=]", re.IGNORECASE),
    re.compile(r"\b(?:sk|ghp|github_pat|xox[baprs])-[-A-Za-z0-9_]{12,}\b"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
)


class AuditError(ValueError):
    """Unsafe or invalid audit input."""


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise AuditError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def parse_json(raw: str) -> Any:
    def reject_constant(value: str) -> None:
        raise AuditError(f"non-standard JSON constant: {value}")

    try:
        return json.loads(raw, object_pairs_hook=_pairs, parse_constant=reject_constant)
    except (json.JSONDecodeError, UnicodeError, AuditError) as exc:
        raise AuditError(f"invalid strict JSON: {exc}") from None


def scan_secrets(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if not isinstance(key, str):
                raise AuditError(f"{path}: object keys must be strings")
            if SECRET_KEY_RE.search(key):
                raise AuditError(f"{path}.{key}: secret-bearing key is forbidden")
            scan_secrets(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            scan_secrets(child, f"{path}[{index}]")
    elif isinstance(value, str) and any(pattern.search(value) for pattern in SECRET_VALUE_RES):
        raise AuditError(f"{path}: secret-bearing value is forbidden")


def _string_array(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or not value or any(not isinstance(item, str) or not item for item in value):
        raise AuditError(f"{label}: expected a non-empty string array")
    if len(set(value)) != len(value):
        raise AuditError(f"{label}: duplicate values are forbidden")
    return value


def audit(document: Any) -> dict[str, Any]:
    scan_secrets(document)
    if not isinstance(document, dict) or set(document) != ROOT_KEYS:
        raise AuditError("root fields must exactly match the documented schema")
    if document["schema_version"] != "1":
        raise AuditError("schema_version: only string version 1 is supported")
    access_tier = document["access_tier"]
    if access_tier not in ACCESS_TIERS:
        raise AuditError("access_tier: unsupported value")
    if not isinstance(document["oauth_client_configured"], bool):
        raise AuditError("oauth_client_configured: expected boolean")
    source = document["configuration_source"]
    if source not in CONFIGURATION_SOURCES:
        raise AuditError("configuration_source: unsupported value")
    if not isinstance(document["beta_scope_exception_approved"], bool):
        raise AuditError("beta_scope_exception_approved: expected boolean")

    operations = _string_array(document["operations"], "operations")
    unknown_operations = sorted(set(operations) - set(OPERATIONS))
    if unknown_operations:
        raise AuditError(f"operations: unsupported values: {', '.join(unknown_operations)}")
    granted = set(_string_array(document["granted_scopes"], "granted_scopes"))
    unknown_scopes = sorted(granted - KNOWN_ENDPOINT_SCOPES)
    if unknown_scopes:
        raise AuditError(f"granted_scopes: undocumented values: {', '.join(unknown_scopes)}")

    required = set().union(*(OPERATIONS[operation] for operation in operations))
    missing_scopes = sorted(required - granted)
    extra_scopes = sorted(granted - required)
    beta_scopes = (
        set().union(*(OPERATIONS[operation] for operation in operations if operation in BETA_OPERATIONS))
        if any(operation in BETA_OPERATIONS for operation in operations)
        else set()
    )
    catalog_gap = sorted(beta_scopes - OFFICIAL_OAUTH_CATALOG_SCOPES)

    reasons: list[str] = []
    if access_tier == "unknown":
        reasons.append("recognized_enterprise_or_institution_wide_education_access_required")
    if not document["oauth_client_configured"]:
        reasons.append("oauth_client_not_configured")
    if source == "unknown":
        reasons.append("approved_configuration_source_required")
    if missing_scopes:
        reasons.append("missing_required_scopes")
    if extra_scopes:
        reasons.append("granted_scope_exceeds_least_privilege")
    if catalog_gap and not document["beta_scope_exception_approved"]:
        reasons.append("beta_scope_documentation_exception_requires_approval")

    return {
        "decision": "READY" if not reasons else "BLOCKED",
        "reasons": reasons,
        "account_access": access_tier,
        "operations": operations,
        "required_scopes": sorted(required),
        "missing_scopes": missing_scopes,
        "extra_scopes": extra_scopes,
        "documentation_flags": (["official_ai_plagiarism_oauth_catalog_inconsistency"] if catalog_gap else []),
        "beta_scope_exception_approved": document["beta_scope_exception_approved"],
        "offline": True,
        "writes_performed": False,
        "network_calls": 0,
    }


def main() -> int:
    try:
        result = audit(parse_json(sys.stdin.read()))
    except (AuditError, RecursionError) as exc:
        result = {
            "decision": "BLOCKED",
            "reasons": ["invalid_or_unsafe_input"],
            "error": str(exc),
            "offline": True,
            "writes_performed": False,
            "network_calls": 0,
        }
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 2
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if result["decision"] == "READY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
