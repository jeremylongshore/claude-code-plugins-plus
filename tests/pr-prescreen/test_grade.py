"""Unit tests for scripts/pr-prescreen/grade.py — PR-level grade composer.

Covers:
    - Score → grade mapping (band boundaries)
    - Grade band lookups
    - points_to_next_grade arithmetic
    - SkillFinding extraction from validator output
    - Overall compose_grade() with golden fixtures (A/B/C/D/F + mixed)
    - render_comment() output structure
    - Hard-block signals always force F + HARD_BLOCK
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT))

_GRADE_PATH = _REPO_ROOT / "scripts" / "pr-prescreen" / "grade.py"
_spec = importlib.util.spec_from_file_location("_grade", _GRADE_PATH)
_grade = importlib.util.module_from_spec(_spec)
# dataclass-decorator needs the module registered in sys.modules during exec.
sys.modules["_grade"] = _grade
_spec.loader.exec_module(_grade)

_GOLDEN = Path(__file__).parent / "golden"


def _load(name: str):
    return json.loads((_GOLDEN / name).read_text(encoding="utf-8"))


# =============================================================================
# score_to_grade — band boundaries
# =============================================================================


@pytest.mark.parametrize(
    "score, expected",
    [
        (100, "A"),
        (95, "A"),
        (90, "A"),  # band low
        (89, "B"),  # B band high
        (85, "B"),
        (80, "B"),  # B band low
        (79, "C"),
        (75, "C"),
        (70, "C"),  # C band low
        (69, "D"),
        (65, "D"),
        (60, "D"),  # D band low
        (59, "F"),
        (0, "F"),
        (None, "F"),  # None defends against null score
    ],
)
def test_score_to_grade_boundaries(score, expected):
    assert _grade.score_to_grade(score) == expected


# =============================================================================
# grade_to_band — lookup table
# =============================================================================


@pytest.mark.parametrize(
    "grade, low, high",
    [
        ("A", 90, 100),
        ("B", 80, 89),
        ("C", 70, 79),
        ("D", 60, 69),
        ("F", 0, 59),
        ("a", 90, 100),  # case-insensitive
    ],
)
def test_grade_to_band(grade, low, high):
    assert _grade.grade_to_band(grade) == (low, high)


# =============================================================================
# points_to_next_grade — arithmetic
# =============================================================================


def test_points_to_next_grade_b_to_a():
    """A 85 (B) needs +5 pts to hit 90 (A low)."""
    assert _grade.points_to_next_grade(85, "B") == 5


def test_points_to_next_grade_c_to_b():
    """A 75 (C) needs +5 pts to hit 80 (B low) — next BAND, not next to A."""
    assert _grade.points_to_next_grade(75, "C") == 5


def test_points_to_next_grade_d_to_c():
    assert _grade.points_to_next_grade(65, "D") == 5


def test_points_to_next_grade_a_already_top():
    """An A-grade score has 0 points to next (we're at the top)."""
    assert _grade.points_to_next_grade(95, "A") == 0


def test_points_to_next_grade_at_band_low():
    """A 80 (B-low) needs +10 pts to hit 90 (A low)."""
    assert _grade.points_to_next_grade(80, "B") == 10


def test_points_to_next_grade_score_above_band_returns_0_not_1():
    """Reviewer fix #840: when validator's grade and score disagree (e.g.
    grade='C' but score=85), the function used to floor at 1. Now floors at 0."""
    assert _grade.points_to_next_grade(85, "C") == 0


# =============================================================================
# points_to_a (NEW — distance to A, not just next band)
# =============================================================================


@pytest.mark.parametrize(
    "score, expected",
    [
        (95, 0),   # already A
        (90, 0),   # at A floor
        (85, 5),
        (75, 15),  # the case reviewer flagged — C-grade is 15 to A, not 5
        (65, 25),
        (50, 40),
        (0, 90),
    ],
)
def test_points_to_a(score, expected):
    assert _grade.points_to_a(score) == expected


# =============================================================================
# extract_skill_findings — pull deltas from validator results
# =============================================================================


class TestExtractSkillFindings:
    def test_a_grade_results_produce_no_findings(self):
        records = _load("a-grade.json")
        findings = _grade.extract_skill_findings(records)
        assert findings == []  # nothing actionable; everything is A

    def test_b_grade_produces_finding_with_points_to_a(self):
        records = _load("b-grade.json")
        findings = _grade.extract_skill_findings(records)
        assert len(findings) == 1
        f = findings[0]
        assert f.current_grade == "B"
        assert f.current_score == 85
        assert f.points_to_a == 5  # 85 → 90 (A floor)
        assert f.points_to_next_band == 5  # B → A, same as above
        assert len(f.warnings) == 2

    def test_c_grade_finding(self):
        """A C-grade skill is +5 to B (next band) and +15 to A (the bar)."""
        findings = _grade.extract_skill_findings(_load("c-grade.json"))
        assert len(findings) == 1
        f = findings[0]
        assert f.current_grade == "C"
        assert f.current_score == 75
        assert f.points_to_a == 15        # 75 → 90 (THE bar)
        assert f.points_to_next_band == 5  # 75 → 80 (next band)

    def test_d_grade_finding_carries_errors(self):
        findings = _grade.extract_skill_findings(_load("d-grade.json"))
        assert len(findings) == 1
        assert findings[0].current_grade == "D"
        assert findings[0].current_score == 65
        assert len(findings[0].errors) == 2

    def test_fatal_entry_becomes_f_finding(self):
        findings = _grade.extract_skill_findings(_load("f-grade-fatal.json"))
        assert len(findings) == 1
        assert findings[0].current_grade == "F"
        assert findings[0].current_score == 0
        assert findings[0].points_to_a == 90  # F → A is 90
        assert "parse error" in findings[0].errors[0].lower()

    def test_mixed_results_sort_worst_first(self):
        findings = _grade.extract_skill_findings(_load("mixed-a-b-c.json"))
        # A-grade entry excluded; C and B remain. C is weaker, should be first.
        grades_in_order = [f.current_grade for f in findings]
        assert grades_in_order == ["C", "B"]


# =============================================================================
# compose_grade — the main entry point
# =============================================================================


class TestComposeGrade:
    def test_a_grade_input_gives_pass_verdict(self):
        result = _grade.compose_grade(_load("a-grade.json"))
        assert result["grade"] == "A"
        assert result["verdict"] == "PASS"
        assert result["score"] == 95
        assert result["deltas"] == []
        assert "PASS" in result["summary_line"]

    def test_b_grade_input_gives_changes_requested(self):
        result = _grade.compose_grade(_load("b-grade.json"))
        assert result["grade"] == "B"
        assert result["verdict"] == "CHANGES_REQUESTED"
        assert result["score"] == 85

    def test_c_grade_input_gives_changes_requested(self):
        result = _grade.compose_grade(_load("c-grade.json"))
        assert result["grade"] == "C"
        assert result["verdict"] == "CHANGES_REQUESTED"

    def test_d_grade_input_gives_changes_requested(self):
        result = _grade.compose_grade(_load("d-grade.json"))
        assert result["grade"] == "D"
        assert result["verdict"] == "CHANGES_REQUESTED"

    def test_fatal_gives_hard_block(self):
        result = _grade.compose_grade(_load("f-grade-fatal.json"))
        assert result["grade"] == "F"
        assert result["verdict"] == "HARD_BLOCK"
        assert result["hard_block_signals"]

    def test_mixed_grade_uses_weakest(self):
        """Mixed A + B + C → PR grade is C (weakest link)."""
        result = _grade.compose_grade(_load("mixed-a-b-c.json"))
        assert result["grade"] == "C"
        assert result["score"] == 73  # min score across components
        assert result["verdict"] == "CHANGES_REQUESTED"

    def test_empty_input_gives_hard_block(self):
        """compose_grade as the failsafe layer returns HARD_BLOCK on empty
        input. The coordinator handles the doc-only-PR-should-PASS case
        upstream and never calls compose_grade in that scenario."""
        result = _grade.compose_grade([])
        assert result["verdict"] == "HARD_BLOCK"
        assert "no validator results" in result["hard_block_signals"][0].lower()

    def test_record_with_grade_but_no_score(self):
        """Reviewer #840: missing coverage for the all-null-scores case.
        A record with only a grade field (no score) should still produce a
        finding using the grade letter directly."""
        records = [
            {"path": "x/SKILL.md", "grade": "D", "errors": 0, "warnings": 0},
            {"path": "y/SKILL.md", "grade": "B", "errors": 0, "warnings": 0},
        ]
        result = _grade.compose_grade(records)
        assert result["grade"] == "D"  # weakest of the two
        # Without explicit scores, min_score is 0 — band interpretation derives
        # from the grade letter.
        assert result["verdict"] == "CHANGES_REQUESTED"

    def test_hard_block_signal_forces_f_regardless_of_grades(self):
        """Even an all-A input must HARD_BLOCK if a hard-block signal is set."""
        result = _grade.compose_grade(
            _load("a-grade.json"),
            hard_block_signals=["secret detected in diff"],
        )
        assert result["grade"] == "F"
        assert result["verdict"] == "HARD_BLOCK"
        assert "secret detected" in result["hard_block_signals"][0]

    def test_multiple_hard_block_signals_listed(self):
        result = _grade.compose_grade(
            _load("a-grade.json"),
            hard_block_signals=["secret in diff", "no catalog entry"],
        )
        assert len(result["hard_block_signals"]) == 2
        assert "+1 more" in result["summary_line"]


# =============================================================================
# render_comment — markdown output
# =============================================================================


class TestRenderComment:
    def test_a_grade_comment_says_pass(self):
        result = _grade.compose_grade(_load("a-grade.json"))
        md = _grade.render_comment(result)
        assert "✅" in md
        assert "Grade **A**" in md
        assert "Ready to merge" in md

    def test_c_grade_comment_lists_deltas(self):
        result = _grade.compose_grade(_load("c-grade.json"))
        md = _grade.render_comment(result)
        assert "🟡" in md
        assert "Grade **C**" in md
        assert "How to reach A" in md
        assert "Prerequisites" in md  # warning message surfaces

    def test_hard_block_comment_shows_blockers(self):
        result = _grade.compose_grade(
            _load("a-grade.json"),
            hard_block_signals=["secret detected in diff"],
        )
        md = _grade.render_comment(result)
        assert "🛑" in md
        assert "HARD BLOCK" in md
        assert "secret detected" in md

    def test_every_comment_links_to_public_rubric(self):
        for fixture in ["a-grade.json", "b-grade.json", "c-grade.json", "d-grade.json"]:
            result = _grade.compose_grade(_load(fixture))
            md = _grade.render_comment(result)
            assert "tonsofskills.com/grading" in md, f"missing rubric URL in {fixture}"

    def test_comment_truncates_long_delta_list(self):
        """A PR with 10 weak skills should show only the first 5 in the comment."""
        records = [
            {
                "path": f"plugins/x/skills/weak-{i}/SKILL.md",
                "score": 75,
                "grade": "C",
                "errors": 0,
                "warnings": 1,
                "warning_messages": [f"finding {i}"],
            }
            for i in range(10)
        ]
        result = _grade.compose_grade(records)
        md = _grade.render_comment(result)
        assert "… and 5 more component(s)" in md


# =============================================================================
# Determinism + stability
# =============================================================================


def test_compose_grade_is_deterministic():
    records = _load("mixed-a-b-c.json")
    r1 = _grade.compose_grade(records)
    r2 = _grade.compose_grade(records)
    assert r1 == r2


def test_render_comment_is_deterministic():
    records = _load("mixed-a-b-c.json")
    md1 = _grade.render_comment(_grade.compose_grade(records))
    md2 = _grade.render_comment(_grade.compose_grade(records))
    assert md1 == md2
