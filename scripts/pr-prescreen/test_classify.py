"""Unit tests for classify.py.

Run: python3 -m pytest scripts/pr-prescreen/test_classify.py -q
Or:  python3 scripts/pr-prescreen/test_classify.py
"""

from __future__ import annotations

import json
import os
import sys
import unittest
from io import StringIO
from unittest.mock import patch

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from classify import classify, main  # noqa: E402


def _r(path: str, score: int, grade: str, errors: int = 0, warnings: int = 0) -> dict:
    return {"path": path, "score": score, "grade": grade, "errors": errors, "warnings": warnings}


class ClassifyTests(unittest.TestCase):
    def test_empty_input_passes(self):
        out = classify([])
        self.assertEqual(out["verdict"], "PASS")
        self.assertEqual(out["blockers"], [])
        self.assertIn("no plugin paths", out["summary"])

    def test_all_grade_a_passes(self):
        out = classify([_r("plugins/x/y/skills/y/SKILL.md", 95, "A")])
        self.assertEqual(out["verdict"], "PASS")
        self.assertEqual(out["blockers"], [])
        self.assertEqual(out["warnings"], [])

    def test_grade_c_passes_with_warning(self):
        # Grade C is the floor for PASS — borderline but acceptable.
        out = classify([_r("plugins/x/y/skills/y/SKILL.md", 72, "C")])
        self.assertEqual(out["verdict"], "PASS")
        self.assertEqual(len(out["warnings"]), 1)

    def test_validator_errors_request_changes(self):
        out = classify([_r("plugins/x/y/skills/y/SKILL.md", 65, "D", errors=2)])
        self.assertEqual(out["verdict"], "CHANGES_REQUESTED")
        self.assertTrue(any("validator errors" in b for b in out["blockers"]))

    def test_grade_f_requests_changes_even_without_errors(self):
        out = classify([_r("plugins/x/y/skills/y/SKILL.md", 40, "F", errors=0)])
        self.assertEqual(out["verdict"], "CHANGES_REQUESTED")
        self.assertTrue(any("grade F" in b for b in out["blockers"]))

    def test_fatal_hard_blocks(self):
        out = classify([{"path": "plugins/x/y/skills/y/SKILL.md", "fatal": "missing frontmatter"}])
        self.assertEqual(out["verdict"], "HARD_BLOCK")
        self.assertTrue(any("fatal" in b for b in out["blockers"]))

    def test_external_hard_block_signal(self):
        # Even an all-A PR hard-blocks if the workflow injected a structural concern.
        out = classify(
            [_r("plugins/x/y/skills/y/SKILL.md", 95, "A")],
            hard_block_signals=["No catalog entry for plugins/x/y in marketplace.extended.json"],
        )
        self.assertEqual(out["verdict"], "HARD_BLOCK")
        self.assertIn(
            "No catalog entry for plugins/x/y in marketplace.extended.json",
            out["blockers"],
        )

    def test_hard_block_signal_iterator_not_exhausted(self):
        # Regression: a generator passed as hard_block_signals must not be
        # consumed by an intermediate loop before the verdict check runs.
        signals = (s for s in ["secret leaked"])
        out = classify([_r("plugins/x/SKILL.md", 95, "A")], hard_block_signals=signals)
        self.assertEqual(out["verdict"], "HARD_BLOCK")
        self.assertIn("secret leaked", out["blockers"])

    def test_null_errors_does_not_crash(self):
        # Regression: validator can emit {"errors": null} on partial results.
        out = classify([{"path": "p", "score": 90, "grade": "A", "errors": None, "warnings": None}])
        self.assertEqual(out["verdict"], "PASS")

    def test_null_score_does_not_crash_in_summary(self):
        out = classify([{"path": "p", "score": None, "grade": "F", "errors": 1}])
        # Verdict is CHANGES_REQUESTED due to errors; summary shouldn't crash.
        self.assertEqual(out["verdict"], "CHANGES_REQUESTED")
        self.assertIn("CHANGES_REQUESTED", out["summary"])

    def test_mixed_results_picks_worst(self):
        out = classify(
            [
                _r("plugins/a/SKILL.md", 95, "A"),
                _r("plugins/b/SKILL.md", 55, "F", errors=3),
            ]
        )
        self.assertEqual(out["verdict"], "CHANGES_REQUESTED")
        self.assertGreaterEqual(len(out["blockers"]), 1)

    def test_summary_includes_average_score(self):
        out = classify([_r("a", 90, "A"), _r("b", 80, "B")])
        self.assertIn("85", out["summary"])

    def test_main_reads_stdin(self):
        payload = json.dumps([_r("plugins/x/SKILL.md", 95, "A")])
        with patch("sys.stdin", StringIO(payload)), patch("sys.stdout", new_callable=StringIO) as out:
            rc = main(["classify.py", "-"])
        self.assertEqual(rc, 0)
        parsed = json.loads(out.getvalue())
        self.assertEqual(parsed["verdict"], "PASS")

    def test_main_rejects_non_list(self):
        payload = json.dumps({"oops": True})
        with patch("sys.stdin", StringIO(payload)):
            rc = main(["classify.py", "-"])
        self.assertEqual(rc, 2)

    def test_main_picks_up_env_signals(self):
        payload = json.dumps([_r("plugins/x/SKILL.md", 95, "A")])
        with (
            patch("sys.stdin", StringIO(payload)),
            patch("sys.stdout", new_callable=StringIO) as out,
            patch.dict(os.environ, {"PR_PRESCREEN_HARD_BLOCKS": "secret detected in diff"}),
        ):
            rc = main(["classify.py", "-"])
        self.assertEqual(rc, 0)
        parsed = json.loads(out.getvalue())
        self.assertEqual(parsed["verdict"], "HARD_BLOCK")
        self.assertIn("secret detected in diff", parsed["blockers"])


if __name__ == "__main__":
    unittest.main()
