"""Unit tests for the databricks-uc-migration-pilot system-schema enabler
(bead claude-8jj0).

Target: plugins/saas-packs/databricks-pack/skills/databricks-uc-migration-pilot/
        scripts/enable-system-schemas.py

The account-level API calls and SQL grants are I/O; the load-bearing logic is
pure and pinned here: schema validation, the idempotency predicate (an
already-enabled schema is success, not error), the injection-safe grant chain,
and the audit record shape.

Run: python3 -m unittest tests.test_enable_system_schemas -v
"""

import importlib.util
import unittest
from pathlib import Path

SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "plugins" / "saas-packs" / "databricks-pack" / "skills"
    / "databricks-uc-migration-pilot" / "scripts" / "enable-system-schemas.py"
)
spec = importlib.util.spec_from_file_location("enable_system_schemas", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class ValidateSchemasTests(unittest.TestCase):
    def test_splits_valid_and_unknown(self):
        valid, unknown = mod.validate_schemas(["billing", "access", "BOGUS", "query"])
        self.assertEqual(valid, ["billing", "access", "query"])
        self.assertEqual(unknown, ["bogus"])

    def test_case_insensitive_and_trims(self):
        valid, unknown = mod.validate_schemas([" Billing ", "COMPUTE"])
        self.assertEqual(valid, ["billing", "compute"])
        self.assertEqual(unknown, [])

    def test_information_schema_is_not_enableable(self):
        # information_schema is always on; enabling it errors, so it is NOT in the
        # known/enableable set and must land in `unknown`.
        _, unknown = mod.validate_schemas(["information_schema"])
        self.assertEqual(unknown, ["information_schema"])

    def test_defaults_are_all_known(self):
        valid, unknown = mod.validate_schemas(list(mod.DEFAULT_SCHEMAS))
        self.assertEqual(len(valid), len(mod.DEFAULT_SCHEMAS))
        self.assertEqual(unknown, [])


class IdempotencyTests(unittest.TestCase):
    def test_enabled_states_are_already_enabled(self):
        for state in ("ENABLE_COMPLETED", "ENABLE_INITIALIZED", "ENABLED", "enable_completed"):
            self.assertTrue(mod.is_already_enabled(state), state)

    def test_non_enabled_states_are_not(self):
        for state in ("DISABLE_COMPLETED", "UNAVAILABLE", "", None):
            self.assertFalse(mod.is_already_enabled(state), repr(state))


class GrantStatementsTests(unittest.TestCase):
    def test_full_grant_chain(self):
        stmts = mod.grant_statements("billing", "data-gov")
        self.assertEqual(len(stmts), 3)
        self.assertIn("GRANT USE CATALOG ON CATALOG system TO `data-gov`", stmts)
        self.assertIn("GRANT USE SCHEMA ON SCHEMA system.billing TO `data-gov`", stmts)
        self.assertIn("GRANT SELECT ON SCHEMA system.billing TO `data-gov`", stmts)

    def test_group_backticks_stripped_no_injection(self):
        # A hostile group name must not break out of the backtick identifier.
        stmts = mod.grant_statements("billing", "evil`; DROP TABLE x; --")
        for s in stmts:
            # exactly the two identifier backticks per statement, none injected
            self.assertEqual(s.count("`"), 2, s)
            self.assertNotIn("DROP TABLE", s.split("system")[0])


class AuditRecordTests(unittest.TestCase):
    def test_summary_counts(self):
        results = [
            {"schema": "billing", "enable": "enabled", "grant": "applied"},
            {"schema": "access", "enable": "already-enabled", "grant": "applied"},
            {"schema": "compute", "enable": "enabled", "error": "grant: boom"},
        ]
        rec = mod.build_audit_record("acct", "meta", "grp", results, dry_run=False)
        self.assertEqual(rec["granted_to"], "grp")
        self.assertEqual(rec["summary"]["enabled"], 2)
        self.assertEqual(rec["summary"]["already_enabled"], 1)
        self.assertEqual(rec["summary"]["granted"], 2)
        self.assertEqual(rec["summary"]["failed"], 1)

    def test_dry_run_flag_recorded(self):
        rec = mod.build_audit_record("a", "m", "g", [], dry_run=True)
        self.assertTrue(rec["dry_run"])
        self.assertEqual(rec["action"], "enable-system-schemas")


if __name__ == "__main__":
    unittest.main(verbosity=2)
