#!/usr/bin/env python3
"""
Tax Engine

Processes transactions and calculates tax events using cost basis engine.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 2.0.0
License: MIT
"""

from decimal import Decimal
from datetime import datetime
from typing import Dict, Any, List
from cost_basis_engine import CostBasisEngine


# Transaction types that are taxable disposals
DISPOSAL_TYPES = {"sell", "trade", "spend", "convert"}

# Transaction types that are income (taxed at receipt)
INCOME_TYPES = {"staking", "airdrop", "mining", "interest", "income"}

# Transaction types that create new lots
ACQUISITION_TYPES = {"buy", "receive", "staking", "airdrop", "mining", "interest", "income"}

# Non-taxable transaction types
NON_TAXABLE_TYPES = {"transfer", "transfer_in", "transfer_out"}


class TaxEngine:
    """Processes transactions and calculates tax events."""

    def __init__(self, verbose: bool = False):
        """Initialize engine.

        Args:
            verbose: Enable verbose output
        """
        self.verbose = verbose

    def calculate(self, transactions: List[Dict[str, Any]], cost_engine: CostBasisEngine) -> Dict[str, Any]:
        """Calculate tax events from transactions.

        Args:
            transactions: List of normalized transactions
            cost_engine: Cost basis engine for lot tracking

        Returns:
            Tax calculation results
        """
        # Process transactions in chronological order
        transactions = sorted(transactions, key=lambda x: x["date"])

        disposals = []
        income_events = []
        skipped = []

        for tx in transactions:
            tx_type = tx.get("type", "other")
            asset = tx.get("asset", "").upper()
            quantity = Decimal(str(tx.get("quantity", 0)))
            date = tx.get("date")
            price = tx.get("price")
            fee = Decimal(str(tx.get("fee", 0)))

            # Skip USD and stablecoin movements (no tax event)
            if asset in {"USD", "USDC", "USDT", "DAI", "BUSD"}:
                continue

            # Skip transfers (non-taxable)
            if tx_type in NON_TAXABLE_TYPES:
                continue

            # Handle acquisitions (create lots)
            if tx_type in ACQUISITION_TYPES:
                # Need price to create lot
                if price is None or price == 0:
                    if self.verbose:
                        print(f"  Warning: Missing price for {tx_type} on {date}, skipping lot creation")
                    skipped.append(tx)
                    continue

                cost_per_unit = Decimal(str(price))
                cost_engine.add_lot(asset, quantity, cost_per_unit, date, fee)

                # If income type, also record as income event
                if tx_type in INCOME_TYPES:
                    fmv = quantity * cost_per_unit
                    income_events.append(
                        {
                            "date": date,
                            "type": tx_type,
                            "asset": asset,
                            "quantity": float(quantity),
                            "fair_market_value": float(fmv),
                            "price_per_unit": float(cost_per_unit),
                        }
                    )

            # Handle disposals (sell lots)
            elif tx_type in DISPOSAL_TYPES:
                if price is None or price == 0:
                    if self.verbose:
                        print(f"  Warning: Missing price for {tx_type} on {date}, skipping disposal")
                    skipped.append(tx)
                    continue

                proceeds_per_unit = Decimal(str(price))

                # Check if we have enough to dispose
                available = cost_engine.get_available(asset)
                if quantity > available:
                    if self.verbose:
                        print(f"  Warning: Disposing {quantity} {asset} but only {available} available")
                    # Dispose what we have
                    quantity = available

                if quantity > 0:
                    results = cost_engine.dispose(asset, quantity, proceeds_per_unit, date, fee)
                    for result in results:
                        disposals.append(
                            {
                                "date_acquired": result.acquired_date,
                                "date_sold": result.disposed_date,
                                "asset": result.asset,
                                "quantity": float(result.quantity),
                                "proceeds": float(result.proceeds),
                                "cost_basis": float(result.cost_basis),
                                "gain_loss": float(result.gain_loss),
                                "is_long_term": result.is_long_term,
                                "holding_days": result.holding_days,
                                "lot_id": result.lot_id,
                            }
                        )

            else:
                # Unknown type
                if self.verbose:
                    print(f"  Skipping unknown transaction type: {tx_type}")
                skipped.append(tx)

        # Calculate summaries
        summary = cost_engine.get_summary()

        return {
            "disposals": disposals,
            "income_events": income_events,
            "summary": {
                "total_proceeds": float(summary["total_proceeds"]),
                "total_cost_basis": float(summary["total_cost_basis"]),
                "net_gain_loss": float(summary["total_gain_loss"]),
                "short_term_gain": float(summary["short_term_gain"]),
                "short_term_loss": float(summary["short_term_loss"]),
                "long_term_gain": float(summary["long_term_gain"]),
                "long_term_loss": float(summary["long_term_loss"]),
                "disposal_count": summary["disposal_count"],
                "income_count": len(income_events),
            },
            "method": cost_engine.method,
            "skipped_count": len(skipped),
        }

    def calculate_income(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate income events only.

        Args:
            transactions: List of normalized transactions

        Returns:
            Income calculation results
        """
        transactions = sorted(transactions, key=lambda x: x["date"])

        income_events = []
        total_income = Decimal("0")

        for tx in transactions:
            tx_type = tx.get("type", "other")

            if tx_type not in INCOME_TYPES:
                continue

            asset = tx.get("asset", "").upper()
            quantity = Decimal(str(tx.get("quantity", 0)))
            date = tx.get("date")
            price = tx.get("price")

            if price is None or price == 0:
                if self.verbose:
                    print(f"  Warning: Missing price for income event on {date}")
                continue

            fmv = quantity * Decimal(str(price))
            total_income += fmv

            income_events.append(
                {
                    "date": date,
                    "type": tx_type,
                    "asset": asset,
                    "quantity": float(quantity),
                    "price_per_unit": float(price),
                    "fair_market_value": float(fmv),
                }
            )

        # Group by type
        by_type = {}
        for event in income_events:
            event_type = event["type"]
            if event_type not in by_type:
                by_type[event_type] = {
                    "count": 0,
                    "total_value": 0.0,
                }
            by_type[event_type]["count"] += 1
            by_type[event_type]["total_value"] += event["fair_market_value"]

        return {
            "income_events": income_events,
            "total_income": float(total_income),
            "by_type": by_type,
            "event_count": len(income_events),
        }


def main():
    """CLI entry point for testing."""

    # Sample transactions
    transactions = [
        {"date": datetime(2024, 1, 15), "type": "buy", "asset": "BTC", "quantity": 1.0, "price": 40000, "fee": 10},
        {"date": datetime(2024, 3, 1), "type": "staking", "asset": "ETH", "quantity": 0.1, "price": 3000, "fee": 0},
        {"date": datetime(2024, 6, 15), "type": "buy", "asset": "BTC", "quantity": 0.5, "price": 65000, "fee": 5},
        {"date": datetime(2025, 1, 20), "type": "sell", "asset": "BTC", "quantity": 0.75, "price": 95000, "fee": 20},
    ]

    print("=== Tax Engine Test ===\n")

    cost_engine = CostBasisEngine(method="fifo", verbose=True)
    tax_engine = TaxEngine(verbose=True)

    result = tax_engine.calculate(transactions, cost_engine)

    print("\n=== Results ===")
    print(f"\nDisposals ({len(result['disposals'])}):")
    for d in result["disposals"]:
        term = "Long-term" if d["is_long_term"] else "Short-term"
        print(f"  {d['quantity']} {d['asset']}: ${d['gain_loss']:.2f} ({term})")

    print(f"\nIncome Events ({len(result['income_events'])}):")
    for i in result["income_events"]:
        print(f"  {i['type']}: {i['quantity']} {i['asset']} = ${i['fair_market_value']:.2f}")

    print("\n=== Summary ===")
    s = result["summary"]
    print(f"Total Proceeds:    ${s['total_proceeds']:.2f}")
    print(f"Total Cost Basis:  ${s['total_cost_basis']:.2f}")
    print(f"Net Gain/Loss:     ${s['net_gain_loss']:.2f}")
    print(f"Short-term Gain:   ${s['short_term_gain']:.2f}")
    print(f"Short-term Loss:   ${s['short_term_loss']:.2f}")
    print(f"Long-term Gain:    ${s['long_term_gain']:.2f}")
    print(f"Long-term Loss:    ${s['long_term_loss']:.2f}")


if __name__ == "__main__":
    main()
