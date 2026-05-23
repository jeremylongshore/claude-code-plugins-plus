#!/usr/bin/env python3
"""
Whale Alert Formatters

Format whale transaction data for various outputs.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 1.0.0
License: MIT
"""

import json
from datetime import datetime
from typing import Dict, Any, List


def format_usd(value: float) -> str:
    """Format USD value with appropriate suffix."""
    if value >= 1e9:
        return f"${value / 1e9:.2f}B"
    elif value >= 1e6:
        return f"${value / 1e6:.2f}M"
    elif value >= 1e3:
        return f"${value / 1e3:.1f}K"
    else:
        return f"${value:,.0f}"


def format_amount(amount: float, symbol: str) -> str:
    """Format token amount."""
    if amount >= 1e6:
        return f"{amount / 1e6:.2f}M {symbol}"
    elif amount >= 1e3:
        return f"{amount / 1e3:.1f}K {symbol}"
    else:
        return f"{amount:,.2f} {symbol}"


def format_address(address: str, length: int = 12) -> str:
    """Truncate address for display."""
    if len(address) <= length:
        return address
    half = (length - 3) // 2
    return f"{address[:half]}...{address[-half:]}"


def format_time_ago(timestamp: int) -> str:
    """Format timestamp as relative time.

    Note: Uses UTC time for consistency across timezones.
    """
    now = datetime.utcnow().timestamp()
    diff = now - timestamp

    if diff < 60:
        return f"{int(diff)}s ago"
    elif diff < 3600:
        return f"{int(diff / 60)}m ago"
    elif diff < 86400:
        return f"{int(diff / 3600)}h ago"
    else:
        return f"{int(diff / 86400)}d ago"


def format_timestamp(timestamp: int) -> str:
    """Format timestamp as UTC datetime string."""
    return datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S UTC")


def format_whale_table(transactions: List[Any], show_addresses: bool = False) -> str:
    """Format whale transactions as ASCII table.

    Args:
        transactions: List of WhaleTransaction objects
        show_addresses: Include full addresses in output

    Returns:
        Formatted table string
    """
    if not transactions:
        return "No whale transactions found."

    lines = [
        "",
        "WHALE ALERT - Recent Large Transactions",
        "=" * 100,
    ]

    if show_addresses:
        lines.append(f"{'Time':<12} {'Chain':<10} {'Amount':<20} {'USD Value':<14} {'From':<20} {'To':<20}")
    else:
        lines.append(
            f"{'Time':<12} {'Chain':<10} {'Amount':<20} {'USD Value':<14} {'From':<18} {'To':<18} {'Type':<10}"
        )

    lines.append("-" * 100)

    for tx in transactions:
        time_str = format_time_ago(tx.timestamp)
        chain = tx.blockchain[:8]
        amount_str = format_amount(tx.amount, tx.symbol)
        usd_str = format_usd(tx.amount_usd)

        # Label or address
        from_label = tx.from_owner if tx.from_owner else format_address(tx.from_address, 16)
        to_label = tx.to_owner if tx.to_owner else format_address(tx.to_address, 16)

        tx_type = tx.transaction_type[:8] if tx.transaction_type else "transfer"

        if show_addresses:
            lines.append(f"{time_str:<12} {chain:<10} {amount_str:<20} {usd_str:<14} {from_label:<20} {to_label:<20}")
        else:
            lines.append(
                f"{time_str:<12} {chain:<10} {amount_str:<20} {usd_str:<14} {from_label:<18} {to_label:<18} {tx_type:<10}"
            )

    lines.append("-" * 100)
    lines.append(f"Total: {len(transactions)} transactions")

    return "\n".join(lines)


def format_whale_alert(transaction: Any) -> str:
    """Format single transaction as alert message.

    Args:
        transaction: WhaleTransaction object

    Returns:
        Alert-style formatted string
    """
    time_str = format_timestamp(transaction.timestamp)
    amount_str = format_amount(transaction.amount, transaction.symbol)
    usd_str = format_usd(transaction.amount_usd)

    from_label = transaction.from_owner or format_address(transaction.from_address)
    to_label = transaction.to_owner or format_address(transaction.to_address)

    # Determine emoji based on transaction type
    if transaction.to_owner_type == "exchange":
        emoji = "🔴"  # Selling pressure
        direction = "DEPOSIT"
    elif transaction.from_owner_type == "exchange":
        emoji = "🟢"  # Buying/withdrawal
        direction = "WITHDRAWAL"
    else:
        emoji = "🐋"
        direction = "TRANSFER"

    lines = [
        f"{emoji} WHALE {direction}",
        f"   {amount_str} ({usd_str})",
        f"   {from_label} → {to_label}",
        f"   Chain: {transaction.blockchain.upper()} | {time_str}",
        f"   TX: {format_address(transaction.tx_hash, 20)}",
    ]

    return "\n".join(lines)


