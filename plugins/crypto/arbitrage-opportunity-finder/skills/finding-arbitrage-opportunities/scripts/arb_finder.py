#!/usr/bin/env python3
"""
Arbitrage Opportunity Finder - Main CLI Entry Point.

Scans for arbitrage opportunities across exchanges with:
- Direct spread detection (CEX-to-CEX, DEX-to-DEX)
- Triangular arbitrage path finding
- Profit calculation after all fees
- Real-time monitoring

Usage:
    python arb_finder.py scan ETH USDC
    python arb_finder.py scan ETH USDC --exchanges binance,coinbase,kraken
    python arb_finder.py triangular binance --min-profit 0.5
    python arb_finder.py monitor ETH USDC --threshold 0.5 --interval 5
    python arb_finder.py calc --buy-exchange binance --sell-exchange coinbase --pair ETH/USDC --amount 10
"""

import argparse
import sys
import time
from decimal import Decimal, InvalidOperation

from price_fetcher import PriceFetcher, ExchangeType
from opportunity_scanner import OpportunityScanner
from triangular_finder import TriangularFinder
from profit_calculator import ProfitCalculator
from formatters import ConsoleFormatter, JSONFormatter


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Arbitrage Opportunity Finder",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scan for ETH/USDC arbitrage across all exchanges
  %(prog)s scan ETH USDC

  # Scan specific exchanges
  %(prog)s scan ETH USDC --exchanges binance,coinbase,kraken

  # Scan DEX only
  %(prog)s scan ETH USDC --dex-only

  # Find triangular arbitrage on Binance
  %(prog)s triangular binance --min-profit 0.1

  # Monitor for opportunities with alerts
  %(prog)s monitor ETH USDC --threshold 0.3 --interval 5

  # Calculate profit for specific trade
  %(prog)s calc --buy-exchange binance --sell-exchange coinbase --pair ETH/USDC --amount 10

Supported Exchanges:
  CEX: binance, coinbase, kraken, kucoin, okx
  DEX: uniswap, sushiswap, curve, balancer

EDUCATIONAL DISCLAIMER:
  This tool is for analysis and learning only.
  Arbitrage involves risks. Always verify data before trading.
