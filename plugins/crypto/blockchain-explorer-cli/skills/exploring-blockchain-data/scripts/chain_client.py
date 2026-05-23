#!/usr/bin/env python3
"""
Multi-Chain Client

Unified interface for querying multiple EVM chains.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 1.0.0
License: MIT
"""

import os
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

try:
    import requests
except ImportError:
    requests = None


@dataclass
class ChainConfig:
    """Configuration for a blockchain network."""

    name: str
    chain_id: int
    rpc_url: str
    explorer_api: str
    explorer_url: str
    native_symbol: str
    api_key_env: str


# Supported chains configuration
CHAINS: Dict[str, ChainConfig] = {
    "ethereum": ChainConfig(
        name="Ethereum",
        chain_id=1,
        rpc_url="https://eth.llamarpc.com",
        explorer_api="https://api.etherscan.io/api",
        explorer_url="https://etherscan.io",
        native_symbol="ETH",
        api_key_env="ETHERSCAN_API_KEY",
    ),
    "polygon": ChainConfig(
        name="Polygon",
        chain_id=137,
        rpc_url="https://polygon.llamarpc.com",
        explorer_api="https://api.polygonscan.com/api",
        explorer_url="https://polygonscan.com",
        native_symbol="MATIC",
        api_key_env="POLYGONSCAN_API_KEY",
    ),
    "bsc": ChainConfig(
        name="BNB Smart Chain",
        chain_id=56,
        rpc_url="https://bsc.llamarpc.com",
        explorer_api="https://api.bscscan.com/api",
        explorer_url="https://bscscan.com",
        native_symbol="BNB",
        api_key_env="BSCSCAN_API_KEY",
    ),
    "arbitrum": ChainConfig(
        name="Arbitrum One",
        chain_id=42161,
        rpc_url="https://arb1.arbitrum.io/rpc",
        explorer_api="https://api.arbiscan.io/api",
        explorer_url="https://arbiscan.io",
        native_symbol="ETH",
        api_key_env="ARBISCAN_API_KEY",
    ),
    "optimism": ChainConfig(
        name="Optimism",
        chain_id=10,
        rpc_url="https://mainnet.optimism.io",
        explorer_api="https://api-optimistic.etherscan.io/api",
        explorer_url="https://optimistic.etherscan.io",
        native_symbol="ETH",
        api_key_env="OPTIMISM_API_KEY",
    ),
    "base": ChainConfig(
        name="Base",
        chain_id=8453,
        rpc_url="https://mainnet.base.org",
        explorer_api="https://api.basescan.org/api",
        explorer_url="https://basescan.org",
        native_symbol="ETH",
        api_key_env="BASESCAN_API_KEY",
    ),
    "avalanche": ChainConfig(
        name="Avalanche C-Chain",
        chain_id=43114,
        rpc_url="https://api.avax.network/ext/bc/C/rpc",
        explorer_api="https://api.snowtrace.io/api",
        explorer_url="https://snowtrace.io",
        native_symbol="AVAX",
        api_key_env="SNOWTRACE_API_KEY",
    ),
}


