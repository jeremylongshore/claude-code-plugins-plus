#!/usr/bin/env python3
"""
Wallet Label Database

Known wallet labels for exchanges, protocols, funds, and bridges.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 1.0.0
License: MIT
"""

import json
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass, asdict


@dataclass
class WalletLabel:
    """Wallet identification label."""

    address: str
    name: str
    entity_type: str  # exchange, protocol, fund, bridge, whale, unknown
    chain: str
    tags: List[str] = None
    notes: str = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


# Known exchange hot/cold wallets (partial list - real implementations would have thousands)
EXCHANGE_WALLETS = {
    # Ethereum
    "0x28c6c06298d514db089934071355e5743bf21d60": WalletLabel(
        address="0x28c6c06298d514db089934071355e5743bf21d60",
        name="Binance Hot Wallet 1",
        entity_type="exchange",
        chain="ethereum",
        tags=["binance", "hot_wallet"],
    ),
    "0x21a31ee1afc51d94c2efccaa2092ad1028285549": WalletLabel(
        address="0x21a31ee1afc51d94c2efccaa2092ad1028285549",
        name="Binance Cold Wallet",
        entity_type="exchange",
        chain="ethereum",
        tags=["binance", "cold_wallet"],
    ),
    "0xa9d1e08c7793af67e9d92fe308d5697fb81d3e43": WalletLabel(
        address="0xa9d1e08c7793af67e9d92fe308d5697fb81d3e43",
        name="Coinbase Commerce",
        entity_type="exchange",
        chain="ethereum",
        tags=["coinbase", "commerce"],
    ),
    "0x71660c4005ba85c37ccec55d0c4493e66fe775d3": WalletLabel(
        address="0x71660c4005ba85c37ccec55d0c4493e66fe775d3",
        name="Coinbase Hot Wallet",
        entity_type="exchange",
        chain="ethereum",
        tags=["coinbase", "hot_wallet"],
    ),
    "0x2910543af39aba0cd09dbb2d50200b3e800a63d2": WalletLabel(
        address="0x2910543af39aba0cd09dbb2d50200b3e800a63d2",
        name="Kraken Hot Wallet",
        entity_type="exchange",
        chain="ethereum",
        tags=["kraken", "hot_wallet"],
    ),
    "0x53d284357ec70ce289d6d64134dfac8e511c8a3d": WalletLabel(
        address="0x53d284357ec70ce289d6d64134dfac8e511c8a3d",
        name="Kraken Cold Wallet",
        entity_type="exchange",
        chain="ethereum",
        tags=["kraken", "cold_wallet"],
    ),
    "0x6cc5f688a315f3dc28a7781717a9a798a59fda7b": WalletLabel(
        address="0x6cc5f688a315f3dc28a7781717a9a798a59fda7b",
        name="OKX Hot Wallet",
        entity_type="exchange",
        chain="ethereum",
        tags=["okx", "hot_wallet"],
    ),
    "0x98ec059dc3adfbdd63429454aeb0c990fba4a128": WalletLabel(
        address="0x98ec059dc3adfbdd63429454aeb0c990fba4a128",
        name="Bybit Hot Wallet",
        entity_type="exchange",
        chain="ethereum",
        tags=["bybit", "hot_wallet"],
    ),
    # Bitcoin (sample)
    "bc1qm34lsc65zpw79lxes69zkqmk6ee3ewf0j77s3h": WalletLabel(
        address="bc1qm34lsc65zpw79lxes69zkqmk6ee3ewf0j77s3h",
        name="Binance BTC Cold",
        entity_type="exchange",
        chain="bitcoin",
        tags=["binance", "cold_wallet"],
    ),
}

