#!/usr/bin/env python3
"""
Yield Formatters

Formats yield data for various output types.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 2.0.0
License: MIT
"""

import json
import csv
import io
from datetime import datetime
from typing import Dict, Any, List


class YieldFormatter:
    """Formats yield data for display."""

    def __init__(self):
        """Initialize formatter."""
        self.timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    def format(self, pools: List[Dict[str, Any]], format_type: str = "table", detailed: bool = False) -> str:
        """Format pools for output.

        Args:
            pools: List of pool data dictionaries
            format_type: Output format (table, json, csv)
            detailed: Show detailed breakdown

        Returns:
            Formatted string
        """
        if format_type == "json":
            return self._format_json(pools)
        elif format_type == "csv":
            return self._format_csv(pools)
        else:
            return self._format_table(pools, detailed)

    def _format_table(self, pools: List[Dict[str, Any]], detailed: bool = False) -> str:
        """Format as ASCII table.

        Args:
            pools: Pool data
            detailed: Show detailed breakdown

        Returns:
            Formatted table string
        """
        lines = []

        # Header
        lines.append("=" * 78)
        lines.append(f"  DEFI YIELD OPTIMIZER{' ' * 35}{self.timestamp}")
        lines.append("=" * 78)
        lines.append("")

        if not pools:
            lines.append("  No pools found matching criteria.")
            lines.append("=" * 78)
            return "\n".join(lines)

        # Summary table
        lines.append("  TOP YIELD OPPORTUNITIES")
        lines.append("-" * 78)

        # Table header
        header = f"  {'Protocol':<15} {'Pool':<12} {'Chain':<12} {'TVL':>10} {'APY':>8} {'Risk':>8} {'Score':>6}"
        lines.append(header)
        lines.append("-" * 78)

        # Table rows
        for pool in pools:
            protocol = (pool.get("project") or "Unknown")[:14]
            symbol = (pool.get("symbol") or "?")[:11]
            chain = (pool.get("chain") or "?")[:11]
            tvl = pool.get("tvlUsd", 0)
            apy = pool.get("apy") or pool.get("total_apy") or 0
            risk = pool.get("risk_level", "?")[:8]
            score = pool.get("risk_score", 0)

            # Format TVL
            if tvl >= 1e9:
                tvl_str = f"${tvl / 1e9:.1f}B"
            elif tvl >= 1e6:
                tvl_str = f"${tvl / 1e6:.0f}M"
            elif tvl >= 1e3:
                tvl_str = f"${tvl / 1e3:.0f}K"
            else:
                tvl_str = f"${tvl:.0f}"

            row = f"  {protocol:<15} {symbol:<12} {chain:<12} {tvl_str:>10} {apy:>7.2f}% {risk:>8} {score:>6.1f}"
            lines.append(row)

        lines.append("-" * 78)

        # Detailed breakdown if requested
        if detailed and pools:
            lines.append("")
            lines.append("  APY BREAKDOWN (Top Result)")
            lines.append("-" * 78)

            top = pools[0]
            base_apy = top.get("base_apy") or top.get("apyBase") or 0
            reward_apy = top.get("reward_apy") or top.get("apyReward") or 0
            total_apy = top.get("total_apy") or top.get("apy") or 0
            il_risk = top.get("il_risk", "Unknown")
            reward_tokens = top.get("rewardTokens", [])

            lines.append(f"  Base APY:     {base_apy:.2f}%")
            if reward_apy > 0:
                # Filter out None values from reward tokens
                valid_tokens = [t for t in (reward_tokens or [])[:3] if t]
                tokens_str = " + ".join(valid_tokens) if valid_tokens else "rewards"
                lines.append(f"  Reward APY:   {reward_apy:.2f}% ({tokens_str})")
            lines.append(f"  Total APY:    {total_apy:.2f}%")
            lines.append(f"  IL Risk:      {il_risk.title()}")

            # Risk factors
            risk_factors = top.get("risk_factors", [])
            if risk_factors:
                lines.append("")
                lines.append("  Risk Factors:")
                for factor in risk_factors[:5]:
                    lines.append(f"    • {factor}")

        lines.append("=" * 78)

        return "\n".join(lines)

    def _format_json(self, pools: List[Dict[str, Any]]) -> str:
        """Format as JSON.

        Args:
            pools: Pool data

        Returns:
            JSON string
        """
        output = {"timestamp": self.timestamp, "count": len(pools), "pools": []}

        for pool in pools:
            # Clean pool data for JSON output
            clean_pool = {
                "protocol": pool.get("project"),
                "pool": pool.get("pool"),
                "symbol": pool.get("symbol"),
                "chain": pool.get("chain"),
                "tvl_usd": pool.get("tvlUsd"),
                "apy": {
                    "base": pool.get("apyBase") or pool.get("base_apy") or 0,
                    "reward": pool.get("apyReward") or pool.get("reward_apy") or 0,
                    "total": pool.get("apy") or pool.get("total_apy") or 0,
                },
                "risk": {
                    "score": pool.get("risk_score"),
                    "level": pool.get("risk_level"),
                    "il_risk": pool.get("il_risk"),
                    "factors": pool.get("risk_factors", []),
                },
                "audited": pool.get("audited", False),
                "auditors": pool.get("auditors", []),
                "reward_tokens": pool.get("rewardTokens", []),
            }
            output["pools"].append(clean_pool)

        return json.dumps(output, indent=2)

    def _format_csv(self, pools: List[Dict[str, Any]]) -> str:
        """Format as CSV.

        Args:
            pools: Pool data

        Returns:
            CSV string
        """
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(
            [
                "Protocol",
                "Pool",
                "Symbol",
                "Chain",
                "TVL (USD)",
                "Base APY",
                "Reward APY",
                "Total APY",
                "Risk Score",
                "Risk Level",
                "IL Risk",
                "Audited",
                "Reward Tokens",
            ]
        )

        # Data rows
        for pool in pools:
            writer.writerow(
                [
                    pool.get("project", ""),
                    pool.get("pool", ""),
                    pool.get("symbol", ""),
                    pool.get("chain", ""),
                    pool.get("tvlUsd", 0),
                    pool.get("apyBase") or pool.get("base_apy") or 0,
                    pool.get("apyReward") or pool.get("reward_apy") or 0,
                    pool.get("apy") or pool.get("total_apy") or 0,
                    pool.get("risk_score", ""),
                    pool.get("risk_level", ""),
                    pool.get("il_risk", ""),
                    "Yes" if pool.get("audited") else "No",
                    ", ".join(t for t in (pool.get("rewardTokens") or []) if t),
                ]
            )

        return output.getvalue()

    def format_pool_detail(self, pool: Dict[str, Any]) -> str:
        """Format detailed view for a single pool.

        Args:
            pool: Pool data dictionary

        Returns:
            Formatted detail string
        """
        lines = []
        lines.append("=" * 78)
        lines.append(f"  POOL ANALYSIS: {pool.get('project', 'Unknown')} - {pool.get('symbol', '?')}")
        lines.append("=" * 78)
        lines.append("")

        # Basic Info
        lines.append("  BASIC INFORMATION")
        lines.append("-" * 78)
        lines.append(f"  Protocol:     {pool.get('project', 'Unknown')}")
        lines.append(f"  Pool:         {pool.get('symbol', 'Unknown')}")
        lines.append(f"  Chain:        {pool.get('chain', 'Unknown')}")
        lines.append(f"  Pool ID:      {pool.get('pool', 'N/A')}")
        lines.append("")

        # TVL
        tvl = pool.get("tvlUsd", 0)
        if tvl >= 1e9:
            tvl_str = f"${tvl / 1e9:.2f}B"
        elif tvl >= 1e6:
            tvl_str = f"${tvl / 1e6:.2f}M"
        else:
            tvl_str = f"${tvl:,.0f}"
        lines.append(f"  TVL:          {tvl_str}")
        lines.append("")

        # APY Breakdown
        lines.append("  APY BREAKDOWN")
        lines.append("-" * 78)
        base_apy = pool.get("apyBase") or pool.get("base_apy") or 0
        reward_apy = pool.get("apyReward") or pool.get("reward_apy") or 0
        total_apy = pool.get("apy") or pool.get("total_apy") or 0

        lines.append(f"  Base APY:       {base_apy:>8.2f}%")
        lines.append(f"  Reward APY:     {reward_apy:>8.2f}%")
        lines.append(f"  Total APY:      {total_apy:>8.2f}%")

        reward_tokens = pool.get("rewardTokens", [])
        if reward_tokens:
            lines.append(f"  Reward Tokens:  {', '.join(reward_tokens)}")
        lines.append("")

        # Risk Assessment
        lines.append("  RISK ASSESSMENT")
        lines.append("-" * 78)
        lines.append(f"  Risk Score:     {pool.get('risk_score', 'N/A')}/10")
        lines.append(f"  Risk Level:     {pool.get('risk_level', 'Unknown')}")
        lines.append(f"  IL Risk:        {pool.get('il_risk', 'Unknown').title()}")
        lines.append(f"  Audited:        {'Yes' if pool.get('audited') else 'No'}")

        auditors = pool.get("auditors", [])
        if auditors:
            lines.append(f"  Auditors:       {', '.join(auditors)}")
        lines.append("")

        # Risk Factors
        risk_factors = pool.get("risk_factors", [])
        if risk_factors:
            lines.append("  RISK FACTORS")
            lines.append("-" * 78)
            for factor in risk_factors:
                lines.append(f"  • {factor}")
            lines.append("")

        # Earnings Projection
        lines.append("  EARNINGS PROJECTION (Example: $10,000 deposit)")
        lines.append("-" * 78)
        principal = 10000
        apy = total_apy / 100
        daily = principal * apy / 365
        monthly = principal * apy / 12
        yearly = principal * apy

        lines.append(f"  Daily:          ${daily:>10.2f}")
        lines.append(f"  Monthly:        ${monthly:>10.2f}")
        lines.append(f"  Yearly:         ${yearly:>10.2f}")

        lines.append("=" * 78)

        return "\n".join(lines)

    def format_comparison(self, pools: List[Dict[str, Any]]) -> str:
        """Format comparison view for multiple pools.

        Args:
            pools: List of pools to compare

        Returns:
            Formatted comparison string
        """
        lines = []
        lines.append("=" * 78)
        lines.append(f"  PROTOCOL COMPARISON{' ' * 36}{self.timestamp}")
        lines.append("=" * 78)
        lines.append("")

        if len(pools) < 2:
            lines.append("  Need at least 2 pools to compare.")
            lines.append("=" * 78)
            return "\n".join(lines)

        # Comparison table
        lines.append("  SIDE-BY-SIDE COMPARISON")
        lines.append("-" * 78)

        # Get max values for highlighting
        max_apy = max(p.get("apy") or p.get("total_apy") or 0 for p in pools)
        max_tvl = max(p.get("tvlUsd", 0) for p in pools)
        max_risk = max(p.get("risk_score", 0) for p in pools)

        for pool in pools:
            protocol = pool.get("project", "Unknown")
            symbol = pool.get("symbol", "?")
            apy = pool.get("apy") or pool.get("total_apy") or 0
            tvl = pool.get("tvlUsd", 0)
            risk = pool.get("risk_score", 0)

            # Format TVL
            if tvl >= 1e9:
                tvl_str = f"${tvl / 1e9:.1f}B"
            elif tvl >= 1e6:
                tvl_str = f"${tvl / 1e6:.0f}M"
            else:
                tvl_str = f"${tvl / 1e3:.0f}K"

            # Markers for best values
            apy_mark = " ★" if apy == max_apy else ""
            tvl_mark = " ★" if tvl == max_tvl else ""
            risk_mark = " ★" if risk == max_risk else ""

            lines.append(f"  {protocol} ({symbol})")
            lines.append(f"    APY:        {apy:>7.2f}%{apy_mark}")
            lines.append(f"    TVL:        {tvl_str:>10}{tvl_mark}")
            lines.append(f"    Risk Score: {risk:>7.1f}/10{risk_mark}")
            lines.append("")

        lines.append("  ★ = Best in category")
        lines.append("=" * 78)

        return "\n".join(lines)


