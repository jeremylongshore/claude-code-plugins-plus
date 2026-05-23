#!/usr/bin/env python3
"""
Report Generator

Formats tax calculation results for output (Form 8949, JSON, CSV).

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 2.0.0
License: MIT
"""

import csv
import io
import json
from datetime import datetime
from typing import Dict, Any, Optional


class ReportGenerator:
    """Formats tax calculation results for output."""

    def format(
        self, data: Dict[str, Any], format_type: str = "table", year: Optional[int] = None, show_lots: bool = False
    ) -> str:
        """Format tax calculation results.

        Args:
            data: Tax calculation results
            format_type: Output format (table, json, csv)
            year: Tax year for report header
            show_lots: Include lot-level details

        Returns:
            Formatted string output
        """
        if format_type == "json":
            return self._format_json(data)
        elif format_type == "csv":
            return self._format_csv(data, year)
        else:
            return self._format_table(data, year, show_lots)

    def format_comparison(self, results: Dict[str, Dict], format_type: str = "table") -> str:
        """Format method comparison results.

        Args:
            results: Dictionary of method -> results
            format_type: Output format

        Returns:
            Formatted comparison output
        """
        if format_type == "json":
            return json.dumps(results, indent=2, default=str)

        lines = []
        w = 70

        lines.append("=" * w)
        lines.append("  COST BASIS METHOD COMPARISON")
        lines.append("=" * w)
        lines.append("")

        # Summary table
        lines.append(f"{'Method':<10} {'Net Gain/Loss':>15} {'ST Gain':>12} {'LT Gain':>12}")
        lines.append("-" * w)

        for method, data in results.items():
            s = data.get("summary", {})
            net = s.get("net_gain_loss", 0)
            st = s.get("short_term_gain", 0) + s.get("short_term_loss", 0)
            lt = s.get("long_term_gain", 0) + s.get("long_term_loss", 0)

            net_str = f"${net:,.2f}" if net >= 0 else f"-${abs(net):,.2f}"
            st_str = f"${st:,.2f}" if st >= 0 else f"-${abs(st):,.2f}"
            lt_str = f"${lt:,.2f}" if lt >= 0 else f"-${abs(lt):,.2f}"

            lines.append(f"{method.upper():<10} {net_str:>15} {st_str:>12} {lt_str:>12}")

        lines.append("")
        lines.append("=" * w)

        # Recommendation
        best = min(results.items(), key=lambda x: x[1].get("summary", {}).get("net_gain_loss", 0))
        lines.append(f"  Lowest tax liability: {best[0].upper()}")
        lines.append("")
        lines.append("  Note: FIFO is the IRS default. Other methods may require")
        lines.append("  consistent application and adequate records.")
        lines.append("=" * w)

        return "\n".join(lines)

    def format_income(self, data: Dict[str, Any], format_type: str = "table") -> str:
        """Format income report.

        Args:
            data: Income calculation results
            format_type: Output format

        Returns:
            Formatted income report
        """
        if format_type == "json":
            return json.dumps(data, indent=2, default=str)

        lines = []
        w = 70

        lines.append("=" * w)
        lines.append("  CRYPTO INCOME REPORT")
        lines.append("=" * w)
        lines.append("")

        events = data.get("income_events", [])

        if events:
            lines.append(f"{'Type':<12} {'Date':<12} {'Asset':<8} {'Quantity':>12} {'FMV (USD)':>12}")
            lines.append("-" * w)

            for event in events:
                date_str = (
                    event["date"].strftime("%Y-%m-%d")
                    if isinstance(event["date"], datetime)
                    else str(event["date"])[:10]
                )
                lines.append(
                    f"{event['type']:<12} {date_str:<12} {event['asset']:<8} "
                    f"{event['quantity']:>12.4f} ${event['fair_market_value']:>10,.2f}"
                )

            lines.append("-" * w)

        # Summary by type
        lines.append("")
        lines.append("  SUMMARY BY TYPE")
        lines.append("-" * w)

        by_type = data.get("by_type", {})
        for income_type, info in by_type.items():
            lines.append(f"  {income_type.capitalize():<15} {info['count']:>5} events  ${info['total_value']:>12,.2f}")

        lines.append("-" * w)
        lines.append(f"  {'TOTAL':<15} {data.get('event_count', 0):>5} events  ${data.get('total_income', 0):>12,.2f}")
        lines.append("")
        lines.append("=" * w)
        lines.append("  Income is taxed as ordinary income at receipt fair market value.")
        lines.append("=" * w)

        return "\n".join(lines)

    def _format_table(self, data: Dict[str, Any], year: Optional[int], show_lots: bool) -> str:
        """Format as terminal table."""
        lines = []
        w = 78

        # Header
        year_str = str(year) if year else "All Years"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

        lines.append("=" * w)
        lines.append(f"  CRYPTO TAX REPORT - {year_str}")
        lines.append(f"  Method: {data.get('method', 'FIFO').upper()}  |  Generated: {timestamp}")
        lines.append("=" * w)
        lines.append("")

        # Separate short-term and long-term disposals
        disposals = data.get("disposals", [])
        short_term = [d for d in disposals if not d.get("is_long_term")]
        long_term = [d for d in disposals if d.get("is_long_term")]

        # Short-term section
        lines.append("  SHORT-TERM CAPITAL GAINS/LOSSES (< 1 year)")
        lines.append("-" * w)

        if short_term:
            lines.append(
                f"  {'Description':<14} {'Acquired':<12} {'Sold':<12} {'Proceeds':>12} {'Cost':>12} {'Gain/Loss':>12}"
            )
            for d in short_term:
                desc = f"{d['quantity']:.4f} {d['asset']}"[:14]
                acq = (
                    d["date_acquired"].strftime("%m/%d/%Y")
                    if isinstance(d["date_acquired"], datetime)
                    else str(d["date_acquired"])[:10]
                )
                sold = (
                    d["date_sold"].strftime("%m/%d/%Y")
                    if isinstance(d["date_sold"], datetime)
                    else str(d["date_sold"])[:10]
                )
                gain_str = f"${d['gain_loss']:,.2f}" if d["gain_loss"] >= 0 else f"-${abs(d['gain_loss']):,.2f}"
                lines.append(
                    f"  {desc:<14} {acq:<12} {sold:<12} ${d['proceeds']:>10,.2f} ${d['cost_basis']:>10,.2f} {gain_str:>12}"
                )
        else:
            lines.append("  (No short-term transactions)")

        # Short-term subtotal
        summary = data.get("summary", {})
        st_net = summary.get("short_term_gain", 0) + summary.get("short_term_loss", 0)
        st_str = f"${st_net:,.2f}" if st_net >= 0 else f"-${abs(st_net):,.2f}"
        lines.append("-" * w)
        lines.append(f"  {'Short-term Total:':<52} {st_str:>24}")
        lines.append("")

        # Long-term section
        lines.append("  LONG-TERM CAPITAL GAINS/LOSSES (>= 1 year)")
        lines.append("-" * w)

        if long_term:
            lines.append(
                f"  {'Description':<14} {'Acquired':<12} {'Sold':<12} {'Proceeds':>12} {'Cost':>12} {'Gain/Loss':>12}"
            )
            for d in long_term:
                desc = f"{d['quantity']:.4f} {d['asset']}"[:14]
                acq = (
                    d["date_acquired"].strftime("%m/%d/%Y")
                    if isinstance(d["date_acquired"], datetime)
                    else str(d["date_acquired"])[:10]
                )
                sold = (
                    d["date_sold"].strftime("%m/%d/%Y")
                    if isinstance(d["date_sold"], datetime)
                    else str(d["date_sold"])[:10]
                )
                gain_str = f"${d['gain_loss']:,.2f}" if d["gain_loss"] >= 0 else f"-${abs(d['gain_loss']):,.2f}"
                lines.append(
                    f"  {desc:<14} {acq:<12} {sold:<12} ${d['proceeds']:>10,.2f} ${d['cost_basis']:>10,.2f} {gain_str:>12}"
                )
        else:
            lines.append("  (No long-term transactions)")

        # Long-term subtotal
        lt_net = summary.get("long_term_gain", 0) + summary.get("long_term_loss", 0)
        lt_str = f"${lt_net:,.2f}" if lt_net >= 0 else f"-${abs(lt_net):,.2f}"
        lines.append("-" * w)
        lines.append(f"  {'Long-term Total:':<52} {lt_str:>24}")
        lines.append("")

        # Summary section
        lines.append("=" * w)
        lines.append("  SUMMARY")
        lines.append("-" * w)

        net = summary.get("net_gain_loss", 0)
        net_str = f"${net:,.2f}" if net >= 0 else f"-${abs(net):,.2f}"

        lines.append(f"  Total Proceeds:           ${summary.get('total_proceeds', 0):>15,.2f}")
        lines.append(f"  Total Cost Basis:         ${summary.get('total_cost_basis', 0):>15,.2f}")
        lines.append(f"  Net Capital Gain/Loss:    {net_str:>16}")
        lines.append("")
        lines.append(f"  Short-term Gains:         ${summary.get('short_term_gain', 0):>15,.2f}")
        lines.append(f"  Short-term Losses:        ${summary.get('short_term_loss', 0):>15,.2f}")
        lines.append(f"  Long-term Gains:          ${summary.get('long_term_gain', 0):>15,.2f}")
        lines.append(f"  Long-term Losses:         ${summary.get('long_term_loss', 0):>15,.2f}")

        # Income events if present
        income = data.get("income_events", [])
        if income:
            lines.append("")
            lines.append(f"  Ordinary Income Events:   {summary.get('income_count', 0):>16}")
            total_income = sum(e.get("fair_market_value", 0) for e in income)
            lines.append(f"  Total Income Value:       ${total_income:>15,.2f}")

        lines.append("=" * w)

        # Lot details if requested
        if show_lots and data.get("lots"):
            lines.append("")
            lines.append("  REMAINING LOT INVENTORY")
            lines.append("-" * w)

            for asset, lots in data["lots"].items():
                if not lots:
                    continue
                lines.append(f"  {asset}:")
                for lot in lots:
                    lines.append(
                        f"    Lot #{lot['lot_id']}: {lot['remaining']:.4f} @ "
                        f"${lot['cost_basis_per_unit']:.2f} (acquired {lot['acquired_date']})"
                    )
            lines.append("")

        # Disclaimer
        lines.append("")
        lines.append("  DISCLAIMER: This report is for informational purposes only.")
        lines.append("  Consult a qualified tax professional for tax advice.")
        lines.append("=" * w)

        return "\n".join(lines)

    def _format_json(self, data: Dict[str, Any]) -> str:
        """Format as JSON."""

        # Convert datetime objects to strings
        def serialize(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            return str(obj)

        return json.dumps(data, indent=2, default=serialize)

    def _format_csv(self, data: Dict[str, Any], year: Optional[int]) -> str:
        """Format as CSV (Form 8949 compatible)."""
        output = io.StringIO()
        writer = csv.writer(output)

        # Form 8949 header
        writer.writerow(
            [
                "Description of Property",
                "Date Acquired",
                "Date Sold or Disposed",
                "Proceeds (Sales Price)",
                "Cost or Other Basis",
                "Gain or (Loss)",
                "Short/Long Term",
                "Holding Period (Days)",
            ]
        )

        disposals = data.get("disposals", [])

        for d in disposals:
            desc = f"{d['quantity']:.8f} {d['asset']}"
            acq = (
                d["date_acquired"].strftime("%m/%d/%Y")
                if isinstance(d["date_acquired"], datetime)
                else str(d["date_acquired"])[:10]
            )
            sold = (
                d["date_sold"].strftime("%m/%d/%Y")
                if isinstance(d["date_sold"], datetime)
                else str(d["date_sold"])[:10]
            )
            term = "Long-term" if d.get("is_long_term") else "Short-term"

            writer.writerow(
                [
                    desc,
                    acq,
                    sold,
                    f"{d['proceeds']:.2f}",
                    f"{d['cost_basis']:.2f}",
                    f"{d['gain_loss']:.2f}",
                    term,
                    d.get("holding_days", ""),
                ]
            )

        # Summary section
        writer.writerow([])
        writer.writerow(["SUMMARY"])

        summary = data.get("summary", {})
        writer.writerow(["Total Proceeds", f"{summary.get('total_proceeds', 0):.2f}"])
        writer.writerow(["Total Cost Basis", f"{summary.get('total_cost_basis', 0):.2f}"])
        writer.writerow(["Net Gain/Loss", f"{summary.get('net_gain_loss', 0):.2f}"])
        writer.writerow(["Short-term Gain", f"{summary.get('short_term_gain', 0):.2f}"])
        writer.writerow(["Short-term Loss", f"{summary.get('short_term_loss', 0):.2f}"])
        writer.writerow(["Long-term Gain", f"{summary.get('long_term_gain', 0):.2f}"])
        writer.writerow(["Long-term Loss", f"{summary.get('long_term_loss', 0):.2f}"])
        writer.writerow(["Method", data.get("method", "fifo").upper()])
        if year:
            writer.writerow(["Tax Year", year])

        return output.getvalue()


def main():
    """CLI entry point for testing."""
    from datetime import datetime

    # Sample data
    data = {
        "disposals": [
            {
                "date_acquired": datetime(2024, 1, 15),
                "date_sold": datetime(2025, 1, 20),
                "asset": "BTC",
                "quantity": 0.5,
                "proceeds": 47500.0,
                "cost_basis": 20000.0,
                "gain_loss": 27500.0,
                "is_long_term": True,
                "holding_days": 371,
                "lot_id": 1,
            },
            {
                "date_acquired": datetime(2024, 6, 15),
                "date_sold": datetime(2025, 1, 20),
                "asset": "BTC",
                "quantity": 0.25,
                "proceeds": 23750.0,
                "cost_basis": 16250.0,
                "gain_loss": 7500.0,
                "is_long_term": False,
                "holding_days": 219,
                "lot_id": 2,
            },
        ],
        "income_events": [
            {
                "date": datetime(2024, 3, 1),
                "type": "staking",
                "asset": "ETH",
                "quantity": 0.1,
                "fair_market_value": 300.0,
                "price_per_unit": 3000.0,
            }
        ],
        "summary": {
            "total_proceeds": 71250.0,
            "total_cost_basis": 36250.0,
            "net_gain_loss": 35000.0,
            "short_term_gain": 7500.0,
            "short_term_loss": 0.0,
            "long_term_gain": 27500.0,
            "long_term_loss": 0.0,
            "disposal_count": 2,
            "income_count": 1,
        },
        "method": "fifo",
    }

    gen = ReportGenerator()

    print("=== TABLE FORMAT ===")
    print(gen.format(data, "table", year=2025))
    print()
    print("=== CSV FORMAT ===")
    print(gen.format(data, "csv", year=2025))


if __name__ == "__main__":
    main()
