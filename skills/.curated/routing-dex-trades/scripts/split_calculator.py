#!/usr/bin/env python3
"""
Split order calculator for large DEX trades.

Optimizes order splitting across multiple DEXs to minimize
price impact and slippage for whale-sized trades.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional

from quote_fetcher import NormalizedQuote


@dataclass
class SplitAllocation:
    """Allocation for a single venue in a split order."""

    source: str
    percentage: float  # 0-100
    input_amount: Decimal
    expected_output: Decimal
    price_impact: float
    gas_cost_usd: float


@dataclass
class SplitRecommendation:
    """Complete split order recommendation."""

    allocations: List[SplitAllocation]
    total_input: Decimal
    total_output: Decimal
    single_venue_output: Decimal
    improvement_amount: Decimal
    improvement_pct: float
    total_gas_cost: float
    net_benefit: Decimal
    recommendation: str
    is_split_beneficial: bool


class SplitCalculator:
    """
    Calculates optimal order splits across multiple DEXs.

    Uses a greedy algorithm to allocate trade volume to venues
    with the lowest marginal price impact at each step.
    """

    # Price impact curve assumptions (simplified)
    # Real implementation would use actual liquidity depth
    IMPACT_MULTIPLIERS = {
        "Uniswap V3": 0.8,  # Lower impact due to concentrated liquidity
        "Curve": 0.5,  # Very low impact for stablecoin pairs
        "Balancer": 1.0,  # Standard impact
        "SushiSwap": 1.2,  # Slightly higher impact
        "Uniswap V2": 1.3,  # Higher impact due to x*y=k
    }

    def __init__(
        self,
        min_split_size_usd: float = 5000.0,
        max_venues: int = 4,
        min_allocation_pct: float = 10.0,
    ):
        """
        Initialize split calculator.

        Args:
            min_split_size_usd: Minimum trade size to consider splitting
            max_venues: Maximum number of venues to split across
            min_allocation_pct: Minimum allocation per venue (%)
        """
        self.min_split_size_usd = min_split_size_usd
        self.max_venues = max_venues
        self.min_allocation_pct = min_allocation_pct

    def calculate_split(
        self,
        quotes: List[NormalizedQuote],
        total_amount: Decimal,
        price_usd: float = 2500.0,
    ) -> Optional[SplitRecommendation]:
        """
        Calculate optimal split across available venues.

        Args:
            quotes: Available quotes from different sources
            total_amount: Total amount to swap
            price_usd: USD price of input token

        Returns:
            SplitRecommendation with optimal allocation
        """
        if not quotes:
            return None

        trade_size_usd = float(total_amount) * price_usd

        # Don't split small trades
        if trade_size_usd < self.min_split_size_usd:
            best_quote = max(quotes, key=lambda q: q.effective_rate)
            return self._single_venue_recommendation(best_quote, total_amount)

        # Calculate optimal split
        allocations = self._optimize_split(quotes, total_amount)

        if not allocations:
            best_quote = max(quotes, key=lambda q: q.effective_rate)
            return self._single_venue_recommendation(best_quote, total_amount)

        # Calculate totals
        total_output = sum(a.expected_output for a in allocations)
        total_gas = sum(a.gas_cost_usd for a in allocations)

        # Compare to single-venue execution
        best_single = max(quotes, key=lambda q: q.effective_rate)
        single_venue_output = best_single.output_amount

        improvement = total_output - single_venue_output
        improvement_pct = float(improvement / single_venue_output * 100) if single_venue_output > 0 else 0.0

        # Net benefit after extra gas
        single_gas = best_single.gas_cost_usd
        extra_gas = total_gas - single_gas
        net_benefit = improvement - Decimal(extra_gas)

        is_beneficial = net_benefit > 0

        if is_beneficial:
            rec = f"Split order saves ${float(net_benefit):.2f} ({improvement_pct:.2f}% improvement after gas)"
        else:
            rec = f"Single venue preferred. Split would cost extra ${float(-net_benefit):.2f} in gas overhead."

        return SplitRecommendation(
            allocations=allocations,
            total_input=total_amount,
            total_output=total_output,
            single_venue_output=single_venue_output,
            improvement_amount=improvement,
            improvement_pct=improvement_pct,
            total_gas_cost=total_gas,
            net_benefit=net_benefit,
            recommendation=rec,
            is_split_beneficial=is_beneficial,
        )

    def _optimize_split(self, quotes: List[NormalizedQuote], total_amount: Decimal) -> List[SplitAllocation]:
        """
        Greedy optimization of split allocations.

        Strategy: Iteratively allocate chunks to the venue with
        the best marginal rate at each step.
        """
        # Sort quotes by effective rate (best first)
        sorted_quotes = sorted(quotes, key=lambda q: q.effective_rate, reverse=True)

        # Limit to max venues
        venues = sorted_quotes[: self.max_venues]

        if len(venues) == 1:
            return [self._create_allocation(venues[0], Decimal(100), total_amount)]

        # Simple allocation: proportional to inverse price impact
        total_weight = sum(
            1 / (q.price_impact + 0.01)
            for q in venues  # Add 0.01 to avoid div by zero
        )

        allocations = []
        remaining = total_amount

        for i, quote in enumerate(venues):
            # Calculate weight-based allocation
            weight = 1 / (quote.price_impact + 0.01)
            pct = (weight / total_weight) * 100

            # Enforce minimum allocation
            if pct < self.min_allocation_pct and i < len(venues) - 1:
                continue

            # Last venue gets remaining
            if i == len(venues) - 1:
                pct = float(remaining / total_amount * 100)

            amount = total_amount * Decimal(pct / 100)

            if amount > 0:
                allocation = self._create_allocation(quote, Decimal(pct), amount)
                allocations.append(allocation)
                remaining -= amount

        return allocations

    def _create_allocation(self, quote: NormalizedQuote, pct: Decimal, amount: Decimal) -> SplitAllocation:
        """Create allocation entry for a venue."""
        # Scale output proportionally (simplified)
        output_ratio = amount / quote.input_amount if quote.input_amount > 0 else Decimal(0)
        expected_output = quote.output_amount * output_ratio

        # Estimate price impact for partial amount
        # Impact typically scales sub-linearly with size
        impact_scale = float(output_ratio) ** 0.5
        adjusted_impact = quote.price_impact * impact_scale

        # Gas cost is fixed per transaction
        gas_cost = quote.gas_cost_usd

        return SplitAllocation(
            source=quote.source,
            percentage=float(pct),
            input_amount=amount,
            expected_output=expected_output,
            price_impact=adjusted_impact,
            gas_cost_usd=gas_cost,
        )

    def _single_venue_recommendation(self, quote: NormalizedQuote, amount: Decimal) -> SplitRecommendation:
        """Create recommendation for single-venue execution."""
        allocation = self._create_allocation(quote, Decimal(100), amount)

        return SplitRecommendation(
            allocations=[allocation],
            total_input=amount,
            total_output=quote.output_amount,
            single_venue_output=quote.output_amount,
            improvement_amount=Decimal(0),
            improvement_pct=0.0,
            total_gas_cost=quote.gas_cost_usd,
            net_benefit=Decimal(0),
            recommendation="Single venue is optimal for this trade size.",
            is_split_beneficial=False,
        )

    def estimate_split_impact(self, base_impact: float, allocation_pct: float) -> float:
        """
        Estimate price impact for a partial allocation.

        Impact scales approximately with sqrt of trade size due to
        AMM mechanics (x*y=k curves).
        """
        return base_impact * (allocation_pct / 100) ** 0.5


def demo():
    """Demonstrate split calculator with mock data."""
    from datetime import datetime

    # Create mock quotes for a large trade
    quotes = [
        NormalizedQuote(
            source="1inch",
            input_token="ETH",
            output_token="USDC",
            input_amount=Decimal("100.0"),
            output_amount=Decimal("251200.00"),
            price=Decimal("2512.00"),
            price_impact=1.5,
            gas_estimate=150000,
            gas_price_gwei=30.0,
            gas_cost_usd=11.25,
            effective_rate=Decimal("2511.89"),
            route=["ETH", "USDC"],
            route_readable=["ETH", "USDC"],
            protocols=["Uniswap V3"],
            timestamp=datetime.now(),
        ),
        NormalizedQuote(
            source="Paraswap",
            input_token="ETH",
            output_token="USDC",
            input_amount=Decimal("100.0"),
            output_amount=Decimal("250800.00"),
            price=Decimal("2508.00"),
            price_impact=1.8,
            gas_estimate=180000,
            gas_price_gwei=30.0,
            gas_cost_usd=13.50,
            effective_rate=Decimal("2507.87"),
            route=["ETH", "USDC"],
            route_readable=["ETH", "USDC"],
            protocols=["Curve"],
            timestamp=datetime.now(),
        ),
        NormalizedQuote(
            source="0x",
            input_token="ETH",
            output_token="USDC",
            input_amount=Decimal("100.0"),
            output_amount=Decimal("250500.00"),
            price=Decimal("2505.00"),
            price_impact=2.0,
            gas_estimate=160000,
            gas_price_gwei=30.0,
            gas_cost_usd=12.00,
            effective_rate=Decimal("2504.88"),
            route=["ETH", "USDC"],
            route_readable=["ETH", "USDC"],
            protocols=["Balancer"],
            timestamp=datetime.now(),
        ),
    ]

    calculator = SplitCalculator()
    result = calculator.calculate_split(quotes, total_amount=Decimal("100.0"), price_usd=2500.0)

    if result:
        print("=" * 60)
        print("SPLIT ORDER ANALYSIS")
        print("=" * 60)

        print(f"\nTotal Input: {result.total_input} ETH")
        print(f"Total Output: {result.total_output:.2f} USDC")
        print(f"Single Venue Output: {result.single_venue_output:.2f} USDC")

        print("\n" + "-" * 60)
        print("ALLOCATIONS")
        print("-" * 60)

        for alloc in result.allocations:
            print(f"\n{alloc.source}: {alloc.percentage:.1f}%")
            print(f"  Amount: {alloc.input_amount} ETH")
            print(f"  Expected: {alloc.expected_output:.2f} USDC")
            print(f"  Impact: {alloc.price_impact:.2f}%")
            print(f"  Gas: ${alloc.gas_cost_usd:.2f}")

        print("\n" + "-" * 60)
        print("SUMMARY")
        print("-" * 60)
        print(f"Improvement: +{result.improvement_amount:.2f} USDC ({result.improvement_pct:.2f}%)")
        print(f"Total Gas: ${result.total_gas_cost:.2f}")
        print(f"Net Benefit: ${float(result.net_benefit):.2f}")
        print(f"\n→ {result.recommendation}")
        print(f"Split Beneficial: {'Yes' if result.is_split_beneficial else 'No'}")


if __name__ == "__main__":
    demo()
