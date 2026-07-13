#!/usr/bin/env python3
"""
Arbitrage profit calculator.

Calculates exact profit after all costs including:
- Trading fees (maker/taker)
- Withdrawal fees
- Gas costs (for DEX)
- Slippage estimates
"""

from dataclasses import dataclass
from decimal import Decimal

from price_fetcher import ExchangeType


@dataclass
class ProfitBreakdown:
    """Detailed profit breakdown for an arbitrage trade."""

    # Trade details
    pair: str
    buy_exchange: str
    sell_exchange: str
    trade_amount: Decimal
    buy_price: Decimal
    sell_price: Decimal

    # Gross profit
    gross_profit: Decimal
    gross_profit_pct: float

    # Costs
    buy_fee: Decimal
    sell_fee: Decimal
    withdrawal_fee: Decimal
    gas_cost_usd: Decimal
    slippage_cost: Decimal
    total_costs: Decimal

    # Net profit
    net_profit: Decimal
    net_profit_pct: float
    net_profit_usd: Decimal

    # Analysis
    breakeven_spread_pct: float
    profit_per_dollar: Decimal
    is_profitable: bool


@dataclass
class SlippageEstimate:
    """Slippage estimate based on trade size and liquidity."""

    base_slippage_pct: float
    size_factor: float
    liquidity_factor: float
    total_slippage_pct: float
    slippage_cost: Decimal


