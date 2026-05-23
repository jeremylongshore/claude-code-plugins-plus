#!/usr/bin/env python3
"""
Crypto Portfolio Tracker - Main CLI Entry Point

Track cryptocurrency portfolio with real-time valuations,
allocation analysis, and P&L tracking.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 2.0.0
License: MIT
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

# Add scripts directory to path for local imports
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from portfolio_loader import PortfolioLoader
from price_fetcher import PriceFetcher
from valuation_engine import ValuationEngine
from formatters import PortfolioFormatter


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Track cryptocurrency portfolio with real-time valuations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --portfolio holdings.json              # Portfolio summary
  %(prog)s --portfolio holdings.json --holdings   # All holdings
  %(prog)s --portfolio holdings.json --detailed   # Full analysis
  %(prog)s --portfolio holdings.json --format json  # JSON export
        """,
    )

    # Required
    parser.add_argument("--portfolio", "-p", type=str, required=True, help="Path to portfolio JSON file")

    # Display options
    parser.add_argument("--holdings", action="store_true", help="Show all holdings breakdown")
    parser.add_argument("--detailed", action="store_true", help="Show detailed analysis with P&L")
    parser.add_argument(
        "--sort",
        type=str,
        choices=["value", "allocation", "name", "change"],
        default="value",
        help="Sort holdings by (default: value)",
    )

    # Thresholds
    parser.add_argument(
        "--threshold", type=float, default=25.0, help="Allocation warning threshold in percent (default: 25)"
    )

    # Output options
    parser.add_argument(
        "--format",
        "-f",
        type=str,
        choices=["table", "json", "csv"],
        default="table",
        help="Output format (default: table)",
    )
    parser.add_argument("--output", "-o", type=str, help="Output file path (default: stdout)")

    # Debug options
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--version", action="version", version="%(prog)s 2.0.0")

    return parser.parse_args()


def main() -> None:
    """Main entry point."""
    args = parse_args()

    # Initialize components
    loader = PortfolioLoader(verbose=args.verbose)
    fetcher = PriceFetcher(verbose=args.verbose)
    engine = ValuationEngine(verbose=args.verbose)
    formatter = PortfolioFormatter()

    # Load portfolio
    if args.verbose:
        print(f"Loading portfolio from {args.portfolio}...", file=sys.stderr)

    portfolio = loader.load(args.portfolio)
    if not portfolio:
        print(f"Error: Failed to load portfolio from {args.portfolio}", file=sys.stderr)
        sys.exit(1)

    if args.verbose:
        print(f"Loaded {len(portfolio.get('holdings', []))} holdings", file=sys.stderr)

    # Get unique coins
    coins = list(set(h.get("coin", "").upper() for h in portfolio.get("holdings", [])))
    coins = [c for c in coins if c]  # Remove empty

    if not coins:
        print("Error: No valid holdings found in portfolio", file=sys.stderr)
        sys.exit(1)

    # Fetch prices
    if args.verbose:
        print(f"Fetching prices for {len(coins)} coins...", file=sys.stderr)

    prices = fetcher.fetch_prices(coins)
    if not prices:
        print("Warning: Could not fetch prices, using cached or fallback values", file=sys.stderr)

    # Calculate valuations
    if args.verbose:
        print("Calculating valuations...", file=sys.stderr)

    valuations = engine.calculate(portfolio=portfolio, prices=prices, threshold=args.threshold)

    # Sort holdings
    if valuations.get("holdings"):
        sort_key = {
            "value": lambda x: x.get("value_usd", 0),
            "allocation": lambda x: x.get("allocation_pct", 0),
            "name": lambda x: x.get("coin", ""),
            "change": lambda x: x.get("change_24h_pct", 0) or 0,
        }.get(args.sort, lambda x: x.get("value_usd", 0))

        reverse = args.sort != "name"
        valuations["holdings"] = sorted(valuations["holdings"], key=sort_key, reverse=reverse)

    # Add metadata
    valuations["meta"] = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "portfolio_file": args.portfolio,
        "threshold": args.threshold,
        "sort_by": args.sort,
    }

    # Determine display mode
    show_all = args.holdings or args.detailed
    show_pnl = args.detailed

    # Format output
    output = formatter.format(valuations, format_type=args.format, show_all_holdings=show_all, show_pnl=show_pnl)

    # Write output
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            f.write(output)
        print(f"Output written to {output_path}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
