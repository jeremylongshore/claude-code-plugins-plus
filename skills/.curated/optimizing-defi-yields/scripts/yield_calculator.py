#!/usr/bin/env python3
"""
Yield Calculator

Calculates and normalizes APY/APR across protocols.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 2.0.0
License: MIT
"""

import math
from typing import Dict, Any


class YieldCalculator:
    """Calculates and normalizes DeFi yields."""

    # Compounding periods for APR to APY conversion
    COMPOUNDING_PERIODS = {
        "continuous": None,  # Use e^r formula
        "daily": 365,
        "weekly": 52,
        "monthly": 12,
        "quarterly": 4,
        "annual": 1,
    }

    def __init__(self, verbose: bool = False):
        """Initialize calculator.

        Args:
            verbose: Enable verbose output
        """
        self.verbose = verbose

    def calculate(self, pool: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate and normalize yields for a pool.

        Args:
            pool: Pool data dictionary

        Returns:
            Pool with calculated yield fields added
        """
        # Extract raw values
        base_apy = pool.get("apyBase") or 0
        reward_apy = pool.get("apyReward") or 0
        total_apy = pool.get("apy") or 0

        # If total not provided, calculate it
        if total_apy == 0 and (base_apy > 0 or reward_apy > 0):
            total_apy = base_apy + reward_apy

        # Store normalized values
        pool["base_apy"] = round(base_apy, 4)
        pool["reward_apy"] = round(reward_apy, 4)
        pool["total_apy"] = round(total_apy, 4)

        # Calculate daily and monthly rates
        if total_apy > 0:
            pool["daily_rate"] = round(total_apy / 365, 6)
            pool["monthly_rate"] = round(total_apy / 12, 4)
        else:
            pool["daily_rate"] = 0
            pool["monthly_rate"] = 0

        # Estimate impermanent loss risk
        pool["il_risk"] = self._estimate_il_risk(pool)

        # Calculate effective APY (accounting for IL if LP)
        pool["effective_apy"] = self._calculate_effective_apy(pool)

        if self.verbose:
            print(f"  Calculated yields for {pool.get('project')}/{pool.get('symbol')}: {pool['total_apy']:.2f}% APY")

        return pool

    def apr_to_apy(self, apr: float, compounding: str = "daily") -> float:
        """Convert APR to APY.

        Args:
            apr: Annual Percentage Rate (as percentage, e.g., 10.0 for 10%)
            compounding: Compounding frequency

        Returns:
            APY as percentage
        """
        apr_decimal = apr / 100

        periods = self.COMPOUNDING_PERIODS.get(compounding)

        if periods is None:  # Continuous compounding
            apy = (math.exp(apr_decimal) - 1) * 100
        else:
            apy = ((1 + apr_decimal / periods) ** periods - 1) * 100

        return round(apy, 4)

    def apy_to_apr(self, apy: float, compounding: str = "daily") -> float:
        """Convert APY to APR.

        Args:
            apy: Annual Percentage Yield (as percentage)
            compounding: Compounding frequency

        Returns:
            APR as percentage
        """
        apy_decimal = apy / 100

        periods = self.COMPOUNDING_PERIODS.get(compounding)

        if periods is None:  # Continuous compounding
            apr = math.log(1 + apy_decimal) * 100
        else:
            apr = periods * ((1 + apy_decimal) ** (1 / periods) - 1) * 100

        return round(apr, 4)

    def calculate_earnings(self, principal: float, apy: float, days: int = 365) -> Dict[str, float]:
        """Calculate expected earnings over time.

        Args:
            principal: Initial investment in USD
            apy: Annual Percentage Yield
            days: Number of days to calculate

        Returns:
            Dictionary with earnings breakdown
        """
        apy_decimal = apy / 100
        daily_rate = apy_decimal / 365

        # Simple interest (for comparison)
        simple_earnings = principal * (apy_decimal * days / 365)

        # Compound interest (daily)
        compound_value = principal * ((1 + daily_rate) ** days)
        compound_earnings = compound_value - principal

        return {
            "principal": round(principal, 2),
            "days": days,
            "apy": apy,
            "simple_earnings": round(simple_earnings, 2),
            "compound_earnings": round(compound_earnings, 2),
            "final_value": round(compound_value, 2),
            "effective_rate": round((compound_earnings / principal) * 100, 4),
        }

    def _estimate_il_risk(self, pool: Dict[str, Any]) -> str:
        """Estimate impermanent loss risk level.

        Args:
            pool: Pool data

        Returns:
            Risk level: "none", "low", "medium", "high"
        """
        symbol = pool.get("symbol", "").upper()
        project = pool.get("project", "").lower()

        # Single-sided staking (no IL)
        single_sided_projects = ["lido", "rocket-pool", "frax-ether", "yearn"]
        if any(p in project for p in single_sided_projects):
            return "none"

        # Stablecoin pools (minimal IL)
        stablecoin_symbols = ["USDC", "USDT", "DAI", "FRAX", "LUSD", "BUSD", "3POOL", "CRVUSD"]
        if any(s in symbol for s in stablecoin_symbols):
            # Check if it's a stablecoin-only pool
            stable_count = sum(1 for s in stablecoin_symbols if s in symbol)
            if stable_count >= 1 and not any(v in symbol for v in ["ETH", "BTC", "WBTC"]):
                return "low"

        # Correlated pairs (ETH-stETH, BTC-WBTC)
        correlated_pairs = [
            ("ETH", "STETH"),
            ("ETH", "RETH"),
            ("ETH", "CBETH"),
            ("BTC", "WBTC"),
            ("BTC", "RENBTC"),
            ("BTC", "SBTC"),
        ]
        for pair in correlated_pairs:
            if pair[0] in symbol and pair[1] in symbol:
                return "low"

        # Volatile pairs
        volatile_assets = ["ETH", "BTC", "SOL", "AVAX", "MATIC", "ARB", "OP"]
        volatile_count = sum(1 for v in volatile_assets if v in symbol)

        if volatile_count >= 2:
            return "high"  # Two volatile assets
        elif volatile_count == 1:
            return "medium"  # One volatile + one stable
        else:
            return "medium"  # Default for unknown

    def _calculate_effective_apy(self, pool: Dict[str, Any]) -> float:
        """Calculate effective APY accounting for IL.

        Args:
            pool: Pool data with IL risk

        Returns:
            Effective APY after IL adjustment
        """
        total_apy = pool.get("total_apy", 0)
        il_risk = pool.get("il_risk", "medium")

        # IL discount factors (conservative estimates)
        il_discounts = {
            "none": 1.0,  # No discount
            "low": 0.98,  # 2% discount
            "medium": 0.90,  # 10% discount
            "high": 0.75,  # 25% discount
        }

        discount = il_discounts.get(il_risk, 0.90)
        effective = total_apy * discount

        return round(effective, 4)

    def calculate_il(self, price_ratio: float) -> float:
        """Calculate impermanent loss for a given price ratio.

        Args:
            price_ratio: Ratio of new price to original price (e.g., 2.0 for 2x)

        Returns:
            Impermanent loss as percentage (negative value)
        """
        if price_ratio <= 0:
            return 0

        # IL formula: 2 * sqrt(price_ratio) / (1 + price_ratio) - 1
        il = (2 * math.sqrt(price_ratio) / (1 + price_ratio)) - 1

        return round(il * 100, 4)

    def calculate_breakeven_apy(self, price_change_percent: float) -> float:
        """Calculate APY needed to break even given expected price change.

        Args:
            price_change_percent: Expected price change (e.g., 50 for 50% increase)

        Returns:
            Minimum APY needed to offset IL
        """
        price_ratio = 1 + (price_change_percent / 100)
        il_percent = abs(self.calculate_il(price_ratio))

        # Add 20% buffer for safety
        return round(il_percent * 1.2, 4)


def main():
    """CLI entry point for testing."""
    calc = YieldCalculator(verbose=True)

    # Test APR/APY conversion
    print("APR to APY Conversions:")
    for apr in [5, 10, 20, 50, 100]:
        apy = calc.apr_to_apy(apr)
        print(f"  {apr}% APR → {apy:.2f}% APY (daily compounding)")

    print("\nImpermanent Loss Examples:")
    for ratio in [1.5, 2.0, 3.0, 4.0]:
        il = calc.calculate_il(ratio)
        print(f"  {ratio}x price change → {il:.2f}% IL")

    print("\nEarnings Projection:")
    earnings = calc.calculate_earnings(10000, 12.5, 365)
    print("  $10,000 at 12.5% APY for 1 year:")
    print(f"    Simple: ${earnings['simple_earnings']:,.2f}")
    print(f"    Compound: ${earnings['compound_earnings']:,.2f}")
    print(f"    Final Value: ${earnings['final_value']:,.2f}")


if __name__ == "__main__":
    main()
