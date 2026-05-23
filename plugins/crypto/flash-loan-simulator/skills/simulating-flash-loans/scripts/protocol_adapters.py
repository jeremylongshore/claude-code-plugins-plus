#!/usr/bin/env python3
"""
Flash loan protocol adapters.

Abstracts flash loan providers (Aave, dYdX, Balancer) with
unified interface for fee calculation and liquidity checks.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List, Optional


@dataclass
class LoanParams:
    """Parameters for a flash loan request."""

    asset: str
    amount: Decimal
    chain: str = "ethereum"


@dataclass
class ProviderInfo:
    """Information about a flash loan provider."""

    name: str
    fee_rate: Decimal
    fee_amount: Decimal
    max_available: Decimal
    supported_chains: List[str]
    gas_overhead: int  # Extra gas for using this provider


class FlashLoanProvider(ABC):
    """Abstract base class for flash loan providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
        pass

    @property
    @abstractmethod
    def fee_rate(self) -> Decimal:
        """Fee rate as decimal (e.g., 0.0009 for 0.09%)."""
        pass

    @abstractmethod
    def get_fee(self, asset: str, amount: Decimal) -> Decimal:
        """Calculate flash loan fee."""
        pass

    @abstractmethod
    def get_max_loan(self, asset: str, chain: str = "ethereum") -> Decimal:
        """Get maximum available loan amount."""
        pass

    @abstractmethod
    def get_supported_assets(self, chain: str = "ethereum") -> List[str]:
        """Get list of supported assets."""
        pass

    @abstractmethod
    def get_gas_overhead(self) -> int:
        """Get extra gas units for using this provider."""
        pass

    def get_info(self, asset: str, amount: Decimal, chain: str = "ethereum") -> ProviderInfo:
        """Get complete provider info for a loan."""
        return ProviderInfo(
            name=self.name,
            fee_rate=self.fee_rate,
            fee_amount=self.get_fee(asset, amount),
            max_available=self.get_max_loan(asset, chain),
            supported_chains=self.supported_chains,
            gas_overhead=self.get_gas_overhead(),
        )

    @property
    @abstractmethod
    def supported_chains(self) -> List[str]:
        """List of supported chains."""
        pass


class AaveV3Provider(FlashLoanProvider):
    """
    Aave V3 flash loan provider.

    Fee: 0.09% (9 basis points)
    Chains: Ethereum, Polygon, Arbitrum, Optimism, Avalanche
    """

    FEE_RATE = Decimal("0.0009")  # 0.09%

    POOL_ADDRESSES = {
        "ethereum": "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
        "polygon": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
        "arbitrum": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
        "optimism": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
        "avalanche": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
    }

    # Approximate max liquidity per asset (in USD equivalent)
    MAX_LIQUIDITY = {
        "ETH": Decimal("500000"),  # ~500K ETH available
        "WETH": Decimal("500000"),
        "USDC": Decimal("1000000000"),  # ~1B USDC
        "USDT": Decimal("500000000"),
        "DAI": Decimal("300000000"),
        "WBTC": Decimal("10000"),  # ~10K WBTC
    }

    @property
    def name(self) -> str:
        return "Aave V3"

    @property
    def fee_rate(self) -> Decimal:
        return self.FEE_RATE

    @property
    def supported_chains(self) -> List[str]:
        return list(self.POOL_ADDRESSES.keys())

    def get_fee(self, asset: str, amount: Decimal) -> Decimal:
        """Aave charges flat 0.09% fee."""
        return amount * self.FEE_RATE

    def get_max_loan(self, asset: str, chain: str = "ethereum") -> Decimal:
        """Get max available from Aave pools."""
        asset_upper = asset.upper()
        return self.MAX_LIQUIDITY.get(asset_upper, Decimal("0"))

    def get_supported_assets(self, chain: str = "ethereum") -> List[str]:
        """Aave supports most major tokens."""
        return list(self.MAX_LIQUIDITY.keys())

    def get_gas_overhead(self) -> int:
        """Aave flash loans add ~100k gas overhead."""
        return 100000


