"""Regression checks for the fail-closed curated-promotion workflow."""

from pathlib import Path
import unittest


WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "promote-curated.yml"


class PromoteCuratedWorkflowTests(unittest.TestCase):
    def test_optional_inventory_refresh_cannot_swallow_correctness_failures(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        start = text.index("- name: Rebuild inventory + grades (optional)")
        end = text.index("- name: Rebuild skills/.curated/ mirror", start)
        refresh = text[start:end]

        self.assertIn(
            "python3 scripts/validate-skills-schema.py --marketplace --populate-db freshie/inventory.sqlite\n",
            refresh,
        )
        self.assertIn("python3 freshie/scripts/dolt-sync.py\n", refresh)
        self.assertNotIn("|| true", refresh)


if __name__ == "__main__":
    unittest.main()
