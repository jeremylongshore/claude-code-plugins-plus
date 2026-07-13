#!/usr/bin/env python3
"""
Gas Price Analyzer

Analyze gas prices and recommend optimal fees.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 1.0.0
License: MIT
"""

from typing import Any, List
from dataclasses import dataclass
import statistics


@dataclass
class GasRecommendation:
    """Gas price recommendation."""

    priority: str  # slow, standard, fast, instant
    max_fee: int  # in wei
    priority_fee: int  # in wei
    estimated_wait: str  # e.g., "2-5 blocks"
    confidence: float  # 0.0 to 1.0


@dataclass
class GasDistribution:
    """Gas price distribution analysis."""

    min_gwei: float
    max_gwei: float
    mean_gwei: float
    median_gwei: float
    p10_gwei: float  # 10th percentile
    p25_gwei: float  # 25th percentile
    p50_gwei: float  # 50th percentile
    p75_gwei: float  # 75th percentile
    p90_gwei: float  # 90th percentile
    sample_count: int


class GasAnalyzer:
    """Analyze mempool gas prices and provide recommendations."""

    def __init__(self, verbose: bool = False):
        """Initialize gas analyzer."""
        self.verbose = verbose

    def analyze_pending_gas(self, pending_txs: List[Any], base_fee: int = None) -> GasDistribution:
        """Analyze gas price distribution in pending transactions.

        Args:
            pending_txs: List of pending transactions
            base_fee: Current base fee in wei

        Returns:
            GasDistribution with statistics
        """
        # Extract gas prices
        gas_prices = []
        for tx in pending_txs:
            if hasattr(tx, "gas_price"):
                gas_prices.append(tx.gas_price)
            elif isinstance(tx, dict) and "gasPrice" in tx:
                price = tx["gasPrice"]
                if isinstance(price, str):
                    price = int(price, 16)
                gas_prices.append(price)

        if not gas_prices:
            # Return defaults if no data
            default_gwei = 30.0
            return GasDistribution(
                min_gwei=default_gwei,
                max_gwei=default_gwei,
                mean_gwei=default_gwei,
                median_gwei=default_gwei,
                p10_gwei=default_gwei - 5,
                p25_gwei=default_gwei - 2,
                p50_gwei=default_gwei,
                p75_gwei=default_gwei + 5,
                p90_gwei=default_gwei + 10,
                sample_count=0,
            )

        # Convert to gwei
        gwei_prices = [p / 10**9 for p in gas_prices]
        sorted_prices = sorted(gwei_prices)
        n = len(sorted_prices)

        def percentile(p: float) -> float:
            idx = int(n * p / 100)
            return sorted_prices[min(idx, n - 1)]

        return GasDistribution(
            min_gwei=min(gwei_prices),
            max_gwei=max(gwei_prices),
            mean_gwei=statistics.mean(gwei_prices),
            median_gwei=statistics.median(gwei_prices),
            p10_gwei=percentile(10),
            p25_gwei=percentile(25),
            p50_gwei=percentile(50),
            p75_gwei=percentile(75),
            p90_gwei=percentile(90),
            sample_count=n,
        )

    def recommend_gas(
        self, distribution: GasDistribution = None, base_fee: int = None, priority: str = "standard"
    ) -> GasRecommendation:
        """Get gas price recommendation.

        Args:
            distribution: Gas distribution from analyze_pending_gas
            base_fee: Current base fee in wei
            priority: slow, standard, fast, or instant

        Returns:
            GasRecommendation
        """
        # Use distribution or defaults
        if distribution:
            prices = {
                "slow": distribution.p10_gwei,
                "standard": distribution.p50_gwei,
                "fast": distribution.p75_gwei,
                "instant": distribution.p90_gwei,
            }
        else:
            # Default recommendations
            prices = {
                "slow": 25,
                "standard": 35,
                "fast": 50,
                "instant": 75,
            }

        wait_times = {
            "slow": "10+ blocks (~3 min)",
            "standard": "2-5 blocks (~1 min)",
            "fast": "1-2 blocks (~30 sec)",
            "instant": "Next block (~12 sec)",
        }

        confidence = {
            "slow": 0.7,
            "standard": 0.9,
            "fast": 0.95,
            "instant": 0.99,
        }

        selected_gwei = prices.get(priority, prices["standard"])

        # Calculate max fee and priority fee
        if base_fee:
            base_gwei = base_fee / 10**9
            priority_fee_gwei = max(selected_gwei - base_gwei, 1.0)
            # Max fee should be 2x base fee + priority to handle base fee spikes
            max_fee_gwei = base_gwei * 2 + priority_fee_gwei
        else:
            priority_fee_gwei = 2.0
            max_fee_gwei = selected_gwei

        return GasRecommendation(
            priority=priority,
            max_fee=int(max_fee_gwei * 10**9),
            priority_fee=int(priority_fee_gwei * 10**9),
            estimated_wait=wait_times.get(priority, "Unknown"),
            confidence=confidence.get(priority, 0.5),
        )

    def estimate_inclusion_time(self, gas_price: int, distribution: GasDistribution) -> str:
        """Estimate time to transaction inclusion.

        Args:
            gas_price: Your gas price in wei
            distribution: Current gas distribution

        Returns:
            Estimated wait time string
        """
        gwei = gas_price / 10**9

        if gwei >= distribution.p90_gwei:
            return "Next block (~12 sec)"
        elif gwei >= distribution.p75_gwei:
            return "1-2 blocks (~30 sec)"
        elif gwei >= distribution.p50_gwei:
            return "2-5 blocks (~1 min)"
        elif gwei >= distribution.p25_gwei:
            return "5-10 blocks (~2 min)"
        elif gwei >= distribution.p10_gwei:
            return "10+ blocks (~3+ min)"
        else:
            return "May not be included"

    def format_distribution(self, dist: GasDistribution) -> str:
        """Format gas distribution for display.

        Args:
            dist: GasDistribution to format

        Returns:
            Formatted string
        """
        lines = [
            "",
            "GAS PRICE DISTRIBUTION",
            "=" * 50,
            f"Sample Size: {dist.sample_count} pending transactions",
            "",
            f"  Min:    {dist.min_gwei:6.1f} gwei",
            f"  10th%:  {dist.p10_gwei:6.1f} gwei (Slow)",
            f"  25th%:  {dist.p25_gwei:6.1f} gwei",
            f"  50th%:  {dist.p50_gwei:6.1f} gwei (Standard)",
            f"  75th%:  {dist.p75_gwei:6.1f} gwei (Fast)",
            f"  90th%:  {dist.p90_gwei:6.1f} gwei (Instant)",
            f"  Max:    {dist.max_gwei:6.1f} gwei",
            "",
            f"  Mean:   {dist.mean_gwei:6.1f} gwei",
            f"  Median: {dist.median_gwei:6.1f} gwei",
            "=" * 50,
        ]
        return "\n".join(lines)

    def format_recommendations(self, base_fee: int = None) -> str:
        """Format all gas recommendations for display.

        Args:
            base_fee: Current base fee in wei

        Returns:
            Formatted string
        """
        lines = [
            "",
            "GAS RECOMMENDATIONS",
            "=" * 60,
        ]

        if base_fee:
            lines.append(f"Current Base Fee: {base_fee / 10**9:.1f} gwei")
            lines.append("")

        lines.append(f"{'Priority':<12} {'Max Fee':<12} {'Priority Fee':<14} {'Est. Wait':<20}")
        lines.append("-" * 60)

        for priority in ["slow", "standard", "fast", "instant"]:
            rec = self.recommend_gas(priority=priority, base_fee=base_fee)
            max_fee_gwei = rec.max_fee / 10**9
            priority_gwei = rec.priority_fee / 10**9
            lines.append(
                f"{priority.capitalize():<12} {max_fee_gwei:<12.1f} {priority_gwei:<14.1f} {rec.estimated_wait:<20}"
            )

        lines.append("=" * 60)
        return "\n".join(lines)


def main():
    """CLI entry point for testing."""
    analyzer = GasAnalyzer(verbose=True)

    # Create mock pending transactions
    class MockTx:
        def __init__(self, gas_price):
            self.gas_price = gas_price

    import random

    base = 30 * 10**9
    mock_txs = [MockTx(base + random.randint(-10, 30) * 10**9) for _ in range(100)]

    # Analyze
    dist = analyzer.analyze_pending_gas(mock_txs, base_fee=base)
    print(analyzer.format_distribution(dist))

    # Recommendations
    print(analyzer.format_recommendations(base_fee=base))

    # Test inclusion estimate
    print("\n=== Inclusion Time Estimates ===")
    for gwei in [25, 30, 40, 50, 70]:
        est = analyzer.estimate_inclusion_time(gwei * 10**9, dist)
        print(f"  {gwei} gwei: {est}")


if __name__ == "__main__":
    main()
