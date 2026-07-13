#!/usr/bin/env python3
"""
Transaction Cost Estimator

Estimate gas costs for common blockchain operations.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 1.0.0
License: MIT
"""

import time
from typing import Dict
from dataclasses import dataclass

try:
    import requests
except ImportError:
    requests = None


# Standard gas limits for common operations
GAS_LIMITS = {
    "eth_transfer": 21000,
    "erc20_transfer": 65000,
    "erc20_approve": 46000,
    "uniswap_v2_swap": 150000,
    "uniswap_v3_swap": 185000,
    "sushiswap_swap": 150000,
    "curve_swap": 300000,
    "nft_mint": 150000,
    "nft_transfer": 85000,
    "opensea_listing": 200000,
    "aave_deposit": 250000,
    "aave_withdraw": 180000,
    "compound_supply": 200000,
    "compound_borrow": 350000,
    "bridge_deposit": 100000,
}


@dataclass
class CostEstimate:
    """Transaction cost estimate."""

    operation: str
    gas_limit: int
    gas_price_gwei: float
    gas_cost_native: float  # in ETH/MATIC
    gas_cost_usd: float
    tier: str  # slow, standard, fast, instant


@dataclass
class MultiTierEstimate:
    """Cost estimates for all tiers."""

    operation: str
    gas_limit: int
    slow: CostEstimate
    standard: CostEstimate
    fast: CostEstimate
    instant: CostEstimate


