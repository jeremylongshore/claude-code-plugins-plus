"""Unit tests for freshie/scripts/run-delta.py (run-tag parsing,
previous-tag selection, DOLT_DIFF_SUMMARY/DOLT_DIFF_STAT row merging,
grade-regression detection, report assembly, and the summary line).

Run: python3 -m unittest tests.test_run_delta -v

Coverage honesty: no Dolt binary, network, or repository state. Immutable-tag
snapshot builders are tested with mocked Dolt query rows; the subprocess query
wrapper and emit()'s filesystem writes remain covered by the end-to-end sync
against a real Dolt repo.
"""

import importlib.util
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "freshie" / "scripts" / "run-delta.py"
spec = importlib.util.spec_from_file_location("run_delta", SCRIPT)
run_delta = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run_delta)


class ParseRunTagTests(unittest.TestCase):
    def test_base_tag(self):
        self.assertEqual(run_delta.parse_run_tag("run-9"), (9, 0))

    def test_suffixed_tag(self):
        self.assertEqual(run_delta.parse_run_tag("run-9.1"), (9, 1))

    def test_suffix_sorts_after_base(self):
        self.assertGreater(run_delta.parse_run_tag("run-9.1"), run_delta.parse_run_tag("run-9"))
        self.assertLess(run_delta.parse_run_tag("run-9.1"), run_delta.parse_run_tag("run-10"))

    def test_non_run_tags_rejected(self):
        for bad in ("run-", "run-x", "v1.0", "release-9", "run-9.1.2", ""):
            self.assertIsNone(run_delta.parse_run_tag(bad), bad)


class PickPreviousTagTests(unittest.TestCase):
    TAGS = ["run-7", "run-8", "run-9", "run-9.1", "v1.0"]

    def test_previous_of_base(self):
        self.assertEqual(run_delta.pick_previous_tag(self.TAGS, "run-9"), "run-8")

    def test_previous_of_suffixed_is_its_base(self):
        # run-9.1 diffs against run-9 — the suffix means "run 9's data moved
        # again", so the meaningful delta is against the prior run-9 state.
        self.assertEqual(run_delta.pick_previous_tag(self.TAGS, "run-9.1"), "run-9")

    def test_next_run_diffs_against_highest_suffix(self):
        self.assertEqual(run_delta.pick_previous_tag(self.TAGS + ["run-10"], "run-10"), "run-9.1")

    def test_earliest_run_has_no_previous(self):
        self.assertIsNone(run_delta.pick_previous_tag(self.TAGS, "run-7"))

    def test_non_run_current_tag(self):
        self.assertIsNone(run_delta.pick_previous_tag(self.TAGS, "v1.0"))

    def test_ignores_non_run_tags(self):
        self.assertEqual(run_delta.pick_previous_tag(["v1.0", "run-3", "run-5"], "run-5"), "run-3")


class MergeDiffRowsTests(unittest.TestCase):
    def test_merges_summary_flags_with_stat_counts(self):
        summary = [
            {
                "from_table_name": "skills",
                "to_table_name": "skills",
                "diff_type": "modified",
                "data_change": "true",
                "schema_change": "false",
            },
            {
                "from_table_name": "skill_compliance",
                "to_table_name": "skill_compliance",
                "diff_type": "modified",
                "data_change": "true",
                "schema_change": "true",
            },
        ]
        stat = [
            {"table_name": "skills", "rows_added": "12", "rows_deleted": "3", "rows_modified": "0"},
            {"table_name": "skill_compliance", "rows_added": "3783", "rows_deleted": "0", "rows_modified": "0"},
        ]
        merged = run_delta.merge_diff_rows(summary, stat)
        self.assertEqual(len(merged), 2)
        by_table = {m["table"]: m for m in merged}
        self.assertEqual(by_table["skills"]["rows_added"], 12)
        self.assertEqual(by_table["skills"]["rows_deleted"], 3)
        self.assertFalse(by_table["skills"]["schema_change"])
        self.assertTrue(by_table["skill_compliance"]["schema_change"])
        self.assertEqual(by_table["skill_compliance"]["rows_added"], 3783)

    def test_pure_schema_change_has_zero_counts(self):
        summary = [{"to_table_name": "docs", "diff_type": "modified", "data_change": "false", "schema_change": "true"}]
        merged = run_delta.merge_diff_rows(summary, [])
        self.assertEqual(merged[0]["rows_added"], 0)
        self.assertEqual(merged[0]["rows_modified"], 0)
        self.assertTrue(merged[0]["schema_change"])

    def test_dropped_table_uses_from_name(self):
        # A dropped table has an empty to_table_name in newer Dolt builds.
        summary = [
            {
                "from_table_name": "old_table",
                "to_table_name": "",
                "diff_type": "dropped",
                "data_change": "true",
                "schema_change": "true",
            }
        ]
        merged = run_delta.merge_diff_rows(summary, [])
        self.assertEqual(merged[0]["table"], "old_table")

    def test_legacy_table_name_column(self):
        summary = [{"table_name": "skills", "diff_type": "modified", "data_change": "1", "schema_change": "0"}]
        merged = run_delta.merge_diff_rows(summary, [])
        self.assertEqual(merged[0]["table"], "skills")
        self.assertTrue(merged[0]["data_change"])
        self.assertFalse(merged[0]["schema_change"])

    def test_output_sorted_by_table(self):
        summary = [
            {"table_name": t, "diff_type": "modified", "data_change": "true", "schema_change": "false"}
            for t in ("zeta", "alpha", "mid")
        ]
        merged = run_delta.merge_diff_rows(summary, [])
        self.assertEqual([m["table"] for m in merged], ["alpha", "mid", "zeta"])


