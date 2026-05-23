#!/usr/bin/env python3
"""
Pool Formatters

Formats pool analysis output.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 2.0.0
License: MIT
"""

import json
import csv
import io
from datetime import datetime
from typing import Dict, Any, List


class PoolFormatter:
    """Formats pool analysis for display."""

    def __init__(self):
        """Initialize formatter."""
        self.timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    def format(self, data: Any, format_type: str = "table", detailed: bool = False) -> str:
        """Format data for output.

        Args:
            data: Pool or list of pools
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
                return self._format_pool_list(data, detailed)
            else:
                return self._format_single_pool(data, detailed)

    def _format_single_pool(self, pool: Dict[str, Any], detailed: bool = False) -> str:
        """Format a single pool analysis.

        Args:
            pool: Pool data
            detailed: Show detailed breakdown

        Returns:
            Formatted string
        """
        lines = []
        metrics = pool.get("metrics", {})

        # Header
        lines.append("=" * 78)
        lines.append(f"  LIQUIDITY POOL ANALYZER{' ' * 31}{self.timestamp}")
        lines.append("=" * 78)
        lines.append("")

        # Pool info
        protocol = pool.get("project", "Unknown")
        symbol = pool.get("symbol", "?")
        chain = pool.get("chain", "?")
        fee_tier = metrics.get("fee_tier_pct", 0)

        lines.append(f"  POOL: {symbol} ({protocol} - {fee_tier}%)")
        lines.append("-" * 78)
        lines.append(f"  Chain:          {chain}")

        # Format TVL
        tvl = metrics.get("tvl", 0)
        lines.append(f"  TVL:            {self._format_usd(tvl)}")

        # Format Volume
        volume = metrics.get("volume_24h", 0)
        lines.append(f"  24h Volume:     {self._format_usd(volume)}")

        lines.append(f"  Fee Tier:       {fee_tier}%")
        lines.append("")

        # Fee metrics
        lines.append("  FEE METRICS")
        lines.append("-" * 78)
        lines.append(f"  24h Fees:       {self._format_usd(metrics.get('daily_fees', 0))}")
        lines.append(f"  Fee APR:        {metrics.get('fee_apr', 0):.2f}%")
        lines.append(f"  Volume/TVL:     {metrics.get('volume_tvl_ratio', 0):.4f}")
        lines.append("")

        # Token composition (if available)
        token0 = pool.get("token0", {})
        token1 = pool.get("token1", {})
        if token0 or token1:
            lines.append("  TOKEN COMPOSITION")
            lines.append("-" * 78)
            if token0.get("symbol"):
                lines.append(f"  {token0.get('symbol', 'Token0')}:           (token details)")
            if token1.get("symbol"):
                lines.append(f"  {token1.get('symbol', 'Token1')}:           (token details)")
            lines.append("")

        # Health indicators
        health_score = metrics.get("health_score", 0)
        health_level = metrics.get("health_level", "unknown")
        lines.append("  HEALTH INDICATORS")
        lines.append("-" * 78)
        lines.append(f"  Health Score:   {health_score}/100 ({health_level.title()})")
        lines.append(f"  Efficiency:     {metrics.get('capital_efficiency', 'N/A').replace('_', ' ').title()}")

        warnings = metrics.get("warnings", [])
        if warnings:
            lines.append("")
            lines.append("  Warnings:")
            for w in warnings:
                lines.append(f"    - {w}")

        lines.append("=" * 78)

        return "\n".join(lines)

    def _format_pool_list(self, pools: List[Dict[str, Any]], detailed: bool = False) -> str:
        """Format a list of pools as table.

        Args:
            pools: List of pools
            detailed: Show detailed breakdown

        Returns:
            Formatted string
        """
        lines = []

        # Header
        lines.append("=" * 78)
        lines.append(f"  LIQUIDITY POOL ANALYZER{' ' * 31}{self.timestamp}")
        lines.append("=" * 78)
        lines.append("")

        if not pools:
            lines.append("  No pools found matching criteria.")
            lines.append("=" * 78)
            return "\n".join(lines)

        # Table header
        lines.append("  POOL COMPARISON")
        lines.append("-" * 78)
        header = f"  {'Protocol':<15} {'Pair':<15} {'Chain':<12} {'TVL':>10} {'Fee APR':>10}"
        lines.append(header)
        lines.append("-" * 78)

        # Table rows
        for pool in pools:
            metrics = pool.get("metrics", {})
            protocol = (pool.get("project") or "?")[:14]
            symbol = (pool.get("symbol") or "?")[:14]
            chain = (pool.get("chain") or "?")[:11]
            tvl = metrics.get("tvl", pool.get("tvlUsd", 0))
            fee_apr = metrics.get("fee_apr", 0)

            tvl_str = self._format_usd_short(tvl)
            row = f"  {protocol:<15} {symbol:<15} {chain:<12} {tvl_str:>10} {fee_apr:>9.2f}%"
            lines.append(row)

        lines.append("-" * 78)
        lines.append(f"  Total: {len(pools)} pools")
        lines.append("=" * 78)

        return "\n".join(lines)

    def format_il_report(self, il_data: Dict[str, Any], pool: Dict[str, Any] = None) -> str:
        """Format impermanent loss report.

        Args:
            il_data: IL calculation results
            pool: Optional pool data for context

        Returns:
            Formatted string
        """
        lines = []

        lines.append("=" * 78)
        lines.append(f"  IMPERMANENT LOSS CALCULATION{' ' * 26}{self.timestamp}")
        lines.append("=" * 78)
        lines.append("")

        lines.append("-" * 78)
        lines.append(f"  Entry Price:    ${il_data.get('entry_price', 0):,.2f}")
        lines.append(f"  Current Price:  ${il_data.get('current_price', 0):,.2f}")
        lines.append(f"  Price Change:   {il_data.get('price_change_pct', 0):+.1f}%")
        lines.append("")

        lines.append(f"  IL (%):         {il_data.get('il_pct', 0):.2f}%")

        if "position_value" in il_data:
            lines.append(f"  IL (USD):       ${il_data.get('il_usd', 0):,.2f}")
            lines.append("")
            lines.append(f"  Value if HODL:  ${il_data.get('value_if_held', 0):,.2f}")
            lines.append(f"  Value in LP:    ${il_data.get('value_in_lp', 0):,.2f}")

        # Breakeven analysis if available
        if pool and pool.get("metrics"):
            lines.append("")
            lines.append("  BREAKEVEN ANALYSIS")
            lines.append("-" * 78)
            metrics = pool["metrics"]
            lines.append(f"  Fee Tier:       {metrics.get('fee_tier_pct', 0)}%")
            lines.append(f"  Daily Fee APR:  {metrics.get('fee_apr', 0) / 365:.4f}%")

            # Calculate breakeven days
            il_pct = abs(il_data.get("il_pct", 0))
            daily_fee_pct = metrics.get("fee_apr", 0) / 365
            if daily_fee_pct > 0:
                days = il_pct / daily_fee_pct
                lines.append(f"  Days to Break:  {days:.0f} days")

        lines.append("=" * 78)

        return "\n".join(lines)

    def format_il_scenarios(self, scenarios: List[Dict[str, float]]) -> str:
        """Format IL scenarios table.

        Args:
            scenarios: List of IL scenarios

        Returns:
            Formatted string
        """
        lines = []

        lines.append("=" * 78)
        lines.append("  IMPERMANENT LOSS SCENARIOS")
        lines.append("=" * 78)
        lines.append("")

        lines.append("-" * 78)
        header = f"  {'Price Change':>15} {'Price Ratio':>15} {'IL':>15}"
        lines.append(header)
        lines.append("-" * 78)

        for s in scenarios:
            pct = s.get("price_change_pct", 0)
            ratio = s.get("price_ratio", 1)
            il = s.get("il_pct", 0)

            row = f"  {pct:>+14.0f}% {ratio:>14.2f}x {il:>14.2f}%"
            lines.append(row)

        lines.append("-" * 78)
        lines.append("=" * 78)

        return "\n".join(lines)

    def _format_json(self, data: Any) -> str:
        """Format as JSON.

        Args:
            data: Data to format

        Returns:
            JSON string
        """
        output = {
            "timestamp": self.timestamp,
            "data": data if isinstance(data, list) else [data],
        }
        return json.dumps(output, indent=2, default=str)

    def _format_csv(self, data: Any) -> str:
        """Format as CSV.

        Args:
            data: Data to format

        Returns:
            CSV string
        """
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
                "Pool Address",
                "TVL (USD)",
                "Volume 24h",
                "Fee Tier (%)",
                "Fee APR (%)",
                "Volume/TVL",
                "Health Score",
            ]
        )

        for pool in data:
            metrics = pool.get("metrics", {})
            writer.writerow(
                [
                    pool.get("project", ""),
                    pool.get("symbol", ""),
                    pool.get("chain", ""),
                    pool.get("pool", ""),
                    metrics.get("tvl", pool.get("tvlUsd", 0)),
                    metrics.get("volume_24h", pool.get("volumeUsd", 0)),
                    metrics.get("fee_tier_pct", 0),
                    metrics.get("fee_apr", 0),
                    metrics.get("volume_tvl_ratio", 0),
                    metrics.get("health_score", 0),
                ]
            )

        return output.getvalue()

    def _format_usd(self, value: float) -> str:
        """Format USD value with appropriate suffix.

        Args:
            value: USD amount

        Returns:
            Formatted string
        """
        if value >= 1e9:
            return f"${value / 1e9:.2f}B"
        elif value >= 1e6:
            return f"${value / 1e6:.2f}M"
        elif value >= 1e3:
            return f"${value / 1e3:.1f}K"
        else:
            return f"${value:,.2f}"

    def _format_usd_short(self, value: float) -> str:
        """Format USD value compactly.

        Args:
            value: USD amount

        Returns:
            Formatted string
        """
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
    formatter = PoolFormatter()

    # Test pool data
    pool = {
        "pool": "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640",
        "project": "uniswap-v3",
        "chain": "Ethereum",
        "symbol": "USDC-WETH",
        "token0": {"symbol": "USDC"},
        "token1": {"symbol": "WETH"},
        "metrics": {
            "tvl": 500_000_000,
            "volume_24h": 125_000_000,
            "fee_tier_pct": 0.05,
            "daily_fees": 62500,
            "fee_apr": 4.56,
            "volume_tvl_ratio": 0.25,
            "capital_efficiency": "high",
            "health_score": 90,
            "health_level": "healthy",
            "warnings": [],
        },
    }

    print(formatter.format(pool, "table"))


if __name__ == "__main__":
    main()
