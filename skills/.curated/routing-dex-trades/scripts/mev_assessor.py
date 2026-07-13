#!/usr/bin/env python3
"""
MEV (Maximal Extractable Value) risk assessment for DEX trades.

Analyzes trades for sandwich attack vulnerability and provides
protection recommendations.
"""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from quote_fetcher import NormalizedQuote


class MEVRiskLevel(Enum):
    """MEV risk classification levels."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class MEVRiskFactor:
    """Individual risk factor in MEV assessment."""

    name: str
    description: str
    score: float  # 0-100, higher = more risk
    weight: float  # Factor weight in overall score


@dataclass
class MEVProtectionOption:
    """MEV protection recommendation."""

    name: str
    description: str
    effectiveness: float  # 0-100
    trade_off: str
    url: Optional[str] = None


@dataclass
class MEVAssessment:
    """Complete MEV risk assessment for a trade."""

    risk_level: MEVRiskLevel
    risk_score: float  # 0-100
    estimated_mev_exposure_usd: float
    risk_factors: List[MEVRiskFactor]
    protection_options: List[MEVProtectionOption]
    recommendation: str


class MEVAssessor:
    """
    Assesses MEV risk for DEX trades.

    Factors considered:
    - Trade size relative to pool liquidity
    - Token volatility
    - Route complexity
    - Mempool visibility
    - Historical MEV extraction on pair
    """

    # Risk factor weights
    FACTOR_WEIGHTS = {
        "trade_size": 0.35,
        "price_impact": 0.25,
        "route_complexity": 0.15,
        "token_volatility": 0.15,
        "liquidity_depth": 0.10,
    }

    # MEV protection options database
    PROTECTION_OPTIONS = [
        MEVProtectionOption(
            name="Flashbots Protect",
            description="Submit transaction to private mempool via Flashbots",
            effectiveness=95,
            trade_off="Slightly slower confirmation, requires ETH mainnet",
            url="https://docs.flashbots.net/flashbots-protect/overview",
        ),
        MEVProtectionOption(
            name="CoW Swap",
            description="Batch auction protocol with built-in MEV protection",
            effectiveness=90,
            trade_off="May have longer settlement time, limited token pairs",
            url="https://cow.fi/",
        ),
        MEVProtectionOption(
            name="MEV Blocker",
            description="RPC endpoint that routes to multiple builders",
            effectiveness=85,
            trade_off="Requires custom RPC setup",
            url="https://mevblocker.io/",
        ),
        MEVProtectionOption(
            name="Private Transaction",
            description="Send directly to block builders",
            effectiveness=80,
            trade_off="May pay premium for inclusion",
        ),
        MEVProtectionOption(
            name="Slippage Tightening",
            description="Set tight slippage tolerance to reject sandwich",
            effectiveness=50,
            trade_off="Trade may fail if market moves",
        ),
    ]

    def __init__(
        self,
        eth_price_usd: float = 2500.0,
        volatility_multiplier: float = 1.0,
    ):
        """
        Initialize MEV assessor.

        Args:
            eth_price_usd: Current ETH price for value calculations
            volatility_multiplier: Adjust for current market volatility
        """
        self.eth_price_usd = eth_price_usd
        self.volatility_multiplier = volatility_multiplier

    def assess_risk(
        self,
        quote: NormalizedQuote,
        trade_value_usd: float,
        is_volatile_token: bool = False,
    ) -> MEVAssessment:
        """
        Perform complete MEV risk assessment.

        Args:
            quote: The trade quote to assess
            trade_value_usd: USD value of the trade
            is_volatile_token: Whether token is known to be volatile

        Returns:
            Complete MEV assessment with recommendations
        """
        risk_factors = self._calculate_risk_factors(quote, trade_value_usd, is_volatile_token)

        # Calculate overall risk score
        total_weight = sum(f.weight for f in risk_factors)
        risk_score = sum(f.score * f.weight for f in risk_factors) / total_weight

        # Determine risk level
        risk_level = self._classify_risk(risk_score)

        # Estimate MEV exposure
        mev_exposure = self._estimate_mev_exposure(trade_value_usd, risk_score, quote.price_impact)

        # Get relevant protection options
        protection_options = self._get_protection_options(risk_level, trade_value_usd)

        # Generate recommendation
        recommendation = self._generate_recommendation(risk_level, mev_exposure, trade_value_usd)

        return MEVAssessment(
            risk_level=risk_level,
            risk_score=risk_score,
            estimated_mev_exposure_usd=mev_exposure,
            risk_factors=risk_factors,
            protection_options=protection_options,
            recommendation=recommendation,
        )

    def _calculate_risk_factors(
        self,
        quote: NormalizedQuote,
        trade_value_usd: float,
        is_volatile_token: bool,
    ) -> List[MEVRiskFactor]:
        """Calculate individual risk factors."""
        factors = []

        # Trade size factor
        size_score = self._score_trade_size(trade_value_usd)
        factors.append(
            MEVRiskFactor(
                name="Trade Size",
                description=f"${trade_value_usd:,.0f} trade attracts MEV searchers",
                score=size_score,
                weight=self.FACTOR_WEIGHTS["trade_size"],
            )
        )

        # Price impact factor
        impact_score = self._score_price_impact(quote.price_impact)
        factors.append(
            MEVRiskFactor(
                name="Price Impact",
                description=f"{quote.price_impact:.2f}% impact creates arbitrage opportunity",
                score=impact_score,
                weight=self.FACTOR_WEIGHTS["price_impact"],
            )
        )

        # Route complexity factor
        route_score = self._score_route_complexity(quote.protocols)
        factors.append(
            MEVRiskFactor(
                name="Route Complexity",
                description=f"{len(quote.protocols)} DEX(s) in route increases surface area",
                score=route_score,
                weight=self.FACTOR_WEIGHTS["route_complexity"],
            )
        )

        # Token volatility factor
        volatility_score = 80.0 if is_volatile_token else 30.0
        volatility_score *= self.volatility_multiplier
        factors.append(
            MEVRiskFactor(
                name="Token Volatility",
                description="Volatile tokens enable larger sandwich profits",
                score=min(100, volatility_score),
                weight=self.FACTOR_WEIGHTS["token_volatility"],
            )
        )

        # Liquidity depth factor (estimated from gas)
        liquidity_score = self._score_liquidity(quote.gas_estimate)
        factors.append(
            MEVRiskFactor(
                name="Liquidity Depth",
                description="Lower liquidity increases MEV opportunity",
                score=liquidity_score,
                weight=self.FACTOR_WEIGHTS["liquidity_depth"],
            )
        )

        return factors

    def _score_trade_size(self, trade_value_usd: float) -> float:
        """Score risk based on trade size."""
        if trade_value_usd < 1000:
            return 10.0  # Too small to attract MEV
        elif trade_value_usd < 5000:
            return 25.0
        elif trade_value_usd < 10000:
            return 40.0
        elif trade_value_usd < 50000:
            return 60.0
        elif trade_value_usd < 100000:
            return 80.0
        else:
            return 95.0  # Large trades are prime targets

    def _score_price_impact(self, price_impact: float) -> float:
        """Score risk based on price impact percentage."""
        if price_impact < 0.1:
            return 10.0
        elif price_impact < 0.5:
            return 30.0
        elif price_impact < 1.0:
            return 50.0
        elif price_impact < 2.0:
            return 70.0
        elif price_impact < 5.0:
            return 85.0
        else:
            return 95.0

    def _score_route_complexity(self, protocols: List[str]) -> float:
        """Score risk based on route complexity."""
        num_protocols = len(protocols)
        if num_protocols <= 1:
            return 20.0
        elif num_protocols == 2:
            return 40.0
        elif num_protocols == 3:
            return 60.0
        else:
            return 80.0

    def _score_liquidity(self, gas_estimate: int) -> float:
        """
        Estimate liquidity score from gas usage.

        Higher gas often indicates more complex routing,
        which may indicate thinner liquidity on direct paths.
        """
        if gas_estimate < 100000:
            return 20.0  # Simple swap, likely good liquidity
        elif gas_estimate < 150000:
            return 35.0
        elif gas_estimate < 200000:
            return 50.0
        elif gas_estimate < 300000:
            return 70.0
        else:
            return 85.0

    def _classify_risk(self, risk_score: float) -> MEVRiskLevel:
        """Classify overall risk level from score."""
        if risk_score < 25:
            return MEVRiskLevel.LOW
        elif risk_score < 50:
            return MEVRiskLevel.MEDIUM
        elif risk_score < 75:
            return MEVRiskLevel.HIGH
        else:
            return MEVRiskLevel.CRITICAL

    def _estimate_mev_exposure(self, trade_value_usd: float, risk_score: float, price_impact: float) -> float:
        """
        Estimate potential MEV extraction in USD.

        Conservative estimate based on typical sandwich profits.
        """
        # Base extraction rate scales with risk
        base_rate = risk_score / 100 * 0.02  # Up to 2% for max risk

        # Adjust for price impact (higher impact = more profit potential)
        impact_multiplier = 1 + (price_impact / 100)

        estimated_mev = trade_value_usd * base_rate * impact_multiplier

        return min(estimated_mev, trade_value_usd * 0.05)  # Cap at 5%

    def _get_protection_options(self, risk_level: MEVRiskLevel, trade_value_usd: float) -> List[MEVProtectionOption]:
        """Get relevant protection options based on risk level."""
        if risk_level == MEVRiskLevel.LOW:
            # Low risk: basic protection sufficient
            return [self.PROTECTION_OPTIONS[4]]  # Slippage tightening

        elif risk_level == MEVRiskLevel.MEDIUM:
            # Medium risk: consider private transactions
            return self.PROTECTION_OPTIONS[2:5]

        elif risk_level == MEVRiskLevel.HIGH:
            # High risk: recommend Flashbots or CoW
            return self.PROTECTION_OPTIONS[0:4]

        else:  # CRITICAL
            # Critical risk: all protection options
            return self.PROTECTION_OPTIONS

    def _generate_recommendation(self, risk_level: MEVRiskLevel, mev_exposure: float, trade_value_usd: float) -> str:
        """Generate human-readable recommendation."""
        if risk_level == MEVRiskLevel.LOW:
            return f"LOW MEV RISK: Safe to execute via public mempool. Estimated exposure: ${mev_exposure:.2f}"

        elif risk_level == MEVRiskLevel.MEDIUM:
            return (
                f"MEDIUM MEV RISK: Consider using MEV Blocker or tight slippage. "
                f"Estimated exposure: ${mev_exposure:.2f}"
            )

        elif risk_level == MEVRiskLevel.HIGH:
            return (
                f"HIGH MEV RISK: Strongly recommend Flashbots Protect or CoW Swap. "
                f"Estimated exposure: ${mev_exposure:.2f}"
            )

        else:
            return (
                f"CRITICAL MEV RISK: Use private transaction ONLY. "
                f"Consider splitting order or waiting for lower volatility. "
                f"Estimated exposure: ${mev_exposure:.2f}"
            )


def demo():
    """Demonstrate MEV assessment with mock data."""
    from datetime import datetime

    # Create mock quote for a moderate-sized trade
    quote = NormalizedQuote(
        source="1inch",
        input_token="ETH",
        output_token="USDC",
        input_amount=Decimal("20.0"),
        output_amount=Decimal("50432.18"),
        price=Decimal("2521.609"),
        price_impact=0.45,
        gas_estimate=165000,
        gas_price_gwei=35.0,
        gas_cost_usd=14.44,
        effective_rate=Decimal("2520.89"),
        route=["ETH", "USDC"],
        route_readable=["ETH", "USDC"],
        protocols=["Uniswap V3", "Curve"],
        timestamp=datetime.now(),
    )

    assessor = MEVAssessor(eth_price_usd=2500.0)
    assessment = assessor.assess_risk(quote, trade_value_usd=50000.0, is_volatile_token=False)

    print("=" * 60)
    print("MEV RISK ASSESSMENT")
    print("=" * 60)

    print(f"\nRisk Level: {assessment.risk_level.value}")
    print(f"Risk Score: {assessment.risk_score:.1f}/100")
    print(f"Estimated MEV Exposure: ${assessment.estimated_mev_exposure_usd:.2f}")

    print("\n" + "-" * 60)
    print("RISK FACTORS")
    print("-" * 60)

    for factor in assessment.risk_factors:
        print(f"\n{factor.name}: {factor.score:.0f}/100 (weight: {factor.weight:.0%})")
        print(f"  {factor.description}")

    print("\n" + "-" * 60)
    print("PROTECTION OPTIONS")
    print("-" * 60)

    for option in assessment.protection_options:
        print(f"\n{option.name} ({option.effectiveness:.0f}% effective)")
        print(f"  {option.description}")
        print(f"  Trade-off: {option.trade_off}")
        if option.url:
            print(f"  URL: {option.url}")

    print("\n" + "-" * 60)
    print("RECOMMENDATION")
    print("-" * 60)
    print(f"\n{assessment.recommendation}")


if __name__ == "__main__":
    demo()