class DetectGradeRegressionsTests(unittest.TestCase):
    def test_drop_detected(self):
        out = run_delta.detect_grade_regressions({"s1": "A"}, {"s1": "B"})
        self.assertEqual(out, [{"skill_path": "s1", "from_grade": "A", "to_grade": "B"}])

    def test_multi_step_drop_detected(self):
        out = run_delta.detect_grade_regressions({"s1": "B"}, {"s1": "F"})
        self.assertEqual(out[0]["to_grade"], "F")

    def test_improvement_is_not_a_regression(self):
        self.assertEqual(run_delta.detect_grade_regressions({"s1": "C"}, {"s1": "A"}), [])

    def test_unchanged_is_not_a_regression(self):
        self.assertEqual(run_delta.detect_grade_regressions({"s1": "B"}, {"s1": "B"}), [])

    def test_added_and_removed_skills_ignored(self):
        # Membership changes are not grade movement.
        self.assertEqual(run_delta.detect_grade_regressions({"gone": "A"}, {"new": "F"}), [])

    def test_unrankable_grades_skipped(self):
        self.assertEqual(
            run_delta.detect_grade_regressions({"s1": "A", "s2": ""}, {"s1": "ungraded", "s2": "F"}),
            [],
        )

    def test_sorted_by_skill_path(self):
        out = run_delta.detect_grade_regressions({"z": "A", "a": "A", "m": "B"}, {"z": "B", "a": "C", "m": "D"})
        self.assertEqual([r["skill_path"] for r in out], ["a", "m", "z"])


class BuildReportTests(unittest.TestCase):
    def _tables(self):
        return [
            {
                "table": "skills",
                "diff_type": "modified",
                "schema_change": False,
                "data_change": True,
                "rows_added": 10,
                "rows_deleted": 2,
                "rows_modified": 1,
            },
            {
                "table": "docs",
                "diff_type": "modified",
                "schema_change": True,
                "data_change": False,
                "rows_added": 0,
                "rows_deleted": 0,
                "rows_modified": 0,
            },
        ]

    def test_shape_and_totals(self):
        regressions = [{"skill_path": "s1", "from_grade": "A", "to_grade": "B"}]
        coherence = {
            "discovery_run_id": 9,
            "header_total_skills": 2,
            "skill_rows": 2,
            "skill_row_delta": 0,
            "skill_compliance_rows": 2,
        }
        grade_export = {
            "row_count": 2,
            "csv_sha256": "a" * 64,
            "grade_counts": {"A": 1, "B": 1},
        }
        forge_proofs = {
            "row_count": 3,
            "records_sha256": "b" * 64,
            "class_counts": {"E0": 3, "E1": 0, "E2": 0, "E3": 0},
            "retained_e2_e3": 0,
            "total_e2_e3": 0,
            "records": [],
        }
        report = run_delta.build_report(
            9,
            "run-8",
            "run-9",
            "abc123",
            self._tables(),
            regressions,
            coherence,
            grade_export,
            forge_proofs,
        )
        self.assertEqual(report["schema_version"], "freshie-run-delta/v3")
        self.assertEqual(report["run_id"], 9)
        self.assertEqual(report["dolt_commit"], "abc123")
        self.assertEqual(report["run_coherence"], coherence)
        self.assertEqual(report["grade_export"], grade_export)
        self.assertEqual(report["forge_proofs"], forge_proofs)
        self.assertEqual(report["tables_changed"], 2)
        self.assertEqual(report["schema_changes"], ["docs"])
        self.assertEqual(report["rows_added"], 10)
        self.assertEqual(report["rows_deleted"], 2)
        self.assertEqual(report["rows_modified"], 1)
        self.assertEqual(report["grade_regressions"], regressions)
        # The report must survive a JSON round-trip (it is written to disk).
        self.assertEqual(json.loads(json.dumps(report)), report)

    def test_first_run_report(self):
        report = run_delta.build_report(1, None, "run-1", "abc", [], [])
        self.assertIsNone(report["from_tag"])
        self.assertIsNone(report["run_coherence"])
        self.assertIsNone(report["grade_export"])
        self.assertIsNone(report["forge_proofs"])
        self.assertEqual(report["tables_changed"], 0)
        self.assertEqual(report["grade_regressions"], [])