def main():
    """CLI entry point for testing."""
    formatter = YieldFormatter()

    # Test data
    pools = [
        {
            "project": "aave-v3",
            "symbol": "USDC",
            "chain": "Ethereum",
            "pool": "aave-v3-usdc-ethereum",
            "tvlUsd": 2100000000,
            "apyBase": 3.5,
            "apyReward": 0.7,
            "apy": 4.2,
            "risk_score": 9.2,
            "risk_level": "Low",
            "il_risk": "none",
            "audited": True,
            "auditors": ["OpenZeppelin", "Trail of Bits"],
            "rewardTokens": ["AAVE"],
            "risk_factors": ["Reward token volatility"],
        },
        {
            "project": "convex-finance",
            "symbol": "cvxCRV",
            "chain": "Ethereum",
            "pool": "convex-cvxcrv",
            "tvlUsd": 450000000,
            "apyBase": 4.5,
            "apyReward": 8.0,
            "apy": 12.5,
            "risk_score": 8.5,
            "risk_level": "Low",
            "il_risk": "none",
            "audited": True,
            "auditors": ["MixBytes"],
            "rewardTokens": ["CRV", "CVX"],
            "risk_factors": ["Reward token volatility", "Smart contract dependency"],
        },
    ]

    print("TABLE FORMAT:")
    print(formatter.format(pools, "table", detailed=True))

    print("\n\nJSON FORMAT (first 50 chars):")
    json_out = formatter.format(pools, "json")
    print(json_out[:500] + "...")

    print("\n\nCOMPARISON VIEW:")
    print(formatter.format_comparison(pools))


if __name__ == "__main__":
    main()
