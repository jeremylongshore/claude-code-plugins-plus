#!/usr/bin/env python3
"""
Whale Alert Monitor CLI

Track large cryptocurrency transactions and whale wallet movements.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 1.0.0
License: MIT

Usage:
    python whale_monitor.py recent                    # Recent whale transactions
    python whale_monitor.py recent --chain ethereum   # Filter by chain
    python whale_monitor.py recent --min-value 10000000  # $10M+ only
    python whale_monitor.py watchlist                 # Show watchlist
    python whale_monitor.py watch <address> --name "Whale 1"  # Add to watchlist
    python whale_monitor.py flows                     # Exchange inflows/outflows
    python whale_monitor.py flows --chain ethereum    # Filter flows by chain
"""

import argparse
import sys

from whale_api import WhaleAlertClient
from wallet_labels import WalletLabeler
from formatters import (
    format_whale_table,
    format_whale_alert,
    format_exchange_flow,
    format_watchlist,
    format_json,
)


def cmd_recent(args):
    """Show recent whale transactions."""
    client = WhaleAlertClient(verbose=args.verbose)
    labeler = WalletLabeler()

    transactions = client.get_transactions(
        blockchain=args.chain,
        min_value=args.min_value,
        limit=args.limit,
    )

    # Enrich with labels
    for tx in transactions:
        if not tx.from_owner:
            label = labeler.label_wallet(tx.from_address, tx.blockchain)
            tx.from_owner = label.name if label.entity_type != "unknown" else None
            tx.from_owner_type = label.entity_type
        if not tx.to_owner:
            label = labeler.label_wallet(tx.to_address, tx.blockchain)
            tx.to_owner = label.name if label.entity_type != "unknown" else None
            tx.to_owner_type = label.entity_type

    if args.format == "json":
        print(format_json(transactions))
    elif args.format == "alert":
        for tx in transactions:
            print(format_whale_alert(tx))
            print()
    else:
        print(format_whale_table(transactions, show_addresses=args.addresses))


def cmd_flows(args):
    """Analyze exchange inflows/outflows."""
    client = WhaleAlertClient(verbose=args.verbose)
    labeler = WalletLabeler()

    transactions = client.get_transactions(
        blockchain=args.chain,
        min_value=args.min_value,
        limit=200,
    )

    # Separate inflows and outflows
    inflows = []
    outflows = []

    for tx in transactions:
        # Check destination
        to_label = labeler.label_wallet(tx.to_address, tx.blockchain)
        from_label = labeler.label_wallet(tx.from_address, tx.blockchain)

        if to_label.entity_type == "exchange":
            inflows.append(
                {
                    "tx_hash": tx.tx_hash,
                    "amount": tx.amount,
                    "amount_usd": tx.amount_usd,
                    "symbol": tx.symbol,
                    "exchange": to_label.name,
                    "from": from_label.name if from_label.entity_type != "unknown" else tx.from_address[:16],
                }
            )
        elif from_label.entity_type == "exchange":
            outflows.append(
                {
                    "tx_hash": tx.tx_hash,
                    "amount": tx.amount,
                    "amount_usd": tx.amount_usd,
                    "symbol": tx.symbol,
                    "exchange": from_label.name,
                    "to": to_label.name if to_label.entity_type != "unknown" else tx.to_address[:16],
                }
            )

    if args.format == "json":
        print(format_json({"inflows": inflows, "outflows": outflows}))
    else:
        print(format_exchange_flow(inflows, outflows))

        if inflows:
            print("\nTop Inflows (Deposits to Exchanges):")
            print("-" * 60)
            for flow in sorted(inflows, key=lambda x: x["amount_usd"], reverse=True)[:5]:
                print(f"  {flow['symbol']}: ${flow['amount_usd']:,.0f} → {flow['exchange']}")

        if outflows:
            print("\nTop Outflows (Withdrawals from Exchanges):")
            print("-" * 60)
            for flow in sorted(outflows, key=lambda x: x["amount_usd"], reverse=True)[:5]:
                print(f"  {flow['symbol']}: ${flow['amount_usd']:,.0f} ← {flow['exchange']}")


def cmd_watchlist(args):
    """Show or manage watchlist."""
    labeler = WalletLabeler()
    wallets = labeler.get_watchlist()
    print(format_watchlist(wallets))


def cmd_watch(args):
    """Add wallet to watchlist."""
    labeler = WalletLabeler()
    label = labeler.add_to_watchlist(
        address=args.address,
        name=args.name,
        chain=args.chain,
        notes=args.notes,
    )
    print(f"✓ Added to watchlist: {label.name} ({label.address[:16]}...)")


def cmd_unwatch(args):
    """Remove wallet from watchlist."""
    labeler = WalletLabeler()
    if labeler.remove_from_watchlist(args.address):
        print(f"✓ Removed from watchlist: {args.address[:16]}...")
    else:
        print(f"✗ Address not found in watchlist: {args.address[:16]}...")


def cmd_track(args):
    """Track a specific wallet's recent activity."""
    client = WhaleAlertClient(verbose=args.verbose)
    labeler = WalletLabeler()

    # Get label info
    label = labeler.label_wallet(args.address, args.chain)

    print(f"\nTracking: {label.name}")
    print(f"Address: {args.address}")
    print(f"Type: {label.entity_type}")
    print(f"Chain: {args.chain}")
    print("-" * 60)

    # Get recent transactions
    transactions = client.get_transactions(
        blockchain=args.chain,
        min_value=args.min_value,
        limit=100,
    )

    # Filter for this address
    addr_lower = args.address.lower()
    matching = [
        tx for tx in transactions if tx.from_address.lower() == addr_lower or tx.to_address.lower() == addr_lower
    ]

    if not matching:
        print("No recent transactions found for this address.")
        return

    if args.format == "json":
        print(format_json(matching))
    else:
        print(format_whale_table(matching))


