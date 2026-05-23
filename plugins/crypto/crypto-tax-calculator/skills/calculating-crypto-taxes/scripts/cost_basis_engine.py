#!/usr/bin/env python3
"""
Cost Basis Engine

Tracks lots and calculates cost basis using various methods
(FIFO, LIFO, HIFO, Specific Identification).

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 2.0.0
License: MIT
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Dict, List
import copy


@dataclass
class Lot:
    """Represents a tax lot (acquisition of an asset)."""

    asset: str
    quantity: Decimal
    cost_per_unit: Decimal
    acquired_date: datetime
    remaining: Decimal = field(default=None)
    fees: Decimal = field(default_factory=lambda: Decimal("0"))
    lot_id: int = 0

    def __post_init__(self):
        if self.remaining is None:
            self.remaining = self.quantity

    @property
    def total_cost(self) -> Decimal:
        """Total cost including fees."""
        return (self.quantity * self.cost_per_unit) + self.fees

    @property
    def cost_basis_per_unit(self) -> Decimal:
        """Cost basis per unit including allocated fees."""
        if self.quantity == 0:
            return Decimal("0")
        return self.total_cost / self.quantity


@dataclass
class DisposalResult:
    """Result of disposing (selling) an asset."""

    asset: str
    quantity: Decimal
    proceeds: Decimal
    cost_basis: Decimal
    gain_loss: Decimal
    acquired_date: datetime
    disposed_date: datetime
    is_long_term: bool
    lot_id: int

    @property
    def holding_days(self) -> int:
        """Days between acquisition and disposal."""
        return (self.disposed_date - self.acquired_date).days


class CostBasisEngine:
    """Tracks lots and calculates cost basis."""

    # Long-term holding period in days (>= 365 days)
    LONG_TERM_DAYS = 365

    def __init__(self, method: str = "fifo", verbose: bool = False):
        """Initialize engine.

        Args:
            method: Cost basis method (fifo, lifo, hifo)
            verbose: Enable verbose output
        """
        self.method = method.lower()
        self.verbose = verbose
        self._lots: Dict[str, List[Lot]] = {}  # asset -> list of lots
        self._lot_counter = 0
        self._disposals: List[DisposalResult] = []

    def add_lot(
        self,
        asset: str,
        quantity: Decimal,
        cost_per_unit: Decimal,
        acquired_date: datetime,
        fees: Decimal = Decimal("0"),
    ) -> Lot:
        """Record acquisition of an asset.

        Args:
            asset: Asset symbol (e.g., "BTC")
            quantity: Amount acquired
            cost_per_unit: Price per unit at acquisition
            acquired_date: Date of acquisition
            fees: Transaction fees (added to cost basis)

        Returns:
            Created Lot object
        """
        self._lot_counter += 1
        lot = Lot(
            asset=asset.upper(),
            quantity=quantity,
            cost_per_unit=cost_per_unit,
            acquired_date=acquired_date,
            fees=fees,
            lot_id=self._lot_counter,
        )

        if asset.upper() not in self._lots:
            self._lots[asset.upper()] = []

        self._lots[asset.upper()].append(lot)

        if self.verbose:
            print(f"  Added lot #{lot.lot_id}: {quantity} {asset} @ ${cost_per_unit:.2f}")

        return lot

    def dispose(
        self,
        asset: str,
        quantity: Decimal,
        proceeds_per_unit: Decimal,
        disposed_date: datetime,
        fees: Decimal = Decimal("0"),
    ) -> List[DisposalResult]:
        """Dispose (sell) an asset and calculate gains/losses.

        Args:
            asset: Asset symbol
            quantity: Amount to dispose
            proceeds_per_unit: Sale price per unit
            disposed_date: Date of sale
            fees: Transaction fees (reduce proceeds)

        Returns:
            List of DisposalResult for each matched lot
        """
        asset = asset.upper()
        available = self.get_available(asset)

        if quantity > available:
            raise ValueError(f"Cannot dispose {quantity} {asset} - only {available} available")

        results = []
        remaining = quantity

        # Get lots in order based on method
        lots = self._get_lots_in_order(asset)

        for lot in lots:
            if remaining <= 0:
                break

            if lot.remaining <= 0:
                continue

            # Calculate amount to take from this lot
            take = min(remaining, lot.remaining)

            # Calculate cost basis for this portion
            cost_basis = take * lot.cost_basis_per_unit

            # Calculate proceeds (with proportional fees)
            fee_portion = (take / quantity) * fees if quantity > 0 else Decimal("0")
            proceeds = (take * proceeds_per_unit) - fee_portion

            # Calculate gain/loss
            gain_loss = proceeds - cost_basis

            # Determine holding period
            holding_days = (disposed_date - lot.acquired_date).days
            is_long_term = holding_days >= self.LONG_TERM_DAYS

            result = DisposalResult(
                asset=asset,
                quantity=take,
                proceeds=proceeds,
                cost_basis=cost_basis,
                gain_loss=gain_loss,
                acquired_date=lot.acquired_date,
                disposed_date=disposed_date,
                is_long_term=is_long_term,
                lot_id=lot.lot_id,
            )

            results.append(result)
            self._disposals.append(result)

            # Update lot
            lot.remaining -= take
            remaining -= take

            if self.verbose:
                term = "long-term" if is_long_term else "short-term"
                gain_str = f"+${gain_loss:.2f}" if gain_loss >= 0 else f"-${abs(gain_loss):.2f}"
                print(f"  Disposed {take} {asset} from lot #{lot.lot_id} ({term}): {gain_str}")

        return results

    def _get_lots_in_order(self, asset: str) -> List[Lot]:
        """Get lots ordered by cost basis method.

        Args:
            asset: Asset symbol

        Returns:
            List of lots in disposal order
        """
        lots = self._lots.get(asset.upper(), [])

        # Filter to lots with remaining quantity
        lots = [lot for lot in lots if lot.remaining > 0]

        if self.method == "fifo":
            # First In First Out - oldest first
            return sorted(lots, key=lambda x: x.acquired_date)

        elif self.method == "lifo":
            # Last In First Out - newest first
            return sorted(lots, key=lambda x: x.acquired_date, reverse=True)

        elif self.method == "hifo":
            # Highest In First Out - highest cost basis first
            return sorted(lots, key=lambda x: x.cost_basis_per_unit, reverse=True)

        else:
            # Default to FIFO
            return sorted(lots, key=lambda x: x.acquired_date)

    def get_available(self, asset: str) -> Decimal:
        """Get available quantity of an asset.

        Args:
            asset: Asset symbol

        Returns:
            Available quantity
        """
        lots = self._lots.get(asset.upper(), [])
        return sum(lot.remaining for lot in lots)

    def get_inventory(self) -> Dict[str, List[Dict]]:
        """Get current inventory by asset.

        Returns:
            Dictionary of asset -> list of lot details
        """
        inventory = {}

        for asset, lots in self._lots.items():
            inventory[asset] = []
            for lot in lots:
                if lot.remaining > 0:
                    inventory[asset].append(
                        {
                            "lot_id": lot.lot_id,
                            "quantity": float(lot.quantity),
                            "remaining": float(lot.remaining),
                            "cost_per_unit": float(lot.cost_per_unit),
                            "cost_basis_per_unit": float(lot.cost_basis_per_unit),
                            "acquired_date": lot.acquired_date.strftime("%Y-%m-%d"),
                            "total_cost": float(lot.total_cost),
                        }
                    )

        return inventory

    def get_disposals(self) -> List[DisposalResult]:
        """Get all disposal results."""
        return self._disposals.copy()

    def get_summary(self) -> Dict:
        """Get summary of all disposals."""
        if not self._disposals:
            return {
                "total_proceeds": Decimal("0"),
                "total_cost_basis": Decimal("0"),
                "total_gain_loss": Decimal("0"),
                "short_term_gain": Decimal("0"),
                "short_term_loss": Decimal("0"),
                "long_term_gain": Decimal("0"),
                "long_term_loss": Decimal("0"),
                "disposal_count": 0,
            }

        total_proceeds = sum(d.proceeds for d in self._disposals)
        total_cost_basis = sum(d.cost_basis for d in self._disposals)
        total_gain_loss = sum(d.gain_loss for d in self._disposals)

        short_term = [d for d in self._disposals if not d.is_long_term]
        long_term = [d for d in self._disposals if d.is_long_term]

        short_term_gain = sum(d.gain_loss for d in short_term if d.gain_loss > 0)
        short_term_loss = sum(d.gain_loss for d in short_term if d.gain_loss < 0)
        long_term_gain = sum(d.gain_loss for d in long_term if d.gain_loss > 0)
        long_term_loss = sum(d.gain_loss for d in long_term if d.gain_loss < 0)

        return {
            "total_proceeds": total_proceeds,
            "total_cost_basis": total_cost_basis,
            "total_gain_loss": total_gain_loss,
            "short_term_gain": short_term_gain,
            "short_term_loss": short_term_loss,
            "long_term_gain": long_term_gain,
            "long_term_loss": long_term_loss,
            "disposal_count": len(self._disposals),
        }

    def clone(self) -> "CostBasisEngine":
        """Create a deep copy of the engine (for comparison)."""
        new_engine = CostBasisEngine(method=self.method, verbose=self.verbose)
        new_engine._lots = copy.deepcopy(self._lots)
        new_engine._lot_counter = self._lot_counter
        new_engine._disposals = copy.deepcopy(self._disposals)
        return new_engine


def main():
    """CLI entry point for testing."""
    # Test scenarios
    engine = CostBasisEngine(method="fifo", verbose=True)

    print("=== FIFO Cost Basis Test ===\n")

    # Add lots
    print("Adding lots:")
    engine.add_lot("BTC", Decimal("1.0"), Decimal("40000"), datetime(2024, 1, 15))
    engine.add_lot("BTC", Decimal("0.5"), Decimal("65000"), datetime(2024, 6, 15))
    engine.add_lot("BTC", Decimal("0.25"), Decimal("95000"), datetime(2025, 1, 1))

    print(f"\nAvailable BTC: {engine.get_available('BTC')}")

    # Dispose
    print("\nDisposing 0.75 BTC @ $100,000:")
    results = engine.dispose("BTC", Decimal("0.75"), Decimal("100000"), datetime(2025, 1, 20))

    print("\nDisposal Results:")
    for r in results:
        term = "Long-term" if r.is_long_term else "Short-term"
        print(
            f"  {r.quantity} BTC: Proceeds ${r.proceeds:.2f}, "
            f"Cost ${r.cost_basis:.2f}, Gain/Loss ${r.gain_loss:.2f} ({term})"
        )

    print("\nSummary:")
    summary = engine.get_summary()
    for key, value in summary.items():
        if isinstance(value, Decimal):
            print(f"  {key}: ${value:.2f}")
        else:
            print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
