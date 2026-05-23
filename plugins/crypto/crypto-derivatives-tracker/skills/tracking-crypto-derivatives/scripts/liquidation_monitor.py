#!/usr/bin/env python3
"""
Liquidation monitor and heatmap generator.

Tracks liquidations across exchanges with:
- Real-time liquidation events
- Liquidation level clustering
- Cascade risk assessment
- Heatmap visualization
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from exchange_client import ExchangeClient, Liquidation, LiquidationLevel


@dataclass
class LiquidationSummary:
    """Summary of liquidation activity."""

    symbol: str
    current_price: Decimal
    total_24h_usd: Decimal
    long_liquidations_usd: Decimal
    short_liquidations_usd: Decimal
    largest_single: Liquidation
    recent_liquidations: List[Liquidation]
    long_levels: List[LiquidationLevel]
    short_levels: List[LiquidationLevel]
    cascade_risk: str  # "low", "medium", "high", "critical"
    nearest_long_level: Optional[LiquidationLevel]
    nearest_short_level: Optional[LiquidationLevel]
    timestamp: datetime


class LiquidationMonitor:
    """
    Monitors liquidation events and levels.

    Features:
    - Real-time liquidation tracking
    - Heatmap generation
    - Cascade risk assessment
    - Level clustering
    """

    # Cascade risk thresholds (USD within 5% of price)
    CRITICAL_THRESHOLD = 500_000_000  # $500M
    HIGH_THRESHOLD = 200_000_000  # $200M
    MEDIUM_THRESHOLD = 100_000_000  # $100M

    def __init__(
        self,
        client: Optional[ExchangeClient] = None,
    ):
        """
        Initialize liquidation monitor.

        Args:
            client: Exchange client for data fetching
        """
        self.client = client or ExchangeClient(use_mock=True)

    def get_summary(
        self,
        symbol: str,
        current_price: Optional[Decimal] = None,
    ) -> LiquidationSummary:
        """
        Get comprehensive liquidation summary.

        Args:
            symbol: Trading symbol (e.g., "BTC")
            current_price: Current price (fetched if not provided)

        Returns:
            LiquidationSummary with all metrics
        """
        # Set default price if not provided
        if current_price is None:
            if symbol == "BTC":
                current_price = Decimal("67500")
            elif symbol == "ETH":
                current_price = Decimal("2500")
            else:
                current_price = Decimal("100")

        # Fetch recent liquidations
        liquidations = self.client.get_recent_liquidations(symbol, limit=100, min_value_usd=100000)

        # Fetch liquidation levels
        levels = self.client.get_liquidation_levels(symbol, current_price)

        # Separate long and short levels
        long_levels = [l for l in levels if l.side == "long"]
        short_levels = [l for l in levels if l.side == "short"]

        # Sort by distance from current price
        long_levels.sort(key=lambda x: x.price, reverse=True)
        short_levels.sort(key=lambda x: x.price)

        # Calculate 24h totals
        cutoff = datetime.now() - timedelta(hours=24)
        recent_24h = [l for l in liquidations if l.timestamp > cutoff]

        total_24h = sum(float(l.value_usd) for l in recent_24h)
        long_24h = sum(float(l.value_usd) for l in recent_24h if l.side == "long")
        short_24h = sum(float(l.value_usd) for l in recent_24h if l.side == "short")

        # Find largest single liquidation
        largest = max(liquidations, key=lambda x: x.value_usd) if liquidations else None

        # Find nearest levels
        nearest_long = long_levels[0] if long_levels else None
        nearest_short = short_levels[0] if short_levels else None

        # Assess cascade risk
        cascade_risk = self._assess_cascade_risk(current_price, long_levels, short_levels)

        return LiquidationSummary(
            symbol=symbol,
            current_price=current_price,
            total_24h_usd=Decimal(str(int(total_24h))),
            long_liquidations_usd=Decimal(str(int(long_24h))),
            short_liquidations_usd=Decimal(str(int(short_24h))),
            largest_single=largest,
            recent_liquidations=liquidations[:20],
            long_levels=long_levels,
            short_levels=short_levels,
            cascade_risk=cascade_risk,
            nearest_long_level=nearest_long,
            nearest_short_level=nearest_short,
            timestamp=datetime.now(),
        )

    def _assess_cascade_risk(
        self,
        current_price: Decimal,
        long_levels: List[LiquidationLevel],
        short_levels: List[LiquidationLevel],
    ) -> str:
        """
        Assess cascade risk based on nearby liquidation levels.

        Considers liquidations within 5% of current price.
        """
        price = float(current_price)
        lower_bound = price * 0.95
        upper_bound = price * 1.05

        # Sum liquidations within range
        nearby_value = 0

        for level in long_levels:
            if float(level.price) >= lower_bound:
                nearby_value += float(level.total_value_usd)

        for level in short_levels:
            if float(level.price) <= upper_bound:
                nearby_value += float(level.total_value_usd)

        # Determine risk level
        if nearby_value >= self.CRITICAL_THRESHOLD:
            return "critical"
        elif nearby_value >= self.HIGH_THRESHOLD:
            return "high"
        elif nearby_value >= self.MEDIUM_THRESHOLD:
            return "medium"
        else:
            return "low"

    def generate_heatmap_data(
        self,
        symbol: str,
        current_price: Decimal,
        levels: int = 5,
    ) -> Dict:
        """
        Generate heatmap visualization data.

        Args:
            symbol: Trading symbol
            current_price: Current price
            levels: Number of levels above/below

        Returns:
            Dict with heatmap data for visualization
        """
        summary = self.get_summary(symbol, current_price)

        heatmap = {
            "symbol": symbol,
            "current_price": float(current_price),
            "long_levels": [],
            "short_levels": [],
        }

        # Add long levels (below price)
        for level in summary.long_levels[:levels]:
            distance_pct = (float(current_price) - float(level.price)) / float(current_price) * 100
            heatmap["long_levels"].append(
                {
                    "price": float(level.price),
                    "value_usd": float(level.total_value_usd),
                    "distance_pct": round(distance_pct, 1),
                    "density": level.density,
                }
            )

        # Add short levels (above price)
        for level in summary.short_levels[:levels]:
            distance_pct = (float(level.price) - float(current_price)) / float(current_price) * 100
            heatmap["short_levels"].append(
                {
                    "price": float(level.price),
                    "value_usd": float(level.total_value_usd),
                    "distance_pct": round(distance_pct, 1),
                    "density": level.density,
                }
            )

        return heatmap

    def get_recent_large_liquidations(
        self,
        symbol: str,
        min_value_usd: float = 1_000_000,
        limit: int = 10,
    ) -> List[Dict]:
        """
        Get recent large liquidation events.

        Args:
            symbol: Trading symbol
            min_value_usd: Minimum liquidation size
            limit: Maximum results

        Returns:
            List of large liquidations
        """
        liquidations = self.client.get_recent_liquidations(symbol, limit=limit * 2, min_value_usd=min_value_usd)

        # Filter by size and limit
        large = [l for l in liquidations if float(l.value_usd) >= min_value_usd]
        large = sorted(large, key=lambda x: x.value_usd, reverse=True)[:limit]

        return [
            {
                "exchange": l.exchange,
                "side": l.side,
                "price": float(l.price),
                "quantity": float(l.quantity),
                "value_usd": float(l.value_usd),
                "time_ago": self._time_ago(l.timestamp),
            }
            for l in large
        ]

    def _time_ago(self, dt: datetime) -> str:
        """Format timestamp as time ago string."""
        delta = datetime.now() - dt
        minutes = int(delta.total_seconds() / 60)

        if minutes < 60:
            return f"{minutes}m ago"
        elif minutes < 1440:
            hours = minutes // 60
            return f"{hours}h ago"
        else:
            days = minutes // 1440
            return f"{days}d ago"


def demo():
    """Demonstrate liquidation monitor."""
    monitor = LiquidationMonitor()

    print("=" * 70)
    print("LIQUIDATION MONITOR")
    print("=" * 70)

    # Get BTC liquidation summary
    summary = monitor.get_summary("BTC", Decimal("67500"))

    print(f"\n💥 {summary.symbol} LIQUIDATION SUMMARY")
    print(f"   Current Price: ${summary.current_price:,}")
    print("-" * 60)

    # 24h totals
    print("\n24h Liquidations:")
    print(f"   Total:  ${float(summary.total_24h_usd) / 1e6:,.1f}M")
    print(f"   Longs:  ${float(summary.long_liquidations_usd) / 1e6:,.1f}M")
    print(f"   Shorts: ${float(summary.short_liquidations_usd) / 1e6:,.1f}M")

    # Cascade risk
    risk_emoji = {
        "low": "🟢",
        "medium": "🟡",
        "high": "🟠",
        "critical": "🔴",
    }
    print(f"\nCascade Risk: {risk_emoji[summary.cascade_risk]} {summary.cascade_risk.upper()}")

    # Heatmap
    print("\n" + "-" * 60)
    print("LIQUIDATION HEATMAP")
    print("-" * 60)

    print(f"\nLONG LIQUIDATIONS (below ${summary.current_price:,}):")
    for level in summary.long_levels[:4]:
        bar_len = min(int(float(level.total_value_usd) / 10_000_000), 20)
        bar = "█" * bar_len
        density_mark = "⚠️ " if level.density in ["high", "critical"] else ""
        print(
            f"  ${float(level.price):>10,.0f} {bar} "
            f"${float(level.total_value_usd) / 1e6:.0f}M {density_mark}{level.density.upper()}"
        )

    print(f"\nSHORT LIQUIDATIONS (above ${summary.current_price:,}):")
    for level in summary.short_levels[:4]:
        bar_len = min(int(float(level.total_value_usd) / 10_000_000), 20)
        bar = "█" * bar_len
        density_mark = "⚠️ " if level.density in ["high", "critical"] else ""
        print(
            f"  ${float(level.price):>10,.0f} {bar} "
            f"${float(level.total_value_usd) / 1e6:.0f}M {density_mark}{level.density.upper()}"
        )

    # Recent large liquidations
    print("\n" + "-" * 60)
    print("RECENT LARGE LIQUIDATIONS (>$1M)")
    print("-" * 60)

    large = monitor.get_recent_large_liquidations("BTC", min_value_usd=1_000_000, limit=5)
    if large:
        print(f"\n{'Exchange':<10} {'Side':<6} {'Price':>12} {'Value':>12} {'When':>10}")
        print("-" * 60)
        for l in large:
            print(
                f"{l['exchange']:<10} "
                f"{l['side']:<6} "
                f"${l['price']:>10,.0f} "
                f"${l['value_usd'] / 1e6:>10.1f}M "
                f"{l['time_ago']:>10}"
            )


if __name__ == "__main__":
    demo()
