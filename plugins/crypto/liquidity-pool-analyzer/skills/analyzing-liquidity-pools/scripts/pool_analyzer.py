#!/usr/bin/env python3
"""
Liquidity Pool Analyzer - Main CLI

Analyze DEX liquidity pools for TVL, volume, fees, and impermanent loss.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 2.0.0
License: MIT
"""

import argparse
import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from pool_fetcher import PoolFetcher
from il_calculator import ILCalculator
from pool_metrics import PoolMetrics
from formatters import PoolFormatter


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze DEX liquidity pools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --pool 0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640
  %(prog)s --pair ETH/USDC --protocol uniswap-v3
  %(prog)s --il-calc --entry-price 2000 --current-price 3000
  %(prog)s --compare --pair ETH/USDC --protocols uniswap-v3,curve
        """,
    )

    # Pool identification
    parser.add_argument("--pool", "-p", help="Pool address to analyze")

    parser.add_argument("--pair", help="Token pair to search (e.g., ETH/USDC)")

    parser.add_argument("--protocol", help="Protocol filter (uniswap-v3, curve, balancer, etc.)")

    parser.add_argument("--chain", "-c", default="ethereum", help="Blockchain (ethereum, arbitrum, polygon, etc.)")

    # IL calculation
    parser.add_argument("--il-calc", action="store_true", help="Calculate impermanent loss")

    parser.add_argument("--entry-price", type=float, help="Entry price for IL calculation")

    parser.add_argument("--current-price", type=float, help="Current price for IL calculation")

    parser.add_argument("--il-scenarios", action="store_true", help="Show IL for various price scenarios")

    # Position analysis
    parser.add_argument("--position", type=float, help="Position size in USD for projections")

    # Comparison
    parser.add_argument("--compare", action="store_true", help="Compare pools")

    parser.add_argument("--protocols", help="Protocols to compare, comma-separated")

    parser.add_argument("--fee-tiers", help="Fee tiers to compare, comma-separated")

    # Filters
    parser.add_argument("--min-tvl", type=float, default=0, help="Minimum TVL in USD")

    parser.add_argument("--top", "-t", type=int, default=10, help="Number of results to show")

    # Output options
    parser.add_argument("--format", "-f", choices=["table", "json", "csv"], default="table", help="Output format")

    parser.add_argument("--output", "-o", help="Output file")

    parser.add_argument("--detailed", action="store_true", help="Show detailed analysis")

    # Other
    parser.add_argument("--no-cache", action="store_true", help="Bypass cache")

    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    parser.add_argument("--version", action="version", version="%(prog)s 2.0.0")

    args = parser.parse_args()

    try:
        # Initialize components
        fetcher = PoolFetcher(use_cache=not args.no_cache, verbose=args.verbose)
        il_calc = ILCalculator(verbose=args.verbose)
        metrics_calc = PoolMetrics(verbose=args.verbose)
        formatter = PoolFormatter()

        # Handle IL calculation mode
        if args.il_calc and args.entry_price and args.current_price:
            return handle_il_calculation(args, il_calc, formatter)

        # Handle IL scenarios mode
        if args.il_scenarios:
            return handle_il_scenarios(il_calc, formatter, args)

        # Fetch pools
        if args.verbose:
            print("Fetching pool data...")

        pools = []

        if args.pool:
            # Specific pool by address
            pool = fetcher.fetch_pool_by_address(args.pool, chain=args.chain, protocol=args.protocol or "uniswap-v3")
            if pool:
                pools = [pool]
        elif args.pair:
            # Search by token pair
            tokens = args.pair.upper().replace("/", "-").split("-")
            if len(tokens) >= 2:
                pools = fetcher.fetch_pools_by_pair(
                    tokens[0], tokens[1], chain=args.chain if args.chain != "ethereum" else None, protocol=args.protocol
                )
        elif args.protocol:
            # All pools for a protocol
            pools = fetcher.fetch_pools_by_protocol(
                args.protocol, chain=args.chain if args.chain != "ethereum" else None, min_tvl=args.min_tvl
            )
        else:
            print("Please specify --pool, --pair, or --protocol", file=sys.stderr)
            sys.exit(1)

        if not pools:
            print("No pools found matching criteria.", file=sys.stderr)
            sys.exit(0)

        # Apply filters
        if args.min_tvl > 0:
            pools = [p for p in pools if (p.get("tvlUsd") or 0) >= args.min_tvl]

        # Calculate metrics
        for pool in pools:
            metrics_calc.calculate_metrics(pool)

        # Limit results
        pools = pools[: args.top]

        if not pools:
            print("No pools match criteria after filtering.", file=sys.stderr)
            sys.exit(0)

        # Handle position projection
        if args.position and len(pools) == 1:
            position_metrics = metrics_calc.calculate_position_metrics(pools[0], args.position)
            pools[0]["position"] = position_metrics

        # Format output
        if len(pools) == 1 and not args.compare:
            output = formatter.format(pools[0], args.format, args.detailed)
        else:
            output = formatter.format(pools, args.format, args.detailed)

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


def handle_il_calculation(args, il_calc, formatter):
    """Handle IL calculation mode.

    Args:
        args: CLI arguments
        il_calc: IL calculator instance
        formatter: Output formatter

    Returns:
        Exit code
    """
    position_value = args.position or 1000

    il_data = il_calc.calculate_position_il(
        entry_price=args.entry_price, current_price=args.current_price, position_value=position_value
    )

    if args.format == "json":
        output = formatter._format_json(il_data)
    else:
        output = formatter.format_il_report(il_data)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Results saved to {args.output}")
    else:
        print(output)

    return 0


def handle_il_scenarios(il_calc, formatter, args):
    """Handle IL scenarios mode.

    Args:
        il_calc: IL calculator instance
        formatter: Output formatter
        args: CLI arguments

    Returns:
        Exit code
    """
    scenarios = il_calc.generate_il_scenarios()

    if args.format == "json":
        output = formatter._format_json(scenarios)
    else:
        output = formatter.format_il_scenarios(scenarios)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Results saved to {args.output}")
    else:
        print(output)

    return 0


if __name__ == "__main__":
    main()
