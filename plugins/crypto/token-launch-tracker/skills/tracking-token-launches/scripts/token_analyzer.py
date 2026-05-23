#!/usr/bin/env python3
"""
Token Contract Analyzer

Analyze token contracts for risk indicators.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 1.0.0
License: MIT
"""

import os
from dataclasses import dataclass, field
from typing import Any, List, Optional

try:
    import requests
except ImportError:
    requests = None

from dex_sources import get_chain_config


@dataclass
class TokenInfo:
    """Complete token information."""

    address: str
    name: str
    symbol: str
    decimals: int
    total_supply: int
    owner: Optional[str] = None
    is_verified: bool = False
    creation_block: Optional[int] = None


@dataclass
class RiskIndicator:
    """Single risk indicator."""

    name: str
    detected: bool
    severity: str  # high, medium, low, info
    description: str


@dataclass
class ContractAnalysis:
    """Complete contract risk analysis."""

    address: str
    risk_score: int  # 0-100 (higher = riskier)
    indicators: List[RiskIndicator] = field(default_factory=list)
    bytecode_size: int = 0
    is_proxy: bool = False
    ownership_renounced: bool = False


# Known risky function signatures
# Note: 0xa9059cbb is the standard ERC20 transfer function, not blacklist
RISKY_FUNCTIONS = {
    "0x40c10f19": ("mint", "high", "Contract has mint function"),
    "0x44337ea1": ("blacklist", "medium", "Contract has blacklist functionality"),  # addToBlacklist(address)
    "0x42966c68": ("burn", "info", "Contract has burn function"),
    "0x23b872dd": ("transferFrom", "info", "Standard ERC20 transferFrom"),
    "0x8da5cb5b": ("owner", "info", "Contract has owner"),
    "0x715018a6": ("renounceOwnership", "info", "Can renounce ownership"),
    "0xf2fde38b": ("transferOwnership", "low", "Can transfer ownership"),
}

# Bytecode patterns for suspicious contracts
SUSPICIOUS_PATTERNS = [
    ("73757370656e64", "medium", "Contains 'suspend' string"),
    ("626c61636b6c697374", "medium", "Contains 'blacklist' string"),
    ("77686974656c697374", "low", "Contains 'whitelist' string"),
    ("6f6e6c794f776e6572", "info", "Contains 'onlyOwner' modifier"),
]