class DydxProvider(FlashLoanProvider):
    """
    dYdX flash loan provider.

    Fee: 0% (FREE flash loans!)
    Chains: Ethereum only
    Assets: ETH, USDC, DAI, WBTC (limited selection)
    """

    FEE_RATE = Decimal("0")  # 0% - FREE!

    SOLO_MARGIN_ADDRESS = "0x1E0447b19BB6EcFdAe1e4AE1694b0C3659614e4e"

    SUPPORTED_ASSETS = ["ETH", "WETH", "USDC", "DAI", "WBTC"]

    MAX_LIQUIDITY = {
        "ETH": Decimal("50000"),
        "WETH": Decimal("50000"),
        "USDC": Decimal("100000000"),
        "DAI": Decimal("50000000"),
        "WBTC": Decimal("1000"),
    }

    @property
    def name(self) -> str:
        return "dYdX"

    @property
    def fee_rate(self) -> Decimal:
        return self.FEE_RATE

    @property
    def supported_chains(self) -> List[str]:
        return ["ethereum"]

    def get_fee(self, asset: str, amount: Decimal) -> Decimal:
        """dYdX has 0% flash loan fee!"""
        return Decimal("0")

    def get_max_loan(self, asset: str, chain: str = "ethereum") -> Decimal:
        """Get max available from dYdX."""
        if chain != "ethereum":
            return Decimal("0")
        return self.MAX_LIQUIDITY.get(asset.upper(), Decimal("0"))

    def get_supported_assets(self, chain: str = "ethereum") -> List[str]:
        """dYdX has limited asset support."""
        if chain != "ethereum":
            return []
        return self.SUPPORTED_ASSETS

    def get_gas_overhead(self) -> int:
        """dYdX flash loans are slightly more gas-intensive."""
        return 150000


class BalancerProvider(FlashLoanProvider):
    """
    Balancer flash loan provider.

    Fee: 0.01% (1 basis point) - Very cheap!
    Chains: Ethereum, Polygon, Arbitrum
    Assets: Any pool token
    """

    FEE_RATE = Decimal("0.0001")  # 0.01%

    VAULT_ADDRESSES = {
        "ethereum": "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
        "polygon": "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
        "arbitrum": "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
    }

    MAX_LIQUIDITY = {
        "ETH": Decimal("100000"),
        "WETH": Decimal("100000"),
        "USDC": Decimal("200000000"),
        "DAI": Decimal("100000000"),
        "WBTC": Decimal("5000"),
        "BAL": Decimal("10000000"),
    }

    @property
    def name(self) -> str:
        return "Balancer"

    @property
    def fee_rate(self) -> Decimal:
        return self.FEE_RATE

    @property
    def supported_chains(self) -> List[str]:
        return list(self.VAULT_ADDRESSES.keys())

    def get_fee(self, asset: str, amount: Decimal) -> Decimal:
        """Balancer charges 0.01% fee."""
        return amount * self.FEE_RATE

    def get_max_loan(self, asset: str, chain: str = "ethereum") -> Decimal:
        """Get max available from Balancer pools."""
        if chain not in self.VAULT_ADDRESSES:
            return Decimal("0")
        return self.MAX_LIQUIDITY.get(asset.upper(), Decimal("0"))

    def get_supported_assets(self, chain: str = "ethereum") -> List[str]:
        """Balancer supports pool tokens."""
        return list(self.MAX_LIQUIDITY.keys())

    def get_gas_overhead(self) -> int:
        """Balancer flash loans are gas-efficient."""
        return 80000


