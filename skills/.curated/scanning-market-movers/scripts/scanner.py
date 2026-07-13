#!/usr/bin/env python3
"""
Market Movers Scanner - Main CLI Entry Point

Detect significant price movements and unusual volume across crypto markets.
Ranks movers by significance score combining price change, volume ratio, and market cap.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 2.0.0
License: MIT
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

# Add scripts directory to path for local imports
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from analyzer import MarketAnalyzer
from filters import apply_filters, FilterConfig
from scorers import calculate_significance
from formatters import MoversFormatter


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Scan cryptocurrency markets for significant movers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                # Default scan
  %(prog)s --min-change 10                # Moves > 10 percent
  %(prog)s --volume-spike 5               # Volume > 5x average
  %(prog)s --category defi                # DeFi tokens only
  %(prog)s --preset aggressive            # Use aggressive preset
  %(prog)s --format json --output out.json  # Export to JSON
        """,
    )

    # Filter options
    parser.add_argument("--min-change", type=float, default=5.0, help="Minimum absolute %% change (default: 5)")
    parser.add_argument(
        "--volume-spike", type=float, default=2.0, help="Minimum volume ratio vs average (default: 2.0)"
    )
    parser.add_argument("--min-cap", type=float, default=10_000_000, help="Minimum market cap in USD (default: 10M)")
    parser.add_argument("--max-cap", type=float, default=None, help="Maximum market cap in USD (default: no limit)")
    parser.add_argument("--min-volume", type=float, default=100_000, help="Minimum 24h volume in USD (default: 100K)")

    # Category and preset options
    parser.add_argument(
        "--category", type=str, choices=["defi", "layer2", "nft", "gaming", "meme"], help="Filter by category"
    )
    parser.add_argument("--preset", type=str, help="Use named preset from config/presets/")

    # Timeframe options
    parser.add_argument(
        "--timeframe",
        type=str,
        choices=["1h", "4h", "24h", "7d"],
        default="24h",
        help="Timeframe for change calculation (default: 24h)",
    )

    # Output options
    parser.add_argument("--top", type=int, default=20, help="Number of results per category (default: 20)")
    parser.add_argument("--gainers-only", action="store_true", help="Only show gainers")
    parser.add_argument("--losers-only", action="store_true", help="Only show losers")
    parser.add_argument(
        "--sort-by",
        type=str,
        choices=["significance", "change", "volume", "market_cap"],
        default="significance",
        help="Sort results by (default: significance)",
    )

    # Format and export
    parser.add_argument(
        "--format",
        "-f",
        type=str,
        choices=["table", "json", "csv"],
        default="table",
        help="Output format (default: table)",
    )
    parser.add_argument("--output", "-o", type=str, help="Output file path (default: stdout)")

    # Debug options
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
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
            pass
        except Exception:
            pass

    # Default configuration
    return {
        "thresholds": {"min_change": 5, "volume_spike": 2, "min_market_cap": 10_000_000, "min_volume": 100_000},
        "scoring": {"change_weight": 0.40, "volume_weight": 0.40, "cap_weight": 0.20},
        "display": {"top_n": 20, "sort_by": "significance"},
    }


def load_preset(preset_name: str) -> Optional[dict]:
    """Load a named preset from config/presets/."""
    preset_path = SCRIPT_DIR.parent / "config" / "presets" / f"{preset_name}.yaml"

    if preset_path.exists():
        try:
            import yaml

            with open(preset_path, "r") as f:
                return yaml.safe_load(f)
        except Exception:
            pass

    return None


