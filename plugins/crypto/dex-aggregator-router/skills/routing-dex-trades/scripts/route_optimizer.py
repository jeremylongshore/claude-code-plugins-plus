#!/usr/bin/env python3
"""
Route optimization and ranking for DEX trades.

Analyzes quotes from multiple sources and ranks them by effective cost,
considering price, gas, and slippage.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional

from quote_fetcher import NormalizedQuote


@dataclass
class RouteAnalysis:
    """Analysis of a swap route with scoring."""

    quote: NormalizedQuote
    rank: int
    score: float  # 0-100, higher is better
    recommendation: str
    savings_vs_worst: Decimal  # Amount saved compared to worst quote
    savings_pct: float  # Percentage improvement


@dataclass
class RouteComparison:
    """Comparison of multiple routes."""

    best_route: RouteAnalysis
    all_routes: List[RouteAnalysis]
    total_quotes: int
    price_spread: float  # % difference between best and worst
    recommendation: str


class RouteOptimizer:
    """
    Optimizes and ranks DEX trade routes.

    Ranking factors:
    - Effective output (after gas)
    - Price impact
    - Route complexity (simpler = better for small trades)
    - Source reliability
    """

    # Reliability scores for aggregators (based on historical performance)
    SOURCE_RELIABILITY = {
        "1inch": 0.95,
        "Paraswap": 0.92,
        "0x": 0.90,
        "Uniswap": 0.98,
        "Curve": 0.97,
        "Balancer": 0.93,
    }

    def __init__(self, trade_size_usd: float = 0.0):
        """
        Initialize optimizer.

        Args:
            trade_size_usd: Approximate USD value of trade for sizing recommendations
        """
        self.trade_size_usd = trade_size_usd

    def rank_quotes(self, quotes: List[NormalizedQuote]) -> List[RouteAnalysis]:
        """
        Rank quotes by effective output.

        Args:
            quotes: List of normalized quotes

        Returns:
            List of RouteAnalysis sorted by score (best first)
        """
        if not quotes:
            return []

        # Calculate scores
        analyses = []
        for quote in quotes:
            score = self._calculate_score(quote, quotes)
            analyses.append(
                RouteAnalysis(
                    quote=quote,
                    rank=0,  # Will be set after sorting
                    score=score,
                    recommendation="",
                    savings_vs_worst=Decimal(0),
                    savings_pct=0.0,
                )
            )

        # Sort by score (highest first)
        analyses.sort(key=lambda x: x.score, reverse=True)

        # Assign ranks and calculate savings
        worst_output = min(a.quote.output_amount for a in analyses)
        max(a.quote.output_amount for a in analyses)

        for i, analysis in enumerate(analyses):
            analysis.rank = i + 1
            analysis.savings_vs_worst = analysis.quote.output_amount - worst_output
            if worst_output > 0:
                analysis.savings_pct = float((analysis.quote.output_amount - worst_output) / worst_output * 100)
            analysis.recommendation = self._get_recommendation(analysis, i == 0)

        return analyses

    def _calculate_score(self, quote: NormalizedQuote, all_quotes: List[NormalizedQuote]) -> float:
        """
        Calculate composite score for a quote.

        Score components:
        - Output score (0-60): Based on effective output relative to best
        - Gas efficiency (0-20): Lower gas = higher score
        - Reliability (0-10): Source reliability rating
        - Freshness (0-10): Newer quotes score higher
        """
        # Output score (60% weight)
        max_output = max(q.effective_rate for q in all_quotes)
        min_output = min(q.effective_rate for q in all_quotes)
        output_range = max_output - min_output

        if output_range > 0:
            output_score = float((quote.effective_rate - min_output) / output_range) * 60
        else:
            output_score = 60.0

        # Gas efficiency (20% weight)
        max_gas = max(q.gas_cost_usd for q in all_quotes)
        min_gas = min(q.gas_cost_usd for q in all_quotes)
        gas_range = max_gas - min_gas

        if gas_range > 0:
            # Invert: lower gas = higher score
            gas_score = (1 - (quote.gas_cost_usd - min_gas) / gas_range) * 20
        else:
            gas_score = 20.0

        # Reliability score (10% weight)
        reliability = self.SOURCE_RELIABILITY.get(quote.source, 0.85)
        reliability_score = reliability * 10

        # Freshness score (10% weight)
        # Assume all quotes are fresh if not expired
        freshness_score = 0.0 if quote.is_expired else 10.0

        return output_score + gas_score + reliability_score + freshness_score

    def _get_recommendation(self, analysis: RouteAnalysis, is_best: bool) -> str:
        """Generate recommendation text for a route."""
        if is_best:
            if analysis.score >= 90:
                return "BEST CHOICE - Optimal price and efficiency"
            elif analysis.score >= 80:
                return "RECOMMENDED - Strong overall value"
            else:
                return "BEST AVAILABLE - Consider waiting for better rates"

        if analysis.score >= 85:
            return "Good alternative with competitive pricing"
        elif analysis.score >= 70:
            return "Acceptable but not optimal"
        else:
            return "Not recommended - significantly worse than best"

    def compare_routes(self, quotes: List[NormalizedQuote]) -> Optional[RouteComparison]:
        """
        Generate comprehensive route comparison.

        Args:
            quotes: List of normalized quotes

        Returns:
            RouteComparison with analysis and recommendations
        """
        if not quotes:
            return None

        analyses = self.rank_quotes(quotes)

        best = analyses[0]
        worst_output = min(a.quote.output_amount for a in analyses)
        best_output = best.quote.output_amount

        # Calculate price spread
        if worst_output > 0:
            price_spread = float((best_output - worst_output) / worst_output * 100)
        else:
            price_spread = 0.0

        # Generate overall recommendation
        if price_spread < 0.1:
            overall_rec = "All sources offer similar rates. Choose based on preference."
        elif price_spread < 1.0:
            overall_rec = f"Best route saves {price_spread:.2f}%. Worth optimizing."
        else:
            overall_rec = f"Significant spread ({price_spread:.2f}%). Use best route."

        return RouteComparison(
            best_route=best,
            all_routes=analyses,
            total_quotes=len(quotes),
            price_spread=price_spread,
            recommendation=overall_rec,
        )

    def get_size_recommendation(self, trade_size_usd: float) -> str:
        """
        Get trade execution recommendation based on size.

        Args:
            trade_size_usd: Approximate USD value of trade

        Returns:
            Recommendation string
        """
        if trade_size_usd < 1000:
            return "Small trade: Use direct quote. Gas optimization savings may not exceed complexity cost."
        elif trade_size_usd < 10000:
            return "Medium trade: Compare routes and consider multi-hop if savings exceed 0.3%."
        elif trade_size_usd < 100000:
            return "Large trade: Analyze split orders across 2-3 venues. Multi-hop routes likely beneficial."
        else:
            return "Whale trade: Use split orders + MEV protection. Consider private transactions or OTC."


def demo():
    """Demonstrate route optimizer with mock data."""
    from datetime import datetime
    from decimal import Decimal

    # Create mock quotes
    quotes = [
        NormalizedQuote(
            source="1inch",
            input_token="ETH",
            output_token="USDC",
            input_amount=Decimal("10.0"),
            output_amount=Decimal("25432.18"),
            price=Decimal("2543.218"),
            price_impact=0.12,
            gas_estimate=150000,
            gas_price_gwei=30.0,
            gas_cost_usd=11.25,
            effective_rate=Decimal("2542.09"),
            route=["ETH", "USDC"],
            route_readable=["ETH", "USDC"],
            protocols=["Uniswap V3"],
            timestamp=datetime.now(),
        ),
        NormalizedQuote(
            source="Paraswap",
            input_token="ETH",
            output_token="USDC",
            input_amount=Decimal("10.0"),
            output_amount=Decimal("25398.45"),
            price=Decimal("2539.845"),
            price_impact=0.15,
            gas_estimate=180000,
            gas_price_gwei=30.0,
            gas_cost_usd=13.50,
            effective_rate=Decimal("2538.50"),
            route=["ETH", "USDC"],
            route_readable=["ETH", "USDC"],
            protocols=["Curve", "Uniswap V2"],
            timestamp=datetime.now(),
        ),
        NormalizedQuote(
            source="0x",
            input_token="ETH",
            output_token="USDC",
            input_amount=Decimal("10.0"),
            output_amount=Decimal("25410.00"),
            price=Decimal("2541.000"),
            price_impact=0.14,
            gas_estimate=160000,
            gas_price_gwei=30.0,
            gas_cost_usd=12.00,
            effective_rate=Decimal("2539.80"),
            route=["ETH", "USDC"],
            route_readable=["ETH", "USDC"],
            protocols=["Balancer", "SushiSwap"],
            timestamp=datetime.now(),
        ),
    ]

    optimizer = RouteOptimizer(trade_size_usd=25000)
    comparison = optimizer.compare_routes(quotes)

    if comparison:
        print("=" * 60)
        print("ROUTE COMPARISON")
        print("=" * 60)
        print(f"\nTotal quotes analyzed: {comparison.total_quotes}")
        print(f"Price spread: {comparison.price_spread:.2f}%")
        print(f"\nOverall: {comparison.recommendation}")

        print("\n" + "-" * 60)
        print("RANKED ROUTES")
        print("-" * 60)

        for analysis in comparison.all_routes:
            print(f"\n#{analysis.rank} {analysis.quote.source}")
            print(f"   Output: {analysis.quote.output_amount:.2f} USDC")
            print(f"   Effective: {analysis.quote.effective_rate:.2f} USDC/ETH")
            print(f"   Gas: ${analysis.quote.gas_cost_usd:.2f}")
            print(f"   Score: {analysis.score:.1f}/100")
            print(f"   Savings: +{analysis.savings_pct:.2f}% vs worst")
            print(f"   → {analysis.recommendation}")

        print("\n" + "-" * 60)
        print("SIZE RECOMMENDATION")
        print("-" * 60)
        print(optimizer.get_size_recommendation(25000))


if __name__ == "__main__":
    demo()
