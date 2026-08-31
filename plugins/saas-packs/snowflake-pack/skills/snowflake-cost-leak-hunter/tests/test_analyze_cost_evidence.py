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
COST_SQL_DIR = SKILL_DIR.parents[1] / "shared" / "evidence" / "sql"
SUPPLEMENTAL_SQL = (
    "cost-adaptive.sql",
    "cost-storage.sql",
    "cost-transfer.sql",
    "cost-internal-transfer.sql",
    "cost-ai-functions.sql",
    "cost-resource-monitors.sql",
    "cost-budgets.sql",
)

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

    def add_baseline_surface_inventory(self, data: dict) -> None:
        sources = {
            "warehouse_metering": ("SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY", "3"),
            "query_attribution": ("SNOWFLAKE.ACCOUNT_USAGE.QUERY_ATTRIBUTION_HISTORY", "8"),
            "warehouse_load": ("SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_LOAD_HISTORY", "8"),
            "serverless_usage": ("SNOWFLAKE.ACCOUNT_USAGE.METERING_HISTORY", "8"),
        }
        data["metadata"]["expected_surfaces"] = list(sources)
        data["surface_inventory"] = [
            {
                "surface": surface,
                "source": source,
                "status": "available",
                "privilege_status": "verified",
                "latest_timestamp": data["source_max_times"][surface],
                "documented_latency_hours": latency,
                "truncated": False,
            }
            for surface, (source, latency) in sources.items()
        ]

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
        self.add_baseline_surface_inventory(data)
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
            self.assertEqual(json.loads(json_out.read_text())["schema_version"], "2.0")
            markdown = markdown_out.read_text(encoding="utf-8")
            self.assertIn("## Typed cost ledger", markdown)
            self.assertIn("## Findings", markdown)
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
            "rollback": {
                "warehouse_size": "MEDIUM",
                "thresholds": {
                    "max_p95_latency_regression_pct": "5",
                    "max_queue_regression_pct": "0",
                },
            },
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
        self.assertIn("COST_ADAPTIVE_ATTRIBUTION_GAP", {finding["code"] for finding in result["findings"]})

    def test_typed_ledger_prevents_query_and_ai_double_counting(self) -> None:
        result = MODULE.analyze(self.load_fixture("cost_evidence_v2.json"))
        ledger = {item["entry_id"]: item for item in result["cost_ledger"]}
        self.assertTrue(ledger["warehouse-compute-total"]["aggregation_eligible"])
        self.assertFalse(ledger["query-attributed-compute"]["aggregation_eligible"])
        self.assertEqual(ledger["query-attributed-compute"]["parent_id"], "warehouse-compute-total")
        self.assertTrue(ledger["serverless-total:AI_SERVICES"]["aggregation_eligible"])
        self.assertFalse(ledger["ai-functions-attribution"]["aggregation_eligible"])
        self.assertEqual(
            ledger["ai-functions-attribution"]["parent_id"],
            "serverless-total:AI_SERVICES",
        )
        self.assertFalse(ledger["adaptive-compute-attribution"]["aggregation_eligible"])
        self.assertEqual(ledger["adaptive-compute-attribution"]["parent_id"], "warehouse-compute-total")
        additive_credits = sum(
            Decimal(item["amount"])
            for item in result["cost_ledger"]
            if item["aggregation_eligible"] and item["unit"] == "credits"
        )
        self.assertEqual(additive_credits, Decimal("28"))
        self.assertNotIn("COST_DOUBLE_COUNT_RISK", {finding["code"] for finding in result["findings"]})

    def test_storage_and_transfer_are_context_not_invoice_totals(self) -> None:
        result = MODULE.analyze(self.load_fixture("cost_evidence_v2.json"))
        ledger = {item["entry_id"]: item for item in result["cost_ledger"]}
        self.assertEqual(ledger["storage-context:table_storage"]["ledger_role"], "context")
        self.assertFalse(ledger["storage-context:table_storage"]["aggregation_eligible"])
        self.assertEqual(ledger["data_transfer_usage-context"]["unit"], "bytes")
        self.assertEqual(ledger["internal_transfer_usage-context"]["unit"], "bytes")
        self.assertIn("COST_INVOICE_ONLY", {finding["code"] for finding in result["findings"]})

    def test_missing_and_region_unavailable_surfaces_are_not_zero(self) -> None:
        data = self.load_fixture("cost_evidence_v2.json")
        data["adaptive_usage"] = []
        adaptive = next(item for item in data["surface_inventory"] if item["surface"] == "adaptive_usage")
        adaptive["status"] = "region_unavailable"
        adaptive.pop("latest_timestamp")
        result = MODULE.analyze(data)
        codes = {finding["code"] for finding in result["findings"]}
        self.assertIn("COST_ADAPTIVE_REGION_UNAVAILABLE", codes)
        self.assertNotIn("adaptive-compute-attribution", {item["entry_id"] for item in result["cost_ledger"]})

        absent = self.load_fixture("cost_evidence_v2.json")
        absent["surface_inventory"] = [
            row for row in absent["surface_inventory"] if row["surface"] != "data_transfer_usage"
        ]
        absent["data_transfer_usage"] = []
        result = MODULE.analyze(absent)
        self.assertTrue(result["completeness_claim_blocked"])
        self.assertTrue(
            any(
                finding["code"] == "COST_SURFACE_MISSING"
                and finding["surface"] == "data_transfer_usage"
                for finding in result["findings"]
            )
        )

    def test_explicit_latency_boundary_drives_stale_finding(self) -> None:
        data = self.load_fixture("cost_evidence_v2.json")
        storage = next(item for item in data["surface_inventory"] if item["surface"] == "storage_usage")
        storage["latest_timestamp"] = "2026-08-08T09:59:59Z"
        result = MODULE.analyze(data)
        self.assertTrue(
            any(
                finding["code"] == "COST_SURFACE_STALE" and finding["surface"] == "storage_usage"
                for finding in result["findings"]
            )
        )

    def test_surface_inventory_rejects_unreviewed_source_substitution(self) -> None:
        data = self.load_fixture("cost_evidence_v2.json")
        storage = next(item for item in data["surface_inventory"] if item["surface"] == "storage_usage")
        storage["source"] = "CUSTOM_DB.PUBLIC.UNREVIEWED_STORAGE"
        with self.assertRaises(MODULE.EvidenceError):
            MODULE.analyze(data)

    def test_control_gaps_cover_serverless_budget_and_monitor_boundaries(self) -> None:
        data = self.load_fixture("cost_evidence_v2.json")
        data["controls_inventory"] = {
            "resource_monitors": [],
            "budgets": [],
            "visibility_is_complete": False,
        }
        result = MODULE.analyze(data)
        codes = {finding["code"] for finding in result["findings"]}
        self.assertIn("COST_RESOURCE_MONITOR_COVERAGE_GAP", codes)
        self.assertIn("COST_BUDGET_COVERAGE_GAP", codes)
        self.assertIn("COST_SERVERLESS_MONITOR_GAP", codes)

    def test_ai_total_without_detail_is_an_attribution_gap(self) -> None:
        data = self.load_fixture("cost_evidence_v2.json")
        data["ai_usage"] = []
        result = MODULE.analyze(data)
        self.assertIn("COST_AI_ATTRIBUTION_GAP", {finding["code"] for finding in result["findings"]})

    def test_rate_conversion_stays_estimate_even_when_invoice_reconciled(self) -> None:
        data = self.load_fixture("cost_evidence_v2.json")
        data["credit_rates"]["warehouse"]["invoice_reconciled"] = True
        result = MODULE.analyze(data)
        entry = next(item for item in result["cost_ledger"] if item["entry_id"] == "estimate:warehouse-compute-total")
        self.assertEqual(entry["ledger_role"], "estimate")
        self.assertFalse(entry["aggregation_eligible"])
        self.assertEqual(entry["invoice_reconciliation"], "reconciled")

    def test_invoice_statement_is_separate_from_rate_estimates(self) -> None:
        data = self.load_fixture("cost_evidence_v2.json")
        data["invoice_usage"] = [
            {
                "start_time": "2026-08-01T00:00:00Z",
                "end_time": "2026-08-08T00:00:00Z",
                "statement_id": "statement-2026-08",
                "domain": "account-billing-period",
                "currency": "USD",
                "amount": "125.50",
            }
        ]
        result = MODULE.analyze(data)
        invoice = next(item for item in result["cost_ledger"] if item["ledger_role"] == "invoice-only")
        estimate = next(item for item in result["cost_ledger"] if item["ledger_role"] == "estimate")
        self.assertEqual(invoice["invoice_reconciliation"], "invoice_only")
        self.assertNotEqual(invoice["overlap_key"], estimate["overlap_key"])
        self.assertFalse(estimate["aggregation_eligible"])

    def test_duplicate_invoice_denominator_is_a_double_count_blocker(self) -> None:
        data = self.load_fixture("cost_evidence_v2.json")
        invoice = {
            "start_time": "2026-08-01T00:00:00Z",
            "end_time": "2026-08-08T00:00:00Z",
            "statement_id": "statement-duplicate",
            "domain": "account-billing-period",
            "currency": "USD",
            "amount": "125.50",
        }
        data["invoice_usage"] = [dict(invoice), dict(invoice)]
        result = MODULE.analyze(data)
        self.assertIn("COST_DOUBLE_COUNT_RISK", {finding["code"] for finding in result["findings"]})
        self.assertTrue(result["completeness_claim_blocked"])

    def test_right_sizing_requires_explicit_rollback_thresholds(self) -> None:
        data = self.load_fixture("cost_evidence_v2.json")
        data["metadata"]["right_sizing"] = {
            "warehouse": "ETL_WH",
            "current_size": "MEDIUM",
            "candidate_sizes": ["SMALL"],
            "max_size_steps": 1,
            "measurement_window": "same seven-day workload window",
            "success_criteria": "no p95 latency regression",
        }
        result = MODULE.analyze(data)
        self.assertEqual(result["right_sizing_experiment"]["status"], "incomplete")
        self.assertIn("COST_EXPERIMENT_ROLLBACK_UNBOUNDED", {finding["code"] for finding in result["findings"]})

    def test_rejects_raw_sql_and_presigned_urls(self) -> None:
        for field, value in (
            ("query_text", "select customer_email from pii"),
            ("presigned_url", "https://example.invalid/object?signature=secret"),
        ):
            data = self.load_fixture("cost_evidence_v2.json")
            data["ai_usage"][0][field] = value
            with self.subTest(field=field), self.assertRaises(MODULE.EvidenceError):
                MODULE.analyze(data)

    def test_supplemental_sql_is_bounded_read_only_and_redacted(self) -> None:
        forbidden = ("ALTER ", "CALL ", "CREATE ", "DELETE ", "DROP ", "GRANT ", "INSERT ", "MERGE ", "REVOKE ", "UPDATE ")
        for name in SUPPLEMENTAL_SQL:
            path = COST_SQL_DIR / name
            self.assertTrue(path.is_file(), name)
            sql = path.read_text(encoding="utf-8")
            normalized = " ".join(
                line.split("--", 1)[0].strip() for line in sql.splitlines() if line.split("--", 1)[0].strip()
            ).upper()
            with self.subTest(name=name):
                self.assertTrue(normalized.startswith(("SELECT ", "SHOW ")))
                self.assertIn("LIMIT ", normalized)
                self.assertFalse(any(token in normalized for token in forbidden))
                self.assertNotIn("QUERY_TEXT", normalized)
                self.assertNotIn("PRESIGNED", normalized)

    def test_v2_ledger_and_findings_are_deterministic_under_row_reordering(self) -> None:
        original = self.load_fixture("cost_evidence_v2.json")
        reordered = self.load_fixture("cost_evidence_v2.json")
        reordered["surface_inventory"].reverse()
        for key in (
            "warehouse_metering",
            "query_attribution",
            "warehouse_load",
            "serverless_usage",
            "adaptive_usage",
            "storage_usage",
            "data_transfer_usage",
            "internal_transfer_usage",
            "ai_usage",
        ):
            reordered[key].reverse()
        first = MODULE.analyze(original)
        second = MODULE.analyze(reordered)
        self.assertEqual(first["cost_ledger"], second["cost_ledger"])
        self.assertEqual(first["findings"], second["findings"])
        self.assertEqual(first["surface_inventory"], second["surface_inventory"])


if __name__ == "__main__":
    unittest.main()
