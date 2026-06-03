"""
Integration tests for the deep eval engine.

Tests the full pipeline: dimensions → engine → badges → ranking → DB.
Uses real SKILL.md files from the repo when available.
"""

import sys
import os
import sqlite3
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import pytest
from deep_eval.engine import DeepEvalEngine
from deep_eval.badges import assign_badge, badge_info, grade_to_badge_comparison
from deep_eval.db import populate_deep_eval_db
from deep_eval.reporter import format_terminal, format_json, format_markdown, format_html


# Repo root for finding real skills
REPO_ROOT = Path(__file__).resolve().parents[1]
REAL_SKILL = REPO_ROOT / "plugins" / "skill-enhancers" / "validate-plugin" / "skills" / "validate-plugin" / "SKILL.md"


# === Fixtures ===

GOOD_FM = {
    "name": "test-good",
    "description": 'Validate configurations. Use when checking YAML. Trigger with "/validate".',
    "allowed-tools": "Read, Bash(yamllint:*), Glob",
    "version": "1.0.0",
    "author": "Test <test@test.com>",
    "license": "MIT",
    "compatible-with": "claude-code",
    "tags": ["validation", "yaml"],
}

GOOD_BODY = """# Config Validator

Validates YAML and JSON configurations.

## Overview

Checks syntax, structure, and best practices.

## Prerequisites

- `yamllint` installed

## Instructions

1. Read the config file
2. Run yamllint
3. Check for common anti-patterns
4. Report results

## Output

```markdown
## Validation Results
- Syntax: PASS
- Structure: PASS
```

## Error Handling

If yamllint is not installed, suggest: `pip install yamllint`
Handle malformed YAML with clear parse error messages.

## Examples

```bash
yamllint config.yaml
```

```yaml
server:
  port: 8080
  host: localhost
```

## Resources

See [YAML spec](https://yaml.org/spec/1.2/spec.html) for reference.
"""

STUB_FM = {"name": "stub", "description": "A stub."}
STUB_BODY = "# Stub\n\nTODO: write this.\n"


class TestEngineEvaluation:
    def test_evaluate_good_skill(self, tmp_path):
        skill_path = tmp_path / "SKILL.md"
        skill_path.write_text("placeholder")

        engine = DeepEvalEngine(use_llm=False)
        result = engine.evaluate_skill(skill_path, GOOD_BODY, GOOD_FM, letter_grade="A", deterministic_score=95)

        assert result["composite_score"] > 60
        assert result["badge"] in ("established", "emerging", "flagship")
        assert result["skill_name"] == "test-good"
        assert "static" in result["layers"]
        assert result["deterministic_score"] == 95

    def test_evaluate_stub_skill(self, tmp_path):
        skill_path = tmp_path / "SKILL.md"
        skill_path.write_text("placeholder")

        engine = DeepEvalEngine(use_llm=False)
        result = engine.evaluate_skill(skill_path, STUB_BODY, STUB_FM, letter_grade="F", deterministic_score=30)

        assert result["composite_score"] < 50
        assert result["badge"] in ("early", None)

    def test_batch_evaluation(self, tmp_path):
        skills = []
        for i, (fm, body) in enumerate([(GOOD_FM, GOOD_BODY), (STUB_FM, STUB_BODY)]):
            path = tmp_path / f"skill_{i}" / "SKILL.md"
            path.parent.mkdir()
            path.write_text("placeholder")
            skills.append({"path": str(path), "body": body, "fm": fm, "name": fm["name"], "grade": "A", "score": 90})

        engine = DeepEvalEngine(use_llm=False)
        results = engine.evaluate_batch(skills)

        assert len(results) == 2
        assert results[0]["composite_score"] > results[1]["composite_score"]

    def test_llm_layer_unavailable(self, tmp_path):
        """Without GROQ_API_KEY, LLM layer should gracefully degrade."""
        skill_path = tmp_path / "SKILL.md"
        skill_path.write_text("placeholder")

        engine = DeepEvalEngine(use_llm=True)
        result = engine.evaluate_skill(skill_path, GOOD_BODY, GOOD_FM)

        # Should still produce a result (static only)
        assert result["composite_score"] > 0
        llm_layer = result.get("layers", {}).get("llm", {})
        assert llm_layer.get("available") is False


class TestRanking:
    def test_rank_results(self, tmp_path):
        skills = []
        scores = [("high", GOOD_FM, GOOD_BODY), ("low", STUB_FM, STUB_BODY)]
        for name, fm, body in scores:
            path = tmp_path / f"{name}" / "SKILL.md"
            path.parent.mkdir()
            path.write_text("placeholder")
            skills.append({"path": str(path), "body": body, "fm": fm, "name": fm["name"], "grade": "A", "score": 90})

        engine = DeepEvalEngine(use_llm=False)
        results = engine.evaluate_batch(skills)
        rankings = engine.rank_results(results)

        assert "global_ranking" in rankings
        assert len(rankings["global_ranking"]) == 2


