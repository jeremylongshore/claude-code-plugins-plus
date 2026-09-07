#!/usr/bin/env python3
"""Adversarial contract tests for trusted, bounded Snowflake cost evidence."""

from __future__ import annotations

import contextlib
import copy
import hashlib
import importlib.util
import inspect
import io
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


TEST_DIR = Path(__file__).resolve().parent
SKILL_DIR = TEST_DIR.parent
ANALYZER_PATH = SKILL_DIR / "scripts" / "analyze_cost_evidence.py"
COLLECTOR_PATH = SKILL_DIR / "scripts" / "collect_snowflake_evidence.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ANALYZER = load_module("snowflake_cost_adversarial_analyzer", ANALYZER_PATH)
COLLECTOR = load_module("snowflake_cost_adversarial_collector", COLLECTOR_PATH)


BASELINE_DATASETS = (
    "warehouse_metering",
    "query_attribution",
    "warehouse_load",
    "serverless_usage",
)
SUPPLEMENTAL = {
    "adaptive_usage": ("cost-adaptive", "adaptive_usage"),
    "storage_usage": ("cost-storage", "storage_usage"),
    "data_transfer_usage": ("cost-transfer", "data_transfer_usage"),
    "internal_transfer_usage": ("cost-internal-transfer", "internal_transfer_usage"),
    "ai_usage": ("cost-ai-functions", "ai_usage"),
    "resource_monitors": ("cost-resource-monitors", "resource_monitors"),
    "budgets": ("cost-budgets", "budgets"),
}
ALL_SURFACES = (*BASELINE_DATASETS, *SUPPLEMENTAL)
LATENCY_HOURS = {
    "warehouse_metering": "6",
    "query_attribution": "8",
    "warehouse_load": "3",
    "serverless_usage": "12",
    "adaptive_usage": "1",
    "storage_usage": "2",
    "data_transfer_usage": "2",
    "internal_transfer_usage": "3",
    "ai_usage": "0.083334",
}
SOURCE_BY_SURFACE = {
    "warehouse_metering": "SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY",
    "query_attribution": "SNOWFLAKE.ACCOUNT_USAGE.QUERY_ATTRIBUTION_HISTORY",
    "warehouse_load": "SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_LOAD_HISTORY",
    "serverless_usage": "SNOWFLAKE.ACCOUNT_USAGE.METERING_HISTORY",
    "adaptive_usage": "SNOWFLAKE.ACCOUNT_USAGE.QUERY_METERING_HISTORY",
    "storage_usage": "SNOWFLAKE.ACCOUNT_USAGE.STORAGE_USAGE",
    "data_transfer_usage": "SNOWFLAKE.ACCOUNT_USAGE.DATA_TRANSFER_HISTORY",
    "internal_transfer_usage": "SNOWFLAKE.ACCOUNT_USAGE.INTERNAL_DATA_TRANSFER_HISTORY",
    "ai_usage": "SNOWFLAKE.ACCOUNT_USAGE.CORTEX_AI_FUNCTIONS_USAGE_HISTORY",
    "resource_monitors": "SHOW RESOURCE MONITORS",
    "budgets": "SHOW SNOWFLAKE.CORE.BUDGET",
}


def iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def canonical_digest(value: Any) -> str:
    return ANALYZER.canonical_bundle_digest(value)


def reseal(receipt: dict[str, Any]) -> None:
    receipt.pop("receipt_sha256", None)
    receipt["result_sha256"] = f"sha256:{hashlib.sha256(COLLECTOR.canonical_json(receipt['datasets'])).hexdigest()}"
    receipt["receipt_sha256"] = f"sha256:{hashlib.sha256(COLLECTOR.canonical_json(receipt)).hexdigest()}"


