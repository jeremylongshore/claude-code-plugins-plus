#!/usr/bin/env python3
"""
Crypto Signal Scanner
Scan multiple assets and generate trading signals.

Usage:
    python scanner.py --symbols BTC-USD,ETH-USD --period 6m
    python scanner.py --watchlist crypto_top10 --output signals.json
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any

import pandas as pd

# Add script directory to path
sys.path.insert(0, str(Path(__file__).parent))

from indicators import calculate_all_indicators
from signals import SignalGenerator, TradingSignal, SignalType, format_signal


# Predefined watchlists
WATCHLISTS = {
    "crypto_top10": [
        "BTC-USD",
        "ETH-USD",
        "BNB-USD",
        "SOL-USD",
        "XRP-USD",
        "ADA-USD",
        "AVAX-USD",
        "DOGE-USD",
        "DOT-USD",
        "MATIC-USD",
    ],
    "crypto_defi": [
        "UNI-USD",
        "AAVE-USD",
        "MKR-USD",
        "CRV-USD",
        "SNX-USD",
        "COMP-USD",
        "SUSHI-USD",
        "YFI-USD",
        "LDO-USD",
        "RPL-USD",
    ],
    "crypto_layer2": ["MATIC-USD", "OP-USD", "ARB-USD", "IMX-USD", "LRC-USD"],
    "stocks_tech": ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AMD", "INTC", "CRM"],
    "etfs_major": ["SPY", "QQQ", "IWM", "DIA", "VTI"],
}


def parse_period(period: str) -> timedelta:
    """Parse period string like '1y', '6m', '30d'."""
    unit = period[-1].lower()
    value = int(period[:-1])

    if unit == "y":
        return timedelta(days=value * 365)
    elif unit == "m":
        return timedelta(days=value * 30)
    elif unit == "d":
        return timedelta(days=value)
    elif unit == "w":
        return timedelta(weeks=value)
    else:
        raise ValueError(f"Unknown period unit: {unit}")


def fetch_data(symbol: str, period: str = "6m", cache_dir: Path = None) -> pd.DataFrame:
    """Fetch price data for a symbol."""
    end = datetime.now()
    start = end - parse_period(period)

    # Check cache first (no yfinance needed)
    if cache_dir:
        cache_file = cache_dir / f"{symbol.replace('/', '_').replace('-', '_')}_1d.csv"
        if cache_file.exists():
            try:
                df = pd.read_csv(cache_file, parse_dates=["date"], index_col="date")
                if df.index.tz is not None:
                    df.index = df.index.tz_localize(None)
                df = df[(df.index >= pd.Timestamp(start)) & (df.index <= pd.Timestamp(end))]
                if len(df) > 50:
                    return df
            except Exception:
                pass  # Fall through to fetch

    # Fetch from yfinance
    try:
        import yfinance as yf

        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start, end=end, interval="1d")
        df.columns = [c.lower() for c in df.columns]
        df.index.name = "date"

        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)

        # Cache the data
        if cache_dir and len(df) > 0:
            cache_dir.mkdir(parents=True, exist_ok=True)
            cache_file = cache_dir / f"{symbol.replace('/', '_').replace('-', '_')}_1d.csv"
            df.to_csv(cache_file)

        return df

    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return pd.DataFrame()


def scan_symbols(
    symbols: List[str], period: str = "6m", params: Dict[str, Any] = None, cache_dir: Path = None, quiet: bool = False
) -> List[TradingSignal]:
    """
    Scan multiple symbols and generate signals.

    Args:
        symbols: List of trading symbols
        period: Lookback period
        params: Signal generator parameters
        cache_dir: Directory for data caching
        quiet: Suppress output

    Returns:
        List of TradingSignal objects
    """
    generator = SignalGenerator(params or {})
    signals = []

    for symbol in symbols:
        if not quiet:
            print(f"Scanning {symbol}...", end=" ")

        df = fetch_data(symbol, period, cache_dir)

        if len(df) < 50:
            if not quiet:
                print("SKIP (insufficient data)")
            continue

        # Calculate indicators
        df = calculate_all_indicators(df, params)

        # Generate signal
        signal = generator.generate_signal(df, symbol)
        signals.append(signal)

        if not quiet:
            emoji = {
                SignalType.STRONG_BUY: "STRONG BUY",
                SignalType.BUY: "BUY",
                SignalType.NEUTRAL: "NEUTRAL",
                SignalType.SELL: "SELL",
                SignalType.STRONG_SELL: "STRONG SELL",
            }
            print(f"{emoji[signal.signal]} ({signal.confidence:.0f}%)")

    return signals


def filter_signals(
    signals: List[TradingSignal], min_confidence: float = 0, signal_types: List[SignalType] = None
) -> List[TradingSignal]:
    """Filter signals by confidence and type."""
    result = signals

    if min_confidence > 0:
        result = [s for s in result if s.confidence >= min_confidence]

    if signal_types:
        result = [s for s in result if s.signal in signal_types]

    return result


def rank_signals(signals: List[TradingSignal], by: str = "confidence") -> List[TradingSignal]:
    """Rank signals by confidence or strength."""
    if by == "confidence":
        return sorted(signals, key=lambda s: s.confidence, reverse=True)
    elif by == "bullish":
        score_map = {
            SignalType.STRONG_BUY: 5,
            SignalType.BUY: 4,
            SignalType.NEUTRAL: 3,
            SignalType.SELL: 2,
            SignalType.STRONG_SELL: 1,
        }
        return sorted(signals, key=lambda s: (score_map[s.signal], s.confidence), reverse=True)
    elif by == "bearish":
        score_map = {
            SignalType.STRONG_SELL: 5,
            SignalType.SELL: 4,
            SignalType.NEUTRAL: 3,
            SignalType.BUY: 2,
            SignalType.STRONG_BUY: 1,
        }
        return sorted(signals, key=lambda s: (score_map[s.signal], s.confidence), reverse=True)
    else:
        return signals


def print_summary(signals: List[TradingSignal]) -> None:
    """Print a summary table of all signals."""
    print("\n" + "=" * 80)
    print("  SIGNAL SCANNER RESULTS")
    print("=" * 80)
    print(f"\n  {'Symbol':<12} {'Signal':<14} {'Confidence':>10} {'Price':>14} {'Stop Loss':>12}")
    print("-" * 80)

    for signal in signals:
        sl = f"${signal.stop_loss:,.2f}" if signal.stop_loss else "N/A"
        print(
            f"  {signal.symbol:<12} {signal.signal.value:<14} {signal.confidence:>9.1f}% ${signal.price:>12,.2f} {sl:>12}"
        )

    print("-" * 80)

    # Summary stats
    buy_count = sum(1 for s in signals if s.signal in [SignalType.STRONG_BUY, SignalType.BUY])
    sell_count = sum(1 for s in signals if s.signal in [SignalType.STRONG_SELL, SignalType.SELL])
    neutral_count = sum(1 for s in signals if s.signal == SignalType.NEUTRAL)

    print(f"\n  Summary: {buy_count} Buy | {neutral_count} Neutral | {sell_count} Sell")
    print(f"  Scanned: {len(signals)} assets | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 80 + "\n")


def save_results(signals: List[TradingSignal], output_path: Path) -> None:
    """Save signals to JSON file."""
    data = {
        "generated_at": datetime.now().isoformat(),
        "count": len(signals),
        "signals": [s.to_dict() for s in signals],
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Results saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Crypto Signal Scanner")
    parser.add_argument("--symbols", "-s", help="Comma-separated symbols (e.g., BTC-USD,ETH-USD)")
    parser.add_argument("--watchlist", "-w", help="Predefined watchlist name")
    parser.add_argument("--period", "-p", default="6m", help="Lookback period (e.g., 6m, 1y)")
    parser.add_argument("--min-confidence", type=float, default=0, help="Minimum confidence filter")
    parser.add_argument("--filter", choices=["buy", "sell", "all"], default="all", help="Filter signals")
    parser.add_argument("--rank", choices=["confidence", "bullish", "bearish"], help="Rank signals")
    parser.add_argument("--output", "-o", help="Output JSON file")
    parser.add_argument("--detail", "-d", action="store_true", help="Show detailed signal breakdown")
    parser.add_argument("--list-watchlists", action="store_true", help="List available watchlists")
    parser.add_argument("--quiet", "-q", action="store_true", help="Minimal output")

    args = parser.parse_args()

    # List watchlists
    if args.list_watchlists:
        print("\nAvailable watchlists:")
        for name, symbols in WATCHLISTS.items():
            print(f"  {name}: {', '.join(symbols[:3])}... ({len(symbols)} symbols)")
        return

    # Determine symbols to scan
    if args.symbols:
        symbols = [s.strip() for s in args.symbols.split(",")]
    elif args.watchlist:
        if args.watchlist not in WATCHLISTS:
            print(f"Unknown watchlist: {args.watchlist}")
            print(f"Available: {', '.join(WATCHLISTS.keys())}")
            sys.exit(1)
        symbols = WATCHLISTS[args.watchlist]
    else:
        symbols = WATCHLISTS["crypto_top10"]

    # Set up paths
    script_dir = Path(__file__).parent.parent
    cache_dir = script_dir / "data"

    if not args.quiet:
        print(f"\nScanning {len(symbols)} symbols...")
        print(f"Period: {args.period}\n")

    # Scan symbols
    signals = scan_symbols(symbols, args.period, cache_dir=cache_dir, quiet=args.quiet)

    # Filter
    if args.filter == "buy":
        signals = filter_signals(signals, signal_types=[SignalType.STRONG_BUY, SignalType.BUY])
    elif args.filter == "sell":
        signals = filter_signals(signals, signal_types=[SignalType.STRONG_SELL, SignalType.SELL])

    if args.min_confidence > 0:
        signals = filter_signals(signals, min_confidence=args.min_confidence)

    # Rank
    if args.rank:
        signals = rank_signals(signals, args.rank)

    # Output
    if args.detail:
        for signal in signals:
            print(format_signal(signal))
    else:
        print_summary(signals)

    # Save to file
    if args.output:
        save_results(signals, Path(args.output))


if __name__ == "__main__":
    main()
