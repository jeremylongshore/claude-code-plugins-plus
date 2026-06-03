"""
Tests for deep_eval.ranking — Elo competitive ranking system.

Uses pre-computed test data for deterministic results.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from deep_eval.ranking import (
    expected_score,
    update_rating,
    determine_outcome,
    run_round_robin,
    rank_skills,
    rating_confidence_interval,
    category_rankings,
    DEFAULT_RATING,
    K_FACTOR,
)


class TestExpectedScore:
    def test_equal_ratings(self):
        """Equal ratings should give 0.5 expected score."""
        assert expected_score(1500, 1500) == 0.5

    def test_higher_rating_favored(self):
        """Higher-rated player should have >0.5 expected score."""
        assert expected_score(1600, 1400) > 0.5

    def test_lower_rating_disadvantaged(self):
        assert expected_score(1400, 1600) < 0.5

    def test_symmetry(self):
        """Expected scores should sum to 1.0."""
        e_a = expected_score(1500, 1600)
        e_b = expected_score(1600, 1500)
        assert abs(e_a + e_b - 1.0) < 0.001

    def test_large_gap(self):
        """400-point gap should give ~0.91 expected score."""
        e = expected_score(1900, 1500)
        assert 0.89 < e < 0.93


class TestUpdateRating:
    def test_win_increases_rating(self):
        new = update_rating(1500, 0.5, 1.0, k=K_FACTOR)
        assert new > 1500

    def test_loss_decreases_rating(self):
        new = update_rating(1500, 0.5, 0.0, k=K_FACTOR)
        assert new < 1500

    def test_draw_no_change_at_equal(self):
        """Draw at equal expected score = no rating change."""
        new = update_rating(1500, 0.5, 0.5, k=K_FACTOR)
        assert abs(new - 1500) < 0.001

    def test_k_factor_magnitude(self):
        """K=32, win against equal opponent: +16 points."""
        new = update_rating(1500, 0.5, 1.0, k=32)
        assert abs(new - 1516) < 0.001

    def test_upset_win(self):
        """Win against stronger opponent gives big boost."""
        expected = expected_score(1400, 1600)  # ~0.24
        new = update_rating(1400, expected, 1.0, k=32)
        assert new - 1400 > 20  # Big gain


class TestDetermineOutcome:
    def test_clear_win(self):
        assert determine_outcome(80.0, 50.0) == (1.0, 0.0)

    def test_clear_loss(self):
        assert determine_outcome(50.0, 80.0) == (0.0, 1.0)

    def test_draw_within_threshold(self):
        assert determine_outcome(75.0, 73.0) == (0.5, 0.5)

    def test_exact_threshold(self):
        assert determine_outcome(75.0, 72.0) == (0.5, 0.5)

    def test_just_outside_threshold(self):
        assert determine_outcome(75.0, 71.9) == (1.0, 0.0)


class TestRoundRobin:
    def test_empty(self):
        assert run_round_robin({}) == {}

    def test_single_skill(self):
        """Single skill can't compete, gets default rating."""
        result = run_round_robin({"skill_a": 80.0})
        assert "skill_a" in result
        assert result["skill_a"]["rating"] == DEFAULT_RATING

    def test_two_skills(self):
        result = run_round_robin({"a": 90.0, "b": 60.0})
        assert result["a"]["rating"] > result["b"]["rating"]
        assert result["a"]["wins"] == 1
        assert result["b"]["losses"] == 1

    def test_three_skills_ordering(self):
        result = run_round_robin({"a": 90.0, "b": 70.0, "c": 50.0})
        ranked = rank_skills(result)
        assert ranked[0][0] == "a"
        assert ranked[-1][0] == "c"

    def test_tied_skills(self):
        result = run_round_robin({"a": 75.0, "b": 75.0})
        assert result["a"]["draws"] == 1
        assert result["b"]["draws"] == 1
        assert abs(result["a"]["rating"] - result["b"]["rating"]) < 0.01


class TestRankSkills:
    def test_sorts_descending(self):
        results = {
            "a": {"rating": 1450, "wins": 0, "losses": 1, "draws": 0, "composite_score": 60},
            "b": {"rating": 1550, "wins": 1, "losses": 0, "draws": 0, "composite_score": 90},
        }
        ranked = rank_skills(results)
        assert ranked[0][0] == "b"
        assert ranked[1][0] == "a"


class TestRatingConfidenceInterval:
    def test_empty(self):
        assert rating_confidence_interval([]) == (0.0, 0.0)

    def test_all_wins(self):
        lower, upper = rating_confidence_interval([1.0] * 10, seed=42)
        assert lower > 0.8
        assert upper <= 1.0

    def test_mixed_results(self):
        results = [1.0, 1.0, 0.5, 0.0, 1.0, 0.5]
        lower, upper = rating_confidence_interval(results, seed=42)
        assert 0.3 < lower < 0.8
        assert 0.5 < upper <= 1.0


class TestCategoryRankings:
    def test_multiple_categories(self):
        skills_by_cat = {
            "devops": {"a": 90.0, "b": 60.0},
            "testing": {"c": 80.0, "d": 70.0},
        }
        rankings = category_rankings(skills_by_cat)
        assert "devops" in rankings
        assert "testing" in rankings
        assert rankings["devops"][0][0] == "a"

    def test_single_skill_category(self):
        skills_by_cat = {"solo": {"x": 50.0}}
        rankings = category_rankings(skills_by_cat)
        assert len(rankings["solo"]) == 1
