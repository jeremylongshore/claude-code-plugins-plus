#!/usr/bin/env python3
"""Create a review-only inactive-license candidate plan from sanitized JSON.

This script is deliberately offline and non-mutating. It accepts only keyed-HMAC
pseudonyms, UTC timestamps, and the admin flag; it never resolves identities, uses
the network, or deletes anything.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HEX_SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")
FORBIDDEN_KEY_PARTS = (
    "name",
    "email",
    "user_id",
    "userid",
    "institution",
    "invitee",
    "raw_id",
    "secret",
    "token",
    "password",
    "authorization",
    "header",
    "credential",
)
ROOT_FIELDS = {
    "snapshot_version",
    "snapshot_generated_at",
    "inactive_before",
    "pseudonymization_attestation",
    "users",
}
ATTESTATION_FIELDS = {"scheme", "key_reference", "key_version", "producer_attested"}
USER_FIELDS = {"resource_id_hmac_sha256", "last_activity_at", "is_admin"}
SAFE_REFERENCE = re.compile(r"^[A-Za-z0-9._:/-]{1,128}$")


class SnapshotError(ValueError):
    """Raised when a snapshot cannot safely support a review plan."""


def _walk_forbidden_keys(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if not isinstance(key, str):
                raise SnapshotError(f"{path}: object keys must be strings")
            lowered = key.casefold()
            if any(part in lowered for part in FORBIDDEN_KEY_PARTS):
                raise SnapshotError(f"{path}.{key}: forbidden identity or secret key")
            _walk_forbidden_keys(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _walk_forbidden_keys(child, f"{path}[{index}]")


def _timestamp(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise SnapshotError(f"{field}: must be an ISO-8601 UTC timestamp ending in Z")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise SnapshotError(f"{field}: invalid ISO-8601 timestamp") from exc
    if parsed.tzinfo != timezone.utc:
        raise SnapshotError(f"{field}: must be UTC")
    return parsed


def _exact_fields(value: dict[str, Any], expected: set[str], path: str) -> None:
    unknown = sorted(set(value) - expected)
    missing = sorted(expected - set(value))
    if unknown:
        raise SnapshotError(f"{path}: unknown field(s): {', '.join(unknown)}")
    if missing:
        raise SnapshotError(f"{path}: missing field(s): {', '.join(missing)}")


def analyze(snapshot: Any) -> dict[str, Any]:
    _walk_forbidden_keys(snapshot)
    if not isinstance(snapshot, dict):
        raise SnapshotError("$: root must be one JSON object")
    _exact_fields(snapshot, ROOT_FIELDS, "$")
    if (
        isinstance(snapshot["snapshot_version"], bool)
        or not isinstance(snapshot["snapshot_version"], int)
        or snapshot["snapshot_version"] != 1
    ):
        raise SnapshotError("snapshot_version: only integer version 1 is accepted")
    generated_at = _timestamp(snapshot["snapshot_generated_at"], "snapshot_generated_at")
    cutoff = _timestamp(snapshot["inactive_before"], "inactive_before")
    if cutoff > generated_at:
        raise SnapshotError("inactive_before: cannot be later than snapshot_generated_at")
    attestation = snapshot["pseudonymization_attestation"]
    if not isinstance(attestation, dict):
        raise SnapshotError("pseudonymization_attestation: must be an object")
    _exact_fields(attestation, ATTESTATION_FIELDS, "$.pseudonymization_attestation")
    if attestation["scheme"] != "HMAC-SHA256":
        raise SnapshotError("pseudonymization_attestation.scheme: must be HMAC-SHA256")
    for field in ("key_reference", "key_version"):
        if not isinstance(attestation[field], str) or not SAFE_REFERENCE.fullmatch(attestation[field]):
            raise SnapshotError(f"pseudonymization_attestation.{field}: invalid non-secret reference")
    if attestation["producer_attested"] is not True:
        raise SnapshotError("pseudonymization_attestation.producer_attested: must be true")
    users = snapshot["users"]
    if not isinstance(users, list):
        raise SnapshotError("users: must be an array")

    seen: set[str] = set()
    candidates: list[dict[str, str]] = []
    excluded_admin_count = 0
    excluded_recent_count = 0
    for index, user in enumerate(users):
        path = f"$.users[{index}]"
        if not isinstance(user, dict):
            raise SnapshotError(f"{path}: must be an object")
        _exact_fields(user, USER_FIELDS, path)
        digest = user["resource_id_hmac_sha256"]
        if not isinstance(digest, str) or not HEX_SHA256.fullmatch(digest):
            raise SnapshotError(f"{path}.resource_id_hmac_sha256: must be exactly 64 hexadecimal characters")
        normalized_digest = digest.lower()
        if normalized_digest in seen:
            raise SnapshotError(f"{path}.resource_id_hmac_sha256: duplicate resource pseudonym")
        seen.add(normalized_digest)
        if not isinstance(user["is_admin"], bool):
            raise SnapshotError(f"{path}.is_admin: must be boolean")
        activity = _timestamp(user["last_activity_at"], f"{path}.last_activity_at")
        if user["is_admin"]:
            excluded_admin_count += 1
        elif activity < cutoff:
            candidates.append(
                {
                    "resource_id_hmac_sha256": normalized_digest,
                    "reason": "last_activity_before_cutoff",
                    "recommended_review_action": "HUMAN_REVIEW_ONLY",
                }
            )
        else:
            excluded_recent_count += 1

    candidates.sort(key=lambda item: item["resource_id_hmac_sha256"])
    return {
        "plan_type": "REVIEW_ONLY",
        "mutation_performed": False,
        "pseudonymization": "PRODUCER_ATTESTED_HMAC_SHA256_NOT_CRYPTOGRAPHICALLY_VERIFIED",
        "snapshot_generated_at": snapshot["snapshot_generated_at"],
        "inactive_before": snapshot["inactive_before"],
        "candidate_count": len(candidates),
        "excluded_admin_count": excluded_admin_count,
        "excluded_recent_count": excluded_recent_count,
        "candidates": candidates,
    }


def _load(source: str) -> Any:
    raw = sys.stdin.read() if source == "-" else Path(source).read_text(encoding="utf-8")

    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise SnapshotError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    def reject_constant(value: str) -> Any:
        raise SnapshotError(f"non-standard JSON constant: {value}")

    try:
        return json.loads(raw, object_pairs_hook=reject_duplicates, parse_constant=reject_constant)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise SnapshotError(f"input is not valid UTF-8 JSON: {exc}") from exc


def _self_test() -> None:
    old = "a" * 64
    admin = "b" * 64
    equal = "c" * 64
    snapshot = {
        "snapshot_version": 1,
        "snapshot_generated_at": "2026-09-04T00:00:00Z",
        "inactive_before": "2026-09-01T00:00:00Z",
        "pseudonymization_attestation": {
            "scheme": "HMAC-SHA256",
            "key_reference": "org-license-audit",
            "key_version": "v1",
            "producer_attested": True,
        },
        "users": [
            {"resource_id_hmac_sha256": old, "last_activity_at": "2026-08-01T00:00:00Z", "is_admin": False},
            {"resource_id_hmac_sha256": admin, "last_activity_at": "2026-01-01T00:00:00Z", "is_admin": True},
            {"resource_id_hmac_sha256": equal, "last_activity_at": "2026-09-01T00:00:00Z", "is_admin": False},
        ],
    }
    result = analyze(snapshot)
    assert result["candidate_count"] == 1
    assert result["excluded_admin_count"] == 1
    assert result["candidates"][0]["resource_id_hmac_sha256"] == old
    assert result["plan_type"] == "REVIEW_ONLY"
    invalid = [
        {"snapshot_version": 1, "users": []},
        {
            "snapshot_version": 1,
            "snapshot_generated_at": "2026-09-04T00:00:00Z",
            "inactive_before": "2026-09-01T00:00:00Z",
            "pseudonymization_attestation": {
                "scheme": "SHA-256",
                "key_reference": "none",
                "key_version": "none",
                "producer_attested": False,
            },
            "users": [],
        },
        {
            "snapshot_version": 1,
            "snapshot_generated_at": "2026-09-04T00:00:00Z",
            "inactive_before": "2026-09-05T00:00:00Z",
            "users": [],
        },
        {
            "snapshot_version": 1,
            "snapshot_generated_at": "2026-09-04T00:00:00Z",
            "inactive_before": "2026-09-01T00:00:00Z",
            "users": [
                {"resource_id_hmac_sha256": "raw-user", "last_activity_at": "2026-08-01T00:00:00Z", "is_admin": False}
            ],
        },
        {
            "snapshot_version": 1,
            "snapshot_generated_at": "2026-09-04T00:00:00Z",
            "inactive_before": "2026-09-01T00:00:00Z",
            "users": [
                {
                    "resource_id_hmac_sha256": old,
                    "last_activity_at": "2026-08-01T00:00:00Z",
                    "is_admin": False,
                    "email": "x@example.com",
                }
            ],
        },
        {
            "snapshot_version": 1,
            "snapshot_generated_at": "2026-09-04T00:00:00Z",
            "inactive_before": "2026-09-01T00:00:00Z",
            "users": [
                {
                    "resource_id_hmac_sha256": old,
                    "last_activity_at": "2026-08-01T00:00:00Z",
                    "is_admin": False,
                    "audit": {"client_secret": "x"},
                }
            ],
        },
    ]
    for candidate in invalid:
        try:
            analyze(candidate)
        except SnapshotError:
            continue
        raise AssertionError(f"unsafe or invalid snapshot was accepted: {candidate}")
    print(f"self-test: {1 + len(invalid)} passed")


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a review-only Grammarly license plan offline.")
    parser.add_argument("source", nargs="?", default="-", help="JSON file, or - for stdin")
    parser.add_argument("--self-test", action="store_true", help="run deterministic built-in checks")
    args = parser.parse_args()
    try:
        if args.self_test:
            _self_test()
        else:
            print(json.dumps(analyze(_load(args.source)), sort_keys=True))
    except (OSError, SnapshotError, AssertionError, RecursionError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
