"""Regression guard for the owner-authorized Perplexity pack retirement."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PerplexityRetirementTests(unittest.TestCase):
    def test_source_and_public_entrypoints_are_absent(self) -> None:
        forbidden = (
            "plugins/saas-packs/perplexity-pack",
            "plugins/saas-packs/skill-databases/perplexity",
            "marketplace/src/pages/learn/perplexity",
        )
        for relative in forbidden:
            with self.subTest(path=relative):
                path = ROOT / relative
                populated = path.is_file() or path.is_symlink()
                if path.is_dir():
                    populated = any(item.is_file() or item.is_symlink() for item in path.rglob("*"))
                self.assertFalse(populated)

        self.assertEqual(list((ROOT / "skills/.curated").glob("perplexity-*")), [])

    def test_catalog_and_vendor_authorities_do_not_register_the_pack(self) -> None:
        catalog = json.loads(
            (ROOT / ".claude-plugin/marketplace.extended.json").read_text(encoding="utf-8")
        )
        self.assertNotIn("perplexity-pack", {row["name"] for row in catalog["plugins"]})

        vendors = json.loads(
            (ROOT / "marketplace/src/data/vendor-packs.json").read_text(encoding="utf-8")
        )
        self.assertNotIn("perplexity", {row["id"] for row in vendors["vendors"]})

    def test_generated_and_operational_surfaces_do_not_advertise_the_pack(self) -> None:
        forbidden_by_path = {
            ".claude-plugin/marketplace.json": ('"name": "perplexity-pack"',),
            "marketplace/src/data/catalog.json": ('"slug": "perplexity-pack"',),
            "marketplace/src/data/skills-index.json": ('"parentPlugin": "perplexity-pack"',),
            "marketplace/src/data/skills-catalog.json": ('"parentPlugin": "perplexity-pack"',),
            "marketplace/src/data/unified-search-index.json": ('"name": "perplexity-pack"',),
            "marketplace/src/data/npm-stats.json": (
                "@intentsolutionsio/perplexity-pack",
                "@intentsolutionsio/perplexity-skill-md-pack",
            ),
            "freshie/grades.csv": ("plugins/saas-packs/perplexity-pack/",),
            "freshie/disposition-ledger.json": ("plugins/saas-packs/perplexity-pack/",),
            "skills/.curated/MANIFEST.json": ("plugins/saas-packs/perplexity-pack/",),
            "scripts/published-count-cohorts.json": ("learn/perplexity/index.astro",),
            "pnpm-lock.yaml": ("plugins/saas-packs/perplexity-pack:",),
        }
        for relative, forbidden_values in forbidden_by_path.items():
            for forbidden in forbidden_values:
                with self.subTest(path=relative, forbidden=forbidden):
                    contents = (ROOT / relative).read_text(encoding="utf-8")
                    self.assertNotIn(forbidden, contents)

    def test_freshie_current_exports_share_the_latest_run_receipt(self) -> None:
        reports = sorted(
            (ROOT / "freshie/reports").glob("run-delta-*.json"),
            key=lambda path: int(path.stem.rsplit("-", 1)[1]),
        )
        self.assertTrue(reports)

        latest = json.loads(reports[-1].read_text(encoding="utf-8"))
        histogram = json.loads(
            (ROOT / "freshie/grade-histogram.json").read_text(encoding="utf-8")
        )
        manifest = json.loads(
            (ROOT / "skills/.curated/MANIFEST.json").read_text(encoding="utf-8")
        )

        expected_tag = f"run-{histogram['run_id']}"
        self.assertEqual(latest["to_tag"], expected_tag)
        self.assertEqual(latest["dolt_commit"], histogram["dolt_commit"])
        self.assertEqual(manifest["run_id"], histogram["run_id"])
        self.assertEqual(manifest["grade_export"]["run_id"], histogram["run_id"])


if __name__ == "__main__":
    unittest.main()
