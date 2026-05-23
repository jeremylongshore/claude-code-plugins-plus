#!/usr/bin/env python3
"""
Market Movers Formatters - Output Formatting

Format mover results for table, JSON, and CSV output.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 2.0.0
License: MIT
"""

import json
import csv
import io
from datetime import datetime
from typing import Dict, Any


class MoversFormatter:
    """Format market mover results for various output types."""

    def format(self, result: Dict[str, Any], format_type: str = "table") -> str:
        """
        Format mover results.

        Args:
            result: Dictionary with gainers, losers, and meta
            format_type: Output format (table, json, csv)

        Returns:
            Formatted output string
        """
        if format_type == "json":
            return self._format_json(result)
        elif format_type == "csv":
            return self._format_csv(result)
        else:
            return self._format_table(result)

    def _format_table(self, result: Dict[str, Any]) -> str:
        """Format results as aligned table."""
        lines = []
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        meta = result.get("meta", {})

        # Header
        lines.append("=" * 90)
        lines.append(f"  MARKET MOVERS{' ' * 50}Updated: {timestamp}")
        lines.append("=" * 90)

        # Gainers section
        gainers = result.get("gainers", [])
        if gainers:
            lines.append("")
            lines.append(f"  TOP GAINERS ({meta.get('timeframe', '24h')})")
            lines.append("-" * 90)
            lines.append(
                f"  {'Rank':<6}{'Symbol':<10}{'Price':>12}"
                f"{'Change':>12}{'Vol Ratio':>12}{'Market Cap':>14}{'Score':>10}"
            )
            lines.append("-" * 90)

            for g in gainers:
                rank = g.get("rank", "-")
                symbol = g.get("symbol", "???")[:8]
                price = self._format_price(g.get("price", 0))
                change = self._format_change(g.get("change", 0))
                vol_ratio = f"{g.get('volume_ratio', 0):.1f}x"
                market_cap = self._format_large_number(g.get("market_cap", 0))
                score = f"{g.get('significance_score', 0):.1f}"

                lines.append(
                    f"  {rank:<6}{symbol:<10}{price:>12}{change:>12}{vol_ratio:>12}{market_cap:>14}{score:>10}"
                )

            lines.append("-" * 90)

        # Losers section
        losers = result.get("losers", [])
        if losers:
            lines.append("")
            lines.append(f"  TOP LOSERS ({meta.get('timeframe', '24h')})")
            lines.append("-" * 90)
            lines.append(
                f"  {'Rank':<6}{'Symbol':<10}{'Price':>12}"
                f"{'Change':>12}{'Vol Ratio':>12}{'Market Cap':>14}{'Score':>10}"
            )
            lines.append("-" * 90)

            for l in losers:
                rank = l.get("rank", "-")
                symbol = l.get("symbol", "???")[:8]
                price = self._format_price(l.get("price", 0))
                change = self._format_change(l.get("change", 0))
                vol_ratio = f"{l.get('volume_ratio', 0):.1f}x"
                market_cap = self._format_large_number(l.get("market_cap", 0))
                score = f"{l.get('significance_score', 0):.1f}"

                lines.append(
                    f"  {rank:<6}{symbol:<10}{price:>12}{change:>12}{vol_ratio:>12}{market_cap:>14}{score:>10}"
                )

            lines.append("-" * 90)

        # Summary
        lines.append("")
        total_movers = len(gainers) + len(losers)
        lines.append(
            f"  Summary: {total_movers} movers shown | "
            f"Scanned: {meta.get('total_scanned', 0)} assets | "
            f"Matched: {meta.get('matches', 0)}"
        )

        if meta.get("category"):
            lines.append(f"  Category: {meta.get('category')}")

        thresholds = meta.get("thresholds", {})
        if thresholds:
            lines.append(
                f"  Thresholds: "
                f"min_change={thresholds.get('min_change', 5)}%, "
                f"vol_spike={thresholds.get('volume_spike', 2)}x, "
                f"min_cap=${thresholds.get('min_market_cap', 0) / 1e6:.0f}M"
            )

        lines.append("=" * 90)

        return "\n".join(lines)

    def _format_json(self, result: Dict[str, Any]) -> str:
        """Format results as JSON."""
        # Add timestamp to meta
        result = result.copy()
        result["meta"] = result.get("meta", {}).copy()
        result["meta"]["scan_time"] = datetime.utcnow().isoformat() + "Z"

        return json.dumps(result, indent=2)

    def _format_csv(self, result: Dict[str, Any]) -> str:
        """Format results as CSV."""
        output = io.StringIO()

        fieldnames = [
            "type",
            "rank",
            "symbol",
            "name",
            "price",
            "change",
            "volume_ratio",
            "market_cap",
            "significance_score",
        ]

        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        # Write gainers
        for g in result.get("gainers", []):
            writer.writerow(
                {
                    "type": "gainer",
                    "rank": g.get("rank", ""),
                    "symbol": g.get("symbol", ""),
                    "name": g.get("name", ""),
                    "price": g.get("price", ""),
                    "change": g.get("change", ""),
                    "volume_ratio": g.get("volume_ratio", ""),
                    "market_cap": g.get("market_cap", ""),
                    "significance_score": g.get("significance_score", ""),
                }
            )

        # Write losers
        for l in result.get("losers", []):
            writer.writerow(
                {
                    "type": "loser",
                    "rank": l.get("rank", ""),
                    "symbol": l.get("symbol", ""),
                    "name": l.get("name", ""),
                    "price": l.get("price", ""),
                    "change": l.get("change", ""),
                    "volume_ratio": l.get("volume_ratio", ""),
                    "market_cap": l.get("market_cap", ""),
                    "significance_score": l.get("significance_score", ""),
                }
            )

        return output.getvalue()

    def _format_price(self, price: float) -> str:
        """Format a price value."""
        if price >= 1000:
            return f"${price:,.2f}"
        elif price >= 1:
            return f"${price:.2f}"
        elif price >= 0.0001:
            return f"${price:.6f}"
        else:
            return f"${price:.8f}"

    def _format_change(self, change: float) -> str:
        """Format percentage change."""
        if change >= 0:
            return f"+{change:.2f}%"
        else:
            return f"{change:.2f}%"

    def _format_large_number(self, value: float) -> str:
        """Format large numbers with K/M/B suffixes."""
        if value >= 1_000_000_000_000:
            return f"${value / 1_000_000_000_000:.1f}T"
        elif value >= 1_000_000_000:
            return f"${value / 1_000_000_000:.1f}B"
        elif value >= 1_000_000:
            return f"${value / 1_000_000:.1f}M"
        elif value >= 1_000:
            return f"${value / 1_000:.1f}K"
        else:
            return f"${value:.0f}"