class ChainClient:
    """Multi-chain blockchain client."""

    def __init__(self, chain: str = "ethereum", verbose: bool = False):
        """Initialize chain client.

        Args:
            chain: Chain name (ethereum, polygon, bsc, etc.)
            verbose: Enable verbose output
        """
        if chain not in CHAINS:
            raise ValueError(f"Unsupported chain: {chain}. Supported: {list(CHAINS.keys())}")

        self.chain = chain
        self.config = CHAINS[chain]
        self.verbose = verbose
        self.api_key = os.environ.get(self.config.api_key_env, "")
        self._last_request = 0
        self._rate_limit = 0.2  # 5 requests per second

    def _rate_limit_wait(self) -> None:
        """Enforce rate limiting."""
        elapsed = time.time() - self._last_request
        if elapsed < self._rate_limit:
            time.sleep(self._rate_limit - elapsed)
        self._last_request = time.time()

    def _rpc_call(self, method: str, params: List[Any]) -> Any:
        """Make JSON-RPC call.

        Args:
            method: RPC method name
            params: Method parameters

        Returns:
            RPC result
        """
        if not requests:
            raise ImportError("requests library required")

        self._rate_limit_wait()

        payload = {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}

        if self.verbose:
            print(f"RPC: {method} -> {self.config.rpc_url}")

        response = requests.post(self.config.rpc_url, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()

        if "error" in data:
            raise Exception(f"RPC error: {data['error']}")

        return data.get("result")

    def _explorer_call(self, params: Dict[str, str]) -> Any:
        """Make Explorer API call.

        Args:
            params: API parameters

        Returns:
            API result
        """
        if not requests:
            raise ImportError("requests library required")

        self._rate_limit_wait()

        if self.api_key:
            params["apikey"] = self.api_key

        if self.verbose:
            print(f"Explorer API: {params.get('action')} -> {self.config.explorer_api}")

        response = requests.get(self.config.explorer_api, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "0" and data.get("message") != "No transactions found":
            raise Exception(f"Explorer API error: {data.get('result', data.get('message'))}")

        return data.get("result")

    def get_transaction(self, tx_hash: str) -> Dict[str, Any]:
        """Get transaction details.

        Args:
            tx_hash: Transaction hash

        Returns:
            Transaction data with receipt
        """
        # Get transaction
        tx = self._rpc_call("eth_getTransactionByHash", [tx_hash])
        if not tx:
            return {"error": "Transaction not found", "hash": tx_hash}

        # Get receipt
        receipt = self._rpc_call("eth_getTransactionReceipt", [tx_hash])

        # Parse values
        result = {
            "hash": tx_hash,
            "chain": self.config.name,
            "status": "success" if receipt and receipt.get("status") == "0x1" else "failed",
            "block_number": int(tx.get("blockNumber", "0x0"), 16),
            "from": tx.get("from"),
            "to": tx.get("to"),
            "value_wei": int(tx.get("value", "0x0"), 16),
            "value": int(tx.get("value", "0x0"), 16) / 1e18,
            "gas_price_gwei": int(tx.get("gasPrice", "0x0"), 16) / 1e9,
            "gas_limit": int(tx.get("gas", "0x0"), 16),
            "gas_used": int(receipt.get("gasUsed", "0x0"), 16) if receipt else 0,
            "input": tx.get("input", "0x"),
            "nonce": int(tx.get("nonce", "0x0"), 16),
            "explorer_url": f"{self.config.explorer_url}/tx/{tx_hash}",
        }

        # Calculate gas cost
        if receipt:
            result["gas_cost"] = result["gas_price_gwei"] * result["gas_used"] / 1e9
            result["logs_count"] = len(receipt.get("logs", []))

        return result

    def get_balance(self, address: str) -> Dict[str, Any]:
        """Get address balance.

        Args:
            address: Wallet address

        Returns:
            Balance data
        """
        balance_hex = self._rpc_call("eth_getBalance", [address, "latest"])
        balance_wei = int(balance_hex, 16)

        # Get transaction count
        tx_count_hex = self._rpc_call("eth_getTransactionCount", [address, "latest"])
        tx_count = int(tx_count_hex, 16)

        return {
            "address": address,
            "chain": self.config.name,
            "balance_wei": balance_wei,
            "balance": balance_wei / 1e18,
            "symbol": self.config.native_symbol,
            "transaction_count": tx_count,
            "explorer_url": f"{self.config.explorer_url}/address/{address}",
        }

    def get_block(self, block_number: Optional[int] = None) -> Dict[str, Any]:
        """Get block information.

        Args:
            block_number: Block number (None for latest)

        Returns:
            Block data
        """
        block_param = hex(block_number) if block_number else "latest"
        block = self._rpc_call("eth_getBlockByNumber", [block_param, False])

        if not block:
            return {"error": "Block not found"}

        return {
            "number": int(block.get("number", "0x0"), 16),
            "chain": self.config.name,
            "timestamp": int(block.get("timestamp", "0x0"), 16),
            "hash": block.get("hash"),
            "parent_hash": block.get("parentHash"),
            "miner": block.get("miner"),
            "gas_limit": int(block.get("gasLimit", "0x0"), 16),
            "gas_used": int(block.get("gasUsed", "0x0"), 16),
            "base_fee_gwei": int(block.get("baseFeePerGas", "0x0"), 16) / 1e9 if block.get("baseFeePerGas") else None,
            "transaction_count": len(block.get("transactions", [])),
            "explorer_url": f"{self.config.explorer_url}/block/{int(block.get('number', '0x0'), 16)}",
        }

    def get_token_balance(self, address: str, token_contract: str) -> Dict[str, Any]:
        """Get ERC20 token balance.

        Args:
            address: Wallet address
            token_contract: Token contract address

        Returns:
            Token balance data
        """
        # balanceOf(address) function signature
        data = f"0x70a08231000000000000000000000000{address[2:].lower()}"

        result = self._rpc_call("eth_call", [{"to": token_contract, "data": data}, "latest"])

        balance_wei = int(result, 16) if result else 0

        # Get token decimals
        decimals_data = "0x313ce567"  # decimals()
        decimals_result = self._rpc_call("eth_call", [{"to": token_contract, "data": decimals_data}, "latest"])
        decimals = int(decimals_result, 16) if decimals_result else 18

        return {
            "address": address,
            "token_contract": token_contract,
            "chain": self.config.name,
            "balance_raw": balance_wei,
            "balance": balance_wei / (10**decimals),
            "decimals": decimals,
        }

    def get_transaction_list(
        self, address: str, start_block: int = 0, end_block: int = 99999999, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get transaction history for address.

        Args:
            address: Wallet address
            start_block: Starting block
            end_block: Ending block
            limit: Maximum transactions

        Returns:
            List of transactions
        """
        result = self._explorer_call(
            {
                "module": "account",
                "action": "txlist",
                "address": address,
                "startblock": str(start_block),
                "endblock": str(end_block),
                "page": "1",
                "offset": str(limit),
                "sort": "desc",
            }
        )

        if not result or isinstance(result, str):
            return []

        transactions = []
        for tx in result[:limit]:
            transactions.append(
                {
                    "hash": tx.get("hash"),
                    "block_number": int(tx.get("blockNumber", 0)),
                    "timestamp": int(tx.get("timeStamp", 0)),
                    "from": tx.get("from"),
                    "to": tx.get("to"),
                    "value": int(tx.get("value", 0)) / 1e18,
                    "gas_used": int(tx.get("gasUsed", 0)),
                    "gas_price_gwei": int(tx.get("gasPrice", 0)) / 1e9,
                    "status": "success" if tx.get("isError") == "0" else "failed",
                    "method": tx.get("functionName", "").split("(")[0] if tx.get("functionName") else "transfer",
                }
            )

        return transactions

    def get_token_transfers(
        self, address: str, contract: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get ERC20 token transfers for address.

        Args:
            address: Wallet address
            contract: Optional specific token contract
            limit: Maximum transfers

        Returns:
            List of token transfers
        """
        params = {
            "module": "account",
            "action": "tokentx",
            "address": address,
            "page": "1",
            "offset": str(limit),
            "sort": "desc",
        }

        if contract:
            params["contractaddress"] = contract

        result = self._explorer_call(params)

        if not result or isinstance(result, str):
            return []

        transfers = []
        for tx in result[:limit]:
            decimals = int(tx.get("tokenDecimal", 18))
            value = int(tx.get("value", 0)) / (10**decimals)

            transfers.append(
                {
                    "hash": tx.get("hash"),
                    "block_number": int(tx.get("blockNumber", 0)),
                    "timestamp": int(tx.get("timeStamp", 0)),
                    "from": tx.get("from"),
                    "to": tx.get("to"),
                    "value": value,
                    "token_symbol": tx.get("tokenSymbol"),
                    "token_name": tx.get("tokenName"),
                    "token_contract": tx.get("contractAddress"),
                }
            )

        return transfers

    def get_contract_abi(self, contract: str) -> Optional[str]:
        """Get contract ABI from explorer.

        Args:
            contract: Contract address

        Returns:
            ABI JSON string or None
        """
        try:
            result = self._explorer_call({"module": "contract", "action": "getabi", "address": contract})
            return result if result and result != "Contract source code not verified" else None
        except Exception:
            return None


def detect_chain(identifier: str) -> str:
    """Detect chain from transaction hash or address.

    This is a heuristic - in practice, you'd query multiple chains.

    Args:
        identifier: Transaction hash or address

    Returns:
        Best guess chain name (defaults to ethereum)
    """
    # All EVM chains use the same address/hash format
    # In production, you'd query multiple chains
    return "ethereum"


def main():
    """CLI entry point for testing."""
    import sys

    if len(sys.argv) < 3:
        print("Usage: chain_client.py <chain> <tx_hash|address>")
        print("Chains:", list(CHAINS.keys()))
        sys.exit(1)

    chain = sys.argv[1]
    identifier = sys.argv[2]

    client = ChainClient(chain=chain, verbose=True)

    if identifier.startswith("0x") and len(identifier) == 66:
        # Transaction hash
        result = client.get_transaction(identifier)
    else:
        # Address
        result = client.get_balance(identifier)

    import json

    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
