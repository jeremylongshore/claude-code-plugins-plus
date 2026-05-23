#!/usr/bin/env python3
"""
Market Analyzer - Core Analysis Logic

Fetches market data from tracking-crypto-prices dependency and prepares
it for mover analysis.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 2.0.0
License: MIT
"""

import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

# Resolve dependency path
SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent
PLUGIN_DIR = SKILL_DIR.parent.parent

# Path to tracking-crypto-prices dependency
PRICE_TRACKER_PATH = PLUGIN_DIR.parent / "market-price-tracker" / "skills" / "tracking-crypto-prices"


class DependencyError(Exception):
    """Raised when a required dependency is not available."""

    pass


class MarketAnalyzer:
    """
    Fetches and analyzes market data for mover detection.

    Uses tracking-crypto-prices skill for price data infrastructure.
    """

    def __init__(self, verbose: bool = False):
        """
        Initialize the analyzer.

        Args:
            verbose: Enable verbose output

        Raises:
            ImportError: If tracking-crypto-prices dependency is not available
        """
        self.verbose = verbose
        self._client = None
        self._cache = None

        # Try to import from dependency
        self._init_dependency()

    def _init_dependency(self) -> None:
        """Initialize connection to tracking-crypto-prices dependency."""
        # Check if dependency exists
        price_tracker_scripts = PRICE_TRACKER_PATH / "scripts"

        if not price_tracker_scripts.exists():
            raise ImportError(
                f"tracking-crypto-prices dependency not found.\n"
                f"Expected path: {PRICE_TRACKER_PATH}\n"
                f"Ensure market-price-tracker plugin is installed."
            )

        # Add to path and import
        sys.path.insert(0, str(price_tracker_scripts))

        try:
            from api_client import CryptoAPIClient
            from cache_manager import CacheManager

            self._client = CryptoAPIClient()
            self._cache = CacheManager(cache_dir=SKILL_DIR / "data")

            if self.verbose:
                print(f"Dependency loaded from {price_tracker_scripts}", file=sys.stderr)

        except ImportError as e:
            raise ImportError(f"Failed to import from tracking-crypto-prices: {e}")

    def fetch_market_data(self, category: Optional[str] = None, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Fetch current market data for all assets.

        Args:
            category: Optional category filter
            limit: Maximum number of assets to fetch

        Returns:
            List of asset dictionaries with price and volume data
        """
        if self._client is None:
            raise DependencyError("API client not initialized")

        try:
            # Use CoinGecko's markets endpoint for bulk data
            import requests

            url = "https://api.coingecko.com/api/v3/coins/markets"
            params = {
                "vs_currency": "usd",
                "order": "market_cap_desc",
                "per_page": min(limit, 250),  # CoinGecko max per page
                "page": 1,
                "sparkline": "false",
                "price_change_percentage": "1h,24h,7d",
            }

            if category:
                # Map category to CoinGecko category ID
                category_map = {
                    "defi": "decentralized-finance-defi",
                    "layer2": "layer-2",
                    "nft": "non-fungible-tokens-nft",
                    "gaming": "gaming",
                    "meme": "meme-token",
                }
                params["category"] = category_map.get(category, category)

            all_data = []
            pages_needed = (limit + 249) // 250  # Ceiling division

            for page in range(1, pages_needed + 1):
                params["page"] = page

                response = requests.get(url, params=params, timeout=10)

                if response.status_code == 429:
                    if self.verbose:
                        print("Rate limited, using partial data", file=sys.stderr)
                    break

                response.raise_for_status()
                page_data = response.json()

                if not page_data:
                    break

                all_data.extend(page_data)

                if len(page_data) < 250:
                    break  # No more pages

            # Transform to our format
            result = []
            for coin in all_data:
                result.append(
                    {
                        "symbol": coin.get("symbol", "").upper(),
                        "name": coin.get("name", ""),
                        "id": coin.get("id", ""),
                        "price": coin.get("current_price", 0),
                        "change_1h": coin.get("price_change_percentage_1h_in_currency"),
                        "change_24h": coin.get("price_change_percentage_24h"),
                        "change_7d": coin.get("price_change_percentage_7d_in_currency"),
                        "volume_24h": coin.get("total_volume", 0),
                        "market_cap": coin.get("market_cap", 0),
                        "market_cap_rank": coin.get("market_cap_rank"),
                        "circulating_supply": coin.get("circulating_supply"),
                        "high_24h": coin.get("high_24h"),
                        "low_24h": coin.get("low_24h"),
                        "ath": coin.get("ath"),
                        "ath_change_pct": coin.get("ath_change_percentage"),
                    }
                )

            return result

        except requests.exceptions.RequestException as e:
            if self.verbose:
                print(f"API error: {e}", file=sys.stderr)

            # Try to use cached data
            return self._get_cached_data() or []

    def _get_cached_data(self) -> Optional[List[Dict[str, Any]]]:
        """Get cached market data as fallback."""
        if self._cache is None:
            return None

        # Try to load from cache
        try:
            cached = self._cache.get_spot_price("_all_markets", "usd", allow_stale=True)
            if cached and isinstance(cached, list):
                return cached
        except Exception:
            pass

        return None

    def get_category_metadata(self) -> Dict[str, List[str]]:
        """Get category to coin ID mappings."""
        return {
            "defi": ["uniswap", "aave", "chainlink", "maker", "compound-governance-token", "curve-dao-token"],
            "layer2": ["matic-network", "arbitrum", "optimism", "immutable-x"],
            "nft": ["apecoin", "blur", "immutable-x"],
            "gaming": ["axie-infinity", "the-sandbox", "gala"],
            "meme": ["dogecoin", "shiba-inu", "pepe", "bonk"],
        }
