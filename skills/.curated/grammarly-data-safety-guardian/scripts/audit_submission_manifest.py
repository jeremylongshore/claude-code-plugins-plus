#!/usr/bin/env python3
"""Gate a metadata-only Grammarly document transfer manifest offline."""

from __future__ import annotations

import json
import re
import sys
from typing import Any
from urllib.parse import urlsplit


API_ORIGIN = "https://api.grammarly.com"
UPLOAD_PROVIDER_SUFFIX = ("amazonaws", "com")
OPERATIONS = frozenset(("writing-score", "ai-detection", "plagiarism"))
SUPPORTED_EXTENSIONS = frozenset((".doc", ".docx", ".odt", ".txt", ".rtf"))
CLASSIFICATIONS = frozenset(("public", "internal", "confidential", "restricted"))
MAX_BYTES = 4_194_304
MAX_CHARACTERS = 100_000
MIN_WORDS = 30
REQUIRED_KEYS = frozenset(
    (
        "schema_version",
        "operation",
        "content_sha256",
        "extension",
        "byte_size",
        "classification",
        "data_owner_approved",
        "consent_confirmed",
        "transfer_approved",
        "provider_retention_acknowledged",
        "api_control_plane_origin",
        "presigned_upload_origin",
        "presigned_upload_origin_approved",
    )
)
OPTIONAL_KEYS = frozenset(("text_character_count", "word_count"))
SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
FORBIDDEN_KEY_PARTS = (
    "raw_text",
    "rawtext",
    "content_body",
    "contentbody",
    "preview",
    "filename",
    "path",
    "secret",
    "token",
    "password",
    "credential",
    "authorization",
    "header",
    "upload_url",
)
SECRET_VALUE_RES = (
    re.compile(r"-----BEGIN [^-]*PRIVATE KEY-----"),
    re.compile(r"\bBearer\s+\S+", re.IGNORECASE),
    re.compile(r"\b(?:sk|ghp|github_pat|xox[baprs])-[-A-Za-z0-9_]{12,}\b"),
)


class AuditError(ValueError):
    """Unsafe or invalid manifest input."""


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


def scan_unsafe(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = key.casefold().replace("-", "_")
            if any(part in normalized for part in FORBIDDEN_KEY_PARTS):
                raise AuditError(f"{path}.{key}: raw-content, location, or credential field is forbidden")
            scan_unsafe(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            scan_unsafe(child, f"{path}[{index}]")
    elif isinstance(value, str) and any(pattern.search(value) for pattern in SECRET_VALUE_RES):
        raise AuditError(f"{path}: secret-bearing value is forbidden")


def _integer(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise AuditError(f"{field}: expected integer")
    return value


def _boolean(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        raise AuditError(f"{field}: expected boolean")
    return value


def _public_https_origin(value: Any) -> bool:
    if not isinstance(value, str) or not value.isascii():
        return False
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        return False
    if (
        parsed.scheme != "https"
        or not parsed.netloc
        or parsed.username
        or parsed.password
        or parsed.path
        or parsed.query
        or parsed.fragment
    ):
        return False
    host = parsed.hostname
    if not host or host.lower() == "localhost" or host.lower().endswith((".localhost", ".local")):
        return False
    normalized_host = host.lower()
    labels = normalized_host.split(".")
    if not (
        len(labels) >= 3
        and tuple(labels[-2:]) == UPLOAD_PROVIDER_SUFFIX
        and any(label == "s3" or label.startswith("s3-") for label in labels[:-2])
    ):
        return False
    if port not in (None, 443):
        return False
    try:
        import ipaddress

        address = ipaddress.ip_address(host)
    except ValueError:
        return True
    return address.is_global


def audit(document: Any) -> dict[str, Any]:
    scan_unsafe(document)
    if not isinstance(document, dict):
        raise AuditError("root must be an object")
    keys = set(document)
    if not REQUIRED_KEYS.issubset(keys) or keys - REQUIRED_KEYS - OPTIONAL_KEYS:
        raise AuditError("root fields must match the documented closed schema")
    if document["schema_version"] != "1":
        raise AuditError("schema_version: only string version 1 is supported")
    if document["operation"] not in OPERATIONS:
        raise AuditError("operation: unsupported value")
    if not isinstance(document["content_sha256"], str) or not SHA256.fullmatch(document["content_sha256"]):
        raise AuditError("content_sha256: expected lowercase sha256 digest")
    if document["extension"] not in SUPPORTED_EXTENSIONS:
        raise AuditError("extension: unsupported value")
    if document["classification"] not in CLASSIFICATIONS:
        raise AuditError("classification: unsupported value")

    byte_size = _integer(document["byte_size"], "byte_size")
    upload_origin = document["presigned_upload_origin"]
    upload_origin_approved = _boolean(
        document["presigned_upload_origin_approved"],
        "presigned_upload_origin_approved",
    )
    inspection_pending = upload_origin is None and not upload_origin_approved
    checks: dict[str, str] = {
        "byte_size": "PASS" if 0 < byte_size <= MAX_BYTES else "FAIL",
        "classification": "FAIL" if document["classification"] == "restricted" else "PASS",
        "data_owner_approved": "PASS" if _boolean(document["data_owner_approved"], "data_owner_approved") else "FAIL",
        "consent_confirmed": "PASS" if _boolean(document["consent_confirmed"], "consent_confirmed") else "FAIL",
        "transfer_approved": "PASS" if _boolean(document["transfer_approved"], "transfer_approved") else "FAIL",
        "provider_retention_acknowledged": "PASS"
        if _boolean(document["provider_retention_acknowledged"], "provider_retention_acknowledged")
        else "FAIL",
        "api_control_plane_origin": "PASS" if document["api_control_plane_origin"] == API_ORIGIN else "FAIL",
        "presigned_upload_origin": "PENDING"
        if inspection_pending
        else "PASS"
        if _public_https_origin(upload_origin)
        else "FAIL",
        "presigned_upload_origin_approved": "PENDING"
        if inspection_pending
        else "PASS"
        if upload_origin_approved
        else "FAIL",
    }

    character_count = document.get("text_character_count")
    word_count = document.get("word_count")
    checks["text_metrics"] = (
        "FAIL" if document["extension"] == ".txt" and (character_count is None or word_count is None) else "PASS"
    )
    if character_count is not None:
        characters = _integer(character_count, "text_character_count")
        checks["text_character_count"] = "PASS" if 0 <= characters <= MAX_CHARACTERS else "FAIL"
    if word_count is not None:
        words = _integer(word_count, "word_count")
        checks["word_count"] = "PASS" if words >= MIN_WORDS else "FAIL"

    failed = sorted(name for name, result in checks.items() if result == "FAIL")
    pending = sorted(name for name, result in checks.items() if result == "PENDING")
    decision = "BLOCKED" if failed else "INSPECTION_READY" if pending else "READY"
    return {
        "decision": decision,
        "failed_checks": failed,
        "pending_checks": pending,
        "checks": checks,
        "operation": document["operation"],
        "extension": document["extension"],
        "byte_size": byte_size,
        "classification": document["classification"],
        "approved_api_control_plane_origin": API_ORIGIN,
        "approved_presigned_upload_origin": upload_origin,
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
            "failed_checks": ["invalid_or_unsafe_input"],
            "error": str(exc),
            "offline": True,
            "writes_performed": False,
            "network_calls": 0,
        }
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 2
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if result["decision"] in {"INSPECTION_READY", "READY"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
