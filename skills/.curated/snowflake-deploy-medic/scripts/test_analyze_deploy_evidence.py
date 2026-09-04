#!/usr/bin/env python3
"""Adversarial tests for the fail-closed Snowflake deploy evidence analyzer."""

from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODULE_PATH = HERE / "analyze_deploy_evidence.py"
SPEC = importlib.util.spec_from_file_location("deploy_analyzer", MODULE_PATH)
assert SPEC and SPEC.loader
analyzer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(analyzer)

AS_OF = "2026-09-03T12:05:00Z"
STAMP = "2026-09-03T12:00:00Z"


def sha(character: str) -> str:
    return "sha256:" + character * 64


def seal(row: dict) -> dict:
    row.pop("receipt_sha256", None)
    row["receipt_sha256"] = "sha256:" + hashlib.sha256(analyzer._canonical(row)).hexdigest()
    return row


def packet() -> dict:
    resources = [
        {
            "resource_ref": sha("1"),
            "type": "snowflake_database",
            "actions": ["no-op"],
            "preview": False,
            "existing": True,
            "import_ref": None,
        }
    ]
    migration = seal(
        {
            "migration_ref": sha("2"),
            "script_type": "V",
            "script_name": "V1.0.0__baseline.sql",
            "version": "1.0.0",
            "checksum_sha256": sha("3"),
            "applied_checksum_sha256": sha("3"),
            "status": "SUCCESS",
            "installed_at": "2026-09-03T11:30:00Z",
            "pending": False,
            "out_of_order": False,
            "dry_run_verified": True,
            "rendered_sql_redacted": True,
            "always_run_reviewed": False,
            "idempotence_verified": True,
        }
    )
    bcr_items = [
        seal(
            {
                "item_id": item_id,
                "affected": False,
                "affected_refs": [],
                "owner_ref": sha("4"),
                "disposition": "NOT_APPLICABLE",
            }
        )
        for item_id in sorted(analyzer.BCR_BUNDLE_ITEMS["2026_06"])
    ]
    plan = seal(
        {
            "format_version": "1.2",
            "terraform_version": "1.9.8",
            "complete": True,
            "errored": False,
            "refresh_enabled": True,
            "action_inventory_complete": True,
            "exit_code": 0,
            "changes": 0,
            "resource_change_count": 1,
            "action_counts": {
                "create": 0,
                "create-delete": 0,
                "delete": 0,
                "delete-create": 0,
                "no-op": 1,
                "read": 0,
                "update": 0,
            },
            "resources_sha256": analyzer.bundle_digest(resources),
            "saved_plan_sha256": sha("5"),
            "prior_state_lineage_ref": sha("6"),
            "prior_state_serial": 42,
            "generated_at": "2026-09-03T11:55:00Z",
        }
    )
    migrations = [migration]
    data = {
        "schema_version": "2",
        "metadata": {
            "account_ref": sha("7"),
            "role_ref": sha("8"),
            "repo_sha": "0123456789abcdef0123456789abcdef01234567",
            "collected_at": STAMP,
            "window_start": "2026-09-03T11:30:00Z",
            "window_end": "2026-09-03T11:59:30Z",
        },
        "terraform": {
            "runtime_version": "1.9.8",
            "platform": "linux_amd64",
            "provider_source": "snowflakedb/snowflake",
            "previous_provider_version": "2.20.0",
            "provider_version": "2.20.0",
            "selected_provider_version": "2.20.0",
            "lockfile_sha256": sha("9"),
            "backend_ref": sha("a"),
            "workspace_ref": sha("b"),
            "state": {
                "parseable": True,
                "valid": True,
                "lineage_ref": sha("6"),
                "serial": 42,
                "resource_count": 1,
                "resource_refs": [sha("1")],
                "resources_sha256": analyzer.bundle_digest([sha("1")]),
                "lock_capability": "SUPPORTED",
                "lock_status": "ACQUIRED",
                "state_sha256": sha("d"),
            },
            "plan": plan,
            "resources": resources,
            "preview_features_enabled": [],
            "preview_inventory": seal(
                {
                    "verified": True,
                    "provider_version": "2.20.0",
                    "expected_count": 0,
                    "detected_count": 0,
                    "resource_refs_sha256": analyzer.bundle_digest([]),
                    "source_url": "https://registry.terraform.io/providers/snowflakedb/snowflake/latest/docs",
                    "observed_at": "2026-09-03T11:58:00Z",
                }
            ),
        },
        "preflight": {},
        "affected_objects_verified": True,
        "affected_objects_expected_count": 0,
        "affected_objects": [],
        "state_backup": seal(
            {
                "created": True,
                "verified": True,
                "account_ref": sha("7"),
                "backend_ref": sha("a"),
                "workspace_ref": sha("b"),
                "lineage_ref": sha("6"),
                "serial": 42,
                "state_sha256": sha("d"),
                "captured_at": "2026-09-03T11:45:00Z",
            }
        ),
        "migrations_verified": True,
        "migrations_expected_count": 1,
        "migrations_observed_at": "2026-09-03T11:58:00Z",
        "migration_repository_sha256": analyzer.bundle_digest(migrations),
        "change_history_expected_count": 1,
        "change_history_sha256": sha("d"),
        "change_history_projection_sha256": analyzer.bundle_digest(migrations),
        "migrations": migrations,
        "provider_migrations_verified": True,
        "provider_migrations_expected_count": 0,
        "provider_migrations": [],
        "dbt_projects_verified": True,
        "dbt_projects_expected_count": 0,
        "dbt_projects": [],
        "post_change_invariants_verified": True,
        "post_change_invariants_expected_count": 0,
        "post_change_invariants": [],
        "tools": {
            "snowflake_cli": {
                "version": "3.12.0",
                "source_url": "https://docs.snowflake.com/developer-guide/snowflake-cli/index",
                "observed_at": "2026-09-03T11:58:00Z",
            },
            "python_connector": {
                "version": "3.17.2",
                "source_url": "https://docs.snowflake.com/developer-guide/python-connector/python-connector",
                "observed_at": "2026-09-03T11:58:00Z",
            },
            "schemachange": {
                "version": "4.0.1",
                "source_url": "https://github.com/Snowflake-Labs/schemachange/releases",
                "observed_at": "2026-09-03T11:58:00Z",
            },
        },
        "bcr": {},
        "rollback": {},
        "zero_change_receipt": {},
    }
    data["bcr"] = seal(
        {
            "bundle": "2026_06",
            "status": "DISABLED",
            "source_url": "https://docs.snowflake.com/en/release-notes/bcr-bundles/2026_06_bundle",
            "source_snapshot_sha256": analyzer.bundle_digest(sorted(analyzer.BCR_BUNDLE_ITEMS["2026_06"])),
            "observed_at": "2026-09-03T11:50:00Z",
            "expected_count": len(bcr_items),
            "complete": True,
            "inventory_sha256": analyzer.bundle_digest(bcr_items),
            "inventory": bcr_items,
        }
    )
    checks = [{"name": name, "status": "PASS"} for name in sorted(analyzer.REQUIRED_PREFLIGHT)]
    data["preflight"] = seal(
        {
            "completed": True,
            "operator_ref": sha("e"),
            "checked_at": "2026-09-03T11:59:00Z",
            "checks": checks,
        }
    )
    data["rollback"] = seal(
        {
            "tested": True,
            "strategy": "STATE_RESTORE",
            "owner_ref": sha("e"),
            "stop_condition_ref": sha("f"),
            "tested_at": "2026-09-03T11:58:00Z",
            "plan_sha256": sha("5"),
            "migration_inventory_sha256": analyzer.bundle_digest(migrations),
        }
    )
    data["zero_change_receipt"] = seal(
        {
            "issued": True,
            "plan_sha256": sha("5"),
            "affected_objects": 0,
            "resources_sha256": analyzer.bundle_digest(resources),
            "issued_at": STAMP,
        }
    )
    return data


