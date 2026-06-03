"""
Tests for deep_eval.dimensions — static dimension scoring.

Uses fixture-based setup with tmp_path for SKILL.md files.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import pytest
from deep_eval.dimensions import (
    score_triggering_accuracy,
    score_orchestration_fitness,
    score_output_quality,
    score_scope_calibration,
    score_progressive_disclosure,
    score_token_efficiency,
    score_robustness,
    score_structural_completeness,
    score_code_template_quality,
    score_ecosystem_coherence,
    score_all_dimensions,
    calculate_anti_pattern_penalty,
    DIMENSION_WEIGHTS,
)
from deep_eval.badges import assign_badge


# === Fixtures ===

GOOD_SKILL_FM = {
    "name": "deploy-checker",
    "description": (
        "Validate deployment configurations before pushing to production. "
        "Use when preparing a deploy, checking Kubernetes manifests, or auditing "
        'CI/CD pipelines. Trigger with "check deploy", "/deploy-checker".'
    ),
    "allowed-tools": "Read, Bash(kubectl:*), Glob, Grep",
    "version": "1.0.0",
    "author": "Jeremy Longshore <jeremy@intentsolutions.io>",
    "license": "MIT",
    "compatible-with": "claude-code",
    "tags": ["devops", "kubernetes", "deployment"],
}

GOOD_SKILL_BODY = """# Deploy Checker

Validates deployment configurations before production push.

## Overview

Runs pre-deployment checks on Kubernetes manifests, Helm charts,
and CI/CD pipeline configurations.

## Prerequisites

- `kubectl` installed and configured
- Access to target cluster namespace

## Instructions

1. Read the deployment manifest
2. Validate resource limits are set
3. Check image tags are pinned (not :latest)
4. Verify health checks are configured
5. Report findings

## Output

Present results in this format:

```markdown
## Deployment Check Results
- Resource limits: PASS/FAIL
- Image tags: PASS/FAIL
- Health checks: PASS/FAIL
```

## Error Handling

If kubectl is not available, report the error and suggest installation.
If the manifest is malformed, provide specific YAML parse errors.
Handle timeout gracefully with retry guidance.

## Examples

```bash
kubectl get deployment -o yaml > manifest.yaml
```

```yaml
resources:
  limits:
    memory: "256Mi"
    cpu: "500m"
```

## Resources

See [Kubernetes best practices](references/k8s-best-practices.md) for details.
"""

STUB_SKILL_FM = {
    "name": "stub-skill",
    "description": "A skill.",
}

STUB_SKILL_BODY = """# Stub Skill

Does something.

## Overview

