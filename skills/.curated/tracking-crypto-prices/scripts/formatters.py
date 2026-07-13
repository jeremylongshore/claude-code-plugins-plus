#!/usr/bin/env python3
"""
Price Formatters - Output Formatting for Price Data

Provides human-readable table output, JSON formatting, CSV export,
and minimal output modes for cryptocurrency price data.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 2.0.0
License: MIT
"""

import json
import csv
import io
from datetime import datetime
from typing import List, Optional


class PriceFormatter:
    """
    Formats cryptocurrency price data for various output modes.

    Supports:
    - Table: Human-readable aligned tables
    - JSON: Machine-readable JSON
    - CSV: Spreadsheet-compatible export
    - Minimal: Single-line output for scripting
    """

    # Currency symbols for formatting
    CURRENCY_SYMBOLS = {
        "USD": "$",
        "EUR": "€",
        "GBP": "£",
        "JPY": "¥",
        "CAD": "C$",
        "AUD": "A$",
        "CHF": "CHF ",
        "CNY": "¥",
        "INR": "₹",
        "KRW": "₩",
    }

    def __init__(self, currency: str = "USD"):
        """
        Initialize formatter.

        Args:
            currency: Default currency code
        """
        self.currency = currency.upper()
        self.currency_symbol = self.CURRENCY_SYMBOLS.get(self.currency, "")

    def _format_price(self, price: float) -> str:
        """
        Format a price value with appropriate precision.

        Args:
            price: Price value

        Returns:
            Formatted price string
        """
        if price >= 1000:
            return f"{self.currency_symbol}{price:,.2f}"
        elif price >= 1:
            return f"{self.currency_symbol}{price:.2f}"
        elif price >= 0.0001:
            return f"{self.currency_symbol}{price:.6f}"
        else:
            return f"{self.currency_symbol}{price:.8f}"

    def _format_large_number(self, value: Optional[float]) -> str:
        """
        Format large numbers with K/M/B suffixes.

        Args:
            value: Number to format

        Returns:
            Formatted string
        """
        if value is None:
            return "N/A"

        if value >= 1_000_000_000_000:
            return f"${value / 1_000_000_000_000:.2f}T"
        elif value >= 1_000_000_000:
            return f"${value / 1_000_000_000:.2f}B"
        elif value >= 1_000_000:
            return f"${value / 1_000_000:.2f}M"
        elif value >= 1_000:
            return f"${value / 1_000:.2f}K"
        else:
            return f"${value:.2f}"

    def _format_change(self, change: Optional[float]) -> str:
        """
        Format percentage change with color indicators.

        Args:
            change: Percentage change

        Returns:
            Formatted change string
        """
        if change is None:
            return "N/A"

        if change >= 0:
            return f"+{change:.2f}%"
        else:
            return f"{change:.2f}%"

    def format_prices(self, prices: List[dict], format_type: str = "table", verbose: bool = False) -> str:
        """
        Format a list of price data.

        Args:
            prices: List of price dictionaries
            format_type: Output format (table, json, csv, minimal)
            verbose: Include extra details

        Returns:
            Formatted output string
        """
        if format_type == "json":
            return self._format_json(prices)
        elif format_type == "csv":
            return self._format_csv_prices(prices)
        elif format_type == "minimal":
            return self._format_minimal(prices)
        else:
            return self._format_table(prices, verbose)

    def _format_table(self, prices: List[dict], verbose: bool = False) -> str:
        """Format prices as aligned table."""
        if not prices:
            return "No price data available"

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines = []

        # Header
        lines.append("=" * 80)
        lines.append(f"  CRYPTO PRICES{' ' * 45}Updated: {timestamp}")
        lines.append("=" * 80)
        lines.append("")

        # Column headers
        if verbose:
            header = f"  {'Symbol':<10} {'Price':>14} {'24h':>10} {'7d':>10} {'Volume':>12} {'Market Cap':>12}"
        else:
            header = f"  {'Symbol':<10} {'Price':>14} {'24h Change':>12} {'Volume (24h)':>14} {'Market Cap':>12}"
        lines.append(header)
        lines.append("-" * 80)

        # Data rows
        total_change = 0
        total_weight = 0

        for p in prices:
            symbol = p.get("symbol", "???").upper()
            price = p.get("price", 0)
            change_24h = p.get("change_24h")
            change_7d = p.get("change_7d")
            volume = p.get("volume_24h")
            market_cap = p.get("market_cap")

            price_str = self._format_price(price)
            change_24h_str = self._format_change(change_24h)
            change_7d_str = self._format_change(change_7d) if verbose else ""
            volume_str = self._format_large_number(volume)
            mcap_str = self._format_large_number(market_cap)

            # Track weighted average change
            if change_24h is not None and market_cap is not None:
                total_change += change_24h * market_cap
                total_weight += market_cap

            # Stale/cached indicators
            suffix = ""
            if p.get("_cache_stale"):
                suffix = " (stale)"
            elif p.get("_cached"):
                suffix = " (cached)"

            if verbose:
                row = f"  {symbol:<10} {price_str:>14} {change_24h_str:>10} {change_7d_str:>10} {volume_str:>12} {mcap_str:>12}{suffix}"
            else:
                row = f"  {symbol:<10} {price_str:>14} {change_24h_str:>12} {volume_str:>14} {mcap_str:>12}{suffix}"

            lines.append(row)

        lines.append("-" * 80)

        # Summary
        if total_weight > 0:
            weighted_change = total_change / total_weight
            lines.append(f"  Total 24h Change: {self._format_change(weighted_change)} (weighted)")
        lines.append("")
        lines.append("=" * 80)

        return "\n".join(lines)

    def _format_json(self, prices: List[dict]) -> str:
        """Format prices as JSON."""
        # Clean internal fields
        cleaned = []
        for p in prices:
            clean_p = {k: v for k, v in p.items() if not k.startswith("_")}
            cleaned.append(clean_p)

        output = {
            "prices": cleaned,
            "meta": {"count": len(cleaned), "currency": self.currency, "timestamp": datetime.utcnow().isoformat()},
        }

        return json.dumps(output, indent=2)

    def _format_csv_prices(self, prices: List[dict]) -> str:
        """Format prices as CSV."""
        if not prices:
            return ""

        output = io.StringIO()
        fieldnames = [
            "symbol",
            "name",
            "price",
            "currency",
            "change_24h",
            "change_7d",
            "volume_24h",
            "market_cap",
            "timestamp",
            "source",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()

        for p in prices:
            # Filter out internal fields
            clean_p = {k: v for k, v in p.items() if not k.startswith("_")}
            writer.writerow(clean_p)

        return output.getvalue()

    def _format_minimal(self, prices: List[dict]) -> str:
        """Format prices as minimal one-line output."""
        parts = []
        for p in prices:
            symbol = p.get("symbol", "???").upper()
            price = p.get("price", 0)
            change = p.get("change_24h")

            if change is not None:
                change_str = f"({self._format_change(change)})"
            else:
                change_str = ""

            parts.append(f"{symbol}:{self._format_price(price)}{change_str}")

        return " | ".join(parts)

    def format_historical(self, symbol: str, data: List[dict], format_type: str = "table") -> str:
        """
        Format historical price data.

        Args:
            symbol: Cryptocurrency symbol
            data: List of historical data points
            format_type: Output format

        Returns:
            Formatted output string
        """
        if format_type == "json":
            return self._format_historical_json(symbol, data)
        elif format_type == "csv":
            return self._format_historical_csv(data)
        else:
            return self._format_historical_table(symbol, data)

    def _format_historical_table(self, symbol: str, data: List[dict]) -> str:
        """Format historical data as table."""
        if not data:
            return "No historical data available"

        lines = []
        lines.append("=" * 70)
        lines.append(f"  HISTORICAL PRICES: {symbol.upper()}")
        lines.append(f"  Period: {data[0].get('date', 'N/A')} to {data[-1].get('date', 'N/A')}")
        lines.append("=" * 70)
        lines.append("")

        # Determine columns based on data
        has_ohlc = "open" in data[0]

        if has_ohlc:
            lines.append(f"  {'Date':<12} {'Open':>12} {'High':>12} {'Low':>12} {'Close':>12}")
        else:
            lines.append(f"  {'Date':<12} {'Price':>14} {'Volume':>16}")

        lines.append("-" * 70)

        for d in data[-30:]:  # Show last 30 entries
            date = d.get("date", "N/A")

            if has_ohlc:
                open_p = self._format_price(d.get("open", 0))
                high = self._format_price(d.get("high", 0))
                low = self._format_price(d.get("low", 0))
                close = self._format_price(d.get("close", 0))
                lines.append(f"  {date:<12} {open_p:>12} {high:>12} {low:>12} {close:>12}")
            else:
                price = self._format_price(d.get("price", 0))
                volume = self._format_large_number(d.get("volume"))
                lines.append(f"  {date:<12} {price:>14} {volume:>16}")

        if len(data) > 30:
            lines.append(f"  ... ({len(data) - 30} more entries)")

        lines.append("-" * 70)
        lines.append(f"  Total data points: {len(data)}")
        lines.append("=" * 70)

        return "\n".join(lines)

    def _format_historical_json(self, symbol: str, data: List[dict]) -> str:
        """Format historical data as JSON."""
        output = {
            "symbol": symbol.upper(),
            "data": data,
            "meta": {
                "count": len(data),
                "start_date": data[0].get("date") if data else None,
                "end_date": data[-1].get("date") if data else None,
                "timestamp": datetime.utcnow().isoformat(),
            },
        }
        return json.dumps(output, indent=2)

    def _format_historical_csv(self, data: List[dict]) -> str:
        """Format historical data as CSV."""
        if not data:
            return ""

        output = io.StringIO()

        # Determine columns from first row
        if "open" in data[0]:
            fieldnames = ["date", "open", "high", "low", "close", "volume"]
        else:
            fieldnames = ["date", "price", "volume"]

        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()

        for d in data:
            writer.writerow(d)

        return output.getvalue()

    def print_coin_list(self, coins: List[dict], query: Optional[str] = None) -> None:
        """
        Print a list of available coins.

        Args:
            coins: List of coin info dictionaries
            query: Search query that was used
        """
        if not coins:
            if query:
                print(f"No coins found matching '{query}'")
            else:
                print("No coins available")
            return

        print("=" * 60)
        if query:
            print(f"  SEARCH RESULTS: '{query}'")
        else:
            print("  AVAILABLE CRYPTOCURRENCIES")
        print("=" * 60)
        print(f"  {'Symbol':<10} {'ID':<25} {'Name':<20}")
        print("-" * 60)

        for coin in coins[:50]:  # Limit to 50 results
            symbol = coin.get("symbol", "").upper()
            coin_id = coin.get("id", "")
            name = coin.get("name", "")

            # Truncate long names
            if len(name) > 18:
                name = name[:17] + "..."

            print(f"  {symbol:<10} {coin_id:<25} {name:<20}")

        if len(coins) > 50:
            print(f"  ... and {len(coins) - 50} more")

        print("-" * 60)
        print(f"  Total: {len(coins)} coins")
        print("=" * 60)