class ProfitCalculator:
    """
    Calculates detailed profit for arbitrage opportunities.

    Accounts for all costs and provides breakeven analysis.
    """

    # Fee structures by exchange
    EXCHANGE_FEES = {
        "binance": {"maker": 0.0010, "taker": 0.0010, "withdrawal": 0.0005},
        "coinbase": {"maker": 0.0040, "taker": 0.0060, "withdrawal": 0.0000},
        "kraken": {"maker": 0.0016, "taker": 0.0026, "withdrawal": 0.0010},
        "kucoin": {"maker": 0.0010, "taker": 0.0010, "withdrawal": 0.0003},
        "okx": {"maker": 0.0008, "taker": 0.0010, "withdrawal": 0.0004},
        "uniswap": {"maker": 0.0030, "taker": 0.0030, "withdrawal": 0.0000},
        "sushiswap": {"maker": 0.0030, "taker": 0.0030, "withdrawal": 0.0000},
        "curve": {"maker": 0.0004, "taker": 0.0004, "withdrawal": 0.0000},
        "balancer": {"maker": 0.0010, "taker": 0.0010, "withdrawal": 0.0000},
    }

    # Gas costs by operation
    GAS_COSTS = {
        "uniswap_swap": 150000,
        "sushiswap_swap": 150000,
        "curve_swap": 200000,
        "balancer_swap": 180000,
        "erc20_transfer": 65000,
    }

    def __init__(
        self,
        gas_price_gwei: float = 30.0,
        eth_price_usd: float = 2500.0,
        default_slippage_pct: float = 0.1,
    ):
        """
        Initialize calculator.

        Args:
            gas_price_gwei: Current gas price in gwei
            eth_price_usd: Current ETH price
            default_slippage_pct: Default slippage assumption
        """
        self.gas_price_gwei = gas_price_gwei
        self.eth_price_usd = eth_price_usd
        self.default_slippage_pct = default_slippage_pct

    def calculate(
        self,
        pair: str,
        buy_exchange: str,
        sell_exchange: str,
        buy_price: Decimal,
        sell_price: Decimal,
        amount: Decimal,
        include_withdrawal: bool = True,
        buy_exchange_type: ExchangeType = ExchangeType.CEX,
        sell_exchange_type: ExchangeType = ExchangeType.CEX,
    ) -> ProfitBreakdown:
        """
        Calculate detailed profit breakdown.

        Args:
            pair: Trading pair (e.g., "ETH/USDC")
            buy_exchange: Exchange to buy on
            sell_exchange: Exchange to sell on
            buy_price: Price to buy at
            sell_price: Price to sell at
            amount: Amount to trade (in base currency)
            include_withdrawal: Include withdrawal fee
            buy_exchange_type: CEX or DEX
            sell_exchange_type: CEX or DEX

        Returns:
            ProfitBreakdown with all details
        """
        # Get fee rates
        buy_fees = self._get_fees(buy_exchange)
        sell_fees = self._get_fees(sell_exchange)

        # Calculate gross profit
        buy_cost = amount * buy_price
        sell_revenue = amount * sell_price
        gross_profit = sell_revenue - buy_cost
        gross_profit_pct = float(gross_profit / buy_cost * 100)

        # Calculate trading fees
        buy_fee = buy_cost * Decimal(str(buy_fees["taker"]))
        sell_fee = sell_revenue * Decimal(str(sell_fees["taker"]))

        # Withdrawal fee (if moving between exchanges)
        withdrawal_fee = Decimal("0")
        if include_withdrawal:
            withdrawal_fee = amount * Decimal(str(buy_fees["withdrawal"]))

        # Gas costs (for DEX)
        gas_cost_usd = Decimal("0")
        if buy_exchange_type == ExchangeType.DEX:
            gas_units = self.GAS_COSTS.get(f"{buy_exchange.lower()}_swap", 150000)
            gas_cost_usd += Decimal(str(gas_units * self.gas_price_gwei * 1e-9 * self.eth_price_usd))
        if sell_exchange_type == ExchangeType.DEX:
            gas_units = self.GAS_COSTS.get(f"{sell_exchange.lower()}_swap", 150000)
            gas_cost_usd += Decimal(str(gas_units * self.gas_price_gwei * 1e-9 * self.eth_price_usd))

        # Slippage estimate
        slippage = self.estimate_slippage(amount, buy_price)
        slippage_cost = slippage.slippage_cost

        # Total costs
        total_costs = buy_fee + sell_fee + withdrawal_fee + slippage_cost
        # Add gas cost (convert to base currency)
        if gas_cost_usd > 0:
            total_costs += gas_cost_usd / buy_price

        # Net profit
        net_profit = gross_profit - total_costs
        net_profit_pct = float(net_profit / buy_cost * 100) if buy_cost > 0 else 0
        net_profit_usd = net_profit * buy_price  # Convert to USD

        # Breakeven analysis
        total_fee_pct = float((buy_fee + sell_fee) / buy_cost * 100) if buy_cost > 0 else 0
        breakeven_spread_pct = total_fee_pct + float(slippage.total_slippage_pct)

        # Profit per dollar invested
        profit_per_dollar = net_profit_usd / buy_cost if buy_cost > 0 else Decimal("0")

        return ProfitBreakdown(
            pair=pair,
            buy_exchange=buy_exchange,
            sell_exchange=sell_exchange,
            trade_amount=amount,
            buy_price=buy_price,
            sell_price=sell_price,
            gross_profit=gross_profit,
            gross_profit_pct=gross_profit_pct,
            buy_fee=buy_fee,
            sell_fee=sell_fee,
            withdrawal_fee=withdrawal_fee,
            gas_cost_usd=gas_cost_usd,
            slippage_cost=slippage_cost,
            total_costs=total_costs,
            net_profit=net_profit,
            net_profit_pct=net_profit_pct,
            net_profit_usd=net_profit_usd,
            breakeven_spread_pct=breakeven_spread_pct,
            profit_per_dollar=profit_per_dollar,
            is_profitable=net_profit > 0,
        )

    def _get_fees(self, exchange: str) -> dict:
        """Get fee structure for an exchange."""
        exchange_lower = exchange.lower().replace(" ", "").replace("v3", "")
        return self.EXCHANGE_FEES.get(exchange_lower, {"maker": 0.001, "taker": 0.001, "withdrawal": 0.0005})

    def estimate_slippage(
        self,
        amount: Decimal,
        price: Decimal,
        liquidity_usd: Decimal = Decimal("1000000"),
    ) -> SlippageEstimate:
        """
        Estimate slippage based on trade size.

        Simplified model:
        - Base slippage for small trades
        - Size factor increases with trade size
        - Liquidity factor based on pool depth
        """
        trade_value = amount * price

        # Base slippage
        base_slippage = self.default_slippage_pct

        # Size factor (larger trades = more slippage)
        size_pct = float(trade_value / liquidity_usd * 100)
        if size_pct < 0.1:
            size_factor = 1.0
        elif size_pct < 1.0:
            size_factor = 1.5
        elif size_pct < 5.0:
            size_factor = 2.5
        else:
            size_factor = 5.0

        # Liquidity factor
        if liquidity_usd < Decimal("100000"):
            liquidity_factor = 2.0
        elif liquidity_usd < Decimal("1000000"):
            liquidity_factor = 1.5
        else:
            liquidity_factor = 1.0

        # Total slippage
        total_slippage_pct = base_slippage * size_factor * liquidity_factor
        slippage_cost = trade_value * Decimal(str(total_slippage_pct / 100))

        return SlippageEstimate(
            base_slippage_pct=base_slippage,
            size_factor=size_factor,
            liquidity_factor=liquidity_factor,
            total_slippage_pct=total_slippage_pct,
            slippage_cost=slippage_cost,
        )

    def calculate_minimum_amount(
        self,
        buy_exchange: str,
        sell_exchange: str,
        spread_pct: float,
        target_profit_usd: Decimal = Decimal("10"),
    ) -> Decimal:
        """
        Calculate minimum trade amount to achieve target profit.

        Args:
            buy_exchange: Exchange to buy on
            sell_exchange: Exchange to sell on
            spread_pct: Current spread percentage
            target_profit_usd: Target profit in USD

        Returns:
            Minimum trade amount in USD
        """
        buy_fees = self._get_fees(buy_exchange)
        sell_fees = self._get_fees(sell_exchange)

        # Total fee percentage
        total_fee_pct = (
            buy_fees["taker"] + sell_fees["taker"] + buy_fees["withdrawal"] + self.default_slippage_pct / 100
        )

        # Net spread after fees
        net_spread_pct = spread_pct / 100 - total_fee_pct

        if net_spread_pct <= 0:
            return Decimal("-1")  # Not profitable at any size

        # Amount needed for target profit
        # profit = amount * net_spread_pct
        # amount = profit / net_spread_pct
        return target_profit_usd / Decimal(str(net_spread_pct))


