"""Regression tests for the root catalog structural invariants."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate-catalog-invariants.py"


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_catalog_invariants", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CatalogInvariantTests(unittest.TestCase):
    def test_name_validation_fails_closed_on_invalid_rows(self):
        validator = load_validator()

        self.assertEqual(
            validator.catalog_name_errors([{}, {"name": ""}, {"name": 7}, "not-an-object"]),
            [
                "catalog row 0: `name` must be a non-empty string",
                "catalog row 1: `name` must be a non-empty string",
                "catalog row 2: `name` must be a non-empty string",
                "catalog row 3: expected an object",
            ],
        )

    def test_main_refuses_duplicate_plugin_names(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog_dir = root / ".claude-plugin"
            plugin_dir = root / "plugins" / "community" / "alpha"
            catalog_dir.mkdir()
            plugin_dir.mkdir(parents=True)
            (plugin_dir / "package.json").write_text("{}")
            duplicate_plugins = [
                {"name": "alpha", "source": "./plugins/community/alpha", "category": "community"},
                {"name": "alpha", "source": "./plugins/community/alpha", "category": "community"},
            ]
            extended = catalog_dir / "marketplace.extended.json"
            synced = catalog_dir / "marketplace.json"
            payload = json.dumps({"plugins": duplicate_plugins})
            extended.write_text(payload)
            synced.write_text(payload)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            subprocess.run(["git", "-C", str(root), "add", "."], check=True)

            validator.ROOT = root
            validator.EXTENDED = extended
            validator.SYNCED = synced
            validator.CANONICAL_CATALOGS = {path.relative_to(root).as_posix() for path in (extended, synced)}
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = validator.main()

            self.assertEqual(result, 1)
            self.assertIn("duplicate plugin name `alpha` appears 2 times", output.getvalue())

    def test_canonical_catalogs_are_not_shadows(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".claude-plugin").mkdir()
            for name in ("marketplace.extended.json", "marketplace.json"):
                (root / ".claude-plugin" / name).write_text("{}")
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            subprocess.run(["git", "-C", str(root), "add", "."], check=True)

            self.assertEqual(validator.tracked_catalog_shadows(root), [])

    def test_tracked_backup_is_a_catalog_shadow(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".claude-plugin").mkdir()
            for name in ("marketplace.extended.json", "marketplace.json"):
                (root / ".claude-plugin" / name).write_text("{}")
            backup = root / ".claude-plugin" / "marketplace.extended.json.backup"
            backup.write_text("{}")
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            subprocess.run(["git", "-C", str(root), "add", "."], check=True)

            self.assertEqual(
                validator.tracked_catalog_shadows(root),
                [".claude-plugin/marketplace.extended.json.backup"],
            )

    def test_unrelated_json_is_not_a_catalog_shadow(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".claude-plugin").mkdir()
            for name in ("marketplace.extended.json", "marketplace.json", "plugin-metadata.json"):
                (root / ".claude-plugin" / name).write_text("{}")
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            subprocess.run(["git", "-C", str(root), "add", "."], check=True)

            self.assertEqual(validator.tracked_catalog_shadows(root), [])

    def test_missing_canonical_catalog_fails_closed(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".claude-plugin").mkdir()
            (root / ".claude-plugin" / "plugin-metadata.json").write_text("{}")
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            subprocess.run(["git", "-C", str(root), "add", "."], check=True)

            with self.assertRaisesRegex(validator.CatalogInventoryError, "canonical root catalogs are not tracked"):
                validator.tracked_catalog_shadows(root)

    def test_main_refuses_tracked_catalog_shadow(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog_dir = root / ".claude-plugin"
            catalog_dir.mkdir()
            extended = catalog_dir / "marketplace.extended.json"
            synced = catalog_dir / "marketplace.json"
            extended.write_text('{"plugins": []}')
            synced.write_text('{"plugins": []}')
            (catalog_dir / "marketplace.extended.json.backup").write_text("{}")
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            subprocess.run(["git", "-C", str(root), "add", "."], check=True)

            validator.ROOT = root
            validator.EXTENDED = extended
            validator.SYNCED = synced
            validator.CANONICAL_CATALOGS = {path.relative_to(root).as_posix() for path in (extended, synced)}
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = validator.main()

            self.assertEqual(result, 1)
            self.assertIn("tracked catalog shadow", output.getvalue())


if __name__ == "__main__":
    unittest.main()