class CostEvidenceFactory:
    def __init__(
        self,
        *,
        recent_window: bool = False,
        window_days: int | None = None,
        end_lag_hours: int | None = None,
        observation_lag_seconds: int = 0,
    ) -> None:
        self.now = datetime.now(timezone.utc).replace(microsecond=0)
        self.observed = self.now - timedelta(seconds=observation_lag_seconds)
        if end_lag_hours is not None:
            self.end = self.now - timedelta(hours=end_lag_hours)
            self.start = self.end - timedelta(days=1)
        elif window_days is not None:
            self.end = self.now - timedelta(days=1)
            self.start = self.end - timedelta(days=window_days)
        elif recent_window:
            self.start = self.now - timedelta(hours=2)
            self.end = self.now - timedelta(minutes=30)
        else:
            self.start = self.now - timedelta(days=8)
            self.end = self.now - timedelta(days=7)
        self.row_start = self.start + timedelta(minutes=5)
        self.row_end = min(self.end, self.row_start + timedelta(minutes=5))
        self.context = {
            "observed_at": iso(self.observed),
            "account_identifier_sha256": "a" * 64,
            "collector_user_sha256": "b" * 64,
            "primary_role_sha256": "c" * 64,
            "primary_role_type": "ROLE",
            "secondary_roles_sha256": "d" * 64,
            "session_timezone": "UTC",
        }

    def data(self) -> dict[str, Any]:
        start = iso(self.row_start)
        end = iso(self.row_end)
        result: dict[str, Any] = {
            "metadata": {
                "account": "account-pseudonym",
                "role": "role-pseudonym",
                "review_owner": "finops-owner",
                "approval_boundary": "finops-plus-platform-approval",
                "identity_disclosure_authorized": True,
                "identity_disclosure_authority": "trusted-test-fixture",
                "window_start": iso(self.start),
                "window_end": iso(self.end),
                "generated_at": iso(self.now),
                "evaluated_at": iso(self.now),
                "max_age_seconds": 3600,
                "max_collection_interval_seconds": 120,
                "expected_surfaces": list(ALL_SURFACES),
            },
            "source_max_times": {name: iso(self.now) for name in BASELINE_DATASETS},
            "warehouse_metering": [
                {
                    "start_time": start,
                    "end_time": end,
                    "warehouse_id": "warehouse-id-1",
                    "warehouse_name_sha256": "1" * 64,
                    "credits_used_compute": "10",
                    "credits_used_cloud_services": "0.2",
                    "credits_attributed_compute_queries": "6",
                }
            ],
            "query_attribution": [
                {
                    "query_id_sha256": "3" * 64,
                    "query_hash": "6" * 64,
                    "query_parameterized_hash": "7" * 64,
                    "warehouse_name_sha256": "1" * 64,
                    "user_name_sha256": "e" * 64,
                    "query_tag_sha256": "f" * 64,
                    "query_tag_present": True,
                    "start_time": start,
                    "end_time": end,
                    "total_elapsed_time_ms": "100",
                    "execution_status": "SUCCESS",
                    "warehouse_size": "SMALL",
                    "credits_attributed_compute": "6",
                    "credits_used_query_acceleration": "0",
                }
            ],
            "warehouse_load": [
                {
                    "warehouse_name_sha256": "1" * 64,
                    "start_time": start,
                    "end_time": end,
                    "avg_running": "1",
                    "avg_queued_load": "0",
                    "avg_queued_provisioning": "0",
                }
            ],
            "serverless_usage": [
                {"start_time": start, "end_time": end, "service_type": "AI_SERVICES", "credits_used": "3"},
                {"start_time": start, "end_time": end, "service_type": "PIPE", "credits_used": "2"},
            ],
            "adaptive_usage": [
                {
                    "start_time": start,
                    "end_time": end,
                    "query_id_sha256": "9" * 64,
                    "warehouse_name_sha256": "8" * 64,
                    "query_hash": "4" * 64,
                    "query_parameterized_hash": "5" * 64,
                    "query_tag_sha256": "1" * 64,
                    "query_tag_present": True,
                    "user_name_sha256": "2" * 64,
                    "credits_used": "1.6",
                    "credits_used_compute": "1.5",
                    "credits_used_cloud_services": "0.1",
                    "query_start_time": start,
                    "query_end_time": end,
                }
            ],
            "storage_usage": [
                {
                    "start_time": start,
                    "end_time": end,
                    "storage_bytes": "1000",
                    "stage_bytes": "200",
                    "failsafe_bytes": "300",
                    "hybrid_table_storage_bytes": "50",
                    "archive_storage_cool_bytes": "0",
                    "archive_storage_cold_bytes": "0",
                    "archive_storage_retrieval_temp_bytes": "0",
                    "invoice_reconciliation": "not_reconciled",
                }
            ],
            "data_transfer_usage": [
                {
                    "start_time": start,
                    "end_time": end,
                    "source_cloud": "AWS",
                    "source_region": "region-a",
                    "target_cloud": "AWS",
                    "target_region": "region-b",
                    "transfer_type": "COPY",
                    "bytes_transferred": "4096",
                }
            ],
            "internal_transfer_usage": [
                {
                    "start_time": start,
                    "end_time": end,
                    "transfer_type": "SNOWPARK_CONTAINER_SERVICES",
                    "compute_pool_name_sha256": "3" * 64,
                    "bytes_transferred": "2048",
                }
            ],
            "ai_usage": [
                {
                    "start_time": start,
                    "end_time": end,
                    "function_name": "COMPLETE",
                    "model_name_sha256": "7" * 64,
                    "query_id_sha256": "6" * 64,
                    "warehouse_id": "warehouse-id-1",
                    "query_tag_sha256": "4" * 64,
                    "user_id_sha256": "5" * 64,
                    "credits_used": "2.5",
                    "is_completed": True,
                }
            ],
            "controls_inventory": {
                "resource_monitors": [
                    {
                        "name_sha256": "6" * 64,
                        "owner_sha256": "7" * 64,
                        "level": "WAREHOUSE",
                        "frequency": "MONTHLY",
                        "credit_quota": None,
                        "used_credits": "0",
                        "remaining_credits": None,
                    }
                ],
                "budgets": [
                    {
                        "name_sha256": "8" * 64,
                        "database_name_sha256": "9" * 64,
                        "schema_name_sha256": "0" * 64,
                        "current_version": "1",
                        "owner_sha256": "a" * 64,
                        "owner_role_type": "ROLE",
                    }
                ],
            },
            "credit_rates": {
                "warehouse": {
                    "unit_price": "2.5",
                    "currency": "USD",
                    "provenance": "customer-rate-card-2026",
                    "effective_period": "2026-Q3",
                }
            },
        }
        result["surface_inventory"] = [
            {
                "surface": surface,
                "source": SOURCE_BY_SURFACE[surface],
                "status": "available",
                "privilege_status": "verified",
                "latest_timestamp": iso(self.now) if surface in LATENCY_HOURS else None,
                "documented_latency_hours": LATENCY_HOURS.get(surface),
                "truncated": False,
            }
            for surface in ALL_SURFACES
        ]
        self.attach_receipts(result)
        return result

    def _raw_rows(self, data: dict[str, Any], surface: str) -> list[dict[str, Any]]:
        if surface == "cost":
            rows = [
                {"EVIDENCE": {"_dataset": dataset, **row}} for dataset in BASELINE_DATASETS for row in data[dataset]
            ]
        else:
            dataset = next(
                dataset for _, (collector_surface, dataset) in SUPPLEMENTAL.items() if collector_surface == surface
            )
            source_rows = data[dataset] if dataset in data else data["controls_inventory"][dataset]
            rows = [{"EVIDENCE": {"_dataset": dataset, **row}} for row in source_rows]
        return [{"EVIDENCE": {"_dataset": "execution_context", **self.context}}, *rows]

    def _receipt(self, data: dict[str, Any], collector_surface: str) -> dict[str, Any]:
        render_kwargs = {}
        if collector_surface in COLLECTOR.COST_WINDOW_SURFACES:
            render_kwargs = {
                "window_start": iso(self.start),
                "window_end": iso(self.end),
            }
        path, template_sql, rendered_sql, sources, selector = COLLECTOR.render_surface(
            collector_surface, **render_kwargs
        )
        kwargs = {
            "raw": self._raw_rows(data, collector_surface),
            "collected_at": iso(self.now),
            "template_sql": template_sql,
            "template_path": path,
            "selector": selector,
            "collection_mode": "live-cli",
            "collection_started_at": iso(self.observed),
            "collection_completed_at": iso(self.now),
        }
        return COLLECTOR.build_receipt(collector_surface, "readonly", rendered_sql, sources, **kwargs)

    def attach_receipts(self, data: dict[str, Any]) -> None:
        data["collector_receipt"] = self._receipt(data, "cost")
        data["supplemental_receipts"] = {
            logical_surface: self._receipt(data, collector_surface)
            for logical_surface, (collector_surface, _) in SUPPLEMENTAL.items()
        }


