#!/usr/bin/env python3
"""
Transaction Parser

Parses and normalizes CSV transaction exports from various exchanges.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 2.0.0
License: MIT
"""

import csv
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import List, Dict, Any, Optional

# Exchange format definitions
EXCHANGE_FORMATS = {
    "coinbase": {
        "date_col": "Timestamp",
        "type_col": "Transaction Type",
        "asset_col": "Asset",
        "quantity_col": "Quantity Transacted",
        "price_col": "Spot Price at Transaction",
        "fee_col": "Fees and/or Spread",
        "total_col": "Total (inclusive of fees and/or spread)",
        "date_format": "%Y-%m-%dT%H:%M:%SZ",
    },
    "binance": {
        "date_col": "Date(UTC)",
        "type_col": "Operation",
        "asset_col": "Coin",
        "quantity_col": "Change",
        "price_col": None,  # Requires external price lookup
        "fee_col": None,
        "total_col": None,
        "date_format": "%Y-%m-%d %H:%M:%S",
    },
    "kraken": {
        "date_col": "time",
        "type_col": "type",
        "asset_col": "asset",
        "quantity_col": "amount",
        "price_col": None,
        "fee_col": "fee",
        "total_col": None,
        "date_format": "%Y-%m-%d %H:%M:%S.%f",
    },
    "gemini": {
        "date_col": "Date",
        "type_col": "Type",
        "asset_col": "Symbol",
        "quantity_col": "Amount",
        "price_col": "Price",
        "fee_col": "Fee",
        "total_col": None,
        "date_format": "%Y-%m-%d %H:%M:%S",
    },
    "generic": {
        "date_col": "date",
        "type_col": "type",
        "asset_col": "asset",
        "quantity_col": "quantity",
        "price_col": "price",
        "fee_col": "fee",
        "total_col": "total",
        "date_format": None,  # Auto-detect
    },
}

# Transaction type mapping
TYPE_MAPPING = {
    # Buys (acquisitions)
    "buy": "buy",
    "receive": "buy",
    "deposit": "transfer_in",
    "advanced trade buy": "buy",
    "rewards income": "staking",
    "staking income": "staking",
    "coinbase earn": "income",
    "learning reward": "income",
    # Sells (disposals)
    "sell": "sell",
    "send": "transfer_out",
    "withdrawal": "transfer_out",
    "advanced trade sell": "sell",
    "convert": "trade",
    # Income events
    "staking": "staking",
    "airdrop": "airdrop",
    "mining": "mining",
    "interest": "interest",
    "reward": "staking",
    # Trades
    "trade": "trade",
    "swap": "trade",
    "exchange": "trade",
    # Transfers (non-taxable)
    "transfer": "transfer",
}


