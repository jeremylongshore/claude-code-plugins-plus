#!/usr/bin/env python3
"""
Price Service

Get cryptocurrency prices for USD conversion.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 1.0.0
License: MIT
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, Optional

try:
    import requests
except ImportError:
    requests = None


COINGECKO_BASE = "https://api.coingecko.com/api/v3"


# Symbol to CoinGecko ID mapping
SYMBOL_TO_ID = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "USDT": "tether",
    "USDC": "usd-coin",
    "BNB": "binancecoin",
    "XRP": "ripple",
    "ADA": "cardano",
    "DOGE": "dogecoin",
    "SOL": "solana",
    "DOT": "polkadot",
    "MATIC": "matic-network",
    "SHIB": "shiba-inu",
    "DAI": "dai",
    "TRX": "tron",
    "AVAX": "avalanche-2",
    "WBTC": "wrapped-bitcoin",
    "LINK": "chainlink",
    "UNI": "uniswap",
    "ATOM": "cosmos",
    "LTC": "litecoin",
    "ETC": "ethereum-classic",
    "XLM": "stellar",
    "NEAR": "near",
    "APT": "aptos",
    "ARB": "arbitrum",
    "OP": "optimism",
    "FTM": "fantom",
    "AAVE": "aave",
    "MKR": "maker",
    "CRV": "curve-dao-token",
    "LDO": "lido-dao",
    "RPL": "rocket-pool",
    "SAND": "the-sandbox",
    "MANA": "decentraland",
    "APE": "apecoin",
}


class PriceService:
    """Service for fetching cryptocurrency prices."""

    def __init__(self, verbose: bool = False):
        """Initialize price service.

        Args:
            verbose: Enable verbose output
        """
        self.verbose = verbose
        self.cache_file = Path.home() / ".crypto_prices_cache.json"
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

        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()

    def get_price(self, symbol: str, vs_currency: str = "usd") -> Optional[float]:
        """Get current price for a cryptocurrency.

        Note: This returns the CURRENT market price, not historical price at
        transaction time. For accurate historical valuations, consider using
        a historical price API endpoint (not implemented yet).

        Args:
            symbol: Token symbol (BTC, ETH, etc.)
            vs_currency: Quote currency (usd, eur, etc.)

        Returns:
            Current price or None if not found
        """
        symbol_upper = symbol.upper()

        # Stablecoins
        if symbol_upper in ["USDT", "USDC", "DAI", "BUSD", "TUSD", "USDP"]:
            return 1.0

        cache_key = f"price_{symbol_upper}_{vs_currency}"
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]

        # Get CoinGecko ID
        coin_id = SYMBOL_TO_ID.get(symbol_upper)
        if not coin_id:
            # Try lowercase symbol as ID
            coin_id = symbol_upper.lower()

        try:
            data = self._api_get(
                f"{COINGECKO_BASE}/simple/price", params={"ids": coin_id, "vs_currencies": vs_currency}
            )
            price = data.get(coin_id, {}).get(vs_currency)

            if price:
                self._cache[cache_key] = price
                self._cache[f"{cache_key}_time"] = time.time()
                self._save_cache()

            return price

        except Exception as e:
            if self.verbose:
                print(f"Price fetch error for {symbol}: {e}")
            return self._get_fallback_price(symbol_upper)

    def _get_fallback_price(self, symbol: str) -> Optional[float]:
        """Get fallback price from cache or defaults."""
        # Try stale cache
        cache_key = f"price_{symbol}_usd"
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Return None for unknown
        return None

    def get_prices_batch(self, symbols: list, vs_currency: str = "usd") -> Dict[str, Optional[float]]:
        """Get prices for multiple cryptocurrencies.

        Args:
            symbols: List of token symbols
            vs_currency: Quote currency

        Returns:
            Dict mapping symbol to price
        """
        results = {}

        # Check cache first
        uncached = []
        for symbol in symbols:
            symbol_upper = symbol.upper()
            cache_key = f"price_{symbol_upper}_{vs_currency}"
            if self._is_cache_valid(cache_key):
                results[symbol_upper] = self._cache[cache_key]
            elif symbol_upper in ["USDT", "USDC", "DAI", "BUSD"]:
                results[symbol_upper] = 1.0
            else:
                uncached.append(symbol_upper)

        if not uncached:
            return results

        # Fetch uncached prices
        coin_ids = []
        symbol_to_id = {}
        for symbol in uncached:
            coin_id = SYMBOL_TO_ID.get(symbol, symbol.lower())
            coin_ids.append(coin_id)
            symbol_to_id[coin_id] = symbol

        try:
            data = self._api_get(
                f"{COINGECKO_BASE}/simple/price", params={"ids": ",".join(coin_ids), "vs_currencies": vs_currency}
            )

            for coin_id, prices in data.items():
                symbol = symbol_to_id.get(coin_id, coin_id.upper())
                price = prices.get(vs_currency)
                if price:
                    results[symbol] = price
                    cache_key = f"price_{symbol}_{vs_currency}"
                    self._cache[cache_key] = price
                    self._cache[f"{cache_key}_time"] = time.time()

            self._save_cache()

        except Exception as e:
            if self.verbose:
                print(f"Batch price fetch error: {e}")
            # Fill with None for failed lookups
            for symbol in uncached:
                if symbol not in results:
                    results[symbol] = None

        return results

    def convert_to_usd(self, amount: float, symbol: str) -> Optional[float]:
        """Convert token amount to USD.

        Args:
            amount: Token amount
            symbol: Token symbol

        Returns:
            USD value or None if price unavailable
        """
        price = self.get_price(symbol)
        if price is not None:
            return amount * price
        return None

    def get_price_change(self, symbol: str, days: int = 1) -> Optional[Dict[str, float]]:
        """Get price change over time period.

        Args:
            symbol: Token symbol
            days: Number of days

        Returns:
            Dict with price_change and price_change_percentage
        """
        symbol_upper = symbol.upper()
        coin_id = SYMBOL_TO_ID.get(symbol_upper, symbol_upper.lower())

        cache_key = f"change_{symbol_upper}_{days}d"
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]

        try:
            data = self._api_get(
                f"{COINGECKO_BASE}/coins/{coin_id}",
                params={"localization": "false", "tickers": "false", "community_data": "false"},
            )

            market_data = data.get("market_data", {})
            result = {
                "current_price": market_data.get("current_price", {}).get("usd"),
                "price_change_24h": market_data.get("price_change_24h"),
                "price_change_percentage_24h": market_data.get("price_change_percentage_24h"),
                "price_change_percentage_7d": market_data.get("price_change_percentage_7d_in_currency", {}).get("usd"),
            }

            self._cache[cache_key] = result
            self._cache[f"{cache_key}_time"] = time.time()
            self._save_cache()

            return result

        except Exception as e:
            if self.verbose:
                print(f"Price change fetch error: {e}")
            return None


def main():
    """CLI entry point for testing."""
    service = PriceService(verbose=True)

    print("=== Single Price Lookup ===")
    for symbol in ["BTC", "ETH", "SOL", "USDT"]:
        price = service.get_price(symbol)
        print(f"  {symbol}: ${price:,.2f}" if price else f"  {symbol}: N/A")

    print("\n=== Batch Price Lookup ===")
    prices = service.get_prices_batch(["BTC", "ETH", "SOL", "MATIC", "ARB"])
    for symbol, price in prices.items():
        print(f"  {symbol}: ${price:,.2f}" if price else f"  {symbol}: N/A")

    print("\n=== USD Conversion ===")
    btc_amount = 100
    usd_value = service.convert_to_usd(btc_amount, "BTC")
    print(f"  {btc_amount} BTC = ${usd_value:,.0f}" if usd_value else f"  {btc_amount} BTC = N/A")


if __name__ == "__main__":
    main()
