"""Unit tests for freshie/scripts/dolt-sync.py (schema translation, the
(NULL,'') fallback SQL generation, the VARCHAR length guard, the export
allowlist, the grades-export run scoping, the push credential env path,
stranded-tag reconciliation, and the JSON-checksum target split).

Run: python3 -m unittest tests.test_dolt_sync -v

Pure-function tests only — no dolt binary, no network, no repo state.
The live round-trip (CSV canary, parity gates, push) is exercised by the
sync itself on every run.
"""

import importlib.util
import sqlite3
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "freshie" / "scripts" / "dolt-sync.py"
spec = importlib.util.spec_from_file_location("dolt_sync", SCRIPT)
dolt_sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dolt_sync)


def fixture_conn(ddl: str) -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(ddl)
    return conn


class TranslateColumnTypeTests(unittest.TestCase):
    def test_base_type_map(self):
        self.assertEqual(dolt_sync.translate_column_type("t", "c", "INTEGER", False), "BIGINT")
        self.assertEqual(dolt_sync.translate_column_type("t", "c", "REAL", False), "DOUBLE")
        self.assertEqual(dolt_sync.translate_column_type("t", "c", "TIMESTAMP", False), "DATETIME(6)")
        self.assertEqual(dolt_sync.translate_column_type("t", "c", "TEXT", False), "LONGTEXT")

    def test_text_pk_becomes_varchar(self):
        self.assertEqual(
            dolt_sync.translate_column_type("npm_packages", "package_name", "TEXT", True),
            "VARCHAR(255)",
        )

    def test_integer_pk_stays_bigint(self):
        self.assertEqual(dolt_sync.translate_column_type("t", "id", "INTEGER", True), "BIGINT")

    def test_blob_hard_fails(self):
        with self.assertRaises(dolt_sync.SyncError):
            dolt_sync.translate_column_type("t", "c", "BLOB", False)

    def test_unknown_type_hard_fails(self):
        with self.assertRaises(dolt_sync.SyncError):
            dolt_sync.translate_column_type("t", "c", "NUMERIC", False)
        with self.assertRaises(dolt_sync.SyncError):
            dolt_sync.translate_column_type("t", "c", "", False)


class BuildCreateTableTests(unittest.TestCase):
    def ddl_for(self, sqlite_ddl: str, table: str) -> str:
        conn = fixture_conn(sqlite_ddl)
        schema = dolt_sync.introspect_schema(conn)
        conn.close()
        return dolt_sync.build_create_table(table, schema[table])

    def test_autoincrement_is_stripped(self):
        ddl = self.ddl_for(
            "CREATE TABLE t (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT);", "t"
        )
        self.assertNotIn("AUTOINCREMENT", ddl.upper().replace("_", ""))
        self.assertIn("`id` BIGINT", ddl)
        self.assertIn("PRIMARY KEY (`id`)", ddl)

    def test_identifiers_are_backticked(self):
        ddl = self.ddl_for("CREATE TABLE t (id INTEGER PRIMARY KEY, name TEXT);", "t")
        self.assertIn("CREATE TABLE `t`", ddl)
        self.assertIn("`name` LONGTEXT", ddl)

    def test_text_primary_key_varchar(self):
        ddl = self.ddl_for("CREATE TABLE p (package_name TEXT PRIMARY KEY, v TEXT);", "p")
        self.assertIn("`package_name` VARCHAR(255)", ddl)
        self.assertIn("PRIMARY KEY (`package_name`)", ddl)

    def test_current_timestamp_default_gets_precision(self):
        ddl = self.ddl_for(
            "CREATE TABLE t (id INTEGER PRIMARY KEY, "
            "validated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);", "t"
        )
        self.assertIn("`validated_at` DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6)", ddl)

    def test_unique_constraint_renamed_and_kept_longtext(self):
        ddl = self.ddl_for(
            "CREATE TABLE t (id INTEGER PRIMARY KEY, skill_path TEXT, run_id INTEGER, "
            "UNIQUE(skill_path, run_id));", "t"
        )
        self.assertIn("UNIQUE KEY `uniq_t_1` (`skill_path`, `run_id`)", ddl)
        self.assertIn("`skill_path` LONGTEXT", ddl)
        self.assertNotIn("sqlite_autoindex", ddl)

    def test_nonunique_text_index_gets_prefix(self):
        ddl = self.ddl_for(
            "CREATE TABLE forge_proofs (id INTEGER PRIMARY KEY, plugin_name TEXT, passed INTEGER);"
            "CREATE INDEX idx_forge_proofs_plugin ON forge_proofs(plugin_name);"
            "CREATE INDEX idx_forge_proofs_passed ON forge_proofs(passed);",
            "forge_proofs",
        )
        self.assertIn("KEY `idx_forge_proofs_plugin` (`plugin_name`(255))", ddl)
        self.assertIn("KEY `idx_forge_proofs_passed` (`passed`)", ddl)

    def test_composite_text_pk_all_varchar(self):
        ddl = self.ddl_for(
            "CREATE TABLE t (a TEXT, b TEXT, PRIMARY KEY (a, b));", "t"
        )
        self.assertIn("`a` VARCHAR(255)", ddl)
        self.assertIn("`b` VARCHAR(255)", ddl)
        self.assertIn("PRIMARY KEY (`a`, `b`)", ddl)

    def test_blob_column_fails_the_whole_table(self):
        conn = fixture_conn("CREATE TABLE t (id INTEGER PRIMARY KEY, payload BLOB);")
        schema = dolt_sync.introspect_schema(conn)
        conn.close()
        with self.assertRaises(dolt_sync.SyncError):
            dolt_sync.build_create_table("t", schema["t"])


