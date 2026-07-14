"""Regression tests for freshie/scripts/promote-to-curated.py (2026-07-14 ops review).

Two defects pinned here:
  1. No-floor wipe (P1/P2): build mode wiped skills/.curated/ BEFORE computing the
     selection outcome, so every upstream failure mode (empty/truncated/corrupt
     grades.csv, a validator API drift nulling every fresh grade) converged on
     deleting all ~1,881 promoted skills and exiting 0 "success". Build now
     computes the selection first and ABORTS non-zero — mirror untouched — when
     the selection is empty or below SHRINK_FLOOR_RATIO of the committed
     MANIFEST count. --allow-shrink overrides for a legitimate large drop.
  2. Degrade contract vs SystemExit (P2): the validator's module-level guard
     calls sys.exit(1) when pyyaml is missing; SystemExit inherits BaseException,
     so load_validator's `except Exception` never caught it and the documented
     "degrades to recorded grades" fallback silently did not apply.

Run: python3 -m unittest tests.test_promote_to_curated_floor -v

Fully self-contained: builds a tmp curated mirror + grades.csv, monkeypatches the
module's ROOT / GRADES_CSV / CURATED_DIR / MANIFEST / tracked_files, and never
touches the real repo.
"""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "freshie" / "scripts" / "promote-to-curated.py"
_spec = importlib.util.spec_from_file_location("promote_to_curated", SCRIPT)
pc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pc)

SKILL_MD = """\
---
name: {name}
description: A promoted test skill.
---
# Body
"""


class PromoteFloorTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        self.root = root
        self.curated = root / "skills" / ".curated"
        self.manifest = self.curated / "MANIFEST.json"

        # An existing mirror with 4 promoted skills + a committed MANIFEST.
        self.existing_dirs = []
        for i in range(4):
            d = self.curated / f"existing-{i}"
            d.mkdir(parents=True)
            (d / "SKILL.md").write_text(SKILL_MD.format(name=f"existing-{i}"), encoding="utf-8")
            self.existing_dirs.append(d)
        self._write_manifest(4)

        self.grades_csv = root / "freshie" / "grades.csv"
        self.grades_csv.parent.mkdir(parents=True)

        self._orig = {k: getattr(pc, k) for k in ("ROOT", "GRADES_CSV", "CURATED_DIR", "MANIFEST", "tracked_files")}
        pc.ROOT = root
        pc.GRADES_CSV = self.grades_csv
        pc.CURATED_DIR = self.curated
        pc.MANIFEST = self.manifest

    def tearDown(self):
        for k, v in self._orig.items():
            setattr(pc, k, v)
        self._tmp.cleanup()

    # ── helpers ──────────────────────────────────────────────────────────
    def _write_manifest(self, n: int) -> None:
        self.manifest.write_text(
            json.dumps({"count": n, "skills": [{"curated_name": f"existing-{i}"} for i in range(n)]})
        )

    def _make_candidates(self, n: int) -> None:
        """Write a grades.csv with n A-grade plugin skills whose sources exist."""
        lines = ["skill_path,grade,score"]
        for i in range(n):
            sp = f"plugins/cat/plug/skills/cand-{i}"
            src = self.root / sp
            src.mkdir(parents=True, exist_ok=True)
            (src / "SKILL.md").write_text(SKILL_MD.format(name=f"cand-{i}"), encoding="utf-8")
            lines.append(f"{sp},A,95")
        self.grades_csv.write_text("\n".join(lines) + "\n")
        # tmp tree is not a git repo — pretend every source tracks its SKILL.md
        pc.tracked_files = lambda skill_dir: ["SKILL.md"]

    def _mirror_intact(self) -> bool:
        return all(d.is_dir() and (d / "SKILL.md").is_file() for d in self.existing_dirs)

    # ── the floor: abort BEFORE the wipe ─────────────────────────────────
    def test_empty_grades_csv_aborts_before_wipe(self):
        self.grades_csv.write_text("skill_path,grade,score\n")  # header only
        rc = pc.build(validate=False, quiet=True)
        self.assertNotEqual(rc, 0)
        self.assertTrue(self._mirror_intact(), "mirror must be untouched on abort")
        self.assertTrue(self.manifest.is_file(), "MANIFEST must survive an abort")

    def test_corrupt_grades_csv_aborts_before_wipe(self):
        self.grades_csv.write_text("garbage\x00not,a,csv\n\n???\n")
        rc = pc.build(validate=False, quiet=True)
        self.assertNotEqual(rc, 0)
        self.assertTrue(self._mirror_intact())

    def test_selection_below_ratio_floor_aborts(self):
        # committed mirror says 10; the new selection is only 2 (< 50% floor)
        self._write_manifest(10)
        self._make_candidates(2)
        rc = pc.build(validate=False, quiet=True)
        self.assertNotEqual(rc, 0)
        self.assertTrue(self._mirror_intact())

    # ── --allow-shrink is the explicit override ──────────────────────────
    def test_allow_shrink_permits_empty_rebuild(self):
        self.grades_csv.write_text("skill_path,grade,score\n")
        rc = pc.build(validate=False, quiet=True, allow_shrink=True)
        self.assertEqual(rc, 0)
        self.assertFalse(self._mirror_intact(), "--allow-shrink rebuild wipes the old mirror")
        manifest = json.loads(self.manifest.read_text())
        self.assertEqual(manifest["count"], 0)

    def test_allow_shrink_permits_ratio_shrink(self):
        self._write_manifest(10)
        self._make_candidates(2)
        rc = pc.build(validate=False, quiet=True, allow_shrink=True)
        self.assertEqual(rc, 0)
        manifest = json.loads(self.manifest.read_text())
        self.assertEqual(manifest["count"], 2)

    # ── healthy paths keep building ──────────────────────────────────────
    def test_healthy_selection_above_floor_builds(self):
        self._make_candidates(4)  # 4 vs committed 4 -> well above the 50% floor
        rc = pc.build(validate=False, quiet=True)
        self.assertEqual(rc, 0)
        manifest = json.loads(self.manifest.read_text())
        self.assertEqual(manifest["count"], 4)
        for i in range(4):
            self.assertTrue((self.curated / f"cand-{i}" / "SKILL.md").is_file())

    def test_first_build_without_manifest_builds(self):
        # no committed MANIFEST / mirror at all -> no baseline, only the
        # empty-selection guard applies
        import shutil

        shutil.rmtree(self.curated)
        self._make_candidates(2)
        rc = pc.build(validate=False, quiet=True)
        self.assertEqual(rc, 0)
        self.assertEqual(json.loads(self.manifest.read_text())["count"], 2)

    def test_first_build_with_empty_selection_still_aborts(self):
        import shutil

        shutil.rmtree(self.curated)
        self.grades_csv.write_text("skill_path,grade,score\n")
        rc = pc.build(validate=False, quiet=True)
        self.assertNotEqual(rc, 0)
        self.assertFalse(self.curated.exists(), "no mirror should be created on abort")


class LoadValidatorDegradeTests(unittest.TestCase):
    """The degrade contract must hold even when the validator hard-exits at
    import time (SystemExit from its missing-pyyaml guard)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._orig_validator = pc.VALIDATOR

    def tearDown(self):
        pc.VALIDATOR = self._orig_validator
        self._tmp.cleanup()

    def test_systemexit_at_import_degrades_to_none(self):
        fake = Path(self._tmp.name) / "fake_validator.py"
        fake.write_text("import sys\nsys.exit(1)\n")  # same shape as the pyyaml guard
        pc.VALIDATOR = fake
        # must NOT raise SystemExit; must return None so build degrades
        self.assertIsNone(pc.load_validator())

    def test_ordinary_exception_at_import_degrades_to_none(self):
        fake = Path(self._tmp.name) / "fake_validator.py"
        fake.write_text("raise RuntimeError('kernel schema missing')\n")
        pc.VALIDATOR = fake
        self.assertIsNone(pc.load_validator())


if __name__ == "__main__":
    unittest.main(verbosity=2)
