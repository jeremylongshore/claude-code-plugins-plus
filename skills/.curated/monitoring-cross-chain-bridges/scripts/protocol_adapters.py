#!/usr/bin/env python3
"""
Protocol Adapters

Protocol-specific adapters for bridge data.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 1.0.0
License: MIT
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List, Optional

try:
    import requests
except ImportError:
    requests = None

from config_loader import get_api_base_url


@dataclass
class FeeEstimate:
    """Bridge fee estimate."""

    bridge: str
    source_chain: str
    dest_chain: str
    token: str
    amount: Decimal
    bridge_fee: Decimal
    gas_fee_source: Decimal
    gas_fee_dest: Decimal
    total_fee: Decimal
    estimated_time_minutes: int


@dataclass
class TxStatus:
    """Bridge transaction status."""

    tx_hash: str
    bridge: str
    source_chain: str
    dest_chain: str
    status: str  # pending, confirmed, completed, failed
    source_confirmed: bool
    dest_confirmed: bool
    amount: Optional[Decimal] = None
    token: Optional[str] = None
    timestamp: Optional[int] = None
    estimated_completion: Optional[int] = None
    dest_tx_hash: Optional[str] = None


class ProtocolAdapter(ABC):
    """Base class for protocol adapters."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Protocol name."""
        pass

    @property
    @abstractmethod
    def supported_chains(self) -> List[str]:
        """List of supported chains."""
        pass

    @abstractmethod
    def get_fee_estimate(
        self, source_chain: str, dest_chain: str, token: str, amount: Decimal
    ) -> Optional[FeeEstimate]:
        """Get fee estimate for a bridge transfer."""
        pass

    @abstractmethod
    def get_tx_status(self, tx_hash: str) -> Optional[TxStatus]:
        """Get transaction status."""
        pass


class WormholeAdapter(ProtocolAdapter):
    """Wormhole bridge adapter."""

    CHAIN_IDS = {
        "ethereum": 2,
        "solana": 1,
        "bsc": 4,
        "polygon": 5,
        "avalanche": 6,
        "fantom": 10,
        "arbitrum": 23,
        "optimism": 24,
        "base": 30,
    }

    @property
    def name(self) -> str:
        return "Wormhole"

    @property
    def supported_chains(self) -> List[str]:
        return list(self.CHAIN_IDS.keys())

    def get_fee_estimate(
        self, source_chain: str, dest_chain: str, token: str, amount: Decimal
    ) -> Optional[FeeEstimate]:
        """Wormhole fee estimate (simplified)."""
        # Wormhole fees are primarily relayer fees
        # This is a simplified estimate
        base_fee = Decimal("0.001")  # ~0.1% bridge fee
        gas_source = Decimal("0.005")  # Estimated gas
        gas_dest = Decimal("0.002")  # Destination gas

        return FeeEstimate(
            bridge=self.name,
            source_chain=source_chain,
            dest_chain=dest_chain,
            token=token,
            amount=amount,
            bridge_fee=amount * base_fee,
            gas_fee_source=gas_source,
            gas_fee_dest=gas_dest,
            total_fee=amount * base_fee + gas_source + gas_dest,
            estimated_time_minutes=15,  # Typical Wormhole time
        )

    def get_tx_status(self, tx_hash: str) -> Optional[TxStatus]:
        """Get Wormhole transaction status."""
        if not requests:
            return None

        try:
            api_base = get_api_base_url("wormhole")
            url = f"{api_base}/vaas/{tx_hash}"
            response = requests.get(url, timeout=30)

            if response.status_code == 404:
                return TxStatus(
                    tx_hash=tx_hash,
                    bridge=self.name,
                    source_chain="",
                    dest_chain="",
                    status="not_found",
                    source_confirmed=False,
                    dest_confirmed=False,
                )

            response.raise_for_status()
            data = response.json()

            # Parse Wormhole VAA data
            return TxStatus(
                tx_hash=tx_hash,
                bridge=self.name,
                source_chain=data.get("emitterChain", ""),
                dest_chain=data.get("targetChain", ""),
                status="completed" if data.get("vaa") else "pending",
                source_confirmed=bool(data.get("vaa")),
                dest_confirmed=bool(data.get("destinationTx")),
                timestamp=data.get("timestamp"),
            )

        except (requests.RequestException, KeyError, ValueError):
            return None