class RequiredCountTests(unittest.TestCase):
    def test_accepts_zero_and_decimal_strings(self):
        self.assertEqual(run_delta._required_count("0", "rows"), 0)
        self.assertEqual(run_delta._required_count("42", "rows"), 42)

    def test_rejects_missing_non_integer_and_negative_values(self):
        for value in (None, "", "1.5", "many"):
            with self.subTest(value=value):
                with self.assertRaisesRegex(run_delta.DeltaError, "is not an integer"):
                    run_delta._required_count(value, "rows")
        with self.assertRaisesRegex(run_delta.DeltaError, "rows is negative: -1"):
            run_delta._required_count("-1", "rows")


class RunCoherenceAtTagTests(unittest.TestCase):
    def test_reads_all_counts_from_the_same_tag(self):
        responses = [
            [{"total_skills": "2"}],
            [{"row_count": "2"}],
            [{"row_count": "3"}],
        ]
        with patch.object(run_delta, "dolt_query_dicts", side_effect=responses) as query:
            result = run_delta.run_coherence_at_tag(Path("/tmp/freshie"), "run-9.1", 9)

        self.assertEqual(
            result,
            {
                "discovery_run_id": 9,
                "header_total_skills": 2,
                "skill_rows": 2,
                "skill_row_delta": 0,
                "skill_compliance_rows": 3,
            },
        )
        self.assertEqual(query.call_count, 3)
        for call in query.call_args_list:
            self.assertIn("AS OF 'run-9.1'", call.args[1])

    def test_requires_exactly_one_discovery_header(self):
        for headers in ([], [{"total_skills": "1"}, {"total_skills": "1"}]):
            with self.subTest(headers=headers):
                with patch.object(run_delta, "dolt_query_dicts", return_value=headers):
                    with self.assertRaisesRegex(
                        run_delta.DeltaError,
                        rf"run 9 has {len(headers)} discovery_runs headers",
                    ):
                        run_delta.run_coherence_at_tag(Path("/tmp/freshie"), "run-9", 9)

    def test_requires_single_count_rows_and_valid_counts(self):
        with patch.object(
            run_delta,
            "dolt_query_dicts",
            side_effect=[[{"total_skills": "2"}], [], [{"row_count": "2"}]],
        ):
            with self.assertRaisesRegex(run_delta.DeltaError, "count queries did not return one row"):
                run_delta.run_coherence_at_tag(Path("/tmp/freshie"), "run-9", 9)

        with patch.object(
            run_delta,
            "dolt_query_dicts",
            side_effect=[
                [{"total_skills": "2"}],
                [{"row_count": "not-a-count"}],
                [{"row_count": "2"}],
            ],
        ):
            with self.assertRaisesRegex(run_delta.DeltaError, "skills row count is not an integer"):
                run_delta.run_coherence_at_tag(Path("/tmp/freshie"), "run-9", 9)


