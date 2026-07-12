"""Unit tests for the dolt-mcp-vcs verb-class SQL classifier — the mutation
chokepoint (blueprint §3 / blocker B1).

Target: plugins/mcp/dolt-mcp-vcs/scripts/sql_classifier.py
Run:    python3 -m unittest tests.test_sql_classifier -v

This is the deterministic coverage that safety-eval.yaml cites (its comment
points here): the executable half of the five mutation-safety invariants —
"never execute a history-affecting statement" and "safe-write only off-main on
a GA flavor" — is enforced by this classifier, so the classifier must be proven
by tests, not just judged behaviorally.

The suite is adversarial-first. The classifier decides whether an agent's SQL is
allowed to rewrite Dolt history; the dangerous verbs (DOLT_PUSH / DOLT_MERGE /
DOLT_RESET --hard / branch-delete / DROP DATABASE) all ride inside the single
`query`/`exec` MCP tool, so a bypass here is a real containment failure. The
bypass class (comments masking a verb, a verb hidden inside a string literal, a
`;`-batch, an interposed comment between CALL and its procedure) gets first-class
coverage alongside the happy path and the full gate truth table.

Pure-function tests only — no dolt binary, no MCP server, no network. The classifier
is stdlib-only and importable with no import side effects, so it is loaded directly.
"""

import importlib.util
import unittest
from pathlib import Path

SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "plugins" / "mcp" / "dolt-mcp-vcs" / "scripts" / "sql_classifier.py"
)
spec = importlib.util.spec_from_file_location("sql_classifier", SCRIPT)
sqlc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sqlc)

READ = sqlc.READ
SAFE_WRITE = sqlc.SAFE_WRITE
HISTORY = sqlc.HISTORY_AFFECTING


class ConstantsTests(unittest.TestCase):
    """The three verb-class labels are the plugin's public contract (exit-code
    and reason strings key off them); pin their exact values."""

    def test_class_labels(self):
        self.assertEqual(READ, "read")
        self.assertEqual(SAFE_WRITE, "safe-write")
        self.assertEqual(HISTORY, "history-affecting")

    def test_severity_ordering_is_total_and_ascending(self):
        # max-wins batch classification depends on this strict ordering.
        self.assertLess(sqlc._SEVERITY[READ], sqlc._SEVERITY[SAFE_WRITE])
        self.assertLess(sqlc._SEVERITY[SAFE_WRITE], sqlc._SEVERITY[HISTORY])


class StripSqlCommentsTests(unittest.TestCase):
    """Comment stripping is the first line of the anti-bypass defense: a verb
    hidden behind a comment must be revealed, but a comment marker *inside* a
    string literal must be preserved (or `DOLT_RESET('--hard')` would be
    misread as a soft reset with a trailing comment)."""

    def test_block_comment_removed(self):
        self.assertEqual(sqlc.strip_sql_comments("A /* x */ B"), "A   B")

    def test_line_comment_removed(self):
        self.assertEqual(sqlc.strip_sql_comments("SELECT 'a''b' -- trailing"),
                         "SELECT 'a''b'  ")

    def test_hash_comment_removed(self):
        self.assertEqual(sqlc.strip_sql_comments("SELECT 1 # hash comment"),
                         "SELECT 1  ")

    def test_hash_inside_string_is_preserved(self):
        # A '#' inside quotes is data, not a comment — stripping it would corrupt
        # the statement and could unmask/mask a verb.
        self.assertEqual(sqlc.strip_sql_comments("SELECT '#notacomment' FROM t"),
                         "SELECT '#notacomment' FROM t")

    def test_double_dash_inside_string_is_preserved(self):
        # The load-bearing case: '--hard' lives inside a string literal and must
        # survive so DOLT_RESET('--hard') classifies as history-affecting.
        self.assertEqual(sqlc.strip_sql_comments("CALL DOLT_RESET('--hard')"),
                         "CALL DOLT_RESET('--hard')")

    def test_doubled_quote_escape_does_not_end_string_early(self):
        # '' is an escaped quote; the string does not terminate at it, so the
        # trailing -- is still a comment (outside the string).
        self.assertEqual(sqlc.strip_sql_comments("'a''b' -- c"), "'a''b'  ")


class SplitStatementsTests(unittest.TestCase):
    def test_simple_split(self):
        self.assertEqual(sqlc.split_statements("a; b ;c"), ["a", "b", "c"])

    def test_semicolon_inside_string_is_not_a_separator(self):
        self.assertEqual(sqlc.split_statements("INSERT INTO t VALUES (';')"),
                         ["INSERT INTO t VALUES (';')"])

    def test_single_statement(self):
        self.assertEqual(sqlc.split_statements("SELECT 1"), ["SELECT 1"])


