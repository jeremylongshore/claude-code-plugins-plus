#!/usr/bin/env python3
"""
Protocol Fetcher

Fetches yield data from DeFiLlama and other APIs.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 2.0.0
License: MIT
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    import requests
except ImportError:
    requests = None


class ProtocolFetcher:
    """Fetches yield data from DeFi protocols."""

    DEFILLAMA_YIELDS_URL = "https://yields.llama.fi/pools"
    DEFILLAMA_PROTOCOLS_URL = "https://api.llama.fi/protocols"

    CACHE_FILE = Path.home() / ".defi_yield_cache.json"
    CACHE_TTL = 300  # 5 minutes

    def __init__(self, use_cache: bool = True, verbose: bool = False):
        """Initialize fetcher.

        Args:
            use_cache: Whether to use cached data
            verbose: Enable verbose output
        """
        self.use_cache = use_cache
        self.verbose = verbose
        self._cache = {}

    def fetch_yields(self) -> List[Dict[str, Any]]:
        """Fetch all yield pools from DeFiLlama.

        Returns:
            List of pool dictionaries
        """
        # Check cache first
        if self.use_cache:
            cached = self._load_cache("yields")
            if cached:
                if self.verbose:
                    print(f"  Using cached data ({len(cached)} pools)")
                return cached

        # Fetch fresh data
        if requests is None:
            if self.verbose:
                print("  Warning: requests library not available, using mock data")
            return self._get_mock_data()

        try:
            if self.verbose:
                print(f"  Fetching from {self.DEFILLAMA_YIELDS_URL}...")

            response = requests.get(self.DEFILLAMA_YIELDS_URL, timeout=30, headers={"Accept": "application/json"})
            response.raise_for_status()

            data = response.json()
            pools = data.get("data", [])

            # Cache the results
            if self.use_cache and pools:
                self._save_cache("yields", pools)

            return pools

        except requests.exceptions.RequestException as e:
            if self.verbose:
                print(f"  API error: {e}")

            # Fall back to cache
            cached = self._load_cache("yields", ignore_ttl=True)
            if cached:
                if self.verbose:
                    print(f"  Using stale cache ({len(cached)} pools)")
                return cached

            # Fall back to mock data
            return self._get_mock_data()

    def fetch_protocol_info(self, protocol: str) -> Optional[Dict[str, Any]]:
        """Fetch detailed info for a specific protocol.

        Args:
            protocol: Protocol name/slug

        Returns:
            Protocol info dictionary or None
        """
        if requests is None:
            return None

        try:
            url = f"https://api.llama.fi/protocol/{protocol}"
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

    def _load_cache(self, key: str, ignore_ttl: bool = False) -> Optional[List]:
        """Load data from cache.

        Args:
            key: Cache key
            ignore_ttl: Ignore TTL (for fallback)

        Returns:
            Cached data or None
        """
        if not self.CACHE_FILE.exists():
            return None

        try:
            with open(self.CACHE_FILE, "r") as f:
                cache = json.load(f)

            entry = cache.get(key)
            if not entry:
                return None

            # Check TTL
            if not ignore_ttl:
                cached_time = entry.get("timestamp", 0)
                if time.time() - cached_time > self.CACHE_TTL:
                    return None

            return entry.get("data")

        except (json.JSONDecodeError, IOError):
            return None

    def _save_cache(self, key: str, data: Any) -> None:
        """Save data to cache.

        Args:
            key: Cache key
            data: Data to cache
        """
        try:
            cache = {}
            if self.CACHE_FILE.exists():
                with open(self.CACHE_FILE, "r") as f:
                    cache = json.load(f)

            cache[key] = {"timestamp": time.time(), "data": data}

            with open(self.CACHE_FILE, "w") as f:
                json.dump(cache, f)

        except IOError:
            pass

    def _get_mock_data(self) -> List[Dict[str, Any]]:
        """Get mock data for testing/fallback.

        Returns:
            List of mock pool data
        """
        return [
            {
                "chain": "Ethereum",
                "project": "aave-v3",
                "symbol": "USDC",
                "tvlUsd": 2100000000,
                "apyBase": 3.5,
                "apyReward": 0.7,
                "apy": 4.2,
                "pool": "aave-v3-usdc-ethereum",
                "rewardTokens": ["AAVE"],
            },
            {
                "chain": "Ethereum",
                "project": "compound-v3",
                "symbol": "USDC",
                "tvlUsd": 1500000000,
                "apyBase": 2.8,
                "apyReward": 0.4,
                "apy": 3.2,
                "pool": "compound-v3-usdc-ethereum",
                "rewardTokens": ["COMP"],
            },
            {
                "chain": "Ethereum",
                "project": "curve-dex",
                "symbol": "3pool",
                "tvlUsd": 890000000,
                "apyBase": 1.2,
                "apyReward": 2.6,
                "apy": 3.8,
                "pool": "curve-3pool",
                "rewardTokens": ["CRV"],
            },
            {
                "chain": "Ethereum",
                "project": "convex-finance",
                "symbol": "cvxCRV",
                "tvlUsd": 450000000,
                "apyBase": 4.5,
                "apyReward": 8.0,
                "apy": 12.5,
                "pool": "convex-cvxcrv",
                "rewardTokens": ["CRV", "CVX"],
            },
            {
                "chain": "Ethereum",
                "project": "yearn-finance",
                "symbol": "yvUSDC",
                "tvlUsd": 120000000,
                "apyBase": 5.1,
                "apyReward": 0,
                "apy": 5.1,
                "pool": "yearn-usdc",
                "rewardTokens": [],
            },
            {
                "chain": "Arbitrum",
                "project": "aave-v3",
                "symbol": "USDC",
                "tvlUsd": 800000000,
                "apyBase": 4.2,
                "apyReward": 1.5,
                "apy": 5.7,
                "pool": "aave-v3-usdc-arbitrum",
                "rewardTokens": ["AAVE", "ARB"],
            },
            {
                "chain": "Polygon",
                "project": "aave-v3",
                "symbol": "USDC",
                "tvlUsd": 500000000,
                "apyBase": 3.8,
                "apyReward": 1.2,
                "apy": 5.0,
                "pool": "aave-v3-usdc-polygon",
                "rewardTokens": ["AAVE"],
            },
            {
                "chain": "Ethereum",
                "project": "lido",
                "symbol": "stETH",
                "tvlUsd": 15000000000,
                "apyBase": 3.8,
                "apyReward": 0,
                "apy": 3.8,
                "pool": "lido-steth",
                "rewardTokens": [],
            },
        ]


def main():
    """CLI entry point for testing."""
    fetcher = ProtocolFetcher(verbose=True)
    pools = fetcher.fetch_yields()

    print(f"\nFetched {len(pools)} pools")
    print("\nTop 5 by TVL:")
    sorted_pools = sorted(pools, key=lambda x: -(x.get("tvlUsd") or 0))
    for pool in sorted_pools[:5]:
        print(
            f"  {pool.get('project')}: {pool.get('symbol')} on {pool.get('chain')} - "
            f"TVL: ${pool.get('tvlUsd', 0) / 1e6:.1f}M, APY: {pool.get('apy', 0):.2f}%"
        )


if __name__ == "__main__":
    main()
