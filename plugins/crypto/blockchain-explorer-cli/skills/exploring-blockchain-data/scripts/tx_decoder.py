#!/usr/bin/env python3
"""
Transaction Decoder

Decode transaction input data using ABIs and known signatures.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 1.0.0
License: MIT
"""

import json
from typing import Dict, Any, List, Optional


# Common function signatures (4-byte selectors)
KNOWN_SIGNATURES: Dict[str, Dict[str, Any]] = {
    # ERC20
    "0xa9059cbb": {"name": "transfer", "params": ["address to", "uint256 amount"]},
    "0x23b872dd": {"name": "transferFrom", "params": ["address from", "address to", "uint256 amount"]},
    "0x095ea7b3": {"name": "approve", "params": ["address spender", "uint256 amount"]},
    # ERC721
    "0x42842e0e": {"name": "safeTransferFrom", "params": ["address from", "address to", "uint256 tokenId"]},
    "0xb88d4fde": {
        "name": "safeTransferFrom",
        "params": ["address from", "address to", "uint256 tokenId", "bytes data"],
    },
    # Uniswap V2 Router
    "0x38ed1739": {
        "name": "swapExactTokensForTokens",
        "params": ["uint256 amountIn", "uint256 amountOutMin", "address[] path", "address to", "uint256 deadline"],
    },
    "0x8803dbee": {
        "name": "swapTokensForExactTokens",
        "params": ["uint256 amountOut", "uint256 amountInMax", "address[] path", "address to", "uint256 deadline"],
    },
    "0x7ff36ab5": {
        "name": "swapExactETHForTokens",
        "params": ["uint256 amountOutMin", "address[] path", "address to", "uint256 deadline"],
    },
    "0x18cbafe5": {
        "name": "swapExactTokensForETH",
        "params": ["uint256 amountIn", "uint256 amountOutMin", "address[] path", "address to", "uint256 deadline"],
    },
    # Uniswap V3 Router
    "0x414bf389": {"name": "exactInputSingle", "params": ["tuple params"]},
    "0xc04b8d59": {"name": "exactInput", "params": ["tuple params"]},
    "0xdb3e2198": {"name": "exactOutputSingle", "params": ["tuple params"]},
    "0xf28c0498": {"name": "exactOutput", "params": ["tuple params"]},
    "0x5ae401dc": {"name": "multicall", "params": ["uint256 deadline", "bytes[] data"]},
    # WETH
    "0xd0e30db0": {"name": "deposit", "params": []},
    "0x2e1a7d4d": {"name": "withdraw", "params": ["uint256 amount"]},
    # Aave
    "0xe8eda9df": {
        "name": "deposit",
        "params": ["address asset", "uint256 amount", "address onBehalfOf", "uint16 referralCode"],
    },
    "0x69328dec": {"name": "withdraw", "params": ["address asset", "uint256 amount", "address to"]},
    "0xa415bcad": {
        "name": "borrow",
        "params": [
            "address asset",
            "uint256 amount",
            "uint256 interestRateMode",
            "uint16 referralCode",
            "address onBehalfOf",
        ],
    },
    "0x573ade81": {
        "name": "repay",
        "params": ["address asset", "uint256 amount", "uint256 rateMode", "address onBehalfOf"],
    },
    # Common
    "0x": {"name": "transfer (native)", "params": []},
    "0x3593564c": {
        "name": "execute (Uniswap Universal Router)",
        "params": ["bytes commands", "bytes[] inputs", "uint256 deadline"],
    },
}


# Common event signatures
KNOWN_EVENTS: Dict[str, str] = {
    "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef": "Transfer(address,address,uint256)",
    "0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925": "Approval(address,address,uint256)",
    "0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822": "Swap(address,uint256,uint256,uint256,uint256,address)",
    "0x1c411e9a96e071241c2f21f7726b17ae89e3cab4c78be50e062b03a9fffbbad1": "Sync(uint112,uint112)",
    "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67": "Swap(address,address,int256,int256,uint160,uint128,int24)",
}


