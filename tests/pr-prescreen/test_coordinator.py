"""Unit tests for scripts/pr-prescreen/coordinator.py.

Covers:
    - End-to-end coordinate() with mocked validator (no subprocess)
    - Classifier-output → grade-result wiring
    - status_check derivation (success on A, failure otherwise)
    - Hard-block signal propagation
    - CLI argument handling
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT))

_COORD_PATH = _REPO_ROOT / "scripts" / "pr-prescreen" / "coordinator.py"
_spec = importlib.util.spec_from_file_location("_coord", _COORD_PATH)
_coord = importlib.util.module_from_spec(_spec)
# Register before exec — the coordinator loads grade.py via importlib too
# and that needs sys.modules for dataclass to work.
sys.modules["_coord"] = _coord
_spec.loader.exec_module(_coord)

_GOLDEN = Path(__file__).parent / "golden"


def _load(name: str):
    return json.loads((_GOLDEN / name).read_text(encoding="utf-8"))


def _classifier_for_skills(skill_names: list[str]) -> dict:
    """Build a synthetic classifier output for tests."""
    return {
        "contribution_types": ["plugin", "skill"],
        "plugin_paths": ["plugins/example/test-plugin"],
        "affected_skills": skill_names,
        "affected_agents": [],
        "affected_mcp": [],
        "affected_hooks": [],
        "catalog_additions": [],
        "sources_additions": [],
        "file_categories": {"md": 1},
        "touches_workflows": False,
        "touches_frontend": False,
        "touches_scripts": False,
        "touches_tests": False,
        "unknown": False,
        "unmatched": [],
    }


# =============================================================================
# End-to-end coordinate()
# =============================================================================


class TestCoordinate:
    def test_a_grade_skill_produces_pass_verdict(self):
        classifier = _classifier_for_skills(["clean-skill"])
        validator_results = _load("a-grade.json")
        result = _coord.coordinate(
            classifier, validator_results=validator_results
        )
        assert result["grade"] == "A"
        assert result["verdict"] == "PASS"
        assert result["status_check"] == "success"

    def test_c_grade_skill_produces_changes_requested_failure(self):
        classifier = _classifier_for_skills(["missing-prerequisites"])
        validator_results = _load("c-grade.json")
        result = _coord.coordinate(
            classifier, validator_results=validator_results
        )
        assert result["grade"] == "C"
        assert result["verdict"] == "CHANGES_REQUESTED"
        assert result["status_check"] == "failure"

    def test_fatal_validator_produces_hard_block(self):
        classifier = _classifier_for_skills(["broken-yaml"])
        validator_results = _load("f-grade-fatal.json")
        result = _coord.coordinate(
            classifier, validator_results=validator_results
        )
        assert result["verdict"] == "HARD_BLOCK"
        assert result["status_check"] == "failure"

    def test_hard_block_signal_overrides_passing_grade(self):
        classifier = _classifier_for_skills(["clean-skill"])
        validator_results = _load("a-grade.json")
        result = _coord.coordinate(
            classifier,
            validator_results=validator_results,
            hard_block_signals=["secret detected in diff"],
        )
        assert result["grade"] == "F"
        assert result["verdict"] == "HARD_BLOCK"
        assert result["status_check"] == "failure"

    def test_doc_only_pr_passes_without_invoking_validator(self):
        """Reviewer fix #840: a doc-only PR (no affected_skills/agents/mcp/
        hooks/catalog_additions) must PASS without invoking the validator.
        Blocking these would block every README typo fix touching a plugin
        dir — the exact PR-class the new track was supposed to UN-stick."""
        classifier = {
            "contribution_types": ["doc"],
            "plugin_paths": [],
            "affected_skills": [],
            "affected_agents": [],
            "affected_mcp": [],
            "affected_hooks": [],
            "catalog_additions": [],
            "sources_additions": [],
            "file_categories": {"md": 1},
            "touches_workflows": False,
            "touches_frontend": False,
            "touches_scripts": False,
            "touches_tests": False,
            "unknown": False,
            "unmatched": [],
        }
        validator_called = False

        def fake_invoker(skill_paths):
            nonlocal validator_called
            validator_called = True
            return []

        result = _coord.coordinate(
            classifier, validator_results=None, validator_invoker=fake_invoker
        )
        assert result["verdict"] == "PASS"
        assert result["grade"] == "A"
        assert result["status_check"] == "success"
        assert not validator_called, "validator should not be invoked for doc-only PRs"

    def test_doc_only_pr_with_hard_block_signal_still_blocks(self):
        """Even a doc-only PR is HARD_BLOCK if a hard-block signal fires
        (e.g. secret in diff). The doc-only fast-path doesn't bypass that."""
        classifier = {
            "contribution_types": ["doc"],
            "plugin_paths": [],
            "affected_skills": [],
            "affected_agents": [],
            "affected_mcp": [],
            "affected_hooks": [],
            "catalog_additions": [],
            "sources_additions": [],
            "file_categories": {"md": 1},
            "touches_workflows": False,
            "touches_frontend": False,
            "touches_scripts": False,
            "touches_tests": False,
            "unknown": False,
            "unmatched": [],
        }
        result = _coord.coordinate(
            classifier,
            validator_results=None,
            hard_block_signals=["secret detected in diff"],
        )
        assert result["verdict"] == "HARD_BLOCK"

    def test_validator_invoker_is_called_with_resolved_paths(self):
        """When validator_results=None, the coordinator must invoke the
        injected validator_invoker with the resolved skill paths."""
        classifier = _classifier_for_skills(["my-skill"])
        called_with: list = []

        def fake_invoker(skill_paths):
            called_with.append(list(skill_paths))
            return _load("a-grade.json")

        _coord.coordinate(
            classifier,
            validator_results=None,
            validator_invoker=fake_invoker,
        )
        # _resolve_skill_paths returns [] when no real file exists under
        # the synthetic plugin path; the invoker gets called with []
        assert called_with == [[]]


