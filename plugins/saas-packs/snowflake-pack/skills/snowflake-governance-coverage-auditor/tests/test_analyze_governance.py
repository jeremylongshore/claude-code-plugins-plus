from __future__ import annotations

import importlib.util
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parents[1]
PACK = SKILL.parents[1]


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


analyzer = load("governance_analyzer", SKILL / "scripts" / "analyze_governance.py")
collector = load("governance_collector", SKILL / "scripts" / "collect_snowflake_evidence.py")

NOW = "2026-09-04T12:00:00Z"
START = "2026-09-04T11:59:55Z"
H = {letter: letter * 64 for letter in "abcdef0123456789"}
ORG, ACCOUNT, USER, ROLE, SECONDARY = H["a"], H["b"], H["c"], H["d"], H["e"]
DATABASE, OBJECT, COLUMN = H["f"], H["0"], H["1"]
TAG_KEY, TAG_BINDING = H["2"], H["3"]
MASK, RAP, AGG, PRIVACY = H["4"], H["5"], H["6"], H["7"]
ENTITY_1, ENTITY_2 = H["8"], H["9"]
SC_MASK, SC_RAP, SC_AGG = H["a"], H["b"], H["c"]
CONTEXT, QUERY = H["d"], H["e"]


def seal(value: dict) -> dict:
    value["receipt_sha256"] = analyzer.digest({k: v for k, v in value.items() if k != "receipt_sha256"})
    return value


def context(selector: str, *, domain: str | None = None, classification: bool = False) -> dict:
    row = {
        "_dataset": "execution_context",
        "observed_at": NOW,
        "organization_name_sha256": ORG,
        "account_identifier_sha256": ACCOUNT,
        "collector_user_sha256": USER,
        "primary_role_sha256": ROLE,
        "primary_role_type": "ROLE",
        "secondary_roles_sha256": SECONDARY,
        "timezone": "UTC",
        "source_row_count": 0,
        "source_row_limit": 5000,
        "truncation_possible": False,
    }
    if classification:
        row |= {"selected_database_key_sha256": selector, "provider_latency_seconds": 10800}
    else:
        row |= {"selected_object_key_sha256": selector, "selected_object_domain": domain}
    return row


def receipt(surface: str, rows: list[dict]) -> dict:
    if surface == "governance-classification-current":
        kwargs = {"governance_database": "GOVERNED_DB"}
        data_name = "classification_latest"
        selected = DATABASE
        classification = True
    else:
        kwargs = {"governance_object": "GOVERNED_DB.GOVERNED_SCHEMA.GOVERNED_TABLE", "governance_domain": "TABLE"}
        data_name = "policy_references" if surface == "governance-policies-current" else "tag_references"
        selected = OBJECT
        classification = False
    path, template, rendered, sources, selector = collector.render_surface(surface, **kwargs)
    ctx = context(selected, domain="TABLE", classification=classification)
    ctx["source_row_count"] = len(rows)
    raw = [ctx] + [{"_dataset": data_name, **row} for row in rows]
    return collector.build_receipt(
        surface,
        "readonly-observer",
        rendered,
        sources,
        raw=raw,
        collected_at=NOW,
        template_sql=template,
        template_path=path,
        selector=selector,
        collection_mode="live-cli",
        collection_started_at=START,
        collection_completed_at=NOW,
    )


def scenario(key: str, asset: str, kind: str) -> dict:
    return {
        "scenario_key_sha256": key,
        "asset_key_sha256": asset,
        "control_kind": kind,
        "context_sha256": CONTEXT,
        "query_shape_sha256": QUERY,
        "expected_outcome": analyzer.OUTCOME_BY_KIND[kind],
    }


def simulation(row: dict, asset: dict) -> dict:
    return seal(
        {
            "schema_version": "1",
            "scenario_key_sha256": row["scenario_key_sha256"],
            "asset_key_sha256": row["asset_key_sha256"],
            "object_key_sha256": asset["object_key_sha256"],
            "control_kind": row["control_kind"],
            "context_sha256": row["context_sha256"],
            "query_shape_sha256": row["query_shape_sha256"],
            "expected_outcome": row["expected_outcome"],
            "outcome_status": "MATCHED",
            "simulated_at": NOW,
            "organization_name_sha256": ORG,
            "account_identifier_sha256": ACCOUNT,
            "collector_user_sha256": USER,
            "primary_role_sha256": ROLE,
            "primary_role_type": "ROLE",
            "secondary_roles_sha256": SECONDARY,
            "source": "POLICY_CONTEXT",
            "collection_mode": "operator-executed-sanitized-receipt",
        }
    )


