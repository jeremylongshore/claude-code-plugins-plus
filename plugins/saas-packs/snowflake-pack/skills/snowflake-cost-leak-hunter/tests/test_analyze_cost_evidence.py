from __future__ import annotations

import importlib.util
import hashlib
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

COLLECTOR_SCRIPT = SKILL_DIR / "scripts" / "collect_snowflake_evidence.py"
COLLECTOR_SPEC = importlib.util.spec_from_file_location("collect_snowflake_evidence", COLLECTOR_SCRIPT)
assert COLLECTOR_SPEC and COLLECTOR_SPEC.loader
COLLECTOR = importlib.util.module_from_spec(COLLECTOR_SPEC)
COLLECTOR_SPEC.loader.exec_module(COLLECTOR)


class CostEvidenceTests(unittest.TestCase):
    def load_fixture(self, name: str) -> dict:
        return json.loads((FIXTURES / name).read_text(encoding="utf-8"))

    def valid_receipt(self, data: dict) -> dict:
        raw = []
        for dataset in ("warehouse_metering", "query_attribution", "warehouse_load", "serverless_usage"):
            raw.extend({"EVIDENCE": {"_dataset": dataset, **row}} for row in data.get(dataset, []))
        _, sql, sources = COLLECTOR.load_surface("cost")
        return COLLECTOR.build_receipt(
            "cost",
            "readonly",
            sql,
            sources,
            raw=raw,
            collected_at=data["metadata"]["generated_at"],
        )

    def rehash_receipt(self, receipt: dict) -> None:
        body = dict(receipt)
        body.pop("receipt_sha256", None)
        receipt["receipt_sha256"] = f"sha256:{hashlib.sha256(COLLECTOR.canonical_json(body)).hexdigest()}"

    def test_classifies_observed_estimated_and_at_risk_separately(self) -> None:
        result = MODULE.analyze(self.load_fixture("cost_evidence.json"))
        self.assertTrue(result["completeness_claim_blocked"])
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

    def test_excludes_rows_outside_requested_window(self) -> None:
        data = self.load_fixture("cost_evidence.json")
        data["warehouse_metering"].append(
            {
                "start_time": "2026-07-31T23:00:00Z",
                "end_time": "2026-08-01T00:00:00Z",
                "warehouse_name": "OUTSIDE_WH",
                "credits_used_compute": "99",
                "credits_attributed_compute_queries": "99",
                "credits_used_cloud_services": "0",
            }
        )
        result = MODULE.analyze(data)
        confirmed = {item["metric"]: item for item in result["confirmed_observations"]}
        self.assertEqual(confirmed["warehouse_compute_credits"]["credits"], "30.5")
        self.assertTrue(any("excluded 1 row(s)" in item for item in result["warnings"]))

    def test_rejects_raw_identity_and_query_tag_fields(self) -> None:
        for field in ("user_name", "query_tag"):
            data = self.load_fixture("cost_evidence.json")
            data["query_attribution"][0][field] = "raw-value"
            with self.subTest(field=field), self.assertRaises(MODULE.EvidenceError):
                MODULE.analyze(data)

    def test_verified_collector_receipt_is_accepted(self) -> None:
        data = self.load_fixture("cost_evidence.json")
        data["collector_receipt"] = self.valid_receipt(data)
        result = MODULE.analyze(data)
        self.assertEqual(result["collector_receipt_assessment"]["status"], "verified")
        self.assertFalse(result["completeness_claim_blocked"])

    def test_truncated_or_error_receipt_blocks_completeness(self) -> None:
        for mutation in ("truncate", "error"):
            data = self.load_fixture("cost_evidence.json")
            receipt = self.valid_receipt(data)
            if mutation == "truncate":
                receipt["truncation_possible"] = True
            else:
                receipt["status"] = "error"
                receipt["errors"] = [{"code": "SNOW_CLI_FAILED", "message": "permission denied"}]
            self.rehash_receipt(receipt)
            data["collector_receipt"] = receipt
            result = MODULE.analyze(data)
            self.assertEqual(result["collector_receipt_assessment"]["status"], "unverifiable")
            self.assertTrue(result["completeness_claim_blocked"])
            self.assertTrue(any("collector receipt unverifiable" in item for item in result["warnings"]))

    def test_rejects_sql_shaped_query_hash(self) -> None:
        data = self.load_fixture("cost_evidence.json")
        data["query_attribution"][0]["query_hash"] = "SELECT secret FROM customer_data"
        with self.assertRaises(MODULE.EvidenceError):
            MODULE.analyze(data)

    def test_receipt_source_provenance_mismatch_blocks_completeness(self) -> None:
        data = self.load_fixture("cost_evidence.json")
        receipt = self.valid_receipt(data)
        receipt["source_views"] = ["SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY"]
        self.rehash_receipt(receipt)
        data["collector_receipt"] = receipt
        result = MODULE.analyze(data)
        self.assertTrue(result["completeness_claim_blocked"])
        self.assertIn(
            "source_views do not match the reviewed cost SQL", result["collector_receipt_assessment"]["issues"]
        )

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

    def test_attribution_pareto_and_bounded_right_sizing_are_explicit(self) -> None:
        data = self.load_fixture("cost_evidence.json")
        data["warehouse_metering"][0]["warehouse_id"] = "wh-1"
        data["warehouse_metering"][1]["warehouse_id"] = "wh-2"
        data["query_attribution"] = [
            {
                "query_id": "q1",
                "query_parameterized_hash": "slow",
                "warehouse_name": "ETL_WH",
                "start_time": "2026-08-03T00:00:00Z",
                "end_time": "2026-08-03T01:00:00Z",
                "query_tag_present": True,
                "credits_attributed_compute": "12",
                "credits_used_query_acceleration": "0",
                "total_elapsed_time_ms": "3000",
            },
            {
                "query_id": "q2",
                "query_parameterized_hash": "cheap",
                "warehouse_name": "BI_WH",
                "start_time": "2026-08-04T00:00:00Z",
                "end_time": "2026-08-04T01:00:00Z",
                "query_tag_present": True,
                "credits_attributed_compute": "2",
                "credits_used_query_acceleration": "0",
                "total_elapsed_time_ms": "1000",
            },
        ]
        data["metadata"]["right_sizing"] = {
            "warehouse": "ETL_WH",
            "current_size": "MEDIUM",
            "candidate_sizes": ["LARGE"],
            "max_size_steps": 1,
            "measurement_window": "same 7-day window",
            "success_criteria": "p95 latency <= baseline and no queue regression",
        }
        result = MODULE.analyze(data)
        self.assertEqual(len(result["attribution_completeness"]), 2)
        self.assertTrue(result["cost_latency_pareto"])
        self.assertEqual(result["right_sizing_experiment"]["status"], "bounded_proposal")
        self.assertFalse(result["right_sizing_experiment"]["mutation_executed"])

    def test_null_attribution_is_unknown_not_zero(self) -> None:
        data = self.load_fixture("cost_evidence.json")
        data["warehouse_metering"][0]["credits_attributed_compute_queries"] = None
        result = MODULE.analyze(data)
        item = next(item for item in result["attribution_completeness"] if item["warehouse_name"] == "ETL_WH")
        self.assertEqual(item["status"], "unknown")
        self.assertEqual(item["unattributed_credits"], "unknown")


if __name__ == "__main__":
    unittest.main()