class UniswapV3Provider(FlashLoanProvider):
    """
    Uniswap V3 flash swap provider.

    Fee: Pool fee (~0.3% for most pairs, but paid implicitly)
    Note: Technically a flash swap, not a loan - you receive
    tokens upfront and pay back with fee in same tx.
    """

    # Pool fees vary: 0.01%, 0.05%, 0.3%, 1%
    # We use 0.3% as default (most common)
    FEE_RATE = Decimal("0.003")

    ROUTER_ADDRESSES = {
        "ethereum": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
        "polygon": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
        "arbitrum": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
        "optimism": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
    }

    MAX_LIQUIDITY = {
        "ETH": Decimal("200000"),
        "WETH": Decimal("200000"),
        "USDC": Decimal("500000000"),
        "USDT": Decimal("300000000"),
        "DAI": Decimal("200000000"),
        "WBTC": Decimal("5000"),
    }

    @property
    def name(self) -> str:
        return "Uniswap V3"

    @property
    def fee_rate(self) -> Decimal:
        return self.FEE_RATE

    @property
    def supported_chains(self) -> List[str]:
        return list(self.ROUTER_ADDRESSES.keys())

    def get_fee(self, asset: str, amount: Decimal) -> Decimal:
        """Uniswap charges pool fee (implicit in swap)."""
        return amount * self.FEE_RATE

    def get_max_loan(self, asset: str, chain: str = "ethereum") -> Decimal:
        """Get max available from Uniswap pools."""
        if chain not in self.ROUTER_ADDRESSES:
            return Decimal("0")
        return self.MAX_LIQUIDITY.get(asset.upper(), Decimal("0"))

    def get_supported_assets(self, chain: str = "ethereum") -> List[str]:
        """Uniswap supports any paired token."""
        return list(self.MAX_LIQUIDITY.keys())

    def get_gas_overhead(self) -> int:
        """Uniswap flash swaps are moderately gas-intensive."""
        return 120000


class ProviderManager:
    """
    Manages all flash loan providers.

    Provides comparison and selection capabilities.
    """

    def __init__(self):
        """Initialize with all providers."""
        self.providers: Dict[str, FlashLoanProvider] = {
            "aave": AaveV3Provider(),
            "dydx": DydxProvider(),
            "balancer": BalancerProvider(),
            "uniswap": UniswapV3Provider(),
        }

    def get_provider(self, name: str) -> Optional[FlashLoanProvider]:
        """Get provider by name."""
        return self.providers.get(name.lower())

    def list_providers(self) -> List[str]:
        """List all available providers."""
        return list(self.providers.keys())

    def compare_providers(self, asset: str, amount: Decimal, chain: str = "ethereum") -> List[ProviderInfo]:
        """
        Compare all providers for a specific loan.

        Returns providers sorted by total cost (lowest first).
        """
        results = []

        for provider in self.providers.values():
            if chain not in provider.supported_chains:
                continue
            if asset.upper() not in provider.get_supported_assets(chain):
                continue
            if amount > provider.get_max_loan(asset, chain):
                continue

            info = provider.get_info(asset, amount, chain)
            results.append(info)

        # Sort by fee amount (cheapest first)
        results.sort(key=lambda x: x.fee_amount)
        return results

    def find_cheapest(self, asset: str, amount: Decimal, chain: str = "ethereum") -> Optional[ProviderInfo]:
        """Find the cheapest provider for a loan."""
        providers = self.compare_providers(asset, amount, chain)
        return providers[0] if providers else None


def demo():
    """Demonstrate provider comparison."""
    manager = ProviderManager()

    print("=" * 60)
    print("FLASH LOAN PROVIDER COMPARISON")
    print("=" * 60)

    # Compare for 100 ETH loan
    asset = "ETH"
    amount = Decimal("100")

    print(f"\nComparing providers for {amount} {asset} flash loan:")
    print("-" * 60)

    providers = manager.compare_providers(asset, amount)

    for info in providers:
        fee_pct = float(info.fee_rate) * 100
        print(f"\n{info.name}:")
        print(f"  Fee Rate: {fee_pct:.2f}%")
        print(f"  Fee Amount: {info.fee_amount:.4f} {asset}")
        print(f"  Max Available: {info.max_available:,.0f} {asset}")
        print(f"  Gas Overhead: {info.gas_overhead:,} units")
        print(f"  Chains: {', '.join(info.supported_chains)}")

    # Find cheapest
    cheapest = manager.find_cheapest(asset, amount)
    if cheapest:
        print(f"\n{'=' * 60}")
        print(f"RECOMMENDATION: {cheapest.name}")
        print(f"  Lowest fee: {cheapest.fee_amount:.4f} {asset}")
        if cheapest.fee_amount == 0:
            print("  (FREE flash loan!)")


if __name__ == "__main__":
    demo()
