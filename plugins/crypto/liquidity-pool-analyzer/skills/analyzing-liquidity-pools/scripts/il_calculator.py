#!/usr/bin/env python3
"""
Impermanent Loss Calculator

Calculates impermanent loss for liquidity positions.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 2.0.0
License: MIT
"""

import math
from typing import Dict, Any, List


class ILCalculator:
    """Calculates impermanent loss for LP positions."""

    def __init__(self, verbose: bool = False):
        """Initialize calculator.

        Args:
            verbose: Enable verbose output
        """
        self.verbose = verbose

    def calculate_il(self, price_ratio: float) -> float:
        """Calculate impermanent loss for a price change.

        The formula: IL = 2 * sqrt(r) / (1 + r) - 1
        where r = new_price / original_price

        Args:
            price_ratio: Ratio of new price to original price

        Returns:
            IL as decimal (negative means loss)
        """
        if price_ratio <= 0:
            return 0.0

        il = (2 * math.sqrt(price_ratio) / (1 + price_ratio)) - 1

        if self.verbose:
            print(f"  Price ratio {price_ratio:.2f}x → IL {il * 100:.2f}%")

        return il

    def calculate_il_from_prices(self, entry_price: float, current_price: float) -> Dict[str, float]:
        """Calculate IL with detailed breakdown.

        Args:
            entry_price: Price at LP entry
            current_price: Current price

        Returns:
            Dictionary with IL details
        """
        price_ratio = current_price / entry_price
        price_change_pct = (price_ratio - 1) * 100
        il_decimal = self.calculate_il(price_ratio)
        il_pct = il_decimal * 100

        return {
            "entry_price": entry_price,
            "current_price": current_price,
            "price_ratio": round(price_ratio, 4),
            "price_change_pct": round(price_change_pct, 2),
            "il_decimal": round(il_decimal, 6),
            "il_pct": round(il_pct, 2),
        }

    def calculate_position_il(
        self, entry_price: float, current_price: float, position_value: float
    ) -> Dict[str, float]:
        """Calculate IL for a specific position size.

        Args:
            entry_price: Price at LP entry
            current_price: Current price
            position_value: Initial position value in USD

        Returns:
            Dictionary with position IL details
        """
        il_info = self.calculate_il_from_prices(entry_price, current_price)
        current_price / entry_price

        # Value if just held 50/50 split
        # Assuming entry was 50% token0 (USD) and 50% token1 (volatile)
        initial_token1_amount = (position_value / 2) / entry_price
        value_if_held = (position_value / 2) + (initial_token1_amount * current_price)

        # Value in LP (affected by IL)
        value_in_lp = value_if_held * (1 + il_info["il_decimal"])
        il_usd = value_in_lp - value_if_held

        return {
            **il_info,
            "position_value": position_value,
            "value_if_held": round(value_if_held, 2),
            "value_in_lp": round(value_in_lp, 2),
            "il_usd": round(il_usd, 2),
            "gain_vs_hold_pct": round((value_in_lp / value_if_held - 1) * 100, 2),
        }

    def calculate_breakeven(self, il_pct: float, fee_tier: float, tvl: float, daily_volume: float) -> Dict[str, float]:
        """Calculate days to break even from fees.

        Args:
            il_pct: Impermanent loss percentage (negative)
            fee_tier: Pool fee tier (e.g., 0.003 for 0.3%)
            tvl: Pool TVL in USD
            daily_volume: Daily trading volume in USD

        Returns:
            Dictionary with breakeven analysis
        """
        if tvl <= 0 or daily_volume <= 0 or fee_tier <= 0:
            return {
                "days_to_breakeven": float("inf"),
                "daily_fee_pct": 0,
                "monthly_fee_pct": 0,
            }

        # Daily fee percentage earned by LPs
        daily_fees_usd = daily_volume * fee_tier
        daily_fee_pct = (daily_fees_usd / tvl) * 100

        # Days to recover IL
        il_abs = abs(il_pct)
        if daily_fee_pct > 0:
            days_to_breakeven = il_abs / daily_fee_pct
        else:
            days_to_breakeven = float("inf")

        return {
            "il_pct": il_pct,
            "fee_tier_pct": fee_tier * 100,
            "daily_fee_pct": round(daily_fee_pct, 4),
            "monthly_fee_pct": round(daily_fee_pct * 30, 2),
            "annual_fee_pct": round(daily_fee_pct * 365, 2),
            "days_to_breakeven": round(days_to_breakeven, 1) if days_to_breakeven != float("inf") else None,
        }

    def generate_il_scenarios(self, price_changes: List[float] = None) -> List[Dict[str, float]]:
        """Generate IL for various price change scenarios.

        Args:
            price_changes: List of price change percentages

        Returns:
            List of IL scenarios
        """
        if price_changes is None:
            price_changes = [-75, -50, -25, -10, 10, 25, 50, 100, 200, 300, 400]

        scenarios = []
        for pct_change in price_changes:
            price_ratio = 1 + (pct_change / 100)
            if price_ratio > 0:
                il = self.calculate_il(price_ratio)
                scenarios.append(
                    {
                        "price_change_pct": pct_change,
                        "price_ratio": round(price_ratio, 2),
                        "il_pct": round(il * 100, 2),
                    }
                )

        return scenarios

    def compare_strategies(
        self, entry_price: float, current_price: float, position_value: float, fee_earned_pct: float
    ) -> Dict[str, Any]:
        """Compare LP strategy vs HODL.

        Args:
            entry_price: Price at LP entry
            current_price: Current price
            position_value: Initial position value
            fee_earned_pct: Total fees earned as percentage

        Returns:
            Strategy comparison
        """
        position_info = self.calculate_position_il(entry_price, current_price, position_value)

        # Value with fees added
        fees_earned = position_value * (fee_earned_pct / 100)
        lp_value_with_fees = position_info["value_in_lp"] + fees_earned

        # Net result
        net_gain_usd = lp_value_with_fees - position_info["value_if_held"]
        net_gain_pct = (net_gain_usd / position_info["value_if_held"]) * 100

        return {
            **position_info,
            "fees_earned_pct": fee_earned_pct,
            "fees_earned_usd": round(fees_earned, 2),
            "lp_value_with_fees": round(lp_value_with_fees, 2),
            "net_gain_usd": round(net_gain_usd, 2),
            "net_gain_pct": round(net_gain_pct, 2),
            "better_strategy": "LP" if net_gain_usd > 0 else "HODL",
        }


