#!/usr/bin/env python3
"""
Token Launch Tracker

Track new token launches across DEXes with risk analysis.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 1.0.0
License: MIT
"""

import argparse
import json
import sys
from datetime import datetime
from typing import Dict, List

# Local imports
from dex_sources import (
    get_chain_config,
    get_dex_factories,
    CHAINS,
)
from event_monitor import EventMonitor, PairCreated
from token_analyzer import TokenAnalyzer, TokenInfo, ContractAnalysis
from formatters import (
    format_new_pairs_table,
    format_launch_detail,
    format_chain_summary,
    format_dex_summary,
    format_risk_badge,
)


def cmd_recent(args) -> int:
    """Show recently launched tokens."""
    print(f"\nScanning {args.chain.upper()} for new launches...")
    print(f"Looking back {args.hours} hours")
    if args.dex:
        print(f"Filtering by DEX: {args.dex}")
    print()

    try:
        monitor = EventMonitor(chain=args.chain, rpc_url=args.rpc_url, verbose=args.verbose)

        pairs = monitor.get_recent_pairs(hours=args.hours, dex=args.dex)

        if not pairs:
            print("No new pairs found in the specified timeframe.")
            return 0

        # Limit results
        pairs = pairs[: args.limit]

        # Enrich with token info and analysis if requested
        token_infos: Dict[str, TokenInfo] = {}
        analyses: Dict[str, ContractAnalysis] = {}

        if args.analyze:
            analyzer = TokenAnalyzer(chain=args.chain, rpc_url=args.rpc_url, verbose=args.verbose)

            print(f"Analyzing {len(pairs)} pairs...")
            for i, pair in enumerate(pairs):
                new_token = monitor.identify_new_token(pair)

                # Get token info
                info = analyzer.get_token_info(new_token)
                if info:
                    token_infos[new_token] = info

                # Analyze contract
                if not args.skip_analysis:
                    analysis = analyzer.analyze_contract(new_token)
                    analyses[new_token] = analysis

                if args.verbose:
                    print(f"  [{i + 1}/{len(pairs)}] {info.symbol if info else 'Unknown'}")

        # Output
        if args.format == "json":
            output = []
            for pair in pairs:
                new_token = monitor.identify_new_token(pair)
                entry = {
                    "pair": vars(pair),
                    "token_info": vars(token_infos.get(new_token)) if new_token in token_infos else None,
                    "analysis": vars(analyses.get(new_token)) if new_token in analyses else None,
                }
                output.append(entry)
            print(json.dumps(output, indent=2, default=str))
        else:
            print(format_new_pairs_table(pairs, token_infos, analyses))

        return 0

    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


def cmd_detail(args) -> int:
    """Show detailed launch information."""
    print(f"\nFetching details for {args.address[:20]}...")

    try:
        EventMonitor(chain=args.chain, rpc_url=args.rpc_url, verbose=args.verbose)

        analyzer = TokenAnalyzer(
            chain=args.chain, rpc_url=args.rpc_url, etherscan_api_key=args.etherscan_key, verbose=args.verbose
        )

        # Get token info
        token_info = analyzer.get_token_info(args.address)

        # Analyze contract
        analysis = analyzer.analyze_contract(args.address)

        # Get chain config
        chain_config = get_chain_config(args.chain)

        # Create a mock pair for display
        mock_pair = PairCreated(
            block_number=0,
            tx_hash="",
            timestamp=int(datetime.now().timestamp()),
            pair_address=args.pair or "Unknown",
            token0=args.address,
            token1="",
            dex=args.dex or "Unknown",
            chain=args.chain,
            factory_address="",
        )

        if args.format == "json":
            output = {
                "token_info": vars(token_info) if token_info else None,
                "analysis": vars(analysis),
                "risk_summary": analyzer.get_risk_summary(analysis),
            }
            print(json.dumps(output, indent=2, default=str))
        else:
            print(format_launch_detail(mock_pair, token_info, analysis, chain_config))

        return 0

    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


