#!/usr/bin/env python3
"""Stdlib fixture tests for analyze_pipeline_state.py."""

import json
import pathlib
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import analyze_pipeline_state as analyzer  # noqa: E402


class PipelineAnalyzerTests(unittest.TestCase):
    def load(self, name):
        return json.loads((HERE / "fixtures" / name).read_text(encoding="utf-8"))

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


if __name__ == "__main__":
    unittest.main()