# Known protocol treasuries
PROTOCOL_WALLETS = {
    "0xbe0eb53f46cd790cd13851d5eff43d12404d33e8": WalletLabel(
        address="0xbe0eb53f46cd790cd13851d5eff43d12404d33e8",
        name="Aave Treasury",
        entity_type="protocol",
        chain="ethereum",
        tags=["aave", "treasury"],
    ),
    "0x40ec5b33f54e0e8a33a975908c5ba1c14e5bbbdf": WalletLabel(
        address="0x40ec5b33f54e0e8a33a975908c5ba1c14e5bbbdf",
        name="Polygon Bridge",
        entity_type="bridge",
        chain="ethereum",
        tags=["polygon", "bridge"],
    ),
    "0x8eb8a3b98659cce290402893d0123abb75e3ab28": WalletLabel(
        address="0x8eb8a3b98659cce290402893d0123abb75e3ab28",
        name="Avalanche Bridge",
        entity_type="bridge",
        chain="ethereum",
        tags=["avalanche", "bridge"],
    ),
}

# Known VC/Fund wallets
FUND_WALLETS = {
    "0x9845e1909dca337944a0272f1f9f7249833d2d19": WalletLabel(
        address="0x9845e1909dca337944a0272f1f9f7249833d2d19",
        name="a16z Crypto",
        entity_type="fund",
        chain="ethereum",
        tags=["a16z", "vc"],
    ),
    "0x7cc61e3ae6360e923e9296c802382ec7c9dd3652": WalletLabel(
        address="0x7cc61e3ae6360e923e9296c802382ec7c9dd3652",
        name="Paradigm",
        entity_type="fund",
        chain="ethereum",
        tags=["paradigm", "vc"],
    ),
}


