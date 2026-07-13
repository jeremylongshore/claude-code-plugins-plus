#!/usr/bin/env python3
"""
Arbitrage opportunity output formatters.

Handles all output formatting:
- Console tables and reports
- JSON export
- Alert messages
"""

import json
from decimal import Decimal
from typing import List, Optional

from opportunity_scanner import ArbitrageOpportunity, ScanResult, RiskLevel
from triangular_finder import ArbitragePath
from profit_calculator import ProfitBreakdown


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

    # Risk level indicators
    RISK_INDICATORS = {
        RiskLevel.LOW: ("🟢", "LOW"),
        RiskLevel.MEDIUM: ("🟡", "MEDIUM"),
        RiskLevel.HIGH: ("🟠", "HIGH"),
        RiskLevel.EXTREME: ("🔴", "EXTREME"),
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

    def format_scan_result(self, result: ScanResult) -> str:
        """Format a scan result with all opportunities."""
        lines = []

        lines.append(self._header("ARBITRAGE SCAN RESULTS"))

        # Summary
        lines.append(f"Pair: {result.pair}")
        lines.append(f"Exchanges scanned: {len(result.quotes)}")
        lines.append(f"Opportunities found: {len(result.opportunities)}")

        if not result.opportunities:
            lines.append("\nNo profitable opportunities found (market is efficient)")
            return "\n".join(lines)

        # Price table
        lines.append(self._subheader("CURRENT PRICES"))
        lines.append(f"{'Exchange':<15} {'Bid':>12} {'Ask':>12} {'Spread':>8}")
        lines.append("-" * 50)

        for quote in sorted(result.quotes, key=lambda x: x.bid, reverse=True):
            lines.append(f"{quote.exchange:<15} ${quote.bid:>11,.2f} ${quote.ask:>11,.2f} {quote.spread_pct:>7.3f}%")

        # Opportunities table
        lines.append(self._subheader("OPPORTUNITIES"))
        lines.append(f"{'Buy On':<15} {'Sell On':<15} {'Gross':>8} {'Net':>8} {'Risk':<8}")
        lines.append("-" * 60)

        for opp in result.opportunities[:10]:
            indicator = "+" if opp.is_profitable else "-"
            risk_icon, _ = self.RISK_INDICATORS.get(opp.risk_level, ("⚪", "?"))
            lines.append(
                f"{opp.buy_exchange:<15} "
                f"{opp.sell_exchange:<15} "
                f"{indicator}{opp.gross_spread_pct:>6.3f}% "
                f"{indicator}{opp.net_spread_pct:>6.3f}% "
                f"{risk_icon} {opp.risk_level.value:<6}"
            )

        # Best opportunity details
        if result.best_opportunity:
            lines.append(self._subheader("BEST OPPORTUNITY"))
            lines.append(self.format_opportunity_details(result.best_opportunity))

        return "\n".join(lines)

    def format_opportunity_details(self, opp: ArbitrageOpportunity) -> str:
        """Format detailed view of a single opportunity."""
        lines = []

        risk_icon, risk_label = self.RISK_INDICATORS.get(opp.risk_level, ("⚪", "UNKNOWN"))

        lines.append(f"Buy on {opp.buy_exchange} at ${opp.buy_price:,.2f}")
        lines.append(f"Sell on {opp.sell_exchange} at ${opp.sell_price:,.2f}")
        lines.append("")
        lines.append(f"Gross spread: {opp.gross_spread_pct:+.4f}%")
        lines.append(f"Buy fee: -{opp.buy_fee_pct:.2f}%")
        lines.append(f"Sell fee: -{opp.sell_fee_pct:.2f}%")
        if opp.estimated_gas_usd > 0:
            lines.append(f"Gas cost: ~${opp.estimated_gas_usd:.2f}")
        lines.append("-" * 40)
        lines.append(f"Net spread: {opp.net_spread_pct:+.4f}%")
        lines.append(f"Risk: {risk_icon} {risk_label}")

        if opp.notes:
            lines.append("")
            lines.append("Notes:")
            for note in opp.notes:
                lines.append(f"  • {note}")

        if opp.is_profitable:
            lines.append("")
            lines.append("✓ PROFITABLE - Consider execution")
        else:
            lines.append("")
            lines.append("✗ NOT PROFITABLE after fees")

        return "\n".join(lines)

    def format_triangular_results(self, paths: List[ArbitragePath]) -> str:
        """Format triangular arbitrage results."""
        lines = []

        lines.append(self._header("TRIANGULAR ARBITRAGE"))

        if not paths:
            lines.append("No profitable triangular paths found")
            return "\n".join(lines)

        lines.append(f"Found {len(paths)} paths\n")

        lines.append(f"{'Path':<30} {'Gross':>10} {'Fees':>10} {'Net':>10}")
        lines.append("-" * 65)

        for path in paths[:10]:
            path_str = " → ".join(path.tokens)
            indicator = "+" if path.is_profitable else "-"
            lines.append(
                f"{path_str:<30} "
                f"{indicator}{abs(path.gross_profit_pct):>8.4f}% "
                f"-{path.total_fees_pct:>8.4f}% "
                f"{indicator}{abs(path.net_profit_pct):>8.4f}%"
            )

        # Best path details
        if paths:
            best = paths[0]
            lines.append(self._subheader("BEST PATH"))
            lines.append(f"Path: {' → '.join(best.tokens)}")
            lines.append(f"Exchange: {best.exchange}")
            lines.append("")
            lines.append("Execution Steps:")
            for i, step in enumerate(best.execution_steps, 1):
                lines.append(f"  {i}. {step}")
            lines.append("")
            lines.append(f"Gross Profit: {best.gross_profit_pct:+.4f}%")
            lines.append(f"Total Fees: -{best.total_fees_pct:.4f}%")
            lines.append(f"Net Profit: {best.net_profit_pct:+.4f}%")

        return "\n".join(lines)

    def format_profit_breakdown(self, breakdown: ProfitBreakdown) -> str:
        """Format profit breakdown."""
        lines = []

        lines.append(self._header("PROFIT BREAKDOWN"))

        lines.append(f"Trade: {breakdown.trade_amount} {breakdown.pair.split('/')[0]}")
        lines.append(f"Buy on {breakdown.buy_exchange} at ${breakdown.buy_price:,.2f}")
        lines.append(f"Sell on {breakdown.sell_exchange} at ${breakdown.sell_price:,.2f}")

        lines.append("")
        lines.append(f"Gross Profit: ${breakdown.gross_profit:,.2f} ({breakdown.gross_profit_pct:+.3f}%)")

        lines.append("")
        lines.append("Costs:")
        lines.append(f"  Buy fee:        -${breakdown.buy_fee:,.2f}")
        lines.append(f"  Sell fee:       -${breakdown.sell_fee:,.2f}")
        lines.append(f"  Withdrawal:     -${breakdown.withdrawal_fee:,.2f}")
        lines.append(f"  Gas:            -${breakdown.gas_cost_usd:,.2f}")
        lines.append(f"  Slippage:       -${breakdown.slippage_cost:,.2f}")
        lines.append(f"  {'-' * 30}")
        lines.append(f"  Total:          -${breakdown.total_costs:,.2f}")

        lines.append("")
        lines.append(f"Net Profit: ${breakdown.net_profit:,.2f} ({breakdown.net_profit_pct:+.3f}%)")
        lines.append(f"Breakeven spread: {breakdown.breakeven_spread_pct:.3f}%")

        if breakdown.is_profitable:
            lines.append("\n✓ PROFITABLE")
        else:
            lines.append("\n✗ NOT PROFITABLE")

        return "\n".join(lines)

    def format_alert(
        self,
        opp: ArbitrageOpportunity,
        trade_amount: Optional[Decimal] = None,
    ) -> str:
        """Format an alert message for a detected opportunity."""
        lines = []

        lines.append("=" * 60)
        lines.append("🚨 ARBITRAGE ALERT")
        lines.append("=" * 60)
        lines.append("")
        lines.append(f"{opp.pair} spread {opp.net_spread_pct:+.3f}%")
        lines.append(f"Buy on {opp.buy_exchange} at ${opp.buy_price:,.2f}")
        lines.append(f"Sell on {opp.sell_exchange} at ${opp.sell_price:,.2f}")

        if trade_amount:
            profit = opp.profit_for_amount(trade_amount)
            lines.append("")
            lines.append(f"For {trade_amount} units:")
            lines.append(f"Estimated profit: ${profit:,.2f}")

        risk_icon, risk_label = self.RISK_INDICATORS.get(opp.risk_level, ("⚪", "?"))
        lines.append("")
        lines.append(f"Risk: {risk_icon} {risk_label}")

        return "\n".join(lines)


class JSONFormatter:
    """Format output as JSON."""

    def format_scan_result(self, result: ScanResult) -> str:
        """Format scan result as JSON."""
        data = {
            "pair": result.pair,
            "timestamp": result.timestamp,
            "quotes_count": len(result.quotes),
            "opportunities_count": len(result.opportunities),
            "quotes": [
                {
                    "exchange": q.exchange,
                    "exchange_type": q.exchange_type.value,
                    "bid": float(q.bid),
                    "ask": float(q.ask),
                    "spread_pct": q.spread_pct,
                    "volume_24h": float(q.volume_24h),
                }
                for q in result.quotes
            ],
            "opportunities": [
                {
                    "buy_exchange": o.buy_exchange,
                    "sell_exchange": o.sell_exchange,
                    "buy_price": float(o.buy_price),
                    "sell_price": float(o.sell_price),
                    "gross_spread_pct": o.gross_spread_pct,
                    "net_spread_pct": o.net_spread_pct,
                    "risk_level": o.risk_level.value,
                    "is_profitable": o.is_profitable,
                }
                for o in result.opportunities
            ],
            "best_opportunity": None,
        }

        if result.best_opportunity:
            o = result.best_opportunity
            data["best_opportunity"] = {
                "buy_exchange": o.buy_exchange,
                "sell_exchange": o.sell_exchange,
                "buy_price": float(o.buy_price),
                "sell_price": float(o.sell_price),
                "net_spread_pct": o.net_spread_pct,
                "risk_level": o.risk_level.value,
            }

        return json.dumps(data, indent=2, cls=DecimalEncoder)

    def format_triangular_results(self, paths: List[ArbitragePath]) -> str:
        """Format triangular results as JSON."""
        data = {
            "paths_count": len(paths),
            "paths": [
                {
                    "tokens": p.tokens,
                    "exchange": p.exchange,
                    "gross_profit_pct": p.gross_profit_pct,
                    "total_fees_pct": p.total_fees_pct,
                    "net_profit_pct": p.net_profit_pct,
                    "is_profitable": p.is_profitable,
                    "steps": p.execution_steps,
                }
                for p in paths
            ],
        }
        return json.dumps(data, indent=2, cls=DecimalEncoder)

    def format_profit_breakdown(self, breakdown: ProfitBreakdown) -> str:
        """Format profit breakdown as JSON."""
        data = {
            "pair": breakdown.pair,
            "buy_exchange": breakdown.buy_exchange,
            "sell_exchange": breakdown.sell_exchange,
            "trade_amount": float(breakdown.trade_amount),
            "buy_price": float(breakdown.buy_price),
            "sell_price": float(breakdown.sell_price),
            "gross_profit": float(breakdown.gross_profit),
            "gross_profit_pct": breakdown.gross_profit_pct,
            "costs": {
                "buy_fee": float(breakdown.buy_fee),
                "sell_fee": float(breakdown.sell_fee),
                "withdrawal_fee": float(breakdown.withdrawal_fee),
                "gas_cost_usd": float(breakdown.gas_cost_usd),
                "slippage_cost": float(breakdown.slippage_cost),
                "total": float(breakdown.total_costs),
            },
            "net_profit": float(breakdown.net_profit),
            "net_profit_pct": breakdown.net_profit_pct,
            "net_profit_usd": float(breakdown.net_profit_usd),
            "breakeven_spread_pct": breakdown.breakeven_spread_pct,
            "is_profitable": breakdown.is_profitable,
        }
        return json.dumps(data, indent=2, cls=DecimalEncoder)


def demo():
    """Demonstrate formatters."""
    from opportunity_scanner import OpportunityScanner

    # Run a scan
    scanner = OpportunityScanner(min_profit_pct=0.0)
    result = scanner.scan("ETH", "USDC")

    # Console format
    console = ConsoleFormatter()
    print(console.format_scan_result(result))

    # JSON format
    print("\n" + "=" * 70)
    print("JSON OUTPUT")
    print("=" * 70)
    json_fmt = JSONFormatter()
    print(json_fmt.format_scan_result(result))


if __name__ == "__main__":
    demo()