This skill does a thing.
"""


# === Tests ===


class TestTriggeringAccuracy:
    def test_good_description(self):
        result = score_triggering_accuracy(GOOD_SKILL_BODY, GOOD_SKILL_FM)
        assert result["score"] >= 70

    def test_empty_description(self):
        result = score_triggering_accuracy("", {"description": ""})
        assert result["score"] == 0

    def test_short_description(self):
        result = score_triggering_accuracy("", {"description": "A skill"})
        assert result["score"] < 30

    def test_trigger_phrases_boost(self):
        fm_with = {"description": 'Use when deploying. Trigger with "/deploy"'}
        fm_without = {"description": "Deployment validation tool"}
        score_with = score_triggering_accuracy("", fm_with)["score"]
        score_without = score_triggering_accuracy("", fm_without)["score"]
        assert score_with > score_without


class TestOrchestrationFitness:
    def test_pure_worker(self):
        result = score_orchestration_fitness(GOOD_SKILL_BODY, GOOD_SKILL_FM)
        assert result["score"] >= 80

    def test_orchestrator_penalty(self):
        body = "Launch a subagent to coordinate multiple tasks. Delegate to worker agents."
        result = score_orchestration_fitness(body, {})
        assert result["score"] < 80

    def test_fork_with_agent(self):
        fm = {"context": "fork", "agent": "Explore"}
        result = score_orchestration_fitness("Simple task", fm)
        assert result["score"] >= 80  # Minor deduction only

    def test_broad_tools_penalty(self):
        fm = {"allowed-tools": "Read, Write, Edit, Bash, Glob, Grep, WebFetch, WebSearch, TodoWrite"}
        result = score_orchestration_fitness("", fm)
        assert result["score"] < 100


class TestOutputQuality:
    def test_good_output(self):
        result = score_output_quality(GOOD_SKILL_BODY, GOOD_SKILL_FM)
        assert result["score"] >= 60

    def test_no_output_section(self):
        result = score_output_quality(STUB_SKILL_BODY, STUB_SKILL_FM)
        assert result["score"] < 40


class TestScopeCalibration:
    def test_well_scoped(self):
        result = score_scope_calibration(GOOD_SKILL_BODY, GOOD_SKILL_FM)
        assert result["score"] >= 45  # 243 words = "thin" band, + section bonus

    def test_stub_detection(self):
        result = score_scope_calibration(STUB_SKILL_BODY, STUB_SKILL_FM)
        assert result["score"] < 50


class TestProgressiveDisclosure:
    def test_with_references(self, tmp_path):
        skill_dir = tmp_path / "skills" / "test-skill"
        skill_dir.mkdir(parents=True)
        refs_dir = skill_dir / "references"
        refs_dir.mkdir()
        (refs_dir / "guide.md").write_text("# Guide\nDetailed content here.")
        skill_path = skill_dir / "SKILL.md"
        skill_path.write_text("placeholder")

        body = "[See guide](references/guide.md)\n${CLAUDE_SKILL_DIR}/scripts/run.sh"
        result = score_progressive_disclosure(body, {}, skill_path)
        assert result["score"] >= 50

    def test_without_references(self, tmp_path):
        skill_dir = tmp_path / "skills" / "test-skill"
        skill_dir.mkdir(parents=True)
        skill_path = skill_dir / "SKILL.md"
        skill_path.write_text("placeholder")

        result = score_progressive_disclosure("Short body\n" * 10, {}, skill_path)
        assert result["score"] >= 20  # Acceptable for short skills


class TestTokenEfficiency:
    def test_concise_skill(self):
        short_body = "# Title\n## Overview\nConcise.\n" * 5  # ~15 lines
        result = score_token_efficiency(short_body, GOOD_SKILL_FM)
        assert result["score"] >= 60

    def test_verbose_skill(self):
        long_body = "Line of content.\n" * 400
        result = score_token_efficiency(long_body, {"description": "x" * 500})
        assert result["score"] < 40


class TestRobustness:
    def test_has_error_handling(self):
        result = score_robustness(GOOD_SKILL_BODY, GOOD_SKILL_FM)
        assert result["score"] >= 60

    def test_no_error_handling(self):
        result = score_robustness(STUB_SKILL_BODY, STUB_SKILL_FM)
        assert result["score"] < 20


class TestStructuralCompleteness:
    def test_complete_structure(self):
        result = score_structural_completeness(GOOD_SKILL_BODY, GOOD_SKILL_FM)
        assert result["score"] >= 70

    def test_minimal_structure(self):
        result = score_structural_completeness(STUB_SKILL_BODY, STUB_SKILL_FM)
        assert result["score"] < 50


class TestCodeTemplateQuality:
    def test_good_code_blocks(self):
        result = score_code_template_quality(GOOD_SKILL_BODY, GOOD_SKILL_FM)
        assert result["score"] >= 50

    def test_no_code_blocks(self):
        body = "No code here, just text."
        fm = {"description": "Text-only skill"}
        result = score_code_template_quality(body, fm)
        assert result["score"] <= 30


class TestEcosystemCoherence:
    def test_with_tags_and_compat(self):
        result = score_ecosystem_coherence(GOOD_SKILL_BODY, GOOD_SKILL_FM)
        assert result["score"] >= 40

    def test_no_ecosystem_signals(self):
        result = score_ecosystem_coherence(STUB_SKILL_BODY, STUB_SKILL_FM)
        assert result["score"] < 20


class TestAntiPatterns:
    def test_clean_body(self):
        result = calculate_anti_pattern_penalty(GOOD_SKILL_BODY)
        assert result["count"] == 0
        assert result["penalty_pct"] == 0.0

    def test_first_person(self):
        body = "I can help you with deployment. I will check your configs."
        result = calculate_anti_pattern_penalty(body)
        assert result["count"] >= 1
        assert result["penalty_pct"] > 0

    def test_placeholder_text(self):
        body = "TODO: implement this. FIXME: broken logic."
        result = calculate_anti_pattern_penalty(body)
        assert result["count"] >= 1

    def test_penalty_floor(self):
        """Penalty should never exceed 50%."""
        body = "I can TODO FIXME [YOUR_NAME] ... I will REPLACE_ME I'm going to TBD"
        result = calculate_anti_pattern_penalty(body)
        assert result["penalty_pct"] <= 0.50


class TestScoreAllDimensions:
    def test_good_skill_composite(self):
        result = score_all_dimensions(GOOD_SKILL_BODY, GOOD_SKILL_FM)
        assert result["composite_score"] > 60
        assert len(result["dimensions"]) == 10

    def test_stub_skill_low_composite(self):
        result = score_all_dimensions(STUB_SKILL_BODY, STUB_SKILL_FM)
        assert result["composite_score"] < 50

    def test_weights_sum_to_one(self):
        total = sum(DIMENSION_WEIGHTS.values())
        assert abs(total - 1.0) < 0.001

    def test_badge_assignment_consistency(self):
        good = score_all_dimensions(GOOD_SKILL_BODY, GOOD_SKILL_FM)
        badge = assign_badge(good["composite_score"])
        # Good skill should get at least silver
        assert badge in ("established", "emerging", "flagship")
