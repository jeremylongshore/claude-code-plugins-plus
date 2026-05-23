#!/usr/bin/env python3
"""
NFT Rarity Formatters

Format rarity data for various outputs.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 1.0.0
License: MIT
"""

import json
from typing import List, Dict, Any


def format_percentage(value: float) -> str:
    """Format percentage value."""
    if value >= 10:
        return f"{value:.1f}%"
    elif value >= 1:
        return f"{value:.2f}%"
    else:
        return f"{value:.3f}%"


def format_rank(rank: int, total: int) -> str:
    """Format rank with total."""
    return f"#{rank:,} of {total:,}"


def format_collection_summary(collection: Any, trait_count: int) -> str:
    """Format collection summary.

    Args:
        collection: CollectionData object
        trait_count: Number of unique trait types

    Returns:
        Formatted summary
    """
    lines = [
        "",
        f"COLLECTION: {collection.name.upper()}",
        "=" * 60,
        f"Contract:     {collection.contract_address[:20]}..." if collection.contract_address else "",
        f"Total Supply: {collection.total_supply:,}",
        f"Fetched:      {len(collection.tokens):,} tokens",
        f"Trait Types:  {trait_count}",
        "=" * 60,
    ]

    return "\n".join(line for line in lines if line)


def format_trait_distribution(trait_summary: List[Dict]) -> str:
    """Format trait type distribution.

    Args:
        trait_summary: List of trait summaries from parser

    Returns:
        Formatted distribution table
    """
    lines = [
        "",
        "TRAIT DISTRIBUTION",
        "=" * 70,
        f"{'Trait Type':<20} {'Values':<10} {'Coverage':<15} {'Rarest Value':<20}",
        "-" * 70,
    ]

    for ts in sorted(trait_summary, key=lambda x: x["unique_values"], reverse=True):
        coverage = ts["total_with"] / (ts["total_with"] + ts["total_without"]) * 100
        rarest = ts["rarest_values"][0] if ts["rarest_values"] else {}
        rarest_str = f"{rarest.get('value', 'N/A')} ({rarest.get('percentage', 0):.1f}%)"

        lines.append(f"{ts['trait_type']:<20} {ts['unique_values']:<10} {coverage:.1f}%{' ':10} {rarest_str:<20}")

    lines.append("=" * 70)

    return "\n".join(lines)


def format_rankings(rarities: List[Any], limit: int = 20) -> str:
    """Format token rankings table.

    Args:
        rarities: List of TokenRarity objects
        limit: Max tokens to show

    Returns:
        Formatted rankings table
    """
    total = len(rarities)

    lines = [
        "",
        "TOKEN RANKINGS (by Rarity Score)",
        "=" * 80,
        f"{'Rank':<8} {'Token':<20} {'Score':<12} {'Percentile':<12} {'Top Trait':<25}",
        "-" * 80,
    ]

    for r in rarities[:limit]:
        top_trait = r.traits[0] if r.traits else None
        top_str = f"{top_trait.trait_type}: {top_trait.value}" if top_trait else "N/A"
        if len(top_str) > 23:
            top_str = top_str[:20] + "..."

        lines.append(
            f"#{r.rank:<7} {r.name[:18]:<20} {r.rarity_score:<12.2f} Top {r.percentile:.1f}%{' ':3} {top_str:<25}"
        )

    if total > limit:
        lines.append(f"... and {total - limit} more tokens")

    lines.append("-" * 80)
    lines.append(f"Algorithm: {rarities[0].algorithm if rarities else 'N/A'}")
    lines.append(f"Total Ranked: {total:,}")
    lines.append("=" * 80)

    return "\n".join(lines)


def format_token_detail(rarity: Any) -> str:
    """Format detailed token rarity.

    Args:
        rarity: TokenRarity object

    Returns:
        Formatted token detail
    """
    lines = [
        "",
        f"TOKEN: {rarity.name}",
        "=" * 60,
        f"Token ID:    {rarity.token_id}",
        f"Rank:        #{rarity.rank:,}",
        f"Percentile:  Top {rarity.percentile:.2f}%",
        f"Score:       {rarity.rarity_score:.4f}",
        f"Algorithm:   {rarity.algorithm}",
        "",
        "TRAIT BREAKDOWN",
        "-" * 60,
        f"{'Trait':<20} {'Value':<20} {'Rarity':<12} {'Score +'}",
        "-" * 60,
    ]

    for t in rarity.traits:
        rarity_str = f"1 in {int(1 / t.frequency)}" if t.frequency > 0 else "Unique"
        lines.append(f"{t.trait_type:<20} {t.value[:18]:<20} {rarity_str:<12} +{t.contribution:.2f}")

    lines.append("=" * 60)

    return "\n".join(lines)


