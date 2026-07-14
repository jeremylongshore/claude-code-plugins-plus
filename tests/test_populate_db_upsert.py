"""Regression test for the --populate-db skill_compliance write (2026-07-14 ops
review): INSERT OR REPLACE under UNIQUE(skill_path, run_id) is delete-then-insert,
so the j-rig-owned jrig_* columns (paid behavioral-eval results, $2-5/skill) were
silently NULLed every time the same discovery run was re-validated. The write is
now an UPSERT whose DO UPDATE clause rewrites only validator-owned columns.

Run: python3 -m unittest tests.test_populate_db_upsert -v

Fully self-contained: tmp sqlite DB + tmp skill tree; never touches the real
freshie/inventory.sqlite.
"""

import importlib.util
import sqlite3
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate-skills-schema.py"
_spec = importlib.util.spec_from_file_location("vss_populate_upsert_tests", SCRIPT)
vss = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vss)

SKILL = """\
---
name: upsert-pin
description: Pins that j-rig columns survive re-population.
---
# Body
"""


class PopulateDbUpsertTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        self.db = root / "inv.sqlite"
        conn = sqlite3.connect(self.db)
        conn.execute(
            "CREATE TABLE discovery_runs (id INTEGER PRIMARY KEY, run_date TEXT, "
            "commit_hash TEXT, total_packs INTEGER, total_plugins INTEGER, "
            "total_skills INTEGER, total_files INTEGER, total_root_files INTEGER)"
        )
        conn.execute("INSERT INTO discovery_runs (id) VALUES (1)")
        conn.commit()
        conn.close()
        skill_dir = root / "plugins" / "cat" / "p" / "skills" / "upsert-pin"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(SKILL, encoding="utf-8")
        self.result = {
            "path": str(skill_dir / "SKILL.md"),
            "score": 80,
            "grade": "B",
            "errors": 0,
            "warnings": 1,
        }

    def tearDown(self):
        self._tmp.cleanup()

    def _rows(self):
        conn = sqlite3.connect(self.db)
        rows = conn.execute(
            "SELECT score, grade, jrig_passed, jrig_tier_blocked, jrig_baseline_delta "
            "FROM skill_compliance"
        ).fetchall()
        conn.close()
        return rows

    def test_repopulate_preserves_jrig_columns_and_updates_validator_columns(self):
        # First populate: fresh row, jrig columns default NULL.
        vss.populate_compliance_db(str(self.db), [self.result])
        rows = self._rows()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0], (80, "B", None, None, None))

        # j-rig writes its behavioral-eval verdict into the same row.
        conn = sqlite3.connect(self.db)
        conn.execute(
            "UPDATE skill_compliance SET jrig_passed=1, jrig_tier_blocked=0, jrig_baseline_delta=0.25"
        )
        conn.commit()
        conn.close()

        # Re-populate the SAME run (e.g. after batch-remediate, to measure grade
        # movement). Validator-owned columns must update; jrig_* must survive.
        vss.populate_compliance_db(str(self.db), [dict(self.result, score=90, grade="A")])
        rows = self._rows()
        self.assertEqual(len(rows), 1)  # still one row per (skill_path, run_id)
        score, grade, jrig_passed, jrig_tier_blocked, jrig_delta = rows[0]
        self.assertEqual((score, grade), (90, "A"))
        self.assertEqual((jrig_passed, jrig_tier_blocked), (1, 0))
        self.assertAlmostEqual(jrig_delta, 0.25)


if __name__ == "__main__":
    unittest.main(verbosity=2)