class TransactionDecoder:
    """Decode transaction input data."""

    def __init__(self, verbose: bool = False):
        """Initialize decoder.

        Args:
            verbose: Enable verbose output
        """
        self.verbose = verbose
        self.custom_abis: Dict[str, List[Dict]] = {}

    def add_abi(self, contract: str, abi: str) -> None:
        """Add custom ABI for contract.

        Args:
            contract: Contract address
            abi: ABI JSON string
        """
        try:
            self.custom_abis[contract.lower()] = json.loads(abi)
        except json.JSONDecodeError:
            if self.verbose:
                print(f"Warning: Invalid ABI for {contract}")

    def decode_input(self, input_data: str, contract: Optional[str] = None) -> Dict[str, Any]:
        """Decode transaction input data.

        Args:
            input_data: Transaction input hex string
            contract: Optional contract address for ABI lookup

        Returns:
            Decoded function call info
        """
        if not input_data or input_data == "0x":
            return {"function": "transfer (native)", "selector": "0x", "params": [], "decoded": True}

        # Extract function selector (first 4 bytes)
        selector = input_data[:10].lower()

        # Check known signatures
        if selector in KNOWN_SIGNATURES:
            sig = KNOWN_SIGNATURES[selector]
            return {
                "function": sig["name"],
                "selector": selector,
                "params": sig["params"],
                "raw_data": input_data[10:] if len(input_data) > 10 else "",
                "decoded": True,
            }

        # Try custom ABI if available
        if contract and contract.lower() in self.custom_abis:
            abi = self.custom_abis[contract.lower()]
            for item in abi:
                if item.get("type") == "function":
                    func_sig = self._get_function_selector(item)
                    if func_sig == selector:
                        return {
                            "function": item["name"],
                            "selector": selector,
                            "params": [f"{inp['type']} {inp.get('name', '')}" for inp in item.get("inputs", [])],
                            "raw_data": input_data[10:],
                            "decoded": True,
                        }

        # Unknown function
        return {
            "function": "unknown",
            "selector": selector,
            "params": [],
            "raw_data": input_data[10:] if len(input_data) > 10 else "",
            "decoded": False,
        }

    def decode_logs(self, logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Decode transaction logs/events.

        Args:
            logs: Transaction receipt logs

        Returns:
            Decoded events
        """
        decoded = []

        for log in logs:
            topics = log.get("topics", [])
            if not topics:
                continue

            event_sig = topics[0] if topics else None
            event_name = KNOWN_EVENTS.get(event_sig, "Unknown")

            decoded.append(
                {
                    "address": log.get("address"),
                    "event": event_name.split("(")[0] if "(" in event_name else event_name,
                    "signature": event_name,
                    "topic0": event_sig,
                    "topics": topics[1:],
                    "data": log.get("data"),
                    "log_index": log.get("logIndex"),
                }
            )

        return decoded

    def _get_function_selector(self, func: Dict[str, Any]) -> str:
        """Calculate function selector from ABI entry.

        Args:
            func: ABI function entry

        Returns:
            4-byte selector hex string
        """
        try:
            import hashlib

            # Build canonical function signature
            inputs = ",".join(inp["type"] for inp in func.get("inputs", []))
            sig = f"{func['name']}({inputs})"

            # Keccak-256 hash (first 4 bytes)
            # Note: This requires web3 or similar for proper keccak
            # Simplified here - in production use eth_abi
            h = hashlib.sha3_256(sig.encode()).hexdigest()
            return "0x" + h[:8]
        except Exception:
            return ""

    def decode_value(self, value_hex: str, param_type: str) -> Any:
        """Decode a single value from hex.

        Args:
            value_hex: Hex encoded value (32 bytes)
            param_type: Solidity type

        Returns:
            Decoded value
        """
        if not value_hex:
            return None

        # Remove 0x prefix if present
        hex_str = value_hex[2:] if value_hex.startswith("0x") else value_hex

        try:
            if "uint" in param_type or "int" in param_type:
                return int(hex_str, 16)
            elif param_type == "address":
                return "0x" + hex_str[-40:]
            elif param_type == "bool":
                return int(hex_str, 16) != 0
            else:
                return value_hex
        except Exception:
            return value_hex

    def format_decoded(self, decoded: Dict[str, Any]) -> str:
        """Format decoded transaction for display.

        Args:
            decoded: Decoded transaction info

        Returns:
            Formatted string
        """
        lines = [f"Function: {decoded['function']}"]
        lines.append(f"Selector: {decoded['selector']}")

        if decoded.get("params"):
            lines.append("Parameters:")
            for param in decoded["params"]:
                lines.append(f"  - {param}")

        if not decoded.get("decoded"):
            lines.append("(Unable to fully decode - unknown function)")

        return "\n".join(lines)


def identify_protocol(contract: str, function: str) -> Optional[str]:
    """Identify protocol from contract and function.

    Args:
        contract: Contract address
        function: Function name

    Returns:
        Protocol name if identified
    """
    # Known routers
    KNOWN_CONTRACTS = {
        "0x7a250d5630b4cf539739df2c5dacb4c659f2488d": "Uniswap V2 Router",
        "0xe592427a0aece92de3edee1f18e0157c05861564": "Uniswap V3 Router",
        "0x68b3465833fb72a70ecdf485e0e4c7bd8665fc45": "Uniswap V3 Router 02",
        "0x3fc91a3afd70395cd496c647d5a6cc9d4b2b7fad": "Uniswap Universal Router",
        "0xd9e1ce17f2641f24ae83637ab66a2cca9c378b9f": "SushiSwap Router",
        "0x1111111254eeb25477b68fb85ed929f73a960582": "1inch V5 Router",
        "0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2": "Aave V3 Pool",
        "0x7d2768de32b0b80b7a3454c06bdac94a69ddc7a9": "Aave V2 Pool",
    }

    contract_lower = contract.lower() if contract else ""
    if contract_lower in KNOWN_CONTRACTS:
        return KNOWN_CONTRACTS[contract_lower]

    # Identify by function
    if function in ["swapExactTokensForTokens", "swapExactETHForTokens"]:
        return "DEX (Uniswap V2 style)"
    elif function in ["exactInputSingle", "exactInput"]:
        return "DEX (Uniswap V3 style)"
    elif function in ["deposit", "withdraw", "borrow", "repay"]:
        return "Lending Protocol"
    elif function in ["transfer", "transferFrom", "approve"]:
        return "Token Contract"

    return None


def main():
    """CLI entry point for testing."""
    decoder = TransactionDecoder(verbose=True)

    # Test decode
    test_input = "0xa9059cbb000000000000000000000000abcdef1234567890abcdef1234567890abcdef120000000000000000000000000000000000000000000000000de0b6b3a7640000"

    result = decoder.decode_input(test_input)
    print(decoder.format_decoded(result))


if __name__ == "__main__":
    main()
