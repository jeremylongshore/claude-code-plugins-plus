#!/usr/bin/env python3
"""
Metrics Calculator

Calculates staking metrics including net yield, gas costs, and projections.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 2.0.0
License: MIT
"""

import math
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class StakingMetrics:
    """Calculated metrics for a staking option."""

    # Yield metrics
    gross_apy: float  # Advertised APY
    protocol_fee_rate: float  # Protocol's cut (decimal)
    net_apy: float  # After protocol fees
    effective_apy: float  # After gas costs (if position provided)

    # Cost metrics
    gas_cost_usd: float  # Estimated staking gas
    gas_as_pct: float  # Gas as % of position

    # Risk metrics
    risk_score: int  # 1-10 (10 = safest)

    # Position metrics (if amount provided)
    position_usd: float  # Position value in USD
    tvl_usd: float  # Total value locked

    # Projections
    projected_1m: float
    projected_3m: float
    projected_6m: float
    projected_1y: float

    # Metadata
    unbonding: str  # Lock-up period
    staking_type: str  # native or liquid


class MetricsCalculator:
    """Calculates comprehensive metrics for staking options."""

    # Typical gas costs in gwei for different operations
    GAS_ESTIMATES = {
        "stake_liquid": 100_000,  # Liquid staking deposit
        "unstake_liquid": 150_000,  # Liquid staking withdrawal
        "stake_native": 200_000,  # Native staking (varies)
        "claim_rewards": 50_000,  # Claim staking rewards
    }

    # Protocol-specific fee rates
    PROTOCOL_FEES = {
        "lido": 0.10,
        "rocket-pool": 0.14,
        "frax-ether": 0.10,
        "coinbase-wrapped-staked-eth": 0.25,
        "marinade-finance": 0.06,
        "benqi-staked-avax": 0.10,
        "ankr": 0.10,
        "stakewise": 0.10,
        "swell": 0.10,
        "stader": 0.10,
    }

    def __init__(self, gas_price_gwei: float = 30, eth_price_usd: float = 2000, verbose: bool = False):
        """Initialize calculator.

        Args:
            gas_price_gwei: Current gas price in gwei
            eth_price_usd: ETH price in USD
            verbose: Enable verbose output
        """
        self.gas_price_gwei = gas_price_gwei
        self.eth_price_usd = eth_price_usd
        self.verbose = verbose

    def calculate_metrics(
        self, pool: Dict[str, Any], position_usd: Optional[float] = None, risk_score: Optional[int] = None
    ) -> StakingMetrics:
        """Calculate comprehensive metrics for a staking option.

        Args:
            pool: Pool data from fetcher
            position_usd: Optional position size for gas-adjusted yield
            risk_score: Pre-calculated risk score (if available)

        Returns:
            StakingMetrics with all calculated values
        """
        # Extract base data
        project = pool.get("project", "").lower()
        gross_apy = pool.get("apy", 0) or pool.get("apyBase", 0) or 0
        tvl_usd = pool.get("tvlUsd", 0) or 0
        staking_type = pool.get("staking_type", "liquid")
        unbonding = pool.get("unbonding", "instant" if staking_type == "liquid" else "varies")

        # Get protocol fee rate
        fee_rate = pool.get("protocol_fee", self.PROTOCOL_FEES.get(project, 0.10))
        if staking_type == "native":
            fee_rate = 0  # Native staking has no protocol fee

        # Calculate net APY after protocol fees
        net_apy = gross_apy * (1 - fee_rate)

        # Calculate gas costs
        if staking_type == "liquid":
            gas_used = self.GAS_ESTIMATES["stake_liquid"]
        else:
            gas_used = self.GAS_ESTIMATES["stake_native"]

        gas_cost_eth = (gas_used * self.gas_price_gwei) / 1e9
        gas_cost_usd = gas_cost_eth * self.eth_price_usd

        # Calculate effective APY if position provided
        if position_usd and position_usd > 0:
            # Amortize gas over 1 year
            gas_drag_pct = (gas_cost_usd / position_usd) * 100
            effective_apy = max(0, net_apy - gas_drag_pct)
            gas_as_pct = gas_drag_pct
        else:
            effective_apy = net_apy
            gas_as_pct = 0
            position_usd = 0

        # Calculate projections
        if position_usd > 0:
            projected_1m = position_usd * (1 + net_apy / 100 / 12)
            projected_3m = position_usd * (1 + net_apy / 100 / 4)
            projected_6m = position_usd * (1 + net_apy / 100 / 2)
            projected_1y = position_usd * (1 + net_apy / 100)
        else:
            # Use $10,000 as reference
            ref = 10000
            projected_1m = ref * (1 + net_apy / 100 / 12)
            projected_3m = ref * (1 + net_apy / 100 / 4)
            projected_6m = ref * (1 + net_apy / 100 / 2)
            projected_1y = ref * (1 + net_apy / 100)

        return StakingMetrics(
            gross_apy=round(gross_apy, 2),
            protocol_fee_rate=fee_rate,
            net_apy=round(net_apy, 2),
            effective_apy=round(effective_apy, 2),
            gas_cost_usd=round(gas_cost_usd, 2),
            gas_as_pct=round(gas_as_pct, 4),
            risk_score=risk_score or 5,
            position_usd=position_usd,
            tvl_usd=tvl_usd,
            projected_1m=round(projected_1m, 2),
            projected_3m=round(projected_3m, 2),
            projected_6m=round(projected_6m, 2),
            projected_1y=round(projected_1y, 2),
            unbonding=unbonding,
            staking_type=staking_type,
        )

    def apr_to_apy(self, apr: float, compounds_per_year: int = 365) -> float:
        """Convert APR to APY with compounding.

        Args:
            apr: Annual percentage rate
            compounds_per_year: Number of compounding periods

        Returns:
            APY with compounding
        """
        apr_decimal = apr / 100
        apy = (1 + apr_decimal / compounds_per_year) ** compounds_per_year - 1
        return apy * 100

    def apy_to_apr(self, apy: float, compounds_per_year: int = 365) -> float:
        """Convert APY to APR.

        Args:
            apy: Annual percentage yield
            compounds_per_year: Number of compounding periods

        Returns:
            APR without compounding
        """
        apy_decimal = apy / 100
        apr = compounds_per_year * ((1 + apy_decimal) ** (1 / compounds_per_year) - 1)
        return apr * 100

    def calculate_position_metrics(self, position_usd: float, net_apy: float, time_days: int = 365) -> Dict[str, float]:
        """Calculate metrics for a specific position and time horizon.

        Args:
            position_usd: Position value in USD
            net_apy: Net APY after fees
            time_days: Time horizon in days

        Returns:
            Dictionary with position metrics
        """
        daily_rate = net_apy / 100 / 365

        # Simple interest
        simple_return = position_usd * (net_apy / 100) * (time_days / 365)

        # Compound interest (daily)
        compound_value = position_usd * ((1 + daily_rate) ** time_days)
        compound_return = compound_value - position_usd

        return {
            "initial_value": position_usd,
            "time_days": time_days,
            "simple_return": round(simple_return, 2),
            "compound_return": round(compound_return, 2),
            "final_value_simple": round(position_usd + simple_return, 2),
            "final_value_compound": round(compound_value, 2),
            "daily_earnings": round(position_usd * daily_rate, 2),
            "monthly_earnings": round(position_usd * (net_apy / 100) / 12, 2),
        }

    def calculate_risk_adjusted_return(self, net_apy: float, risk_score: int) -> float:
        """Calculate risk-adjusted return for ranking.

        Args:
            net_apy: Net APY after fees
            risk_score: Risk score (1-10, 10 = safest)

        Returns:
            Risk-adjusted return (higher is better)
        """
        # Simple formula: APY * (risk_score / 10)
        return net_apy * (risk_score / 10)

    def calculate_breakeven_days(self, gas_cost_usd: float, position_usd: float, net_apy: float) -> int:
        """Calculate days to break even on gas costs.

        Args:
            gas_cost_usd: Gas cost in USD
            position_usd: Position value in USD
            net_apy: Net APY after fees

        Returns:
            Days to break even
        """
        if position_usd <= 0 or net_apy <= 0:
            return 9999

        daily_earnings = position_usd * (net_apy / 100) / 365
        if daily_earnings <= 0:
            return 9999

        return math.ceil(gas_cost_usd / daily_earnings)