class GradeExportAtTagTests(unittest.TestCase):
    def test_hashes_the_exact_canonical_csv_and_grade_counts(self):
        rows = [
            {"skill_path": "plugins/a,one", "grade": "A", "score": "95"},
            {"skill_path": "plugins/b", "grade": "F", "score": ""},
        ]
        with patch.object(run_delta, "dolt_query_dicts", return_value=rows) as query:
            result = run_delta.grade_export_at_tag(Path("/tmp/freshie"), "run-9", 9)

        self.assertEqual(result["row_count"], 2)
        self.assertEqual(result["grade_counts"], {"A": 1, "F": 1})
        self.assertEqual(
            result["csv_sha256"],
            "5b64e404d44ea5de24d93734a22f555b3c6ac9ae46cc4c2dad714963a728ca08",
        )
        self.assertIn("ORDER BY skill_path", query.call_args.args[1])
        self.assertIn("AS OF 'run-9'", query.call_args.args[1])

    def test_rejects_duplicate_paths(self):
        rows = [
            {"skill_path": "plugins/duplicate", "grade": "A", "score": "90"},
            {"skill_path": "plugins/duplicate", "grade": "B", "score": "80"},
        ]
        with patch.object(run_delta, "dolt_query_dicts", return_value=rows):
            with self.assertRaisesRegex(run_delta.DeltaError, "duplicate skill_path"):
                run_delta.grade_export_at_tag(Path("/tmp/freshie"), "run-9", 9)

    def test_rejects_unrankable_grades(self):
        rows = [{"skill_path": "plugins/one", "grade": "ungraded", "score": "0"}]
        with patch.object(run_delta, "dolt_query_dicts", return_value=rows):
            with self.assertRaisesRegex(run_delta.DeltaError, "unrankable grade 'ungraded'"):
                run_delta.grade_export_at_tag(Path("/tmp/freshie"), "run-9", 9)


