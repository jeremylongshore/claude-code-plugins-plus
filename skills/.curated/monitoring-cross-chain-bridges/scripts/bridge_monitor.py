#!/usr/bin/env python3
"""
Cross-Chain Bridge Monitor

Monitor bridge TVL, volume, and transaction status.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 1.0.0
License: MIT
"""

import argparse
import json
import sys
from decimal import Decimal
from typing import List

# Local imports
from bridge_fetcher import BridgeFetcher
from protocol_adapters import get_all_adapters, FeeEstimate
from tx_tracker import TxTracker
from formatters import (
    format_bridges_table,
    format_tvl_table,
    format_bridge_detail,
    format_fee_comparison,
    format_tx_status,
    format_chains_list,
    format_json,
)


def cmd_tvl(args) -> int:
    """Show bridge TVL rankings."""
    print("\nFetching bridge TVL data...")

    try:
        fetcher = BridgeFetcher(verbose=args.verbose)
        bridges = fetcher.get_all_bridges()

        if not bridges:
            print("No bridges found")
            return 1

        # Fetch TVL for top bridges
        tvl_data = []
        for bridge in bridges[: args.limit]:
            if args.verbose:
                print(f"  Fetching TVL for {bridge.display_name}...")

            tvl = fetcher.get_bridge_tvl(bridge.id)
            tvl_data.append((bridge.display_name, tvl))

        if args.format == "json":
            output = [{"bridge": name, "tvl": vars(tvl) if tvl else None} for name, tvl in tvl_data]
            print(json.dumps(output, indent=2, default=str))
        else:
            print(format_tvl_table(tvl_data))

        return 0

    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


def cmd_bridges(args) -> int:
    """List all bridges."""
    print("\nFetching bridge data...")

    try:
        fetcher = BridgeFetcher(verbose=args.verbose)
        bridges = fetcher.get_all_bridges()

        if args.chain:
            # Filter by chain
            chain_lower = args.chain.lower()
            bridges = [b for b in bridges if chain_lower in [c.lower() for c in b.chains + b.destination_chains]]

        if not bridges:
            print("No bridges found")
            return 1

        if args.format == "json":
            print(format_json(bridges[: args.limit]))
        else:
            print(format_bridges_table(bridges, limit=args.limit))

        return 0

    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


def cmd_detail(args) -> int:
    """Show detailed bridge information."""
    print(f"\nFetching details for {args.bridge}...")

    try:
        fetcher = BridgeFetcher(verbose=args.verbose)
        bridge = fetcher.get_bridge_by_name(args.bridge)

        if not bridge:
            print(f"Bridge not found: {args.bridge}")
            print("\nAvailable bridges:")
            bridges = fetcher.get_all_bridges()
            for b in bridges[:10]:
                print(f"  - {b.display_name}")
            return 1

        tvl = fetcher.get_bridge_tvl(bridge.id)

        if args.format == "json":
            output = {"bridge": vars(bridge), "tvl": vars(tvl) if tvl else None}
            print(json.dumps(output, indent=2, default=str))
        else:
            print(format_bridge_detail(bridge, tvl))

        return 0

    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


def cmd_compare(args) -> int:
    """Compare bridge fees and times."""
    print(f"\nComparing routes: {args.source} → {args.dest}")
    print(f"Amount: {args.amount} {args.token}")

    try:
        estimates: List[FeeEstimate] = []
        adapters = get_all_adapters()

        for name, adapter in adapters.items():
            # Check if both chains supported
            chains = [c.lower() for c in adapter.supported_chains]
            if args.source.lower() in chains and args.dest.lower() in chains:
                estimate = adapter.get_fee_estimate(args.source, args.dest, args.token, Decimal(str(args.amount)))
                if estimate:
                    estimates.append(estimate)

        if not estimates:
            print(f"No bridges support {args.source} → {args.dest}")
            return 1

        if args.format == "json":
            print(format_json(estimates))
        else:
            print(format_fee_comparison(estimates))

        return 0

    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