class SqlLiteralTests(unittest.TestCase):
    def test_null_and_empty_are_distinct(self):
        self.assertEqual(dolt_sync.sql_literal(None), "NULL")
        self.assertEqual(dolt_sync.sql_literal(""), "''")

    def test_quote_and_backslash_escaping(self):
        self.assertEqual(dolt_sync.sql_literal("it's"), "'it''s'")
        self.assertEqual(dolt_sync.sql_literal("a\\b"), "'a\\\\b'")

    def test_numbers(self):
        self.assertEqual(dolt_sync.sql_literal(7), "7")
        self.assertEqual(dolt_sync.sql_literal(0.1), "0.1")
        # repr round-trips doubles exactly
        self.assertEqual(float(dolt_sync.sql_literal(1 / 3)), 1 / 3)


class BuildInsertBatchesTests(unittest.TestCase):
    def test_batching_and_null_vs_empty(self):
        rows = [(1, None), (2, ""), (3, "x")]
        stmts = dolt_sync.build_insert_batches("t", ["id", "v"], rows, batch_size=2)
        self.assertEqual(len(stmts), 2)
        self.assertIn("(1, NULL)", stmts[0])
        self.assertIn("(2, '')", stmts[0])
        self.assertIn("(3, 'x')", stmts[1])
        self.assertTrue(stmts[0].startswith("INSERT INTO `t` (`id`, `v`) VALUES"))

    def test_no_rows_no_statements(self):
        self.assertEqual(dolt_sync.build_insert_batches("t", ["id"], []), [])


class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.conn = fixture_conn(
            "CREATE TABLE a (id INTEGER PRIMARY KEY, pct REAL, name TEXT);"
            "CREATE TABLE b (package_name TEXT PRIMARY KEY, score REAL);"
            "CREATE TABLE c (id INTEGER PRIMARY KEY, note TEXT);"
        )
        self.schema = dolt_sync.introspect_schema(self.conn)

    def tearDown(self):
        self.conn.close()

    def test_real_columns_discovered(self):
        self.assertEqual(
            dolt_sync.real_columns(self.schema), {"a": ["pct"], "b": ["score"]}
        )

    def test_text_pk_guards_discovered(self):
        self.assertEqual(dolt_sync.text_pk_guards(self.schema), [("b", "package_name")])

    def test_sqlite_sequence_is_skipped(self):
        conn = fixture_conn(
            "CREATE TABLE t (id INTEGER PRIMARY KEY AUTOINCREMENT, v TEXT);"
            "INSERT INTO t (v) VALUES ('x');"
        )
        schema = dolt_sync.introspect_schema(conn)
        conn.close()
        self.assertIn("t", schema)
        self.assertNotIn("sqlite_sequence", schema)


