from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock
from pathlib import Path


HERE = Path(__file__).resolve().parent
SCRIPT = HERE.parent / "sync_bundled_collectors.py"
SPEC = importlib.util.spec_from_file_location("sync_bundled_collectors", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def snapshot(root: Path, *, include_mtime: bool = True) -> dict[str, tuple[str, int, int, bytes]]:
    result = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        kind = "symlink" if path.is_symlink() else "directory" if path.is_dir() else "file"
        payload = path.read_bytes() if kind == "file" else b""
        mtime = path.stat().st_mtime_ns if include_mtime else 0
        result[relative] = (kind, path.stat().st_mode & 0o777, mtime, payload)
    return result


class CollectorBundleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name) / "snowflake-pack"
        canonical = MODULE.PACK_ROOT / MODULE.CANONICAL_COLLECTOR
        canonical_sql = MODULE.PACK_ROOT / MODULE.CANONICAL_SQL
        shared = self.root / MODULE.SHARED_EVIDENCE
        (shared / "sql").mkdir(parents=True)
        shutil.copy2(canonical, shared / canonical.name)
        for source in canonical_sql.iterdir():
            shutil.copy2(source, shared / "sql" / source.name)
        for skill in MODULE.BUNDLES:
            scripts = self.root / "skills" / skill / "scripts"
            (scripts / "sql").mkdir(parents=True)
            (scripts.parent / "SKILL.md").write_text(f"# {skill}\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_repository_tree_passes_and_has_exact_bundle_count(self) -> None:
        self.assertEqual(MODULE.check_tree(MODULE.PACK_ROOT), [])
        self.assertEqual(len(MODULE.BUNDLES), 8)

    def test_writer_reconstructs_only_registered_files_and_preserves_modes(self) -> None:
        unrelated = self.root / "skills" / "snowflake-distinct-contract"
        unrelated.mkdir()
        marker = unrelated / "SKILL.md"
        marker.write_text("unchanged\n", encoding="utf-8")

        MODULE.write_tree(self.root)

        self.assertEqual(MODULE.check_tree(self.root), [])
        self.assertEqual(marker.read_text(encoding="utf-8"), "unchanged\n")
        canonical = self.root / MODULE.CANONICAL_COLLECTOR
        for skill, filenames in MODULE.BUNDLES.items():
            scripts = self.root / MODULE.SKILLS_DIR / skill / "scripts"
            bundled = scripts / "collect_snowflake_evidence.py"
            self.assertEqual(bundled.read_bytes(), canonical.read_bytes())
            self.assertEqual(bundled.stat().st_mode & 0o777, canonical.stat().st_mode & 0o777)
            for filename in filenames:
                source = self.root / MODULE.CANONICAL_SQL / filename
                destination = scripts / "sql" / filename
                self.assertEqual(destination.read_bytes(), source.read_bytes())
                self.assertEqual(destination.stat().st_mode & 0o777, source.stat().st_mode & 0o777)

    def test_default_check_is_non_mutating(self) -> None:
        MODULE.write_tree(self.root)
        before = snapshot(self.root)

        completed = subprocess.run(
            ["python3", str(SCRIPT), "--root", str(self.root)],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(snapshot(self.root), before)

    def test_check_fails_closed_with_hashes_on_missing_extra_and_drift(self) -> None:
        MODULE.write_tree(self.root)
        cost = self.root / MODULE.SKILLS_DIR / "snowflake-cost-leak-hunter" / "scripts"
        (cost / "sql" / "cost.sql").unlink()
        (cost / "sql" / "unexpected.sql").write_text("SELECT 1;\n", encoding="utf-8")
        (cost / "collect_snowflake_evidence.py").write_bytes(b"drift\n")
        before = snapshot(self.root)

        rendered = "\n".join(MODULE.check_tree(self.root))

        self.assertIn("missing bundled SQL entry", rendered)
        self.assertIn("unexpected bundled SQL entry", rendered)
        self.assertIn("bundled collector (snowflake-cost-leak-hunter) drifts", rendered)
        self.assertIn("canonical sha256:", rendered)
        self.assertIn("bundled sha256:", rendered)
        completed = subprocess.run(
            ["python3", str(SCRIPT), "--check", "--root", str(self.root)],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 1)
        self.assertIn("canonical sha256:", completed.stderr)
        self.assertEqual(snapshot(self.root), before)

    def test_check_rejects_orphan_template_and_unregistered_collector(self) -> None:
        MODULE.write_tree(self.root)
        (self.root / MODULE.CANONICAL_SQL / "unreviewed.sql").write_text("SELECT 1;\n", encoding="utf-8")
        scripts = self.root / "skills" / "snowflake-unregistered" / "scripts"
        scripts.mkdir(parents=True)
        (scripts / "collect_snowflake_evidence.py").write_text("# copy\n", encoding="utf-8")

        rendered = "\n".join(MODULE.check_tree(self.root))

        self.assertIn("unexpected canonical SQL entry", rendered)
        self.assertIn("unregistered shared collector copy", rendered)

    def test_writer_refuses_missing_skill_structure(self) -> None:
        shutil.rmtree(self.root / MODULE.SKILLS_DIR / "snowflake-query-forensics" / "scripts")

        with self.assertRaisesRegex(ValueError, "missing scripts directory"):
            MODULE.write_tree(self.root)
        self.assertFalse((self.root / MODULE.SKILLS_DIR / "snowflake-query-forensics" / "scripts").exists())

    def test_writer_refuses_missing_skill_definition(self) -> None:
        skill = self.root / MODULE.SKILLS_DIR / "snowflake-access-guardian"
        (skill / "SKILL.md").unlink()

        with self.assertRaisesRegex(ValueError, "missing skill definition"):
            MODULE.write_tree(self.root)
        self.assertFalse((skill / "scripts" / "collect_snowflake_evidence.py").exists())

    def test_writer_refuses_missing_sql_directory(self) -> None:
        scripts = self.root / MODULE.SKILLS_DIR / "snowflake-pipeline-guardian" / "scripts"
        shutil.rmtree(scripts / "sql")

        with self.assertRaisesRegex(ValueError, "missing bundled SQL directory"):
            MODULE.write_tree(self.root)
        self.assertFalse((scripts / "collect_snowflake_evidence.py").exists())

    def test_check_rejects_symlinked_source_and_destination(self) -> None:
        if not hasattr(os, "symlink"):
            self.skipTest("symlinks are unavailable")
        MODULE.write_tree(self.root)
        access = self.root / MODULE.SKILLS_DIR / "snowflake-access-guardian" / "scripts"
        bundled = access / "collect_snowflake_evidence.py"
        bundled.unlink()
        bundled.symlink_to(self.root / MODULE.CANONICAL_COLLECTOR)
        source = self.root / MODULE.CANONICAL_SQL / "auth.sql"
        source.unlink()
        source.symlink_to(self.root / MODULE.CANONICAL_SQL / "access.sql")

        rendered = "\n".join(MODULE.check_tree(self.root))

        self.assertIn("projection path component must not be a symlink", rendered)
        with self.assertRaisesRegex(ValueError, "path component must not be a symlink"):
            MODULE.write_tree(self.root)

    def test_check_rejects_symlinked_parent_component(self) -> None:
        if not hasattr(os, "symlink"):
            self.skipTest("symlinks are unavailable")
        MODULE.write_tree(self.root)
        evidence = self.root / "shared" / "evidence"
        real_evidence = self.root / "shared" / "evidence-real"
        evidence.rename(real_evidence)
        evidence.symlink_to(real_evidence, target_is_directory=True)

        rendered = "\n".join(MODULE.check_tree(self.root))

        self.assertIn("projection path component must not be a symlink", rendered)
        with self.assertRaisesRegex(ValueError, "path component must not be a symlink"):
            MODULE.write_tree(self.root)

    def test_check_rejects_dangling_symlink_component(self) -> None:
        if not hasattr(os, "symlink"):
            self.skipTest("symlinks are unavailable")
        scripts = self.root / MODULE.SKILLS_DIR / "snowflake-pipeline-guardian" / "scripts"
        (scripts / "sql").rmdir()
        (scripts / "sql").symlink_to(self.root / "missing-sql", target_is_directory=True)

        rendered = "\n".join(MODULE.check_tree(self.root))

        self.assertIn("projection path component must not be a symlink", rendered)
        with self.assertRaisesRegex(ValueError, "path component must not be a symlink"):
            MODULE.write_tree(self.root)

    def test_check_rejects_mode_drift(self) -> None:
        MODULE.write_tree(self.root)
        bundled = (
            self.root / MODULE.SKILLS_DIR / "snowflake-access-guardian" / "scripts" / "collect_snowflake_evidence.py"
        )
        bundled.chmod(0o755)

        rendered = "\n".join(MODULE.check_tree(self.root))

        self.assertIn("mode drifts from canonical source", rendered)

    def test_write_failure_rolls_back_every_projection(self) -> None:
        MODULE.write_tree(self.root)
        canonical = self.root / MODULE.CANONICAL_COLLECTOR
        canonical.write_bytes(canonical.read_bytes() + b"\n# reviewed update\n")
        before = snapshot(self.root, include_mtime=False)
        real_replace = MODULE._replace
        for failure_call in (1, 17, 32):
            calls = 0

            def fail_selected_replace(source, destination):
                nonlocal calls
                calls += 1
                if calls == failure_call:
                    raise OSError(f"injected rename failure {failure_call}")
                return real_replace(source, destination)

            with self.subTest(failure_call=failure_call):
                with mock.patch.object(MODULE, "_replace", side_effect=fail_selected_replace):
                    with self.assertRaisesRegex(OSError, f"injected rename failure {failure_call}"):
                        MODULE.write_tree(self.root)
                self.assertEqual(snapshot(self.root, include_mtime=False), before)

    def test_stage_failure_changes_no_projection(self) -> None:
        MODULE.write_tree(self.root)
        canonical = self.root / MODULE.CANONICAL_COLLECTOR
        canonical.write_bytes(canonical.read_bytes() + b"\n# reviewed update\n")
        before = snapshot(self.root, include_mtime=False)
        real_stage_file = MODULE._stage_file
        for failure_call in (1, 8, 16):
            calls = 0

            def fail_selected_stage(destination, payload, mode):
                nonlocal calls
                calls += 1
                if calls == failure_call:
                    raise OSError(f"injected stage failure {failure_call}")
                return real_stage_file(destination, payload, mode)

            with self.subTest(failure_call=failure_call):
                with mock.patch.object(MODULE, "_stage_file", side_effect=fail_selected_stage):
                    with self.assertRaisesRegex(OSError, f"injected stage failure {failure_call}"):
                        MODULE.write_tree(self.root)
                self.assertEqual(snapshot(self.root, include_mtime=False), before)

    def test_registry_matches_collector_surface_templates(self) -> None:
        collector_script = HERE.parent / "collect_snowflake_evidence.py"
        collector_spec = importlib.util.spec_from_file_location("collect_snowflake_evidence", collector_script)
        assert collector_spec and collector_spec.loader
        collector = importlib.util.module_from_spec(collector_spec)
        collector_spec.loader.exec_module(collector)

        registered = {filename for filenames in MODULE.BUNDLES.values() for filename in filenames}
        contracts = {**collector.SURFACES, **getattr(collector, "SUBSURFACES", {})}
        surfaced = {contract[0] for contract in contracts.values()}
        self.assertEqual(registered, surfaced)
        self.assertEqual(registered, {path.name for path in (MODULE.PACK_ROOT / MODULE.CANONICAL_SQL).iterdir()})
        for filename in registered:
            collector.validate_read_only_sql(
                (MODULE.PACK_ROOT / MODULE.CANONICAL_SQL / filename).read_text(encoding="utf-8")
            )

    def test_registry_rejects_path_tokens(self) -> None:
        with mock.patch.dict(MODULE.BUNDLES, {"../escape": ("../escape.sql",)}, clear=True):
            rendered = "\n".join(MODULE.check_tree(self.root))
        self.assertIn("invalid Snowflake skill token", rendered)
        self.assertIn("invalid SQL filename token", rendered)

    def test_generator_has_no_dynamic_or_subprocess_execution_path(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("import subprocess", source)
        self.assertNotIn("from subprocess", source)
        tree = __import__("ast").parse(source)
        self.assertFalse(
            any(
                isinstance(node, __import__("ast").Call)
                and isinstance(node.func, __import__("ast").Name)
                and node.func.id in {"eval", "exec"}
                for node in __import__("ast").walk(tree)
            )
        )

    def test_check_never_executes_canonical_top_level_payloads(self) -> None:
        MODULE.write_tree(self.root)
        collector = self.root / MODULE.CANONICAL_COLLECTOR
        direct_marker = self.root / "direct-execution-marker"
        subprocess_marker = self.root / "subprocess-execution-marker"
        collector.write_text(
            collector.read_text(encoding="utf-8")
            + f"\nPath({str(direct_marker)!r}).write_text('executed', encoding='utf-8')\n"
            + f"__import__('subprocess').run(['touch', {str(subprocess_marker)!r}], check=True)\n",
            encoding="utf-8",
        )

        before = snapshot(self.root)
        issues = MODULE.check_tree(self.root)

        self.assertTrue(issues)
        self.assertFalse(direct_marker.exists())
        self.assertFalse(subprocess_marker.exists())
        self.assertEqual(snapshot(self.root), before)

    def test_check_applies_literal_collector_sql_policy_without_execution(self) -> None:
        MODULE.write_tree(self.root)
        cost_sql = self.root / MODULE.CANONICAL_SQL / "cost.sql"
        cost_sql.write_text(
            cost_sql.read_text(encoding="utf-8").replace("SELECT", "DELETE", 1),
            encoding="utf-8",
        )

        rendered = "\n".join(MODULE.check_tree(self.root))

        self.assertIn("canonical SQL safety validation failed (cost.sql)", rendered)
        self.assertIn("forbidden statement tokens", rendered)


if __name__ == "__main__":
    unittest.main()