class LayerZeroAdapter(ProtocolAdapter):
    """LayerZero bridge adapter."""

    CHAIN_IDS = {
        "ethereum": 101,
        "bsc": 102,
        "avalanche": 106,
        "polygon": 109,
        "arbitrum": 110,
        "optimism": 111,
        "fantom": 112,
        "base": 184,
    }

    @property
    def name(self) -> str:
        return "LayerZero"

    @property
    def supported_chains(self) -> List[str]:
        return list(self.CHAIN_IDS.keys())

    def get_fee_estimate(
        self, source_chain: str, dest_chain: str, token: str, amount: Decimal
    ) -> Optional[FeeEstimate]:
        """LayerZero fee estimate (simplified)."""
        # LayerZero fees depend on the app (Stargate, etc.)
        base_fee = Decimal("0.0006")  # ~0.06% typical
        gas_source = Decimal("0.008")
        gas_dest = Decimal("0.003")

        return FeeEstimate(
            bridge=self.name,
            source_chain=source_chain,
            dest_chain=dest_chain,
            token=token,
            amount=amount,
            bridge_fee=amount * base_fee,
            gas_fee_source=gas_source,
            gas_fee_dest=gas_dest,
            total_fee=amount * base_fee + gas_source + gas_dest,
            estimated_time_minutes=3,  # LayerZero is fast
        )

    def get_tx_status(self, tx_hash: str) -> Optional[TxStatus]:
        """Get LayerZero transaction status."""
        if not requests:
            return None

        try:
            api_base = get_api_base_url("layerzero")
            url = f"{api_base}/message/tx/{tx_hash}"
            response = requests.get(url, timeout=30)

            if response.status_code == 404:
                return TxStatus(
                    tx_hash=tx_hash,
                    bridge=self.name,
                    source_chain="",
                    dest_chain="",
                    status="not_found",
                    source_confirmed=False,
                    dest_confirmed=False,
                )

            response.raise_for_status()
            data = response.json()

            status = data.get("status", "pending")
            return TxStatus(
                tx_hash=tx_hash,
                bridge=self.name,
                source_chain=data.get("srcChainId", ""),
                dest_chain=data.get("dstChainId", ""),
                status="completed" if status == "DELIVERED" else "pending",
                source_confirmed=status in ["INFLIGHT", "DELIVERED"],
                dest_confirmed=status == "DELIVERED",
                timestamp=data.get("created"),
            )

        except (requests.RequestException, KeyError, ValueError):
            return None


class StargateAdapter(ProtocolAdapter):
    """Stargate bridge adapter (uses LayerZero)."""

    CHAIN_IDS = {
        "ethereum": 101,
        "bsc": 102,
        "avalanche": 106,
        "polygon": 109,
        "arbitrum": 110,
        "optimism": 111,
        "fantom": 112,
        "base": 184,
    }

    @property
    def name(self) -> str:
        return "Stargate"

    @property
    def supported_chains(self) -> List[str]:
        return list(self.CHAIN_IDS.keys())

    def get_fee_estimate(
        self, source_chain: str, dest_chain: str, token: str, amount: Decimal
    ) -> Optional[FeeEstimate]:
        """Stargate fee estimate."""
        # Stargate has liquidity pool fees
        base_fee = Decimal("0.0006")  # 0.06% fee
        gas_source = Decimal("0.01")
        gas_dest = Decimal("0.005")

        return FeeEstimate(
            bridge=self.name,
            source_chain=source_chain,
            dest_chain=dest_chain,
            token=token,
            amount=amount,
            bridge_fee=amount * base_fee,
            gas_fee_source=gas_source,
            gas_fee_dest=gas_dest,
            total_fee=amount * base_fee + gas_source + gas_dest,
            estimated_time_minutes=2,  # Stargate is very fast
        )

    def get_tx_status(self, tx_hash: str) -> Optional[TxStatus]:
        """Get Stargate transaction status (via LayerZero)."""
        # Stargate uses LayerZero, so delegate
        lz_adapter = LayerZeroAdapter()
        status = lz_adapter.get_tx_status(tx_hash)
        if status:
            status.bridge = self.name
        return status