class TypeViolationTests(unittest.TestCase):
    """SQLite typing is advisory — declared-INTEGER columns can hold TEXT.
    Violating non-PK columns must widen to LONGTEXT; PK violations hard-fail."""

    def test_text_in_integer_column_widens(self):
        conn = fixture_conn(
            "CREATE TABLE t (id INTEGER PRIMARY KEY, fm_max_turns INTEGER DEFAULT 0);"
        )
        conn.execute("INSERT INTO t VALUES (1, 10)")
        conn.execute("INSERT INTO t VALUES (2, '10 # yaml comment cruft')")
        schema = dolt_sync.introspect_schema(conn)
        violations = dolt_sync.scan_type_violations(conn, schema)
        self.assertEqual(violations, {("t", "fm_max_turns"): 1})
        ddl = dolt_sync.build_create_table("t", schema["t"], frozenset(violations))
        self.assertIn("`fm_max_turns` LONGTEXT", ddl)
        # literal DEFAULTs are invalid on TEXT-class columns — must be dropped
        self.assertNotIn("LONGTEXT DEFAULT", ddl)
        conn.close()

    def test_clean_data_no_violations(self):
        conn = fixture_conn("CREATE TABLE t (id INTEGER PRIMARY KEY, n INTEGER, r REAL);")
        conn.execute("INSERT INTO t VALUES (1, 5, 0.5)")
        schema = dolt_sync.introspect_schema(conn)
        self.assertEqual(dolt_sync.scan_type_violations(conn, schema), {})
        conn.close()

    def test_bad_timestamp_widens(self):
        conn = fixture_conn(
            "CREATE TABLE t (id INTEGER PRIMARY KEY, at TIMESTAMP);"
        )
        conn.execute("INSERT INTO t VALUES (1, '2026-05-04T00:45:25.457182')")
        conn.execute("INSERT INTO t VALUES (2, 'not a datetime')")
        schema = dolt_sync.introspect_schema(conn)
        self.assertEqual(
            dolt_sync.scan_type_violations(conn, schema), {("t", "at"): 1}
        )
        conn.close()

    def test_pk_violation_hard_fails(self):
        # composite PK: `a` is INTEGER but not a rowid alias, so SQLite
        # happily stores TEXT in it — the scan must refuse to widen a key
        conn = fixture_conn("CREATE TABLE t (a INTEGER, b TEXT, PRIMARY KEY (a, b));")
        conn.execute("INSERT INTO t VALUES ('oops', 'x')")
        schema = dolt_sync.introspect_schema(conn)
        with self.assertRaises(dolt_sync.SyncError):
            dolt_sync.scan_type_violations(conn, schema)
        conn.close()


class ExportAllowlistTests(unittest.TestCase):
    """Only the intended CMDB tables may reach the public DoltHub record.
    Known j-rig runtime tables are excluded quietly; anything else is a
    hard failure naming the table."""

    def test_allowed_tables_pass_through_in_order(self):
        allowed, excluded = dolt_sync.filter_export_tables(
            ["plugins", "skill_compliance", "skills"]
        )
        self.assertEqual(allowed, ["plugins", "skill_compliance", "skills"])
        self.assertEqual(excluded, [])

    def test_jrig_contaminants_are_excluded_not_fatal(self):
        allowed, excluded = dolt_sync.filter_export_tables(
            ["criterion_results", "runs", "skills"]
        )
        self.assertEqual(allowed, ["skills"])
        self.assertEqual(excluded, ["criterion_results", "runs"])

    def test_every_known_jrig_table_is_excluded(self):
        # The full recorder schema of @intentsolutions/jrig-cli — including
        # run_summaries, which the original leak report under-counted.
        jrig = sorted(dolt_sync.JRIG_RUNTIME_TABLES)
        self.assertEqual(
            jrig,
            ["artifacts", "criterion_results", "run_summaries", "runs",
             "skill_human_reviews", "skill_usage_events", "skill_versions"],
        )
        allowed, excluded = dolt_sync.filter_export_tables(jrig)
        self.assertEqual(allowed, [])
        self.assertEqual(excluded, jrig)

    def test_unknown_table_hard_fails_naming_it(self):
        with self.assertRaises(dolt_sync.SyncError) as ctx:
            dolt_sync.filter_export_tables(["skills", "totally_new_table"])
        self.assertIn("totally_new_table", str(ctx.exception))
        self.assertIn("EXPORT_ALLOWLIST", str(ctx.exception))

    def test_allowlist_and_contaminants_are_disjoint(self):
        self.assertEqual(
            dolt_sync.EXPORT_ALLOWLIST & dolt_sync.JRIG_RUNTIME_TABLES,
            frozenset(),
        )

    def test_allowlist_matches_readme_table_count(self):
        # freshie/README.md documents the 51-table CMDB inventory.
        self.assertEqual(len(dolt_sync.EXPORT_ALLOWLIST), 51)


