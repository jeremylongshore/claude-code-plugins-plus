#!/usr/bin/env python3
"""
Output Formatters

Format on-chain analytics data for various outputs.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 1.0.0
License: MIT
"""

import json
import csv
import io
from typing import Dict, Any, List


def format_usd(value: float) -> str:
    """Format USD value."""
    if value >= 1e12:
        return f"${value / 1e12:.2f}T"
    elif value >= 1e9:
        return f"${value / 1e9:.2f}B"
    elif value >= 1e6:
        return f"${value / 1e6:.2f}M"
    elif value >= 1e3:
        return f"${value / 1e3:.2f}K"
    else:
        return f"${value:.2f}"


def format_percent(value: float) -> str:
    """Format percentage with sign."""
    if value > 0:
        return f"+{value:.1f}%"
    else:
        return f"{value:.1f}%"


def format_protocols_table(protocols: List[Dict[str, Any]], title: str = "Protocol Rankings") -> str:
    """Format protocols as ASCII table.

    Args:
        protocols: List of protocol data
        title: Table title

    Returns:
        Formatted table string
    """
    lines = [
        f"\n{title}",
        "=" * 95,
        f"{'Rank':<6} {'Protocol':<20} {'TVL':<14} {'24h':<10} {'7d':<10} {'Share':<10} {'Category':<15}",
        "-" * 95,
    ]

    for p in protocols[:50]:
        rank = p.get("rank", "-")
        name = p.get("name", "Unknown")[:18]
        tvl = format_usd(p.get("tvl", 0))
        change_24h = format_percent(p.get("change_1d", 0) or p.get("tvl_change_24h", 0) or 0)
        change_7d = format_percent(p.get("change_7d", 0) or p.get("tvl_change_7d", 0) or 0)
        share = f"{p.get('market_share', 0):.1f}%"
        category = p.get("category", "Unknown")[:13]

        lines.append(f"{rank:<6} {name:<20} {tvl:<14} {change_24h:<10} {change_7d:<10} {share:<10} {category:<15}")

    lines.append("-" * 95)
    lines.append(f"Total: {len(protocols)} protocols")

    return "\n".join(lines)


def format_chains_table(chains: List[Dict[str, Any]]) -> str:
    """Format chains as ASCII table.

    Args:
        chains: List of chain data

    Returns:
        Formatted table string
    """
    lines = [
        "\nChain TVL Rankings",
        "=" * 70,
        f"{'Rank':<6} {'Chain':<20} {'TVL':<14} {'Dominance':<12} {'Protocols':<10}",
        "-" * 70,
    ]

    for i, c in enumerate(chains[:30], 1):
        name = c.get("name", "Unknown")[:18]
        tvl = format_usd(c.get("tvl", 0))
        dominance = f"{c.get('dominance', 0):.2f}%"
        protocols = c.get("protocols", "-")

        lines.append(f"{i:<6} {name:<20} {tvl:<14} {dominance:<12} {protocols:<10}")

    lines.append("-" * 70)

    return "\n".join(lines)


def format_fees_table(fees_data: List[Dict[str, Any]]) -> str:
    """Format fees/revenue as ASCII table.

    Args:
        fees_data: List of fee data

    Returns:
        Formatted table string
    """
    lines = [
        "\nProtocol Fees & Revenue",
        "=" * 85,
        f"{'Protocol':<20} {'Fees 24h':<14} {'Fees 30d':<14} {'Rev 24h':<14} {'Rev 30d':<14}",
        "-" * 85,
    ]

    for p in fees_data[:30]:
        name = p.get("name", p.get("displayName", "Unknown"))[:18]
        fees_24h = format_usd(p.get("total24h", 0) or 0)
        fees_30d = format_usd(p.get("total30d", 0) or 0)
        rev_24h = format_usd(p.get("revenue24h", 0) or 0)
        rev_30d = format_usd(p.get("revenue30d", 0) or 0)

        lines.append(f"{name:<20} {fees_24h:<14} {fees_30d:<14} {rev_24h:<14} {rev_30d:<14}")

    lines.append("-" * 85)

    return "\n".join(lines)


def format_trends_table(trends: Dict[str, List[Dict]]) -> str:
    """Format trending protocols.

    Args:
        trends: Dict with trending_up and trending_down lists

    Returns:
        Formatted table string
    """
    lines = ["\nTrending Protocols (7d)", "=" * 60]

    lines.append("\nTrending Up:")
    lines.append("-" * 40)
    for p in trends.get("trending_up", [])[:5]:
        lines.append(f"  {p['name']}: {format_percent(p['growth'])} ({format_usd(p['tvl'])})")

    lines.append("\nTrending Down:")
    lines.append("-" * 40)
    for p in trends.get("trending_down", [])[:5]:
        lines.append(f"  {p['name']}: {format_percent(p['growth'])} ({format_usd(p['tvl'])})")

    return "\n".join(lines)


def format_category_summary(categories: Dict[str, Dict[str, Any]]) -> str:
    """Format category summary.

    Args:
        categories: Dict of category metrics

    Returns:
        Formatted table string
    """
    sorted_cats = sorted(categories.values(), key=lambda x: x["total_tvl"], reverse=True)

    lines = [
        "\nCategory Summary",
        "=" * 70,
        f"{'Category':<25} {'TVL':<14} {'Share':<10} {'Protocols':<10}",
        "-" * 70,
    ]

    for c in sorted_cats[:20]:
        name = c.get("name", "Unknown")[:23]
        tvl = format_usd(c.get("total_tvl", 0))
        share = f"{c.get('market_share', 0):.1f}%"
        count = c.get("protocol_count", 0)

        lines.append(f"{name:<25} {tvl:<14} {share:<10} {count:<10}")

    lines.append("-" * 70)

    return "\n".join(lines)


def format_json(data: Any) -> str:
    """Format data as JSON."""
    return json.dumps(data, indent=2, default=str)


def format_csv(data: List[Dict[str, Any]], fields: List[str] = None) -> str:
    """Format data as CSV."""
    if not data:
        return ""

    if not fields:
        fields = list(data[0].keys())

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(data)

    return output.getvalue()


def main():
    """CLI entry point for testing."""
    # Test with sample data
    protocols = [
        {
            "rank": 1,
            "name": "Lido",
            "tvl": 15e9,
            "change_1d": 2.5,
            "change_7d": 5.0,
            "market_share": 30.0,
            "category": "Liquid Staking",
        },
        {
            "rank": 2,
            "name": "Aave",
            "tvl": 8e9,
            "change_1d": -1.2,
            "change_7d": 3.0,
            "market_share": 16.0,
            "category": "Lending",
        },
    ]

    print(format_protocols_table(protocols))


if __name__ == "__main__":
    main()