class ForgeProofsAtTagTests(unittest.TestCase):
    @staticmethod
    def _row(**overrides):
        row = {
            "plugin_name": "databricks-pack",
            "jrig_run_id": "2",
            "discovery_run_id": "",
            "evidence_class": "E0",
            "artifact_uri": "",
            "artifact_sha256": "",
            "baseline_delta": "",
        }
        row.update(overrides)
        return row

    def test_snapshots_e0_and_hash_verified_e2_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "proof.json"
            artifact.write_bytes(b'{"decision":"ship"}\n')
            digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
            rows = [
                self._row(),
                self._row(
                    plugin_name="retained-pack",
                    jrig_run_id="7",
                    discovery_run_id="13",
                    evidence_class="E2",
                    artifact_uri=str(artifact),
                    artifact_sha256=digest.upper(),
                ),
            ]
            with patch.object(run_delta, "dolt_query_dicts", return_value=rows) as query:
                result = run_delta.forge_proofs_at_tag(Path(tmp), "run-13")

        expected_records = [
            {
                "plugin_name": "databricks-pack",
                "jrig_run_id": 2,
                "discovery_run_id": None,
                "evidence_class": "E0",
                "artifact_uri": None,
                "artifact_sha256": None,
                "baseline_delta": None,
            },
            {
                "plugin_name": "retained-pack",
                "jrig_run_id": 7,
                "discovery_run_id": 13,
                "evidence_class": "E2",
                "artifact_uri": str(artifact),
                "artifact_sha256": digest,
                "baseline_delta": None,
            },
        ]
        canonical = json.dumps(expected_records, sort_keys=True, separators=(",", ":")).encode()
        self.assertEqual(result["records"], expected_records)
        self.assertEqual(result["row_count"], 2)
        self.assertEqual(result["class_counts"], {"E0": 1, "E1": 0, "E2": 1, "E3": 0})
        self.assertEqual(result["retained_e2_e3"], 1)
        self.assertEqual(result["total_e2_e3"], 1)
        self.assertEqual(result["records_sha256"], hashlib.sha256(canonical).hexdigest())
        self.assertIn("AS OF 'run-13'", query.call_args.args[1])
        self.assertIn("jrig_run_id", query.call_args.args[1])
        self.assertIn("evidence_class", query.call_args.args[1])

    def test_propagates_legacy_schema_query_failure(self):
        failure = run_delta.DeltaError("dolt query failed: unknown column jrig_run_id")
        with patch.object(run_delta, "dolt_query_dicts", side_effect=failure):
            with self.assertRaisesRegex(run_delta.DeltaError, "unknown column jrig_run_id"):
                run_delta.forge_proofs_at_tag(Path("/tmp/freshie"), "run-13")

    def test_rejects_missing_artifact(self):
        row = self._row(evidence_class="E2")
        with patch.object(run_delta, "dolt_query_dicts", return_value=[row]):
            with self.assertRaisesRegex(run_delta.DeltaError, "without a retained artifact"):
                run_delta.forge_proofs_at_tag(Path("/tmp/freshie"), "run-13")

    def test_rejects_unretrievable_and_hash_mismatched_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing.json"
            row = self._row(
                evidence_class="E2",
                artifact_uri=str(missing),
                artifact_sha256="a" * 64,
            )
            with patch.object(run_delta, "dolt_query_dicts", return_value=[row]):
                with self.assertRaisesRegex(run_delta.DeltaError, "artifact is not retrievable"):
                    run_delta.forge_proofs_at_tag(Path(tmp), "run-13")

            artifact = Path(tmp) / "proof.json"
            artifact.write_text("primary evidence\n", encoding="utf-8")
            row["artifact_uri"] = str(artifact)
            with patch.object(run_delta, "dolt_query_dicts", return_value=[row]):
                with self.assertRaisesRegex(run_delta.DeltaError, "artifact hash mismatch"):
                    run_delta.forge_proofs_at_tag(Path(tmp), "run-13")

    def test_rejects_e3_without_baseline_delta(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "proof.json"
            artifact.write_text("primary evidence\n", encoding="utf-8")
            digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
            row = self._row(
                evidence_class="E3",
                artifact_uri=str(artifact),
                artifact_sha256=digest,
            )
            with patch.object(run_delta, "dolt_query_dicts", return_value=[row]):
                with self.assertRaisesRegex(run_delta.DeltaError, "E3 without baseline_delta"):
                    run_delta.forge_proofs_at_tag(Path(tmp), "run-13")


class BuildForgeProofReceiptTests(unittest.TestCase):
    def test_binds_receipt_to_run_tag_commit_digest_and_records(self):
        records = [
            {
                "plugin_name": "databricks-pack",
                "jrig_run_id": 2,
                "discovery_run_id": None,
                "evidence_class": "E0",
                "artifact_uri": None,
                "artifact_sha256": None,
                "baseline_delta": None,
            }
        ]
        report = {
            "run_id": 13,
            "to_tag": "run-13",
            "dolt_commit": "9g8rmug5asj787a2sthkq68v2htckdvc",
            "forge_proofs": {
                "records_sha256": "c" * 64,
                "records": records,
                "total_e2_e3": 0,
            },
        }

        self.assertEqual(
            run_delta.build_forge_proof_receipt(report),
            {
                "schema_version": "forge-proof-demotion/v2",
                "status": "immutable-ledger-snapshot",
                "source": "freshie/reports/run-delta-<N>.json forge_proofs snapshot",
                "source_run_id": 13,
                "source_tag": "run-13",
                "source_dolt_commit": "9g8rmug5asj787a2sthkq68v2htckdvc",
                "records_sha256": "c" * 64,
                "records": records,
                "rendering": {"badge": "disabled", "claim_ceiling": "E0"},
            },
        )


class SummaryLineTests(unittest.TestCase):
    def test_normal_line_carries_the_signal_numbers(self):
        report = run_delta.build_report(
            9,
            "run-8",
            "run-9",
            "abc",
            [
                {
                    "table": "skills",
                    "diff_type": "modified",
                    "schema_change": True,
                    "data_change": True,
                    "rows_added": 5,
                    "rows_deleted": 0,
                    "rows_modified": 0,
                }
            ],
            [{"skill_path": "s", "from_grade": "A", "to_grade": "B"}],
        )
        line = run_delta.summary_line(report, Path("freshie/reports/run-delta-9.json"))
        self.assertIn("run-8 → run-9", line)
        self.assertIn("1 table changed (1 schema)", line)
        self.assertIn("1 grade regression →", line)
        self.assertIn("run-delta-9.json", line)

    def test_plural_counts_stay_plural(self):
        report = run_delta.build_report(
            9,
            "run-8",
            "run-9",
            "abc",
            [
                {
                    "table": t,
                    "diff_type": "modified",
                    "schema_change": False,
                    "data_change": True,
                    "rows_added": 1,
                    "rows_deleted": 0,
                    "rows_modified": 0,
                }
                for t in ("a", "b")
            ],
            [{"skill_path": s, "from_grade": "A", "to_grade": "B"} for s in ("s1", "s2")],
        )
        line = run_delta.summary_line(report, Path("x.json"))
        self.assertIn("2 tables changed", line)
        self.assertIn("2 grade regressions", line)

    def test_first_run_line(self):
        report = run_delta.build_report(1, None, "run-1", "abc", [], [])
        line = run_delta.summary_line(report, Path("x.json"))
        self.assertIn("no previous run", line)


class NewestRunTagTests(unittest.TestCase):
    def test_picks_highest_run_and_suffix(self):
        self.assertEqual(
            run_delta.newest_run_tag(["run-8", "run-9", "run-9.1", "v2"]),
            "run-9.1",
        )

    def test_none_when_no_run_tags(self):
        self.assertIsNone(run_delta.newest_run_tag(["v1", "release"]))


if __name__ == "__main__":
    unittest.main()
