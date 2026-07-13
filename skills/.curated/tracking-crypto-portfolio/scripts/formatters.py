#!/usr/bin/env python3
"""
Portfolio Output Formatters

Formats portfolio data in various output formats:
- Table (default): Terminal-friendly dashboard
- JSON: Machine-readable export
- CSV: Spreadsheet-compatible

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 2.0.0
License: MIT
"""

import csv
import io
import json
from datetime import datetime
from typing import Dict, Any


class PortfolioFormatter:
    """Formats portfolio data for output."""

    def format(
        self, data: Dict[str, Any], format_type: str = "table", show_all_holdings: bool = False, show_pnl: bool = False
    ) -> str:
        """Format portfolio data for output.

        Args:
            data: Portfolio valuation data
            format_type: Output format ("table", "json", "csv")
            show_all_holdings: Show all holdings (not just top 5)
            show_pnl: Show P&L information

        Returns:
            Formatted string output
        """
        if format_type == "json":
            return self._format_json(data)
        elif format_type == "csv":
            return self._format_csv(data, show_pnl)
        else:
            return self._format_table(data, show_all_holdings, show_pnl)

    def _format_table(self, data: Dict[str, Any], show_all: bool, show_pnl: bool) -> str:
        """Format as terminal table/dashboard."""
        lines = []
        w = 78  # Width

        # Header
        timestamp = data.get("meta", {}).get("timestamp", "")
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                time_str = dt.strftime("%Y-%m-%d %H:%M UTC")
            except ValueError:
                time_str = timestamp[:19]
        else:
            time_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

        lines.append("=" * w)
        lines.append(f"  CRYPTO PORTFOLIO TRACKER{' ' * (w - 41)}{time_str}")
        lines.append("=" * w)
        lines.append("")

        # Portfolio Summary
        name = data.get("portfolio_name", "My Portfolio")
        total = data.get("total_value_usd", 0)
        holdings_count = data.get("holdings_count", 0)

        lines.append(f"  PORTFOLIO SUMMARY: {name}")
        lines.append("-" * w)
        lines.append(f"  Total Value:    ${total:,.2f} USD")

        # 24h change
        change_24h = data.get("change_24h", {})
        if change_24h.get("percent") is not None:
            amount = change_24h.get("amount", 0)
            pct = change_24h.get("percent", 0)
            sign = "+" if amount >= 0 else ""
            lines.append(f"  24h Change:     {sign}${amount:,.2f} ({sign}{pct:.2f}%)")

        # 7d change
        change_7d = data.get("change_7d", {})
        if change_7d.get("percent") is not None:
            amount = change_7d.get("amount", 0)
            pct = change_7d.get("percent", 0)
            sign = "+" if amount >= 0 else ""
            lines.append(f"  7d Change:      {sign}${amount:,.2f} ({sign}{pct:.2f}%)")

        lines.append(f"  Holdings:       {holdings_count} assets")

        # Total P&L if available
        if show_pnl and data.get("total_unrealized_pnl") is not None:
            pnl = data.get("total_unrealized_pnl", 0)
            pnl_pct = data.get("total_pnl_pct", 0)
            sign = "+" if pnl >= 0 else ""
            lines.append(f"  Total P&L:      {sign}${pnl:,.2f} ({sign}{pnl_pct:.2f}%)")

        lines.append("")

        # Holdings Table
        holdings = data.get("holdings", [])
        if holdings:
            display_count = len(holdings) if show_all else min(5, len(holdings))

            if show_all:
                lines.append("  ALL HOLDINGS")
            else:
                lines.append("  TOP HOLDINGS")
            lines.append("-" * w)

            # Table header
            if show_pnl:
                lines.append(f"  {'Coin':<6} {'Quantity':>12} {'Price':>12} {'Value':>14} {'Alloc':>7} {'P&L':>10}")
            else:
                lines.append(f"  {'Coin':<6} {'Quantity':>12} {'Price':>12} {'Value':>14} {'Alloc':>7} {'24h':>8}")

            for holding in holdings[:display_count]:
                coin = holding.get("coin", "")
                qty = holding.get("quantity", 0)
                price = holding.get("price_usd", 0)
                value = holding.get("value_usd", 0)
                alloc = holding.get("allocation_pct", 0)

                if show_pnl and holding.get("pnl_pct") is not None:
                    pnl_pct = holding.get("pnl_pct", 0)
                    sign = "+" if pnl_pct >= 0 else ""
                    change_str = f"{sign}{pnl_pct:.1f}%"
                else:
                    change_24h = holding.get("change_24h_pct")
                    if change_24h is not None:
                        sign = "+" if change_24h >= 0 else ""
                        change_str = f"{sign}{change_24h:.1f}%"
                    else:
                        change_str = "N/A"

                lines.append(
                    f"  {coin:<6} {qty:>12.4f} ${price:>10,.2f} ${value:>12,.2f} {alloc:>6.1f}% {change_str:>8}"
                )

            if not show_all and len(holdings) > 5:
                remaining = len(holdings) - 5
                lines.append(f"  ... and {remaining} more holdings")

            lines.append("")

        # Category Allocation
        categories = data.get("allocation_by_category", {})
        if categories and show_all:
            lines.append("  ALLOCATION BY CATEGORY")
            lines.append("-" * w)
            for category, pct in categories.items():
                bar_len = int(pct / 2)  # Scale to fit
                bar = "█" * bar_len
                lines.append(f"  {category:<15} {pct:>5.1f}% {bar}")
            lines.append("")

        # Risk Flags
        risk_flags = data.get("risk_flags", [])
        if risk_flags:
            lines.append("  ⚠ CONCENTRATION WARNINGS")
            lines.append("-" * w)
            for flag in risk_flags:
                lines.append(f"  • {flag}")
            lines.append("")

        # Footer
        lines.append("=" * w)
        threshold = data.get("meta", {}).get("threshold", 25)
        lines.append(f"  Concentration threshold: {threshold}%  |  Data: CoinGecko")
        lines.append("=" * w)

        return "\n".join(lines)

    def _format_json(self, data: Dict[str, Any]) -> str:
        """Format as JSON."""
        return json.dumps(data, indent=2, default=str)

    def _format_csv(self, data: Dict[str, Any], include_pnl: bool) -> str:
        """Format as CSV."""
        output = io.StringIO()
        writer = csv.writer(output)

        # Header row
        headers = [
            "coin",
            "quantity",
            "price_usd",
            "value_usd",
            "allocation_pct",
            "change_24h_pct",
            "change_7d_pct",
            "market_cap",
        ]

        if include_pnl:
            headers.extend(["cost_basis", "total_cost", "unrealized_pnl", "pnl_pct"])

        writer.writerow(headers)

        # Data rows
        for holding in data.get("holdings", []):
            row = [
                holding.get("coin", ""),
                holding.get("quantity", 0),
                holding.get("price_usd", 0),
                holding.get("value_usd", 0),
                holding.get("allocation_pct", 0),
                holding.get("change_24h_pct", ""),
                holding.get("change_7d_pct", ""),
                holding.get("market_cap", ""),
            ]

            if include_pnl:
                row.extend(
                    [
                        holding.get("cost_basis", ""),
                        holding.get("total_cost", ""),
                        holding.get("unrealized_pnl", ""),
                        holding.get("pnl_pct", ""),
                    ]
                )

            writer.writerow(row)

        # Summary row
        writer.writerow([])
        writer.writerow(["SUMMARY"])
        writer.writerow(["Portfolio Name", data.get("portfolio_name", "")])
        writer.writerow(["Total Value USD", data.get("total_value_usd", 0)])
        writer.writerow(["Holdings Count", data.get("holdings_count", 0)])

        if data.get("change_24h", {}).get("percent") is not None:
            writer.writerow(["24h Change %", data["change_24h"]["percent"]])

        if include_pnl and data.get("total_unrealized_pnl") is not None:
            writer.writerow(["Total Unrealized P&L", data.get("total_unrealized_pnl", 0)])
            writer.writerow(["Total P&L %", data.get("total_pnl_pct", 0)])

        return output.getvalue()


