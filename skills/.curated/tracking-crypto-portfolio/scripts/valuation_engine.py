#!/usr/bin/env python3
"""
Valuation Engine

Calculates portfolio valuations, allocations, and P&L.
Generates risk flags for concentration warnings.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 2.0.0
License: MIT
"""

from typing import Optional, Dict, Any, List


class ValuationEngine:
    """Calculates portfolio valuations and analytics."""

    def __init__(self, verbose: bool = False):
        """Initialize engine.

        Args:
            verbose: Enable verbose output
        """
        self.verbose = verbose

    def calculate(
        self, portfolio: Dict[str, Any], prices: Dict[str, Dict[str, Any]], threshold: float = 25.0
    ) -> Dict[str, Any]:
        """Calculate portfolio valuations.

        Args:
            portfolio: Validated portfolio dict
            prices: Price data keyed by symbol
            threshold: Allocation warning threshold (percent)

        Returns:
            Valuation result with holdings and analytics
        """
        holdings = portfolio.get("holdings", [])
        categories = portfolio.get("categories", {})

        # Calculate individual holdings
        valued_holdings = []
        total_value = 0
        total_cost = 0
        has_cost_basis = False

        for holding in holdings:
            coin = holding.get("coin", "").upper()
            quantity = holding.get("quantity", 0)
            cost_basis = holding.get("cost_basis")

            # Get price data
            price_data = prices.get(coin, {})
            price = price_data.get("price", 0)

            # Calculate value
            value = quantity * price

            entry = {
                "coin": coin,
                "quantity": quantity,
                "price_usd": price,
                "value_usd": value,
                "change_24h_pct": price_data.get("change_24h"),
                "change_7d_pct": price_data.get("change_7d"),
                "change_30d_pct": price_data.get("change_30d"),
                "market_cap": price_data.get("market_cap"),
            }

            # Add cost basis and P&L if available
            if cost_basis is not None:
                has_cost_basis = True
                cost = quantity * cost_basis
                pnl = value - cost
                pnl_pct = ((price - cost_basis) / cost_basis * 100) if cost_basis > 0 else 0

                entry["cost_basis"] = cost_basis
                entry["total_cost"] = cost
                entry["unrealized_pnl"] = pnl
                entry["pnl_pct"] = pnl_pct

                total_cost += cost

            # Track category
            if coin in categories:
                entry["category"] = categories[coin]

            # Add wallets if tracked
            if holding.get("wallets"):
                entry["wallets"] = holding["wallets"]

            valued_holdings.append(entry)
            total_value += value

        # Calculate allocations
        for holding in valued_holdings:
            if total_value > 0:
                holding["allocation_pct"] = (holding["value_usd"] / total_value) * 100
            else:
                holding["allocation_pct"] = 0

        # Calculate totals
        total_change_24h = self._calculate_total_change(valued_holdings, "change_24h_pct", total_value)
        total_change_7d = self._calculate_total_change(valued_holdings, "change_7d_pct", total_value)

        # Generate risk flags
        risk_flags = self._generate_risk_flags(valued_holdings, threshold)

        # Calculate category allocation
        category_allocation = self._calculate_category_allocation(valued_holdings, total_value)

        # Build result
        result = {
            "portfolio_name": portfolio.get("name", "My Portfolio"),
            "total_value_usd": round(total_value, 2),
            "change_24h": {
                "amount": round(total_change_24h["amount"], 2) if total_change_24h else None,
                "percent": round(total_change_24h["percent"], 2) if total_change_24h else None,
            },
            "change_7d": {
                "amount": round(total_change_7d["amount"], 2) if total_change_7d else None,
                "percent": round(total_change_7d["percent"], 2) if total_change_7d else None,
            },
            "holdings": valued_holdings,
            "holdings_count": len(valued_holdings),
            "risk_flags": risk_flags,
            "allocation_by_category": category_allocation,
        }

        # Add total P&L if cost basis available
        if has_cost_basis and total_cost > 0:
            total_pnl = total_value - total_cost
            total_pnl_pct = (total_pnl / total_cost) * 100

            result["total_cost"] = round(total_cost, 2)
            result["total_unrealized_pnl"] = round(total_pnl, 2)
            result["total_pnl_pct"] = round(total_pnl_pct, 2)

        return result

    def _calculate_total_change(
        self, holdings: List[Dict[str, Any]], change_key: str, total_value: float
    ) -> Optional[Dict[str, float]]:
        """Calculate weighted total change."""
        if total_value <= 0:
            return None

        weighted_change = 0
        valid_weight = 0

        for holding in holdings:
            change = holding.get(change_key)
            value = holding.get("value_usd", 0)

            if change is not None and value > 0:
                weighted_change += (value / total_value) * change
                valid_weight += value / total_value

        if valid_weight < 0.5:  # Less than 50% of portfolio has change data
            return None

        # Calculate dollar amount
        # If current value is V and it changed by P%, then previous value was V/(1 + P/100)
        if weighted_change != -100:
            previous_value = total_value / (1 + weighted_change / 100)
            change_amount = total_value - previous_value
        else:
            change_amount = -total_value

        return {"amount": change_amount, "percent": weighted_change}

    def _generate_risk_flags(self, holdings: List[Dict[str, Any]], threshold: float) -> List[str]:
        """Generate risk flags for portfolio."""
        flags = []

        # Check concentration
        for holding in holdings:
            allocation = holding.get("allocation_pct", 0)
            coin = holding.get("coin", "")

            if allocation > threshold:
                flags.append(f"{coin} allocation ({allocation:.1f}%) exceeds {threshold:.0f}% threshold")

        # Check for single asset dominance
        if holdings and holdings[0].get("allocation_pct", 0) > 50:
            coin = holdings[0].get("coin", "")
            flags.append(f"{coin} represents majority of portfolio (>50%)")

        # Check for lack of diversification
        if len(holdings) < 3:
            flags.append("Portfolio has limited diversification (<3 assets)")

        return flags

    def _calculate_category_allocation(self, holdings: List[Dict[str, Any]], total_value: float) -> Dict[str, float]:
        """Calculate allocation by category."""
        if total_value <= 0:
            return {}

        categories = {}

        for holding in holdings:
            category = holding.get("category", "Other")
            value = holding.get("value_usd", 0)

            if category not in categories:
                categories[category] = 0
            categories[category] += value

        # Convert to percentages
        return {
            cat: round((val / total_value) * 100, 1) for cat, val in sorted(categories.items(), key=lambda x: -x[1])
        }


def main():
    """CLI entry point for testing."""
    import json

    # Test with sample data
    portfolio = {
        "name": "Test Portfolio",
        "holdings": [
            {"coin": "BTC", "quantity": 0.5, "cost_basis": 50000},
            {"coin": "ETH", "quantity": 10, "cost_basis": 2500},
            {"coin": "SOL", "quantity": 100, "cost_basis": 100},
        ],
        "categories": {"BTC": "Layer 1", "ETH": "Layer 1", "SOL": "Layer 1"},
    }

    prices = {
        "BTC": {"price": 95000, "change_24h": 2.5, "change_7d": 5.0},
        "ETH": {"price": 3200, "change_24h": 1.8, "change_7d": 3.5},
        "SOL": {"price": 180, "change_24h": 4.2, "change_7d": 8.0},
    }

    engine = ValuationEngine(verbose=True)
    result = engine.calculate(portfolio, prices, threshold=25.0)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