def cmd_labels(args):
    """Search or list known wallet labels."""
    labeler = WalletLabeler()

    if args.query:
        results = labeler.search_labels(args.query)
        if not results:
            print(f"No labels found matching: {args.query}")
            return

        print(f"\nLabels matching '{args.query}':")
        print("-" * 60)
        for label in results:
            print(f"  {label.name:<25} {label.entity_type:<12} {label.chain}")
    elif args.type:
        results = labeler.get_by_type(args.type)
        if not results:
            print(f"No labels found for type: {args.type}")
            return

        print(f"\n{args.type.upper()} wallets:")
        print("-" * 60)
        for label in results[:20]:
            print(f"  {label.name:<30} {label.address[:20]}...")
    else:
        # Show summary
        print("\nKnown Wallet Labels:")
        print("-" * 40)
        for entity_type in ["exchange", "protocol", "fund", "bridge"]:
            count = len(labeler.get_by_type(entity_type))
            print(f"  {entity_type.capitalize()}: {count}")
        print(f"  Watchlist: {len(labeler.get_watchlist())}")


def cmd_status(args):
    """Show API status and configuration."""
    client = WhaleAlertClient(verbose=args.verbose)
    status = client.get_status()

    print("\nWhale Alert Monitor Status")
    print("=" * 40)
    print(f"API Status: {status.get('status', 'unknown')}")

    if status.get("message"):
        print(f"Message: {status['message']}")

    if status.get("blockchains"):
        print(f"Supported Chains: {', '.join(status['blockchains'])}")

    if status.get("rate_limit_remaining"):
        print(f"Rate Limit Remaining: {status['rate_limit_remaining']}")

    print("\nConfiguration:")
    print("  Cache TTL: 60 seconds")
    print("  Default Min Value: $500,000")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Whale Alert Monitor - Track large crypto transactions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s recent                          Show recent whale transactions
  %(prog)s recent --chain ethereum         Filter by blockchain
  %(prog)s recent --min-value 10000000     $10M+ transactions only
  %(prog)s flows                           Exchange inflow/outflow analysis
  %(prog)s watchlist                       Show your watchlist
  %(prog)s watch 0x123... --name "Whale1"  Add wallet to watchlist
  %(prog)s track 0x123...                  Track specific wallet
  %(prog)s labels --type exchange          List known exchange wallets
  %(prog)s status                          Show API status
        """,
    )

    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--format", choices=["table", "json", "alert"], default="table", help="Output format")

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # recent command
    recent_parser = subparsers.add_parser("recent", help="Show recent whale transactions")
    recent_parser.add_argument("--chain", help="Filter by blockchain (ethereum, bitcoin, etc.)")
    recent_parser.add_argument("--min-value", type=int, default=500000, help="Minimum USD value (default: 500000)")
    recent_parser.add_argument("--limit", type=int, default=20, help="Max transactions to show (default: 20)")
    recent_parser.add_argument("--addresses", action="store_true", help="Show full addresses instead of labels")

    # flows command
    flows_parser = subparsers.add_parser("flows", help="Analyze exchange inflows/outflows")
    flows_parser.add_argument("--chain", help="Filter by blockchain")
    flows_parser.add_argument("--min-value", type=int, default=500000, help="Minimum USD value")

    # watchlist command
    subparsers.add_parser("watchlist", help="Show your watchlist")

    # watch command
    watch_parser = subparsers.add_parser("watch", help="Add wallet to watchlist")
    watch_parser.add_argument("address", help="Wallet address to watch")
    watch_parser.add_argument("--name", required=True, help="Display name for wallet")
    watch_parser.add_argument("--chain", default="ethereum", help="Blockchain network")
    watch_parser.add_argument("--notes", help="Optional notes")

    # unwatch command
    unwatch_parser = subparsers.add_parser("unwatch", help="Remove wallet from watchlist")
    unwatch_parser.add_argument("address", help="Wallet address to remove")

    # track command
    track_parser = subparsers.add_parser("track", help="Track specific wallet activity")
    track_parser.add_argument("address", help="Wallet address to track")
    track_parser.add_argument("--chain", default="ethereum", help="Blockchain network")
    track_parser.add_argument("--min-value", type=int, default=100000, help="Minimum USD value")

    # labels command
    labels_parser = subparsers.add_parser("labels", help="Search or list known wallet labels")
    labels_parser.add_argument("--query", help="Search query")
    labels_parser.add_argument(
        "--type", choices=["exchange", "protocol", "fund", "bridge"], help="Filter by entity type"
    )

    # status command
    subparsers.add_parser("status", help="Show API status")

    args = parser.parse_args()

    if not args.command:
        # Default to recent
        args.command = "recent"
        args.chain = None
        args.min_value = 500000
        args.limit = 20
        args.addresses = False

    commands = {
        "recent": cmd_recent,
        "flows": cmd_flows,
        "watchlist": cmd_watchlist,
        "watch": cmd_watch,
        "unwatch": cmd_unwatch,
        "track": cmd_track,
        "labels": cmd_labels,
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
