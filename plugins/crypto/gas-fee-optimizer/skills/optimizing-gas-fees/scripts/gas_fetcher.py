#!/usr/bin/env python3
"""
Gas Data Fetcher

Fetch gas prices from multiple sources.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 1.0.0
License: MIT
"""

import json
import os
import time
from pathlib import Path
from typing import Dict, Any, List
from dataclasses import dataclass

try:
    import requests
except ImportError:
    requests = None


# Chain configurations
CHAIN_CONFIG = {
    "ethereum": {
        "rpc": "https://eth.llamarpc.com",
        "explorer_api": "https://api.etherscan.io/api",
        "native_symbol": "ETH",
        "chain_id": 1,
    },
    "polygon": {
        "rpc": "https://polygon-rpc.com",
        "explorer_api": "https://api.polygonscan.com/api",
        "native_symbol": "MATIC",
        "chain_id": 137,
    },
    "arbitrum": {
        "rpc": "https://arb1.arbitrum.io/rpc",
        "explorer_api": "https://api.arbiscan.io/api",
        "native_symbol": "ETH",
        "chain_id": 42161,
    },
    "optimism": {
        "rpc": "https://mainnet.optimism.io",
        "explorer_api": "https://api-optimistic.etherscan.io/api",
        "native_symbol": "ETH",
        "chain_id": 10,
    },
    "base": {
        "rpc": "https://mainnet.base.org",
        "explorer_api": "https://api.basescan.org/api",
        "native_symbol": "ETH",
        "chain_id": 8453,
    },
}


@dataclass
class GasData:
    """Gas price data."""

    chain: str
    base_fee: int  # in wei
    priority_fee: int  # in wei
    gas_price: int  # legacy gas price in wei
    slow: int  # 10th percentile
    standard: int  # 50th percentile
    fast: int  # 75th percentile
    instant: int  # 90th percentile
    timestamp: int
    source: str


@dataclass
class BaseFeeHistory:
    """Base fee history entry."""

    block_number: int
    base_fee: int
    gas_used_ratio: float
    timestamp: int


