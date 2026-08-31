from __future__ import annotations

import importlib.util
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


class QueryEvidenceTests(unittest.TestCase):
    def load_fixture(self, name: str) -> dict:
        return json.loads((FIXTURES / name).read_text(encoding="utf-8"))

    def test_separates_observations_ratios_and_hypotheses(self) -> None:
        result = MODULE.analyze(self.load_fixture("query_evidence.json"))
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


if __name__ == "__main__":
    unittest.main()
