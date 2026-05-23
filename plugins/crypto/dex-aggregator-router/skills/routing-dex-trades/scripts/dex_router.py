#!/usr/bin/env python3
"""
DEX Aggregator Router - Main CLI

Route trades across multiple DEXs to find optimal prices with
minimal slippage and gas costs.

Usage:
    python dex_router.py ETH USDC 1.0
    python dex_router.py ETH USDC 10.0 --compare
    python dex_router.py ETH USDC 50.0 --split
    python dex_router.py ETH USDC 25.0 --mev-check
    python dex_router.py ETH USDC 100.0 --full --output json
"""

import argparse
import asyncio
import os
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

# Add scripts directory to path for imports
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from quote_fetcher import QuoteFetcher, SwapParams
from route_optimizer import RouteOptimizer
from split_calculator import SplitCalculator
from mev_assessor import MEVAssessor
from formatters import OutputFormatter


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="DEX Aggregator Router - Find optimal swap routes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s ETH USDC 1.0              # Quick quote
  %(prog)s ETH USDC 10.0 --compare   # Compare all DEXs
  %(prog)s ETH USDC 50.0 --routes    # Analyze routes
  %(prog)s ETH USDC 100.0 --split    # Split order analysis
  %(prog)s ETH USDC 25.0 --mev-check # MEV risk assessment
  %(prog)s ETH USDC 50.0 --full      # Complete analysis
        """,
    )

    # Positional arguments
    parser.add_argument(
        "from_token",
        help="Input token symbol (e.g., ETH, WBTC)",
    )
    parser.add_argument(
        "to_token",
        help="Output token symbol (e.g., USDC, DAI)",
    )
    parser.add_argument(
        "amount",
        type=str,
        help="Amount to swap",
    )

    # Analysis modes
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Compare quotes from all aggregators",
    )
    parser.add_argument(
        "--routes",
        action="store_true",
        help="Analyze direct vs multi-hop routes",
    )
    parser.add_argument(
        "--split",
        action="store_true",
        help="Calculate optimal split across DEXs",
    )
    parser.add_argument(
        "--mev-check",
        action="store_true",
        help="Assess MEV risk and protection options",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Run complete analysis (compare + split + MEV)",
    )

    # Configuration
    parser.add_argument(
        "--chain",
        default="ethereum",
        choices=["ethereum", "arbitrum", "polygon", "optimism"],
        help="Blockchain network (default: ethereum)",
    )
    parser.add_argument(
        "--slippage",
        type=float,
        default=0.5,
        help="Slippage tolerance in %% (default: 0.5)",
    )

    # Output format
    parser.add_argument(
        "--output",
        choices=["table", "json", "csv"],
        default="table",
        help="Output format (default: table)",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output",
    )

    # Price configuration
    parser.add_argument(
        "--eth-price",
        type=float,
        default=2500.0,
        help="ETH price in USD for calculations (default: 2500)",
    )
    parser.add_argument(
        "--gas-price",
        type=float,
        default=30.0,
        help="Gas price in gwei (default: 30)",
    )

    return parser.parse_args()


async def fetch_quotes(args) -> list:
    """Fetch quotes from all aggregators."""
    try:
        amount = Decimal(args.amount)
    except InvalidOperation:
        print(f"Error: Invalid amount '{args.amount}'")
        sys.exit(1)

    # Load API keys from environment
    api_keys = {}
    if os.environ.get("ONEINCH_API_KEY"):
        api_keys["oneinch"] = os.environ["ONEINCH_API_KEY"]
    if os.environ.get("ZEROX_API_KEY"):
        api_keys["zerox"] = os.environ["ZEROX_API_KEY"]

    fetcher = QuoteFetcher(
        api_keys=api_keys,
        eth_price_usd=args.eth_price,
        gas_price_gwei=args.gas_price,
    )

    params = SwapParams(
        from_token=args.from_token,
        to_token=args.to_token,
        amount=amount,
        chain=args.chain,
        slippage=args.slippage,
    )

    print(f"Fetching quotes for {amount} {args.from_token} → {args.to_token}...")
    quotes = await fetcher.fetch_all_quotes(params)

    if not quotes:
        print("\nNo quotes received. This may be due to:")
        print("  - API rate limits (try again in 60 seconds)")
        print("  - Invalid token pair")
        print("  - Network issues")
        print("\nTip: Set ONEINCH_API_KEY or ZEROX_API_KEY for better results.")

    return quotes


def run_quick_quote(quotes, formatter, output_format):
    """Display best quote only."""
    if not quotes:
        return

    best = max(quotes, key=lambda q: q.effective_rate)
    print(formatter.format_quote(best, output_format))


def run_comparison(quotes, formatter, output_format, trade_value_usd):
    """Compare all quotes."""
    if not quotes:
        return

    optimizer = RouteOptimizer(trade_size_usd=trade_value_usd)
    comparison = optimizer.compare_routes(quotes)

    if comparison:
        print(formatter.format_comparison(comparison, output_format))
        print(f"\n{optimizer.get_size_recommendation(trade_value_usd)}")


def run_split_analysis(quotes, formatter, output_format, amount, eth_price):
    """Analyze split order opportunities."""
    if not quotes:
        return

    calculator = SplitCalculator()
    result = calculator.calculate_split(
        quotes,
        total_amount=amount,
        price_usd=eth_price,
    )

    if result:
        print(formatter.format_split(result, output_format))


def run_mev_assessment(quotes, formatter, output_format, trade_value_usd, eth_price):
    """Assess MEV risk."""
    if not quotes:
        return

    best = max(quotes, key=lambda q: q.effective_rate)
    assessor = MEVAssessor(eth_price_usd=eth_price)
    assessment = assessor.assess_risk(best, trade_value_usd)

    print(formatter.format_mev(assessment, output_format))


def run_full_analysis(quotes, formatter, output_format, amount, eth_price):
    """Run complete analysis."""
    if not quotes:
        return

    trade_value_usd = float(amount) * eth_price

    print("=" * 60)
    print("COMPLETE DEX ANALYSIS")
    print("=" * 60)

    # Comparison
    print("\n--- ROUTE COMPARISON ---\n")
    run_comparison(quotes, formatter, output_format, trade_value_usd)

    # Split analysis
    print("\n--- SPLIT ORDER ANALYSIS ---\n")
    run_split_analysis(quotes, formatter, output_format, amount, eth_price)

    # MEV assessment
    print("\n--- MEV RISK ASSESSMENT ---\n")
    run_mev_assessment(quotes, formatter, output_format, trade_value_usd, eth_price)


async def main():
    """Main entry point."""
    args = parse_args()

    # Parse amount
    try:
        amount = Decimal(args.amount)
    except InvalidOperation:
        print(f"Error: Invalid amount '{args.amount}'")
        sys.exit(1)

    # Initialize formatter
    formatter = OutputFormatter(use_color=not args.no_color)

    # Fetch quotes
    quotes = await fetch_quotes(args)

    if not quotes:
        sys.exit(1)

    # Calculate trade value for recommendations
    trade_value_usd = float(amount) * args.eth_price

    # Run requested analysis
    if args.full:
        run_full_analysis(quotes, formatter, args.output, amount, args.eth_price)
    elif args.compare:
        run_comparison(quotes, formatter, args.output, trade_value_usd)
    elif args.split:
        run_split_analysis(quotes, formatter, args.output, amount, args.eth_price)
    elif args.mev_check:
        run_mev_assessment(quotes, formatter, args.output, trade_value_usd, args.eth_price)
    elif args.routes:
        # Routes mode is essentially comparison with route details
        run_comparison(quotes, formatter, args.output, trade_value_usd)
    else:
        # Default: quick quote
        run_quick_quote(quotes, formatter, args.output)


def demo_mode():
    """Run demo with mock data when APIs unavailable."""

    print("=" * 60)
    print("DEX AGGREGATOR ROUTER - DEMO MODE")
    print("=" * 60)
    print("\nRunning with mock data (no API keys configured)\n")

    # Create mock quotes
    mock_quotes = [
        {
            "source": "1inch",
            "output": "2543.22",
            "rate": "2543.22",
            "impact": "0.12%",
            "gas": "$11.25",
            "protocols": "Uniswap V3",
        },
        {
            "source": "Paraswap",
            "output": "2539.84",
            "rate": "2539.84",
            "impact": "0.15%",
            "gas": "$13.50",
            "protocols": "Curve, Uniswap V2",
        },
        {
            "source": "0x",
            "output": "2541.00",
            "rate": "2541.00",
            "impact": "0.14%",
            "gas": "$12.00",
            "protocols": "Balancer",
        },
    ]

    print("Quote Comparison (1 ETH → USDC)")
    print("-" * 60)
    print(f"{'Source':<12} {'Output':>12} {'Rate':>12} {'Impact':>8} {'Gas':>8}")
    print("-" * 60)

    for q in mock_quotes:
        print(f"{q['source']:<12} {q['output']:>12} {q['rate']:>12} {q['impact']:>8} {q['gas']:>8}")

    print("-" * 60)
    print("\nBest Route: 1inch via Uniswap V3")
    print("Spread: 0.13%")
    print("\nTo use with live data, set environment variables:")
    print("  export ONEINCH_API_KEY=your-api-key")
    print("  export ZEROX_API_KEY=your-api-key")


if __name__ == "__main__":
    # Check if running in demo mode
    if "--demo" in sys.argv:
        demo_mode()
    else:
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            print("\nAborted.")
            sys.exit(0)
