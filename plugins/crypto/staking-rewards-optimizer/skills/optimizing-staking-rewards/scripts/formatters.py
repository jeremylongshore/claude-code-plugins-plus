#!/usr/bin/env python3
"""
Staking Output Formatters

Formats staking analysis output for display.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 2.0.0
License: MIT
"""

import json
import csv
import io
from datetime import datetime
from typing import Dict, Any, List


class StakingFormatter:
    """Formats staking analysis for display."""

    def __init__(self):
        """Initialize formatter."""
        self.timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    def format(self, data: Any, format_type: str = "table", detailed: bool = False) -> str:
        """Format data for output.

        Args:
            data: Staking data (single option or list)
            format_type: Output format (table, json, csv)
            detailed: Show detailed breakdown

        Returns:
            Formatted string
        """
        if format_type == "json":
            return self._format_json(data)
        elif format_type == "csv":
            return self._format_csv(data)
        else:
            if isinstance(data, list):
                return self._format_table(data, detailed)
            else:
                return self._format_single(data, detailed)

    def _format_table(self, options: List[Dict[str, Any]], detailed: bool = False) -> str:
        """Format as comparison table.

        Args:
            options: List of staking options
            detailed: Show detailed info

        Returns:
            Formatted table string
        """
        lines = []

        # Header
        lines.append("=" * 78)
        lines.append(f"  STAKING REWARDS OPTIMIZER{' ' * 29}{self.timestamp}")
        lines.append("=" * 78)
        lines.append("")

        if not options:
            lines.append("  No staking options found.")
            lines.append("=" * 78)
            return "\n".join(lines)

        # Determine asset from first option
        asset = options[0].get("base_asset", "")
        if asset:
            lines.append(f"  STAKING OPTIONS FOR {asset}")
        else:
            lines.append("  STAKING OPTIONS")
        lines.append("-" * 78)

        # Table header
        if detailed:
            header = f"  {'Protocol':<18} {'Type':<8} {'Gross':>7} {'Net':>7} {'Risk':>5} {'TVL':>10} {'Unbond':<10}"
        else:
            header = f"  {'Protocol':<20} {'Type':<8} {'Net APY':>10} {'Risk':>6} {'TVL':>12}"
        lines.append(header)
        lines.append("-" * 78)

        # Table rows
        for opt in options:
            metrics = opt.get("metrics", {})
            risk = opt.get("risk_assessment", {})

            name = opt.get("project", "?")
            symbol = opt.get("symbol", "")
            if symbol:
                name = f"{name} ({symbol})"
            name = name[: 18 if detailed else 20]

            stype = (opt.get("staking_type", "?"))[:7]
            gross_apy = metrics.get("gross_apy", opt.get("apy", 0) or 0)
            net_apy = metrics.get("net_apy", gross_apy)
            risk_score = risk.get("overall_score", 5) if isinstance(risk, dict) else 5
            tvl = metrics.get("tvl_usd", opt.get("tvlUsd", 0) or 0)
            unbonding = metrics.get("unbonding", opt.get("unbonding", "?"))[:9]

            tvl_str = self._format_usd_short(tvl)

            if detailed:
                row = f"  {name:<18} {stype:<8} {gross_apy:>6.2f}% {net_apy:>6.2f}% {risk_score:>4}/10 {tvl_str:>10} {unbonding:<10}"
            else:
                row = f"  {name:<20} {stype:<8} {net_apy:>9.2f}% {risk_score:>4}/10 {tvl_str:>12}"
            lines.append(row)

        lines.append("-" * 78)
        lines.append(f"  Total: {len(options)} options | Ranked by risk-adjusted return")
        lines.append("=" * 78)

        return "\n".join(lines)

    def _format_single(self, option: Dict[str, Any], detailed: bool = False) -> str:
        """Format single staking option.

        Args:
            option: Staking option data
            detailed: Show detailed info

        Returns:
            Formatted string
        """
        lines = []
        metrics = option.get("metrics", {})
        risk = option.get("risk_assessment", {})

        # Header
        lines.append("=" * 78)
        lines.append(f"  STAKING REWARDS OPTIMIZER{' ' * 29}{self.timestamp}")
        lines.append("=" * 78)
        lines.append("")

        # Protocol info
        name = option.get("project", "Unknown")
        symbol = option.get("symbol", "")
        stype = option.get("staking_type", "liquid")
        chain = option.get("chain", "?")

        lines.append(f"  PROTOCOL: {name} ({symbol})")
        lines.append("-" * 78)
        lines.append(f"  Chain:          {chain}")
        lines.append(f"  Type:           {stype.title()}")
        lines.append("")

        # Yield metrics
        lines.append("  YIELD METRICS")
        lines.append("-" * 78)
        gross_apy = metrics.get("gross_apy", option.get("apy", 0) or 0)
        fee_rate = metrics.get("protocol_fee_rate", 0)
        net_apy = metrics.get("net_apy", gross_apy)
        effective_apy = metrics.get("effective_apy", net_apy)

        lines.append(f"  Gross APY:      {gross_apy:.2f}%")
        if fee_rate > 0:
            lines.append(f"  Protocol Fee:   {fee_rate * 100:.1f}%")
        lines.append(f"  Net APY:        {net_apy:.2f}%")

        position_usd = metrics.get("position_usd", 0)
        if position_usd > 0:
            lines.append(f"  Effective APY:  {effective_apy:.2f}% (after gas)")
        lines.append("")

        # TVL and position
        tvl = metrics.get("tvl_usd", option.get("tvlUsd", 0) or 0)
        lines.append("  LIQUIDITY")
        lines.append("-" * 78)
        lines.append(f"  Total TVL:      {self._format_usd(tvl)}")
        unbonding = metrics.get("unbonding", option.get("unbonding", "varies"))
        lines.append(f"  Unbonding:      {unbonding}")
        lines.append("")

        # Position projections (if provided)
        if position_usd > 0:
            lines.append("  POSITION PROJECTIONS")
            lines.append("-" * 78)
            lines.append(f"  Position:       {self._format_usd(position_usd)}")
            lines.append(f"  1 Month:        {self._format_usd(metrics.get('projected_1m', 0))}")
            lines.append(f"  3 Months:       {self._format_usd(metrics.get('projected_3m', 0))}")
            lines.append(f"  6 Months:       {self._format_usd(metrics.get('projected_6m', 0))}")
            lines.append(f"  1 Year:         {self._format_usd(metrics.get('projected_1y', 0))}")
            lines.append("")

        # Risk assessment
        if risk:
            lines.append("  RISK ASSESSMENT")
            lines.append("-" * 78)
            score = risk.get("overall_score", 5)
            level = risk.get("risk_level", "medium")
            lines.append(f"  Overall Score:  {score}/10 ({level.replace('_', ' ').title()} Risk)")
            lines.append("")

            if detailed:
                lines.append("  Score Breakdown:")
                lines.append(f"    Audit Status:       {risk.get('audit_score', 0)}/10")
                lines.append(f"    Time in Production: {risk.get('production_score', 0)}/10")
                lines.append(f"    TVL Size:           {risk.get('tvl_score', 0)}/10")
                lines.append(f"    Reputation:         {risk.get('reputation_score', 0)}/10")
                lines.append(f"    Validator Diversity:{risk.get('validator_score', 0)}/10")
                lines.append("")

            factors = risk.get("factors", [])
            if factors:
                lines.append("  Positive Factors:")
                for f in factors[:4]:
                    lines.append(f"    + {f}")
                lines.append("")

            warnings = risk.get("warnings", [])
            if warnings:
                lines.append("  Warnings:")
                for w in warnings[:4]:
                    lines.append(f"    ! {w}")
                lines.append("")

            considerations = risk.get("considerations", [])
            if detailed and considerations:
                lines.append("  Considerations:")
                for c in considerations[:4]:
                    lines.append(f"    - {c}")
                lines.append("")

        lines.append("=" * 78)

        return "\n".join(lines)

    def format_optimization_report(
        self, current_positions: List[Dict], recommendations: List[Dict], summary: Dict[str, Any]
    ) -> str:
        """Format portfolio optimization report.

        Args:
            current_positions: Current staking positions
            recommendations: Optimization recommendations
            summary: Optimization summary

        Returns:
            Formatted report
        """
        lines = []

        # Header
        lines.append("=" * 78)
        lines.append(f"  PORTFOLIO OPTIMIZATION{' ' * 32}{self.timestamp}")
        lines.append("=" * 78)
        lines.append("")

        # Current portfolio
        lines.append("  CURRENT PORTFOLIO")
        lines.append("-" * 78)
        header = f"  {'Position':<25} {'APY':>10} {'Annual Return':>15}"
        lines.append(header)
        lines.append("-" * 78)

        for pos in current_positions:
            amount = pos.get("amount", 0)
            asset = pos.get("asset", "?")
            protocol = pos.get("protocol", "?")
            apy = pos.get("apy", 0)
            annual = pos.get("annual_return", 0)

            name = f"{amount} {asset} @ {protocol}"[:24]
            row = f"  {name:<25} {apy:>9.2f}% {self._format_usd(annual):>15}"
            lines.append(row)

        lines.append("-" * 78)
        total_value = summary.get("total_value", 0)
        blended_apy = summary.get("blended_apy", 0)
        total_annual = summary.get("total_annual", 0)
        lines.append(
            f"  Total: {self._format_usd(total_value):<17} {blended_apy:>9.2f}% {self._format_usd(total_annual):>15}"
        )
        lines.append("")

        # Recommendations
        lines.append("  OPTIMIZED ALLOCATION")
        lines.append("-" * 78)
        header = f"  {'Recommendation':<25} {'APY':>10} {'Annual':>10} {'Change':>12}"
        lines.append(header)
        lines.append("-" * 78)

        for rec in recommendations:
            action = rec.get("action", "Keep")
            asset = rec.get("asset", "?")
            target = rec.get("target_protocol", "")
            new_apy = rec.get("new_apy", 0)
            new_annual = rec.get("new_annual", 0)
            change = rec.get("change", 0)

            if action == "move":
                name = f"{asset} → {target}"[:24]
            else:
                name = f"{asset} → Keep"[:24]

            change_str = f"+{self._format_usd(change)}" if change > 0 else self._format_usd(change)
            row = f"  {name:<25} {new_apy:>9.2f}% {self._format_usd(new_annual):>10} {change_str:>12}"
            lines.append(row)

        lines.append("-" * 78)
        new_annual = summary.get("optimized_annual", 0)
        improvement = summary.get("improvement", 0)
        improvement_pct = summary.get("improvement_pct", 0)
        lines.append(
            f"  Optimized Annual: {self._format_usd(new_annual)}      Improvement: +{self._format_usd(improvement)} (+{improvement_pct:.1f}%)"
        )
        lines.append("")

        # Implementation steps
        steps = summary.get("implementation_steps", [])
        if steps:
            lines.append("  IMPLEMENTATION")
            lines.append("-" * 78)
            for i, step in enumerate(steps[:5], 1):
                lines.append(f"  {i}. {step}")
            lines.append("")

        lines.append("=" * 78)

        return "\n".join(lines)

    def _format_json(self, data: Any) -> str:
        """Format as JSON."""
        output = {
            "timestamp": self.timestamp,
            "data": data if isinstance(data, list) else [data],
        }
        return json.dumps(output, indent=2, default=str)

    def _format_csv(self, data: Any) -> str:
        """Format as CSV."""
        if not isinstance(data, list):
            data = [data]

        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(
            [
                "Protocol",
                "Symbol",
                "Chain",
                "Type",
                "Gross APY",
                "Net APY",
                "Protocol Fee",
                "TVL (USD)",
                "Risk Score",
                "Risk Level",
                "Unbonding",
            ]
        )

        for opt in data:
            metrics = opt.get("metrics", {})
            risk = opt.get("risk_assessment", {})

            writer.writerow(
                [
                    opt.get("project", ""),
                    opt.get("symbol", ""),
                    opt.get("chain", ""),
                    opt.get("staking_type", ""),
                    metrics.get("gross_apy", opt.get("apy", 0)),
                    metrics.get("net_apy", 0),
                    metrics.get("protocol_fee_rate", 0),
                    metrics.get("tvl_usd", opt.get("tvlUsd", 0)),
                    risk.get("overall_score", 0) if isinstance(risk, dict) else 0,
                    risk.get("risk_level", "") if isinstance(risk, dict) else "",
                    metrics.get("unbonding", opt.get("unbonding", "")),
                ]
            )

        return output.getvalue()

    def _format_usd(self, value: float) -> str:
        """Format USD value."""
        if value >= 1e9:
            return f"${value / 1e9:.2f}B"
        elif value >= 1e6:
            return f"${value / 1e6:.2f}M"
        elif value >= 1e3:
            return f"${value / 1e3:.1f}K"
        else:
            return f"${value:,.2f}"

    def _format_usd_short(self, value: float) -> str:
        """Format USD value compactly."""
        if value >= 1e9:
            return f"${value / 1e9:.1f}B"
        elif value >= 1e6:
            return f"${value / 1e6:.0f}M"
        elif value >= 1e3:
            return f"${value / 1e3:.0f}K"
        else:
            return f"${value:.0f}"


