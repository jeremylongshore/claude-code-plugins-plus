#!/usr/bin/env python3
"""
Flash loan simulation output formatters.

Handles all output formatting:
- Console tables and reports
- JSON export
- Summary cards
"""

import json
from decimal import Decimal
from typing import List, Optional

from strategy_engine import StrategyResult, StrategyType
from profit_calculator import ProfitBreakdown
from risk_assessor import RiskAssessment, RiskLevel
from protocol_adapters import ProviderInfo


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder that handles Decimal types."""

    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if hasattr(obj, "value"):  # Enum
            return obj.value
        return super().default(obj)


class ConsoleFormatter:
    """Format output for console display."""

    # Box drawing characters
    BOX_H = "─"
    BOX_V = "│"
    BOX_TL = "┌"
    BOX_TR = "┐"
    BOX_BL = "└"
    BOX_BR = "┘"
    BOX_LT = "├"
    BOX_RT = "┤"
    BOX_TB = "┬"
    BOX_BT = "┴"
    BOX_X = "┼"

    # Risk level indicators
    RISK_INDICATORS = {
        RiskLevel.LOW: ("🟢", "LOW"),
        RiskLevel.MEDIUM: ("🟡", "MEDIUM"),
        RiskLevel.HIGH: ("🟠", "HIGH"),
        RiskLevel.CRITICAL: ("🔴", "CRITICAL"),
    }

    def __init__(self, width: int = 70):
        """Initialize formatter with display width."""
        self.width = width

    def _header(self, title: str) -> str:
        """Create a section header."""
        padding = (self.width - len(title) - 2) // 2
        return f"\n{'=' * padding} {title} {'=' * padding}\n"

    def _subheader(self, title: str) -> str:
        """Create a subsection header."""
        return f"\n{'-' * self.width}\n{title}\n{'-' * self.width}\n"

    def _box(self, lines: List[str], title: str = "") -> str:
        """Create a box around content."""
        inner_width = self.width - 4

        result = []

        # Top border with title
        if title:
            title_part = f" {title} "
            border_left = (inner_width - len(title_part)) // 2
            border_right = inner_width - len(title_part) - border_left
            result.append(
                f"{self.BOX_TL}{self.BOX_H * border_left}{title_part}{self.BOX_H * border_right}{self.BOX_TR}"
            )
        else:
            result.append(f"{self.BOX_TL}{self.BOX_H * (inner_width + 2)}{self.BOX_TR}")

        # Content
        for line in lines:
            # Truncate if too long
            if len(line) > inner_width:
                line = line[: inner_width - 3] + "..."
            result.append(f"{self.BOX_V} {line:<{inner_width}} {self.BOX_V}")

        # Bottom border
        result.append(f"{self.BOX_BL}{self.BOX_H * (inner_width + 2)}{self.BOX_BR}")

        return "\n".join(result)

    def format_strategy_result(self, result: StrategyResult) -> str:
        """Format strategy simulation result."""
        lines = []

        # Header
        lines.append(self._header("FLASH LOAN SIMULATION"))

        # Strategy summary box
        summary = [
            f"Strategy: {result.strategy_type.value}",
            f"Loan: {result.loan_amount} {result.loan_asset}",
            f"Provider: {result.provider}",
            f"Profitable: {'YES ✓' if result.is_profitable else 'NO ✗'}",
        ]
        lines.append(self._box(summary, "SUMMARY"))

        # Transaction steps
        lines.append(self._subheader("TRANSACTION STEPS"))
        for i, step in enumerate(result.steps, 1):
            lines.append(f"  {i}. [{step.protocol}] {step.action}")
            lines.append(f"     {step.asset_in} → {step.asset_out}")
            lines.append(f"     {step.amount_in:.6f} → {step.amount_out:.6f}")
            lines.append(f"     Gas: ~{step.gas_estimate:,} units")
            lines.append("")

        # Profit summary
        lines.append(self._subheader("PROFIT BREAKDOWN"))
        lines.append(f"  Gross Profit:  {result.gross_profit:+.6f} {result.loan_asset}")
        lines.append(f"  Flash Loan Fee: -{result.loan_fee:.6f} {result.loan_asset}")
        lines.append(f"  Gas Cost:       -{result.gas_cost_eth:.6f} ETH (${result.gas_cost_usd:.2f})")
        lines.append(f"  {'-' * 40}")
        lines.append(f"  Net Profit:    {result.net_profit:+.6f} {result.loan_asset} (${result.net_profit_usd:+.2f})")
        lines.append(f"  ROI:           {result.roi_percent:.4f}%")

        return "\n".join(lines)

    def format_profit_breakdown(self, breakdown: ProfitBreakdown) -> str:
        """Format detailed profit breakdown."""
        lines = []

        lines.append(self._header("PROFIT BREAKDOWN"))

        # Revenue
        lines.append(f"\n  Gross Revenue: {breakdown.gross_revenue:.6f} ETH")

        # Costs
        lines.append("\n  Costs:")
        lines.append(f"    Flash Loan Fee: -{breakdown.flash_loan_fee:.6f} ETH")
        lines.append(f"    Gas Cost:       -{breakdown.gas_cost_eth:.6f} ETH (${breakdown.gas_cost_usd:.2f})")
        lines.append(f"    Est. Slippage:  -{breakdown.slippage_cost:.6f} ETH")
        lines.append(f"    DEX Fees:       ~{breakdown.dex_fees:.6f} ETH (in price)")
        lines.append(f"    {'-' * 45}")
        lines.append(f"    Total Costs:    -{breakdown.total_costs:.6f} ETH")

        # Net
        lines.append(f"\n  Net Profit: {breakdown.net_profit:+.6f} ETH (${breakdown.net_profit_usd:+.2f})")
        lines.append(f"  ROI: {breakdown.roi_percent:.4f}%")
        lines.append(f"  Breakeven Gas: {breakdown.breakeven_gas_price:.1f} gwei")

        # Verdict
        if breakdown.is_profitable:
            lines.append("\n  ✓ PROFITABLE")
        else:
            lines.append("\n  ✗ NOT PROFITABLE")

        return "\n".join(lines)

    def format_risk_assessment(self, assessment: RiskAssessment) -> str:
        """Format risk assessment report."""
        lines = []

        lines.append(self._header("RISK ASSESSMENT"))

        # Overall rating
        indicator, label = self.RISK_INDICATORS.get(assessment.overall_level, ("⚪", "UNKNOWN"))
        lines.append(f"\n  Overall Risk: {indicator} {label}")
        lines.append(f"  Risk Score: {assessment.overall_score:.0f}/100")
        lines.append(f"  Viability: {assessment.viability}")

        # Individual factors
        lines.append(self._subheader("RISK FACTORS"))

        for factor in assessment.factors:
            ind, lbl = self.RISK_INDICATORS.get(factor.level, ("⚪", "?"))
            lines.append(f"\n  {ind} {factor.name}: {lbl} ({factor.score:.0f})")
            lines.append(f"     {factor.description}")
            lines.append(f"     → {factor.mitigation}")

        # Warnings
        if assessment.warnings:
            lines.append(self._subheader("WARNINGS"))
            for warning in assessment.warnings:
                lines.append(f"  ⚠️  {warning}")

        # Recommendations
        lines.append(self._subheader("RECOMMENDATIONS"))
        for rec in assessment.recommendations:
            lines.append(f"  • {rec}")

        return "\n".join(lines)

    def format_provider_comparison(self, providers: List[ProviderInfo], asset: str, amount: Decimal) -> str:
        """Format provider comparison table."""
        lines = []

        lines.append(self._header("PROVIDER COMPARISON"))
        lines.append(f"\n  Comparing {amount} {asset} flash loan:\n")

        # Table header
        lines.append(f"  {'Provider':<14} {'Fee %':<8} {'Fee Amount':<14} {'Gas OH':<10} {'Chains':<20}")
        lines.append(f"  {'-' * 66}")

        # Table rows
        for info in providers:
            fee_pct = f"{float(info.fee_rate) * 100:.2f}%"
            fee_amt = f"{info.fee_amount:.4f} {asset}"
            gas_oh = f"{info.gas_overhead:,}"
            chains = ", ".join(info.supported_chains[:2])
            if len(info.supported_chains) > 2:
                chains += "..."

            lines.append(f"  {info.name:<14} {fee_pct:<8} {fee_amt:<14} {gas_oh:<10} {chains:<20}")

        # Recommendation
        if providers:
            best = providers[0]
            lines.append(f"\n  Recommended: {best.name}")
            if best.fee_amount == 0:
                lines.append("  (FREE flash loan!)")
            else:
                lines.append(f"  (Lowest fee: {best.fee_amount:.4f} {asset})")

        return "\n".join(lines)

    def format_quick_summary(self, result: StrategyResult, assessment: Optional[RiskAssessment] = None) -> str:
        """Format a quick one-box summary."""
        lines = []

        # Profit line
        profit_emoji = "✓" if result.is_profitable else "✗"
        lines.append(
            f"Net Profit: {result.net_profit:+.6f} {result.loan_asset} (${result.net_profit_usd:+.2f}) {profit_emoji}"
        )

        # Provider
        lines.append(f"Provider: {result.provider} (fee: {result.loan_fee:.6f})")

        # Risk if available
        if assessment:
            ind, lbl = self.RISK_INDICATORS.get(assessment.overall_level, ("⚪", "?"))
            lines.append(f"Risk: {ind} {lbl} | Viability: {assessment.viability}")

        # Verdict
        if result.is_profitable and (assessment is None or assessment.viability != "NO-GO"):
            lines.append("Verdict: PROCEED WITH CAUTION")
        elif result.is_profitable:
            lines.append("Verdict: HIGH RISK - RECONSIDER")
        else:
            lines.append("Verdict: DO NOT EXECUTE")

        return self._box(lines, "QUICK SUMMARY")


class JSONFormatter:
    """Format output as JSON."""

    def format_full_report(
        self,
        result: StrategyResult,
        breakdown: Optional[ProfitBreakdown] = None,
        assessment: Optional[RiskAssessment] = None,
        providers: Optional[List[ProviderInfo]] = None,
    ) -> str:
        """Format complete simulation report as JSON."""
        report = {
            "simulation": {
                "strategy_type": result.strategy_type.value,
                "loan_asset": result.loan_asset,
                "loan_amount": float(result.loan_amount),
                "provider": result.provider,
                "is_profitable": result.is_profitable,
            },
            "profit": {
                "gross_profit": float(result.gross_profit),
                "loan_fee": float(result.loan_fee),
                "gas_cost_eth": float(result.gas_cost_eth),
                "gas_cost_usd": float(result.gas_cost_usd),
                "net_profit": float(result.net_profit),
                "net_profit_usd": float(result.net_profit_usd),
                "roi_percent": result.roi_percent,
            },
            "steps": [
                {
                    "protocol": s.protocol,
                    "action": s.action,
                    "asset_in": s.asset_in,
                    "asset_out": s.asset_out,
                    "amount_in": float(s.amount_in),
                    "amount_out": float(s.amount_out),
                    "gas_estimate": s.gas_estimate,
                }
                for s in result.steps
            ],
        }

        if breakdown:
            report["breakdown"] = {
                "gross_revenue": float(breakdown.gross_revenue),
                "flash_loan_fee": float(breakdown.flash_loan_fee),
                "gas_cost_eth": float(breakdown.gas_cost_eth),
                "gas_cost_usd": float(breakdown.gas_cost_usd),
                "dex_fees": float(breakdown.dex_fees),
                "slippage_cost": float(breakdown.slippage_cost),
                "total_costs": float(breakdown.total_costs),
                "breakeven_gas_price": breakdown.breakeven_gas_price,
            }

        if assessment:
            report["risk"] = {
                "overall_level": assessment.overall_level.value,
                "overall_score": assessment.overall_score,
                "viability": assessment.viability,
                "factors": [
                    {
                        "name": f.name,
                        "level": f.level.value,
                        "score": f.score,
                        "description": f.description,
                        "mitigation": f.mitigation,
                    }
                    for f in assessment.factors
                ],
                "warnings": assessment.warnings,
                "recommendations": assessment.recommendations,
            }

        if providers:
            report["providers"] = [
                {
                    "name": p.name,
                    "fee_rate": float(p.fee_rate),
                    "fee_amount": float(p.fee_amount),
                    "max_available": float(p.max_available),
                    "gas_overhead": p.gas_overhead,
                    "supported_chains": p.supported_chains,
                }
                for p in providers
            ]

        return json.dumps(report, indent=2, cls=DecimalEncoder)

    def format_strategy_result(self, result: StrategyResult) -> str:
        """Format just the strategy result as JSON."""
        return self.format_full_report(result)


class MarkdownFormatter:
    """Format output as Markdown (for reports/docs)."""

    def format_simulation_report(
        self,
        result: StrategyResult,
        breakdown: Optional[ProfitBreakdown] = None,
        assessment: Optional[RiskAssessment] = None,
    ) -> str:
        """Format as Markdown report."""
        lines = []

        lines.append("# Flash Loan Simulation Report\n")

        # Summary
        lines.append("## Summary\n")
        lines.append(f"- **Strategy**: {result.strategy_type.value}")
        lines.append(f"- **Loan**: {result.loan_amount} {result.loan_asset}")
        lines.append(f"- **Provider**: {result.provider}")
        lines.append(f"- **Profitable**: {'Yes ✓' if result.is_profitable else 'No ✗'}")
        lines.append("")

        # Profit
        lines.append("## Profit Analysis\n")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Gross Profit | {result.gross_profit:+.6f} {result.loan_asset} |")
        lines.append(f"| Flash Loan Fee | -{result.loan_fee:.6f} {result.loan_asset} |")
        lines.append(f"| Gas Cost | -{result.gas_cost_eth:.6f} ETH (${result.gas_cost_usd:.2f}) |")
        lines.append(f"| **Net Profit** | **{result.net_profit:+.6f} {result.loan_asset}** |")
        lines.append(f"| ROI | {result.roi_percent:.4f}% |")
        lines.append("")

        # Steps
        lines.append("## Transaction Steps\n")
        for i, step in enumerate(result.steps, 1):
            lines.append(f"### Step {i}: {step.action} on {step.protocol}\n")
            lines.append(f"- Input: {step.amount_in:.6f} {step.asset_in}")
            lines.append(f"- Output: {step.amount_out:.6f} {step.asset_out}")
            lines.append(f"- Gas: ~{step.gas_estimate:,} units")
            lines.append("")

        # Risk if available
        if assessment:
            lines.append("## Risk Assessment\n")
            lines.append(f"- **Overall Level**: {assessment.overall_level.value}")
            lines.append(f"- **Risk Score**: {assessment.overall_score:.0f}/100")
            lines.append(f"- **Viability**: {assessment.viability}")
            lines.append("")

            lines.append("### Risk Factors\n")
            lines.append("| Factor | Level | Score | Description |")
            lines.append("|--------|-------|-------|-------------|")
            for f in assessment.factors:
                lines.append(f"| {f.name} | {f.level.value} | {f.score:.0f} | {f.description} |")
            lines.append("")

            if assessment.warnings:
                lines.append("### Warnings\n")
                for w in assessment.warnings:
                    lines.append(f"- ⚠️ {w}")
                lines.append("")

            lines.append("### Recommendations\n")
            for r in assessment.recommendations:
                lines.append(f"- {r}")
            lines.append("")

        # Disclaimer
        lines.append("---\n")
        lines.append("*This simulation is for educational purposes only. ")
        lines.append("Do not execute without proper testing and risk assessment.*")

        return "\n".join(lines)


def demo():
    """Demonstrate formatters."""
    from strategy_engine import StrategyFactory, ArbitrageParams
    from profit_calculator import ProfitCalculator
    from risk_assessor import RiskAssessor
    from protocol_adapters import ProviderManager

    # Run simulation
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

    # Calculate breakdown
    calculator = ProfitCalculator(eth_price_usd=2500.0, gas_price_gwei=30.0)
    breakdown = calculator.calculate_breakdown(result)

    # Assess risk
    assessor = RiskAssessor(eth_price_usd=2500.0)
    assessment = assessor.assess(result)

    # Get providers
    manager = ProviderManager()
    providers = manager.compare_providers("ETH", Decimal("100"))

    # Console format
    console = ConsoleFormatter()
    print(console.format_strategy_result(result))
    print(console.format_risk_assessment(assessment))
    print(console.format_provider_comparison(providers, "ETH", Decimal("100")))
    print(console.format_quick_summary(result, assessment))

    # JSON format
    print("\n" + "=" * 70)
    print("JSON OUTPUT")
    print("=" * 70)
    json_fmt = JSONFormatter()
    print(json_fmt.format_full_report(result, breakdown, assessment, providers))


if __name__ == "__main__":
    demo()
