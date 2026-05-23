#!/usr/bin/env python3
"""
Basis and spread calculator.

Calculates futures basis and spreads with:
- Spot-futures basis tracking
- Annualized basis yield
- Term structure analysis
- Contango/backwardation detection
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List, Optional
from datetime import datetime

from exchange_client import ExchangeClient, BasisData, Exchange


@dataclass
class BasisAnalysis:
    """Comprehensive basis analysis."""

    symbol: str
    spot_price: Decimal
    basis_data: List[BasisData]
    avg_basis_pct: float
    avg_annualized: float
    market_structure: str  # "contango", "backwardation", "mixed"
    structure_strength: str  # "strong", "moderate", "weak"
    best_carry_expiry: Optional[str]
    best_carry_yield: float
    timestamp: datetime


@dataclass
class CarryOpportunity:
    """Cash-and-carry arbitrage opportunity."""

    symbol: str
    exchange: str
    expiry: str
    spot_price: Decimal
    futures_price: Decimal
    basis_pct: float
    days_to_expiry: int
    annualized_yield: float
    direction: str  # "long_basis" or "short_basis"
    strategy: str  # Trade description
    risk_notes: str


class BasisCalculator:
    """
    Calculates and analyzes futures basis.

    Features:
    - Multi-expiry analysis
    - Term structure visualization
    - Carry trade identification
    - Contango/backwardation detection
    """

    # Structure interpretation
    STRONG_BASIS = 5.0  # >5% annualized is strong
    MODERATE_BASIS = 2.0  # >2% is moderate

    def __init__(
        self,
        client: Optional[ExchangeClient] = None,
    ):
        """
        Initialize basis calculator.

        Args:
            client: Exchange client for data fetching
        """
        self.client = client or ExchangeClient(use_mock=True)

    def analyze(
        self,
        symbol: str,
        spot_price: Optional[Decimal] = None,
        exchanges: Optional[List[Exchange]] = None,
    ) -> BasisAnalysis:
        """
        Analyze basis for a symbol.

        Args:
            symbol: Trading symbol (e.g., "BTC")
            spot_price: Current spot price
            exchanges: Exchanges to include

        Returns:
            BasisAnalysis with all metrics
        """
        # Set default spot price if not provided
        if spot_price is None:
            if symbol == "BTC":
                spot_price = Decimal("67500")
            elif symbol == "ETH":
                spot_price = Decimal("2500")
            else:
                spot_price = Decimal("100")

        # Fetch basis data
        basis_list = self.client.get_all_basis(symbol, spot_price, exchanges)

        if not basis_list:
            raise ValueError(f"No basis data available for {symbol}")

        # Calculate averages
        avg_basis = sum(b.basis_pct for b in basis_list) / len(basis_list)
        avg_annual = sum(b.annualized_pct for b in basis_list) / len(basis_list)

        # Determine market structure
        structure, strength = self._analyze_structure(basis_list)

        # Find best carry opportunity
        best_carry = max(basis_list, key=lambda b: b.annualized_pct)

        return BasisAnalysis(
            symbol=symbol,
            spot_price=spot_price,
            basis_data=basis_list,
            avg_basis_pct=round(avg_basis, 3),
            avg_annualized=round(avg_annual, 2),
            market_structure=structure,
            structure_strength=strength,
            best_carry_expiry=best_carry.expiry,
            best_carry_yield=best_carry.annualized_pct,
            timestamp=datetime.now(),
        )

    def _analyze_structure(
        self,
        basis_list: List[BasisData],
    ) -> tuple:
        """
        Analyze term structure from basis data.

        Returns:
            (structure, strength) tuple
        """
        positive = sum(1 for b in basis_list if b.basis_pct > 0)
        negative = sum(1 for b in basis_list if b.basis_pct < 0)
        total = len(basis_list)

        # Determine structure
        if positive == total:
            structure = "contango"
        elif negative == total:
            structure = "backwardation"
        elif positive > negative:
            structure = "contango"  # Mostly contango
        elif negative > positive:
            structure = "backwardation"
        else:
            structure = "mixed"

        # Determine strength from magnitude
        avg_abs = sum(abs(b.annualized_pct) for b in basis_list) / total
        if avg_abs >= self.STRONG_BASIS:
            strength = "strong"
        elif avg_abs >= self.MODERATE_BASIS:
            strength = "moderate"
        else:
            strength = "weak"

        return structure, strength

    def find_carry_opportunities(
        self,
        symbols: List[str],
        min_yield: float = 5.0,
    ) -> List[CarryOpportunity]:
        """
        Find cash-and-carry arbitrage opportunities.

        Strategy:
        - Contango: Buy spot, sell futures, collect basis
        - Backwardation: Sell spot (if possible), buy futures

        Args:
            symbols: Symbols to scan
            min_yield: Minimum annualized yield (%)

        Returns:
            List of carry opportunities
        """
        opportunities = []

        for symbol in symbols:
            try:
                analysis = self.analyze(symbol)

                for basis in analysis.basis_data:
                    if abs(basis.annualized_pct) >= min_yield:
                        if basis.basis_pct > 0:
                            # Contango - long basis trade
                            direction = "long_basis"
                            strategy = (
                                f"Buy {symbol} spot at ${float(analysis.spot_price):,.0f}, "
                                f"sell {basis.expiry} futures at ${float(basis.futures_price):,.0f}"
                            )
                            risk_notes = "Funding costs may reduce yield; early liquidation risk"
                        else:
                            # Backwardation - short basis trade
                            direction = "short_basis"
                            strategy = (
                                f"Short {symbol} spot (borrow), "
                                f"buy {basis.expiry} futures at ${float(basis.futures_price):,.0f}"
                            )
                            risk_notes = "Borrowing costs apply; squeeze risk in tight markets"

                        opportunities.append(
                            CarryOpportunity(
                                symbol=symbol,
                                exchange=basis.exchange,
                                expiry=basis.expiry,
                                spot_price=analysis.spot_price,
                                futures_price=basis.futures_price,
                                basis_pct=basis.basis_pct,
                                days_to_expiry=basis.days_to_expiry,
                                annualized_yield=basis.annualized_pct,
                                direction=direction,
                                strategy=strategy,
                                risk_notes=risk_notes,
                            )
                        )
            except Exception:
                continue

        # Sort by yield descending
        opportunities.sort(key=lambda x: abs(x.annualized_yield), reverse=True)
        return opportunities

    def get_term_structure(
        self,
        symbol: str,
        spot_price: Optional[Decimal] = None,
    ) -> List[Dict]:
        """
        Get term structure data for visualization.

        Args:
            symbol: Trading symbol
            spot_price: Current spot price

        Returns:
            List of expiry data points
        """
        analysis = self.analyze(symbol, spot_price)

        # Sort by days to expiry
        sorted_basis = sorted(analysis.basis_data, key=lambda b: b.days_to_expiry)

        return [
            {
                "expiry": b.expiry,
                "days": b.days_to_expiry,
                "futures_price": float(b.futures_price),
                "basis_pct": b.basis_pct,
                "annualized_pct": b.annualized_pct,
                "exchange": b.exchange,
            }
            for b in sorted_basis
        ]

    def calculate_implied_rate(
        self,
        spot: Decimal,
        futures: Decimal,
        days: int,
    ) -> Dict:
        """
        Calculate implied interest rate from basis.

        Args:
            spot: Spot price
            futures: Futures price
            days: Days to expiry

        Returns:
            Dict with rate calculations
        """
        if days <= 0:
            return {"error": "Days must be positive"}

        basis = float(futures - spot)
        basis_pct = basis / float(spot) * 100
        annualized = basis_pct * 365 / days

        return {
            "spot": float(spot),
            "futures": float(futures),
            "days_to_expiry": days,
            "basis_usd": round(basis, 2),
            "basis_pct": round(basis_pct, 3),
            "annualized_rate": round(annualized, 2),
            "structure": "contango" if basis > 0 else "backwardation",
        }


def demo():
    """Demonstrate basis calculator."""
    calc = BasisCalculator()

    print("=" * 70)
    print("BASIS CALCULATOR")
    print("=" * 70)

    # Analyze BTC basis
    analysis = calc.analyze("BTC", Decimal("67500"))

    print(f"\n📈 {analysis.symbol} BASIS ANALYSIS")
    print(f"   Spot Price: ${analysis.spot_price:,}")
    print("-" * 60)

    print(f"\n{'Expiry':<12} {'Futures':>12} {'Basis':>10} {'Annual':>10} {'Days':>6}")
    print("-" * 60)

    for basis in sorted(analysis.basis_data, key=lambda b: b.days_to_expiry):
        print(
            f"{basis.expiry:<12} "
            f"${float(basis.futures_price):>10,.0f} "
            f"{basis.basis_pct:>+9.2f}% "
            f"{basis.annualized_pct:>+9.1f}% "
            f"{basis.days_to_expiry:>6}"
        )

    print("-" * 60)
    print(f"\nMarket Structure: {analysis.structure_strength.title()} {analysis.market_structure.title()}")
    print(f"Average Basis: {analysis.avg_basis_pct:+.2f}%")
    print(f"Average Annualized: {analysis.avg_annualized:+.1f}%")
    print(f"Best Carry: {analysis.best_carry_expiry} ({analysis.best_carry_yield:+.1f}% annualized)")

    # Term structure
    print("\n" + "-" * 60)
    print("TERM STRUCTURE")
    print("-" * 60)

    structure = calc.get_term_structure("BTC", Decimal("67500"))
    for point in structure:
        bar = "+" * min(int(abs(point["annualized_pct"]) / 2), 20)
        direction = "▲" if point["annualized_pct"] > 0 else "▼"
        print(f"{point['expiry']:<12} {direction} {bar} {point['annualized_pct']:+.1f}%")

    # Carry opportunities
    print("\n" + "=" * 70)
    print("CARRY TRADE SCANNER")
    print("=" * 70)

    opportunities = calc.find_carry_opportunities(["BTC", "ETH"], min_yield=5.0)
    if opportunities:
        print(f"\n{'Symbol':<6} {'Expiry':<12} {'Basis':>8} {'Annual':>10} {'Direction':<12}")
        print("-" * 60)
        for opp in opportunities[:5]:
            print(
                f"{opp.symbol:<6} "
                f"{opp.expiry:<12} "
                f"{opp.basis_pct:>+7.2f}% "
                f"{opp.annualized_yield:>+9.1f}% "
                f"{opp.direction:<12}"
            )

        print("\nTop Opportunity:")
        top = opportunities[0]
        print(f"   Strategy: {top.strategy}")
        print(f"   Risk: {top.risk_notes}")
    else:
        print("\nNo carry opportunities found above threshold")


if __name__ == "__main__":
    demo()
