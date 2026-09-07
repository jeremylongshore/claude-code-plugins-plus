from __future__ import annotations

import importlib.util
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
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
BASELINE_DATASETS = (
    "warehouse_metering",
    "query_attribution",
    "warehouse_load",
    "serverless_usage",
)
ALL_SURFACES = (
    *BASELINE_DATASETS,
    "adaptive_usage",
    "storage_usage",
    "data_transfer_usage",
    "internal_transfer_usage",
    "ai_usage",
    "resource_monitors",
    "budgets",
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

    @staticmethod
    def iso(value: datetime) -> str:
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

    def prepare_live_collection(self, data: dict) -> None:
        observed = datetime.now(timezone.utc).replace(microsecond=0) - timedelta(seconds=5)
        data["metadata"]["generated_at"] = self.iso(observed)
        data["metadata"]["expected_surfaces"] = list(ALL_SURFACES)
        for dataset in (
            *BASELINE_DATASETS,
            "adaptive_usage",
            "storage_usage",
            "data_transfer_usage",
            "internal_transfer_usage",
            "ai_usage",
        ):
            data.setdefault(dataset, [])
        controls = data.setdefault("controls_inventory", {})
        controls.setdefault("resource_monitors", [])
        controls.setdefault("budgets", [])
        if not data.get("surface_inventory"):
            data["surface_inventory"] = [
                {
                    "surface": surface,
                    "source": MODULE.EXPECTED_SURFACE_SOURCES[surface],
                    "status": "available",
                    "privilege_status": "verified",
                    "latest_timestamp": data.get("source_max_times", {}).get(surface),
                    "documented_latency_hours": str(MODULE.SURFACE_LATENCY_HOURS[surface]),
                    "truncated": False,
                }
                for surface in ALL_SURFACES
            ]

    def execution_context(self, data: dict) -> dict:
        return {
            "observed_at": data["metadata"]["generated_at"],
            "account_identifier_sha256": "a" * 64,
            "collector_user_sha256": "b" * 64,
            "primary_role_sha256": "c" * 64,
            "primary_role_type": "ROLE",
            "secondary_roles_sha256": "d" * 64,
            "session_timezone": "UTC",
        }

    def receipt_for_surface(self, data: dict, surface: str, dataset: str, rows: list[dict]) -> dict:
        render_kwargs = {}
        if surface in COLLECTOR.COST_WINDOW_SURFACES:
            render_kwargs = {
                "window_start": data["metadata"]["window_start"],
                "window_end": data["metadata"]["window_end"],
            }
        path, template_sql, rendered_sql, sources, selector = COLLECTOR.render_surface(surface, **render_kwargs)
        raw = [
            {"EVIDENCE": {"_dataset": "execution_context", **self.execution_context(data)}},
            *({"EVIDENCE": {"_dataset": dataset, **row}} for row in rows),
        ]
        observed = data["metadata"]["generated_at"]
        return COLLECTOR.build_receipt(
            surface,
            "readonly",
            rendered_sql,
            sources,
            raw=raw,
            collected_at=observed,
            template_sql=template_sql,
            template_path=path,
            selector=selector,
            collection_mode="live-cli",
            collection_started_at=observed,
            collection_completed_at=observed,
        )

    def valid_receipt(self, data: dict) -> dict:
        rows = [{"_dataset": dataset, **row} for dataset in BASELINE_DATASETS for row in data.get(dataset, [])]
        # receipt_for_surface adds one dataset name to every row, so construct
        # the baseline envelope directly to preserve its four distinct datasets.
        render_kwargs = {
            "window_start": data["metadata"]["window_start"],
            "window_end": data["metadata"]["window_end"],
        }
        path, template_sql, rendered_sql, sources, selector = COLLECTOR.render_surface("cost", **render_kwargs)
        raw = [
            {"EVIDENCE": {"_dataset": "execution_context", **self.execution_context(data)}},
            *({"EVIDENCE": row} for row in rows),
        ]
        observed = data["metadata"]["generated_at"]
        return COLLECTOR.build_receipt(
            "cost",
            "readonly",
            rendered_sql,
            sources,
            raw=raw,
            collected_at=observed,
            template_sql=template_sql,
            template_path=path,
            selector=selector,
            collection_mode="live-cli",
            collection_started_at=observed,
            collection_completed_at=observed,
        )

    def rehash_receipt(self, receipt: dict) -> None:
        receipt["result_sha256"] = "sha256:" + hashlib.sha256(COLLECTOR.canonical_json(receipt["datasets"])).hexdigest()
        body = dict(receipt)
        body.pop("receipt_sha256", None)
        receipt["receipt_sha256"] = f"sha256:{hashlib.sha256(COLLECTOR.canonical_json(body)).hexdigest()}"

    def valid_supplemental_receipt(self, data: dict, surface: str) -> dict:
        collector_surface, dataset = MODULE.SUPPLEMENTAL_RECEIPT_SURFACES[surface]
        rows = MODULE._supplemental_input_rows(data, surface)
        return self.receipt_for_surface(data, collector_surface, dataset, rows)

    def add_supplemental_receipts(self, data: dict) -> None:
        data["supplemental_receipts"] = {
            surface: self.valid_supplemental_receipt(data, surface) for surface in MODULE.SUPPLEMENTAL_RECEIPT_SURFACES
        }

    def add_live_receipts(self, data: dict) -> None:
        self.prepare_live_collection(data)
        data["collector_receipt"] = self.valid_receipt(data)
        self.add_supplemental_receipts(data)

    def analyze_trusted(self, data: dict) -> dict:
        return MODULE.analyze(
            data,
            trusted_input_sha256=MODULE.canonical_bundle_digest(data),
        )

    def test_classifies_observed_estimated_and_at_risk_separately(self) -> None:
        data = self.load_fixture("cost_evidence.json")
        self.add_live_receipts(data)
        result = self.analyze_trusted(data)
        self.assertFalse(result["completeness_claim_blocked"])
        confirmed = {item["metric"]: item for item in result["confirmed_observations"]}
        self.assertEqual(confirmed["warehouse_compute_credits"]["credits"], "30.5")
        self.assertEqual(
            confirmed["query_attributed_compute_credits_excluding_idle"]["credits"],
            "16",
        )
        self.assertEqual(confirmed["metering:SNOWPIPE"]["credits"], "3.25")

        estimates = {item["basis"]: item for item in result["estimated_amounts"]}
        self.assertEqual(estimates["warehouse_compute"]["classification"], "estimated")
        self.assertEqual(Decimal(estimates["warehouse_compute"]["amount"]), Decimal("83.875"))

        idle_credits = {item["credits"] for item in result["at_risk_opportunities"] if item.get("warehouse_name")}
        self.assertEqual(idle_credits, {"5.5", "0.5"})
        self.assertIn(
            "untagged_query_attributed_compute",
            {item.get("metric") for item in result["at_risk_opportunities"]},
        )
        self.assertTrue(any("not reconciled" in item for item in result["warnings"]))
        self.assertTrue(result["approval_queue"])
        self.assertTrue(all(item["competing_explanation"] for item in result["at_risk_opportunities"]))

    def test_unknown_surface(self) -> None:
        data = self.load_fixture("cost_evidence_partial.json")
        self.add_live_receipts(data)
        result = self.analyze_trusted(data)
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
        self.add_live_receipts(data)
        with self.assertRaises(MODULE.EvidenceError):
            self.analyze_trusted(data)

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

    def test_rows_outside_requested_window_block_completeness(self) -> None:
        data = self.load_fixture("cost_evidence.json")
        data["warehouse_metering"].append(
            {
                "start_time": "2026-07-31T23:00:00Z",
                "end_time": "2026-08-01T00:00:00Z",
                "warehouse_name_sha256": "f" * 64,
                "credits_used_compute": "99",
                "credits_attributed_compute_queries": "99",
                "credits_used_cloud_services": "0",
            }
        )
        self.add_live_receipts(data)
        result = self.analyze_trusted(data)
        self.assertTrue(result["completeness_claim_blocked"])
        self.assertFalse(result["confirmed_observations"])
        self.assertIn(
            "COST_WINDOW_COVERAGE_GAP",
            {item["code"] for item in result["findings"]},
        )

    def test_rejects_raw_identity_and_query_tag_fields(self) -> None:
        cases = (
            ("query_attribution", "user_name"),
            ("query_attribution", "query_tag"),
            ("query_attribution", "query_id"),
            ("warehouse_metering", "warehouse_name"),
            ("internal_transfer_usage", "compute_pool_name"),
            ("ai_usage", "model_name"),
            ("ai_usage", "user_id"),
        )
        for dataset, field in cases:
            data = self.load_fixture("cost_evidence_v2.json")
            data[dataset][0][field] = "raw-value"
            with self.subTest(dataset=dataset, field=field), self.assertRaises(MODULE.EvidenceError):
                MODULE.analyze(data)

    def test_trusted_local_boundary_collector_receipt_is_accepted(self) -> None:
        data = self.load_fixture("cost_evidence_v2.json")
        self.add_live_receipts(data)
        receipt = data["collector_receipt"]
        self.assertEqual(receipt["schema_version"], "2")
        self.assertEqual(receipt["collection_mode"], "live-cli")
        self.assertEqual(
            receipt["source_metadata"]["selector"],
            {"window_start": True, "window_end": True},
        )
        self.assertEqual(len(receipt["datasets"]["execution_context"]), 1)
        result = self.analyze_trusted(data)
        self.assertEqual(
            result["collector_receipt_assessment"]["status"],
            "trusted_local_boundary",
        )
        self.assertFalse(result["completeness_claim_blocked"])

    def test_trusted_supplemental_receipts_bind_every_cost_surface(self) -> None:
        data = self.load_fixture("cost_evidence_v2.json")
        self.add_live_receipts(data)
        baseline_context = data["collector_receipt"]["datasets"]["execution_context"]
        for surface, receipt in data["supplemental_receipts"].items():
            with self.subTest(surface=surface):
                self.assertEqual(receipt["schema_version"], "2")
                self.assertEqual(receipt["collection_mode"], "live-cli")
                self.assertEqual(receipt["datasets"]["execution_context"], baseline_context)
        result = self.analyze_trusted(data)
        self.assertTrue(
            all(
                item["status"] == "trusted_local_boundary"
                for item in result["supplemental_receipt_assessments"].values()
            )
        )
        self.assertFalse(result["completeness_claim_blocked"])

    def test_self_consistent_receipts_without_trusted_bundle_digest_fail_closed(self) -> None:
        data = self.load_fixture("cost_evidence_v2.json")
        self.add_live_receipts(data)
        result = MODULE.analyze(data)
        self.assertEqual(
            result["collector_receipt_assessment"]["status"],
            "self_consistent_untrusted",
        )
        self.assertTrue(result["completeness_claim_blocked"])
        self.assertFalse(result["confirmed_observations"])

    def test_context_mismatch_blocks_an_otherwise_trusted_bundle(self) -> None:
        data = self.load_fixture("cost_evidence_v2.json")
        self.add_live_receipts(data)
        receipt = data["supplemental_receipts"]["storage_usage"]
        receipt["datasets"]["execution_context"][0]["primary_role_sha256"] = "0" * 64
        self.rehash_receipt(receipt)
        result = self.analyze_trusted(data)
        self.assertTrue(result["completeness_claim_blocked"])
        self.assertIn(
            "execution_context identity differs from the baseline cost receipt",
            result["supplemental_receipt_assessments"]["storage_usage"]["issues"],
        )

    def test_staggered_observation_times_preserve_identical_identity_context(self) -> None:
        data = self.load_fixture("cost_evidence_v2.json")
        self.add_live_receipts(data)
        receipt = data["supplemental_receipts"]["storage_usage"]
        completed = datetime.fromisoformat(receipt["collection_completed_at"].replace("Z", "+00:00"))
        observed = completed - timedelta(seconds=1)
        receipt["collection_started_at"] = self.iso(observed)
        receipt["datasets"]["execution_context"][0]["observed_at"] = self.iso(observed)
        self.rehash_receipt(receipt)
        result = self.analyze_trusted(data)
        self.assertFalse(result["completeness_claim_blocked"])
        self.assertEqual(
            result["supplemental_receipt_assessments"]["storage_usage"]["status"],
            "trusted_local_boundary",
        )

    def test_receipt_row_caps_are_bound_to_each_reviewed_template(self) -> None:
        cases = (
            ("baseline", 5000),
            ("storage_usage", 1000),
            ("resource_monitors", 10000),
        )
        for surface, expected in cases:
            data = self.load_fixture("cost_evidence_v2.json")
            self.add_live_receipts(data)
            receipt = data["collector_receipt"] if surface == "baseline" else data["supplemental_receipts"][surface]
            receipt["row_limit"] = 999999
            self.rehash_receipt(receipt)
            result = self.analyze_trusted(data)
            assessment = (
                result["collector_receipt_assessment"]
                if surface == "baseline"
                else result["supplemental_receipt_assessments"][surface]
            )
            with self.subTest(surface=surface):
                self.assertTrue(result["completeness_claim_blocked"])
                self.assertIn(
                    f"row_limit does not match the reviewed SQL cap {expected}",
                    assessment["issues"],
                )

        data = self.load_fixture("cost_evidence_v2.json")
        self.add_live_receipts(data)
        receipt = data["supplemental_receipts"]["storage_usage"]
        receipt["cap_scope"] = "per_dataset"
        self.rehash_receipt(receipt)
        result = self.analyze_trusted(data)
        self.assertTrue(result["completeness_claim_blocked"])
        self.assertIn(
            "cap_scope is not single_dataset_or_result",
            result["supplemental_receipt_assessments"]["storage_usage"]["issues"],
        )

    def test_untrusted_receipts_cannot_establish_positive_freshness(self) -> None:
        data = self.load_fixture("cost_evidence_v2.json")
        self.add_live_receipts(data)
        result = MODULE.analyze(data)
        self.assertTrue(result["completeness_claim_blocked"])
        self.assertFalse(
            {item["freshness_status"] for item in result["surface_inventory"]}
            & {"settled_window", "current_role_scoped_observation"}
        )

    def test_adaptive_finality_requires_a_valid_non_future_interval(self) -> None:
        for query_end in ("", "not-a-time", "2099-01-01T00:00:00Z", "2000-01-01T00:00:00Z"):
            data = self.load_fixture("cost_evidence_v2.json")
            data["adaptive_usage"][0]["query_end_time"] = query_end
            self.add_live_receipts(data)
            with self.subTest(query_end=query_end), self.assertRaises(MODULE.EvidenceError):
                self.analyze_trusted(data)

    def test_query_tag_presence_must_match_the_scoped_digest(self) -> None:
        for present, digest in ((True, None), (False, "f" * 64)):
            data = self.load_fixture("cost_evidence_v2.json")
            data["query_attribution"][0]["query_tag_present"] = present
            data["query_attribution"][0]["query_tag_sha256"] = digest
            self.add_live_receipts(data)
            with self.subTest(present=present), self.assertRaises(MODULE.EvidenceError):
                self.analyze_trusted(data)

    def test_original_trusted_digest_detects_synchronized_receipt_rehash(self) -> None:
        data = self.load_fixture("cost_evidence_v2.json")
        self.add_live_receipts(data)
        trusted_digest = MODULE.canonical_bundle_digest(data)
        data["storage_usage"][0]["storage_bytes"] = "999999"
        receipt = data["supplemental_receipts"]["storage_usage"]
        receipt["datasets"]["storage_usage"][0]["storage_bytes"] = "999999"
        self.rehash_receipt(receipt)
        result = MODULE.analyze(data, trusted_input_sha256=trusted_digest)
        self.assertTrue(result["completeness_claim_blocked"])
        self.assertEqual(result["evidence_trust"]["status"], "DIGEST_MISMATCH")
        self.assertFalse(result["confirmed_observations"])

    def test_missing_or_tampered_supplemental_receipt_blocks_completeness(self) -> None:
        for mutation in ("missing", "template", "payload", "hash"):
            data = self.load_fixture("cost_evidence_v2.json")
            self.add_live_receipts(data)
            if mutation == "missing":
                del data["supplemental_receipts"]["storage_usage"]
            else:
                receipt = data["supplemental_receipts"]["storage_usage"]
                if mutation == "template":
                    receipt["source_metadata"]["template"] = "cost-transfer.sql"
                    self.rehash_receipt(receipt)
                elif mutation == "payload":
                    receipt["datasets"]["storage_usage"][0]["storage_bytes"] = "999999"
                    self.rehash_receipt(receipt)
                else:
                    receipt["receipt_sha256"] = "sha256:" + "0" * 64
            result = self.analyze_trusted(data)
            assessment = result["supplemental_receipt_assessments"]["storage_usage"]
            self.assertNotEqual(assessment["status"], "trusted_local_boundary")
            self.assertTrue(result["completeness_claim_blocked"])

    def test_truncated_or_error_receipt_blocks_completeness(self) -> None:
        for mutation in ("truncate", "error"):
            data = self.load_fixture("cost_evidence_v2.json")
            self.add_live_receipts(data)
            receipt = data["collector_receipt"]
            if mutation == "truncate":
                receipt["truncation_possible"] = True
            else:
                receipt["status"] = "error"
                receipt["errors"] = [{"code": "SNOW_CLI_FAILED", "message": "permission denied"}]
            self.rehash_receipt(receipt)
            result = self.analyze_trusted(data)
            self.assertEqual(result["collector_receipt_assessment"]["status"], "unverifiable")
            self.assertTrue(result["completeness_claim_blocked"])
            self.assertTrue(any("collector receipt unverifiable" in item for item in result["warnings"]))

    def test_rejects_sql_shaped_query_hash(self) -> None:
        data = self.load_fixture("cost_evidence.json")
        data["query_attribution"][0]["query_hash"] = "SELECT secret FROM customer_data"
        with self.assertRaises(MODULE.EvidenceError):
            MODULE.analyze(data)

    def test_receipt_source_provenance_mismatch_blocks_completeness(self) -> None:
        data = self.load_fixture("cost_evidence_v2.json")
        self.add_live_receipts(data)
        receipt = data["collector_receipt"]
        receipt["source_views"] = ["SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY"]
        self.rehash_receipt(receipt)
        result = self.analyze_trusted(data)
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
            self.add_live_receipts(data)
            with self.subTest(surface=surface, field=field), self.assertRaises(MODULE.EvidenceError):
                self.analyze_trusted(data)

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
            self.add_live_receipts(data)
            with self.subTest(field=field), self.assertRaises(MODULE.EvidenceError):
                self.analyze_trusted(data)
        injected = self.load_fixture("cost_evidence.json")
        injected["warehouse_metering"][0]["warehouse_name"] = "WH\n## forged"
        self.add_live_receipts(injected)
        with self.assertRaises(MODULE.EvidenceError):
            self.analyze_trusted(injected)

    def test_cli_writes_json_and_markdown(self) -> None:
        data = self.load_fixture("cost_evidence.json")
        trusted_digest = MODULE.canonical_bundle_digest(data)
        with tempfile.TemporaryDirectory() as directory:
            json_out = Path(directory) / "report.json"
            markdown_out = Path(directory) / "report.md"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--input",
                    str(FIXTURES / "cost_evidence.json"),
                    "--trusted-input-sha256",
                    trusted_digest,
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

    def test_trusted_report_projects_provenance_caps_and_priced_markdown(self) -> None:
        data = self.load_fixture("cost_evidence_v2.json")
        self.add_live_receipts(data)
        result = self.analyze_trusted(data)
        baseline = result["collection_provenance"]["baseline"]
        self.assertEqual(baseline["row_limit"], 5000)
        self.assertEqual(baseline["cap_scope"], "per_dataset")
        self.assertRegex(baseline["template_sha256"], r"^sha256:[0-9a-f]{64}$")
        self.assertRegex(baseline["result_sha256"], r"^sha256:[0-9a-f]{64}$")
        self.assertEqual(baseline["context"]["session_timezone"], "UTC")
        self.assertEqual(set(result["included_surfaces"]), set(ALL_SURFACES))
        self.assertFalse(result["excluded_surfaces"])
        self.assertTrue(all(item["settled_cutoff"] for item in result["surface_inventory"]))
        for item in result["surface_inventory"]:
            observation_time = datetime.fromisoformat(item["settlement_observed_at"])
            expected_cutoff = observation_time - timedelta(
                seconds=float(Decimal(item["documented_latency_hours"]) * Decimal("3600"))
            )
            with self.subTest(surface=item["surface"]):
                self.assertEqual(item["collection_time"], item["settlement_observed_at"])
                self.assertEqual(item["settled_cutoff"], expected_cutoff.isoformat())
                self.assertEqual(
                    item["window_end_precedes_settled_cutoff"],
                    datetime.fromisoformat(result["scope"]["window_end"]) <= expected_cutoff,
                )
        markdown = MODULE.render_markdown(result)
        for field in (
            "Session timezone",
            "Baseline collection completed",
            "Snowflake query ID",
            "Reviewed / rendered SQL",
            "Normalized result hash",
            "Row count / cap",
            "Source-specific settled cutoffs",
            "Parent",
            "Overlap key",
        ):
            with self.subTest(field=field):
                self.assertIn(field, markdown)
        self.assertIn("per credit", markdown)
        self.assertIn("2026-Q3", markdown)
        self.assertIn("not_reconciled", markdown)

    def test_attribution_pareto_and_bounded_right_sizing_are_explicit(self) -> None:
        data = self.load_fixture("cost_evidence.json")
        data["warehouse_metering"][0]["warehouse_id"] = "wh-1"
        data["warehouse_metering"][1]["warehouse_id"] = "wh-2"
        data["query_attribution"] = [
            {
                "query_id_sha256": "3" * 64,
                "query_parameterized_hash": "3" * 64,
                "warehouse_name_sha256": "1" * 64,
                "start_time": "2026-08-03T00:00:00Z",
                "end_time": "2026-08-03T01:00:00Z",
                "query_tag_present": True,
                "query_tag_sha256": "5" * 64,
                "credits_attributed_compute": "12",
                "credits_used_query_acceleration": "0",
                "total_elapsed_time_ms": "3000",
            },
            {
                "query_id_sha256": "4" * 64,
                "query_parameterized_hash": "4" * 64,
                "warehouse_name_sha256": "2" * 64,
                "start_time": "2026-08-04T00:00:00Z",
                "end_time": "2026-08-04T01:00:00Z",
                "query_tag_present": True,
                "query_tag_sha256": "6" * 64,
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
        self.add_live_receipts(data)
        result = self.analyze_trusted(data)
        self.assertEqual(len(result["attribution_completeness"]), 2)
        self.assertTrue(result["cost_latency_pareto"])
        self.assertEqual(result["right_sizing_experiment"]["status"], "bounded_proposal")
        self.assertFalse(result["right_sizing_experiment"]["mutation_executed"])

    def test_null_attribution_is_unknown_not_zero(self) -> None:
        data = self.load_fixture("cost_evidence.json")
        data["warehouse_metering"][0]["credits_attributed_compute_queries"] = None
        self.add_live_receipts(data)
        result = self.analyze_trusted(data)
        item = next(item for item in result["attribution_completeness"] if item["compute_credits"] == "20.5")
        self.assertEqual(item["status"], "unknown")
        self.assertEqual(item["unattributed_credits"], "unknown")
        self.assertIn("COST_ADAPTIVE_ATTRIBUTION_GAP", {finding["code"] for finding in result["findings"]})

    def test_typed_ledger_prevents_query_and_ai_double_counting(self) -> None:
        data = self.load_fixture("cost_evidence_v2.json")
        self.add_live_receipts(data)
        result = self.analyze_trusted(data)
        ledger = {item["entry_id"]: item for item in result["cost_ledger"]}
        self.assertTrue(ledger["warehouse-compute-total"]["aggregation_eligible"])
        self.assertFalse(ledger["query-attributed-compute"]["aggregation_eligible"])
        self.assertEqual(ledger["query-attributed-compute"]["parent_id"], "warehouse-compute-total")
        self.assertTrue(ledger["metering-total:AI_SERVICES"]["aggregation_eligible"])
        self.assertFalse(ledger["ai-functions-attribution"]["aggregation_eligible"])
        self.assertEqual(
            ledger["ai-functions-attribution"]["parent_id"],
            "metering-total:AI_SERVICES",
        )
        self.assertFalse(ledger["adaptive-compute-attribution"]["aggregation_eligible"])
        self.assertEqual(ledger["adaptive-compute-attribution"]["parent_id"], "warehouse-compute-total")
        self.assertEqual(ledger["adaptive-compute-attribution"]["amount"], "1.8")
        self.assertEqual(ledger["adaptive-cloud-services-context"]["amount"], "0.2")
        additive_credits = sum(
            Decimal(item["amount"])
            for item in result["cost_ledger"]
            if item["aggregation_eligible"] and item["unit"] == "credits"
        )
        self.assertEqual(additive_credits, Decimal("28.5"))
        self.assertNotIn("COST_DOUBLE_COUNT_RISK", {finding["code"] for finding in result["findings"]})

    def test_storage_and_transfer_are_context_not_invoice_totals(self) -> None:
        data = self.load_fixture("cost_evidence_v2.json")
        self.add_live_receipts(data)
        result = self.analyze_trusted(data)
        ledger = {item["entry_id"]: item for item in result["cost_ledger"]}
        self.assertEqual(ledger["storage-context:table_storage"]["ledger_role"], "context")
        self.assertFalse(ledger["storage-context:table_storage"]["aggregation_eligible"])
        self.assertEqual(ledger["storage-context:table_storage"]["unit"], "byte-days")
        self.assertEqual(
            ledger["storage-context:table_storage"]["measurement_basis"],
            "average_daily_bytes_times_interval_days",
        )
        self.assertEqual(ledger["storage-context:hybrid_table_storage"]["amount"], "50")
        self.assertEqual(ledger["storage-context:archive_storage_cool"]["amount"], "0")
        self.assertEqual(ledger["data_transfer_usage-context"]["unit"], "bytes")
        self.assertEqual(ledger["internal_transfer_usage-context"]["unit"], "bytes")
        self.assertIn("COST_INVOICE_ONLY", {finding["code"] for finding in result["findings"]})

    def test_storage_daily_averages_become_non_overlapping_byte_days(self) -> None:
        data = self.load_fixture("cost_evidence_v2.json")
        second = dict(data["storage_usage"][0])
        second["start_time"] = "2026-08-05T00:00:00Z"
        second["end_time"] = "2026-08-06T00:00:00Z"
        second["storage_bytes"] = "1500"
        second["hybrid_table_storage_bytes"] = "75"
        data["storage_usage"].append(second)
        self.add_live_receipts(data)
        result = self.analyze_trusted(data)
        ledger = {item["entry_id"]: item for item in result["cost_ledger"]}
        self.assertEqual(ledger["storage-context:table_storage"]["amount"], "2500")
        self.assertEqual(ledger["storage-context:hybrid_table_storage"]["amount"], "125")

        overlap = self.load_fixture("cost_evidence_v2.json")
        duplicate = dict(overlap["storage_usage"][0])
        duplicate["start_time"] = "2026-08-04T12:00:00Z"
        duplicate["end_time"] = "2026-08-05T12:00:00Z"
        overlap["storage_usage"].append(duplicate)
        self.add_live_receipts(overlap)
        with self.assertRaisesRegex(MODULE.EvidenceError, "must not overlap"):
            self.analyze_trusted(overlap)

    def test_missing_and_region_unavailable_surfaces_are_not_zero(self) -> None:
        data = self.load_fixture("cost_evidence_v2.json")
        data["adaptive_usage"] = []
        adaptive = next(item for item in data["surface_inventory"] if item["surface"] == "adaptive_usage")
        adaptive["status"] = "region_unavailable"
        adaptive.pop("latest_timestamp")
        self.add_live_receipts(data)
        result = self.analyze_trusted(data)
        codes = {finding["code"] for finding in result["findings"]}
        self.assertIn("COST_ADAPTIVE_REGION_UNAVAILABLE", codes)
        self.assertNotIn("adaptive-compute-attribution", {item["entry_id"] for item in result["cost_ledger"]})

        absent = self.load_fixture("cost_evidence_v2.json")
        absent["surface_inventory"] = [
            row for row in absent["surface_inventory"] if row["surface"] != "data_transfer_usage"
        ]
        absent["data_transfer_usage"] = []
        self.add_live_receipts(absent)
        result = self.analyze_trusted(absent)
        self.assertTrue(result["completeness_claim_blocked"])
        self.assertTrue(
            any(
                finding["code"] == "COST_SURFACE_MISSING" and finding["surface"] == "data_transfer_usage"
                for finding in result["findings"]
            )
        )

    def test_fixed_latency_contract_rejects_caller_override(self) -> None:
        data = self.load_fixture("cost_evidence_v2.json")
        storage = next(item for item in data["surface_inventory"] if item["surface"] == "storage_usage")
        storage["documented_latency_hours"] = "1.999"
        self.add_live_receipts(data)
        with self.assertRaises(MODULE.EvidenceError):
            self.analyze_trusted(data)

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
        self.add_live_receipts(data)
        result = self.analyze_trusted(data)
        codes = {finding["code"] for finding in result["findings"]}
        self.assertIn("COST_RESOURCE_MONITOR_COVERAGE_GAP", codes)
        self.assertIn("COST_BUDGET_COVERAGE_GAP", codes)
        self.assertIn("COST_SERVERLESS_MONITOR_GAP", codes)
        self.assertEqual(
            result["controls_assessment"]["budget_coverage_status"],
            "unknown_without_separately_receipted_budget_scope_and_actions",
        )
        self.assertFalse(result["controls_assessment"]["visibility_is_complete"])

    def test_ai_total_without_detail_is_an_attribution_gap(self) -> None:
        data = self.load_fixture("cost_evidence_v2.json")
        data["ai_usage"] = []
        self.add_live_receipts(data)
        result = self.analyze_trusted(data)
        self.assertIn("COST_AI_ATTRIBUTION_GAP", {finding["code"] for finding in result["findings"]})

    def test_rate_row_cannot_fabricate_invoice_reconciliation(self) -> None:
        data = self.load_fixture("cost_evidence_v2.json")
        data["credit_rates"]["warehouse"]["invoice_reconciled"] = True
        self.add_live_receipts(data)
        with self.assertRaises(MODULE.EvidenceError):
            self.analyze_trusted(data)

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
        self.add_live_receipts(data)
        result = self.analyze_trusted(data)
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
        self.add_live_receipts(data)
        with self.assertRaises(MODULE.EvidenceError):
            self.analyze_trusted(data)

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
        self.add_live_receipts(data)
        result = self.analyze_trusted(data)
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
        forbidden = (
            "ALTER ",
            "CALL ",
            "CREATE ",
            "DELETE ",
            "DROP ",
            "GRANT ",
            "INSERT ",
            "MERGE ",
            "REVOKE ",
            "UPDATE ",
        )
        for name in SUPPLEMENTAL_SQL:
            path = COST_SQL_DIR / name
            self.assertTrue(path.is_file(), name)
            sql = path.read_text(encoding="utf-8")
            normalized = " ".join(
                line.split("--", 1)[0].strip() for line in sql.splitlines() if line.split("--", 1)[0].strip()
            ).upper()
            with self.subTest(name=name):
                self.assertTrue(normalized.startswith(("WITH ", "SHOW ")))
                if name == "cost-resource-monitors.sql":
                    self.assertEqual(COLLECTOR.INTRINSIC_ROW_LIMITS["cost-resource-monitors"], 10000)
                else:
                    self.assertIn("LIMIT ", normalized)
                self.assertFalse(any(token in normalized for token in forbidden))
                self.assertNotIn("QUERY_TEXT", normalized)
                self.assertNotIn("PRESIGNED", normalized)
                self.assertIn("EXECUTION_CONTEXT", normalized)

        adaptive = (COST_SQL_DIR / "cost-adaptive.sql").read_text(encoding="utf-8").upper()
        self.assertIn("CREDITS_USED_COMPUTE", adaptive)
        self.assertIn("CREDITS_USED_CLOUD_SERVICES", adaptive)
        ai = (COST_SQL_DIR / "cost-ai-functions.sql").read_text(encoding="utf-8").upper()
        self.assertIn("IS_COMPLETED", ai)
        self.assertIn("MODEL_NAME_SHA256", ai)

    def test_v2_ledger_and_findings_are_deterministic_under_row_reordering(self) -> None:
        original = self.load_fixture("cost_evidence_v2.json")
        self.add_live_receipts(original)
        reordered = json.loads(json.dumps(original))
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
        first = self.analyze_trusted(original)
        second = self.analyze_trusted(reordered)
        self.assertEqual(first["cost_ledger"], second["cost_ledger"])
        self.assertEqual(first["findings"], second["findings"])
        self.assertEqual(first["surface_inventory"], second["surface_inventory"])


if __name__ == "__main__":
    unittest.main()
