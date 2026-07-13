#!/usr/bin/env python3
"""
Output Formatters

Format blockchain data for console, JSON, and CSV output.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 1.0.0
License: MIT
"""

import json
import csv
import io
from datetime import datetime
from typing import Dict, Any, List


def format_timestamp(ts: int) -> str:
    """Format Unix timestamp.

    Args:
        ts: Unix timestamp

    Returns:
        Formatted datetime string
    """
    if not ts:
        return "N/A"
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


def format_value(value: float, symbol: str, decimals: int = 4) -> str:
    """Format token value.

    Args:
        value: Token amount
        symbol: Token symbol
        decimals: Decimal places

    Returns:
        Formatted string
    """
    if value >= 1_000_000:
        return f"{value / 1_000_000:.2f}M {symbol}"
    elif value >= 1_000:
        return f"{value / 1_000:.2f}K {symbol}"
    else:
        return f"{value:.{decimals}f} {symbol}"


def format_usd(value: float) -> str:
    """Format USD value.

    Args:
        value: USD amount

    Returns:
        Formatted string
    """
    if value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    elif value >= 1_000:
        return f"${value / 1_000:.2f}K"
    else:
        return f"${value:.2f}"


def truncate_hash(hash_str: str, length: int = 10) -> str:
    """Truncate hash for display.

    Args:
        hash_str: Full hash
        length: Characters to show on each end

    Returns:
        Truncated hash
    """
    if not hash_str or len(hash_str) <= length * 2 + 3:
        return hash_str or "N/A"
    return f"{hash_str[:length]}...{hash_str[-length:]}"


def truncate_address(address: str) -> str:
    """Truncate address for display.

    Args:
        address: Full address

    Returns:
        Truncated address
    """
    if not address:
        return "N/A"
    return f"{address[:6]}...{address[-4:]}"


class TransactionFormatter:
    """Format transaction data."""

    def format_table(self, tx: Dict[str, Any]) -> str:
        """Format transaction as table.

        Args:
            tx: Transaction data

        Returns:
            Formatted string
        """
        if tx.get("error"):
            return f"Error: {tx['error']}"

        status_icon = "✓" if tx.get("status") == "success" else "✗"

        lines = [
            "╔══════════════════════════════════════════════════════════════════════╗",
            "║  Transaction Details                                                  ║",
            "╠══════════════════════════════════════════════════════════════════════╣",
            f"║  Hash:     {tx.get('hash', 'N/A')[:50]:50} ║",
            f"║  Chain:    {tx.get('chain', 'N/A'):54} ║",
            f"║  Status:   {status_icon} {tx.get('status', 'N/A'):52} ║",
            f"║  Block:    {str(tx.get('block_number', 'N/A')):54} ║",
            "╠══════════════════════════════════════════════════════════════════════╣",
            f"║  From:     {tx.get('from', 'N/A'):54} ║",
            f"║  To:       {tx.get('to', 'N/A') or 'Contract Creation':54} ║",
            f"║  Value:    {format_value(tx.get('value', 0), 'ETH'):54} ║",
            "╠══════════════════════════════════════════════════════════════════════╣",
            f"║  Gas Price: {tx.get('gas_price_gwei', 0):.2f} Gwei{' ' * 43}║",
            f"║  Gas Limit: {tx.get('gas_limit', 0):,}{' ' * (42 - len(str(tx.get('gas_limit', 0))))}║",
            f"║  Gas Used:  {tx.get('gas_used', 0):,}{' ' * (42 - len(str(tx.get('gas_used', 0))))}║",
        ]

        if tx.get("gas_cost"):
            lines.append(f"║  Gas Cost:  {format_value(tx.get('gas_cost', 0), 'ETH', 6):54} ║")

        lines.extend(
            [
                "╠══════════════════════════════════════════════════════════════════════╣",
                f"║  Explorer: {tx.get('explorer_url', 'N/A')[:54]:54} ║",
                "╚══════════════════════════════════════════════════════════════════════╝",
            ]
        )

        return "\n".join(lines)

    def format_json(self, tx: Dict[str, Any]) -> str:
        """Format transaction as JSON.

        Args:
            tx: Transaction data

        Returns:
            JSON string
        """
        return json.dumps(tx, indent=2, default=str)

    def format_compact(self, tx: Dict[str, Any]) -> str:
        """Format transaction as compact line.

        Args:
            tx: Transaction data

        Returns:
            Single line string
        """
        status = "✓" if tx.get("status") == "success" else "✗"
        return (
            f"{status} {truncate_hash(tx.get('hash'))} | "
            f"{truncate_address(tx.get('from'))} → {truncate_address(tx.get('to'))} | "
            f"{format_value(tx.get('value', 0), 'ETH')}"
        )