class AcrossAdapter(ProtocolAdapter):
    """Across bridge adapter."""

    CHAIN_IDS = {
        "ethereum": 1,
        "optimism": 10,
        "arbitrum": 42161,
        "polygon": 137,
        "base": 8453,
        "zksync": 324,
    }

    @property
    def name(self) -> str:
        return "Across"

    @property
    def supported_chains(self) -> List[str]:
        return list(self.CHAIN_IDS.keys())

    def get_fee_estimate(
        self, source_chain: str, dest_chain: str, token: str, amount: Decimal
    ) -> Optional[FeeEstimate]:
        """Across fee estimate."""
        # Across uses relayers with variable fees
        base_fee = Decimal("0.0004")  # ~0.04% typical
        gas_source = Decimal("0.006")
        gas_dest = Decimal("0")  # Relayer pays dest gas

        return FeeEstimate(
            bridge=self.name,
            source_chain=source_chain,
            dest_chain=dest_chain,
            token=token,
            amount=amount,
            bridge_fee=amount * base_fee,
            gas_fee_source=gas_source,
            gas_fee_dest=gas_dest,
            total_fee=amount * base_fee + gas_source,
            estimated_time_minutes=1,  # Across is fastest
        )

    def get_tx_status(self, tx_hash: str) -> Optional[TxStatus]:
        """Get Across transaction status."""
        if not requests:
            return None

        try:
            api_base = get_api_base_url("across")
            url = f"{api_base}/deposit/status"
            params = {"depositTxHash": tx_hash}
            response = requests.get(url, params=params, timeout=30)

            if response.status_code == 404:
                return TxStatus(
                    tx_hash=tx_hash,
                    bridge=self.name,
                    source_chain="",
                    dest_chain="",
                    status="not_found",
                    source_confirmed=False,
                    dest_confirmed=False,
                )

            response.raise_for_status()
            data = response.json()

            status = data.get("status", "pending")
            return TxStatus(
                tx_hash=tx_hash,
                bridge=self.name,
                source_chain=str(data.get("originChainId", "")),
                dest_chain=str(data.get("destinationChainId", "")),
                status="completed" if status == "filled" else "pending",
                source_confirmed=True,
                dest_confirmed=status == "filled",
                amount=Decimal(str(data.get("amount", 0))),
                dest_tx_hash=data.get("fillTxHash"),
            )

        except (requests.RequestException, KeyError, ValueError):
            return None


# Registry of available adapters
ADAPTERS: Dict[str, ProtocolAdapter] = {
    "wormhole": WormholeAdapter(),
    "layerzero": LayerZeroAdapter(),
    "stargate": StargateAdapter(),
    "across": AcrossAdapter(),
}


def get_adapter(bridge: str) -> Optional[ProtocolAdapter]:
    """Get adapter for a bridge.

    Args:
        bridge: Bridge name (case-insensitive)

    Returns:
        ProtocolAdapter or None
    """
    return ADAPTERS.get(bridge.lower())


def get_all_adapters() -> Dict[str, ProtocolAdapter]:
    """Get all available adapters."""
    return ADAPTERS


def main():
    """CLI entry point for testing."""
    print("=== Protocol Adapters ===")

    for name, adapter in ADAPTERS.items():
        print(f"\n{adapter.name}:")
        print(f"  Chains: {', '.join(adapter.supported_chains[:5])}...")

        # Test fee estimate
        fee = adapter.get_fee_estimate("ethereum", "arbitrum", "USDC", Decimal("1000"))
        if fee:
            print(f"  Fee (1000 USDC ETH→ARB): ${fee.total_fee:.4f}")
            print(f"  Estimated time: {fee.estimated_time_minutes} min")


if __name__ == "__main__":
    main()
