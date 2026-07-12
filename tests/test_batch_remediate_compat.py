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