def run(data: dict, *, trusted: str | None = None, as_of: str = AS_OF) -> dict:
    digest = analyzer.bundle_digest(data) if trusted is None else trusted
    return analyzer.analyze(data, analysis_as_of=as_of, trusted_bundle_sha256=digest)


def codes(report: dict) -> set[str]:
    return {item["code"] for item in report["findings"]}


def refresh_migration_denominator(data: dict) -> None:
    digest = analyzer.bundle_digest(data["migrations"])
    data["migrations_expected_count"] = len(data["migrations"])
    data["change_history_expected_count"] = len(data["migrations"])
    data["migration_repository_sha256"] = digest
    data["change_history_projection_sha256"] = digest


def provider_segment(source: str, target: str, *, status: str = "NOT_APPLICABLE") -> dict:
    refs = [] if status == "NOT_APPLICABLE" else [sha("1")]
    return seal(
        {
            "from_version": source,
            "to_version": target,
            "source_url": "https://github.com/snowflakedb/terraform-provider-snowflake/blob/0123456789abcdef0123456789abcdef01234567/MIGRATION_GUIDE.md",
            "source_snapshot_sha256": sha("c"),
            "observed_at": "2026-09-03T11:58:00Z",
            "affected_count": len(refs),
            "affected_address_refs": refs,
            "affected_addresses_sha256": analyzer.bundle_digest(refs),
            "state_move_required": False,
            "state_move_completed": False,
            "isolated_state_tested": True,
            "status": status,
        }
    )


def add_dbt_project(data: dict, *, staged_sha: str | None = None) -> None:
    project_ref = sha("0")
    data["terraform"]["resources"][0]["type"] = "snowflake_dbt_project"
    data["terraform"]["plan"]["resources_sha256"] = analyzer.bundle_digest(data["terraform"]["resources"])
    seal(data["terraform"]["plan"])
    bcr_item = next(item for item in data["bcr"]["inventory"] if item["item_id"] == "BCR-2362")
    bcr_item.update({"affected": True, "affected_refs": [project_ref], "disposition": "VERIFIED"})
    seal(bcr_item)
    data["bcr"]["inventory_sha256"] = analyzer.bundle_digest(data["bcr"]["inventory"])
    seal(data["bcr"])
    data["dbt_projects"] = [
        seal(
            {
                "project_ref": project_ref,
                "plan_resource_ref": sha("1"),
                "current_model": "VERSIONED",
                "target_model": "VERSIONED",
                "bundle_status": "DISABLED",
                "bcr_item_id": "BCR-2362",
                "bcr_disposition": "VERIFIED",
                "target_version_supported": True,
                "deployed_code_sha256": sha("a"),
                "staged_code_sha256": staged_sha or sha("a"),
                "rollback_artifact_sha256": sha("b"),
                "profile_verified": True,
                "dependencies_verified": True,
                "compile_verified": True,
                "build_verified": True,
                "tests_verified": True,
                "force_replace": False,
                "ownership_verified": True,
                "early_opt_in_verified": False,
                "early_opt_in_ref": None,
                "demigration_available": False,
                "observed_at": "2026-09-03T11:58:00Z",
            }
        )
    ]
    data["dbt_projects_expected_count"] = 1


