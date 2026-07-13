#!/usr/bin/env python3
"""
Mempool Analyzer CLI

Monitor blockchain mempools for pending transactions and MEV opportunities.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 1.0.0
License: MIT

Usage:
    python mempool_analyzer.py pending                # View pending transactions
    python mempool_analyzer.py gas                    # Gas price analysis
    python mempool_analyzer.py swaps                  # Pending DEX swaps
    python mempool_analyzer.py mev                    # MEV opportunity scan
    python mempool_analyzer.py summary                # Overall summary
"""

import argparse
import sys

from rpc_client import RPCClient
from tx_decoder import TransactionDecoder
from gas_analyzer import GasAnalyzer
from mev_detector import MEVDetector
from formatters import (
    format_pending_tx_table,
    format_pending_swaps_table,
    format_mempool_summary,
    format_json,
)


DEFAULT_ETH_PRICE = 3000.0


def cmd_pending(args):
    """Show pending transactions."""
    client = RPCClient(
        rpc_url=args.rpc_url,
        chain=args.chain,
        verbose=args.verbose,
    )

    pending = client.get_pending_transactions(limit=args.limit, allow_mock=args.demo)

    if args.format == "json":
        print(format_json(pending))
    else:
        print(format_pending_tx_table(pending, eth_price=args.eth_price))


def cmd_gas(args):
    """Analyze gas prices."""
    client = RPCClient(
        rpc_url=args.rpc_url,
        chain=args.chain,
        verbose=args.verbose,
    )
    analyzer = GasAnalyzer(verbose=args.verbose)

    # Get gas info
    gas_info = client.get_gas_price()

    # Get pending transactions for distribution analysis
    pending = client.get_pending_transactions(limit=200, allow_mock=args.demo)
    distribution = analyzer.analyze_pending_gas(pending, base_fee=gas_info.base_fee)

    if args.format == "json":
        result = {
            "gas_info": vars(gas_info),
            "distribution": vars(distribution),
        }
        print(format_json(result))
    else:
        print(analyzer.format_distribution(distribution))
        print(analyzer.format_recommendations(base_fee=gas_info.base_fee))


def cmd_swaps(args):
    """Show pending DEX swaps."""
    client = RPCClient(
        rpc_url=args.rpc_url,
        chain=args.chain,
        verbose=args.verbose,
    )
    detector = MEVDetector(verbose=args.verbose)

    pending = client.get_pending_transactions(limit=args.limit, allow_mock=args.demo)
    swaps = detector.detect_pending_swaps(pending, eth_price=args.eth_price)

    if args.format == "json":
        print(format_json(swaps))
    else:
        print(format_pending_swaps_table(swaps))


def cmd_mev(args):
    """Scan for MEV opportunities."""
    client = RPCClient(
        rpc_url=args.rpc_url,
        chain=args.chain,
        verbose=args.verbose,
    )
    detector = MEVDetector(verbose=args.verbose)

    pending = client.get_pending_transactions(limit=args.limit, allow_mock=args.demo)
    results = detector.detect_all_opportunities(pending, eth_price=args.eth_price)

    if args.format == "json":
        # Convert opportunities to serializable format
        serialized = {
            "pending_swaps": results["pending_swaps"],
            "sandwich": [vars(o) for o in results["sandwich"]],
            "arbitrage": [vars(o) for o in results["arbitrage"]],
            "liquidation": [vars(o) for o in results["liquidation"]],
        }
        print(format_json(serialized))
    else:
        print(f"\nPending Swaps Analyzed: {results['pending_swaps']}")

        all_opps = results["sandwich"] + results["arbitrage"] + results["liquidation"]
        print(detector.format_opportunities(all_opps))


def cmd_summary(args):
    """Show mempool summary."""
    client = RPCClient(
        rpc_url=args.rpc_url,
        chain=args.chain,
        verbose=args.verbose,
    )
    detector = MEVDetector(verbose=args.verbose)

    # Gather data
    gas_info = client.get_gas_price()
    pending = client.get_pending_transactions(limit=200, allow_mock=args.demo)
    swaps = detector.detect_pending_swaps(pending, eth_price=args.eth_price)
    results = detector.detect_all_opportunities(pending, eth_price=args.eth_price)

    total_opportunities = len(results["sandwich"]) + len(results["arbitrage"]) + len(results["liquidation"])

    if args.format == "json":
        summary = {
            "pending_count": len(pending),
            "swap_count": len(swaps),
            "opportunity_count": total_opportunities,
            "gas_info": vars(gas_info),
        }
        print(format_json(summary))
    else:
        print(
            format_mempool_summary(
                pending_count=len(pending),
                gas_info=gas_info,
                swap_count=len(swaps),
                opportunities=total_opportunities,
            )
        )


