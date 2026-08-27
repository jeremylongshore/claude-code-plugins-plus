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

    def test_unknown_rule_id_requires_conscious_rebaseline(self):
        baseline = {"schema_version": "4.1.0", "rule_inventory": ["E-ONE"]}
        current = {"schema_version": "4.1.0", "rule_inventory": ["E-ONE", "E-NEW"]}
        self.assertEqual(
            self.ratchet.metadata_drift(baseline, current),
            ["unknown live rule id(s): E-NEW"],
        )

    def test_schema_version_drift_requires_conscious_rebaseline(self):
        baseline = {"schema_version": "4.1.0", "rule_inventory": ["E-ONE"]}
        current = {"schema_version": "4.2.0", "rule_inventory": ["E-ONE"]}
        self.assertEqual(
            self.ratchet.metadata_drift(baseline, current),
            ["schema_version drift: baseline=4.1.0, live=4.2.0"],
        )

    def test_baseline_growth_is_refused_on_a_regular_pull_request(self):
        baseline = {"entries": ["a/SKILL.md :: E-ONE :: name"]}
        current = {"entries": ["a/SKILL.md :: E-ONE :: name", "b/SKILL.md :: E-TWO :: tags"]}
        self.assertEqual(
            self.ratchet.baseline_growth_error(
                baseline,
                current,
                {"scripts/.marketplace-compliance-baseline.json", "plugins/example/SKILL.md"},
                "feature/ordinary-change",
            ),
            "baseline growth may only occur in a one-file baseline-only pull request",
        )

    def test_baseline_growth_is_only_allowed_on_the_ci_capture_branch(self):
        baseline = {"entries": ["a/SKILL.md :: E-ONE :: name"]}
        current = {"entries": ["a/SKILL.md :: E-ONE :: name", "b/SKILL.md :: E-TWO :: tags"]}
        self.assertIsNone(
            self.ratchet.baseline_growth_error(
                baseline,
                current,
                {"scripts/.marketplace-compliance-baseline.json"},
                "automation/compliance-baseline-123",
            )
        )


if __name__ == "__main__":
    unittest.main()
