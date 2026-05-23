#!/usr/bin/env python3
"""
Pool Fetcher

Fetches liquidity pool data from subgraphs and APIs.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 2.0.0
License: MIT
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

try:
    import requests
except ImportError:
    requests = None


class PoolFetcher:
    """Fetches pool data from DEX subgraphs and APIs."""

    # DeFiLlama endpoints
    DEFILLAMA_POOLS_URL = "https://yields.llama.fi/pools"

    # Subgraph endpoints
    SUBGRAPH_ENDPOINTS = {
        "uniswap-v3-ethereum": "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3",
        "uniswap-v3-arbitrum": "https://api.thegraph.com/subgraphs/name/ianlapham/uniswap-v3-arbitrum",
        "uniswap-v3-polygon": "https://api.thegraph.com/subgraphs/name/ianlapham/uniswap-v3-polygon",
        "uniswap-v2-ethereum": "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2",
    }

    CACHE_FILE = Path.home() / ".lp_analyzer_cache.json"
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

    def fetch_pool_by_address(
        self, address: str, chain: str = "ethereum", protocol: str = "uniswap-v3"
    ) -> Optional[Dict[str, Any]]:
        """Fetch pool data by contract address.

        Args:
            address: Pool contract address
            chain: Blockchain (ethereum, arbitrum, etc.)
            protocol: DEX protocol

        Returns:
            Pool data dictionary or None
        """
        cache_key = f"pool_{address}_{chain}"

        # Check cache
        if self.use_cache:
            cached = self._load_cache(cache_key)
            if cached:
                if self.verbose:
                    print(f"  Using cached data for {address[:10]}...")
                return cached

        # Try subgraph first
        subgraph_key = f"{protocol}-{chain}"
        if subgraph_key in self.SUBGRAPH_ENDPOINTS:
            pool = self._fetch_from_subgraph(address, subgraph_key)
            if pool:
                self._save_cache(cache_key, pool)
                return pool

        # Fallback to DeFiLlama
        pool = self._fetch_from_defillama(address)
        if pool:
            self._save_cache(cache_key, pool)
            return pool

        # Return mock data as last resort
        if self.verbose:
            print("  Pool not found, using mock data")
        return self._get_mock_pool(address)

    def fetch_pools_by_pair(
        self, token0: str, token1: str, chain: str = None, protocol: str = None
    ) -> List[Dict[str, Any]]:
        """Fetch pools for a token pair.

        Args:
            token0: First token symbol
            token1: Second token symbol
            chain: Optional chain filter
            protocol: Optional protocol filter

        Returns:
            List of matching pools
        """
        # Fetch from DeFiLlama (has all pools)
        all_pools = self._fetch_all_pools()

        # Normalize search terms
        search_tokens = {token0.upper(), token1.upper()}

        # Filter matching pools
        matches = []
        for pool in all_pools:
            symbol = pool.get("symbol", "").upper()
            # Check if both tokens are in the symbol
            if all(t in symbol for t in search_tokens):
                if chain and pool.get("chain", "").lower() != chain.lower():
                    continue
                if protocol and protocol.lower() not in pool.get("project", "").lower():
                    continue
                matches.append(pool)

        # Sort by TVL
        matches.sort(key=lambda x: -(x.get("tvlUsd") or 0))

        if self.verbose:
            print(f"  Found {len(matches)} pools for {token0}/{token1}")

        return matches

    def fetch_pools_by_protocol(self, protocol: str, chain: str = None, min_tvl: float = 0) -> List[Dict[str, Any]]:
        """Fetch all pools for a protocol.

        Args:
            protocol: Protocol name (uniswap-v3, curve, etc.)
            chain: Optional chain filter
            min_tvl: Minimum TVL filter

        Returns:
            List of pools
        """
        all_pools = self._fetch_all_pools()

        matches = []
        for pool in all_pools:
            if protocol.lower() not in pool.get("project", "").lower():
                continue
            if chain and pool.get("chain", "").lower() != chain.lower():
                continue
            if (pool.get("tvlUsd") or 0) < min_tvl:
                continue
            matches.append(pool)

        matches.sort(key=lambda x: -(x.get("tvlUsd") or 0))

        return matches

    def _fetch_all_pools(self) -> List[Dict[str, Any]]:
        """Fetch all pools from DeFiLlama.

        Returns:
            List of all pools
        """
        cache_key = "all_pools"

        if self.use_cache:
            cached = self._load_cache(cache_key)
            if cached:
                return cached

        if requests is None:
            return self._get_mock_pools()

        try:
            if self.verbose:
                print("  Fetching from DeFiLlama...")

            response = requests.get(self.DEFILLAMA_POOLS_URL, timeout=30, headers={"Accept": "application/json"})
            response.raise_for_status()

            data = response.json()
            pools = data.get("data", [])

            if self.use_cache and pools:
                self._save_cache(cache_key, pools)

            return pools

        except Exception as e:
            if self.verbose:
                print(f"  API error: {e}")
            return self._get_mock_pools()

    def _fetch_from_subgraph(self, address: str, subgraph_key: str) -> Optional[Dict[str, Any]]:
        """Fetch pool from The Graph subgraph.

        Args:
            address: Pool address
            subgraph_key: Subgraph identifier

        Returns:
            Pool data or None
        """
        if requests is None:
            return None

        endpoint = self.SUBGRAPH_ENDPOINTS.get(subgraph_key)
        if not endpoint:
            return None

        query = """
        query Pool($id: ID!) {
            pool(id: $id) {
                id
                token0 { symbol, decimals, name }
                token1 { symbol, decimals, name }
                feeTier
                liquidity
                sqrtPrice
                tick
                totalValueLockedUSD
                volumeUSD
                feesUSD
                txCount
                createdAtTimestamp
            }
        }
        """

        try:
            response = requests.post(endpoint, json={"query": query, "variables": {"id": address.lower()}}, timeout=15)
            response.raise_for_status()

            data = response.json()
            pool_data = data.get("data", {}).get("pool")

            if pool_data:
                return self._normalize_subgraph_pool(pool_data, subgraph_key)

        except Exception as e:
            if self.verbose:
                print(f"  Subgraph error: {e}")

        return None

    def _fetch_from_defillama(self, address: str) -> Optional[Dict[str, Any]]:
        """Fetch pool from DeFiLlama by address.

        Args:
            address: Pool address

        Returns:
            Pool data or None
        """
        pools = self._fetch_all_pools()
        address_lower = address.lower()

        for pool in pools:
            pool_id = pool.get("pool", "")
            if address_lower in pool_id.lower():
                return pool

        return None

    def _normalize_subgraph_pool(self, pool: Dict[str, Any], subgraph_key: str) -> Dict[str, Any]:
        """Normalize subgraph pool data to standard format.

        Args:
            pool: Raw subgraph pool data
            subgraph_key: Source subgraph

        Returns:
            Normalized pool data
        """
        # Extract chain and protocol from subgraph key
        parts = subgraph_key.split("-")
        protocol = "-".join(parts[:-1])
        chain = parts[-1]

        fee_tier = int(pool.get("feeTier", 0))
        fee_pct = fee_tier / 10000 if fee_tier else 0.003

        return {
            "pool": pool.get("id"),
            "project": protocol,
            "chain": chain.capitalize(),
            "symbol": f"{pool['token0']['symbol']}-{pool['token1']['symbol']}",
            "token0": pool["token0"],
            "token1": pool["token1"],
            "tvlUsd": float(pool.get("totalValueLockedUSD", 0)),
            "volumeUsd": float(pool.get("volumeUSD", 0)),
            "feesUsd": float(pool.get("feesUSD", 0)),
            "feeTier": fee_pct,
            "txCount": int(pool.get("txCount", 0)),
            "createdAt": pool.get("createdAtTimestamp"),
            "source": "subgraph",
        }

    def _load_cache(self, key: str) -> Optional[Any]:
        """Load data from cache.

        Args:
            key: Cache key

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

    def _get_mock_pool(self, address: str) -> Dict[str, Any]:
        """Get mock pool data for testing.

        Args:
            address: Pool address

        Returns:
            Mock pool data
        """
        return {
            "pool": address,
            "project": "uniswap-v3",
            "chain": "Ethereum",
            "symbol": "ETH-USDC",
            "token0": {"symbol": "USDC", "decimals": 6},
            "token1": {"symbol": "WETH", "decimals": 18},
            "tvlUsd": 500_000_000,
            "volumeUsd": 100_000_000,
            "feeTier": 0.0005,
            "feesUsd": 50_000,
            "source": "mock",
        }

    def _get_mock_pools(self) -> List[Dict[str, Any]]:
        """Get mock pools for testing.

        Returns:
            List of mock pools
        """
        return [
            {
                "pool": "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640",
                "project": "uniswap-v3",
                "chain": "Ethereum",
                "symbol": "USDC-WETH",
                "tvlUsd": 500_000_000,
                "volumeUsd": 125_000_000,
                "apy": 4.5,
                "feeTier": 0.0005,
            },
            {
                "pool": "0x4e68ccd3e89f51c3074ca5072bbac773960dfa36",
                "project": "uniswap-v3",
                "chain": "Ethereum",
                "symbol": "WETH-USDT",
                "tvlUsd": 150_000_000,
                "volumeUsd": 45_000_000,
                "apy": 8.2,
                "feeTier": 0.003,
            },
            {
                "pool": "curve-3pool",
                "project": "curve-dex",
                "chain": "Ethereum",
                "symbol": "DAI-USDC-USDT",
                "tvlUsd": 890_000_000,
                "volumeUsd": 50_000_000,
                "apy": 2.1,
                "feeTier": 0.0004,
            },
        ]


def main():
    """CLI entry point for testing."""
    fetcher = PoolFetcher(verbose=True)

    print("Fetching ETH/USDC pools:")
    pools = fetcher.fetch_pools_by_pair("ETH", "USDC")

    print(f"\nFound {len(pools)} pools:")
    for pool in pools[:5]:
        tvl = pool.get("tvlUsd", 0)
        if tvl >= 1e9:
            tvl_str = f"${tvl / 1e9:.1f}B"
        elif tvl >= 1e6:
            tvl_str = f"${tvl / 1e6:.0f}M"
        else:
            tvl_str = f"${tvl:,.0f}"

        print(f"  {pool.get('project')}: {pool.get('symbol')} on {pool.get('chain')} - TVL: {tvl_str}")


if __name__ == "__main__":
    main()
