#!/usr/bin/env python3
"""
Blockchain Explorer CLI

Query and analyze blockchain data across multiple EVM chains.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 1.0.0
License: MIT
"""

import argparse
import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from chain_client import ChainClient, CHAINS, detect_chain
from tx_decoder import TransactionDecoder, identify_protocol
from token_resolver import TokenResolver
from formatters import format_output


def cmd_transaction(args) -> int:
    """Query transaction details.

    Args:
        args: CLI arguments

    Returns:
        Exit code
    """
    chain = args.chain or detect_chain(args.hash)
    client = ChainClient(chain=chain, verbose=args.verbose)
    decoder = TransactionDecoder(verbose=args.verbose)
    resolver = TokenResolver(chain=chain, verbose=args.verbose)

    if args.verbose:
        print(f"Querying transaction on {chain}...")

    tx = client.get_transaction(args.hash)

    if tx.get("error"):
        print(f"Error: {tx['error']}", file=sys.stderr)
        return 1

    # Decode input data
    if tx.get("input") and tx.get("input") != "0x":
        decoded = decoder.decode_input(tx["input"], tx.get("to"))
        tx["decoded_function"] = decoded.get("function", "unknown")
        tx["decoded_params"] = decoded.get("params", [])

        # Identify protocol
        protocol = identify_protocol(tx.get("to"), decoded.get("function", ""))
        if protocol:
            tx["protocol"] = protocol

    # Add USD value
    native_token = resolver.get_native_token(chain)
    if native_token.price_usd and tx.get("value"):
        tx["value_usd"] = tx["value"] * native_token.price_usd

    # Format output
    output = format_output(tx, args.format, "transaction")
    print(output)

    # Show decoded data if detailed
    if args.detailed and tx.get("decoded_function"):
        print(f"\nDecoded: {tx['decoded_function']}")
        if tx.get("protocol"):
            print(f"Protocol: {tx['protocol']}")

    return 0


def cmd_address(args) -> int:
    """Query address details.

    Args:
        args: CLI arguments

    Returns:
        Exit code
    """
    chain = args.chain or "ethereum"
    client = ChainClient(chain=chain, verbose=args.verbose)
    resolver = TokenResolver(chain=chain, verbose=args.verbose)

    if args.verbose:
        print(f"Querying address on {chain}...")

    data = client.get_balance(args.address)

    # Add USD value
    native_token = resolver.get_native_token(chain)
    if native_token.price_usd:
        data["balance_usd"] = data["balance"] * native_token.price_usd

    # Format output
    output = format_output(data, args.format, "address")
    print(output)

    # Show transaction history if requested
    if args.history:
        print("\nFetching transaction history...")
        transactions = client.get_transaction_list(args.address, limit=args.limit)
        tx_output = format_output(transactions, args.format, "tx_list")
        print(tx_output)

    # Show token transfers if requested
    if args.tokens:
        print("\nFetching token transfers...")
        transfers = client.get_token_transfers(args.address, limit=args.limit)
        transfer_output = format_output(transfers, args.format, "transfers")
        print(transfer_output)

    return 0


def cmd_block(args) -> int:
    """Query block details.

    Args:
        args: CLI arguments

    Returns:
        Exit code
    """
    chain = args.chain or "ethereum"
    client = ChainClient(chain=chain, verbose=args.verbose)

    if args.verbose:
        print(f"Querying block on {chain}...")

    block_num = None if args.number == "latest" else int(args.number)
    block = client.get_block(block_num)

    if block.get("error"):
        print(f"Error: {block['error']}", file=sys.stderr)
        return 1

    output = format_output(block, args.format, "block")
    print(output)

    return 0


def cmd_token(args) -> int:
    """Query token balance.

    Args:
        args: CLI arguments

    Returns:
        Exit code
    """
    chain = args.chain or "ethereum"
    client = ChainClient(chain=chain, verbose=args.verbose)
    resolver = TokenResolver(chain=chain, verbose=args.verbose)

    if args.verbose:
        print(f"Querying token balance on {chain}...")

    # Get token balance
    data = client.get_token_balance(args.address, args.contract)

    # Resolve token info
    token = resolver.resolve(args.contract, chain)
    data["token_symbol"] = token.symbol
    data["token_name"] = token.name

    if token.price_usd:
        data["balance_usd"] = data["balance"] * token.price_usd

    # Format output
    if args.format == "json":
        import json

        print(json.dumps(data, indent=2, default=str))
    else:
        print("\nToken Balance")
        print("=" * 60)
        print(f"Address:  {data['address']}")
        print(f"Token:    {data['token_name']} ({data['token_symbol']})")
        print(f"Contract: {data['token_contract']}")
        print(f"Chain:    {data['chain']}")
        print(f"Balance:  {data['balance']:.{min(data['decimals'], 8)}f} {data['token_symbol']}")
        if data.get("balance_usd"):
            print(f"Value:    ${data['balance_usd']:.2f}")

    return 0


