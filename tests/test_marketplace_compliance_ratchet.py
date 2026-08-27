"""Regression coverage for Blueprint 727 E6.3's R1 comparator."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check-marketplace-compliance-baseline.py"


def load_module():
    spec = importlib.util.spec_from_file_location("marketplace_compliance_ratchet", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load ratchet")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MarketplaceComplianceRatchetTests(unittest.TestCase):
    def setUp(self):
        self.ratchet = load_module()

    def test_existing_baselined_debt_passes_r1(self):
        baseline = {"entries": ["a/SKILL.md :: E-ONE :: name"]}
        current = {"entries": ["a/SKILL.md :: E-ONE :: name"]}
        self.assertEqual(self.ratchet.compare(baseline, current), [])

    def test_planted_new_triple_fails_r1(self):
        baseline = {"entries": ["a/SKILL.md :: E-ONE :: name"]}
        current = {
            "entries": [
                "a/SKILL.md :: E-ONE :: name",
                "b/SKILL.md :: E-MISSING-REQUIRED-FIELD :: author",
            ]
        }
        self.assertEqual(
            self.ratchet.compare(baseline, current),
            ["b/SKILL.md :: E-MISSING-REQUIRED-FIELD :: author"],
        )

    def test_malformed_entries_fail_closed(self):
        with self.assertRaises(ValueError):
            self.ratchet.compare({"entries": "not-a-list"}, {"entries": []})


if __name__ == "__main__":
    unittest.main()
