#!/usr/bin/env python3
"""
Blockchain Event Monitor

Monitor DEX factory events for new pair creations.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 1.0.0
License: MIT
"""

import os
import time
from dataclasses import dataclass
from typing import Dict, Any, List, Optional

try:
    import requests
except ImportError:
    requests = None

from dex_sources import (
    get_chain_config,
    get_dex_factories,
    identify_dex,
    is_base_token,
    PAIR_CREATED_TOPIC,
)


@dataclass
class PairCreated:
    """New trading pair event."""

    block_number: int
    tx_hash: str
    timestamp: int
    pair_address: str
    token0: str
    token1: str
    dex: str
    chain: str
    factory_address: str


@dataclass
class TokenBasicInfo:
    """Basic token info from RPC."""

    address: str
    name: str
    symbol: str
    decimals: int


class EventMonitor:
    """Monitor blockchain events for new pairs."""

    def __init__(self, chain: str = "ethereum", rpc_url: str = None, verbose: bool = False):
        """Initialize event monitor.

        Args:
            chain: Chain to monitor
            rpc_url: Custom RPC URL
            verbose: Enable verbose output
        """
        self.chain = chain.lower()
        self.config = get_chain_config(chain)
        self.rpc_url = rpc_url or os.environ.get(f"{chain.upper()}_RPC_URL", self.config.rpc_url)
        self.verbose = verbose
        # Use a size-limited cache to prevent memory leaks on long-running instances
        # Keeps most recent 1000 block timestamps
        self._block_cache = {}
        self._block_cache_max_size = 1000

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

    def _get_block_timestamp(self, block_number: int) -> int:
        """Get block timestamp with size-limited caching."""
        if block_number in self._block_cache:
            return self._block_cache[block_number]

        block = self._rpc_call("eth_getBlockByNumber", [hex(block_number), False])

        if block:
            timestamp = int(block.get("timestamp", "0x0"), 16)

            # Evict old entries if cache is full
            if len(self._block_cache) >= self._block_cache_max_size:
                # Remove oldest entries (first 100)
                oldest_keys = sorted(self._block_cache.keys())[:100]
                for key in oldest_keys:
                    del self._block_cache[key]

            self._block_cache[block_number] = timestamp
            return timestamp

        return int(time.time())

    def get_current_block(self) -> int:
        """Get current block number."""
        result = self._rpc_call("eth_blockNumber")
        return int(result, 16)

    def get_recent_pairs(self, hours: int = 24, dex: str = None) -> List[PairCreated]:
        """Get recently created pairs.

        Args:
            hours: Hours to look back
            dex: Filter by specific DEX

        Returns:
            List of PairCreated events
        """
        current_block = self.get_current_block()
        blocks_per_hour = int(3600 / self.config.block_time)
        from_block = current_block - (blocks_per_hour * hours)

        factories = get_dex_factories(self.chain)
        factory_addresses = []

        for name, factory in factories.items():
            if dex is None or dex.lower() in name.lower():
                factory_addresses.append(factory.address)

        if not factory_addresses:
            return []

        pairs = []

        for factory_addr in factory_addresses:
            try:
                logs = self._rpc_call(
                    "eth_getLogs",
                    [
                        {
                            "fromBlock": hex(from_block),
                            "toBlock": "latest",
                            "address": factory_addr,
                            "topics": [PAIR_CREATED_TOPIC],
                        }
                    ],
                )

                for log in logs or []:
                    pair = self._parse_pair_created(log, factory_addr)
                    if pair:
                        pairs.append(pair)

            except Exception as e:
                if self.verbose:
                    print(f"Error fetching logs from {factory_addr}: {e}")

        # Sort by block number descending (newest first)
        pairs.sort(key=lambda x: x.block_number, reverse=True)

        return pairs

    def _parse_pair_created(self, log: Dict, factory_address: str) -> Optional[PairCreated]:
        """Parse PairCreated event log."""
        try:
            block_number = int(log["blockNumber"], 16)
            tx_hash = log["transactionHash"]
            topics = log.get("topics", [])
            data = log.get("data", "0x")

            # For Uniswap V2 style: topics[1] = token0, topics[2] = token1
            # data contains pair address and pair index
            if len(topics) >= 3:
                token0 = "0x" + topics[1][-40:]
                token1 = "0x" + topics[2][-40:]

                # Pair address is first 32 bytes of data
                pair_address = "0x" + data[26:66]

                timestamp = self._get_block_timestamp(block_number)
                dex = identify_dex(self.chain, factory_address)

                return PairCreated(
                    block_number=block_number,
                    tx_hash=tx_hash,
                    timestamp=timestamp,
                    pair_address=pair_address,
                    token0=token0,
                    token1=token1,
                    dex=dex,
                    chain=self.chain,
                    factory_address=factory_address,
                )

        except Exception as e:
            if self.verbose:
                print(f"Error parsing log: {e}")

        return None

    def get_token_info(self, address: str) -> Optional[TokenBasicInfo]:
        """Get basic token info via RPC calls.

        Args:
            address: Token contract address

        Returns:
            TokenBasicInfo or None
        """
        try:
            # ERC20 function signatures
            name_sig = "0x06fdde03"  # name()
            symbol_sig = "0x95d89b41"  # symbol()
            decimals_sig = "0x313ce567"  # decimals()

            name = self._call_contract(address, name_sig)
            symbol = self._call_contract(address, symbol_sig)
            decimals = self._call_contract(address, decimals_sig)

            return TokenBasicInfo(
                address=address,
                name=self._decode_string(name) if name else "Unknown",
                symbol=self._decode_string(symbol) if symbol else "???",
                decimals=int(decimals, 16) if decimals else 18,
            )

        except Exception as e:
            if self.verbose:
                print(f"Error getting token info for {address}: {e}")
            return None

    def _call_contract(self, address: str, data: str) -> Optional[str]:
        """Make eth_call to contract."""
        try:
            result = self._rpc_call("eth_call", [{"to": address, "data": data}, "latest"])
            return result if result and result != "0x" else None
        except Exception:
            return None

    def _decode_string(self, data: str) -> str:
        """Decode string from ABI-encoded data."""
        if not data or data == "0x":
            return ""

        try:
            # Remove 0x prefix
            data = data[2:]

            # If short string (< 32 bytes, not ABI encoded)
            if len(data) <= 64:
                return bytes.fromhex(data).decode("utf-8", errors="ignore").strip("\x00")

            # ABI encoded string: offset (32 bytes) + length (32 bytes) + data
            if len(data) >= 128:
                length = int(data[64:128], 16)
                string_data = data[128 : 128 + length * 2]
                return bytes.fromhex(string_data).decode("utf-8", errors="ignore")

            return bytes.fromhex(data).decode("utf-8", errors="ignore").strip("\x00")

        except Exception:
            return "Unknown"

    def identify_new_token(self, pair: PairCreated) -> str:
        """Identify which token in the pair is the new one.

        Args:
            pair: PairCreated event

        Returns:
            Address of the new token
        """
        # If one is a base token (WETH, stablecoin), the other is new
        if is_base_token(self.chain, pair.token0):
            return pair.token1
        if is_base_token(self.chain, pair.token1):
            return pair.token0

        # Otherwise, consider both as potentially new
        return pair.token0


def main():
    """CLI entry point for testing."""
    monitor = EventMonitor(chain="ethereum", verbose=True)

    print("=== Recent Pairs (Last 1 Hour) ===")
    pairs = monitor.get_recent_pairs(hours=1)

    if not pairs:
        print("No new pairs found")
        return

    for pair in pairs[:10]:
        print(f"\n{pair.dex} on {pair.chain}")
        print(f"  Block: {pair.block_number}")
        print(f"  Pair: {pair.pair_address[:20]}...")
        print(f"  Token0: {pair.token0[:20]}...")
        print(f"  Token1: {pair.token1[:20]}...")

        # Get token info
        new_token = monitor.identify_new_token(pair)
        token_info = monitor.get_token_info(new_token)
        if token_info:
            print(f"  New Token: {token_info.symbol} ({token_info.name})")


if __name__ == "__main__":
    main()