class AdversarialAssertions(unittest.TestCase):
    def call_analyzer(
        self,
        data: dict[str, Any],
        *,
        trusted: bool = True,
        supplied_digest: str | None = None,
    ) -> dict[str, Any]:
        if not trusted:
            return ANALYZER.analyze(data)
        digest = supplied_digest if supplied_digest is not None else canonical_digest(data)
        return ANALYZER.analyze(data, trusted_input_sha256=digest)

    def assert_fail_closed(self, data: dict[str, Any], *, supplied_digest: str | None = None) -> None:
        try:
            result = self.call_analyzer(data, supplied_digest=supplied_digest)
        except ANALYZER.EvidenceError:
            return
        self.assertTrue(result.get("completeness_claim_blocked"), result)
        self.assertFalse(result.get("confirmed_observations"), result)
        self.assertFalse(result.get("estimated_amounts"), result)
        self.assertFalse(result.get("approval_queue"), result)
        additive = [row for row in result.get("cost_ledger", []) if row.get("aggregation_eligible") is True]
        self.assertFalse(additive, result)

    @staticmethod
    def sync_dataset_row(data: dict[str, Any], dataset: str) -> None:
        if dataset in BASELINE_DATASETS:
            receipt = data["collector_receipt"]
        else:
            receipt = data["supplemental_receipts"][dataset]
        source_rows = data[dataset] if dataset in data else data["controls_inventory"][dataset]
        receipt["datasets"][dataset] = copy.deepcopy(source_rows)
        receipt["dataset_row_counts"] = {name: len(rows) for name, rows in receipt["datasets"].items()}
        receipt["row_count"] = sum(len(rows) for rows in receipt["datasets"].values())
        reseal(receipt)