def main():
    """CLI entry point for testing."""
    calc = ILCalculator(verbose=True)

    print("Impermanent Loss Scenarios:")
    print("-" * 50)
    scenarios = calc.generate_il_scenarios()
    for s in scenarios:
        print(f"  {s['price_change_pct']:+4d}% price change → {s['il_pct']:+6.2f}% IL")

    print("\nPosition Analysis:")
    print("-" * 50)
    position = calc.calculate_position_il(entry_price=2000, current_price=3000, position_value=10000)
    print(f"  Entry: ${position['entry_price']}")
    print(f"  Current: ${position['current_price']}")
    print(f"  Price Change: {position['price_change_pct']:+.2f}%")
    print(f"  IL: {position['il_pct']:.2f}%")
    print(f"  Value if HODL: ${position['value_if_held']:,.2f}")
    print(f"  Value in LP: ${position['value_in_lp']:,.2f}")
    print(f"  IL Loss: ${position['il_usd']:,.2f}")

    print("\nBreakeven Analysis (0.3% fee tier):")
    print("-" * 50)
    breakeven = calc.calculate_breakeven(
        il_pct=position["il_pct"], fee_tier=0.003, tvl=500_000_000, daily_volume=100_000_000
    )
    print(f"  Daily Fee APR: {breakeven['daily_fee_pct']:.4f}%")
    print(f"  Annual Fee APR: {breakeven['annual_fee_pct']:.2f}%")
    if breakeven["days_to_breakeven"]:
        print(f"  Days to Breakeven: {breakeven['days_to_breakeven']:.0f}")


if __name__ == "__main__":
    main()
