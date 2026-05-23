#!/usr/bin/env python3
"""
Gas Fee Optimizer CLI

Optimize gas costs by analyzing current prices, historical patterns,
and providing timing recommendations.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 1.0.0
License: MIT
"""

import argparse
import sys
from datetime import datetime, timedelta

from gas_fetcher import GasFetcher, CHAIN_CONFIG
from pattern_analyzer import PatternAnalyzer
from cost_estimator import CostEstimator, GAS_LIMITS
from formatters import (
    format_current_gas,
    format_cost_estimate,
    format_multi_tier_estimate,
    format_hourly_patterns,
    format_daily_patterns,
    format_optimal_window,
    format_prediction,
    format_json,
)


def cmd_current(args):
    """Show current gas prices."""
    fetcher = GasFetcher(chain=args.chain, verbose=args.verbose)
    gas_data = fetcher.get_current_gas()

    native_symbol = CHAIN_CONFIG.get(args.chain, {}).get("native_symbol", "ETH")

    if args.json:
        print(format_json(gas_data))
    else:
        print(format_current_gas(gas_data, native_symbol))

    # Record for pattern analysis
    if not args.no_record:
        analyzer = PatternAnalyzer(verbose=args.verbose)
        analyzer.record_gas_data(gas_data.standard / 10**9)


def cmd_estimate(args):
    """Estimate transaction cost."""
    fetcher = GasFetcher(chain=args.chain, verbose=args.verbose)
    gas_data = fetcher.get_current_gas()

    native_symbol = CHAIN_CONFIG.get(args.chain, {}).get("native_symbol", "ETH")
    estimator = CostEstimator(native_symbol=native_symbol, verbose=args.verbose)

    # Determine gas limit
    if args.gas_limit:
        gas_limit = args.gas_limit
        operation = "custom"
    else:
        operation = args.operation or "eth_transfer"
        gas_limit = GAS_LIMITS.get(operation, 100000)

    if args.all_tiers:
        # Show all tier estimates
        multi = estimator.estimate_all_tiers(
            operation,
            gas_data.slow / 10**9,
            gas_data.standard / 10**9,
            gas_data.fast / 10**9,
            gas_data.instant / 10**9,
            gas_limit,
        )

        if args.json:
            print(format_json(multi))
        else:
            print(format_multi_tier_estimate(multi, native_symbol))
    else:
        # Single tier estimate
        tier_prices = {
            "slow": gas_data.slow,
            "standard": gas_data.standard,
            "fast": gas_data.fast,
            "instant": gas_data.instant,
        }
        gas_price_wei = tier_prices.get(args.tier, gas_data.standard)
        gas_price_gwei = gas_price_wei / 10**9

        estimate = estimator.estimate_cost(operation, gas_price_gwei, args.tier, gas_limit)

        if args.json:
            print(format_json(estimate))
        else:
            print(format_cost_estimate(estimate, native_symbol))


def cmd_patterns(args):
    """Show historical gas patterns."""
    analyzer = PatternAnalyzer(verbose=args.verbose)

    if args.daily:
        patterns = analyzer.analyze_daily_pattern()
        if args.json:
            print(format_json(patterns))
        else:
            print(format_daily_patterns(patterns))
    else:
        patterns = analyzer.analyze_hourly_pattern()
        if args.json:
            print(format_json(patterns))
        else:
            print(format_hourly_patterns(patterns))


def cmd_optimal(args):
    """Find optimal transaction window."""
    fetcher = GasFetcher(chain=args.chain, verbose=args.verbose)
    gas_data = fetcher.get_current_gas()
    current_gas = gas_data.standard / 10**9

    analyzer = PatternAnalyzer(verbose=args.verbose)
    window = analyzer.find_optimal_window(current_gas)

    if args.json:
        print(format_json(window))
    else:
        print(format_optimal_window(window))

        # Show comparison with current
        if current_gas > window.expected_gas_gwei * 1.1:
            savings_pct = ((current_gas - window.expected_gas_gwei) / current_gas) * 100
            print(f"\nCurrent gas ({current_gas:.1f} gwei) is {savings_pct:.0f}% higher than optimal.")
            print("Consider waiting for the recommended window.")
        else:
            print(f"\nCurrent gas ({current_gas:.1f} gwei) is near optimal - good time to transact!")


def cmd_predict(args):
    """Predict gas for a future time."""
    analyzer = PatternAnalyzer(verbose=args.verbose)

    # Parse target time
    if args.time:
        try:
            target = datetime.strptime(args.time, "%Y-%m-%d %H:%M")
        except ValueError:
            try:
                # Try just hour
                hour = int(args.time)
                now = datetime.now()
                target = now.replace(hour=hour, minute=0, second=0, microsecond=0)
                if target < now:
                    target += timedelta(days=1)
            except ValueError:
                print(f"Invalid time format: {args.time}")
                print("Use: 'YYYY-MM-DD HH:MM' or just hour (0-23)")
                sys.exit(1)
    else:
        # Default to 1 hour from now
        target = datetime.now() + timedelta(hours=1)

    prediction = analyzer.predict_gas(target)

    if args.json:
        print(format_json(prediction))
    else:
        print(format_prediction(prediction))


def cmd_operations(args):
    """List known operations and gas limits."""
    print("\nKNOWN OPERATIONS")
    print("=" * 50)
    print(f"{'Operation':<25} {'Gas Limit':>15}")
    print("-" * 50)

    for op, gas in sorted(GAS_LIMITS.items(), key=lambda x: x[1]):
        print(f"{op:<25} {gas:>15,}")

    print("=" * 50)
    print("\nUse --operation <name> with 'estimate' command")
    print("Or use --gas-limit <number> for custom operations")


