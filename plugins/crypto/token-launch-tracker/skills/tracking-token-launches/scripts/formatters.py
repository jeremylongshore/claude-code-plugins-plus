#!/usr/bin/env python3
"""
Token Launch Formatters

Format launch data for various outputs.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 1.0.0
License: MIT
"""

import json
from datetime import datetime
from typing import List, Dict, Any


def format_timestamp(ts: int) -> str:
    """Format Unix timestamp."""
    dt = datetime.fromtimestamp(ts)
    return dt.strftime("%Y-%m-%d %H:%M")


def format_age(ts: int) -> str:
    """Format time ago."""
    now = int(datetime.now().timestamp())
    diff = now - ts

    if diff < 60:
        return f"{diff}s ago"
    elif diff < 3600:
        return f"{diff // 60}m ago"
    elif diff < 86400:
        return f"{diff // 3600}h ago"
    else:
        return f"{diff // 86400}d ago"


def format_address(address: str, length: int = 10) -> str:
    """Format address with ellipsis."""
    if not address:
        return "N/A"
    if len(address) <= length * 2:
        return address
    return f"{address[:length]}...{address[-4:]}"


def format_risk_badge(score: int) -> str:
    """Format risk score as badge."""
    if score >= 70:
        return f"[HIGH RISK: {score}]"
    elif score >= 40:
        return f"[MEDIUM: {score}]"
    elif score >= 20:
        return f"[LOW: {score}]"
    else:
        return f"[OK: {score}]"


def format_supply(supply: int, decimals: int) -> str:
    """Format token supply."""
    value = supply / (10**decimals)

    if value >= 1e12:
        return f"{value / 1e12:.2f}T"
    elif value >= 1e9:
        return f"{value / 1e9:.2f}B"
    elif value >= 1e6:
        return f"{value / 1e6:.2f}M"
    elif value >= 1e3:
        return f"{value / 1e3:.2f}K"
    else:
        return f"{value:.2f}"


def format_new_pairs_table(pairs: List[Any], token_infos: Dict[str, Any], analyses: Dict[str, Any]) -> str:
    """Format new pairs as table.

    Args:
        pairs: List of PairCreated events
        token_infos: Dict of address -> TokenInfo
        analyses: Dict of address -> ContractAnalysis

    Returns:
        Formatted table string
    """
    lines = [
        "",
        "NEW TOKEN LAUNCHES",
        "=" * 90,
        f"{'Time':<12} {'Token':<20} {'DEX':<15} {'Chain':<10} {'Risk':<15} {'Pair':<18}",
        "-" * 90,
    ]

    for pair in pairs:
        # Get new token address (not the base token)
        new_token = pair.token0  # Simplified - should use identify_new_token

        info = token_infos.get(new_token)
        analysis = analyses.get(new_token)

        token_str = f"{info.symbol if info else '???'}" if info else "Unknown"
        if len(token_str) > 18:
            token_str = token_str[:15] + "..."

        risk_str = format_risk_badge(analysis.risk_score) if analysis else "[N/A]"
        pair_str = format_address(pair.pair_address, 8)
        time_str = format_age(pair.timestamp)

        lines.append(f"{time_str:<12} {token_str:<20} {pair.dex:<15} {pair.chain:<10} {risk_str:<15} {pair_str:<18}")

    lines.append("=" * 90)
    lines.append(f"Total: {len(pairs)} new pairs")

    return "\n".join(lines)