def make_packet() -> dict:
    scenarios = [
        scenario(SC_AGG, OBJECT, "AGGREGATION_POLICY"),
        scenario(SC_RAP, OBJECT, "ROW_ACCESS_POLICY"),
        scenario(SC_MASK, COLUMN, "MASKING_POLICY"),
    ]
    assets = [
        {
            "asset_key_sha256": OBJECT,
            "object_key_sha256": OBJECT,
            "database_key_sha256": DATABASE,
            "asset_domain": "TABLE",
            "object_domain": "TABLE",
            "require_classification": True,
            "required_tag_keys_sha256": [TAG_KEY],
            "required_tag_bindings_sha256": [TAG_BINDING],
            "required_controls": ["AGGREGATION_POLICY", "ROW_ACCESS_POLICY"],
            "scenario_keys_sha256": sorted([SC_AGG, SC_RAP]),
        },
        {
            "asset_key_sha256": COLUMN,
            "object_key_sha256": OBJECT,
            "database_key_sha256": DATABASE,
            "asset_domain": "COLUMN",
            "object_domain": "TABLE",
            "require_classification": True,
            "required_tag_keys_sha256": [TAG_KEY],
            "required_tag_bindings_sha256": [TAG_BINDING],
            "required_controls": ["MASKING_POLICY"],
            "scenario_keys_sha256": [SC_MASK],
        },
    ]
    policy = {
        "schema_version": "1",
        "analysis_as_of_utc": NOW,
        "organization_name_sha256": ORG,
        "account_identifier_sha256": ACCOUNT,
        "account_edition": "ENTERPRISE",
        "receipt_max_age_seconds": 900,
        "classification_max_age_seconds": 86400,
        "preview_features_enabled": ["ROW_ACCESS_POLICY"],
        "assets_expected_count": len(assets),
        "assets_sha256": analyzer.digest(assets),
        "assets": assets,
        "scenarios_expected_count": len(scenarios),
        "scenarios_sha256": analyzer.digest(scenarios),
        "scenarios": scenarios,
    }
    classification = receipt(
        "governance-classification-current",
        [
            {
                "database_key_sha256": DATABASE,
                "object_key_sha256": OBJECT,
                "classification_status": "CLASSIFIED",
                "trigger_type": "AUTO CLASSIFICATION",
                "last_classified_on": "2026-09-04T08:00:00Z",
                "last_attempt_on": "2026-09-04T08:00:00Z",
                "error_present": False,
            }
        ],
    )
    tags = receipt(
        "governance-tags-current",
        [
            {
                "object_key_sha256": OBJECT,
                "asset_key_sha256": OBJECT,
                "asset_domain": "TABLE",
                "tag_key_sha256": TAG_KEY,
                "tag_binding_sha256": TAG_BINDING,
                "apply_method": "MANUAL",
            },
            {
                "object_key_sha256": OBJECT,
                "asset_key_sha256": COLUMN,
                "asset_domain": "COLUMN",
                "tag_key_sha256": TAG_KEY,
                "tag_binding_sha256": TAG_BINDING,
                "apply_method": "INHERITED",
            },
        ],
    )
    policies = receipt(
        "governance-policies-current",
        [
            {
                "object_key_sha256": OBJECT,
                "asset_key_sha256": OBJECT,
                "asset_domain": "TABLE",
                "policy_key_sha256": AGG,
                "policy_kind": "AGGREGATION_POLICY",
                "assignment": "DIRECT",
                "tag_key_sha256": None,
                "policy_status": "ACTIVE",
                "entity_key_set_sha256": ENTITY_1,
            },
            {
                "object_key_sha256": OBJECT,
                "asset_key_sha256": OBJECT,
                "asset_domain": "TABLE",
                "policy_key_sha256": RAP,
                "policy_kind": "ROW_ACCESS_POLICY",
                "assignment": "TAG",
                "tag_key_sha256": TAG_KEY,
                "policy_status": "ACTIVE",
                "entity_key_set_sha256": None,
            },
            {
                "object_key_sha256": OBJECT,
                "asset_key_sha256": COLUMN,
                "asset_domain": "COLUMN",
                "policy_key_sha256": MASK,
                "policy_kind": "MASKING_POLICY",
                "assignment": "DIRECT",
                "tag_key_sha256": None,
                "policy_status": "ACTIVE",
                "entity_key_set_sha256": None,
            },
        ],
    )
    scope = seal(
        {
            "schema_version": "1",
            "organization_name_sha256": ORG,
            "account_identifier_sha256": ACCOUNT,
            "collector_user_sha256": USER,
            "primary_role_sha256": ROLE,
            "primary_role_type": "ROLE",
            "secondary_roles_sha256": SECONDARY,
            "object_keys_sha256": [OBJECT],
            "database_keys_sha256": [DATABASE],
            "policy_kinds_visible": sorted(analyzer.POLICY_KINDS),
            "object_visibility_verified": True,
            "tag_visibility_verified": True,
            "classification_visibility_verified": True,
            "classification_profile_scope_verified": True,
            "classification_profiles": [{"database_key_sha256": DATABASE, "profile_status": "ACTIVE"}],
            "verified_at": NOW,
            "source": "OWNER_APPROVED_PRIVILEGE_RECONCILIATION",
        }
    )
    asset_map = {row["asset_key_sha256"]: row for row in assets}
    return {
        "schema_version": "2",
        "policy": policy,
        "collector_receipts": [classification, policies, tags],
        "scope_receipt": scope,
        "simulation_receipts": [simulation(row, asset_map[row["asset_key_sha256"]]) for row in scenarios],
    }