def main():
    """CLI entry point for testing."""
    formatter = StakingFormatter()

    # Test data
    options = [
        {
            "project": "lido",
            "symbol": "stETH",
            "chain": "Ethereum",
            "staking_type": "liquid",
            "apy": 4.0,
            "tvlUsd": 15_000_000_000,
            "base_asset": "ETH",
            "metrics": {
                "gross_apy": 4.0,
                "net_apy": 3.6,
                "protocol_fee_rate": 0.10,
                "tvl_usd": 15_000_000_000,
                "unbonding": "instant",
            },
            "risk_assessment": {
                "overall_score": 9,
                "risk_level": "low",
            },
        },
        {
            "project": "rocket-pool",
            "symbol": "rETH",
            "chain": "Ethereum",
            "staking_type": "liquid",
            "apy": 4.2,
            "tvlUsd": 3_000_000_000,
            "base_asset": "ETH",
            "metrics": {
                "gross_apy": 4.2,
                "net_apy": 3.61,
                "protocol_fee_rate": 0.14,
                "tvl_usd": 3_000_000_000,
                "unbonding": "instant",
            },
            "risk_assessment": {
                "overall_score": 8,
                "risk_level": "low",
            },
        },
    ]

    print(formatter.format(options, "table"))


if __name__ == "__main__":
    main()
