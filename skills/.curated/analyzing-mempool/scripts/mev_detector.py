#!/usr/bin/env python3
"""
MEV Opportunity Detector

Detect potential MEV opportunities in pending transactions.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 1.0.0
License: MIT
"""

import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

try:
    import yaml

    HAS_YAML = True
except ImportError:
    HAS_YAML = False

from tx_decoder import TransactionDecoder


@dataclass
class MEVOpportunity:
    """Detected MEV opportunity."""

    opportunity_type: str  # sandwich, arbitrage, liquidation, backrun
    target_tx: str  # Target transaction hash
    estimated_profit_usd: float
    required_capital_usd: float
    risk_level: str  # low, medium, high
    confidence: float  # 0.0 to 1.0
    details: Dict[str, Any]


@dataclass
class PendingSwap:
    """Detected pending swap transaction."""

    tx_hash: str
    dex: str
    amount_in: Optional[int]
    amount_out_min: Optional[int]
    gas_price: int
    from_address: str


class MEVDetector:
    """Detect MEV opportunities in pending transactions."""

    # Default thresholds (can be overridden via config)
    DEFAULT_MIN_SWAP_VALUE_USD = 10000  # $10k minimum swap
    DEFAULT_MIN_PROFIT_USD = 100  # $100 minimum profit

    def __init__(
        self,
        verbose: bool = False,
        min_swap_value_usd: Optional[float] = None,
        min_profit_usd: Optional[float] = None,
        config_path: Optional[str] = None,
    ):
        """Initialize MEV detector.

        Args:
            verbose: Enable verbose output
            min_swap_value_usd: Minimum swap value for detection (overrides config)
            min_profit_usd: Minimum profit for detection (overrides config)
            config_path: Path to settings.yaml config file
        """
        self.verbose = verbose
        self.decoder = TransactionDecoder(verbose=verbose)

        # Load config if available
        config = self._load_config(config_path)

        # Set thresholds with priority: explicit arg > config > default
        config_mev = config.get("mev", {}) if config else {}
        self.min_swap_value_usd = (
            min_swap_value_usd
            if min_swap_value_usd is not None
            else config_mev.get("min_swap_value_usd", self.DEFAULT_MIN_SWAP_VALUE_USD)
        )
        self.min_profit_usd = (
            min_profit_usd
            if min_profit_usd is not None
            else config_mev.get("min_profit_usd", self.DEFAULT_MIN_PROFIT_USD)
        )

    def _load_config(self, config_path: Optional[str] = None) -> Optional[Dict]:
        """Load configuration from YAML file.

        Args:
            config_path: Explicit path to config, or None to use defaults

        Returns:
            Config dict or None if not found/loaded
        """
        if not HAS_YAML:
            return None

        # Search paths for config
        search_paths = []
        if config_path:
            search_paths.append(config_path)

        # Default locations
        script_dir = os.path.dirname(os.path.abspath(__file__))
        search_paths.extend(
            [
                os.path.join(script_dir, "..", "config", "settings.yaml"),
                os.path.expanduser("~/.mempool_analyzer.yaml"),
            ]
        )

        for path in search_paths:
            if os.path.exists(path):
                try:
                    with open(path) as f:
                        return yaml.safe_load(f)
                except Exception as e:
                    if self.verbose:
                        print(f"Warning: Could not load config from {path}: {e}")

        return None

    def detect_pending_swaps(self, pending_txs: List[Any], eth_price: float = 3000.0) -> List[PendingSwap]:
        """Identify pending swap transactions.

        Args:
            pending_txs: List of pending transactions
            eth_price: Current ETH price for USD estimation

        Returns:
            List of detected pending swaps
        """
        swaps = []

        for tx in pending_txs:
            # Get transaction fields
            if hasattr(tx, "input_data"):
                input_data = tx.input_data
                to_address = tx.to_address
                tx_hash = tx.hash
                gas_price = tx.gas_price
                from_address = tx.from_address
            else:
                input_data = tx.get("input", "")
                to_address = tx.get("to", "")
                tx_hash = tx.get("hash", "")
                gas_price = tx.get("gasPrice", 0)
                from_address = tx.get("from", "")
                if isinstance(gas_price, str):
                    gas_price = int(gas_price, 16)

            # Try to identify as swap
            swap_info = self.decoder.identify_dex_swap(input_data, to_address)
            if swap_info:
                swaps.append(
                    PendingSwap(
                        tx_hash=tx_hash,
                        dex=swap_info.dex,
                        amount_in=swap_info.amount_in,
                        amount_out_min=swap_info.amount_out_min,
                        gas_price=gas_price,
                        from_address=from_address,
                    )
                )

        return swaps

    def detect_sandwich_opportunities(
        self, pending_swaps: List[PendingSwap], eth_price: float = 3000.0
    ) -> List[MEVOpportunity]:
        """Detect potential sandwich attack opportunities.

        Sandwich: Front-run a large swap, then back-run after price moves.

        Args:
            pending_swaps: List of detected pending swaps
            eth_price: Current ETH price

        Returns:
            List of potential sandwich opportunities
        """
        opportunities = []

        for swap in pending_swaps:
            # Skip small swaps
            if not swap.amount_in:
                continue

            # Estimate swap value (simplified - assumes ETH value)
            value_eth = swap.amount_in / 10**18
            value_usd = value_eth * eth_price

            if value_usd < self.min_swap_value_usd:
                continue

            # Estimate potential profit (very simplified)
            # Real sandwich profit depends on pool liquidity, slippage, etc.
            estimated_slippage = min(value_usd / 1000000, 0.05)  # Up to 5% for large swaps
            estimated_profit = value_usd * estimated_slippage * 0.3  # Capture 30% of slippage

            if estimated_profit < self.min_profit_usd:
                continue

            opportunities.append(
                MEVOpportunity(
                    opportunity_type="sandwich",
                    target_tx=swap.tx_hash,
                    estimated_profit_usd=estimated_profit,
                    required_capital_usd=value_usd * 0.5,  # Need capital to front-run
                    risk_level="high",  # Sandwiches are risky
                    confidence=0.3,  # Low confidence without pool analysis
                    details={
                        "dex": swap.dex,
                        "swap_value_usd": value_usd,
                        "target_slippage": estimated_slippage,
                        "gas_price_gwei": swap.gas_price / 10**9,
                    },
                )
            )

        return opportunities

    def detect_arbitrage_opportunities(
        self, pending_swaps: List[PendingSwap], pool_prices: Dict[str, float] = None
    ) -> List[MEVOpportunity]:
        """Detect arbitrage opportunities from pending swaps.

        Args:
            pending_swaps: List of detected pending swaps
            pool_prices: Optional pool price data for comparison

        Returns:
            List of potential arbitrage opportunities
        """
        # Simplified detection - would need real pool data
        opportunities = []

        # Group swaps by apparent token pair
        # In real implementation, would decode full path and check pool prices

        for swap in pending_swaps:
            if not swap.amount_in or swap.amount_in < 10**18:
                continue

            # Mock arbitrage detection (placeholder)
            # Real implementation would:
            # 1. Decode swap path
            # 2. Check prices on other DEXes
            # 3. Calculate if price difference creates opportunity

            if self.verbose:
                print(f"Checking arb opportunity for {swap.tx_hash[:16]}...")

        return opportunities

    def detect_liquidation_opportunities(self, pending_txs: List[Any]) -> List[MEVOpportunity]:
        """Detect pending liquidation opportunities.

        Args:
            pending_txs: List of pending transactions

        Returns:
            List of potential liquidation opportunities
        """
        opportunities = []

        # Look for lending protocol interactions that might indicate
        # underwater positions or pending liquidations

        # This would require:
        # 1. Monitoring Aave/Compound/etc health factors
        # 2. Detecting position updates that lower health
        # 3. Calculating profitability of liquidation

        # Placeholder - real implementation is complex

        return opportunities

    def detect_all_opportunities(
        self, pending_txs: List[Any], eth_price: float = 3000.0
    ) -> Dict[str, List[MEVOpportunity]]:
        """Run all MEV detection algorithms.

        Args:
            pending_txs: List of pending transactions
            eth_price: Current ETH price

        Returns:
            Dict mapping opportunity type to list of opportunities
        """
        # First, identify swaps
        swaps = self.detect_pending_swaps(pending_txs, eth_price)

        results = {
            "pending_swaps": len(swaps),
            "sandwich": self.detect_sandwich_opportunities(swaps, eth_price),
            "arbitrage": self.detect_arbitrage_opportunities(swaps),
            "liquidation": self.detect_liquidation_opportunities(pending_txs),
        }

        return results

    def format_opportunities(self, opportunities: List[MEVOpportunity]) -> str:
        """Format opportunities for display.

        Args:
            opportunities: List of MEV opportunities

        Returns:
            Formatted string
        """
        if not opportunities:
            return "No MEV opportunities detected."

        lines = [
            "",
            "MEV OPPORTUNITIES DETECTED",
            "=" * 80,
            f"{'Type':<12} {'Est. Profit':<14} {'Capital Req':<14} {'Risk':<10} {'Confidence':<12}",
            "-" * 80,
        ]

        for opp in sorted(opportunities, key=lambda x: x.estimated_profit_usd, reverse=True):
            lines.append(
                f"{opp.opportunity_type:<12} "
                f"${opp.estimated_profit_usd:>11,.0f} "
                f"${opp.required_capital_usd:>11,.0f} "
                f"{opp.risk_level:<10} "
                f"{opp.confidence * 100:>10.0f}%"
            )

        lines.append("-" * 80)
        lines.append(f"Total: {len(opportunities)} potential opportunities")
        lines.append("")
        lines.append("⚠️  WARNING: MEV detection is for educational purposes only.")
        lines.append("    Actual profitability requires real-time pool data and")
        lines.append("    sophisticated execution infrastructure.")

        return "\n".join(lines)


def main():
    """CLI entry point for testing."""
    detector = MEVDetector(verbose=True)

    # Create mock pending transactions
    class MockTx:
        def __init__(self, value, gas_price):
            import random

            self.hash = f"0x{''.join(random.choices('0123456789abcdef', k=64))}"
            self.from_address = f"0x{''.join(random.choices('0123456789abcdef', k=40))}"
            self.to_address = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
            self.value = value
            self.gas_price = gas_price
            self.input_data = "0x38ed1739" + "0" * 256

    import random

    mock_txs = [MockTx(random.randint(1, 100) * 10**18, (30 + random.randint(0, 20)) * 10**9) for _ in range(20)]

    # Detect
    print("=== Scanning for Pending Swaps ===")
    swaps = detector.detect_pending_swaps(mock_txs)
    print(f"Found {len(swaps)} pending swaps")

    print("\n=== Checking for MEV Opportunities ===")
    opportunities = detector.detect_sandwich_opportunities(swaps)
    print(detector.format_opportunities(opportunities))


if __name__ == "__main__":
    main()
