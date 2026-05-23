"""
Trust Badge System for the Tons of Skills marketplace.

Maps composite scores to visual trust signals:
  Flagship:    90+  — Exemplary quality, reference implementation
  Established: 75+  — Production-ready, well-crafted
  Emerging:    60+  — Adequate, meets baseline quality
  Early:       40+  — Functional but needs improvement
  None:        <40  — Below marketplace minimum

Badge assignment uses the deep eval composite score,
NOT the existing letter grade (which uses a different rubric).

Author: Jeremy Longshore <jeremy@intentsolutions.io>
"""

from typing import Dict, Any, Optional


# Badge thresholds (composite score from deep eval)
BADGE_THRESHOLDS = {
    "flagship": 90,
    "established": 75,
    "emerging": 60,
    "early": 40,
}

# Badge metadata for display
BADGE_META = {
    "flagship": {
        "label": "Flagship",
        "emoji": "\u2b50",  # star
        "color": "#DA70D6",
        "description": "Exemplary quality — reference implementation",
    },
    "established": {
        "label": "Established",
        "emoji": "\u2705",  # check mark
        "color": "#4CAF50",
        "description": "Production-ready — well-crafted",
    },
    "emerging": {
        "label": "Emerging",
        "emoji": "\U0001f331",  # seedling
        "color": "#FF9800",
        "description": "Adequate — meets baseline quality",
    },
    "early": {
        "label": "Early",
        "emoji": "\U0001f527",  # wrench
        "color": "#9E9E9E",
        "description": "Functional — needs improvement",
    },
}


def assign_badge(composite_score: float) -> Optional[str]:
    """
    Assign a trust badge based on composite deep eval score.

    Args:
        composite_score: Score in [0, 100]

    Returns:
        Badge level ('flagship', 'established', 'emerging', 'early') or None
    """
    if composite_score >= BADGE_THRESHOLDS["flagship"]:
        return "flagship"
    elif composite_score >= BADGE_THRESHOLDS["established"]:
        return "established"
    elif composite_score >= BADGE_THRESHOLDS["emerging"]:
        return "emerging"
    elif composite_score >= BADGE_THRESHOLDS["early"]:
        return "early"
    return None


def badge_info(badge: Optional[str]) -> Dict[str, Any]:
    """
    Get display metadata for a badge.

    Returns dict with label, emoji, color, description, or empty dict if no badge.
    """
    if badge and badge in BADGE_META:
        return {**BADGE_META[badge], "level": badge}
    return {
        "label": "Unrated",
        "emoji": "",
        "color": "#666666",
        "description": "Below marketplace minimum",
        "level": None,
    }


def grade_to_badge_comparison(
    letter_grade: str,
    badge: Optional[str],
) -> Dict[str, Any]:
    """
    Compare existing letter grade with deep eval badge.
    Useful for identifying divergences between deterministic and deep scoring.
    """
    grade_rank = {"A": 4, "B": 3, "C": 2, "D": 1, "F": 0}
    badge_rank = {"flagship": 4, "established": 3, "emerging": 2, "early": 1, None: 0}

    g_rank = grade_rank.get(letter_grade, 0)
    b_rank = badge_rank.get(badge, 0)

    if g_rank == b_rank:
        alignment = "aligned"
    elif g_rank > b_rank:
        alignment = "grade_higher"
    else:
        alignment = "badge_higher"

    return {
        "letter_grade": letter_grade,
        "badge": badge,
        "alignment": alignment,
        "divergence": abs(g_rank - b_rank),
    }
