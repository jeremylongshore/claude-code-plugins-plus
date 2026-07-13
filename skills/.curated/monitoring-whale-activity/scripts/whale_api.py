#!/usr/bin/env python3
"""
Whale Alert API Client

Fetch large cryptocurrency transactions from Whale Alert and blockchain APIs.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 1.0.0
License: MIT
"""

import json
import os
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

try:
    import requests
except ImportError:
    requests = None


WHALE_ALERT_BASE = "https://api.whale-alert.io/v1"
ETHERSCAN_BASE = "https://api.etherscan.io/api"


@dataclass
class WhaleTransaction:
    """Represents a large cryptocurrency transaction."""

    tx_hash: str
    blockchain: str
    symbol: str
    amount: float
    amount_usd: float
    from_address: str
    from_owner: Optional[str]
    from_owner_type: Optional[str]
    to_address: str
    to_owner: Optional[str]
    to_owner_type: Optional[str]
    timestamp: int
    transaction_type: str  # transfer, mint, burn, etc.


class WhaleAlertClient:
    """Client for Whale Alert API."""

    def __init__(self, api_key: str = None, verbose: bool = False):
        """Initialize Whale Alert client.

        Args:
            api_key: Whale Alert API key (or set WHALE_ALERT_API_KEY env var)
            verbose: Enable verbose output
        """
        self.api_key = api_key or os.environ.get("WHALE_ALERT_API_KEY", "")
        self.verbose = verbose
        self.cache_file = Path.home() / ".whale_alert_cache.json"
        self.cache_ttl = 60  # 1 minute
        self._cache = self._load_cache()

    def _load_cache(self) -> Dict[str, Any]:
        """Load cache from file."""
        try:
            if self.cache_file.exists():
                with open(self.cache_file) as f:
                    return json.load(f)
        except (json.JSONDecodeError, IOError):
            # Cache is optional - start fresh if corrupted or unreadable
            pass
        return {}

    def _save_cache(self) -> None:
        """Save cache to file."""
        try:
            with open(self.cache_file, "w") as f:
                json.dump(self._cache, f)
        except IOError:
            # Cache write failures are non-fatal - continue without persistence
            pass

    def _is_cache_valid(self, key: str) -> bool:
        """Check if cached data is still valid."""
        if key not in self._cache:
            return False
        cached_time = self._cache.get(f"{key}_time", 0)
        return time.time() - cached_time < self.cache_ttl

    def _api_get(self, url: str, params: Dict = None) -> Any:
        """Make API request."""
        if not requests:
            raise ImportError("requests library required: pip install requests")

        if self.verbose:
            print(f"API: {url}")

        headers = {}
        if self.api_key:
            params = params or {}
            params["api_key"] = self.api_key

        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()

    def get_transactions(
        self,
        blockchain: str = None,
        min_value: int = 500000,
        limit: int = 100,
        start: int = None,
        end: int = None,
        cursor: str = None,
    ) -> List[WhaleTransaction]:
        """Fetch recent whale transactions.

        Args:
            blockchain: Filter by blockchain (ethereum, bitcoin, etc.)
            min_value: Minimum USD value threshold
            limit: Max transactions to return
            start: Start timestamp (unix)
            end: End timestamp (unix)
            cursor: Pagination cursor

        Returns:
            List of whale transactions
        """
        if not self.api_key:
            # Return mock data for demo
            return self._get_mock_transactions(blockchain, min_value, limit)

        params = {
            "min_value": min_value,
            "limit": min(limit, 100),  # API max is 100
        }

        if blockchain:
            params["blockchain"] = blockchain
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        if cursor:
            params["cursor"] = cursor

        cache_key = f"txs_{blockchain}_{min_value}_{limit}"
        if self._is_cache_valid(cache_key):
            data = self._cache[cache_key]
        else:
            try:
                data = self._api_get(f"{WHALE_ALERT_BASE}/transactions", params)
                self._cache[cache_key] = data
                self._cache[f"{cache_key}_time"] = time.time()
                self._save_cache()
            except Exception as e:
                if self.verbose:
                    print(f"API error: {e}, using mock data")
                return self._get_mock_transactions(blockchain, min_value, limit)

        transactions = []
        for tx in data.get("transactions", []):
            transactions.append(
                WhaleTransaction(
                    tx_hash=tx.get("hash", ""),
                    blockchain=tx.get("blockchain", "unknown"),
                    symbol=tx.get("symbol", "").upper(),
                    amount=tx.get("amount", 0),
                    amount_usd=tx.get("amount_usd", 0),
                    from_address=tx.get("from", {}).get("address", ""),
                    from_owner=tx.get("from", {}).get("owner", None),
                    from_owner_type=tx.get("from", {}).get("owner_type", None),
                    to_address=tx.get("to", {}).get("address", ""),
                    to_owner=tx.get("to", {}).get("owner", None),
                    to_owner_type=tx.get("to", {}).get("owner_type", None),
                    timestamp=tx.get("timestamp", 0),
                    transaction_type=tx.get("transaction_type", "transfer"),
                )
            )

        return transactions[:limit]

    def _get_mock_transactions(
        self, blockchain: str = None, min_value: int = 500000, limit: int = 10
    ) -> List[WhaleTransaction]:
        """Generate mock transactions for demo/testing."""
        now = int(time.time())
        mock_data = [
            WhaleTransaction(
                tx_hash="0x" + "a" * 64,
                blockchain="ethereum",
                symbol="ETH",
                amount=5000,
                amount_usd=15000000,
                from_address="0x" + "1" * 40,
                from_owner="binance",
                from_owner_type="exchange",
                to_address="0x" + "2" * 40,
                to_owner=None,
                to_owner_type="unknown",
                timestamp=now - 300,
                transaction_type="transfer",
            ),
            WhaleTransaction(
                tx_hash="0x" + "b" * 64,
                blockchain="ethereum",
                symbol="USDT",
                amount=50000000,
                amount_usd=50000000,
                from_address="0x" + "3" * 40,
                from_owner=None,
                from_owner_type="unknown",
                to_address="0x" + "4" * 40,
                to_owner="coinbase",
                to_owner_type="exchange",
                timestamp=now - 600,
                transaction_type="transfer",
            ),
            WhaleTransaction(
                tx_hash="1" + "c" * 63,
                blockchain="bitcoin",
                symbol="BTC",
                amount=500,
                amount_usd=21000000,
                from_address="bc1q" + "x" * 38,
                from_owner="kraken",
                from_owner_type="exchange",
                to_address="bc1q" + "y" * 38,
                to_owner=None,
                to_owner_type="unknown",
                timestamp=now - 900,
                transaction_type="transfer",
            ),
            WhaleTransaction(
                tx_hash="0x" + "d" * 64,
                blockchain="ethereum",
                symbol="USDC",
                amount=25000000,
                amount_usd=25000000,
                from_address="0x" + "5" * 40,
                from_owner="circle",
                from_owner_type="issuer",
                to_address="0x" + "6" * 40,
                to_owner="aave",
                to_owner_type="protocol",
                timestamp=now - 1200,
                transaction_type="transfer",
            ),
            WhaleTransaction(
                tx_hash="0x" + "e" * 64,
                blockchain="solana",
                symbol="SOL",
                amount=100000,
                amount_usd=10000000,
                from_address="So1" + "1" * 40,
                from_owner=None,
                from_owner_type="unknown",
                to_address="So1" + "2" * 40,
                to_owner="ftx_cold",
                to_owner_type="exchange",
                timestamp=now - 1500,
                transaction_type="transfer",
            ),
        ]

        # Filter by blockchain if specified
        if blockchain:
            mock_data = [tx for tx in mock_data if tx.blockchain == blockchain.lower()]

        # Filter by min_value
        mock_data = [tx for tx in mock_data if tx.amount_usd >= min_value]

        return mock_data[:limit]

    def get_status(self) -> Dict[str, Any]:
        """Get API status and rate limit info."""
        if not self.api_key:
            return {"status": "demo_mode", "message": "No API key configured, using mock data", "rate_limit": "N/A"}

        try:
            data = self._api_get(f"{WHALE_ALERT_BASE}/status")
            return {
                "status": "ok",
                "blockchains": data.get("blockchains", []),
                "rate_limit_remaining": data.get("rate_limit_remaining", "unknown"),
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}


