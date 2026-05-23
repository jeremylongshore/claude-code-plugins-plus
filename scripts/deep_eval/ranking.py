"""
Elo Ranking System for skill-vs-skill competitive ranking.

Chess-style Elo with K=32, applied to skills within the same category.
Uses composite deep eval scores to determine matchup outcomes.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
"""

import math
from typing import Dict, List, Tuple, Optional

from .stats import bootstrap_ci

# Elo constants
DEFAULT_RATING = 1500
K_FACTOR = 32
DRAW_THRESHOLD = 3.0  # Score difference within this = draw


def expected_score(rating_a: float, rating_b: float) -> float:
    """
    Calculate expected score for player A against player B.
    Returns probability in [0, 1].
    """
    return 1.0 / (1.0 + math.pow(10.0, (rating_b - rating_a) / 400.0))


def update_rating(
    rating: float,
    expected: float,
    actual: float,
    k: int = K_FACTOR,
) -> float:
    """
    Update Elo rating after a matchup.

    Args:
        rating: Current rating
        expected: Expected score (from expected_score())
        actual: Actual result (1.0 = win, 0.5 = draw, 0.0 = loss)
        k: K-factor (higher = more volatile)

    Returns:
        Updated rating
    """
    return rating + k * (actual - expected)


def determine_outcome(
    score_a: float,
    score_b: float,
    draw_threshold: float = DRAW_THRESHOLD,
) -> Tuple[float, float]:
    """
    Determine matchup outcome from composite scores.

    Returns (result_a, result_b) where:
        win = 1.0, draw = 0.5, loss = 0.0
    """
    diff = score_a - score_b
    if abs(diff) <= draw_threshold:
        return (0.5, 0.5)
    elif diff > 0:
        return (1.0, 0.0)
    else:
        return (0.0, 1.0)


def run_round_robin(
    skills: Dict[str, float],
    initial_ratings: Optional[Dict[str, float]] = None,
) -> Dict[str, Dict]:
    """
    Run round-robin Elo tournament among skills in a category.

    Args:
        skills: {skill_id: composite_score}
        initial_ratings: Optional starting ratings (default 1500 for all)

    Returns:
        {skill_id: {'rating': float, 'wins': int, 'losses': int, 'draws': int}}
    """
    if not skills:
        return {}

    ratings = {}
    records = {}
    for skill_id in skills:
        ratings[skill_id] = (initial_ratings or {}).get(skill_id, DEFAULT_RATING)
        records[skill_id] = {"wins": 0, "losses": 0, "draws": 0}

    skill_ids = list(skills.keys())

    for i in range(len(skill_ids)):
        for j in range(i + 1, len(skill_ids)):
            a, b = skill_ids[i], skill_ids[j]
            score_a, score_b = skills[a], skills[b]

            exp_a = expected_score(ratings[a], ratings[b])
            exp_b = expected_score(ratings[b], ratings[a])

            result_a, result_b = determine_outcome(score_a, score_b)

            ratings[a] = update_rating(ratings[a], exp_a, result_a)
            ratings[b] = update_rating(ratings[b], exp_b, result_b)

            if result_a == 1.0:
                records[a]["wins"] += 1
                records[b]["losses"] += 1
            elif result_b == 1.0:
                records[b]["wins"] += 1
                records[a]["losses"] += 1
            else:
                records[a]["draws"] += 1
                records[b]["draws"] += 1

    results = {}
    for skill_id in skill_ids:
        results[skill_id] = {
            "rating": round(ratings[skill_id], 1),
            "wins": records[skill_id]["wins"],
            "losses": records[skill_id]["losses"],
            "draws": records[skill_id]["draws"],
            "composite_score": skills[skill_id],
        }

    return results


def rank_skills(results: Dict[str, Dict]) -> List[Tuple[str, Dict]]:
    """Sort skills by Elo rating, descending."""
    return sorted(results.items(), key=lambda x: x[1]["rating"], reverse=True)


def rating_confidence_interval(
    matchup_results: List[float],
    confidence: float = 0.95,
    seed: int = 42,
) -> Tuple[float, float]:
    """
    Bootstrap CI on a skill's matchup results.

    Args:
        matchup_results: List of actual results (1.0/0.5/0.0) from matchups
        confidence: Confidence level
        seed: Random seed

    Returns:
        (lower, upper) CI bounds on the skill's win rate
    """
    if not matchup_results:
        return (0.0, 0.0)
    return bootstrap_ci(matchup_results, confidence=confidence, seed=seed)


def category_rankings(
    skills_by_category: Dict[str, Dict[str, float]],
) -> Dict[str, List[Tuple[str, Dict]]]:
    """
    Run Elo tournaments per category.

    Args:
        skills_by_category: {category: {skill_id: composite_score}}

    Returns:
        {category: [(skill_id, {rating, wins, losses, draws, composite_score})]}
    """
    rankings = {}
    for category, skills in skills_by_category.items():
        if len(skills) < 2:
            # Can't rank a single skill
            rankings[category] = [
                (sid, {"rating": DEFAULT_RATING, "wins": 0, "losses": 0, "draws": 0, "composite_score": score})
                for sid, score in skills.items()
            ]
            continue
        results = run_round_robin(skills)
        rankings[category] = rank_skills(results)
    return rankings
