#!/usr/bin/env python3
"""
Main Backtesting Engine
Run trading strategy backtests with performance analysis.

Usage:
    python backtest.py --strategy sma_crossover --symbol BTC-USD --period 1y
    python backtest.py --strategy rsi_reversal --symbol ETH-USD --start 2023-01-01 --end 2024-01-01
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

import pandas as pd
import numpy as np

try:
    import yaml
except ImportError:
    yaml = None

# Add script directory to path
sys.path.insert(0, str(Path(__file__).parent))

from strategies import get_strategy, list_strategies, Signal
from metrics import Trade, BacktestResult, calculate_all_metrics, format_results
from fetch_data import parse_period


def load_settings(skill_dir: Path) -> dict:
    """Load settings from config/settings.yaml if present, else return defaults."""
    settings_file = skill_dir / 'config' / 'settings.yaml'
    if yaml is not None and settings_file.exists():
        with open(settings_file) as f:
            return yaml.safe_load(f) or {}
    return {}


def load_data(symbol: str, start: datetime, end: datetime, data_dir: Path) -> pd.DataFrame:
    """Load price data from CSV or fetch if not cached."""

    # Try to load from cache
    cache_file = data_dir / f"{symbol.replace('/', '_').replace('-', '_')}_1d.csv"

    if cache_file.exists():
        df = pd.read_csv(cache_file, parse_dates=['date'], index_col='date')
        # Remove timezone info for comparison
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        df = df[(df.index >= pd.Timestamp(start)) & (df.index <= pd.Timestamp(end))]
        if len(df) > 0:
            return df

    # Fetch using yfinance
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start, end=end, interval='1d')
        df.columns = [c.lower() for c in df.columns]
        df.index.name = 'date'

        # Remove timezone for consistency
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)

        # Cache the data
        data_dir.mkdir(parents=True, exist_ok=True)
        df.to_csv(cache_file)

        return df
    except ImportError:
        print("yfinance not installed. Install with: pip install yfinance")
        sys.exit(1)
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        sys.exit(1)


def run_backtest(
    strategy_name: str,
    data: pd.DataFrame,
    initial_capital: float = 10000,
    params: Dict[str, Any] = None,
    commission: float = 0.001,
    slippage: float = 0.0005,
    risk_settings: Dict[str, Any] = None,
) -> BacktestResult:
    """Run a backtest on historical data.

    Args:
        risk_settings: Dict with optional keys:
            - stop_loss: float or None, max loss % before forced exit (e.g. 0.05 = 5%)
            - take_profit: float or None, profit % target for forced exit
            - max_position_size: float, fraction of cash to allocate (default 0.95)
    """

    params = params or {}
    risk_settings = risk_settings or {}
    strategy = get_strategy(strategy_name)

    stop_loss = risk_settings.get('stop_loss')
    take_profit = risk_settings.get('take_profit')
    max_position_size = risk_settings.get('max_position_size', 0.95)

    trades: List[Trade] = []
    equity = [initial_capital]
    cash = initial_capital
    position = None
    position_size = 0

    for i in range(strategy.lookback, len(data)):
        # Get data slice up to current bar
        slice_data = data.iloc[:i+1].copy()
        current_bar = data.iloc[i]
        current_price = current_bar['close']
        current_time = data.index[i]

        # Generate signals
        signal = strategy.generate_signals(slice_data, params)

        # Apply slippage
        buy_price = current_price * (1 + slippage)
        sell_price = current_price * (1 - slippage)

        # --- Check stop-loss / take-profit ---
        force_exit = False
        if position is not None:
            if position['direction'] == 'long':
                unrealized_pnl_pct = (current_price - position['entry_price']) / position['entry_price']
            else:
                unrealized_pnl_pct = (position['entry_price'] - current_price) / position['entry_price']

            if stop_loss is not None and unrealized_pnl_pct <= -stop_loss:
                force_exit = True
            elif take_profit is not None and unrealized_pnl_pct >= take_profit:
                force_exit = True

        # --- Exit logic (checked before entry to allow same-bar flips) ---
        if position is not None and (signal.exit or force_exit):
            if position['direction'] == 'long':
                exit_value = position_size * sell_price
                commission_cost = exit_value * commission
                cash += exit_value - commission_cost
                trade_exit_price = sell_price
            else:  # short
                pnl = position_size * (position['entry_price'] - buy_price)
                commission_cost = position_size * buy_price * commission
                cash += position['collateral'] + pnl - commission_cost
                trade_exit_price = buy_price

            trade = Trade(
                entry_time=position['entry_time'],
                exit_time=current_time,
                entry_price=position['entry_price'],
                exit_price=trade_exit_price,
                direction=position['direction'],
                size=position['size'],
            )
            trades.append(trade)
            position = None
            position_size = 0

        # --- Entry logic (separate if, enables same-bar exit+entry) ---
        if signal.entry and position is None:
            if signal.direction == 'long':
                position_value = cash * max_position_size
                position_size = position_value / buy_price
                commission_cost = position_value * commission
                cash -= position_value + commission_cost

                position = {
                    'entry_time': current_time,
                    'entry_price': buy_price,
                    'direction': 'long',
                    'size': position_size,
                }
            else:  # short
                position_value = cash * max_position_size
                position_size = position_value / sell_price
                commission_cost = position_value * commission
                cash -= position_value + commission_cost

                position = {
                    'entry_time': current_time,
                    'entry_price': sell_price,
                    'direction': 'short',
                    'size': position_size,
                    'collateral': position_value,
                }

        # Calculate equity (cash + position value)
        if position is not None:
            if position['direction'] == 'long':
                equity.append(cash + position_size * current_price)
            else:
                equity.append(cash + position['collateral'] + position_size * (position['entry_price'] - current_price))
        else:
            equity.append(cash)

    # Close any open position at end
    if position is not None:
        if position['direction'] == 'long':
            final_price = data.iloc[-1]['close'] * (1 - slippage)
            exit_value = position_size * final_price
            commission_cost = exit_value * commission
            cash += exit_value - commission_cost
            trade_exit_price = final_price
        else:
            final_price = data.iloc[-1]['close'] * (1 + slippage)
            pnl = position_size * (position['entry_price'] - final_price)
            commission_cost = position_size * final_price * commission
            cash += position['collateral'] + pnl - commission_cost
            trade_exit_price = final_price

        trade = Trade(
            entry_time=position['entry_time'],
            exit_time=data.index[-1],
            entry_price=position['entry_price'],
            exit_price=trade_exit_price,
            direction=position['direction'],
            size=position['size'],
        )
        trades.append(trade)
        equity[-1] = cash

    # Create equity curve
    equity_curve = pd.Series(equity, index=data.index[strategy.lookback-1:])

    # Build result
    result = BacktestResult(
        strategy=strategy_name,
        symbol=data.attrs.get('symbol', 'Unknown'),
        start_date=data.index[0],
        end_date=data.index[-1],
        initial_capital=initial_capital,
        final_capital=equity[-1],
        trades=trades,
        equity_curve=equity_curve,
        parameters=params,
    )

    # Calculate all metrics
    result = calculate_all_metrics(result)

    return result


def save_results(result: BacktestResult, output_dir: Path) -> None:
    """Save backtest results to files."""
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    base_name = f"{result.strategy}_{result.symbol.replace('/', '_')}_{timestamp}"

    # Save summary
    summary_file = output_dir / f"{base_name}_summary.txt"
    with open(summary_file, 'w') as f:
        f.write(format_results(result))

    # Save trades to CSV
    if result.trades:
        trades_file = output_dir / f"{base_name}_trades.csv"
        trades_df = pd.DataFrame([
            {
                'entry_time': t.entry_time,
                'exit_time': t.exit_time,
                'entry_price': t.entry_price,
                'exit_price': t.exit_price,
                'direction': t.direction,
                'size': t.size,
                'pnl': t.pnl,
                'pnl_pct': t.pnl_pct,
                'duration': t.duration,
            }
            for t in result.trades
        ])
        trades_df.to_csv(trades_file, index=False)

    # Save equity curve
    equity_file = output_dir / f"{base_name}_equity.csv"
    result.equity_curve.to_csv(equity_file, header=['equity'])

    # Try to plot equity curve
    try:
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(2, 1, figsize=(12, 8))

        # Equity curve
        axes[0].plot(result.equity_curve, label='Portfolio Value', color='blue')
        axes[0].set_title(f'{result.strategy.upper()} - {result.symbol} Equity Curve')
        axes[0].set_ylabel('Portfolio Value ($)')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)

        # Drawdown
        rolling_max = result.equity_curve.expanding().max()
        drawdown = (result.equity_curve - rolling_max) / rolling_max * 100
        axes[1].fill_between(drawdown.index, drawdown, 0, alpha=0.5, color='red')
        axes[1].set_title('Drawdown')
        axes[1].set_ylabel('Drawdown (%)')
        axes[1].set_xlabel('Date')
        axes[1].grid(True, alpha=0.3)

        plt.tight_layout()
        chart_file = output_dir / f"{base_name}_chart.png"
        plt.savefig(chart_file, dpi=100)
        plt.close()

        print(f"Chart saved to: {chart_file}")
    except ImportError:
        pass  # matplotlib not available

    print(f"Results saved to: {output_dir}")


def main():
    parser = argparse.ArgumentParser(description='Backtest trading strategies')
    parser.add_argument('--strategy', '-s', required=True, help='Strategy name')
    parser.add_argument('--symbol', required=True, help='Trading symbol (e.g., BTC-USD)')
    parser.add_argument('--period', '-p', help='Lookback period (e.g., 1y, 6m, 30d)')
    parser.add_argument('--start', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', help='End date (YYYY-MM-DD)')
    parser.add_argument('--capital', '-c', type=float, default=None, help='Initial capital')
    parser.add_argument('--params', help='Strategy parameters as JSON')
    parser.add_argument('--commission', type=float, default=None, help='Commission per trade')
    parser.add_argument('--slippage', type=float, default=None, help='Slippage per trade')
    parser.add_argument('--output', '-o', help='Output directory')
    parser.add_argument('--list', action='store_true', help='List available strategies')
    parser.add_argument('--quiet', '-q', action='store_true', help='Minimal output')

    args = parser.parse_args()

    # List strategies
    if args.list:
        print("Available strategies:")
        for name, desc in list_strategies().items():
            print(f"  {name}: {desc}")
        return

    # Load settings: CLI args > settings.yaml > hardcoded defaults
    script_dir = Path(__file__).parent.parent
    settings = load_settings(script_dir)
    backtest_settings = settings.get('backtest', {})
    risk_settings = settings.get('risk', {})

    capital = args.capital if args.capital is not None else backtest_settings.get('default_capital', 10000)
    commission = args.commission if args.commission is not None else backtest_settings.get('commission', 0.001)
    slippage = args.slippage if args.slippage is not None else backtest_settings.get('slippage', 0.0005)

    # Determine date range
    if args.start and args.end:
        start = datetime.strptime(args.start, '%Y-%m-%d')
        end = datetime.strptime(args.end, '%Y-%m-%d')
    elif args.period:
        end = datetime.now()
        start = end - parse_period(args.period)
    else:
        end = datetime.now()
        start = end - timedelta(days=365)

    # Parse parameters
    params = json.loads(args.params) if args.params else {}

    # Set up directories
    data_dir = script_dir / 'data'
    output_dir = Path(args.output) if args.output else script_dir / 'reports'

    # Load data
    if not args.quiet:
        print(f"Loading data for {args.symbol} from {start.date()} to {end.date()}...")

    data = load_data(args.symbol, start, end, data_dir)
    data.attrs['symbol'] = args.symbol

    if len(data) < 50:
        print(f"Error: Insufficient data. Got {len(data)} bars, need at least 50.")
        sys.exit(1)

    if not args.quiet:
        print(f"Loaded {len(data)} bars")
        print(f"Running backtest with {args.strategy} strategy...")

    # Run backtest
    result = run_backtest(
        strategy_name=args.strategy,
        data=data,
        initial_capital=capital,
        params=params,
        commission=commission,
        slippage=slippage,
        risk_settings=risk_settings,
    )

    # Print results
    print(format_results(result))

    # Save results
    save_results(result, output_dir)


if __name__ == '__main__':
    main()