# =============================================================================
# Embedded grade pieces (verify the coordinator surfaces what grade.py emits)
# =============================================================================


class TestCoordinateOutputShape:
    def test_output_includes_classifier_echo(self):
        classifier = _classifier_for_skills(["clean-skill"])
        result = _coord.coordinate(classifier, validator_results=_load("a-grade.json"))
        assert result["classifier"] == classifier

    def test_output_includes_comment(self):
        classifier = _classifier_for_skills(["clean-skill"])
        result = _coord.coordinate(classifier, validator_results=_load("a-grade.json"))
        assert "✅" in result["comment"]

    def test_output_includes_deltas(self):
        classifier = _classifier_for_skills(["missing-prereq"])
        result = _coord.coordinate(classifier, validator_results=_load("c-grade.json"))
        assert result["deltas"]
        assert result["deltas"][0]["current_grade"] == "C"

    def test_output_status_check_is_success_only_for_a(self):
        for fixture, expected_status in [
            ("a-grade.json", "success"),
            ("b-grade.json", "failure"),
            ("c-grade.json", "failure"),
            ("d-grade.json", "failure"),
            ("f-grade-fatal.json", "failure"),
        ]:
            classifier = _classifier_for_skills(["test"])
            result = _coord.coordinate(classifier, validator_results=_load(fixture))
            assert result["status_check"] == expected_status, (
                f"{fixture}: expected {expected_status}, got {result['status_check']}"
            )


# =============================================================================
# CLI smoke test
# =============================================================================


class TestCLI:
    def test_cli_writes_comment_and_verdict_files(self, tmp_path):
        # Build classifier output file
        classifier_path = tmp_path / "classifier.json"
        classifier_path.write_text(
            json.dumps(_classifier_for_skills(["test-skill"])), encoding="utf-8"
        )
        validator_path = tmp_path / "validator.json"
        validator_path.write_text(json.dumps(_load("a-grade.json")), encoding="utf-8")
        comment_path = tmp_path / "comment.md"
        verdict_path = tmp_path / "verdict.json"

        exit_code = _coord.main([
            "--classifier-output", str(classifier_path),
            "--validator-results-file", str(validator_path),
            "--comment-output", str(comment_path),
            "--verdict-output", str(verdict_path),
        ])
        assert exit_code == 0
        assert comment_path.exists()
        assert verdict_path.exists()

        # Verdict JSON should NOT include the embedded comment markdown
        verdict = json.loads(verdict_path.read_text())
        assert "comment" not in verdict
        assert verdict["grade"] == "A"
        assert verdict["status_check"] == "success"

    def test_cli_missing_classifier_file_exits_2(self, tmp_path):
        exit_code = _coord.main([
            "--classifier-output", str(tmp_path / "missing.json"),
        ])
        assert exit_code == 2

    def test_resolve_skill_paths_rejects_traversal(self, tmp_path):
        """Reviewer fix #840 (security): _resolve_skill_paths must reject
        path-traversal attempts that would resolve outside the repo root."""
        # A malicious classifier outputs a skill name with ../ traversal.
        # The function should silently drop it (returning an empty list)
        # rather than constructing a path outside the repo.
        result = _coord._resolve_skill_paths(
            affected_skills=["../../../etc"],
            plugin_paths=["plugins/security/example"],
        )
        assert result == []

    def test_is_within_repo_returns_false_for_traversal(self):
        """The bounds-check helper is the linchpin of the traversal fix."""
        from pathlib import Path as _P
        # Construct a path that, after resolution, escapes the repo
        bad = _coord._REPO_ROOT / "../../etc/passwd"
        assert _coord._is_within_repo(bad) is False
        # Sanity-check a known-good path resolves as inside
        good = _coord._REPO_ROOT / "scripts" / "pr-prescreen" / "grade.py"
        assert _coord._is_within_repo(good) is True

    def test_cli_hard_block_signal_arg(self, tmp_path):
        classifier_path = tmp_path / "classifier.json"
        classifier_path.write_text(
            json.dumps(_classifier_for_skills(["test-skill"])), encoding="utf-8"
        )
        validator_path = tmp_path / "validator.json"
        validator_path.write_text(json.dumps(_load("a-grade.json")), encoding="utf-8")
        verdict_path = tmp_path / "verdict.json"

        exit_code = _coord.main([
            "--classifier-output", str(classifier_path),
            "--validator-results-file", str(validator_path),
            "--verdict-output", str(verdict_path),
            "--hard-block-signal", "test signal",
        ])
        assert exit_code == 0
        verdict = json.loads(verdict_path.read_text())
        assert verdict["verdict"] == "HARD_BLOCK"
        assert "test signal" in verdict["hard_block_signals"]
