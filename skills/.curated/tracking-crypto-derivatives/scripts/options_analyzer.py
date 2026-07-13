#!/usr/bin/env python3
"""
Options market analyzer.

Analyzes crypto options markets with:
- Implied volatility tracking
- Put/call ratio analysis
- Max pain calculation
- Options flow detection
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List, Optional
from datetime import datetime, date

from exchange_client import ExchangeClient, OptionsSnapshot


@dataclass
class OptionsAnalysis:
    """Comprehensive options analysis."""

    symbol: str
    snapshot: OptionsSnapshot
    iv_interpretation: str  # "high", "normal", "low"
    iv_percentile: float  # Estimated percentile (0-100)
    sentiment_from_pcr: str  # "bullish", "bearish", "neutral"
    sentiment_from_skew: str  # "bullish", "bearish", "neutral"
    overall_sentiment: str
    max_pain_distance_pct: float  # Distance from current to max pain
    expiry_pressure: str  # "high", "medium", "low"
    timestamp: datetime


@dataclass
class OptionsFlow:
    """Significant options trade."""

    symbol: str
    expiry: str
    strike: Decimal
    option_type: str  # "call" or "put"
    side: str  # "buy" or "sell"
    size_contracts: int
    premium_usd: Decimal
    iv_at_trade: float
    interpretation: str
    timestamp: datetime


class OptionsAnalyzer:
    """
    Analyzes crypto options markets.

    Features:
    - IV analysis and percentile ranking
    - Put/call ratio interpretation
    - Max pain calculation
    - Flow analysis
    """

    # IV interpretation thresholds
    HIGH_IV = 70.0
    LOW_IV = 40.0

    # Put/call interpretation
    BEARISH_PCR = 1.2  # Above this is bearish
    BULLISH_PCR = 0.7  # Below this is bullish

    def __init__(
        self,
        client: Optional[ExchangeClient] = None,
    ):
        """
        Initialize options analyzer.

        Args:
            client: Exchange client for data fetching
        """
        self.client = client or ExchangeClient(use_mock=True)

    def analyze(
        self,
        symbol: str,
        expiry: Optional[str] = None,
        current_price: Optional[Decimal] = None,
    ) -> OptionsAnalysis:
        """
        Analyze options market for a symbol.

        Args:
            symbol: Trading symbol (e.g., "BTC")
            expiry: Target expiry date (default: nearest)
            current_price: Current spot price

        Returns:
            OptionsAnalysis with all metrics
        """
        # Fetch options snapshot
        snapshot = self.client.get_options_snapshot(symbol, expiry)

        if snapshot is None:
            raise ValueError(f"No options data available for {symbol}")

        # Set default price if not provided
        if current_price is None:
            if symbol == "BTC":
                current_price = Decimal("67500")
            elif symbol == "ETH":
                current_price = Decimal("2500")
            else:
                current_price = Decimal("100")

        # Interpret IV
        iv_interp, iv_pctl = self._interpret_iv(snapshot.atm_iv, symbol)

        # Interpret put/call ratio
        pcr_sentiment = self._interpret_pcr(snapshot.put_call_ratio_volume)

        # Interpret skew (simplified - just using PCR OI as proxy)
        skew_sentiment = self._interpret_pcr(snapshot.put_call_ratio_oi)

        # Overall sentiment (combine signals)
        overall = self._combine_sentiment(pcr_sentiment, skew_sentiment)

        # Max pain distance
        max_pain_dist = (float(snapshot.max_pain) - float(current_price)) / float(current_price) * 100

        # Expiry pressure (days until expiry)
        expiry_pressure = self._assess_expiry_pressure(snapshot.expiry)

        return OptionsAnalysis(
            symbol=symbol,
            snapshot=snapshot,
            iv_interpretation=iv_interp,
            iv_percentile=iv_pctl,
            sentiment_from_pcr=pcr_sentiment,
            sentiment_from_skew=skew_sentiment,
            overall_sentiment=overall,
            max_pain_distance_pct=round(max_pain_dist, 2),
            expiry_pressure=expiry_pressure,
            timestamp=datetime.now(),
        )

    def _interpret_iv(
        self,
        iv: float,
        symbol: str,
    ) -> tuple:
        """
        Interpret implied volatility.

        Returns:
            (interpretation, estimated_percentile)
        """
        # Adjust thresholds by asset (crypto generally high IV)
        high = self.HIGH_IV
        low = self.LOW_IV

        if iv >= high:
            interp = "high"
            pctl = min(100, 50 + (iv - high))
        elif iv <= low:
            interp = "low"
            pctl = max(0, 50 - (low - iv))
        else:
            interp = "normal"
            pctl = 50 + ((iv - 55) / 15 * 30)  # Scale around 55

        return interp, round(pctl, 0)

    def _interpret_pcr(self, pcr: float) -> str:
        """Interpret put/call ratio."""
        if pcr >= self.BEARISH_PCR:
            return "bearish"
        elif pcr <= self.BULLISH_PCR:
            return "bullish"
        else:
            return "neutral"

    def _combine_sentiment(self, pcr_sent: str, skew_sent: str) -> str:
        """Combine sentiment signals."""
        if pcr_sent == skew_sent:
            return pcr_sent
        elif pcr_sent == "neutral":
            return skew_sent
        elif skew_sent == "neutral":
            return pcr_sent
        else:
            return "mixed"

    def _assess_expiry_pressure(self, expiry: str) -> str:
        """Assess expiry pressure based on days remaining."""
        try:
            exp_date = datetime.strptime(expiry, "%Y-%m-%d").date()
            days = (exp_date - date.today()).days

            if days <= 2:
                return "high"
            elif days <= 7:
                return "medium"
            else:
                return "low"
        except Exception:
            return "unknown"

    def get_max_pain_levels(
        self,
        symbol: str,
        expiries: Optional[List[str]] = None,
    ) -> List[Dict]:
        """
        Get max pain levels for multiple expiries.

        Args:
            symbol: Trading symbol
            expiries: List of expiry dates

        Returns:
            List of max pain levels by expiry
        """
        if expiries is None:
            # Default expiries (next few Fridays)
            expiries = ["2025-01-17", "2025-01-24", "2025-01-31"]

        levels = []
        for exp in expiries:
            try:
                snapshot = self.client.get_options_snapshot(symbol, exp)
                if snapshot:
                    levels.append(
                        {
                            "expiry": exp,
                            "max_pain": float(snapshot.max_pain),
                            "call_oi": float(snapshot.total_call_oi),
                            "put_oi": float(snapshot.total_put_oi),
                            "pcr_oi": snapshot.put_call_ratio_oi,
                        }
                    )
            except Exception:
                continue

        return levels

    def generate_mock_flow(
        self,
        symbol: str,
        count: int = 5,
    ) -> List[OptionsFlow]:
        """
        Generate mock options flow data.

        In production, this would track actual large trades.
        """
        import random

        if symbol == "BTC":
            base_price = 67500
        elif symbol == "ETH":
            base_price = 2500
        else:
            base_price = 100

        flows = []
        for i in range(count):
            opt_type = random.choice(["call", "put"])
            # Strikes around current price
            strike = base_price * (1 + random.uniform(-0.15, 0.15))
            strike = round(strike / 1000) * 1000  # Round to nearest 1000

            size = random.randint(100, 2000)
            premium = size * random.uniform(500, 5000)

            # Interpretation based on type and likely direction
            if opt_type == "call":
                interp = "Bullish positioning" if random.random() > 0.3 else "Covered call selling"
            else:
                interp = "Bearish bet" if random.random() > 0.5 else "Protective put"

            flows.append(
                OptionsFlow(
                    symbol=symbol,
                    expiry="2025-01-31",
                    strike=Decimal(str(int(strike))),
                    option_type=opt_type,
                    side=random.choice(["buy", "sell"]),
                    size_contracts=size,
                    premium_usd=Decimal(str(int(premium))),
                    iv_at_trade=round(55 + random.uniform(-10, 15), 1),
                    interpretation=interp,
                    timestamp=datetime.now(),
                )
            )

        return sorted(flows, key=lambda x: x.premium_usd, reverse=True)


def demo():
    """Demonstrate options analyzer."""
    analyzer = OptionsAnalyzer()

    print("=" * 70)
    print("OPTIONS MARKET ANALYZER")
    print("=" * 70)

    # Analyze BTC options
    analysis = analyzer.analyze("BTC", current_price=Decimal("67500"))

    print(f"\n📊 {analysis.symbol} OPTIONS ANALYSIS")
    print("-" * 50)

    snap = analysis.snapshot
    print(f"\nExpiry: {snap.expiry}")
    print(f"Exchange: {snap.exchange}")

    print("\nImplied Volatility:")
    print(f"   ATM IV: {snap.atm_iv:.1f}%")
    print(f"   Interpretation: {analysis.iv_interpretation.upper()}")
    print(f"   IV Rank: {analysis.iv_percentile:.0f}th percentile")

    print("\nPut/Call Analysis:")
    print(f"   PCR (Volume): {snap.put_call_ratio_volume:.2f}")
    print(f"   PCR (OI): {snap.put_call_ratio_oi:.2f}")
    print(f"   Sentiment: {analysis.sentiment_from_pcr.upper()}")

    print("\nMax Pain:")
    print(f"   Price: ${snap.max_pain:,.0f}")
    print(f"   Distance: {analysis.max_pain_distance_pct:+.1f}% from current")

    print("\nOpen Interest:")
    print(f"   Calls: ${float(snap.total_call_oi) / 1e9:.2f}B")
    print(f"   Puts:  ${float(snap.total_put_oi) / 1e9:.2f}B")

    print(f"\nOverall Sentiment: {analysis.overall_sentiment.upper()}")
    print(f"Expiry Pressure: {analysis.expiry_pressure.upper()}")

    # Max pain levels
    print("\n" + "-" * 50)
    print("MAX PAIN BY EXPIRY")
    print("-" * 50)

    levels = analyzer.get_max_pain_levels("BTC")
    print(f"\n{'Expiry':<12} {'Max Pain':>12} {'Call OI':>12} {'Put OI':>12} {'PCR':>6}")
    print("-" * 50)
    for lvl in levels:
        print(
            f"{lvl['expiry']:<12} "
            f"${lvl['max_pain']:>10,.0f} "
            f"${lvl['call_oi'] / 1e9:>10.1f}B "
            f"${lvl['put_oi'] / 1e9:>10.1f}B "
            f"{lvl['pcr_oi']:>5.2f}"
        )

    # Options flow
    print("\n" + "-" * 50)
    print("SIGNIFICANT OPTIONS FLOW (Simulated)")
    print("-" * 50)

    flows = analyzer.generate_mock_flow("BTC", count=5)
    print(f"\n{'Type':<6} {'Strike':>10} {'Size':>8} {'Premium':>12} {'Interpretation':<25}")
    print("-" * 70)
    for flow in flows:
        print(
            f"{flow.option_type.upper():<6} "
            f"${float(flow.strike):>8,.0f} "
            f"{flow.size_contracts:>8} "
            f"${float(flow.premium_usd):>10,.0f} "
            f"{flow.interpretation:<25}"
        )


if __name__ == "__main__":
    demo()
