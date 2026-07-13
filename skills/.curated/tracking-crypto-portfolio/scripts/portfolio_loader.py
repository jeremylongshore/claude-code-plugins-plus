#!/usr/bin/env python3
"""
Portfolio Loader

Loads and validates portfolio JSON files.
Supports multiple portfolio formats with graceful handling.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 2.0.0
License: MIT
"""

import json
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List


class PortfolioLoader:
    """Loads and validates portfolio files."""

    def __init__(self, verbose: bool = False):
        """Initialize loader.

        Args:
            verbose: Enable verbose output
        """
        self.verbose = verbose

    def load(self, path: str) -> Optional[Dict[str, Any]]:
        """Load portfolio from JSON file.

        Args:
            path: Path to portfolio JSON file

        Returns:
            Validated portfolio dict or None on error
        """
        file_path = Path(path).expanduser()

        # Check file exists
        if not file_path.exists():
            print(f"Error: Portfolio file not found: {file_path}", file=sys.stderr)
            return None

        # Load JSON
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in portfolio file: {e}", file=sys.stderr)
            return None
        except Exception as e:
            print(f"Error: Failed to read portfolio file: {e}", file=sys.stderr)
            return None

        # Validate and normalize
        return self._validate_portfolio(data)

    def _validate_portfolio(self, data: Any) -> Optional[Dict[str, Any]]:
        """Validate and normalize portfolio data."""
        # Handle list format (just holdings array)
        if isinstance(data, list):
            data = {"holdings": data}

        if not isinstance(data, dict):
            print("Error: Portfolio must be a JSON object or array", file=sys.stderr)
            return None

        # Check for holdings
        holdings = data.get("holdings", [])
        if not holdings:
            print("Error: Portfolio has no holdings", file=sys.stderr)
            return None

        # Validate each holding
        valid_holdings = []
        for i, holding in enumerate(holdings):
            validated = self._validate_holding(holding, i)
            if validated:
                valid_holdings.append(validated)

        if not valid_holdings:
            print("Error: No valid holdings found in portfolio", file=sys.stderr)
            return None

        # Aggregate duplicate coins
        aggregated = self._aggregate_holdings(valid_holdings)

        return {
            "name": data.get("name", "My Portfolio"),
            "holdings": aggregated,
            "categories": data.get("categories", {}),
            "currency": data.get("currency", "USD"),
        }

    def _validate_holding(self, holding: Any, index: int) -> Optional[Dict[str, Any]]:
        """Validate a single holding entry."""
        if not isinstance(holding, dict):
            if self.verbose:
                print(f"Warning: Holding {index} is not an object, skipping", file=sys.stderr)
            return None

        # Required: coin symbol
        coin = holding.get("coin") or holding.get("symbol") or holding.get("ticker")
        if not coin:
            if self.verbose:
                print(f"Warning: Holding {index} missing coin symbol, skipping", file=sys.stderr)
            return None

        coin = str(coin).upper().strip()

        # Required: quantity
        quantity = holding.get("quantity") or holding.get("amount") or holding.get("qty")
        if quantity is None:
            if self.verbose:
                print(f"Warning: Holding {index} ({coin}) missing quantity, skipping", file=sys.stderr)
            return None

        try:
            quantity = float(quantity)
        except (TypeError, ValueError):
            if self.verbose:
                print(f"Warning: Holding {index} ({coin}) has invalid quantity, skipping", file=sys.stderr)
            return None

        if quantity <= 0:
            if self.verbose:
                print(f"Warning: Holding {index} ({coin}) has non-positive quantity, skipping", file=sys.stderr)
            return None

        # Optional: cost basis
        cost_basis = holding.get("cost_basis") or holding.get("cost") or holding.get("avg_cost")
        if cost_basis is not None:
            try:
                cost_basis = float(cost_basis)
                if cost_basis < 0:
                    cost_basis = None
            except (TypeError, ValueError):
                cost_basis = None

        # Optional: acquired date
        acquired = holding.get("acquired") or holding.get("date") or holding.get("purchase_date")

        # Optional: wallet/location
        wallet = holding.get("wallet") or holding.get("location") or holding.get("exchange")

        # Optional: notes
        notes = holding.get("notes") or holding.get("memo")

        return {
            "coin": coin,
            "quantity": quantity,
            "cost_basis": cost_basis,
            "acquired": acquired,
            "wallet": wallet,
            "notes": notes,
        }

    def _aggregate_holdings(self, holdings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Aggregate holdings for the same coin."""
        aggregated = {}

        for holding in holdings:
            coin = holding["coin"]

            if coin not in aggregated:
                aggregated[coin] = {
                    "coin": coin,
                    "quantity": 0,
                    "total_cost": 0,
                    "has_cost_basis": False,
                    "wallets": [],
                    "notes": [],
                }

            aggregated[coin]["quantity"] += holding["quantity"]

            # Track cost basis if available
            if holding.get("cost_basis") is not None:
                cost = holding["quantity"] * holding["cost_basis"]
                aggregated[coin]["total_cost"] += cost
                aggregated[coin]["has_cost_basis"] = True

            # Track wallets
            if holding.get("wallet"):
                aggregated[coin]["wallets"].append(holding["wallet"])

            # Track notes
            if holding.get("notes"):
                aggregated[coin]["notes"].append(holding["notes"])

        # Convert to list with calculated average cost basis
        result = []
        for coin, data in aggregated.items():
            entry = {"coin": coin, "quantity": data["quantity"]}

            # Calculate average cost basis
            if data["has_cost_basis"] and data["quantity"] > 0:
                entry["cost_basis"] = data["total_cost"] / data["quantity"]

            # Include wallets if tracked
            if data["wallets"]:
                entry["wallets"] = list(set(data["wallets"]))

            # Include notes
            if data["notes"]:
                entry["notes"] = "; ".join(data["notes"])

            result.append(entry)

        return result


def main():
    """CLI entry point for testing."""
    import argparse

    parser = argparse.ArgumentParser(description="Load and validate portfolio file")
    parser.add_argument("portfolio", type=str, help="Path to portfolio JSON")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    loader = PortfolioLoader(verbose=args.verbose)
    portfolio = loader.load(args.portfolio)

    if portfolio:
        print(json.dumps(portfolio, indent=2))
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