def format_rarest_traits(rarities: List[Any], top_n: int = 10) -> str:
    """Format rarest traits across collection.

    Args:
        rarities: List of TokenRarity objects
        top_n: Number of traits to show

    Returns:
        Formatted rarest traits
    """
    # Collect all traits with their tokens
    all_traits = []
    for r in rarities:
        for t in r.traits:
            all_traits.append(
                {
                    "trait_type": t.trait_type,
                    "value": t.value,
                    "count": t.count,
                    "frequency": t.frequency,
                    "token_id": r.token_id,
                    "token_name": r.name,
                    "token_rank": r.rank,
                }
            )

    # Remove duplicates and sort by frequency (ascending = rarest)
    seen = set()
    unique_traits = []
    for t in all_traits:
        key = (t["trait_type"], t["value"])
        if key not in seen:
            seen.add(key)
            unique_traits.append(t)

    unique_traits.sort(key=lambda x: x["frequency"])

    lines = [
        "",
        f"RAREST TRAITS (Top {top_n})",
        "=" * 70,
        f"{'Trait':<20} {'Value':<20} {'Count':<10} {'Frequency':<12}",
        "-" * 70,
    ]

    for t in unique_traits[:top_n]:
        freq_str = format_percentage(t["frequency"] * 100)
        lines.append(f"{t['trait_type']:<20} {t['value'][:18]:<20} {t['count']:<10} {freq_str:<12}")

    lines.append("=" * 70)

    return "\n".join(lines)


def format_comparison(tokens: List[Any]) -> str:
    """Format token comparison table.

    Args:
        tokens: List of TokenRarity objects to compare

    Returns:
        Formatted comparison
    """
    if not tokens:
        return "No tokens to compare"

    lines = [
        "",
        "TOKEN COMPARISON",
        "=" * 80,
    ]

    # Header
    header = f"{'Trait':<20}"
    for t in tokens:
        header += f" {t.name[:15]:<16}"
    lines.append(header)
    lines.append("-" * 80)

    # Get all trait types
    trait_types = set()
    for t in tokens:
        for tr in t.traits:
            trait_types.add(tr.trait_type)

    # Build rows
    for trait_type in sorted(trait_types):
        row = f"{trait_type:<20}"
        for token in tokens:
            trait = next((t for t in token.traits if t.trait_type == trait_type), None)
            if trait:
                val = f"{trait.value[:12]} ({trait.frequency:.0%})"
            else:
                val = "None"
            row += f" {val:<16}"
        lines.append(row)

    lines.append("-" * 80)

    # Summary row
    summary = f"{'RANK':<20}"
    for t in tokens:
        summary += f" #{t.rank:<15}"
    lines.append(summary)

    score = f"{'SCORE':<20}"
    for t in tokens:
        score += f" {t.rarity_score:<15.2f}"
    lines.append(score)

    lines.append("=" * 80)

    return "\n".join(lines)


def format_json(data: Any) -> str:
    """Format data as JSON.

    Args:
        data: Data to format

    Returns:
        JSON string
    """
    if hasattr(data, "__dict__"):
        obj = _to_dict(data)
    elif isinstance(data, list):
        obj = [_to_dict(x) for x in data]
    else:
        obj = data

    return json.dumps(obj, indent=2, default=str)


def _to_dict(obj: Any) -> Dict:
    """Convert object to dict recursively."""
    if hasattr(obj, "__dict__"):
        result = {}
        for k, v in vars(obj).items():
            if isinstance(v, list):
                result[k] = [_to_dict(x) for x in v]
            elif hasattr(v, "__dict__"):
                result[k] = _to_dict(v)
            else:
                result[k] = v
        return result
    return obj


def format_csv_rankings(rarities: List[Any]) -> str:
    """Format rankings as CSV.

    Args:
        rarities: List of TokenRarity

    Returns:
        CSV string
    """
    lines = ["rank,token_id,name,score,percentile,algorithm"]

    for r in rarities:
        name = r.name.replace(",", " ")
        lines.append(f"{r.rank},{r.token_id},{name},{r.rarity_score:.4f},{r.percentile:.2f},{r.algorithm}")

    return "\n".join(lines)


def main():
    """CLI entry point for testing."""
    print("=== Formatter Tests ===")
    print(f"Percentage: {format_percentage(0.5)}")
    print(f"Percentage: {format_percentage(5.5)}")
    print(f"Percentage: {format_percentage(50.5)}")
    print(f"Rank: {format_rank(42, 10000)}")


if __name__ == "__main__":
    main()