class GradesExportScopingTests(unittest.TestCase):
    """grades.csv is scoped to the latest graded run — a skill deleted from
    the repo must drop out of the export instead of ghosting forever on its
    last recorded grade."""

    def setUp(self):
        self.conn = fixture_conn(
            "CREATE TABLE skill_compliance ("
            "  id INTEGER PRIMARY KEY,"
            "  skill_path TEXT,"
            "  run_id INTEGER,"
            "  grade TEXT,"
            "  score REAL,"
            "  UNIQUE(skill_path, run_id)"
            ");"
        )
        self.conn.executemany(
            "INSERT INTO skill_compliance (skill_path, run_id, grade, score) "
            "VALUES (?, ?, ?, ?)",
            [
                ("plugins/x/skills/ghost", 8, "B", 80.0),   # deleted after run 8
                ("plugins/x/skills/alive", 8, "B", 82.0),
                ("plugins/x/skills/alive", 9, "A", 91.0),   # improved in run 9
                ("plugins/x/skills/newer", 9, "B", 85.0),
            ],
        )

    def tearDown(self):
        self.conn.close()

    def test_latest_graded_run_id(self):
        self.assertEqual(dolt_sync.latest_graded_run_id(self.conn), 9)

    def test_ghost_row_excluded_from_scoped_export(self):
        rows = dolt_sync.grades_export_rows(self.conn, 9)
        paths = [r[0] for r in rows]
        self.assertNotIn("plugins/x/skills/ghost", paths)
        self.assertEqual(
            paths, ["plugins/x/skills/alive", "plugins/x/skills/newer"]
        )

    def test_scoped_export_uses_the_scoped_runs_grade(self):
        rows = {r[0]: r[1] for r in dolt_sync.grades_export_rows(self.conn, 9)}
        self.assertEqual(rows["plugins/x/skills/alive"], "A")  # not run 8's B

    def test_empty_compliance_table_reports_run_zero(self):
        conn = fixture_conn(
            "CREATE TABLE skill_compliance (skill_path TEXT, run_id INTEGER,"
            " grade TEXT, score REAL);"
        )
        self.assertEqual(dolt_sync.latest_graded_run_id(conn), 0)
        self.assertEqual(dolt_sync.grades_export_rows(conn, 0), [])
        conn.close()


class PushAuthArgsTests(unittest.TestCase):
    """CI env-var credential path: --user only when BOTH vars are present."""

    def test_both_vars_enable_the_user_flag(self):
        self.assertEqual(
            dolt_sync.push_auth_args(
                {"DOLT_REMOTE_USER": "ci-bot", "DOLT_REMOTE_PASSWORD": "tok"}
            ),
            ["--user", "ci-bot"],
        )

    def test_password_alone_is_not_enough(self):
        self.assertEqual(
            dolt_sync.push_auth_args({"DOLT_REMOTE_PASSWORD": "tok"}), []
        )

    def test_user_alone_is_not_enough(self):
        self.assertEqual(
            dolt_sync.push_auth_args({"DOLT_REMOTE_USER": "ci-bot"}), []
        )

    def test_empty_env_falls_back_to_creds_path(self):
        self.assertEqual(dolt_sync.push_auth_args({}), [])


class StrandedTagsTests(unittest.TestCase):
    """A run-* tag left local-only by a failed push must be pushed by the
    next successful sync — not just the current run's tag."""

    def test_missing_run_tag_detected(self):
        self.assertEqual(
            dolt_sync.stranded_tags(
                {"run-8", "run-9", "run-9.1"}, {"run-8"}, "run-9.1"
            ),
            ["run-9"],
        )

    def test_current_tag_is_not_duplicated(self):
        self.assertEqual(
            dolt_sync.stranded_tags({"run-10"}, set(), "run-10"), []
        )

    def test_non_run_tags_are_ignored(self):
        self.assertEqual(
            dolt_sync.stranded_tags({"experiment", "run-7"}, set(), None),
            ["run-7"],
        )

    def test_nothing_stranded_when_remote_has_all(self):
        self.assertEqual(
            dolt_sync.stranded_tags(
                {"run-8", "run-9"}, {"run-8", "run-9"}, None
            ),
            [],
        )


class ChecksumTargetSplitTests(unittest.TestCase):
    """The JSON checksum gate must know (and report) which targets it
    actually verified; a listed-but-absent table is surfaced, not skipped."""

    def test_present_and_missing_split(self):
        present, missing = dolt_sync.split_checksum_targets(
            {"a": {}}, [("a", "j"), ("b", "k")]
        )
        self.assertEqual(present, [("a", "j")])
        self.assertEqual(missing, [("b", "k")])

    def test_default_targets_all_present(self):
        schema = {t: {} for t, _ in dolt_sync.JSON_CHECKSUM_COLUMNS}
        present, missing = dolt_sync.split_checksum_targets(schema)
        self.assertEqual(present, dolt_sync.JSON_CHECKSUM_COLUMNS)
        self.assertEqual(missing, [])


class VarcharGuardTests(unittest.TestCase):
    def test_over_length_pk_fails(self):
        conn = fixture_conn("CREATE TABLE b (package_name TEXT PRIMARY KEY);")
        conn.execute("INSERT INTO b VALUES (?)", ("x" * 300,))
        with self.assertRaises(dolt_sync.SyncError):
            dolt_sync.gate_varchar_lengths(conn, [("b", "package_name")])
        conn.close()

    def test_within_length_passes(self):
        conn = fixture_conn("CREATE TABLE b (package_name TEXT PRIMARY KEY);")
        conn.execute("INSERT INTO b VALUES (?)", ("x" * 214,))
        dolt_sync.gate_varchar_lengths(conn, [("b", "package_name")])
        conn.close()


if __name__ == "__main__":
    unittest.main()