class AddressFormatter:
    """Format address data."""

    def format_table(self, data: Dict[str, Any]) -> str:
        """Format address as table.

        Args:
            data: Address data

        Returns:
            Formatted string
        """
        lines = [
            "╔══════════════════════════════════════════════════════════════════════╗",
            "║  Address Details                                                      ║",
            "╠══════════════════════════════════════════════════════════════════════╣",
            f"║  Address:  {data.get('address', 'N/A'):54} ║",
            f"║  Chain:    {data.get('chain', 'N/A'):54} ║",
            "╠══════════════════════════════════════════════════════════════════════╣",
            f"║  Balance:  {format_value(data.get('balance', 0), data.get('symbol', 'ETH')):54} ║",
            f"║  Txns:     {data.get('transaction_count', 0):,}{' ' * (53 - len(str(data.get('transaction_count', 0))))}║",
            "╠══════════════════════════════════════════════════════════════════════╣",
            f"║  Explorer: {data.get('explorer_url', 'N/A')[:54]:54} ║",
            "╚══════════════════════════════════════════════════════════════════════╝",
        ]

        return "\n".join(lines)

    def format_json(self, data: Dict[str, Any]) -> str:
        """Format address as JSON.

        Args:
            data: Address data

        Returns:
            JSON string
        """
        return json.dumps(data, indent=2, default=str)


class BlockFormatter:
    """Format block data."""

    def format_table(self, block: Dict[str, Any]) -> str:
        """Format block as table.

        Args:
            block: Block data

        Returns:
            Formatted string
        """
        if block.get("error"):
            return f"Error: {block['error']}"

        lines = [
            "╔══════════════════════════════════════════════════════════════════════╗",
            "║  Block Details                                                        ║",
            "╠══════════════════════════════════════════════════════════════════════╣",
            f"║  Number:   {block.get('number', 'N/A'):,}{' ' * (53 - len(str(block.get('number', 0))))}║",
            f"║  Chain:    {block.get('chain', 'N/A'):54} ║",
            f"║  Time:     {format_timestamp(block.get('timestamp', 0)):54} ║",
            "╠══════════════════════════════════════════════════════════════════════╣",
            f"║  Hash:     {truncate_hash(block.get('hash'), 25):54} ║",
            f"║  Miner:    {truncate_address(block.get('miner')):54} ║",
            "╠══════════════════════════════════════════════════════════════════════╣",
            f"║  Gas Used: {block.get('gas_used', 0):,} / {block.get('gas_limit', 0):,}{' ' * 30}║",
        ]

        if block.get("base_fee_gwei"):
            lines.append(f"║  Base Fee: {block.get('base_fee_gwei', 0):.2f} Gwei{' ' * 43}║")

        lines.extend(
            [
                f"║  Txns:     {block.get('transaction_count', 0):,}{' ' * (53 - len(str(block.get('transaction_count', 0))))}║",
                "╠══════════════════════════════════════════════════════════════════════╣",
                f"║  Explorer: {block.get('explorer_url', 'N/A')[:54]:54} ║",
                "╚══════════════════════════════════════════════════════════════════════╝",
            ]
        )

        return "\n".join(lines)

    def format_json(self, block: Dict[str, Any]) -> str:
        """Format block as JSON.

        Args:
            block: Block data

        Returns:
            JSON string
        """
        return json.dumps(block, indent=2, default=str)


