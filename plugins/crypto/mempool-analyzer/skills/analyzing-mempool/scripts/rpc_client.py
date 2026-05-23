#!/usr/bin/env python3
"""
Ethereum RPC Client

Connect to Ethereum nodes and fetch mempool data.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 1.0.0
License: MIT
"""

import os
import sys
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

try:
    import requests
except ImportError:
    requests = None


# Default RPC endpoints (public, may be rate limited)
DEFAULT_RPC_URLS = {
    "ethereum": "https://eth.llamarpc.com",
    "polygon": "https://polygon-rpc.com",
    "arbitrum": "https://arb1.arbitrum.io/rpc",
    "optimism": "https://mainnet.optimism.io",
    "base": "https://mainnet.base.org",
}


@dataclass
class PendingTransaction:
    """Represents a pending transaction in the mempool."""

    hash: str
    from_address: str
    to_address: Optional[str]
    value: int  # in wei
    gas: int
    gas_price: int  # in wei
    max_fee_per_gas: Optional[int]
    max_priority_fee_per_gas: Optional[int]
    nonce: int
    input_data: str
    block_number: Optional[int]


@dataclass
class GasInfo:
    """Current gas price information."""

    base_fee: int
    priority_fee: int
    gas_price: int  # legacy
    pending_count: int


