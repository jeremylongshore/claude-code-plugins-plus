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

import importlib.util
import sqlite3
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
