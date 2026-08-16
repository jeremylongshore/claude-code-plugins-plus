"""Regression tests for the root catalog structural invariants."""

from __future__ import annotations

import importlib.util
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
            (root / ".claude-plugin" / "marketplace.extended.json").write_text("{}")
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
            (root / ".claude-plugin" / "plugin-metadata.json").write_text("{}")
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            subprocess.run(["git", "-C", str(root), "add", "."], check=True)

            self.assertEqual(validator.tracked_catalog_shadows(root), [])


if __name__ == "__main__":
    unittest.main()
