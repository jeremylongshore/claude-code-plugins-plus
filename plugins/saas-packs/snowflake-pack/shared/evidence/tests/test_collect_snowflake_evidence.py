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
SYNC_SCRIPT = HERE.parent / "sync_bundled_collectors.py"
SYNC_SPEC = importlib.util.spec_from_file_location("sync_bundled_collectors", SYNC_SCRIPT)
assert SYNC_SPEC and SYNC_SPEC.loader
SYNC_MODULE = importlib.util.module_from_spec(SYNC_SPEC)
SYNC_SPEC.loader.exec_module(SYNC_MODULE)


class CollectorTests(unittest.TestCase):
    def test_installed_skills_bundle_the_canonical_collector(self) -> None:
        canonical = SCRIPT.read_bytes()
        canonical_sql = {path.name: path.read_bytes() for path in sorted((SCRIPT.parent / "sql").glob("*.sql"))}
        skills_dir = SCRIPT.parents[2] / "skills"
        bundled = sorted(skills_dir.glob("*/scripts/collect_snowflake_evidence.py"))
        self.assertEqual(len(bundled), 8)
        for path in bundled:
            with self.subTest(skill=path.parents[1].name):
                self.assertEqual(path.read_bytes(), canonical)
                bundled_sql = {item.name: item.read_bytes() for item in sorted((path.parent / "sql").glob("*.sql"))}
                filenames = SYNC_MODULE.BUNDLES[path.parents[1].name]
                self.assertEqual(bundled_sql, {filename: canonical_sql[filename] for filename in filenames})

    def test_all_tracked_surfaces_pass_read_only_gate(self) -> None:
        for surface in {**MODULE.SURFACES, **MODULE.SUBSURFACES}:
            with self.subTest(surface=surface):
                query_id = "01abc-example" if surface in {"query-operator-stats", "query-insights"} else None
                database = "ANALYTICS" if surface == "access-future" else None
                path, template_sql, sql, sources, _ = MODULE.render_surface(
                    surface,
                    query_id=query_id,
                    database=database,
                )
                self.assertTrue(path.is_file())
                self.assertTrue(sources)
                if template_sql != sql:
                    self.assertNotIn("__QUERY_ID__", sql)
                    self.assertNotIn("__DATABASE_IDENTIFIER__", sql)
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

    def test_current_state_show_surfaces_export_only_safe_pipe_projections(self) -> None:
        auth = MODULE.load_surface("auth-current")[1]
        pipeline = MODULE.load_surface("pipeline-current")[1]
        replication = MODULE.load_surface("replication-current")[1]
        self.assertIn("SHOW USERS\n->> SELECT OBJECT_CONSTRUCT_KEEP_NULL", auth)
        self.assertIn("'user_name_sha256', SHA2", auth)
        self.assertNotIn("SHOW USERS LIMIT", auth)
        self.assertIn("SHOW TASKS IN ACCOUNT\n->> SELECT OBJECT_CONSTRUCT_KEEP_NULL", pipeline)
        self.assertIn("SHOW REPLICATION GROUPS\n->> SELECT OBJECT_CONSTRUCT_KEEP_NULL", replication)
        self.assertNotIn("RESULT_SCAN", pipeline)
        self.assertNotIn("RESULT_SCAN", replication)
        projected = MODULE.strip_sql_comments_and_strings(pipeline + replication)
        for forbidden in (
            "allowed_accounts",
            "account_locator",
            "owner",
            "DETAILS",
            "definition",
            "notification_channel",
        ):
            with self.subTest(field=forbidden):
                self.assertNotIn(forbidden, projected)
        data_quality = MODULE.strip_sql_comments_and_strings(MODULE.load_surface("data-quality-current")[1]).upper()
        self.assertNotIn("WITHIN_GROUP", data_quality)
        self.assertNotRegex(data_quality, r"\bFILTER\b")
        auth_projection = MODULE.strip_sql_comments_and_strings(auth).casefold()
        for forbidden in (
            "login_name",
            "display_name",
            "first_name",
            "last_name",
            "email",
            "comment",
            "default_namespace",
            "default_warehouse",
            "default_role",
        ):
            with self.subTest(auth_field=forbidden):
                self.assertNotIn(forbidden, auth_projection)

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

    def test_auth_current_rejects_raw_show_users_fields(self) -> None:
        raw_show_row = {
            "EVIDENCE": {
                "_dataset": "current_users",
                "user_name_sha256": "a" * 64,
                "email": "person@example.com",
                "login_name": "person",
                "display_name": "Person Name",
                "comment": "customer metadata",
            }
        }
        with self.assertRaises(MODULE.CollectionError):
            MODULE.normalize_cli_json([raw_show_row], surface="auth-current")
        safe = {
            "EVIDENCE": {
                "_dataset": "current_users",
                "user_name_sha256": "a" * 64,
                "disabled": False,
                "type": "PERSON",
                "has_password": True,
            }
        }
        datasets, _ = MODULE.normalize_cli_json([safe], surface="auth-current")
        self.assertEqual(datasets["current_users"][0]["user_name_sha256"], "a" * 64)

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

    def test_receipt_detects_aggregate_multi_dataset_limit(self) -> None:
        raw = [{"EVIDENCE": {"_dataset": "queries", "id": str(index)}} for index in range(500)] + [
            {"EVIDENCE": {"_dataset": "warehouses", "id": str(index)}} for index in range(500)
        ]
        receipt = MODULE.build_receipt("query", "readonly", "SELECT 1 LIMIT 1000", ["QUERY_HISTORY"], raw=raw)
        self.assertTrue(receipt["truncation_possible"])
        self.assertFalse(any(receipt["dataset_truncation_possible"].values()))

    def test_account_wide_pipeline_show_queries_are_bounded(self) -> None:
        sql = MODULE.load_surface("pipeline-current")[1]
        self.assertEqual(len(__import__("re").findall(r"\bLIMIT\s+10000\b", sql)), 4)

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

    def test_selector_subsurfaces_reject_sql_fragments(self):
        for value in ("01abc'; DROP TABLE X;--", "01abc\nSELECT 1", "' OR '1'='1"):
            with self.subTest(value=value), self.assertRaises(MODULE.CollectionError):
                MODULE.render_surface("query-operator-stats", query_id=value)
        for value in ("ANALYTICS.PUBLIC; DROP TABLE X", "db.schema", "'quoted'"):
            with self.subTest(value=value), self.assertRaises(MODULE.CollectionError):
                MODULE.render_surface("access-future", database=value)
        with self.assertRaises(MODULE.CollectionError):
            MODULE.render_surface("query-operator-stats")

    def test_dynamic_selector_receipt_preserves_template_and_rendered_provenance(self):
        path, template, rendered, sources, selector = MODULE.render_surface("query-insights", query_id="01abc-example")
        self.assertNotEqual(template, rendered)
        self.assertIn("01abc-example", rendered)
        receipt = MODULE.build_receipt(
            "query-insights",
            "readonly",
            rendered,
            sources,
            raw=[],
            template_sql=template,
            template_path=path,
            selector=selector,
        )
        self.assertEqual(receipt["sql_sha256"], receipt["template_sha256"])
        self.assertNotEqual(receipt["template_sha256"], receipt["rendered_sql_sha256"])
        self.assertRegex(receipt["selector_fingerprint"], r"^sha256:[0-9a-f]{64}$")
        self.assertEqual(receipt["source_metadata"]["template"], "query-insights.sql")
        self.assertEqual(receipt["source_metadata"]["selector"], {"query_id": True})
        self.assertNotIn("01abc-example", json.dumps(receipt["source_metadata"]))

    def test_dynamic_runner_removes_rendered_selector_file(self):
        captured = {}

        def runner(command, **kwargs):
            captured["path"] = Path(command[3])
            captured["sql"] = captured["path"].read_text(encoding="utf-8")
            return subprocess.CompletedProcess(command, 0, stdout="[]", stderr="")

        receipt, code = MODULE.execute_surface(
            "query-operator-stats", "readonly-profile", query_id="01abc-example", runner=runner
        )
        self.assertEqual(code, 0)
        self.assertIn("01abc-example", captured["sql"])
        self.assertFalse(captured["path"].exists())
        self.assertNotEqual(captured["path"].parent, MODULE.SQL_DIR)
        self.assertEqual(receipt["source_metadata"]["selector"], {"query_id": True})
        self.assertNotIn("01abc-example", json.dumps(receipt["source_metadata"]))

    def test_dynamic_collection_never_mutates_package_tree_on_failure_timeout_or_bad_json(self):
        before = {path.name: path.read_bytes() for path in MODULE.SQL_DIR.iterdir()}

        def failing(command, **kwargs):
            self.assertNotEqual(Path(command[3]).parent, MODULE.SQL_DIR)
            return subprocess.CompletedProcess(command, 7, stdout="", stderr="permission denied")

        MODULE.execute_surface("query-insights", "readonly", query_id="01abc-example", runner=failing)

        def timeout(command, **kwargs):
            self.assertNotEqual(Path(command[3]).parent, MODULE.SQL_DIR)
            raise subprocess.TimeoutExpired(command, 120)

        MODULE.execute_surface("query-insights", "readonly", query_id="01abc-example", runner=timeout)

        def invalid_json(command, **kwargs):
            self.assertNotEqual(Path(command[3]).parent, MODULE.SQL_DIR)
            return subprocess.CompletedProcess(command, 0, stdout="not-json", stderr="")

        with self.assertRaises(MODULE.CollectionError):
            MODULE.execute_surface("query-insights", "readonly", query_id="01abc-example", runner=invalid_json)
        after = {path.name: path.read_bytes() for path in MODULE.SQL_DIR.iterdir()}
        self.assertEqual(before, after)

    def test_unexpected_runner_oserror_still_cleans_selector_file(self):
        before = {path.name: path.read_bytes() for path in MODULE.SQL_DIR.iterdir()}
        captured = {}

        def runner(command, **kwargs):
            captured["path"] = Path(command[3])
            self.assertTrue(captured["path"].exists())
            raise PermissionError("runner unavailable")

        with self.assertRaises(PermissionError):
            MODULE.execute_surface("query-operator-stats", "readonly", query_id="01abc-example", runner=runner)
        self.assertFalse(captured["path"].exists())
        self.assertEqual(before, {path.name: path.read_bytes() for path in MODULE.SQL_DIR.iterdir()})

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

    def test_failed_dynamic_collection_redacts_selector(self) -> None:
        selector = "01customer-query-id"

        def runner(command, **kwargs):
            return subprocess.CompletedProcess(
                command,
                5,
                stdout="",
                stderr=f"query {selector} was not visible in database ANALYTICS",
            )

        receipt, code = MODULE.execute_surface("query-insights", "readonly", query_id=selector, runner=runner)
        self.assertEqual(code, 5)
        rendered = json.dumps(receipt)
        self.assertNotIn(selector, rendered)
        self.assertIn("[REDACTED_SELECTOR]", rendered)

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
