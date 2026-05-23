#!/usr/bin/env python3
"""
Market Momentum Analyzer

Calculates market momentum from price and volume data using CoinGecko API.
Converts momentum indicators to sentiment-compatible scores.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 2.0.0
License: MIT
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

try:
    import requests
except ImportError:
    print("Error: requests library required. Install with: pip install requests", file=sys.stderr)
    sys.exit(1)


class MarketMomentumAnalyzer:
    """Calculates market momentum from price and volume data."""

    COINGECKO_API = "https://api.coingecko.com/api/v3"
    CACHE_FILE = Path(__file__).parent / ".momentum_cache.json"
    CACHE_TTL = 60  # 1 minute

    # Map symbols to CoinGecko IDs
    COIN_IDS = {
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
        "ARB": "arbitrum",
    }

    def __init__(self, verbose: bool = False):
        """Initialize analyzer.

        Args:
            verbose: Enable verbose output
        """
        self.verbose = verbose
        self._cache: Dict[str, Any] = {}
        self._cache_time: float = 0

    def analyze(self, coin: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Analyze market momentum.

        Args:
            coin: Specific coin to analyze (default: market overall)

        Returns:
            Dict with score (0-100), price changes, volume ratio
        """
        cache_key = coin or "market"
        if self._is_cache_valid(cache_key):
            if self.verbose:
                print(f"Using cached momentum for {cache_key}", file=sys.stderr)
            return self._cache.get(cache_key)

        if coin:
            result = self._analyze_coin(coin.upper())
        else:
            result = self._analyze_market()

        if result:
            self._cache[cache_key] = result
            self._cache_time = time.time()

        return result

    def _analyze_market(self) -> Optional[Dict[str, Any]]:
        """Analyze overall market momentum using BTC and ETH."""
        btc_data = self._fetch_coin_data("bitcoin")
        eth_data = self._fetch_coin_data("ethereum")

        if not btc_data:
            return self._get_fallback()

        # Calculate market momentum from major coins
        btc_change = btc_data.get("price_change_percentage_24h", 0)
        eth_change = eth_data.get("price_change_percentage_24h", 0) if eth_data else 0

        # Volume analysis
        btc_volume_ratio = self._calculate_volume_ratio(btc_data)

        # Convert to momentum score (0-100)
        # Price change component (60% weight)
        avg_change = btc_change * 0.7 + eth_change * 0.3  # BTC-weighted
        price_score = self._change_to_score(avg_change)

        # Volume component (40% weight)
        volume_score = self._volume_ratio_to_score(btc_volume_ratio)

        # Combined score
        momentum_score = (price_score * 0.6) + (volume_score * 0.4)

        return {
            "score": round(momentum_score, 1),
            "btc_change_24h": round(btc_change, 2),
            "eth_change_24h": round(eth_change, 2),
            "btc_price": btc_data.get("current_price"),
            "eth_price": eth_data.get("current_price") if eth_data else None,
            "volume_ratio": round(btc_volume_ratio, 2),
            "market_cap": btc_data.get("market_cap"),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    def _analyze_coin(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Analyze momentum for specific coin."""
        coin_id = self.COIN_IDS.get(symbol, symbol.lower())
        data = self._fetch_coin_data(coin_id)

        if not data:
            # Fall back to market analysis
            if self.verbose:
                print(f"No data for {symbol}, using market analysis", file=sys.stderr)
            return self._analyze_market()

        change_24h = data.get("price_change_percentage_24h", 0)
        volume_ratio = self._calculate_volume_ratio(data)

        # Convert to score
        price_score = self._change_to_score(change_24h)
        volume_score = self._volume_ratio_to_score(volume_ratio)
        momentum_score = (price_score * 0.6) + (volume_score * 0.4)

        return {
            "score": round(momentum_score, 1),
            "coin": symbol,
            "change_24h": round(change_24h, 2),
            "current_price": data.get("current_price"),
            "volume_ratio": round(volume_ratio, 2),
            "market_cap": data.get("market_cap"),
            "market_cap_rank": data.get("market_cap_rank"),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    def _fetch_coin_data(self, coin_id: str) -> Optional[Dict[str, Any]]:
        """Fetch coin data from CoinGecko."""
        try:
            if self.verbose:
                print(f"Fetching data for {coin_id}", file=sys.stderr)

            url = f"{self.COINGECKO_API}/coins/markets"
            params = {
                "vs_currency": "usd",
                "ids": coin_id,
                "order": "market_cap_desc",
                "sparkline": "false",
                "price_change_percentage": "24h",
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            if data and len(data) > 0:
                return data[0]

            return None

        except requests.exceptions.RequestException as e:
            if self.verbose:
                print(f"API request failed: {e}", file=sys.stderr)
            return None
        except (json.JSONDecodeError, IndexError) as e:
            if self.verbose:
                print(f"Failed to parse response: {e}", file=sys.stderr)
            return None

    def _calculate_volume_ratio(self, data: Dict[str, Any]) -> float:
        """Calculate volume to market cap ratio.

        Higher ratio suggests more activity relative to size.
        """
        volume = data.get("total_volume", 0)
        market_cap = data.get("market_cap", 1)

        if market_cap == 0:
            return 1.0

        # Typical ratio is around 0.02-0.05 (2-5%)
        ratio = volume / market_cap
        # Normalize to 0-2 range (1.0 being average)
        return min(2.0, ratio / 0.03)

    def _change_to_score(self, change: float) -> float:
        """Convert price change percentage to 0-100 score.

        -20% or worse = 0 (extreme bearish)
        0% = 50 (neutral)
        +20% or better = 100 (extreme bullish)
        """
        # Clamp to -20 to +20 range
        clamped = max(-20, min(20, change))
        # Linear mapping to 0-100
        return (clamped + 20) * 2.5

    def _volume_ratio_to_score(self, ratio: float) -> float:
        """Convert volume ratio to 0-100 score.

        Low volume (< 0.5) = bearish (30-50)
        Normal volume (0.5-1.5) = neutral (40-60)
        High volume (> 1.5) = can go either way, slight bullish (60-70)
        """
        if ratio < 0.5:
            return 30 + (ratio * 40)  # 30-50
        elif ratio < 1.5:
            return 40 + (ratio - 0.5) * 20  # 40-60
        else:
            return min(70, 60 + (ratio - 1.5) * 20)  # 60-70

    def _is_cache_valid(self, key: str) -> bool:
        """Check if cache is valid."""
        if key not in self._cache:
            return False
        return (time.time() - self._cache_time) < self.CACHE_TTL

    def _get_fallback(self) -> Dict[str, Any]:
        """Return fallback data when API unavailable."""
        return {
            "score": 50,
            "btc_change_24h": None,
            "eth_change_24h": None,
            "volume_ratio": None,
            "error": "Market data unavailable",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }


def main():
    """CLI entry point for testing."""
    import argparse

    parser = argparse.ArgumentParser(description="Analyze market momentum")
    parser.add_argument("--coin", type=str, help="Specific coin (BTC, ETH, etc.)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    analyzer = MarketMomentumAnalyzer(verbose=args.verbose)
    result = analyzer.analyze(coin=args.coin)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
