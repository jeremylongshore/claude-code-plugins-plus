#!/usr/bin/env python3
"""
On-Chain Analytics CLI

Analyze DeFi protocol metrics and blockchain data.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 1.0.0
License: MIT
"""

import argparse
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from data_fetcher import DataFetcher
from metrics_calculator import MetricsCalculator
from formatters import (
    format_protocols_table,
    format_chains_table,
    format_fees_table,
    format_trends_table,
    format_category_summary,
    format_json,
    format_csv,
)


def cmd_protocols(args) -> int:
    """List protocols by TVL.

    Args:
        args: CLI arguments

    Returns:
        Exit code
    """
    fetcher = DataFetcher(verbose=args.verbose)
    calc = MetricsCalculator()

    protocols = fetcher.fetch_protocols(limit=args.limit)

    # Convert to dict format
    data = [vars(p) for p in protocols]

    # Filter by category
    if args.category:
        data = [p for p in data if p.get("category", "").lower() == args.category.lower()]

    # Filter by chain
    if args.chain:
        data = [p for p in data if args.chain.lower() in [c.lower() for c in p.get("chains", [])]]

    # Calculate metrics
    data = calc.calculate_market_share(data)
    data = calc.calculate_tvl_to_mcap(data)
    data = calc.rank_protocols(data, args.sort)

    # Output
    if args.format == "json":
        print(format_json(data))
    elif args.format == "csv":
        print(format_csv(data, ["rank", "name", "tvl", "market_share", "category"]))
    else:
        print(format_protocols_table(data))

    return 0


def cmd_chains(args) -> int:
    """List chains by TVL.

    Args:
        args: CLI arguments

    Returns:
        Exit code
    """
    fetcher = DataFetcher(verbose=args.verbose)
    calc = MetricsCalculator()

    chains = fetcher.fetch_chains()
    chains = calc.calculate_chain_dominance(chains)

    if args.format == "json":
        print(format_json(chains))
    elif args.format == "csv":
        print(format_csv(chains, ["name", "tvl", "dominance"]))
    else:
        print(format_chains_table(chains))

    return 0


def cmd_fees(args) -> int:
    """Show protocol fees and revenue.

    Args:
        args: CLI arguments

    Returns:
        Exit code
    """
    fetcher = DataFetcher(verbose=args.verbose)

    fees = fetcher.fetch_fees_revenue(args.protocol)

    if not fees:
        print("No fee data available.")
        return 0

    # Sort by 30d fees
    fees.sort(key=lambda x: x.get("total30d", 0) or 0, reverse=True)

    if args.format == "json":
        print(format_json(fees[: args.limit]))
    elif args.format == "csv":
        print(format_csv(fees[: args.limit], ["name", "total24h", "total30d", "revenue24h", "revenue30d"]))
    else:
        print(format_fees_table(fees[: args.limit]))

    return 0


def cmd_dex(args) -> int:
    """Show DEX volumes.

    Args:
        args: CLI arguments

    Returns:
        Exit code
    """
    fetcher = DataFetcher(verbose=args.verbose)

    volumes = fetcher.fetch_dex_volumes(args.chain)

    if not volumes:
        print("No DEX volume data available.")
        return 0

    # Sort by volume
    volumes.sort(key=lambda x: x.get("total24h", 0) or 0, reverse=True)

    if args.format == "json":
        print(format_json(volumes[: args.limit]))
    else:
        from formatters import format_usd

        print("\nDEX 24h Volumes")
        print("=" * 60)
        for i, d in enumerate(volumes[: args.limit], 1):
            name = d.get("displayName", d.get("name", "Unknown"))
            vol = d.get("total24h", 0) or 0
            print(f"{i}. {name}: {format_usd(vol)}")

    return 0


def cmd_categories(args) -> int:
    """Show category breakdown.

    Args:
        args: CLI arguments

    Returns:
        Exit code
    """
    fetcher = DataFetcher(verbose=args.verbose)
    calc = MetricsCalculator()

    protocols = fetcher.fetch_protocols(limit=500)
    data = [vars(p) for p in protocols]

    categories = calc.calculate_category_metrics(data)

    if args.format == "json":
        print(format_json(categories))
    else:
        print(format_category_summary(categories))

    return 0


def cmd_trends(args) -> int:
    """Show trending protocols.

    Args:
        args: CLI arguments

    Returns:
        Exit code
    """
    fetcher = DataFetcher(verbose=args.verbose)
    calc = MetricsCalculator()

    protocols = fetcher.fetch_protocols(limit=200)
    data = [vars(p) for p in protocols]

    trends = calc.identify_trends(data, min_growth=args.threshold)

    if args.format == "json":
        print(format_json(trends))
    else:
        print(format_trends_table(trends))

    return 0


