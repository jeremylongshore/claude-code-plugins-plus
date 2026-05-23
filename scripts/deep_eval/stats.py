"""
Statistical confidence intervals and metrics.

Implements standard statistical methods for scoring reliability:
- Wilson score confidence interval
- Bootstrap confidence interval
- Clopper-Pearson exact confidence interval
- Coefficient of variation
- Cohen's kappa (inter-rater agreement)

All methods are pure Python — no external dependencies.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
"""

import math
import random
from typing import List, Tuple, Optional


def wilson_score_ci(
    successes: int,
    total: int,
    confidence: float = 0.95,
) -> Tuple[float, float]:
    """
    Wilson score confidence interval for a binomial proportion.

    More accurate than the normal approximation for small samples
    and extreme proportions (near 0 or 1).

    Args:
        successes: Number of successes (e.g., skills passing a check)
        total: Total number of trials
        confidence: Confidence level (default 0.95 for 95% CI)

    Returns:
        (lower_bound, upper_bound) as proportions in [0, 1]
    """
    if total == 0:
        return (0.0, 0.0)

    # Z-score lookup for common confidence levels
    z_scores = {0.90: 1.645, 0.95: 1.96, 0.99: 2.576}
    z = z_scores.get(confidence, 1.96)

    p_hat = successes / total
    denominator = 1 + z * z / total

    center = (p_hat + z * z / (2 * total)) / denominator
    spread = z * math.sqrt((p_hat * (1 - p_hat) + z * z / (4 * total)) / total) / denominator

    lower = max(0.0, center - spread)
    upper = min(1.0, center + spread)

    return (lower, upper)


def bootstrap_ci(
    values: List[float],
    confidence: float = 0.95,
    n_bootstrap: int = 1000,
    seed: int = 42,
) -> Tuple[float, float]:
    """
    Bootstrap confidence interval for the mean.

    Resamples with replacement to estimate the sampling distribution
    of the mean, then extracts percentile-based CI bounds.

    Args:
        values: List of observed values
        confidence: Confidence level (default 0.95)
        n_bootstrap: Number of bootstrap iterations
        seed: Random seed for reproducibility

    Returns:
        (lower_bound, upper_bound)
    """
    if not values:
        return (0.0, 0.0)
    if len(values) == 1:
        return (values[0], values[0])

    rng = random.Random(seed)
    n = len(values)

    means = []
    for _ in range(n_bootstrap):
        sample = [rng.choice(values) for _ in range(n)]
        means.append(sum(sample) / n)

    means.sort()
    alpha = 1 - confidence
    lower_idx = int(math.floor(alpha / 2 * n_bootstrap))
    upper_idx = int(math.ceil((1 - alpha / 2) * n_bootstrap)) - 1

    lower_idx = max(0, min(lower_idx, n_bootstrap - 1))
    upper_idx = max(0, min(upper_idx, n_bootstrap - 1))

    return (means[lower_idx], means[upper_idx])


def clopper_pearson_ci(
    successes: int,
    total: int,
    confidence: float = 0.95,
) -> Tuple[float, float]:
    """
    Clopper-Pearson exact confidence interval for a binomial proportion.

    Conservative (wider than Wilson) — guarantees at least the nominal
    coverage probability. Uses the beta distribution quantile function
    approximated via the incomplete beta function.

    Args:
        successes: Number of successes
        total: Total number of trials
        confidence: Confidence level

    Returns:
        (lower_bound, upper_bound) as proportions in [0, 1]
    """
    if total == 0:
        return (0.0, 0.0)

    alpha = 1 - confidence

    # Use beta distribution quantiles via the regularized incomplete beta function
    # Approximation using the normal distribution for large samples
    if successes == 0:
        lower = 0.0
    else:
        lower = _beta_ppf(alpha / 2, successes, total - successes + 1)

    if successes == total:
        upper = 1.0
    else:
        upper = _beta_ppf(1 - alpha / 2, successes + 1, total - successes)

    return (max(0.0, lower), min(1.0, upper))


def _beta_ppf(p: float, a: float, b: float) -> float:
    """
    Approximate the percent point function (inverse CDF) of the beta distribution.

    Uses Newton's method with the beta PDF. For production accuracy this would
    use scipy.stats.beta.ppf, but we avoid the dependency.
    """
    if a <= 0 or b <= 0:
        return 0.0
    if p <= 0:
        return 0.0
    if p >= 1:
        return 1.0

    # Initial guess from normal approximation
    mu = a / (a + b)
    var = (a * b) / ((a + b) ** 2 * (a + b + 1))
    std = math.sqrt(var) if var > 0 else 0.01

    # Normal approximation z-score
    z_scores = {0.025: -1.96, 0.975: 1.96, 0.05: -1.645, 0.95: 1.645, 0.005: -2.576, 0.995: 2.576}
    # For arbitrary p, use probit approximation
    if p in z_scores:
        z = z_scores[p]
    else:
        # Rational approximation of the inverse normal CDF (Abramowitz & Stegun)
        z = _norm_ppf(p)

    x = max(0.001, min(0.999, mu + z * std))

    # Newton-Raphson refinement (5 iterations usually sufficient)
    for _ in range(20):
        cdf_val = _beta_cdf(x, a, b)
        pdf_val = _beta_pdf(x, a, b)
        if pdf_val < 1e-15:
            break
        x_new = x - (cdf_val - p) / pdf_val
        x_new = max(1e-10, min(1 - 1e-10, x_new))
        if abs(x_new - x) < 1e-10:
            break
        x = x_new

    return x