def main():
    """CLI entry point for testing."""
    # Test with sample data
    sample_data = {
        "portfolio_name": "Test Portfolio",
        "total_value_usd": 125450.00,
        "change_24h": {"amount": 2540.50, "percent": 2.07},
        "change_7d": {"amount": 8125.00, "percent": 6.92},
        "holdings_count": 5,
        "total_cost": 80000,
        "total_unrealized_pnl": 45450,
        "total_pnl_pct": 56.8,
        "holdings": [
            {
                "coin": "BTC",
                "quantity": 0.5,
                "price_usd": 95000,
                "value_usd": 47500,
                "allocation_pct": 37.9,
                "change_24h_pct": 2.5,
                "cost_basis": 50000,
                "total_cost": 25000,
                "unrealized_pnl": 22500,
                "pnl_pct": 90.0,
            },
            {
                "coin": "ETH",
                "quantity": 10,
                "price_usd": 3200,
                "value_usd": 32000,
                "allocation_pct": 25.5,
                "change_24h_pct": 1.8,
                "cost_basis": 2500,
                "total_cost": 25000,
                "unrealized_pnl": 7000,
                "pnl_pct": 28.0,
            },
            {
                "coin": "SOL",
                "quantity": 100,
                "price_usd": 180,
                "value_usd": 18000,
                "allocation_pct": 14.4,
                "change_24h_pct": 4.2,
            },
        ],
        "allocation_by_category": {"Layer 1": 77.8, "Other": 22.2},
        "risk_flags": ["BTC allocation (37.9%) exceeds 25% threshold", "ETH allocation (25.5%) exceeds 25% threshold"],
        "meta": {"timestamp": "2026-01-14T15:30:00Z", "threshold": 25},
    }

    formatter = PortfolioFormatter()

    print("=== TABLE FORMAT ===")
    print(formatter.format(sample_data, "table", show_all_holdings=True, show_pnl=True))
    print()
    print("=== JSON FORMAT ===")
    print(formatter.format(sample_data, "json"))
    print()
    print("=== CSV FORMAT ===")
    print(formatter.format(sample_data, "csv", show_pnl=True))


if __name__ == "__main__":
    main()