def analyze(packet: dict, *, input_digest: str | None = None):
    return analyzer.analyze(
        packet,
        evaluated_at=datetime.fromisoformat(NOW.replace("Z", "+00:00")).astimezone(timezone.utc),
        trusted_input_sha256=input_digest or analyzer.canonical_input_digest(packet),
        trusted_policy_sha256=analyzer.canonical_policy_digest(packet),
    )


def reseal_collector(receipt_value: dict) -> None:
    datasets = receipt_value["datasets"]
    receipt_value["dataset_row_counts"] = {key: len(value) for key, value in datasets.items()}
    receipt_value["row_count"] = sum(receipt_value["dataset_row_counts"].values())
    receipt_value["result_sha256"] = analyzer.digest(datasets)
    seal(receipt_value)


def add_policy_scenario(packet: dict, scenario_row: dict, *, outcome_status: str) -> None:
    policy = packet["policy"]
    policy["scenarios"].append(scenario_row)
    policy["scenarios_expected_count"] = len(policy["scenarios"])
    policy["scenarios_sha256"] = analyzer.digest(policy["scenarios"])
    asset = next(row for row in policy["assets"] if row["asset_key_sha256"] == scenario_row["asset_key_sha256"])
    asset["scenario_keys_sha256"] = sorted([*asset["scenario_keys_sha256"], scenario_row["scenario_key_sha256"]])
    policy["assets_sha256"] = analyzer.digest(policy["assets"])
    receipt_value = simulation(scenario_row, asset)
    receipt_value["outcome_status"] = outcome_status
    seal(receipt_value)
    packet["simulation_receipts"].append(receipt_value)


def test_clean_is_bounded_observation_not_pass_and_inherited_tag_counts():
    fixture = json.loads((SKILL / "tests" / "fixtures" / "clean-observations.json").read_text())
    report = analyze(make_packet())
    assert report["overall_status"] == fixture["expected_status"]
    assert report["bounded_coverage_claim_supported"] is True
    assert report["pass_supported"] is False
    assert report["findings"] == []


def test_unsafe_fixture_records_only_nonpositive_expectations():
    fixture = json.loads((SKILL / "tests" / "fixtures" / "unsafe-observations.json").read_text())
    assert fixture["expected_status"] == "GAPS_OBSERVED"
    assert fixture["pass_supported"] is False
    assert fixture["visibility_complete"] is False