def cmd_yields(args) -> int:
    """Show top yields.

    Args:
        args: CLI arguments

    Returns:
        Exit code
    """
    fetcher = DataFetcher(verbose=args.verbose)

    pools = fetcher.fetch_yields(args.chain)

    # Sort by APY
    pools.sort(key=lambda x: x.get("apy", 0) or 0, reverse=True)

    # Filter by minimum TVL
    if args.min_tvl:
        pools = [p for p in pools if (p.get("tvlUsd", 0) or 0) >= args.min_tvl]

    if args.format == "json":
        print(format_json(pools[: args.limit]))
    else:
        from formatters import format_usd

        print(f"\nTop Yields{' on ' + args.chain if args.chain else ''}")
        print("=" * 80)
        print(f"{'Pool':<30} {'APY':<12} {'TVL':<14} {'Chain':<12}")
        print("-" * 80)
        for p in pools[: args.limit]:
            name = f"{p.get('project', '?')}: {p.get('symbol', '?')}"[:28]
            apy = f"{p.get('apy', 0):.2f}%"
            tvl = format_usd(p.get("tvlUsd", 0) or 0)
            chain = p.get("chain", "?")[:10]
            print(f"{name:<30} {apy:<12} {tvl:<14} {chain:<12}")

    return 0


def cmd_stables(args) -> int:
    """Show stablecoin metrics.

    Args:
        args: CLI arguments

    Returns:
        Exit code
    """
    fetcher = DataFetcher(verbose=args.verbose)

    stables = fetcher.fetch_stablecoin_data()

    # Sort by market cap
    stables.sort(key=lambda x: x.get("circulating", {}).get("peggedUSD", 0) or 0, reverse=True)

    if args.format == "json":
        print(format_json(stables[: args.limit]))
    else:
        from formatters import format_usd

        print("\nStablecoin Market Caps")
        print("=" * 70)
        for i, s in enumerate(stables[: args.limit], 1):
            name = s.get("name", "Unknown")
            mcap = s.get("circulating", {}).get("peggedUSD", 0) or 0
            price = s.get("price", 1.0) or 1.0
            print(f"{i}. {name}: {format_usd(mcap)} (${price:.4f})")

    return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="On-chain analytics for DeFi protocols",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s protocols                       # Top protocols by TVL
  %(prog)s protocols --category lending    # Lending protocols only
  %(prog)s chains                          # Chain TVL rankings
  %(prog)s fees                            # Protocol fees/revenue
  %(prog)s dex                             # DEX volumes
  %(prog)s trends                          # Trending protocols
  %(prog)s yields --min-tvl 1000000        # Top yields with >$1M TVL
  %(prog)s stables                         # Stablecoin market caps
        """,
    )

    parser.add_argument("--format", "-f", choices=["table", "json", "csv"], default="table")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--version", action="version", version="%(prog)s 1.0.0")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Protocols command
    proto_parser = subparsers.add_parser("protocols", help="Protocol TVL rankings")
    proto_parser.add_argument("--limit", "-l", type=int, default=50)
    proto_parser.add_argument("--category", "-c", help="Filter by category")
    proto_parser.add_argument("--chain", help="Filter by chain")
    proto_parser.add_argument("--sort", default="tvl", choices=["tvl", "market_share", "tvl_to_mcap"])
    proto_parser.set_defaults(func=cmd_protocols)

    # Chains command
    chain_parser = subparsers.add_parser("chains", help="Chain TVL rankings")
    chain_parser.set_defaults(func=cmd_chains)

    # Fees command
    fees_parser = subparsers.add_parser("fees", help="Protocol fees and revenue")
    fees_parser.add_argument("--protocol", "-p", help="Specific protocol")
    fees_parser.add_argument("--limit", "-l", type=int, default=30)
    fees_parser.set_defaults(func=cmd_fees)

    # DEX command
    dex_parser = subparsers.add_parser("dex", help="DEX volumes")
    dex_parser.add_argument("--chain", "-c", help="Filter by chain")
    dex_parser.add_argument("--limit", "-l", type=int, default=20)
    dex_parser.set_defaults(func=cmd_dex)

    # Categories command
    cat_parser = subparsers.add_parser("categories", help="Category breakdown")
    cat_parser.set_defaults(func=cmd_categories)

    # Trends command
    trends_parser = subparsers.add_parser("trends", help="Trending protocols")
    trends_parser.add_argument("--threshold", "-t", type=float, default=10.0, help="Min growth %")
    trends_parser.set_defaults(func=cmd_trends)

    # Yields command
    yields_parser = subparsers.add_parser("yields", help="Top yields")
    yields_parser.add_argument("--chain", "-c", help="Filter by chain")
    yields_parser.add_argument("--min-tvl", type=float, help="Minimum TVL")
    yields_parser.add_argument("--limit", "-l", type=int, default=20)
    yields_parser.set_defaults(func=cmd_yields)

    # Stablecoins command
    stables_parser = subparsers.add_parser("stables", help="Stablecoin metrics")
    stables_parser.add_argument("--limit", "-l", type=int, default=20)
    stables_parser.set_defaults(func=cmd_stables)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\nInterrupted.")
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
