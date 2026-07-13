#!/usr/bin/env python3
"""
Token Approval Scanner

Scan wallet for ERC20 token approvals.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 1.0.0
License: MIT
"""

import os
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict, Any, List, Optional

try:
    import requests
except ImportError:
    requests = None


# ERC20 Approval event topic
APPROVAL_TOPIC = "0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925"

# Unlimited approval threshold (2^256 - 1 or close to it)
UNLIMITED_THRESHOLD = 2**200

# Known risky spenders (placeholder - would be populated from security APIs)
KNOWN_RISKY_SPENDERS: Dict[str, str] = {
    # "0xaddress": "Known scam contract"
}

# Chain configurations
CHAIN_CONFIGS = {
    "ethereum": {
        "chain_id": 1,
        "rpc_url": "https://eth.llamarpc.com",
        "explorer_api": "https://api.etherscan.io/api",
        "explorer_url": "https://etherscan.io",
    },
    "bsc": {
        "chain_id": 56,
        "rpc_url": "https://bsc-dataseed1.binance.org",
        "explorer_api": "https://api.bscscan.com/api",
        "explorer_url": "https://bscscan.com",
    },
    "polygon": {
        "chain_id": 137,
        "rpc_url": "https://polygon-rpc.com",
        "explorer_api": "https://api.polygonscan.com/api",
        "explorer_url": "https://polygonscan.com",
    },
    "arbitrum": {
        "chain_id": 42161,
        "rpc_url": "https://arb1.arbitrum.io/rpc",
        "explorer_api": "https://api.arbiscan.io/api",
        "explorer_url": "https://arbiscan.io",
    },
    "optimism": {
        "chain_id": 10,
        "rpc_url": "https://mainnet.optimism.io",
        "explorer_api": "https://api-optimistic.etherscan.io/api",
        "explorer_url": "https://optimistic.etherscan.io",
    },
    "base": {
        "chain_id": 8453,
        "rpc_url": "https://mainnet.base.org",
        "explorer_api": "https://api.basescan.org/api",
        "explorer_url": "https://basescan.org",
    },
}


@dataclass
class TokenApproval:
    """Token approval data."""

    token_address: str
    token_symbol: str
    token_name: str
    spender: str
    spender_name: Optional[str]
    allowance: Decimal
    allowance_raw: int
    is_unlimited: bool
    approval_tx: str
    approval_block: int
    is_risky: bool = False
    risk_reason: Optional[str] = None


@dataclass
class ApprovalSummary:
    """Summary of all approvals."""

    total_approvals: int
    unlimited_approvals: int
    risky_approvals: int
    unique_spenders: int
    unique_tokens: int
    approvals: List[TokenApproval] = field(default_factory=list)