class GasFetcher:
    """Fetch gas prices from multiple sources."""

    def __init__(self, chain: str = "ethereum", rpc_url: str = None, api_key: str = None, verbose: bool = False):
        """Initialize gas fetcher.

        Args:
            chain: Blockchain network
            rpc_url: Custom RPC URL
            api_key: Explorer API key
            verbose: Enable verbose output
        """
        self.chain = chain.lower()
        self.config = CHAIN_CONFIG.get(self.chain, CHAIN_CONFIG["ethereum"])
        self.rpc_url = rpc_url or os.environ.get(f"{chain.upper()}_RPC_URL") or self.config["rpc"]
        self.api_key = api_key or os.environ.get("ETHERSCAN_API_KEY", "")
        self.verbose = verbose
        self.cache_file = Path.home() / f".gas_cache_{chain}.json"
        self.cache_ttl = 15  # seconds
        self._cache = self._load_cache()

    def _load_cache(self) -> Dict[str, Any]:
        """Load cache from file."""
        try:
            if self.cache_file.exists():
                with open(self.cache_file) as f:
                    return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass  # Cache file corrupted or missing - start fresh
        return {}

    def _save_cache(self) -> None:
        """Save cache to file."""
        try:
            with open(self.cache_file, "w") as f:
                json.dump(self._cache, f)
        except IOError:
            pass  # Non-critical - cache save failed, will refetch next time

    def _is_cache_valid(self, key: str) -> bool:
        """Check if cached data is still valid."""
        if key not in self._cache:
            return False
        cached_time = self._cache.get(f"{key}_time", 0)
        return time.time() - cached_time < self.cache_ttl

    def _rpc_call(self, method: str, params: List = None) -> Any:
        """Make JSON-RPC call."""
        if not requests:
            raise ImportError("requests library required")

        if self.verbose:
            print(f"RPC: {method}")

        response = requests.post(
            self.rpc_url,
            json={
                "jsonrpc": "2.0",
                "method": method,
                "params": params or [],
                "id": 1,
            },
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        response.raise_for_status()

        result = response.json()
        if "error" in result:
            raise Exception(f"RPC error: {result['error']}")

        return result.get("result")

    def get_current_gas(self) -> GasData:
        """Get current gas prices.

        Returns:
            GasData with current prices
        """
        cache_key = "current_gas"
        if self._is_cache_valid(cache_key):
            cached = self._cache[cache_key]
            return GasData(**cached)

        try:
            # Try EIP-1559 style (eth_feeHistory)
            fee_history = self._rpc_call("eth_feeHistory", ["0xa", "latest", [10, 25, 50, 75, 90]])

            if fee_history and fee_history.get("baseFeePerGas"):
                base_fees = [int(x, 16) for x in fee_history["baseFeePerGas"]]
                current_base_fee = base_fees[-1]

                # Get priority fees from percentiles
                rewards = fee_history.get("reward", [])
                if rewards:
                    latest_rewards = rewards[-1]
                    percentiles = [int(x, 16) for x in latest_rewards]

                    gas_data = GasData(
                        chain=self.chain,
                        base_fee=current_base_fee,
                        priority_fee=percentiles[2],  # 50th percentile
                        gas_price=current_base_fee + percentiles[2],
                        slow=current_base_fee + percentiles[0],
                        standard=current_base_fee + percentiles[2],
                        fast=current_base_fee + percentiles[3],
                        instant=current_base_fee + percentiles[4],
                        timestamp=int(time.time()),
                        source="rpc_feeHistory",
                    )
                else:
                    # Fallback without reward data
                    gas_price = int(self._rpc_call("eth_gasPrice"), 16)
                    gas_data = self._make_gas_data_from_price(gas_price, "rpc_gasPrice")
            else:
                # Legacy gas price
                gas_price = int(self._rpc_call("eth_gasPrice"), 16)
                gas_data = self._make_gas_data_from_price(gas_price, "rpc_gasPrice")

        except Exception as e:
            if self.verbose:
                print(f"RPC error: {e}, trying explorer API")
            gas_data = self._get_from_explorer()

        # Cache result
        self._cache[cache_key] = vars(gas_data)
        self._cache[f"{cache_key}_time"] = time.time()
        self._save_cache()

        return gas_data

    def _make_gas_data_from_price(self, gas_price: int, source: str) -> GasData:
        """Create GasData from single gas price."""
        # Estimate tiers from base price
        return GasData(
            chain=self.chain,
            base_fee=int(gas_price * 0.8),
            priority_fee=int(gas_price * 0.2),
            gas_price=gas_price,
            slow=int(gas_price * 0.8),
            standard=gas_price,
            fast=int(gas_price * 1.2),
            instant=int(gas_price * 1.5),
            timestamp=int(time.time()),
            source=source,
        )

    def _get_from_explorer(self) -> GasData:
        """Get gas from blockchain explorer API."""
        if not requests:
            raise ImportError("requests library required")

        params = {
            "module": "gastracker",
            "action": "gasoracle",
        }
        if self.api_key:
            params["apikey"] = self.api_key

        response = requests.get(self.config["explorer_api"], params=params, timeout=30)
        data = response.json()

        if data.get("status") == "1" and data.get("result"):
            result = data["result"]
            # Explorer returns gwei, convert to wei
            safe = int(float(result.get("SafeGasPrice", 30)) * 10**9)
            proposed = int(float(result.get("ProposeGasPrice", 35)) * 10**9)
            fast = int(float(result.get("FastGasPrice", 50)) * 10**9)
            base_fee = (
                int(float(result.get("suggestBaseFee", 25)) * 10**9)
                if result.get("suggestBaseFee")
                else int(proposed * 0.8)
            )

            return GasData(
                chain=self.chain,
                base_fee=base_fee,
                priority_fee=proposed - base_fee,
                gas_price=proposed,
                slow=safe,
                standard=proposed,
                fast=fast,
                instant=int(fast * 1.3),
                timestamp=int(time.time()),
                source="explorer_api",
            )

        # Return defaults
        return self._make_gas_data_from_price(30 * 10**9, "default")

    def get_base_fee_history(self, blocks: int = 100) -> List[BaseFeeHistory]:
        """Get base fee history.

        Args:
            blocks: Number of blocks to fetch

        Returns:
            List of BaseFeeHistory entries
        """
        try:
            fee_history = self._rpc_call("eth_feeHistory", [hex(blocks), "latest", []])

            if not fee_history:
                return []

            base_fees = fee_history.get("baseFeePerGas", [])
            gas_ratios = fee_history.get("gasUsedRatio", [])
            oldest_block = int(fee_history.get("oldestBlock", "0x0"), 16)

            history = []
            for i, (base_fee, ratio) in enumerate(zip(base_fees, gas_ratios)):
                history.append(
                    BaseFeeHistory(
                        block_number=oldest_block + i,
                        base_fee=int(base_fee, 16),
                        gas_used_ratio=ratio,
                        timestamp=0,  # Would need block timestamps
                    )
                )

            return history

        except Exception as e:
            if self.verbose:
                print(f"History fetch error: {e}")
            return []

    def get_gas_for_chain(self, chain: str) -> GasData:
        """Get gas for a specific chain.

        Args:
            chain: Chain name

        Returns:
            GasData for the chain
        """
        fetcher = GasFetcher(chain=chain, verbose=self.verbose)
        return fetcher.get_current_gas()


def main():
    """CLI entry point for testing."""
    fetcher = GasFetcher(verbose=True)

    print("=== Current Gas Prices ===")
    gas = fetcher.get_current_gas()

    print(f"Chain: {gas.chain}")
    print(f"Base Fee: {gas.base_fee / 10**9:.2f} gwei")
    print(f"Priority Fee: {gas.priority_fee / 10**9:.2f} gwei")
    print(f"Source: {gas.source}")
    print()
    print("Tiers:")
    print(f"  Slow:     {gas.slow / 10**9:.2f} gwei")
    print(f"  Standard: {gas.standard / 10**9:.2f} gwei")
    print(f"  Fast:     {gas.fast / 10**9:.2f} gwei")
    print(f"  Instant:  {gas.instant / 10**9:.2f} gwei")

    print("\n=== Base Fee History (last 10 blocks) ===")
    history = fetcher.get_base_fee_history(10)
    for entry in history[-5:]:
        print(f"  Block {entry.block_number}: {entry.base_fee / 10**9:.2f} gwei ({entry.gas_used_ratio:.1%} used)")


if __name__ == "__main__":
    main()