def _norm_ppf(p: float) -> float:
    """Rational approximation of inverse normal CDF (Abramowitz & Stegun 26.2.23)."""
    if p <= 0:
        return -6.0
    if p >= 1:
        return 6.0
    if p == 0.5:
        return 0.0

    if p > 0.5:
        return -_norm_ppf(1 - p)

    t = math.sqrt(-2.0 * math.log(p))
    c0, c1, c2 = 2.515517, 0.802853, 0.010328
    d1, d2, d3 = 1.432788, 0.189269, 0.001308
    return -(t - (c0 + c1 * t + c2 * t * t) / (1 + d1 * t + d2 * t * t + d3 * t * t * t))


def _beta_pdf(x: float, a: float, b: float) -> float:
    """Beta distribution PDF."""
    if x <= 0 or x >= 1:
        return 0.0
    try:
        log_pdf = (a - 1) * math.log(x) + (b - 1) * math.log(1 - x) - _log_beta(a, b)
        return math.exp(log_pdf)
    except (ValueError, OverflowError):
        return 0.0


def _beta_cdf(x: float, a: float, b: float, steps: int = 100) -> float:
    """
    Beta distribution CDF via numerical integration (Simpson's rule).
    Accurate enough for CI estimation.
    """
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0

    # Simpson's 1/3 rule
    h = x / steps
    total = _beta_pdf(0.001, a, b) + _beta_pdf(x, a, b)

    for i in range(1, steps):
        xi = i * h
        if xi <= 0 or xi >= 1:
            continue
        coeff = 4 if i % 2 == 1 else 2
        total += coeff * _beta_pdf(xi, a, b)

    return total * h / 3


def _log_beta(a: float, b: float) -> float:
    """Log of the beta function: log(B(a,b)) = lgamma(a) + lgamma(b) - lgamma(a+b)."""
    return math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)


def coefficient_of_variation(values: List[float]) -> float:
    """
    Coefficient of variation (CV) — ratio of std dev to mean.
    Measures output consistency: lower CV = more consistent.

    Returns 0.0 for empty lists or zero mean.
    """
    if not values or len(values) < 2:
        return 0.0

    mean = sum(values) / len(values)
    if mean == 0:
        return 0.0

    variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
    std_dev = math.sqrt(variance)

    return std_dev / abs(mean)


def cohens_kappa(
    rater1: List[int],
    rater2: List[int],
    num_categories: Optional[int] = None,
) -> float:
    """
    Cohen's kappa — inter-rater agreement beyond chance.

    Used to measure agreement between deterministic and LLM scoring.
    Values: <0 = worse than chance, 0 = chance, 1 = perfect agreement.

    Args:
        rater1: List of category assignments from rater 1
        rater2: List of category assignments from rater 2
        num_categories: Number of possible categories (auto-detected if None)

    Returns:
        Kappa coefficient in [-1, 1]
    """
    if len(rater1) != len(rater2) or not rater1:
        return 0.0

    n = len(rater1)
    if num_categories is None:
        categories = sorted(set(rater1) | set(rater2))
    else:
        categories = list(range(num_categories))

    # Build confusion matrix
    matrix = {}
    for cat in categories:
        matrix[cat] = {c: 0 for c in categories}

    for r1, r2 in zip(rater1, rater2):
        if r1 in matrix and r2 in matrix[r1]:
            matrix[r1][r2] += 1

    # Observed agreement
    p_o = sum(matrix[c][c] for c in categories) / n

    # Expected agreement by chance
    p_e = 0.0
    for c in categories:
        row_sum = sum(matrix[c].values()) / n
        col_sum = sum(matrix[r][c] for r in categories) / n
        p_e += row_sum * col_sum

    if p_e >= 1.0:
        return 1.0 if p_o >= 1.0 else 0.0

    return (p_o - p_e) / (1 - p_e)


def weighted_composite(
    scores: dict,
    weights: dict,
    available_only: bool = True,
) -> float:
    """
    Calculate weighted composite score with automatic renormalization.

    When a dimension is unavailable (not in scores), its weight is
    redistributed proportionally among available dimensions.

    Args:
        scores: {dimension_name: score} where scores are 0-100
        weights: {dimension_name: weight} where weights sum to 1.0
        available_only: If True, renormalize weights for available dims only

    Returns:
        Composite score in [0, 100]
    """
    if not scores:
        return 0.0

    if available_only:
        available = {k: v for k, v in weights.items() if k in scores}
        if not available:
            return 0.0
        total_weight = sum(available.values())
        if total_weight == 0:
            return 0.0
        normalized = {k: v / total_weight for k, v in available.items()}
    else:
        normalized = weights

    composite = sum(scores.get(dim, 0) * w for dim, w in normalized.items())
    return max(0.0, min(100.0, composite))
