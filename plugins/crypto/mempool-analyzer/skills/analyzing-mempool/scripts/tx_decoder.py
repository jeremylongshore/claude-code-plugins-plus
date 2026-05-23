#!/usr/bin/env python3
"""
Transaction Decoder

Decode Ethereum transaction input data using known ABIs.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 1.0.0
License: MIT
"""

from typing import Any, Dict, Optional
from dataclasses import dataclass


# Common DEX method signatures (first 4 bytes of keccak256)
METHOD_SIGNATURES = {
    # Uniswap V2 Router
    "0x38ed1739": {"name": "swapExactTokensForTokens", "type": "swap"},
    "0x8803dbee": {"name": "swapTokensForExactTokens", "type": "swap"},
    "0x7ff36ab5": {"name": "swapExactETHForTokens", "type": "swap"},
    "0x4a25d94a": {"name": "swapTokensForExactETH", "type": "swap"},
    "0x18cbafe5": {"name": "swapExactTokensForETH", "type": "swap"},
    "0xfb3bdb41": {"name": "swapETHForExactTokens", "type": "swap"},
    "0xe8e33700": {"name": "addLiquidity", "type": "liquidity"},
    "0xf305d719": {"name": "addLiquidityETH", "type": "liquidity"},
    "0xbaa2abde": {"name": "removeLiquidity", "type": "liquidity"},
    "0x02751cec": {"name": "removeLiquidityETH", "type": "liquidity"},
    # Uniswap V3 Router
    "0x414bf389": {"name": "exactInputSingle", "type": "swap"},
    "0xc04b8d59": {"name": "exactInput", "type": "swap"},
    "0xdb3e2198": {"name": "exactOutputSingle", "type": "swap"},
    "0xf28c0498": {"name": "exactOutput", "type": "swap"},
    "0x5ae401dc": {"name": "multicall", "type": "multicall"},
    "0xac9650d8": {"name": "multicall", "type": "multicall"},
    # ERC20
    "0xa9059cbb": {"name": "transfer", "type": "transfer"},
    "0x23b872dd": {"name": "transferFrom", "type": "transfer"},
    "0x095ea7b3": {"name": "approve", "type": "approval"},
    # Common
    "0x": {"name": "ETH Transfer", "type": "transfer"},
}

# Known contract addresses
KNOWN_CONTRACTS = {
    # Ethereum Mainnet
    "0x7a250d5630b4cf539739df2c5dacb4c659f2488d": "Uniswap V2 Router",
    "0xe592427a0aece92de3edee1f18e0157c05861564": "Uniswap V3 Router",
    "0x68b3465833fb72a70ecdf485e0e4c7bd8665fc45": "Uniswap Universal Router",
    "0xd9e1ce17f2641f24ae83637ab66a2cca9c378b9f": "SushiSwap Router",
    "0x1111111254fb6c44bac0bed2854e76f90643097d": "1inch Router",
    "0xdef1c0ded9bec7f1a1670819833240f027b25eff": "0x Exchange Proxy",
    "0x881d40237659c251811cec9c364ef91dc08d300c": "Metamask Swap Router",
    # Tokens
    "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2": "WETH",
    "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": "USDC",
    "0xdac17f958d2ee523a2206206994597c13d831ec7": "USDT",
    "0x6b175474e89094c44da98b954eedeac495271d0f": "DAI",
}


@dataclass
class DecodedCall:
    """Decoded function call."""

    method_name: str
    method_type: str  # swap, transfer, approval, liquidity, multicall, unknown
    contract_name: Optional[str]
    raw_signature: str
    params: Dict[str, Any]


@dataclass
class SwapInfo:
    """Detected swap information."""

    dex: str
    method: str
    token_in: Optional[str]
    token_out: Optional[str]
    amount_in: Optional[int]
    amount_out_min: Optional[int]
    is_exact_input: bool


