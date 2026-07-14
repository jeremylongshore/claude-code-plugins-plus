"""Regression tests for freshie/scripts/promote-to-curated.py build-mode guards
(2026-07-14 ops review):

  1. Wipe floor — every selection failure mode (empty/truncated grades.csv,
     validator API drift dropping 100% of candidates) used to converge on
     wiping all ~1,881 skills/.curated/ dirs and exiting 0. build() now refuses
     to touch the mirror when the fresh selection collapses; --force-floor is
     the deliberate-shrink override.
  2. Degrade contract — the validator sys.exit(1)s at import when pyyaml is
     missing; SystemExit does not inherit Exception, so load_validator's
     documented "fall back to recorded grades" never fired and the whole
     promoter died (the 2026-07-13 CI incident, previously patched only in the
     workflow).

Run: python3 -m unittest tests.test_promote_curated_floor -v

Fully self-contained: tmp tree, module globals monkeypatched; never touches the
real skills/.curated/ mirror.
"""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "freshie" / "scripts" / "promote-to-curated.py"
_spec = importlib.util.spec_from_file_location("promote_to_curated_tests", SCRIPT)
pc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pc)


class WipeFloorTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        # Header-only grades.csv — the truncated-export failure mode.
        self.grades = root / "grades.csv"
        self.grades.write_text("skill_path,grade,score\n", encoding="utf-8")
        # An existing mirror with one promoted dir + a committed MANIFEST.
        self.curated = root / "skills" / ".curated"
        self.survivor = self.curated / "existing-skill"
        self.survivor.mkdir(parents=True)
        (self.survivor / "SKILL.md").write_text("# existing\n", encoding="utf-8")
        self.manifest = self.curated / "MANIFEST.json"
        self.manifest.write_text(json.dumps({"count": 1881, "skills": []}), encoding="utf-8")

        self._orig = {k: getattr(pc, k) for k in ("ROOT", "GRADES_CSV", "CURATED_DIR", "MANIFEST")}
        pc.ROOT = root
        pc.GRADES_CSV = self.grades
        pc.CURATED_DIR = self.curated
        pc.MANIFEST = self.manifest

    def tearDown(self):
        for k, v in self._orig.items():
            setattr(pc, k, v)
        self._tmp.cleanup()

    def test_empty_selection_refuses_to_wipe(self):
        rc = pc.build(validate=False, quiet=True)
        self.assertEqual(rc, 1)
        # Mirror and manifest untouched.
        self.assertTrue((self.survivor / "SKILL.md").is_file())
        self.assertEqual(json.loads(self.manifest.read_text())["count"], 1881)

    def test_floor_triggers_below_ratio_of_committed_count(self):
        # A selection well under 50% of the committed 1,881 (and under the
        # absolute floor of 500) must also refuse — even when nonzero.
        self.grades.write_text(
            "skill_path,grade,score\nplugins/cat/p/skills/only-one,A,95\n",
            encoding="utf-8",
        )
        # Source dir must exist for load_candidates to keep the row.
        (pc.ROOT / "plugins" / "cat" / "p" / "skills" / "only-one").mkdir(parents=True)
        rc = pc.build(validate=False, quiet=True)
        self.assertEqual(rc, 1)
        self.assertTrue((self.survivor / "SKILL.md").is_file())

    def test_force_floor_allows_deliberate_shrink(self):
        rc = pc.build(validate=False, quiet=True, force_floor=True)
        self.assertEqual(rc, 0)
        self.assertFalse(self.survivor.exists())
        self.assertEqual(json.loads(self.manifest.read_text())["count"], 0)


class ValidatorImportDegradeTests(unittest.TestCase):
    def test_load_validator_degrades_on_systemexit(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp) / "fake-validator.py"
            fake.write_text("import sys\nsys.exit(1)\n", encoding="utf-8")
            orig = pc.VALIDATOR
            pc.VALIDATOR = fake
            try:
                self.assertIsNone(pc.load_validator())
            finally:
                pc.VALIDATOR = orig

    def test_load_validator_degrades_on_plain_exception(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp) / "fake-validator.py"
            fake.write_text("raise RuntimeError('boom')\n", encoding="utf-8")
            orig = pc.VALIDATOR
            pc.VALIDATOR = fake
            try:
                self.assertIsNone(pc.load_validator())
            finally:
                pc.VALIDATOR = orig


if __name__ == "__main__":
    unittest.main(verbosity=2)