""",
    )

    subparsers = parser.add_subparsers(dest="command", help="Command")

    # Scan subcommand
    scan_parser = subparsers.add_parser("scan", help="Scan for direct arbitrage opportunities")
    scan_parser.add_argument("base", help="Base token (e.g., ETH)")
    scan_parser.add_argument("quote", help="Quote token (e.g., USDC)")
    scan_parser.add_argument(
        "--exchanges",
        type=str,
        help="Comma-separated list of exchanges",
    )
    scan_parser.add_argument(
        "--cex-only",
        action="store_true",
        help="Only scan centralized exchanges",
    )
    scan_parser.add_argument(
        "--dex-only",
        action="store_true",
        help="Only scan decentralized exchanges",
    )
    scan_parser.add_argument(
        "--min-profit",
        type=float,
        default=0.0,
        help="Minimum profit percentage to show (default: 0.0)",
    )

    # Triangular subcommand
    tri_parser = subparsers.add_parser("triangular", help="Find triangular arbitrage paths")
    tri_parser.add_argument("exchange", help="Exchange to analyze")
    tri_parser.add_argument(
        "--min-profit",
        type=float,
        default=0.1,
        help="Minimum profit percentage (default: 0.1)",
    )

    # Monitor subcommand
    mon_parser = subparsers.add_parser("monitor", help="Real-time opportunity monitoring")
    mon_parser.add_argument("base", help="Base token (e.g., ETH)")
    mon_parser.add_argument("quote", help="Quote token (e.g., USDC)")
    mon_parser.add_argument(
        "--threshold",
        type=float,
        default=0.3,
        help="Alert threshold percentage (default: 0.3)",
    )
    mon_parser.add_argument(
        "--interval",
        type=int,
        default=5,
        help="Polling interval in seconds (default: 5)",
    )
    mon_parser.add_argument(
        "--exchanges",
        type=str,
        help="Comma-separated list of exchanges",
    )

    # Calc subcommand
    calc_parser = subparsers.add_parser("calc", help="Calculate profit for specific trade")
    calc_parser.add_argument(
        "--buy-exchange",
        required=True,
        help="Exchange to buy on",
    )
    calc_parser.add_argument(
        "--sell-exchange",
        required=True,
        help="Exchange to sell on",
    )
    calc_parser.add_argument(
        "--pair",
        required=True,
        help="Trading pair (e.g., ETH/USDC)",
    )
    calc_parser.add_argument(
        "--amount",
        type=str,
        required=True,
        help="Trade amount in base currency",
    )
    calc_parser.add_argument(
        "--buy-price",
        type=str,
        help="Buy price (fetched if not provided)",
    )
    calc_parser.add_argument(
        "--sell-price",
        type=str,
        help="Sell price (fetched if not provided)",
    )

    # Global options for all subcommands
    for sub in [scan_parser, tri_parser, mon_parser, calc_parser]:
        sub.add_argument(
            "--output",
            choices=["console", "json"],
            default="console",
            help="Output format (default: console)",
        )
        sub.add_argument(
            "--eth-price",
            type=float,
            default=2500.0,
            help="ETH price in USD (default: 2500)",
        )
        sub.add_argument(
            "--gas-price",
            type=float,
            default=30.0,
            help="Gas price in gwei (default: 30)",
        )

    return parser.parse_args()


def run_scan(args: argparse.Namespace) -> int:
    """Run direct arbitrage scan."""
    # Parse exchanges
    exchanges = None
    if args.exchanges:
        exchanges = [e.strip() for e in args.exchanges.split(",")]

    exchange_type = None
    if args.cex_only:
        exchange_type = ExchangeType.CEX
    elif args.dex_only:
        exchange_type = ExchangeType.DEX

    # Create scanner
    scanner = OpportunityScanner(
        min_profit_pct=args.min_profit,
        gas_price_gwei=args.gas_price,
        eth_price_usd=args.eth_price,
    )

    # Run scan
    result = scanner.scan(
        args.base.upper(),
        args.quote.upper(),
        exchanges,
        exchange_type,
    )

    # Format output
    if args.output == "json":
        fmt = JSONFormatter()
        print(fmt.format_scan_result(result))
    else:
        fmt = ConsoleFormatter()
        print(fmt.format_scan_result(result))

    # Return code based on findings
    return 0 if result.opportunities else 1


def run_triangular(args: argparse.Namespace) -> int:
    """Run triangular arbitrage finder."""
    finder = TriangularFinder(min_profit_pct=args.min_profit)

    # Find opportunities
    paths = finder.find_opportunities(args.exchange)

    # Format output
    if args.output == "json":
        fmt = JSONFormatter()
        print(fmt.format_triangular_results(paths))
    else:
        fmt = ConsoleFormatter()
        print(fmt.format_triangular_results(paths))

    return 0 if paths else 1


def run_monitor(args: argparse.Namespace) -> int:
    """Run real-time monitoring."""
    # Parse exchanges
    exchanges = None
    if args.exchanges:
        exchanges = [e.strip() for e in args.exchanges.split(",")]

    scanner = OpportunityScanner(
        min_profit_pct=args.threshold,
        gas_price_gwei=args.gas_price,
        eth_price_usd=args.eth_price,
    )

    console = ConsoleFormatter()

    print(f"Monitoring {args.base}/{args.quote} for spreads > {args.threshold}%")
    print(f"Interval: {args.interval}s | Press Ctrl+C to stop\n")

    iteration = 0
    try:
        while True:
            iteration += 1
            result = scanner.scan(
                args.base.upper(),
                args.quote.upper(),
                exchanges,
            )

            if result.best_opportunity:
                best = result.best_opportunity
                if best.net_spread_pct >= args.threshold:
                    print(console.format_alert(best))
                    print()
                else:
                    print(
                        f"[{iteration}] Best: {best.buy_exchange} → {best.sell_exchange} "
                        f"({best.net_spread_pct:+.3f}%) - below threshold"
                    )
            else:
                print(f"[{iteration}] No opportunities found")

            time.sleep(args.interval)

    except KeyboardInterrupt:
        print("\nMonitoring stopped")
        return 0


def run_calc(args: argparse.Namespace) -> int:
    """Run profit calculation."""
    try:
        amount = Decimal(args.amount)
    except InvalidOperation:
        print(f"Error: Invalid amount '{args.amount}'", file=sys.stderr)
        return 1

    # Parse pair
    if "/" in args.pair:
        base, quote = args.pair.split("/")
    else:
        print(f"Error: Invalid pair format '{args.pair}' (use BASE/QUOTE)", file=sys.stderr)
        return 1

    # Get prices if not provided
    fetcher = PriceFetcher(use_mock=True)

    if args.buy_price:
        buy_price = Decimal(args.buy_price)
    else:
        quote_obj = fetcher.fetch_all_prices_sync(base, quote, [args.buy_exchange])
        if quote_obj:
            buy_price = quote_obj[0].ask
        else:
            print(f"Error: Could not fetch price from {args.buy_exchange}", file=sys.stderr)
            return 1

    if args.sell_price:
        sell_price = Decimal(args.sell_price)
    else:
        quote_obj = fetcher.fetch_all_prices_sync(base, quote, [args.sell_exchange])
        if quote_obj:
            sell_price = quote_obj[0].bid
        else:
            print(f"Error: Could not fetch price from {args.sell_exchange}", file=sys.stderr)
            return 1

    # Calculate
    calc = ProfitCalculator(
        gas_price_gwei=args.gas_price,
        eth_price_usd=args.eth_price,
    )

    breakdown = calc.calculate(
        pair=args.pair,
        buy_exchange=args.buy_exchange,
        sell_exchange=args.sell_exchange,
        buy_price=buy_price,
        sell_price=sell_price,
        amount=amount,
    )

    # Format output
    if args.output == "json":
        fmt = JSONFormatter()
        print(fmt.format_profit_breakdown(breakdown))
    else:
        fmt = ConsoleFormatter()
        print(fmt.format_profit_breakdown(breakdown))

    return 0 if breakdown.is_profitable else 1


def print_banner():
    """Print startup banner."""
    banner = """
╔══════════════════════════════════════════════════════════════════╗
║            ARBITRAGE OPPORTUNITY FINDER v1.0.0                  ║
║                                                                  ║
║  Find profitable arbitrage across CEX, DEX, and cross-chain    ║
║  Exchanges: Binance | Coinbase | Kraken | Uniswap | SushiSwap  ║
║                                                                  ║
║  ⚠️  EDUCATIONAL PURPOSES ONLY - Verify before trading          ║
╚══════════════════════════════════════════════════════════════════╝
"""
    print(banner, file=sys.stderr)


def main() -> int:
    """Main entry point."""
    args = parse_args()

    if not args.command:
        print_banner()
        print("Use --help for usage information", file=sys.stderr)
        print("\nQuick start:")
        print("  arb_finder.py scan ETH USDC")
        print("  arb_finder.py triangular binance")
        print("  arb_finder.py monitor ETH USDC --threshold 0.3")
        return 1

    # Run appropriate command
    if args.command == "scan":
        return run_scan(args)
    elif args.command == "triangular":
        return run_triangular(args)
    elif args.command == "monitor":
        return run_monitor(args)
    elif args.command == "calc":
        return run_calc(args)
    else:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