def cmd_compare(args):
    """Compare gas across chains."""
    chains = args.chains.split(",") if args.chains else list(CHAIN_CONFIG.keys())

    print("\nMULTI-CHAIN GAS COMPARISON")
    print("=" * 70)
    print(f"{'Chain':<15} {'Standard':<15} {'Fast':<15} {'Source':<20}")
    print("-" * 70)

    for chain in chains:
        try:
            fetcher = GasFetcher(chain=chain.strip(), verbose=args.verbose)
            gas = fetcher.get_current_gas()
            std_gwei = gas.standard / 10**9
            fast_gwei = gas.fast / 10**9
            print(f"{chain:<15} {std_gwei:<15.2f} {fast_gwei:<15.2f} {gas.source:<20}")
        except Exception as e:
            print(f"{chain:<15} {'Error':<15} {'':<15} {str(e)[:20]:<20}")

    print("=" * 70)


def cmd_history(args):
    """Show base fee history."""
    fetcher = GasFetcher(chain=args.chain, verbose=args.verbose)
    history = fetcher.get_base_fee_history(args.blocks)

    if not history:
        print("No history available")
        return

    if args.json:
        print(format_json(history))
    else:
        print(f"\nBASE FEE HISTORY (Last {len(history)} blocks)")
        print("=" * 60)
        print(f"{'Block':<12} {'Base Fee (gwei)':<18} {'Gas Used %':<15}")
        print("-" * 60)

        for entry in history[-20:]:  # Show last 20
            base_gwei = entry.base_fee / 10**9
            gas_pct = entry.gas_used_ratio * 100
            print(f"{entry.block_number:<12} {base_gwei:<18.2f} {gas_pct:<15.1f}")

        # Summary
        base_fees = [e.base_fee / 10**9 for e in history]
        avg_fee = sum(base_fees) / len(base_fees)
        min_fee = min(base_fees)
        max_fee = max(base_fees)

        print("-" * 60)
        print(f"Average: {avg_fee:.2f} gwei | Min: {min_fee:.2f} | Max: {max_fee:.2f}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Gas Fee Optimizer - Optimize blockchain transaction costs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  gas_optimizer.py current                    # Current gas prices
  gas_optimizer.py current --chain polygon    # Polygon gas prices
  gas_optimizer.py estimate --operation uniswap_v2_swap --all-tiers
  gas_optimizer.py estimate --gas-limit 150000 --tier fast
  gas_optimizer.py patterns                   # Hourly patterns
  gas_optimizer.py patterns --daily           # Daily patterns
  gas_optimizer.py optimal                    # Best time to transact
  gas_optimizer.py predict --time "14"        # Predict gas at 2 PM
  gas_optimizer.py compare                    # Compare all chains
  gas_optimizer.py operations                 # List known operations
        """,
    )

    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--json", "-j", action="store_true", help="JSON output")
    parser.add_argument(
        "--chain",
        "-c",
        default="ethereum",
        choices=list(CHAIN_CONFIG.keys()),
        help="Blockchain network (default: ethereum)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # current command
    p_current = subparsers.add_parser("current", help="Show current gas prices")
    p_current.add_argument("--no-record", action="store_true", help="Don't record for pattern analysis")
    p_current.set_defaults(func=cmd_current)

    # estimate command
    p_estimate = subparsers.add_parser("estimate", help="Estimate transaction cost")
    p_estimate.add_argument("--operation", "-o", help="Operation name (use 'operations' to list)")
    p_estimate.add_argument("--gas-limit", "-g", type=int, help="Custom gas limit")
    p_estimate.add_argument(
        "--tier",
        "-t",
        default="standard",
        choices=["slow", "standard", "fast", "instant"],
        help="Gas price tier (default: standard)",
    )
    p_estimate.add_argument("--all-tiers", "-a", action="store_true", help="Show all tier estimates")
    p_estimate.set_defaults(func=cmd_estimate)

    # patterns command
    p_patterns = subparsers.add_parser("patterns", help="Show gas patterns")
    p_patterns.add_argument("--daily", "-d", action="store_true", help="Show daily patterns instead of hourly")
    p_patterns.set_defaults(func=cmd_patterns)

    # optimal command
    p_optimal = subparsers.add_parser("optimal", help="Find optimal transaction window")
    p_optimal.set_defaults(func=cmd_optimal)

    # predict command
    p_predict = subparsers.add_parser("predict", help="Predict gas for future time")
    p_predict.add_argument("--time", "-t", help="Target time (YYYY-MM-DD HH:MM or just hour 0-23)")
    p_predict.set_defaults(func=cmd_predict)

    # operations command
    p_ops = subparsers.add_parser("operations", help="List known operations")
    p_ops.set_defaults(func=cmd_operations)

    # compare command
    p_compare = subparsers.add_parser("compare", help="Compare gas across chains")
    p_compare.add_argument("--chains", help="Comma-separated chain list")
    p_compare.set_defaults(func=cmd_compare)

    # history command
    p_history = subparsers.add_parser("history", help="Show base fee history")
    p_history.add_argument("--blocks", "-b", type=int, default=100, help="Number of blocks (default: 100)")
    p_history.set_defaults(func=cmd_history)

    args = parser.parse_args()

    if not args.command:
        # Default to current
        args.command = "current"
        args.no_record = False
        cmd_current(args)
    elif hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