class ApprovalScanner:
    """Scan wallet for token approvals."""

    def __init__(
        self, chain: str = "ethereum", rpc_url: str = None, explorer_api_key: str = None, verbose: bool = False
    ):
        """Initialize approval scanner.

        Args:
            chain: Chain to scan
            rpc_url: Custom RPC URL
            explorer_api_key: Block explorer API key
            verbose: Enable verbose output
        """
        if not requests:
            raise ImportError("requests library required: pip install requests")

        self.chain = chain.lower()
        if self.chain not in CHAIN_CONFIGS:
            raise ValueError(f"Unsupported chain: {chain}")

        self.config = CHAIN_CONFIGS[self.chain]
        self.rpc_url = rpc_url or os.environ.get(f"{chain.upper()}_RPC_URL", self.config["rpc_url"])
        self.explorer_api_key = explorer_api_key or os.environ.get("ETHERSCAN_API_KEY", "")
        self.verbose = verbose
        self._token_cache: Dict[str, Dict] = {}

    def _rpc_call(self, method: str, params: List = None) -> Any:
        """Make JSON-RPC call."""
        response = requests.post(
            self.rpc_url,
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

    def _call_contract(self, address: str, data: str) -> Optional[str]:
        """Make eth_call to contract."""
        try:
            result = self._rpc_call("eth_call", [{"to": address, "data": data}, "latest"])
            return result if result and result != "0x" else None
        except (requests.RequestException, KeyError, ValueError):
            # Contract call failed - contract may not be ERC20 or is inaccessible
            return None

    def _get_token_info(self, address: str) -> Dict[str, Any]:
        """Get token name and symbol."""
        if address in self._token_cache:
            return self._token_cache[address]

        # name()
        name_result = self._call_contract(address, "0x06fdde03")
        # symbol()
        symbol_result = self._call_contract(address, "0x95d89b41")
        # decimals()
        decimals_result = self._call_contract(address, "0x313ce567")

        info = {
            "name": self._decode_string(name_result) if name_result else "Unknown",
            "symbol": self._decode_string(symbol_result) if symbol_result else "???",
            "decimals": int(decimals_result, 16) if decimals_result else 18,
        }

        self._token_cache[address] = info
        return info

    def _decode_string(self, data: str) -> str:
        """Decode ABI-encoded string."""
        if not data or data == "0x":
            return ""

        try:
            data = data[2:]

            if len(data) <= 64:
                return bytes.fromhex(data).decode("utf-8", errors="ignore").strip("\x00")

            if len(data) >= 128:
                length = int(data[64:128], 16)
                string_data = data[128 : 128 + length * 2]
                return bytes.fromhex(string_data).decode("utf-8", errors="ignore")

            return bytes.fromhex(data).decode("utf-8", errors="ignore").strip("\x00")

        except Exception:
            return "Unknown"

    def _get_spender_name(self, address: str) -> Optional[str]:
        """Get spender contract name if verified."""
        if not self.explorer_api_key:
            return None

        try:
            response = requests.get(
                self.config["explorer_api"],
                params={
                    "module": "contract",
                    "action": "getsourcecode",
                    "address": address,
                    "apikey": self.explorer_api_key,
                },
                timeout=10,
            )
            data = response.json()

            if data.get("status") == "1" and data.get("result"):
                name = data["result"][0].get("ContractName", "")
                if name:
                    return name

        except Exception:
            pass

        return None

    def get_all_approvals(self, address: str, from_block: int = 0) -> ApprovalSummary:
        """Get all token approvals for an address.

        Args:
            address: Wallet address to scan
            from_block: Starting block (0 = genesis)

        Returns:
            ApprovalSummary with all approvals
        """
        address = address.lower()

        # Get all Approval events where owner is this address
        # Topic 1 = owner (padded address)
        owner_topic = "0x" + address[2:].zfill(64)

        if self.verbose:
            print(f"Scanning approvals for {address[:20]}...")

        try:
            logs = self._rpc_call(
                "eth_getLogs",
                [
                    {
                        "fromBlock": hex(from_block) if from_block else "0x0",
                        "toBlock": "latest",
                        "topics": [APPROVAL_TOPIC, owner_topic],
                    }
                ],
            )
        except Exception as e:
            if self.verbose:
                print(f"Error fetching logs: {e}")
            logs = []

        approvals: Dict[str, TokenApproval] = {}
        spenders = set()
        tokens = set()

        for log in logs or []:
            try:
                token_address = log["address"].lower()
                topics = log.get("topics", [])
                data = log.get("data", "0x")

                if len(topics) < 3:
                    continue

                spender = "0x" + topics[2][-40:]
                allowance_raw = int(data, 16) if data != "0x" else 0

                # Get token info
                token_info = self._get_token_info(token_address)

                # Check if unlimited
                is_unlimited = allowance_raw >= UNLIMITED_THRESHOLD

                # Calculate human-readable allowance
                decimals = token_info["decimals"]
                allowance = Decimal(allowance_raw) / Decimal(10**decimals)

                # Check if risky
                is_risky = False
                risk_reason = None

                if spender.lower() in KNOWN_RISKY_SPENDERS:
                    is_risky = True
                    risk_reason = KNOWN_RISKY_SPENDERS[spender.lower()]

                # Get spender name
                spender_name = self._get_spender_name(spender)

                # Create approval record (latest overwrites previous)
                key = f"{token_address}:{spender}"
                approvals[key] = TokenApproval(
                    token_address=token_address,
                    token_symbol=token_info["symbol"],
                    token_name=token_info["name"],
                    spender=spender,
                    spender_name=spender_name,
                    allowance=allowance,
                    allowance_raw=allowance_raw,
                    is_unlimited=is_unlimited,
                    approval_tx=log.get("transactionHash", ""),
                    approval_block=int(log.get("blockNumber", "0x0"), 16),
                    is_risky=is_risky,
                    risk_reason=risk_reason,
                )

                spenders.add(spender)
                tokens.add(token_address)

            except Exception as e:
                if self.verbose:
                    print(f"Error parsing log: {e}")

        # Filter out zero allowances (revoked)
        active_approvals = [a for a in approvals.values() if a.allowance_raw > 0]

        return ApprovalSummary(
            total_approvals=len(active_approvals),
            unlimited_approvals=sum(1 for a in active_approvals if a.is_unlimited),
            risky_approvals=sum(1 for a in active_approvals if a.is_risky),
            unique_spenders=len(spenders),
            unique_tokens=len(tokens),
            approvals=sorted(active_approvals, key=lambda x: x.allowance_raw, reverse=True),
        )

    def get_unlimited_approvals(self, address: str) -> List[TokenApproval]:
        """Get only unlimited approvals.

        Args:
            address: Wallet address

        Returns:
            List of unlimited approvals
        """
        summary = self.get_all_approvals(address)
        return [a for a in summary.approvals if a.is_unlimited]

    def get_risky_approvals(self, address: str) -> List[TokenApproval]:
        """Get only risky approvals.

        Args:
            address: Wallet address

        Returns:
            List of risky approvals
        """
        summary = self.get_all_approvals(address)
        return [a for a in summary.approvals if a.is_risky]


def main():
    """CLI entry point for testing."""
    scanner = ApprovalScanner(chain="ethereum", verbose=True)

    # Test with a sample address (vitalik.eth)
    test_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"

    print("=== Approval Scanner Test ===")
    print(f"Scanning: {test_address[:20]}...")

    summary = scanner.get_all_approvals(test_address)

    print("\nResults:")
    print(f"  Total approvals: {summary.total_approvals}")
    print(f"  Unlimited: {summary.unlimited_approvals}")
    print(f"  Risky: {summary.risky_approvals}")
    print(f"  Unique spenders: {summary.unique_spenders}")
    print(f"  Unique tokens: {summary.unique_tokens}")

    if summary.approvals:
        print("\nTop Approvals:")
        for approval in summary.approvals[:5]:
            unlimited_str = " [UNLIMITED]" if approval.is_unlimited else ""
            risky_str = " [RISKY]" if approval.is_risky else ""
            print(f"  {approval.token_symbol}: {approval.spender[:20]}...{unlimited_str}{risky_str}")


if __name__ == "__main__":
    main()
