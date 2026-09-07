from __future__ import annotations

import ast
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("analyzer", HERE / "analyze_native_app_release.py")
assert SPEC and SPEC.loader
ANALYZER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ANALYZER)
COLLECTOR_SPEC = importlib.util.spec_from_file_location("collector", HERE / "collect_snowflake_evidence.py")
assert COLLECTOR_SPEC and COLLECTOR_SPEC.loader
COLLECTOR = importlib.util.module_from_spec(COLLECTOR_SPEC)
COLLECTOR_SPEC.loader.exec_module(COLLECTOR)

NOW = "2026-09-04T12:00:00Z"
H = "a" * 64
D = "sha256:" + "b" * 64


def context(*, cohort: bool = False, count: int = 1) -> dict:
    row = {
        "_dataset": "execution_context",
        "observed_at": NOW,
        "organization_name_sha256": H,
        "account_identifier_sha256": H,
        "collector_user_sha256": H,
        "primary_role_sha256": H,
        "primary_role_type": "ROLE",
        "secondary_roles_sha256": H,
        "timezone": "UTC",
        "selected_package_key_sha256": H,
        "source_row_count": count,
        "source_row_limit": 5000,
        "truncation_possible": False,
        "provider_latency_documented": cohort,
    }
    if cohort:
        row.update(
            {
                "provider_latency_seconds": 600,
                "provider_latency_semantics": "APPROXIMATE_CURRENT_SNAPSHOT_NOT_SETTLEMENT",
            }
        )
    return row


def receipt(surface: str, record: dict | list[dict], dataset: str, *, cohort: bool = False) -> dict:
    _, template, sql, sources, selector = COLLECTOR.render_surface(surface, application_package="APP_PACKAGE")
    records = record if isinstance(record, list) else [record]
    raw = [{"EVIDENCE": context(cohort=cohort, count=sum(item.get("instance_count", 1) for item in records))}]
    raw.extend({"EVIDENCE": {"_dataset": dataset, **item}} for item in records)
    return COLLECTOR.build_receipt(
        surface,
        "observer",
        sql,
        sources,
        raw=raw,
        template_sql=template,
        template_path=HERE / "sql" / COLLECTOR.SUBSURFACES[surface][0],
        selector=selector,
        collection_mode="live-cli",
        collected_at=NOW,
        collection_started_at=NOW,
        collection_completed_at=NOW,
    )


def bundle() -> dict:
    version = {
        "package_key_sha256": H,
        "version_key_sha256": H,
        "version": "2.0",
        "patch": 0,
        "state": "READY",
        "review_status": "APPROVED",
        "created_on": NOW,
        "dropped_on": None,
    }
    previous = {
        "package_key_sha256": H,
        "version_key_sha256": "c" * 64,
        "version": "1.0",
        "patch": 0,
        "state": "READY",
        "review_status": "APPROVED",
        "created_on": NOW,
        "dropped_on": None,
    }
    directive = {
        "package_key_sha256": H,
        "directive_key_sha256": H,
        "target_type": "DEFAULT",
        "target_key_sha256": None,
        "version": "1.0",
        "patch": 0,
        "release_status": "DEPLOYED",
        "release_channel": "DEFAULT",
        "upgrade_in_maintenance_window": True,
        "upgrade_deadline": None,
        "modified_on": NOW,
    }
    cohort = {
        "package_key_sha256": H,
        "cohort_key_sha256": H,
        "current_version": "1.0",
        "current_patch": 0,
        "previous_version_state": "COMPLETE",
        "previous_version": "0.9",
        "previous_patch": 1,
        "upgrade_state": "COMPLETE",
        "target_version": None,
        "target_patch": None,
        "instance_count": 1,
        "latest_state_updated_on": NOW,
        "latest_upgrade_attempted_on": None,
        "maximum_upgrade_attempt": 0,
    }
    receipts = {
        "native-app-versions-current": receipt("native-app-versions-current", [version, previous], "versions"),
        "native-app-release-directives-current": receipt(
            "native-app-release-directives-current", directive, "release_directives"
        ),
        "native-app-upgrade-cohorts-current": receipt(
            "native-app-upgrade-cohorts-current", cohort, "upgrade_cohorts", cohort=True
        ),
    }
    result = {
        "schema_version": "2",
        "release": {
            "package_key_sha256": H,
            "distribution": "EXTERNAL",
            "release_channel": "DEFAULT",
            "target_version": "2.0",
            "target_patch": 0,
            "manifest_version": 2,
            "previous_manifest_version": 2,
            "release_kind": "MAJOR",
            "automated_privileges_changed": False,
            "manifest_sha256": D,
            "setup_sha256": D,
            "expected_cohort_count": 1,
            "expected_installed_instance_count": 1,
            "expected_setup_statement_count": 1,
            "setup_statements": [
                {
                    "statement_key_sha256": H,
                    "ordinal": 1,
                    "replay_safe": True,
                    "grant_effect": "PRESERVES_GRANTS",
                    "restore_ordinal": None,
                    "forbidden_construct": False,
                }
            ],
            "expected_privilege_delta_count": 0,
            "privilege_deltas": [],
            "expected_reference_count": 1,
            "references": [
                {
                    "reference_key_sha256": H,
                    "object_types_sha256": D,
                    "privileges_sha256": D,
                    "callback_registered": True,
                }
            ],
            "expected_app_spec_delta_count": 0,
            "app_spec_deltas": [],
        },
        "receipts": receipts,
        "compatibility": {
            "expected_count": 1,
            "rows": [
                {
                    "from_version": "1.0",
                    "from_patch": 0,
                    "target_version": "2.0",
                    "target_patch": 0,
                    "status": "COMPATIBLE",
                }
            ],
        },
        "rollback": {
            "previous_version": "1.0",
            "previous_patch": 0,
            "artifact_sha256": D,
            "tested": True,
            "privileges_preserved": True,
            "app_specs_reconciled": True,
            "owner_receipt_sha256": D,
        },
        "lifecycle": {
            "expected_event_count": 1,
            "events": [
                {
                    "event_key_sha256": H,
                    "package_key_sha256": H,
                    "cohort_key_sha256": H,
                    "version": "1.0",
                    "patch": 0,
                    "event_type": "INSTALL",
                    "observed_at": NOW,
                    "outcome": "SUCCEEDED",
                }
            ],
            "receipt_sha256": D,
            "observed_at": NOW,
        },
    }
    body = dict(result["lifecycle"])
    body.pop("receipt_sha256")
    result["lifecycle"]["receipt_sha256"] = ANALYZER.digest(body)
    rollback_body = dict(result["rollback"])
    rollback_body.pop("owner_receipt_sha256")
    result["rollback"]["owner_receipt_sha256"] = ANALYZER.digest(rollback_body)
    return result