class CollectorTrustContractTests(AdversarialAssertions):
    def test_cost_surfaces_are_schema2_live_receipts_with_exact_context(self) -> None:
        data = CostEvidenceFactory().data()
        receipts = {"cost": data["collector_receipt"], **data["supplemental_receipts"]}
        for surface, receipt in receipts.items():
            with self.subTest(surface=surface):
                self.assertEqual(receipt.get("schema_version"), "2")
                self.assertEqual(receipt.get("collection_mode"), "live-cli")
                self.assertIn("collection_started_at", receipt)
                self.assertIn("collection_completed_at", receipt)
                contexts = receipt.get("datasets", {}).get("execution_context")
                self.assertIsInstance(contexts, list)
                self.assertEqual(len(contexts), 1)
                self.assertEqual(set(contexts[0]), set(CostEvidenceFactory().context))
                self.assertEqual(receipt.get("errors"), [])
                expected_selector = (
                    {"window_start": True, "window_end": True}
                    if receipt["surface"] in COLLECTOR.COST_WINDOW_SURFACES
                    else {}
                )
                self.assertEqual(receipt["source_metadata"]["selector"], expected_selector)
                self.assertEqual(
                    receipt["selector_fingerprint"] is not None,
                    bool(expected_selector),
                )

    def test_offline_normalization_cannot_create_cost_proof(self) -> None:
        factory = CostEvidenceFactory()
        for surface in ("cost", "cost-storage"):
            with self.subTest(surface=surface), tempfile.TemporaryDirectory() as temporary:
                raw_path = Path(temporary) / "rows.json"
                raw_path.write_text("[]\n", encoding="utf-8")
                stderr = io.StringIO()
                stdout = io.StringIO()
                argv = [
                    "--surface",
                    surface,
                    "--input-json",
                    str(raw_path),
                    "--window-start",
                    iso(factory.start),
                    "--window-end",
                    iso(factory.end),
                ]
                with contextlib.redirect_stderr(stderr), contextlib.redirect_stdout(stdout):
                    code = COLLECTOR.main(argv)
                self.assertNotEqual(code, 0)
                self.assertIn("offline", stderr.getvalue().casefold())
                self.assertNotIn('"status": "collected"', stdout.getvalue())

    def test_cost_window_selectors_are_required_and_injection_safe(self) -> None:
        parameters = inspect.signature(COLLECTOR.render_surface).parameters
        self.assertIn("window_start", parameters)
        self.assertIn("window_end", parameters)
        start = "2026-08-01T00:00:00Z"
        end = "2026-08-02T00:00:00Z"
        _, _, rendered, _, selector = COLLECTOR.render_surface("cost", window_start=start, window_end=end)
        self.assertEqual(selector["window_start"], start)
        self.assertEqual(selector["window_end"], end)
        self.assertIn(start, rendered)
        self.assertIn(end, rendered)
        with self.assertRaises(COLLECTOR.CollectionError):
            COLLECTOR.render_surface(
                "cost",
                window_start="2026-08-01T00:00:00Z'); DROP DATABASE PROD; --",
                window_end=end,
            )