class CostEstimator:
    """Estimate transaction costs."""

    def __init__(self, native_symbol: str = "ETH", verbose: bool = False):
        """Initialize cost estimator.

        Args:
            native_symbol: Native token symbol for the chain
            verbose: Enable verbose output
        """
        self.native_symbol = native_symbol
        self.verbose = verbose
        self._price_cache = {}
        self._price_cache_time = 0
        self._price_cache_ttl = 60  # seconds

    def _get_native_price(self) -> float:
        """Get native token price in USD."""
        now = time.time()
        if now - self._price_cache_time < self._price_cache_ttl:
            return self._price_cache.get(self.native_symbol, 3000.0)

        if not requests:
            return 3000.0 if self.native_symbol == "ETH" else 1.0

        try:
            # Map symbols to CoinGecko IDs
            symbol_to_id = {
                "ETH": "ethereum",
                "MATIC": "matic-network",
            }
            coin_id = symbol_to_id.get(self.native_symbol, "ethereum")

            response = requests.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={"ids": coin_id, "vs_currencies": "usd"},
                timeout=10,
            )
            data = response.json()
            price = data.get(coin_id, {}).get("usd", 3000.0)

            self._price_cache[self.native_symbol] = price
            self._price_cache_time = now

            return price

        except Exception as e:
            if self.verbose:
                print(f"Price fetch error: {e}")
            return 3000.0 if self.native_symbol == "ETH" else 1.0

    def estimate_cost(
        self, operation: str, gas_price_gwei: float, tier: str = "standard", custom_gas_limit: int = None
    ) -> CostEstimate:
        """Estimate cost for an operation.

        Args:
            operation: Operation name (eth_transfer, uniswap_v2_swap, etc.)
            gas_price_gwei: Gas price in gwei
            tier: Price tier (slow, standard, fast, instant)
            custom_gas_limit: Override default gas limit

        Returns:
            CostEstimate with costs
        """
        gas_limit = custom_gas_limit or GAS_LIMITS.get(operation, 100000)
        gas_cost_wei = gas_limit * gas_price_gwei * 10**9
        gas_cost_native = gas_cost_wei / 10**18
        native_price = self._get_native_price()
        gas_cost_usd = gas_cost_native * native_price

        return CostEstimate(
            operation=operation,
            gas_limit=gas_limit,
            gas_price_gwei=gas_price_gwei,
            gas_cost_native=gas_cost_native,
            gas_cost_usd=gas_cost_usd,
            tier=tier,
        )

    def estimate_all_tiers(
        self,
        operation: str,
        gas_slow: float,
        gas_standard: float,
        gas_fast: float,
        gas_instant: float,
        custom_gas_limit: int = None,
    ) -> MultiTierEstimate:
        """Estimate costs for all tiers.

        Args:
            operation: Operation name
            gas_slow: Slow tier gas price (gwei)
            gas_standard: Standard tier gas price (gwei)
            gas_fast: Fast tier gas price (gwei)
            gas_instant: Instant tier gas price (gwei)
            custom_gas_limit: Override default gas limit

        Returns:
            MultiTierEstimate with all tier estimates
        """
        gas_limit = custom_gas_limit or GAS_LIMITS.get(operation, 100000)

        return MultiTierEstimate(
            operation=operation,
            gas_limit=gas_limit,
            slow=self.estimate_cost(operation, gas_slow, "slow", gas_limit),
            standard=self.estimate_cost(operation, gas_standard, "standard", gas_limit),
            fast=self.estimate_cost(operation, gas_fast, "fast", gas_limit),
            instant=self.estimate_cost(operation, gas_instant, "instant", gas_limit),
        )

    def estimate_transfer(self, gas_price_gwei: float) -> CostEstimate:
        """Estimate ETH transfer cost."""
        return self.estimate_cost("eth_transfer", gas_price_gwei)

    def estimate_swap(self, gas_price_gwei: float, dex: str = "uniswap_v2") -> CostEstimate:
        """Estimate DEX swap cost.

        Args:
            gas_price_gwei: Gas price in gwei
            dex: DEX name (uniswap_v2, uniswap_v3, sushiswap, curve)

        Returns:
            CostEstimate for the swap
        """
        operation = f"{dex}_swap"
        return self.estimate_cost(operation, gas_price_gwei)

    def estimate_nft_mint(self, gas_price_gwei: float) -> CostEstimate:
        """Estimate NFT mint cost."""
        return self.estimate_cost("nft_mint", gas_price_gwei)

    def estimate_custom(self, gas_price_gwei: float, gas_limit: int) -> CostEstimate:
        """Estimate cost for custom gas limit.

        Args:
            gas_price_gwei: Gas price in gwei
            gas_limit: Custom gas limit

        Returns:
            CostEstimate for custom operation
        """
        return self.estimate_cost("custom", gas_price_gwei, "standard", gas_limit)

    def list_operations(self) -> Dict[str, int]:
        """List all known operations and their gas limits.

        Returns:
            Dict mapping operation name to gas limit
        """
        return GAS_LIMITS.copy()


def main():
    """CLI entry point for testing."""
    estimator = CostEstimator(verbose=True)

    print("=== Known Operations ===")
    for op, gas in sorted(GAS_LIMITS.items(), key=lambda x: x[1]):
        print(f"  {op:<20}: {gas:,} gas")

    print("\n=== Cost Estimates at 30 gwei ===")
    gas_price = 30.0

    ops = ["eth_transfer", "erc20_transfer", "uniswap_v2_swap", "nft_mint"]
    for op in ops:
        est = estimator.estimate_cost(op, gas_price)
        print(f"  {op:<20}: {est.gas_cost_native:.6f} {estimator.native_symbol} (${est.gas_cost_usd:.2f})")

    print("\n=== Multi-Tier Estimate for Uniswap Swap ===")
    multi = estimator.estimate_all_tiers("uniswap_v2_swap", 20, 30, 45, 60)
    print(f"  Slow:     ${multi.slow.gas_cost_usd:.2f}")
    print(f"  Standard: ${multi.standard.gas_cost_usd:.2f}")
    print(f"  Fast:     ${multi.fast.gas_cost_usd:.2f}")
    print(f"  Instant:  ${multi.instant.gas_cost_usd:.2f}")


if __name__ == "__main__":
    main()
