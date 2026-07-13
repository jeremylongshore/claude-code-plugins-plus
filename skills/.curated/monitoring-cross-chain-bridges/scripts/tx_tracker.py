#!/usr/bin/env python3
"""
Bridge Transaction Tracker

Track cross-chain bridge transactions.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 1.0.0
License: MIT
"""

from datetime import datetime
from typing import Dict, Any, List, Optional

try:
    import requests
except ImportError:
    requests = None

from protocol_adapters import (
    TxStatus,
    get_adapter,
    ADAPTERS,
)
from config_loader import get_chain_rpc_url


class TxTracker:
    """Track bridge transactions across protocols."""

    def __init__(self, verbose: bool = False):
        """Initialize transaction tracker.

        Args:
            verbose: Enable verbose output
        """
        if not requests:
            raise ImportError("requests library required: pip install requests")

        self.verbose = verbose

    def _rpc_call(self, chain: str, method: str, params: List = None) -> Any:
        """Make RPC call to chain.

        Args:
            chain: Chain name
            method: RPC method
            params: Method parameters

        Returns:
            RPC result
        """
        # Config loader checks environment variable first, then settings.yaml
        rpc_url = get_chain_rpc_url(chain)

        if not rpc_url:
            raise ValueError(f"No RPC URL for chain: {chain}")

        response = requests.post(
            rpc_url,
            json={
                "jsonrpc": "2.0",
                "method": method,
                "params": params or [],
                "id": 1,
            },
            timeout=30,
        )
        response.raise_for_status()

        result = response.json()
        if "error" in result:
            raise Exception(f"RPC error: {result['error']}")

        return result.get("result")

    def verify_tx_on_chain(self, chain: str, tx_hash: str) -> Dict[str, Any]:
        """Verify transaction exists on chain.

        Args:
            chain: Chain name
            tx_hash: Transaction hash

        Returns:
            Transaction receipt or status dict
        """
        try:
            receipt = self._rpc_call(chain, "eth_getTransactionReceipt", [tx_hash])

            if receipt:
                return {
                    "found": True,
                    "block": int(receipt.get("blockNumber", "0x0"), 16),
                    "status": "success" if receipt.get("status") == "0x1" else "failed",
                    "gas_used": int(receipt.get("gasUsed", "0x0"), 16),
                }
            else:
                # Check if pending
                tx = self._rpc_call(chain, "eth_getTransactionByHash", [tx_hash])
                if tx:
                    return {
                        "found": True,
                        "block": None,
                        "status": "pending",
                        "gas_used": None,
                    }

            return {"found": False, "status": "not_found"}

        except (requests.RequestException, KeyError, ValueError) as e:
            if self.verbose:
                print(f"Error verifying tx: {e}")
            return {"found": False, "status": "error", "error": str(e)}

    def track_bridge_tx(self, tx_hash: str, bridge: str = None, source_chain: str = None) -> Optional[TxStatus]:
        """Track a bridge transaction.

        Args:
            tx_hash: Transaction hash
            bridge: Bridge name (optional, will auto-detect)
            source_chain: Source chain (optional)

        Returns:
            TxStatus or None
        """
        # If bridge specified, use that adapter
        if bridge:
            adapter = get_adapter(bridge)
            if adapter:
                status = adapter.get_tx_status(tx_hash)
                if status:
                    return status

        # Try all adapters
        for name, adapter in ADAPTERS.items():
            if self.verbose:
                print(f"Trying {name}...")

            status = adapter.get_tx_status(tx_hash)
            if status and status.status != "not_found":
                return status

        # If source chain provided, verify on-chain
        if source_chain:
            verification = self.verify_tx_on_chain(source_chain, tx_hash)
            if verification.get("found"):
                return TxStatus(
                    tx_hash=tx_hash,
                    bridge="Unknown",
                    source_chain=source_chain,
                    dest_chain="Unknown",
                    status=verification.get("status", "unknown"),
                    source_confirmed=verification.get("status") == "success",
                    dest_confirmed=False,
                )

        return None

    def get_tx_status_all_bridges(self, tx_hash: str) -> Dict[str, Optional[TxStatus]]:
        """Check tx status across all bridges.

        Args:
            tx_hash: Transaction hash

        Returns:
            Dict of bridge -> TxStatus
        """
        results = {}

        for name, adapter in ADAPTERS.items():
            status = adapter.get_tx_status(tx_hash)
            if status and status.status != "not_found":
                results[name] = status

        return results

    def estimate_completion_time(self, bridge: str, source_chain: str, dest_chain: str) -> int:
        """Estimate completion time in minutes.

        Args:
            bridge: Bridge name
            source_chain: Source chain
            dest_chain: Destination chain

        Returns:
            Estimated minutes
        """
        # Base estimates by bridge
        base_times = {
            "wormhole": 15,
            "layerzero": 3,
            "stargate": 2,
            "across": 1,
            "hop": 5,
            "celer": 10,
            "synapse": 10,
            "multichain": 20,
        }

        base = base_times.get(bridge.lower(), 15)

        # Adjust for chain finality
        slow_chains = {"ethereum": 1.5, "polygon": 1.2}
        fast_chains = {"arbitrum": 0.8, "optimism": 0.8, "base": 0.8}

        multiplier = 1.0
        if source_chain.lower() in slow_chains:
            multiplier *= slow_chains[source_chain.lower()]
        if dest_chain.lower() in fast_chains:
            multiplier *= fast_chains[dest_chain.lower()]

        return int(base * multiplier)


def format_status(status: TxStatus) -> str:
    """Format status for display.

    Args:
        status: TxStatus object

    Returns:
        Formatted string
    """
    lines = [
        "",
        "BRIDGE TRANSACTION STATUS",
        "=" * 60,
        f"TX Hash:      {status.tx_hash}",
        f"Bridge:       {status.bridge}",
        f"Route:        {status.source_chain} → {status.dest_chain}",
        f"Status:       {status.status.upper()}",
        "",
        "CONFIRMATION STATUS",
        "-" * 60,
        f"Source:       {'Confirmed' if status.source_confirmed else 'Pending'}",
        f"Destination:  {'Confirmed' if status.dest_confirmed else 'Pending'}",
    ]

    if status.amount:
        lines.append(f"Amount:       {status.amount} {status.token or ''}")

    if status.dest_tx_hash:
        lines.append(f"Dest TX:      {status.dest_tx_hash}")

    if status.timestamp:
        dt = datetime.fromtimestamp(status.timestamp)
        lines.append(f"Timestamp:    {dt.strftime('%Y-%m-%d %H:%M:%S')}")

    lines.append("=" * 60)

    return "\n".join(lines)


def main():
    """CLI entry point for testing."""
    tracker = TxTracker(verbose=True)

    # Test with a sample tx hash (this won't find anything real)
    test_hash = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"

    print("=== Transaction Tracker ===")
    print(f"Tracking: {test_hash[:20]}...")

    status = tracker.track_bridge_tx(test_hash)
    if status:
        print(format_status(status))
    else:
        print("Transaction not found in any bridge")

    print("\n=== Completion Time Estimates ===")
    bridges = ["wormhole", "layerzero", "stargate", "across"]
    for bridge in bridges:
        time_est = tracker.estimate_completion_time(bridge, "ethereum", "arbitrum")
        print(f"  {bridge}: ~{time_est} minutes (ETH → ARB)")


if __name__ == "__main__":
    main()