class AnalyzerTrustContractTests(AdversarialAssertions):
    def test_identity_disclosure_requires_explicit_authority_or_hashes(self) -> None:
        missing = CostEvidenceFactory().data()
        missing["metadata"].pop("identity_disclosure_authorized")
        missing["metadata"].pop("identity_disclosure_authority")
        with self.assertRaises(ANALYZER.EvidenceError):
            self.call_analyzer(missing)

        unauthorized_raw = CostEvidenceFactory().data()
        unauthorized_raw["metadata"]["identity_disclosure_authorized"] = False
        unauthorized_raw["metadata"].pop("identity_disclosure_authority")
        with self.assertRaises(ANALYZER.EvidenceError):
            self.call_analyzer(unauthorized_raw)

        hashed = CostEvidenceFactory().data()
        hashed["metadata"]["identity_disclosure_authorized"] = False
        hashed["metadata"].pop("identity_disclosure_authority")
        for offset, field in enumerate(("account", "role", "review_owner", "approval_boundary")):
            hashed["metadata"][field] = f"{offset + 1:x}" * 64
        result = self.call_analyzer(hashed)
        self.assertEqual(result["identity_disclosure"], {"authorized": False, "authority": None})

    def test_cost_window_is_capped_at_seven_days(self) -> None:
        seven_days = CostEvidenceFactory(window_days=7)
        accepted = self.call_analyzer(seven_days.data())
        self.assertEqual(
            datetime.fromisoformat(accepted["scope"]["window_start"]),
            seven_days.start,
        )

        overlong_factory = CostEvidenceFactory(window_days=7)
        overlong = overlong_factory.data()
        overlong["metadata"]["window_start"] = iso(overlong_factory.start - timedelta(days=1))
        with self.assertRaisesRegex(ANALYZER.EvidenceError, "cannot exceed seven days"):
            self.call_analyzer(overlong)

    def test_analyzer_requires_out_of_band_digest(self) -> None:
        self.assertIn("trusted_input_sha256", inspect.signature(ANALYZER.analyze).parameters)
        result = self.call_analyzer(CostEvidenceFactory().data(), trusted=False)
        self.assertTrue(result["completeness_claim_blocked"])
        self.assertFalse(result["confirmed_observations"])
        self.assertFalse(any(row.get("aggregation_eligible") for row in result["cost_ledger"]))

    def test_self_rehash_does_not_replace_out_of_band_bundle_digest(self) -> None:
        data = CostEvidenceFactory().data()
        trusted_digest = canonical_digest(data)
        data["warehouse_metering"][0]["credits_used_compute"] = "999"
        self.sync_dataset_row(data, "warehouse_metering")
        self.assert_fail_closed(data, supplied_digest=trusted_digest)

    def test_exact_receipt_payload_binding_survives_a_new_bundle_digest(self) -> None:
        data = CostEvidenceFactory().data()
        data["supplemental_receipts"]["storage_usage"]["datasets"]["storage_usage"][0]["storage_bytes"] = "999999"
        reseal(data["supplemental_receipts"]["storage_usage"])
        self.assert_fail_closed(data)

    def test_every_authorization_context_dimension_must_match(self) -> None:
        for field, replacement in (
            ("account_identifier_sha256", "0" * 64),
            ("collector_user_sha256", "1" * 64),
            ("primary_role_sha256", "2" * 64),
            ("primary_role_type", "DATABASE_ROLE"),
            ("secondary_roles_sha256", "3" * 64),
            ("session_timezone", "America/Los_Angeles"),
        ):
            data = CostEvidenceFactory().data()
            receipt = data["supplemental_receipts"]["storage_usage"]
            self.assertEqual(receipt.get("schema_version"), "2")
            receipt["datasets"]["execution_context"][0][field] = replacement
            reseal(receipt)
            with self.subTest(field=field):
                self.assert_fail_closed(data)

    def test_database_role_is_rejected_even_when_every_receipt_agrees(self) -> None:
        factory = CostEvidenceFactory()
        factory.context["primary_role_type"] = "DATABASE_ROLE"
        data = factory.data()
        self.assert_fail_closed(data)

    def test_offline_stale_long_interval_and_out_of_interval_observation_fail_closed(self) -> None:
        mutations = ("offline", "stale", "long_interval", "observation_outside")
        for mutation in mutations:
            factory = CostEvidenceFactory()
            data = factory.data()
            receipt = data["supplemental_receipts"]["storage_usage"]
            self.assertEqual(receipt.get("schema_version"), "2")
            if mutation == "offline":
                receipt["collection_mode"] = "offline-normalized"
            elif mutation == "stale":
                old = iso(factory.now - timedelta(hours=2))
                receipt["collected_at"] = old
                receipt["collection_started_at"] = old
                receipt["collection_completed_at"] = old
                receipt["datasets"]["execution_context"][0]["observed_at"] = old
            elif mutation == "long_interval":
                receipt["collection_started_at"] = iso(factory.now - timedelta(minutes=10))
            else:
                receipt["datasets"]["execution_context"][0]["observed_at"] = iso(factory.now - timedelta(minutes=5))
            reseal(receipt)
            with self.subTest(mutation=mutation):
                self.assert_fail_closed(data)