class TransactionListFormatter:
    """Format transaction lists."""

    def format_table(self, transactions: List[Dict[str, Any]], title: str = "Transaction History") -> str:
        """Format transaction list as table.

        Args:
            transactions: List of transactions
            title: Table title

        Returns:
            Formatted string
        """
        if not transactions:
            return "No transactions found."

        lines = [
            f"\n{title}",
            "=" * 100,
            f"{'Status':<8} {'Hash':<18} {'From':<14} {'To':<14} {'Value':<16} {'Method':<20}",
            "-" * 100,
        ]

        for tx in transactions:
            status = "✓" if tx.get("status") == "success" else "✗"
            lines.append(
                f"{status:<8} "
                f"{truncate_hash(tx.get('hash'), 6):<18} "
                f"{truncate_address(tx.get('from')):<14} "
                f"{truncate_address(tx.get('to')):<14} "
                f"{format_value(tx.get('value', 0), 'ETH'):<16} "
                f"{tx.get('method', 'transfer')[:18]:<20}"
            )

        lines.append("-" * 100)
        lines.append(f"Total: {len(transactions)} transactions")

        return "\n".join(lines)

    def format_csv(self, transactions: List[Dict[str, Any]]) -> str:
        """Format transaction list as CSV.

        Args:
            transactions: List of transactions

        Returns:
            CSV string
        """
        if not transactions:
            return ""

        output = io.StringIO()
        writer = csv.DictWriter(
            output, fieldnames=["hash", "block_number", "timestamp", "from", "to", "value", "status", "method"]
        )
        writer.writeheader()
        writer.writerows(transactions)

        return output.getvalue()

    def format_json(self, transactions: List[Dict[str, Any]]) -> str:
        """Format transaction list as JSON.

        Args:
            transactions: List of transactions

        Returns:
            JSON string
        """
        return json.dumps(transactions, indent=2, default=str)


class TokenTransferFormatter:
    """Format token transfers."""

    def format_table(self, transfers: List[Dict[str, Any]]) -> str:
        """Format token transfers as table.

        Args:
            transfers: List of token transfers

        Returns:
            Formatted string
        """
        if not transfers:
            return "No token transfers found."

        lines = [
            "\nToken Transfers",
            "=" * 110,
            f"{'Hash':<18} {'From':<14} {'To':<14} {'Amount':<20} {'Token':<15} {'Contract':<18}",
            "-" * 110,
        ]

        for tx in transfers:
            lines.append(
                f"{truncate_hash(tx.get('hash'), 6):<18} "
                f"{truncate_address(tx.get('from')):<14} "
                f"{truncate_address(tx.get('to')):<14} "
                f"{tx.get('value', 0):<20.4f} "
                f"{tx.get('token_symbol', '???'):<15} "
                f"{truncate_address(tx.get('token_contract')):<18}"
            )

        lines.append("-" * 110)
        lines.append(f"Total: {len(transfers)} transfers")

        return "\n".join(lines)


def format_output(data: Any, output_format: str = "table", data_type: str = "transaction") -> str:
    """Format data based on type and format.

    Args:
        data: Data to format
        output_format: Output format (table, json, csv)
        data_type: Data type (transaction, address, block, tx_list, transfers)

    Returns:
        Formatted string
    """
    formatters = {
        "transaction": TransactionFormatter(),
        "address": AddressFormatter(),
        "block": BlockFormatter(),
        "tx_list": TransactionListFormatter(),
        "transfers": TokenTransferFormatter(),
    }

    formatter = formatters.get(data_type)
    if not formatter:
        return json.dumps(data, indent=2, default=str)

    if output_format == "json":
        return formatter.format_json(data)
    elif output_format == "csv" and hasattr(formatter, "format_csv"):
        return formatter.format_csv(data)
    else:
        return formatter.format_table(data)


def main():
    """CLI entry point for testing."""
    # Test transaction formatting
    tx = {
        "hash": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
        "chain": "Ethereum",
        "status": "success",
        "block_number": 18500000,
        "from": "0xabcdef1234567890abcdef1234567890abcdef12",
        "to": "0x1234567890abcdef1234567890abcdef12345678",
        "value": 1.5,
        "gas_price_gwei": 25.5,
        "gas_limit": 21000,
        "gas_used": 21000,
        "gas_cost": 0.00053,
        "explorer_url": "https://etherscan.io/tx/0x1234...",
    }

    formatter = TransactionFormatter()
    print(formatter.format_table(tx))


if __name__ == "__main__":
    main()
