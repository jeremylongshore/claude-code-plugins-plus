#!/usr/bin/env python3
"""
Flash loan profitability calculator.

Calculates net profit after all costs including:
- Flash loan fees
- Gas costs
- DEX fees (implicit in swaps)
- Slippage
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import List

from strategy_engine import StrategyResult, TransactionStep


@dataclass
class ProfitBreakdown:
    """Detailed profit breakdown."""

    gross_revenue: Decimal
    flash_loan_fee: Decimal
    gas_cost_eth: Decimal
    gas_cost_usd: Decimal
    dex_fees: Decimal
    slippage_cost: Decimal
    total_costs: Decimal
    net_profit: Decimal
    net_profit_usd: Decimal
    roi_percent: float
    breakeven_gas_price: float  # Max gas price for profitability
    is_profitable: bool


@dataclass
class GasEstimate:
    """Gas estimation for a transaction."""

    gas_units: int
    gas_price_gwei: float
    cost_eth: Decimal
    cost_usd: Decimal


class ProfitCalculator:
    """
    Calculates detailed profitability for flash loan strategies.

    Accounts for all costs and provides breakeven analysis.
    """

    def __init__(
        self,
        eth_price_usd: float = 2500.0,
        gas_price_gwei: float = 30.0,
    ):
        """
        Initialize calculator.

        Args:
            eth_price_usd: Current ETH price
            gas_price_gwei: Current gas price
        """
        self.eth_price_usd = Decimal(str(eth_price_usd))
        self.gas_price_gwei = gas_price_gwei

    def calculate_breakdown(
        self,
        result: StrategyResult,
        slippage_pct: float = 0.5,
    ) -> ProfitBreakdown:
        """
        Calculate detailed profit breakdown from strategy result.

        Args:
            result: Strategy simulation result
            slippage_pct: Expected slippage percentage

        Returns:
            Detailed profit breakdown
        """
        # Calculate gross revenue (profit before any costs)
        gross_revenue = result.gross_profit + result.loan_fee + result.gas_cost_eth

        # Flash loan fee
        flash_loan_fee = result.loan_fee

        # Gas costs
        gas_cost_eth = result.gas_cost_eth
        gas_cost_usd = result.gas_cost_usd

        # DEX fees (usually included in price, but track separately)
        # Estimate ~0.3% per swap
        num_swaps = sum(1 for s in result.steps if s.action == "swap")
        dex_fee_rate = Decimal("0.003")  # 0.3%
        dex_fees = result.loan_amount * dex_fee_rate * num_swaps

        # Slippage cost
        slippage_rate = Decimal(str(slippage_pct / 100))
        slippage_cost = result.loan_amount * slippage_rate

        # Total costs
        total_costs = flash_loan_fee + gas_cost_eth + slippage_cost
        # Note: DEX fees already reflected in swap outputs

        # Net profit
        net_profit = result.net_profit
        net_profit_usd = result.net_profit_usd

        # ROI
        roi = result.roi_percent

        # Breakeven gas price
        # At what gas price does profit = 0?
        profit_before_gas = gross_revenue - flash_loan_fee - slippage_cost
        total_gas_units = sum(s.gas_estimate for s in result.steps)

        if total_gas_units > 0 and profit_before_gas > 0:
            # profit_before_gas = gas_units * gas_price * eth_price
            # gas_price = profit_before_gas / (gas_units * eth_price)
            breakeven_gas = float(profit_before_gas * Decimal("1e9") / (total_gas_units * self.eth_price_usd))
        else:
            breakeven_gas = 0.0

        return ProfitBreakdown(
            gross_revenue=gross_revenue,
            flash_loan_fee=flash_loan_fee,
            gas_cost_eth=gas_cost_eth,
            gas_cost_usd=gas_cost_usd,
            dex_fees=dex_fees,
            slippage_cost=slippage_cost,
            total_costs=total_costs,
            net_profit=net_profit,
            net_profit_usd=net_profit_usd,
            roi_percent=roi,
            breakeven_gas_price=breakeven_gas,
            is_profitable=net_profit > 0,
        )

    def estimate_gas(self, steps: List[TransactionStep]) -> GasEstimate:
        """
        Estimate total gas cost for transaction steps.

        Args:
            steps: List of transaction steps

        Returns:
            Gas estimate with cost
        """
        total_units = sum(s.gas_estimate for s in steps)

        cost_eth = Decimal(total_units * self.gas_price_gwei) / Decimal("1e9")
        cost_usd = cost_eth * self.eth_price_usd

        return GasEstimate(
            gas_units=total_units,
            gas_price_gwei=self.gas_price_gwei,
            cost_eth=cost_eth,
            cost_usd=cost_usd,
        )

    def calculate_minimum_profit(
        self,
        loan_amount: Decimal,
        loan_fee_rate: Decimal,
        gas_units: int,
        num_swaps: int = 2,
    ) -> Decimal:
        """
        Calculate minimum profit needed to break even.

        Useful for determining if an opportunity is worth pursuing.
        """
        # Flash loan fee
        loan_fee = loan_amount * loan_fee_rate

        # Gas cost
        gas_cost = Decimal(gas_units * self.gas_price_gwei) / Decimal("1e9")

        # Minimum slippage assumption (0.5%)
        slippage = loan_amount * Decimal("0.005")

        return loan_fee + gas_cost + slippage

    def compare_providers(
        self,
        loan_amount: Decimal,
        asset: str,
        gas_units: int,
        providers: dict,
    ) -> List[dict]:
        """
        Compare profitability across flash loan providers.

        Args:
            loan_amount: Amount to borrow
            asset: Asset to borrow
            gas_units: Base gas units (before provider overhead)
            providers: Dict of provider name -> fee rate

        Returns:
            List of provider comparisons sorted by net cost
        """
        results = []

        for name, fee_rate in providers.items():
            # Calculate fee
            fee = loan_amount * Decimal(str(fee_rate))

            # Estimate gas (with provider overhead)
            overhead = {
                "aave": 100000,
                "dydx": 150000,
                "balancer": 80000,
            }.get(name.lower(), 100000)

            total_gas = gas_units + overhead
            gas_cost = Decimal(total_gas * self.gas_price_gwei) / Decimal("1e9")

            total_cost = fee + gas_cost

            results.append(
                {
                    "provider": name,
                    "fee_rate": float(fee_rate) * 100,
                    "fee_amount": float(fee),
                    "gas_overhead": overhead,
                    "gas_cost_eth": float(gas_cost),
                    "total_cost_eth": float(total_cost),
                    "total_cost_usd": float(total_cost * self.eth_price_usd),
                }
            )

        # Sort by total cost
        results.sort(key=lambda x: x["total_cost_eth"])

        return results


def demo():
    """Demonstrate profit calculator."""
    from strategy_engine import StrategyFactory, StrategyType, ArbitrageParams

    # Run a simulation first
    factory = StrategyFactory()
    strategy = factory.create(StrategyType.SIMPLE_ARBITRAGE)

    params = ArbitrageParams(
        input_token="ETH",
        output_token="USDC",
        amount=Decimal("100"),
        dex_buy="sushiswap",
        dex_sell="uniswap",
        provider="aave",
    )

    result = strategy.simulate(params)

    # Calculate detailed breakdown
    calculator = ProfitCalculator(eth_price_usd=2500.0, gas_price_gwei=30.0)
    breakdown = calculator.calculate_breakdown(result)

    print("=" * 60)
    print("PROFIT BREAKDOWN")
    print("=" * 60)

    print(f"\nGross Revenue: {breakdown.gross_revenue:.6f} ETH")
    print("\nCosts:")
    print(f"  Flash Loan Fee: -{breakdown.flash_loan_fee:.6f} ETH")
    print(f"  Gas Cost: -{breakdown.gas_cost_eth:.6f} ETH (${breakdown.gas_cost_usd:.2f})")
    print(f"  Est. Slippage: -{breakdown.slippage_cost:.6f} ETH")
    print("  ────────────────────────────────")
    print(f"  Total Costs: -{breakdown.total_costs:.6f} ETH")

    print(f"\nNet Profit: {breakdown.net_profit:.6f} ETH (${breakdown.net_profit_usd:.2f})")
    print(f"ROI: {breakdown.roi_percent:.4f}%")
    print(f"Breakeven Gas: {breakdown.breakeven_gas_price:.1f} gwei")
    print(f"\nProfitable: {'YES ✓' if breakdown.is_profitable else 'NO ✗'}")

    # Compare providers
    print("\n" + "=" * 60)
    print("PROVIDER COMPARISON")
    print("=" * 60)

    providers = {
        "Aave V3": 0.0009,
        "dYdX": 0.0,
        "Balancer": 0.0001,
    }

    comparisons = calculator.compare_providers(
        loan_amount=Decimal("100"),
        asset="ETH",
        gas_units=300000,
        providers=providers,
    )

    print("\nFor 100 ETH flash loan:")
    print(f"{'Provider':<12} {'Fee %':<8} {'Fee ETH':<12} {'Gas ETH':<12} {'Total':<12}")
    print("-" * 56)

    for comp in comparisons:
        print(
            f"{comp['provider']:<12} "
            f"{comp['fee_rate']:.2f}%{'':<4} "
            f"{comp['fee_amount']:.4f}{'':<6} "
            f"{comp['gas_cost_eth']:.4f}{'':<6} "
            f"{comp['total_cost_eth']:.4f}"
        )


if __name__ == "__main__":
    demo()