def test_self_resealed_change_fails_out_of_band_digest():
    packet = make_packet()
    trusted = analyzer.canonical_input_digest(packet)
    packet["scope_receipt"]["tag_visibility_verified"] = False
    seal(packet["scope_receipt"])
    with pytest.raises(analyzer.EvidenceError, match="invalid trust"):
        analyze(packet, input_digest=trusted)


def test_missing_object_receipt_fails_exact_denominator():
    packet = make_packet()
    packet["collector_receipts"].pop()
    with pytest.raises(analyzer.EvidenceError, match="invalid evidence"):
        analyze(packet)


def test_non_active_conditional_masking_status_is_gap():
    packet = make_packet()
    receipt_value = next(r for r in packet["collector_receipts"] if r["surface"] == "governance-policies-current")
    row = next(r for r in receipt_value["datasets"]["policy_references"] if r["policy_kind"] == "MASKING_POLICY")
    row["policy_status"] = "COLUMN_IS_MISSING_FOR_SECONDARY_ARG"
    reseal_collector(receipt_value)
    report = analyze(packet)
    assert {item["code"] for item in report["findings"]} >= {"POLICY_NON_ACTIVE", "CONTROL_NOT_EFFECTIVE"}
    assert report["bounded_coverage_claim_supported"] is False


def test_simulation_context_mismatch_fails_before_findings():
    packet = make_packet()
    packet["simulation_receipts"][0]["context_sha256"] = H["f"]
    seal(packet["simulation_receipts"][0])
    with pytest.raises(analyzer.EvidenceError, match="invalid evidence"):
        analyze(packet)


def test_newer_failed_classification_attempt_blocks_bounded_result():
    packet = make_packet()
    receipt_value = next(r for r in packet["collector_receipts"] if r["surface"] == "governance-classification-current")
    row = receipt_value["datasets"]["classification_latest"][0]
    row["last_attempt_on"] = "2026-09-04T09:00:00Z"
    row["error_present"] = True
    reseal_collector(receipt_value)
    report = analyze(packet)
    assert "CLASSIFICATION_FAILED_OR_NONCURRENT" in {item["code"] for item in report["findings"]}


def test_non_active_classification_profile_blocks_bounded_result():
    packet = make_packet()
    packet["scope_receipt"]["classification_profiles"][0]["profile_status"] = "DISABLED"
    seal(packet["scope_receipt"])
    report = analyze(packet)
    assert "CLASSIFICATION_PROFILE_NOT_ACTIVE" in {item["code"] for item in report["findings"]}


def test_standard_edition_is_not_positive():
    packet = make_packet()
    packet["policy"]["account_edition"] = "STANDARD"
    report = analyze(packet)
    assert "UNSUPPORTED_EDITION" in {item["code"] for item in report["findings"]}


def test_unknown_edition_is_invalid_policy():
    packet = make_packet()
    packet["policy"]["account_edition"] = "UNKNOWN"
    with pytest.raises(analyzer.EvidenceError, match="invalid policy"):
        analyze(packet)


def test_cap_and_truncation_cannot_be_resealed_into_positive():
    packet = make_packet()
    receipt_value = packet["collector_receipts"][0]
    receipt_value["datasets"]["execution_context"][0]["source_row_count"] = 5000
    receipt_value["datasets"]["execution_context"][0]["truncation_possible"] = True
    receipt_value["truncation_possible"] = True
    reseal_collector(receipt_value)
    with pytest.raises(analyzer.EvidenceError, match="invalid evidence"):
        analyze(packet)


def test_mixed_execution_context_fails_closed():
    packet = make_packet()
    receipt_value = packet["collector_receipts"][1]
    receipt_value["datasets"]["execution_context"][0]["primary_role_sha256"] = H["f"]
    reseal_collector(receipt_value)
    with pytest.raises(analyzer.EvidenceError, match="invalid evidence"):
        analyze(packet)


def test_stale_current_receipt_fails_closed():
    packet = make_packet()
    receipt_value = packet["collector_receipts"][0]
    receipt_value["collection_started_at"] = "2026-09-04T11:39:55Z"
    receipt_value["collection_completed_at"] = "2026-09-04T11:40:00Z"
    receipt_value["collected_at"] = "2026-09-04T11:40:00Z"
    receipt_value["datasets"]["execution_context"][0]["observed_at"] = "2026-09-04T11:40:00Z"
    reseal_collector(receipt_value)
    with pytest.raises(analyzer.EvidenceError, match="invalid evidence"):
        analyze(packet)


