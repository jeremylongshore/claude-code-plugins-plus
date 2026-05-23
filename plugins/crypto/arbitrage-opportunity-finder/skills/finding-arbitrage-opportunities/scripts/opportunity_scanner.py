#!/usr/bin/env python3
"""
Arbitrage opportunity scanner.

Detects direct arbitrage opportunities (buy low, sell high)
across multiple exchanges with profit calculation.
"""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import List, Optional, Tuple

from price_fetcher import PriceFetcher, PriceQuote, ExchangeType


class OpportunityType(Enum):
    """Type of arbitrage opportunity."""

    DIRECT = "DIRECT"  # Buy on A, sell on B
    TRIANGULAR = "TRIANGULAR"  # A→B→C→A circular
    CROSS_CHAIN = "CROSS_CHAIN"  # Same asset across chains


class RiskLevel(Enum):
    """Risk level classification."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    EXTREME = "EXTREME"


@dataclass
class ArbitrageOpportunity:
    """Represents a single arbitrage opportunity."""

    opportunity_type: OpportunityType
    pair: str
    buy_exchange: str
    sell_exchange: str
    buy_price: Decimal
    sell_price: Decimal
    gross_spread_pct: float
    net_spread_pct: float
    gross_profit_per_unit: Decimal
    net_profit_per_unit: Decimal
    buy_fee_pct: float
    sell_fee_pct: float
    estimated_gas_usd: float  # For DEX
    risk_level: RiskLevel
    notes: List[str]
    buy_exchange_type: ExchangeType
    sell_exchange_type: ExchangeType

    @property
    def is_profitable(self) -> bool:
        """Check if opportunity is profitable after fees."""
        return self.net_profit_per_unit > 0

    def profit_for_amount(self, amount: Decimal) -> Decimal:
        """Calculate profit for a specific trade amount."""
        return amount * self.net_profit_per_unit / self.buy_price


@dataclass
class ScanResult:
    """Result of an arbitrage scan."""

    pair: str
    quotes: List[PriceQuote]
    opportunities: List[ArbitrageOpportunity]
    best_opportunity: Optional[ArbitrageOpportunity]
    timestamp: float


class OpportunityScanner:
    """
    Scans for arbitrage opportunities across exchanges.

    Features:
    - Direct spread detection (CEX-to-CEX, DEX-to-DEX, CEX-to-DEX)
    - Fee-aware profit calculation
    - Risk assessment
    """

    def __init__(
        self,
        fetcher: Optional[PriceFetcher] = None,
        min_profit_pct: float = 0.1,  # Minimum 0.1% profit
        gas_price_gwei: float = 30.0,
        eth_price_usd: float = 2500.0,
    ):
        """
        Initialize scanner.

        Args:
            fetcher: Price fetcher instance
            min_profit_pct: Minimum net profit percentage to report
            gas_price_gwei: Current gas price in gwei
            eth_price_usd: Current ETH price
        """
        self.fetcher = fetcher or PriceFetcher(use_mock=True)
        self.min_profit_pct = min_profit_pct
        self.gas_price_gwei = gas_price_gwei
        self.eth_price_usd = eth_price_usd

    def scan(
        self,
        base: str,
        quote: str,
        exchanges: Optional[List[str]] = None,
        exchange_type: Optional[ExchangeType] = None,
    ) -> ScanResult:
        """
        Scan for arbitrage opportunities on a pair.

        Args:
            base: Base token (e.g., ETH)
            quote: Quote token (e.g., USDC)
            exchanges: Specific exchanges to scan
            exchange_type: Filter by CEX or DEX

        Returns:
            ScanResult with all opportunities
        """
        import time

        # Fetch all prices
        quotes = self.fetcher.fetch_all_prices_sync(base, quote, exchanges, exchange_type)

        if len(quotes) < 2:
            return ScanResult(
                pair=f"{base}/{quote}",
                quotes=quotes,
                opportunities=[],
                best_opportunity=None,
                timestamp=time.time(),
            )

        # Find all opportunities
        opportunities = []

        for buy_quote in quotes:
            for sell_quote in quotes:
                if buy_quote.exchange == sell_quote.exchange:
                    continue

                opp = self._evaluate_opportunity(buy_quote, sell_quote)
                if opp and opp.net_spread_pct >= self.min_profit_pct:
                    opportunities.append(opp)

        # Sort by net profit
        opportunities.sort(key=lambda x: x.net_spread_pct, reverse=True)

        return ScanResult(
            pair=f"{base}/{quote}",
            quotes=quotes,
            opportunities=opportunities,
            best_opportunity=opportunities[0] if opportunities else None,
            timestamp=time.time(),
        )

    def _evaluate_opportunity(
        self,
        buy_quote: PriceQuote,
        sell_quote: PriceQuote,
    ) -> Optional[ArbitrageOpportunity]:
        """
        Evaluate a potential arbitrage opportunity.

        Args:
            buy_quote: Quote from buy exchange (use ask price)
            sell_quote: Quote from sell exchange (use bid price)

        Returns:
            ArbitrageOpportunity or None if not profitable
        """
        # Check basic profitability (sell price > buy price)
        if sell_quote.bid <= buy_quote.ask:
            return None

        # Get exchange configs
        buy_config = self.fetcher.get_exchange_config(buy_quote.exchange.lower().replace(" ", "").replace("v3", ""))
        sell_config = self.fetcher.get_exchange_config(sell_quote.exchange.lower().replace(" ", "").replace("v3", ""))

        # Default fees if config not found
        buy_fee = buy_config.taker_fee if buy_config else Decimal("0.001")
        sell_fee = sell_config.taker_fee if sell_config else Decimal("0.001")

        # Calculate gross spread
        gross_profit = sell_quote.bid - buy_quote.ask
        gross_spread_pct = float(gross_profit / buy_quote.ask * 100)

        # Calculate fees
        buy_fee_amount = buy_quote.ask * buy_fee
        sell_fee_amount = sell_quote.bid * sell_fee
        total_fees = buy_fee_amount + sell_fee_amount

        # Calculate gas costs (for DEX)
        gas_cost_usd = 0.0
        if buy_quote.exchange_type == ExchangeType.DEX:
            gas_units = buy_config.gas_overhead if buy_config else 150000
            gas_cost_usd += gas_units * self.gas_price_gwei * 1e-9 * self.eth_price_usd
        if sell_quote.exchange_type == ExchangeType.DEX:
            gas_units = sell_config.gas_overhead if sell_config else 150000
            gas_cost_usd += gas_units * self.gas_price_gwei * 1e-9 * self.eth_price_usd

        # Calculate net profit
        net_profit = gross_profit - total_fees
        net_spread_pct = float(net_profit / buy_quote.ask * 100)

        # Assess risk
        risk_level = self._assess_risk(buy_quote, sell_quote, net_spread_pct)

        # Generate notes
        notes = []
        if not buy_quote.is_fresh or not sell_quote.is_fresh:
            notes.append("Warning: Price data may be stale")
        if buy_quote.exchange_type == ExchangeType.DEX:
            notes.append(f"Buy requires on-chain tx (~${gas_cost_usd:.2f} gas)")
        if sell_quote.exchange_type == ExchangeType.DEX:
            notes.append("Sell requires on-chain tx")
        if gross_spread_pct > 2.0:
            notes.append("Large spread may indicate low liquidity or stale data")

        return ArbitrageOpportunity(
            opportunity_type=OpportunityType.DIRECT,
            pair=buy_quote.pair,
            buy_exchange=buy_quote.exchange,
            sell_exchange=sell_quote.exchange,
            buy_price=buy_quote.ask,
            sell_price=sell_quote.bid,
            gross_spread_pct=gross_spread_pct,
            net_spread_pct=net_spread_pct,
            gross_profit_per_unit=gross_profit,
            net_profit_per_unit=net_profit,
            buy_fee_pct=float(buy_fee) * 100,
            sell_fee_pct=float(sell_fee) * 100,
            estimated_gas_usd=gas_cost_usd,
            risk_level=risk_level,
            notes=notes,
            buy_exchange_type=buy_quote.exchange_type,
            sell_exchange_type=sell_quote.exchange_type,
        )

    def _assess_risk(
        self,
        buy_quote: PriceQuote,
        sell_quote: PriceQuote,
        net_spread_pct: float,
    ) -> RiskLevel:
        """Assess risk level of an opportunity."""
        risk_score = 0

        # Staleness
        if buy_quote.staleness_seconds > 10:
            risk_score += 2
        if sell_quote.staleness_seconds > 10:
            risk_score += 2

        # Spread size (very large spreads are suspicious)
        if net_spread_pct > 5.0:
            risk_score += 3
        elif net_spread_pct > 2.0:
            risk_score += 1

        # DEX involvement (execution uncertainty)
        if buy_quote.exchange_type == ExchangeType.DEX:
            risk_score += 1
        if sell_quote.exchange_type == ExchangeType.DEX:
            risk_score += 1

        # Volume (low volume = slippage risk)
        min_volume = min(buy_quote.volume_24h, sell_quote.volume_24h)
        if min_volume < Decimal("1000"):
            risk_score += 2
        elif min_volume < Decimal("10000"):
            risk_score += 1

        # Map to risk level
        if risk_score <= 1:
            return RiskLevel.LOW
        elif risk_score <= 3:
            return RiskLevel.MEDIUM
        elif risk_score <= 5:
            return RiskLevel.HIGH
        else:
            return RiskLevel.EXTREME

    def scan_multiple_pairs(
        self,
        pairs: List[Tuple[str, str]],
        exchanges: Optional[List[str]] = None,
    ) -> List[ScanResult]:
        """Scan multiple pairs for opportunities."""
        results = []
        for base, quote in pairs:
            result = self.scan(base, quote, exchanges)
            results.append(result)
        return results


def demo():
    """Demonstrate opportunity scanner."""
    scanner = OpportunityScanner(min_profit_pct=0.0)  # Show all

    print("=" * 70)
    print("ARBITRAGE OPPORTUNITY SCANNER")
    print("=" * 70)

    # Scan ETH/USDC
    result = scanner.scan("ETH", "USDC")

    print(f"\nScanned {len(result.quotes)} exchanges for ETH/USDC")
    print(f"Found {len(result.opportunities)} opportunities\n")

    if result.opportunities:
        print(f"{'Buy On':<15} {'Sell On':<15} {'Gross':>8} {'Net':>8} {'Risk':<8}")
        print("-" * 70)

        for opp in result.opportunities[:10]:
            profit_color = "+" if opp.is_profitable else "-"
            print(
                f"{opp.buy_exchange:<15} "
                f"{opp.sell_exchange:<15} "
                f"{profit_color}{opp.gross_spread_pct:>6.3f}% "
                f"{profit_color}{opp.net_spread_pct:>6.3f}% "
                f"{opp.risk_level.value:<8}"
            )

        if result.best_opportunity:
            best = result.best_opportunity
            print("\nBest Opportunity:")
            print(f"  Buy on {best.buy_exchange} at ${best.buy_price:,.2f}")
            print(f"  Sell on {best.sell_exchange} at ${best.sell_price:,.2f}")
            print(f"  Gross spread: {best.gross_spread_pct:.3f}%")
            print(f"  Net spread: {best.net_spread_pct:.3f}%")
            print(f"  Buy fee: {best.buy_fee_pct:.2f}%")
            print(f"  Sell fee: {best.sell_fee_pct:.2f}%")
            if best.notes:
                print(f"  Notes: {'; '.join(best.notes)}")
    else:
        print("No profitable opportunities found (market is efficient)")


if __name__ == "__main__":
    demo()
