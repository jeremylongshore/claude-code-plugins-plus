#!/usr/bin/env python3
"""
On-Chain Data Fetcher

Fetch protocol metrics from DeFiLlama and other sources.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 1.0.0
License: MIT
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

try:
    import requests
except ImportError:
    requests = None


DEFILLAMA_BASE = "https://api.llama.fi"
COINGECKO_BASE = "https://api.coingecko.com/api/v3"


@dataclass
class ProtocolData:
    """Protocol metrics."""

    name: str
    slug: str
    tvl: float
    tvl_change_24h: float
    tvl_change_7d: float
    chains: List[str]
    category: str
    token: Optional[str] = None
    mcap: Optional[float] = None
    fdv: Optional[float] = None


class DataFetcher:
    """Fetch on-chain analytics data."""

    def __init__(self, verbose: bool = False):
        """Initialize fetcher."""
        self.verbose = verbose
        self.cache_file = Path.home() / ".onchain_analytics_cache.json"
        self.cache_ttl = 300  # 5 minutes
        self._cache = self._load_cache()

    def _load_cache(self) -> Dict[str, Any]:
        """Load cache from file."""
        try:
            if self.cache_file.exists():
                with open(self.cache_file) as f:
                    return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
        return {}

    def _save_cache(self) -> None:
        """Save cache to file."""
        try:
            with open(self.cache_file, "w") as f:
                json.dump(self._cache, f)
        except IOError:
            pass

    def _is_cache_valid(self, key: str, ttl: int = None) -> bool:
        """Check if cached data is still valid."""
        if key not in self._cache:
            return False
        cached_time = self._cache.get(f"{key}_time", 0)
        return time.time() - cached_time < (ttl or self.cache_ttl)

    def _api_get(self, url: str, params: Dict = None) -> Any:
        """Make API request."""
        if not requests:
            raise ImportError("requests library required")

        if self.verbose:
            print(f"API: {url}")

        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()

    def fetch_protocols(self, limit: int = 100) -> List[ProtocolData]:
        """Fetch all protocols with TVL.

        Args:
            limit: Max protocols to return

        Returns:
            List of protocol data
        """
        cache_key = "protocols"
        if self._is_cache_valid(cache_key):
            data = self._cache[cache_key]
        else:
            data = self._api_get(f"{DEFILLAMA_BASE}/protocols")
            self._cache[cache_key] = data
            self._cache[f"{cache_key}_time"] = time.time()
            self._save_cache()

        protocols = []
        for p in data[:limit]:
            protocols.append(
                ProtocolData(
                    name=p.get("name", "Unknown"),
                    slug=p.get("slug", ""),
                    tvl=p.get("tvl", 0),
                    tvl_change_24h=p.get("change_1d", 0) or 0,
                    tvl_change_7d=p.get("change_7d", 0) or 0,
                    chains=p.get("chains", []),
                    category=p.get("category", "Unknown"),
                    token=p.get("symbol"),
                    mcap=p.get("mcap"),
                    fdv=p.get("fdv"),
                )
            )

        return protocols

    def fetch_chains(self) -> List[Dict[str, Any]]:
        """Fetch TVL by chain.

        Returns:
            List of chain data
        """
        cache_key = "chains"
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]

        data = self._api_get(f"{DEFILLAMA_BASE}/v2/chains")

        self._cache[cache_key] = data
        self._cache[f"{cache_key}_time"] = time.time()
        self._save_cache()

        return data

    def fetch_protocol_tvl_history(self, slug: str) -> List[Dict[str, Any]]:
        """Fetch historical TVL for protocol.

        Args:
            slug: Protocol slug

        Returns:
            List of {date, tvl} entries
        """
        cache_key = f"tvl_history_{slug}"
        if self._is_cache_valid(cache_key, ttl=3600):
            return self._cache[cache_key]

        data = self._api_get(f"{DEFILLAMA_BASE}/protocol/{slug}")
        tvl_data = data.get("tvl", [])

        self._cache[cache_key] = tvl_data
        self._cache[f"{cache_key}_time"] = time.time()
        self._save_cache()

        return tvl_data

    def fetch_fees_revenue(self, protocol: str = None) -> List[Dict[str, Any]]:
        """Fetch protocol fees and revenue.

        Args:
            protocol: Optional specific protocol

        Returns:
            List of fee/revenue data
        """
        cache_key = f"fees_{protocol or 'all'}"
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]

        if protocol:
            url = f"{DEFILLAMA_BASE}/summary/fees/{protocol}"
        else:
            url = f"{DEFILLAMA_BASE}/overview/fees"

        try:
            data = self._api_get(url)
            result = data.get("protocols", [data]) if protocol else data.get("protocols", [])
        except Exception:
            result = []

        self._cache[cache_key] = result
        self._cache[f"{cache_key}_time"] = time.time()
        self._save_cache()

        return result

    def fetch_dex_volumes(self, chain: str = None) -> List[Dict[str, Any]]:
        """Fetch DEX trading volumes.

        Args:
            chain: Optional chain filter

        Returns:
            List of DEX volume data
        """
        cache_key = f"dex_volumes_{chain or 'all'}"
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]

        url = f"{DEFILLAMA_BASE}/overview/dexs"
        if chain:
            url += f"/{chain}"

        data = self._api_get(url)
        result = data.get("protocols", [])

        self._cache[cache_key] = result
        self._cache[f"{cache_key}_time"] = time.time()
        self._save_cache()

        return result

    def fetch_yields(self, chain: str = None) -> List[Dict[str, Any]]:
        """Fetch yield/APY data.

        Args:
            chain: Optional chain filter

        Returns:
            List of yield pools
        """
        cache_key = f"yields_{chain or 'all'}"
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]

        url = "https://yields.llama.fi/pools"
        data = self._api_get(url)
        pools = data.get("data", [])

        if chain:
            pools = [p for p in pools if p.get("chain", "").lower() == chain.lower()]

        self._cache[cache_key] = pools
        self._cache[f"{cache_key}_time"] = time.time()
        self._save_cache()

        return pools

    def fetch_stablecoin_data(self) -> List[Dict[str, Any]]:
        """Fetch stablecoin metrics.

        Returns:
            List of stablecoin data
        """
        cache_key = "stablecoins"
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]

        data = self._api_get(f"{DEFILLAMA_BASE}/stablecoins")
        result = data.get("peggedAssets", [])

        self._cache[cache_key] = result
        self._cache[f"{cache_key}_time"] = time.time()
        self._save_cache()

        return result


def main():
    """CLI entry point for testing."""
    fetcher = DataFetcher(verbose=True)

    print("=== Top 10 Protocols by TVL ===")
    protocols = fetcher.fetch_protocols(limit=10)

    for p in protocols:
        print(f"{p.name}: ${p.tvl / 1e9:.2f}B ({p.tvl_change_24h:+.1f}% 24h)")


if __name__ == "__main__":
    main()
