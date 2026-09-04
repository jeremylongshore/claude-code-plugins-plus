#!/usr/bin/env python3
"""Adversarial schema-2 tests for the data-quality analyzer."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest import mock

HERE = pathlib.Path(__file__).resolve().parent
SCRIPT = HERE.parent / "scripts" / "analyze_data_quality.py"
COLLECTOR_SCRIPT = HERE.parent / "scripts" / "collect_snowflake_evidence.py"
SPEC = importlib.util.spec_from_file_location("analyze_data_quality", SCRIPT)
assert SPEC and SPEC.loader
analyzer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(analyzer)
COLLECTOR_SPEC = importlib.util.spec_from_file_location("collect_snowflake_evidence", COLLECTOR_SCRIPT)
assert COLLECTOR_SPEC and COLLECTOR_SPEC.loader
collector = importlib.util.module_from_spec(COLLECTOR_SPEC)
COLLECTOR_SPEC.loader.exec_module(collector)


class DataQualityAnalyzerTests(unittest.TestCase):
    EVALUATED = datetime(2026, 9, 3, 12, tzinfo=timezone.utc)

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.sql_dir = pathlib.Path(self.temp.name)

    @staticmethod
    def h(character: str) -> str:
        return character * 64

    def requirement(self, **updates) -> dict:
        row = {
            "requirement_key_sha256": self.h("1"),
            "object_key_sha256": self.h("2"),
            "association_key_sha256": self.h("3"),
            "metric_key_sha256": self.h("4"),
            "expectation_key_sha256": self.h("5"),
            "definition_sha256": self.h("6"),
            "schedule_sha256": self.h("7"),
            "expected_execution_role_sha256": self.h("8"),
            "group_definition_sha256": None,
            "schedule_mode": "INTERVAL",
            "max_result_age_seconds": 10800,
            "notification_required": False,
            "objective_mode": "EXPECTATION",
            "object_domain": "TABLE",
            "filter_sha256": None,
            "expected_group_limit": None,
        }
        row.update(updates)
        return row

    def context(self) -> dict:
        return {
            "observed_at": "2026-09-03T11:59:30+00:00",
            "organization_name_sha256": self.h("a"),
            "account_identifier_sha256": self.h("b"),
            "collector_user_sha256": self.h("c"),
            "primary_role_sha256": self.h("d"),
            "primary_role_type": "ROLE",
            "secondary_roles_sha256": self.h("e"),
            "timezone": "UTC",
        }

    def row(self, dataset: str, **updates) -> dict:
        values = {field: None for field in analyzer.DATASET_FIELDS[dataset]}
        if dataset == "expectation_history":
            values.update(
                object_key_sha256=self.h("2"),
                association_key_sha256=self.h("3"),
                metric_key_sha256=self.h("4"),
                expectation_key_sha256=self.h("5"),
                definition_sha256=self.h("6"),
                scheduled_time="2026-09-03T09:55:00+00:00",
                change_commit_time="2026-09-03T09:56:00+00:00",
                measurement_time="2026-09-03T10:00:00+00:00",
                expectation_violated=False,
            )
        elif dataset == "current_associations":
            values.update(
                object_key_sha256=self.h("2"),
                association_key_sha256=self.h("3"),
                metric_key_sha256=self.h("4"),
                object_domain="TABLE",
                schedule_sha256=self.h("7"),
                schedule_status="STARTED",
                execution_role_sha256=self.h("8"),
                association_level="TABLE",
                filter_sha256=None,
                group_definition_sha256=None,
                group_limit=None,
                anomaly_status="NOT_CONFIGURED",
                anomaly_sensitivity="NOT_CONFIGURED",
            )
        elif dataset == "current_expectations":
            values.update(
                object_key_sha256=self.h("2"),
                association_key_sha256=self.h("3"),
                metric_key_sha256=self.h("4"),
                expectation_key_sha256=self.h("5"),
                definition_sha256=self.h("6"),
            )
        else:
            values.update(
                object_key_sha256=self.h("2"),
                association_key_sha256=self.h("3"),
                metric_key_sha256=self.h("4"),
                object_domain="TABLE",
                notification_status="ENABLED",
            )
        values.update(updates)
        return values

    def receipt(
        self,
        surface: str,
        rows: list[dict] | None = None,
        *,
        selected_object_key_sha256: str | None = None,
        selected_object_domain: str = "TABLE",
    ) -> dict:
        contract = analyzer.RECEIPT_CONTRACTS[surface]
        dataset = next(iter(contract["cap_datasets"]))
        rows = list(rows if rows is not None else [self.row(dataset)])
        context = self.context()
        metadata = {
            "template": contract["template"],
            "source_views": contract["sources"],
            "selector": dict(contract["selector"]),
        }
        sql_path = analyzer.SQL_DIR / contract["template"]
        sql = sql_path.read_text(encoding="utf-8")
        sql_hash = "sha256:" + hashlib.sha256(sql_path.read_bytes()).hexdigest()
        rendered_hash = sql_hash
        selector_fingerprint = None
        if surface == "data-quality":
            context.update(
                window_start_utc="2026-09-01T00:00:00+00:00",
                window_end_utc="2026-09-03T11:00:00+00:00",
                window_semantics="HALF_OPEN_UTC",
                per_dataset_row_limit=5000,
                provider_latency_documented=False,
                settlement_policy_status="NOT_DECLARED",
            )
            selector = {"window_start": "2026-09-01T00:00:00Z", "window_end": "2026-09-03T11:00:00Z"}
            metadata["selector_values"] = selector
            selector_fingerprint = analyzer.digest(selector)
            rendered = sql.replace("__WINDOW_START_UTC__", selector["window_start"]).replace(
                "__WINDOW_END_UTC__", selector["window_end"]
            )
            rendered_hash = "sha256:" + hashlib.sha256(rendered.encode()).hexdigest()
        else:
            selected_object_key_sha256 = selected_object_key_sha256 or self.h("2")
            context.update(
                source_row_count=len(rows),
                source_row_limit=5000,
                truncation_possible=False,
                selected_object_key_sha256=selected_object_key_sha256,
                selected_object_domain=selected_object_domain,
            )
            binding = {
                "selected_object_key_sha256": selected_object_key_sha256,
                "selected_object_domain": selected_object_domain,
            }
            metadata.update(selector_binding=binding, rendered_sql_contract="privacy-bound-selector-v1")
            selector_fingerprint = analyzer.digest(binding)
            rendered = sql.replace(
                "__DATA_QUALITY_DATABASE_IDENTIFIER__",
                f"__DATA_QUALITY_DATABASE_BOUND_TO_OBJECT_KEY_SHA256_{selected_object_key_sha256}__",
            )
            rendered = rendered.replace(
                "__DATA_QUALITY_OBJECT_IDENTIFIER__",
                f"__DATA_QUALITY_OBJECT_KEY_SHA256_{selected_object_key_sha256}__",
            )
            rendered = rendered.replace("__DATA_QUALITY_DOMAIN__", f"__DATA_QUALITY_DOMAIN_{selected_object_domain}__")
            rendered_hash = "sha256:" + hashlib.sha256(rendered.encode()).hexdigest()
        datasets = {dataset: rows, "execution_context": [context]}
        receipt = {
            "schema_version": "2",
            "surface": surface,
            "status": "collected",
            "collected_at": "2026-09-03T12:00:00+00:00",
            "collection_mode": "live-cli",
            "collection_started_at": "2026-09-03T11:59:00+00:00",
            "collection_completed_at": "2026-09-03T12:00:00+00:00",
            "connection_profile_sha256": "sha256:" + self.h("f"),
            "sql_sha256": sql_hash,
            "template_sha256": sql_hash,
            "rendered_sql_sha256": rendered_hash,
            "selector_fingerprint": selector_fingerprint,
            "source_metadata": metadata,
            "source_views": contract["sources"],
            "row_count": sum(len(value) for value in datasets.values()),
            "row_limit": 5000,
            "cap_scope": "per_dataset",
            "truncation_possible": False,
            "dataset_row_counts": {name: len(value) for name, value in datasets.items()},
            "expected_datasets": sorted(contract["datasets"]),
            "datasets": datasets,
            "errors": [],
            "non_claims": list(analyzer.RECEIPT_NON_CLAIMS),
            "result_sha256": analyzer.digest(datasets),
            "snowflake_query_id": None,
            "snowflake_query_id_status": "not_exposed_by_snow_cli_json_ext",
        }
        self.rehash_receipt(receipt)
        return receipt

    @staticmethod
    def rehash_receipt(receipt: dict) -> None:
        body = dict(receipt)
        body.pop("receipt_sha256", None)
        receipt["receipt_sha256"] = analyzer.digest(body)

    def rehash_result(self, receipt: dict) -> None:
        receipt["row_count"] = sum(len(rows) for rows in receipt["datasets"].values())
        receipt["dataset_row_counts"] = {name: len(rows) for name, rows in receipt["datasets"].items()}
        receipt["result_sha256"] = analyzer.digest(receipt["datasets"])
        self.rehash_receipt(receipt)

    def bundle(self, requirement: dict | None = None) -> dict:
        requirement = requirement or self.requirement()
        return {
            "schema_version": "2",
            "policy": {
                "schema_version": "1",
                "expected_requirement_count": 1,
                "analysis_as_of_utc": self.EVALUATED.isoformat(),
                "history_assumption_delay_seconds": 1800,
                "history_assumption_status": "OWNER_DECLARED_NOT_PROVIDER_GUARANTEED",
                "requirements": [requirement],
            },
            "collector_receipts": [
                self.receipt("data-quality"),
                self.receipt("data-quality-associations-current"),
                self.receipt("data-quality-expectations-current"),
            ],
        }

    def analyze(self, data: dict, *, input_digest: str | None = None, policy_digest: str | None = None) -> dict:
        return analyzer.analyze(
            data,
            evaluated_at=self.EVALUATED.isoformat(),
            trusted_input_sha256=input_digest or analyzer.canonical_input_digest(data),
            trusted_policy_sha256=policy_digest or analyzer.canonical_policy_digest(data),
        )

    @staticmethod
    def codes(report: dict) -> set[str]:
        return {item["code"] for item in report["findings"]}

    def test_false_result_is_satisfied_observation_never_quality_pass(self):
        report = self.analyze(self.bundle())
        self.assertTrue(report["structural_evidence_valid"])
        self.assertEqual(report["evidence_integrity_status"], "VALID")
        self.assertEqual(report["governed_coverage_status"], "COMPLETE")
        self.assertFalse(report["evidence_complete"])
        self.assertEqual(report["configuration_status"], "PASS")
        self.assertEqual(report["quality_status"], "INCONCLUSIVE")
        self.assertEqual(report["history_observation_status"], "SATISFIED_OBSERVATION")
        self.assertEqual(report["history_completeness_status"], "UNPROVEN_NO_PROVIDER_SLA")
        self.assertFalse(report["pass_supported"])
        self.assertIsNone(report["settled_through_utc"])
        self.assertEqual(report["findings"], [])

    def test_current_contracts_are_selector_bound_live_information_schema(self):
        expected_sources = {
            "data-quality-associations-current": ["INFORMATION_SCHEMA.DATA_METRIC_FUNCTION_REFERENCES"],
            "data-quality-expectations-current": ["INFORMATION_SCHEMA.DATA_METRIC_FUNCTION_EXPECTATIONS"],
        }
        for surface, sources in expected_sources.items():
            with self.subTest(surface=surface):
                contract = analyzer.RECEIPT_CONTRACTS[surface]
                self.assertEqual(contract["sources"], sources)
                self.assertEqual(
                    contract["selector"],
                    {"data_quality_object": True, "data_quality_domain": True},
                )
                self.assertNotIn("ACCOUNT_USAGE", " ".join(contract["sources"]))

    def test_no_evaluation_is_inconclusive_not_pass(self):
        data = self.bundle()
        data["collector_receipts"][0] = self.receipt("data-quality", [])
        report = self.analyze(data)
        self.assertEqual(report["quality_status"], "INCONCLUSIVE")
        self.assertIn("DQ_NO_EVALUATION", self.codes(report))

    def test_zero_requirement_policy_does_not_report_configuration_pass(self):
        data = self.bundle()
        data["policy"]["expected_requirement_count"] = 0
        data["policy"]["requirements"] = []
        data["collector_receipts"] = [data["collector_receipts"][0]]
        report = self.analyze(data)
        self.assertTrue(report["structural_evidence_valid"])
        self.assertEqual(report["configuration_status"], "INCONCLUSIVE")
        self.assertEqual(report["quality_status"], "INCONCLUSIVE")
        self.assertEqual(report["history_observation_status"], "NOT_OBSERVED")

    def test_owner_history_assumption_never_becomes_provider_finality(self):
        for delay in (None, 0, 3600):
            with self.subTest(delay=delay):
                data = self.bundle()
                data["policy"]["history_assumption_delay_seconds"] = delay
                report = self.analyze(data)
                self.assertEqual(report["quality_status"], "INCONCLUSIVE")
                self.assertEqual(report["history_completeness_status"], "UNPROVEN_NO_PROVIDER_SLA")
                self.assertFalse(report["pass_supported"])

    def test_true_and_null_results_are_distinct(self):
        for value, code, quality in (
            (True, "DQ_EXPECTATION_VIOLATED", "FAIL"),
            (None, "DQ_EXPECTATION_EVALUATION_FAILED", "INCONCLUSIVE"),
        ):
            with self.subTest(value=value):
                data = self.bundle()
                data["collector_receipts"][0] = self.receipt(
                    "data-quality", [self.row("expectation_history", expectation_violated=value)]
                )
                report = self.analyze(data)
                self.assertEqual(report["quality_status"], quality)
                self.assertIn(code, self.codes(report))

    def test_policy_denominator_count_and_duplicate_expectation_keys_are_rejected(self):
        for mutation in ("count", "requirement", "expectation"):
            data = self.bundle()
            duplicate = copy.deepcopy(data["policy"]["requirements"][0])
            if mutation == "count":
                data["policy"]["expected_requirement_count"] = 2
            else:
                if mutation == "requirement":
                    duplicate["expectation_key_sha256"] = self.h("9")
                else:
                    duplicate["requirement_key_sha256"] = self.h("9")
                data["policy"]["requirements"].append(duplicate)
                data["policy"]["expected_requirement_count"] = 2
            with self.subTest(mutation=mutation), self.assertRaises(analyzer.EvidenceError):
                self.analyze(data)

    def test_multiple_expectations_may_share_one_association(self):
        data = self.bundle()
        second = self.requirement(
            requirement_key_sha256=self.h("9"),
            expectation_key_sha256=self.h("0"),
            definition_sha256=self.h("a"),
        )
        data["policy"]["requirements"].append(second)
        data["policy"]["expected_requirement_count"] = 2
        history = data["collector_receipts"][0]
        history["datasets"]["expectation_history"].append(
            self.row(
                "expectation_history",
                expectation_key_sha256=self.h("0"),
                definition_sha256=self.h("a"),
            )
        )
        self.rehash_result(history)
        expectations = data["collector_receipts"][2]
        expectations["datasets"]["current_expectations"].append(
            self.row(
                "current_expectations",
                expectation_key_sha256=self.h("0"),
                definition_sha256=self.h("a"),
            )
        )
        expectations["datasets"]["execution_context"][0]["source_row_count"] = 2
        self.rehash_result(expectations)
        report = self.analyze(data)
        self.assertTrue(report["structural_evidence_valid"])
        self.assertEqual(report["configuration_status"], "PASS")
        self.assertEqual(report["denominator"]["evaluated_requirements"], 2)

    def test_missing_surface_and_each_surface_truncation_fail_closed(self):
        data = self.bundle()
        data["collector_receipts"].pop()
        report = self.analyze(data)
        self.assertFalse(report["structural_evidence_valid"])
        self.assertEqual(report["quality_status"], "INCONCLUSIVE")
        for surface in analyzer.REQUIRED_SINGLETON_SURFACES:
            with self.subTest(surface=surface):
                data = self.bundle()
                receipt = next(r for r in data["collector_receipts"] if r["surface"] == surface)
                receipt["truncation_possible"] = True
                receipt["datasets"][next(iter(analyzer.RECEIPT_CONTRACTS[surface]["cap_datasets"]))] *= 5000
                self.rehash_result(receipt)
                self.assertFalse(self.analyze(data)["structural_evidence_valid"])

    def test_self_rehashed_tamper_still_fails_external_trust(self):
        data = self.bundle()
        trusted = analyzer.canonical_input_digest(data)
        history = data["collector_receipts"][0]
        history["datasets"]["expectation_history"][0]["expectation_violated"] = True
        self.rehash_result(history)
        report = self.analyze(data, input_digest=trusted)
        self.assertFalse(report["structural_evidence_valid"])
        self.assertNotIn("DQ_EXPECTATION_VIOLATED", self.codes(report))

    def test_policy_tamper_has_an_independent_trust_boundary(self):
        data = self.bundle()
        trusted_policy = analyzer.canonical_policy_digest(data)
        data["policy"]["requirements"][0]["max_result_age_seconds"] += 1
        report = self.analyze(data, policy_digest=trusted_policy)
        self.assertFalse(report["structural_evidence_valid"])
        self.assertFalse(report["provenance"]["trusted_policy"])

    def test_stale_collection_and_mixed_context_fail_closed(self):
        data = self.bundle()
        receipt = data["collector_receipts"][1]
        receipt["collection_started_at"] = "2026-09-03T11:40:00+00:00"
        self.rehash_receipt(receipt)
        self.assertFalse(self.analyze(data)["structural_evidence_valid"])
        data = self.bundle()
        receipt = data["collector_receipts"][1]
        receipt["datasets"]["execution_context"][0]["account_identifier_sha256"] = self.h("9")
        self.rehash_result(receipt)
        report = self.analyze(data)
        self.assertFalse(report["structural_evidence_valid"])
        self.assertIn("mixed_execution_context", report["evidence_gap_codes"])

    def test_observed_at_freshness_accepts_900_seconds_and_rejects_901(self):
        for age, valid in ((900, True), (901, False)):
            with self.subTest(age=age):
                data = self.bundle()
                observed = self.EVALUATED - timedelta(seconds=age)
                for receipt in data["collector_receipts"]:
                    receipt["collection_started_at"] = observed.isoformat()
                    receipt["collection_completed_at"] = "2026-09-03T11:45:00+00:00"
                    receipt["collected_at"] = "2026-09-03T11:45:00+00:00"
                    receipt["datasets"]["execution_context"][0]["observed_at"] = observed.isoformat()
                    self.rehash_result(receipt)
                self.assertIs(self.analyze(data)["structural_evidence_valid"], valid)

    def test_policy_analysis_time_is_bound_to_evaluated_at(self):
        data = self.bundle()
        data["policy"]["analysis_as_of_utc"] = "2026-09-03T11:59:59+00:00"
        with self.assertRaises(analyzer.EvidenceError):
            self.analyze(data)

    def test_selector_contract_requires_real_booleans(self):
        for surface in analyzer.RECEIPT_CONTRACTS:
            with self.subTest(surface=surface):
                data = self.bundle(
                    self.requirement(notification_required=surface == "data-quality-notification-current")
                )
                if surface == "data-quality-notification-current":
                    data["collector_receipts"].append(self.receipt(surface))
                receipt = next(item for item in data["collector_receipts"] if item["surface"] == surface)
                receipt["source_metadata"]["selector"][next(iter(receipt["source_metadata"]["selector"]))] = 1
                self.rehash_receipt(receipt)
                report = self.analyze(data)
                self.assertFalse(report["structural_evidence_valid"])
                self.assertIn("receipt_source_contract", report["evidence_gap_codes"])

    def test_every_governed_object_requires_both_live_receipts(self):
        data = self.bundle()
        second = self.requirement(
            requirement_key_sha256=self.h("9"),
            object_key_sha256=self.h("0"),
            association_key_sha256=self.h("a"),
            metric_key_sha256=self.h("b"),
            expectation_key_sha256=self.h("c"),
            definition_sha256=self.h("d"),
            schedule_sha256=self.h("e"),
            expected_execution_role_sha256=self.h("f"),
        )
        data["policy"]["requirements"].append(second)
        data["policy"]["expected_requirement_count"] = 2
        missing = self.analyze(data)
        self.assertFalse(missing["structural_evidence_valid"])
        self.assertIn("governed_object_coverage", missing["evidence_gap_codes"])

        association = self.row(
            "current_associations",
            object_key_sha256=self.h("0"),
            association_key_sha256=self.h("a"),
            metric_key_sha256=self.h("b"),
            schedule_sha256=self.h("e"),
            execution_role_sha256=self.h("f"),
        )
        expectation = self.row(
            "current_expectations",
            object_key_sha256=self.h("0"),
            association_key_sha256=self.h("a"),
            metric_key_sha256=self.h("b"),
            expectation_key_sha256=self.h("c"),
            definition_sha256=self.h("d"),
        )
        data["collector_receipts"].extend(
            [
                self.receipt(
                    "data-quality-associations-current",
                    [association],
                    selected_object_key_sha256=self.h("0"),
                ),
                self.receipt(
                    "data-quality-expectations-current",
                    [expectation],
                    selected_object_key_sha256=self.h("0"),
                ),
            ]
        )
        report = self.analyze(data)
        self.assertTrue(report["structural_evidence_valid"])
        self.assertIn("DQ_NO_EVALUATION", self.codes(report))

    def test_definition_schedule_role_and_group_drift_block_pass(self):
        cases = (
            (
                "data-quality-expectations-current",
                "current_expectations",
                "definition_sha256",
                self.h("9"),
                "DQ_DEFINITION_DRIFT",
            ),
            (
                "data-quality-associations-current",
                "current_associations",
                "schedule_sha256",
                self.h("9"),
                "DQ_SCHEDULE_DRIFT",
            ),
            (
                "data-quality-associations-current",
                "current_associations",
                "execution_role_sha256",
                None,
                "DQ_EXECUTION_ROLE_DRIFT",
            ),
            (
                "data-quality-associations-current",
                "current_associations",
                "group_definition_sha256",
                self.h("9"),
                "DQ_GROUP_DEFINITION_DRIFT",
            ),
        )
        for surface, dataset, field, value, code in cases:
            with self.subTest(field=field):
                data = self.bundle()
                receipt = next(r for r in data["collector_receipts"] if r["surface"] == surface)
                receipt["datasets"][dataset][0][field] = value
                self.rehash_result(receipt)
                report = self.analyze(data)
                self.assertIn(code, self.codes(report))
                self.assertNotEqual(report["configuration_status"], "PASS")

    def test_object_domain_filter_and_group_limit_drift_block_pass(self):
        cases = (
            ("object_domain", "VIEW", "DQ_OBJECT_DOMAIN_DRIFT"),
            ("filter_sha256", self.h("9"), "DQ_FILTER_DRIFT"),
            ("group_limit", 12, "DQ_GROUP_LIMIT_DRIFT"),
        )
        for field, value, code in cases:
            with self.subTest(field=field):
                data = self.bundle()
                receipt = data["collector_receipts"][1]
                receipt["datasets"]["current_associations"][0][field] = value
                self.rehash_result(receipt)
                report = self.analyze(data)
                if field == "object_domain":
                    self.assertFalse(report["structural_evidence_valid"])
                else:
                    self.assertIn(code, self.codes(report))
                    self.assertNotEqual(report["configuration_status"], "PASS")

    def test_group_limit_is_nullable_or_between_one_and_one_thousand(self):
        for value in (0, 1001, True):
            with self.subTest(policy_value=value):
                with self.assertRaises(analyzer.EvidenceError):
                    self.analyze(self.bundle(self.requirement(expected_group_limit=value)))
            with self.subTest(row_value=value):
                data = self.bundle()
                receipt = data["collector_receipts"][1]
                receipt["datasets"]["current_associations"][0]["group_limit"] = value
                self.rehash_result(receipt)
                self.assertFalse(self.analyze(data)["structural_evidence_valid"])

    def test_documented_and_provider_other_association_states_fail_closed(self):
        cases = (
            (
                "schedule_status",
                "STARTED_AND_PENDING_SCHEDULE_UPDATE",
                "DQ_SCHEDULE_UPDATE_PENDING",
            ),
            (
                "schedule_status",
                "SUSPENDED_INSUFFICIENT_PRIVILEGE_TO_EXECUTE_DATA_METRIC_FUNCTION",
                "DQ_ASSOCIATION_SUSPENDED",
            ),
            ("schedule_status", "PROVIDER_OTHER", "DQ_SCHEDULE_STATE_UNREVIEWED"),
            ("association_level", "PROVIDER_OTHER", "DQ_ASSOCIATION_LEVEL_UNREVIEWED"),
            ("object_domain", "PROVIDER_OTHER", "DQ_OBJECT_DOMAIN_DRIFT"),
        )
        for field, value, code in cases:
            with self.subTest(field=field, value=value):
                data = self.bundle()
                receipt = data["collector_receipts"][1]
                receipt["datasets"]["current_associations"][0][field] = value
                self.rehash_result(receipt)
                report = self.analyze(data)
                if field == "object_domain":
                    self.assertFalse(report["structural_evidence_valid"])
                else:
                    self.assertTrue(report["structural_evidence_valid"])
                    self.assertIn(code, self.codes(report))
                    self.assertNotEqual(report["configuration_status"], "PASS")
                    if code == "DQ_SCHEDULE_UPDATE_PENDING":
                        pending = next(item for item in report["findings"] if item["code"] == code)
                        self.assertIn("Wait for Snowflake", pending["action"])
                        self.assertIn("recollect", pending["action"])
                        self.assertNotIn("Resume", pending["action"])

    def test_trigger_group_and_anomaly_claims_remain_inconclusive(self):
        cases = (
            ({"schedule_mode": "TRIGGER_ON_CHANGES"}, "DQ_TRIGGER_FRESHNESS_UNPROVEN"),
            ({"group_definition_sha256": self.h("9")}, "DQ_GROUP_EVIDENCE_UNAVAILABLE"),
            ({"objective_mode": "ANOMALY"}, "DQ_ANOMALY_EVIDENCE_UNAVAILABLE"),
        )
        for changes, code in cases:
            with self.subTest(code=code):
                requirement = self.requirement(**changes)
                data = self.bundle(requirement)
                if "group_definition_sha256" in changes:
                    association = data["collector_receipts"][1]
                    association["datasets"]["current_associations"][0]["group_definition_sha256"] = self.h("9")
                    self.rehash_result(association)
                report = self.analyze(data)
                self.assertEqual(report["quality_status"], "INCONCLUSIVE")
                self.assertIn(code, self.codes(report))

    def test_notification_states_do_not_claim_delivery(self):
        for state, code in (
            ("ENABLED", None),
            ("DISABLED", "DQ_NOTIFICATION_DISABLED"),
            ("ERROR_INSUFFICIENT_PRIVILEGE", "DQ_NOTIFICATION_PRIVILEGE_ERROR"),
            ("NOT_CONFIGURED", "DQ_NOTIFICATION_NOT_CONFIGURED"),
            ("PROVIDER_OTHER", "DQ_NOTIFICATION_STATE_UNREVIEWED"),
        ):
            with self.subTest(state=state):
                data = self.bundle(self.requirement(notification_required=True))
                data["collector_receipts"].append(
                    self.receipt(
                        "data-quality-notification-current",
                        [self.row("notification_associations", notification_status=state)],
                    )
                )
                report = self.analyze(data)
                self.assertEqual(report["notification_delivery_status"], "NOT_OBSERVED")
                if code:
                    self.assertIn(code, self.codes(report))
                else:
                    self.assertEqual(report["configuration_status"], "PASS")

    def test_missing_or_duplicate_notification_selector_fails_closed(self):
        data = self.bundle(self.requirement(notification_required=True))
        self.assertFalse(self.analyze(data)["structural_evidence_valid"])
        data["collector_receipts"].extend(
            [
                self.receipt("data-quality-notification-current"),
                self.receipt("data-quality-notification-current"),
            ]
        )
        report = self.analyze(data)
        self.assertFalse(report["structural_evidence_valid"])
        self.assertIn("duplicate_object_selector", report["evidence_gap_codes"])
        self.assertEqual(report["governed_coverage_status"], "INCOMPLETE")

    def test_duplicate_natural_keys_are_rejected_before_classification(self):
        for surface in analyzer.REQUIRED_SINGLETON_SURFACES:
            with self.subTest(surface=surface):
                data = self.bundle()
                receipt = next(r for r in data["collector_receipts"] if r["surface"] == surface)
                dataset = next(iter(analyzer.RECEIPT_CONTRACTS[surface]["cap_datasets"]))
                receipt["datasets"][dataset].append(copy.deepcopy(receipt["datasets"][dataset][0]))
                receipt["datasets"]["execution_context"][0]["source_row_count"] = (
                    2
                    if surface != "data-quality"
                    else receipt["datasets"]["execution_context"][0].get("source_row_count")
                )
                if surface == "data-quality":
                    receipt["datasets"]["execution_context"][0].pop("source_row_count", None)
                self.rehash_result(receipt)
                report = self.analyze(data)
                self.assertFalse(report["structural_evidence_valid"])
                self.assertEqual(self.codes(report), {"DQ_EVIDENCE_INCOMPLETE"})

    def test_invalid_schema_enum_hash_and_offline_mode_never_classify(self):
        mutations = (
            lambda r: r.update(collection_mode="offline-normalized"),
            lambda r: r["datasets"]["current_associations"][0].update(object_domain="RAW_MARKER"),
            lambda r: r["datasets"]["current_associations"][0].update(metric_key_sha256="bad"),
            lambda r: r.update(unreviewed_raw_field="RAW_MARKER"),
        )
        for mutate in mutations:
            data = self.bundle()
            receipt = data["collector_receipts"][1]
            mutate(receipt)
            self.rehash_result(receipt)
            report = self.analyze(data)
            rendered = json.dumps(report)
            self.assertFalse(report["structural_evidence_valid"])
            self.assertEqual(self.codes(report), {"DQ_EVIDENCE_INCOMPLETE"})
            self.assertNotIn("RAW_MARKER", rendered)

    def test_unexpected_receipt_field_and_value_never_reflect(self):
        marker = "ATTACKER_RAW_IDENTITY_MARKER"
        data = self.bundle()
        receipt = data["collector_receipts"][1]
        receipt[marker] = marker
        self.rehash_receipt(receipt)
        report = self.analyze(data)
        self.assertNotIn(marker, json.dumps(report))
        policy_path = self.sql_dir / "policy.json"
        policy_path.write_text(json.dumps(data["policy"]), encoding="utf-8")
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--evaluated-at",
                self.EVALUATED.isoformat(),
                "--trusted-input-sha256",
                analyzer.canonical_input_digest(data),
                "--trusted-policy-sha256",
                analyzer.canonical_policy_digest(data),
                "--policy-file",
                str(policy_path),
            ],
            input=json.dumps(data),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0)
        self.assertNotIn(marker, completed.stdout + completed.stderr)

    def test_out_of_scope_history_is_counted_without_identity_reflection(self):
        data = self.bundle()
        history = data["collector_receipts"][0]
        history["datasets"]["expectation_history"].append(
            self.row(
                "expectation_history",
                object_key_sha256=self.h("9"),
                association_key_sha256=self.h("a"),
                metric_key_sha256=self.h("b"),
                expectation_key_sha256=self.h("c"),
                definition_sha256=self.h("d"),
            )
        )
        self.rehash_result(history)
        report = self.analyze(data)
        rendered = json.dumps(report)
        self.assertEqual(report["out_of_scope_observation_count"], 1)
        self.assertNotIn(self.h("9"), rendered)
        self.assertEqual(report["history_observation_status"], "SATISFIED_OBSERVATION")

    def test_measurement_at_half_open_window_end_fails_closed(self):
        data = self.bundle()
        receipt = data["collector_receipts"][0]
        receipt["datasets"]["expectation_history"][0]["measurement_time"] = "2026-09-03T11:00:00+00:00"
        self.rehash_result(receipt)
        report = self.analyze(data)
        self.assertFalse(report["structural_evidence_valid"])
        self.assertEqual(self.codes(report), {"DQ_EVIDENCE_INCOMPLETE"})

    def test_result_freshness_cutoff_is_inclusive_then_stale_by_one_second(self):
        exact = self.analyze(self.bundle(self.requirement(max_result_age_seconds=7200)))
        self.assertEqual(exact["history_observation_status"], "SATISFIED_OBSERVATION")
        stale = self.analyze(self.bundle(self.requirement(max_result_age_seconds=7199)))
        self.assertEqual(stale["quality_status"], "INCONCLUSIVE")
        self.assertIn("DQ_RESULT_STALE", self.codes(stale))

    def test_analyzer_source_has_no_network_collector_or_write_path(self):
        source = SCRIPT.read_text(encoding="utf-8")
        for forbidden in (
            "import subprocess",
            "import socket",
            "snowflake.connector",
            "collect_snowflake_evidence",
            ".write_text(",
            ".write_bytes(",
            ".unlink(",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)

    def test_boolean_values_do_not_satisfy_integer_receipt_fields(self):
        for field in ("row_count", "row_limit"):
            with self.subTest(field=field):
                data = self.bundle()
                receipt = data["collector_receipts"][0]
                receipt[field] = True
                self.rehash_receipt(receipt)
                self.assertFalse(self.analyze(data)["structural_evidence_valid"])

    def test_current_full_count_may_exceed_capped_rows_but_not_below_cap(self):
        data = self.bundle()
        receipt = data["collector_receipts"][1]
        rows = receipt["datasets"]["current_associations"] * 5000
        receipt["datasets"]["current_associations"] = rows
        context = receipt["datasets"]["execution_context"][0]
        context["source_row_count"] = 7000
        context["truncation_possible"] = True
        receipt["truncation_possible"] = True
        self.rehash_result(receipt)
        report = self.analyze(data)
        self.assertFalse(report["structural_evidence_valid"])
        self.assertIn("receipt_truncated", report["evidence_gap_codes"])

        data = self.bundle()
        receipt = data["collector_receipts"][1]
        receipt["datasets"]["execution_context"][0]["source_row_count"] = 2
        self.rehash_result(receipt)
        report = self.analyze(data)
        self.assertFalse(report["structural_evidence_valid"])
        self.assertIn("selector_context", report["evidence_gap_codes"])

    def test_notification_rendered_sql_hash_is_verified(self):
        data = self.bundle(self.requirement(notification_required=True))
        receipt = self.receipt("data-quality-notification-current")
        receipt["rendered_sql_sha256"] = "sha256:" + self.h("0")
        self.rehash_receipt(receipt)
        data["collector_receipts"].append(receipt)
        report = self.analyze(data)
        self.assertFalse(report["structural_evidence_valid"])
        self.assertIn("selector_rendered_hash", report["evidence_gap_codes"])

    def test_input_is_not_mutated_and_output_is_deterministic(self):
        data = self.bundle()
        before = copy.deepcopy(data)
        with mock.patch("pathlib.Path.write_text", side_effect=AssertionError("write attempted")):
            first = self.analyze(data)
            second = self.analyze(data)
        self.assertEqual(data, before)
        self.assertEqual(first, second)

    def test_actual_collector_history_receipt_matches_analyzer_contract(self):
        path, template, rendered, sources, selector = collector.render_surface(
            "data-quality",
            window_start="2026-09-01T00:00:00Z",
            window_end="2026-09-03T11:00:00Z",
        )
        context = self.context()
        context.update(
            _dataset="execution_context",
            window_start_utc="2026-09-01T00:00:00+00:00",
            window_end_utc="2026-09-03T11:00:00+00:00",
            window_semantics="HALF_OPEN_UTC",
            per_dataset_row_limit=5000,
            provider_latency_documented=False,
            settlement_policy_status="NOT_DECLARED",
        )
        history = self.row("expectation_history")
        history["_dataset"] = "expectation_history"
        receipt = collector.build_receipt(
            "data-quality",
            "private-profile",
            rendered,
            sources,
            raw=[{"EVIDENCE": context}, {"EVIDENCE": history}],
            template_sql=template,
            template_path=path,
            selector=selector,
            collection_mode="live-cli",
            collection_started_at="2026-09-03T11:59:00+00:00",
            collection_completed_at="2026-09-03T12:00:00+00:00",
        )
        with mock.patch.object(analyzer, "SQL_DIR", path.parent):
            self.assertEqual(analyzer.receipt_issues(receipt, self.EVALUATED), [])

    def test_cli_digest_modes_and_sanitized_failure(self):
        data = self.bundle()
        for option, expected in (("--print-input-sha256", analyzer.canonical_input_digest(data)),):
            completed = subprocess.run(
                [sys.executable, str(SCRIPT), option],
                input=json.dumps(data),
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual((completed.returncode, completed.stdout.strip()), (0, expected))
        policy_path = self.sql_dir / "policy.json"
        policy_path.write_text(json.dumps(data["policy"]), encoding="utf-8")
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--print-policy-sha256", "--policy-file", str(policy_path)],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.stdout.strip(), analyzer.canonical_policy_digest(data))
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--print-policy-sha256"],
            input=json.dumps(data),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(completed.stderr, "error: evidence input is invalid\n")
        data["RAW_SECRET_MARKER"] = "RAW_SECRET_MARKER"
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--evaluated-at",
                self.EVALUATED.isoformat(),
                "--trusted-input-sha256",
                "bad",
                "--trusted-policy-sha256",
                "bad",
            ],
            input=json.dumps(data),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(completed.stdout, "")
        self.assertEqual(completed.stderr, "error: evidence input is invalid\n")

    def test_cli_rejects_policy_file_that_differs_from_evidence_wrapper(self):
        data = self.bundle()
        owner_policy = copy.deepcopy(data["policy"])
        owner_policy["requirements"][0]["max_result_age_seconds"] += 1
        policy_path = self.sql_dir / "owner-policy.json"
        policy_path.write_text(json.dumps(owner_policy), encoding="utf-8")
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--evaluated-at",
                self.EVALUATED.isoformat(),
                "--trusted-input-sha256",
                analyzer.canonical_input_digest(data),
                "--trusted-policy-sha256",
                analyzer.digest(owner_policy),
                "--policy-file",
                str(policy_path),
            ],
            input=json.dumps(data),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(completed.stderr, "error: evidence input is invalid\n")


if __name__ == "__main__":
    unittest.main()
