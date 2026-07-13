#!/usr/bin/env python3
"""
Triangular arbitrage path finder.

Uses graph algorithms to find profitable circular arbitrage paths:
A → B → C → A
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List, Optional, Tuple


@dataclass
class TradingPair:
    """Trading pair with price data."""

    base: str
    quote: str
    bid: Decimal  # You sell base at this price
    ask: Decimal  # You buy base at this price
    fee_rate: Decimal  # Trading fee
    exchange: str


@dataclass
class ArbitragePath:
    """A potential triangular arbitrage path."""

    tokens: List[str]  # e.g., ["ETH", "BTC", "USDT", "ETH"]
    pairs: List[TradingPair]
    gross_profit_pct: float
    net_profit_pct: float
    total_fees_pct: float
    exchange: str
    execution_steps: List[str]

    @property
    def is_profitable(self) -> bool:
        """Check if path is profitable after fees."""
        return self.net_profit_pct > 0


class TriangularFinder:
    """
    Finds triangular arbitrage opportunities using graph algorithms.

    The algorithm:
    1. Build a graph where tokens are nodes and pairs are edges
    2. Find all cycles of length 3 (triangles)
    3. Calculate profit for each triangle considering:
       - Price slippage on each edge
       - Trading fees on each trade
    4. Filter to profitable paths
    """

    # Mock trading pairs for a single exchange
    MOCK_PAIRS = {
        "binance": [
            # ETH pairs
            TradingPair("ETH", "USDT", Decimal("2541.20"), Decimal("2541.50"), Decimal("0.001"), "binance"),
            TradingPair("ETH", "BTC", Decimal("0.03745"), Decimal("0.03748"), Decimal("0.001"), "binance"),
            TradingPair("ETH", "USDC", Decimal("2540.80"), Decimal("2541.20"), Decimal("0.001"), "binance"),
            # BTC pairs
            TradingPair("BTC", "USDT", Decimal("67850.00"), Decimal("67865.00"), Decimal("0.001"), "binance"),
            TradingPair("BTC", "USDC", Decimal("67840.00"), Decimal("67860.00"), Decimal("0.001"), "binance"),
            # Stablecoin pairs
            TradingPair("USDC", "USDT", Decimal("0.9998"), Decimal("1.0002"), Decimal("0.001"), "binance"),
            # More pairs for triangular opportunities
            TradingPair("BNB", "USDT", Decimal("580.50"), Decimal("580.80"), Decimal("0.001"), "binance"),
            TradingPair("BNB", "ETH", Decimal("0.2285"), Decimal("0.2288"), Decimal("0.001"), "binance"),
            TradingPair("BNB", "BTC", Decimal("0.00855"), Decimal("0.00857"), Decimal("0.001"), "binance"),
        ],
        "coinbase": [
            TradingPair("ETH", "USD", Decimal("2543.80"), Decimal("2544.10"), Decimal("0.006"), "coinbase"),
            TradingPair("ETH", "BTC", Decimal("0.03752"), Decimal("0.03756"), Decimal("0.006"), "coinbase"),
            TradingPair("BTC", "USD", Decimal("67920.00"), Decimal("67950.00"), Decimal("0.006"), "coinbase"),
        ],
    }

    def __init__(
        self,
        fee_rate: Decimal = Decimal("0.001"),  # 0.1% default
        min_profit_pct: float = 0.1,  # Minimum 0.1% profit
    ):
        """
        Initialize triangular finder.

        Args:
            fee_rate: Default trading fee rate
            min_profit_pct: Minimum net profit percentage to report
        """
        self.fee_rate = fee_rate
        self.min_profit_pct = min_profit_pct

    def find_opportunities(
        self,
        exchange: str,
        pairs: Optional[List[TradingPair]] = None,
    ) -> List[ArbitragePath]:
        """
        Find all triangular arbitrage opportunities on an exchange.

        Args:
            exchange: Exchange name
            pairs: Trading pairs (uses mock if not provided)

        Returns:
            List of profitable ArbitragePath objects
        """
        if pairs is None:
            pairs = self.MOCK_PAIRS.get(exchange.lower(), [])

        if not pairs:
            return []

        # Build adjacency graph
        graph = self._build_graph(pairs)

        # Find all triangles
        triangles = self._find_triangles(graph)

        # Evaluate each triangle
        opportunities = []
        for triangle in triangles:
            path = self._evaluate_triangle(triangle, pairs, exchange)
            if path and path.net_profit_pct >= self.min_profit_pct:
                opportunities.append(path)

        # Sort by profit
        opportunities.sort(key=lambda x: x.net_profit_pct, reverse=True)

        return opportunities

    def _build_graph(
        self,
        pairs: List[TradingPair],
    ) -> Dict[str, List[str]]:
        """Build adjacency list from trading pairs."""
        graph: Dict[str, List[str]] = {}

        for pair in pairs:
            # Add both directions since we can trade either way
            if pair.base not in graph:
                graph[pair.base] = []
            if pair.quote not in graph:
                graph[pair.quote] = []

            if pair.quote not in graph[pair.base]:
                graph[pair.base].append(pair.quote)
            if pair.base not in graph[pair.quote]:
                graph[pair.quote].append(pair.base)

        return graph

    def _find_triangles(
        self,
        graph: Dict[str, List[str]],
    ) -> List[Tuple[str, str, str]]:
        """Find all unique triangles in the graph."""
        triangles = set()
        tokens = list(graph.keys())

        for a in tokens:
            for b in graph.get(a, []):
                for c in graph.get(b, []):
                    if c != a and a in graph.get(c, []):
                        # Found a triangle a → b → c → a
                        # Normalize to avoid duplicates
                        triangle = tuple(sorted([a, b, c]))
                        triangles.add(triangle)

        return [t for t in triangles]

    def _evaluate_triangle(
        self,
        triangle: Tuple[str, str, str],
        pairs: List[TradingPair],
        exchange: str,
    ) -> Optional[ArbitragePath]:
        """
        Evaluate profit potential for a triangle.

        We need to check all 6 possible orderings (3! = 6) to find the best path.
        """
        tokens = list(triangle)
        best_path = None
        best_profit = -float("inf")

        # Try all permutations
        from itertools import permutations

        for perm in permutations(tokens):
            # Try starting with each token
            path_tokens = list(perm) + [perm[0]]  # Complete the cycle
            profit, fees, steps, used_pairs = self._calculate_path_profit(path_tokens, pairs)

            if profit is not None and profit > best_profit:
                best_profit = profit
                net_profit = profit - fees
                best_path = ArbitragePath(
                    tokens=path_tokens,
                    pairs=used_pairs,
                    gross_profit_pct=profit,
                    net_profit_pct=net_profit,
                    total_fees_pct=fees,
                    exchange=exchange,
                    execution_steps=steps,
                )

        return best_path

    def _calculate_path_profit(
        self,
        path_tokens: List[str],
        pairs: List[TradingPair],
    ) -> Tuple[Optional[float], float, List[str], List[TradingPair]]:
        """
        Calculate profit for a specific path.

        Returns:
            (gross_profit_pct, total_fees_pct, execution_steps, used_pairs)
        """
        # Build pair lookup
        pair_map: Dict[Tuple[str, str], TradingPair] = {}
        for pair in pairs:
            pair_map[(pair.base, pair.quote)] = pair
            pair_map[(pair.quote, pair.base)] = pair

        # Start with 1 unit of first token
        amount = Decimal("1.0")
        total_fee_pct = 0.0
        steps = []
        used_pairs = []

        for i in range(len(path_tokens) - 1):
            from_token = path_tokens[i]
            to_token = path_tokens[i + 1]

            # Find the pair
            pair = pair_map.get((from_token, to_token))
            if pair is None:
                pair = pair_map.get((to_token, from_token))
                if pair is None:
                    return None, 0.0, [], []

            used_pairs.append(pair)

            # Determine trade direction
            if pair.base == from_token:
                # Selling base for quote (use bid)
                price = pair.bid
                new_amount = amount * price
                step = f"Sell {from_token} for {to_token} at {price}"
            else:
                # Buying base with quote (use ask)
                price = pair.ask
                new_amount = amount / price
                step = f"Buy {to_token} with {from_token} at {price}"

            # Apply fee
            fee = float(pair.fee_rate) * 100
            total_fee_pct += fee
            new_amount = new_amount * (1 - pair.fee_rate)

            steps.append(step)
            amount = new_amount

        # Calculate profit (ending amount vs starting amount of 1)
        gross_profit_pct = float(amount - Decimal("1.0")) * 100

        return gross_profit_pct, total_fee_pct, steps, used_pairs

    def analyze_single_triangle(
        self,
        token_a: str,
        token_b: str,
        token_c: str,
        exchange: str,
    ) -> Optional[ArbitragePath]:
        """
        Analyze a specific triangle for arbitrage.

        Args:
            token_a, token_b, token_c: The three tokens
            exchange: Exchange name

        Returns:
            Best ArbitragePath if profitable, None otherwise
        """
        pairs = self.MOCK_PAIRS.get(exchange.lower(), [])
        triangle = (token_a.upper(), token_b.upper(), token_c.upper())
        return self._evaluate_triangle(triangle, pairs, exchange)


def demo():
    """Demonstrate triangular arbitrage finder."""
    finder = TriangularFinder(min_profit_pct=-1.0)  # Show all for demo

    print("=" * 70)
    print("TRIANGULAR ARBITRAGE FINDER")
    print("=" * 70)

    # Find opportunities on Binance
    opportunities = finder.find_opportunities("binance")

    print(f"\nFound {len(opportunities)} triangular paths on Binance\n")

    if opportunities:
        print(f"{'Path':<30} {'Gross':>10} {'Fees':>10} {'Net':>10}")
        print("-" * 70)

        for opp in opportunities[:10]:
            path_str = " → ".join(opp.tokens)
            profit_indicator = "+" if opp.is_profitable else "-"
            print(
                f"{path_str:<30} "
                f"{profit_indicator}{abs(opp.gross_profit_pct):>8.4f}% "
                f"-{opp.total_fees_pct:>8.4f}% "
                f"{profit_indicator}{abs(opp.net_profit_pct):>8.4f}%"
            )

        # Show best opportunity details
        best = opportunities[0]
        print(f"\nBest Path: {' → '.join(best.tokens)}")
        print(f"Exchange: {best.exchange}")
        print("\nExecution Steps:")
        for i, step in enumerate(best.execution_steps, 1):
            print(f"  {i}. {step}")
        print(f"\nGross Profit: {best.gross_profit_pct:+.4f}%")
        print(f"Total Fees: -{best.total_fees_pct:.4f}%")
        print(f"Net Profit: {best.net_profit_pct:+.4f}%")

        if best.is_profitable:
            print("\n✓ PROFITABLE - Consider execution")
        else:
            print("\n✗ NOT PROFITABLE after fees")
    else:
        print("No triangular paths found")


if __name__ == "__main__":
    demo()
