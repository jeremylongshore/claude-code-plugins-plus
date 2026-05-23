#!/usr/bin/env python3
"""
Funding rate tracker and analyzer.

Tracks funding rates across exchanges with:
- Multi-exchange aggregation
- Historical averages
- Arbitrage opportunity detection
- Sentiment analysis
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime

from exchange_client import ExchangeClient, FundingRate, Exchange


@dataclass
class FundingAnalysis:
    """Aggregated funding rate analysis."""

    symbol: str
    rates: List[FundingRate]
    weighted_avg: float
    annualized_avg: float
    min_rate: FundingRate
    max_rate: FundingRate
    spread: float  # Max - min rate
    sentiment: str  # "bullish", "bearish", "neutral"
    sentiment_strength: str  # "strong", "moderate", "weak"
    arbitrage_opportunity: bool
    arbitrage_spread: float
    timestamp: datetime

    @property
    def is_extreme(self) -> bool:
        """Check if funding is at extreme levels."""
        return abs(self.weighted_avg) > 0.08  # 0.08% 8-hour

    @property
    def exchanges_count(self) -> int:
        """Number of exchanges with data."""
        return len(self.rates)


class FundingTracker:
    """
    Tracks and analyzes funding rates across exchanges.

    Features:
    - Real-time funding aggregation
    - Weighted average calculation
    - Sentiment analysis
    - Arbitrage detection
    """

    # Funding rate interpretation thresholds
    NEUTRAL_THRESHOLD = 0.005  # Below this is neutral
    MODERATE_THRESHOLD = 0.03  # Below this is moderate
    EXTREME_THRESHOLD = 0.08  # Above this is extreme

    # Arbitrage minimum spread
    ARB_MIN_SPREAD = 0.02  # 0.02% minimum for arbitrage

    def __init__(
        self,
        client: Optional[ExchangeClient] = None,
    ):
        """
        Initialize funding tracker.

        Args:
            client: Exchange client for data fetching
        """
        self.client = client or ExchangeClient(use_mock=True)

    def analyze(
        self,
        symbol: str,
        exchanges: Optional[List[Exchange]] = None,
    ) -> FundingAnalysis:
        """
        Analyze funding rates for a symbol.

        Args:
            symbol: Trading symbol (e.g., "BTC")
            exchanges: Exchanges to include

        Returns:
            FundingAnalysis with all metrics
        """
        # Fetch rates from all exchanges
        rates = self.client.get_all_funding_rates(symbol, exchanges)

        if not rates:
            raise ValueError(f"No funding data available for {symbol}")

        # Calculate weighted average (by estimated OI)
        # For simplicity, use equal weights
        avg_rate = sum(float(r.rate) for r in rates) / len(rates)
        avg_annualized = sum(r.annualized for r in rates) / len(rates)

        # Find min and max
        min_rate = min(rates, key=lambda r: r.rate)
        max_rate = max(rates, key=lambda r: r.rate)
        spread = float(max_rate.rate - min_rate.rate)

        # Determine sentiment
        sentiment, strength = self._analyze_sentiment(avg_rate)

        # Check for arbitrage opportunity
        arb_opportunity = spread >= self.ARB_MIN_SPREAD

        return FundingAnalysis(
            symbol=symbol,
            rates=rates,
            weighted_avg=round(avg_rate, 6),
            annualized_avg=round(avg_annualized, 2),
            min_rate=min_rate,
            max_rate=max_rate,
            spread=round(spread, 6),
            sentiment=sentiment,
            sentiment_strength=strength,
            arbitrage_opportunity=arb_opportunity,
            arbitrage_spread=round(spread, 6),
            timestamp=datetime.now(),
        )

    def _analyze_sentiment(
        self,
        avg_rate: float,
    ) -> tuple:
        """
        Analyze market sentiment from funding rate.

        Returns:
            (sentiment, strength) tuple
        """
        abs_rate = abs(avg_rate)

        # Determine direction
        if avg_rate > self.NEUTRAL_THRESHOLD:
            sentiment = "bullish"
        elif avg_rate < -self.NEUTRAL_THRESHOLD:
            sentiment = "bearish"
        else:
            sentiment = "neutral"

        # Determine strength
        if abs_rate >= self.EXTREME_THRESHOLD:
            strength = "extreme"
        elif abs_rate >= self.MODERATE_THRESHOLD:
            strength = "strong"
        elif abs_rate >= self.NEUTRAL_THRESHOLD:
            strength = "moderate"
        else:
            strength = "weak"

        return sentiment, strength

    def get_arbitrage_opportunities(
        self,
        symbols: List[str],
        min_spread: float = 0.02,
    ) -> List[Dict]:
        """
        Find funding arbitrage opportunities across symbols.

        Strategy: Long on exchange with negative/low funding,
        Short on exchange with positive/high funding.

        Args:
            symbols: Symbols to check
            min_spread: Minimum spread to report

        Returns:
            List of arbitrage opportunities
        """
        opportunities = []

        for symbol in symbols:
            analysis = self.analyze(symbol)

            if analysis.spread >= min_spread:
                profit_8h = analysis.spread
                profit_daily = profit_8h * 3
                profit_annual = profit_8h * 365 * 3

                opportunities.append(
                    {
                        "symbol": symbol,
                        "long_exchange": analysis.min_rate.exchange,
                        "long_rate": float(analysis.min_rate.rate),
                        "short_exchange": analysis.max_rate.exchange,
                        "short_rate": float(analysis.max_rate.rate),
                        "spread": analysis.spread,
                        "profit_8h_pct": round(profit_8h, 4),
                        "profit_daily_pct": round(profit_daily, 4),
                        "profit_annual_pct": round(profit_annual, 2),
                    }
                )

        # Sort by spread descending
        opportunities.sort(key=lambda x: x["spread"], reverse=True)
        return opportunities

    def get_extreme_funding(
        self,
        symbols: List[str],
        threshold: float = 0.08,
    ) -> List[Dict]:
        """
        Find symbols with extreme funding rates.

        Extreme funding often indicates crowded trades and
        potential mean reversion opportunities.

        Args:
            symbols: Symbols to check
            threshold: Extreme threshold (default 0.08%)

        Returns:
            List of extreme funding situations
        """
        extreme = []

        for symbol in symbols:
            analysis = self.analyze(symbol)

            if abs(analysis.weighted_avg) >= threshold:
                extreme.append(
                    {
                        "symbol": symbol,
                        "avg_rate": analysis.weighted_avg,
                        "annualized": analysis.annualized_avg,
                        "sentiment": analysis.sentiment,
                        "strength": analysis.sentiment_strength,
                        "signal": "short" if analysis.weighted_avg > 0 else "long",
                        "signal_reason": "Contrarian: extreme funding often reverts",
                    }
                )

        # Sort by absolute rate descending
        extreme.sort(key=lambda x: abs(x["avg_rate"]), reverse=True)
        return extreme


def demo():
    """Demonstrate funding tracker."""
    tracker = FundingTracker()

    print("=" * 70)
    print("FUNDING RATE TRACKER")
    print("=" * 70)

    # Analyze BTC funding
    analysis = tracker.analyze("BTC")

    print(f"\n📊 {analysis.symbol} FUNDING ANALYSIS")
    print("-" * 50)

    print(f"\n{'Exchange':<12} {'Current':>10} {'Annualized':>12} {'Next Payment':>14}")
    print("-" * 50)

    for rate in sorted(analysis.rates, key=lambda r: r.rate, reverse=True):
        print(
            f"{rate.exchange:<12} {float(rate.rate):>+9.4%} {rate.annualized:>+11.2f}% {rate.time_to_payment_str:>14}"
        )

    print("-" * 50)
    print(f"\nWeighted Average: {analysis.weighted_avg:+.4%}")
    print(f"Annualized: {analysis.annualized_avg:+.2f}%")
    print(f"Spread (max-min): {analysis.spread:.4%}")
    print(f"\nSentiment: {analysis.sentiment_strength.title()} {analysis.sentiment.title()}")

    if analysis.is_extreme:
        print("\n⚠️  EXTREME FUNDING - Contrarian opportunity")

    if analysis.arbitrage_opportunity:
        print("\n💰 ARBITRAGE OPPORTUNITY")
        print(f"   Long on {analysis.min_rate.exchange} ({float(analysis.min_rate.rate):+.4%})")
        print(f"   Short on {analysis.max_rate.exchange} ({float(analysis.max_rate.rate):+.4%})")
        print(f"   Profit: {analysis.arbitrage_spread:.4%} per 8h")

    # Check multiple symbols for arbitrage
    print("\n" + "=" * 70)
    print("FUNDING ARBITRAGE SCANNER")
    print("=" * 70)

    opportunities = tracker.get_arbitrage_opportunities(["BTC", "ETH", "SOL"])
    if opportunities:
        print(f"\n{'Symbol':<8} {'Long On':<12} {'Short On':<12} {'Spread':>8} {'Annual':>10}")
        print("-" * 50)
        for opp in opportunities:
            print(
                f"{opp['symbol']:<8} "
                f"{opp['long_exchange']:<12} "
                f"{opp['short_exchange']:<12} "
                f"{opp['spread']:>7.4%} "
                f"{opp['profit_annual_pct']:>+9.1f}%"
            )
    else:
        print("\nNo arbitrage opportunities found")


if __name__ == "__main__":
    demo()
