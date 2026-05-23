#!/usr/bin/env python3
"""
Flash loan risk assessment engine.

Evaluates risks for flash loan strategies:
- MEV competition
- Execution risk
- Protocol risk
- Liquidity risk
"""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import List

from strategy_engine import StrategyResult, StrategyType


class RiskLevel(Enum):
    """Risk level classification."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class RiskFactor:
    """Individual risk factor assessment."""

    name: str
    level: RiskLevel
    score: float  # 0-100, higher = more risky
    description: str
    mitigation: str


@dataclass
class RiskAssessment:
    """Complete risk assessment for a strategy."""

    overall_level: RiskLevel
    overall_score: float
    viability: str  # "GO", "CAUTION", "NO-GO"
    factors: List[RiskFactor]
    recommendations: List[str]
    warnings: List[str]


class RiskAssessor:
    """
    Assesses risks for flash loan strategies.

    Factors evaluated:
    - MEV Competition: Bot activity on the pair/strategy
    - Execution Risk: Slippage, timing, gas volatility
    - Protocol Risk: Smart contract and oracle risks
    - Liquidity Risk: Pool depth and availability
    """

    # MEV risk by token pair (common pairs = more competition)
    MEV_COMPETITION = {
        ("ETH", "USDC"): 90,
        ("ETH", "USDT"): 85,
        ("WBTC", "ETH"): 80,
        ("ETH", "DAI"): 75,
        "default": 50,
    }

    # Protocol risk scores (higher = riskier)
    PROTOCOL_RISK = {
        "aave": 15,  # Well-audited, proven
        "compound": 20,
        "dydx": 25,
        "balancer": 30,
        "uniswap": 20,
        "sushiswap": 35,
        "curve": 25,
        "default": 50,
    }

    def __init__(self, eth_price_usd: float = 2500.0):
        """Initialize assessor."""
        self.eth_price_usd = eth_price_usd

    def assess(self, result: StrategyResult) -> RiskAssessment:
        """
        Perform complete risk assessment.

        Args:
            result: Strategy simulation result

        Returns:
            Complete risk assessment
        """
        factors = []
        recommendations = []
        warnings = []

        # 1. MEV Competition Risk
        mev_factor = self._assess_mev_risk(result)
        factors.append(mev_factor)

        # 2. Execution Risk
        exec_factor = self._assess_execution_risk(result)
        factors.append(exec_factor)

        # 3. Protocol Risk
        protocol_factor = self._assess_protocol_risk(result)
        factors.append(protocol_factor)

        # 4. Liquidity Risk
        liquidity_factor = self._assess_liquidity_risk(result)
        factors.append(liquidity_factor)

        # 5. Profitability Risk
        profit_factor = self._assess_profit_risk(result)
        factors.append(profit_factor)

        # Calculate overall score (weighted average)
        weights = {
            "MEV Competition": 0.30,
            "Execution Risk": 0.25,
            "Protocol Risk": 0.15,
            "Liquidity Risk": 0.15,
            "Profit Margin": 0.15,
        }

        overall_score = sum(f.score * weights.get(f.name, 0.2) for f in factors)

        # Determine overall level
        if overall_score < 30:
            overall_level = RiskLevel.LOW
            viability = "GO"
        elif overall_score < 50:
            overall_level = RiskLevel.MEDIUM
            viability = "CAUTION"
        elif overall_score < 70:
            overall_level = RiskLevel.HIGH
            viability = "CAUTION"
        else:
            overall_level = RiskLevel.CRITICAL
            viability = "NO-GO"

        # Generate recommendations
        recommendations = self._generate_recommendations(factors, result)

        # Generate warnings
        for factor in factors:
            if factor.level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                warnings.append(f"{factor.name}: {factor.description}")

        return RiskAssessment(
            overall_level=overall_level,
            overall_score=overall_score,
            viability=viability,
            factors=factors,
            recommendations=recommendations,
            warnings=warnings,
        )

    def _assess_mev_risk(self, result: StrategyResult) -> RiskFactor:
        """Assess MEV competition risk."""
        # Higher score = more competition
        pair_key = (result.loan_asset, "USDC")  # Simplified

        score = self.MEV_COMPETITION.get(pair_key, self.MEV_COMPETITION.get("default", 50))

        # Adjust for trade size (larger = more attractive to MEV)
        if result.loan_amount > 100:
            score = min(100, score + 15)
        elif result.loan_amount > 50:
            score = min(100, score + 10)

        # Adjust for profit (more profit = more competition)
        if result.net_profit_usd > 500:
            score = min(100, score + 10)

        if score < 30:
            level = RiskLevel.LOW
        elif score < 50:
            level = RiskLevel.MEDIUM
        elif score < 70:
            level = RiskLevel.HIGH
        else:
            level = RiskLevel.CRITICAL

        return RiskFactor(
            name="MEV Competition",
            level=level,
            score=score,
            description=f"High bot activity on {result.loan_asset} pairs",
            mitigation="Use Flashbots Protect or private transactions",
        )

    def _assess_execution_risk(self, result: StrategyResult) -> RiskFactor:
        """Assess execution risk (slippage, timing)."""
        # Base score from number of steps
        num_steps = len(result.steps)
        score = min(100, num_steps * 15)

        # Adjust for gas cost relative to profit
        if result.net_profit > 0:
            gas_ratio = float(result.gas_cost_eth / result.net_profit)
            if gas_ratio > 0.5:
                score = min(100, score + 20)
            elif gas_ratio > 0.3:
                score = min(100, score + 10)

        if score < 30:
            level = RiskLevel.LOW
        elif score < 50:
            level = RiskLevel.MEDIUM
        elif score < 70:
            level = RiskLevel.HIGH
        else:
            level = RiskLevel.CRITICAL

        return RiskFactor(
            name="Execution Risk",
            level=level,
            score=score,
            description=f"{num_steps} steps with gas-sensitive timing",
            mitigation="Set tight slippage tolerance; use gas price oracles",
        )

    def _assess_protocol_risk(self, result: StrategyResult) -> RiskFactor:
        """Assess protocol/smart contract risk."""
        # Get protocols involved
        protocols = set()
        for step in result.steps:
            protocols.add(step.protocol.lower())

        # Sum risk scores
        total_risk = sum(self.PROTOCOL_RISK.get(p, self.PROTOCOL_RISK["default"]) for p in protocols)

        # Average across protocols
        score = total_risk / len(protocols) if protocols else 50

        if score < 25:
            level = RiskLevel.LOW
        elif score < 40:
            level = RiskLevel.MEDIUM
        elif score < 60:
            level = RiskLevel.HIGH
        else:
            level = RiskLevel.CRITICAL

        return RiskFactor(
            name="Protocol Risk",
            level=level,
            score=score,
            description=f"Using {len(protocols)} protocol(s): {', '.join(protocols)}",
            mitigation="Verify protocol audits; monitor for exploits",
        )

    def _assess_liquidity_risk(self, result: StrategyResult) -> RiskFactor:
        """Assess liquidity/slippage risk."""
        # Simplified: larger trades = higher liquidity risk
        trade_usd = float(result.loan_amount * Decimal(str(self.eth_price_usd)))

        if trade_usd < 10000:
            score = 20
        elif trade_usd < 50000:
            score = 35
        elif trade_usd < 100000:
            score = 50
        elif trade_usd < 500000:
            score = 70
        else:
            score = 90

        if score < 30:
            level = RiskLevel.LOW
        elif score < 50:
            level = RiskLevel.MEDIUM
        elif score < 70:
            level = RiskLevel.HIGH
        else:
            level = RiskLevel.CRITICAL

        return RiskFactor(
            name="Liquidity Risk",
            level=level,
            score=score,
            description=f"${trade_usd:,.0f} trade may cause significant slippage",
            mitigation="Check pool liquidity; consider splitting order",
        )

    def _assess_profit_risk(self, result: StrategyResult) -> RiskFactor:
        """Assess profit margin risk."""
        # Thin margins = high risk
        if result.loan_amount > 0:
            margin_pct = float(result.net_profit / result.loan_amount * 100)
        else:
            margin_pct = 0

        if margin_pct < 0:
            score = 100  # Negative profit = maximum risk
        elif margin_pct < 0.1:
            score = 80
        elif margin_pct < 0.5:
            score = 50
        elif margin_pct < 1.0:
            score = 30
        else:
            score = 15

        if score < 30:
            level = RiskLevel.LOW
        elif score < 50:
            level = RiskLevel.MEDIUM
        elif score < 70:
            level = RiskLevel.HIGH
        else:
            level = RiskLevel.CRITICAL

        return RiskFactor(
            name="Profit Margin",
            level=level,
            score=score,
            description=f"{margin_pct:.3f}% profit margin {'(NEGATIVE!)' if margin_pct < 0 else ''}",
            mitigation="Increase trade size or wait for better opportunity",
        )

    def _generate_recommendations(self, factors: List[RiskFactor], result: StrategyResult) -> List[str]:
        """Generate actionable recommendations."""
        recs = []

        # Check MEV risk
        mev_factor = next((f for f in factors if f.name == "MEV Competition"), None)
        if mev_factor and mev_factor.level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            recs.append("Use Flashbots Protect to avoid sandwich attacks")
            recs.append("Consider private transaction submission")

        # Check execution risk
        exec_factor = next((f for f in factors if f.name == "Execution Risk"), None)
        if exec_factor and exec_factor.level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            recs.append("Set tight slippage tolerance (0.5% or less)")
            recs.append("Monitor gas prices before execution")

        # Check profit margin
        profit_factor = next((f for f in factors if f.name == "Profit Margin"), None)
        if profit_factor and profit_factor.level == RiskLevel.CRITICAL:
            if result.net_profit < 0:
                recs.append("Strategy is UNPROFITABLE - do not execute")
            else:
                recs.append("Profit margin too thin - wait for better opportunity")

        # Check liquidity
        liq_factor = next((f for f in factors if f.name == "Liquidity Risk"), None)
        if liq_factor and liq_factor.level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            recs.append("Consider splitting into smaller trades")
            recs.append("Check DEX liquidity depth before execution")

        # General recommendations
        if not recs:
            recs.append("Conditions appear favorable - proceed with caution")
            recs.append("Always test on testnet first")

        return recs


def demo():
    """Demonstrate risk assessment."""
    from strategy_engine import StrategyFactory, ArbitrageParams

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

    # Assess risk
    assessor = RiskAssessor(eth_price_usd=2500.0)
    assessment = assessor.assess(result)

    print("=" * 60)
    print("RISK ASSESSMENT")
    print("=" * 60)

    print(f"\nOverall Risk: {assessment.overall_level.value}")
    print(f"Risk Score: {assessment.overall_score:.0f}/100")
    print(f"Viability: {assessment.viability}")

    print("\n" + "-" * 60)
    print("RISK FACTORS")
    print("-" * 60)

    for factor in assessment.factors:
        indicator = {
            RiskLevel.LOW: "🟢",
            RiskLevel.MEDIUM: "🟡",
            RiskLevel.HIGH: "🟠",
            RiskLevel.CRITICAL: "🔴",
        }.get(factor.level, "⚪")

        print(f"\n{indicator} {factor.name}: {factor.level.value} ({factor.score:.0f})")
        print(f"   {factor.description}")
        print(f"   → {factor.mitigation}")

    if assessment.warnings:
        print("\n" + "-" * 60)
        print("WARNINGS")
        print("-" * 60)
        for warning in assessment.warnings:
            print(f"  ⚠️  {warning}")

    print("\n" + "-" * 60)
    print("RECOMMENDATIONS")
    print("-" * 60)
    for rec in assessment.recommendations:
        print(f"  • {rec}")


if __name__ == "__main__":
    demo()