class ClassifyReadTests(unittest.TestCase):
    def test_select(self):
        self.assertEqual(sqlc.classify_sql("SELECT * FROM issues"), READ)

    def test_case_insensitive(self):
        self.assertEqual(sqlc.classify_sql("select 1"), READ)

    def test_read_leaders(self):
        for kw in ("SELECT 1", "SHOW TABLES", "DESCRIBE t", "DESC t",
                   "EXPLAIN SELECT 1", "USE beads", "VALUES (1)", "HELP 'x'"):
            self.assertEqual(sqlc.classify_sql(kw), READ, kw)

    def test_empty_and_whitespace_are_read(self):
        self.assertEqual(sqlc.classify_sql(""), READ)
        self.assertEqual(sqlc.classify_sql("   "), READ)

    def test_comment_only_is_read(self):
        self.assertEqual(sqlc.classify_sql("-- just a comment"), READ)
        self.assertEqual(sqlc.classify_sql("/* only a comment */"), READ)

    def test_leading_paren_select_is_read(self):
        self.assertEqual(sqlc.classify_sql("(SELECT 1)"), READ)

    def test_leading_block_comment_then_select_is_read(self):
        self.assertEqual(sqlc.classify_sql("/* c */ SELECT 1"), READ)

    def test_set_session_var_is_read(self):
        self.assertEqual(sqlc.classify_sql("SET autocommit=1"), READ)

    def test_with_pure_select_is_read(self):
        self.assertEqual(sqlc.classify_sql("WITH x AS (SELECT 1) SELECT * FROM x"), READ)


class ClassifySafeWriteTests(unittest.TestCase):
    def test_dml_verbs(self):
        for kw in ("INSERT INTO t VALUES (1)", "UPDATE t SET a=1", "DELETE FROM t",
                   "REPLACE INTO t VALUES (1)", "TRUNCATE t"):
            self.assertEqual(sqlc.classify_sql(kw), SAFE_WRITE, kw)

    def test_create_table_is_safe_write(self):
        self.assertEqual(sqlc.classify_sql("CREATE TABLE t (a int)"), SAFE_WRITE)

    def test_alter_table_is_safe_write(self):
        self.assertEqual(sqlc.classify_sql("ALTER TABLE t ADD COLUMN b int"), SAFE_WRITE)

    def test_drop_table_is_recoverable_safe_write(self):
        # A dropped table is recoverable through Dolt history; only DROP DATABASE
        # / SCHEMA / USER / ROLE escalate to history-affecting.
        self.assertEqual(sqlc.classify_sql("DROP TABLE t"), SAFE_WRITE)
        self.assertEqual(sqlc.classify_sql("DROP VIEW v"), SAFE_WRITE)

    def test_set_global_and_password_escalate_to_safe_write(self):
        self.assertEqual(sqlc.classify_sql("SET GLOBAL x=1"), SAFE_WRITE)
        self.assertEqual(sqlc.classify_sql("SET PASSWORD FOR u = 'x'"), SAFE_WRITE)

    def test_with_containing_write_verb_is_safe_write(self):
        self.assertEqual(sqlc.classify_sql("WITH x AS (SELECT 1) DELETE FROM t"),
                         SAFE_WRITE)

    def test_unknown_leading_keyword_fails_safe_to_at_least_safe_write(self):
        # Fail-safe bias: anything not provably a read is never classified read.
        self.assertEqual(sqlc.classify_sql("FROBNICATE THE WIDGETS"), SAFE_WRITE)


class ClassifyHistoryAffectingTests(unittest.TestCase):
    def test_drop_database_family(self):
        for kw in ("DROP DATABASE beads", "DROP   SCHEMA s", "DROP USER u", "DROP ROLE r"):
            self.assertEqual(sqlc.classify_sql(kw), HISTORY, kw)

    def test_create_user_and_role(self):
        self.assertEqual(sqlc.classify_sql("CREATE USER bob"), HISTORY)
        self.assertEqual(sqlc.classify_sql("CREATE ROLE admins"), HISTORY)

    def test_admin_leaders(self):
        for kw in ("GRANT ALL ON *.* TO u", "REVOKE ALL ON *.* FROM u",
                   "FLUSH PRIVILEGES", "SHUTDOWN", "KILL 5", "RESET MASTER",
                   "LOCK TABLES t WRITE", "PURGE BINARY LOGS BEFORE '2020'"):
            self.assertEqual(sqlc.classify_sql(kw), HISTORY, kw)


