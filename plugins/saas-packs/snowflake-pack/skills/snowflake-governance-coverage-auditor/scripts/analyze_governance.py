#!/usr/bin/env python3
"""Deterministically assess trusted, hash-only Snowflake governance evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

VERSION = "1.0.0"
SQL_DIR = Path(__file__).resolve().parent / "sql"
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")

RECEIPT_NON_CLAIMS = [
    "No Snowflake mutation was executed by the reviewed collector SQL.",
    "Missing rows or permission-blocked views do not prove health.",
    "Account Usage evidence can lag and must not be treated as real-time state.",
    "The selected domain skill must evaluate freshness and completeness.",
    "A row count at the reviewed SQL limit may indicate truncated evidence.",
    "The embedded receipt SHA-256 is a self-checksum, not proof of origin or authenticity.",
    "The collector does not attest to operations performed elsewhere in the surrounding session or workflow.",
]
CONTROL_KINDS = {
    "MASKING_POLICY",
    "ROW_ACCESS_POLICY",
    "PROJECTION_POLICY",
    "JOIN_POLICY",
    "AGGREGATION_POLICY",
}
POLICY_KINDS = CONTROL_KINDS | {"PRIVACY_POLICY"}
TAG_PREVIEW_KINDS = {
    "ROW_ACCESS_POLICY",
    "PROJECTION_POLICY",
    "JOIN_POLICY",
    "AGGREGATION_POLICY",
}
OUTCOME_BY_KIND = {
    "MASKING_POLICY": "MASKED",
    "ROW_ACCESS_POLICY": "FILTERED",
    "PROJECTION_POLICY": "PROJECTION_RESTRICTED",
    "JOIN_POLICY": "JOIN_RESTRICTED",
    "AGGREGATION_POLICY": "AGGREGATED",
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
COMMON_CONTEXT_FIELDS = {
    "observed_at",
    "organization_name_sha256",
    "account_identifier_sha256",
    "collector_user_sha256",
    "primary_role_sha256",
    "primary_role_type",
    "secondary_roles_sha256",
    "timezone",
    "source_row_count",
    "source_row_limit",
    "truncation_possible",
}
SURFACES = {
    "governance-classification-current": {
        "template": "governance-classification-current.sql",
        "sources": ["SNOWFLAKE.ACCOUNT_USAGE.DATA_CLASSIFICATION_LATEST"],
        "datasets": {"classification_latest", "execution_context"},
        "data": "classification_latest",
        "selector": "selected_database_key_sha256",
        "selector_domain": False,
    },
    "governance-policies-current": {
        "template": "governance-policies-current.sql",
        "sources": ["INFORMATION_SCHEMA.POLICY_REFERENCES"],
        "datasets": {"execution_context", "policy_references"},
        "data": "policy_references",
        "selector": "selected_object_key_sha256",
        "selector_domain": True,
    },
    "governance-tags-current": {
        "template": "governance-tags-current.sql",
        "sources": ["INFORMATION_SCHEMA.TAG_REFERENCES", "INFORMATION_SCHEMA.TAG_REFERENCES_ALL_COLUMNS"],
        "datasets": {"execution_context", "tag_references"},
        "data": "tag_references",
        "selector": "selected_object_key_sha256",
        "selector_domain": True,
    },
}
CLASSIFICATION_FIELDS = {
    "database_key_sha256",
    "object_key_sha256",
    "classification_status",
    "trigger_type",
    "last_classified_on",
    "last_attempt_on",
    "error_present",
}
TAG_FIELDS = {
    "object_key_sha256",
    "asset_key_sha256",
    "asset_domain",
    "tag_key_sha256",
    "tag_binding_sha256",
    "apply_method",
}
POLICY_ROW_FIELDS = {
    "object_key_sha256",
    "asset_key_sha256",
    "asset_domain",
    "policy_key_sha256",
    "policy_kind",
    "assignment",
    "tag_key_sha256",
    "policy_status",
    "entity_key_set_sha256",
}
POLICY_FIELDS = {
    "schema_version",
    "analysis_as_of_utc",
    "organization_name_sha256",
    "account_identifier_sha256",
    "account_edition",
    "receipt_max_age_seconds",
    "classification_max_age_seconds",
    "preview_features_enabled",
    "assets_expected_count",
    "assets_sha256",
    "assets",
    "scenarios_expected_count",
    "scenarios_sha256",
    "scenarios",
}
ASSET_FIELDS = {
    "asset_key_sha256",
    "object_key_sha256",
    "database_key_sha256",
    "asset_domain",
    "object_domain",
    "require_classification",
    "required_tag_keys_sha256",
    "required_tag_bindings_sha256",
    "required_controls",
    "scenario_keys_sha256",
}
SCENARIO_FIELDS = {
    "scenario_key_sha256",
    "asset_key_sha256",
    "control_kind",
    "context_sha256",
    "query_shape_sha256",
    "expected_outcome",
}
SCOPE_FIELDS = {
    "schema_version",
    "organization_name_sha256",
    "account_identifier_sha256",
    "collector_user_sha256",
    "primary_role_sha256",
    "primary_role_type",
    "secondary_roles_sha256",
    "object_keys_sha256",
    "database_keys_sha256",
    "policy_kinds_visible",
    "object_visibility_verified",
    "tag_visibility_verified",
    "classification_visibility_verified",
    "classification_profile_scope_verified",
    "classification_profiles",
    "verified_at",
    "source",
    "receipt_sha256",
}
SIMULATION_FIELDS = {
    "schema_version",
    "scenario_key_sha256",
    "asset_key_sha256",
    "object_key_sha256",
    "control_kind",
    "context_sha256",
    "query_shape_sha256",
    "expected_outcome",
    "outcome_status",
    "simulated_at",
    "organization_name_sha256",
    "account_identifier_sha256",
    "collector_user_sha256",
    "primary_role_sha256",
    "primary_role_type",
    "secondary_roles_sha256",
    "source",
    "collection_mode",
    "receipt_sha256",
}


class EvidenceError(ValueError):
    """Invalid trusted input; messages are intentionally generic."""


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def digest(value: Any) -> str:
    return f"sha256:{hashlib.sha256(canonical_json(value)).hexdigest()}"


def parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return result.astimezone(timezone.utc) if result.tzinfo else None


def hex64(value: Any, nullable: bool = False) -> bool:
    return (nullable and value is None) or isinstance(value, str) and bool(HEX64_RE.fullmatch(value))


def self_sealed(value: dict[str, Any]) -> bool:
    claimed = value.get("receipt_sha256")
    body = dict(value)
    body.pop("receipt_sha256", None)
    return isinstance(claimed, str) and claimed == digest(body)


def canonical_input_digest(data: dict[str, Any]) -> str:
    if not isinstance(data, dict):
        raise EvidenceError("invalid input")
    return digest(
        {
            "schema_version": data.get("schema_version"),
            "collector_receipts": data.get("collector_receipts"),
            "scope_receipt": data.get("scope_receipt"),
            "simulation_receipts": data.get("simulation_receipts"),
        }
    )


def canonical_policy_digest(data: dict[str, Any]) -> str:
    if not isinstance(data, dict) or not isinstance(data.get("policy"), dict):
        raise EvidenceError("invalid policy")
    validate_policy(data["policy"])
    return digest(data["policy"])


def validate_policy(policy: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not isinstance(policy, dict) or set(policy) != POLICY_FIELDS or policy.get("schema_version") != "1":
        raise EvidenceError("invalid policy")
    if parse_time(policy.get("analysis_as_of_utc")) is None:
        raise EvidenceError("invalid policy")
    for field in ("organization_name_sha256", "account_identifier_sha256"):
        if not hex64(policy.get(field)):
            raise EvidenceError("invalid policy")
    if policy.get("account_edition") not in {"STANDARD", "ENTERPRISE", "BUSINESS_CRITICAL", "VPS"}:
        raise EvidenceError("invalid policy")
    if type(policy.get("receipt_max_age_seconds")) is not int or not 1 <= policy["receipt_max_age_seconds"] <= 900:
        raise EvidenceError("invalid policy")
    if (
        type(policy.get("classification_max_age_seconds")) is not int
        or not 1 <= policy["classification_max_age_seconds"] <= 2_592_000
    ):
        raise EvidenceError("invalid policy")
    previews = policy.get("preview_features_enabled")
    if (
        not isinstance(previews, list)
        or len(previews) != len(set(previews))
        or any(item not in TAG_PREVIEW_KINDS for item in previews)
    ):
        raise EvidenceError("invalid policy")
    assets = policy.get("assets")
    scenarios = policy.get("scenarios")
    if not isinstance(assets, list) or not isinstance(scenarios, list):
        raise EvidenceError("invalid policy")
    if (
        type(policy.get("assets_expected_count")) is not int
        or policy["assets_expected_count"] != len(assets)
        or not assets
    ):
        raise EvidenceError("invalid policy")
    if type(policy.get("scenarios_expected_count")) is not int or policy["scenarios_expected_count"] != len(scenarios):
        raise EvidenceError("invalid policy")
    if policy.get("assets_sha256") != digest(assets) or policy.get("scenarios_sha256") != digest(scenarios):
        raise EvidenceError("invalid policy")
    asset_keys: set[str] = set()
    object_to_database: dict[str, str] = {}
    for row in assets:
        if not isinstance(row, dict) or set(row) != ASSET_FIELDS:
            raise EvidenceError("invalid policy")
        if any(not hex64(row.get(field)) for field in ("asset_key_sha256", "object_key_sha256", "database_key_sha256")):
            raise EvidenceError("invalid policy")
        if (
            row["asset_key_sha256"] in asset_keys
            or row.get("asset_domain") not in {"COLUMN", "TABLE", "VIEW"}
            or row.get("object_domain") not in {"TABLE", "VIEW"}
        ):
            raise EvidenceError("invalid policy")
        if type(row.get("require_classification")) is not bool:
            raise EvidenceError("invalid policy")
        for field in ("required_tag_keys_sha256", "required_tag_bindings_sha256", "scenario_keys_sha256"):
            values = row.get(field)
            if not isinstance(values, list) or values != sorted(set(values)) or any(not hex64(v) for v in values):
                raise EvidenceError("invalid policy")
        controls = row.get("required_controls")
        if (
            not isinstance(controls, list)
            or controls != sorted(set(controls))
            or any(v not in CONTROL_KINDS for v in controls)
        ):
            raise EvidenceError("invalid policy")
        if row["asset_domain"] != "COLUMN" and any(v in controls for v in {"MASKING_POLICY", "PROJECTION_POLICY"}):
            raise EvidenceError("invalid policy")
        if row["asset_domain"] == "COLUMN" and any(
            v in controls for v in {"ROW_ACCESS_POLICY", "JOIN_POLICY", "AGGREGATION_POLICY"}
        ):
            raise EvidenceError("invalid policy")
        previous_db = object_to_database.setdefault(row["object_key_sha256"], row["database_key_sha256"])
        if previous_db != row["database_key_sha256"]:
            raise EvidenceError("invalid policy")
        asset_keys.add(row["asset_key_sha256"])
    scenario_keys: set[str] = set()
    scenarios_by_asset: dict[str, set[str]] = {key: set() for key in asset_keys}
    asset_by_key = {row["asset_key_sha256"]: row for row in assets}
    for row in scenarios:
        if not isinstance(row, dict) or set(row) != SCENARIO_FIELDS:
            raise EvidenceError("invalid policy")
        if any(
            not hex64(row.get(field))
            for field in ("scenario_key_sha256", "asset_key_sha256", "context_sha256", "query_shape_sha256")
        ):
            raise EvidenceError("invalid policy")
        if row["scenario_key_sha256"] in scenario_keys or row["asset_key_sha256"] not in asset_keys:
            raise EvidenceError("invalid policy")
        if (
            row.get("control_kind") not in CONTROL_KINDS
            or row.get("expected_outcome") != OUTCOME_BY_KIND[row["control_kind"]]
        ):
            raise EvidenceError("invalid policy")
        if row["control_kind"] not in asset_by_key[row["asset_key_sha256"]]["required_controls"]:
            raise EvidenceError("invalid policy")
        scenario_keys.add(row["scenario_key_sha256"])
        scenarios_by_asset[row["asset_key_sha256"]].add(row["scenario_key_sha256"])
    for asset in assets:
        if set(asset["scenario_keys_sha256"]) != scenarios_by_asset[asset["asset_key_sha256"]]:
            raise EvidenceError("invalid policy")
        scenario_kinds = {
            row["control_kind"] for row in scenarios if row["asset_key_sha256"] == asset["asset_key_sha256"]
        }
        if set(asset["required_controls"]) != scenario_kinds:
            raise EvidenceError("invalid policy")
    return sorted(assets, key=lambda r: r["asset_key_sha256"]), sorted(
        scenarios, key=lambda r: r["scenario_key_sha256"]
    )


def _row_valid(dataset: str, row: Any) -> bool:
    fields = {
        "classification_latest": CLASSIFICATION_FIELDS,
        "tag_references": TAG_FIELDS,
        "policy_references": POLICY_ROW_FIELDS,
    }[dataset]
    if not isinstance(row, dict) or set(row) != fields:
        return False
    hash_fields = [field for field in fields if field.endswith("_sha256")]
    nullable = {"tag_key_sha256", "entity_key_set_sha256"}
    if any(not hex64(row.get(field), field in nullable) for field in hash_fields):
        return False
    if dataset == "classification_latest":
        return (
            row.get("classification_status") in {"CLASSIFIED", "REVIEWED", "PROVIDER_OTHER"}
            and row.get("trigger_type") in {"MANUAL", "AUTO CLASSIFICATION", "PROVIDER_OTHER"}
            and parse_time(row.get("last_classified_on")) is not None
            and parse_time(row.get("last_attempt_on")) is not None
            and type(row.get("error_present")) is bool
        )
    if row.get("asset_domain") not in {"COLUMN", "TABLE", "VIEW"}:
        return False
    if dataset == "tag_references":
        return row.get("apply_method") in {
            "CLASSIFIED",
            "INHERITED",
            "MANUAL",
            "PROPAGATED",
            "LEGACY_UNKNOWN",
            "PROVIDER_OTHER",
        }
    return (
        row.get("policy_kind") in POLICY_KINDS
        and row.get("assignment") in {"DIRECT", "TAG"}
        and isinstance(row.get("policy_status"), str)
        and row["policy_status"]
        in {
            "ACTIVE",
            "MULTIPLE_MASKING_POLICY_ASSIGNED_TO_THE_COLUMN",
            "COLUMN_IS_MISSING_FOR_SECONDARY_ARG",
            "COLUMN_DATATYPE_MISMATCH_FOR_SECONDARY_ARG",
        }
        and ((row["assignment"] == "TAG") == (row.get("tag_key_sha256") is not None))
        and ((row["policy_kind"] == "AGGREGATION_POLICY") == (row.get("entity_key_set_sha256") is not None))
    )


def validate_receipt(
    receipt: Any, evaluated_at: datetime, max_age: int
) -> tuple[str, str, str, dict[str, list[dict[str, Any]]], dict[str, Any]]:
    if not isinstance(receipt, dict) or set(receipt) != RECEIPT_FIELDS or receipt.get("schema_version") != "2":
        raise EvidenceError("invalid evidence")
    surface = receipt.get("surface")
    contract = SURFACES.get(surface)
    if contract is None or receipt.get("status") != "collected" or receipt.get("errors") != []:
        raise EvidenceError("invalid evidence")
    if receipt.get("collection_mode") != "live-cli" or receipt.get("non_claims") != RECEIPT_NON_CLAIMS:
        raise EvidenceError("invalid evidence")
    if (
        receipt.get("snowflake_query_id") is not None
        or receipt.get("snowflake_query_id_status") != "not_exposed_by_snow_cli_json_ext"
    ):
        raise EvidenceError("invalid evidence")
    if not isinstance(receipt.get("connection_profile_sha256"), str) or not SHA256_RE.fullmatch(
        receipt["connection_profile_sha256"]
    ):
        raise EvidenceError("invalid evidence")
    started, completed, collected = map(
        parse_time,
        (receipt.get("collection_started_at"), receipt.get("collection_completed_at"), receipt.get("collected_at")),
    )
    if not started or not completed or not collected or not started <= collected == completed <= evaluated_at:
        raise EvidenceError("invalid evidence")
    if completed - started > timedelta(seconds=130) or evaluated_at - completed > timedelta(seconds=max_age):
        raise EvidenceError("invalid evidence")
    datasets = receipt.get("datasets")
    if (
        not isinstance(datasets, dict)
        or set(datasets) != contract["datasets"]
        or any(not isinstance(v, list) for v in datasets.values())
    ):
        raise EvidenceError("invalid evidence")
    counts = {name: len(rows) for name, rows in datasets.items()}
    if receipt.get("expected_datasets") != sorted(contract["datasets"]) or receipt.get("dataset_row_counts") != counts:
        raise EvidenceError("invalid evidence")
    if type(receipt.get("row_count")) is not int or receipt["row_count"] != sum(counts.values()):
        raise EvidenceError("invalid evidence")
    if (
        receipt.get("row_limit") != 5000
        or receipt.get("cap_scope") != "per_dataset"
        or type(receipt.get("truncation_possible")) is not bool
    ):
        raise EvidenceError("invalid evidence")
    context_rows = datasets.get("execution_context")
    if not isinstance(context_rows, list) or len(context_rows) != 1 or not isinstance(context_rows[0], dict):
        raise EvidenceError("invalid evidence")
    context = context_rows[0]
    expected_context = COMMON_CONTEXT_FIELDS | {contract["selector"]}
    if contract["selector_domain"]:
        expected_context.add("selected_object_domain")
    if surface == "governance-classification-current":
        expected_context.add("provider_latency_seconds")
    if set(context) != expected_context:
        raise EvidenceError("invalid evidence")
    for field in (
        "organization_name_sha256",
        "account_identifier_sha256",
        "collector_user_sha256",
        "primary_role_sha256",
        "secondary_roles_sha256",
        contract["selector"],
    ):
        if not hex64(context.get(field)):
            raise EvidenceError("invalid evidence")
    observed = parse_time(context.get("observed_at"))
    if not observed or not started <= observed <= completed or evaluated_at - observed > timedelta(seconds=max_age):
        raise EvidenceError("invalid evidence")
    if context.get("timezone") != "UTC" or context.get("primary_role_type") not in {"ROLE", "APPLICATION_INSTANCE"}:
        raise EvidenceError("invalid evidence")
    if (
        context.get("source_row_limit") != 5000
        or type(context.get("source_row_count")) is not int
        or context["source_row_count"] < 0
    ):
        raise EvidenceError("invalid evidence")
    capped = context["source_row_count"] >= 5000
    if capped or context.get("truncation_possible") is not capped or receipt["truncation_possible"] is not capped:
        raise EvidenceError("invalid evidence")
    if surface == "governance-classification-current" and context.get("provider_latency_seconds") != 10800:
        raise EvidenceError("invalid evidence")
    if contract["selector_domain"] and context.get("selected_object_domain") not in {"TABLE", "VIEW"}:
        raise EvidenceError("invalid evidence")
    metadata = receipt.get("source_metadata")
    binding = {contract["selector"]: context[contract["selector"]]}
    if contract["selector_domain"]:
        binding["selected_object_domain"] = context["selected_object_domain"]
    if not isinstance(metadata, dict) or set(metadata) != {
        "template",
        "source_views",
        "selector",
        "selector_binding",
        "rendered_sql_contract",
    }:
        raise EvidenceError("invalid evidence")
    selector_names = (
        {"governance_database"}
        if surface == "governance-classification-current"
        else {"governance_object", "governance_domain"}
    )
    if (
        metadata.get("template") != contract["template"]
        or metadata.get("source_views") != contract["sources"]
        or metadata.get("selector") != {name: True for name in selector_names}
        or metadata.get("selector_binding") != binding
        or metadata.get("rendered_sql_contract") != "privacy-bound-selector-v1"
        or receipt.get("selector_fingerprint") != digest(binding)
        or receipt.get("source_views") != contract["sources"]
    ):
        raise EvidenceError("invalid evidence")
    path = SQL_DIR / contract["template"]
    if not path.is_file():
        raise EvidenceError("invalid evidence")
    template = path.read_text()
    template_hash = f"sha256:{hashlib.sha256(template.encode()).hexdigest()}"
    rendered = template
    selected = context[contract["selector"]]
    if surface == "governance-classification-current":
        rendered = rendered.replace(
            "__GOVERNANCE_DATABASE_IDENTIFIER__", f"__GOVERNANCE_DATABASE_KEY_SHA256_{selected}__"
        )
    else:
        rendered = rendered.replace("__GOVERNANCE_OBJECT_IDENTIFIER__", f"__GOVERNANCE_OBJECT_KEY_SHA256_{selected}__")
        rendered = rendered.replace(
            "__GOVERNANCE_DOMAIN__", f"__GOVERNANCE_DOMAIN_{context['selected_object_domain']}__"
        )
        rendered = rendered.replace(
            "__GOVERNANCE_OBJECT_DATABASE_IDENTIFIER__",
            f"__GOVERNANCE_DATABASE_BOUND_TO_OBJECT_KEY_SHA256_{selected}__",
        )
    if receipt.get("sql_sha256") != template_hash or receipt.get("template_sha256") != template_hash:
        raise EvidenceError("invalid evidence")
    if receipt.get("rendered_sql_sha256") != f"sha256:{hashlib.sha256(rendered.encode()).hexdigest()}":
        raise EvidenceError("invalid evidence")
    if receipt.get("result_sha256") != digest(datasets) or not self_sealed(receipt):
        raise EvidenceError("invalid evidence")
    rows = datasets[contract["data"]]
    if len(rows) != context["source_row_count"] or any(not _row_valid(contract["data"], row) for row in rows):
        raise EvidenceError("invalid evidence")
    keys: set[tuple[Any, ...]] = set()
    for row in rows:
        if surface == "governance-classification-current" and row["database_key_sha256"] != selected:
            raise EvidenceError("invalid evidence")
        if row.get("object_key_sha256") not in {selected} and surface != "governance-classification-current":
            raise EvidenceError("invalid evidence")
        key = tuple(
            row.get(name)
            for name in (
                ("object_key_sha256",)
                if surface == "governance-classification-current"
                else ("asset_key_sha256", "tag_key_sha256", "tag_binding_sha256")
                if surface == "governance-tags-current"
                else (
                    "asset_key_sha256",
                    "policy_kind",
                    "assignment",
                    "policy_key_sha256",
                    "tag_key_sha256",
                    "entity_key_set_sha256",
                )
            )
        )
        if key in keys:
            raise EvidenceError("invalid evidence")
        keys.add(key)
    return surface, selected, context.get("selected_object_domain", "DATABASE"), datasets, context


def validate_attestations(
    data: dict[str, Any],
    policy: dict[str, Any],
    evaluated_at: datetime,
    contexts: list[dict[str, Any]],
    assets: list[dict[str, Any]],
    scenarios: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    scope = data.get("scope_receipt")
    if (
        not isinstance(scope, dict)
        or set(scope) != SCOPE_FIELDS
        or scope.get("schema_version") != "1"
        or not self_sealed(scope)
    ):
        raise EvidenceError("invalid evidence")
    hashes = (
        "organization_name_sha256",
        "account_identifier_sha256",
        "collector_user_sha256",
        "primary_role_sha256",
        "secondary_roles_sha256",
    )
    if any(not hex64(scope.get(field)) for field in hashes):
        raise EvidenceError("invalid evidence")
    common = tuple(contexts[0][field] for field in hashes + ("primary_role_type",))
    if any(tuple(context[field] for field in hashes + ("primary_role_type",)) != common for context in contexts):
        raise EvidenceError("invalid evidence")
    if tuple(scope[field] for field in hashes + ("primary_role_type",)) != common:
        raise EvidenceError("invalid evidence")
    if (
        scope["organization_name_sha256"] != policy["organization_name_sha256"]
        or scope["account_identifier_sha256"] != policy["account_identifier_sha256"]
    ):
        raise EvidenceError("invalid evidence")
    object_keys = sorted({a["object_key_sha256"] for a in assets})
    database_keys = sorted({a["database_key_sha256"] for a in assets})
    if scope.get("object_keys_sha256") != object_keys or scope.get("database_keys_sha256") != database_keys:
        raise EvidenceError("invalid evidence")
    if scope.get("policy_kinds_visible") != sorted(POLICY_KINDS) or any(
        scope.get(field) is not True
        for field in (
            "object_visibility_verified",
            "tag_visibility_verified",
            "classification_visibility_verified",
            "classification_profile_scope_verified",
        )
    ):
        raise EvidenceError("invalid evidence")
    verified = parse_time(scope.get("verified_at"))
    if (
        not verified
        or evaluated_at - verified > timedelta(seconds=policy["receipt_max_age_seconds"])
        or verified > evaluated_at
    ):
        raise EvidenceError("invalid evidence")
    if scope.get("source") != "OWNER_APPROVED_PRIVILEGE_RECONCILIATION":
        raise EvidenceError("invalid evidence")
    profiles = scope.get("classification_profiles")
    if (
        not isinstance(profiles, list)
        or [row.get("database_key_sha256") for row in profiles if isinstance(row, dict)] != database_keys
        or any(
            not isinstance(row, dict)
            or set(row) != {"database_key_sha256", "profile_status"}
            or not hex64(row.get("database_key_sha256"))
            or row.get("profile_status") not in {"ACTIVE", "MISSING", "DISABLED", "UNKNOWN"}
            for row in profiles
        )
    ):
        raise EvidenceError("invalid evidence")
    receipts = data.get("simulation_receipts")
    if not isinstance(receipts, list) or len(receipts) != len(scenarios):
        raise EvidenceError("invalid evidence")
    expected = {row["scenario_key_sha256"]: row for row in scenarios}
    result: dict[str, dict[str, Any]] = {}
    asset_map = {row["asset_key_sha256"]: row for row in assets}
    for receipt in receipts:
        if (
            not isinstance(receipt, dict)
            or set(receipt) != SIMULATION_FIELDS
            or receipt.get("schema_version") != "1"
            or not self_sealed(receipt)
        ):
            raise EvidenceError("invalid evidence")
        scenario = expected.get(receipt.get("scenario_key_sha256"))
        if scenario is None or receipt["scenario_key_sha256"] in result:
            raise EvidenceError("invalid evidence")
        asset = asset_map[scenario["asset_key_sha256"]]
        exact = {
            "asset_key_sha256": scenario["asset_key_sha256"],
            "object_key_sha256": asset["object_key_sha256"],
            "control_kind": scenario["control_kind"],
            "context_sha256": scenario["context_sha256"],
            "query_shape_sha256": scenario["query_shape_sha256"],
            "expected_outcome": scenario["expected_outcome"],
        }
        if any(receipt.get(field) != value for field, value in exact.items()):
            raise EvidenceError("invalid evidence")
        if tuple(receipt[field] for field in hashes + ("primary_role_type",)) != common:
            raise EvidenceError("invalid evidence")
        when = parse_time(receipt.get("simulated_at"))
        if (
            not when
            or when > evaluated_at
            or evaluated_at - when > timedelta(seconds=policy["receipt_max_age_seconds"])
        ):
            raise EvidenceError("invalid evidence")
        if (
            receipt.get("source") != "POLICY_CONTEXT"
            or receipt.get("collection_mode") != "operator-executed-sanitized-receipt"
        ):
            raise EvidenceError("invalid evidence")
        if receipt.get("outcome_status") not in {"MATCHED", "MISMATCH", "ERROR"}:
            raise EvidenceError("invalid evidence")
        result[receipt["scenario_key_sha256"]] = receipt
    return result


def analyze(
    data: Any, *, evaluated_at: datetime, trusted_input_sha256: str, trusted_policy_sha256: str
) -> dict[str, Any]:
    if (
        not isinstance(data, dict)
        or set(data) != {"schema_version", "policy", "collector_receipts", "scope_receipt", "simulation_receipts"}
        or data.get("schema_version") != "2"
    ):
        raise EvidenceError("invalid input")
    if trusted_input_sha256 != canonical_input_digest(data) or trusted_policy_sha256 != canonical_policy_digest(data):
        raise EvidenceError("invalid trust")
    policy = data["policy"]
    assets, scenarios = validate_policy(policy)
    if parse_time(policy["analysis_as_of_utc"]) != evaluated_at:
        raise EvidenceError("invalid policy")
    receipts = data.get("collector_receipts")
    if not isinstance(receipts, list):
        raise EvidenceError("invalid evidence")
    object_map: dict[str, str] = {}
    for asset in assets:
        prior = object_map.setdefault(asset["object_key_sha256"], asset["object_domain"])
        if prior != asset["object_domain"]:
            raise EvidenceError("invalid policy")
    expected_pairs = {
        ("governance-classification-current", key, "DATABASE") for key in {a["database_key_sha256"] for a in assets}
    } | {
        (surface, key, domain)
        for key, domain in object_map.items()
        for surface in ("governance-policies-current", "governance-tags-current")
    }
    if len(receipts) != len(expected_pairs):
        raise EvidenceError("invalid evidence")
    observed: dict[tuple[str, str, str], dict[str, list[dict[str, Any]]]] = {}
    contexts: list[dict[str, Any]] = []
    for receipt in receipts:
        surface, selected, domain, datasets, context = validate_receipt(
            receipt, evaluated_at, policy["receipt_max_age_seconds"]
        )
        key = (surface, selected, domain)
        if key not in expected_pairs or key in observed:
            raise EvidenceError("invalid evidence")
        observed[key] = datasets
        contexts.append(context)
    simulations = validate_attestations(data, policy, evaluated_at, contexts, assets, scenarios)
    classification_rows = [row for value in observed.values() for row in value.get("classification_latest", [])]
    tag_rows = [row for value in observed.values() for row in value.get("tag_references", [])]
    policy_rows = [row for value in observed.values() for row in value.get("policy_references", [])]
    object_databases = {asset["object_key_sha256"]: asset["database_key_sha256"] for asset in assets}
    in_scope_classification_rows = [row for row in classification_rows if row["object_key_sha256"] in object_databases]
    if any(
        object_databases[row["object_key_sha256"]] != row["database_key_sha256"] for row in in_scope_classification_rows
    ) or len({row["object_key_sha256"] for row in in_scope_classification_rows}) != len(in_scope_classification_rows):
        raise EvidenceError("invalid evidence")
    classifications = {row["object_key_sha256"]: row for row in in_scope_classification_rows}
    tags_by_asset: dict[str, list[dict[str, Any]]] = {}
    for row in tag_rows:
        tags_by_asset.setdefault(row["asset_key_sha256"], []).append(row)
    policies_by_scope: dict[str, list[dict[str, Any]]] = {}
    for row in policy_rows:
        policies_by_scope.setdefault(row["asset_key_sha256"], []).append(row)
    findings: list[dict[str, Any]] = []
    precedence_observations: list[dict[str, Any]] = []

    def finding(code: str, scope: str, detail: str, action: str) -> None:
        findings.append({"code": code, "scope_sha256": scope, "detail": detail, "recommended_action": action})

    if policy["account_edition"] == "STANDARD":
        finding(
            "UNSUPPORTED_EDITION",
            policy["account_identifier_sha256"],
            "Enterprise features are required for governed classification coverage.",
            "Verify edition and feature availability before reassessment.",
        )
    for profile in data["scope_receipt"]["classification_profiles"]:
        if profile["profile_status"] != "ACTIVE":
            finding(
                "CLASSIFICATION_PROFILE_NOT_ACTIVE",
                profile["database_key_sha256"],
                "The independently reviewed classification profile is missing, disabled, or unknown.",
                "Review profile attachment and automatic-classification state before reassessment.",
            )
    for asset in assets:
        scope = asset["asset_key_sha256"]
        object_key = asset["object_key_sha256"]
        if asset["require_classification"]:
            row = classifications.get(object_key)
            classified = parse_time(row.get("last_classified_on")) if row else None
            attempted = parse_time(row.get("last_attempt_on")) if row else None
            if not row:
                finding(
                    "CLASSIFICATION_NOT_OBSERVED",
                    scope,
                    "No current classification record matched the governed object.",
                    "Review classification profile attachment and rerun after provider latency.",
                )
            elif (
                row["classification_status"] not in {"CLASSIFIED", "REVIEWED"}
                or row["error_present"]
                or not classified
                or not attempted
                or attempted > classified
            ):
                finding(
                    "CLASSIFICATION_FAILED_OR_NONCURRENT",
                    scope,
                    "The latest classification attempt is failed, incomplete, or not in a reviewed state.",
                    "Resolve the classification attempt or profile state, then recollect.",
                )
            elif evaluated_at - classified > timedelta(seconds=policy["classification_max_age_seconds"] + 10800):
                finding(
                    "CLASSIFICATION_STALE",
                    scope,
                    "The latest successful classification exceeds the owner threshold plus documented provider latency.",
                    "Run or repair classification and recollect after the latency window.",
                )
        current_tags = tags_by_asset.get(scope, [])
        current_tag_keys = {row["tag_key_sha256"] for row in current_tags}
        current_bindings = {row["tag_binding_sha256"] for row in current_tags}
        for required in asset["required_tag_keys_sha256"]:
            if required not in current_tag_keys:
                finding(
                    "TAG_KEY_MISSING",
                    scope,
                    "A required tag key is not present on the governed asset.",
                    "Prepare a separately authorized tag assignment change.",
                )
        for required in asset["required_tag_bindings_sha256"]:
            if required not in current_bindings:
                finding(
                    "TAG_BINDING_MISSING",
                    scope,
                    "A required tag key/value binding is not present, including inherited tags.",
                    "Prepare a separately authorized tag value correction.",
                )
        object_rows = policies_by_scope.get(object_key, [])
        asset_rows = policies_by_scope.get(scope, [])
        relevant = asset_rows + ([] if scope == object_key else object_rows)
        privacy = [
            row for row in object_rows if row["policy_kind"] == "PRIVACY_POLICY" and row["policy_status"] == "ACTIVE"
        ]
        if privacy and any(
            row["policy_kind"] in {"MASKING_POLICY", "AGGREGATION_POLICY", "PROJECTION_POLICY"} for row in relevant
        ):
            finding(
                "UNSUPPORTED_POLICY_COMBINATION",
                scope,
                "Privacy policy interaction can conflict with masking, aggregation, or projection behavior.",
                "Review the combination with POLICY_CONTEXT and a separately authorized design change.",
            )
        for kind in asset["required_controls"]:
            target_rows = asset_rows if kind in {"MASKING_POLICY", "PROJECTION_POLICY"} else object_rows
            candidates = [row for row in target_rows if row["policy_kind"] == kind]
            active = [row for row in candidates if row["policy_status"] == "ACTIVE"]
            direct = [row for row in active if row["assignment"] == "DIRECT"]
            tag = [row for row in active if row["assignment"] == "TAG" and row["tag_key_sha256"] in current_tag_keys]
            effective = direct or tag
            if direct and tag:
                precedence_observations.append({"code": "DIRECT_POLICY_SHADOWS_TAG_POLICY", "scope_sha256": scope})
            if len(direct) > 1 or (kind != "AGGREGATION_POLICY" and len(tag) > 1 and not direct):
                finding(
                    "MULTIPLE_ACTIVE_POLICY_ASSOCIATIONS",
                    scope,
                    "Multiple ACTIVE policy associations leave the required control ambiguous.",
                    "Reconcile assignments through a separately authorized change.",
                )
            if candidates and any(row["policy_status"] != "ACTIVE" for row in candidates):
                finding(
                    "POLICY_NON_ACTIVE",
                    scope,
                    "A relevant policy association has a non-ACTIVE provider status.",
                    "Correct the policy association and secondary argument configuration.",
                )
            if not effective:
                finding(
                    "CONTROL_NOT_EFFECTIVE",
                    scope,
                    "No ACTIVE direct or applicable tag-based association satisfies a required control.",
                    "Prepare a separately authorized policy assignment correction.",
                )
            if not direct and tag and kind in TAG_PREVIEW_KINDS and kind not in policy["preview_features_enabled"]:
                finding(
                    "PREVIEW_FEATURE_UNATTESTED",
                    scope,
                    "A required tag-based control depends on an owner-unattested preview feature.",
                    "Record feature enablement and support posture before reassessment.",
                )
            control_simulations = [
                simulations[key] for key in asset["scenario_keys_sha256"] if simulations[key]["control_kind"] == kind
            ]
            if not control_simulations or any(
                simulation["outcome_status"] != "MATCHED" for simulation in control_simulations
            ):
                finding(
                    "SIMULATION_NOT_MATCHED",
                    scope,
                    "At least one sanitized POLICY_CONTEXT scenario did not match the owner-approved outcome.",
                    "Re-run every exact scenario under its approved role context.",
                )
        aggregation = [
            row
            for row in object_rows
            if row["policy_kind"] == "AGGREGATION_POLICY" and row["policy_status"] == "ACTIVE"
        ]
        direct_entities = {row["entity_key_set_sha256"] for row in aggregation if row["assignment"] == "DIRECT"}
        tag_entities = {row["entity_key_set_sha256"] for row in aggregation if row["assignment"] == "TAG"}
        if direct_entities & tag_entities:
            precedence_observations.append(
                {
                    "code": "AGGREGATION_DIRECT_SHADOWS_SAME_ENTITY_TAG",
                    "scope_sha256": scope,
                }
            )
        if direct_entities and tag_entities - direct_entities:
            precedence_observations.append(
                {
                    "code": "AGGREGATION_DIFFERENT_ENTITY_TAG_REMAINS_CUMULATIVE",
                    "scope_sha256": scope,
                }
            )
    findings.sort(key=lambda row: (row["scope_sha256"], row["code"]))
    bounded = not findings
    remediation = [
        {
            "action_code": row["code"],
            "scope_sha256": row["scope_sha256"],
            "mutation_sql": None,
            "requires_separate_authorization": True,
        }
        for row in findings
    ]
    report: dict[str, Any] = {
        "schema_version": "1",
        "analyzer_version": VERSION,
        "overall_status": "BOUNDED_COVERAGE_OBSERVED" if bounded else "GAPS_OBSERVED",
        "bounded_coverage_claim_supported": bounded,
        "pass_supported": False,
        "evidence_integrity_status": "VALID",
        "evidence_scope_status": "OWNER_ATTESTED_EXACT_DENOMINATOR",
        "classification_time_semantics": "ACCOUNT_USAGE_OBSERVATION_WITH_3H_PROVIDER_LATENCY",
        "evaluated_at": evaluated_at.isoformat().replace("+00:00", "Z"),
        "classification_observed_through_utc": (evaluated_at - timedelta(seconds=10800))
        .isoformat()
        .replace("+00:00", "Z"),
        "assets_evaluated": len(assets),
        "scenarios_evaluated": len(scenarios),
        "findings": findings,
        "precedence_observations": sorted(precedence_observations, key=lambda row: (row["scope_sha256"], row["code"])),
        "dry_run_remediation_packet": remediation,
        "non_claims": [
            "This is not an unqualified PASS, compliance certification, or authorization to mutate Snowflake.",
            "Account Usage classification evidence is latency-bounded observation, not current-state proof.",
            "POLICY_REFERENCES and tag functions are privilege-filtered; completeness depends on the separately trusted scope receipt.",
            "POLICY_CONTEXT is operator-executed, privilege-dependent simulation and does not prove all runtime paths.",
            "Row access policies evaluate before masking policies; projection policies affect final output and do not prevent inner-query or predicate exposure.",
            "No notification, enforcement delivery, customer-row value, raw identifier, policy body, or query text was observed.",
        ],
    }
    report["report_sha256"] = digest(report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", nargs="?", type=Path)
    parser.add_argument("--policy-file", type=Path)
    parser.add_argument("--evaluated-at")
    parser.add_argument("--trusted-input-sha256")
    parser.add_argument("--trusted-policy-sha256")
    parser.add_argument("--print-input-sha256", action="store_true")
    parser.add_argument("--print-policy-sha256", action="store_true")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    try:
        data = json.loads(args.evidence.read_text()) if args.evidence else {}
        if args.policy_file:
            policy = json.loads(args.policy_file.read_text())
            if data and data.get("policy") != policy:
                raise EvidenceError("invalid policy")
            if data:
                data["policy"] = policy
            else:
                data = {"policy": policy}
        if args.print_input_sha256:
            print(canonical_input_digest(data))
            return 0
        if args.print_policy_sha256:
            print(canonical_policy_digest(data))
            return 0
        evaluated_at = parse_time(args.evaluated_at)
        if (
            not evaluated_at
            or not isinstance(args.trusted_input_sha256, str)
            or not isinstance(args.trusted_policy_sha256, str)
        ):
            raise EvidenceError("invalid invocation")
        result = analyze(
            data,
            evaluated_at=evaluated_at,
            trusted_input_sha256=args.trusted_input_sha256,
            trusted_policy_sha256=args.trusted_policy_sha256,
        )
        print(json.dumps(result, indent=2 if args.pretty else None, sort_keys=True))
        return 0
    except (EvidenceError, OSError, json.JSONDecodeError, TypeError, KeyError, OverflowError):
        print("ERROR: invalid governance evidence", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