def cmd_watch(args):
    """Watch contract for pending interactions."""
    client = RPCClient(
        rpc_url=args.rpc_url,
        chain=args.chain,
        verbose=args.verbose,
    )
    decoder = TransactionDecoder(verbose=args.verbose)

    contract = args.contract.lower()

    print(f"\nWatching for pending transactions to: {contract}")
    print("=" * 60)

    pending = client.get_pending_transactions(limit=args.limit, allow_mock=args.demo)

    matching = [tx for tx in pending if tx.to_address and tx.to_address.lower() == contract]

    if not matching:
        print("No pending transactions found for this contract.")
        return

    if args.format == "json":
        print(format_json(matching))
    else:
        print(f"Found {len(matching)} pending transactions:\n")
        for tx in matching:
            decoded = decoder.decode_input(tx.input_data, tx.to_address)
            print(f"  {tx.hash[:16]}...")
            print(f"    Method: {decoded.method_name}")
            print(f"    From: {tx.from_address[:16]}...")
            print(f"    Gas: {tx.gas_price / 10**9:.1f} gwei")
            print()


def cmd_status(args):
    """Show connection status."""
    client = RPCClient(
        rpc_url=args.rpc_url,
        chain=args.chain,
        verbose=args.verbose,
    )

    print("\nMEMPOOL ANALYZER STATUS")
    print("=" * 50)
    print(f"Chain: {args.chain}")
    print(f"RPC URL: {client.rpc_url[:50]}...")

    try:
        block = client.get_block_number()
        print(f"Current Block: {block:,}")
        print("Connection: OK")
    except Exception as e:
        print(f"Connection: Error - {e}")

    gas_info = client.get_gas_price()
    print(f"\nGas Price: {gas_info.gas_price / 10**9:.1f} gwei")
    print(f"Base Fee: {gas_info.base_fee / 10**9:.1f} gwei")
    print("=" * 50)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Mempool Analyzer - Monitor pending transactions and MEV",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s pending                       View pending transactions
  %(prog)s gas                           Analyze gas prices
  %(prog)s swaps                         Show pending DEX swaps
  %(prog)s mev                           Scan for MEV opportunities
  %(prog)s summary                       Overall mempool summary
  %(prog)s watch 0x7a250d...             Watch contract for pending txs
  %(prog)s status                        Check connection status
  %(prog)s --demo pending                Use mock data for testing
        """,
    )

    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--format", choices=["table", "json"], default="table", help="Output format")
    parser.add_argument("--rpc-url", help="Custom RPC URL")
    parser.add_argument(
        "--chain",
        default="ethereum",
        choices=["ethereum", "polygon", "arbitrum", "optimism", "base"],
        help="Blockchain network",
    )
    parser.add_argument(
        "--eth-price",
        type=float,
        default=DEFAULT_ETH_PRICE,
        help=f"ETH price for USD conversion (default: {DEFAULT_ETH_PRICE})",
    )
    parser.add_argument("--demo", action="store_true", help="Use mock data when RPC fails (for testing/demo)")

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # pending command
    pending_parser = subparsers.add_parser("pending", help="View pending transactions")
    pending_parser.add_argument("--limit", type=int, default=50, help="Max transactions to show")

    # gas command
    subparsers.add_parser("gas", help="Analyze gas prices")

    # swaps command
    swaps_parser = subparsers.add_parser("swaps", help="Show pending DEX swaps")
    swaps_parser.add_argument("--limit", type=int, default=100, help="Max transactions to analyze")

    # mev command
    mev_parser = subparsers.add_parser("mev", help="Scan for MEV opportunities")
    mev_parser.add_argument("--limit", type=int, default=200, help="Max transactions to analyze")

    # summary command
    subparsers.add_parser("summary", help="Mempool summary")

    # watch command
    watch_parser = subparsers.add_parser("watch", help="Watch contract for pending txs")
    watch_parser.add_argument("contract", help="Contract address to watch")
    watch_parser.add_argument("--limit", type=int, default=100, help="Max transactions to check")

    # status command
    subparsers.add_parser("status", help="Check connection status")

    args = parser.parse_args()

    if not args.command:
        # Default to summary
        args.command = "summary"

    commands = {
        "pending": cmd_pending,
        "gas": cmd_gas,
        "swaps": cmd_swaps,
        "mev": cmd_mev,
        "summary": cmd_summary,
        "watch": cmd_watch,
        "status": cmd_status,
    }

    try:
        commands[args.command](args)
    except KeyboardInterrupt:
        print("\nInterrupted")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
