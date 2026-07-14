"""Regression tests for phantom half-run handling in
freshie/scripts/rebuild-inventory.py (2026-07-14 ops review).

A crash mid-scan leaves a discovery_runs row whose totals were never written
(the totals UPDATE is the LAST step of a successful run) plus partial rows in
every table the scan had reached. The default rerun used to compute MAX(id)+1
and leave the phantom behind, where dolt-sync exported it permanently into the
append-only Dolt history. find_phantom_runs() is the detector; run_scan purges
the newest phantom and reuses its id.

Run: python3 -m unittest tests.test_rebuild_inventory_phantom -v
"""

import importlib.util
import sqlite3
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "freshie" / "scripts" / "rebuild-inventory.py"
_spec = importlib.util.spec_from_file_location("rebuild_inventory_tests", SCRIPT)
ri = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ri)


def _db_with_phantom() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row  # matches open_db()
    conn.execute(
        "CREATE TABLE discovery_runs (id INTEGER PRIMARY KEY, run_date TEXT, "
        "commit_hash TEXT, total_packs INTEGER, total_plugins INTEGER, "
        "total_skills INTEGER, total_files INTEGER, total_root_files INTEGER)"
    )
    conn.execute("CREATE TABLE skills (id INTEGER PRIMARY KEY, run_id INTEGER)")
    # Run 1 completed: totals written by Step 15.
    conn.execute(
        "INSERT INTO discovery_runs (id, run_date, total_packs, total_plugins, "
        "total_skills, total_files, total_root_files) VALUES (1, '2026-01-01', 1, 1, 10, 100, 5)"
    )
    conn.execute("INSERT INTO skills (run_id) VALUES (1)")
    # Run 2 crashed mid-scan: row inserted up front, totals never written.
    conn.execute("INSERT INTO discovery_runs (id, run_date) VALUES (2, '2026-01-02')")
    conn.execute("INSERT INTO skills (run_id) VALUES (2)")
    conn.commit()
    return conn


class FindPhantomRunsTests(unittest.TestCase):
    def test_detects_run_with_null_totals(self):
        conn = _db_with_phantom()
        self.assertEqual(ri.find_phantom_runs(conn), [2])
        conn.close()

    def test_no_phantoms_when_all_runs_complete(self):
        conn = _db_with_phantom()
        conn.execute("UPDATE discovery_runs SET total_skills = 7 WHERE id = 2")
        self.assertEqual(ri.find_phantom_runs(conn), [])
        conn.close()

    def test_legacy_schema_without_totals_column_returns_empty(self):
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        conn.execute("CREATE TABLE discovery_runs (id INTEGER PRIMARY KEY)")
        conn.execute("INSERT INTO discovery_runs (id) VALUES (1)")
        self.assertEqual(ri.find_phantom_runs(conn), [])
        conn.close()


class PurgePhantomTests(unittest.TestCase):
    def test_purge_run_removes_phantom_rows_and_keeps_complete_run(self):
        conn = _db_with_phantom()
        ri.purge_run(conn, 2)
        runs = [row["id"] for row in conn.execute("SELECT id FROM discovery_runs").fetchall()]
        self.assertEqual(runs, [1])
        self.assertEqual(
            conn.execute("SELECT COUNT(*) FROM skills WHERE run_id = 2").fetchone()[0], 0
        )
        self.assertEqual(
            conn.execute("SELECT COUNT(*) FROM skills WHERE run_id = 1").fetchone()[0], 1
        )
        # The freed id is reused by the next default run.
        self.assertEqual(ri.next_run_id(conn), 2)
        conn.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