def cmd_risk(args) -> int:
    """Analyze token contract for risks."""
    print(f"\nAnalyzing contract: {args.address[:20]}...")

    try:
        analyzer = TokenAnalyzer(
            chain=args.chain, rpc_url=args.rpc_url, etherscan_api_key=args.etherscan_key, verbose=args.verbose
        )

        analysis = analyzer.analyze_contract(args.address)

        if args.format == "json":
            output = {
                "address": args.address,
                "risk_score": analysis.risk_score,
                "risk_level": analyzer.get_risk_summary(analysis),
                "is_proxy": analysis.is_proxy,
                "ownership_renounced": analysis.ownership_renounced,
                "bytecode_size": analysis.bytecode_size,
                "indicators": [vars(ind) for ind in analysis.indicators],
            }
            print(json.dumps(output, indent=2, default=str))
        else:
            print()
            print("RISK ANALYSIS")
            print("=" * 60)
            print(f"Address:      {args.address}")
            print(f"Chain:        {args.chain.upper()}")
            print()
            print(f"Risk Score:   {analysis.risk_score}/100 {format_risk_badge(analysis.risk_score)}")
            print(f"Risk Level:   {analyzer.get_risk_summary(analysis)}")
            print()
            print("CONTRACT INFO")
            print("-" * 60)
            print(f"Bytecode:     {analysis.bytecode_size:,} bytes")
            print(f"Is Proxy:     {'Yes' if analysis.is_proxy else 'No'}")
            print(f"Ownership:    {'Renounced' if analysis.ownership_renounced else 'Active'}")
            print()
            print("RISK INDICATORS")
            print("-" * 60)

            if analysis.indicators:
                for ind in sorted(
                    analysis.indicators, key=lambda x: {"high": 0, "medium": 1, "low": 2, "info": 3}.get(x.severity, 4)
                ):
                    severity_marker = {
                        "high": "!!",
                        "medium": "! ",
                        "low": ". ",
                        "info": "  ",
                    }.get(ind.severity, "  ")
                    print(f"  {severity_marker} [{ind.severity.upper():6}] {ind.name}")
                    print(f"              {ind.description}")
            else:
                print("  No risk indicators detected")

            print()
            print("=" * 60)

        return 0

    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


def cmd_summary(args) -> int:
    """Show launch summary statistics."""
    chains = args.chains.split(",") if args.chains else list(CHAINS.keys())

    print("\nGenerating launch summary...")
    print(f"Chains: {', '.join(chains)}")
    print(f"Period: Last {args.hours} hours")
    print()

    try:
        pairs_by_chain: Dict[str, int] = {}
        pairs_by_dex: Dict[str, int] = {}
        all_pairs: List[PairCreated] = []

        for chain in chains:
            if chain not in CHAINS:
                print(f"Warning: Skipping unsupported chain: {chain}")
                continue

            if args.verbose:
                print(f"Scanning {chain}...")

            try:
                monitor = EventMonitor(chain=chain, verbose=args.verbose)
                pairs = monitor.get_recent_pairs(hours=args.hours)

                pairs_by_chain[chain] = len(pairs)
                all_pairs.extend(pairs)

                for pair in pairs:
                    dex_key = f"{chain}:{pair.dex}"
                    pairs_by_dex[dex_key] = pairs_by_dex.get(dex_key, 0) + 1

            except Exception as e:
                print(f"Error scanning {chain}: {e}")
                pairs_by_chain[chain] = 0

        if args.format == "json":
            output = {
                "period_hours": args.hours,
                "chains": chains,
                "by_chain": pairs_by_chain,
                "by_dex": pairs_by_dex,
                "total": sum(pairs_by_chain.values()),
            }
            print(json.dumps(output, indent=2))
        else:
            print(format_chain_summary(pairs_by_chain))
            print(format_dex_summary(pairs_by_dex))

        return 0

    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


def cmd_dexes(args) -> int:
    """List supported DEXes."""
    chain = args.chain

    if chain:
        if chain not in CHAINS:
            print(f"Error: Unsupported chain: {chain}")
            print(f"Supported chains: {', '.join(CHAINS.keys())}")
            return 1

        factories = get_dex_factories(chain)

        if args.format == "json":
            output = {
                "chain": chain,
                "dexes": [
                    {
                        "name": f.name,
                        "address": f.address,
                        "version": f.version,
                    }
                    for f in factories.values()
                ],
            }
            print(json.dumps(output, indent=2))
        else:
            print()
            print(f"SUPPORTED DEXES ON {chain.upper()}")
            print("=" * 60)
            for key, factory in factories.items():
                print(f"  {factory.name:<25} ({factory.version})")
                print(f"    Factory: {factory.address}")
            print("=" * 60)
    else:
        # List all
        if args.format == "json":
            output = {}
            for chain_id in CHAINS:
                factories = get_dex_factories(chain_id)
                output[chain_id] = [
                    {"name": f.name, "address": f.address, "version": f.version} for f in factories.values()
                ]
            print(json.dumps(output, indent=2))
        else:
            print()
            print("SUPPORTED DEXES BY CHAIN")
            print("=" * 60)
            for chain_id, config in CHAINS.items():
                factories = get_dex_factories(chain_id)
                print(f"\n{config.name} ({chain_id})")
                print("-" * 40)
                for factory in factories.values():
                    print(f"  {factory.name:<25} {factory.version}")
            print()
            print("=" * 60)

    return 0


