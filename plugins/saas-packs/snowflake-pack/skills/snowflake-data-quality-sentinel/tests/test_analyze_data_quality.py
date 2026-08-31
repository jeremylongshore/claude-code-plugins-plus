#!/usr/bin/env python3
"""Behavior tests for the deterministic Snowflake data-quality analyzer."""

from __future__ import annotations

import copy
import importlib.util
import json
import pathlib
import subprocess
import sys
import unittest


HERE = pathlib.Path(__file__).resolve().parent
SCRIPT = HERE.parent / "scripts" / "analyze_data_quality.py"
SPEC = importlib.util.spec_from_file_location("analyze_data_quality", SCRIPT)
assert SPEC and SPEC.loader
analyzer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(analyzer)


class DataQualityAnalyzerTests(unittest.TestCase):
    def fixture(self, name: str) -> dict:
        return json.loads((HERE / "fixtures" / name).read_text(encoding="utf-8"))

    def codes(self, report: dict) -> set[str]:
        return {finding["code"] for finding in report["findings"]}

    def test_clean_denominator_passes_both_statuses(self):
        report = analyzer.analyze(self.fixture("pass.json"))
        self.assertEqual(report["quality_status"], "PASS")
        self.assertEqual(report["monitoring_status"], "PASS")
        self.assertEqual(report["findings"], [])
        self.assertEqual(report["denominator"]["requirements"], 1)
        self.assertRegex(report["receipt_sha256"], r"^sha256:[0-9a-f]{64}$")

    def test_problem_fixture_separates_quality_failure_and_monitoring_failure(self):
        report = analyzer.analyze(self.fixture("problems.json"))
        self.assertEqual(report["quality_status"], "FAIL")
        self.assertEqual(report["monitoring_status"], "FAIL")
        self.assertTrue(
            {
                "DQ_EXPECTATION_VIOLATED",
                "DQ_ASSOCIATION_SUSPENDED",
                "DQ_SCHEDULE_UPDATE_PENDING",
                "DQ_NOTIFICATION_DISABLED",
                "DQ_EXECUTION_ROLE_DRIFT",
                "DQ_GROUP_COVERAGE_GAP",
                "DQ_RESULT_STALE",
                "DQ_ANOMALY_TRAINING",
                "DQ_USAGE_VISIBILITY_GAP",
            }
            <= self.codes(report)
        )

    def test_failed_evaluation_is_inconclusive_not_violation(self):
        data = self.fixture("pass.json")
        measurement = data["measurements"][0]
        measurement["evaluation_status"] = "FAILED"
        measurement["expectation_violated"] = None
        report = analyzer.analyze(data)
        self.assertEqual(report["quality_status"], "INCONCLUSIVE")
        self.assertEqual(report["monitoring_status"], "DEGRADED")
        self.assertIn("DQ_EXPECTATION_EVALUATION_FAILED", self.codes(report))
        self.assertNotIn("DQ_EXPECTATION_VIOLATED", self.codes(report))

    def test_anomaly_training_is_not_health(self):
        data = self.fixture("pass.json")
        data["requirements"][0]["objective"] = {"mode": "anomaly", "name": "row-count-anomaly"}
        data["associations"][0]["anomaly_status"] = "TRAINING_IN_PROGRESS"
        data["measurements"][0]["anomaly_detected"] = False
        report = analyzer.analyze(data)
        self.assertEqual(report["quality_status"], "INCONCLUSIVE")
        self.assertEqual(report["monitoring_status"], "DEGRADED")
        self.assertIn("DQ_ANOMALY_TRAINING", self.codes(report))

    def test_anomaly_detected_fails_quality_only(self):
        data = self.fixture("pass.json")
        data["requirements"][0]["objective"] = {"mode": "anomaly", "name": "row-count-anomaly"}
        data["measurements"][0]["anomaly_detected"] = True
        report = analyzer.analyze(data)
        self.assertEqual(report["quality_status"], "FAIL")
        self.assertEqual(report["monitoring_status"], "PASS")
        self.assertIn("DQ_ANOMALY_DETECTED", self.codes(report))

    def test_raw_metric_without_objective_is_observation_not_violation(self):
        data = self.fixture("pass.json")
        data["requirements"][0]["objective"] = None
        report = analyzer.analyze(data)
        self.assertEqual(report["quality_status"], "INCONCLUSIVE")
        self.assertNotIn("DQ_EXPECTATION_VIOLATED", self.codes(report))
        self.assertTrue({"DQ_OBJECTIVE_MISSING", "DQ_METRIC_OBSERVED_NO_OBJECTIVE"} <= self.codes(report))

    def test_missing_association_and_result_do_not_pass(self):
        data = self.fixture("pass.json")
        data["associations"] = []
        data["measurements"] = []
        report = analyzer.analyze(data)
        self.assertEqual(report["quality_status"], "INCONCLUSIVE")
        self.assertEqual(report["monitoring_status"], "FAIL")
        self.assertTrue({"DQ_ASSOCIATION_MISSING", "DQ_RESULT_MISSING"} <= self.codes(report))

    def test_edition_unavailable_is_bounded_inconclusive_blocker(self):
        data = self.fixture("pass.json")
        data["associations"] = []
        data["measurements"] = []
        data["source_metadata"][0]["status"] = "edition_unavailable"
        data["source_metadata"][0]["error_code"] = "ENTERPRISE_EDITION_REQUIRED"
        report = analyzer.analyze(data)
        self.assertEqual(report["quality_status"], "INCONCLUSIVE")
        self.assertEqual(report["monitoring_status"], "INCONCLUSIVE")
        self.assertIn("DQ_EDITION_UNAVAILABLE", self.codes(report))
        self.assertNotIn("DQ_RESULT_MISSING", self.codes(report))

    def test_notification_privilege_error_is_explicit(self):
        data = self.fixture("pass.json")
        data["source_metadata"].append(
            {
                "source": "notification-control",
                "kind": "notification",
                "status": "error",
                "collected_at": "2026-08-31T12:00:00Z",
                "latest_record_at": None,
                "max_latency_seconds": 1800,
                "row_count": 0,
                "error_code": "INSUFFICIENT_PRIVILEGES",
            }
        )
        report = analyzer.analyze(data)
        self.assertEqual(report["monitoring_status"], "FAIL")
        self.assertIn("DQ_NOTIFICATION_PRIVILEGE_ERROR", self.codes(report))

    def test_unsupported_object_is_not_silently_accepted(self):
        data = self.fixture("pass.json")
        data["requirements"][0]["object"]["type"] = "STAGE"
        report = analyzer.analyze(data)
        self.assertEqual(report["quality_status"], "INCONCLUSIVE")
        self.assertEqual(report["monitoring_status"], "FAIL")
        self.assertIn("DQ_UNSUPPORTED_OBJECT", self.codes(report))

    def test_empty_denominator_has_explicit_no_required_checks_status(self):
        data = self.fixture("pass.json")
        data["requirements"] = []
        data["associations"] = []
        data["measurements"] = []
        report = analyzer.analyze(data)
        self.assertEqual(report["quality_status"], "NO_REQUIRED_CHECKS")
        self.assertEqual(report["monitoring_status"], "NO_REQUIRED_CHECKS")

    def test_output_is_deterministic(self):
        data = self.fixture("problems.json")
        first = analyzer.analyze(copy.deepcopy(data))
        second = analyzer.analyze(copy.deepcopy(data))
        self.assertEqual(first, second)
        self.assertEqual(first["receipt_sha256"], second["receipt_sha256"])

    def test_rejects_raw_rows_pii_credentials_sql_and_presigned_urls(self):
        bad_fields = {
            "raw_failed_rows": [{"value": "x"}],
            "email": "person@example.com",
            "password": "never",
            "query_text": "select customer data",
            "presigned_url": "https://bucket.example/file?X-Amz-Signature=abc",
        }
        for field, value in bad_fields.items():
            with self.subTest(field=field):
                data = self.fixture("pass.json")
                data[field] = value
                with self.assertRaises(analyzer.EvidenceError):
                    analyzer.analyze(data)

    def test_rejects_pii_and_signed_url_values_even_under_neutral_keys(self):
        values = [
            "person@example.com",
            "192.0.2.10",
            "123-45-6789",
            "Bearer abcdefghijklmnop",
            "https://bucket.example/file?sig=abc",
        ]
        for value in values:
            with self.subTest(value=value):
                data = self.fixture("pass.json")
                data["measurements"][0]["observed_value"] = value
                with self.assertRaises(analyzer.EvidenceError):
                    analyzer.analyze(data)

    def test_rejects_measurements_outside_declared_window(self):
        data = self.fixture("pass.json")
        data["measurements"][0]["measured_at"] = "2099-01-01T00:00:00Z"
        with self.assertRaisesRegex(analyzer.EvidenceError, "window_start/window_end"):
            analyzer.analyze(data)

    def test_rejects_future_and_out_of_window_source_receipts(self):
        for field, value in (
            ("collected_at", "2099-01-01T00:00:00Z"),
            ("latest_record_at", "2099-01-01T00:00:00Z"),
            ("latest_record_at", "2026-08-29T00:00:00Z"),
        ):
            with self.subTest(field=field, value=value):
                data = self.fixture("pass.json")
                data["source_metadata"][0][field] = value
                with self.assertRaises(analyzer.EvidenceError):
                    analyzer.analyze(data)

        data = self.fixture("pass.json")
        data["metadata"]["collected_at"] = "2099-01-01T00:00:00Z"
        with self.assertRaisesRegex(analyzer.EvidenceError, "cannot be in the future"):
            analyzer.analyze(data)

    def test_cli_returns_two_for_unsafe_input(self):
        data = self.fixture("pass.json")
        data["measurements"][0]["sql_text"] = "SELECT sensitive_column FROM table"
        completed = subprocess.run(
            [sys.executable, str(SCRIPT)],
            input=json.dumps(data),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(completed.stdout, "")
        self.assertIn("prohibited field", completed.stderr)

    def test_current_association_and_notification_state_are_required_for_health(self):
        data = self.fixture("pass.json")
        data["current_state"]["associations"][0]["status"] = "SUSPENDED"
        data["current_state"]["associations"][0]["notification_status"] = "DISABLED"
        data["current_state"]["notifications"][0]["status"] = "DISABLED"
        report = analyzer.analyze(data)
        self.assertEqual(report["quality_status"], "INCONCLUSIVE")
        self.assertEqual(report["monitoring_status"], "FAIL")
        self.assertTrue(
            {"DQ_CURRENT_ASSOCIATION_NOT_ACTIVE", "DQ_CURRENT_NOTIFICATION_DISABLED"}
            <= self.codes(report)
        )

    def test_stale_current_state_blocks_monitoring_claim(self):
        data = self.fixture("pass.json")
        data["current_state"]["observed_at"] = "2026-08-30T12:00:00Z"
        report = analyzer.analyze(data)
        self.assertIn("DQ_CURRENT_STATE_STALE", self.codes(report))
        self.assertEqual(report["monitoring_status"], "INCONCLUSIVE")

    def test_current_state_shape_rejects_raw_group_values_and_duplicates(self):
        data = self.fixture("pass.json")
        data["current_state"]["associations"][0]["raw_group_values"] = ["customer@example.com"]
        with self.assertRaises(analyzer.EvidenceError):
            analyzer.analyze(data)

        data = self.fixture("pass.json")
        duplicate = dict(data["current_state"]["associations"][0])
        data["current_state"]["associations"].append(duplicate)
        with self.assertRaisesRegex(analyzer.EvidenceError, "duplicate current association"):
            analyzer.analyze(data)


if __name__ == "__main__":
    unittest.main()