def demo():
    """Demonstrate profit calculator."""
    calc = ProfitCalculator(gas_price_gwei=30.0, eth_price_usd=2500.0)

    print("=" * 70)
    print("ARBITRAGE PROFIT CALCULATOR")
    print("=" * 70)

    # Calculate profit for ETH/USDC arbitrage
    breakdown = calc.calculate(
        pair="ETH/USDC",
        buy_exchange="binance",
        sell_exchange="coinbase",
        buy_price=Decimal("2541.50"),
        sell_price=Decimal("2543.80"),
        amount=Decimal("10"),  # 10 ETH
        buy_exchange_type=ExchangeType.CEX,
        sell_exchange_type=ExchangeType.CEX,
    )

    print(f"\nTrade: {breakdown.trade_amount} ETH/USDC")
    print(f"Buy on {breakdown.buy_exchange} at ${breakdown.buy_price:,.2f}")
    print(f"Sell on {breakdown.sell_exchange} at ${breakdown.sell_price:,.2f}")

    print(f"\n{'─' * 50}")
    print("PROFIT BREAKDOWN")
    print(f"{'─' * 50}")

    print(f"\nGross Profit: ${breakdown.gross_profit:,.2f} ({breakdown.gross_profit_pct:+.3f}%)")

    print("\nCosts:")
    print(f"  Buy fee ({breakdown.buy_exchange}):  ${breakdown.buy_fee:,.2f}")
    print(f"  Sell fee ({breakdown.sell_exchange}): ${breakdown.sell_fee:,.2f}")
    print(f"  Withdrawal fee:     ${breakdown.withdrawal_fee:,.2f}")
    print(f"  Gas cost:           ${breakdown.gas_cost_usd:,.2f}")
    print(f"  Est. slippage:      ${breakdown.slippage_cost:,.2f}")
    print(f"  {'─' * 30}")
    print(f"  Total costs:        ${breakdown.total_costs:,.2f}")

    print(f"\nNet Profit: ${breakdown.net_profit:,.2f} ({breakdown.net_profit_pct:+.3f}%)")
    print(f"Net Profit (USD): ${breakdown.net_profit_usd:,.2f}")

    print(f"\nBreakeven spread: {breakdown.breakeven_spread_pct:.3f}%")
    print(f"Profit per $1000: ${float(breakdown.profit_per_dollar) * 1000:.2f}")

    if breakdown.is_profitable:
        print("\n✓ PROFITABLE")
    else:
        print("\n✗ NOT PROFITABLE")

    # Calculate minimum amount
    print(f"\n{'─' * 50}")
    print("MINIMUM TRADE ANALYSIS")
    print(f"{'─' * 50}")

    min_amount = calc.calculate_minimum_amount(
        buy_exchange="binance",
        sell_exchange="coinbase",
        spread_pct=0.09,  # 0.09% spread
        target_profit_usd=Decimal("100"),
    )

    if min_amount > 0:
        print("\nTo make $100 profit with 0.09% spread:")
        print(f"Minimum trade: ${min_amount:,.2f}")
    else:
        print("\n0.09% spread is not profitable after fees")


if __name__ == "__main__":
    demo()