def main():
    """CLI entry point for testing."""
    calc = MetricsCalculator(gas_price_gwei=30, eth_price_usd=2000, verbose=True)

    # Test pool data
    test_pool = {
        "project": "lido",
        "symbol": "stETH",
        "apy": 4.0,
        "tvlUsd": 15_000_000_000,
        "staking_type": "liquid",
        "protocol_fee": 0.10,
    }

    print("\n" + "=" * 60)
    print("Testing Metrics Calculator")
    print("=" * 60)

    # Calculate without position
    metrics = calc.calculate_metrics(test_pool)
    print("\nLido (stETH) - No Position:")
    print(f"  Gross APY: {metrics.gross_apy}%")
    print(f"  Protocol Fee: {metrics.protocol_fee_rate * 100}%")
    print(f"  Net APY: {metrics.net_apy}%")
    print(f"  Gas Cost: ${metrics.gas_cost_usd}")

    # Calculate with position
    metrics = calc.calculate_metrics(test_pool, position_usd=10000, risk_score=9)
    print("\nLido (stETH) - $10,000 Position:")
    print(f"  Gross APY: {metrics.gross_apy}%")
    print(f"  Net APY: {metrics.net_apy}%")
    print(f"  Effective APY: {metrics.effective_apy}%")
    print(f"  Gas Drag: {metrics.gas_as_pct:.4f}%")
    print(f"  1 Year Projection: ${metrics.projected_1y:,.2f}")

    # Position metrics
    print("\nPosition Metrics ($10,000 @ 3.6% net APY):")
    pos_metrics = calc.calculate_position_metrics(10000, 3.6, 365)
    print(f"  Daily Earnings: ${pos_metrics['daily_earnings']}")
    print(f"  Monthly Earnings: ${pos_metrics['monthly_earnings']}")
    print(f"  1 Year Compound: ${pos_metrics['final_value_compound']:,.2f}")

    # Breakeven
    breakeven = calc.calculate_breakeven_days(6.0, 10000, 3.6)
    print(f"  Breakeven Days: {breakeven}")


if __name__ == "__main__":
    main()
