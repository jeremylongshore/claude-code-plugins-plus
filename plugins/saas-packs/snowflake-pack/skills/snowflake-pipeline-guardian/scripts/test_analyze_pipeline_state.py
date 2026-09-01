#!/usr/bin/env python3
"""Stdlib fixture tests for analyze_pipeline_state.py."""

import hashlib
import json
import pathlib
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import analyze_pipeline_state as analyzer  # noqa: E402
import collect_snowflake_evidence as collector  # noqa: E402


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

    def current_state_receipt(self):
        path, template_sql, rendered_sql, sources, selector = collector.render_surface("pipeline-current")
        raw = [
            {
                "EVIDENCE": {
                    "_dataset": "task_current",
                    "database_name": "DB",
                    "schema_name": "PUBLIC",
                    "name": "LOAD_TASK",
                    "id": "101",
                    "state": "STARTED",
                    "predecessors": [],
                    "schedule": "USING CRON 0 * * * * UTC",
                    "last_committed_on": "2026-08-30T12:00:00Z",
                }
            },
            {
                "EVIDENCE": {
                    "_dataset": "stream_current",
                    "database_name": "DB",
                    "schema_name": "PUBLIC",
                    "name": "ORDERS_STREAM",
                    "table_name": "ORDERS",
                    "stale": False,
                    "stale_after": "2026-09-01T12:00:00Z",
                    "invalid": False,
                }
            },
            {
                "EVIDENCE": {
                    "_dataset": "dynamic_table_current",
                    "database_name": "DB",
                    "schema_name": "PUBLIC",
                    "name": "ORDERS_DT",
                    "scheduling_state": "RUNNING",
                    "target_lag": "5 minutes",
                    "refresh_mode": "INCREMENTAL",
                    "warehouse": "PIPELINE_WH",
                }
            },
            {
                "EVIDENCE": {
                    "_dataset": "pipe_current",
                    "database_name": "DB",
                    "schema_name": "PUBLIC",
                    "name": "ORDERS_PIPE",
                    "type": "AUTO_INGEST",
                    "invalid_reason": None,
                    "last_ingested_timestamp": "2026-08-30T11:59:00Z",
                }
            },
        ]
        return collector.build_receipt(
            "pipeline-current",
            "readonly-observer",
            rendered_sql,
            sources,
            raw=raw,
            collected_at="2026-08-30T12:00:00Z",
            template_sql=template_sql,
            template_path=path,
            selector=selector,
        )

    def current_state_snapshot(self):
        nodes = [
            {"id": "DB.PUBLIC.LOAD_TASK", "kind": "TASK", "status": "STARTED"},
            {"id": "DB.PUBLIC.ORDERS_STREAM", "kind": "STREAM", "status": "OK"},
            {"id": "DB.PUBLIC.ORDERS_DT", "kind": "DYNAMIC_TABLE", "status": "RUNNING"},
            {"id": "DB.PUBLIC.ORDERS_PIPE", "kind": "PIPE", "status": "OK"},
        ]
        return {
            "observed_at": "2026-08-30T12:05:00Z",
            "evidence_source": "pipeline-current receipt fixture",
            "nodes": nodes,
            "edges": [
                {"from": "DB.PUBLIC.ORDERS_STREAM", "to": "DB.PUBLIC.LOAD_TASK"},
                {"from": "DB.PUBLIC.LOAD_TASK", "to": "DB.PUBLIC.ORDERS_DT"},
                {"from": "DB.PUBLIC.ORDERS_DT", "to": "DB.PUBLIC.ORDERS_PIPE"},
            ],
            "current_state": {
                "status": "collected",
                "observed_at": "2026-08-30T12:00:00Z",
                "max_age_minutes": 15,
                "complete": True,
                "nodes": nodes,
            },
            "current_state_receipt": self.current_state_receipt(),
        }

    @staticmethod
    def rehash(receipt):
        unsigned = dict(receipt)
        unsigned.pop("receipt_sha256", None)
        receipt["receipt_sha256"] = "sha256:" + hashlib.sha256(analyzer._canonical_json(unsigned)).hexdigest()

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
        report = analyzer.analyze(
            {
                "collector_receipt": {
                    "collected_at": "2026-08-30T12:00:00Z",
                    "status": "collected",
                    "row_count": 1,
                    "datasets": {"task_history": [{"name": "load_task", "state": "SKIPPED", "run_id": "run-skipped"}]},
                }
            }
        )
        self.assertEqual(report["collector_ingestion"]["status"], "collected")
        self.assertIn("task_history", report["collector_ingestion"]["datasets"])
        self.assertFalse(report["graph_complete"])
        self.assertIn("TASK_SKIPPED", {item["code"] for item in report["findings"]})

    def test_collector_adapter_preserves_current_state_envelope(self):
        report = analyzer.analyze(
            {
                "collector_receipt": self.collector_receipt(),
                "current_state": {
                    "status": "collected",
                    "observed_at": "2026-08-30T11:58:00Z",
                    "max_age_minutes": 15,
                    "complete": True,
                    "nodes": [{"id": "load_task", "kind": "TASK", "status": "SUCCEEDED"}],
                    "edges": [],
                },
            }
        )
        self.assertEqual(report["state_reconciliation"]["current_nodes"], 1)
        self.assertNotIn("current_state must be an object", report["evidence_gaps"])

    def test_verified_receipt_can_support_complete_bounded_graph(self):
        report = analyzer.analyze(
            {
                "collector_receipt": self.collector_receipt(),
                "edges": [{"from": "load_task@run-a", "to": "load_task@run-a"}],
            }
        )
        self.assertTrue(report["evidence_complete"])
        self.assertTrue(report["graph_complete"])

        receipt = self.collector_receipt()
        receipt["sql_sha256"] = "sha256:" + "a" * 64
        unsigned = dict(receipt)
        unsigned.pop("receipt_sha256")
        receipt["receipt_sha256"] = "sha256:" + hashlib.sha256(analyzer._canonical_json(unsigned)).hexdigest()
        report = analyzer.analyze(
            {
                "collector_receipt": receipt,
                "edges": [{"from": "load_task@run-a", "to": "load_task@run-a"}],
            }
        )
        self.assertFalse(report["evidence_complete"])
        self.assertTrue(any("reviewed pipeline SQL" in gap for gap in report["evidence_gaps"]))

    def test_collector_error_or_truncation_never_completes_and_is_sanitized(self):
        report = analyzer.analyze(
            {
                "observed_at": "2026-08-30T12:00:00Z",
                "evidence_source": "collector",
                "nodes": [{"id": "stream", "kind": "STREAM", "status": "OK"}],
                "edges": [{"from": "stream", "to": "stream"}],
                "collector_receipt": {
                    "schema_version": "1",
                    "surface": "pipeline",
                    "status": "error",
                    "collected_at": "2026-08-30T12:00:00Z",
                    "connection_profile": "readonly-observer",
                    "sql_sha256": "sha256:" + "a" * 64,
                    "source_views": ["SNOWFLAKE.ACCOUNT_USAGE.TASK_HISTORY"],
                    "row_count": 1000,
                    "row_limit": 1000,
                    "truncation_possible": True,
                    "datasets": {"task_history": []},
                    "errors": [{"message": "password=do-not-emit"}],
                    "receipt_sha256": "sha256:" + "b" * 64,
                },
            }
        )
        self.assertFalse(report["graph_complete"])
        self.assertFalse(report["evidence_complete"])
        self.assertNotIn("do-not-emit", json.dumps(report))
        self.assertTrue(any("truncated" in gap for gap in report["evidence_gaps"]))
        self.assertTrue(any("status is error" in gap for gap in report["evidence_gaps"]))

    def test_collector_history_without_stable_identity_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "lacks stable identity"):
            analyzer.analyze(
                {
                    "collector_receipt": {
                        "collected_at": "2026-08-30T12:00:00Z",
                        "status": "collected",
                        "row_count": 1,
                        "datasets": {"task_history": [{"name": "load_task", "state": "SUCCEEDED"}]},
                    }
                }
            )

    def test_collector_history_rows_for_one_object_get_unique_run_ids(self):
        report = analyzer.analyze(
            {
                "collector_receipt": {
                    "collected_at": "2026-08-30T12:00:00Z",
                    "status": "collected",
                    "row_count": 2,
                    "datasets": {
                        "task_history": [
                            {"name": "load_task", "state": "SUCCEEDED", "run_id": "run-a"},
                            {"name": "load_task", "state": "FAILED", "run_id": "run-b"},
                        ]
                    },
                }
            }
        )
        self.assertEqual(report["node_count"], 2)
        self.assertEqual(
            {node_id for component in report["connected_components"] for node_id in component},
            {"load_task@run-a", "load_task@run-b"},
        )
        self.assertIn("TASK_FAILED", {item["code"] for item in report["findings"]})

    def test_collector_retries_with_same_run_id_use_attempt_identity(self):
        report = analyzer.analyze(
            {
                "collector_receipt": {
                    "collected_at": "2026-08-30T12:00:00Z",
                    "status": "collected",
                    "row_count": 2,
                    "datasets": {
                        "task_history": [
                            {"name": "load_task", "state": "FAILED", "run_id": "run-a", "attempt_number": 1},
                            {"name": "load_task", "state": "SUCCEEDED", "run_id": "run-a", "attempt_number": 2},
                        ]
                    },
                }
            }
        )
        self.assertEqual(
            {node_id for component in report["connected_components"] for node_id in component},
            {"load_task@run-a|1", "load_task@run-a|2"},
        )

    def test_current_state_is_fresh_and_reconciled_to_history(self):
        report = analyzer.analyze(self.load("current-state-drift.json"))
        self.assertEqual(report["state_reconciliation"]["current_nodes"], 2)
        self.assertEqual(report["state_reconciliation"]["history_nodes"], 2)
        self.assertEqual(report["state_reconciliation"]["drift"][0]["id"], "load_task")
        self.assertIn("CURRENT_HISTORY_STATE_DRIFT", {item["code"] for item in report["findings"]})
        self.assertIn("current state and history disagree", " ".join(report["evidence_gaps"]))

    def test_stale_or_incomplete_current_state_blocks_completeness(self):
        data = self.load("current-state-drift.json")
        data["current_state"]["observed_at"] = "2026-08-29T12:00:00Z"
        data["current_state"]["complete"] = False
        report = analyzer.analyze(data)
        self.assertFalse(report["evidence_complete"])
        self.assertTrue(any("current_state" in gap for gap in report["evidence_gaps"]))

    def test_pipeline_current_receipt_verifies_and_binds_all_nodes(self):
        report = analyzer.analyze(self.current_state_snapshot())
        assessment = report["current_state_receipt_assessment"]
        self.assertEqual(assessment["status"], "verified")
        self.assertEqual(
            assessment["binding"],
            {"receipt_nodes": 4, "current_nodes": 4, "matched_nodes": 4},
        )
        self.assertTrue(report["evidence_complete"])
        self.assertTrue(report["graph_complete"])

    def test_pipeline_current_receipt_tamper_is_rejected(self):
        data = self.current_state_snapshot()
        data["current_state_receipt"]["datasets"]["task_current"][0]["state"] = "SUSPENDED"
        report = analyzer.analyze(data)
        self.assertFalse(report["evidence_complete"])
        self.assertTrue(
            any(
                "receipt_sha256 does not match" in issue
                for issue in report["current_state_receipt_assessment"]["issues"]
            )
        )

    def test_pipeline_current_receipt_rejects_rehashed_provenance_mismatch(self):
        for variant in ("schema", "surface", "status", "errors", "sources", "template", "sql_hash"):
            with self.subTest(variant=variant):
                data = self.current_state_snapshot()
                receipt = data["current_state_receipt"]
                if variant == "schema":
                    receipt["schema_version"] = "2"
                elif variant == "surface":
                    receipt["surface"] = "pipeline"
                elif variant == "status":
                    receipt["status"] = "error"
                elif variant == "errors":
                    receipt["errors"] = [{"message": "permission denied"}]
                elif variant == "sources":
                    receipt["source_views"] = ["SHOW TASKS"]
                elif variant == "template":
                    receipt["source_metadata"]["template"] = "foreign.sql"
                else:
                    receipt["sql_sha256"] = "sha256:" + "0" * 64
                    receipt["template_sha256"] = "sha256:" + "0" * 64
                    receipt["rendered_sql_sha256"] = "sha256:" + "0" * 64
                self.rehash(receipt)
                report = analyzer.analyze(data)
                self.assertFalse(report["evidence_complete"])
                self.assertFalse(report["graph_complete"])
                self.assertTrue(report["current_state_receipt_assessment"]["issues"])

    def test_pipeline_current_receipt_stale_truncated_or_missing_fails_closed(self):
        for variant in ("stale", "truncated", "missing"):
            with self.subTest(variant=variant):
                data = self.current_state_snapshot()
                if variant == "stale":
                    data["observed_at"] = "2026-08-30T12:30:01Z"
                elif variant == "truncated":
                    data["current_state_receipt"]["truncation_possible"] = True
                    data["current_state_receipt"]["dataset_truncation_possible"]["task_current"] = True
                    self.rehash(data["current_state_receipt"])
                else:
                    del data["current_state_receipt"]
                report = analyzer.analyze(data)
                self.assertFalse(report["evidence_complete"])
                self.assertFalse(report["graph_complete"])
                self.assertNotEqual(report["current_state_receipt_assessment"]["status"], "verified")

    def test_pipeline_current_receipt_rejects_dataset_and_projection_drift(self):
        for variant in ("dataset", "raw_definition", "row_count", "cap"):
            with self.subTest(variant=variant):
                data = self.current_state_snapshot()
                receipt = data["current_state_receipt"]
                if variant == "dataset":
                    receipt["datasets"]["foreign_current"] = []
                    receipt["dataset_truncation_possible"]["foreign_current"] = False
                elif variant == "raw_definition":
                    receipt["datasets"]["pipe_current"][0]["definition"] = "COPY INTO private_target"
                elif variant == "row_count":
                    receipt["row_count"] = 3
                else:
                    receipt["row_count"] = analyzer.MAX_CURRENT_RECEIPT_ROWS
                self.rehash(receipt)
                report = analyzer.analyze(data)
                self.assertFalse(report["evidence_complete"])
                self.assertTrue(report["current_state_receipt_assessment"]["issues"])
                self.assertNotIn("COPY INTO private_target", json.dumps(report))

    def test_pipeline_current_payload_status_and_id_mismatches_fail_closed(self):
        for variant in ("status", "id"):
            with self.subTest(variant=variant):
                data = self.current_state_snapshot()
                if variant == "status":
                    data["current_state"]["nodes"][0]["status"] = "SUSPENDED"
                else:
                    data["current_state"]["nodes"][0]["id"] = "DB.PUBLIC.WRONG_TASK"
                report = analyzer.analyze(data)
                self.assertFalse(report["evidence_complete"])
                self.assertFalse(report["graph_complete"])
                self.assertTrue(
                    any(
                        variant in issue or "identify" in issue
                        for issue in report["current_state_receipt_assessment"]["issues"]
                    )
                )


if __name__ == "__main__":
    unittest.main()
