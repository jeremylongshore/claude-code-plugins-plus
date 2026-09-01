#!/usr/bin/env python3
"""Deterministic, read-only Snowflake Native App release preflight."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

SCHEMA_VERSION = "1"
CHANGE_KINDS = {"VERSION", "PATCH"}
CHANNELS = {"QA", "ALPHA", "DEFAULT"}
SCAN_STATUSES = {"NOT_REVIEWED", "IN_PROGRESS", "APPROVED", "REJECTED"}
RETIREMENT_STATES = {"PLANNED", "IN_PROGRESS", "COMPLETE"}
SETUP_OPERATIONS = {
    "CREATE_IF_NOT_EXISTS",
    "CREATE_OR_ALTER",
    "CREATE_OR_REPLACE",
    "ALTER_IDEMPOTENT",
    "MERGE_GUARDED",
    "GRANT",
    "OTHER",
}
REQUIRED_SOURCE_TOPICS = {
    "setup_script",
    "manifest_privileges",
    "app_specifications",
    "security_scan",
    "release_channels",
    "upgrades",
    "release_notes",
}
REQUIRED_ROLLBACK_OBSERVABLES = {"upgrade_failures", "disabled_instances"}
RECEIPT_SOURCES = {
    "artifact": "CI_NATIVE_APP_BUNDLE",
    "setup_parser": "STATIC_SETUP_SQL_PARSER",
    "security_scan": "SHOW VERSIONS IN APPLICATION PACKAGE",
    "channels": "SHOW RELEASE CHANNELS AND VERSION INVENTORY",
    "cohorts": "SNOWFLAKE.DATA_SHARING_USAGE.APPLICATION_STATE",
    "compatibility": "CI_NATIVE_APP_COMPATIBILITY",
    "retirements": "PROVIDER_VERSION_RETIREMENT_INVENTORY",
    "rollback": "CI_NATIVE_APP_ROLLBACK_DRY_RUN",
}
SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
SENSITIVE_KEY_RE = re.compile(
    r"password|passphrase|secret|private.?key|credential|token|authorization|"
    r"sql.?text|query.?text|raw.?sql|raw.?row|customer.?data|pii",
    re.IGNORECASE,
)
SENSITIVE_VALUE_RE = re.compile(
    r"(?i)(?:password|passphrase|secret|token|authorization|api[_-]?key)\s*[:=]|"
    r"bearer\s+[a-z0-9._~-]{8,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
)
PRESIGNED_URL_RE = re.compile(
    r"https?://\S+[?&](?:X-Amz-|X-Goog-|sig=|signature=)", re.IGNORECASE
)

REMEDIATION = {
    "SOURCE_REVIEW_INCOMPLETE": "Review the missing official Snowflake topic and record its URL and UTC timestamp.",
    "SOURCE_REVIEW_STALE": "Re-read the official Snowflake source for the target release window.",
    "MANIFEST_SETUP_PATH_MISMATCH": "Reconcile the candidate manifest artifact path with the tested setup-script path.",
    "PRIVILEGE_DELTA_UNDISCLOSED": "Document the exact privilege delta and obtain consumer-facing review evidence.",
    "APP_SPEC_DELTA_UNDISCLOSED": "Document the controlled-access delta and consumer approval impact.",
    "APP_SPEC_SEQUENCE_NOT_ADVANCED": "Recollect the App Spec definition and sequence after the definition update.",
    "PATCH_MANIFEST_VERSION_CHANGE": "Move the manifest-version change to a new app version.",
    "PATCH_PRIVILEGE_DELTA_UNSUPPORTED": "Move the privilege request change to a new app version.",
    "MANIFEST_V2_TO_V1_REVOCATION_RISK": "Keep manifest v2 or design and disclose a new-version privilege migration.",
    "SETUP_EVIDENCE_INCOMPLETE": "Run fresh-install, restart-from-beginning, repeat-run, and prior-version upgrade tests.",
    "SETUP_NON_IDEMPOTENT": "Replace the statement with a guarded idempotent form and rerun all setup tests.",
    "SETUP_UNCLASSIFIED_STATEMENT": "Classify the statement deterministically or block the setup artifact as ambiguous.",
    "STATEFUL_CREATE_OR_REPLACE": "Use a state-preserving migration and verify state invariants.",
    "APPLICATION_ROLE_REPLACE_GRANT_LOSS": "Use CREATE APPLICATION ROLE IF NOT EXISTS and verify retained account-role grants.",
    "SCAN_NOT_APPROVED": "After a separately approved channel action, recollect SHOW VERSIONS review_status.",
    "SCAN_IN_PROGRESS": "Wait for scan completion and recollect read-only scan evidence.",
    "SCAN_REJECTED": "Resolve the reported review issue and submit a new candidate through an approved process.",
    "CHANNEL_VERSION_LIMIT": "Wait for an old version to complete upgrade/removal before proposing the candidate.",
    "COHORT_EVIDENCE_INCOMPLETE": "Reconcile observed instances to the full target-channel cohort denominator.",
    "COHORT_PREFLIGHT_FAILED": "Resolve disabled, failed, incompatible, or rollback-unready cohort instances.",
    "VERSION_COMPATIBILITY_UNPROVEN": "Test the candidate against the immediately prior version and hash the receipt.",
    "PATCH_STATE_CHANGE": "Move state changes to a compatible version release rather than a patch.",
    "RETIREMENT_ASYNCHRONOUS_PENDING": "Recollect consumer and running-code counts; do not treat the drop request as completion.",
    "ROLLBACK_PACKET_INCOMPLETE": "Define owner, tested artifact, baseline, halt plan, stop conditions, and observables.",
    "EVIDENCE_STALE": "Recollect the named read-only surface inside the allowed evidence window.",
    "ARTIFACT_RECEIPT_UNVERIFIABLE": "Rebuild the exact-schema bundle receipt from the immutable candidate artifact.",
    "SETUP_PARSER_RECEIPT_UNVERIFIABLE": "Reparse the setup SQL statically and bind the complete normalized statement payload.",
    "SECURITY_SCAN_RECEIPT_UNVERIFIABLE": "Recollect one exact candidate row from SHOW VERSIONS and hash the receipt.",
    "CHANNEL_RECEIPT_UNVERIFIABLE": "Recollect the complete channel/version inventory without truncation and hash it.",
    "COHORT_RECEIPT_UNVERIFIABLE": "Recollect the full installed-instance denominator and bind its aggregate payload.",
    "COMPATIBILITY_RECEIPT_UNVERIFIABLE": "Rerun the candidate/prior-version compatibility suite and hash its exact payload.",
    "RETIREMENT_RECEIPT_UNVERIFIABLE": "Recollect the complete retirement inventory and bind its exact payload.",
    "ROLLBACK_RECEIPT_UNVERIFIABLE": "Rerun the rollback dry-run and hash its exact observables and stop conditions.",
}


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def receipt_hash(value: dict[str, Any]) -> str:
    unsigned = dict(value)
    unsigned.pop("receipt_sha256", None)
    return "sha256:" + hashlib.sha256(canonical_bytes(unsigned)).hexdigest()


def require_object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    return value


def require_list(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be an array")
    return value


def require_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def require_bool(value: Any, field: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field} must be boolean")
    return value


def require_int(value: Any, field: str, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise ValueError(f"{field} must be an integer >= {minimum}")
    return value


def require_hash(value: Any, field: str) -> str:
    if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
        raise ValueError(f"{field} must be a canonical sha256 hash")
    return value


def parse_timestamp(value: Any, field: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a timezone-aware ISO 8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(
            f"{field} must be a timezone-aware ISO 8601 timestamp"
        ) from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field} must include a timezone")
    if parsed > datetime.now(parsed.tzinfo) + timedelta(minutes=1):
        raise ValueError(f"{field} cannot be in the future")
    return parsed


def reject_sensitive(value: Any, path: str = "input") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if SENSITIVE_KEY_RE.search(str(key)):
                raise ValueError(f"sensitive field is not accepted: {path}.{key}")
            reject_sensitive(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            reject_sensitive(child, f"{path}[{index}]")
    elif isinstance(value, str):
        if SENSITIVE_VALUE_RE.search(value):
            raise ValueError(f"credential-shaped value is not accepted: {path}")
        if PRESIGNED_URL_RE.search(value):
            raise ValueError(f"presigned URL is not accepted: {path}")


def add_finding(
    findings: list[dict[str, str]],
    code: str,
    surface: str,
    message: str,
    evidence_state: str = "derived",
) -> None:
    findings.append(
        {
            "code": code,
            "severity": "BLOCKER",
            "surface": surface,
            "evidence_state": evidence_state,
            "message": message,
            "next_read_only_check": REMEDIATION[code],
        }
    )


def stale(
    observed: datetime,
    as_of: datetime,
    minutes: int,
    findings: list[dict[str, str]],
    surface: str,
) -> None:
    if observed > as_of:
        raise ValueError(f"{surface} observation cannot be after as_of")
    if as_of - observed > timedelta(minutes=minutes):
        add_finding(
            findings,
            "EVIDENCE_STALE",
            surface,
            f"{surface} evidence is older than {minutes} minutes",
            "observed",
        )


def validate_bound_receipt(
    value: Any,
    *,
    findings: list[dict[str, str]],
    label: str,
    code: str,
    expected_fields: set[str],
    expected_source: str,
    expected_artifact: str,
    expected_count: int,
    expected_bindings: dict[str, Any],
    as_of: datetime,
) -> dict[str, Any] | None:
    """Validate exact schema, canonical hash, provenance, count, and payload bindings."""
    if not isinstance(value, dict):
        add_finding(
            findings,
            code,
            label,
            f"{label} receipt is missing or not an object",
            "missing",
        )
        return None
    receipt = value
    problems: list[str] = []
    if set(receipt) != expected_fields:
        missing = sorted(expected_fields - set(receipt))
        extra = sorted(set(receipt) - expected_fields)
        problems.append(f"field mismatch missing={missing} extra={extra}")
    if receipt.get("schema_version") != SCHEMA_VERSION:
        problems.append("schema_version mismatch")
    if receipt.get("source") != expected_source:
        problems.append("source mismatch")
    if receipt.get("artifact_sha256") != expected_artifact:
        problems.append("candidate artifact mismatch")
    if (
        type(receipt.get("row_count")) is not int
        or receipt.get("row_count") != expected_count
    ):
        problems.append("row_count mismatch")
    if receipt.get("truncated") is not False:
        problems.append("receipt is truncated or truncation is not false")
    for key, expected in expected_bindings.items():
        if receipt.get(key) != expected:
            problems.append(f"{key} payload mismatch")
    hash_value = receipt.get("receipt_sha256")
    if not isinstance(hash_value, str) or not SHA256_RE.fullmatch(hash_value):
        problems.append("receipt_sha256 is invalid")
    elif hash_value != receipt_hash(receipt):
        problems.append("receipt_sha256 does not match receipt contents")
    try:
        collected = parse_timestamp(
            receipt.get("collected_at"), f"{label}.collected_at"
        )
        if collected > as_of:
            problems.append("collected_at is after as_of")
        elif as_of - collected > timedelta(minutes=60):
            add_finding(
                findings,
                "EVIDENCE_STALE",
                label,
                f"{label} receipt is older than 60 minutes",
                "observed",
            )
    except ValueError as exc:
        problems.append(str(exc))
    if problems:
        add_finding(
            findings,
            code,
            label,
            "; ".join(problems),
            "observed",
        )
    return receipt


def unique_named(rows: Any, field: str) -> list[dict[str, Any]]:
    result = require_list(rows, field)
    names: set[str] = set()
    for index, row_value in enumerate(result):
        row = require_object(row_value, f"{field}[{index}]")
        name = require_string(row.get("name"), f"{field}[{index}].name")
        if name in names:
            raise ValueError(f"{field} contains duplicate name {name!r}")
        names.add(name)
    return result


def normalize_manifest(value: Any, field: str) -> dict[str, Any]:
    manifest = require_object(value, field)
    expected = {
        "source_sha256",
        "manifest_version",
        "setup_script",
        "privileges",
        "references",
        "app_specs",
    }
    if set(manifest) != expected:
        raise ValueError(f"{field} must contain exactly {sorted(expected)}")
    manifest_version = require_int(
        manifest.get("manifest_version"), f"{field}.manifest_version", 1
    )
    setup_script = require_string(manifest.get("setup_script"), f"{field}.setup_script")

    privileges = unique_named(manifest.get("privileges"), f"{field}.privileges")
    normalized_privileges: list[dict[str, str]] = []
    for index, item in enumerate(privileges):
        if set(item) != {"name", "description"}:
            raise ValueError(f"{field}.privileges[{index}] contains unexpected fields")
        normalized_privileges.append(
            {
                "name": require_string(
                    item.get("name"), f"{field}.privileges[{index}].name"
                ),
                "description": require_string(
                    item.get("description"), f"{field}.privileges[{index}].description"
                ),
            }
        )

    references = unique_named(manifest.get("references"), f"{field}.references")
    normalized_references: list[dict[str, Any]] = []
    for index, item in enumerate(references):
        if set(item) != {"name", "object_type", "privileges"}:
            raise ValueError(f"{field}.references[{index}] contains unexpected fields")
        privileges_value = require_list(
            item.get("privileges"), f"{field}.references[{index}].privileges"
        )
        reference_privileges = sorted(
            {
                require_string(entry, f"{field}.references[{index}].privileges")
                for entry in privileges_value
            }
        )
        normalized_references.append(
            {
                "name": item["name"],
                "object_type": require_string(
                    item.get("object_type"), f"{field}.references[{index}].object_type"
                ),
                "privileges": reference_privileges,
            }
        )

    app_specs = unique_named(manifest.get("app_specs"), f"{field}.app_specs")
    normalized_specs: list[dict[str, Any]] = []
    for index, item in enumerate(app_specs):
        if set(item) != {"name", "type", "sequence", "definition_sha256"}:
            raise ValueError(f"{field}.app_specs[{index}] contains unexpected fields")
        normalized_specs.append(
            {
                "name": item["name"],
                "type": require_string(
                    item.get("type"), f"{field}.app_specs[{index}].type"
                ),
                "sequence": require_int(
                    item.get("sequence"), f"{field}.app_specs[{index}].sequence", 0
                ),
                "definition_sha256": require_hash(
                    item.get("definition_sha256"),
                    f"{field}.app_specs[{index}].definition_sha256",
                ),
            }
        )
    return {
        "source_sha256": require_hash(
            manifest.get("source_sha256"), f"{field}.source_sha256"
        ),
        "manifest_version": manifest_version,
        "setup_script": setup_script,
        "privileges": sorted(normalized_privileges, key=lambda row: row["name"]),
        "references": sorted(normalized_references, key=lambda row: row["name"]),
        "app_specs": sorted(normalized_specs, key=lambda row: row["name"]),
    }


def named_map(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {row["name"]: row for row in rows}


def diff_names(
    previous: list[dict[str, Any]], candidate: list[dict[str, Any]]
) -> dict[str, list[str]]:
    old = named_map(previous)
    new = named_map(candidate)
    return {
        "added": sorted(set(new) - set(old)),
        "removed": sorted(set(old) - set(new)),
        "changed": sorted(
            name for name in set(old) & set(new) if old[name] != new[name]
        ),
    }


def validate_source_review(
    value: Any, as_of: datetime, findings: list[dict[str, str]]
) -> list[dict[str, str]]:
    rows = require_list(value, "source_review")
    seen: set[str] = set()
    normalized: list[dict[str, str]] = []
    for index, row_value in enumerate(rows):
        row = require_object(row_value, f"source_review[{index}]")
        if set(row) != {"topic", "url", "reviewed_at"}:
            raise ValueError(f"source_review[{index}] contains unexpected fields")
        topic = require_string(row.get("topic"), f"source_review[{index}].topic")
        if topic not in REQUIRED_SOURCE_TOPICS:
            raise ValueError(f"unknown source_review topic {topic!r}")
        if topic in seen:
            raise ValueError(f"source_review contains duplicate topic {topic!r}")
        seen.add(topic)
        url = require_string(row.get("url"), f"source_review[{index}].url")
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.netloc != "docs.snowflake.com":
            raise ValueError(
                f"source_review[{index}].url must be an official Snowflake documentation URL"
            )
        reviewed_text = require_string(
            row.get("reviewed_at"), f"source_review[{index}].reviewed_at"
        )
        reviewed_at = parse_timestamp(
            reviewed_text, f"source_review[{index}].reviewed_at"
        )
        if reviewed_at > as_of:
            raise ValueError(
                f"source_review[{index}].reviewed_at cannot be after as_of"
            )
        if as_of - reviewed_at > timedelta(days=30):
            add_finding(
                findings,
                "SOURCE_REVIEW_STALE",
                f"source_review.{topic}",
                f"official source review for {topic} is older than 30 days",
                "observed",
            )
        normalized.append({"topic": topic, "url": url, "reviewed_at": reviewed_text})
    missing = sorted(REQUIRED_SOURCE_TOPICS - seen)
    if missing:
        add_finding(
            findings,
            "SOURCE_REVIEW_INCOMPLETE",
            "source_review",
            f"missing official source topics: {', '.join(missing)}",
            "missing",
        )
    return sorted(normalized, key=lambda row: row["topic"])


def analyze(data: Any) -> dict[str, Any]:
    root = require_object(data, "input")
    reject_sensitive(root)
    expected_root = {
        "schema_version",
        "as_of",
        "package",
        "source_review",
        "manifest",
        "setup_script",
        "artifact_receipt",
        "security_scan",
        "channels",
        "channel_receipt",
        "cohorts",
        "cohort_receipt",
        "retirements",
        "retirement_receipt",
        "compatibility",
        "rollback",
    }
    if set(root) != expected_root:
        raise ValueError(f"input must contain exactly {sorted(expected_root)}")
    if root.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"schema_version must be {SCHEMA_VERSION!r}")
    as_of_text = require_string(root.get("as_of"), "as_of")
    as_of = parse_timestamp(as_of_text, "as_of")
    findings: list[dict[str, str]] = []

    package = require_object(root.get("package"), "package")
    package_fields = {
        "name",
        "candidate_version",
        "candidate_patch",
        "change_kind",
        "artifact_sha256",
    }
    if set(package) != package_fields:
        raise ValueError(f"package must contain exactly {sorted(package_fields)}")
    normalized_package = {
        "name": require_string(package.get("name"), "package.name"),
        "candidate_version": require_string(
            package.get("candidate_version"), "package.candidate_version"
        ),
        "candidate_patch": require_int(
            package.get("candidate_patch"), "package.candidate_patch"
        ),
        "change_kind": require_string(
            package.get("change_kind"), "package.change_kind"
        ).upper(),
        "artifact_sha256": require_hash(
            package.get("artifact_sha256"), "package.artifact_sha256"
        ),
    }
    if normalized_package["change_kind"] not in CHANGE_KINDS:
        raise ValueError("package.change_kind must be VERSION or PATCH")

    source_review = validate_source_review(root.get("source_review"), as_of, findings)

    manifest_root = require_object(root.get("manifest"), "manifest")
    if set(manifest_root) != {"previous", "candidate", "consumer_disclosure"}:
        raise ValueError("manifest contains unexpected or missing fields")
    previous_manifest = normalize_manifest(
        manifest_root.get("previous"), "manifest.previous"
    )
    candidate_manifest = normalize_manifest(
        manifest_root.get("candidate"), "manifest.candidate"
    )
    disclosure = require_object(
        manifest_root.get("consumer_disclosure"), "manifest.consumer_disclosure"
    )
    if set(disclosure) != {"privilege_delta_reviewed", "app_spec_delta_reviewed"}:
        raise ValueError(
            "manifest.consumer_disclosure contains unexpected or missing fields"
        )
    privilege_reviewed = require_bool(
        disclosure.get("privilege_delta_reviewed"),
        "manifest.consumer_disclosure.privilege_delta_reviewed",
    )
    app_spec_reviewed = require_bool(
        disclosure.get("app_spec_delta_reviewed"),
        "manifest.consumer_disclosure.app_spec_delta_reviewed",
    )
    privilege_delta = diff_names(
        previous_manifest["privileges"], candidate_manifest["privileges"]
    )
    reference_delta = diff_names(
        previous_manifest["references"], candidate_manifest["references"]
    )
    app_spec_delta = diff_names(
        previous_manifest["app_specs"], candidate_manifest["app_specs"]
    )
    privilege_changed = any(privilege_delta.values()) or any(reference_delta.values())
    app_spec_changed = any(app_spec_delta.values())
    if privilege_changed and not privilege_reviewed:
        add_finding(
            findings,
            "PRIVILEGE_DELTA_UNDISCLOSED",
            "manifest",
            "candidate privilege/reference delta lacks consumer-facing review",
            "observed",
        )
    if app_spec_changed and not app_spec_reviewed:
        add_finding(
            findings,
            "APP_SPEC_DELTA_UNDISCLOSED",
            "manifest",
            "candidate App Spec delta lacks consumer-facing review",
            "observed",
        )
    old_specs = named_map(previous_manifest["app_specs"])
    new_specs = named_map(candidate_manifest["app_specs"])
    for name in sorted(set(old_specs) & set(new_specs)):
        old = old_specs[name]
        new = new_specs[name]
        if (
            old["definition_sha256"] != new["definition_sha256"]
            and new["sequence"] <= old["sequence"]
        ):
            add_finding(
                findings,
                "APP_SPEC_SEQUENCE_NOT_ADVANCED",
                f"manifest.app_specs.{name}",
                "App Spec definition changed without a larger sequence",
                "derived",
            )
    if (
        previous_manifest["manifest_version"] == 2
        and candidate_manifest["manifest_version"] == 1
    ):
        add_finding(
            findings,
            "MANIFEST_V2_TO_V1_REVOCATION_RISK",
            "manifest",
            "manifest v2 to v1 can revoke automatic privileges during upgrade",
            "derived",
        )
    if normalized_package["change_kind"] == "PATCH":
        if (
            previous_manifest["manifest_version"]
            != candidate_manifest["manifest_version"]
        ):
            add_finding(
                findings,
                "PATCH_MANIFEST_VERSION_CHANGE",
                "manifest",
                "patch changes manifest_version",
                "derived",
            )
        if privilege_changed:
            add_finding(
                findings,
                "PATCH_PRIVILEGE_DELTA_UNSUPPORTED",
                "manifest",
                "patch changes requested privileges or references",
                "derived",
            )

    setup = require_object(root.get("setup_script"), "setup_script")
    setup_fields = {
        "path",
        "sha256",
        "parse_status",
        "self_contained",
        "fresh_install_tested",
        "restart_from_beginning_tested",
        "repeat_run_tested",
        "upgrade_from_previous_tested",
        "test_receipt_sha256",
        "statements",
        "parser_receipt",
    }
    if set(setup) != setup_fields:
        raise ValueError(f"setup_script must contain exactly {sorted(setup_fields)}")
    setup_path = require_string(setup.get("path"), "setup_script.path")
    setup_hash = require_hash(setup.get("sha256"), "setup_script.sha256")
    if setup_path != candidate_manifest["setup_script"]:
        add_finding(
            findings,
            "MANIFEST_SETUP_PATH_MISMATCH",
            "setup_script",
            "tested setup path does not match candidate manifest",
            "observed",
        )
    if (
        require_string(setup.get("parse_status"), "setup_script.parse_status")
        != "PARSED"
    ):
        add_finding(
            findings,
            "SETUP_EVIDENCE_INCOMPLETE",
            "setup_script",
            "setup script was not parsed successfully",
            "observed",
        )
    setup_tests = (
        "self_contained",
        "fresh_install_tested",
        "restart_from_beginning_tested",
        "repeat_run_tested",
        "upgrade_from_previous_tested",
    )
    for field in setup_tests:
        if not require_bool(setup.get(field), f"setup_script.{field}"):
            add_finding(
                findings,
                "SETUP_EVIDENCE_INCOMPLETE",
                f"setup_script.{field}",
                f"{field} is not proven",
                "observed",
            )
    require_hash(setup.get("test_receipt_sha256"), "setup_script.test_receipt_sha256")
    statements = require_list(setup.get("statements"), "setup_script.statements")
    if not statements:
        add_finding(
            findings,
            "SETUP_EVIDENCE_INCOMPLETE",
            "setup_script.statements",
            "normalized setup statement denominator is empty",
            "missing",
        )
    expected_index = 1
    for index, statement_value in enumerate(statements):
        statement = require_object(statement_value, f"setup_script.statements[{index}]")
        if set(statement) != {
            "index",
            "operation",
            "object_type",
            "object_name",
            "idempotent",
            "stateful",
        }:
            raise ValueError(
                f"setup_script.statements[{index}] contains unexpected fields"
            )
        actual_index = require_int(
            statement.get("index"), f"setup_script.statements[{index}].index", 1
        )
        if actual_index != expected_index:
            raise ValueError("setup_script statement indexes must be contiguous from 1")
        expected_index += 1
        operation = require_string(
            statement.get("operation"), f"setup_script.statements[{index}].operation"
        ).upper()
        if operation not in SETUP_OPERATIONS:
            raise ValueError(f"unknown setup operation {operation!r}")
        object_type = require_string(
            statement.get("object_type"),
            f"setup_script.statements[{index}].object_type",
        ).upper()
        require_string(
            statement.get("object_name"),
            f"setup_script.statements[{index}].object_name",
        )
        idempotent = require_bool(
            statement.get("idempotent"), f"setup_script.statements[{index}].idempotent"
        )
        stateful = require_bool(
            statement.get("stateful"), f"setup_script.statements[{index}].stateful"
        )
        if operation == "CREATE_OR_REPLACE" and object_type == "APPLICATION_ROLE":
            add_finding(
                findings,
                "APPLICATION_ROLE_REPLACE_GRANT_LOSS",
                f"setup_script.statement.{actual_index}",
                "CREATE OR REPLACE APPLICATION ROLE can remove account-role grants",
                "observed",
            )
        if operation == "OTHER":
            add_finding(
                findings,
                "SETUP_UNCLASSIFIED_STATEMENT",
                f"setup_script.statement.{actual_index}",
                "setup statement remains unclassified despite a non-ambiguous parser claim",
                "observed",
            )
        if not idempotent:
            add_finding(
                findings,
                "SETUP_NON_IDEMPOTENT",
                f"setup_script.statement.{actual_index}",
                "statement is not idempotent when setup restarts from the beginning",
                "observed",
            )
        if operation == "CREATE_OR_REPLACE" and stateful:
            add_finding(
                findings,
                "STATEFUL_CREATE_OR_REPLACE",
                f"setup_script.statement.{actual_index}",
                "stateful object is replaced rather than migrated",
                "observed",
            )

    artifact_receipt_fields = {
        "schema_version",
        "source",
        "collected_at",
        "artifact_sha256",
        "candidate_version",
        "candidate_patch",
        "previous_manifest_sha256",
        "candidate_manifest_sha256",
        "previous_manifest_normalized_sha256",
        "candidate_manifest_normalized_sha256",
        "setup_sha256",
        "row_count",
        "truncated",
        "receipt_sha256",
    }
    validate_bound_receipt(
        root.get("artifact_receipt"),
        findings=findings,
        label="artifact_receipt",
        code="ARTIFACT_RECEIPT_UNVERIFIABLE",
        expected_fields=artifact_receipt_fields,
        expected_source=RECEIPT_SOURCES["artifact"],
        expected_artifact=normalized_package["artifact_sha256"],
        expected_count=3,
        expected_bindings={
            "candidate_version": normalized_package["candidate_version"],
            "candidate_patch": normalized_package["candidate_patch"],
            "previous_manifest_sha256": previous_manifest["source_sha256"],
            "candidate_manifest_sha256": candidate_manifest["source_sha256"],
            "previous_manifest_normalized_sha256": "sha256:"
            + hashlib.sha256(canonical_bytes(previous_manifest)).hexdigest(),
            "candidate_manifest_normalized_sha256": "sha256:"
            + hashlib.sha256(canonical_bytes(candidate_manifest)).hexdigest(),
            "setup_sha256": setup_hash,
        },
        as_of=as_of,
    )
    parser_receipt = setup.get("parser_receipt")
    parser_version = (
        require_string(
            parser_receipt.get("parser_version"),
            "setup_script.parser_receipt.parser_version",
        )
        if isinstance(parser_receipt, dict)
        else "missing"
    )
    validate_bound_receipt(
        parser_receipt,
        findings=findings,
        label="setup_script.parser_receipt",
        code="SETUP_PARSER_RECEIPT_UNVERIFIABLE",
        expected_fields={
            "schema_version",
            "source",
            "collected_at",
            "artifact_sha256",
            "source_sha256",
            "normalized_statements_sha256",
            "parser_version",
            "candidate_version",
            "candidate_patch",
            "ambiguous",
            "executed",
            "row_count",
            "truncated",
            "receipt_sha256",
        },
        expected_source=RECEIPT_SOURCES["setup_parser"],
        expected_artifact=normalized_package["artifact_sha256"],
        expected_count=len(statements),
        expected_bindings={
            "source_sha256": setup_hash,
            "normalized_statements_sha256": "sha256:"
            + hashlib.sha256(canonical_bytes(statements)).hexdigest(),
            "parser_version": parser_version,
            "candidate_version": normalized_package["candidate_version"],
            "candidate_patch": normalized_package["candidate_patch"],
            "ambiguous": False,
            "executed": False,
        },
        as_of=as_of,
    )

    compatibility = require_object(root.get("compatibility"), "compatibility")
    previous_version = require_string(
        compatibility.get("previous_version"), "compatibility.previous_version"
    )
    supported = [
        require_string(item, "compatibility.supported_upgrade_from[]")
        for item in require_list(
            compatibility.get("supported_upgrade_from"),
            "compatibility.supported_upgrade_from",
        )
    ]
    if len(supported) != len(set(supported)):
        raise ValueError("compatibility.supported_upgrade_from contains duplicates")
    pair_tested = require_bool(
        compatibility.get("manifest_setup_pair_tested"),
        "compatibility.manifest_setup_pair_tested",
    )
    state_change = require_bool(
        compatibility.get("state_change"), "compatibility.state_change"
    )
    require_hash(
        compatibility.get("test_receipt_sha256"), "compatibility.test_receipt_sha256"
    )
    contract_tests = unique_named(
        compatibility.get("contract_tests"), "compatibility.contract_tests"
    )
    for index, test in enumerate(contract_tests):
        if set(test) != {"name", "status"}:
            raise ValueError(
                f"compatibility.contract_tests[{index}] contains unexpected fields"
            )
    compatibility_fields = {
        "schema_version",
        "source",
        "collected_at",
        "artifact_sha256",
        "previous_version",
        "supported_upgrade_from",
        "manifest_setup_pair_tested",
        "state_change",
        "contract_tests",
        "test_receipt_sha256",
        "row_count",
        "truncated",
        "receipt_sha256",
    }
    validate_bound_receipt(
        compatibility,
        findings=findings,
        label="compatibility",
        code="COMPATIBILITY_RECEIPT_UNVERIFIABLE",
        expected_fields=compatibility_fields,
        expected_source=RECEIPT_SOURCES["compatibility"],
        expected_artifact=normalized_package["artifact_sha256"],
        expected_count=len(contract_tests),
        expected_bindings={
            "previous_version": previous_version,
            "supported_upgrade_from": compatibility.get("supported_upgrade_from"),
            "manifest_setup_pair_tested": pair_tested,
            "state_change": state_change,
            "contract_tests": compatibility.get("contract_tests"),
            "test_receipt_sha256": compatibility.get("test_receipt_sha256"),
        },
        as_of=as_of,
    )
    contract_failed = False
    for index, test in enumerate(contract_tests):
        status = require_string(
            test.get("status"), f"compatibility.contract_tests[{index}].status"
        ).upper()
        if status not in {"PASS", "FAIL"}:
            raise ValueError("compatibility contract test status must be PASS or FAIL")
        if status != "PASS":
            contract_failed = True
    if (
        not contract_tests
        or not pair_tested
        or previous_version not in supported
        or contract_failed
    ):
        add_finding(
            findings,
            "VERSION_COMPATIBILITY_UNPROVEN",
            "compatibility",
            "candidate is not proven compatible with the immediately prior version",
            "observed",
        )
    if normalized_package["change_kind"] == "PATCH" and state_change:
        add_finding(
            findings,
            "PATCH_STATE_CHANGE",
            "compatibility",
            "patch declares a state change while multiple patches can remain active",
            "observed",
        )

    scan = require_object(root.get("security_scan"), "security_scan")
    scan_status = require_string(
        scan.get("review_status"), "security_scan.review_status"
    ).upper()
    if scan_status not in SCAN_STATUSES:
        raise ValueError(
            f"security_scan.review_status must be one of {sorted(SCAN_STATUSES)}"
        )
    scan_time_text = require_string(
        scan.get("observed_at"), "security_scan.observed_at"
    )
    scan_time = parse_timestamp(scan_time_text, "security_scan.observed_at")
    stale(scan_time, as_of, 60, findings, "security_scan")
    validate_bound_receipt(
        scan,
        findings=findings,
        label="security_scan",
        code="SECURITY_SCAN_RECEIPT_UNVERIFIABLE",
        expected_fields={
            "schema_version",
            "source",
            "collected_at",
            "artifact_sha256",
            "candidate_version",
            "candidate_patch",
            "review_status",
            "observed_at",
            "row_count",
            "truncated",
            "receipt_sha256",
        },
        expected_source=RECEIPT_SOURCES["security_scan"],
        expected_artifact=normalized_package["artifact_sha256"],
        expected_count=1,
        expected_bindings={
            "candidate_version": normalized_package["candidate_version"],
            "candidate_patch": normalized_package["candidate_patch"],
            "review_status": scan_status,
            "observed_at": scan_time_text,
        },
        as_of=as_of,
    )

    channel_rows = require_list(root.get("channels"), "channels")
    if not channel_rows:
        raise ValueError("channels must not be empty")
    seen_channels: set[str] = set()
    targeted_channels: set[str] = set()
    channel_summary: list[dict[str, Any]] = []
    for index, channel_value in enumerate(channel_rows):
        channel = require_object(channel_value, f"channels[{index}]")
        if set(channel) != {
            "name",
            "versions",
            "candidate_already_present",
            "targeted",
            "observed_at",
        }:
            raise ValueError(f"channels[{index}] contains unexpected fields")
        name = require_string(channel.get("name"), f"channels[{index}].name").upper()
        if name not in CHANNELS:
            raise ValueError(f"unknown release channel {name!r}")
        if name in seen_channels:
            raise ValueError(f"duplicate release channel {name!r}")
        seen_channels.add(name)
        versions = [
            require_string(item, f"channels[{index}].versions[]")
            for item in require_list(
                channel.get("versions"), f"channels[{index}].versions"
            )
        ]
        if len(versions) != len(set(versions)):
            raise ValueError(f"channels[{index}].versions contains duplicates")
        present = require_bool(
            channel.get("candidate_already_present"),
            f"channels[{index}].candidate_already_present",
        )
        targeted = require_bool(channel.get("targeted"), f"channels[{index}].targeted")
        observed_text = require_string(
            channel.get("observed_at"), f"channels[{index}].observed_at"
        )
        observed = parse_timestamp(observed_text, f"channels[{index}].observed_at")
        stale(observed, as_of, 60, findings, f"channel.{name}")
        candidate = normalized_package["candidate_version"]
        if present != (candidate in versions):
            raise ValueError(
                f"channels[{index}].candidate_already_present disagrees with versions"
            )
        projected = sorted(set(versions) | ({candidate} if targeted else set()))
        if targeted:
            targeted_channels.add(name)
            if len(projected) > 2:
                add_finding(
                    findings,
                    "CHANNEL_VERSION_LIMIT",
                    f"channel.{name}",
                    f"target channel projects {len(projected)} simultaneous versions",
                    "derived",
                )
        channel_summary.append(
            {
                "name": name,
                "targeted": targeted,
                "observed_versions": sorted(versions),
                "projected_versions": projected,
                "observed_at": observed_text,
            }
        )
    if not targeted_channels:
        raise ValueError("at least one release channel must be targeted")
    validate_bound_receipt(
        root.get("channel_receipt"),
        findings=findings,
        label="channel_receipt",
        code="CHANNEL_RECEIPT_UNVERIFIABLE",
        expected_fields={
            "schema_version",
            "source",
            "collected_at",
            "artifact_sha256",
            "channels",
            "row_count",
            "truncated",
            "receipt_sha256",
        },
        expected_source=RECEIPT_SOURCES["channels"],
        expected_artifact=normalized_package["artifact_sha256"],
        expected_count=len(channel_rows),
        expected_bindings={"channels": channel_rows},
        as_of=as_of,
    )
    scan_required = bool(targeted_channels & {"ALPHA", "DEFAULT"})
    if scan_status == "REJECTED":
        add_finding(
            findings,
            "SCAN_REJECTED",
            "security_scan",
            "candidate security scan is rejected",
            "observed",
        )
    elif scan_status == "IN_PROGRESS":
        add_finding(
            findings,
            "SCAN_IN_PROGRESS",
            "security_scan",
            "candidate security scan is still in progress",
            "observed",
        )
    elif scan_required and scan_status != "APPROVED":
        add_finding(
            findings,
            "SCAN_NOT_APPROVED",
            "security_scan",
            "ALPHA or DEFAULT target requires an approved candidate scan",
            "observed",
        )

    cohorts = require_list(root.get("cohorts"), "cohorts")
    cohort_names: set[str] = set()
    cohort_channels: set[str] = set()
    cohort_summary: list[dict[str, Any]] = []
    for index, cohort_value in enumerate(cohorts):
        cohort = require_object(cohort_value, f"cohorts[{index}]")
        if set(cohort) != {
            "name",
            "channel",
            "consumer_count",
            "observed_count",
            "from_versions",
            "preflight_status",
            "disabled_instances",
            "failed_upgrades",
            "rollback_observables_ready",
            "observed_at",
        }:
            raise ValueError(f"cohorts[{index}] contains unexpected fields")
        name = require_string(cohort.get("name"), f"cohorts[{index}].name")
        if name in cohort_names:
            raise ValueError(f"duplicate cohort name {name!r}")
        cohort_names.add(name)
        channel = require_string(
            cohort.get("channel"), f"cohorts[{index}].channel"
        ).upper()
        if channel not in targeted_channels:
            raise ValueError(f"cohort {name!r} refers to a non-target channel")
        cohort_channels.add(channel)
        consumer_count = require_int(
            cohort.get("consumer_count"), f"cohorts[{index}].consumer_count"
        )
        observed_count = require_int(
            cohort.get("observed_count"), f"cohorts[{index}].observed_count"
        )
        from_versions = [
            require_string(item, f"cohorts[{index}].from_versions[]")
            for item in require_list(
                cohort.get("from_versions"), f"cohorts[{index}].from_versions"
            )
        ]
        if consumer_count > 0 and not from_versions:
            raise ValueError(f"cohort {name!r} requires from_versions")
        preflight = require_string(
            cohort.get("preflight_status"), f"cohorts[{index}].preflight_status"
        ).upper()
        if preflight not in {"PASS", "FAIL"}:
            raise ValueError("cohort preflight_status must be PASS or FAIL")
        disabled = require_int(
            cohort.get("disabled_instances"), f"cohorts[{index}].disabled_instances"
        )
        failed = require_int(
            cohort.get("failed_upgrades"), f"cohorts[{index}].failed_upgrades"
        )
        rollback_ready = require_bool(
            cohort.get("rollback_observables_ready"),
            f"cohorts[{index}].rollback_observables_ready",
        )
        observed_text = require_string(
            cohort.get("observed_at"), f"cohorts[{index}].observed_at"
        )
        observed = parse_timestamp(observed_text, f"cohorts[{index}].observed_at")
        stale(observed, as_of, 60, findings, f"cohort.{name}")
        if observed_count != consumer_count:
            add_finding(
                findings,
                "COHORT_EVIDENCE_INCOMPLETE",
                f"cohort.{name}",
                f"observed {observed_count} of {consumer_count} instances",
                "observed",
            )
        incompatible = sorted(set(from_versions) - set(supported))
        if (
            preflight != "PASS"
            or disabled
            or failed
            or not rollback_ready
            or incompatible
        ):
            add_finding(
                findings,
                "COHORT_PREFLIGHT_FAILED",
                f"cohort.{name}",
                "cohort has failed, disabled, incompatible, or rollback-unready instances",
                "observed",
            )
        cohort_summary.append(
            {
                "name": name,
                "channel": channel,
                "consumer_count": consumer_count,
                "observed_count": observed_count,
                "from_versions": sorted(from_versions),
                "preflight_status": preflight,
                "observed_at": observed_text,
            }
        )
    missing_cohorts = sorted(targeted_channels - cohort_channels)
    if missing_cohorts:
        add_finding(
            findings,
            "COHORT_EVIDENCE_INCOMPLETE",
            "cohorts",
            f"target channels lack a cohort denominator: {', '.join(missing_cohorts)}",
            "missing",
        )
    validate_bound_receipt(
        root.get("cohort_receipt"),
        findings=findings,
        label="cohort_receipt",
        code="COHORT_RECEIPT_UNVERIFIABLE",
        expected_fields={
            "schema_version",
            "source",
            "collected_at",
            "artifact_sha256",
            "cohorts",
            "row_count",
            "truncated",
            "receipt_sha256",
        },
        expected_source=RECEIPT_SOURCES["cohorts"],
        expected_artifact=normalized_package["artifact_sha256"],
        expected_count=sum(item["observed_count"] for item in cohort_summary),
        expected_bindings={"cohorts": cohorts},
        as_of=as_of,
    )

    retirements = require_list(root.get("retirements"), "retirements")
    retirement_summary: list[dict[str, Any]] = []
    for index, retirement_value in enumerate(retirements):
        retirement = require_object(retirement_value, f"retirements[{index}]")
        if set(retirement) != {
            "channel",
            "version",
            "state",
            "consumers_remaining",
            "running_code_remaining",
            "observed_at",
        }:
            raise ValueError(f"retirements[{index}] contains unexpected fields")
        channel = require_string(
            retirement.get("channel"), f"retirements[{index}].channel"
        ).upper()
        if channel not in CHANNELS:
            raise ValueError(f"unknown retirement channel {channel!r}")
        version = require_string(
            retirement.get("version"), f"retirements[{index}].version"
        )
        state = require_string(
            retirement.get("state"), f"retirements[{index}].state"
        ).upper()
        if state not in RETIREMENT_STATES:
            raise ValueError(f"unknown retirement state {state!r}")
        consumers = require_int(
            retirement.get("consumers_remaining"),
            f"retirements[{index}].consumers_remaining",
        )
        running = require_int(
            retirement.get("running_code_remaining"),
            f"retirements[{index}].running_code_remaining",
        )
        observed_text = require_string(
            retirement.get("observed_at"), f"retirements[{index}].observed_at"
        )
        observed = parse_timestamp(observed_text, f"retirements[{index}].observed_at")
        stale(observed, as_of, 60, findings, f"retirement.{channel}.{version}")
        if state != "COMPLETE" or consumers != 0 or running != 0:
            add_finding(
                findings,
                "RETIREMENT_ASYNCHRONOUS_PENDING",
                f"retirement.{channel}.{version}",
                "old version removal is not complete for every consumer and running statement",
                "observed",
            )
        retirement_summary.append(
            {
                "channel": channel,
                "version": version,
                "state": state,
                "consumers_remaining": consumers,
                "running_code_remaining": running,
                "observed_at": observed_text,
            }
        )
    validate_bound_receipt(
        root.get("retirement_receipt"),
        findings=findings,
        label="retirement_receipt",
        code="RETIREMENT_RECEIPT_UNVERIFIABLE",
        expected_fields={
            "schema_version",
            "source",
            "collected_at",
            "artifact_sha256",
            "retirements",
            "row_count",
            "truncated",
            "receipt_sha256",
        },
        expected_source=RECEIPT_SOURCES["retirements"],
        expected_artifact=normalized_package["artifact_sha256"],
        expected_count=len(retirements),
        expected_bindings={"retirements": retirements},
        as_of=as_of,
    )

    rollback = require_object(root.get("rollback"), "rollback")
    rollback_owner = require_string(rollback.get("owner"), "rollback.owner")
    rollback_target = require_string(
        rollback.get("target_version"), "rollback.target_version"
    )
    rollback_artifact = require_hash(
        rollback.get("target_artifact_sha256"), "rollback.target_artifact_sha256"
    )
    rollback_baseline = require_hash(
        rollback.get("baseline_sha256"), "rollback.baseline_sha256"
    )
    dry_run_status = require_string(
        rollback.get("dry_run_status"), "rollback.dry_run_status"
    ).upper()
    tested_text = require_string(rollback.get("tested_at"), "rollback.tested_at")
    tested_at = parse_timestamp(tested_text, "rollback.tested_at")
    stale(tested_at, as_of, 60, findings, "rollback")
    halt_plan = require_string(
        rollback.get("cohort_halt_plan"), "rollback.cohort_halt_plan"
    )
    stop_conditions = [
        require_string(item, "rollback.stop_conditions[]")
        for item in require_list(
            rollback.get("stop_conditions"), "rollback.stop_conditions"
        )
    ]
    observables = unique_named(rollback.get("observables"), "rollback.observables")
    normalized_observables: list[dict[str, Any]] = []
    for index, observable in enumerate(observables):
        if set(observable) != {"name", "source", "threshold", "window_minutes"}:
            raise ValueError(
                f"rollback.observables[{index}] contains unexpected fields"
            )
        normalized_observables.append(
            {
                "name": observable["name"],
                "source": require_string(
                    observable.get("source"), f"rollback.observables[{index}].source"
                ),
                "threshold": require_string(
                    observable.get("threshold"),
                    f"rollback.observables[{index}].threshold",
                ),
                "window_minutes": require_int(
                    observable.get("window_minutes"),
                    f"rollback.observables[{index}].window_minutes",
                    1,
                ),
            }
        )
    observable_names = {item["name"] for item in normalized_observables}
    application_specific = observable_names - REQUIRED_ROLLBACK_OBSERVABLES
    validate_bound_receipt(
        rollback,
        findings=findings,
        label="rollback",
        code="ROLLBACK_RECEIPT_UNVERIFIABLE",
        expected_fields={
            "schema_version",
            "source",
            "collected_at",
            "artifact_sha256",
            "owner",
            "target_version",
            "target_artifact_sha256",
            "baseline_sha256",
            "dry_run_status",
            "tested_at",
            "cohort_halt_plan",
            "stop_conditions",
            "observables",
            "row_count",
            "truncated",
            "receipt_sha256",
        },
        expected_source=RECEIPT_SOURCES["rollback"],
        expected_artifact=normalized_package["artifact_sha256"],
        expected_count=len(observables),
        expected_bindings={
            "owner": rollback_owner,
            "target_version": rollback_target,
            "target_artifact_sha256": rollback_artifact,
            "baseline_sha256": rollback_baseline,
            "dry_run_status": dry_run_status,
            "tested_at": tested_text,
            "cohort_halt_plan": halt_plan,
            "stop_conditions": rollback.get("stop_conditions"),
            "observables": rollback.get("observables"),
        },
        as_of=as_of,
    )
    rollback_complete = (
        dry_run_status == "PASS"
        and bool(stop_conditions)
        and REQUIRED_ROLLBACK_OBSERVABLES <= observable_names
        and bool(application_specific)
        and rollback_target == previous_version
        and bool(halt_plan)
    )
    if not rollback_complete:
        add_finding(
            findings,
            "ROLLBACK_PACKET_INCOMPLETE",
            "rollback",
            "rollback packet lacks a passing dry run, prior target, stop conditions, or required observables",
            "observed",
        )

    findings.sort(
        key=lambda row: (row["severity"], row["code"], row["surface"], row["message"])
    )
    gate = "BLOCKED" if findings else "READY_FOR_EXPLICIT_APPROVAL"
    remediation = [
        {
            "code": finding["code"],
            "surface": finding["surface"],
            "required_evidence": finding["next_read_only_check"],
        }
        for finding in findings
    ]
    report: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "as_of": as_of_text,
        "gate": gate,
        "package": normalized_package,
        "source_review": source_review,
        "manifest_delta": {
            "manifest_version": {
                "previous": previous_manifest["manifest_version"],
                "candidate": candidate_manifest["manifest_version"],
            },
            "privileges": privilege_delta,
            "references": reference_delta,
            "app_specs": app_spec_delta,
        },
        "setup_script": {
            "path": setup_path,
            "sha256": setup_hash,
            "statement_count": len(statements),
            "restart_from_beginning_tested": setup.get("restart_from_beginning_tested"),
            "repeat_run_tested": setup.get("repeat_run_tested"),
        },
        "security_scan": {
            "review_status": scan_status,
            "observed_at": scan_time_text,
            "scan_required_for_targets": scan_required,
            "qa_alone_does_not_initiate_scan": targeted_channels == {"QA"},
        },
        "channels": sorted(channel_summary, key=lambda row: row["name"]),
        "cohorts": sorted(cohort_summary, key=lambda row: row["name"]),
        "retirements": sorted(
            retirement_summary, key=lambda row: (row["channel"], row["version"])
        ),
        "compatibility": {
            "previous_version": previous_version,
            "supported_upgrade_from": sorted(supported),
            "contract_test_count": len(contract_tests),
            "state_change": state_change,
        },
        "findings": findings,
        "dry_run_packet": {
            "mode": "READ_ONLY_DRY_RUN",
            "decision": gate,
            "remediation": remediation,
            "rollback": {
                "owner": rollback_owner,
                "target_version": rollback_target,
                "target_artifact_sha256": rollback_artifact,
                "baseline_sha256": rollback_baseline,
                "dry_run_status": dry_run_status,
                "tested_at": tested_text,
                "cohort_halt_plan": halt_plan,
                "stop_conditions": stop_conditions,
                "observables": sorted(
                    normalized_observables, key=lambda row: row["name"]
                ),
            },
            "approval_boundary": "A named operator must separately approve and execute every release or recovery mutation.",
            "prohibited_actions": [
                "register or deregister a version",
                "add or drop a version from a channel",
                "set a release directive or publish a listing",
                "upgrade an installed application",
                "grant or revoke a privilege or role",
                "execute a setup script or mutating SQL",
            ],
        },
        "non_claims": [
            "No Snowflake command or network call was executed.",
            "No version was registered, published, upgraded, dropped, or deregistered.",
            "No privilege, role, release directive, listing, or App Spec was changed.",
            "READY_FOR_EXPLICIT_APPROVAL is a preflight result, not release authorization.",
        ],
    }
    report["receipt_sha256"] = receipt_hash(report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="redacted release evidence JSON")
    parser.add_argument("--output", help="write report JSON instead of stdout")
    args = parser.parse_args()
    try:
        data = json.loads(Path(args.input).read_text(encoding="utf-8"))
        report = analyze(data)
        rendered = (
            json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        )
        if args.output:
            Path(args.output).write_text(rendered, encoding="utf-8")
        else:
            sys.stdout.write(rendered)
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
