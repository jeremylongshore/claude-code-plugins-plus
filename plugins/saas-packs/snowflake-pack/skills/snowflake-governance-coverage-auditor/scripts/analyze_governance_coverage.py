#!/usr/bin/env python3
"""Deterministic, offline Snowflake governance coverage analyzer.

The input is a sanitized evidence bundle. This program never connects to
Snowflake, renders mutation SQL, or treats a missing metadata row as proof that
an asset is unprotected.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


POLICY_KINDS = {
    "MASKING_POLICY",
    "ROW_ACCESS_POLICY",
    "PROJECTION_POLICY",
    "JOIN_POLICY",
    "AGGREGATION_POLICY",
}
POLICY_STATUSES = {
    "ACTIVE",
    "MULTIPLE_MASKING_POLICY_ASSIGNED_TO_THE_COLUMN",
    "COLUMN_IS_MISSING_FOR_SECONDARY_ARG",
    "COLUMN_DATATYPE_MISMATCH_FOR_SECONDARY_ARG",
}
PREVIEW_TAG_POLICIES = POLICY_KINDS - {"MASKING_POLICY"}
EDITION_RANK = {"STANDARD": 0, "ENTERPRISE": 1, "BUSINESS_CRITICAL": 2, "VPS": 3}
MAX_ASSETS = 10_000
MAX_ROWS = 50_000
SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
OPAQUE_KEY = re.compile(r"^(?:asset|policy|tag|scenario)_[a-z0-9][a-z0-9_-]{0,126}$")
SQL_DIR = Path(__file__).resolve().parent / "sql"
SURFACE_CONTRACTS = {
    "denominator": [("governance-denominator.sql", "SNOWFLAKE.ACCOUNT_USAGE.TABLES+COLUMNS")],
    "tag_references": [("governance-tag-references.sql", "SNOWFLAKE.ACCOUNT_USAGE.TAG_REFERENCES")],
    "policy_references": [
        ("governance-policy-references.sql", "SNOWFLAKE.ACCOUNT_USAGE.POLICY_REFERENCES"),
        ("governance-policy-references-current.sql", "BOUNDED.INFORMATION_SCHEMA.POLICY_REFERENCES"),
    ],
    "classification_latest": [
        ("governance-classification-latest.sql", "SNOWFLAKE.ACCOUNT_USAGE.DATA_CLASSIFICATION_LATEST+TABLES")
    ],
}
POLICY_SOURCE_CAPABILITIES = {
    "SNOWFLAKE.ACCOUNT_USAGE.POLICY_REFERENCES": POLICY_KINDS - {"JOIN_POLICY"},
    "BOUNDED.INFORMATION_SCHEMA.POLICY_REFERENCES": POLICY_KINDS,
}
SECRET_KEYS = (
    "password",
    "passphrase",
    "secret",
    "token",
    "apikey",
    "privatekey",
    "authorization",
    "credential",
)
SECRET_VALUES = (
    re.compile(r"(?i)\b(?:password|secret|token|api[_ -]?key|authorization)\b\s*[:=]\s*\S+"),
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{8,}"),
    re.compile(r"-----BEGIN(?: [A-Z0-9]+)? PRIVATE KEY-----"),
)
FORBIDDEN_EXPORT_KEYS = {
    "database_name",
    "schema_name",
    "table_name",
    "column_name",
    "object_name",
    "tag_value",
    "policy_body",
    "query_text",
    "sql_text",
}


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def _hash(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _upper(value: object) -> str:
    return str(value or "").strip().upper()


def _timestamp(value: object, path: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{path} must be an RFC3339 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(f"{path} must be an RFC3339 timestamp") from error
    if parsed.tzinfo is None:
        raise ValueError(f"{path} must include a timezone")
    return parsed.astimezone(timezone.utc)


def _rows(doc: dict, field: str, *, required: bool = True) -> list[dict]:
    if field not in doc and not required:
        return []
    value = doc.get(field)
    if not isinstance(value, list):
        raise ValueError(f"{field} must be an array")
    if len(value) > (MAX_ASSETS if field == "assets" else MAX_ROWS):
        raise ValueError(f"{field} exceeds the bounded row limit")
    for index, row in enumerate(value):
        if not isinstance(row, dict):
            raise ValueError(f"{field}[{index}] must be an object")
    return value


def _strings(value: object, path: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError(f"{path} must be an array of strings")
    return value


def _opaque(value: object, path: str) -> str:
    key = str(value or "").strip()
    if not OPAQUE_KEY.fullmatch(key):
        raise ValueError(f"{path} must be an opaque key such as asset_42, not an object name")
    return key


def reject_secrets(value: object, path: str = "input") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = "".join(char for char in str(key).casefold() if char.isalnum())
            if any(fragment in normalized for fragment in SECRET_KEYS):
                raise ValueError(f"credential-bearing field is not accepted: {path}.{key}")
            if normalized in {item.replace("_", "") for item in FORBIDDEN_EXPORT_KEYS}:
                raise ValueError(f"raw identity or sensitive metadata field is not accepted: {path}.{key}")
            reject_secrets(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            reject_secrets(child, f"{path}[{index}]")
    elif isinstance(value, str) and any(pattern.search(value) for pattern in SECRET_VALUES):
        raise ValueError(f"credential-shaped value is not accepted: {path}")


def _receipt(name: str, value: object, dataset: list[dict], assessed_at: datetime, max_age_hours: float) -> dict:
    issues: list[str] = []
    if not isinstance(value, dict):
        return {"surface": name, "status": "UNVERIFIABLE", "issues": ["receipt missing"]}
    if value.get("schema_version") != "1":
        issues.append("schema_version is not 1")
    if value.get("surface") != name:
        issues.append("surface mismatch")
    if value.get("status") != "COLLECTED":
        issues.append("status is not COLLECTED")
    if value.get("truncated") is not False:
        issues.append("truncated is not false")
    if value.get("privilege_scope") != "COMPLETE":
        issues.append("privilege scope is not COMPLETE")
    if not isinstance(value.get("row_count"), int) or isinstance(value.get("row_count"), bool) or value["row_count"] < 0:
        issues.append("row_count is invalid")
    elif value["row_count"] != len(dataset):
        issues.append("row_count does not match the bound dataset")
    row_limit = value.get("row_limit")
    raw_row_count = value.get("raw_row_count")
    if not isinstance(row_limit, int) or isinstance(row_limit, bool) or not 1 <= row_limit <= MAX_ASSETS:
        issues.append("row_limit is invalid")
    if not isinstance(raw_row_count, int) or isinstance(raw_row_count, bool) or raw_row_count < len(dataset):
        issues.append("raw_row_count is invalid")
    contract = next((item for item in SURFACE_CONTRACTS[name] if item[1] == value.get("source")), None)
    if contract is None:
        issues.append("source does not match the surface contract")
    else:
        template_hash = f"sha256:{hashlib.sha256((SQL_DIR / contract[0]).read_bytes()).hexdigest()}"
        if value.get("template_sha256") != template_hash:
            issues.append("template_sha256 does not match the bundled template")
    if not SHA256.fullmatch(str(value.get("rendered_sql_sha256") or "")):
        issues.append("rendered_sql_sha256 is missing or malformed")
    if value.get("query_sha256") != value.get("rendered_sql_sha256"):
        issues.append("query_sha256 does not match rendered_sql_sha256")
    expected_dataset_hash = f"sha256:{hashlib.sha256(_canonical(dataset)).hexdigest()}"
    if value.get("dataset_sha256") != expected_dataset_hash:
        issues.append("dataset_sha256 does not match the analyzer rows")
    selector_metadata = value.get("source_metadata")
    selector = selector_metadata.get("selector") if isinstance(selector_metadata, dict) else None
    selector_ok = selector == {"database": True} or (
        isinstance(selector, dict)
        and selector.get("database") is True
        and isinstance(selector.get("objects"), int)
        and not isinstance(selector.get("objects"), bool)
        and selector["objects"] > 0
        and set(selector) == {"database", "objects"}
    )
    if value.get("source") == "BOUNDED.INFORMATION_SCHEMA.POLICY_REFERENCES":
        selector_ok = selector_ok and isinstance(selector, dict) and isinstance(selector.get("objects"), int)
    if not selector_ok:
        issues.append("source_metadata selector is not the privacy-safe database binding")
    elif isinstance(row_limit, int) and isinstance(raw_row_count, int):
        partitions = selector.get("objects", 1)
        if raw_row_count > row_limit * partitions:
            issues.append("raw_row_count exceeds the bounded selector capacity")
    if not SHA256.fullmatch(str(value.get("selector_fingerprint") or "")):
        issues.append("selector_fingerprint is missing or malformed")
    try:
        collected_at = _timestamp(value.get("collected_at"), f"receipts.{name}.collected_at")
        age_hours = (assessed_at - collected_at).total_seconds() / 3600
        if age_hours < 0:
            issues.append("collected_at is in the future")
        elif age_hours > max_age_hours:
            issues.append(f"receipt is stale ({age_hours:.2f}h > {max_age_hours:.2f}h)")
    except ValueError:
        collected_at = None
        age_hours = None
        issues.append("collected_at is invalid")
    body = dict(value)
    supplied = body.pop("receipt_sha256", None)
    expected = f"sha256:{hashlib.sha256(_canonical(body)).hexdigest()}"
    if supplied != expected:
        issues.append("receipt_sha256 is missing or invalid")
    return {
        "surface": name,
        "status": "VERIFIED" if not issues else "UNVERIFIABLE",
        "issues": issues,
        "age_hours": round(age_hours, 3) if age_hours is not None else None,
        "collected_at": collected_at.isoformat().replace("+00:00", "Z") if collected_at else None,
        "source": value.get("source"),
        "template_sha256": value.get("template_sha256"),
        "dataset_sha256": value.get("dataset_sha256"),
        "selector_fingerprint": value.get("selector_fingerprint"),
    }


def _classification_state(row: dict, assessed_at: datetime, max_age_hours: float) -> tuple[str, list[str]]:
    status = _upper(row.get("status"))
    if status not in {"CLASSIFIED", "REVIEWED", "FAILED", "PENDING", "NOT_OBSERVED"}:
        raise ValueError("classification status is invalid")
    issues: list[str] = []
    last_classified = None
    if row.get("last_classified_on"):
        last_classified = _timestamp(row["last_classified_on"], "classifications.last_classified_on")
    last_attempt = None
    if row.get("last_attempt_on"):
        last_attempt = _timestamp(row["last_attempt_on"], "classifications.last_attempt_on")
    if row.get("error_present") not in (True, False, None):
        raise ValueError("classifications.error_present must be boolean")
    if last_attempt and last_classified and last_attempt > last_classified and row.get("error_present") is True:
        status = "FAILED"
        issues.append("last classification attempt failed after the last success")
    if status in {"CLASSIFIED", "REVIEWED"}:
        if last_classified is None:
            status = "NOT_PROVEN"
            issues.append("successful classification timestamp missing")
        else:
            age_hours = (assessed_at - last_classified).total_seconds() / 3600
            if age_hours < 0:
                status = "NOT_PROVEN"
                issues.append("classification timestamp is in the future")
            elif age_hours > max_age_hours:
                status = "STALE"
                issues.append(f"classification is stale ({age_hours:.2f}h > {max_age_hours:.2f}h)")
    return status, issues


def _entity_keys(row: dict) -> tuple[str, ...]:
    values = _strings(row.get("entity_key_hashes", []), "policies.entity_key_hashes")
    normalized = tuple(sorted(set(values)))
    for value in normalized:
        if not SHA256.fullmatch(value):
            raise ValueError("aggregation entity keys must be sha256: hashes")
    return normalized


def _effective_policies(rows: list[dict], kind: str) -> tuple[list[dict], list[dict], list[dict]]:
    active = [row for row in rows if row["policy_status"] == "ACTIVE"]
    direct = [row for row in active if row["assignment"] == "DIRECT"]
    tagged = [row for row in active if row["assignment"] == "TAG"]
    if not direct:
        return tagged, [], []
    if kind != "AGGREGATION_POLICY":
        return direct, tagged, []
    effective = list(direct)
    shadowed: list[dict] = []
    cumulative: list[dict] = []
    direct_keys = {_entity_keys(row) for row in direct}
    for row in tagged:
        if _entity_keys(row) in direct_keys:
            shadowed.append(row)
        else:
            effective.append(row)
            cumulative.append(row)
    return effective, shadowed, cumulative


def analyze(doc: dict) -> dict:
    if not isinstance(doc, dict):
        raise ValueError("input must be a JSON object")
    reject_secrets(doc)
    if doc.get("schema_version") != "1":
        raise ValueError("schema_version must be 1")
    metadata = doc.get("metadata")
    if not isinstance(metadata, dict):
        raise ValueError("metadata must be an object")
    assessed_at = _timestamp(metadata.get("assessed_at"), "metadata.assessed_at")
    edition = _upper(metadata.get("edition"))
    if edition not in EDITION_RANK:
        raise ValueError("metadata.edition must be STANDARD, ENTERPRISE, BUSINESS_CRITICAL, or VPS")
    preview_features = {_upper(item) for item in _strings(metadata.get("preview_features_enabled", []), "metadata.preview_features_enabled")}
    max_age = metadata.get("max_age_hours", {})
    if not isinstance(max_age, dict):
        raise ValueError("metadata.max_age_hours must be an object")
    receipt_max_age = float(max_age.get("evidence", 4))
    classification_max_age = float(max_age.get("classification", 24 * 30))
    if receipt_max_age <= 0 or classification_max_age <= 0:
        raise ValueError("freshness bounds must be positive")

    assets = _rows(doc, "assets")
    tags = _rows(doc, "tags")
    classifications = _rows(doc, "classifications")
    policies = _rows(doc, "policies")
    simulations = _rows(doc, "policy_context", required=False)
    if not assets:
        raise ValueError("assets denominator must not be empty")

    asset_map: dict[str, dict] = {}
    for index, row in enumerate(assets):
        key = _opaque(row.get("asset_key"), f"assets[{index}].asset_key")
        if key in asset_map:
            raise ValueError(f"duplicate asset_key: {key}")
        domain = _upper(row.get("domain"))
        if domain not in {"COLUMN", "TABLE", "VIEW"}:
            raise ValueError(f"assets[{index}].domain is invalid")
        required = {_upper(item) for item in _strings(row.get("required_controls", []), f"assets[{index}].required_controls")}
        unknown = required - POLICY_KINDS
        if unknown:
            raise ValueError(f"assets[{index}] has unsupported controls: {sorted(unknown)}")
        if not isinstance(row.get("require_tag"), bool) or not isinstance(row.get("require_classification"), bool):
            raise ValueError(f"assets[{index}] tag/classification requirements must be boolean")
        asset_map[key] = {
            "asset_key": key,
            "domain": domain,
            "require_tag": row.get("require_tag") is True,
            "require_classification": row.get("require_classification") is True,
            "required_controls": sorted(required),
        }

    tags_by_asset: dict[str, list[dict]] = defaultdict(list)
    for index, row in enumerate(tags):
        key = _opaque(row.get("asset_key"), f"tags[{index}].asset_key")
        if key not in asset_map:
            raise ValueError(f"tags[{index}] references an asset outside the denominator")
        tag_key = _opaque(row.get("tag_key"), f"tags[{index}].tag_key")
        method = _upper(row.get("apply_method"))
        if method not in {"CLASSIFIED", "MANUAL", "PROPAGATED", "INHERITED", "LEGACY"}:
            raise ValueError(f"tags[{index}].apply_method is invalid")
        tags_by_asset[key].append({"tag_key": tag_key, "apply_method": method})

    classifications_by_asset: dict[str, list[dict]] = defaultdict(list)
    for index, row in enumerate(classifications):
        key = _opaque(row.get("asset_key"), f"classifications[{index}].asset_key")
        if key not in asset_map:
            raise ValueError(f"classifications[{index}] references an asset outside the denominator")
        state, issues = _classification_state(row, assessed_at, classification_max_age)
        classifications_by_asset[key].append({"state": state, "issues": issues})

    policies_by_asset: dict[str, list[dict]] = defaultdict(list)
    for index, row in enumerate(policies):
        key = _opaque(row.get("asset_key"), f"policies[{index}].asset_key")
        if key not in asset_map:
            raise ValueError(f"policies[{index}] references an asset outside the denominator")
        kind = _upper(row.get("policy_kind"))
        if kind not in POLICY_KINDS:
            raise ValueError(f"policies[{index}].policy_kind is invalid")
        policy_key = _opaque(row.get("policy_key"), f"policies[{index}].policy_key")
        assignment = _upper(row.get("assignment"))
        if assignment not in {"DIRECT", "TAG"}:
            raise ValueError(f"policies[{index}].assignment is invalid")
        status = _upper(row.get("policy_status"))
        if status not in POLICY_STATUSES:
            raise ValueError(f"policies[{index}].policy_status is invalid")
        normalized = {
            "policy_key": policy_key,
            "policy_kind": kind,
            "assignment": assignment,
            "policy_status": status,
            "entity_key_hashes": list(_entity_keys(row)) if kind == "AGGREGATION_POLICY" else [],
        }
        policies_by_asset[key].append(normalized)

    simulation_by_asset: dict[str, list[dict]] = defaultdict(list)
    for index, row in enumerate(simulations):
        key = _opaque(row.get("asset_key"), f"policy_context[{index}].asset_key")
        if key not in asset_map:
            raise ValueError(f"policy_context[{index}] references an asset outside the denominator")
        scenario = _opaque(row.get("scenario_key"), f"policy_context[{index}].scenario_key")
        status = _upper(row.get("status"))
        if status not in {"PASS", "FAIL", "ERROR"}:
            raise ValueError(f"policy_context[{index}].status is invalid")
        simulated_at = _timestamp(row.get("simulated_at"), f"policy_context[{index}].simulated_at")
        kinds = {_upper(item) for item in _strings(row.get("policy_kinds", []), f"policy_context[{index}].policy_kinds")}
        if kinds - POLICY_KINDS:
            raise ValueError(f"policy_context[{index}] has unsupported policy kinds")
        age_hours = (assessed_at - simulated_at).total_seconds() / 3600
        simulation_by_asset[key].append(
            {"scenario_key": scenario, "status": status, "policy_kinds": sorted(kinds), "fresh": 0 <= age_hours <= receipt_max_age}
        )

    receipts_doc = doc.get("receipts")
    if not isinstance(receipts_doc, dict):
        receipts_doc = {}
    required_surfaces = ("denominator", "tag_references", "policy_references", "classification_latest")
    datasets = {
        "denominator": assets,
        "tag_references": tags,
        "policy_references": policies,
        "classification_latest": classifications,
    }
    receipt_assessments = {
        name: _receipt(name, receipts_doc.get(name), datasets[name], assessed_at, receipt_max_age)
        for name in required_surfaces
    }
    required_policy_kinds = {kind for asset in asset_map.values() for kind in asset["required_controls"]}
    policy_source = receipts_doc.get("policy_references", {}).get("source") if isinstance(receipts_doc.get("policy_references"), dict) else None
    unsupported_policy_kinds = required_policy_kinds - POLICY_SOURCE_CAPABILITIES.get(policy_source, set())
    if unsupported_policy_kinds:
        policy_receipt = receipt_assessments["policy_references"]
        policy_receipt["issues"].append(
            "source cannot prove required policy kinds: " + ", ".join(sorted(unsupported_policy_kinds))
        )
        policy_receipt["status"] = "UNVERIFIABLE"
    for assessment in receipt_assessments.values():
        assessment["issues"] = sorted(set(assessment["issues"]))
    evidence_complete = all(item["status"] == "VERIFIED" for item in receipt_assessments.values())

    findings: list[dict] = []
    coverage_rows: list[dict] = []
    precedence_rows: list[dict] = []
    simulation_rows: list[dict] = []
    edition_ok = EDITION_RANK[edition] >= EDITION_RANK["ENTERPRISE"]
    for key in sorted(asset_map):
        asset = asset_map[key]
        asset_findings: list[str] = []
        tag_state = "PRESENT" if tags_by_asset[key] else "MISSING"
        classification_states = [row["state"] for row in classifications_by_asset[key]]
        classification_state = "NOT_OBSERVED"
        if classification_states:
            order = {"FAILED": 0, "PENDING": 1, "STALE": 2, "NOT_PROVEN": 3, "REVIEWED": 4, "CLASSIFIED": 5}
            classification_state = min(classification_states, key=lambda item: order.get(item, -1))
        if asset["require_tag"] and tag_state == "MISSING":
            asset_findings.append("TAG_MISSING")
            findings.append({"severity": "high", "category": "tag-coverage", "asset_key": key, "detail": "required governance tag not observed"})
        if asset["require_classification"] and classification_state not in {"CLASSIFIED", "REVIEWED"}:
            asset_findings.append("CLASSIFICATION_NOT_CURRENT")
            findings.append({"severity": "high", "category": "classification", "asset_key": key, "detail": f"classification state is {classification_state}"})
        if (asset["require_classification"] or asset["required_controls"]) and not edition_ok:
            asset_findings.append("EDITION_BOUNDARY")
            findings.append({"severity": "high", "category": "edition-boundary", "asset_key": key, "detail": "Enterprise Edition or higher is required for this governance claim"})

        controls: list[dict] = []
        for kind in asset["required_controls"]:
            candidates = [row for row in policies_by_asset[key] if row["policy_kind"] == kind]
            broken = [row for row in candidates if row["policy_status"] != "ACTIVE"]
            effective, shadowed, cumulative = _effective_policies(candidates, kind)
            preview_blocked = bool(
                any(row["assignment"] == "TAG" for row in effective)
                and kind in PREVIEW_TAG_POLICIES
                and f"TAG_BASED_{kind}" not in preview_features
            )
            state = "COVERED" if effective and not preview_blocked and not broken and edition_ok else "UNCOVERED"
            if broken:
                state = "MISCONFIGURED"
            if preview_blocked:
                state = "PREVIEW_NOT_ENABLED"
            if any(row["assignment"] == "TAG" for row in effective) and not tags_by_asset[key]:
                state = "TAG_EVIDENCE_MISSING"
            controls.append(
                {
                    "policy_kind": kind,
                    "state": state,
                    "effective_policy_keys": sorted(row["policy_key"] for row in effective),
                    "shadowed_policy_keys": sorted(row["policy_key"] for row in shadowed),
                    "cumulative_tag_policy_keys": sorted(row["policy_key"] for row in cumulative),
                }
            )
            if shadowed or cumulative:
                precedence_rows.append(
                    {
                        "asset_key": key,
                        "policy_kind": kind,
                        "rule": "DIRECT_PRECEDENCE" if kind != "AGGREGATION_POLICY" or not cumulative else "ENTITY_KEY_EXCEPTION",
                        "shadowed_policy_keys": sorted(row["policy_key"] for row in shadowed),
                        "cumulative_policy_keys": sorted(row["policy_key"] for row in cumulative),
                    }
                )
            if state != "COVERED":
                asset_findings.append(f"{kind}_{state}")
                findings.append({"severity": "critical", "category": "policy-coverage", "asset_key": key, "policy_kind": kind, "detail": state})

        required_kinds = set(asset["required_controls"])
        good_simulations = [
            row
            for row in simulation_by_asset[key]
            if row["status"] == "PASS" and row["fresh"] and required_kinds <= set(row["policy_kinds"])
        ]
        simulation_state = "PROVEN" if good_simulations else "NOT_PROVEN"
        if required_kinds and simulation_state != "PROVEN":
            findings.append({"severity": "medium", "category": "policy-context", "asset_key": key, "detail": "fresh passing POLICY_CONTEXT dry-run not supplied"})
        simulation_rows.append({"asset_key": key, "status": simulation_state, "scenario_keys": sorted(row["scenario_key"] for row in good_simulations)})
        coverage_rows.append(
            {
                **asset,
                "tag_state": tag_state,
                "classification_state": classification_state,
                "controls": controls,
                "policy_context_status": simulation_state,
                "coverage_status": "PASS" if not asset_findings else "FAIL",
                "reason_codes": sorted(asset_findings),
            }
        )

    if not evidence_complete:
        findings.append({"severity": "critical", "category": "evidence-completeness", "asset_key": "portfolio", "detail": "one or more core evidence receipts are unverifiable"})
    failed_assets = sum(row["coverage_status"] == "FAIL" for row in coverage_rows)
    simulations_proven = all(row["status"] == "PROVEN" for row in simulation_rows if asset_map[row["asset_key"]]["required_controls"])
    verified = evidence_complete and failed_assets == 0 and simulations_proven
    findings.sort(key=lambda row: ({"critical": 0, "high": 1, "medium": 2}.get(row["severity"], 9), row["asset_key"], row["category"], row.get("policy_kind", "")))
    dry_run_packet = [
        {
            "asset_key": row["asset_key"],
            "reason_codes": row["reason_codes"],
            "operator_action": "review coverage evidence and prepare an authorized policy/tag/classification change outside this skill",
            "required_precheck": "refresh bounded metadata and run POLICY_CONTEXT under approved ownership/APPLY privileges",
            "mutation_sql": None,
        }
        for row in coverage_rows
        if row["coverage_status"] == "FAIL"
    ]
    return {
        "schema_version": "1",
        "input_sha256": f"sha256:{_hash(doc)}",
        "decision": "VERIFIED" if verified else "NOT_PROVEN",
        "completeness_claim_blocked": not evidence_complete,
        "summary": {
            "denominator_assets": len(coverage_rows),
            "passing_assets": len(coverage_rows) - failed_assets,
            "failing_assets": failed_assets,
            "policy_context_proven": simulations_proven,
        },
        "coverage": coverage_rows,
        "precedence": sorted(precedence_rows, key=lambda row: (row["asset_key"], row["policy_kind"])),
        "policy_context": simulation_rows,
        "receipts": receipt_assessments,
        "findings": findings,
        "dry_run_remediation_packet": dry_run_packet,
        "boundaries": {
            "read_only": True,
            "mutation_sql_emitted": False,
            "edition": edition,
            "preview_features_enabled": sorted(preview_features),
            "account_usage_latency_is_not_current_state": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="sanitized governance evidence JSON")
    parser.add_argument("--out", type=Path, help="write the JSON report to this path")
    args = parser.parse_args()
    try:
        doc = json.loads(args.input.read_text(encoding="utf-8"))
        report = analyze(doc)
        rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
        if args.out:
            args.out.write_text(rendered, encoding="utf-8")
        else:
            sys.stdout.write(rendered)
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as error:
        print(f"governance coverage analysis failed: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
