"""Regression coverage for the Snowflake v2 pack cleanup and npm artifact."""

from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "plugins" / "saas-packs" / "snowflake-pack"
GENERATOR = ROOT / "plugins" / "saas-packs" / "scripts" / "generate-skill-db.py"
STALE_DATABASE = ROOT / "plugins" / "saas-packs" / "skill-databases" / "snowflake"


def load_generator():
    spec = importlib.util.spec_from_file_location("generate_skill_db", GENERATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {GENERATOR}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def npm_pack_files(pack: Path) -> set[str]:
    completed = subprocess.run(
        ["npm", "pack", "--dry-run", "--json"],
        cwd=pack,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)
    if isinstance(payload, list):
        package = payload[0]
    else:
        package = next(iter(payload.values()))
    return {entry["path"] for entry in package["files"]}


class SnowflakePackIntegrityTests(unittest.TestCase):
    def test_pack_has_only_the_research_approved_operator_skills(self) -> None:
        expected = {
            "snowflake-access-guardian",
            "snowflake-cost-leak-hunter",
            "snowflake-data-quality-sentinel",
            "snowflake-deploy-medic",
            "snowflake-failover-readiness-drill",
            "snowflake-governance-coverage-auditor",
            "snowflake-native-app-release-sheriff",
            "snowflake-pipeline-guardian",
            "snowflake-query-forensics",
            "snowflake-strong-auth-migration-pilot",
        }
        actual = {entry.name for entry in (PACK / "skills").iterdir() if entry.is_dir()}
        self.assertEqual(actual, expected)

    def test_retired_database_is_absent(self) -> None:
        self.assertFalse(STALE_DATABASE.exists())

    def test_generator_refuses_to_recreate_retired_snowflake_database(self) -> None:
        generator = load_generator()
        with tempfile.TemporaryDirectory() as temporary_directory:
            working_directory = Path(temporary_directory)
            previous_directory = Path.cwd()
            try:
                # The guard must fire before any output directory is created.
                os.chdir(working_directory)
                with self.assertRaisesRegex(ValueError, "retired for 'Snowflake'"):
                    generator.generate_skill_database("Snowflake", "Snowflake", "flagship+")
            finally:
                os.chdir(previous_directory)

            self.assertFalse((working_directory / "plugins/saas-packs/skill-databases/Snowflake").exists())

    def test_cli_refuses_retired_database_with_actionable_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            completed = subprocess.run(
                ["python3", str(GENERATOR), "snowflake", "Snowflake", "flagship+"],
                cwd=temporary_directory,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 2)
            self.assertIn("generation is retired", completed.stderr)
            self.assertFalse((Path(temporary_directory) / "plugins/saas-packs/skill-databases/snowflake").exists())

    def test_generator_still_supports_non_retired_vendors(self) -> None:
        generator = load_generator()
        with tempfile.TemporaryDirectory() as temporary_directory:
            working_directory = Path(temporary_directory)
            previous_directory = Path.cwd()
            try:
                os.chdir(working_directory)
                generated_count = generator.generate_skill_database("examplevendor", "Example Vendor", "standard")
            finally:
                os.chdir(previous_directory)

            output_directory = working_directory / "plugins/saas-packs/skill-databases/examplevendor"
            self.assertEqual(generated_count, 12)
            self.assertEqual(len(list(output_directory.glob("*.md"))), 12)
            self.assertTrue((output_directory / "examplevendor-skills.csv").is_file())

    def test_npm_artifact_keeps_readme_links_and_excludes_python_caches(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            copied_pack = Path(temporary_directory) / "snowflake-pack"
            shutil.copytree(PACK, copied_pack)

            cache_directory = copied_pack / "skills" / "snowflake-cost-leak-hunter" / "scripts" / "__pycache__"
            cache_directory.mkdir(exist_ok=True)
            (cache_directory / "probe.cpython-312.pyc").write_bytes(b"not-bytecode")
            (cache_directory.parent / "probe.pyo").write_bytes(b"not-bytecode")

            packed_files = npm_pack_files(copied_pack)

        cache_files = {path for path in packed_files if "__pycache__" in path or Path(path).suffix in {".pyc", ".pyo"}}
        self.assertEqual(cache_files, set())

        for document in (PACK / "README.md", PACK / "000-docs" / "000-INDEX.md"):
            relative_links = {
                match
                for match in re.findall(r"\[[^]]+\]\(([^)]+)\)", document.read_text(encoding="utf-8"))
                if not match.startswith(("http://", "https://", "#"))
            }
            self.assertTrue(relative_links, document)
            resolved = {
                (document.parent / match).resolve().relative_to(PACK.resolve()).as_posix() for match in relative_links
            }
            self.assertTrue(resolved.issubset(packed_files), document)
        self.assertIn("000-docs/000-INDEX.md", packed_files)
        self.assertIn("LICENSE", packed_files)
        self.assertIn("shared/snowflake_operator.py", packed_files)
        self.assertTrue(os.access(PACK / "shared" / "snowflake_operator.py", os.X_OK))
        self.assertIn("shared/evidence/collect_snowflake_evidence.py", packed_files)
        self.assertIn("shared/evidence/sql/replication.sql", packed_files)


if __name__ == "__main__":
    unittest.main()