class TokenAnalyzer:
    """Analyze token contracts for risks."""

    def __init__(
        self, chain: str = "ethereum", rpc_url: str = None, etherscan_api_key: str = None, verbose: bool = False
    ):
        """Initialize token analyzer.

        Args:
            chain: Chain to analyze on
            rpc_url: Custom RPC URL
            etherscan_api_key: Etherscan API key for verification check
            verbose: Enable verbose output
        """
        self.chain = chain.lower()
        self.config = get_chain_config(chain)
        self.rpc_url = rpc_url or os.environ.get(f"{chain.upper()}_RPC_URL", self.config.rpc_url)
        self.etherscan_key = etherscan_api_key or os.environ.get("ETHERSCAN_API_KEY", "")
        self.verbose = verbose

    def _rpc_call(self, method: str, params: List = None) -> Any:
        """Make JSON-RPC call."""
        if not requests:
            raise ImportError("requests library required")

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

    def _call_contract(self, address: str, data: str) -> Optional[str]:
        """Make eth_call."""
        try:
            result = self._rpc_call("eth_call", [{"to": address, "data": data}, "latest"])
            return result if result and result != "0x" else None
        except Exception:
            return None

    def get_token_info(self, address: str) -> TokenInfo:
        """Get complete token information.

        Args:
            address: Token contract address

        Returns:
            TokenInfo object
        """
        # ERC20 function signatures
        name_result = self._call_contract(address, "0x06fdde03")
        symbol_result = self._call_contract(address, "0x95d89b41")
        decimals_result = self._call_contract(address, "0x313ce567")
        supply_result = self._call_contract(address, "0x18160ddd")
        owner_result = self._call_contract(address, "0x8da5cb5b")

        return TokenInfo(
            address=address,
            name=self._decode_string(name_result) if name_result else "Unknown",
            symbol=self._decode_string(symbol_result) if symbol_result else "???",
            decimals=int(decimals_result, 16) if decimals_result else 18,
            total_supply=int(supply_result, 16) if supply_result else 0,
            owner="0x" + owner_result[-40:] if owner_result and len(owner_result) >= 42 else None,
            is_verified=self._check_verified(address),
        )

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

    def _check_verified(self, address: str) -> bool:
        """Check if contract is verified on block explorer."""
        if not requests or not self.etherscan_key:
            return False

        try:
            # Map chain to explorer API
            explorer_apis = {
                "ethereum": "https://api.etherscan.io/api",
                "bsc": "https://api.bscscan.com/api",
                "arbitrum": "https://api.arbiscan.io/api",
                "base": "https://api.basescan.org/api",
                "polygon": "https://api.polygonscan.com/api",
            }

            api_url = explorer_apis.get(self.chain)
            if not api_url:
                return False

            response = requests.get(
                api_url,
                params={
                    "module": "contract",
                    "action": "getsourcecode",
                    "address": address,
                    "apikey": self.etherscan_key,
                },
                timeout=10,
            )

            data = response.json()
            if data.get("status") == "1" and data.get("result"):
                source = data["result"][0].get("SourceCode", "")
                return bool(source and source != "")

        except Exception as e:
            if self.verbose:
                print(f"Verification check error: {e}")

        return False

    def analyze_contract(self, address: str) -> ContractAnalysis:
        """Analyze contract for risk indicators.

        Args:
            address: Contract address

        Returns:
            ContractAnalysis with risk score and indicators
        """
        indicators = []
        risk_score = 0

        # Get bytecode
        bytecode = self._rpc_call("eth_getCode", [address, "latest"])
        bytecode_size = (len(bytecode) - 2) // 2 if bytecode else 0

        # Check if proxy
        is_proxy = self._detect_proxy(address, bytecode)
        if is_proxy:
            indicators.append(
                RiskIndicator(
                    name="Proxy Contract",
                    detected=True,
                    severity="medium",
                    description="Contract is a proxy - implementation can be changed",
                )
            )
            risk_score += 20

        # Check ownership
        owner_result = self._call_contract(address, "0x8da5cb5b")
        owner = "0x" + owner_result[-40:] if owner_result and len(owner_result) >= 42 else None
        ownership_renounced = owner and owner.lower() == "0x0000000000000000000000000000000000000000"

        if owner:
            if ownership_renounced:
                indicators.append(
                    RiskIndicator(
                        name="Ownership Renounced",
                        detected=True,
                        severity="info",
                        description="Ownership has been renounced",
                    )
                )
            else:
                indicators.append(
                    RiskIndicator(
                        name="Has Owner",
                        detected=True,
                        severity="low",
                        description=f"Contract has active owner: {owner[:20]}...",
                    )
                )
                risk_score += 10

        # Check for risky function signatures in bytecode
        for sig, (name, severity, desc) in RISKY_FUNCTIONS.items():
            if sig[2:] in bytecode.lower():
                indicators.append(RiskIndicator(name=f"Has {name}", detected=True, severity=severity, description=desc))
                if severity == "high":
                    risk_score += 30
                elif severity == "medium":
                    risk_score += 15
                elif severity == "low":
                    risk_score += 5

        # Check for suspicious patterns
        for pattern, severity, desc in SUSPICIOUS_PATTERNS:
            if pattern in bytecode.lower():
                indicators.append(
                    RiskIndicator(name="Suspicious Pattern", detected=True, severity=severity, description=desc)
                )
                if severity == "high":
                    risk_score += 25
                elif severity == "medium":
                    risk_score += 10

        # Check verification
        is_verified = self._check_verified(address)
        if not is_verified:
            indicators.append(
                RiskIndicator(
                    name="Not Verified",
                    detected=True,
                    severity="medium",
                    description="Contract source code not verified",
                )
            )
            risk_score += 15

        # Very small bytecode might be suspicious
        if bytecode_size < 500:
            indicators.append(
                RiskIndicator(
                    name="Small Contract",
                    detected=True,
                    severity="info",
                    description=f"Bytecode is only {bytecode_size} bytes",
                )
            )

        # Cap at 100
        risk_score = min(risk_score, 100)

        return ContractAnalysis(
            address=address,
            risk_score=risk_score,
            indicators=indicators,
            bytecode_size=bytecode_size,
            is_proxy=is_proxy,
            ownership_renounced=ownership_renounced,
        )

    def _detect_proxy(self, address: str, bytecode: str) -> bool:
        """Detect if contract is a proxy.

        Args:
            address: Contract address
            bytecode: Contract bytecode

        Returns:
            True if proxy detected
        """
        # Common proxy patterns
        proxy_patterns = [
            "363d3d373d3d3d363d73",  # Minimal proxy
            "5155f3",  # DELEGATECALL
            "363d3d373d3d3d363d",  # EIP-1167
        ]

        bytecode_lower = bytecode.lower()
        for pattern in proxy_patterns:
            if pattern in bytecode_lower:
                return True

        # Check EIP-1967 implementation slot
        impl_slot = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
        try:
            storage = self._rpc_call("eth_getStorageAt", [address, impl_slot, "latest"])
            if storage and storage != "0x" + "0" * 64:
                return True
        except Exception:
            pass  # Storage read failed - likely not a proxy or access issue

        return False

    def get_risk_summary(self, analysis: ContractAnalysis) -> str:
        """Get human-readable risk summary.

        Args:
            analysis: ContractAnalysis object

        Returns:
            Risk level string
        """
        if analysis.risk_score >= 70:
            return "HIGH RISK"
        elif analysis.risk_score >= 40:
            return "MEDIUM RISK"
        elif analysis.risk_score >= 20:
            return "LOW RISK"
        else:
            return "MINIMAL RISK"


def main():
    """CLI entry point for testing."""
    analyzer = TokenAnalyzer(chain="ethereum", verbose=True)

    # Test with a known token (USDC)
    test_address = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"

    print("=== Token Info ===")
    info = analyzer.get_token_info(test_address)
    print(f"Name: {info.name}")
    print(f"Symbol: {info.symbol}")
    print(f"Decimals: {info.decimals}")
    print(f"Supply: {info.total_supply / 10**info.decimals:,.0f}")
    print(f"Owner: {info.owner}")
    print(f"Verified: {info.is_verified}")

    print("\n=== Contract Analysis ===")
    analysis = analyzer.analyze_contract(test_address)
    print(f"Risk Score: {analysis.risk_score}/100")
    print(f"Summary: {analyzer.get_risk_summary(analysis)}")
    print(f"Bytecode Size: {analysis.bytecode_size} bytes")
    print(f"Is Proxy: {analysis.is_proxy}")
    print(f"Ownership Renounced: {analysis.ownership_renounced}")

    print("\nIndicators:")
    for ind in analysis.indicators:
        print(f"  [{ind.severity.upper()}] {ind.name}: {ind.description}")


if __name__ == "__main__":
    main()