class CompletenessAndSemanticContractTests(AdversarialAssertions):
    def test_settlement_uses_same_statement_observation_not_cli_completion(self) -> None:
        data = CostEvidenceFactory(
            end_lag_hours=12,
            observation_lag_seconds=119,
        ).data()
        result = self.call_analyzer(data)
        serverless = next(row for row in result["surface_inventory"] if row["surface"] == "serverless_usage")
        self.assertEqual(serverless["freshness_status"], "unsettled_window")
        self.assertFalse(serverless["window_end_precedes_settled_cutoff"])
        self.assertEqual(
            serverless["settlement_observed_at"],
            data["collector_receipt"]["datasets"]["execution_context"][0]["observed_at"].replace("Z", "+00:00"),
        )
        self.assertTrue(result["completeness_claim_blocked"])

    def test_raw_query_uuid_cannot_enter_hash_labeled_output(self) -> None:
        data = CostEvidenceFactory().data()
        row = data["query_attribution"][0]
        row["query_id_sha256"] = "123e4567-e89b-12d3-a456-426614174000"
        row["query_hash"] = None
        row["query_parameterized_hash"] = None
        self.sync_dataset_row(data, "query_attribution")
        with self.assertRaisesRegex(ANALYZER.EvidenceError, "query_id_sha256"):
            self.call_analyzer(data)

    def test_raw_query_fingerprints_cannot_enter_cost_outputs(self) -> None:
        for dataset in ("query_attribution", "adaptive_usage"):
            for field in ("query_hash", "query_parameterized_hash"):
                data = CostEvidenceFactory().data()
                data[dataset][0][field] = "ALICE"
                self.sync_dataset_row(data, dataset)
                with self.subTest(dataset=dataset, field=field), self.assertRaisesRegex(ANALYZER.EvidenceError, field):
                    self.call_analyzer(data)

    def test_raw_control_identifiers_cannot_enter_sha256_fields(self) -> None:
        cases = (
            ("resource_monitors", "name_sha256", "123e4567-e89b-12d3-a456-426614174000"),
            ("resource_monitors", "owner_sha256", "RAW_MONITOR_OWNER"),
            ("budgets", "name_sha256", "123e4567-e89b-12d3-a456-426614174000"),
            ("budgets", "database_name_sha256", "RAW_DATABASE"),
            ("budgets", "schema_name_sha256", "RAW_SCHEMA"),
            ("budgets", "owner_sha256", "RAW_BUDGET_OWNER"),
        )
        for dataset, field, value in cases:
            data = CostEvidenceFactory().data()
            data["controls_inventory"][dataset][0][field] = value
            self.sync_dataset_row(data, dataset)
            with self.subTest(dataset=dataset, field=field), self.assertRaisesRegex(ANALYZER.EvidenceError, field):
                self.call_analyzer(data)

    def test_caller_cannot_shrink_the_surface_denominator(self) -> None:
        data = CostEvidenceFactory().data()
        data["metadata"]["expected_surfaces"].remove("ai_usage")
        data["surface_inventory"] = [row for row in data["surface_inventory"] if row["surface"] != "ai_usage"]
        data["ai_usage"] = []
        data["supplemental_receipts"].pop("ai_usage")
        self.assert_fail_closed(data)

    def test_caller_latency_cannot_settle_a_recent_account_usage_window(self) -> None:
        data = CostEvidenceFactory(recent_window=True).data()
        for row in data["surface_inventory"]:
            row["documented_latency_hours"] = "1000000"
            row["latest_timestamp"] = data["metadata"]["generated_at"]
        self.assert_fail_closed(data)

    def test_metering_history_services_are_not_labeled_serverless(self) -> None:
        data = CostEvidenceFactory().data()
        data["serverless_usage"][1]["service_type"] = "WAREHOUSE_METERING"
        self.sync_dataset_row(data, "serverless_usage")
        result = self.call_analyzer(data)
        ledger = {row["entry_id"]: row for row in result["cost_ledger"]}
        warehouse = ledger["metering-total:WAREHOUSE_METERING"]
        self.assertEqual(warehouse["domain"], "metering:WAREHOUSE_METERING")
        self.assertEqual(warehouse["ledger_role"], "context")
        self.assertFalse(
            any(
                "serverless" in str(row.get(field, "")).casefold()
                for row in result["cost_ledger"]
                for field in ("entry_id", "domain")
            )
        )

    def test_query_acceleration_null_is_documented_zero_but_missing_is_invalid(self) -> None:
        data = CostEvidenceFactory().data()
        data["serverless_usage"].append(
            {
                "start_time": data["query_attribution"][0]["start_time"],
                "end_time": data["query_attribution"][0]["end_time"],
                "service_type": "QUERY_ACCELERATION",
                "credits_used": "0",
            }
        )
        data["query_attribution"][0]["credits_used_query_acceleration"] = None
        self.sync_dataset_row(data, "serverless_usage")
        self.sync_dataset_row(data, "query_attribution")
        result = self.call_analyzer(data)
        qas = next(row for row in result["cost_ledger"] if row["entry_id"] == "query-acceleration-attribution")
        self.assertEqual(qas["amount"], "0")

        missing = CostEvidenceFactory().data()
        missing["serverless_usage"].append(
            {
                "start_time": missing["query_attribution"][0]["start_time"],
                "end_time": missing["query_attribution"][0]["end_time"],
                "service_type": "QUERY_ACCELERATION",
                "credits_used": "0",
            }
        )
        missing["query_attribution"][0].pop("credits_used_query_acceleration")
        self.sync_dataset_row(missing, "serverless_usage")
        self.sync_dataset_row(missing, "query_attribution")
        with self.assertRaises(ANALYZER.EvidenceError):
            self.call_analyzer(missing)

    def test_unfinished_ai_and_adaptive_rows_are_quarantined(self) -> None:
        ai = CostEvidenceFactory().data()
        ai["ai_usage"][0]["is_completed"] = False
        self.sync_dataset_row(ai, "ai_usage")
        result = self.call_analyzer(ai)
        self.assertTrue(result["completeness_claim_blocked"])
        self.assertNotIn("ai-functions-attribution", {row["entry_id"] for row in result["cost_ledger"]})

        adaptive = CostEvidenceFactory().data()
        adaptive["adaptive_usage"][0]["query_end_time"] = None
        self.sync_dataset_row(adaptive, "adaptive_usage")
        result = self.call_analyzer(adaptive)
        self.assertTrue(result["completeness_claim_blocked"])
        self.assertNotIn("adaptive-compute-attribution", {row["entry_id"] for row in result["cost_ledger"]})

    def test_multi_hour_ai_call_includes_all_rows_only_after_completion(self) -> None:
        completed = CostEvidenceFactory().data()
        earlier = copy.deepcopy(completed["ai_usage"][0])
        earlier["credits_used"] = "3"
        earlier["is_completed"] = False
        earlier["function_name"] = "EMBED_TEXT_768"
        earlier["model_name_sha256"] = "8" * 64
        earlier["warehouse_id"] = "warehouse-id-2"
        completed_start = datetime.fromisoformat(
            completed["ai_usage"][0]["start_time"].replace("Z", "+00:00")
        ) + timedelta(hours=1)
        completed_end = datetime.fromisoformat(completed["ai_usage"][0]["end_time"].replace("Z", "+00:00")) + timedelta(
            hours=1
        )
        completed["ai_usage"][0]["start_time"] = iso(completed_start)
        completed["ai_usage"][0]["end_time"] = iso(completed_end)
        completed["ai_usage"].insert(0, earlier)
        self.sync_dataset_row(completed, "ai_usage")
        result = self.call_analyzer(completed)
        ledger = {row["entry_id"]: row for row in result["cost_ledger"]}
        self.assertEqual(ledger["ai-functions-attribution"]["amount"], "5.5")
        self.assertNotIn("COST_AI_IN_PROGRESS", {row["code"] for row in result["findings"]})

        mutable = CostEvidenceFactory().data()
        mutable["ai_usage"][0]["is_completed"] = False
        self.sync_dataset_row(mutable, "ai_usage")
        result = self.call_analyzer(mutable)
        self.assertIn("COST_AI_IN_PROGRESS", {row["code"] for row in result["findings"]})
        self.assertNotIn("ai-functions-attribution", {row["entry_id"] for row in result["cost_ledger"]})

    def test_adaptive_compute_and_cloud_services_do_not_share_a_compute_parent_amount(self) -> None:
        result = self.call_analyzer(CostEvidenceFactory().data())
        ledger = {row["entry_id"]: row for row in result["cost_ledger"]}
        adaptive_compute = ledger["adaptive-compute-attribution"]
        self.assertEqual(adaptive_compute["amount"], "1.5")
        self.assertEqual(adaptive_compute["parent_id"], "warehouse-compute-total")
        cloud_rows = [row for row in ledger.values() if row["domain"] == "adaptive_cloud_services"]
        self.assertEqual(len(cloud_rows), 1)
        self.assertEqual(cloud_rows[0]["amount"], "0.1")
        self.assertFalse(cloud_rows[0]["aggregation_eligible"])

    def test_rate_boolean_cannot_claim_invoice_reconciliation(self) -> None:
        data = CostEvidenceFactory().data()
        data["credit_rates"]["warehouse"]["invoice_reconciled"] = True
        with self.assertRaises(ANALYZER.EvidenceError):
            self.call_analyzer(data)

    def test_unreceipted_or_overlapping_invoice_rows_fail_closed(self) -> None:
        factory = CostEvidenceFactory()
        invoice = {
            "start_time": iso(factory.start),
            "end_time": iso(factory.end),
            "domain": "account-billing-period",
            "currency": "USD",
            "amount": "100",
        }
        single = factory.data()
        single["invoice_usage"] = [{**invoice, "statement_id": "statement-a"}]
        self.assert_fail_closed(single)

        duplicate = CostEvidenceFactory().data()
        duplicate["invoice_usage"] = [
            {**invoice, "statement_id": "statement-a"},
            {**invoice, "statement_id": "statement-b"},
        ]
        self.assert_fail_closed(duplicate)

    def test_control_coverage_and_visibility_cannot_be_added_outside_receipt(self) -> None:
        data = CostEvidenceFactory().data()
        data["controls_inventory"]["visibility_is_complete"] = True
        data["controls_inventory"]["budgets"][0]["covered_domains"] = [
            "serverless",
            "adaptive",
            "ai",
        ]
        try:
            result = self.call_analyzer(data)
        except ANALYZER.EvidenceError:
            return
        self.assertTrue(result["completeness_claim_blocked"])
        controls = result["controls_assessment"]
        self.assertFalse(controls.get("visibility_is_complete", False))
        self.assertFalse(controls.get("budget_covered_domains", []))

    def test_assigned_monitor_without_quota_or_actions_is_not_active_or_enforcing(self) -> None:
        result = self.call_analyzer(CostEvidenceFactory().data())
        controls = result["controls_assessment"]
        self.assertEqual(controls["visible_resource_monitors"], 1)
        self.assertEqual(controls["visible_assigned_monitors"], 1)
        self.assertEqual(controls["visible_enforcing_monitors"], 0)
        self.assertFalse(controls["visibility_is_complete"])
        self.assertNotIn("active_resource_monitors", controls)
        self.assertNotIn("monitor_enforcement_proven", controls)

    def test_duplicate_source_keys_or_incompatible_units_fail_closed(self) -> None:
        duplicate = CostEvidenceFactory().data()
        second = copy.deepcopy(duplicate["warehouse_metering"][0])
        second["warehouse_name_sha256"] = "2" * 64
        duplicate["warehouse_metering"].append(second)
        self.sync_dataset_row(duplicate, "warehouse_metering")
        self.assert_fail_closed(duplicate)

        duplicate_load = CostEvidenceFactory().data()
        second_load = copy.deepcopy(duplicate_load["warehouse_load"][0])
        second_load["warehouse_name_sha256"] = "2" * 64
        duplicate_load["warehouse_load"].append(second_load)
        self.sync_dataset_row(duplicate_load, "warehouse_load")
        self.assert_fail_closed(duplicate_load)

        duplicate_serverless = CostEvidenceFactory().data()
        duplicate_serverless["serverless_usage"].append(copy.deepcopy(duplicate_serverless["serverless_usage"][0]))
        self.sync_dataset_row(duplicate_serverless, "serverless_usage")
        self.assert_fail_closed(duplicate_serverless)

        incompatible = CostEvidenceFactory().data()
        incompatible["adaptive_usage"][0]["unit"] = "currency"
        self.sync_dataset_row(incompatible, "adaptive_usage")
        self.assert_fail_closed(incompatible)

    def test_orphan_attribution_parent_is_not_emitted(self) -> None:
        data = CostEvidenceFactory().data()
        data["serverless_usage"] = [row for row in data["serverless_usage"] if row["service_type"] != "AI_SERVICES"]
        self.sync_dataset_row(data, "serverless_usage")
        result = self.call_analyzer(data)
        self.assertTrue(result["completeness_claim_blocked"])
        self.assertNotIn("ai-functions-attribution", {row["entry_id"] for row in result["cost_ledger"]})

    def test_nonclaims_are_scoped_to_reviewed_code_not_the_surrounding_session(self) -> None:
        result = self.call_analyzer(CostEvidenceFactory().data())
        joined = " ".join(result["non_claims"]).casefold()
        self.assertIn("reviewed collector sql", joined)
        self.assertIn("surrounding session", joined)
        self.assertNotIn("no snowflake object or configuration was mutated", joined)


if __name__ == "__main__":
    unittest.main()
