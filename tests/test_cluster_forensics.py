"""Unit tests for the databricks-cluster-forensics deterministic scripts
(beads claude-4x0v cold-start bucketer + claude-c54a CWD-write scanner).

Targets:
  plugins/saas-packs/databricks-pack/skills/databricks-cluster-forensics/scripts/
    cluster-coldstart-forensics.py  — bucket cold-start PENDING time by stage
    find-cwd-writes.py              — AST scan for DBR-14 CWD (500MB-cap) writes

Both are the deterministic half of the skill (the LLM never eyeballs timestamps or
paths); their contracts are pinned here.

Run: python3 -m unittest tests.test_cluster_forensics -v
"""

import importlib.util
import unittest
from pathlib import Path

BASE = (
    Path(__file__).resolve().parents[1]
    / "plugins" / "saas-packs" / "databricks-pack" / "skills"
    / "databricks-cluster-forensics" / "scripts"
)


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, BASE / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


cs = _load("coldstart", "cluster-coldstart-forensics.py")
cw = _load("cwdwrites", "find-cwd-writes.py")


class ColdStartBucketTests(unittest.TestCase):
    def _events(self, *pairs):
        return {"events": [{"type": t, "timestamp": ts} for t, ts in pairs]}

    def test_provisioning_dominant(self):
        ev = self._events(
            ("CREATING", 0), ("INIT_SCRIPTS_STARTED", 1_080_000),
            ("INIT_SCRIPTS_FINISHED", 1_140_000), ("DRIVER_HEALTHY", 1_320_000),
        )
        r = cs.bucket_coldstart(ev)
        self.assertEqual(r["dominant"], "provisioning")
        self.assertEqual(r["stages"]["provisioning"]["ms"], 1_080_000)
        self.assertEqual(r["stages"]["init_scripts"]["ms"], 60_000)
        self.assertEqual(r["total_ms"], 1_320_000)

    def test_init_scripts_dominant(self):
        ev = self._events(
            ("CREATING", 0), ("INIT_SCRIPTS_STARTED", 60_000),
            ("INIT_SCRIPTS_FINISHED", 660_000), ("RUNNING", 720_000),
        )
        r = cs.bucket_coldstart(ev)
        self.assertEqual(r["dominant"], "init_scripts")

    def test_failed_start_is_flagged(self):
        ev = self._events(("CREATING", 0), ("TERMINATING", 600_000))
        r = cs.bucket_coldstart(ev)
        self.assertTrue(any("did NOT reach a ready state" in n for n in r["notes"]))

    def test_missing_init_events_are_unmeasured_not_folded(self):
        # No init-script events: init_scripts must be unmeasured, never merged.
        ev = self._events(("CREATING", 0), ("STARTING", 300_000), ("RUNNING", 360_000))
        r = cs.bucket_coldstart(ev)
        self.assertFalse(r["stages"]["init_scripts"]["measured"])
        self.assertIsNone(r["stages"]["init_scripts"]["ms"])
        self.assertTrue(any("no INIT_SCRIPTS" in n for n in r["notes"]))

    def test_empty_events(self):
        r = cs.bucket_coldstart({"events": []})
        self.assertIsNone(r["dominant"])
        self.assertIsNone(r["total_ms"])

    def test_accepts_bare_list_and_sorts(self):
        # out-of-order bare list
        ev = [{"type": "RUNNING", "timestamp": 500}, {"type": "CREATING", "timestamp": 0}]
        r = cs.bucket_coldstart(ev)
        self.assertEqual(r["total_ms"], 500)

    def test_drops_malformed_rows(self):
        ev = {"events": [{"type": "CREATING", "timestamp": 0}, {"type": "X"}, {"timestamp": 5},
                         {"type": "RUNNING", "timestamp": 100}]}
        r = cs.bucket_coldstart(ev)
        self.assertEqual(r["total_ms"], 100)


class CwdWriteScanTests(unittest.TestCase):
    def test_relative_write_is_cwd_at_risk(self):
        f = cw.find_cwd_writes("df.to_parquet('staging/x.parquet')")
        self.assertEqual(len(f), 1)
        self.assertEqual(f[0]["kind"], cw.CWD)
        self.assertEqual(f[0]["sink"], ".to_parquet")

    def test_cloud_and_dbfs_and_tmp_are_safe(self):
        for path in ("/dbfs/tmp/x.csv", "s3://b/x", "abfss://c@a/x", "/tmp/x", "/Volumes/c/s/v/x"):
            f = cw.find_cwd_writes(f"df.to_csv({path!r})")
            self.assertEqual(f[0]["kind"], cw.SAFE, path)

    def test_open_write_mode_is_a_write_read_is_not(self):
        w = cw.find_cwd_writes("open('scratch.txt', 'w')")
        self.assertEqual(w[0]["kind"], cw.CWD)
        r = cw.find_cwd_writes("open('data.txt')")  # no mode = read
        self.assertEqual(r, [])
        r2 = cw.find_cwd_writes("open('data.txt', 'r')")
        self.assertEqual(r2, [])

    def test_dynamic_path_is_review(self):
        f = cw.find_cwd_writes("df.to_csv(out_path)")
        self.assertEqual(f[0]["kind"], cw.DYNAMIC)
        self.assertIsNone(f[0]["path"])

    def test_spark_write_relative(self):
        f = cw.find_cwd_writes("spark_df.write.parquet('results')")
        self.assertEqual(f[0]["kind"], cw.CWD)

    def test_path_write_text(self):
        f = cw.find_cwd_writes("Path('out.txt').write_text('x')")
        self.assertEqual(len(f), 1)
        self.assertEqual(f[0]["kind"], cw.CWD)

    def test_line_numbers_reported(self):
        src = "a = 1\ndf.to_csv('x.csv')\n"
        f = cw.find_cwd_writes(src)
        self.assertEqual(f[0]["line"], 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
