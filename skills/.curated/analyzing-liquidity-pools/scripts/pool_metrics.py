#!/usr/bin/env python3
"""
Pool Metrics Calculator

Calculates derived metrics for liquidity pools.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 2.0.0
License: MIT
"""

from typing import Dict, Any, List


class PoolMetrics:
    """Calculates metrics for liquidity pools."""

    def __init__(self, verbose: bool = False):
        """Initialize metrics calculator.

        Args:
            verbose: Enable verbose output
        """
        self.verbose = verbose

    def calculate_metrics(self, pool: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate all metrics for a pool.

        Args:
            pool: Pool data dictionary

        Returns:
            Pool with metrics added
        """
        # Basic metrics
        pool["metrics"] = {}

        # TVL metrics
        self._calculate_tvl_metrics(pool)

        # Fee metrics
        self._calculate_fee_metrics(pool)

        # Efficiency metrics
        self._calculate_efficiency_metrics(pool)

        # Health indicators
        self._calculate_health_indicators(pool)

        if self.verbose:
            print(f"  Calculated metrics for {pool.get('symbol')}")

        return pool

    def _calculate_tvl_metrics(self, pool: Dict[str, Any]) -> None:
        """Calculate TVL-related metrics.

        Args:
            pool: Pool data (modified in place)
        """
        tvl = pool.get("tvlUsd", 0)
        volume_24h = pool.get("volumeUsd", 0) or pool.get("volume24h", 0)

        # TVL category
        if tvl >= 100_000_000:
            tvl_category = "large"
        elif tvl >= 10_000_000:
            tvl_category = "medium"
        elif tvl >= 1_000_000:
            tvl_category = "small"
        else:
            tvl_category = "micro"

        pool["metrics"]["tvl"] = tvl
        pool["metrics"]["tvl_category"] = tvl_category
        pool["metrics"]["volume_24h"] = volume_24h

    def _calculate_fee_metrics(self, pool: Dict[str, Any]) -> None:
        """Calculate fee-related metrics.

        Args:
            pool: Pool data (modified in place)
        """
        tvl = pool.get("tvlUsd", 0)
        volume_24h = pool.get("volumeUsd", 0) or pool.get("volume24h", 0)
        fee_tier = pool.get("feeTier", 0.003)  # Default 0.3%

        # Ensure fee_tier is decimal (not percentage)
        if fee_tier > 1:
            fee_tier = fee_tier / 10000  # Convert from basis points

        # Calculate fees
        if volume_24h > 0:
            daily_fees = volume_24h * fee_tier
        else:
            daily_fees = 0

        # Calculate APR
        if tvl > 0 and daily_fees > 0:
            fee_apr = (daily_fees / tvl) * 365 * 100
        else:
            fee_apr = 0

        pool["metrics"]["fee_tier"] = fee_tier
        pool["metrics"]["fee_tier_pct"] = round(fee_tier * 100, 4)
        pool["metrics"]["daily_fees"] = round(daily_fees, 2)
        pool["metrics"]["weekly_fees"] = round(daily_fees * 7, 2)
        pool["metrics"]["monthly_fees"] = round(daily_fees * 30, 2)
        pool["metrics"]["annual_fees"] = round(daily_fees * 365, 2)
        pool["metrics"]["fee_apr"] = round(fee_apr, 2)

    def _calculate_efficiency_metrics(self, pool: Dict[str, Any]) -> None:
        """Calculate efficiency metrics.

        Args:
            pool: Pool data (modified in place)
        """
        tvl = pool.get("tvlUsd", 0)
        volume_24h = pool.get("volumeUsd", 0) or pool.get("volume24h", 0)

        # Volume/TVL ratio (turnover)
        if tvl > 0:
            volume_tvl_ratio = volume_24h / tvl
        else:
            volume_tvl_ratio = 0

        # Capital efficiency rating
        if volume_tvl_ratio >= 0.5:
            efficiency = "very_high"
        elif volume_tvl_ratio >= 0.1:
            efficiency = "high"
        elif volume_tvl_ratio >= 0.05:
            efficiency = "medium"
        elif volume_tvl_ratio >= 0.01:
            efficiency = "low"
        else:
            efficiency = "very_low"

        pool["metrics"]["volume_tvl_ratio"] = round(volume_tvl_ratio, 4)
        pool["metrics"]["capital_efficiency"] = efficiency

    def _calculate_health_indicators(self, pool: Dict[str, Any]) -> None:
        """Calculate pool health indicators.

        Args:
            pool: Pool data (modified in place)
        """
        tvl = pool.get("tvlUsd", 0)
        volume_24h = pool.get("volumeUsd", 0) or pool.get("volume24h", 0)
        fee_apr = pool["metrics"].get("fee_apr", 0)

        warnings = []
        health_score = 100

        # TVL check
        if tvl < 100_000:
            warnings.append("Very low TVL - high slippage risk")
            health_score -= 30
        elif tvl < 1_000_000:
            warnings.append("Low TVL - moderate slippage risk")
            health_score -= 15

        # Volume check
        if volume_24h < 10_000:
            warnings.append("Very low volume - illiquid")
            health_score -= 25
        elif volume_24h < 100_000:
            warnings.append("Low volume - may be illiquid")
            health_score -= 10

        # Fee APR check
        if fee_apr < 1:
            warnings.append("Low fee income - may not offset IL")
            health_score -= 15
        elif fee_apr > 100:
            warnings.append("Unusually high APR - verify data")
            health_score -= 10

        # Volume/TVL ratio check
        vol_tvl = pool["metrics"].get("volume_tvl_ratio", 0)
        if vol_tvl < 0.01:
            warnings.append("Very low capital utilization")
            health_score -= 10

        # Determine health level
        if health_score >= 80:
            health_level = "healthy"
        elif health_score >= 60:
            health_level = "moderate"
        elif health_score >= 40:
            health_level = "poor"
        else:
            health_level = "risky"

        pool["metrics"]["health_score"] = max(0, health_score)
        pool["metrics"]["health_level"] = health_level
        pool["metrics"]["warnings"] = warnings

    def calculate_position_metrics(self, pool: Dict[str, Any], position_value: float) -> Dict[str, Any]:
        """Calculate metrics for a specific position size.

        Args:
            pool: Pool data with metrics
            position_value: Position size in USD

        Returns:
            Position-specific metrics
        """
        metrics = pool.get("metrics", {})
        tvl = metrics.get("tvl", 0)
        fee_apr = metrics.get("fee_apr", 0)

        # Position share of pool
        if tvl > 0:
            position_share = (position_value / tvl) * 100
        else:
            position_share = 0

        # Projected fees
        daily_fees_pool = metrics.get("daily_fees", 0)
        if tvl > 0:
            position_daily_fees = daily_fees_pool * (position_value / tvl)
        else:
            position_daily_fees = 0

        return {
            "position_value": position_value,
            "position_share_pct": round(position_share, 4),
            "daily_fees": round(position_daily_fees, 2),
            "weekly_fees": round(position_daily_fees * 7, 2),
            "monthly_fees": round(position_daily_fees * 30, 2),
            "annual_fees": round(position_daily_fees * 365, 2),
            "fee_apr": fee_apr,
        }

    def compare_pools(self, pools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compare metrics across multiple pools.

        Args:
            pools: List of pools with metrics

        Returns:
            Comparison summary
        """
        if not pools:
            return {}

        # Find best in each category
        max_tvl = max(pools, key=lambda p: p.get("metrics", {}).get("tvl", 0))
        max_apr = max(pools, key=lambda p: p.get("metrics", {}).get("fee_apr", 0))
        max_efficiency = max(pools, key=lambda p: p.get("metrics", {}).get("volume_tvl_ratio", 0))
        healthiest = max(pools, key=lambda p: p.get("metrics", {}).get("health_score", 0))

        return {
            "pool_count": len(pools),
            "highest_tvl": {
                "pool": max_tvl.get("symbol"),
                "tvl": max_tvl.get("metrics", {}).get("tvl"),
            },
            "highest_apr": {
                "pool": max_apr.get("symbol"),
                "apr": max_apr.get("metrics", {}).get("fee_apr"),
            },
            "most_efficient": {
                "pool": max_efficiency.get("symbol"),
                "ratio": max_efficiency.get("metrics", {}).get("volume_tvl_ratio"),
            },
            "healthiest": {
                "pool": healthiest.get("symbol"),
                "score": healthiest.get("metrics", {}).get("health_score"),
            },
        }


def main():
    """CLI entry point for testing."""
    calculator = PoolMetrics(verbose=True)

    # Test pool
    pool = {
        "pool": "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640",
        "project": "uniswap-v3",
        "chain": "Ethereum",
        "symbol": "USDC-WETH",
        "tvlUsd": 500_000_000,
        "volumeUsd": 125_000_000,
        "feeTier": 0.0005,
    }

    calculator.calculate_metrics(pool)

    print("\nPool Metrics:")
    print("-" * 50)
    metrics = pool["metrics"]
    print(f"  TVL: ${metrics['tvl']:,.0f} ({metrics['tvl_category']})")
    print(f"  Volume/24h: ${metrics['volume_24h']:,.0f}")
    print(f"  Fee Tier: {metrics['fee_tier_pct']}%")
    print(f"  Daily Fees: ${metrics['daily_fees']:,.2f}")
    print(f"  Fee APR: {metrics['fee_apr']:.2f}%")
    print(f"  Volume/TVL: {metrics['volume_tvl_ratio']:.4f}")
    print(f"  Capital Efficiency: {metrics['capital_efficiency']}")
    print(f"  Health Score: {metrics['health_score']}/100 ({metrics['health_level']})")

    if metrics["warnings"]:
        print("  Warnings:")
        for w in metrics["warnings"]:
            print(f"    - {w}")

    print("\nPosition Projection ($10,000):")
    position = calculator.calculate_position_metrics(pool, 10000)
    print(f"  Share of Pool: {position['position_share_pct']:.4f}%")
    print(f"  Daily Fees: ${position['daily_fees']:.2f}")
    print(f"  Monthly Fees: ${position['monthly_fees']:.2f}")
    print(f"  Annual Fees: ${position['annual_fees']:.2f}")


if __name__ == "__main__":
    main()
