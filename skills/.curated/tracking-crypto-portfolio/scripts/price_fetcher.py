#!/usr/bin/env python3
"""
Price Fetcher

Fetches cryptocurrency prices from CoinGecko API.
Implements caching and batch requests for efficiency.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 2.0.0
License: MIT
"""

import json
import sys
import time
from pathlib import Path
from typing import Dict, Any, List

try:
    import requests
except ImportError:
    print("Error: requests library required. Install with: pip install requests", file=sys.stderr)
    sys.exit(1)


# Map common symbols to CoinGecko IDs
SYMBOL_TO_ID = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "XRP": "ripple",
    "ADA": "cardano",
    "DOGE": "dogecoin",
    "DOT": "polkadot",
    "LINK": "chainlink",
    "AVAX": "avalanche-2",
    "MATIC": "matic-network",
    "BNB": "binancecoin",
    "LTC": "litecoin",
    "ATOM": "cosmos",
    "UNI": "uniswap",
    "AAVE": "aave",
    "CRV": "curve-dao-token",
    "MKR": "maker",
    "COMP": "compound-governance-token",
    "SNX": "havven",
    "SUSHI": "sushi",
    "YFI": "yearn-finance",
    "1INCH": "1inch",
    "ENS": "ethereum-name-service",
    "LDO": "lido-dao",
    "ARB": "arbitrum",
    "OP": "optimism",
    "APT": "aptos",
    "SUI": "sui",
    "SEI": "sei-network",
    "TIA": "celestia",
    "INJ": "injective-protocol",
    "FET": "fetch-ai",
    "RNDR": "render-token",
    "GRT": "the-graph",
    "FIL": "filecoin",
    "NEAR": "near",
    "ICP": "internet-computer",
    "HBAR": "hedera-hashgraph",
    "VET": "vechain",
    "ALGO": "algorand",
    "XLM": "stellar",
    "XTZ": "tezos",
    "EOS": "eos",
    "FLOW": "flow",
    "MANA": "decentraland",
    "SAND": "the-sandbox",
    "AXS": "axie-infinity",
    "APE": "apecoin",
    "SHIB": "shiba-inu",
    "PEPE": "pepe",
    "WIF": "dogwifcoin",
    "BONK": "bonk",
    # Stablecoins
    "USDC": "usd-coin",
    "USDT": "tether",
    "DAI": "dai",
    "BUSD": "binance-usd",
    "TUSD": "true-usd",
    "FRAX": "frax",
    "LUSD": "liquity-usd",
    "USDD": "usdd",
}


class PriceFetcher:
    """Fetches cryptocurrency prices from CoinGecko."""

    COINGECKO_API = "https://api.coingecko.com/api/v3"
    CACHE_FILE = Path(__file__).parent / ".price_cache.json"
    CACHE_TTL = 60  # 1 minute

    def __init__(self, verbose: bool = False):
        """Initialize fetcher.

        Args:
            verbose: Enable verbose output
        """
        self.verbose = verbose
        self._cache: Dict[str, Any] = {}
        self._cache_time: float = 0

    def fetch_prices(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """Fetch prices for list of symbols.

        Args:
            symbols: List of coin symbols (e.g., ["BTC", "ETH"])

        Returns:
            Dict mapping symbol to price data
        """
        # Check cache first
        if self._is_cache_valid():
            if self.verbose:
                print("Using cached prices", file=sys.stderr)
            return self._get_cached_prices(symbols)

        # Map symbols to CoinGecko IDs
        id_to_symbol = {}
        unknown = []

        for symbol in symbols:
            symbol = symbol.upper()
            coin_id = SYMBOL_TO_ID.get(symbol, symbol.lower())
            id_to_symbol[coin_id] = symbol

            if symbol not in SYMBOL_TO_ID:
                unknown.append(symbol)

        if unknown and self.verbose:
            print(f"Warning: Unknown symbols, trying lowercase: {unknown}", file=sys.stderr)

        # Fetch from API
        prices = self._fetch_from_api(list(id_to_symbol.keys()))

        # Map back to symbols
        result = {}
        for coin_id, data in prices.items():
            symbol = id_to_symbol.get(coin_id, coin_id.upper())
            result[symbol] = data

        # Update cache
        self._cache = result
        self._cache_time = time.time()
        self._save_cache()

        return result

    def _fetch_from_api(self, coin_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """Fetch prices from CoinGecko API."""
        results = {}

        # Batch into groups of 250 (API limit)
        batches = [coin_ids[i : i + 250] for i in range(0, len(coin_ids), 250)]

        for batch in batches:
            try:
                if self.verbose:
                    print(f"Fetching prices for {len(batch)} coins...", file=sys.stderr)

                response = requests.get(
                    f"{self.COINGECKO_API}/coins/markets",
                    params={
                        "vs_currency": "usd",
                        "ids": ",".join(batch),
                        "order": "market_cap_desc",
                        "sparkline": "false",
                        "price_change_percentage": "24h,7d,30d",
                    },
                    timeout=15,
                )
                response.raise_for_status()

                data = response.json()
                for coin in data:
                    results[coin["id"]] = {
                        "price": coin.get("current_price", 0),
                        "change_24h": coin.get("price_change_percentage_24h"),
                        "change_7d": coin.get("price_change_percentage_7d_in_currency"),
                        "change_30d": coin.get("price_change_percentage_30d_in_currency"),
                        "market_cap": coin.get("market_cap"),
                        "volume_24h": coin.get("total_volume"),
                        "last_updated": coin.get("last_updated"),
                    }

                # Rate limit protection
                if len(batches) > 1:
                    time.sleep(0.5)

            except requests.exceptions.RequestException as e:
                if self.verbose:
                    print(f"API request failed: {e}", file=sys.stderr)
                # Try to load from cache
                return self._load_cached_prices()

        return results

    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid."""
        if not self._cache:
            self._load_cache_file()
        return (time.time() - self._cache_time) < self.CACHE_TTL

    def _get_cached_prices(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get prices from cache."""
        return {s: self._cache.get(s.upper(), {}) for s in symbols}

    def _load_cache_file(self) -> None:
        """Load cache from file."""
        try:
            if self.CACHE_FILE.exists():
                with open(self.CACHE_FILE, "r") as f:
                    data = json.load(f)
                self._cache = data.get("prices", {})
                self._cache_time = data.get("timestamp", 0)
        except Exception:
            self._cache = {}
            self._cache_time = 0

    def _save_cache(self) -> None:
        """Save cache to file."""
        try:
            with open(self.CACHE_FILE, "w") as f:
                json.dump({"prices": self._cache, "timestamp": self._cache_time}, f)
        except Exception:
            pass  # Cache save failure is non-fatal

    def _load_cached_prices(self) -> Dict[str, Dict[str, Any]]:
        """Load prices from cache file (fallback)."""
        self._load_cache_file()
        if self._cache:
            if self.verbose:
                print("Using stale cached prices as fallback", file=sys.stderr)
        return self._cache


def main():
    """CLI entry point for testing."""
    import argparse

    parser = argparse.ArgumentParser(description="Fetch cryptocurrency prices")
    parser.add_argument("symbols", nargs="+", help="Coin symbols (BTC, ETH, etc.)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    fetcher = PriceFetcher(verbose=args.verbose)
    prices = fetcher.fetch_prices(args.symbols)
    print(json.dumps(prices, indent=2))


if __name__ == "__main__":
    main()
