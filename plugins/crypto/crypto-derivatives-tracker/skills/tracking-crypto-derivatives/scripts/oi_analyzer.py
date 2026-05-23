#!/usr/bin/env python3
"""
Open Interest analyzer.

Analyzes open interest across exchanges with:
- Multi-exchange aggregation
- Trend analysis
- OI vs price divergence detection
- Long/short ratio tracking
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List, Optional
from datetime import datetime

from exchange_client import ExchangeClient, OpenInterest, Exchange


@dataclass
class OIAnalysis:
    """Aggregated open interest analysis."""

    symbol: str
    exchanges: List[OpenInterest]
    total_oi_usd: Decimal
    total_oi_contracts: Decimal
    avg_change_24h: float
    avg_change_7d: float
    weighted_long_ratio: float
    dominant_exchange: str
    dominant_share: float
    trend: str  # "increasing", "decreasing", "stable"
    trend_strength: str  # "strong", "moderate", "weak"
    timestamp: datetime

    @property
    def is_increasing(self) -> bool:
        """Check if OI is increasing."""
        return self.avg_change_24h > 2.0

    @property
    def is_decreasing(self) -> bool:
        """Check if OI is decreasing."""
        return self.avg_change_24h < -2.0

    @property
    def long_percentage(self) -> float:
        """Calculate long percentage from ratio."""
        return self.weighted_long_ratio / (1 + self.weighted_long_ratio) * 100


@dataclass
class OIDivergence:
    """OI vs Price divergence signal."""

    symbol: str
    oi_direction: str  # "up" or "down"
    price_direction: str  # "up" or "down"
    oi_change_pct: float
    price_change_pct: float
    signal: str  # "bullish", "bearish", "short_squeeze", "long_liquidation"
    description: str
    confidence: str  # "high", "medium", "low"


class OIAnalyzer:
    """
    Analyzes open interest patterns and signals.

    Features:
    - Multi-exchange aggregation
    - Trend detection
    - Divergence analysis
    - Long/short positioning
    """

    # Trend thresholds
    STRONG_CHANGE = 10.0  # >10% is strong
    MODERATE_CHANGE = 5.0  # >5% is moderate

    def __init__(
        self,
        client: Optional[ExchangeClient] = None,
    ):
        """
        Initialize OI analyzer.

        Args:
            client: Exchange client for data fetching
        """
        self.client = client or ExchangeClient(use_mock=True)

    def analyze(
        self,
        symbol: str,
        exchanges: Optional[List[Exchange]] = None,
    ) -> OIAnalysis:
        """
        Analyze open interest for a symbol.

        Args:
            symbol: Trading symbol (e.g., "BTC")
            exchanges: Exchanges to include

        Returns:
            OIAnalysis with all metrics
        """
        # Fetch OI from all exchanges
        oi_list = self.client.get_all_open_interest(symbol, exchanges)

        if not oi_list:
            raise ValueError(f"No OI data available for {symbol}")

        # Calculate totals
        total_usd = sum(float(oi.oi_usd) for oi in oi_list)
        total_contracts = sum(float(oi.oi_contracts) for oi in oi_list)

        # Calculate weighted averages
        avg_24h = sum(oi.change_24h_pct * float(oi.oi_usd) for oi in oi_list) / total_usd
        avg_7d = sum(oi.change_7d_pct * float(oi.oi_usd) for oi in oi_list) / total_usd

        # Weighted long ratio
        weighted_long = sum(oi.long_ratio * float(oi.oi_usd) for oi in oi_list) / total_usd

        # Find dominant exchange
        dominant = max(oi_list, key=lambda x: x.oi_usd)
        dominant_share = float(dominant.oi_usd) / total_usd * 100

        # Determine trend
        trend, strength = self._analyze_trend(avg_24h, avg_7d)

        return OIAnalysis(
            symbol=symbol,
            exchanges=oi_list,
            total_oi_usd=Decimal(str(int(total_usd))),
            total_oi_contracts=Decimal(str(int(total_contracts))),
            avg_change_24h=round(avg_24h, 2),
            avg_change_7d=round(avg_7d, 2),
            weighted_long_ratio=round(weighted_long, 2),
            dominant_exchange=dominant.exchange,
            dominant_share=round(dominant_share, 1),
            trend=trend,
            trend_strength=strength,
            timestamp=datetime.now(),
        )

    def _analyze_trend(
        self,
        change_24h: float,
        change_7d: float,
    ) -> tuple:
        """
        Analyze OI trend from changes.

        Returns:
            (trend, strength) tuple
        """
        # Determine direction from 24h change
        if change_24h > 2.0:
            trend = "increasing"
        elif change_24h < -2.0:
            trend = "decreasing"
        else:
            trend = "stable"

        # Determine strength from magnitude
        abs_change = abs(change_24h)
        if abs_change >= self.STRONG_CHANGE:
            strength = "strong"
        elif abs_change >= self.MODERATE_CHANGE:
            strength = "moderate"
        else:
            strength = "weak"

        return trend, strength

    def detect_divergence(
        self,
        symbol: str,
        price_change_24h: float,
    ) -> Optional[OIDivergence]:
        """
        Detect OI vs price divergence.

        Classic interpretation:
        - Rising OI + Rising Price = Strong bullish trend
        - Rising OI + Falling Price = Strong bearish trend
        - Falling OI + Rising Price = Short covering (weak rally)
        - Falling OI + Falling Price = Long liquidation (weak selloff)

        Args:
            symbol: Trading symbol
            price_change_24h: Price change in last 24h (%)

        Returns:
            OIDivergence if divergence detected
        """
        analysis = self.analyze(symbol)
        oi_change = analysis.avg_change_24h

        oi_dir = "up" if oi_change > 0 else "down"
        price_dir = "up" if price_change_24h > 0 else "down"

        # Determine signal
        if oi_change > 2 and price_change_24h > 2:
            signal = "bullish"
            desc = "Rising OI confirms bullish trend - new longs entering"
            confidence = "high" if oi_change > 5 else "medium"
        elif oi_change > 2 and price_change_24h < -2:
            signal = "bearish"
            desc = "Rising OI during selloff - new shorts entering"
            confidence = "high" if oi_change > 5 else "medium"
        elif oi_change < -2 and price_change_24h > 2:
            signal = "short_squeeze"
            desc = "Falling OI during rally - short covering, may be weak"
            confidence = "medium"
        elif oi_change < -2 and price_change_24h < -2:
            signal = "long_liquidation"
            desc = "Falling OI during selloff - long liquidations, may find support"
            confidence = "medium"
        else:
            return None  # No significant divergence

        return OIDivergence(
            symbol=symbol,
            oi_direction=oi_dir,
            price_direction=price_dir,
            oi_change_pct=oi_change,
            price_change_pct=price_change_24h,
            signal=signal,
            description=desc,
            confidence=confidence,
        )

    def get_market_share(
        self,
        symbol: str,
    ) -> List[Dict]:
        """
        Get OI market share by exchange.

        Args:
            symbol: Trading symbol

        Returns:
            List of exchange market shares
        """
        analysis = self.analyze(symbol)
        total = float(analysis.total_oi_usd)

        shares = []
        for oi in analysis.exchanges:
            share = float(oi.oi_usd) / total * 100
            shares.append(
                {
                    "exchange": oi.exchange,
                    "oi_usd": float(oi.oi_usd),
                    "share_pct": round(share, 1),
                    "change_24h": oi.change_24h_pct,
                    "long_ratio": oi.long_ratio,
                }
            )

        return sorted(shares, key=lambda x: x["oi_usd"], reverse=True)


def demo():
    """Demonstrate OI analyzer."""
    analyzer = OIAnalyzer()

    print("=" * 70)
    print("OPEN INTEREST ANALYZER")
    print("=" * 70)

    # Analyze BTC OI
    analysis = analyzer.analyze("BTC")

    print(f"\n📈 {analysis.symbol} OPEN INTEREST ANALYSIS")
    print("-" * 60)

    print(f"\n{'Exchange':<12} {'OI (USD)':>14} {'24h Chg':>10} {'7d Chg':>10} {'Share':>8}")
    print("-" * 60)

    for oi in sorted(analysis.exchanges, key=lambda x: x.oi_usd, reverse=True):
        share = float(oi.oi_usd) / float(analysis.total_oi_usd) * 100
        print(
            f"{oi.exchange:<12} "
            f"${float(oi.oi_usd) / 1e9:>12.2f}B "
            f"{oi.change_24h_pct:>+9.1f}% "
            f"{oi.change_7d_pct:>+9.1f}% "
            f"{share:>7.1f}%"
        )

    print("-" * 60)
    print(f"\nTotal OI: ${float(analysis.total_oi_usd) / 1e9:.2f}B")
    print(f"24h Change: {analysis.avg_change_24h:+.1f}%")
    print(f"7d Change: {analysis.avg_change_7d:+.1f}%")
    print(f"\nLong/Short Ratio: {analysis.weighted_long_ratio:.2f} ({analysis.long_percentage:.1f}% long)")
    print(f"Trend: {analysis.trend_strength.title()} {analysis.trend.title()}")
    print(f"Dominant Exchange: {analysis.dominant_exchange} ({analysis.dominant_share:.1f}%)")

    # Check for divergence
    print("\n" + "=" * 70)
    print("DIVERGENCE ANALYSIS")
    print("=" * 70)

    # Simulate price change
    price_change = 3.5  # Example: +3.5% price move
    divergence = analyzer.detect_divergence("BTC", price_change)

    if divergence:
        print("\n🔍 Divergence Detected!")
        print(f"   OI:    {divergence.oi_direction} ({divergence.oi_change_pct:+.1f}%)")
        print(f"   Price: {divergence.price_direction} ({divergence.price_change_pct:+.1f}%)")
        print(f"   Signal: {divergence.signal.upper()}")
        print(f"   {divergence.description}")
        print(f"   Confidence: {divergence.confidence}")
    else:
        print("\nNo significant divergence detected")

    # Market share breakdown
    print("\n" + "=" * 70)
    print("MARKET SHARE BREAKDOWN")
    print("=" * 70)

    shares = analyzer.get_market_share("BTC")
    for s in shares:
        bar = "█" * int(s["share_pct"] / 2)
        print(f"{s['exchange']:<12} {bar} {s['share_pct']:.1f}%")


if __name__ == "__main__":
    demo()
