"""Unit tests for the databricks-uc-migration-pilot HMS-readiness classifier
(bead claude-q9d7).

Target: plugins/saas-packs/databricks-pack/skills/databricks-uc-migration-pilot/
        scripts/audit-hms-readiness.py

The classifier is the deterministic heart of the migration pilot — it decides,
per Hive Metastore table, whether it is UC-migration READY (cloud-native path),
BLOCKED (a named un-migratable condition), or ORPHAN (a dangling HMS entry). The
LLM never eyeballs a storage URI, so the classification rule must be pinned:
s3/abfss/gs = ready; wasbs/adl/dbfs = blocked; missing storage = orphan (surfaced,
never mis-reported as a blocker).

Run: python3 -m unittest tests.test_hms_readiness_classifier -v

Pure-function tests — no databricks CLI, no network.
"""

import importlib.util
import unittest
from pathlib import Path

SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "plugins" / "saas-packs" / "databricks-pack" / "skills"
    / "databricks-uc-migration-pilot" / "scripts" / "audit-hms-readiness.py"
)
spec = importlib.util.spec_from_file_location("audit_hms_readiness", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def verdict(row):
    """READY / BLOCKED / ORPHAN for a row, mirroring rows_to_csv's bucketing."""
    _, blocker, _ = mod.classify(row)
    if not (row.get("storage_uri") or "").strip():
        return mod.ORPHAN
    return mod.BLOCKED if blocker else mod.READY


class UriSchemeTests(unittest.TestCase):
    def test_scheme_extraction(self):
        self.assertEqual(mod.uri_scheme("s3://bucket/x"), "s3")
        self.assertEqual(mod.uri_scheme("abfss://c@a.dfs.core.windows.net/y"), "abfss")
        self.assertEqual(mod.uri_scheme("dbfs:/user/hive/warehouse/x"), "dbfs")
        self.assertEqual(mod.uri_scheme("dbfs:///user/hive/x"), "dbfs")
        self.assertEqual(mod.uri_scheme("WASBS://X"), "wasbs")  # case-insensitive
        self.assertEqual(mod.uri_scheme(""), "")
        self.assertEqual(mod.uri_scheme(None), "")


class ReadySchemesTests(unittest.TestCase):
    def test_cloud_native_delta_is_ready(self):
        for uri in ("s3://bkt/x", "abfss://c@a.dfs.core.windows.net/x", "gs://bkt/x"):
            row = {"storage_uri": uri, "table_type": "EXTERNAL", "table_format": "DELTA"}
            self.assertEqual(verdict(row), mod.READY, uri)

    def test_ready_delta_suggests_sync(self):
        row = {"storage_uri": "s3://bkt/x", "table_type": "EXTERNAL", "table_format": "DELTA"}
        _, blocker, suggested = mod.classify(row)
        self.assertEqual(blocker, "")
        self.assertIn("SYNC", suggested)


class BlockedSchemesTests(unittest.TestCase):
    def test_azure_legacy_schemes_blocked(self):
        for uri in ("wasbs://c@a.blob.core.windows.net/x", "adl://store.azuredatalakestore.net/y"):
            row = {"storage_uri": uri}
            self.assertEqual(verdict(row), mod.BLOCKED, uri)
            _, blocker, suggested = mod.classify(row)
            self.assertIn("legacy Azure", blocker)
            self.assertIn("abfss://", suggested)

    def test_dbfs_root_blocked(self):
        row = {"storage_uri": "dbfs:/user/hive/warehouse/sales.db/orders", "table_type": "MANAGED"}
        self.assertEqual(verdict(row), mod.BLOCKED)
        _, blocker, suggested = mod.classify(row)
        self.assertIn("DBFS", blocker)
        self.assertIn("DEEP CLONE", suggested)

    def test_unknown_scheme_blocked(self):
        row = {"storage_uri": "file:/tmp/x"}
        self.assertEqual(verdict(row), mod.BLOCKED)


class OrphanTests(unittest.TestCase):
    def test_missing_storage_is_orphan_not_blocked(self):
        for uri in (None, "", "   "):
            row = {"storage_uri": uri, "table_type": "MANAGED"}
            self.assertEqual(verdict(row), mod.ORPHAN, repr(uri))
            _, blocker, suggested = mod.classify(row)
            self.assertEqual(blocker, mod.ORPHAN)
            self.assertIn("Dangling", suggested)


class NonDeltaAndAclFlagTests(unittest.TestCase):
    def test_ready_but_non_delta_external_flagged(self):
        row = {"storage_uri": "gs://bkt/x", "table_type": "EXTERNAL", "table_format": "PARQUET"}
        self.assertEqual(verdict(row), mod.READY)  # ready, but with a caveat action
        _, _, suggested = mod.classify(row)
        self.assertIn("Non-Delta", suggested)
        self.assertIn("PARQUET", suggested)

    def test_ready_with_legacy_acl_flags_grant_rewrite(self):
        row = {"storage_uri": "abfss://c@a.dfs.core.windows.net/x", "table_type": "EXTERNAL",
               "table_format": "DELTA", "acl_mode": "LEGACY_TABLE_ACL"}
        self.assertEqual(verdict(row), mod.READY)  # data ready; grants need re-auth
        _, _, suggested = mod.classify(row)
        self.assertIn("LEGACY_TABLE_ACL", suggested)

    def test_blocked_and_legacy_acl_notes_both(self):
        row = {"storage_uri": "wasbs://c@a.blob.core.windows.net/x", "acl_mode": "LEGACY_TABLE_ACL"}
        self.assertEqual(verdict(row), mod.BLOCKED)
        _, blocker, _ = mod.classify(row)
        self.assertIn("legacy Azure", blocker)
        self.assertIn("LEGACY_TABLE_ACL", blocker)


class CsvOutputTests(unittest.TestCase):
    def test_rows_to_csv_tally_and_header(self):
        import io
        rows = [
            {"table_name": "hive_metastore.s.a", "storage_uri": "s3://b/a", "table_format": "DELTA"},
            {"table_name": "hive_metastore.s.b", "storage_uri": "wasbs://c@a/x"},
            {"table_name": "hive_metastore.s.c", "storage_uri": None},
        ]
        buf = io.StringIO()
        counts = mod.rows_to_csv(rows, buf)
        self.assertEqual(counts, {mod.READY: 1, mod.BLOCKED: 1, mod.ORPHAN: 1})
        out = buf.getvalue()
        self.assertTrue(out.startswith("table_name,storage_uri,scheme,migration_blocker,suggested_action"))
        self.assertIn("hive_metastore.s.a", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