class ClassifyDoltProceduresTests(unittest.TestCase):
    def test_safe_write_procs(self):
        for proc in ("DOLT_COMMIT('-m','x')", "DOLT_ADD('-A')", "DOLT_CHECKOUT('-b','f')",
                     "DOLT_BRANCH('newbr')", "DOLT_TAG('v1')", "DOLT_FETCH('origin')",
                     "DOLT_REMOTE('add','origin','url')", "DOLT_VERIFY_CONSTRAINTS()"):
            self.assertEqual(sqlc.classify_sql(f"CALL {proc}"), SAFE_WRITE, proc)

    def test_history_affecting_procs(self):
        for proc in ("DOLT_PUSH('origin','main')", "DOLT_PULL('origin')",
                     "DOLT_MERGE('feature')", "DOLT_REVERT('HEAD')",
                     "DOLT_CHERRY_PICK('abc')", "DOLT_REBASE('main')",
                     "DOLT_CLEAN()", "DOLT_GC()", "DOLT_PURGE_DROPPED_DATABASES()"):
            self.assertEqual(sqlc.classify_sql(f"CALL {proc}"), HISTORY, proc)

    def test_reset_soft_vs_hard(self):
        self.assertEqual(sqlc.classify_sql("CALL DOLT_RESET('--soft')"), SAFE_WRITE)
        self.assertEqual(sqlc.classify_sql("CALL DOLT_RESET('--hard')"), HISTORY)

    def test_branch_and_tag_deletion_are_history_affecting(self):
        self.assertEqual(sqlc.classify_sql("CALL DOLT_BRANCH('-d','old')"), HISTORY)
        self.assertEqual(sqlc.classify_sql("CALL DOLT_BRANCH('--delete','old')"), HISTORY)
        self.assertEqual(sqlc.classify_sql("CALL DOLT_TAG('-d','v1')"), HISTORY)

    def test_unknown_dolt_proc_is_denied(self):
        # A DOLT_* procedure we do not recognize could do anything — deny.
        self.assertEqual(sqlc.classify_sql("CALL DOLT_FROBNICATE()"), HISTORY)

    def test_non_dolt_stored_proc_is_denied(self):
        self.assertEqual(sqlc.classify_sql("CALL SOME_RANDOM_PROC()"), HISTORY)

    def test_call_with_no_resolvable_proc_name_is_denied(self):
        self.assertEqual(sqlc.classify_sql("CALL"), HISTORY)


class BatchSeverityTests(unittest.TestCase):
    """A multi-statement batch is classified at the severity of its most
    dangerous statement — a read prefix never lowers the verdict."""

    def test_read_then_write_is_safe_write(self):
        self.assertEqual(sqlc.classify_sql("SELECT 1; INSERT INTO t VALUES (2)"),
                         SAFE_WRITE)

    def test_read_then_history_is_history(self):
        self.assertEqual(sqlc.classify_sql("SELECT 1; CALL DOLT_PUSH('origin','main')"),
                         HISTORY)

    def test_write_then_history_is_history(self):
        self.assertEqual(
            sqlc.classify_sql("INSERT INTO t VALUES (1); CALL DOLT_MERGE('f')"),
            HISTORY)


class AdversarialBypassTests(unittest.TestCase):
    """The containment-critical cases: a dangerous verb must not be able to hide
    behind a comment, a string literal, an interposed comment, or a read-looking
    batch prefix. A regression here is a real security failure, not cosmetics."""

    def test_block_comment_cannot_mask_a_push(self):
        self.assertEqual(sqlc.classify_sql("SELECT 1; /* */ CALL DOLT_PUSH()"), HISTORY)

    def test_line_comment_cannot_mask_a_push(self):
        self.assertEqual(sqlc.classify_sql("SELECT 1 -- ok\n; CALL DOLT_PUSH()"), HISTORY)

    def test_interposed_comment_between_call_and_proc(self):
        # `CALL/**/DOLT_PUSH()` — the comment collapses to a space; the proc name
        # must still be resolved and denied.
        self.assertEqual(sqlc.classify_sql("CALL/**/DOLT_PUSH()"), HISTORY)

    def test_hard_flag_hidden_in_string_still_history(self):
        self.assertEqual(sqlc.classify_sql("CALL DOLT_RESET('--hard') -- trailing"),
                         HISTORY)

    def test_semicolon_in_string_does_not_split_and_hide_a_verb(self):
        # The ';' is data; the whole thing is one INSERT — safe-write, and never
        # mis-split into a harmless-looking fragment.
        self.assertEqual(sqlc.classify_sql("INSERT INTO t VALUES (';')"), SAFE_WRITE)

    def test_no_read_ever_leaks_a_write_verb(self):
        # Property check: for a spread of statements that contain a mutating verb
        # anywhere, the verdict is never `read`.
        never_read = [
            "SELECT 1; UPDATE t SET a=1",
            "/* SELECT */ DELETE FROM t",
            "WITH c AS (SELECT 1) INSERT INTO t SELECT * FROM c",
            "  \n  CALL DOLT_PUSH()",
            "(SELECT 1); DROP DATABASE beads",
        ]
        for sql in never_read:
            self.assertNotEqual(sqlc.classify_sql(sql), READ, sql)


