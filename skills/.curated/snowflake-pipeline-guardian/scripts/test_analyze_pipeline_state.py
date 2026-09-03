#!/usr/bin/env python3
"""Stdlib fixture tests for analyze_pipeline_state.py."""

import hashlib
import json
import pathlib
import sys
import unittest
from datetime import datetime, timedelta, timezone

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import analyze_pipeline_state as analyzer  # noqa: E402


class PipelineAnalyzerTests(unittest.TestCase):
    def load(self, name):
        return json.loads((HERE / "fixtures" / name).read_text(encoding="utf-8"))

    def collector_receipt(self):
        sql_path = HERE / "sql" / "pipeline.sql"
        receipt = {
            "schema_version": "1",
            "surface": "pipeline",
            "status": "collected",
            "collected_at": "2026-08-30T12:00:00Z",
            "connection_profile": "readonly-observer",
            "sql_sha256": "sha256:" + hashlib.sha256(sql_path.read_bytes()).hexdigest(),
            "source_views": analyzer.EXPECTED_PIPELINE_SOURCES,
            "row_count": 1,
            "row_limit": 1000,
            "truncation_possible": False,
            "datasets": {"task_history": [{"name": "load_task", "state": "SUCCEEDED", "run_id": "run-a"}]},
            "errors": [],
        }
        receipt["receipt_sha256"] = "sha256:" + hashlib.sha256(analyzer._canonical_json(receipt)).hexdigest()
        return receipt

    @staticmethod
    def trusted_digest(data):
        return "sha256:" + hashlib.sha256(analyzer._canonical_json(data)).hexdigest()

    @staticmethod
    def evaluation_time():
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    def analyze_bundle(self, data, *, trusted=True, evaluated_at=None):
        return analyzer.analyze(
            data,
            trusted_input_sha256=self.trusted_digest(data) if trusted else None,
            evaluated_at=evaluated_at or self.evaluation_time(),
        )

    @staticmethod
    def projected_row(dataset_name, values):
        row = {field: None for field in analyzer.DATASET_FIELDS[dataset_name]}
        row.update(values)
        return row

    def schema2_history_receipt(self, *, collected_at=None, task_rows=None):
        collected = collected_at or datetime.now(timezone.utc).replace(microsecond=0) - timedelta(minutes=1)
        started = collected - timedelta(minutes=1)
        observed = collected - timedelta(seconds=30)
        window_start = observed - timedelta(days=7)
        window_end = observed - timedelta(days=2)
        selector = {
            "window_start": window_start.isoformat().replace("+00:00", "Z"),
            "window_end": window_end.isoformat().replace("+00:00", "Z"),
        }
        expected = sorted(
            [
                "execution_context",
                "task_history",
                "dynamic_table_refresh_history",
                "copy_history",
            ]
        )
        datasets = {
            "execution_context": [
                {
                    "observed_at": observed.isoformat(),
                    "organization_name_sha256": "0" * 64,
                    "account_identifier_sha256": "a" * 64,
                    "collector_user_sha256": "b" * 64,
                    "primary_role_sha256": "c" * 64,
                    "primary_role_type": "ROLE",
                    "secondary_roles_sha256": "d" * 64,
                    "timezone": "UTC",
                    "window_start_utc": window_start.isoformat(),
                    "window_end_utc": window_end.isoformat(),
                    "window_semantics": "HALF_OPEN_UTC",
                    "task_history_settled_through_utc": window_end.isoformat(),
                    "dynamic_table_refresh_history_settled_through_utc": window_end.isoformat(),
                    "copy_history_settled_through_utc": window_end.isoformat(),
                    "per_dataset_row_limit": 5000,
                }
            ],
            "task_history": task_rows
            if task_rows is not None
            else [
                {
                    "object_key_sha256": "1" * 64,
                    "run_id_sha256": "2" * 64,
                    "state": "SUCCEEDED",
                    "scheduled_time": (window_end - timedelta(hours=1, minutes=5)).isoformat(),
                    "completed_time": (window_end - timedelta(hours=1)).isoformat(),
                }
            ],
            "dynamic_table_refresh_history": [],
            "copy_history": [],
        }
        for row in datasets["task_history"]:
            row.pop("_dataset", None)
            row.setdefault("completed_time", (window_end - timedelta(hours=1)).isoformat())
        datasets["task_history"] = [self.projected_row("task_history", row) for row in datasets["task_history"]]
        sql_path = HERE / "sql" / "pipeline.sql"
        sql_sha256 = "sha256:" + hashlib.sha256(sql_path.read_bytes()).hexdigest()
        receipt = {
            "schema_version": "2",
            "surface": "pipeline",
            "status": "collected",
            "collected_at": collected.isoformat(),
            "collection_mode": "live-cli",
            "collection_started_at": started.isoformat(),
            "collection_completed_at": collected.isoformat(),
            "connection_profile_sha256": "sha256:" + "3" * 64,
            "sql_sha256": sql_sha256,
            "template_sha256": sql_sha256,
            "rendered_sql_sha256": "sha256:" + "5" * 64,
            "selector_fingerprint": "sha256:" + hashlib.sha256(analyzer._canonical_json(selector)).hexdigest(),
            "result_sha256": "sha256:" + hashlib.sha256(analyzer._canonical_json(datasets)).hexdigest(),
            "source_metadata": {
                "template": "pipeline.sql",
                "source_views": analyzer.EXPECTED_PIPELINE_SOURCES,
                "selector": {name: True for name in selector},
                "selector_values": selector,
            },
            "source_views": analyzer.EXPECTED_PIPELINE_SOURCES,
            "row_count": sum(len(rows) for rows in datasets.values()),
            "row_limit": 5000,
            "cap_scope": "per_dataset",
            "truncation_possible": False,
            "dataset_row_counts": {name: len(rows) for name, rows in datasets.items()},
            "expected_datasets": expected,
            "datasets": datasets,
            "errors": [],
            "non_claims": list(analyzer.RECEIPT_NON_CLAIMS),
            "snowflake_query_id": None,
            "snowflake_query_id_status": "not_exposed_by_snow_cli_json_ext",
        }
        rendered = sql_path.read_text(encoding="utf-8")
        rendered = rendered.replace("__WINDOW_START_UTC__", selector["window_start"])
        rendered = rendered.replace("__WINDOW_END_UTC__", selector["window_end"])
        receipt["rendered_sql_sha256"] = "sha256:" + hashlib.sha256(rendered.encode("utf-8")).hexdigest()
        receipt["receipt_sha256"] = "sha256:" + hashlib.sha256(analyzer._canonical_json(receipt)).hexdigest()
        return receipt

    def schema2_current_receipt(self, surface, dataset_name, rows, *, collected_at=None):
        collected = collected_at or datetime.now(timezone.utc).replace(microsecond=0) - timedelta(minutes=1)
        observed = collected - timedelta(seconds=30)
        context = {
            "observed_at": observed.isoformat(),
            "organization_name_sha256": "0" * 64,
            "account_identifier_sha256": "a" * 64,
            "collector_user_sha256": "b" * 64,
            "primary_role_sha256": "c" * 64,
            "primary_role_type": "ROLE",
            "secondary_roles_sha256": "d" * 64,
            "timezone": "UTC",
            "source_row_count": len(rows),
            "source_row_limit": analyzer.PIPELINE_RECEIPT_CONTRACTS[surface]["row_limit"],
            "truncation_possible": len(rows) >= analyzer.PIPELINE_RECEIPT_CONTRACTS[surface]["row_limit"],
        }
        if surface == "pipeline-pipe-status":
            for field in ("source_row_count", "source_row_limit", "truncation_possible"):
                context.pop(field)
        rows = [self.projected_row(dataset_name, row) for row in rows]
        datasets = {dataset_name: rows, "execution_context": [context]}
        contract = analyzer.PIPELINE_RECEIPT_CONTRACTS[surface]
        sql_path = HERE / "sql" / contract["template"]
        sql_sha256 = "sha256:" + hashlib.sha256(sql_path.read_bytes()).hexdigest()
        receipt = {
            "schema_version": "2",
            "surface": surface,
            "status": "collected",
            "collected_at": collected.isoformat(),
            "collection_mode": "live-cli",
            "collection_started_at": (collected - timedelta(minutes=1)).isoformat(),
            "collection_completed_at": collected.isoformat(),
            "connection_profile_sha256": "sha256:" + "3" * 64,
            "sql_sha256": sql_sha256,
            "template_sha256": sql_sha256,
            "rendered_sql_sha256": sql_sha256,
            "selector_fingerprint": None,
            "result_sha256": "sha256:" + hashlib.sha256(analyzer._canonical_json(datasets)).hexdigest(),
            "source_metadata": {
                "template": contract["template"],
                "source_views": contract["sources"],
                "selector": contract["selector"],
            },
            "source_views": contract["sources"],
            "row_count": sum(len(dataset) for dataset in datasets.values()),
            "row_limit": contract["row_limit"],
            "cap_scope": "single_dataset_or_result",
            "truncation_possible": False,
            "dataset_row_counts": {name: len(dataset) for name, dataset in datasets.items()},
            "expected_datasets": sorted(contract["datasets"]),
            "datasets": datasets,
            "errors": [],
            "non_claims": list(analyzer.RECEIPT_NON_CLAIMS),
            "snowflake_query_id": None,
            "snowflake_query_id_status": "not_exposed_by_snow_cli_json_ext",
        }
        if surface == "pipeline-pipe-status" and len(rows) == 1:
            binding = {"pipe_object_key_sha256": rows[0].get("object_key_sha256")}
            receipt["source_metadata"]["selector_binding"] = binding
            receipt["source_metadata"]["rendered_sql_contract"] = "privacy-bound-selector-v1"
            receipt["selector_fingerprint"] = "sha256:" + hashlib.sha256(analyzer._canonical_json(binding)).hexdigest()
            privacy_bound_sql = sql_path.read_text(encoding="utf-8").replace(
                "__PIPE_IDENTIFIER__", f"__PIPE_OBJECT_KEY_SHA256_{binding['pipe_object_key_sha256']}__"
            )
            receipt["rendered_sql_sha256"] = "sha256:" + hashlib.sha256(privacy_bound_sql.encode()).hexdigest()
        receipt["receipt_sha256"] = "sha256:" + hashlib.sha256(analyzer._canonical_json(receipt)).hexdigest()
        return receipt

    @staticmethod
    def rehash_receipt(receipt):
        body = dict(receipt)
        body.pop("receipt_sha256", None)
        receipt["receipt_sha256"] = "sha256:" + hashlib.sha256(analyzer._canonical_json(body)).hexdigest()

    def rehash_result(self, receipt):
        receipt["row_count"] = sum(len(rows) for rows in receipt["datasets"].values())
        receipt["dataset_row_counts"] = {name: len(rows) for name, rows in receipt["datasets"].items()}
        receipt["result_sha256"] = "sha256:" + hashlib.sha256(analyzer._canonical_json(receipt["datasets"])).hexdigest()
        self.rehash_receipt(receipt)

    def complete_receipts(self):
        return [
            self.schema2_history_receipt(),
            self.schema2_current_receipt("pipeline-task-current", "current_tasks", []),
            self.schema2_current_receipt("pipeline-stream-current", "current_streams", []),
            self.schema2_current_receipt("pipeline-dynamic-table-current", "current_dynamic_tables", []),
            self.schema2_current_receipt("pipeline-pipe-current", "current_pipes", []),
        ]

    def complete_receipts_with_pipe(self, *, execution_state="RUNNING"):
        pipe_key = "9" * 64
        receipts = self.complete_receipts()
        receipts[-1] = self.schema2_current_receipt(
            "pipeline-pipe-current", "current_pipes", [{"object_key_sha256": pipe_key, "kind": "STAGE"}]
        )
        receipts.append(
            self.schema2_current_receipt(
                "pipeline-pipe-status",
                "pipe_status",
                [{"object_key_sha256": pipe_key, "execution_state": execution_state}],
            )
        )
        return receipts

    def test_upstream_stale_stream_is_first_causal_finding(self):
        report = analyzer.analyze(self.load("stale-chain.json"))
        codes = [item["code"] for item in report["findings"]]
        self.assertIn("STREAM_STALE", codes)
        self.assertIn("TASK_FAILED", codes)
        self.assertIn("LAG_BREACH", codes)
        dt_chains = [item for item in report["causal_chains"] if item["endpoint"] == "orders_dt"]
        self.assertTrue(dt_chains)
        finding_nodes = [node["node_id"] for node in dt_chains[0]["nodes"] if node["findings"]]
        self.assertEqual(finding_nodes[0], "orders_stream")
        self.assertEqual(dt_chains[0]["nodes"][-1]["node_id"], "orders_dt")
        self.assertEqual(dt_chains[0]["classification"], "dependency_order_not_proven_causality")
        self.assertEqual(report["ordered_recovery"][0]["for"], "STREAM_STALE")
        self.assertTrue(any("idempotent backfill" in item["action"] for item in report["ordered_recovery"]))
        self.assertTrue(report["post_fix_invariants"])

    def test_pipe_schema_and_duplicates_are_distinct(self):
        report = analyzer.analyze(self.load("pipe-schema-duplicates.json"))
        codes = {item["code"] for item in report["findings"]}
        self.assertEqual(
            codes,
            {
                "PIPE_NOTIFICATION_GAP",
                "DUPLICATE_DELIVERY",
                "CHANGE_TRACKING_MISSING",
                "SCHEMA_DRIFT",
                "DYNAMIC_REFRESH_FAILED",
            },
        )
        self.assertEqual(report["node_count"], 3)
        self.assertEqual(report["edge_count"], 2)

    def test_missing_evidence_does_not_create_health_finding(self):
        report = analyzer.analyze({"nodes": [{"id": "raw", "kind": "TABLE"}], "edges": []})
        self.assertEqual(report["findings"], [])
        self.assertEqual(report["causal_chains"], [])
        self.assertEqual(report["edge_count"], 0)
        self.assertFalse(report["evidence_complete"])
        self.assertTrue(report["evidence_gaps"])

    def test_duplicate_ids_are_rejected(self):
        with self.assertRaises(ValueError):
            analyzer.analyze({"nodes": [{"id": "x"}, {"id": "x"}]})

    def test_negated_and_zero_value_status_text_does_not_false_positive(self):
        report = analyzer.analyze(
            {
                "observed_at": "2026-08-30T12:00:00Z",
                "evidence_source": "unit fixture",
                "nodes": [
                    {"id": "stream", "kind": "STREAM", "status": "NOT_STALE"},
                    {
                        "id": "pipe",
                        "kind": "PIPE",
                        "status": "OK",
                        "state_message": "notification received successfully",
                    },
                    {
                        "id": "dt",
                        "kind": "DYNAMIC_TABLE",
                        "status": "OK",
                        "change_tracking": True,
                        "state_message": "change tracking enabled",
                    },
                    {"id": "task", "kind": "TASK", "status": "OK", "state_message": "error count 0; not suspended"},
                ],
            }
        )
        self.assertEqual(report["findings"], [])

    def test_preserves_independent_branches_and_dangling_edges(self):
        report = analyzer.analyze(
            {
                "observed_at": "2026-08-30T12:00:00Z",
                "evidence_source": "unit fixture",
                "nodes": [
                    {"id": "a", "kind": "STREAM", "status": "STALE"},
                    {"id": "b", "kind": "TASK", "status": "FAILED"},
                    {"id": "c", "kind": "PIPE", "status": "FAILED"},
                ],
                "edges": [
                    {"from": "a", "to": "b"},
                    {"from": "missing", "to": "c"},
                ],
            }
        )
        endpoints = {item["endpoint"] for item in report["causal_chains"]}
        self.assertTrue({"a", "b", "c"} <= endpoints)
        self.assertFalse(report["graph_complete"])
        self.assertEqual(report["dangling_edges"][0]["from"], "missing")

    def test_disconnected_nodes_are_not_a_complete_graph(self):
        report = analyzer.analyze(
            {
                "observed_at": "2026-08-30T12:00:00Z",
                "evidence_source": "unit fixture",
                "nodes": [
                    {"id": "a", "kind": "TASK"},
                    {"id": "b", "kind": "PIPE"},
                ],
                "edges": [],
            }
        )
        self.assertFalse(report["graph_complete"])
        self.assertFalse(report["evidence_complete"])
        self.assertEqual(len(report["connected_components"]), 2)

    def test_redaction(self):
        report = analyzer.analyze(
            {
                "observed_at": "2026-08-30T12:00:00Z",
                "evidence_source": "https://collector/" + "?token=raw",
                "nodes": [
                    {
                        "id": "task",
                        "kind": "TASK",
                        "status": "FAILED",
                        "last_error": (
                            "token=abc123 jane@example.com https://example.test/x?sig=secret "
                            "SNOWFLAKE_PASSWORD=hunter2 CLIENT_SECRET=abc "
                            "AWS_SECRET_ACCESS_KEY=raw DATABASE_URL=" + "post" + "gres://u:p@h/db"
                        ),
                    }
                ],
            }
        )
        rendered = json.dumps(report)
        for secret in (
            "abc123",
            "jane@example.com",
            "example.test",
            "hunter2",
            "CLIENT_SECRET=abc",
            "AWS_SECRET_ACCESS_KEY=raw",
            "post" + "gres://u:p@h/db",
            "collector/?token=raw",
        ):
            self.assertNotIn(secret, rendered)

    def test_secret_bearing_fields_are_rejected(self):
        for field in ("AWS_ACCESS_KEY_ID", "SESSION_TOKEN", "api_key", "jwt"):
            with self.subTest(field=field), self.assertRaises(ValueError):
                analyzer.analyze({"nodes": [{"id": "x", field: "never"}]})

    def test_detects_skips_overlap_and_replay_holds(self):
        report = analyzer.analyze(
            {
                "observed_at": "2026-08-30T12:00:00Z",
                "evidence_source": "task history export",
                "nodes": [
                    {
                        "id": "load_task",
                        "kind": "TASK",
                        "status": "OK",
                        "idempotency_status": "UNKNOWN",
                        "replay_requested": True,
                        "replay_window": "2026-08-30T10:00:00Z/2026-08-30T11:00:00Z",
                        "run_history": [
                            {
                                "state": "SUCCEEDED",
                                "scheduled_time": "2026-08-30T10:00:00Z",
                                "completed_time": "2026-08-30T10:20:00Z",
                            },
                            {
                                "state": "SKIPPED",
                                "scheduled_time": "2026-08-30T10:10:00Z",
                                "completed_time": "2026-08-30T10:10:01Z",
                            },
                        ],
                    }
                ],
            }
        )
        codes = {item["code"] for item in report["findings"]}
        self.assertTrue({"TASK_SKIPPED", "TASK_OVERLAP", "IDEMPOTENCY_UNPROVEN", "REPLAY_RISK"} <= codes)

    def test_ingests_shared_collector_receipt_and_marks_graph_incomplete(self):
        receipt = self.schema2_history_receipt(
            task_rows=[
                {
                    "_dataset": "task_history",
                    "object_key_sha256": "1" * 64,
                    "run_id_sha256": "2" * 64,
                    "state": "SKIPPED",
                }
            ]
        )
        data = {"collector_receipt": receipt}
        report = self.analyze_bundle(data)
        self.assertEqual(report["collector_ingestion"]["status"], "insufficient_evidence")
        self.assertEqual(report["collector_ingestion"]["surfaces"], ["pipeline"])
        self.assertFalse(report["evidence_complete"])
        self.assertFalse(report["graph_complete"])
        self.assertIn("TASK_SKIPPED", {item["code"] for item in report["findings"]})

    def test_one_receipt_and_self_loop_cannot_support_complete_bounded_graph(self):
        data = {
            "observed_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "evidence_source": "shared Snowflake evidence collector",
            "nodes": [{"id": "task", "kind": "TASK", "status": "OK"}],
            "edges": [{"from": "task", "to": "task"}],
            "collector_receipt": self.schema2_history_receipt(),
        }
        with self.assertRaisesRegex(ValueError, "cannot include analyzer overlays"):
            self.analyze_bundle(data)

        receipt = self.schema2_history_receipt()
        receipt["sql_sha256"] = "sha256:" + "a" * 64
        self.rehash_receipt(receipt)
        data = {"collector_receipt": receipt}
        report = self.analyze_bundle(data)
        self.assertFalse(report["evidence_complete"])
        self.assertTrue(any("reviewed pipeline SQL" in gap for gap in report["evidence_gaps"]))

    def test_pipeline_receipt_missing_any_required_dataset_fails_closed(self):
        observed_at = datetime.now(timezone.utc).replace(microsecond=0)
        self.assertEqual(
            analyzer._collector_receipt_issues(self.schema2_history_receipt(), observed_at),
            [],
        )
        for missing in (
            "execution_context",
            "task_history",
            "dynamic_table_refresh_history",
            "copy_history",
        ):
            receipt = self.schema2_history_receipt()
            del receipt["datasets"][missing]
            receipt["dataset_row_counts"].pop(missing)
            receipt["row_count"] = sum(len(rows) for rows in receipt["datasets"].values())
            receipt["result_sha256"] = (
                "sha256:" + hashlib.sha256(analyzer._canonical_json(receipt["datasets"])).hexdigest()
            )
            self.rehash_receipt(receipt)
            issues = analyzer._collector_receipt_issues(receipt, observed_at)
            with self.subTest(missing=missing):
                self.assertTrue(
                    any("dataset" in issue.lower() for issue in issues),
                    issues,
                )

    def test_pipeline_receipt_older_than_current_state_horizon_fails_closed(self):
        evaluated_at = datetime.now(timezone.utc).replace(microsecond=0)
        fresh = self.schema2_history_receipt(collected_at=evaluated_at - timedelta(minutes=14))
        self.assertFalse(
            any("stale" in issue.lower() for issue in analyzer._collector_receipt_issues(fresh, evaluated_at))
        )
        receipt = self.schema2_history_receipt(collected_at=evaluated_at - timedelta(minutes=15, seconds=1))
        issues = analyzer._collector_receipt_issues(receipt, evaluated_at)
        self.assertTrue(any("stale" in issue.lower() for issue in issues), issues)

    def test_self_consistent_receipt_without_trusted_digest_is_untrusted(self):
        data = {"collector_receipt": self.schema2_history_receipt()}
        report = self.analyze_bundle(data, trusted=False)
        self.assertEqual(report["evidence_trust"]["status"], "UNTRUSTED")
        self.assertFalse(report["evidence_complete"])
        self.assertFalse(report["graph_complete"])

    def test_rehashed_receipt_tamper_does_not_defeat_trusted_bundle_digest(self):
        data = {"collector_receipt": self.schema2_history_receipt()}
        trusted = self.trusted_digest(data)
        data["collector_receipt"]["datasets"]["task_history"][0]["state"] = "FAILED"
        data["collector_receipt"]["result_sha256"] = (
            "sha256:" + hashlib.sha256(analyzer._canonical_json(data["collector_receipt"]["datasets"])).hexdigest()
        )
        self.rehash_receipt(data["collector_receipt"])
        report = analyzer.analyze(data, trusted_input_sha256=trusted, evaluated_at=self.evaluation_time())
        self.assertEqual(report["evidence_trust"]["status"], "DIGEST_MISMATCH")
        self.assertFalse(report["evidence_complete"])
        self.assertFalse(report["graph_complete"])

    def test_complete_schema2_surface_set_is_bounded_complete_but_not_a_proven_graph(self):
        receipts = self.complete_receipts()
        data = {"collector_receipts": receipts}
        report = self.analyze_bundle(data)
        self.assertTrue(report["evidence_complete"], report["evidence_gaps"])
        self.assertFalse(report["graph_complete"])
        self.assertEqual(report["evidence_trust"]["status"], "DIGEST_MATCHED_OPERATOR_ASSERTED")
        self.assertEqual(
            report["evidence_coverage"]["history"]["datasets"]["task_history"]["event_time_basis"],
            "completed_time",
        )
        self.assertTrue(all(item["scope"] == "current_role_visible" for item in report["evidence_coverage"]["current"]))

    def test_complete_receipts_reject_manual_node_overlay(self):
        data = {
            "collector_receipts": self.complete_receipts(),
            "nodes": [{"id": "fabricated", "kind": "TASK", "status": "SUSPENDED"}],
        }
        with self.assertRaisesRegex(ValueError, "cannot include analyzer overlays"):
            self.analyze_bundle(data)

    def test_malformed_or_ambiguous_receipt_collections_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "every collector receipt member"):
            self.analyze_bundle({"collector_receipts": [*self.complete_receipts(), "NOT_A_RECEIPT"]})
        with self.assertRaisesRegex(ValueError, "not both"):
            self.analyze_bundle(
                {
                    "collector_receipts": self.complete_receipts(),
                    "collector_receipt": self.schema2_history_receipt(),
                }
            )

    def test_missing_current_state_fields_fail_closed(self):
        cases = (
            (1, "pipeline-task-current", "current_tasks", "state"),
            (2, "pipeline-stream-current", "current_streams", "stale"),
            (3, "pipeline-dynamic-table-current", "current_dynamic_tables", "scheduling_state"),
            (4, "pipeline-pipe-current", "current_pipes", "kind"),
        )
        for receipt_index, surface, dataset, missing_field in cases:
            receipts = self.complete_receipts()
            receipts[receipt_index] = self.schema2_current_receipt(surface, dataset, [{"object_key_sha256": "1" * 64}])
            report = self.analyze_bundle({"collector_receipts": receipts})
            with self.subTest(surface=surface):
                self.assertFalse(report["evidence_complete"])
                self.assertTrue(
                    any(f"missing required evidence: {missing_field}" in gap for gap in report["evidence_gaps"])
                )

        pipe_key = "9" * 64
        receipts = self.complete_receipts()
        receipts[-1] = self.schema2_current_receipt(
            "pipeline-pipe-current", "current_pipes", [{"object_key_sha256": pipe_key, "kind": "STAGE"}]
        )
        receipts.append(
            self.schema2_current_receipt("pipeline-pipe-status", "pipe_status", [{"object_key_sha256": pipe_key}])
        )
        report = self.analyze_bundle({"collector_receipts": receipts})
        self.assertFalse(report["evidence_complete"])
        self.assertTrue(any("missing required evidence: execution_state" in gap for gap in report["evidence_gaps"]))

    def test_show_source_controls_and_sql_hashes_are_bound(self):
        for field, value in {
            "source_row_count": 1,
            "source_row_limit": 9999,
            "truncation_possible": True,
        }.items():
            receipts = self.complete_receipts()
            current = receipts[1]
            current["datasets"]["execution_context"][0][field] = value
            self.rehash_result(current)
            report = self.analyze_bundle({"collector_receipts": receipts})
            with self.subTest(control=field):
                self.assertFalse(report["evidence_complete"])
                self.assertTrue(any(field in gap for gap in report["evidence_gaps"]))

        receipts = self.complete_receipts()
        receipts[1]["rendered_sql_sha256"] = "sha256:" + "f" * 64
        self.rehash_receipt(receipts[1])
        report = self.analyze_bundle({"collector_receipts": receipts})
        self.assertFalse(report["evidence_complete"])
        self.assertTrue(any("unselected reviewed template" in gap for gap in report["evidence_gaps"]))

        receipts = self.complete_receipts()
        receipts[0]["selector_fingerprint"] = "sha256:" + "e" * 64
        self.rehash_receipt(receipts[0])
        report = self.analyze_bundle({"collector_receipts": receipts})
        self.assertFalse(report["evidence_complete"])
        self.assertTrue(any("selector_fingerprint" in gap for gap in report["evidence_gaps"]))

        receipts = self.complete_receipts()
        receipts[0]["rendered_sql_sha256"] = "sha256:" + "d" * 64
        self.rehash_receipt(receipts[0])
        report = self.analyze_bundle({"collector_receipts": receipts})
        self.assertFalse(report["evidence_complete"])
        self.assertTrue(any("bound reviewed SQL" in gap for gap in report["evidence_gaps"]))

        for mutation, expected_gap in (
            ("selector_binding", "selector binding"),
            ("selector_fingerprint", "selector_fingerprint"),
            ("rendered_sql_sha256", "privacy-bound selector projection"),
        ):
            receipts = self.complete_receipts_with_pipe()
            status = receipts[-1]
            if mutation == "selector_binding":
                status["source_metadata"][mutation] = {"pipe_object_key_sha256": "8" * 64}
            else:
                status[mutation] = "sha256:" + "f" * 64
            self.rehash_receipt(status)
            report = self.analyze_bundle({"collector_receipts": receipts})
            with self.subTest(pipe_binding=mutation):
                self.assertFalse(report["evidence_complete"])
                self.assertTrue(any(expected_gap in gap for gap in report["evidence_gaps"]))

    def test_evaluation_time_is_explicit_and_replay_deterministic(self):
        data = {"collector_receipts": self.complete_receipts()}
        trusted = self.trusted_digest(data)
        missing = analyzer.analyze(data, trusted_input_sha256=trusted)
        self.assertFalse(missing["evidence_complete"])
        evaluated_at = self.evaluation_time()
        first = analyzer.analyze(data, trusted_input_sha256=trusted, evaluated_at=evaluated_at)
        second = analyzer.analyze(data, trusted_input_sha256=trusted, evaluated_at=evaluated_at)
        self.assertEqual(first, second)

    def test_unsettled_window_and_out_of_window_events_fail_closed(self):
        receipt = self.schema2_history_receipt()
        context = receipt["datasets"]["execution_context"][0]
        observed = datetime.fromisoformat(context["observed_at"])
        start = observed - timedelta(minutes=20)
        end = observed
        context["window_start_utc"] = start.isoformat()
        context["window_end_utc"] = end.isoformat()
        for field, latency in (
            ("task_history_settled_through_utc", timedelta(minutes=45)),
            ("dynamic_table_refresh_history_settled_through_utc", timedelta(hours=3)),
            ("copy_history_settled_through_utc", timedelta(hours=48)),
        ):
            context[field] = (observed - latency).isoformat()
        receipt["datasets"]["task_history"] = []
        selector = {
            "window_start": start.isoformat().replace("+00:00", "Z"),
            "window_end": end.isoformat().replace("+00:00", "Z"),
        }
        receipt["source_metadata"]["selector_values"] = selector
        receipt["selector_fingerprint"] = "sha256:" + hashlib.sha256(analyzer._canonical_json(selector)).hexdigest()
        rendered = (HERE / "sql" / "pipeline.sql").read_text(encoding="utf-8")
        rendered = rendered.replace("__WINDOW_START_UTC__", selector["window_start"])
        rendered = rendered.replace("__WINDOW_END_UTC__", selector["window_end"])
        receipt["rendered_sql_sha256"] = "sha256:" + hashlib.sha256(rendered.encode()).hexdigest()
        self.rehash_result(receipt)
        report = self.analyze_bundle({"collector_receipt": receipt})
        self.assertFalse(report["evidence_complete"])
        self.assertTrue(any("no settled coverage" in gap for gap in report["evidence_gaps"]))
        self.assertEqual(
            report["evidence_coverage"]["history"]["datasets"]["copy_history"]["unsettled_tail"]["classification"],
            "unknown",
        )

        receipt = self.schema2_history_receipt()
        receipt["datasets"]["task_history"][0]["completed_time"] = receipt["datasets"]["execution_context"][0][
            "window_end_utc"
        ]
        self.rehash_result(receipt)
        report = self.analyze_bundle({"collector_receipt": receipt})
        self.assertFalse(report["evidence_complete"])
        self.assertTrue(any("falls outside settled coverage" in gap for gap in report["evidence_gaps"]))

        for dataset_name, time_field, values in (
            (
                "dynamic_table_refresh_history",
                "refresh_end_time",
                {"object_key_sha256": "4" * 64, "state": "FAILED"},
            ),
            (
                "copy_history",
                "last_load_time",
                {
                    "object_key_sha256": "7" * 64,
                    "file_identifier_sha256": "8" * 64,
                    "status": "Load failed",
                    "error_count": 1,
                },
            ),
        ):
            receipt = self.schema2_history_receipt()
            receipt["datasets"][dataset_name] = [
                self.projected_row(
                    dataset_name,
                    {
                        **values,
                        time_field: receipt["datasets"]["execution_context"][0]["window_end_utc"],
                    },
                )
            ]
            self.rehash_result(receipt)
            report = self.analyze_bundle({"collector_receipt": receipt})
            with self.subTest(history_dataset=dataset_name):
                self.assertFalse(report["evidence_complete"])
                self.assertTrue(
                    any(
                        f"{dataset_name}[0].{time_field} falls outside settled coverage" in gap
                        for gap in report["evidence_gaps"]
                    )
                )

    def test_copy_rows_use_pipe_identity_and_partial_loads_are_findings(self):
        receipt = self.schema2_history_receipt()
        event_time = receipt["datasets"]["task_history"][0]["completed_time"]
        pipe_key = "9" * 64
        receipt["datasets"]["copy_history"] = [
            self.projected_row(
                "copy_history",
                {
                    "object_key_sha256": "7" * 64,
                    "pipe_identifier_sha256": pipe_key,
                    "file_identifier_sha256": "8" * 64,
                    "last_load_time": event_time,
                    "status": "Partially loaded",
                    "error_count": 3,
                },
            ),
            self.projected_row(
                "copy_history",
                {
                    "object_key_sha256": "7" * 64,
                    "pipe_identifier_sha256": None,
                    "file_identifier_sha256": "6" * 64,
                    "last_load_time": event_time,
                    "status": "Load failed",
                    "error_count": 1,
                },
            ),
            self.projected_row(
                "copy_history",
                {
                    "object_key_sha256": "7" * 64,
                    "pipe_identifier_sha256": None,
                    "file_identifier_sha256": "5" * 64,
                    "last_load_time": event_time,
                    "status": "Partially loaded",
                    "error_count": 2,
                },
            ),
        ]
        self.rehash_result(receipt)
        report = self.analyze_bundle({"collector_receipt": receipt})
        partial = next(
            item for item in report["findings"] if item["code"] == "COPY_PARTIALLY_LOADED" and item["kind"] == "PIPE"
        )
        self.assertEqual(partial["kind"], "PIPE")
        self.assertTrue(partial["node_id"].startswith(pipe_key + "@"))
        self.assertEqual(partial["evidence_plane"], "settled_history")
        bulk_failure = next(item for item in report["findings"] if item["code"] == "COPY_LOAD_FAILURE")
        self.assertEqual(bulk_failure["kind"], "COPY_LOAD")
        bulk_partial = next(
            item
            for item in report["findings"]
            if item["code"] == "COPY_PARTIALLY_LOADED" and item["kind"] == "COPY_LOAD"
        )
        self.assertTrue(bulk_partial["node_id"].startswith("7" * 64 + "@"))

    def test_unreviewed_free_text_is_rejected_and_never_echoed(self):
        raw = "Customer AcmeCorp prod_db.finance.payments"
        cases = []

        receipts = self.complete_receipts()
        receipts[2] = self.schema2_current_receipt(
            "pipeline-stream-current",
            "current_streams",
            [{"object_key_sha256": "4" * 64, "stale": True, "stale_reason": raw}],
        )
        cases.append(receipts)

        receipts = self.complete_receipts()
        receipts[1] = self.schema2_current_receipt(
            "pipeline-task-current",
            "current_tasks",
            [{"object_key_sha256": "1" * 64, "state": raw}],
        )
        cases.append(receipts)

        receipts = self.complete_receipts()
        receipts[3] = self.schema2_current_receipt(
            "pipeline-dynamic-table-current",
            "current_dynamic_tables",
            [{"object_key_sha256": "4" * 64, "scheduling_state": "SUSPENDED", "state_message": raw}],
        )
        cases.append(receipts)

        cases.append(self.complete_receipts_with_pipe(execution_state=raw))

        receipts = self.complete_receipts()
        receipts[0]["non_claims"] = [raw]
        self.rehash_receipt(receipts[0])
        cases.append(receipts)

        for index, receipts in enumerate(cases):
            report = self.analyze_bundle({"collector_receipts": receipts})
            with self.subTest(injection=index):
                self.assertFalse(report["evidence_complete"])
                self.assertEqual(report["findings"], [])
                self.assertNotIn("AcmeCorp", json.dumps(report))

    def test_unreviewed_field_and_surface_names_are_never_echoed(self):
        raw = "Customer-AcmeCorp-Private-Name"

        receipts = self.complete_receipts()
        receipts[0][raw] = "value"
        self.rehash_receipt(receipts[0])
        report = self.analyze_bundle({"collector_receipts": receipts})
        self.assertFalse(report["evidence_complete"])
        self.assertEqual(report["findings"], [])
        self.assertNotIn(raw, json.dumps(report))

        receipts = self.complete_receipts()
        receipts[0]["datasets"][raw] = []
        self.rehash_result(receipts[0])
        report = self.analyze_bundle({"collector_receipts": receipts})
        self.assertFalse(report["evidence_complete"])
        self.assertEqual(report["findings"], [])
        self.assertNotIn(raw, json.dumps(report))

        receipts = self.complete_receipts()
        receipts[1] = self.schema2_current_receipt(
            "pipeline-task-current",
            "current_tasks",
            [{"object_key_sha256": "1" * 64, "state": "STARTED", raw: "value"}],
        )
        report = self.analyze_bundle({"collector_receipts": receipts})
        self.assertFalse(report["evidence_complete"])
        self.assertEqual(report["findings"], [])
        self.assertNotIn(raw, json.dumps(report))

        for task_rows in (
            [{"object_key_sha256": raw, "state": "STARTED"}],
            [
                {"object_key_sha256": raw, "state": "STARTED"},
                {"object_key_sha256": raw, "state": "STARTED"},
            ],
        ):
            receipts = self.complete_receipts()
            receipts[1] = self.schema2_current_receipt(
                "pipeline-task-current",
                "current_tasks",
                task_rows,
            )
            report = self.analyze_bundle({"collector_receipts": receipts})
            self.assertFalse(report["evidence_complete"])
            self.assertEqual(report["findings"], [])
            self.assertEqual(report["connected_components"], [["invalid-collector-evidence"]])
            self.assertNotIn(raw, json.dumps(report))

        receipts = self.complete_receipts()
        receipts[0] = self.schema2_history_receipt(
            task_rows=[
                {
                    "object_key_sha256": "1" * 64,
                    "run_id_sha256": raw,
                    "state": "SUCCEEDED",
                }
            ]
        )
        report = self.analyze_bundle({"collector_receipts": receipts})
        self.assertFalse(report["evidence_complete"])
        self.assertEqual(report["findings"], [])
        self.assertNotIn(raw, json.dumps(report))

        receipts = self.complete_receipts()
        receipts[0]["surface"] = raw
        self.rehash_receipt(receipts[0])
        report = self.analyze_bundle({"collector_receipts": receipts})
        self.assertFalse(report["evidence_complete"])
        self.assertEqual(report["findings"], [])
        self.assertNotIn(raw, json.dumps(report))

        with self.assertRaisesRegex(ValueError, "cannot include analyzer overlays") as raised:
            self.analyze_bundle({"collector_receipts": self.complete_receipts(), raw: []})
        self.assertNotIn(raw, str(raised.exception))

    def test_documented_terminal_task_and_dynamic_states_are_classified(self):
        receipts = self.complete_receipts()
        receipts[0] = self.schema2_history_receipt(
            task_rows=[
                {
                    "object_key_sha256": "1" * 64,
                    "run_id_sha256": "2" * 64,
                    "state": "FAILED_AND_AUTO_SUSPENDED",
                }
            ]
        )
        report = self.analyze_bundle({"collector_receipts": receipts})
        self.assertTrue(report["evidence_complete"], report["evidence_gaps"])
        self.assertIn("TASK_FAILED", {finding["code"] for finding in report["findings"]})

        for state, expected_code in (
            ("UPSTREAM_FAILED", "DYNAMIC_REFRESH_FAILED"),
            ("CANCELLED", "DYNAMIC_REFRESH_CANCELLED"),
        ):
            receipts = self.complete_receipts()
            history = self.schema2_history_receipt(task_rows=[])
            refresh_end = datetime.fromisoformat(
                history["datasets"]["execution_context"][0]["window_end_utc"]
            ) - timedelta(hours=1)
            history["datasets"]["dynamic_table_refresh_history"] = [
                self.projected_row(
                    "dynamic_table_refresh_history",
                    {
                        "object_key_sha256": "4" * 64,
                        "state": state,
                        "refresh_end_time": refresh_end.isoformat(),
                    },
                )
            ]
            self.rehash_result(history)
            receipts[0] = history
            report = self.analyze_bundle({"collector_receipts": receipts})
            with self.subTest(state=state):
                self.assertTrue(report["evidence_complete"], report["evidence_gaps"])
                self.assertIn(expected_code, {finding["code"] for finding in report["findings"]})

    def test_duplicate_current_pipe_identity_fails_closed_before_classification(self):
        pipe_key = "9" * 64
        receipts = self.complete_receipts_with_pipe()
        receipts[-2] = self.schema2_current_receipt(
            "pipeline-pipe-current",
            "current_pipes",
            [
                {"object_key_sha256": pipe_key, "kind": "STAGE"},
                {"object_key_sha256": pipe_key, "kind": "STAGE"},
            ],
        )
        report = self.analyze_bundle({"collector_receipts": receipts})
        self.assertFalse(report["evidence_complete"])
        self.assertTrue(any("duplicate natural keys" in gap for gap in report["evidence_gaps"]))
        self.assertEqual(report["findings"], [])

    def test_every_admitted_text_field_has_a_finite_reviewed_domain(self):
        for dataset_name, fields in analyzer.DATASET_FIELDS.items():
            text_fields = {
                field
                for field in fields
                if not field.endswith("_sha256")
                and field not in analyzer.TIMESTAMP_FIELDS
                and field not in analyzer.BOOLEAN_FIELDS
                and field not in analyzer.NUMBER_FIELDS
            }
            self.assertEqual(text_fields, set(analyzer.ENUM_FIELDS.get(dataset_name, {})))
            for field in text_fields:
                row = self.projected_row(dataset_name, {field: "Customer AcmeCorp prod_db.finance.payments"})
                issues = analyzer._dataset_row_issues("surface", dataset_name, row, 0)
                with self.subTest(dataset=dataset_name, field=field):
                    self.assertTrue(any(f".{field} is outside the reviewed" in issue for issue in issues))

    def test_current_and_history_incidents_remain_distinct_findings(self):
        history = self.schema2_history_receipt(
            task_rows=[
                {
                    "object_key_sha256": "1" * 64,
                    "run_id_sha256": "2" * 64,
                    "state": "SKIPPED",
                }
            ]
        )
        history["datasets"]["dynamic_table_refresh_history"] = [
            self.projected_row(
                "dynamic_table_refresh_history",
                {
                    "object_key_sha256": "4" * 64,
                    "query_id_sha256": "5" * 64,
                    "refresh_start_time": (
                        datetime.fromisoformat(history["datasets"]["task_history"][0]["completed_time"])
                        - timedelta(minutes=5)
                    ).isoformat(),
                    "refresh_end_time": history["datasets"]["task_history"][0]["completed_time"],
                    "state": "FAILED",
                },
            )
        ]
        history["row_count"] += 1
        history["dataset_row_counts"]["dynamic_table_refresh_history"] = 1
        history["result_sha256"] = "sha256:" + hashlib.sha256(analyzer._canonical_json(history["datasets"])).hexdigest()
        self.rehash_receipt(history)
        pipe_key = "9" * 64
        receipts = [
            history,
            self.schema2_current_receipt(
                "pipeline-task-current",
                "current_tasks",
                [{"object_key_sha256": "1" * 64, "state": "SUSPENDED"}],
            ),
            self.schema2_current_receipt(
                "pipeline-stream-current",
                "current_streams",
                [{"object_key_sha256": "3" * 64, "stale": True}],
            ),
            self.schema2_current_receipt(
                "pipeline-dynamic-table-current",
                "current_dynamic_tables",
                [{"object_key_sha256": "4" * 64, "scheduling_state": "SUSPENDED"}],
            ),
            self.schema2_current_receipt(
                "pipeline-pipe-current",
                "current_pipes",
                [{"object_key_sha256": pipe_key, "kind": "STAGE"}],
            ),
            self.schema2_current_receipt(
                "pipeline-pipe-status",
                "pipe_status",
                [{"object_key_sha256": pipe_key, "execution_state": "PAUSED"}],
            ),
        ]
        data = {"collector_receipts": receipts}
        report = self.analyze_bundle(data)
        codes = {finding["code"] for finding in report["findings"]}
        self.assertTrue(
            {
                "TASK_SKIPPED",
                "TASK_SUSPENDED",
                "STREAM_MAY_BE_STALE",
                "DYNAMIC_REFRESH_FAILED",
                "DYNAMIC_TABLE_SUSPENDED",
                "PIPE_NOT_RUNNING",
            }
            <= codes
        )
        self.assertTrue(report["evidence_complete"], report["evidence_gaps"])

    def test_raw_current_identity_and_pipe_payload_fields_fail_privacy_gate(self):
        task = self.schema2_current_receipt(
            "pipeline-task-current",
            "current_tasks",
            [{"object_key_sha256": "1" * 64, "state": "STARTED", "database_name": "RAW_DB"}],
        )
        status = self.schema2_current_receipt(
            "pipeline-pipe-status",
            "pipe_status",
            [{"object_key_sha256": "2" * 64, "execution_state": "RUNNING", "path": "secret/file.csv"}],
        )
        self.assertTrue(analyzer._receipt_privacy_issues(task))
        self.assertTrue(analyzer._receipt_privacy_issues(status))

    def test_cross_receipt_execution_context_mismatch_fails_closed(self):
        receipts = [
            self.schema2_history_receipt(),
            self.schema2_current_receipt("pipeline-task-current", "current_tasks", []),
            self.schema2_current_receipt("pipeline-stream-current", "current_streams", []),
            self.schema2_current_receipt("pipeline-dynamic-table-current", "current_dynamic_tables", []),
            self.schema2_current_receipt("pipeline-pipe-current", "current_pipes", []),
        ]
        receipts[2]["datasets"]["execution_context"][0]["primary_role_sha256"] = "e" * 64
        receipts[2]["result_sha256"] = (
            "sha256:" + hashlib.sha256(analyzer._canonical_json(receipts[2]["datasets"])).hexdigest()
        )
        self.rehash_receipt(receipts[2])
        data = {"collector_receipts": receipts}
        report = self.analyze_bundle(data)
        self.assertFalse(report["evidence_complete"])
        self.assertTrue(any("primary_role_sha256" in gap for gap in report["evidence_gaps"]))

    def test_collector_error_or_truncation_never_completes_and_is_sanitized(self):
        receipt = self.schema2_history_receipt()
        receipt["status"] = "error"
        receipt["errors"] = [{"message": "password=do-not-emit"}]
        receipt["row_limit"] = 1
        receipt["truncation_possible"] = True
        self.rehash_receipt(receipt)
        data = {"collector_receipt": receipt}
        report = self.analyze_bundle(data)
        self.assertFalse(report["graph_complete"])
        self.assertFalse(report["evidence_complete"])
        self.assertNotIn("do-not-emit", json.dumps(report))
        self.assertTrue(any("truncated" in gap for gap in report["evidence_gaps"]))
        self.assertTrue(any("status must be collected" in gap for gap in report["evidence_gaps"]))

    def test_collector_history_without_stable_identity_is_rejected(self):
        receipt = self.schema2_history_receipt(
            task_rows=[{"_dataset": "task_history", "object_key_sha256": "1" * 64, "state": "SUCCEEDED"}]
        )
        with self.assertRaisesRegex(ValueError, "lacks stable identity"):
            self.analyze_bundle({"collector_receipt": receipt})

    def test_collector_history_rows_for_one_object_get_unique_run_ids(self):
        object_key = "1" * 64
        run_a = "2" * 64
        run_b = "3" * 64
        receipt = self.schema2_history_receipt(
            task_rows=[
                {
                    "_dataset": "task_history",
                    "object_key_sha256": object_key,
                    "state": "SUCCEEDED",
                    "run_id_sha256": run_a,
                },
                {
                    "_dataset": "task_history",
                    "object_key_sha256": object_key,
                    "state": "FAILED",
                    "run_id_sha256": run_b,
                },
            ]
        )
        data = {"collector_receipt": receipt}
        report = self.analyze_bundle(data)
        self.assertEqual(report["node_count"], 2)
        self.assertEqual(
            {node_id for component in report["connected_components"] for node_id in component},
            {f"{object_key}@{run_a}", f"{object_key}@{run_b}"},
        )
        self.assertIn("TASK_FAILED", {item["code"] for item in report["findings"]})

    def test_collector_retries_with_same_run_id_use_attempt_identity(self):
        object_key = "1" * 64
        run_key = "2" * 64
        receipt = self.schema2_history_receipt(
            task_rows=[
                {
                    "_dataset": "task_history",
                    "object_key_sha256": object_key,
                    "state": "FAILED",
                    "run_id_sha256": run_key,
                    "attempt_number": 1,
                },
                {
                    "_dataset": "task_history",
                    "object_key_sha256": object_key,
                    "state": "SUCCEEDED",
                    "run_id_sha256": run_key,
                    "attempt_number": 2,
                },
            ]
        )
        data = {"collector_receipt": receipt}
        report = self.analyze_bundle(data)
        self.assertEqual(
            {node_id for component in report["connected_components"] for node_id in component},
            {f"{object_key}@{run_key}|1", f"{object_key}@{run_key}|2"},
        )


if __name__ == "__main__":
    unittest.main()
