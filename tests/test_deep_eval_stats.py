"""
Tests for deep_eval.stats — statistical confidence intervals and metrics.

Uses seed-controlled randomness and pre-computed test data for deterministic CI.
"""

import sys
from pathlib import Path

# Add scripts/ to path so deep_eval is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from deep_eval.stats import (
    wilson_score_ci,
    bootstrap_ci,
    clopper_pearson_ci,
    coefficient_of_variation,
    cohens_kappa,
    weighted_composite,
)


class TestWilsonScoreCI:
    def test_zero_total(self):
        assert wilson_score_ci(0, 0) == (0.0, 0.0)

    def test_all_successes(self):
        lower, upper = wilson_score_ci(100, 100)
        assert lower > 0.95
        assert upper <= 1.0

    def test_no_successes(self):
        lower, upper = wilson_score_ci(0, 100)
        assert lower >= 0.0
        assert upper < 0.05

    def test_half_successes(self):
        lower, upper = wilson_score_ci(50, 100)
        assert 0.35 < lower < 0.50
        assert 0.50 < upper < 0.65

    def test_small_sample(self):
        """Wilson should still work with small samples (unlike normal approx)."""
        lower, upper = wilson_score_ci(1, 3)
        assert 0.0 < lower < 0.5
        assert 0.3 < upper < 1.0

    def test_confidence_levels(self):
        """Higher confidence = wider interval."""
        _, upper_90 = wilson_score_ci(50, 100, confidence=0.90)
        _, upper_95 = wilson_score_ci(50, 100, confidence=0.95)
        _, upper_99 = wilson_score_ci(50, 100, confidence=0.99)
        assert upper_90 <= upper_95 <= upper_99


class TestBootstrapCI:
    def test_empty_values(self):
        assert bootstrap_ci([]) == (0.0, 0.0)

    def test_single_value(self):
        assert bootstrap_ci([42.0]) == (42.0, 42.0)

    def test_deterministic_with_seed(self):
        """Same seed = same result."""
        values = [10.0, 20.0, 30.0, 40.0, 50.0]
        ci1 = bootstrap_ci(values, seed=42)
        ci2 = bootstrap_ci(values, seed=42)
        assert ci1 == ci2

    def test_different_seeds(self):
        """Different seeds may give different results."""
        values = [10.0, 20.0, 30.0, 40.0, 50.0]
        ci1 = bootstrap_ci(values, seed=42)
        ci2 = bootstrap_ci(values, seed=99)
        # They CAN be equal by chance, but usually won't be
        # Just verify they're both valid
        assert ci1[0] <= ci1[1]
        assert ci2[0] <= ci2[1]

    def test_bounds_contain_mean(self):
        values = [10.0, 20.0, 30.0, 40.0, 50.0]
        lower, upper = bootstrap_ci(values, seed=42)
        mean = sum(values) / len(values)
        assert lower <= mean <= upper

    def test_uniform_values(self):
        """All same values = CI is just that value."""
        lower, upper = bootstrap_ci([50.0] * 10, seed=42)
        assert abs(lower - 50.0) < 0.001
        assert abs(upper - 50.0) < 0.001

    def test_pre_computed_data(self):
        """Test with pre-computed data mimicking 48 success + 2 failure pattern."""
        values = [1.0] * 48 + [0.0] * 2  # 96% success rate
        lower, upper = bootstrap_ci(values, seed=42)
        assert 0.85 < lower < 1.0
        assert 0.90 < upper <= 1.0


class TestClopperPearsonCI:
    def test_zero_total(self):
        assert clopper_pearson_ci(0, 0) == (0.0, 0.0)

    def test_all_successes(self):
        lower, upper = clopper_pearson_ci(100, 100)
        assert lower > 0.9
        assert upper == 1.0

    def test_no_successes(self):
        lower, upper = clopper_pearson_ci(0, 100)
        assert lower == 0.0
        assert upper < 0.1

    def test_wider_than_wilson(self):
        """Clopper-Pearson is conservative (wider than Wilson)."""
        w_lower, w_upper = wilson_score_ci(30, 100)
        cp_lower, cp_upper = clopper_pearson_ci(30, 100)
        # CP should be at least as wide
        assert cp_lower <= w_lower + 0.01  # small tolerance
        assert cp_upper >= w_upper - 0.01


class TestCoefficientOfVariation:
    def test_empty(self):
        assert coefficient_of_variation([]) == 0.0

    def test_single_value(self):
        assert coefficient_of_variation([42.0]) == 0.0

    def test_uniform(self):
        """All same values = CV is 0."""
        assert coefficient_of_variation([5.0, 5.0, 5.0]) == 0.0

    def test_known_cv(self):
        """Values [1, 2, 3] have known CV."""
        cv = coefficient_of_variation([1.0, 2.0, 3.0])
        assert 0.4 < cv < 0.6  # CV = 1/2 = 0.5

    def test_higher_spread_higher_cv(self):
        cv_narrow = coefficient_of_variation([49.0, 50.0, 51.0])
        cv_wide = coefficient_of_variation([10.0, 50.0, 90.0])
        assert cv_wide > cv_narrow


class TestCohensKappa:
    def test_perfect_agreement(self):
        rater1 = [0, 1, 2, 0, 1, 2]
        rater2 = [0, 1, 2, 0, 1, 2]
        assert cohens_kappa(rater1, rater2) == 1.0

    def test_no_agreement(self):
        """Systematic disagreement should give kappa < 0."""
        rater1 = [0, 0, 0, 1, 1, 1]
        rater2 = [1, 1, 1, 0, 0, 0]
        kappa = cohens_kappa(rater1, rater2)
        assert kappa < 0

    def test_empty(self):
        assert cohens_kappa([], []) == 0.0

    def test_partial_agreement(self):
        rater1 = [0, 1, 2, 0, 1, 2]
        rater2 = [0, 1, 1, 0, 2, 2]  # 4/6 agree
        kappa = cohens_kappa(rater1, rater2)
        assert 0.0 < kappa < 1.0


class TestWeightedComposite:
    def test_empty_scores(self):
        assert weighted_composite({}, {"a": 0.5, "b": 0.5}) == 0.0

    def test_equal_weights(self):
        scores = {"a": 80, "b": 60}
        weights = {"a": 0.5, "b": 0.5}
        assert weighted_composite(scores, weights) == 70.0

    def test_unequal_weights(self):
        scores = {"a": 100, "b": 0}
        weights = {"a": 0.75, "b": 0.25}
        assert weighted_composite(scores, weights) == 75.0

    def test_renormalization(self):
        """When a dimension is missing, weights should renormalize."""
        scores = {"a": 80}  # b is missing
        weights = {"a": 0.5, "b": 0.5}
        # a gets all the weight (renormalized to 1.0)
        assert weighted_composite(scores, weights) == 80.0

    def test_clamped_to_100(self):
        scores = {"a": 150}
        weights = {"a": 1.0}
        assert weighted_composite(scores, weights) == 100.0

    def test_clamped_to_0(self):
        scores = {"a": -50}
        weights = {"a": 1.0}
        assert weighted_composite(scores, weights) == 0.0
