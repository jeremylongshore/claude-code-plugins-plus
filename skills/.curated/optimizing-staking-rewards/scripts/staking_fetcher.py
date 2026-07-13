#!/usr/bin/env python3
"""
Staking Data Fetcher

Fetches staking pool data from DeFiLlama and other sources.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 2.0.0
License: MIT
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, List

try:
    import requests
except ImportError:
    requests = None


# Known staking protocols in DeFiLlama
STAKING_PROTOCOLS = {
    "lido": {"name": "Lido", "type": "liquid", "fee": 0.10, "assets": ["ETH", "SOL", "MATIC"]},
    "rocket-pool": {"name": "Rocket Pool", "type": "liquid", "fee": 0.14, "assets": ["ETH"]},
    "frax-ether": {"name": "Frax Ether", "type": "liquid", "fee": 0.10, "assets": ["ETH"]},
    "coinbase-wrapped-staked-eth": {"name": "Coinbase cbETH", "type": "liquid", "fee": 0.25, "assets": ["ETH"]},
    "marinade-finance": {"name": "Marinade", "type": "liquid", "fee": 0.06, "assets": ["SOL"]},
    "benqi-staked-avax": {"name": "Benqi sAVAX", "type": "liquid", "fee": 0.10, "assets": ["AVAX"]},
    "ankr": {"name": "Ankr", "type": "liquid", "fee": 0.10, "assets": ["ETH", "BNB", "AVAX", "MATIC"]},
    "stakewise": {"name": "StakeWise", "type": "liquid", "fee": 0.10, "assets": ["ETH"]},
    "swell": {"name": "Swell", "type": "liquid", "fee": 0.10, "assets": ["ETH"]},
    "stader": {"name": "Stader", "type": "liquid", "fee": 0.10, "assets": ["ETH", "MATIC", "BNB"]},
}

# Native staking rates (approximate, updated periodically)
NATIVE_STAKING = {
    "ETH": {"apr": 4.0, "unbonding": "variable", "min_stake": 32},
    "ATOM": {"apr": 19.0, "unbonding": "21 days", "min_stake": 0.001},
    "DOT": {"apr": 15.0, "unbonding": "28 days", "min_stake": 1},
    "SOL": {"apr": 7.0, "unbonding": "~2 days", "min_stake": 0.01},
    "AVAX": {"apr": 8.0, "unbonding": "2 weeks", "min_stake": 25},
    "NEAR": {"apr": 9.5, "unbonding": "36-48 hours", "min_stake": 1},
    "MATIC": {"apr": 5.0, "unbonding": "3-4 days", "min_stake": 1},
    "ADA": {"apr": 4.5, "unbonding": "instant", "min_stake": 10},
    "BNB": {"apr": 3.0, "unbonding": "7 days", "min_stake": 1},
}

# Asset symbol mappings
ASSET_ALIASES = {
    "ETHEREUM": "ETH",
    "WETH": "ETH",
    "STETH": "ETH",
    "RETH": "ETH",
    "COSMOS": "ATOM",
    "POLKADOT": "DOT",
    "SOLANA": "SOL",
    "AVALANCHE": "AVAX",
    "POLYGON": "MATIC",
    "CARDANO": "ADA",
    "BINANCE": "BNB",
}


class StakingFetcher:
    """Fetches staking data from multiple sources."""

    def __init__(self, use_cache: bool = True, verbose: bool = False):
        """Initialize fetcher.

        Args:
            use_cache: Whether to use cached data
            verbose: Enable verbose output
        """
        self.use_cache = use_cache
        self.verbose = verbose
        self.cache_file = Path.home() / ".staking_optimizer_cache.json"
        self.cache_ttl = 300  # 5 minutes
        self._cache = self._load_cache()

    def _load_cache(self) -> Dict[str, Any]:
        """Load cache from file."""
        if not self.use_cache:
            return {}

        try:
            if self.cache_file.exists():
                with open(self.cache_file) as f:
                    return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
        return {}

    def _save_cache(self) -> None:
        """Save cache to file."""
        if not self.use_cache:
            return

        try:
            with open(self.cache_file, "w") as f:
                json.dump(self._cache, f)
        except IOError:
            pass

    def _is_cache_valid(self, key: str) -> bool:
        """Check if cached data is still valid."""
        if key not in self._cache:
            return False

        cached_time = self._cache.get(f"{key}_time", 0)
        return time.time() - cached_time < self.cache_ttl

    def fetch_all_staking_pools(self) -> List[Dict[str, Any]]:
        """Fetch all staking-related pools from DeFiLlama.

        Returns:
            List of staking pool data
        """
        cache_key = "all_staking_pools"
        if self._is_cache_valid(cache_key):
            if self.verbose:
                print("Using cached staking pool data")
            return self._cache[cache_key]

        if not requests:
            if self.verbose:
                print("Warning: requests library not available, using static data")
            return self._get_fallback_pools()

        try:
            if self.verbose:
                print("Fetching staking pools from DeFiLlama...")

            response = requests.get("https://yields.llama.fi/pools", timeout=30)
            response.raise_for_status()
            data = response.json()

            pools = data.get("data", [])

            # Filter for staking-related pools
            staking_pools = []
            for pool in pools:
                project = pool.get("project", "").lower()
                symbol = pool.get("symbol", "").upper()
                category = pool.get("category", "").lower()

                # Check if it's a known staking protocol
                is_staking = (
                    project in STAKING_PROTOCOLS
                    or category == "liquid staking"
                    or any(kw in project for kw in ["stak", "lsd"])
                    or any(kw in symbol for kw in ["STETH", "RETH", "CBETH", "FRXETH", "MSOL", "SAVAX"])
                )

                if is_staking:
                    # Enrich with protocol metadata
                    protocol_meta = STAKING_PROTOCOLS.get(project, {})
                    pool["protocol_meta"] = protocol_meta
                    pool["staking_type"] = protocol_meta.get("type", "liquid")
                    pool["protocol_fee"] = protocol_meta.get("fee", 0.10)
                    staking_pools.append(pool)

            if self.verbose:
                print(f"Found {len(staking_pools)} staking pools")

            # Cache results
            self._cache[cache_key] = staking_pools
            self._cache[f"{cache_key}_time"] = time.time()
            self._save_cache()

            return staking_pools

        except requests.RequestException as e:
            if self.verbose:
                print(f"API error: {e}, using fallback data")
            return self._get_fallback_pools()

    def fetch_pools_by_asset(self, asset: str, include_native: bool = True) -> List[Dict[str, Any]]:
        """Fetch staking pools for a specific asset.

        Args:
            asset: Asset symbol (ETH, SOL, etc.)
            include_native: Include native staking option

        Returns:
            List of staking options for the asset
        """
        # Normalize asset symbol
        asset = asset.upper()
        asset = ASSET_ALIASES.get(asset, asset)

        all_pools = self.fetch_all_staking_pools()

        # Filter for this asset
        asset_pools = []
        for pool in all_pools:
            symbol = pool.get("symbol", "").upper()
            # Check if asset is in the pool symbol
            if asset in symbol or f"W{asset}" in symbol:
                pool["base_asset"] = asset
                asset_pools.append(pool)

        # Add native staking option
        if include_native and asset in NATIVE_STAKING:
            native = NATIVE_STAKING[asset]
            native_pool = {
                "pool": f"{asset}-native-staking",
                "project": f"{asset} Native",
                "symbol": asset,
                "chain": self._get_chain_for_asset(asset),
                "apy": native["apr"],
                "apyBase": native["apr"],
                "tvlUsd": self._estimate_native_tvl(asset),
                "staking_type": "native",
                "protocol_fee": 0,
                "unbonding": native["unbonding"],
                "min_stake": native["min_stake"],
                "base_asset": asset,
            }
            asset_pools.append(native_pool)

        # Sort by APY descending
        asset_pools.sort(key=lambda x: x.get("apy", 0) or 0, reverse=True)

        return asset_pools

    def fetch_pool_by_protocol(self, protocol: str) -> List[Dict[str, Any]]:
        """Fetch pools for a specific protocol.

        Args:
            protocol: Protocol name (lido, rocket-pool, etc.)

        Returns:
            List of pools for the protocol
        """
        protocol = protocol.lower().replace(" ", "-")
        all_pools = self.fetch_all_staking_pools()

        return [p for p in all_pools if p.get("project", "").lower() == protocol]

    def _get_chain_for_asset(self, asset: str) -> str:
        """Get the primary chain for an asset."""
        chain_map = {
            "ETH": "Ethereum",
            "SOL": "Solana",
            "ATOM": "Cosmos",
            "DOT": "Polkadot",
            "AVAX": "Avalanche",
            "MATIC": "Polygon",
            "NEAR": "Near",
            "ADA": "Cardano",
            "BNB": "BSC",
        }
        return chain_map.get(asset, "Unknown")

    def _estimate_native_tvl(self, asset: str) -> float:
        """Estimate native staking TVL (rough approximations)."""
        tvl_estimates = {
            "ETH": 50_000_000_000,  # ~$50B
            "SOL": 15_000_000_000,  # ~$15B
            "ATOM": 5_000_000_000,  # ~$5B
            "DOT": 8_000_000_000,  # ~$8B
            "AVAX": 4_000_000_000,  # ~$4B
            "MATIC": 3_000_000_000,  # ~$3B
            "ADA": 10_000_000_000,  # ~$10B
        }
        return tvl_estimates.get(asset, 1_000_000_000)

    def _get_fallback_pools(self) -> List[Dict[str, Any]]:
        """Return static fallback data when API is unavailable."""
        fallback = []

        # Generate fallback data from known protocols
        for project_key, meta in STAKING_PROTOCOLS.items():
            for asset in meta.get("assets", []):
                fallback.append(
                    {
                        "pool": f"{project_key}-{asset.lower()}",
                        "project": project_key,
                        "symbol": f"st{asset}" if meta["type"] == "liquid" else asset,
                        "chain": self._get_chain_for_asset(asset),
                        "apy": self._get_estimated_apy(project_key, asset),
                        "apyBase": self._get_estimated_apy(project_key, asset),
                        "tvlUsd": self._get_estimated_tvl(project_key),
                        "staking_type": meta["type"],
                        "protocol_fee": meta["fee"],
                        "protocol_meta": meta,
                        "base_asset": asset,
                    }
                )

        return fallback

    def _get_estimated_apy(self, protocol: str, asset: str) -> float:
        """Get estimated APY for a protocol/asset pair."""
        # Rough estimates based on typical rates
        estimates = {
            ("lido", "ETH"): 4.0,
            ("lido", "SOL"): 7.0,
            ("rocket-pool", "ETH"): 4.2,
            ("frax-ether", "ETH"): 5.1,
            ("coinbase-wrapped-staked-eth", "ETH"): 3.8,
            ("marinade-finance", "SOL"): 7.5,
            ("benqi-staked-avax", "AVAX"): 6.5,
        }
        return estimates.get((protocol, asset), 4.0)

    def _get_estimated_tvl(self, protocol: str) -> float:
        """Get estimated TVL for a protocol."""
        tvl_estimates = {
            "lido": 15_000_000_000,
            "rocket-pool": 3_000_000_000,
            "frax-ether": 450_000_000,
            "coinbase-wrapped-staked-eth": 2_000_000_000,
            "marinade-finance": 1_500_000_000,
            "benqi-staked-avax": 200_000_000,
        }
        return tvl_estimates.get(protocol, 100_000_000)


def main():
    """CLI entry point for testing."""
    fetcher = StakingFetcher(verbose=True)

    print("\n" + "=" * 60)
    print("Fetching ETH staking options...")
    print("=" * 60)

    pools = fetcher.fetch_pools_by_asset("ETH")

    for pool in pools[:10]:
        name = pool.get("project", "?")
        symbol = pool.get("symbol", "?")
        apy = pool.get("apy", 0) or 0
        tvl = pool.get("tvlUsd", 0) or 0
        stype = pool.get("staking_type", "?")

        print(f"\n{name} ({symbol})")
        print(f"  Type: {stype}")
        print(f"  APY: {apy:.2f}%")
        print(f"  TVL: ${tvl:,.0f}")


if __name__ == "__main__":
    main()