def cmd_tx(args) -> int:
    """Track bridge transaction status."""
    print(f"\nTracking transaction: {args.tx_hash[:20]}...")

    try:
        tracker = TxTracker(verbose=args.verbose)
        status = tracker.track_bridge_tx(args.tx_hash, bridge=args.bridge, source_chain=args.chain)

        if not status:
            print("Transaction not found in any bridge")
            return 1

        if args.format == "json":
            print(format_json(status))
        else:
            print(format_tx_status(status))

        return 0

    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


def cmd_chains(args) -> int:
    """List supported chains."""
    print("\nFetching chain data...")

    try:
        fetcher = BridgeFetcher(verbose=args.verbose)
        chains = fetcher.get_all_chains()

        if args.format == "json":
            print(json.dumps({"chains": chains}, indent=2))
        else:
            print(format_chains_list(chains))

        return 0

    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


def cmd_protocols(args) -> int:
    """List supported bridge protocols."""
    adapters = get_all_adapters()

    if args.format == "json":
        output = {
            name: {"name": adapter.name, "chains": adapter.supported_chains} for name, adapter in adapters.items()
        }
        print(json.dumps(output, indent=2))
    else:
        print()
        print("SUPPORTED BRIDGE PROTOCOLS")
        print("=" * 60)

        for name, adapter in adapters.items():
            print(f"\n{adapter.name}")
            print("-" * 40)
            chains = adapter.supported_chains
            print(f"  Chains: {', '.join(chains[:5])}")
            if len(chains) > 5:
                print(f"          +{len(chains) - 5} more")

        print()
        print("=" * 60)
        print(f"Total protocols: {len(adapters)}")

    return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Monitor cross-chain bridges",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show bridge TVL rankings
  %(prog)s tvl --limit 20

  # List all bridges
  %(prog)s bridges

  # Get bridge details
  %(prog)s detail --bridge stargate

  # Compare bridge fees
  %(prog)s compare --source ethereum --dest arbitrum --amount 1000 --token USDC

  # Track transaction
  %(prog)s tx --tx-hash 0x...

  # List supported chains
  %(prog)s chains
        """,
    )

    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument(
        "-f", "--format", choices=["text", "json"], default="text", help="Output format (default: text)"
    )

    subparsers = parser.add_subparsers(dest="command", help="Command")

    # tvl command
    tvl_parser = subparsers.add_parser("tvl", help="Show bridge TVL rankings")
    tvl_parser.add_argument("--limit", "-l", type=int, default=20, help="Maximum bridges (default: 20)")
    tvl_parser.set_defaults(func=cmd_tvl)

    # bridges command
    bridges_parser = subparsers.add_parser("bridges", help="List all bridges")
    bridges_parser.add_argument("--chain", "-c", help="Filter by chain")
    bridges_parser.add_argument("--limit", "-l", type=int, default=30, help="Maximum bridges (default: 30)")
    bridges_parser.set_defaults(func=cmd_bridges)

    # detail command
    detail_parser = subparsers.add_parser("detail", help="Show bridge details")
    detail_parser.add_argument("--bridge", "-b", required=True, help="Bridge name")
    detail_parser.set_defaults(func=cmd_detail)

    # compare command
    compare_parser = subparsers.add_parser("compare", help="Compare bridge fees and times")
    compare_parser.add_argument("--source", "-s", required=True, help="Source chain")
    compare_parser.add_argument("--dest", "-d", required=True, help="Destination chain")
    compare_parser.add_argument("--amount", "-a", type=float, default=1000, help="Amount to bridge (default: 1000)")
    compare_parser.add_argument("--token", "-t", default="USDC", help="Token symbol (default: USDC)")
    compare_parser.set_defaults(func=cmd_compare)

    # tx command
    tx_parser = subparsers.add_parser("tx", help="Track transaction status")
    tx_parser.add_argument("--tx-hash", required=True, help="Transaction hash")
    tx_parser.add_argument("--bridge", "-b", help="Bridge name (optional)")
    tx_parser.add_argument("--chain", "-c", help="Source chain (optional)")
    tx_parser.set_defaults(func=cmd_tx)

    # chains command
    chains_parser = subparsers.add_parser("chains", help="List supported chains")
    chains_parser.set_defaults(func=cmd_chains)

    # protocols command
    protocols_parser = subparsers.add_parser("protocols", help="List supported bridge protocols")
    protocols_parser.set_defaults(func=cmd_protocols)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
