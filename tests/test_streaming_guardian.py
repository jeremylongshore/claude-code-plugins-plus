"""Unit tests for the databricks-streaming-guardian deterministic core
(bead claude-vjaw: the PreToolUse guard hook + the streaming-recovery decision tree).

Targets:
  plugins/saas-packs/databricks-pack/skills/databricks-streaming-guardian/
    hooks/streaming-guard-hook.py       — classify_destructive_op precision + decide fail-open
    scripts/recover-streaming-source.py — the 4-way recovery decision tree

The hook's precision contract is the load-bearing part: a false-positive block of a
routine command (a `git commit` mentioning "drop table", an `echo`) is a serious
behavioral defect, so those cases are pinned here. The consumer check must fail OPEN.

Run: python3 -m unittest tests.test_streaming_guardian -v
"""

import importlib.util
import unittest
from pathlib import Path

SKILL = (
    Path(__file__).resolve().parents[1]
    / "plugins" / "saas-packs" / "databricks-pack" / "skills"
    / "databricks-streaming-guardian"
)


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


hook = _load("streaming_guard_hook", SKILL / "hooks" / "streaming-guard-hook.py")
rec = _load("recover_streaming_source", SKILL / "scripts" / "recover-streaming-source.py")


class ClassifyDestructiveOpTests(unittest.TestCase):
    """The precision contract: only a real SQL-surface destructive op classifies."""

    def test_raw_sql_drop_classifies(self):
        r = hook.classify_destructive_op("DROP TABLE main.sales.orders")
        self.assertIsNotNone(r)
        self.assertEqual(r[0], "DROP TABLE")
        self.assertEqual(r[1], "main.sales.orders")
        self.assertEqual(r[2], "D12")

    def test_create_or_replace_classifies(self):
        r = hook.classify_destructive_op("CREATE OR REPLACE TABLE db.t AS SELECT 1")
        self.assertEqual(r[0], "CREATE OR REPLACE TABLE")
        self.assertEqual(r[1], "db.t")

    def test_vacuum_classifies_as_d03(self):
        r = hook.classify_destructive_op("VACUUM main.sales.orders RETAIN 0 HOURS")
        self.assertEqual(r[0], "VACUUM")
        self.assertEqual(r[2], "D03/D07")

    def test_drop_via_statement_execution_api_classifies(self):
        cmd = "databricks api post /api/2.0/sql/statements --json '{\"statement\":\"DROP TABLE x.y\"}'"
        r = hook.classify_destructive_op(cmd)
        self.assertIsNotNone(r)
        self.assertEqual(r[0], "DROP TABLE")

    def test_drop_via_spark_sql_classifies(self):
        r = hook.classify_destructive_op("spark.sql('DROP TABLE catalog.schema.t')")
        self.assertIsNotNone(r)
        self.assertEqual(r[1], "catalog.schema.t")

    def test_backticked_identifier_is_normalized(self):
        r = hook.classify_destructive_op("DROP TABLE `my cat`.`my schema`.`my tbl`")
        self.assertIsNotNone(r)
        self.assertNotIn("`", r[1])

    def test_if_exists_is_skipped(self):
        r = hook.classify_destructive_op("DROP TABLE IF EXISTS db.t")
        self.assertEqual(r[1], "db.t")

    # --- the false-positive guard: routine commands must NOT classify ---
    def test_git_commit_mentioning_drop_table_is_ignored(self):
        self.assertIsNone(hook.classify_destructive_op("git commit -m 'drop table feature'"))

    def test_echo_mentioning_drop_table_is_ignored(self):
        self.assertIsNone(hook.classify_destructive_op("echo 'remember to drop table x later'"))

    def test_grep_for_vacuum_is_ignored(self):
        self.assertIsNone(hook.classify_destructive_op("grep -r 'VACUUM' ./migrations"))

    def test_cat_of_sql_file_is_ignored(self):
        self.assertIsNone(hook.classify_destructive_op("cat migrations/003_drop_table.sql"))

    def test_comment_mentioning_create_or_replace_is_ignored(self):
        self.assertIsNone(hook.classify_destructive_op("# TODO: create or replace table later"))

    def test_empty_and_non_string(self):
        self.assertIsNone(hook.classify_destructive_op(""))
        self.assertIsNone(hook.classify_destructive_op(None))