class TestBadges:
    def test_flagship(self):
        assert assign_badge(95) == "flagship"

    def test_established(self):
        assert assign_badge(80) == "established"

    def test_emerging(self):
        assert assign_badge(65) == "emerging"

    def test_early(self):
        assert assign_badge(45) == "early"

    def test_none(self):
        assert assign_badge(30) is None

    def test_badge_info(self):
        info = badge_info("established")
        assert info["label"] == "Established"
        assert info["level"] == "established"

    def test_grade_comparison_aligned(self):
        result = grade_to_badge_comparison("A", "flagship")
        assert result["alignment"] == "aligned"

    def test_grade_comparison_divergent(self):
        result = grade_to_badge_comparison("A", "early")
        assert result["alignment"] == "grade_higher"
        assert result["divergence"] == 3


class TestDBIntegration:
    def test_populate_and_query(self, tmp_path):
        db_path = str(tmp_path / "test.sqlite")

        skill_path = tmp_path / "SKILL.md"
        skill_path.write_text("placeholder")

        engine = DeepEvalEngine(use_llm=False)
        result = engine.evaluate_skill(skill_path, GOOD_BODY, GOOD_FM)
        summary = engine.summary([result])

        run_id = populate_deep_eval_db(db_path, [result], summary)

        # Verify data was written
        conn = sqlite3.connect(db_path)
        c = conn.cursor()

        c.execute("SELECT COUNT(*) FROM deep_eval_runs")
        assert c.fetchone()[0] == 1

        c.execute("SELECT COUNT(*) FROM deep_eval_results")
        assert c.fetchone()[0] == 1

        c.execute("SELECT composite_score, badge FROM deep_eval_results WHERE run_id=?", (run_id,))
        row = c.fetchone()
        assert row[0] > 0
        assert row[1] in ("flagship", "established", "emerging", "early", None)

        c.execute("SELECT COUNT(*) FROM deep_eval_dimensions WHERE run_id=?", (run_id,))
        dim_count = c.fetchone()[0]
        assert dim_count == 10  # 10 static dimensions

        conn.close()


class TestReporters:
    def test_terminal_format(self, tmp_path):
        skill_path = tmp_path / "SKILL.md"
        skill_path.write_text("placeholder")
        engine = DeepEvalEngine(use_llm=False)
        result = engine.evaluate_skill(skill_path, GOOD_BODY, GOOD_FM, letter_grade="A")
        summary = engine.summary([result])

        output = format_terminal([result], summary)
        assert "INTENT SOLUTIONS DEEP EVALUATION ENGINE" in output
        assert "Badge Distribution" in output

    def test_json_format(self, tmp_path):
        skill_path = tmp_path / "SKILL.md"
        skill_path.write_text("placeholder")
        engine = DeepEvalEngine(use_llm=False)
        result = engine.evaluate_skill(skill_path, GOOD_BODY, GOOD_FM)
        summary = engine.summary([result])

        import json

        output = format_json([result], summary)
        parsed = json.loads(output)
        assert parsed["version"] == "1.0.0"
        assert len(parsed["results"]) == 1

    def test_markdown_format(self, tmp_path):
        skill_path = tmp_path / "SKILL.md"
        skill_path.write_text("placeholder")
        engine = DeepEvalEngine(use_llm=False)
        result = engine.evaluate_skill(skill_path, GOOD_BODY, GOOD_FM)
        summary = engine.summary([result])

        output = format_markdown([result], summary)
        assert "# Intent Solutions Deep Evaluation Report" in output

    def test_html_format(self, tmp_path):
        skill_path = tmp_path / "SKILL.md"
        skill_path.write_text("placeholder")
        engine = DeepEvalEngine(use_llm=False)
        result = engine.evaluate_skill(skill_path, GOOD_BODY, GOOD_FM)
        summary = engine.summary([result])

        output = format_html([result], summary)
        assert "<!DOCTYPE html>" in output
        assert "Deep Evaluation Report" in output


@pytest.mark.skipif(not REAL_SKILL.exists(), reason="Real skill file not available (running outside repo)")
class TestRealSkill:
    """E2E test using a real SKILL.md from the repo."""

    def test_real_skill_evaluation(self):
        import yaml
        import re

        content = REAL_SKILL.read_text(encoding="utf-8")
        m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)
        assert m, "Failed to parse frontmatter"
        fm = yaml.safe_load(m.group(1))
        body = m.group(2)

        engine = DeepEvalEngine(use_llm=False)
        result = engine.evaluate_skill(REAL_SKILL, body, fm, letter_grade="A", deterministic_score=97)

        # A-grade real skill should get at least Emerging badge
        assert result["composite_score"] >= 60
        assert result["badge"] in ("flagship", "established", "emerging")
        assert result["elapsed_seconds"] < 5.0