def reseal_receipt(value: dict, surface: str) -> None:
    receipt_value = value["receipts"][surface]
    receipt_value["dataset_row_counts"] = {key: len(rows) for key, rows in sorted(receipt_value["datasets"].items())}
    receipt_value["row_count"] = sum(receipt_value["dataset_row_counts"].values())
    receipt_value["result_sha256"] = ANALYZER.digest(receipt_value["datasets"])
    receipt_value["receipt_sha256"] = ANALYZER.receipt_self_hash(receipt_value)


def reseal_lifecycle(value: dict) -> None:
    body = dict(value["lifecycle"])
    body.pop("receipt_sha256")
    value["lifecycle"]["receipt_sha256"] = ANALYZER.digest(body)


class NativeAppAnalyzerTests(unittest.TestCase):
    def analyze(self, value: dict) -> dict:
        cohorts = value["receipts"]["native-app-upgrade-cohorts-current"]["datasets"]["upgrade_cohorts"]
        cohort_trust = ANALYZER.digest(
            {
                "expected_cohort_count": value["release"]["expected_cohort_count"],
                "expected_installed_instance_count": value["release"]["expected_installed_instance_count"],
                "rows": cohorts,
            }
        )
        return ANALYZER.analyze(
            value,
            ANALYZER.parse_time(NOW),
            D,
            D,
            cohort_trust,
            value["lifecycle"]["receipt_sha256"],
            value["rollback"]["owner_receipt_sha256"],
        )

    def test_safe_cohort_is_as_of_only_and_dry_run(self) -> None:
        report = self.analyze(bundle())
        self.assertEqual(report["status"], "READY_FOR_OPERATOR_RELEASE_AS_OF")
        self.assertTrue(report["dry_run"])
        self.assertFalse(report["safe_to_publish"])

    def test_analyzer_has_no_snowflake_subprocess_or_write_path(self) -> None:
        tree = ast.parse((HERE / "analyze_native_app_release.py").read_text(encoding="utf-8"))
        imports = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        calls = {
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        }
        self.assertNotIn("subprocess", imports)
        self.assertFalse({"run", "Popen", "write_text", "write_bytes"} & calls)
        self.assertNotIn("snowflake", imports)

    def test_named_release_scenarios_are_packaged(self) -> None:
        fixtures = HERE.parent / "fixtures"
        self.assertEqual(
            {path.name for path in fixtures.glob("*.json")},
            {
                "safe-cohorts.json",
                "partial-setup-failure.json",
                "removed-grants.json",
                "incompatible-versions.json",
                "missing-scans.json",
            },
        )
        for path in fixtures.glob("*.json"):
            self.assertIsInstance(json.loads(path.read_text(encoding="utf-8"))["scenario"], str)

    def test_partial_setup_and_removed_grants_block(self) -> None:
        value = bundle()
        value["release"]["setup_statements"][0].update(
            replay_safe=False, grant_effect="REMOVES_GRANTS", restore_ordinal=3
        )
        value["release"]["privilege_deltas"] = [
            {
                "delta_key_sha256": H,
                "principal_key_sha256": H,
                "object_key_sha256": H,
                "privilege_sha256": D,
                "action": "REMOVE",
                "automated": True,
            }
        ]
        value["release"]["expected_privilege_delta_count"] = 1
        report = self.analyze(value)
        self.assertIn("PARTIAL_SETUP_REPLAY_UNSAFE", report["findings"])
        self.assertIn("PARTIAL_SETUP_GRANT_GAP", report["findings"])
        self.assertIn("REMOVED_PRIVILEGE", report["findings"])

    def test_v2_patch_automated_delta_cannot_hide_behind_false_flag(self) -> None:
        for action in ("ADD", "REMOVE"):
            value = bundle()
            value["release"].update(release_kind="PATCH", automated_privileges_changed=False)
            value["release"]["expected_privilege_delta_count"] = 1
            value["release"]["privilege_deltas"] = [
                {
                    "delta_key_sha256": H,
                    "principal_key_sha256": H,
                    "object_key_sha256": H,
                    "privilege_sha256": D,
                    "action": action,
                    "automated": True,
                }
            ]
            with self.subTest(action=action):
                report = self.analyze(value)
                self.assertIn("AUTOMATED_PRIVILEGE_CHANGE_CONTRADICTION", report["findings"])
                self.assertIn("V2_AUTOMATED_PRIVILEGE_PATCH_CHANGE", report["findings"])

    def test_missing_scan_incompatible_and_bad_cohort_block(self) -> None:
        value = bundle()
        versions = value["receipts"]["native-app-versions-current"]["datasets"]["versions"]
        next(row for row in versions if row["version"] == "2.0")["review_status"] = "IN_PROGRESS"
        value["compatibility"] = {"expected_count": 0, "rows": []}
        value["receipts"]["native-app-upgrade-cohorts-current"]["datasets"]["upgrade_cohorts"][0]["upgrade_state"] = (
            "FAILED"
        )
        for surface in ("native-app-versions-current", "native-app-upgrade-cohorts-current"):
            r = value["receipts"][surface]
            r["result_sha256"] = ANALYZER.digest(r["datasets"])
            r["receipt_sha256"] = ANALYZER.receipt_self_hash(r)
        report = self.analyze(value)
        self.assertIn("SECURITY_SCAN_NOT_APPROVED", report["findings"])
        self.assertIn("INCOMPATIBLE_OR_UNTESTED_COHORT", report["findings"])
        self.assertIn("UNSAFE_UPGRADE_COHORT", report["findings"])

    def test_qa_does_not_invent_scan_approval(self) -> None:
        value = bundle()
        value["release"]["release_channel"] = "QA"
        version_receipt = value["receipts"]["native-app-versions-current"]
        version_receipt["datasets"]["versions"][0]["review_status"] = "NOT_REVIEWED"
        version_receipt["result_sha256"] = ANALYZER.digest(version_receipt["datasets"])
        version_receipt["receipt_sha256"] = ANALYZER.receipt_self_hash(version_receipt)
        self.assertNotIn("SECURITY_SCAN_NOT_APPROVED", self.analyze(value)["findings"])

    def test_queued_cohort_is_blocking(self) -> None:
        value = bundle()
        value["receipts"]["native-app-upgrade-cohorts-current"]["datasets"]["upgrade_cohorts"][0]["upgrade_state"] = (
            "QUEUED"
        )
        reseal_receipt(value, "native-app-upgrade-cohorts-current")
        self.assertIn("UNSAFE_UPGRADE_COHORT", self.analyze(value)["findings"])

    def test_app_spec_pending_and_manifest_v1_block(self) -> None:
        value = bundle()
        value["release"]["manifest_version"] = 1
        value["release"]["previous_manifest_version"] = 1
        value["release"]["expected_app_spec_delta_count"] = 1
        value["release"]["app_spec_deltas"] = [
            {
                "spec_key_sha256": H,
                "change": "ADD",
                "definition_sha256": D,
                "current_sequence": 0,
                "target_sequence": 1,
                "status": "PENDING",
                "approval_observed_at": NOW,
            }
        ]
        report = self.analyze(value)
        self.assertIn("APP_SPEC_REQUIRES_MANIFEST_V2", report["findings"])
        self.assertIn("APP_SPEC_APPROVAL_UNPROVED", report["findings"])

    def test_app_spec_change_requires_next_sequence_and_nonfuture_approval(self) -> None:
        for current_sequence, target_sequence, observed_at in (
            (2, 4, NOW),
            (2, 3, "2026-09-04T12:00:01Z"),
            (-10, 1, NOW),
        ):
            value = bundle()
            value["release"]["expected_app_spec_delta_count"] = 1
            value["release"]["app_spec_deltas"] = [
                {
                    "spec_key_sha256": H,
                    "change": "CHANGE",
                    "definition_sha256": D,
                    "current_sequence": current_sequence,
                    "target_sequence": target_sequence,
                    "status": "APPROVED",
                    "approval_observed_at": observed_at,
                }
            ]
            with self.subTest(
                current_sequence=current_sequence,
                target_sequence=target_sequence,
                observed_at=observed_at,
            ):
                self.assertIn("APP_SPEC_APPROVAL_UNPROVED", self.analyze(value)["findings"])

    def test_app_spec_add_starts_at_sequence_one(self) -> None:
        for current_sequence, target_sequence in ((9, 9), (0, 2)):
            value = bundle()
            value["release"]["expected_app_spec_delta_count"] = 1
            value["release"]["app_spec_deltas"] = [
                {
                    "spec_key_sha256": H,
                    "change": "ADD",
                    "definition_sha256": D,
                    "current_sequence": current_sequence,
                    "target_sequence": target_sequence,
                    "status": "APPROVED",
                    "approval_observed_at": NOW,
                }
            ]
            with self.subTest(current_sequence=current_sequence, target_sequence=target_sequence):
                self.assertIn("APP_SPEC_APPROVAL_UNPROVED", self.analyze(value)["findings"])

    def test_strict_context_and_provider_timestamp_types(self) -> None:
        cases = (
            ("provider_latency_documented", "true"),
            ("primary_role_type", "DATABASE_ROLE"),
        )
        for field, invalid_value in cases:
            value = bundle()
            context_row = value["receipts"]["native-app-versions-current"]["datasets"]["execution_context"][0]
            context_row[field] = invalid_value
            reseal_receipt(value, "native-app-versions-current")
            with self.subTest(field=field), self.assertRaises(ANALYZER.Invalid):
                self.analyze(value)

        for timestamp in ("not-a-timestamp", "2026-09-04T12:00:01Z"):
            value = bundle()
            versions = value["receipts"]["native-app-versions-current"]["datasets"]["versions"]
            versions[0]["created_on"] = timestamp
            reseal_receipt(value, "native-app-versions-current")
            with self.subTest(timestamp=timestamp), self.assertRaises(ANALYZER.Invalid):
                self.analyze(value)

    def test_semantic_duplicate_directives_and_cohorts_are_invalid(self) -> None:
        directive_value = bundle()
        directives = directive_value["receipts"]["native-app-release-directives-current"]["datasets"][
            "release_directives"
        ]
        duplicate_directive = dict(directives[0], directive_key_sha256="c" * 64)
        directives.append(duplicate_directive)
        directive_value["receipts"]["native-app-release-directives-current"]["datasets"]["execution_context"][0][
            "source_row_count"
        ] = 2
        reseal_receipt(directive_value, "native-app-release-directives-current")
        with self.assertRaisesRegex(ANALYZER.Invalid, "DUPLICATE_NATURAL_IDENTITY"):
            self.analyze(directive_value)

        cohort_value = bundle()
        cohorts = cohort_value["receipts"]["native-app-upgrade-cohorts-current"]["datasets"]["upgrade_cohorts"]
        cohorts.append(dict(cohorts[0], cohort_key_sha256="c" * 64))
        cohort_value["release"].update(expected_cohort_count=2, expected_installed_instance_count=2)
        cohort_value["receipts"]["native-app-upgrade-cohorts-current"]["datasets"]["execution_context"][0][
            "source_row_count"
        ] = 2
        reseal_receipt(cohort_value, "native-app-upgrade-cohorts-current")
        with self.assertRaisesRegex(ANALYZER.Invalid, "DUPLICATE_NATURAL_IDENTITY"):
            self.analyze(cohort_value)

    def test_lifecycle_must_be_fresh_and_bound_to_package_version_and_cohort(self) -> None:
        mutations = (
            {"observed_at": "not-a-timestamp"},
            {"observed_at": "2026-09-04T12:00:01Z"},
            {"package_key_sha256": "c" * 64},
            {"cohort_key_sha256": "c" * 64},
            {"version": "9.9"},
            {"version": {"malformed": True}},
            {"outcome": "FAILED"},
        )
        for mutation in mutations:
            value = bundle()
            value["lifecycle"]["events"][0].update(mutation)
            reseal_lifecycle(value)
            with self.subTest(mutation=mutation):
                self.assertIn("LIFECYCLE_COMPLETENESS_UNPROVED", self.analyze(value)["findings"])

    def test_uninstall_event_does_not_prove_current_cohort_coverage(self) -> None:
        value = bundle()
        value["lifecycle"]["events"][0]["event_type"] = "UNINSTALL"
        reseal_lifecycle(value)
        self.assertIn("LIFECYCLE_COMPLETENESS_UNPROVED", self.analyze(value)["findings"])

    def test_all_provider_version_fields_fail_closed_on_non_strings(self) -> None:
        cases = (
            ("native-app-versions-current", "versions", "version"),
            ("native-app-release-directives-current", "release_directives", "version"),
            ("native-app-upgrade-cohorts-current", "upgrade_cohorts", "current_version"),
        )
        for surface, dataset, field in cases:
            value = bundle()
            value["receipts"][surface]["datasets"][dataset][0][field] = {"malformed": True}
            reseal_receipt(value, surface)
            with self.subTest(surface=surface, field=field), self.assertRaises(ANALYZER.Invalid):
                self.analyze(value)

        value = bundle()
        value["compatibility"]["rows"][0]["from_version"] = {"malformed": True}
        self.assertIn("COMPATIBILITY_ROW_INVALID", self.analyze(value)["findings"])

    def test_rollback_digest_binds_artifact_and_owner_receipt(self) -> None:
        value = bundle()
        value["rollback"]["artifact_sha256"] = "sha256:" + "c" * 64
        self.assertIn("ROLLBACK_UNPROVED", self.analyze(value)["findings"])

    def test_tampering_cap_raw_identity_and_bool_integer_fail(self) -> None:
        for mutate in (
            lambda value: value["receipts"]["native-app-versions-current"].update(truncation_possible=True),
            lambda value: value.update(package_name="private"),
            lambda value: value["release"].update(target_patch=True),
        ):
            value = bundle()
            mutate(value)
            with self.assertRaises(ANALYZER.Invalid):
                self.analyze(value)

    def test_stale_receipt_target_mismatch_and_finalizing_block(self) -> None:
        stale = bundle()
        stale_receipt = stale["receipts"]["native-app-release-directives-current"]
        stale_receipt["collected_at"] = "2026-09-04T11:00:00Z"
        stale_receipt["collection_completed_at"] = "2026-09-04T11:00:00Z"
        stale_receipt["receipt_sha256"] = ANALYZER.receipt_self_hash(stale_receipt)
        with self.assertRaises(ANALYZER.Invalid):
            self.analyze(stale)

        value = bundle()
        cohort = value["receipts"]["native-app-upgrade-cohorts-current"]["datasets"]["upgrade_cohorts"][0]
        cohort.update(previous_version_state="FINALIZING", target_version="3.0", target_patch=0)
        cohort_receipt = value["receipts"]["native-app-upgrade-cohorts-current"]
        cohort_receipt["result_sha256"] = ANALYZER.digest(cohort_receipt["datasets"])
        cohort_receipt["receipt_sha256"] = ANALYZER.receipt_self_hash(cohort_receipt)
        report = self.analyze(value)
        self.assertIn("UNSAFE_UPGRADE_COHORT", report["findings"])
        self.assertIn("COHORT_TARGET_MISMATCH", report["findings"])

    def test_cli_error_is_non_reflective(self) -> None:
        value = bundle()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"
            path.write_text(json.dumps(value), encoding="utf-8")
            completed = subprocess.run(
                [
                    "python3",
                    str(HERE / "analyze_native_app_release.py"),
                    "--input",
                    str(path),
                    "--evaluated-at",
                    NOW,
                    "--trusted-input-sha256",
                    D,
                    "--trusted-manifest-sha256",
                    D,
                    "--trusted-setup-sha256",
                    D,
                    "--trusted-cohort-sha256",
                    D,
                    "--trusted-lifecycle-sha256",
                    D,
                    "--trusted-rollback-sha256",
                    D,
                ],
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(json.loads(completed.stdout)["findings"], ["EVIDENCE_REJECTED"])


if __name__ == "__main__":
    unittest.main()