class EtherscanClient:
    """Fallback client for Ethereum whale transactions via Etherscan."""

    def __init__(self, api_key: str = None, verbose: bool = False):
        """Initialize Etherscan client."""
        self.api_key = api_key or os.environ.get("ETHERSCAN_API_KEY", "")
        self.verbose = verbose

    def get_large_transfers(self, address: str = None, min_value_eth: float = 100) -> List[Dict[str, Any]]:
        """Get large ETH transfers."""
        if not requests:
            raise ImportError("requests library required")

        params = {
            "module": "account",
            "action": "txlist",
            "sort": "desc",
            "page": 1,
            "offset": 100,
        }

        if address:
            params["address"] = address
        if self.api_key:
            params["apikey"] = self.api_key

        response = requests.get(ETHERSCAN_BASE, params=params, timeout=30)
        data = response.json()

        if data.get("status") != "1":
            return []

        transfers = []
        for tx in data.get("result", []):
            value_eth = int(tx.get("value", 0)) / 1e18
            if value_eth >= min_value_eth:
                transfers.append(
                    {
                        "hash": tx.get("hash"),
                        "from": tx.get("from"),
                        "to": tx.get("to"),
                        "value_eth": value_eth,
                        "timestamp": int(tx.get("timeStamp", 0)),
                        "block": tx.get("blockNumber"),
                    }
                )

        return transfers


def main():
    """CLI entry point for testing."""
    client = WhaleAlertClient(verbose=True)

    print("=== Whale Alert Status ===")
    status = client.get_status()
    print(json.dumps(status, indent=2))

    print("\n=== Recent Whale Transactions ===")
    txs = client.get_transactions(min_value=1000000, limit=5)

    for tx in txs:
        time_str = datetime.utcfromtimestamp(tx.timestamp).strftime("%H:%M:%S UTC")
        from_label = tx.from_owner or tx.from_address[:10] + "..."
        to_label = tx.to_owner or tx.to_address[:10] + "..."
        print(f"[{time_str}] {tx.amount:,.0f} {tx.symbol} (${tx.amount_usd:,.0f}) {from_label} → {to_label}")


if __name__ == "__main__":
    main()
