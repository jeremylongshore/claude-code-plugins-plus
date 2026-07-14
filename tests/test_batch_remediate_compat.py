"""Regression tests for freshie/scripts/batch-remediate.py --fix-compatible-with
(bead claude-juoz.6).

Four defects fixed and pinned here:
  1. DB query matched the DEPRECATED `compatible-with` (never in missing_fields)
     instead of the canonical `compatibility` -> a silent 0-row no-op in DB mode.
  2. The writer emitted the deprecated `compatible-with: claude-code` field.
  3. The fs-walk selector only checked `compatible-with`, so ~2,857 already-
     compliant files were re-selected and double-stamped.
  4. DB `skill_compliance.skill_path` is a skill DIRECTORY, not the SKILL.md file;
     `Path(row).read_text()` hit the directory (IsADirectoryError -> counted as a
     skip), so even the tags fixer added nothing in DB mode.

Run: python3 -m unittest tests.test_batch_remediate_compat -v

Fully self-contained: builds a tmp skill tree + a tmp sqlite `skill_compliance`,
monkeypatches the module's REPO_ROOT / PLUGINS_ROOT / DB_PATH at that tree, and
never touches the real repo or freshie/inventory.sqlite.
"""

import contextlib
import importlib.util
import io
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "freshie" / "scripts" / "batch-remediate.py"
_spec = importlib.util.spec_from_file_location("batch_remediate", SCRIPT)
br = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(br)

MISSING = """\
---
name: needs-compat
description: A skill that is missing the compatibility field entirely.
tags: [test]
---
# Body
"""

HAS_COMPAT = """\
---
name: has-compat
description: A skill that already declares the modern compatibility field.
compatibility: Designed for Claude Code
tags: [test]
---
# Body
"""

HAS_LEGACY = """\
---
name: has-legacy
description: A skill that still carries the deprecated compatible-with field.
compatible-with: claude-code
tags: [test]
---
# Body
"""


class BatchRemediateCompatTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        self.root = root
        plugins = root / "plugins"
        # skill directories (the DB stores the DIRECTORY, not the SKILL.md path)
        self.missing_dir = plugins / "cat" / "p" / "skills" / "needs-compat"
        self.compat_dir = plugins / "cat" / "p" / "skills" / "has-compat"
        self.legacy_dir = plugins / "cat" / "p" / "skills" / "has-legacy"
        for d, body in (
            (self.missing_dir, MISSING),
            (self.compat_dir, HAS_COMPAT),
            (self.legacy_dir, HAS_LEGACY),
        ):
            d.mkdir(parents=True)
            (d / "SKILL.md").write_text(body, encoding="utf-8")

        # tmp DB with the same shape the real skill_compliance uses: skill_path =
        # a repo-relative DIRECTORY, missing_fields = a JSON list string.
        self.db_path = root / "inv.sqlite"
        conn = sqlite3.connect(self.db_path)
        conn.execute("CREATE TABLE skill_compliance (skill_path TEXT, missing_fields TEXT)")
        conn.execute(
            "INSERT INTO skill_compliance VALUES (?, ?)",
            (str(self.missing_dir.relative_to(root)), '["compatibility", "tags"]'),
        )
        conn.execute(
            "INSERT INTO skill_compliance VALUES (?, ?)",
            (str(self.compat_dir.relative_to(root)), '["author"]'),
        )
        conn.commit()
        conn.close()

        # Point the module at the tmp tree. Functions read these module globals
        # at call time, so patching the attributes is sufficient.
        self._orig = {k: getattr(br, k) for k in ("REPO_ROOT", "PLUGINS_ROOT", "DB_PATH")}
        br.REPO_ROOT = root
        br.PLUGINS_ROOT = plugins
        br.DB_PATH = self.db_path

    def tearDown(self):
        for k, v in self._orig.items():
            setattr(br, k, v)
        self._tmp.cleanup()

    # ── defect 4: directory-row -> SKILL.md resolver ────────────────────
    def test_skill_md_from_row_resolves_directory_to_file(self):
        rel = str(self.missing_dir.relative_to(self.root))
        resolved = br._skill_md_from_row(rel)
        self.assertEqual(resolved, self.missing_dir / "SKILL.md")
        self.assertTrue(resolved.is_file())

    # ── defect 1: DB query uses `compatibility`, resolver returns the file ──
    def test_db_query_finds_missing_compatibility_as_skill_md(self):
        conn = sqlite3.connect(self.db_path)
        paths = br.get_skills_missing_compatible_with(conn)
        conn.close()
        # only the row whose missing_fields contains 'compatibility', resolved to
        # the actual SKILL.md file (not the bare directory).
        self.assertEqual(paths, [self.missing_dir / "SKILL.md"])

    def test_old_deprecated_field_name_would_have_matched_nothing(self):
        # Proves the original bug: the DB never records the deprecated name.
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute(
            "SELECT COUNT(*) FROM skill_compliance WHERE missing_fields LIKE '%compatible-with%'"
        ).fetchone()[0]
        conn.close()
        self.assertEqual(rows, 0)

    # ── defect 2: writes the modern field, never the deprecated one ─────
    def test_writes_modern_compatibility_field(self):
        changed, err = br.add_compatible_with_to_file(self.missing_dir / "SKILL.md", dry_run=False)
        self.assertTrue(changed)
        self.assertIsNone(err)
        text = (self.missing_dir / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("compatibility: Designed for Claude Code", text)
        self.assertNotIn("compatible-with:", text)

    def test_dry_run_does_not_write(self):
        before = (self.missing_dir / "SKILL.md").read_text(encoding="utf-8")
        changed, _ = br.add_compatible_with_to_file(self.missing_dir / "SKILL.md", dry_run=True)
        self.assertTrue(changed)
        self.assertEqual((self.missing_dir / "SKILL.md").read_text(encoding="utf-8"), before)

    # ── defect 3: no double-stamping ────────────────────────────────────
    def test_skips_file_that_already_has_compatibility(self):
        before = (self.compat_dir / "SKILL.md").read_text(encoding="utf-8")
        changed, err = br.add_compatible_with_to_file(self.compat_dir / "SKILL.md", dry_run=False)
        self.assertFalse(changed)
        self.assertIsNone(err)
        self.assertEqual((self.compat_dir / "SKILL.md").read_text(encoding="utf-8"), before)

    def test_skips_file_with_legacy_compatible_with(self):
        # A file still carrying the deprecated field is left for the migrate tool,
        # not double-stamped with the modern field.
        before = (self.legacy_dir / "SKILL.md").read_text(encoding="utf-8")
        changed, err = br.add_compatible_with_to_file(self.legacy_dir / "SKILL.md", dry_run=False)
        self.assertFalse(changed)
        self.assertIsNone(err)
        after = (self.legacy_dir / "SKILL.md").read_text(encoding="utf-8")
        self.assertEqual(after, before)
        self.assertNotIn("compatibility:", after)

    def test_fs_walk_excludes_files_that_already_have_either_field(self):
        found = set(br._skills_missing_compat_from_fs())
        self.assertIn(self.missing_dir / "SKILL.md", found)
        self.assertNotIn(self.compat_dir / "SKILL.md", found)   # has compatibility
        self.assertNotIn(self.legacy_dir / "SKILL.md", found)   # has compatible-with


if __name__ == "__main__":
    unittest.main(verbosity=2)


class DgplTagInferenceTests(unittest.TestCase):
    """claude-dgpl: batch-remediate could not tag the 500 top-level numbered
    skills (skills/NN-topic/...) because _category_from_path only understood the
    plugins/ tree. It now handles the legacy skills/ tree, and TAG_MAP carries
    the 20 numbered categories."""

    def test_category_from_numbered_skills_tree(self):
        p = br.REPO_ROOT / "skills" / "01-devops-basics" / "x" / "SKILL.md"
        self.assertEqual(br._category_from_path(p), "01-devops-basics")

    def test_category_from_plugins_tree_still_works(self):
        p = br.PLUGINS_ROOT / "security" / "pentest" / "skills" / "q" / "SKILL.md"
        self.assertEqual(br._category_from_path(p), "security")

    def test_infer_tags_for_numbered_skill(self):
        p = br.REPO_ROOT / "skills" / "07-ml-training" / "x" / "SKILL.md"
        self.assertEqual(br.infer_tags(p), ["ai", "machine-learning"])

    def test_all_twenty_numbered_dirs_are_mapped(self):
        for n, name in enumerate(
            [
                "devops-basics", "devops-advanced", "security-fundamentals",
                "security-advanced", "frontend-dev", "backend-dev", "ml-training",
                "ml-deployment", "test-automation", "performance-testing",
                "data-pipelines", "data-analytics", "aws-skills", "gcp-skills",
                "api-development", "api-integration", "technical-docs",
                "visual-content", "business-automation", "enterprise-workflows",
            ],
            start=1,
        ):
            cat = f"{n:02d}-{name}"
            self.assertIn(cat, br.TAG_MAP, cat)
            self.assertTrue(br.TAG_MAP[cat], f"{cat} has empty tags")

    def test_unmapped_path_still_returns_none(self):
        self.assertIsNone(br._category_from_path(br.REPO_ROOT / "README.md"))


AGENT_WITH_COLOR_AND_INVALID = """\
---
name: test-agent
description: An A-grade agent used to pin the color-survival contract.
tools: Read, Grep
model: sonnet
color: blue
version: 1.0.0
author: Test <test@example.com>
tags: [test]
capabilities: [analysis]
expertise_level: expert
---
# Body
"""

AGENT_REQUIRED_ONLY = """\
---
name: clean-agent
description: A fully compliant agent carrying only the kernel-floor 8 fields.
tools: Read
model: sonnet
color: green
version: 1.0.0
author: Test <test@example.com>
tags: [test]
---
# Body
"""


class ColorSurvivalTests(unittest.TestCase):
    """2026-07-14 ops review P1: DEPRECATED_AGENT_FIELDS wrongly contained
    `color` — a kernel-floor-8 REQUIRED agent field — so --fix-agents would
    have stripped it from every A-grade agent in the corpus (255+ files).
    These tests pin: (a) the removable set can never contain a required field,
    (b) `color` survives remediation, (c) a compliant agent is never selected,
    (d) the removable set stays derived from the canonical validator."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        self.root = root
        plugins = root / "plugins"
        self.agents_dir = plugins / "cat" / "p" / "agents"
        self.agents_dir.mkdir(parents=True)
        self.flagged = self.agents_dir / "test-agent.md"
        self.flagged.write_text(AGENT_WITH_COLOR_AND_INVALID, encoding="utf-8")
        self.clean = self.agents_dir / "clean-agent.md"
        self.clean.write_text(AGENT_REQUIRED_ONLY, encoding="utf-8")

        self._orig = {k: getattr(br, k) for k in ("REPO_ROOT", "PLUGINS_ROOT", "DB_PATH")}
        br.REPO_ROOT = root
        br.PLUGINS_ROOT = plugins
        br.DB_PATH = root / "absent.sqlite"  # DB deliberately absent

    def tearDown(self):
        for k, v in self._orig.items():
            setattr(br, k, v)
        self._tmp.cleanup()

    def test_removable_set_never_contains_a_required_field(self):
        for field in br.AGENT_REQUIRED_FIELDS:
            self.assertNotIn(field, br.REMOVABLE_AGENT_FIELDS, field)
        self.assertIn("color", br.AGENT_REQUIRED_FIELDS)
        self.assertNotIn("color", br.REMOVABLE_AGENT_FIELDS)

    def test_color_survives_remediation_execute(self):
        changed, removed, err = br.remove_deprecated_agent_fields(self.flagged, dry_run=False)
        self.assertTrue(changed)
        self.assertIsNone(err)
        self.assertIn("capabilities", removed)
        self.assertIn("expertise_level", removed)
        self.assertNotIn("color", removed)
        text = self.flagged.read_text(encoding="utf-8")
        self.assertIn("color: blue", text)  # REQUIRED field survives
        self.assertNotIn("capabilities:", text)
        self.assertNotIn("expertise_level:", text)
        # every other kernel-floor field survives too
        for line in ("name: test-agent", "tools: Read, Grep", "model: sonnet",
                     "version: 1.0.0", "tags: [test]"):
            self.assertIn(line, text)

    def test_compliant_agent_is_not_selected_by_fs_walk(self):
        found = br._agents_with_invalid_fields_from_fs()
        self.assertIn(self.flagged, found)   # carries genuinely invalid fields
        self.assertNotIn(self.clean, found)  # color alone must NOT flag it

    def test_compliant_agent_untouched_by_fixer(self):
        before = self.clean.read_text(encoding="utf-8")
        changed, removed, err = br.remove_deprecated_agent_fields(self.clean, dry_run=False)
        self.assertFalse(changed)
        self.assertEqual(removed, [])
        self.assertIsNone(err)
        self.assertEqual(self.clean.read_text(encoding="utf-8"), before)

    def test_removable_set_matches_canonical_validator(self):
        """Pin non-divergence: removable = validator (invalid ∪ deprecated) − required."""
        validator = Path(__file__).resolve().parents[1] / "scripts" / "validate-skills-schema.py"
        spec = importlib.util.spec_from_file_location("vss_for_test", validator)
        vss = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(vss)
        expected = (
            set(vss.INVALID_AGENT_FIELDS) | set(vss.DEPRECATED_AGENT_FIELDS)
        ) - set(vss.AGENT_ALWAYS_REQUIRED) - set(br.AGENT_REQUIRED_FIELDS)
        self.assertEqual(set(br.REMOVABLE_AGENT_FIELDS), expected)

    def test_agent_db_rows_resolve_against_repo_root(self):
        """P3: DB stores repo-relative agent paths; unresolved they no-op from
        any cwd except the repo root."""
        db_path = self.root / "inv.sqlite"
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE agent_compliance (agent_path TEXT, has_invalid_fields INTEGER)")
        conn.execute(
            "INSERT INTO agent_compliance VALUES (?, 1)",
            (str(self.flagged.relative_to(self.root)),),
        )
        conn.commit()
        paths = br.get_agents_with_invalid_fields(conn)
        conn.close()
        self.assertEqual(paths, [self.flagged])
        self.assertTrue(paths[0].is_absolute())
        self.assertTrue(paths[0].is_file())


class CliGuardrailTests(unittest.TestCase):
    """--fix-agents FS fallback needs explicit consent; --dry-run beats --execute."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        plugins = root / "plugins"
        self.agents_dir = plugins / "cat" / "p" / "agents"
        self.agents_dir.mkdir(parents=True)
        self.flagged = self.agents_dir / "test-agent.md"
        self.flagged.write_text(AGENT_WITH_COLOR_AND_INVALID, encoding="utf-8")

        self._orig = {k: getattr(br, k) for k in ("REPO_ROOT", "PLUGINS_ROOT", "DB_PATH")}
        self._argv = sys.argv
        br.REPO_ROOT = root
        br.PLUGINS_ROOT = plugins
        br.DB_PATH = root / "absent.sqlite"  # DB deliberately absent

    def tearDown(self):
        sys.argv = self._argv
        for k, v in self._orig.items():
            setattr(br, k, v)
        self._tmp.cleanup()

    def _run_main(self, *argv: str) -> int:
        sys.argv = ["batch-remediate.py", *argv]
        buf_out, buf_err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err):
            return br.main()

    def test_fix_agents_refuses_silent_fs_fallback_when_db_absent(self):
        before = self.flagged.read_text(encoding="utf-8")
        rc = self._run_main("--fix-agents", "--execute")
        self.assertEqual(rc, 1)  # counted as an error -> non-zero exit
        self.assertEqual(self.flagged.read_text(encoding="utf-8"), before)  # untouched

    def test_fix_agents_runs_with_explicit_allow_fs_fallback(self):
        rc = self._run_main("--fix-agents", "--allow-fs-fallback", "--execute")
        self.assertEqual(rc, 0)
        text = self.flagged.read_text(encoding="utf-8")
        self.assertNotIn("capabilities:", text)
        self.assertIn("color: blue", text)  # required field still survives

    def test_dry_run_and_execute_are_mutually_exclusive(self):
        with self.assertRaises(SystemExit) as ctx:
            self._run_main("--fix-agents", "--dry-run", "--execute")
        self.assertEqual(ctx.exception.code, 2)
        # and nothing was written
        self.assertIn("capabilities:", self.flagged.read_text(encoding="utf-8"))


class FilterByScopeTests(unittest.TestCase):
    def test_scope_prefix_filters(self):
        paths = [
            br.REPO_ROOT / "skills" / "01-x" / "a" / "SKILL.md",
            br.PLUGINS_ROOT / "security" / "p" / "SKILL.md",
        ]
        out = br._filter_by_scope(paths, ["skills/"])
        self.assertEqual(out, [paths[0]])

    def test_scope_dedups_even_without_prefixes(self):
        p = br.REPO_ROOT / "skills" / "01-x" / "a" / "SKILL.md"
        self.assertEqual(br._filter_by_scope([p, p, p], None), [p])

    def test_multiple_prefixes(self):
        a = br.REPO_ROOT / "skills" / "01-x" / "a" / "SKILL.md"
        b = br.PLUGINS_ROOT / "saas-packs" / "skill-databases" / "w" / "s" / "SKILL.md"
        c = br.PLUGINS_ROOT / "security" / "p" / "SKILL.md"
        out = br._filter_by_scope([a, b, c], ["skills/", "plugins/saas-packs/skill-databases/"])
        self.assertEqual(set(out), {a, b})