class DecideTests(unittest.TestCase):
    def setUp(self):
        self._orig = hook.active_stream_consumers

    def tearDown(self):
        hook.active_stream_consumers = self._orig

    def _event(self, command, tool="Bash"):
        return {"tool_name": tool, "tool_input": {"command": command}}

    def test_non_bash_tool_allows(self):
        d = hook.decide({"tool_name": "Read", "tool_input": {}})
        self.assertEqual(d["hookSpecificOutput"]["permissionDecision"], "allow")

    def test_harmless_command_allows(self):
        d = hook.decide(self._event("ls -la"))
        self.assertEqual(d["hookSpecificOutput"]["permissionDecision"], "allow")

    def test_confirmed_consumer_denies(self):
        hook.active_stream_consumers = lambda table: ["run-1", "run-2"]
        d = hook.decide(self._event("DROP TABLE main.sales.orders"))
        self.assertEqual(d["hookSpecificOutput"]["permissionDecision"], "deny")
        reason = d["hookSpecificOutput"]["permissionDecisionReason"]
        self.assertIn("main.sales.orders", reason)
        self.assertIn("2 active", reason)

    def test_no_consumers_allows(self):
        hook.active_stream_consumers = lambda table: []
        d = hook.decide(self._event("DROP TABLE main.sales.orders"))
        self.assertEqual(d["hookSpecificOutput"]["permissionDecision"], "allow")

    def test_unverifiable_fails_open(self):
        # None = check could not run → must ALLOW, never block on an unverifiable check.
        hook.active_stream_consumers = lambda table: None
        d = hook.decide(self._event("DROP TABLE main.sales.orders"))
        self.assertEqual(d["hookSpecificOutput"]["permissionDecision"], "allow")


class RecoveryDecisionTests(unittest.TestCase):
    def test_transient_is_safe_restart(self):
        r = rec.recovery_decision("transient", None, None, None)
        self.assertEqual(r["tier"], rec.SAFE_RESTART)

    def test_file_not_found_with_time_travel_restores_no_loss(self):
        r = rec.recovery_decision("file-not-found", None, None, True)
        self.assertEqual(r["tier"], rec.TIME_TRAVEL)
        self.assertEqual(r["data_loss_risk"], "none")

    def test_file_not_found_replayable_idempotent_reprocesses(self):
        r = rec.recovery_decision("file-not-found", True, True, False)
        self.assertEqual(r["tier"], rec.REPROCESS)

    def test_file_not_found_worst_case_full_reset_high_loss(self):
        r = rec.recovery_decision("file-not-found", False, False, False)
        self.assertEqual(r["tier"], rec.FULL_RESET)
        self.assertIn("HIGH", r["data_loss_risk"])

    def test_uuid_changed_not_replayable_is_high_loss(self):
        r = rec.recovery_decision("uuid-changed", False, None, None)
        self.assertEqual(r["tier"], rec.FULL_RESET)
        self.assertIn("HIGH", r["data_loss_risk"])

    def test_uuid_changed_replayable_full_reset_low_loss(self):
        r = rec.recovery_decision("uuid-changed", True, None, None)
        self.assertEqual(r["tier"], rec.FULL_RESET)
        self.assertNotIn("HIGH", r["data_loss_risk"])

    def test_checkpoint_reset_idempotent_reprocesses(self):
        r = rec.recovery_decision("checkpoint-reset", True, True, None)
        self.assertEqual(r["tier"], rec.REPROCESS)

    def test_checkpoint_reset_unsafe_needs_review(self):
        r = rec.recovery_decision("checkpoint-reset", False, False, None)
        self.assertEqual(r["tier"], rec.FULL_RESET)

    def test_none_inputs_treated_pessimistically(self):
        # file-not-found with all-unknown must NOT pick the no-loss path.
        r = rec.recovery_decision("file-not-found", None, None, None)
        self.assertEqual(r["tier"], rec.FULL_RESET)

    def test_every_result_has_steps(self):
        for f in rec.FAILURES:
            r = rec.recovery_decision(f, None, None, None)
            self.assertTrue(r["steps"], f)
            self.assertIn("tier", r)
            self.assertIn("rationale", r)

    def test_canonical_error_codes_mapped(self):
        # The skill's SRE value is naming the exact searchable code, not a paraphrase.
        self.assertEqual(rec.FAILURE_CODES["file-not-found"], "DELTA_FILE_NOT_FOUND_DETAILED")
        self.assertEqual(
            rec.FAILURE_CODES["uuid-changed"], "DIFFERENT_DELTA_TABLE_READ_BY_STREAMING_SOURCE"
        )
        # every failure class has an entry
        for f in rec.FAILURES:
            self.assertIn(f, rec.FAILURE_CODES)


if __name__ == "__main__":
    unittest.main(verbosity=2)