class DeployAnalyzerTests(unittest.TestCase):
    def test_clean_packet_passes_only_as_of_and_never_authorizes_apply(self) -> None:
        report = run(packet())
        self.assertEqual(report["status"], "PASS_AS_OF")
        self.assertFalse(report["safe_to_apply"])
        self.assertEqual(report["findings"], [])
        self.assertEqual(report["temporal_qualification"]["valid_until_utc"], AS_OF)

    def test_out_of_band_digest_is_mandatory(self) -> None:
        data = packet()
        report = analyzer.analyze(data, analysis_as_of=AS_OF, trusted_bundle_sha256=None)
        self.assertIn("TRUSTED_BUNDLE_DIGEST_MISSING_OR_MISMATCHED", codes(report))

    def test_resealed_tamper_cannot_reuse_old_trusted_digest(self) -> None:
        data = packet()
        trusted = analyzer.bundle_digest(data)
        data["state_backup"]["serial"] = 43
        seal(data["state_backup"])
        self.assertIn("TRUSTED_BUNDLE_DIGEST_MISSING_OR_MISMATCHED", codes(run(data, trusted=trusted)))

    def test_stale_and_future_packets_fail(self) -> None:
        data = packet()
        self.assertIn("EVIDENCE_CONTEXT_INVALID_OR_STALE", codes(run(data, as_of="2026-09-03T12:15:01Z")))
        self.assertIn("EVIDENCE_CONTEXT_INVALID_OR_STALE", codes(run(data, as_of="2026-09-03T11:59:59Z")))

    def test_zero_length_observation_window_fails(self) -> None:
        data = packet()
        data["metadata"]["window_start"] = data["metadata"]["window_end"]
        self.assertIn("EVIDENCE_CONTEXT_INVALID_OR_STALE", codes(run(data)))

    def test_plan_exit_code_and_action_inventory_must_reconcile(self) -> None:
        for exit_code, changes in ((0, 1), (2, 0)):
            data = packet()
            data["terraform"]["plan"]["exit_code"] = exit_code
            data["terraform"]["plan"]["changes"] = changes
            seal(data["terraform"]["plan"])
            self.assertIn("PLAN_EXIT_ACTION_CONTRADICTION", codes(run(data)))

    def test_create_action_cannot_pass_as_zero_change(self) -> None:
        data = packet()
        data["terraform"]["resources"][0]["actions"] = ["create"]
        data["terraform"]["resources"][0]["existing"] = False
        data["terraform"]["state"]["resource_refs"] = []
        data["terraform"]["state"]["resource_count"] = 0
        data["terraform"]["state"]["resources_sha256"] = analyzer.bundle_digest([])
        found = codes(run(data))
        self.assertIn("PLAN_RECEIPT_UNVERIFIABLE", found)
        self.assertIn("PLAN_EXIT_ACTION_CONTRADICTION", found)

    def test_noop_resource_must_exist_in_bound_state(self) -> None:
        data = packet()
        data["terraform"]["resources"][0]["existing"] = False
        data["terraform"]["state"]["resource_refs"] = []
        data["terraform"]["state"]["resource_count"] = 0
        data["terraform"]["state"]["resources_sha256"] = analyzer.bundle_digest([])
        self.assertIn("PLAN_RESOURCE_INVENTORY_INVALID", codes(run(data)))

    def test_incomplete_plan_and_disabled_refresh_fail(self) -> None:
        data = packet()
        data["terraform"]["plan"]["complete"] = False
        data["terraform"]["plan"]["refresh_enabled"] = False
        seal(data["terraform"]["plan"])
        self.assertIn("PLAN_RECEIPT_UNVERIFIABLE", codes(run(data)))

    def test_affected_objects_rejects_boolean_denominator(self) -> None:
        data = packet()
        data["affected_objects_expected_count"] = True
        self.assertIn("AFFECTED_OBJECT_DENOMINATOR_UNVERIFIED", codes(run(data)))

    def test_backup_must_precede_plan(self) -> None:
        data = packet()
        data["state_backup"]["captured_at"] = STAMP
        seal(data["state_backup"])
        self.assertIn("STATE_BACKUP_RECEIPT_UNVERIFIABLE", codes(run(data)))

    def test_provider_upgrade_requires_segments(self) -> None:
        data = packet()
        data["terraform"]["previous_provider_version"] = "2.18.0"
        self.assertIn("PROVIDER_MIGRATION_DENOMINATOR_UNVERIFIED", codes(run(data)))

    def test_preview_remains_blocking(self) -> None:
        data = packet()
        data["terraform"]["preview_features_enabled"] = ["experimental_feature"]
        self.assertIn("PROVIDER_PREVIEW_FEATURE", codes(run(data)))

    def test_bcr_rejects_string_boolean_and_fake_id(self) -> None:
        data = packet()
        item = data["bcr"]["inventory"][0]
        item.update({"affected": "false", "item_id": "BCR-anything"})
        seal(item)
        data["bcr"]["inventory_sha256"] = analyzer.bundle_digest(data["bcr"]["inventory"])
        seal(data["bcr"])
        self.assertIn("BCR_INVENTORY_UNVERIFIED", codes(run(data)))

    def test_unaffected_bcr_requires_not_applicable_disposition(self) -> None:
        data = packet()
        item = data["bcr"]["inventory"][0]
        item["disposition"] = "ACCEPTED"
        seal(item)
        data["bcr"]["inventory_sha256"] = analyzer.bundle_digest(data["bcr"]["inventory"])
        seal(data["bcr"])
        self.assertIn("BCR_INVENTORY_UNVERIFIED", codes(run(data)))

    def test_bcr_denominator_and_freshness_are_gates(self) -> None:
        data = packet()
        data["bcr"].update({"expected_count": 0, "observed_at": "2026-09-01T00:00:00Z"})
        seal(data["bcr"])
        self.assertIn("BCR_INVENTORY_UNVERIFIED", codes(run(data)))

    def test_empty_bcr_inventory_never_passes(self) -> None:
        data = packet()
        data["bcr"].update({"inventory": [], "expected_count": 0, "inventory_sha256": analyzer.bundle_digest([])})
        seal(data["bcr"])
        self.assertIn("BCR_INVENTORY_UNVERIFIED", codes(run(data)))

    def test_versioned_checksum_drift_blocks(self) -> None:
        data = packet()
        data["migrations"][0]["checksum_sha256"] = sha("0")
        seal(data["migrations"][0])
        self.assertIn("VERSIONED_CHECKSUM_DRIFT-0", codes(run(data)))

    def test_always_run_requires_review_and_idempotence(self) -> None:
        data = packet()
        row = data["migrations"][0]
        row.update(
            {
                "script_type": "A",
                "script_name": "A__baseline.sql",
                "version": None,
                "always_run_reviewed": False,
                "idempotence_verified": False,
            }
        )
        seal(row)
        self.assertIn("ALWAYS_MIGRATION_UNREVIEWED-0", codes(run(data)))

    def test_successful_repeatable_and_always_rows_bind_installed_checksum(self) -> None:
        data = packet()
        row = data["migrations"][0]
        row.update(
            {
                "script_type": "R",
                "script_name": "R__baseline.sql",
                "version": None,
                "applied_checksum_sha256": None,
            }
        )
        seal(row)
        refresh_migration_denominator(data)
        self.assertIn("REPEATABLE_HISTORY_MISSING-0", codes(run(data)))

        data = packet()
        row = data["migrations"][0]
        row.update(
            {
                "script_type": "A",
                "script_name": "A__baseline.sql",
                "version": None,
                "always_run_reviewed": True,
                "applied_checksum_sha256": sha("f"),
            }
        )
        seal(row)
        refresh_migration_denominator(data)
        self.assertIn("ALWAYS_HISTORY_MISMATCH-0", codes(run(data)))

    def test_duplicate_migration_ref_fails(self) -> None:
        data = packet()
        data["migrations"].append(copy.deepcopy(data["migrations"][0]))
        data["migrations_expected_count"] = 2
        self.assertIn("MIGRATION_DENOMINATOR_UNVERIFIED", codes(run(data)))

    def test_version_components_are_canonical_without_leading_zero_collisions(self) -> None:
        data = packet()
        second = copy.deepcopy(data["migrations"][0])
        second.update({"migration_ref": sha("f"), "script_name": "V01.0__duplicate.sql", "version": "01.0"})
        seal(second)
        data["migrations"].append(second)
        refresh_migration_denominator(data)
        self.assertIn("MIGRATION_DENOMINATOR_UNVERIFIED", codes(run(data)))

    def test_arbitrary_preflight_subset_does_not_pass(self) -> None:
        data = packet()
        data["preflight"]["checks"] = [{"name": "plan", "status": "PASS"}]
        seal(data["preflight"])
        self.assertIn("PREFLIGHT_DENOMINATOR_UNVERIFIED", codes(run(data)))

    def test_preflight_and_rollback_cannot_predate_bound_plan(self) -> None:
        data = packet()
        data["preflight"]["checked_at"] = "2026-09-03T11:57:00Z"
        seal(data["preflight"])
        data["rollback"]["tested_at"] = "2026-09-03T11:50:00Z"
        seal(data["rollback"])
        found = codes(run(data))
        self.assertIn("PREFLIGHT_DENOMINATOR_UNVERIFIED", found)
        self.assertIn("ROLLBACK_RECEIPT_UNVERIFIABLE", found)

    def test_preflight_cannot_complete_before_rollback_test(self) -> None:
        data = packet()
        data["rollback"]["tested_at"] = "2026-09-03T11:59:15Z"
        seal(data["rollback"])
        self.assertIn("PREFLIGHT_DENOMINATOR_UNVERIFIED", codes(run(data)))

    def test_source_evidence_must_fall_inside_declared_window(self) -> None:
        data = packet()
        data["metadata"]["window_start"] = "2026-09-03T11:59:00Z"
        found = codes(run(data))
        self.assertIn("PLAN_RECEIPT_UNVERIFIABLE", found)
        self.assertIn("BCR_INVENTORY_UNVERIFIED", found)
        self.assertIn("STATE_BACKUP_RECEIPT_UNVERIFIABLE", found)

    def test_changed_plan_requires_structured_invariant(self) -> None:
        data = packet()
        data["terraform"]["resources"][0]["actions"] = ["update"]
        plan = data["terraform"]["plan"]
        plan.update(
            {
                "exit_code": 2,
                "changes": 1,
                "action_counts": {
                    "create": 0,
                    "create-delete": 0,
                    "delete": 0,
                    "delete-create": 0,
                    "no-op": 0,
                    "read": 0,
                    "update": 1,
                },
                "resources_sha256": analyzer.bundle_digest(data["terraform"]["resources"]),
            }
        )
        seal(plan)
        data["affected_objects"] = [{"object_ref": sha("0"), "plan_resource_ref": sha("1")}]
        data["affected_objects_expected_count"] = 1
        data["zero_change_receipt"].update(
            {
                "issued": False,
                "affected_objects": 1,
                "resources_sha256": analyzer.bundle_digest(data["terraform"]["resources"]),
            }
        )
        seal(data["zero_change_receipt"])
        self.assertIn("POST_CHANGE_INVARIANTS_UNVERIFIED", codes(run(data)))

        data["post_change_invariants"] = [
            seal(
                {
                    "invariant_ref": sha("a"),
                    "plan_resource_ref": sha("1"),
                    "account_ref": sha("7"),
                    "plan_sha256": sha("5"),
                    "owner_ref": sha("e"),
                    "expected_digest": sha("b"),
                    "verification_kind": "READ_ONLY_SQL",
                    "rollback_trigger_ref": sha("f"),
                    "status": "PLANNED",
                }
            )
        ]
        data["post_change_invariants_expected_count"] = 1
        self.assertNotIn("POST_CHANGE_INVARIANTS_UNVERIFIED", codes(run(data)))

    def test_zero_receipt_rejects_boolean_count(self) -> None:
        data = packet()
        data["zero_change_receipt"]["affected_objects"] = False
        seal(data["zero_change_receipt"])
        self.assertIn("ZERO_CHANGE_RECEIPT_UNVERIFIABLE", codes(run(data)))

    def test_query_receipt_cannot_substitute_for_deploy_evidence(self) -> None:
        data = packet()
        data["query_receipt"] = {"verified": True}
        with self.assertRaisesRegex(ValueError, "unexpected top-level"):
            run(data)

    def test_strict_json_rejects_duplicates_and_nan(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicate"):
            analyzer._strict_json('{"a":1,"a":2}')
        with self.assertRaisesRegex(ValueError, "non-finite"):
            analyzer._strict_json('{"a":NaN}')

    def test_analysis_is_deterministic_and_nonmutating(self) -> None:
        data = packet()
        before = copy.deepcopy(data)
        self.assertEqual(run(data), run(data))
        self.assertEqual(data, before)

    def test_output_does_not_reflect_unknown_caller_text(self) -> None:
        data = packet()
        sentinel = "DO_NOT_REFLECT_ATTACKER_CONTROLLED_TEXT"
        data["terraform"]["platform"] = sentinel
        self.assertNotIn(sentinel, json.dumps(run(data)))

    def test_metadata_requires_exact_privacy_safe_fields(self) -> None:
        data = packet()
        data["metadata"]["account_name"] = "RAW_ACCOUNT_SENTINEL"
        self.assertIn("EVIDENCE_CONTEXT_INVALID_OR_STALE", codes(run(data)))

    def test_boolean_plan_and_preview_counts_are_rejected(self) -> None:
        data = packet()
        data["terraform"]["plan"]["resource_change_count"] = True
        data["terraform"]["plan"]["action_counts"]["no-op"] = True
        seal(data["terraform"]["plan"])
        data["terraform"]["preview_inventory"]["expected_count"] = False
        data["terraform"]["preview_inventory"]["detected_count"] = False
        seal(data["terraform"]["preview_inventory"])
        found = codes(run(data))
        self.assertIn("PLAN_RECEIPT_UNVERIFIABLE", found)
        self.assertIn("PROVIDER_PREVIEW_DENOMINATOR_UNVERIFIED", found)

    def test_state_inventory_must_bind_count_and_digest(self) -> None:
        data = packet()
        data["terraform"]["state"]["resource_count"] = 999
        data["terraform"]["state"]["resources_sha256"] = sha("f")
        self.assertIn("TERRAFORM_STATE_UNREADABLE_OR_UNBOUND", codes(run(data)))

    def test_unknown_plan_format_and_pre_v2_target_are_rejected(self) -> None:
        data = packet()
        data["terraform"]["plan"]["format_version"] = "garbage"
        seal(data["terraform"]["plan"])
        data["terraform"]["previous_provider_version"] = "1.5.0"
        data["terraform"]["provider_version"] = "1.5.0"
        data["terraform"]["selected_provider_version"] = "1.5.0"
        self.assertIn("PLAN_RECEIPT_UNVERIFIABLE", codes(run(data)))
        self.assertIn("TERRAFORM_TOOLCHAIN_OR_CONTEXT_UNVERIFIED", codes(run(data)))

        data = packet()
        data["terraform"]["plan"]["format_version"] = "1.99"
        seal(data["terraform"]["plan"])
        self.assertNotIn("PLAN_RECEIPT_UNVERIFIABLE", codes(run(data)))

    def test_migration_requires_dry_run_nonfuture_install_and_order(self) -> None:
        data = packet()
        row = data["migrations"][0]
        row.update({"dry_run_verified": False, "installed_at": "2099-01-01T00:00:00Z"})
        seal(row)
        refresh_migration_denominator(data)
        self.assertIn("MIGRATION_DENOMINATOR_UNVERIFIED", codes(run(data)))

    def test_historical_install_is_allowed_when_history_observation_is_current(self) -> None:
        data = packet()
        data["migrations"][0]["installed_at"] = "2024-01-01T00:00:00Z"
        seal(data["migrations"][0])
        refresh_migration_denominator(data)
        self.assertNotIn("MIGRATION_DENOMINATOR_UNVERIFIED", codes(run(data)))

        data = packet()
        second = copy.deepcopy(data["migrations"][0])
        data["migrations"][0]["version"] = "2.0.0"
        data["migrations"][0]["script_name"] = "V2.0.0__second.sql"
        seal(data["migrations"][0])
        second["migration_ref"] = sha("f")
        second["version"] = "1.0.0"
        second["script_name"] = "V1.0.0__first.sql"
        seal(second)
        data["migrations"].append(second)
        refresh_migration_denominator(data)
        self.assertIn("MIGRATION_DENOMINATOR_UNVERIFIED", codes(run(data)))

    def test_migration_install_cannot_postdate_history_observation(self) -> None:
        data = packet()
        data["migrations"][0]["installed_at"] = "2026-09-03T11:58:30Z"
        seal(data["migrations"][0])
        refresh_migration_denominator(data)
        self.assertIn("MIGRATION_DENOMINATOR_UNVERIFIED", codes(run(data)))

    def test_history_observation_must_be_current_even_inside_wide_window(self) -> None:
        data = packet()
        data["metadata"]["window_start"] = "2018-01-01T00:00:00Z"
        data["migrations_observed_at"] = "2020-01-01T00:00:00Z"
        self.assertIn("MIGRATION_DENOMINATOR_UNVERIFIED", codes(run(data)))

    def test_migration_versions_allow_underscores_and_script_groups_use_natural_order(self) -> None:
        data = packet()
        row = data["migrations"][0]
        row.update({"version": "1_1", "script_name": "V1_1__baseline.sql"})
        seal(row)
        refresh_migration_denominator(data)
        self.assertNotIn("MIGRATION_DENOMINATOR_UNVERIFIED", codes(run(data)))

        data = packet()
        first = data["migrations"][0]
        first.update(
            {
                "script_type": "R",
                "script_name": "R__view10.sql",
                "version": None,
                "migration_ref": sha("e"),
            }
        )
        seal(first)
        second = copy.deepcopy(first)
        second.update({"script_name": "R__view2.sql", "migration_ref": sha("f")})
        seal(second)
        data["migrations"] = [first, second]
        refresh_migration_denominator(data)
        self.assertIn("MIGRATION_DENOMINATOR_UNVERIFIED", codes(run(data)))

        data = packet()
        first = data["migrations"][0]
        first.update({"version": "1_1", "script_name": "V1_1__first.sql"})
        seal(first)
        second = copy.deepcopy(first)
        second.update({"version": "1.2", "script_name": "V1.2__second.sql", "migration_ref": sha("f")})
        seal(second)
        data["migrations"] = [first, second]
        refresh_migration_denominator(data)
        self.assertIn("MIGRATION_DENOMINATOR_UNVERIFIED", codes(run(data)))

    def test_repository_script_names_are_unique_case_insensitively(self) -> None:
        for script_type in ("R", "A"):
            with self.subTest(script_type=script_type):
                data = packet()
                first = data["migrations"][0]
                first.update(
                    {
                        "script_type": script_type,
                        "script_name": f"{script_type}__shared.sql",
                        "version": None,
                        "always_run_reviewed": script_type == "A",
                    }
                )
                seal(first)
                second = copy.deepcopy(first)
                second.update({"migration_ref": sha("f"), "script_name": f"{script_type.lower()}__SHARED.SQL"})
                seal(second)
                data["migrations"] = [first, second]
                refresh_migration_denominator(data)
                self.assertIn("MIGRATION_DENOMINATOR_UNVERIFIED", codes(run(data)))

    def test_repository_script_names_normalize_jinja_aliases(self) -> None:
        for script_type in ("R", "A"):
            for suffix in (".sql", ".cli.yml"):
                with self.subTest(script_type=script_type, suffix=suffix):
                    data = packet()
                    first = data["migrations"][0]
                    first.update(
                        {
                            "script_type": script_type,
                            "script_name": f"{script_type}__shared{suffix}",
                            "version": None,
                            "always_run_reviewed": script_type == "A",
                        }
                    )
                    seal(first)
                    second = copy.deepcopy(first)
                    second.update({"migration_ref": sha("f"), "script_name": f"{script_type}__shared{suffix}.jinja"})
                    seal(second)
                    data["migrations"] = [first, second]
                    refresh_migration_denominator(data)
                    self.assertIn("MIGRATION_DENOMINATOR_UNVERIFIED", codes(run(data)))

    def test_provider_chain_rejects_cycles_and_synthetic_leaps(self) -> None:
        data = packet()
        data["terraform"]["previous_provider_version"] = "2.18.0"
        data["provider_migrations"] = [
            provider_segment("2.18.0", "2.19.0"),
            provider_segment("2.19.0", "2.18.0"),
            provider_segment("2.18.0", "2.20.0"),
        ]
        data["provider_migrations_expected_count"] = 3
        self.assertIn("PROVIDER_MIGRATION_DENOMINATOR_UNVERIFIED", codes(run(data)))

        data["provider_migrations"] = [provider_segment("2.18.0", "2.20.0")]
        data["provider_migrations_expected_count"] = 1
        self.assertIn("PROVIDER_MIGRATION_DENOMINATOR_UNVERIFIED", codes(run(data)))

    def test_provider_segment_requires_fresh_immutable_source(self) -> None:
        data = packet()
        data["terraform"]["previous_provider_version"] = "2.19.0"
        row = provider_segment("2.19.0", "2.20.0")
        row["source_url"] = "https://github.com/snowflakedb/terraform-provider-snowflake/blob/main/MIGRATION_GUIDE.md"
        row["observed_at"] = "2020-01-01T00:00:00Z"
        seal(row)
        data["provider_migrations"] = [row]
        data["provider_migrations_expected_count"] = 1
        self.assertIn("PROVIDER_MIGRATION_DENOMINATOR_UNVERIFIED", codes(run(data)))

    def test_valid_provider_chain_passes_its_denominator(self) -> None:
        data = packet()
        data["terraform"]["previous_provider_version"] = "2.18.0"
        data["provider_migrations"] = [
            provider_segment("2.18.0", "2.19.0"),
            provider_segment("2.19.0", "2.20.0"),
        ]
        data["provider_migrations_expected_count"] = 2
        self.assertNotIn("PROVIDER_MIGRATION_DENOMINATOR_UNVERIFIED", codes(run(data)))

    def test_provider_target_is_exactly_v2(self) -> None:
        data = packet()
        for field in ("previous_provider_version", "provider_version", "selected_provider_version"):
            data["terraform"][field] = "3.0.0"
        data["terraform"]["preview_inventory"]["provider_version"] = "3.0.0"
        seal(data["terraform"]["preview_inventory"])
        self.assertIn("TERRAFORM_TOOLCHAIN_OR_CONTEXT_UNVERIFIED", codes(run(data)))

    def test_verified_provider_state_move_requires_completion_and_isolated_test(self) -> None:
        data = packet()
        data["terraform"]["previous_provider_version"] = "2.19.0"
        row = provider_segment("2.19.0", "2.20.0", status="VERIFIED")
        row.update({"state_move_required": True, "state_move_completed": False, "isolated_state_tested": False})
        seal(row)
        data["provider_migrations"] = [row]
        data["provider_migrations_expected_count"] = 1
        self.assertIn("PROVIDER_MIGRATION_DENOMINATOR_UNVERIFIED", codes(run(data)))

    def test_provider_affected_addresses_bind_to_plan_and_state(self) -> None:
        data = packet()
        data["terraform"]["previous_provider_version"] = "2.19.0"
        state_only_ref = sha("f")
        data["terraform"]["state"]["resource_refs"].append(state_only_ref)
        data["terraform"]["state"]["resource_count"] = 2
        data["terraform"]["state"]["resources_sha256"] = analyzer.bundle_digest(
            data["terraform"]["state"]["resource_refs"]
        )
        row = provider_segment("2.19.0", "2.20.0", status="VERIFIED")
        row.update(
            {
                "affected_address_refs": [state_only_ref],
                "affected_addresses_sha256": analyzer.bundle_digest([state_only_ref]),
                "state_move_required": True,
                "state_move_completed": True,
            }
        )
        seal(row)
        data["provider_migrations"] = [row]
        data["provider_migrations_expected_count"] = 1
        self.assertIn("PROVIDER_MIGRATION_DENOMINATOR_UNVERIFIED", codes(run(data)))

    def test_provider_state_move_requires_affected_addresses(self) -> None:
        data = packet()
        data["terraform"]["previous_provider_version"] = "2.19.0"
        row = provider_segment("2.19.0", "2.20.0", status="VERIFIED")
        row.update(
            {
                "affected_count": 0,
                "affected_address_refs": [],
                "affected_addresses_sha256": analyzer.bundle_digest([]),
                "state_move_required": True,
                "state_move_completed": True,
            }
        )
        seal(row)
        data["provider_migrations"] = [row]
        data["provider_migrations_expected_count"] = 1
        self.assertIn("PROVIDER_MIGRATION_DENOMINATOR_UNVERIFIED", codes(run(data)))

    def test_not_applicable_provider_segment_has_no_affected_work(self) -> None:
        data = packet()
        data["terraform"]["previous_provider_version"] = "2.19.0"
        row = provider_segment("2.19.0", "2.20.0")
        row.update(
            {
                "affected_count": 1,
                "affected_address_refs": [sha("1")],
                "affected_addresses_sha256": analyzer.bundle_digest([sha("1")]),
                "state_move_required": True,
                "state_move_completed": False,
            }
        )
        seal(row)
        data["provider_migrations"] = [row]
        data["provider_migrations_expected_count"] = 1
        self.assertIn("PROVIDER_MIGRATION_DENOMINATOR_UNVERIFIED", codes(run(data)))

    def test_terraform_action_arrays_are_exact(self) -> None:
        data = packet()
        data["terraform"]["resources"][0]["actions"] = ["delete-create"]
        self.assertIn("PLAN_RESOURCE_INVENTORY_INVALID", codes(run(data)))

    def test_provider_invalid_row_does_not_reflect_raw_text(self) -> None:
        data = packet()
        data["terraform"]["previous_provider_version"] = "2.18.0"
        row = provider_segment("2.18.0", "2.20.0")
        row["from_version"] = "ATTACKER_RAW_IDENTITY"
        seal(row)
        data["provider_migrations"] = [row]
        data["provider_migrations_expected_count"] = 1
        self.assertNotIn("ATTACKER_RAW_IDENTITY", json.dumps(run(data)))

    def test_extra_tool_key_does_not_leak(self) -> None:
        data = packet()
        data["tools"]["PRIVATE_TOOL_SENTINEL"] = {
            "version": "1.0.0",
            "source_url": "https://docs.snowflake.com/private",
            "observed_at": STAMP,
        }
        report = run(data)
        self.assertIn("DEPLOY_TOOLCHAIN_UNVERIFIED", codes(report))
        self.assertNotIn("PRIVATE_TOOL_SENTINEL", json.dumps(report))

    def test_official_urls_are_bound_to_their_evidence_surface(self) -> None:
        data = packet()
        data["tools"]["snowflake_cli"]["source_url"] = data["tools"]["schemachange"]["source_url"]
        data["bcr"]["source_url"] = "https://docs.snowflake.com/developer-guide/snowflake-cli/index"
        seal(data["bcr"])
        found = codes(run(data))
        self.assertIn("DEPLOY_TOOLCHAIN_UNVERIFIED", found)
        self.assertIn("BCR_INVENTORY_UNVERIFIED", found)

    def test_bcr_source_url_must_match_declared_bundle(self) -> None:
        data = packet()
        data["bcr"]["source_url"] = "https://docs.snowflake.com/en/release-notes/bcr-bundles/2025_05_bundle"
        seal(data["bcr"])
        self.assertIn("BCR_INVENTORY_UNVERIFIED", codes(run(data)))

    def test_nested_input_and_naive_datetime_fail_safely(self) -> None:
        data = packet()
        nested: dict = {}
        cursor = nested
        for _ in range(100):
            cursor["x"] = {}
            cursor = cursor["x"]
        data["metadata"]["extra"] = nested
        with self.assertRaisesRegex(ValueError, "nesting"):
            run(data)
        from datetime import datetime

        with self.assertRaisesRegex(ValueError, "timezone-aware"):
            analyzer.analyze(
                packet(),
                analysis_as_of=datetime(2026, 9, 3, 12, 5),
                trusted_bundle_sha256=analyzer.bundle_digest(packet()),
            )

    def test_dbt_project_binds_bcr_and_noop_artifact(self) -> None:
        data = packet()
        add_dbt_project(data)
        self.assertFalse(run(data)["dbt_projects"][0]["safe"])

        data = packet()
        add_dbt_project(data, staged_sha=sha("f"))
        found = codes(run(data))
        self.assertIn("DBT_PROJECT_PREFLIGHT_INCOMPLETE-0", found)
        self.assertFalse(run(data)["dbt_projects"][0]["safe"])

        data = packet()
        add_dbt_project(data)
        item = next(item for item in data["bcr"]["inventory"] if item["item_id"] == "BCR-2362")
        item["affected"] = False
        item["affected_refs"] = []
        item["disposition"] = "NOT_APPLICABLE"
        seal(item)
        data["bcr"]["inventory_sha256"] = analyzer.bundle_digest(data["bcr"]["inventory"])
        seal(data["bcr"])
        self.assertIn("DBT_PROJECT_DENOMINATOR_UNVERIFIED", codes(run(data)))

    def test_dbt_version_model_obeys_bundle_and_demigration_state(self) -> None:
        data = packet()
        add_dbt_project(data)
        data["dbt_projects"][0]["target_model"] = "LIVE"
        seal(data["dbt_projects"][0])
        report = run(data)
        self.assertIn("DBT_PROJECT_BCR_NOT_ACTIVE-0", codes(report))
        self.assertFalse(report["dbt_projects"][0]["safe"])

        data = packet()
        add_dbt_project(data)
        row = data["dbt_projects"][0]
        row.update(
            {
                "target_model": "LIVE",
                "early_opt_in_verified": True,
                "early_opt_in_ref": sha("c"),
                "demigration_available": True,
            }
        )
        seal(row)
        report = run(data)
        self.assertNotIn("DBT_PROJECT_BCR_NOT_ACTIVE-0", codes(report))
        self.assertNotIn("DBT_PROJECT_DEMIGRATION_BOUNDARY_INVALID-0", codes(report))

        data = packet()
        add_dbt_project(data)
        row = data["dbt_projects"][0]
        row.update({"early_opt_in_verified": True, "early_opt_in_ref": None})
        seal(row)
        self.assertIn("DBT_PROJECT_DENOMINATOR_UNVERIFIED", codes(run(data)))

        data = packet()
        add_dbt_project(data)
        data["bcr"]["status"] = "RELEASED"
        seal(data["bcr"])
        data["dbt_projects"][0]["bundle_status"] = "RELEASED"
        seal(data["dbt_projects"][0])
        found = codes(run(data))
        self.assertIn("DBT_PROJECT_LIVE_VERSION_REQUIRED-0", found)
        self.assertNotIn("DBT_PROJECT_DEMIGRATION_BOUNDARY_INVALID-0", found)
        self.assertFalse(run(data)["dbt_projects"][0]["safe"])

        data = packet()
        add_dbt_project(data)
        data["bcr"]["status"] = "ENABLED"
        seal(data["bcr"])
        data["dbt_projects"][0]["bundle_status"] = "ENABLED"
        data["dbt_projects"][0]["target_model"] = "LIVE"
        seal(data["dbt_projects"][0])
        report = run(data)
        self.assertIn("DBT_PROJECT_DEMIGRATION_BOUNDARY_INVALID-0", codes(report))
        self.assertFalse(report["dbt_projects"][0]["safe"])

        data = packet()
        add_dbt_project(data)
        data["bcr"]["status"] = "ENABLED"
        seal(data["bcr"])
        data["dbt_projects"][0]["bundle_status"] = "ENABLED"
        data["dbt_projects"][0]["demigration_available"] = False
        seal(data["dbt_projects"][0])
        report = run(data)
        self.assertNotIn("DBT_PROJECT_DEMIGRATION_BOUNDARY_INVALID-0", codes(report))

    def test_source_has_no_network_process_or_write_capability(self) -> None:
        tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
        allowed_imports = {
            "__future__",
            "argparse",
            "collections",
            "datetime",
            "hashlib",
            "json",
            "pathlib",
            "re",
            "sys",
            "typing",
        }
        imported, calls = set(), set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                calls.add(node.func.attr)
        self.assertLessEqual(imported, allowed_imports)
        self.assertFalse(calls & {"write", "write_text", "write_bytes", "unlink", "rename", "system", "run", "Popen"})


if __name__ == "__main__":
    unittest.main()