class TransactionParser:
    """Parses transaction CSV files from various exchanges."""

    def __init__(self, verbose: bool = False):
        """Initialize parser.

        Args:
            verbose: Enable verbose output
        """
        self.verbose = verbose

    def parse(self, filepath: str, exchange: Optional[str] = None) -> List[Dict[str, Any]]:
        """Parse a transaction CSV file.

        Args:
            filepath: Path to CSV file
            exchange: Exchange format (auto-detected if not specified)

        Returns:
            List of normalized transaction dictionaries
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Transaction file not found: {filepath}")

        # Read CSV
        with open(path, "r", encoding="utf-8-sig") as f:
            # Detect delimiter
            sample = f.read(4096)
            f.seek(0)

            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
            reader = csv.DictReader(f, dialect=dialect)

            headers = reader.fieldnames
            if not headers:
                raise ValueError(f"No headers found in {filepath}")

            # Auto-detect exchange format
            if not exchange:
                exchange = self._detect_exchange(headers)
                if self.verbose:
                    print(f"  Detected exchange format: {exchange}")

            format_spec = EXCHANGE_FORMATS.get(exchange, EXCHANGE_FORMATS["generic"])

            transactions = []
            for row_num, row in enumerate(reader, start=2):
                try:
                    tx = self._parse_row(row, format_spec, row_num)
                    if tx:
                        transactions.append(tx)
                except Exception as e:
                    if self.verbose:
                        print(f"  Warning: Row {row_num} skipped: {e}")

        return transactions

    def _detect_exchange(self, headers: List[str]) -> str:
        """Detect exchange format from CSV headers."""
        headers_lower = [h.lower() for h in headers]

        # Check each exchange format
        for exchange, format_spec in EXCHANGE_FORMATS.items():
            if exchange == "generic":
                continue

            date_col = format_spec["date_col"].lower()
            if date_col in headers_lower:
                return exchange

        return "generic"

    def _parse_row(self, row: Dict[str, str], format_spec: Dict[str, Any], row_num: int) -> Optional[Dict[str, Any]]:
        """Parse a single CSV row into normalized transaction.

        Args:
            row: CSV row dictionary
            format_spec: Exchange format specification
            row_num: Row number for error reporting

        Returns:
            Normalized transaction dict or None if invalid
        """
        # Get values using format specification
        date_str = self._get_value(row, format_spec["date_col"])
        type_str = self._get_value(row, format_spec["type_col"])
        asset = self._get_value(row, format_spec["asset_col"])
        quantity_str = self._get_value(row, format_spec["quantity_col"])

        # Validate required fields
        if not all([date_str, type_str, asset, quantity_str]):
            return None

        # Parse date
        date = self._parse_date(date_str, format_spec.get("date_format"))
        if not date:
            raise ValueError(f"Cannot parse date: {date_str}")

        # Parse quantity
        quantity = self._parse_decimal(quantity_str)
        if quantity is None or quantity == 0:
            return None

        # Normalize type
        tx_type = self._normalize_type(type_str)

        # Parse optional fields
        price = None
        if format_spec.get("price_col"):
            price_str = self._get_value(row, format_spec["price_col"])
            if price_str:
                price = self._parse_decimal(price_str)

        fee = Decimal("0")
        if format_spec.get("fee_col"):
            fee_str = self._get_value(row, format_spec["fee_col"])
            if fee_str:
                fee = self._parse_decimal(fee_str) or Decimal("0")

        total = None
        if format_spec.get("total_col"):
            total_str = self._get_value(row, format_spec["total_col"])
            if total_str:
                total = self._parse_decimal(total_str)

        # Normalize asset symbol
        asset = self._normalize_asset(asset)

        return {
            "date": date,
            "type": tx_type,
            "asset": asset,
            "quantity": abs(quantity),  # Always positive
            "price": price,
            "fee": abs(fee),
            "total": total,
            "raw_type": type_str,
            "row": row_num,
        }

    def _get_value(self, row: Dict[str, str], col: Optional[str]) -> Optional[str]:
        """Get value from row by column name (case-insensitive)."""
        if not col:
            return None

        # Try exact match first
        if col in row:
            return row[col].strip()

        # Try case-insensitive match
        col_lower = col.lower()
        for key, value in row.items():
            if key.lower() == col_lower:
                return value.strip()

        return None

    def _parse_date(self, date_str: str, format_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime."""
        # Try specified format first
        if format_str:
            try:
                return datetime.strptime(date_str, format_str)
            except ValueError:
                pass

        # Try common formats
        formats = [
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%d",
            "%m/%d/%Y %H:%M:%S",
            "%m/%d/%Y",
            "%d/%m/%Y %H:%M:%S",
            "%d/%m/%Y",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        return None

    def _parse_decimal(self, value: str) -> Optional[Decimal]:
        """Parse string to Decimal."""
        if not value:
            return None

        # Remove currency symbols and commas
        clean = value.replace("$", "").replace(",", "").replace(" ", "").strip()

        # Handle parentheses for negative numbers
        if clean.startswith("(") and clean.endswith(")"):
            clean = "-" + clean[1:-1]

        try:
            return Decimal(clean)
        except InvalidOperation:
            return None

    def _normalize_type(self, type_str: str) -> str:
        """Normalize transaction type."""
        type_lower = type_str.lower().strip()

        # Check direct mapping
        if type_lower in TYPE_MAPPING:
            return TYPE_MAPPING[type_lower]

        # Check partial matches
        for key, value in TYPE_MAPPING.items():
            if key in type_lower:
                return value

        return "other"

    def _normalize_asset(self, asset: str) -> str:
        """Normalize asset symbol."""
        # Remove common prefixes/suffixes
        asset = asset.upper().strip()

        # Handle Kraken-style symbols (XXBT -> BTC, XETH -> ETH)
        if asset.startswith("X") and len(asset) == 4:
            asset = asset[1:]
        if asset.startswith("XX") and len(asset) == 4:
            asset = asset[2:]
        if asset.startswith("Z") and len(asset) == 4:
            asset = asset[1:]

        # Common normalizations
        normalizations = {
            "XBT": "BTC",
            "XXBT": "BTC",
            "XETH": "ETH",
            "ZUSD": "USD",
        }

        return normalizations.get(asset, asset)


def main():
    """CLI entry point for testing."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python transaction_parser.py <csv_file> [exchange]")
        sys.exit(1)

    filepath = sys.argv[1]
    exchange = sys.argv[2] if len(sys.argv) > 2 else None

    parser = TransactionParser(verbose=True)
    transactions = parser.parse(filepath, exchange=exchange)

    print(f"\nParsed {len(transactions)} transactions:")
    for tx in transactions[:10]:
        print(f"  {tx['date'].strftime('%Y-%m-%d')} {tx['type']:12} {tx['quantity']:>12.4f} {tx['asset']}")

    if len(transactions) > 10:
        print(f"  ... and {len(transactions) - 10} more")


if __name__ == "__main__":
    main()