@pytest.mark.parametrize(
    ("surface", "kwargs"),
    [
        ("governance-classification-current", {"governance_database": "DB;DROP_DATABASE_X"}),
        (
            "governance-policies-current",
            {"governance_object": "DB.SCHEMA.T' OR 1=1--", "governance_domain": "TABLE"},
        ),
    ],
)
def test_selector_injection_is_rejected(surface, kwargs):
    with pytest.raises(collector.CollectionError):
        collector.render_surface(surface, **kwargs)


def test_arbitrary_simulation_field_is_rejected_without_reflection():
    packet = make_packet()
    packet["simulation_receipts"][0]["raw_result"] = "SECRET_POLICY_OUTPUT"
    seal(packet["simulation_receipts"][0])
    with pytest.raises(analyzer.EvidenceError) as error:
        analyze(packet)
    assert "SECRET_POLICY_OUTPUT" not in str(error.value)


@pytest.mark.parametrize(
    ("scenario_key", "asset_key", "control_kind", "outcome_status"),
    [
        (H["f"], COLUMN, "MASKING_POLICY", "MISMATCH"),
        (H["e"], OBJECT, "AGGREGATION_POLICY", "ERROR"),
    ],
)
def test_all_simulations_for_asset_control_are_cumulative_and_any_unsafe_outcome_blocks(
    scenario_key, asset_key, control_kind, outcome_status
):
    packet = make_packet()
    # The original scenario sorts first and MATCHES. This later scenario
    # must still block; selecting the first row would produce a false positive.
    second_scenario = scenario(scenario_key, asset_key, control_kind)
    second_scenario["context_sha256"] = H["0"]
    second_scenario["query_shape_sha256"] = H["1"]
    add_policy_scenario(packet, second_scenario, outcome_status=outcome_status)
    report = analyze(packet)
    assert report["bounded_coverage_claim_supported"] is False
    assert [row["code"] for row in report["findings"]].count("SIMULATION_NOT_MATCHED") == 1


def test_view_tag_collection_uses_table_domain_for_both_tag_functions():
    _, _, rendered, _, selector = collector.render_surface(
        "governance-tags-current",
        governance_object="GOVERNED_DB.GOVERNED_SCHEMA.GOVERNED_VIEW",
        governance_domain="VIEW",
    )
    object_match = re.search(r"TAG_REFERENCES\(\s*'[^']+',\s*'([^']+)'\s*\)", rendered)
    columns_match = re.search(r"TAG_REFERENCES_ALL_COLUMNS\(\s*'[^']+',\s*'([^']+)'\s*\)", rendered)
    assert object_match and object_match.group(1) == "TABLE"
    assert columns_match and columns_match.group(1) == "TABLE"
    assert selector["governance_domain"] == "VIEW"


def test_database_wide_classification_accepts_valid_out_of_scope_rows():
    packet = make_packet()
    receipt_value = next(
        row for row in packet["collector_receipts"] if row["surface"] == "governance-classification-current"
    )
    rows = receipt_value["datasets"]["classification_latest"]
    rows.append(
        {
            **rows[0],
            "object_key_sha256": H["2"],
            "classification_status": "PROVIDER_OTHER",
            "error_present": True,
        }
    )
    receipt_value["datasets"]["execution_context"][0]["source_row_count"] = len(rows)
    reseal_collector(receipt_value)
    report = analyze(packet)
    assert report["bounded_coverage_claim_supported"] is True
    assert report["findings"] == []


def test_database_wide_classification_rejects_in_scope_database_contradiction():
    packet = make_packet()
    receipt_value = next(
        row for row in packet["collector_receipts"] if row["surface"] == "governance-classification-current"
    )
    receipt_value["datasets"]["classification_latest"][0]["database_key_sha256"] = H["2"]
    reseal_collector(receipt_value)
    with pytest.raises(analyzer.EvidenceError, match="invalid evidence"):
        analyze(packet)


