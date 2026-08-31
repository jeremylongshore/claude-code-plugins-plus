from __future__ import annotations

import importlib.util
import shutil
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
SCRIPT = HERE.parent / "sync_bundled_collectors.py"
SPEC = importlib.util.spec_from_file_location("sync_bundled_collectors", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class CollectorBundleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name) / "snowflake-pack"
        shared = self.root / "shared" / "evidence"
        shutil.copytree(MODULE.PACK_ROOT / "shared" / "evidence", shared)
        (self.root / "skills").mkdir()

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_repository_tree_passes_and_has_exact_bundle_count(self) -> None:
        self.assertEqual(MODULE.check_tree(MODULE.PACK_ROOT), [])
        self.assertEqual(len(MODULE.BUNDLES), 8)

    def test_writer_reconstructs_self_contained_copies(self) -> None:
        MODULE.write_tree(self.root)
        self.assertEqual(MODULE.check_tree(self.root), [])
        canonical = (self.root / MODULE.CANONICAL_COLLECTOR).read_bytes()
        for skill, filename in MODULE.BUNDLES.items():
            skill_root = self.root / MODULE.SKILLS_DIR / skill / "scripts"
            self.assertEqual((skill_root / "collect_snowflake_evidence.py").read_bytes(), canonical)
            self.assertEqual(
                (skill_root / "sql" / filename).read_bytes(),
                (self.root / MODULE.CANONICAL_SQL / filename).read_bytes(),
            )

    def test_check_fails_closed_on_missing_extra_and_drift(self) -> None:
        MODULE.write_tree(self.root)
        cost = self.root / MODULE.SKILLS_DIR / "snowflake-cost-leak-hunter" / "scripts"

        (cost / "sql" / "cost.sql").unlink()
        (cost / "sql" / "unexpected.sql").write_text("SELECT 1;\n", encoding="utf-8")
        (cost / "collect_snowflake_evidence.py").write_bytes(b"drift\n")

        issues = MODULE.check_tree(self.root)
        rendered = "\n".join(issues)
        self.assertIn("missing bundled SQL template", rendered)
        self.assertIn("unexpected bundled SQL", rendered)
        self.assertIn("bundled collector drifts from canonical source", rendered)

    def test_check_fails_closed_on_unexpected_skill_and_template(self) -> None:
        MODULE.write_tree(self.root)
        (self.root / "skills" / "snowflake-unregistered").mkdir()
        (self.root / MODULE.CANONICAL_SQL / "unreviewed.sql").write_text("SELECT 1;\n", encoding="utf-8")

        issues = MODULE.check_tree(self.root)
        rendered = "\n".join(issues)
        self.assertIn("unexpected Snowflake skill entry", rendered)
        self.assertIn("unexpected canonical SQL entry", rendered)

    def test_check_fails_closed_on_missing_bundle_directory(self) -> None:
        MODULE.write_tree(self.root)
        shutil.rmtree(
            self.root
            / MODULE.SKILLS_DIR
            / "snowflake-query-forensics"
            / "scripts"
            / "sql"
        )

        issues = MODULE.check_tree(self.root)
        self.assertTrue(any("missing bundled SQL directory" in issue for issue in issues))

    def test_check_rejects_symlinked_bundle_files(self) -> None:
        MODULE.write_tree(self.root)
        access = self.root / MODULE.SKILLS_DIR / "snowflake-access-guardian" / "scripts"
        collector = access / "collect_snowflake_evidence.py"
        collector.unlink()
        collector.symlink_to(self.root / MODULE.CANONICAL_COLLECTOR)

        issues = MODULE.check_tree(self.root)
        self.assertTrue(any("must be a regular file, not a symlink" in issue for issue in issues))


if __name__ == "__main__":
    unittest.main()
