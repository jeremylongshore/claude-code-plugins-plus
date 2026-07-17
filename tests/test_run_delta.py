"""Unit tests for freshie/scripts/run-delta.py (run-tag parsing,
previous-tag selection, DOLT_DIFF_SUMMARY/DOLT_DIFF_STAT row merging,
grade-regression detection, report assembly, and the summary line).

Run: python3 -m unittest tests.test_run_delta -v

Coverage honesty: pure-function tests only — no dolt binary, no network,
no repo state. The thin Dolt-query wrappers (dolt_query_dicts, local_tags,
commit_of_tag, grades_at_tag) and emit()'s filesystem write are exercised
by the end-to-end sync against a real Dolt repo, not here.
"""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

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
        self.assertGreater(run_delta.parse_run_tag("run-9.1"),
                           run_delta.parse_run_tag("run-9"))
        self.assertLess(run_delta.parse_run_tag("run-9.1"),
                        run_delta.parse_run_tag("run-10"))

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
        self.assertEqual(
            run_delta.pick_previous_tag(self.TAGS + ["run-10"], "run-10"), "run-9.1"
        )

    def test_earliest_run_has_no_previous(self):
        self.assertIsNone(run_delta.pick_previous_tag(self.TAGS, "run-7"))

    def test_non_run_current_tag(self):
        self.assertIsNone(run_delta.pick_previous_tag(self.TAGS, "v1.0"))

    def test_ignores_non_run_tags(self):
        self.assertEqual(run_delta.pick_previous_tag(["v1.0", "run-3", "run-5"],
                                                     "run-5"), "run-3")


class MergeDiffRowsTests(unittest.TestCase):
    def test_merges_summary_flags_with_stat_counts(self):
        summary = [
            {"from_table_name": "skills", "to_table_name": "skills",
             "diff_type": "modified", "data_change": "true", "schema_change": "false"},
            {"from_table_name": "skill_compliance", "to_table_name": "skill_compliance",
             "diff_type": "modified", "data_change": "true", "schema_change": "true"},
        ]
        stat = [
            {"table_name": "skills", "rows_added": "12", "rows_deleted": "3",
             "rows_modified": "0"},
            {"table_name": "skill_compliance", "rows_added": "3783",
             "rows_deleted": "0", "rows_modified": "0"},
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
        summary = [{"to_table_name": "docs", "diff_type": "modified",
                    "data_change": "false", "schema_change": "true"}]
        merged = run_delta.merge_diff_rows(summary, [])
        self.assertEqual(merged[0]["rows_added"], 0)
        self.assertEqual(merged[0]["rows_modified"], 0)
        self.assertTrue(merged[0]["schema_change"])

    def test_dropped_table_uses_from_name(self):
        # A dropped table has an empty to_table_name in newer Dolt builds.
        summary = [{"from_table_name": "old_table", "to_table_name": "",
                    "diff_type": "dropped", "data_change": "true",
                    "schema_change": "true"}]
        merged = run_delta.merge_diff_rows(summary, [])
        self.assertEqual(merged[0]["table"], "old_table")

    def test_legacy_table_name_column(self):
        summary = [{"table_name": "skills", "diff_type": "modified",
                    "data_change": "1", "schema_change": "0"}]
        merged = run_delta.merge_diff_rows(summary, [])
        self.assertEqual(merged[0]["table"], "skills")
        self.assertTrue(merged[0]["data_change"])
        self.assertFalse(merged[0]["schema_change"])

    def test_output_sorted_by_table(self):
        summary = [{"table_name": t, "diff_type": "modified",
                    "data_change": "true", "schema_change": "false"}
                   for t in ("zeta", "alpha", "mid")]
        merged = run_delta.merge_diff_rows(summary, [])
        self.assertEqual([m["table"] for m in merged], ["alpha", "mid", "zeta"])


class DetectGradeRegressionsTests(unittest.TestCase):
    def test_drop_detected(self):
        out = run_delta.detect_grade_regressions({"s1": "A"}, {"s1": "B"})
        self.assertEqual(out, [{"skill_path": "s1", "from_grade": "A",
                                "to_grade": "B"}])

    def test_multi_step_drop_detected(self):
        out = run_delta.detect_grade_regressions({"s1": "B"}, {"s1": "F"})
        self.assertEqual(out[0]["to_grade"], "F")

    def test_improvement_is_not_a_regression(self):
        self.assertEqual(
            run_delta.detect_grade_regressions({"s1": "C"}, {"s1": "A"}), []
        )

    def test_unchanged_is_not_a_regression(self):
        self.assertEqual(
            run_delta.detect_grade_regressions({"s1": "B"}, {"s1": "B"}), []
        )

    def test_added_and_removed_skills_ignored(self):
        # Membership changes are not grade movement.
        self.assertEqual(
            run_delta.detect_grade_regressions({"gone": "A"}, {"new": "F"}), []
        )

    def test_unrankable_grades_skipped(self):
        self.assertEqual(
            run_delta.detect_grade_regressions(
                {"s1": "A", "s2": ""}, {"s1": "ungraded", "s2": "F"}
            ),
            [],
        )

    def test_sorted_by_skill_path(self):
        out = run_delta.detect_grade_regressions(
            {"z": "A", "a": "A", "m": "B"}, {"z": "B", "a": "C", "m": "D"}
        )
        self.assertEqual([r["skill_path"] for r in out], ["a", "m", "z"])


class BuildReportTests(unittest.TestCase):
    def _tables(self):
        return [
            {"table": "skills", "diff_type": "modified", "schema_change": False,
             "data_change": True, "rows_added": 10, "rows_deleted": 2,
             "rows_modified": 1},
            {"table": "docs", "diff_type": "modified", "schema_change": True,
             "data_change": False, "rows_added": 0, "rows_deleted": 0,
             "rows_modified": 0},
        ]

    def test_shape_and_totals(self):
        regressions = [{"skill_path": "s1", "from_grade": "A", "to_grade": "B"}]
        report = run_delta.build_report(9, "run-8", "run-9", "abc123",
                                        self._tables(), regressions)
        self.assertEqual(report["run_id"], 9)
        self.assertEqual(report["dolt_commit"], "abc123")
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
        self.assertEqual(report["tables_changed"], 0)
        self.assertEqual(report["grade_regressions"], [])


class SummaryLineTests(unittest.TestCase):
    def test_normal_line_carries_the_signal_numbers(self):
        report = run_delta.build_report(
            9, "run-8", "run-9", "abc",
            [{"table": "skills", "diff_type": "modified", "schema_change": True,
              "data_change": True, "rows_added": 5, "rows_deleted": 0,
              "rows_modified": 0}],
            [{"skill_path": "s", "from_grade": "A", "to_grade": "B"}],
        )
        line = run_delta.summary_line(report, Path("freshie/reports/run-delta-9.json"))
        self.assertIn("run-8 → run-9", line)
        self.assertIn("1 table changed (1 schema)", line)
        self.assertIn("1 grade regression →", line)
        self.assertIn("run-delta-9.json", line)

    def test_plural_counts_stay_plural(self):
        report = run_delta.build_report(
            9, "run-8", "run-9", "abc",
            [{"table": t, "diff_type": "modified", "schema_change": False,
              "data_change": True, "rows_added": 1, "rows_deleted": 0,
              "rows_modified": 0} for t in ("a", "b")],
            [{"skill_path": s, "from_grade": "A", "to_grade": "B"}
             for s in ("s1", "s2")],
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
