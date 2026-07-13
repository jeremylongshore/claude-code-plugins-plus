#!/usr/bin/env python3
"""
Metrics Calculator

Calculate derived on-chain metrics and analytics.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 1.0.0
License: MIT
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class ProtocolMetrics:
    """Calculated protocol metrics."""

    name: str
    tvl: float
    market_share: float
    tvl_to_mcap: Optional[float]
    revenue_24h: Optional[float]
    revenue_30d: Optional[float]
    fees_24h: Optional[float]
    pe_ratio: Optional[float]
    growth_7d: float
    growth_30d: float
    rank: int


class MetricsCalculator:
    """Calculate on-chain analytics metrics."""

    def calculate_market_share(self, protocols: List[Dict[str, Any]], category: str = None) -> List[Dict[str, Any]]:
        """Calculate market share for protocols.

        Args:
            protocols: List of protocol data
            category: Optional category filter

        Returns:
            Protocols with market_share added
        """
        if category:
            protocols = [p for p in protocols if p.get("category", "").lower() == category.lower()]

        total_tvl = sum(p.get("tvl", 0) for p in protocols)

        for p in protocols:
            tvl = p.get("tvl", 0)
            p["market_share"] = (tvl / total_tvl * 100) if total_tvl > 0 else 0

        return protocols

    def calculate_tvl_to_mcap(self, protocols: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculate TVL/Market Cap ratio.

        Args:
            protocols: List of protocol data

        Returns:
            Protocols with tvl_to_mcap ratio
        """
        for p in protocols:
            tvl = p.get("tvl", 0)
            mcap = p.get("mcap")

            if mcap and mcap > 0:
                p["tvl_to_mcap"] = tvl / mcap
            else:
                p["tvl_to_mcap"] = None

        return protocols

    def calculate_pe_ratio(self, protocols: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculate P/E ratios for protocols.

        Args:
            protocols: List of protocol data with fees

        Returns:
            Protocols with pe_ratio
        """
        for p in protocols:
            mcap = p.get("mcap")
            annual_fees = p.get("total30d", 0) * 12  # Annualized from 30d

            if mcap and annual_fees > 0:
                p["pe_ratio"] = mcap / annual_fees
            else:
                p["pe_ratio"] = None

        return protocols

    def calculate_growth_rates(self, tvl_history: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate growth rates from TVL history.

        Args:
            tvl_history: List of {date, tvl} entries

        Returns:
            Growth rates for various periods
        """
        if not tvl_history or len(tvl_history) < 2:
            return {"growth_24h": 0, "growth_7d": 0, "growth_30d": 0}

        current = tvl_history[-1].get("totalLiquidityUSD", 0)

        # 24h ago (index -2 if daily data)
        if len(tvl_history) >= 2:
            prev_24h = tvl_history[-2].get("totalLiquidityUSD", current)
            growth_24h = ((current - prev_24h) / prev_24h * 100) if prev_24h > 0 else 0
        else:
            growth_24h = 0

        # 7d ago
        if len(tvl_history) >= 8:
            prev_7d = tvl_history[-8].get("totalLiquidityUSD", current)
            growth_7d = ((current - prev_7d) / prev_7d * 100) if prev_7d > 0 else 0
        else:
            growth_7d = 0

        # 30d ago
        if len(tvl_history) >= 31:
            prev_30d = tvl_history[-31].get("totalLiquidityUSD", current)
            growth_30d = ((current - prev_30d) / prev_30d * 100) if prev_30d > 0 else 0
        else:
            growth_30d = 0

        return {
            "growth_24h": growth_24h,
            "growth_7d": growth_7d,
            "growth_30d": growth_30d,
        }

    def rank_protocols(self, protocols: List[Dict[str, Any]], metric: str = "tvl") -> List[Dict[str, Any]]:
        """Rank protocols by metric.

        Args:
            protocols: List of protocol data
            metric: Metric to rank by

        Returns:
            Ranked protocols
        """
        # Sort by metric (descending for most metrics)
        reverse = metric not in ["pe_ratio"]  # Lower PE is better
        protocols.sort(key=lambda x: x.get(metric, 0) or 0, reverse=reverse)

        # Add rank
        for i, p in enumerate(protocols):
            p["rank"] = i + 1

        return protocols

    def calculate_chain_dominance(self, chains: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculate chain TVL dominance.

        Args:
            chains: List of chain TVL data

        Returns:
            Chains with dominance percentage
        """
        total_tvl = sum(c.get("tvl", 0) for c in chains)

        for c in chains:
            tvl = c.get("tvl", 0)
            c["dominance"] = (tvl / total_tvl * 100) if total_tvl > 0 else 0

        chains.sort(key=lambda x: x.get("tvl", 0), reverse=True)

        return chains

    def calculate_category_metrics(self, protocols: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Calculate metrics grouped by category.

        Args:
            protocols: List of protocol data

        Returns:
            Category-level metrics
        """
        categories: Dict[str, Dict[str, Any]] = {}

        for p in protocols:
            cat = p.get("category", "Other")
            if cat not in categories:
                categories[cat] = {"name": cat, "protocol_count": 0, "total_tvl": 0, "protocols": []}

            categories[cat]["protocol_count"] += 1
            categories[cat]["total_tvl"] += p.get("tvl", 0)
            categories[cat]["protocols"].append(p.get("name"))

        # Calculate market share per category
        total_tvl = sum(c["total_tvl"] for c in categories.values())
        for cat in categories.values():
            cat["market_share"] = (cat["total_tvl"] / total_tvl * 100) if total_tvl > 0 else 0

        return categories

    def identify_trends(
        self, protocols: List[Dict[str, Any]], min_growth: float = 10.0
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Identify trending protocols.

        Args:
            protocols: List of protocol data
            min_growth: Minimum growth % to be considered trending

        Returns:
            Trending up and down protocols
        """
        trending_up = []
        trending_down = []

        for p in protocols:
            growth = p.get("change_7d", 0) or 0

            if growth >= min_growth:
                trending_up.append({"name": p.get("name"), "growth": growth, "tvl": p.get("tvl", 0)})
            elif growth <= -min_growth:
                trending_down.append({"name": p.get("name"), "growth": growth, "tvl": p.get("tvl", 0)})

        trending_up.sort(key=lambda x: x["growth"], reverse=True)
        trending_down.sort(key=lambda x: x["growth"])

        return {"trending_up": trending_up[:10], "trending_down": trending_down[:10]}


def main():
    """CLI entry point for testing."""
    calc = MetricsCalculator()

    # Test with sample data
    protocols = [
        {"name": "Lido", "tvl": 15000000000, "category": "Liquid Staking", "mcap": 2000000000},
        {"name": "Aave", "tvl": 8000000000, "category": "Lending", "mcap": 1500000000},
        {"name": "Uniswap", "tvl": 5000000000, "category": "DEX", "mcap": 4000000000},
    ]

    protocols = calc.calculate_market_share(protocols)
    protocols = calc.calculate_tvl_to_mcap(protocols)
    protocols = calc.rank_protocols(protocols, "tvl")

    for p in protocols:
        print(f"#{p['rank']} {p['name']}: ${p['tvl'] / 1e9:.2f}B ({p['market_share']:.1f}%)")


if __name__ == "__main__":
    main()
