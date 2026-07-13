#!/usr/bin/env python3
"""
Bridge Data Fetcher

Fetch bridge data from DefiLlama and other APIs.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 1.0.0
License: MIT
"""

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional

try:
    import requests
except ImportError:
    requests = None

from config_loader import get_api_base_url


@dataclass
class BridgeInfo:
    """Bridge protocol information."""

    id: str
    name: str
    display_name: str
    icon: str
    volume_prev_day: float
    volume_prev2_day: float
    chains: List[str] = field(default_factory=list)
    destination_chains: List[str] = field(default_factory=list)


@dataclass
class TVLData:
    """Bridge TVL data."""

    bridge_id: str
    total_tvl: float
    tvl_by_chain: Dict[str, float] = field(default_factory=dict)
    tvl_by_token: Dict[str, float] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class ChainVolume:
    """Volume data by chain."""

    chain: str
    total_volume_24h: float
    total_volume_7d: float
    inflow_24h: float
    outflow_24h: float
    net_flow_24h: float


@dataclass
class BridgeVolume:
    """Daily volume data for a bridge."""

    date: str
    deposit_usd: float
    withdraw_usd: float
    deposit_txs: int
    withdraw_txs: int


# DefiLlama API endpoints
DEFILLAMA_BASE = "https://bridges.llama.fi"


