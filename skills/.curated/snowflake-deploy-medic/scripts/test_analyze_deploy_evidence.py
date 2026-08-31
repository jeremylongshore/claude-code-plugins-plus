#!/usr/bin/env python3
"""Stdlib fixture tests for analyze_deploy_evidence.py."""

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


if __name__ == "__main__":
    unittest.main()