def cmd_history(args) -> int:
    """Query transaction history.

    Args:
        args: CLI arguments

    Returns:
        Exit code
    """
    chain = args.chain or "ethereum"
    client = ChainClient(chain=chain, verbose=args.verbose)

    if args.verbose:
        print(f"Querying transaction history on {chain}...")

    transactions = client.get_transaction_list(args.address, limit=args.limit)

    if not transactions:
        print("No transactions found.")
        return 0

    output = format_output(transactions, args.format, "tx_list")
    print(output)

    return 0


def cmd_transfers(args) -> int:
    """Query token transfers.

    Args:
        args: CLI arguments

    Returns:
        Exit code
    """
    chain = args.chain or "ethereum"
    client = ChainClient(chain=chain, verbose=args.verbose)

    if args.verbose:
        print(f"Querying token transfers on {chain}...")

    transfers = client.get_token_transfers(args.address, contract=args.contract, limit=args.limit)

    if not transfers:
        print("No token transfers found.")
        return 0

    output = format_output(transfers, args.format, "transfers")
    print(output)

    return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Query and analyze blockchain data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s tx 0x1234...                    # Query transaction
  %(prog)s address 0xabcd...               # Query address balance
  %(prog)s address 0xabcd... --history     # Address with tx history
  %(prog)s block latest                    # Query latest block
  %(prog)s block 18500000 --chain polygon  # Query Polygon block
  %(prog)s token 0xaddr 0xtoken            # Query token balance
  %(prog)s history 0xaddr --limit 50       # Transaction history
  %(prog)s transfers 0xaddr                # Token transfers

Supported chains: ethereum, polygon, bsc, arbitrum, optimism, base, avalanche
        """,
    )

    parser.add_argument("--chain", "-c", choices=list(CHAINS.keys()), help="Blockchain network (default: ethereum)")
    parser.add_argument("--format", "-f", choices=["table", "json", "csv"], default="table", help="Output format")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--version", action="version", version="%(prog)s 1.0.0")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Transaction command
    tx_parser = subparsers.add_parser("tx", help="Query transaction")
    tx_parser.add_argument("hash", help="Transaction hash")
    tx_parser.add_argument("--detailed", "-d", action="store_true", help="Show decoded data")
    tx_parser.set_defaults(func=cmd_transaction)

    # Address command
    addr_parser = subparsers.add_parser("address", help="Query address")
    addr_parser.add_argument("address", help="Wallet address")
    addr_parser.add_argument("--history", "-H", action="store_true", help="Include transaction history")
    addr_parser.add_argument("--tokens", "-t", action="store_true", help="Include token transfers")
    addr_parser.add_argument("--limit", "-l", type=int, default=20, help="History limit")
    addr_parser.set_defaults(func=cmd_address)

    # Block command
    block_parser = subparsers.add_parser("block", help="Query block")
    block_parser.add_argument("number", help="Block number or 'latest'")
    block_parser.set_defaults(func=cmd_block)

    # Token command
    token_parser = subparsers.add_parser("token", help="Query token balance")
    token_parser.add_argument("address", help="Wallet address")
    token_parser.add_argument("contract", help="Token contract address")
    token_parser.set_defaults(func=cmd_token)

    # History command
    history_parser = subparsers.add_parser("history", help="Transaction history")
    history_parser.add_argument("address", help="Wallet address")
    history_parser.add_argument("--limit", "-l", type=int, default=50, help="Max transactions")
    history_parser.set_defaults(func=cmd_history)

    # Transfers command
    transfers_parser = subparsers.add_parser("transfers", help="Token transfers")
    transfers_parser.add_argument("address", help="Wallet address")
    transfers_parser.add_argument("--contract", help="Filter by token contract")
    transfers_parser.add_argument("--limit", "-l", type=int, default=50, help="Max transfers")
    transfers_parser.set_defaults(func=cmd_transfers)

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