class BridgeFetcher:
    """Fetch bridge data from APIs."""

    def __init__(self, verbose: bool = False):
        """Initialize bridge fetcher.

        Args:
            verbose: Enable verbose output
        """
        if not requests:
            raise ImportError("requests library required: pip install requests")

        self.verbose = verbose
        self._cache: Dict[str, Any] = {}
        self._cache_times: Dict[str, float] = {}
        self._cache_ttl = 300  # 5 minutes

    def _get_cached(self, key: str) -> Optional[Any]:
        """Get cached value if not expired."""
        if key in self._cache:
            if time.time() - self._cache_times.get(key, 0) < self._cache_ttl:
                return self._cache[key]
        return None

    def _set_cached(self, key: str, value: Any):
        """Set cached value."""
        self._cache[key] = value
        self._cache_times[key] = time.time()

    def _api_call(self, endpoint: str) -> Any:
        """Make API call to DefiLlama."""
        base_url = get_api_base_url("defillama")
        url = f"{base_url}{endpoint}"

        if self.verbose:
            print(f"API: {url}")

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            if self.verbose:
                print(f"API error: {e}")
            raise

    def get_all_bridges(self) -> List[BridgeInfo]:
        """Get list of all bridges.

        Returns:
            List of BridgeInfo objects
        """
        cached = self._get_cached("bridges")
        if cached:
            return cached

        data = self._api_call("/bridges")
        bridges = []

        for item in data.get("bridges", []):
            bridge = BridgeInfo(
                id=str(item.get("id", "")),
                name=item.get("name", ""),
                display_name=item.get("displayName", item.get("name", "")),
                icon=item.get("icon", ""),
                volume_prev_day=item.get("volumePrevDay", 0) or 0,
                volume_prev2_day=item.get("volumePrev2Day", 0) or 0,
                chains=item.get("chains", []),
                destination_chains=item.get("destinationChain", []),
            )
            bridges.append(bridge)

        # Sort by volume
        bridges.sort(key=lambda x: x.volume_prev_day, reverse=True)

        self._set_cached("bridges", bridges)
        return bridges

    def get_bridge_by_name(self, name: str) -> Optional[BridgeInfo]:
        """Get bridge by name (case-insensitive).

        Args:
            name: Bridge name to search

        Returns:
            BridgeInfo or None
        """
        bridges = self.get_all_bridges()
        name_lower = name.lower()

        for bridge in bridges:
            if bridge.name.lower() == name_lower or bridge.display_name.lower() == name_lower or bridge.id == name:
                return bridge

        return None

    def get_bridge_tvl(self, bridge_id: str) -> Optional[TVLData]:
        """Get TVL data for a bridge.

        Args:
            bridge_id: Bridge ID

        Returns:
            TVLData or None
        """
        cache_key = f"tvl_{bridge_id}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        try:
            data = self._api_call(f"/bridge/{bridge_id}")

            tvl_by_chain = {}
            tvl_by_token = {}
            total_tvl = 0

            # Parse chain TVL from currentChainTvls
            chain_tvls = data.get("currentChainTvls", {})
            for chain, tvl in chain_tvls.items():
                if isinstance(tvl, (int, float)):
                    tvl_by_chain[chain] = tvl
                    total_tvl += tvl

            # Parse token TVL if available
            token_tvls = data.get("tokens", {})
            for token, tvl in token_tvls.items():
                if isinstance(tvl, (int, float)):
                    tvl_by_token[token] = tvl

            result = TVLData(
                bridge_id=bridge_id,
                total_tvl=total_tvl,
                tvl_by_chain=tvl_by_chain,
                tvl_by_token=tvl_by_token,
                last_updated=datetime.now(),
            )

            self._set_cached(cache_key, result)
            return result

        except (requests.RequestException, KeyError, ValueError) as e:
            if self.verbose:
                print(f"Error fetching TVL for {bridge_id}: {e}")
            return None

    def get_chain_volume(self, chain: str) -> Optional[ChainVolume]:
        """Get bridge volume for a chain.

        Args:
            chain: Chain name

        Returns:
            ChainVolume or None
        """
        cache_key = f"chain_vol_{chain}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        try:
            data = self._api_call(f"/bridgevolume/{chain}")

            # Sum up volumes from all bridges
            total_24h = 0
            total_7d = 0
            inflow_24h = 0
            outflow_24h = 0

            for item in data:
                total_24h += item.get("volumeUsd", 0) or 0

            result = ChainVolume(
                chain=chain,
                total_volume_24h=total_24h,
                total_volume_7d=total_7d,  # Would need 7-day data
                inflow_24h=inflow_24h,
                outflow_24h=outflow_24h,
                net_flow_24h=inflow_24h - outflow_24h,
            )

            self._set_cached(cache_key, result)
            return result

        except (requests.RequestException, KeyError, ValueError) as e:
            if self.verbose:
                print(f"Error fetching volume for {chain}: {e}")
            return None

    def get_bridge_volume_history(self, bridge_id: str, days: int = 7) -> List[BridgeVolume]:
        """Get historical volume for a bridge.

        Args:
            bridge_id: Bridge ID
            days: Number of days

        Returns:
            List of BridgeVolume objects
        """
        try:
            data = self._api_call(f"/bridgevolume/{bridge_id}")

            volumes = []
            for item in data[-days:] if len(data) > days else data:
                vol = BridgeVolume(
                    date=item.get("date", ""),
                    deposit_usd=item.get("depositUSD", 0) or 0,
                    withdraw_usd=item.get("withdrawUSD", 0) or 0,
                    deposit_txs=item.get("depositTxs", 0) or 0,
                    withdraw_txs=item.get("withdrawTxs", 0) or 0,
                )
                volumes.append(vol)

            return volumes

        except (requests.RequestException, KeyError, ValueError) as e:
            if self.verbose:
                print(f"Error fetching volume history for {bridge_id}: {e}")
            return []

    def get_all_chains(self) -> List[str]:
        """Get list of all chains with bridge activity.

        Returns:
            List of chain names
        """
        bridges = self.get_all_bridges()
        chains = set()

        for bridge in bridges:
            chains.update(bridge.chains)
            chains.update(bridge.destination_chains)

        return sorted(chains)

    def search_bridges(self, query: str) -> List[BridgeInfo]:
        """Search bridges by name.

        Args:
            query: Search query

        Returns:
            Matching bridges
        """
        bridges = self.get_all_bridges()
        query_lower = query.lower()

        return [b for b in bridges if query_lower in b.name.lower() or query_lower in b.display_name.lower()]


def main():
    """CLI entry point for testing."""
    fetcher = BridgeFetcher(verbose=True)

    print("=== All Bridges ===")
    bridges = fetcher.get_all_bridges()
    for bridge in bridges[:10]:
        print(f"  {bridge.display_name}: ${bridge.volume_prev_day:,.0f} (24h)")

    print("\n=== Top Bridge TVL ===")
    if bridges:
        tvl = fetcher.get_bridge_tvl(bridges[0].id)
        if tvl:
            print(f"  {bridges[0].display_name}: ${tvl.total_tvl:,.0f}")
            for chain, amount in sorted(tvl.tvl_by_chain.items(), key=lambda x: -x[1])[:5]:
                print(f"    {chain}: ${amount:,.0f}")

    print("\n=== Supported Chains ===")
    chains = fetcher.get_all_chains()
    print(f"  {len(chains)} chains: {', '.join(chains[:10])}...")


if __name__ == "__main__":
    main()