def format_exchange_flow(inflows: List[Dict[str, Any]], outflows: List[Dict[str, Any]]) -> str:
    """Format exchange inflow/outflow summary.

    Args:
        inflows: List of inflow transactions
        outflows: List of outflow transactions

    Returns:
        Formatted flow summary
    """
    total_inflow = sum(tx.get("amount_usd", 0) for tx in inflows)
    total_outflow = sum(tx.get("amount_usd", 0) for tx in outflows)
    net_flow = total_inflow - total_outflow

    lines = [
        "",
        "EXCHANGE FLOW ANALYSIS",
        "=" * 50,
        f"Inflows:  {format_usd(total_inflow):>14} ({len(inflows)} txns)",
        f"Outflows: {format_usd(total_outflow):>14} ({len(outflows)} txns)",
        "-" * 50,
    ]

    if net_flow > 0:
        lines.append(f"Net Flow: {format_usd(net_flow):>14} (SELLING PRESSURE)")
    elif net_flow < 0:
        lines.append(f"Net Flow: {format_usd(abs(net_flow)):>14} (BUYING PRESSURE)")
    else:
        lines.append(f"Net Flow: {format_usd(0):>14} (NEUTRAL)")

    lines.append("=" * 50)

    return "\n".join(lines)


def format_watchlist(wallets: List[Any]) -> str:
    """Format watchlist display.

    Args:
        wallets: List of WalletLabel objects

    Returns:
        Formatted watchlist
    """
    if not wallets:
        return "Watchlist is empty. Add wallets with: --watch <address> --name <name>"

    lines = [
        "",
        "WHALE WATCHLIST",
        "=" * 80,
        f"{'Name':<25} {'Address':<45} {'Chain':<10}",
        "-" * 80,
    ]

    for wallet in wallets:
        name = wallet.name[:23]
        address = format_address(wallet.address, 42)
        chain = wallet.chain[:8]
        lines.append(f"{name:<25} {address:<45} {chain:<10}")

    lines.append("-" * 80)
    lines.append(f"Total: {len(wallets)} watched wallets")

    return "\n".join(lines)


def format_transaction_detail(tx: Any, label_info: Dict = None) -> str:
    """Format detailed transaction view.

    Args:
        tx: WhaleTransaction object
        label_info: Additional label info

    Returns:
        Detailed formatted output
    """
    lines = [
        "",
        "TRANSACTION DETAIL",
        "=" * 70,
        f"TX Hash:    {tx.tx_hash}",
        f"Chain:      {tx.blockchain.upper()}",
        f"Time:       {format_timestamp(tx.timestamp)}",
        "",
        f"Amount:     {format_amount(tx.amount, tx.symbol)}",
        f"USD Value:  {format_usd(tx.amount_usd)}",
        f"Type:       {tx.transaction_type}",
        "",
        "FROM:",
        f"  Address:  {tx.from_address}",
        f"  Label:    {tx.from_owner or 'Unknown'}",
        f"  Type:     {tx.from_owner_type or 'Unknown'}",
        "",
        "TO:",
        f"  Address:  {tx.to_address}",
        f"  Label:    {tx.to_owner or 'Unknown'}",
        f"  Type:     {tx.to_owner_type or 'Unknown'}",
        "=" * 70,
    ]

    return "\n".join(lines)


def format_json(data: Any) -> str:
    """Format data as JSON."""
    if hasattr(data, "__iter__") and not isinstance(data, (str, dict)):
        # Handle list of dataclass objects
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


def main():
    """CLI entry point for testing."""
    # Test formatting functions
    print("=== Format Tests ===")
    print(f"USD: {format_usd(1234567890)}")
    print(f"Amount: {format_amount(5000000, 'ETH')}")
    print(f"Address: {format_address('0x1234567890abcdef1234567890abcdef12345678')}")

    import time

    print(f"Time ago: {format_time_ago(int(time.time()) - 3600)}")


if __name__ == "__main__":
    main()