class TransactionDecoder:
    """Decode Ethereum transaction input data."""

    def __init__(self, verbose: bool = False):
        """Initialize decoder."""
        self.verbose = verbose

    def decode_input(self, input_data: str, to_address: str = None) -> DecodedCall:
        """Decode transaction input data.

        Args:
            input_data: Transaction input (hex string)
            to_address: Destination contract address

        Returns:
            DecodedCall with decoded information
        """
        if not input_data or input_data == "0x":
            return DecodedCall(
                method_name="ETH Transfer",
                method_type="transfer",
                contract_name=self._get_contract_name(to_address) if to_address else None,
                raw_signature="0x",
                params={},
            )

        # Get method signature (first 4 bytes)
        signature = input_data[:10].lower()

        method_info = METHOD_SIGNATURES.get(
            signature,
            {
                "name": "Unknown",
                "type": "unknown",
            },
        )

        contract_name = self._get_contract_name(to_address) if to_address else None

        return DecodedCall(
            method_name=method_info["name"],
            method_type=method_info["type"],
            contract_name=contract_name,
            raw_signature=signature,
            params=self._decode_params(input_data, signature),
        )

    def _get_contract_name(self, address: str) -> Optional[str]:
        """Get known contract name."""
        if not address:
            return None
        return KNOWN_CONTRACTS.get(address.lower())

    def _decode_params(self, input_data: str, signature: str) -> Dict[str, Any]:
        """Decode function parameters (simplified)."""
        if len(input_data) < 10:
            return {}

        # Remove signature
        data = input_data[10:]
        if not data:
            return {}

        params = {}

        # Parse 32-byte chunks
        chunks = [data[i : i + 64] for i in range(0, len(data), 64)]

        # For swaps, try to extract amounts
        if signature in ["0x38ed1739", "0x8803dbee"]:
            # swapExactTokensForTokens / swapTokensForExactTokens
            if len(chunks) >= 2:
                params["amountIn"] = int(chunks[0], 16) if chunks[0] else 0
                params["amountOutMin"] = int(chunks[1], 16) if chunks[1] else 0

        elif signature in ["0x7ff36ab5", "0xfb3bdb41"]:
            # swapExactETHForTokens / swapETHForExactTokens
            if len(chunks) >= 1:
                params["amountOutMin"] = int(chunks[0], 16) if chunks[0] else 0

        elif signature == "0xa9059cbb":
            # transfer(address, uint256)
            if len(chunks) >= 2:
                params["to"] = "0x" + chunks[0][-40:]
                params["amount"] = int(chunks[1], 16) if chunks[1] else 0

        elif signature == "0x095ea7b3":
            # approve(address, uint256)
            if len(chunks) >= 2:
                params["spender"] = "0x" + chunks[0][-40:]
                params["amount"] = int(chunks[1], 16) if chunks[1] else 0

        return params

    def identify_dex_swap(self, input_data: str, to_address: str) -> Optional[SwapInfo]:
        """Identify if transaction is a DEX swap.

        Args:
            input_data: Transaction input data
            to_address: Destination address

        Returns:
            SwapInfo if swap detected, None otherwise
        """
        decoded = self.decode_input(input_data, to_address)

        if decoded.method_type != "swap":
            return None

        dex = decoded.contract_name or "Unknown DEX"
        is_exact_input = "exact" in decoded.method_name.lower() and "input" in decoded.method_name.lower()

        return SwapInfo(
            dex=dex,
            method=decoded.method_name,
            token_in=None,  # Would need path decoding
            token_out=None,
            amount_in=decoded.params.get("amountIn"),
            amount_out_min=decoded.params.get("amountOutMin"),
            is_exact_input=is_exact_input,
        )

    def classify_transaction(self, tx: Dict) -> str:
        """Classify transaction type.

        Args:
            tx: Transaction dict with 'input' and 'to' fields

        Returns:
            Transaction type string
        """
        input_data = tx.get("input_data", "") or tx.get("input", "")
        to_address = tx.get("to_address", "") or tx.get("to", "")

        decoded = self.decode_input(input_data, to_address)
        return decoded.method_type

    def estimate_attached_eth_usd_value(self, tx: Dict, eth_price: float = 3000.0) -> float:
        """Estimate USD value of ETH attached to transaction (msg.value).

        Note: This only calculates the USD value of ETH sent with the transaction.
        For token swaps, the actual value is in the tokens being exchanged,
        not the attached ETH (which is often zero). Use this for ETH transfers
        or transactions that include ETH payment.

        Args:
            tx: Transaction dict with 'value' field (in wei)
            eth_price: Current ETH price in USD

        Returns:
            USD value of attached ETH (not the full transaction value for swaps)
        """
        value_wei = tx.get("value", 0)
        if isinstance(value_wei, str):
            value_wei = int(value_wei, 16) if value_wei.startswith("0x") else int(value_wei)

        value_eth = value_wei / 10**18
        return value_eth * eth_price

    # Backward compatibility alias
    estimate_usd_value = estimate_attached_eth_usd_value


def main():
    """CLI entry point for testing."""
    decoder = TransactionDecoder(verbose=True)

    # Test decode
    test_cases = [
        ("0x38ed1739" + "0" * 256, "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"),
        ("0xa9059cbb" + "0" * 128, "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"),
        ("0x", None),
    ]

    print("=== Transaction Decoding Tests ===")
    for input_data, to_addr in test_cases:
        decoded = decoder.decode_input(input_data, to_addr)
        print(f"\nInput: {input_data[:20]}...")
        print(f"  Method: {decoded.method_name}")
        print(f"  Type: {decoded.method_type}")
        print(f"  Contract: {decoded.contract_name or 'Unknown'}")


if __name__ == "__main__":
    main()
