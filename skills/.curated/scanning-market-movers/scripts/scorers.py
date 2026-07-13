#!/usr/bin/env python3
"""
Significance Scorers - Composite Scoring for Market Movers

Calculate significance scores combining price change, volume ratio, and market cap.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 2.0.0
License: MIT
"""

import math
from typing import Dict, Optional


def calculate_significance(
    change_pct: float, volume_ratio: float, market_cap: float, weights: Optional[Dict[str, float]] = None
) -> float:
    """
    Calculate composite significance score for ranking movers.

    The score combines:
    - Price change % (normalized, capped at 100)
    - Volume ratio (normalized, capped at 100)
    - Market cap (log scale, capped at 100)

    Args:
        change_pct: Percentage price change
        volume_ratio: Current volume / average volume
        market_cap: Market cap in USD
        weights: Optional custom weights (change, volume, cap)

    Returns:
        Significance score from 0-100
    """
    weights = weights or {"change_weight": 0.40, "volume_weight": 0.40, "cap_weight": 0.20}

    # Normalize change score (cap at 100)
    # 50% change = 100 score
    change_score = min(100, abs(change_pct) * 2)

    # Normalize volume ratio score (cap at 100)
    # 5x volume = 100 score
    volume_score = min(100, volume_ratio * 20)

    # Normalize market cap score (log scale, cap at 100)
    # $10B cap = 100 score (log10(10B) = 10, * 10 = 100)
    if market_cap > 0:
        cap_score = min(100, math.log10(market_cap) * 10)
    else:
        cap_score = 0

    # Calculate weighted sum
    score = (
        weights.get("change_weight", 0.4) * change_score
        + weights.get("volume_weight", 0.4) * volume_score
        + weights.get("cap_weight", 0.2) * cap_score
    )

    return round(score, 1)


def calculate_momentum_score(
    change_1h: Optional[float], change_24h: Optional[float], change_7d: Optional[float]
) -> float:
    """
    Calculate momentum score based on multi-timeframe changes.

    Higher scores indicate consistent directional movement.

    Args:
        change_1h: 1-hour change %
        change_24h: 24-hour change %
        change_7d: 7-day change %

    Returns:
        Momentum score from 0-100
    """
    changes = []
    if change_1h is not None:
        changes.append(change_1h)
    if change_24h is not None:
        changes.append(change_24h)
    if change_7d is not None:
        changes.append(change_7d)

    if not changes:
        return 0

    # Check if all changes are in same direction
    positive = sum(1 for c in changes if c > 0)
    negative = sum(1 for c in changes if c < 0)

    # Alignment score (0-1): all same direction = 1
    total = len(changes)
    alignment = max(positive, negative) / total

    # Magnitude score (average absolute change, capped)
    avg_change = sum(abs(c) for c in changes) / total
    magnitude = min(100, avg_change * 2)

    # Combine alignment and magnitude
    score = alignment * magnitude

    return round(score, 1)


def calculate_volatility_score(high_24h: Optional[float], low_24h: Optional[float], current_price: float) -> float:
    """
    Calculate volatility score based on 24h range.

    Args:
        high_24h: 24-hour high price
        low_24h: 24-hour low price
        current_price: Current price

    Returns:
        Volatility score from 0-100
    """
    if not all([high_24h, low_24h, current_price]) or current_price <= 0:
        return 0

    # Calculate range as percentage of current price
    range_pct = ((high_24h - low_24h) / current_price) * 100

    # Normalize (20% range = 100 score)
    score = min(100, range_pct * 5)

    return round(score, 1)


def calculate_relative_strength(change: float, market_avg_change: float) -> float:
    """
    Calculate relative strength vs market average.

    Args:
        change: Asset's change %
        market_avg_change: Market average change %

    Returns:
        Relative strength score (can be negative)
    """
    if market_avg_change == 0:
        return change * 10  # Simple scaling if no market avg

    # Relative outperformance
    relative = change - market_avg_change

    # Normalize to score
    score = relative * 5

    return round(score, 1)


def explain_score(
    change_pct: float,
    volume_ratio: float,
    market_cap: float,
    final_score: float,
    weights: Optional[Dict[str, float]] = None,
) -> Dict[str, str]:
    """
    Generate human-readable explanation of score components.

    Args:
        change_pct: Percentage price change
        volume_ratio: Volume ratio
        market_cap: Market cap
        final_score: Final significance score
        weights: Scoring weights

    Returns:
        Dictionary with explanation strings
    """
    weights = weights or {"change_weight": 0.40, "volume_weight": 0.40, "cap_weight": 0.20}

    explanations = {}

    # Change component
    change_score = min(100, abs(change_pct) * 2)
    change_contribution = weights.get("change_weight", 0.4) * change_score
    explanations["change"] = (
        f"{change_pct:+.1f}% change → {change_score:.0f} points (contributes {change_contribution:.1f} to score)"
    )

    # Volume component
    volume_score = min(100, volume_ratio * 20)
    volume_contribution = weights.get("volume_weight", 0.4) * volume_score
    explanations["volume"] = (
        f"{volume_ratio:.1f}x volume → {volume_score:.0f} points (contributes {volume_contribution:.1f} to score)"
    )

    # Cap component
    if market_cap > 0:
        cap_score = min(100, math.log10(market_cap) * 10)
    else:
        cap_score = 0
    cap_contribution = weights.get("cap_weight", 0.2) * cap_score

    cap_str = f"${market_cap / 1e9:.1f}B" if market_cap >= 1e9 else f"${market_cap / 1e6:.1f}M"
    explanations["market_cap"] = f"{cap_str} cap → {cap_score:.0f} points (contributes {cap_contribution:.1f} to score)"

    # Summary
    explanations["summary"] = (
        f"Final Score: {final_score:.1f}/100 "
        f"(Change: {change_contribution:.1f} + "
        f"Volume: {volume_contribution:.1f} + "
        f"Cap: {cap_contribution:.1f})"
    )

    return explanations