def format_launch_detail(pair: Any, token_info: Any, analysis: Any, chain_config: Any) -> str:
    """Format detailed launch info.

    Args:
        pair: PairCreated event
        token_info: TokenInfo object
        analysis: ContractAnalysis object
        chain_config: ChainConfig object

    Returns:
        Formatted detail string
    """
    lines = [
        "",
        f"TOKEN LAUNCH: {token_info.symbol if token_info else 'Unknown'}",
        "=" * 60,
        f"Name:         {token_info.name if token_info else 'Unknown'}",
        f"Symbol:       {token_info.symbol if token_info else '???'}",
        f"Address:      {pair.token0}",
        f"Pair:         {pair.pair_address}",
        "",
        "LAUNCH INFO",
        "-" * 60,
        f"DEX:          {pair.dex}",
        f"Chain:        {pair.chain.upper()}",
        f"Block:        {pair.block_number:,}",
        f"Time:         {format_timestamp(pair.timestamp)} ({format_age(pair.timestamp)})",
        f"Tx:           {pair.tx_hash}",
        "",
    ]

    if token_info:
        lines.extend(
            [
                "TOKEN INFO",
                "-" * 60,
                f"Decimals:     {token_info.decimals}",
                f"Total Supply: {format_supply(token_info.total_supply, token_info.decimals)}",
                f"Owner:        {format_address(token_info.owner) if token_info.owner else 'None'}",
                f"Verified:     {'Yes' if token_info.is_verified else 'No'}",
                "",
            ]
        )

    if analysis:
        lines.extend(
            [
                "RISK ANALYSIS",
                "-" * 60,
                f"Risk Score:   {analysis.risk_score}/100 {format_risk_badge(analysis.risk_score)}",
                f"Is Proxy:     {'Yes' if analysis.is_proxy else 'No'}",
                f"Ownership:    {'Renounced' if analysis.ownership_renounced else 'Active'}",
                "",
                "Indicators:",
            ]
        )

        for ind in analysis.indicators:
            severity_marker = {
                "high": "!!",
                "medium": "! ",
                "low": ". ",
                "info": "  ",
            }.get(ind.severity, "  ")
            lines.append(f"  {severity_marker} {ind.name}: {ind.description}")

    lines.append("")
    lines.append("LINKS")
    lines.append("-" * 60)
    lines.append(f"Explorer:     {chain_config.explorer_url}/address/{pair.token0}")
    lines.append(f"DEXScreener:  https://dexscreener.com/{pair.chain}/{pair.pair_address}")

    lines.append("=" * 60)

    return "\n".join(lines)


def format_chain_summary(pairs_by_chain: Dict[str, int]) -> str:
    """Format summary by chain.

    Args:
        pairs_by_chain: Dict of chain -> count

    Returns:
        Formatted summary
    """
    lines = [
        "",
        "LAUNCHES BY CHAIN",
        "=" * 40,
    ]

    total = 0
    for chain, count in sorted(pairs_by_chain.items(), key=lambda x: -x[1]):
        lines.append(f"  {chain.upper():<15} {count:>10}")
        total += count

    lines.append("-" * 40)
    lines.append(f"  {'TOTAL':<15} {total:>10}")
    lines.append("=" * 40)

    return "\n".join(lines)


def format_dex_summary(pairs_by_dex: Dict[str, int]) -> str:
    """Format summary by DEX.

    Args:
        pairs_by_dex: Dict of dex -> count

    Returns:
        Formatted summary
    """
    lines = [
        "",
        "LAUNCHES BY DEX",
        "=" * 40,
    ]

    for dex, count in sorted(pairs_by_dex.items(), key=lambda x: -x[1]):
        lines.append(f"  {dex:<25} {count:>10}")

    lines.append("=" * 40)

    return "\n".join(lines)


def format_json(data: Any) -> str:
    """Format data as JSON."""
    if hasattr(data, "__dict__"):
        return json.dumps(vars(data), indent=2, default=str)
    elif isinstance(data, list):
        return json.dumps([vars(x) if hasattr(x, "__dict__") else x for x in data], indent=2, default=str)
    else:
        return json.dumps(data, indent=2, default=str)


def main():
    """CLI entry point for testing."""
    print("=== Formatter Tests ===")
    print(f"Timestamp: {format_timestamp(1705784400)}")
    print(f"Age: {format_age(1705784400)}")
    print(f"Address: {format_address('0x1234567890abcdef1234567890abcdef12345678')}")
    print(f"Risk: {format_risk_badge(75)}")
    print(f"Risk: {format_risk_badge(45)}")
    print(f"Risk: {format_risk_badge(15)}")
    print(f"Supply: {format_supply(1000000000000000000000000, 18)}")


if __name__ == "__main__":
    main()
