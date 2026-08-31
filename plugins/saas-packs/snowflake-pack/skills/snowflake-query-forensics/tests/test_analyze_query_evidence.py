from __future__ import annotations

import importlib.util
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_DIR / "scripts" / "analyze_query_evidence.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures"

SPEC = importlib.util.spec_from_file_location("analyze_query_evidence", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

COLLECTOR_SCRIPT = SKILL_DIR / "scripts" / "collect_snowflake_evidence.py"
COLLECTOR_SPEC = importlib.util.spec_from_file_location("collect_snowflake_evidence", COLLECTOR_SCRIPT)
assert COLLECTOR_SPEC and COLLECTOR_SPEC.loader
COLLECTOR = importlib.util.module_from_spec(COLLECTOR_SPEC)
COLLECTOR_SPEC.loader.exec_module(COLLECTOR)


class QueryEvidenceTests(unittest.TestCase):
    def load_fixture(self, name: str) -> dict:
        return json.loads((FIXTURES / name).read_text(encoding="utf-8"))

    def valid_receipt(self, data: dict) -> dict:
        raw = []
        for dataset in ("query_history", "warehouse_load"):
            if dataset in data:
                value = data.get(dataset, [])
                rows = [value] if isinstance(value, dict) else value
                raw.extend({"EVIDENCE": {"_dataset": dataset, **row}} for row in rows if isinstance(row, dict))
        _, sql, sources = COLLECTOR.load_surface("query")
        return COLLECTOR.build_receipt(
            "query",
            "readonly",
            sql,
            sources,
            raw=raw,
            collected_at=data["metadata"]["collected_at"],
        )

    def rehash_receipt(self, receipt: dict) -> None:
        body = dict(receipt)
        body.pop("receipt_sha256", None)
        receipt["receipt_sha256"] = f"sha256:{hashlib.sha256(COLLECTOR.canonical_json(body)).hexdigest()}"

    def valid_subsurface_receipt(self, surface: str, data: dict) -> dict:
        query_id = data["metadata"]["query_id"]
        path, template_sql, rendered_sql, sources, selector = COLLECTOR.render_surface(
            surface,
            query_id=query_id,
        )
        return COLLECTOR.build_receipt(
            surface,
            "readonly",
            rendered_sql,
            sources,
            raw=[],
            collected_at=data["metadata"]["collected_at"],
            template_sql=template_sql,
            template_path=path,
            selector=selector,
        )

    def test_separates_observations_ratios_and_hypotheses(self) -> None:
        result = MODULE.analyze(self.load_fixture("query_evidence.json"))
        self.assertTrue(result["completeness_claim_blocked"])
        confirmed_metrics = {item["metric"] for item in result["confirmed_observations"]}
        self.assertIn("queued_overload_time_ms", confirmed_metrics)
        self.assertIn("transaction_blocked_time_ms", confirmed_metrics)
        self.assertIn("bytes_spilled_remote_storage", confirmed_metrics)
        self.assertIn("QUERY_INSIGHT_REMOTE_SPILLAGE", confirmed_metrics)

        derived = {(item["metric"], item["operator_id"]): item for item in result["estimated_or_derived_metrics"]}
        self.assertEqual(derived[("output_to_input_row_multiple", "3")]["value"], "5")
        self.assertEqual(derived[("partitions_scanned_fraction", "3")]["value"], "1")
        self.assertEqual(derived[("partitions_scanned_fraction", "4")]["value"], "0.2")

        hypotheses = {item["hypothesis"] for item in result["at_risk_hypotheses"]}
        self.assertIn("join expansion requires semantic review", hypotheses)
        self.assertIn("no partition pruning observed for this scan", hypotheses)
        self.assertIn("query shape or warehouse capacity contributed to remote spill", hypotheses)
        self.assertEqual(result["top_operators_by_observed_percentage"][0]["operator_id"], "3")
        self.assertEqual(result["timeline_ms"]["total_elapsed_time_ms"], "153000")
        self.assertEqual(result["timeline_ms"]["other_or_unexplained_time_ms"], "0")
        self.assertTrue(all(item["falsification_evidence"] for item in result["at_risk_hypotheses"]))

    def test_running_query_reports_unknown_operator_state(self) -> None:
        result = MODULE.analyze(self.load_fixture("query_evidence_incomplete.json"))
        self.assertFalse(result["estimated_or_derived_metrics"])
        self.assertFalse(result["at_risk_hypotheses"])
        warnings = "\n".join(result["warnings"])
        self.assertIn("operator statistics absent", warnings)
        self.assertIn("until completion", warnings)
        self.assertIn("absence is not proof", warnings)

    def test_running_query_does_not_interpret_supplied_operator_evidence(self) -> None:
        data = self.load_fixture("query_evidence.json")
        data["query_history"]["execution_status"] = "running"
        result = MODULE.analyze(data)
        self.assertEqual(result["top_operators_by_observed_percentage"], [])
        operator_hypotheses = {
            "join expansion requires semantic review",
            "no partition pruning observed for this scan",
            "query shape or warehouse capacity contributed to remote spill",
        }
        self.assertTrue(operator_hypotheses.isdisjoint({item["hypothesis"] for item in result["at_risk_hypotheses"]}))
        self.assertFalse(any(item["kind"] == "operator" for item in result["confirmed_observations"]))

    def test_rejects_impossible_percentages_and_partition_counts(self) -> None:
        percentage = self.load_fixture("query_evidence.json")
        percentage["operators"][0]["execution_time_breakdown"]["overall_percentage"] = 1000
        with self.assertRaises(MODULE.EvidenceError):
            MODULE.analyze(percentage)
        partitions = self.load_fixture("query_evidence.json")
        partitions["operators"][0]["operator_statistics"]["pruning"] = {
            "partitions_scanned": 200,
            "partitions_total": 100,
        }
        with self.assertRaises(MODULE.EvidenceError):
            MODULE.analyze(partitions)

    def test_rejects_negative_operator_counter(self) -> None:
        data = self.load_fixture("query_evidence.json")
        data["operators"][0]["operator_statistics"]["input_rows"] = -1
        with self.assertRaises(MODULE.EvidenceError):
            MODULE.analyze(data)

    def test_rejects_future_history_timestamp(self) -> None:
        data = self.load_fixture("query_evidence.json")
        data["metadata"]["history_source_max_time"] = "2026-08-30T12:00:00Z"
        with self.assertRaises(MODULE.EvidenceError):
            MODULE.analyze(data)

    def test_requires_scope_owner_and_non_future_collection(self) -> None:
        for field in ("account", "role", "history_source", "experiment_owner"):
            data = self.load_fixture("query_evidence.json")
            data["metadata"][field] = ""
            with self.subTest(field=field), self.assertRaises(MODULE.EvidenceError):
                MODULE.analyze(data)
        future = self.load_fixture("query_evidence.json")
        future["metadata"]["collected_at"] = "2099-01-01T00:00:00Z"
        future["metadata"]["history_source_max_time"] = "2098-01-01T00:00:00Z"
        with self.assertRaises(MODULE.EvidenceError):
            MODULE.analyze(future)

    def test_redacts_insight_messages_and_rejects_secret_fields(self) -> None:
        data = self.load_fixture("query_evidence.json")
        data["query_insights"][0]["message"] = "password=hunter2 token=abc123 https://signed.example/?sig=xyz"
        rendered = json.dumps(MODULE.analyze(data))
        self.assertNotIn("hunter2", rendered)
        self.assertNotIn("abc123", rendered)
        self.assertNotIn("signed.example", rendered)
        for field in ("api_key", "SESSION_TOKEN", "jwt"):
            bad = self.load_fixture("query_evidence.json")
            bad[field] = "never"
            with self.subTest(field=field), self.assertRaises(MODULE.EvidenceError):
                MODULE.analyze(bad)

    def test_cli_writes_json_and_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            json_out = Path(directory) / "packet.json"
            markdown_out = Path(directory) / "packet.md"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--input",
                    str(FIXTURES / "query_evidence.json"),
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
            self.assertIn("## Estimated or derived metrics", markdown)
            self.assertIn("## At-risk hypotheses", markdown)
            self.assertIn("## Timeline", markdown)
            self.assertIn("## One-variable experiment boundary", markdown)

    def test_correlates_load_hashes_and_sos_roi_without_recommending_mutation(self) -> None:
        data = self.load_fixture("query_evidence.json")
        data["warehouse_load"] = [
            {
                "warehouse_name": "ETL_WH",
                "start_time": "2026-08-30T10:20:00Z",
                "end_time": "2026-08-30T10:22:00Z",
                "avg_running": "1.2",
                "avg_queued_load": "0.4",
                "avg_queued_provisioning": "0",
            }
        ]
        data["query_runs"] = [
            {
                "query_id": "old",
                "query_parameterized_hash": "phash-1",
                "warehouse_name": "ETL_WH",
                "total_elapsed_time_ms": "1000",
            },
            {
                "query_id": "new",
                "query_parameterized_hash": "phash-1",
                "warehouse_name": "ETL_WH",
                "total_elapsed_time_ms": "2000",
            },
        ]
        data["comparison_alignment"] = {
            "status": "aligned",
            "warehouse_name": "ETL_WH",
            "data_scope": "orders-2026-08-30",
            "parameters": {},
            "cache_state": "disabled",
            "session_parameters": {},
        }
        data["search_optimization"] = {
            "credits_used": "2.5",
            "latency_before_ms": "5000",
            "latency_after_ms": "2500",
            "bytes_scanned_before": "1000",
            "bytes_scanned_after": "400",
        }
        data["query_insights_status"] = {"status": "available", "reason": "operator-supplied Query Insights export"}
        result = MODULE.analyze(data)
        self.assertEqual(result["warehouse_load_summary"][0]["avg_queued_load_sum"], "0.4")
        self.assertEqual(result["query_hash_comparison"][0]["sample_count"], 2)
        self.assertEqual(result["search_optimization_roi"][0]["latency_reduction_ms"], "2500")
        self.assertEqual(result["query_insights_coverage"]["status"], "available")

    def test_rejects_query_identity_mismatch(self) -> None:
        data = self.load_fixture("query_evidence.json")
        data["metadata"]["query_id"] = "claimed-query"
        with self.assertRaises(MODULE.EvidenceError):
            MODULE.analyze(data)

    def test_load_correlation_requires_same_interval_and_warehouse(self) -> None:
        data = self.load_fixture("query_evidence.json")
        data["warehouse_load"] = [
            {
                "warehouse_name": "OTHER_WH",
                "start_time": "2026-08-30T10:20:00Z",
                "end_time": "2026-08-30T10:22:00Z",
                "avg_queued_load": "99",
            },
            {
                "warehouse_name": "ETL_WH",
                "start_time": "2026-08-30T09:00:00Z",
                "end_time": "2026-08-30T09:05:00Z",
                "avg_queued_load": "88",
            },
        ]
        result = MODULE.analyze(data)
        self.assertEqual(result["warehouse_load_summary"], [])
        self.assertTrue(any("outside the query interval or warehouse" in item for item in result["warnings"]))

    def test_unaligned_hash_runs_are_not_compared(self) -> None:
        data = self.load_fixture("query_evidence.json")
        data["query_runs"] = [
            {
                "query_id": "old",
                "query_parameterized_hash": "phash-1",
                "warehouse_name": "ETL_WH",
                "total_elapsed_time_ms": "1000",
            },
            {
                "query_id": "new",
                "query_parameterized_hash": "phash-1",
                "warehouse_name": "ETL_WH",
                "total_elapsed_time_ms": "2000",
            },
        ]
        result = MODULE.analyze(data)
        self.assertEqual(result["query_hash_comparison"], [])
        self.assertTrue(any("aligned comparison receipt is missing" in item for item in result["warnings"]))

    def test_rejects_raw_identity_and_query_tag_fields(self) -> None:
        for field in ("user_name", "query_tag"):
            data = self.load_fixture("query_evidence.json")
            data["query_history"][field] = "raw-value"
            with self.subTest(field=field), self.assertRaises(MODULE.EvidenceError):
                MODULE.analyze(data)

    def test_verified_collector_receipt_is_accepted(self) -> None:
        data = self.load_fixture("query_evidence.json")
        data["collector_receipt"] = self.valid_receipt(data)
        result = MODULE.analyze(data)
        self.assertEqual(result["collector_receipt_assessment"]["status"], "verified")
        self.assertFalse(result["completeness_claim_blocked"])

    def test_truncated_or_unverifiable_receipt_blocks_completeness(self) -> None:
        for mutation in ("truncate", "hash"):
            data = self.load_fixture("query_evidence.json")
            receipt = self.valid_receipt(data)
            if mutation == "truncate":
                receipt["truncation_possible"] = True
                self.rehash_receipt(receipt)
            else:
                del receipt["receipt_sha256"]
            data["collector_receipt"] = receipt
            result = MODULE.analyze(data)
            self.assertEqual(result["collector_receipt_assessment"]["status"], "unverifiable")
            self.assertTrue(result["completeness_claim_blocked"])
            self.assertTrue(any("collector receipt unverifiable" in item for item in result["warnings"]))

    def test_query_id_is_opaque_and_source_freshness_is_bounded(self) -> None:
        injection = self.load_fixture("query_evidence.json")
        injection["metadata"]["query_id"] = "01abc;DROP"
        with self.assertRaises(MODULE.EvidenceError):
            MODULE.analyze(injection)
        stale = self.load_fixture("query_evidence.json")
        stale["metadata"]["source_max_age_seconds"] = 60
        result = MODULE.analyze(stale)
        self.assertEqual(result["source_freshness"]["status"], "STALE")
        self.assertTrue(result["completeness_claim_blocked"])

    def test_subsurface_receipt_cannot_bind_another_query_or_truncation(self) -> None:
        data = self.load_fixture("query_evidence.json")
        data["operator_stats_receipt"] = {
            "status": "collected", "truncation_possible": False,
            "selector": "different-query", "collected_at": data["metadata"]["collected_at"],
        }
        result = MODULE.analyze(data)
        self.assertEqual(result["operator_stats_receipt_assessment"]["status"], "unverifiable")
        self.assertTrue(result["completeness_claim_blocked"])

    def test_valid_subsurface_receipts_are_cryptographically_bound(self) -> None:
        data = self.load_fixture("query_evidence.json")
        data["collector_receipt"] = self.valid_receipt(data)
        data["operator_stats_receipt"] = self.valid_subsurface_receipt("query-operator-stats", data)
        data["query_insights_receipt"] = self.valid_subsurface_receipt("query-insights", data)
        result = MODULE.analyze(data)
        self.assertEqual(result["operator_stats_receipt_assessment"]["status"], "verified")
        self.assertEqual(result["query_insights_receipt_assessment"]["status"], "verified")
        self.assertFalse(result["completeness_claim_blocked"])

    def test_subsurface_receipt_schema_template_or_hash_tamper_blocks_completeness(self) -> None:
        for mutation in ("schema", "template", "hash"):
            data = self.load_fixture("query_evidence.json")
            data["collector_receipt"] = self.valid_receipt(data)
            receipt = self.valid_subsurface_receipt("query-operator-stats", data)
            if mutation == "schema":
                receipt["schema_version"] = "2"
                self.rehash_receipt(receipt)
            elif mutation == "template":
                receipt["source_metadata"]["template"] = "query-insights.sql"
                self.rehash_receipt(receipt)
            else:
                receipt["receipt_sha256"] = "sha256:" + "0" * 64
            data["operator_stats_receipt"] = receipt
            result = MODULE.analyze(data)
            self.assertEqual(result["operator_stats_receipt_assessment"]["status"], "unverifiable")
            self.assertTrue(result["completeness_claim_blocked"])

    def test_rejects_sql_shaped_query_hash(self) -> None:
        data = self.load_fixture("query_evidence.json")
        data["query_history"]["query_hash"] = "SELECT secret FROM customer_data"
        with self.assertRaises(MODULE.EvidenceError):
            MODULE.analyze(data)

    def test_receipt_dataset_tamper_blocks_completeness(self) -> None:
        data = self.load_fixture("query_evidence.json")
        receipt = self.valid_receipt(data)
        receipt["datasets"]["query_history"][0]["query_id"] = "different-query"
        self.rehash_receipt(receipt)
        data["collector_receipt"] = receipt
        result = MODULE.analyze(data)
        self.assertTrue(result["completeness_claim_blocked"])
        self.assertIn(
            "query_history rows do not match collector receipt", result["collector_receipt_assessment"]["issues"]
        )


if __name__ == "__main__":
    unittest.main()