class RPCClient:
    """Ethereum JSON-RPC client for mempool access."""

    def __init__(self, rpc_url: str = None, chain: str = "ethereum", verbose: bool = False):
        """Initialize RPC client.

        Args:
            rpc_url: Custom RPC URL or None for default
            chain: Chain name for default URL lookup
            verbose: Enable verbose output
        """
        self.rpc_url = rpc_url or os.environ.get("ETH_RPC_URL") or DEFAULT_RPC_URLS.get(chain)
        self.chain = chain
        self.verbose = verbose
        self._request_id = 0

    def _rpc_call(self, method: str, params: List = None) -> Any:
        """Make JSON-RPC call."""
        if not requests:
            raise ImportError("requests library required: pip install requests")

        self._request_id += 1
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or [],
            "id": self._request_id,
        }

        if self.verbose:
            print(f"RPC: {method}")

        response = requests.post(
            self.rpc_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        response.raise_for_status()

        result = response.json()
        if "error" in result:
            raise Exception(f"RPC error: {result['error']}")

        return result.get("result")

    def get_pending_transactions(self, limit: int = 100, allow_mock: bool = False) -> List[PendingTransaction]:
        """Get pending transactions from mempool.

        Note: Not all nodes support txpool_content.

        Args:
            limit: Maximum transactions to return
            allow_mock: If True, return mock data when RPC fails (for demo/testing)

        Returns:
            List of pending transactions

        Raises:
            RuntimeError: If no RPC method succeeds and allow_mock is False
        """
        errors = []

        try:
            # Try txpool_content (Geth nodes)
            result = self._rpc_call("txpool_content")
            if result:
                return self._parse_txpool_content(result, limit)
        except Exception as e:
            errors.append(f"txpool_content: {e}")
            if self.verbose:
                print(f"txpool_content not available: {e}", file=sys.stderr)

        try:
            # Try eth_pendingTransactions (some nodes)
            result = self._rpc_call("eth_pendingTransactions")
            if result:
                return self._parse_pending_transactions(result[:limit])
        except Exception as e:
            errors.append(f"eth_pendingTransactions: {e}")
            if self.verbose:
                print(f"eth_pendingTransactions not available: {e}", file=sys.stderr)

        # If allow_mock is True (demo mode), return mock data with warning
        if allow_mock:
            print("WARNING: Using mock data - could not fetch real mempool data", file=sys.stderr)
            return self._get_mock_pending_transactions(limit)

        # Otherwise raise an exception
        raise RuntimeError(
            f"Could not fetch pending transactions from RPC. "
            f"Both 'txpool_content' and 'eth_pendingTransactions' failed.\n"
            f"Errors: {'; '.join(errors)}\n"
            f"Hint: Use --demo flag to use mock data for testing."
        )

    def _parse_txpool_content(self, content: Dict, limit: int) -> List[PendingTransaction]:
        """Parse txpool_content response."""
        transactions = []

        for pool in ["pending", "queued"]:
            pool_data = content.get(pool, {})
            for address, nonces in pool_data.items():
                for nonce, tx in nonces.items():
                    if len(transactions) >= limit:
                        break
                    transactions.append(self._tx_to_pending(tx))

        return transactions[:limit]

    def _parse_pending_transactions(self, txs: List[Dict]) -> List[PendingTransaction]:
        """Parse eth_pendingTransactions response."""
        return [self._tx_to_pending(tx) for tx in txs]

    def _tx_to_pending(self, tx: Dict) -> PendingTransaction:
        """Convert raw tx dict to PendingTransaction."""
        return PendingTransaction(
            hash=tx.get("hash", ""),
            from_address=tx.get("from", ""),
            to_address=tx.get("to"),
            value=int(tx.get("value", "0x0"), 16),
            gas=int(tx.get("gas", "0x0"), 16),
            gas_price=int(tx.get("gasPrice", "0x0"), 16),
            max_fee_per_gas=int(tx.get("maxFeePerGas", "0x0"), 16) if tx.get("maxFeePerGas") else None,
            max_priority_fee_per_gas=int(tx.get("maxPriorityFeePerGas", "0x0"), 16)
            if tx.get("maxPriorityFeePerGas")
            else None,
            nonce=int(tx.get("nonce", "0x0"), 16),
            input_data=tx.get("input", "0x"),
            block_number=int(tx.get("blockNumber", "0x0"), 16) if tx.get("blockNumber") else None,
        )

    def _get_mock_pending_transactions(self, limit: int) -> List[PendingTransaction]:
        """Generate mock pending transactions for demo."""
        import random

        mock_txs = []
        base_gas_price = 30 * 10**9  # 30 gwei

        # Common router addresses
        routers = [
            "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",  # Uniswap V2
            "0xE592427A0AEce92De3Edee1F18E0157C05861564",  # Uniswap V3
            "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F",  # SushiSwap
        ]

        # Sample swap input data prefix
        swap_input = "0x38ed1739"  # swapExactTokensForTokens

        for i in range(min(limit, 20)):
            gas_price = base_gas_price + random.randint(-5, 20) * 10**9
            mock_txs.append(
                PendingTransaction(
                    hash=f"0x{''.join(random.choices('0123456789abcdef', k=64))}",
                    from_address=f"0x{''.join(random.choices('0123456789abcdef', k=40))}",
                    to_address=random.choice(routers),
                    value=random.randint(0, 10) * 10**18,
                    gas=random.randint(100000, 500000),
                    gas_price=gas_price,
                    max_fee_per_gas=gas_price + 5 * 10**9,
                    max_priority_fee_per_gas=2 * 10**9,
                    nonce=random.randint(1, 1000),
                    input_data=swap_input + "0" * 128,
                    block_number=None,
                )
            )

        return mock_txs

    def get_gas_price(self) -> GasInfo:
        """Get current gas price information.

        Returns:
            GasInfo with current gas prices
        """
        try:
            # Get base fee from latest block
            block = self._rpc_call("eth_getBlockByNumber", ["latest", False])
            base_fee = int(block.get("baseFeePerGas", "0x0"), 16)

            # Get legacy gas price
            gas_price = int(self._rpc_call("eth_gasPrice"), 16)

            # Estimate priority fee
            priority_fee = max(gas_price - base_fee, 1 * 10**9)

            # Get pending tx count (optional - not all nodes support txpool_status)
            pending_count = 0
            try:
                txpool_status = self._rpc_call("txpool_status")
                pending_count = int(txpool_status.get("pending", "0x0"), 16)
            except Exception:
                # txpool_status not supported by this node - use 0 as fallback
                pass

            return GasInfo(
                base_fee=base_fee,
                priority_fee=priority_fee,
                gas_price=gas_price,
                pending_count=pending_count,
            )

        except Exception as e:
            if self.verbose:
                print(f"Error getting gas price: {e}")
            # Return reasonable defaults
            return GasInfo(
                base_fee=30 * 10**9,
                priority_fee=2 * 10**9,
                gas_price=32 * 10**9,
                pending_count=0,
            )

    def get_transaction(self, tx_hash: str) -> Optional[Dict]:
        """Get transaction by hash.

        Args:
            tx_hash: Transaction hash

        Returns:
            Transaction dict or None
        """
        try:
            return self._rpc_call("eth_getTransactionByHash", [tx_hash])
        except Exception:
            # Transaction not found or RPC error - return None
            return None

    def get_block_number(self) -> int:
        """Get current block number."""
        result = self._rpc_call("eth_blockNumber")
        return int(result, 16)


def main():
    """CLI entry point for testing."""
    client = RPCClient(verbose=True)

    print("=== Current Gas Prices ===")
    gas = client.get_gas_price()
    print(f"Base Fee: {gas.base_fee / 10**9:.2f} gwei")
    print(f"Priority Fee: {gas.priority_fee / 10**9:.2f} gwei")
    print(f"Gas Price: {gas.gas_price / 10**9:.2f} gwei")
    print(f"Pending Txs: {gas.pending_count}")

    print("\n=== Pending Transactions ===")
    pending = client.get_pending_transactions(limit=5)
    for tx in pending:
        print(f"  {tx.hash[:16]}... | {tx.gas_price / 10**9:.1f} gwei | {tx.gas} gas")


if __name__ == "__main__":
    main()
