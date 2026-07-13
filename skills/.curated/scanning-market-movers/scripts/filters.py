#!/usr/bin/env python3
"""
Market Movers Filters - Threshold Filtering

Apply user-defined thresholds to identify significant market moves.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 2.0.0
License: MIT
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional


@dataclass
class FilterConfig:
    """Configuration for market mover filtering."""

    min_change: float = 5.0  # Minimum absolute % change
    volume_spike: float = 2.0  # Minimum volume ratio
    min_market_cap: float = 10_000_000  # Minimum market cap
    max_market_cap: Optional[float] = None  # Maximum market cap
    min_volume: float = 100_000  # Minimum 24h volume


def apply_filters(assets: List[Dict[str, Any]], config: FilterConfig) -> List[Dict[str, Any]]:
    """
    Filter assets based on threshold configuration.

    Args:
        assets: List of asset dictionaries
        config: Filter configuration

    Returns:
        List of assets that pass all filters
    """
    filtered = []

    for asset in assets:
        # Get values with defaults
        change = asset.get("change", 0) or 0
        volume_ratio = asset.get("volume_ratio", 0) or 0
        market_cap = asset.get("market_cap", 0) or 0
        volume = asset.get("volume_24h", 0) or 0

        # Check minimum change
        if abs(change) < config.min_change:
            continue

        # Check volume spike
        if volume_ratio < config.volume_spike:
            continue

        # Check market cap range
        if market_cap < config.min_market_cap:
            continue
        if config.max_market_cap and market_cap > config.max_market_cap:
            continue

        # Check minimum volume
        if volume < config.min_volume:
            continue

        filtered.append(asset)

    return filtered


def filter_by_category(
    assets: List[Dict[str, Any]], category: str, category_map: Dict[str, List[str]]
) -> List[Dict[str, Any]]:
    """
    Filter assets by category.

    Args:
        assets: List of asset dictionaries
        category: Category name
        category_map: Mapping of category to coin IDs

    Returns:
        Filtered list of assets
    """
    if category not in category_map:
        return assets

    allowed_ids = set(category_map[category])

    return [a for a in assets if a.get("id", "") in allowed_ids]


def filter_gainers(assets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter to only gainers (positive change)."""
    return [a for a in assets if (a.get("change", 0) or 0) > 0]


def filter_losers(assets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter to only losers (negative change)."""
    return [a for a in assets if (a.get("change", 0) or 0) < 0]


def filter_by_rank(
    assets: List[Dict[str, Any]], min_rank: Optional[int] = None, max_rank: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Filter by market cap rank.

    Args:
        assets: List of asset dictionaries
        min_rank: Minimum rank (1 = highest cap)
        max_rank: Maximum rank

    Returns:
        Filtered list
    """
    filtered = []

    for asset in assets:
        rank = asset.get("market_cap_rank")
        if rank is None:
            continue

        if min_rank and rank < min_rank:
            continue
        if max_rank and rank > max_rank:
            continue

        filtered.append(asset)

    return filtered


def suggest_relaxed_filters(config: FilterConfig, result_count: int, target_count: int = 10) -> Dict[str, Any]:
    """
    Suggest relaxed filter parameters if too few results.

    Args:
        config: Current filter configuration
        result_count: Number of results with current filters
        target_count: Desired minimum result count

    Returns:
        Dictionary with suggested parameter adjustments
    """
    if result_count >= target_count:
        return {}

    suggestions = {}

    # Suggest reducing thresholds by 30%
    if config.min_change > 3:
        suggestions["min_change"] = max(3, config.min_change * 0.7)

    if config.volume_spike > 1.5:
        suggestions["volume_spike"] = max(1.5, config.volume_spike * 0.7)

    if config.min_market_cap > 1_000_000:
        suggestions["min_market_cap"] = config.min_market_cap * 0.5

    return suggestions
