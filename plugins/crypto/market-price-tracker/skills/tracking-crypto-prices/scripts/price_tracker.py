#!/usr/bin/env python3
"""
Crypto Price Tracker - Main CLI Entry Point

Track real-time and historical cryptocurrency prices across exchanges.
Foundation skill for the crypto plugin ecosystem.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 2.0.0
License: MIT
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add scripts directory to path for local imports
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from api_client import CryptoAPIClient, APIError
from cache_manager import CacheManager
from formatters import PriceFormatter


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Track real-time and historical cryptocurrency prices",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --symbol BTC                    # Get Bitcoin price
  %(prog)s --symbols BTC,ETH,SOL           # Get multiple prices
  %(prog)s --watchlist top10               # Scan top 10 by market cap
  %(prog)s --symbol BTC --period 30d       # 30-day history
  %(prog)s --symbol ETH --output csv       # Export to CSV
  %(prog)s --list                          # Search available coins
        """,
    )

    # Symbol selection (mutually exclusive)
    symbol_group = parser.add_mutually_exclusive_group()
    symbol_group.add_argument("--symbol", "-s", type=str, help="Single cryptocurrency symbol (e.g., BTC, ETH)")
    symbol_group.add_argument("--symbols", type=str, help="Comma-separated list of symbols (e.g., BTC,ETH,SOL)")
    symbol_group.add_argument(
        "--watchlist",
        "-w",
        type=str,
        choices=["top10", "defi", "layer2", "stablecoins", "memecoins", "custom"],
        help="Use predefined watchlist",
    )
    symbol_group.add_argument(
        "--list", "-l", action="store_true", help="List available cryptocurrencies (search with --query)"
    )

    # Search options
    parser.add_argument("--query", "-q", type=str, help="Search query for --list mode")

    # Historical data options
    parser.add_argument("--period", "-p", type=str, help="Historical period (e.g., 7d, 30d, 90d, 1y, max)")
    parser.add_argument("--start", type=str, help="Start date for custom range (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, help="End date for custom range (YYYY-MM-DD)")

    # Output options
    parser.add_argument(
        "--format",
        "-f",
        type=str,
        choices=["table", "json", "csv", "minimal"],
        default="table",
        help="Output format (default: table)",
    )
    parser.add_argument("--output", "-o", type=str, help="Output file path (default: stdout)")

    # Currency options
    parser.add_argument("--currency", "-c", type=str, default="usd", help="Fiat currency for prices (default: usd)")

    # Cache control
    parser.add_argument("--no-cache", action="store_true", help="Bypass cache and fetch fresh data")
    parser.add_argument("--clear-cache", action="store_true", help="Clear all cached data")

    # Verbosity
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--quiet", action="store_true", help="Suppress non-essential output")

    # Version
    parser.add_argument("--version", action="version", version="%(prog)s 2.0.0")

    return parser.parse_args()


def load_config() -> dict:
    """Load configuration from settings.yaml."""
    config_path = SCRIPT_DIR.parent / "config" / "settings.yaml"

    if config_path.exists():
        try:
            import yaml

            with open(config_path, "r") as f:
                return yaml.safe_load(f) or {}
        except ImportError:
            # Fallback if PyYAML not installed
            pass
        except Exception:
            pass

    # Default configuration
    return {
        "cache": {
            "enabled": True,
            "spot_ttl": 30,
            "historical_ttl": 3600,
            "directory": str(SCRIPT_DIR.parent / "data"),
        },
        "currency": {"default": "usd"},
        "watchlists": {
            "top10": [
                "bitcoin",
                "ethereum",
                "tether",
                "binancecoin",
                "solana",
                "ripple",
                "cardano",
                "avalanche-2",
                "dogecoin",
                "polkadot",
            ],
            "defi": ["uniswap", "aave", "chainlink", "maker", "compound-governance-token", "curve-dao-token", "sushi"],
            "layer2": ["matic-network", "arbitrum", "optimism", "immutable-x"],
            "stablecoins": ["tether", "usd-coin", "dai", "frax", "true-usd"],
            "memecoins": ["dogecoin", "shiba-inu", "pepe", "floki", "bonk"],
        },
    }


def get_watchlist_symbols(watchlist_name: str, config: dict) -> list:
    """Get symbols for a watchlist."""
    watchlists = config.get("watchlists", {})

    if watchlist_name == "custom":
        custom = watchlists.get("custom", [])
        if not custom:
            print("Error: Custom watchlist is empty. Configure in settings.yaml", file=sys.stderr)
            sys.exit(1)
        return custom

    symbols = watchlists.get(watchlist_name)
    if not symbols:
        print(f"Error: Unknown watchlist '{watchlist_name}'", file=sys.stderr)
        sys.exit(1)

    return symbols


def handle_list_command(
    client: CryptoAPIClient, query: Optional[str], formatter: PriceFormatter, args: argparse.Namespace
) -> None:
    """Handle --list command to search available coins."""
    try:
        coins = client.list_coins(query=query)

        if args.format == "json":
            print(json.dumps(coins, indent=2))
        else:
            formatter.print_coin_list(coins, query)

    except APIError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def handle_price_command(
    symbols: list,
    client: CryptoAPIClient,
    cache: CacheManager,
    formatter: PriceFormatter,
    args: argparse.Namespace,
    config: dict,
) -> None:
    """Handle price lookup for one or more symbols."""
    currency = args.currency.lower()
    use_cache = not args.no_cache and config.get("cache", {}).get("enabled", True)

    results = []
    cache_hits = 0

    for symbol in symbols:
        # Check cache first
        if use_cache:
            cached = cache.get_spot_price(symbol, currency)
            if cached:
                results.append(cached)
                cache_hits += 1
                continue

        # Fetch from API
        try:
            price_data = client.get_current_price(symbol, currency)
            results.append(price_data)

            # Cache the result
            if use_cache:
                cache.set_spot_price(symbol, currency, price_data)

        except APIError as e:
            if args.verbose:
                print(f"Warning: Failed to fetch {symbol}: {e}", file=sys.stderr)

            # Try cache as fallback
            if use_cache:
                stale = cache.get_spot_price(symbol, currency, allow_stale=True)
                if stale:
                    stale["_stale"] = True
                    results.append(stale)
                    if not args.quiet:
                        print(f"Warning: Using stale cache for {symbol}", file=sys.stderr)

    if not results:
        print("Error: No price data available", file=sys.stderr)
        sys.exit(1)

    # Output results
    output_text = formatter.format_prices(results, format_type=args.format, verbose=args.verbose)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            f.write(output_text)
        if not args.quiet:
            print(f"Output written to {output_path}")
    else:
        print(output_text)

    # Cache stats
    if args.verbose and use_cache and len(symbols) > 1:
        print(f"\nCache: {cache_hits}/{len(symbols)} hits", file=sys.stderr)


def handle_historical_command(
    symbol: str,
    client: CryptoAPIClient,
    cache: CacheManager,
    formatter: PriceFormatter,
    args: argparse.Namespace,
    config: dict,
) -> None:
    """Handle historical price lookup."""
    currency = args.currency.lower()
    use_cache = not args.no_cache and config.get("cache", {}).get("enabled", True)

    # Parse period or date range
    if args.start and args.end:
        start_date = datetime.strptime(args.start, "%Y-%m-%d")
        end_date = datetime.strptime(args.end, "%Y-%m-%d")
        period = None
    elif args.period:
        period = args.period
        start_date = None
        end_date = None
    else:
        period = "30d"  # Default
        start_date = None
        end_date = None

    # Check cache
    cache_key = f"{symbol}_{period or f'{args.start}_{args.end}'}_{currency}"
    if use_cache:
        cached = cache.get_historical(cache_key)
        if cached:
            results = cached
        else:
            results = None
    else:
        results = None

    # Fetch if not cached
    if results is None:
        try:
            results = client.get_historical_prices(
                symbol, currency=currency, period=period, start_date=start_date, end_date=end_date
            )

            if use_cache:
                cache.set_historical(cache_key, results)

        except APIError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    # Output results
    output_text = formatter.format_historical(symbol, results, format_type=args.format)

    if args.output:
        output_path = Path(args.output)
        if args.format == "csv" and not output_path.suffix:
            output_path = output_path.with_suffix(".csv")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            f.write(output_text)
        if not args.quiet:
            print(f"Output written to {output_path}")
    else:
        print(output_text)


def main() -> None:
    """Main entry point."""
    args = parse_args()
    config = load_config()

    # Initialize components
    cache_dir = Path(config.get("cache", {}).get("directory", str(SCRIPT_DIR.parent / "data")))
    cache = CacheManager(
        cache_dir=cache_dir,
        spot_ttl=config.get("cache", {}).get("spot_ttl", 30),
        historical_ttl=config.get("cache", {}).get("historical_ttl", 3600),
    )

    client = CryptoAPIClient(config=config)
    formatter = PriceFormatter(currency=args.currency.upper())

    # Handle cache operations
    if args.clear_cache:
        cache.clear()
        if not args.quiet:
            print("Cache cleared")
        return

    # Handle list command
    if args.list:
        handle_list_command(client, args.query, formatter, args)
        return

    # Determine symbols to fetch
    symbols = []
    if args.symbol:
        symbols = [args.symbol]
    elif args.symbols:
        symbols = [s.strip() for s in args.symbols.split(",")]
    elif args.watchlist:
        symbols = get_watchlist_symbols(args.watchlist, config)
    else:
        # Default: show help
        print("Error: Specify --symbol, --symbols, --watchlist, or --list", file=sys.stderr)
        print("Use --help for usage information", file=sys.stderr)
        sys.exit(1)

    # Handle historical vs current prices
    if args.period or args.start:
        if len(symbols) > 1:
            print("Error: Historical data supports single symbol only", file=sys.stderr)
            sys.exit(1)
        handle_historical_command(symbols[0], client, cache, formatter, args, config)
    else:
        handle_price_command(symbols, client, cache, formatter, args, config)


if __name__ == "__main__":
    main()
