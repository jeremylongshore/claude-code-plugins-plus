#!/usr/bin/env python3
"""
Bridge Data Formatters

Format bridge data for various outputs.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 1.0.0
License: MIT
"""

import json
from datetime import datetime
from typing import List, Any, Optional
from decimal import Decimal

from bridge_fetcher import BridgeInfo, TVLData, ChainVolume
from protocol_adapters import FeeEstimate, TxStatus


def format_number(value: float, decimals: int = 2) -> str:
    """Format large numbers with suffixes."""
    if value >= 1e12:
        return f"${value / 1e12:.{decimals}f}T"
    elif value >= 1e9:
        return f"${value / 1e9:.{decimals}f}B"
    elif value >= 1e6:
        return f"${value / 1e6:.{decimals}f}M"
    elif value >= 1e3:
        return f"${value / 1e3:.{decimals}f}K"
    else:
        return f"${value:,.{decimals}f}"


def format_percent(value: float) -> str:
    """Format percentage."""
    if value > 0:
        return f"+{value:.2f}%"
    else:
        return f"{value:.2f}%"


def format_time(minutes: int) -> str:
    """Format time duration."""
    if minutes < 1:
        return "<1 min"
    elif minutes < 60:
        return f"~{minutes} min"
    else:
        hours = minutes // 60
        return f"~{hours}h {minutes % 60}m"


def format_bridges_table(bridges: List[BridgeInfo], limit: int = 20) -> str:
    """Format bridges as table.

    Args:
        bridges: List of BridgeInfo
        limit: Maximum rows

    Returns:
        Formatted table string
    """
    lines = [
        "",
        "CROSS-CHAIN BRIDGES",
        "=" * 90,
        f"{'Rank':<6} {'Bridge':<25} {'24h Volume':<15} {'Chains':<10} {'Change':<10}",
        "-" * 90,
    ]

    for i, bridge in enumerate(bridges[:limit], 1):
        vol_str = format_number(bridge.volume_prev_day)
        chain_count = len(set(bridge.chains + bridge.destination_chains))

        # Calculate change
        if bridge.volume_prev2_day > 0:
            change = (bridge.volume_prev_day - bridge.volume_prev2_day) / bridge.volume_prev2_day * 100
            change_str = format_percent(change)
        else:
            change_str = "N/A"

        name = bridge.display_name
        if len(name) > 23:
            name = name[:20] + "..."

        lines.append(f"{i:<6} {name:<25} {vol_str:<15} {chain_count:<10} {change_str:<10}")

    lines.append("=" * 90)
    lines.append(f"Total bridges: {len(bridges)}")

    return "\n".join(lines)


def format_tvl_table(tvl_data: List[tuple]) -> str:
    """Format TVL data as table.

    Args:
        tvl_data: List of (bridge_name, TVLData) tuples

    Returns:
        Formatted table string
    """
    lines = [
        "",
        "BRIDGE TVL RANKINGS",
        "=" * 80,
        f"{'Rank':<6} {'Bridge':<25} {'Total TVL':<20} {'Chains':<10}",
        "-" * 80,
    ]

    # Sort by TVL
    tvl_data.sort(key=lambda x: x[1].total_tvl if x[1] else 0, reverse=True)

    for i, (name, tvl) in enumerate(tvl_data[:20], 1):
        if not tvl:
            continue

        tvl_str = format_number(tvl.total_tvl)
        chain_count = len(tvl.tvl_by_chain)

        if len(name) > 23:
            name = name[:20] + "..."

        lines.append(f"{i:<6} {name:<25} {tvl_str:<20} {chain_count:<10}")

    lines.append("=" * 80)

    return "\n".join(lines)


def format_bridge_detail(bridge: BridgeInfo, tvl: Optional[TVLData]) -> str:
    """Format detailed bridge info.

    Args:
        bridge: BridgeInfo object
        tvl: Optional TVLData object

    Returns:
        Formatted detail string
    """
    lines = [
        "",
        f"BRIDGE: {bridge.display_name}",
        "=" * 60,
        f"Name:         {bridge.name}",
        f"ID:           {bridge.id}",
        "",
        "VOLUME",
        "-" * 60,
        f"24h Volume:   {format_number(bridge.volume_prev_day)}",
        f"Previous 24h: {format_number(bridge.volume_prev2_day)}",
    ]

    if bridge.volume_prev2_day > 0:
        change = (bridge.volume_prev_day - bridge.volume_prev2_day) / bridge.volume_prev2_day * 100
        lines.append(f"Change:       {format_percent(change)}")

    lines.append("")
    lines.append("SUPPORTED CHAINS")
    lines.append("-" * 60)

    # Combine and deduplicate chains
    all_chains = sorted(set(bridge.chains + bridge.destination_chains))
    for i in range(0, len(all_chains), 5):
        chunk = all_chains[i : i + 5]
        lines.append(f"  {', '.join(chunk)}")

    if tvl:
        lines.append("")
        lines.append("TVL BY CHAIN")
        lines.append("-" * 60)

        for chain, amount in sorted(tvl.tvl_by_chain.items(), key=lambda x: -x[1])[:10]:
            lines.append(f"  {chain:<20} {format_number(amount)}")

        lines.append(f"  {'Total':<20} {format_number(tvl.total_tvl)}")

    lines.append("=" * 60)

    return "\n".join(lines)