class WalletLabeler:
    """Manage and lookup wallet labels."""

    def __init__(self, custom_labels_file: str = None):
        """Initialize wallet labeler.

        Args:
            custom_labels_file: Path to custom labels JSON file
        """
        self.labels: Dict[str, WalletLabel] = {}
        self.watchlist: Dict[str, WalletLabel] = {}
        self.watchlist_file = Path.home() / ".whale_watchlist.json"

        # Load built-in labels
        self._load_builtin_labels()

        # Load custom labels if provided
        if custom_labels_file:
            self._load_custom_labels(custom_labels_file)

        # Load user watchlist
        self._load_watchlist()

    def _load_builtin_labels(self) -> None:
        """Load built-in wallet labels."""
        self.labels.update(EXCHANGE_WALLETS)
        self.labels.update(PROTOCOL_WALLETS)
        self.labels.update(FUND_WALLETS)

    def _load_custom_labels(self, filepath: str) -> None:
        """Load custom labels from JSON file."""
        try:
            with open(filepath) as f:
                data = json.load(f)
                for addr, info in data.items():
                    self.labels[addr.lower()] = WalletLabel(
                        address=addr.lower(),
                        name=info.get("name", "Unknown"),
                        entity_type=info.get("type", "unknown"),
                        chain=info.get("chain", "ethereum"),
                        tags=info.get("tags", []),
                    )
        except (IOError, json.JSONDecodeError):
            # Custom labels file is optional - continue with built-in labels only
            pass

    def _load_watchlist(self) -> None:
        """Load user watchlist from file."""
        try:
            if self.watchlist_file.exists():
                with open(self.watchlist_file) as f:
                    data = json.load(f)
                    for addr, info in data.items():
                        self.watchlist[addr.lower()] = WalletLabel(
                            address=addr.lower(),
                            name=info.get("name", "Watched"),
                            entity_type=info.get("type", "watched"),
                            chain=info.get("chain", "ethereum"),
                            tags=info.get("tags", ["watchlist"]),
                            notes=info.get("notes"),
                        )
        except (IOError, json.JSONDecodeError):
            # Watchlist is user-created - start empty if missing or corrupted
            pass

    def _save_watchlist(self) -> None:
        """Save watchlist to file."""
        try:
            data = {}
            for addr, label in self.watchlist.items():
                data[addr] = asdict(label)
            with open(self.watchlist_file, "w") as f:
                json.dump(data, f, indent=2)
        except IOError:
            # Watchlist save failures are non-fatal - changes may be lost on restart
            pass

    def label_wallet(self, address: str, chain: str = "ethereum") -> WalletLabel:
        """Get label for a wallet address.

        Args:
            address: Wallet address
            chain: Blockchain network

        Returns:
            WalletLabel with identification info
        """
        addr_lower = address.lower()

        # Check watchlist first
        if addr_lower in self.watchlist:
            return self.watchlist[addr_lower]

        # Check known labels
        if addr_lower in self.labels:
            return self.labels[addr_lower]

        # Return unknown label
        return WalletLabel(
            address=address,
            name=self._generate_short_name(address),
            entity_type="unknown",
            chain=chain,
            tags=[],
        )

    def _generate_short_name(self, address: str) -> str:
        """Generate a short display name for unknown address."""
        if address.startswith("0x"):
            return f"{address[:6]}...{address[-4:]}"
        elif address.startswith("bc1"):
            return f"{address[:8]}...{address[-4:]}"
        else:
            return f"{address[:8]}..."

    def add_to_watchlist(self, address: str, name: str, chain: str = "ethereum", notes: str = None) -> WalletLabel:
        """Add wallet to watchlist.

        Args:
            address: Wallet address
            name: Display name
            chain: Blockchain network
            notes: Optional notes

        Returns:
            Created WalletLabel
        """
        label = WalletLabel(
            address=address.lower(),
            name=name,
            entity_type="watched",
            chain=chain,
            tags=["watchlist"],
            notes=notes,
        )
        self.watchlist[address.lower()] = label
        self._save_watchlist()
        return label

    def remove_from_watchlist(self, address: str) -> bool:
        """Remove wallet from watchlist.

        Args:
            address: Wallet address

        Returns:
            True if removed, False if not found
        """
        addr_lower = address.lower()
        if addr_lower in self.watchlist:
            del self.watchlist[addr_lower]
            self._save_watchlist()
            return True
        return False

    def get_watchlist(self) -> List[WalletLabel]:
        """Get all watched wallets.

        Returns:
            List of WalletLabel entries
        """
        return list(self.watchlist.values())

    def search_labels(self, query: str) -> List[WalletLabel]:
        """Search labels by name or tag.

        Args:
            query: Search query

        Returns:
            Matching labels
        """
        query_lower = query.lower()
        results = []

        for label in list(self.labels.values()) + list(self.watchlist.values()):
            if query_lower in label.name.lower():
                results.append(label)
            elif any(query_lower in tag.lower() for tag in label.tags):
                results.append(label)

        return results

    def get_by_type(self, entity_type: str) -> List[WalletLabel]:
        """Get all wallets of a specific type.

        Args:
            entity_type: exchange, protocol, fund, bridge, etc.

        Returns:
            Matching labels
        """
        results = []
        for label in list(self.labels.values()) + list(self.watchlist.values()):
            if label.entity_type == entity_type:
                results.append(label)
        return results


def main():
    """CLI entry point for testing."""
    labeler = WalletLabeler()

    print("=== Known Exchange Wallets ===")
    exchanges = labeler.get_by_type("exchange")
    for wallet in exchanges[:5]:
        print(f"  {wallet.name}: {wallet.address[:20]}...")

    print("\n=== Total Labels ===")
    print(f"  Built-in: {len(labeler.labels)}")
    print(f"  Watchlist: {len(labeler.watchlist)}")

    print("\n=== Test Label Lookup ===")
    test_addr = "0x28c6c06298d514db089934071355e5743bf21d60"
    label = labeler.label_wallet(test_addr)
    print(f"  {test_addr[:20]}... → {label.name} ({label.entity_type})")

    unknown_addr = "0x1234567890abcdef1234567890abcdef12345678"
    label = labeler.label_wallet(unknown_addr)
    print(f"  {unknown_addr[:20]}... → {label.name} ({label.entity_type})")


if __name__ == "__main__":
    main()