def cmd_chains(args) -> int:
    """List supported chains."""
    if args.format == "json":
        output = {
            chain_id: {
                "name": config.name,
                "chain_id": config.chain_id,
                "native_symbol": config.native_symbol,
                "block_time": config.block_time,
                "explorer_url": config.explorer_url,
            }
            for chain_id, config in CHAINS.items()
        }
        print(json.dumps(output, indent=2))
    else:
        print()
        print("SUPPORTED CHAINS")
        print("=" * 70)
        print(f"{'Chain':<15} {'Name':<20} {'ID':<10} {'Symbol':<8} {'Block':<8}")
        print("-" * 70)
        for chain_id, config in CHAINS.items():
            print(
                f"{chain_id:<15} {config.name:<20} {config.chain_id:<10} {config.native_symbol:<8} {config.block_time}s"
            )
        print("=" * 70)

    return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Track new token launches across DEXes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show recent launches on Ethereum
  %(prog)s recent --chain ethereum --hours 24

  # Get detailed info for a specific token
  %(prog)s detail --address 0x... --chain ethereum

  # Analyze token risk
  %(prog)s risk --address 0x... --chain base

  # Show launch summary across all chains
  %(prog)s summary --hours 24

  # List supported DEXes
  %(prog)s dexes --chain bsc
        """,
    )

    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument(
        "-f", "--format", choices=["text", "json"], default="text", help="Output format (default: text)"
    )

    subparsers = parser.add_subparsers(dest="command", help="Command")

    # recent command
    recent_parser = subparsers.add_parser("recent", help="Show recently launched tokens")
    recent_parser.add_argument("--chain", "-c", default="ethereum", help="Chain to scan (default: ethereum)")
    recent_parser.add_argument("--hours", "-H", type=int, default=24, help="Hours to look back (default: 24)")
    recent_parser.add_argument("--dex", "-d", help="Filter by DEX name")
    recent_parser.add_argument("--limit", "-l", type=int, default=50, help="Maximum results (default: 50)")
    recent_parser.add_argument("--analyze", "-a", action="store_true", help="Include token analysis")
    recent_parser.add_argument("--skip-analysis", action="store_true", help="Skip contract analysis (faster)")
    recent_parser.add_argument("--rpc-url", help="Custom RPC URL")
    recent_parser.set_defaults(func=cmd_recent)

    # detail command
    detail_parser = subparsers.add_parser("detail", help="Show detailed launch information")
    detail_parser.add_argument("--address", "-a", required=True, help="Token contract address")
    detail_parser.add_argument("--chain", "-c", default="ethereum", help="Chain (default: ethereum)")
    detail_parser.add_argument("--pair", "-p", help="Pair address (optional)")
    detail_parser.add_argument("--dex", "-d", help="DEX name (optional)")
    detail_parser.add_argument("--etherscan-key", help="Etherscan API key for verification check")
    detail_parser.add_argument("--rpc-url", help="Custom RPC URL")
    detail_parser.set_defaults(func=cmd_detail)

    # risk command
    risk_parser = subparsers.add_parser("risk", help="Analyze token contract for risks")
    risk_parser.add_argument("--address", "-a", required=True, help="Token contract address")
    risk_parser.add_argument("--chain", "-c", default="ethereum", help="Chain (default: ethereum)")
    risk_parser.add_argument("--etherscan-key", help="Etherscan API key for verification check")
    risk_parser.add_argument("--rpc-url", help="Custom RPC URL")
    risk_parser.set_defaults(func=cmd_risk)

    # summary command
    summary_parser = subparsers.add_parser("summary", help="Show launch summary statistics")
    summary_parser.add_argument("--chains", help="Comma-separated chains (default: all)")
    summary_parser.add_argument("--hours", "-H", type=int, default=24, help="Hours to look back (default: 24)")
    summary_parser.set_defaults(func=cmd_summary)

    # dexes command
    dexes_parser = subparsers.add_parser("dexes", help="List supported DEXes")
    dexes_parser.add_argument("--chain", "-c", help="Show DEXes for specific chain")
    dexes_parser.set_defaults(func=cmd_dexes)

    # chains command
    chains_parser = subparsers.add_parser("chains", help="List supported chains")
    chains_parser.set_defaults(func=cmd_chains)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
