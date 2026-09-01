#!/usr/bin/env python3
"""Stdlib fixture tests for analyze_deploy_evidence.py."""

import hashlib
import json
import pathlib
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import analyze_deploy_evidence as analyzer  # noqa: E402


class DeployAnalyzerTests(unittest.TestCase):
    def load(self, name):
        return json.loads((HERE / "fixtures" / name).read_text(encoding="utf-8"))

    def rehash(self, value):
        body = dict(value)
        body.pop("receipt_sha256", None)
        value["receipt_sha256"] = (
            "sha256:"
            + hashlib.sha256(
                json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
            ).hexdigest()
        )

    def test_unsafe_fixture_finds_adoption_checksum_and_release_risks(self):
        report = analyzer.analyze(self.load("unsafe-deploy.json"))
        codes = {item["code"] for item in report["findings"]}
        self.assertTrue(
            {
                "GRANT_IMPORT_REQUIRED",
                "DESTRUCTIVE_PLAN_CHANGE",
                "VERSIONED_CHECKSUM_DRIFT",
                "VERSION_COLLISION",
                "REPEATABLE_CHANGE_DETECTED",
                "BCR_NOT_CHECKED",
                "ROLLBACK_UNTESTED",
            }
            <= codes
        )
        self.assertFalse(report["zero_change_plan"])
        self.assertEqual(report["provider"]["major"], 2)
        self.assertEqual(report["ordered_recovery"][0]["for"], "EVIDENCE_PROVENANCE_INCOMPLETE")

    def test_clean_fixture_is_zero_change_and_has_no_findings(self):
        report = analyzer.analyze(self.load("clean-preview.json"))
        self.assertTrue(report["zero_change_plan"])
        self.assertEqual(report["release_gate"], "pass")
        self.assertEqual(report["findings"], [])
        self.assertGreaterEqual(len(report["post_deploy_invariants"]), 7)
        self.assertEqual(report["provider"]["version"], "2.20.0")
        self.assertEqual(report["toolchain"]["snowflake_cli"]["version"], "3.12.0")
        self.assertEqual(report["behavior_change_review"]["id"], "BCR-2026-08")
        self.assertEqual(report["migration_evidence"][0]["checksum_status"], "match")
        self.assertTrue(report["rollback_receipt"]["tested"])
        self.assertEqual(report["provenance"]["collected_at"], "2026-08-30T12:00:00Z")

    def test_pre_two_provider_and_missing_plan_are_blocking_findings(self):
        report = analyzer.analyze({"terraform": {"version": "1.5", "state": {"parseable": False}}})
        codes = {item["code"] for item in report["findings"]}
        self.assertIn("PROVIDER_PRE_2", codes)
        self.assertIn("TERRAFORM_STATE_UNREADABLE", codes)
        self.assertIn("PLAN_NOT_VERIFIED", codes)
        self.assertIn("TOOLCHAIN_UNVERIFIED", codes)
        self.assertIn("BCR_NOT_CHECKED", codes)
        self.assertIn("ROLLBACK_UNTESTED", codes)
        self.assertIn("EVIDENCE_PROVENANCE_INCOMPLETE", codes)
        self.assertEqual(report["release_gate"], "blocked")

    def test_rejects_fake_booleans_numbers_and_timestamps(self):
        data = self.load("clean-preview.json")
        data["metadata"]["collected_at"] = "not-a-time"
        data["terraform"]["plan"]["generated_at"] = "tomorrow-ish"
        data["terraform"]["plan"]["exit_code"] = False
        data["terraform"]["plan"]["changes"] = False
        data["terraform"]["state"]["parseable"] = "false"
        data["bcr"]["checked"] = "passed"
        data["bcr"]["checked_at"] = "never"
        data["rollback"]["tested"] = "ok"
        data["rollback"]["tested_at"] = "eventually"
        report = analyzer.analyze(data)
        codes = {item["code"] for item in report["findings"]}
        self.assertIn("EVIDENCE_PROVENANCE_INCOMPLETE", codes)
        self.assertIn("TERRAFORM_STATE_UNREADABLE", codes)
        self.assertIn("PLAN_NOT_VERIFIED", codes)
        self.assertIn("BCR_NOT_CHECKED", codes)
        self.assertIn("ROLLBACK_UNTESTED", codes)
        self.assertFalse(report["zero_change_plan"])
        self.assertEqual(report["release_gate"], "blocked")

    def test_requires_exact_provider_tool_versions_and_safe_backend(self):
        data = self.load("clean-preview.json")
        del data["terraform"]["provider_source"]
        data["terraform"]["version"] = "2garbage"
        data["tools"]["snowflake_cli"]["version"] = "latest"
        data["terraform"]["backend"] = "https://user:" + "password@state.example/path?token=abc123"
        report = analyzer.analyze(data)
        self.assertEqual(report["release_gate"], "blocked")
        self.assertIsNone(report["provenance"]["backend"])
        self.assertNotIn("abc123", json.dumps(report))

    def test_rejects_secret_bearing_fields(self):
        data = self.load("clean-preview.json")
        data["api_key"] = "never"
        with self.assertRaises(ValueError):
            analyzer.analyze(data)

    def test_rejects_credential_shaped_values_under_neutral_keys(self):
        for value in (
            "password=supersecret",
            "Authorization: Bearer abcdefghijklmnop",
            "-----BEGIN PRIVATE KEY-----",
        ):
            data = self.load("clean-preview.json")
            data["note"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                analyzer.analyze(data)

    def test_malformed_collections_and_blank_rollback_cannot_pass(self):
        for mutate in (
            lambda data: data["terraform"].__setitem__("resources", {"destroy": True}),
            lambda data: data.__setitem__("migrations", {"checksum": "drift"}),
            lambda data: data["terraform"].__setitem__("resources", ["not-an-object"]),
        ):
            data = self.load("clean-preview.json")
            mutate(data)
            with self.assertRaises(ValueError):
                analyzer.analyze(data)
        data = self.load("clean-preview.json")
        data["rollback"]["strategy"] = ""
        self.assertEqual(analyzer.analyze(data)["release_gate"], "blocked")

    def test_preflight_backup_affected_objects_and_zero_change_receipt_are_gates(self):
        data = self.load("clean-preview.json")
        for field in ("preflight", "state_backup", "affected_objects", "zero_change_receipt"):
            candidate = json.loads(json.dumps(data))
            if field == "affected_objects":
                candidate["affected_objects_verified"] = False
            else:
                candidate.pop(field, None)
            report = analyzer.analyze(candidate)
            codes = {item["code"] for item in report["findings"]}
            expected = {
                "preflight": "PREFLIGHT_INCOMPLETE",
                "state_backup": "STATE_BACKUP_MISSING",
                "affected_objects": "AFFECTED_OBJECTS_UNVERIFIED",
                "zero_change_receipt": "ZERO_CHANGE_RECEIPT_MISSING",
            }[field]
            self.assertIn(expected, codes)

    def test_bcr_inventory_requires_disposition_for_affected_change(self):
        data = self.load("clean-preview.json")
        data["bcr"]["inventory"] = [{"id": "BCR-1", "source": "release notes", "affected": True}]
        codes = {item["code"] for item in analyzer.analyze(data)["findings"]}
        self.assertIn("BCR_AFFECTED_UNRESOLVED-0", codes)

    def test_future_preflight_and_backup_receipts_block_gate(self):
        for field in ("preflight", "state_backup"):
            data = self.load("clean-preview.json")
            data[field]["checked_at" if field == "preflight" else "captured_at"] = "2099-01-01T00:00:00Z"
            report = analyzer.analyze(data)
            self.assertEqual(report["release_gate"], "blocked")
            self.assertIn("EVIDENCE_PROVENANCE_INCOMPLETE", {item["code"] for item in report["findings"]})

    def test_future_zero_change_receipt_is_blocked_and_recovery_is_ordered(self):
        data = self.load("clean-preview.json")
        data["zero_change_receipt"]["issued_at"] = "2099-01-01T00:00:00Z"
        report = analyzer.analyze(data)
        self.assertEqual(report["release_gate"], "blocked")
        self.assertIn("ZERO_CHANGE_RECEIPT_MISSING", {item["code"] for item in report["findings"]})
        self.assertIn("ZERO_CHANGE_RECEIPT_MISSING", {item["for"] for item in report["ordered_recovery"]})

    def test_plan_and_state_receipt_tamper_are_blocking(self):
        for target, field, value, code in (
            ("plan", "changes", 1, "PLAN_RECEIPT_UNVERIFIABLE"),
            ("state_backup", "state_sha256", "c" * 64, "STATE_BACKUP_RECEIPT_UNVERIFIABLE"),
        ):
            data = self.load("clean-preview.json")
            container = data["terraform"]["plan"] if target == "plan" else data["state_backup"]
            container[field] = value
            report = analyzer.analyze(data)
            self.assertIn(code, {item["code"] for item in report["findings"]})
            self.assertEqual(report["release_gate"], "blocked")

    def test_provider_migration_segments_are_versioned_and_hash_bound(self):
        data = self.load("clean-preview.json")
        segment = {
            "from_version": "2.19.0",
            "to_version": "2.20.0",
            "source": "official migration guide",
            "status": "VERIFIED",
            "affected_addresses": [],
            "state_move_required": False,
        }
        self.rehash(segment)
        data["provider_migrations"] = [segment]
        self.assertEqual(analyzer.analyze(data)["release_gate"], "pass")
        segment["status"] = "OPEN"
        report = analyzer.analyze(data)
        codes = {item["code"] for item in report["findings"]}
        self.assertIn("PROVIDER_MIGRATION_SEGMENT_UNVERIFIABLE-0", codes)
        self.rehash(segment)
        codes = {item["code"] for item in analyzer.analyze(data)["findings"]}
        self.assertIn("PROVIDER_MIGRATION_SEGMENT_OPEN-0", codes)

    def test_preview_feature_remains_blocking_even_with_a_green_plan(self):
        data = self.load("clean-preview.json")
        data["terraform"]["preview_features"] = ["snowflake_table_resource"]
        report = analyzer.analyze(data)
        self.assertIn("PROVIDER_PREVIEW_FEATURE", {item["code"] for item in report["findings"]})
        self.assertEqual(report["release_gate"], "blocked")

    def test_dbt_project_live_version_bcr_support_and_rollback_are_gated(self):
        data = self.load("clean-preview.json")
        project = {
            "name": "analytics",
            "current_model": "VERSIONED",
            "target_model": "LIVE",
            "bcr_disposition": "OPEN",
            "target_version_supported": False,
            "deployed_code_sha256": "a" * 64,
            "staged_code_sha256": "b" * 64,
            "rollback_artifact_sha256": "",
        }
        self.rehash(project)
        data["dbt_projects"] = [project]
        codes = {item["code"] for item in analyzer.analyze(data)["findings"]}
        self.assertTrue(
            {
                "DBT_PROJECT_BCR_UNRESOLVED-0",
                "DBT_PROJECT_VERSION_UNSUPPORTED-0",
                "DBT_PROJECT_ROLLBACK_UNBOUNDED-0",
            }.issubset(codes)
        )

    def test_nonzero_plan_requires_hashed_post_change_invariant_denominator(self):
        data = self.load("clean-preview.json")
        data["terraform"]["plan"]["exit_code"] = 2
        data["terraform"]["plan"]["changes"] = 1
        self.rehash(data["terraform"]["plan"])
        data["post_change_invariants_verified"] = False
        report = analyzer.analyze(data)
        self.assertIn("POST_CHANGE_INVARIANTS_MISSING", {item["code"] for item in report["findings"]})
        self.assertEqual(report["release_gate"], "blocked")


if __name__ == "__main__":
    unittest.main()