class GateDecisionTests(unittest.TestCase):
    """The gate is the actual enforcement point. Truth table:
       read              -> always allowed (any branch / maturity / flag)
       history-affecting -> always refused (any branch / maturity / flag)
       safe-write        -> allowed IFF allow_mutation AND branch not in {'', main}
                            AND maturity is GA
    """

    def _decide(self, sql, **kw):
        kw.setdefault("allow_mutation", False)
        kw.setdefault("branch", "main")
        kw.setdefault("maturity", "ga")
        return sqlc.gate_decision(sql, **kw)

    # --- read: always allowed ---
    def test_read_allowed_on_main_without_mutation(self):
        allowed, verb, _ = self._decide("SELECT 1")
        self.assertTrue(allowed)
        self.assertEqual(verb, READ)

    def test_read_allowed_even_pre_ga(self):
        allowed, _, _ = self._decide("SELECT 1", maturity="alpha")
        self.assertTrue(allowed)

    # --- history-affecting: always refused ---
    def test_history_refused_even_with_all_permissions(self):
        allowed, verb, reason = self._decide(
            "CALL DOLT_PUSH()", allow_mutation=True, branch="agent/x", maturity="ga")
        self.assertFalse(allowed)
        self.assertEqual(verb, HISTORY)
        self.assertIn("recommend-only", reason)

    # --- safe-write matrix ---
    def test_safe_write_refused_without_allow_mutation(self):
        allowed, verb, reason = self._decide("INSERT INTO t VALUES (1)", branch="agent/x")
        self.assertFalse(allowed)
        self.assertEqual(verb, SAFE_WRITE)
        self.assertIn("--allow-mutation", reason)

    def test_safe_write_refused_on_main(self):
        allowed, _, reason = self._decide(
            "INSERT INTO t VALUES (1)", allow_mutation=True, branch="main")
        self.assertFalse(allowed)
        self.assertIn("agent-owned branch", reason)

    def test_safe_write_refused_on_empty_branch(self):
        allowed, _, _ = self._decide(
            "INSERT INTO t VALUES (1)", allow_mutation=True, branch="")
        self.assertFalse(allowed)

    def test_safe_write_refused_on_main_case_insensitive(self):
        allowed, _, _ = self._decide(
            "INSERT INTO t VALUES (1)", allow_mutation=True, branch="MAIN")
        self.assertFalse(allowed)

    def test_safe_write_refused_pre_ga(self):
        for maturity in ("alpha", "experimental"):
            allowed, _, reason = self._decide(
                "INSERT INTO t VALUES (1)", allow_mutation=True,
                branch="agent/x", maturity=maturity)
            self.assertFalse(allowed, maturity)
            self.assertIn("pre-GA", reason)

    def test_safe_write_allowed_the_one_permitted_path(self):
        allowed, verb, reason = self._decide(
            "INSERT INTO t VALUES (1)", allow_mutation=True,
            branch="agent/my-task", maturity="ga")
        self.assertTrue(allowed)
        self.assertEqual(verb, SAFE_WRITE)
        self.assertIn("agent/my-task", reason)

    def test_none_maturity_defaults_to_ga(self):
        allowed, _, _ = self._decide(
            "INSERT INTO t VALUES (1)", allow_mutation=True,
            branch="agent/x", maturity=None)
        self.assertTrue(allowed)

    def test_maturity_is_case_insensitive(self):
        allowed, _, _ = self._decide(
            "INSERT INTO t VALUES (1)", allow_mutation=True,
            branch="agent/x", maturity="GA")
        self.assertTrue(allowed)


if __name__ == "__main__":
    unittest.main(verbosity=2)
