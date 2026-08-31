from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_DIR / "scripts" / "analyze_cost_evidence.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures"

SPEC = importlib.util.spec_from_file_location("analyze_cost_evidence", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class CostEvidenceTests(unittest.TestCase):
    def load_fixture(self, name: str) -> dict:
        return json.loads((FIXTURES / name).read_text(encoding="utf-8"))

    def test_classifies_observed_estimated_and_at_risk_separately(self) -> None:
        result = MODULE.analyze(self.load_fixture("cost_evidence.json"))
        confirmed = {item["metric"]: item for item in result["confirmed_observations"]}
        self.assertEqual(confirmed["warehouse_compute_credits"]["credits"], "30.5")
        self.assertEqual(
            confirmed["query_attributed_compute_credits_excluding_idle"]["credits"],
            "16",
        )
        self.assertEqual(confirmed["serverless:SNOWPIPE"]["credits"], "3.25")

        estimates = {item["basis"]: item for item in result["estimated_amounts"]}
        self.assertEqual(estimates["warehouse"]["classification"], "estimated")
        self.assertEqual(Decimal(estimates["warehouse"]["amount"]), Decimal("83.875"))

        idle = {
            item.get("warehouse_name"): item for item in result["at_risk_opportunities"] if item.get("warehouse_name")
        }
        self.assertEqual(idle["ETL_WH"]["credits"], "5.5")
        self.assertEqual(idle["BI_WH"]["credits"], "0.5")
        self.assertIn(
            "untagged_query_attributed_compute",
            {item.get("metric") for item in result["at_risk_opportunities"]},
        )
        self.assertTrue(any("not reconciled" in item for item in result["warnings"]))
        self.assertTrue(result["approval_queue"])
        self.assertTrue(all(item["competing_explanation"] for item in result["at_risk_opportunities"]))

    def test_unknown_surface(self) -> None:
        result = MODULE.analyze(self.load_fixture("cost_evidence_partial.json"))
        self.assertFalse(result["at_risk_opportunities"])
        confirmed_metrics = {item["metric"] for item in result["confirmed_observations"]}
        self.assertNotIn("query_attributed_compute_credits_excluding_idle", confirmed_metrics)
        warnings = "\n".join(result["warnings"])
        self.assertIn("attributed-query credits are NULL", warnings)
        self.assertIn("query_attribution evidence absent", warnings)
        self.assertIn("freshness unknown", warnings)

    def test_rejects_negative_credits(self) -> None:
        data = self.load_fixture("cost_evidence.json")
        data["warehouse_metering"][0]["credits_used_compute"] = "-1"
        with self.assertRaises(MODULE.EvidenceError):
            MODULE.analyze(data)

    def test_rejects_future_or_missing_source_timestamp_for_rows(self) -> None:
        future = self.load_fixture("cost_evidence.json")
        future["source_max_times"]["warehouse_metering"] = "2026-08-09T00:00:00Z"
        with self.assertRaises(MODULE.EvidenceError):
            MODULE.analyze(future)
        missing = self.load_fixture("cost_evidence.json")
        del missing["source_max_times"]["warehouse_metering"]
        with self.assertRaises(MODULE.EvidenceError):
            MODULE.analyze(missing)

    def test_requires_scope_owner_approval_and_non_future_collection(self) -> None:
        for field in ("account", "role", "review_owner", "approval_boundary"):
            data = self.load_fixture("cost_evidence.json")
            data["metadata"][field] = ""
            with self.subTest(field=field), self.assertRaises(MODULE.EvidenceError):
                MODULE.analyze(data)
        future = self.load_fixture("cost_evidence.json")
        future["metadata"]["generated_at"] = "2099-01-01T00:00:00Z"
        with self.assertRaises(MODULE.EvidenceError):
            MODULE.analyze(future)
        incomplete_window = self.load_fixture("cost_evidence.json")
        incomplete_window["metadata"]["generated_at"] = "2026-08-02T00:00:00Z"
        with self.assertRaises(MODULE.EvidenceError):
            MODULE.analyze(incomplete_window)

    def test_source_max_before_window_end_is_bounded_partial(self) -> None:
        data = self.load_fixture("cost_evidence.json")
        data["source_max_times"]["warehouse_metering"] = "2026-08-07T23:00:00Z"
        result = MODULE.analyze(data)
        self.assertEqual(result["coverage_status"], "bounded_partial")
        self.assertTrue(any("coverage is partial" in item for item in result["warnings"]))

    def test_missing_metric_fields_are_unknown_not_confirmed_zero(self) -> None:
        cases = (
            ("warehouse_metering", "credits_used_compute"),
            ("warehouse_metering", "credits_used_cloud_services"),
            ("query_attribution", "credits_attributed_compute"),
            ("query_attribution", "credits_used_query_acceleration"),
            ("serverless_usage", "credits_used"),
        )
        for surface, field in cases:
            data = self.load_fixture("cost_evidence.json")
            del data[surface][0][field]
            with self.subTest(surface=surface, field=field), self.assertRaises(MODULE.EvidenceError):
                MODULE.analyze(data)

    def test_rejects_secret_fields_and_unsafe_report_text(self) -> None:
        secret = self.load_fixture("cost_evidence.json")
        secret["metadata"]["access_token"] = "never"
        with self.assertRaises(MODULE.EvidenceError):
            MODULE.analyze(secret)
        for field, value in (
            ("provenance", "https://rates.example/download?token=rawsecret"),
            ("currency", "USD|forged"),
        ):
            data = self.load_fixture("cost_evidence.json")
            data["credit_rates"]["warehouse"][field] = value
            with self.subTest(field=field), self.assertRaises(MODULE.EvidenceError):
                MODULE.analyze(data)
        injected = self.load_fixture("cost_evidence.json")
        injected["warehouse_metering"][0]["warehouse_name"] = "WH\n## forged"
        with self.assertRaises(MODULE.EvidenceError):
            MODULE.analyze(injected)

    def test_cli_writes_json_and_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            json_out = Path(directory) / "report.json"
            markdown_out = Path(directory) / "report.md"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--input",
                    str(FIXTURES / "cost_evidence.json"),
                    "--json-out",
                    str(json_out),
                    "--markdown-out",
                    str(markdown_out),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(json.loads(json_out.read_text())["schema_version"], "1.0")
            markdown = markdown_out.read_text(encoding="utf-8")
            self.assertIn("## Confirmed observations", markdown)
            self.assertIn("## Estimated amounts", markdown)
            self.assertIn("## At-risk opportunities", markdown)


if __name__ == "__main__":
    unittest.main()