def format_chain_volume_table(volumes: List[ChainVolume]) -> str:
    """Format chain volumes as table.

    Args:
        volumes: List of ChainVolume objects

    Returns:
        Formatted table string
    """
    lines = [
        "",
        "BRIDGE VOLUME BY CHAIN",
        "=" * 70,
        f"{'Chain':<20} {'24h Volume':<20} {'Net Flow':<15}",
        "-" * 70,
    ]

    # Sort by volume
    volumes.sort(key=lambda x: x.total_volume_24h, reverse=True)

    for vol in volumes:
        vol_str = format_number(vol.total_volume_24h)
        net_str = format_number(vol.net_flow_24h) if vol.net_flow_24h else "N/A"

        lines.append(f"{vol.chain:<20} {vol_str:<20} {net_str:<15}")

    lines.append("=" * 70)

    return "\n".join(lines)


def format_fee_comparison(estimates: List[FeeEstimate]) -> str:
    """Format fee comparison table.

    Args:
        estimates: List of FeeEstimate objects

    Returns:
        Formatted table string
    """
    if not estimates:
        return "No fee estimates available"

    first = estimates[0]
    lines = [
        "",
        f"BRIDGE FEE COMPARISON: {first.source_chain.upper()} → {first.dest_chain.upper()}",
        f"Amount: {first.amount} {first.token}",
        "=" * 80,
        f"{'Bridge':<20} {'Bridge Fee':<15} {'Gas (Total)':<15} {'Total Fee':<15} {'Time':<10}",
        "-" * 80,
    ]

    # Sort by total fee
    estimates.sort(key=lambda x: x.total_fee)

    for est in estimates:
        bridge_fee = f"${est.bridge_fee:.4f}"
        gas_fee = f"${est.gas_fee_source + est.gas_fee_dest:.4f}"
        total_fee = f"${est.total_fee:.4f}"
        time_str = format_time(est.estimated_time_minutes)

        lines.append(f"{est.bridge:<20} {bridge_fee:<15} {gas_fee:<15} {total_fee:<15} {time_str:<10}")

    lines.append("=" * 80)
    lines.append(f"Cheapest: {estimates[0].bridge}")
    lines.append(f"Fastest: {min(estimates, key=lambda x: x.estimated_time_minutes).bridge}")

    return "\n".join(lines)


def format_tx_status(status: TxStatus) -> str:
    """Format transaction status.

    Args:
        status: TxStatus object

    Returns:
        Formatted status string
    """
    status_icons = {
        "completed": "[OK]",
        "confirmed": "[OK]",
        "pending": "[..]",
        "failed": "[!!]",
        "not_found": "[??]",
    }

    icon = status_icons.get(status.status, "[??]")

    lines = [
        "",
        "BRIDGE TRANSACTION STATUS",
        "=" * 60,
        f"TX Hash:      {status.tx_hash}",
        f"Bridge:       {status.bridge}",
        f"Route:        {status.source_chain} → {status.dest_chain}",
        f"Status:       {icon} {status.status.upper()}",
        "",
        "CONFIRMATION",
        "-" * 60,
        f"Source Chain: {'Confirmed' if status.source_confirmed else 'Pending'}",
        f"Dest Chain:   {'Confirmed' if status.dest_confirmed else 'Pending'}",
    ]

    if status.amount:
        lines.append(f"Amount:       {status.amount} {status.token or ''}")

    if status.dest_tx_hash:
        lines.append(f"Dest TX:      {status.dest_tx_hash}")

    if status.timestamp:
        dt = datetime.fromtimestamp(status.timestamp)
        lines.append(f"Timestamp:    {dt.strftime('%Y-%m-%d %H:%M:%S')}")

    if status.estimated_completion:
        lines.append(f"Est. Complete: ~{status.estimated_completion} minutes")

    lines.append("=" * 60)

    return "\n".join(lines)


def format_chains_list(chains: List[str]) -> str:
    """Format chains list.

    Args:
        chains: List of chain names

    Returns:
        Formatted list string
    """
    lines = [
        "",
        "SUPPORTED CHAINS",
        "=" * 60,
    ]

    # Group into columns
    for i in range(0, len(chains), 4):
        chunk = chains[i : i + 4]
        lines.append("  " + "  ".join(f"{c:<15}" for c in chunk))

    lines.append("=" * 60)
    lines.append(f"Total: {len(chains)} chains")

    return "\n".join(lines)


def format_json(data: Any) -> str:
    """Format data as JSON.

    Args:
        data: Data to format

    Returns:
        JSON string
    """

    def default_serializer(obj):
        if hasattr(obj, "__dict__"):
            return vars(obj)
        elif isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        else:
            return str(obj)

    if isinstance(data, list):
        items = []
        for item in data:
            if hasattr(item, "__dict__"):
                items.append(vars(item))
            else:
                items.append(item)
        return json.dumps(items, indent=2, default=default_serializer)
    elif hasattr(data, "__dict__"):
        return json.dumps(vars(data), indent=2, default=default_serializer)
    else:
        return json.dumps(data, indent=2, default=default_serializer)


def main():
    """CLI entry point for testing."""
    print("=== Formatter Tests ===")
    print(f"Number: {format_number(1234567890)}")
    print(f"Percent: {format_percent(5.5)}")
    print(f"Time: {format_time(45)}")
    print(f"Time: {format_time(90)}")


if __name__ == "__main__":
    main()
