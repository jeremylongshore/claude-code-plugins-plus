#!/usr/bin/env python3
"""
Mempool Analyzer Formatters

Format mempool data for various outputs.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 1.0.0
License: MIT
"""

import json
from datetime import datetime
from typing import Any, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from tx_decoder import TransactionDecoder


def format_gwei(wei: int) -> str:
    """Format wei as gwei."""
    gwei = wei / 10**9
    return f"{gwei:.1f} gwei"


def format_eth(wei: int) -> str:
    """Format wei as ETH."""
    eth = wei / 10**18
    if eth >= 1:
        return f"{eth:.4f} ETH"
    else:
        return f"{eth:.6f} ETH"


def format_usd(value: float) -> str:
    """Format USD value."""
    if value >= 1e6:
        return f"${value / 1e6:.2f}M"
    elif value >= 1e3:
        return f"${value / 1e3:.1f}K"
    else:
        return f"${value:,.2f}"


def format_address(address: str, length: int = 12) -> str:
    """Truncate address for display."""
    if not address:
        return "N/A"
    if len(address) <= length:
        return address
    half = (length - 3) // 2
    return f"{address[:half]}...{address[-half:]}"


def format_pending_tx_table(
    transactions: List[Any],
    eth_price: float = 3000.0,
    decoder: Optional["TransactionDecoder"] = None,
) -> str:
    """Format pending transactions as table.

    Args:
        transactions: List of PendingTransaction objects
        eth_price: Current ETH price for USD conversion
        decoder: Optional TransactionDecoder instance (created if not provided)

    Returns:
        Formatted table string
    """
    if not transactions:
        return "No pending transactions."

    lines = [
        "",
        "PENDING TRANSACTIONS",
        "=" * 100,
        f"{'Hash':<18} {'From':<14} {'To':<14} {'Value':<12} {'Gas Price':<12} {'Gas':<10} {'Type':<12}",
        "-" * 100,
    ]

    # Create decoder only if not provided
    if decoder is None:
        from tx_decoder import TransactionDecoder

        decoder = TransactionDecoder()

    for tx in transactions[:50]:
        tx_hash = format_address(tx.hash, 16)
        from_addr = format_address(tx.from_address, 12)
        to_addr = format_address(tx.to_address or "Contract", 12)

        # Value
        if tx.value > 0:
            value_str = format_eth(tx.value)
        else:
            value_str = "0"

        gas_price_str = format_gwei(tx.gas_price)
        gas_str = f"{tx.gas:,}"

        # Decode type
        decoded = decoder.decode_input(tx.input_data, tx.to_address)
        tx_type = decoded.method_type[:10]

        lines.append(
            f"{tx_hash:<18} {from_addr:<14} {to_addr:<14} {value_str:<12} {gas_price_str:<12} {gas_str:<10} {tx_type:<12}"
        )

    lines.append("-" * 100)
    lines.append(f"Showing {min(len(transactions), 50)} of {len(transactions)} pending transactions")

    return "\n".join(lines)


def format_pending_swaps_table(swaps: List[Any]) -> str:
    """Format pending swaps as table.

    Args:
        swaps: List of PendingSwap objects

    Returns:
        Formatted table string
    """
    if not swaps:
        return "No pending swaps detected."

    lines = [
        "",
        "PENDING DEX SWAPS",
        "=" * 90,
        f"{'Hash':<18} {'DEX':<20} {'Amount In':<16} {'Gas Price':<12} {'From':<14}",
        "-" * 90,
    ]

    for swap in swaps[:30]:
        tx_hash = format_address(swap.tx_hash, 16)
        dex = swap.dex[:18] if swap.dex else "Unknown"

        if swap.amount_in:
            amount = format_eth(swap.amount_in)
        else:
            amount = "Unknown"

        gas_price = format_gwei(swap.gas_price)
        from_addr = format_address(swap.from_address, 12)

        lines.append(f"{tx_hash:<18} {dex:<20} {amount:<16} {gas_price:<12} {from_addr:<14}")

    lines.append("-" * 90)
    lines.append(f"Total: {len(swaps)} pending swaps")

    return "\n".join(lines)


def format_mempool_summary(pending_count: int, gas_info: Any, swap_count: int, opportunities: int) -> str:
    """Format mempool summary.

    Args:
        pending_count: Number of pending transactions
        gas_info: GasInfo object
        swap_count: Number of pending swaps
        opportunities: Number of MEV opportunities

    Returns:
        Formatted summary string
    """
    lines = [
        "",
        "MEMPOOL SUMMARY",
        "=" * 50,
        f"Pending Transactions: {pending_count:,}",
        f"Pending Swaps:        {swap_count}",
        f"MEV Opportunities:    {opportunities}",
        "",
        "Gas Prices:",
        f"  Base Fee:     {format_gwei(gas_info.base_fee)}",
        f"  Priority Fee: {format_gwei(gas_info.priority_fee)}",
        f"  Gas Price:    {format_gwei(gas_info.gas_price)}",
        "=" * 50,
    ]

    return "\n".join(lines)


def format_json(data: Any) -> str:
    """Format data as JSON."""
    if hasattr(data, "__iter__") and not isinstance(data, (str, dict)):
        serialized = []
        for item in data:
            if hasattr(item, "__dict__"):
                serialized.append(vars(item))
            else:
                serialized.append(item)
        return json.dumps(serialized, indent=2, default=str)
    elif hasattr(data, "__dict__"):
        return json.dumps(vars(data), indent=2, default=str)
    else:
        return json.dumps(data, indent=2, default=str)


def format_stream_alert(
    tx: Any,
    decoder: Optional["TransactionDecoder"] = None,
) -> str:
    """Format single transaction for stream output.

    Args:
        tx: Transaction object
        decoder: Optional TransactionDecoder instance (created if not provided)

    Returns:
        Single-line alert string
    """
    timestamp = datetime.now().strftime("%H:%M:%S")
    tx_hash = format_address(tx.hash, 12)
    gas_price = tx.gas_price / 10**9

    # Create decoder only if not provided
    if decoder is None:
        from tx_decoder import TransactionDecoder

        decoder = TransactionDecoder()
    decoded = decoder.decode_input(tx.input_data, tx.to_address)

    if tx.value > 0:
        value = format_eth(tx.value)
        return f"[{timestamp}] {tx_hash} | {gas_price:.1f} gwei | {value} | {decoded.method_type}"
    else:
        return f"[{timestamp}] {tx_hash} | {gas_price:.1f} gwei | {decoded.method_name}"


def main():
    """CLI entry point for testing."""
    # Test formatting functions
    print("=== Format Tests ===")
    print(f"Gwei: {format_gwei(30 * 10**9)}")
    print(f"ETH: {format_eth(1.5 * 10**18)}")
    print(f"USD: {format_usd(1234567)}")
    print(f"Address: {format_address('0x1234567890abcdef1234567890abcdef12345678')}")


if __name__ == "__main__":
    main()
