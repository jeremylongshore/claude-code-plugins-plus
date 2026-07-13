#!/usr/bin/env python3
"""
DeFi Yield Optimizer - Main CLI

Find and compare DeFi yield opportunities across protocols with
APY calculations, risk assessment, and optimization recommendations.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 2.0.0
License: MIT
"""

import argparse
import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from protocol_fetcher import ProtocolFetcher
from yield_calculator import YieldCalculator
from risk_assessor import RiskAssessor
from formatters import YieldFormatter


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Find and compare DeFi yield opportunities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --top 20
  %(prog)s --chain ethereum --min-tvl 10000000
  %(prog)s --risk low --audited-only --min-apy 3
  %(prog)s --asset USDC --protocol aave,compound
  %(prog)s --format json --output yields.json
        """,
    )

    # Search options
    parser.add_argument("--top", "-t", type=int, default=10, help="Number of top yields to show (default: 10)")

    parser.add_argument("--chain", "-c", help="Filter by chain(s), comma-separated (ethereum, arbitrum, polygon, etc.)")

    parser.add_argument("--protocol", "-p", help="Filter by protocol(s), comma-separated (aave, compound, curve, etc.)")

    parser.add_argument("--asset", "-a", help="Filter by asset(s), comma-separated (USDC, ETH, WBTC, etc.)")

    # TVL and APY filters
    parser.add_argument("--min-tvl", type=float, default=0, help="Minimum TVL in USD (default: 0)")

    parser.add_argument("--min-apy", type=float, default=0, help="Minimum APY percentage (default: 0)")

    parser.add_argument("--max-apy", type=float, help="Maximum APY percentage (filter outliers)")

    # Risk filters
    parser.add_argument(
        "--risk", choices=["low", "medium", "high", "all"], default="all", help="Filter by risk level (default: all)"
    )

    parser.add_argument("--audited-only", action="store_true", help="Only show audited protocols")

    # Analysis options
    parser.add_argument("--pool", help="Show detailed analysis for specific pool")

    parser.add_argument("--compare", help="Compare specific protocols, comma-separated")

    parser.add_argument("--detailed", action="store_true", help="Show detailed breakdown")

    # Output options
    parser.add_argument(
        "--format", "-f", choices=["table", "json", "csv"], default="table", help="Output format (default: table)"
    )

    parser.add_argument("--output", "-o", help="Output file (default: stdout)")

    parser.add_argument(
        "--sort", choices=["apy", "tvl", "risk", "name"], default="apy", help="Sort results by (default: apy)"
    )

    # Other
    parser.add_argument("--no-cache", action="store_true", help="Bypass cache and fetch fresh data")

    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    parser.add_argument("--version", action="version", version="%(prog)s 2.0.0")

    args = parser.parse_args()

    try:
        # Initialize components
        fetcher = ProtocolFetcher(use_cache=not args.no_cache, verbose=args.verbose)
        calculator = YieldCalculator(verbose=args.verbose)
        assessor = RiskAssessor(verbose=args.verbose)
        formatter = YieldFormatter()

        # Fetch yield data
        if args.verbose:
            print("Fetching yield data...")

        pools = fetcher.fetch_yields()

        if not pools:
            print("No yield data available. Check network connection.", file=sys.stderr)
            sys.exit(1)

        if args.verbose:
            print(f"Fetched {len(pools)} pools")

        # Apply filters
        filtered = pools

        # Chain filter
        if args.chain:
            chains = [c.strip().lower() for c in args.chain.split(",")]
            filtered = [p for p in filtered if p.get("chain", "").lower() in chains]

        # Protocol filter
        if args.protocol:
            protocols = [p.strip().lower() for p in args.protocol.split(",")]
            filtered = [p for p in filtered if p.get("project", "").lower() in protocols]

        # Asset filter
        if args.asset:
            assets = [a.strip().upper() for a in args.asset.split(",")]
            filtered = [p for p in filtered if any(a in p.get("symbol", "").upper() for a in assets)]

        # TVL filter
        if args.min_tvl > 0:
            filtered = [p for p in filtered if p.get("tvlUsd", 0) >= args.min_tvl]

        # APY filters
        if args.min_apy > 0:
            filtered = [p for p in filtered if (p.get("apy") or 0) >= args.min_apy]

        if args.max_apy:
            filtered = [p for p in filtered if (p.get("apy") or 0) <= args.max_apy]

        # Calculate yields and assess risks
        for pool in filtered:
            calculator.calculate(pool)
            assessor.assess(pool)

        # Risk filter (after assessment)
        if args.risk != "all":
            risk_map = {"low": (7, 10), "medium": (4, 7), "high": (0, 4)}
            min_score, max_score = risk_map.get(args.risk, (0, 10))
            filtered = [p for p in filtered if min_score <= p.get("risk_score", 5) < max_score]

        # Audited filter
        if args.audited_only:
            filtered = [p for p in filtered if p.get("audited", False)]

        # Sort
        sort_key = {
            "apy": lambda x: -(x.get("apy") or 0),
            "tvl": lambda x: -(x.get("tvlUsd") or 0),
            "risk": lambda x: -(x.get("risk_score") or 0),
            "name": lambda x: x.get("project", "").lower(),
        }
        filtered.sort(key=sort_key.get(args.sort, sort_key["apy"]))

        # Limit results
        filtered = filtered[: args.top]

        if not filtered:
            print("No pools match your criteria. Try broadening filters.", file=sys.stderr)
            sys.exit(0)

        # Format output
        output = formatter.format(filtered, format_type=args.format, detailed=args.detailed)

        # Output
        if args.output:
            with open(args.output, "w") as f:
                f.write(output)
            print(f"Results saved to {args.output}")
        else:
            print(output)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
