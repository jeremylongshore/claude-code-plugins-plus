#!/usr/bin/env python3
"""Fail-closed Snowflake Native App provider release preflight."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

VERSION = "1.0.0"
SQL_DIR = Path(__file__).resolve().parent / "sql"
HEX = re.compile(r"^[0-9a-f]{64}$")
DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$")
VERSION_TOKEN = re.compile(r"^[A-Za-z0-9_.$-]{1,128}$")
MAX_AGE_SECONDS = 900

CONTRACTS = {
    "native-app-versions-current": (
        "native-app-versions-current.sql",
        ["SHOW VERSIONS IN APPLICATION PACKAGE"],
        "versions",
    ),
    "native-app-release-directives-current": (
        "native-app-release-directives-current.sql",
        ["SHOW RELEASE DIRECTIVES IN APPLICATION PACKAGE"],
        "release_directives",
    ),
    "native-app-upgrade-cohorts-current": (
        "native-app-upgrade-cohorts-current.sql",
        ["SNOWFLAKE.DATA_SHARING_USAGE.APPLICATION_STATE"],
        "upgrade_cohorts",
    ),
}
ROW_FIELDS = {
    "versions": {
        "package_key_sha256",
        "version_key_sha256",
        "version",
        "patch",
        "state",
        "review_status",
        "created_on",
        "dropped_on",
    },
    "release_directives": {
        "package_key_sha256",
        "directive_key_sha256",
        "target_type",
        "target_key_sha256",
        "version",
        "patch",
        "release_status",
        "release_channel",
        "upgrade_in_maintenance_window",
        "upgrade_deadline",
        "modified_on",
    },
    "upgrade_cohorts": {
        "package_key_sha256",
        "cohort_key_sha256",
        "current_version",
        "current_patch",
        "previous_version_state",
        "previous_version",
        "previous_patch",
        "upgrade_state",
        "target_version",
        "target_patch",
        "instance_count",
        "latest_state_updated_on",
        "latest_upgrade_attempted_on",
        "maximum_upgrade_attempt",
    },
}
CONTEXT_FIELDS = {
    "observed_at",
    "organization_name_sha256",
    "account_identifier_sha256",
    "collector_user_sha256",
    "primary_role_sha256",
    "primary_role_type",
    "secondary_roles_sha256",
    "timezone",
    "selected_package_key_sha256",
    "source_row_count",
    "source_row_limit",
    "truncation_possible",
    "provider_latency_documented",
}
RECEIPT_FIELDS = {
    "schema_version",
    "surface",
    "status",
    "collected_at",
    "sql_sha256",
    "template_sha256",
    "rendered_sql_sha256",
    "selector_fingerprint",
    "source_metadata",
    "source_views",
    "row_count",
    "row_limit",
    "cap_scope",
    "truncation_possible",
    "dataset_row_counts",
    "expected_datasets",
    "datasets",
    "errors",
    "non_claims",
    "result_sha256",
    "connection_profile_sha256",
    "snowflake_query_id",
    "snowflake_query_id_status",
    "collection_mode",
    "collection_started_at",
    "collection_completed_at",
    "receipt_sha256",
}
BLOCKING_COHORT_STATES = {
    "INSTALL_FAILED",
    "FAILED",
    "QUEUED_DELAYED",
    "QUEUED_RETRY",
    "UPGRADING",
    "INSTALLING",
    "QUEUED",
    "PROVIDER_OTHER",
}
SUPPORTED_PRIMARY_ROLE_TYPES = {"ROLE", "APPLICATION_INSTANCE"}
FORBIDDEN_KEYS = {
    "package_name",
    "application_name",
    "consumer_name",
    "account_name",
    "organization_name",
    "failure_reason",
    "sql_text",
    "manifest_text",
    "setup_text",
}


class Invalid(ValueError):
    pass


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical(value)).hexdigest()


def parse_time(value: Any) -> datetime:
    if not isinstance(value, str) or not UTC.fullmatch(value):
        raise Invalid("INVALID_TIMESTAMP")
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00").astimezone(timezone.utc)
    except ValueError as exc:
        raise Invalid("INVALID_TIMESTAMP") from exc


def exact(value: Any, fields: set[str], code: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != fields:
        raise Invalid(code)
    return value


def require_hex(value: Any, code: str) -> str:
    if not isinstance(value, str) or not HEX.fullmatch(value):
        raise Invalid(code)
    return value


def no_raw_identity(value: Any) -> None:
    if isinstance(value, dict):
        if {str(key).lower() for key in value} & FORBIDDEN_KEYS:
            raise Invalid("RAW_IDENTITY_OR_SOURCE_TEXT")
        for child in value.values():
            no_raw_identity(child)
    elif isinstance(value, list):
        for child in value:
            no_raw_identity(child)


def receipt_self_hash(receipt: dict[str, Any]) -> str:
    body = dict(receipt)
    body.pop("receipt_sha256", None)
    return digest(body)


def validate_receipt(surface: str, receipt: Any, evaluated: datetime, package_key: str) -> list[dict[str, Any]]:
    exact(receipt, RECEIPT_FIELDS, "RECEIPT_FIELDS")
    template, sources, dataset = CONTRACTS[surface]
    if receipt["schema_version"] != "2" or receipt["surface"] != surface or receipt["status"] != "collected":
        raise Invalid("RECEIPT_IDENTITY")
    if receipt["receipt_sha256"] != receipt_self_hash(receipt):
        raise Invalid("RECEIPT_SELF_HASH")
    for key in (
        "sql_sha256",
        "template_sha256",
        "rendered_sql_sha256",
        "selector_fingerprint",
        "result_sha256",
        "connection_profile_sha256",
        "receipt_sha256",
    ):
        if not isinstance(receipt[key], str) or not DIGEST.fullmatch(receipt[key]):
            raise Invalid("RECEIPT_HASH_FORMAT")
    sql_hash = "sha256:" + hashlib.sha256((SQL_DIR / template).read_bytes()).hexdigest()
    if receipt["sql_sha256"] != sql_hash or receipt["template_sha256"] != sql_hash:
        raise Invalid("RECEIPT_TEMPLATE")
    if receipt["source_views"] != sources or receipt["source_metadata"].get("template") != template:
        raise Invalid("RECEIPT_SOURCE")
    if receipt["source_metadata"].get("selector") != {"application_package": True}:
        raise Invalid("SELECTOR_PRESENCE")
    binding = receipt["source_metadata"].get("selector_binding")
    if set(receipt["source_metadata"]) != {
        "template",
        "source_views",
        "selector",
        "selector_binding",
        "rendered_sql_contract",
    }:
        raise Invalid("SOURCE_METADATA_FIELDS")
    if (
        binding != {"selected_package_key_sha256": package_key}
        or receipt["source_metadata"].get("rendered_sql_contract") != "privacy-bound-selector-v1"
    ):
        raise Invalid("SELECTOR_BINDING")
    expected = ["execution_context", dataset]
    if receipt["expected_datasets"] != expected or set(receipt["datasets"]) != set(expected):
        raise Invalid("DATASET_COVERAGE")
    if receipt["dataset_row_counts"] != {key: len(rows) for key, rows in sorted(receipt["datasets"].items())}:
        raise Invalid("DATASET_COUNTS")
    if receipt["result_sha256"] != digest(receipt["datasets"]):
        raise Invalid("RESULT_HASH")
    if (
        receipt["row_limit"] != 5000
        or receipt["cap_scope"] != "per_dataset"
        or receipt["truncation_possible"] is not False
    ):
        raise Invalid("CAPPED_OR_PARTIAL")
    if receipt["row_count"] != sum(len(rows) for rows in receipt["datasets"].values()):
        raise Invalid("RECEIPT_ROW_COUNT")
    if receipt["collection_mode"] != "live-cli" or receipt["errors"]:
        raise Invalid("NOT_LIVE_CLEAN_RECEIPT")
    collected = parse_time(receipt["collected_at"])
    started = parse_time(receipt["collection_started_at"])
    completed = parse_time(receipt["collection_completed_at"])
    if not started <= completed == collected <= evaluated or (evaluated - collected).total_seconds() > MAX_AGE_SECONDS:
        raise Invalid("STALE_OR_INVALID_COLLECTION_INTERVAL")
    contexts = receipt["datasets"]["execution_context"]
    if len(contexts) != 1:
        raise Invalid("EXECUTION_CONTEXT_COUNT")
    context_fields = set(CONTEXT_FIELDS)
    if surface == "native-app-upgrade-cohorts-current":
        context_fields |= {"provider_latency_seconds", "provider_latency_semantics"}
    context = exact(contexts[0], context_fields, "EXECUTION_CONTEXT_FIELDS")
    for key in (
        "organization_name_sha256",
        "account_identifier_sha256",
        "collector_user_sha256",
        "primary_role_sha256",
        "secondary_roles_sha256",
        "selected_package_key_sha256",
    ):
        require_hex(context[key], "EXECUTION_CONTEXT_HASH")
    if context["selected_package_key_sha256"] != package_key or context["timezone"] != "UTC":
        raise Invalid("EXECUTION_CONTEXT_SCOPE")
    if context["primary_role_type"] not in SUPPORTED_PRIMARY_ROLE_TYPES:
        raise Invalid("EXECUTION_CONTEXT_ROLE_TYPE")
    if not isinstance(context["provider_latency_documented"], bool):
        raise Invalid("PROVIDER_LATENCY_TYPE")
    if context["provider_latency_documented"] is not (surface == "native-app-upgrade-cohorts-current"):
        raise Invalid("PROVIDER_LATENCY_CONTRACT")
    if surface == "native-app-upgrade-cohorts-current" and (
        context["provider_latency_seconds"] != 600
        or context["provider_latency_semantics"] != "APPROXIMATE_CURRENT_SNAPSHOT_NOT_SETTLEMENT"
    ):
        raise Invalid("PROVIDER_LATENCY_CONTRACT")
    observed = parse_time(context["observed_at"])
    if observed > collected or (collected - observed).total_seconds() > 120:
        raise Invalid("EXECUTION_CONTEXT_TIME")
    if context["source_row_limit"] != 5000 or context["truncation_possible"] is not False:
        raise Invalid("SOURCE_CAP")
    rows = receipt["datasets"][dataset]
    if (
        not isinstance(context["source_row_count"], int)
        or isinstance(context["source_row_count"], bool)
        or context["source_row_count"] < 0
    ):
        raise Invalid("SOURCE_COUNT")
    if dataset != "upgrade_cohorts" and context["source_row_count"] != len(rows):
        raise Invalid("SOURCE_COUNT")
    if dataset == "upgrade_cohorts" and context["source_row_count"] != sum(
        row.get("instance_count", -1) for row in rows
    ):
        raise Invalid("COHORT_DENOMINATOR")
    for row in rows:
        exact(row, ROW_FIELDS[dataset], "ROW_FIELDS")
        if row["package_key_sha256"] != package_key:
            raise Invalid("ROW_SCOPE")
        require_hex(
            row["version_key_sha256"]
            if dataset == "versions"
            else row["directive_key_sha256"]
            if dataset == "release_directives"
            else row["cohort_key_sha256"],
            "ROW_KEY",
        )
        for key in (
            "patch",
            "current_patch",
            "previous_patch",
            "target_patch",
            "instance_count",
            "maximum_upgrade_attempt",
        ):
            if (
                key in row
                and row[key] is not None
                and (not isinstance(row[key], int) or isinstance(row[key], bool) or row[key] < 0)
            ):
                raise Invalid("ROW_NUMBER_TYPE")
        if dataset == "versions":
            if row["state"] not in {"READY", "DROPPED", "PROVIDER_OTHER"} or row["review_status"] not in {
                "NOT_REVIEWED",
                "IN_PROGRESS",
                "APPROVED",
                "REJECTED",
                "PROVIDER_OTHER",
            }:
                raise Invalid("VERSION_ENUM")
            if (
                not isinstance(row["version"], str)
                or not VERSION_TOKEN.fullmatch(row["version"])
                or row["patch"] is None
            ):
                raise Invalid("VERSION_TYPE")
            created = parse_time(row["created_on"])
            if created > observed:
                raise Invalid("VERSION_TIMESTAMP")
            if row["dropped_on"] is not None:
                dropped = parse_time(row["dropped_on"])
                if dropped < created or dropped > observed:
                    raise Invalid("VERSION_TIMESTAMP")
        elif dataset == "release_directives":
            if (
                row["target_type"] not in {"DEFAULT", "ACCOUNT", "PROVIDER_OTHER"}
                or row["release_status"] not in {"IN_PROGRESS", "HOLDING", "DEPLOYED", "PROVIDER_OTHER"}
                or row["release_channel"] not in {"QA", "ALPHA", "DEFAULT", "PROVIDER_OTHER"}
                or not isinstance(row["upgrade_in_maintenance_window"], bool)
            ):
                raise Invalid("DIRECTIVE_ENUM_OR_TYPE")
            if (
                (row["target_type"] == "DEFAULT" and row["target_key_sha256"] is not None)
                or (row["target_type"] == "ACCOUNT" and not HEX.fullmatch(str(row["target_key_sha256"] or "")))
                or (row["target_key_sha256"] is not None and not HEX.fullmatch(str(row["target_key_sha256"])))
            ):
                raise Invalid("DIRECTIVE_TARGET_TYPE")
            if (
                not isinstance(row["version"], str)
                or not VERSION_TOKEN.fullmatch(row["version"])
                or row["patch"] is None
            ):
                raise Invalid("DIRECTIVE_VERSION_TYPE")
            if row["modified_on"] is not None and parse_time(row["modified_on"]) > observed:
                raise Invalid("DIRECTIVE_TIMESTAMP")
            if row["upgrade_deadline"] is not None:
                parse_time(row["upgrade_deadline"])
        elif (
            row["upgrade_state"]
            not in {
                "INSTALLING",
                "INSTALL_FAILED",
                "COMPLETE",
                "QUEUED",
                "UPGRADING",
                "FAILED",
                "QUEUED_DELAYED",
                "QUEUED_RETRY",
                "DISABLED",
                "PROVIDER_OTHER",
            }
            or row["previous_version_state"] not in {None, "COMPLETE", "FINALIZING", "PROVIDER_OTHER"}
            or row["instance_count"] < 1
        ):
            raise Invalid("COHORT_ENUM_OR_TYPE")
        elif any(
            parse_time(row[key]) > observed
            for key in ("latest_state_updated_on", "latest_upgrade_attempted_on")
            if row[key] is not None
        ):
            raise Invalid("COHORT_TIMESTAMP")
        elif (
            not isinstance(row["current_version"], str)
            or not VERSION_TOKEN.fullmatch(row["current_version"])
            or row["current_patch"] is None
            or (row["previous_version"] is None) != (row["previous_patch"] is None)
            or (row["target_version"] is None) != (row["target_patch"] is None)
            or (
                row["previous_version"] is not None
                and (
                    not isinstance(row["previous_version"], str) or not VERSION_TOKEN.fullmatch(row["previous_version"])
                )
            )
            or (
                row["target_version"] is not None
                and (not isinstance(row["target_version"], str) or not VERSION_TOKEN.fullmatch(row["target_version"]))
            )
        ):
            raise Invalid("COHORT_VERSION_TYPE")
    row_keys = [
        row["version_key_sha256"]
        if dataset == "versions"
        else row["directive_key_sha256"]
        if dataset == "release_directives"
        else row["cohort_key_sha256"]
        for row in rows
    ]
    if len(row_keys) != len(set(row_keys)):
        raise Invalid("DUPLICATE_ROW_KEY")
    if dataset == "versions":
        natural_keys = [(row["version"], row["patch"]) for row in rows]
    elif dataset == "release_directives":
        natural_keys = [
            (
                row["target_type"],
                row["target_key_sha256"],
                row["version"],
                row["patch"],
                row["release_status"],
                row["release_channel"],
                row["upgrade_in_maintenance_window"],
                row["upgrade_deadline"],
                row["modified_on"],
            )
            for row in rows
        ]
    else:
        natural_keys = [
            (
                row["current_version"],
                row["current_patch"],
                row["previous_version_state"],
                row["previous_version"],
                row["previous_patch"],
                row["upgrade_state"],
                row["target_version"],
                row["target_patch"],
            )
            for row in rows
        ]
    if len(natural_keys) != len(set(natural_keys)):
        raise Invalid("DUPLICATE_NATURAL_IDENTITY")
    return rows


def analyze(
    bundle: dict[str, Any],
    evaluated: datetime,
    trusted_manifest: str,
    trusted_setup: str,
    trusted_cohort: str,
    trusted_lifecycle: str,
    trusted_rollback: str,
) -> dict[str, Any]:
    no_raw_identity(bundle)
    exact(bundle, {"schema_version", "release", "receipts", "compatibility", "rollback", "lifecycle"}, "BUNDLE_FIELDS")
    if bundle["schema_version"] != "2":
        raise Invalid("BUNDLE_SCHEMA")
    release = exact(
        bundle["release"],
        {
            "package_key_sha256",
            "distribution",
            "release_channel",
            "target_version",
            "target_patch",
            "manifest_version",
            "manifest_sha256",
            "setup_sha256",
            "expected_setup_statement_count",
            "setup_statements",
            "expected_privilege_delta_count",
            "privilege_deltas",
            "expected_reference_count",
            "references",
            "expected_app_spec_delta_count",
            "app_spec_deltas",
            "release_kind",
            "previous_manifest_version",
            "automated_privileges_changed",
            "expected_cohort_count",
            "expected_installed_instance_count",
        },
        "RELEASE_FIELDS",
    )
    package_key = require_hex(release["package_key_sha256"], "PACKAGE_HASH")
    if release["manifest_sha256"] != trusted_manifest or release["setup_sha256"] != trusted_setup:
        raise Invalid("MANIFEST_OR_SETUP_TRUST")
    for key in (
        "target_patch",
        "manifest_version",
        "previous_manifest_version",
        "expected_setup_statement_count",
        "expected_privilege_delta_count",
        "expected_reference_count",
        "expected_app_spec_delta_count",
        "expected_cohort_count",
        "expected_installed_instance_count",
    ):
        if not isinstance(release[key], int) or isinstance(release[key], bool) or release[key] < 0:
            raise Invalid("RELEASE_NUMBER_TYPE")
    if not isinstance(release["automated_privileges_changed"], bool):
        raise Invalid("RELEASE_BOOLEAN_TYPE")
    if release["manifest_version"] not in {1, 2} or release["previous_manifest_version"] not in {1, 2}:
        raise Invalid("MANIFEST_VERSION")
    if not isinstance(release["target_version"], str) or not VERSION_TOKEN.fullmatch(release["target_version"]):
        raise Invalid("TARGET_VERSION")
    findings: set[str] = set()
    receipts = exact(bundle["receipts"], set(CONTRACTS), "RECEIPT_SET")
    versions = validate_receipt(
        "native-app-versions-current", receipts["native-app-versions-current"], evaluated, package_key
    )
    directives = validate_receipt(
        "native-app-release-directives-current",
        receipts["native-app-release-directives-current"],
        evaluated,
        package_key,
    )
    cohorts = validate_receipt(
        "native-app-upgrade-cohorts-current", receipts["native-app-upgrade-cohorts-current"], evaluated, package_key
    )
    cohort_trust_payload = {
        "expected_cohort_count": release["expected_cohort_count"],
        "expected_installed_instance_count": release["expected_installed_instance_count"],
        "rows": cohorts,
    }
    if digest(cohort_trust_payload) != trusted_cohort:
        raise Invalid("COHORT_TRUST")
    if release["expected_cohort_count"] != len(cohorts) or release["expected_installed_instance_count"] != sum(
        row["instance_count"] for row in cohorts
    ):
        findings.add("COHORT_DENOMINATOR_MISMATCH")
    accounts = {receipts[s]["datasets"]["execution_context"][0]["account_identifier_sha256"] for s in CONTRACTS}
    if len(accounts) != 1:
        raise Invalid("AUTHORIZATION_SCOPE_MISMATCH")

    target = [
        row
        for row in versions
        if row["version"] == release["target_version"] and row["patch"] == release["target_patch"]
    ]
    if len(target) != 1 or target[0]["state"] != "READY":
        findings.add("TARGET_VERSION_NOT_READY")
    elif (
        release["distribution"] == "EXTERNAL"
        and release["release_channel"] in {"ALPHA", "DEFAULT"}
        and target[0]["review_status"] != "APPROVED"
    ):
        findings.add("SECURITY_SCAN_NOT_APPROVED")
    if release["release_channel"] not in {"QA", "ALPHA", "DEFAULT"} or release["distribution"] not in {
        "INTERNAL",
        "EXTERNAL",
    }:
        findings.add("INVALID_RELEASE_POLICY")
    if release["release_kind"] not in {"MAJOR", "PATCH"}:
        findings.add("INVALID_RELEASE_POLICY")
    if release["manifest_version"] != release["previous_manifest_version"] and release["release_kind"] != "MAJOR":
        findings.add("MANIFEST_VERSION_CHANGE_REQUIRES_MAJOR")
    statements = release["setup_statements"]
    if release["expected_setup_statement_count"] != len(statements) or not statements:
        findings.add("SETUP_DENOMINATOR_MISMATCH")
    ordinals = [item.get("ordinal") for item in statements]
    if ordinals != list(range(1, len(statements) + 1)):
        findings.add("SETUP_ORDER_INVALID")
    for item in statements:
        if set(item) != {
            "statement_key_sha256",
            "ordinal",
            "replay_safe",
            "grant_effect",
            "restore_ordinal",
            "forbidden_construct",
        }:
            findings.add("SETUP_STATEMENT_INVALID")
            continue
        if (
            not isinstance(item["ordinal"], int)
            or isinstance(item["ordinal"], bool)
            or not isinstance(item["replay_safe"], bool)
            or not isinstance(item["forbidden_construct"], bool)
            or item["grant_effect"] not in {"NONE", "PRESERVES_GRANTS", "REMOVES_GRANTS"}
            or (
                item["restore_ordinal"] is not None
                and (not isinstance(item["restore_ordinal"], int) or isinstance(item["restore_ordinal"], bool))
            )
            or not HEX.fullmatch(str(item["statement_key_sha256"]))
        ):
            findings.add("SETUP_STATEMENT_INVALID")
        if item["replay_safe"] is not True or item["forbidden_construct"] is not False:
            findings.add("PARTIAL_SETUP_REPLAY_UNSAFE")
        if item["grant_effect"] == "REMOVES_GRANTS" and item["restore_ordinal"] != item["ordinal"] + 1:
            findings.add("PARTIAL_SETUP_GRANT_GAP")

    for count_key, rows_key in (
        ("expected_privilege_delta_count", "privilege_deltas"),
        ("expected_reference_count", "references"),
        ("expected_app_spec_delta_count", "app_spec_deltas"),
    ):
        if release[count_key] != len(release[rows_key]):
            findings.add("RELEASE_DENOMINATOR_MISMATCH")
        keys = [
            row.get("delta_key_sha256") or row.get("reference_key_sha256") or row.get("spec_key_sha256")
            for row in release[rows_key]
        ]
        if any(not isinstance(key, str) or not HEX.fullmatch(key) for key in keys) or len(keys) != len(set(keys)):
            findings.add("RELEASE_ROWS_INVALID_OR_DUPLICATE")
    if any(delta.get("action") == "REMOVE" for delta in release["privilege_deltas"]):
        findings.add("REMOVED_PRIVILEGE")
    if any(
        set(delta)
        != {"delta_key_sha256", "principal_key_sha256", "object_key_sha256", "privilege_sha256", "action", "automated"}
        or delta.get("action") not in {"ADD", "REMOVE"}
        or not isinstance(delta.get("automated"), bool)
        or any(
            not HEX.fullmatch(str(delta.get(key, "")))
            for key in ("delta_key_sha256", "principal_key_sha256", "object_key_sha256")
        )
        or not DIGEST.fullmatch(str(delta.get("privilege_sha256", "")))
        for delta in release["privilege_deltas"]
    ):
        findings.add("PRIVILEGE_DELTA_INVALID")
    automated_privilege_deltas = [
        delta
        for delta in release["privilege_deltas"]
        if delta.get("automated") is True and delta.get("action") in {"ADD", "REMOVE"}
    ]
    if bool(automated_privilege_deltas) != release["automated_privileges_changed"]:
        findings.add("AUTOMATED_PRIVILEGE_CHANGE_CONTRADICTION")
    if release["manifest_version"] == 2 and release["release_kind"] == "PATCH" and automated_privilege_deltas:
        findings.add("V2_AUTOMATED_PRIVILEGE_PATCH_CHANGE")
    if any(
        set(ref) != {"reference_key_sha256", "object_types_sha256", "privileges_sha256", "callback_registered"}
        or ref.get("callback_registered") is not True
        or not DIGEST.fullmatch(str(ref.get("privileges_sha256", "")))
        or not DIGEST.fullmatch(str(ref.get("object_types_sha256", "")))
        for ref in release["references"]
    ):
        findings.add("REFERENCE_CONTRACT_INCOMPLETE")
    if release["app_spec_deltas"] and release["manifest_version"] != 2:
        findings.add("APP_SPEC_REQUIRES_MANIFEST_V2")
    for spec in release["app_spec_deltas"]:
        if (
            set(spec)
            != {
                "spec_key_sha256",
                "change",
                "definition_sha256",
                "current_sequence",
                "target_sequence",
                "status",
                "approval_observed_at",
            }
            or spec.get("change") not in {"ADD", "CHANGE", "REMOVE"}
            or spec.get("status") != "APPROVED"
            or not isinstance(spec.get("current_sequence"), int)
            or isinstance(spec.get("current_sequence"), bool)
            or not isinstance(spec.get("target_sequence"), int)
            or isinstance(spec.get("target_sequence"), bool)
            or spec.get("current_sequence", -1) < 0
            or spec.get("target_sequence", 0) < 1
            or spec.get("target_sequence") < spec.get("current_sequence", 0)
            or (spec.get("change") == "ADD" and (spec.get("current_sequence") != 0 or spec.get("target_sequence") != 1))
            or (spec.get("change") == "CHANGE" and spec.get("target_sequence") != spec.get("current_sequence") + 1)
            or (
                spec.get("change") == "REMOVE"
                and (spec.get("current_sequence", 0) < 1 or spec.get("target_sequence") != spec.get("current_sequence"))
            )
            or not DIGEST.fullmatch(str(spec.get("definition_sha256", "")))
        ):
            findings.add("APP_SPEC_APPROVAL_UNPROVED")
        else:
            try:
                approval_age = (evaluated - parse_time(spec["approval_observed_at"])).total_seconds()
                if approval_age < 0 or approval_age > MAX_AGE_SECONDS:
                    findings.add("APP_SPEC_APPROVAL_UNPROVED")
            except Invalid:
                findings.add("APP_SPEC_APPROVAL_UNPROVED")

    cohort_versions = {(row["current_version"], row["current_patch"]) for row in cohorts}
    compatibility = bundle["compatibility"]
    if (
        not isinstance(compatibility, dict)
        or set(compatibility) != {"expected_count", "rows"}
        or not isinstance(compatibility.get("expected_count"), int)
        or isinstance(compatibility.get("expected_count"), bool)
        or compatibility.get("expected_count", -1) < 0
        or not isinstance(compatibility.get("rows"), list)
        or compatibility["expected_count"] != len(compatibility["rows"])
    ):
        findings.add("COMPATIBILITY_DENOMINATOR_MISMATCH")
        compatibility_rows = []
    else:
        compatibility_rows = compatibility["rows"]
    compatibility_invalid = any(
        not isinstance(row, dict)
        or set(row) != {"from_version", "from_patch", "target_version", "target_patch", "status"}
        or row.get("status") not in {"COMPATIBLE", "INCOMPATIBLE"}
        or any(
            not isinstance(row.get(key), str) or not VERSION_TOKEN.fullmatch(row[key])
            for key in ("from_version", "target_version")
        )
        or any(
            not isinstance(row.get(key), int) or isinstance(row.get(key), bool) or row.get(key) < 0
            for key in ("from_patch", "target_patch")
        )
        for row in compatibility_rows
    )
    if compatibility_invalid:
        findings.add("COMPATIBILITY_ROW_INVALID")
        compatibility_rows = []
    if len(
        {
            (row.get("from_version"), row.get("from_patch"), row.get("target_version"), row.get("target_patch"))
            for row in compatibility_rows
        }
    ) != len(compatibility_rows):
        findings.add("COMPATIBILITY_ROW_DUPLICATE")
    compatible_versions = {
        (row.get("from_version"), row.get("from_patch"))
        for row in compatibility_rows
        if row.get("status") == "COMPATIBLE"
        and row.get("target_version") == release["target_version"]
        and row.get("target_patch") == release["target_patch"]
    }
    if cohort_versions - compatible_versions:
        findings.add("INCOMPATIBLE_OR_UNTESTED_COHORT")
    for row in cohorts:
        if row["upgrade_state"] in BLOCKING_COHORT_STATES or row["previous_version_state"] == "FINALIZING":
            findings.add("UNSAFE_UPGRADE_COHORT")
        if row["target_version"] is not None and (row["target_version"], row["target_patch"]) != (
            release["target_version"],
            release["target_patch"],
        ):
            findings.add("COHORT_TARGET_MISMATCH")

    deployed = [
        row
        for row in directives
        if row["release_channel"] == release["release_channel"]
        and row["version"] == release["target_version"]
        and row["patch"] == release["target_patch"]
    ]
    if not directives:
        findings.add("RELEASE_DIRECTIVE_VISIBILITY_UNPROVED")
    if any(
        row["target_type"] == "PROVIDER_OTHER"
        or row["release_status"] == "PROVIDER_OTHER"
        or row["release_channel"] == "PROVIDER_OTHER"
        for row in directives
    ):
        findings.add("RELEASE_DIRECTIVE_STATE_UNKNOWN")
    if any(row["release_status"] in {"IN_PROGRESS", "HOLDING"} for row in deployed):
        findings.add("DIRECTIVE_NOT_SETTLED")
    rollback = bundle["rollback"]
    rollback_body = dict(rollback) if isinstance(rollback, dict) else {}
    rollback_body.pop("owner_receipt_sha256", None)
    if not isinstance(rollback, dict) or set(rollback) != {
        "previous_version",
        "previous_patch",
        "artifact_sha256",
        "tested",
        "privileges_preserved",
        "app_specs_reconciled",
        "owner_receipt_sha256",
    }:
        findings.add("ROLLBACK_CONTRACT_INVALID")
    elif (
        rollback["tested"] is not True
        or rollback["privileges_preserved"] is not True
        or rollback["app_specs_reconciled"] is not True
        or not isinstance(rollback["previous_patch"], int)
        or isinstance(rollback["previous_patch"], bool)
        or rollback["previous_patch"] < 0
        or not isinstance(rollback["previous_version"], str)
        or not VERSION_TOKEN.fullmatch(rollback["previous_version"])
        or not DIGEST.fullmatch(str(rollback["artifact_sha256"]))
        or not DIGEST.fullmatch(str(rollback["owner_receipt_sha256"]))
        or rollback["owner_receipt_sha256"] != trusted_rollback
        or digest(rollback_body) != trusted_rollback
    ):
        findings.add("ROLLBACK_UNPROVED")
    elif (
        len(
            [
                row
                for row in versions
                if row["version"] == rollback["previous_version"]
                and row["patch"] == rollback["previous_patch"]
                and row["state"] == "READY"
            ]
        )
        != 1
    ):
        findings.add("ROLLBACK_VERSION_NOT_READY")
    lifecycle = bundle["lifecycle"]
    lifecycle_body = dict(lifecycle) if isinstance(lifecycle, dict) else {}
    lifecycle_body.pop("receipt_sha256", None)
    if (
        not isinstance(lifecycle, dict)
        or set(lifecycle) != {"expected_event_count", "events", "receipt_sha256", "observed_at"}
        or not isinstance(lifecycle.get("expected_event_count"), int)
        or isinstance(lifecycle.get("expected_event_count"), bool)
        or not isinstance(lifecycle.get("events"), list)
        or lifecycle["expected_event_count"] != len(lifecycle["events"])
        or lifecycle.get("receipt_sha256") != trusted_lifecycle
        or digest(lifecycle_body) != trusted_lifecycle
    ):
        findings.add("LIFECYCLE_COMPLETENESS_UNPROVED")
    else:
        event_keys: list[str] = []
        event_cohort_keys: set[str] = set()
        visible_versions = {(row["version"], row["patch"]) for row in versions}
        current_cohort_keys = {row["cohort_key_sha256"] for row in cohorts}
        for event in lifecycle["events"]:
            if (
                not isinstance(event, dict)
                or set(event)
                != {
                    "event_key_sha256",
                    "package_key_sha256",
                    "cohort_key_sha256",
                    "version",
                    "patch",
                    "event_type",
                    "observed_at",
                    "outcome",
                }
                or not HEX.fullmatch(str(event.get("event_key_sha256", "")))
                or event.get("package_key_sha256") != package_key
                or not HEX.fullmatch(str(event.get("cohort_key_sha256", "")))
                or not isinstance(event.get("patch"), int)
                or isinstance(event.get("patch"), bool)
                or event.get("patch") < 0
                or not isinstance(event.get("version"), str)
                or not VERSION_TOKEN.fullmatch(event.get("version", ""))
                or (event.get("version"), event.get("patch")) not in visible_versions
                or event.get("event_type") not in {"INSTALL", "UPGRADE", "UNINSTALL"}
                or event.get("outcome") != "SUCCEEDED"
                or (
                    event.get("event_type") != "UNINSTALL" and event.get("cohort_key_sha256") not in current_cohort_keys
                )
            ):
                findings.add("LIFECYCLE_COMPLETENESS_UNPROVED")
                continue
            event_keys.append(event["event_key_sha256"])
            if event["event_type"] in {"INSTALL", "UPGRADE"}:
                event_cohort_keys.add(event["cohort_key_sha256"])
            try:
                event_age = (evaluated - parse_time(event["observed_at"])).total_seconds()
                if event_age < 0 or event_age > MAX_AGE_SECONDS:
                    findings.add("LIFECYCLE_COMPLETENESS_UNPROVED")
            except Invalid:
                findings.add("LIFECYCLE_COMPLETENESS_UNPROVED")
        try:
            lifecycle_age = (evaluated - parse_time(lifecycle["observed_at"])).total_seconds()
            if lifecycle_age < 0 or lifecycle_age > MAX_AGE_SECONDS:
                findings.add("LIFECYCLE_COMPLETENESS_UNPROVED")
        except Invalid:
            findings.add("LIFECYCLE_COMPLETENESS_UNPROVED")
        if len(event_keys) != len(set(event_keys)):
            findings.add("LIFECYCLE_COMPLETENESS_UNPROVED")
        if {row["cohort_key_sha256"] for row in cohorts} - event_cohort_keys:
            findings.add("LIFECYCLE_COMPLETENESS_UNPROVED")

    ordered = sorted(findings)
    status = "READY_FOR_OPERATOR_RELEASE_AS_OF" if not ordered else "BLOCKED"
    report = {
        "schema_version": "2",
        "analyzer_version": VERSION,
        "evaluated_at": evaluated.isoformat().replace("+00:00", "Z"),
        "status": status,
        "findings": ordered,
        "denominators": {
            "versions": len(versions),
            "directives": len(directives),
            "cohort_groups": len(cohorts),
            "installed_instances": sum(row["instance_count"] for row in cohorts),
            "setup_statements": len(statements),
            "privilege_deltas": len(release["privilege_deltas"]),
            "references": len(release["references"]),
            "app_spec_deltas": len(release["app_spec_deltas"]),
            "compatibility_rows": len(compatibility_rows),
            "lifecycle_events": len(lifecycle.get("events", [])) if isinstance(lifecycle, dict) else 0,
        },
        "safe_to_publish": False,
        "safe_to_upgrade": False,
        "dry_run": True,
        "remediation_packet": [{"finding": code, "action": "OWNER_REVIEW_AND_RECOLLECT"} for code in ordered],
        "non_claims": [
            "This preflight does not publish, upgrade, alter, grant, revoke, or approve anything.",
            "READY is an as-of provider evidence result, not consumer approval, installation success, or future upgrade safety.",
            "APPLICATION_STATE is a delayed current snapshot and does not retain uninstalled instances; lifecycle history remains separately trusted evidence.",
            "Manifest-version restrictions beyond documented platform behavior are release policy, not Snowflake facts.",
        ],
    }
    report["report_sha256"] = digest(report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--evaluated-at", required=True)
    parser.add_argument("--trusted-input-sha256", required=True)
    parser.add_argument("--trusted-manifest-sha256", required=True)
    parser.add_argument("--trusted-setup-sha256", required=True)
    parser.add_argument("--trusted-cohort-sha256", required=True)
    parser.add_argument("--trusted-lifecycle-sha256", required=True)
    parser.add_argument("--trusted-rollback-sha256", required=True)
    args = parser.parse_args(argv)
    try:
        payload = args.input.read_bytes()
        if "sha256:" + hashlib.sha256(payload).hexdigest() != args.trusted_input_sha256:
            raise Invalid("INPUT_TRUST")
        if not all(
            DIGEST.fullmatch(value)
            for value in (
                args.trusted_manifest_sha256,
                args.trusted_setup_sha256,
                args.trusted_cohort_sha256,
                args.trusted_lifecycle_sha256,
                args.trusted_rollback_sha256,
            )
        ):
            raise Invalid("TRUST_DIGEST_FORMAT")
        bundle = json.loads(payload)
        report = analyze(
            bundle,
            parse_time(args.evaluated_at),
            args.trusted_manifest_sha256,
            args.trusted_setup_sha256,
            args.trusted_cohort_sha256,
            args.trusted_lifecycle_sha256,
            args.trusted_rollback_sha256,
        )
        print(json.dumps(report, sort_keys=True, indent=2))
        return 0 if report["status"] == "READY_FOR_OPERATOR_RELEASE_AS_OF" else 1
    except (OSError, json.JSONDecodeError, Invalid, KeyError, TypeError, AttributeError):
        print(
            json.dumps(
                {"schema_version": "2", "status": "INVALID_EVIDENCE", "findings": ["EVIDENCE_REJECTED"]}, sort_keys=True
            )
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
