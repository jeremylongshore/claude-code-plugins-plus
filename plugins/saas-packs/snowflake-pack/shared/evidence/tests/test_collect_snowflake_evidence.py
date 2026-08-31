from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
SCRIPT = HERE.parent / "collect_snowflake_evidence.py"
SPEC = importlib.util.spec_from_file_location("collect_snowflake_evidence", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class CollectorTests(unittest.TestCase):
    def test_installed_skills_bundle_the_canonical_collector(self) -> None:
        canonical = SCRIPT.read_bytes()
        canonical_sql = {path.name: path.read_bytes() for path in sorted((SCRIPT.parent / "sql").glob("*.sql"))}
        expected_sql = {
            "snowflake-access-guardian": "access.sql",
            "snowflake-cost-leak-hunter": "cost.sql",
            "snowflake-data-quality-sentinel": "data-quality.sql",
            "snowflake-deploy-medic": "query.sql",
            "snowflake-failover-readiness-drill": "replication.sql",
            "snowflake-pipeline-guardian": "pipeline.sql",
            "snowflake-query-forensics": "query.sql",
            "snowflake-strong-auth-migration-pilot": "auth.sql",
        }
        skills_dir = SCRIPT.parents[2] / "skills"
        bundled = sorted(skills_dir.glob("*/scripts/collect_snowflake_evidence.py"))
        self.assertEqual(len(bundled), 8)
        for path in bundled:
            with self.subTest(skill=path.parents[1].name):
                self.assertEqual(path.read_bytes(), canonical)
                bundled_sql = {item.name: item.read_bytes() for item in sorted((path.parent / "sql").glob("*.sql"))}
                filename = expected_sql[path.parents[1].name]
                self.assertEqual(bundled_sql, {filename: canonical_sql[filename]})

    def test_all_tracked_surfaces_pass_read_only_gate(self) -> None:
        for surface in MODULE.SURFACES:
            with self.subTest(surface=surface):
                path, sql, sources = MODULE.load_surface(surface)
                self.assertTrue(path.is_file())
                self.assertTrue(sources)
                MODULE.validate_read_only_sql(sql)
                for source in sources:
                    self.assertIn(source, sql)

    def test_reviewed_templates_do_not_reintroduce_nonexistent_columns(self) -> None:
        rejected = {
            "auth": {"DEFAULT_SECONDARY_ROLES"},
            "data-quality": {"EXPECTATION_EVALUATION_ERROR"},
            "replication": {
                "REPLICATION_GROUP_TYPE",
                "CREDITS_USED",
                "BYTES_TRANSFERRED",
                "SOURCE_ACCOUNT_NAME",
                "SOURCE_REGION",
                "TARGET_ACCOUNT_NAME",
                "TARGET_REGION",
            },
        }
        for surface, columns in rejected.items():
            _, sql, _ = MODULE.load_surface(surface)
            for column in columns:
                with self.subTest(surface=surface, column=column):
                    self.assertNotRegex(sql, rf"\b{column}\b")

    def test_gate_rejects_mutation_and_session_changes(self) -> None:
        for sql in (
            "ALTER WAREHOUSE X SUSPEND",
            "WITH rows AS (SELECT 1) DELETE FROM t",
            "SELECT 1; GRANT ROLE x TO USER y",
            "/* harmless */ USE ROLE ACCOUNTADMIN",
            "SELECT 1; CALL SYSTEM$WAIT(1)",
        ):
            with self.subTest(sql=sql), self.assertRaises(MODULE.CollectionError):
                MODULE.validate_read_only_sql(sql)
        MODULE.validate_read_only_sql("SELECT 'ALTER TABLE x' AS inert_text")

    def test_normalizer_groups_rows_deterministically(self) -> None:
        raw = [
            {"EVIDENCE": {"_dataset": "queries", "id": "b", "value": 2}},
            {"EVIDENCE": {"_dataset": "queries", "id": "a", "value": 1}},
            {"EVIDENCE": {"_dataset": "warehouses", "id": "w"}},
        ]
        datasets, count = MODULE.normalize_cli_json(raw)
        self.assertEqual(count, 3)
        self.assertEqual(list(datasets), ["queries", "warehouses"])
        self.assertEqual([row["id"] for row in datasets["queries"]], ["a", "b"])

    def test_normalizer_rejects_credentials_and_malformed_rows(self) -> None:
        for raw in (
            [{"EVIDENCE": {"_dataset": "x", "oauth_token": "never"}}],
            [{"EVIDENCE": {"_dataset": "x", "note": "password=hunter2"}}],
            [{"EVIDENCE": {"_dataset": "x", "query_text": "select customer_email"}}],
            [{"EVIDENCE": {"_dataset": "x", "note": "https://x.test/file?X-Amz-Signature=abc"}}],
            [{"EVIDENCE": {"_dataset": "query_history", "query_tag": "tenant=raw"}}],
            [{"EVIDENCE": []}],
            ["not-an-object"],
        ):
            with self.subTest(raw=raw), self.assertRaises(MODULE.CollectionError):
                MODULE.normalize_cli_json(raw)
        datasets, _ = MODULE.normalize_cli_json([{"EVIDENCE": {"_dataset": "users", "has_password": True}}])
        self.assertTrue(datasets["users"][0]["has_password"])

    def test_relevant_sql_surfaces_are_deterministically_ordered(self) -> None:
        for surface in ("cost", "query", "pipeline"):
            with self.subTest(surface=surface):
                _, sql, _ = MODULE.load_surface(surface)
                self.assertIn("ORDER BY dataset, sort_key", sql)

    def test_receipt_exposes_limit_and_possible_truncation(self) -> None:
        path, sql, sources = MODULE.load_surface("query")
        del path
        del sources
        raw = [{"EVIDENCE": {"_dataset": "query_history", "query_id": str(index)}} for index in range(1000)]
        receipt = MODULE.build_receipt("query", "readonly", sql, ["QUERY_HISTORY"], raw=raw)
        self.assertEqual(receipt["row_limit"], 1000)
        self.assertTrue(receipt["truncation_possible"])

    def test_runner_uses_profile_only_and_emits_provenance(self) -> None:
        captured = {}

        def runner(command, **kwargs):
            captured["command"] = command
            captured["kwargs"] = kwargs
            return subprocess.CompletedProcess(
                command,
                0,
                stdout=json.dumps([{"EVIDENCE": {"_dataset": "query_history", "query_id": "01a"}}]),
                stderr="",
            )

        receipt, code = MODULE.execute_surface("query", "readonly-profile", runner=runner)
        self.assertEqual(code, 0)
        self.assertEqual(receipt["status"], "collected")
        self.assertEqual(receipt["row_count"], 1)
        self.assertRegex(receipt["sql_sha256"], r"^sha256:[0-9a-f]{64}$")
        self.assertRegex(receipt["receipt_sha256"], r"^sha256:[0-9a-f]{64}$")
        command = captured["command"]
        self.assertEqual(command[:2], ["snow", "sql"])
        self.assertIn("--connection", command)
        self.assertIn("--local-only", command)
        self.assertFalse(any(flag in command for flag in ("--password", "--token", "--private-key-file")))
        self.assertEqual(captured["kwargs"]["timeout"], 120)

    def test_failed_collection_is_sanitized_and_still_receipted(self) -> None:
        def runner(command, **kwargs):
            return subprocess.CompletedProcess(command, 5, stdout="", stderr="token=rawsecret permission denied")

        receipt, code = MODULE.execute_surface("cost", "readonly", runner=runner)
        self.assertEqual(code, 5)
        self.assertEqual(receipt["status"], "error")
        rendered = json.dumps(receipt)
        self.assertNotIn("rawsecret", rendered)
        self.assertIn("[REDACTED_CREDENTIAL]", rendered)
        self.assertEqual(receipt["row_count"], 0)

    def test_cli_offline_normalization_writes_atomically(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "raw.json"
            output = root / "receipt.json"
            source.write_text(
                json.dumps([{"EVIDENCE": {"_dataset": "query_history", "query_id": "01a"}}]),
                encoding="utf-8",
            )
            completed = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    "--surface",
                    "query",
                    "--input-json",
                    str(source),
                    "--output",
                    str(output),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            receipt = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(receipt["datasets"]["query_history"][0]["query_id"], "01a")
            self.assertFalse((root / ".receipt.json.tmp").exists())


if __name__ == "__main__":
    unittest.main()