def test_database_wide_classification_rejects_duplicate_in_scope_object():
    packet = make_packet()
    receipt_value = next(
        row for row in packet["collector_receipts"] if row["surface"] == "governance-classification-current"
    )
    rows = receipt_value["datasets"]["classification_latest"]
    rows.append({**rows[0], "classification_status": "REVIEWED"})
    receipt_value["datasets"]["execution_context"][0]["source_row_count"] = len(rows)
    reseal_collector(receipt_value)
    with pytest.raises(analyzer.EvidenceError, match="invalid evidence"):
        analyze(packet)


def test_same_entity_direct_aggregation_shadows_tag_but_different_is_cumulative():
    packet = make_packet()
    receipt_value = next(r for r in packet["collector_receipts"] if r["surface"] == "governance-policies-current")
    rows = receipt_value["datasets"]["policy_references"]
    template = next(row for row in rows if row["policy_kind"] == "AGGREGATION_POLICY")
    rows.extend(
        [
            {**template, "policy_key_sha256": H["d"], "assignment": "TAG", "tag_key_sha256": TAG_KEY},
            {
                **template,
                "policy_key_sha256": H["e"],
                "assignment": "TAG",
                "tag_key_sha256": TAG_KEY,
                "entity_key_set_sha256": ENTITY_2,
            },
        ]
    )
    receipt_value["datasets"]["execution_context"][0]["source_row_count"] = len(rows)
    reseal_collector(receipt_value)
    report = analyze(packet)
    codes = {row["code"] for row in report["precedence_observations"]}
    assert codes == {
        "DIRECT_POLICY_SHADOWS_TAG_POLICY",
        "AGGREGATION_DIRECT_SHADOWS_SAME_ENTITY_TAG",
        "AGGREGATION_DIFFERENT_ENTITY_TAG_REMAINS_CUMULATIVE",
    }
    assert report["bounded_coverage_claim_supported"] is True


def test_privacy_policy_combination_is_blocked():
    packet = make_packet()
    receipt_value = next(r for r in packet["collector_receipts"] if r["surface"] == "governance-policies-current")
    rows = receipt_value["datasets"]["policy_references"]
    rows.append(
        {
            "object_key_sha256": OBJECT,
            "asset_key_sha256": OBJECT,
            "asset_domain": "TABLE",
            "policy_key_sha256": PRIVACY,
            "policy_kind": "PRIVACY_POLICY",
            "assignment": "DIRECT",
            "tag_key_sha256": None,
            "policy_status": "ACTIVE",
            "entity_key_set_sha256": None,
        }
    )
    receipt_value["datasets"]["execution_context"][0]["source_row_count"] = len(rows)
    reseal_collector(receipt_value)
    report = analyze(packet)
    assert "UNSUPPORTED_POLICY_COMBINATION" in {item["code"] for item in report["findings"]}


def test_unattested_tag_preview_is_not_positive():
    packet = make_packet()
    packet["policy"]["preview_features_enabled"] = []
    report = analyze(packet)
    assert "PREVIEW_FEATURE_UNATTESTED" in {item["code"] for item in report["findings"]}


def test_arbitrary_row_key_is_rejected_without_reflection():
    packet = make_packet()
    receipt_value = packet["collector_receipts"][0]
    receipt_value["datasets"]["classification_latest"][0]["secret_name"] = "RAW_PRIVATE_NAME"
    reseal_collector(receipt_value)
    with pytest.raises(analyzer.EvidenceError) as error:
        analyze(packet)
    assert "RAW_PRIVATE_NAME" not in str(error.value)


def test_sql_and_remediation_are_read_only():
    forbidden = re.compile(r"\b(INSERT|UPDATE|DELETE|MERGE|CREATE|ALTER|DROP|GRANT|REVOKE|CALL|EXECUTE)\b", re.I)
    for path in (SKILL / "scripts" / "sql").glob("*.sql"):
        sql = "\n".join(line for line in path.read_text().splitlines() if not line.lstrip().startswith("--"))
        assert not forbidden.search(sql)
    report = analyze(make_packet())
    assert all(
        row["mutation_sql"] is None and row["requires_separate_authorization"]
        for row in report["dry_run_remediation_packet"]
    )
