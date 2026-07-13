#!/usr/bin/env python3
"""
Historical Data Fetcher
Fetch and cache price data from various sources.

Usage:
    python fetch_data.py --symbol BTC-USD --period 2y --interval 1d
    python fetch_data.py --symbol ETH-USD --start 2020-01-01 --end 2024-01-01
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from pathlib import Path
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd  # noqa: F401  — used in deferred type hints


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


def fetch_yfinance(symbol: str, start: datetime, end: datetime, interval: str) -> "pd.DataFrame":
    """Fetch data from Yahoo Finance."""
    try:
        import yfinance as yf
    except ImportError:
        print("yfinance not installed. Install with: pip install yfinance pandas")
        sys.exit(1)

    print(f"Fetching {symbol} from Yahoo Finance...")
    ticker = yf.Ticker(symbol)
    df = ticker.history(start=start, end=end, interval=interval)

    if df.empty:
        raise ValueError(f"No data returned for {symbol}")

    df.columns = [c.lower() for c in df.columns]
    df.index.name = "date"

    return df


def fetch_coingecko(symbol: str, days: int) -> "pd.DataFrame":
    """Fetch data from CoinGecko (crypto only)."""
    try:
        import requests
        import pandas as pd
    except ImportError:
        print("requests/pandas not installed")
        sys.exit(1)

    # Map common symbols to CoinGecko IDs
    symbol_map = {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "SOL": "solana",
        "AVAX": "avalanche-2",
        "MATIC": "matic-network",
        "DOT": "polkadot",
        "LINK": "chainlink",
        "UNI": "uniswap",
        "AAVE": "aave",
    }

    coin_id = symbol_map.get(symbol.split("-")[0].upper(), symbol.lower())

    print(f"Fetching {coin_id} from CoinGecko...")
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {"vs_currency": "usd", "days": days}

    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    df = pd.DataFrame(data["prices"], columns=["timestamp", "close"])
    df["date"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.set_index("date", inplace=True)
    df.drop("timestamp", axis=1, inplace=True)

    # Add OHLV columns (approximations for daily)
    df["open"] = df["close"].shift(1).fillna(df["close"])
    df["high"] = df["close"] * 1.01  # Rough estimate
    df["low"] = df["close"] * 0.99
    df["volume"] = 0  # Not available in basic API

    return df[["open", "high", "low", "close", "volume"]]


def main():
    parser = argparse.ArgumentParser(description="Fetch historical price data")
    parser.add_argument("--symbol", "-s", required=True, help="Trading symbol")
    parser.add_argument("--period", "-p", help="Lookback period (e.g., 2y, 6m)")
    parser.add_argument("--start", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", help="End date (YYYY-MM-DD)")
    parser.add_argument("--interval", "-i", default="1d", help="Data interval (1d, 1h, etc.)")
    parser.add_argument("--source", default="yfinance", choices=["yfinance", "coingecko"])
    parser.add_argument("--output", "-o", help="Output directory")

    args = parser.parse_args()

    # Determine date range
    if args.start and args.end:
        start = datetime.strptime(args.start, "%Y-%m-%d")
        end = datetime.strptime(args.end, "%Y-%m-%d")
    elif args.period:
        end = datetime.now()
        start = end - parse_period(args.period)
    else:
        end = datetime.now()
        start = end - timedelta(days=730)  # 2 years default

    # Fetch data
    if args.source == "yfinance":
        df = fetch_yfinance(args.symbol, start, end, args.interval)
    else:
        days = (end - start).days
        df = fetch_coingecko(args.symbol, days)

    # Save to file
    script_dir = Path(__file__).parent.parent
    output_dir = Path(args.output) if args.output else script_dir / "data"
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{args.symbol.replace('/', '_').replace('-', '_')}_{args.interval}.csv"
    output_file = output_dir / filename

    df.to_csv(output_file)

    print(f"Data saved to: {output_file}")
    print(f"  Rows: {len(df)}")
    print(f"  Date range: {df.index[0]} to {df.index[-1]}")
    print(f"  Columns: {list(df.columns)}")


if __name__ == "__main__":
    main()
