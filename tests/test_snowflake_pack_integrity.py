"""Regression coverage for the Snowflake v2 pack cleanup and npm artifact."""

from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import subprocess
import tarfile
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "plugins" / "saas-packs" / "snowflake-pack"
GENERATOR = ROOT / "plugins" / "saas-packs" / "scripts" / "generate-skill-db.py"
SYNC_GENERATOR = PACK / "shared" / "evidence" / "sync_bundled_collectors.py"
STALE_DATABASE = ROOT / "plugins" / "saas-packs" / "skill-databases" / "snowflake"


def load_generator():
    spec = importlib.util.spec_from_file_location("generate_skill_db", GENERATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {GENERATOR}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_sync_generator():
    spec = importlib.util.spec_from_file_location("sync_bundled_collectors", SYNC_GENERATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load collector generator from {SYNC_GENERATOR}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def npm_pack_entries(pack: Path) -> dict[str, dict]:
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
    return {entry["path"]: entry for entry in package["files"]}


def npm_pack_files(pack: Path) -> set[str]:
    return set(npm_pack_entries(pack))


class SnowflakePackIntegrityTests(unittest.TestCase):
    def test_curated_evidence_skills_match_packaged_source(self) -> None:
        def packaged_files(root: Path) -> dict[str, Path]:
            return {
                path.relative_to(root).as_posix(): path
                for path in root.rglob("*")
                if path.is_file() and "__pycache__" not in path.parts and path.suffix not in {".pyc", ".pyo"}
            }

        skills = tuple(sorted(path.name for path in (PACK / "skills").iterdir() if path.is_dir()))
        self.assertEqual(len(skills), 10)

        for skill in skills:
            source = PACK / "skills" / skill
            curated = ROOT / "skills" / ".curated" / skill
            source_files = packaged_files(source)
            curated_files = packaged_files(curated)
            self.assertEqual(set(curated_files), set(source_files), skill)
            for relative in sorted(source_files):
                with self.subTest(skill=skill, path=relative):
                    self.assertEqual(curated_files[relative].read_bytes(), source_files[relative].read_bytes())

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

            packed_entries = npm_pack_entries(copied_pack)
            packed_files = set(packed_entries)

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
        self.assertIn("shared/evidence/collect_snowflake_evidence.py", packed_files)
        self.assertIn("shared/snowflake_operator.py", packed_files)
        self.assertEqual(packed_entries["shared/snowflake_operator.py"]["mode"], 0o755)
        operator_targets = {
            "skills/snowflake-pipeline-guardian/scripts/analyze_pipeline_state.py",
            "skills/snowflake-query-forensics/scripts/analyze_query_evidence.py",
            "skills/snowflake-deploy-medic/scripts/analyze_deploy_evidence.py",
            "skills/snowflake-access-guardian/scripts/analyze_access_evidence.py",
            "skills/snowflake-failover-readiness-drill/scripts/analyze_failover_readiness.py",
        }
        self.assertTrue(operator_targets.issubset(packed_files))
        self.assertIn(
            "skills/snowflake-access-guardian/scripts/analyze_access_evidence.py",
            packed_files,
        )
        self.assertIn(
            "skills/snowflake-access-guardian/references/current-evidence-contract.md",
            packed_files,
        )
        self.assertIn(
            "skills/snowflake-strong-auth-migration-pilot/scripts/analyze_auth_evidence.py",
            packed_files,
        )
        self.assertIn(
            "skills/snowflake-strong-auth-migration-pilot/references/current-evidence-contract.md",
            packed_files,
        )
        self.assertIn(
            "skills/snowflake-governance-coverage-auditor/scripts/analyze_governance.py",
            packed_files,
        )
        self.assertIn(
            "skills/snowflake-governance-coverage-auditor/references/input-contract.md",
            packed_files,
        )
        self.assertIn(
            "skills/snowflake-native-app-release-sheriff/scripts/analyze_native_app_release.py",
            packed_files,
        )
        self.assertIn(
            "skills/snowflake-native-app-release-sheriff/references/evidence-contract.md",
            packed_files,
        )
        sync_generator = load_sync_generator()
        expected_canonical_sql = {
            f"shared/evidence/sql/{filename}" for filenames in sync_generator.BUNDLES.values() for filename in filenames
        }
        actual_canonical_sql = {
            path for path in packed_files if path.startswith("shared/evidence/sql/") and path.endswith(".sql")
        }
        self.assertEqual(actual_canonical_sql, expected_canonical_sql)
        expected_collectors = {
            f"skills/{skill}/scripts/collect_snowflake_evidence.py" for skill in sync_generator.BUNDLES
        }
        actual_collectors = {path for path in packed_files if path.endswith("/scripts/collect_snowflake_evidence.py")}
        self.assertEqual(actual_collectors, expected_collectors)
        expected_bundle_sql = {
            f"skills/{skill}/scripts/sql/{filename}"
            for skill, filenames in sync_generator.BUNDLES.items()
            for filename in filenames
        }
        actual_bundle_sql = {
            path
            for path in packed_files
            if path.startswith(tuple(f"skills/{skill}/scripts/sql/" for skill in sync_generator.BUNDLES))
            and path.endswith(".sql")
        }
        self.assertEqual(actual_bundle_sql, expected_bundle_sql)
        for skill, filenames in sync_generator.BUNDLES.items():
            for filename in filenames:
                self.assertIn(f"skills/{skill}/scripts/sql/{filename}", packed_files)
        self.assertFalse(
            any(
                ".rollback." in path or re.search(r"/\.(?:collect_snowflake_evidence\.py|[^/]+\.sql)\.", path)
                for path in packed_files
            )
        )

    def test_packed_operator_is_executable_and_standalone(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            packed = subprocess.run(
                ["npm", "pack", "--json", "--pack-destination", str(root)],
                cwd=PACK,
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(packed.stdout)
            package = payload[0] if isinstance(payload, list) else next(iter(payload.values()))
            archive = root / package["filename"]
            extract_root = root / "extracted"
            extract_root.mkdir()
            with tarfile.open(archive, "r:gz") as bundle:
                member = bundle.getmember("package/shared/snowflake_operator.py")
                self.assertEqual(member.mode, 0o755)
                operator_targets = {
                    "package/skills/snowflake-pipeline-guardian/scripts/analyze_pipeline_state.py",
                    "package/skills/snowflake-query-forensics/scripts/analyze_query_evidence.py",
                    "package/skills/snowflake-deploy-medic/scripts/analyze_deploy_evidence.py",
                    "package/skills/snowflake-access-guardian/scripts/analyze_access_evidence.py",
                    "package/skills/snowflake-failover-readiness-drill/scripts/analyze_failover_readiness.py",
                }
                for target in operator_targets:
                    self.assertFalse(bundle.getmember(target).issym())
                bundle.extractall(extract_root, filter="data")

            operator = extract_root / "package" / "shared" / "snowflake_operator.py"
            self.assertEqual(operator.stat().st_mode & 0o777, 0o755)
            completed = subprocess.run(
                [str(operator), "list"],
                cwd=root,
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("query-id-forensics", completed.stdout)
            self.assertEqual(completed.stderr, "")

            pipeline_fixture = (
                extract_root / "package/skills/snowflake-pipeline-guardian/scripts/fixtures/stale-chain.json"
            )
            analysis = subprocess.run(
                [str(operator), "pipeline-triage", f"--input={pipeline_fixture}"],
                cwd=root,
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )
            self.assertEqual(analysis.returncode, 0, analysis.stderr)
            self.assertEqual(json.loads(analysis.stdout)["schema_version"], "2")
            self.assertEqual(analysis.stderr, "")


if __name__ == "__main__":
    unittest.main()