def main() -> None:
    """Main entry point."""
    args = parse_args()
    config = load_config()

    # Load preset if specified
    if args.preset:
        preset = load_preset(args.preset)
        if preset:
            # Preset overrides defaults
            args.min_change = preset.get("min_change", args.min_change)
            args.volume_spike = preset.get("volume_spike", args.volume_spike)
            args.min_cap = preset.get("min_market_cap", args.min_cap)
            args.min_volume = preset.get("min_volume", args.min_volume)
            args.top = preset.get("top_n", args.top)
        else:
            print(f"Warning: Preset '{args.preset}' not found, using defaults", file=sys.stderr)

    # Initialize analyzer
    try:
        analyzer = MarketAnalyzer(verbose=args.verbose)
    except ImportError as e:
        print(f"Error: {e}", file=sys.stderr)
        print("\nEnsure tracking-crypto-prices skill is available.", file=sys.stderr)
        sys.exit(1)

    # Fetch market data
    if args.verbose:
        print("Fetching market data...", file=sys.stderr)

    try:
        market_data = analyzer.fetch_market_data(category=args.category, limit=1000)
    except Exception as e:
        print(f"Error fetching market data: {e}", file=sys.stderr)
        sys.exit(1)

    if not market_data:
        print("Error: No market data available", file=sys.stderr)
        sys.exit(1)

    if args.verbose:
        print(f"Fetched {len(market_data)} assets", file=sys.stderr)

    # Calculate metrics for each asset
    for asset in market_data:
        # Get change based on timeframe
        if args.timeframe == "24h":
            change = asset.get("change_24h", 0) or 0
        elif args.timeframe == "7d":
            change = asset.get("change_7d", 0) or 0
        else:
            change = asset.get("change_24h", 0) or 0  # Default to 24h

        asset["change"] = change

        # Calculate volume ratio (simple estimate if avg not available)
        volume = asset.get("volume_24h", 0) or 0
        market_cap = asset.get("market_cap", 0) or 0

        # Estimate average daily volume as volume / typical_turnover_ratio
        # This is a rough approximation
        if market_cap > 0:
            typical_turnover = 0.05  # 5% daily turnover assumption
            estimated_avg_volume = market_cap * typical_turnover
            volume_ratio = volume / estimated_avg_volume if estimated_avg_volume > 0 else 1
        else:
            volume_ratio = 1

        asset["volume_ratio"] = round(volume_ratio, 2)

        # Calculate significance score
        weights = config.get("scoring", {})
        asset["significance_score"] = calculate_significance(
            change_pct=change, volume_ratio=volume_ratio, market_cap=market_cap, weights=weights
        )

    # Apply filters
    filter_config = FilterConfig(
        min_change=args.min_change,
        volume_spike=args.volume_spike,
        min_market_cap=args.min_cap,
        max_market_cap=args.max_cap,
        min_volume=args.min_volume,
    )

    filtered = apply_filters(market_data, filter_config)

    if args.verbose:
        print(f"After filtering: {len(filtered)} assets match criteria", file=sys.stderr)

    # Separate gainers and losers
    gainers = [a for a in filtered if a.get("change", 0) > 0]
    losers = [a for a in filtered if a.get("change", 0) < 0]

    # Sort based on sort_by option
    sort_key = {
        "significance": lambda x: x.get("significance_score", 0),
        "change": lambda x: abs(x.get("change", 0)),
        "volume": lambda x: x.get("volume_ratio", 0),
        "market_cap": lambda x: x.get("market_cap", 0),
    }.get(args.sort_by, lambda x: x.get("significance_score", 0))

    gainers.sort(key=sort_key, reverse=True)
    losers.sort(key=sort_key, reverse=True)

    # Limit results
    gainers = gainers[: args.top]
    losers = losers[: args.top]

    # Add ranks
    for i, g in enumerate(gainers, 1):
        g["rank"] = i
    for i, l in enumerate(losers, 1):
        l["rank"] = i

    # Prepare result
    result = {
        "gainers": [] if args.losers_only else gainers,
        "losers": [] if args.gainers_only else losers,
        "meta": {
            "timeframe": args.timeframe,
            "thresholds": {
                "min_change": args.min_change,
                "volume_spike": args.volume_spike,
                "min_market_cap": args.min_cap,
            },
            "total_scanned": len(market_data),
            "matches": len(filtered),
            "category": args.category,
        },
    }

    # Format output
    formatter = MoversFormatter()
    output = formatter.format(result, format_type=args.format)

    # Write output
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            f.write(output)
        print(f"Output written to {output_path}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
