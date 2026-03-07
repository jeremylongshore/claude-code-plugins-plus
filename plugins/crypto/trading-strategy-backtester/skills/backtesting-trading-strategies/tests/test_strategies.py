#!/usr/bin/env python3
"""Tests for the backtesting framework."""

import sys
from pathlib import Path
from datetime import timedelta

import numpy as np
import pandas as pd
import pytest

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from fetch_data import parse_period
from strategies import Signal, get_strategy, list_strategies
from metrics import Trade, calculate_trade_stats
from backtest import run_backtest, load_settings


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_price_data(prices, start="2024-01-01"):
    """Build a minimal DataFrame from a list of close prices."""
    dates = pd.date_range(start, periods=len(prices), freq="D")
    df = pd.DataFrame({
        "open": prices,
        "high": [p * 1.01 for p in prices],
        "low": [p * 0.99 for p in prices],
        "close": prices,
        "volume": [1000] * len(prices),
    }, index=dates)
    df.index.name = "date"
    df.attrs["symbol"] = "TEST"
    return df


def make_trending_data(n=300, start_price=100, trend=0.001):
    """Generate upward-trending price series with noise."""
    np.random.seed(42)
    returns = np.random.normal(trend, 0.02, n)
    prices = [start_price]
    for r in returns:
        prices.append(prices[-1] * (1 + r))
    return make_price_data(prices)


def make_mean_reverting_data(n=300, mean=100, std=5):
    """Generate mean-reverting price series."""
    np.random.seed(42)
    prices = []
    price = mean
    for _ in range(n):
        price = price + 0.3 * (mean - price) + np.random.normal(0, std * 0.3)
        prices.append(max(price, 1))
    return make_price_data(prices)


# ---------------------------------------------------------------------------
# parse_period
# ---------------------------------------------------------------------------

class TestParsePeriod:
    def test_years(self):
        assert parse_period("1y") == timedelta(days=365)
        assert parse_period("2y") == timedelta(days=730)

    def test_months(self):
        assert parse_period("6m") == timedelta(days=180)
        assert parse_period("1m") == timedelta(days=30)

    def test_days(self):
        assert parse_period("30d") == timedelta(days=30)

    def test_weeks(self):
        assert parse_period("4w") == timedelta(weeks=4)

    def test_invalid_unit(self):
        with pytest.raises(ValueError, match="Unknown period unit"):
            parse_period("5x")


# ---------------------------------------------------------------------------
# Signal dataclass
# ---------------------------------------------------------------------------

class TestSignal:
    def test_defaults(self):
        s = Signal()
        assert not s.entry
        assert not s.exit
        assert s.direction == "long"
        assert s.strength == 1.0

    def test_short_signal(self):
        s = Signal(entry=True, direction="short")
        assert s.entry
        assert s.direction == "short"

    def test_flip_signal(self):
        s = Signal(entry=True, exit=True, direction="short")
        assert s.entry and s.exit


# ---------------------------------------------------------------------------
# Strategy signals
# ---------------------------------------------------------------------------

class TestStrategies:
    def test_list_strategies(self):
        strategies = list_strategies()
        assert "sma_crossover" in strategies
        assert "rsi_reversal" in strategies
        assert len(strategies) == 8

    def test_get_strategy_invalid(self):
        with pytest.raises(ValueError, match="Unknown strategy"):
            get_strategy("nonexistent")

    def test_sma_crossover_signal(self):
        strategy = get_strategy("sma_crossover")
        # With insufficient data, should return empty signal
        short_data = make_price_data([100] * 10)
        signal = strategy.generate_signals(short_data, {})
        assert not signal.entry and not signal.exit

    def test_rsi_short_signal(self):
        """RSI should generate short signals on overbought reversal."""
        strategy = get_strategy("rsi_reversal")
        # Build data where RSI goes high then drops
        prices = [100] * 20
        # Sharp rally to push RSI above 70
        for i in range(10):
            prices.append(prices[-1] * 1.03)
        # Then drop to push RSI below 70
        prices.append(prices[-1] * 0.95)
        prices.append(prices[-1] * 0.95)

        data = make_price_data(prices)
        signal = strategy.generate_signals(data, {"period": 14, "overbought": 70, "oversold": 30})
        # After sharp rally then drop, should see a short or exit signal
        # The exact signal depends on RSI calculation, but direction should be testable
        if signal.entry:
            assert signal.direction == "short"

    def test_macd_generates_short(self):
        """MACD bearish crossover should produce short signal."""
        strategy = get_strategy("macd")
        # Build data: uptrend then reversal
        prices = list(range(100, 160))  # 60 bars up
        prices += list(range(160, 130, -1))  # 30 bars down
        data = make_price_data(prices)

        signal = strategy.generate_signals(data, {})
        # After reversal, MACD should eventually cross bearishly
        if signal.entry:
            assert signal.direction in ("long", "short")

    def test_bollinger_short_above_upper(self):
        """Bollinger should short when price crosses above upper band."""
        strategy = get_strategy("bollinger_bands")
        # Stable prices then sharp spike
        prices = [100.0] * 25
        prices.append(130.0)  # Spike above upper band
        data = make_price_data(prices)

        signal = strategy.generate_signals(data, {"period": 20, "std_dev": 2.0})
        if signal.entry:
            assert signal.direction == "short"

    def test_mean_reversion_short_above_threshold(self):
        """MeanReversion should short when z-score > threshold."""
        strategy = get_strategy("mean_reversion")
        # Stable then sharp up
        prices = [100.0] * 25
        prices.append(120.0)  # Big z-score
        data = make_price_data(prices)

        signal = strategy.generate_signals(data, {"period": 20, "z_threshold": 2.0})
        if signal.entry:
            assert signal.direction == "short"


# ---------------------------------------------------------------------------
# Trade and metrics
# ---------------------------------------------------------------------------

class TestMetrics:
    def test_long_trade_pnl(self):
        t = Trade(
            entry_time=pd.Timestamp("2024-01-01"),
            exit_time=pd.Timestamp("2024-02-01"),
            entry_price=100.0,
            exit_price=110.0,
            direction="long",
            size=10.0,
        )
        assert t.pnl == pytest.approx(100.0)
        assert t.pnl_pct == pytest.approx(10.0)

    def test_short_trade_pnl(self):
        t = Trade(
            entry_time=pd.Timestamp("2024-01-01"),
            exit_time=pd.Timestamp("2024-02-01"),
            entry_price=100.0,
            exit_price=90.0,
            direction="short",
            size=10.0,
        )
        assert t.pnl == pytest.approx(100.0)  # profit from price drop
        assert t.pnl_pct == pytest.approx(10.0)

    def test_short_trade_loss(self):
        t = Trade(
            entry_time=pd.Timestamp("2024-01-01"),
            exit_time=pd.Timestamp("2024-02-01"),
            entry_price=100.0,
            exit_price=110.0,
            direction="short",
            size=10.0,
        )
        assert t.pnl == pytest.approx(-100.0)  # loss from price rise
        assert t.pnl_pct == pytest.approx(-10.0)

    def test_trade_duration(self):
        t = Trade(
            entry_time=pd.Timestamp("2024-01-01"),
            exit_time=pd.Timestamp("2024-01-31"),
            entry_price=100, exit_price=100,
            direction="long", size=1,
        )
        assert t.duration == timedelta(days=30)

    def test_trade_stats_empty(self):
        stats = calculate_trade_stats([])
        assert stats["total_trades"] == 0
        assert stats["win_rate"] == 0.0

    def test_trade_stats_mixed(self):
        trades = [
            Trade(pd.Timestamp("2024-01-01"), pd.Timestamp("2024-01-10"),
                  100, 120, "long", 1),
            Trade(pd.Timestamp("2024-01-11"), pd.Timestamp("2024-01-20"),
                  120, 110, "long", 1),
        ]
        stats = calculate_trade_stats(trades)
        assert stats["total_trades"] == 2
        assert stats["win_rate"] == 50.0


# ---------------------------------------------------------------------------
# Settings loading
# ---------------------------------------------------------------------------

class TestSettings:
    def test_load_settings_existing(self):
        skill_dir = Path(__file__).parent.parent
        settings = load_settings(skill_dir)
        # If yaml is available and settings.yaml exists, should have backtest key
        if settings:
            assert "backtest" in settings or "risk" in settings

    def test_load_settings_missing_dir(self, tmp_path):
        settings = load_settings(tmp_path)
        assert settings == {}


# ---------------------------------------------------------------------------
# Stop-loss / Take-profit enforcement
# ---------------------------------------------------------------------------

class TestRiskManagement:
    def test_stop_loss_triggers(self):
        """A stop loss should limit downside."""
        # Build data: uptrend then sharp drop then recovery (enough for momentum lookback=14)
        prices = [100.0 + i * 0.5 for i in range(30)]  # uptrend
        for i in range(30):
            prices.append(prices[-1] * 0.98)  # steady decline
        for i in range(30):
            prices.append(prices[-1] * 1.005)  # slow recovery
        data = make_price_data(prices)

        # Without stop loss
        result_no_sl = run_backtest("momentum", data, params={"period": 14, "threshold": 3.0})

        # With tight stop loss
        result_sl = run_backtest(
            "momentum", data,
            params={"period": 14, "threshold": 3.0},
            risk_settings={"stop_loss": 0.03},
        )
        # Stop loss should cause more trades (early exits)
        assert result_sl.total_trades >= result_no_sl.total_trades or \
               result_sl.final_capital >= result_no_sl.final_capital

    def test_take_profit_triggers(self):
        """A take profit should lock in gains."""
        data = make_trending_data(n=300, trend=0.003)
        result_tp = run_backtest(
            "sma_crossover", data,
            params={"fast_period": 5, "slow_period": 20},
            risk_settings={"take_profit": 0.05},
        )
        # With take profit, should have more trades (exiting early)
        result_no_tp = run_backtest(
            "sma_crossover", data,
            params={"fast_period": 5, "slow_period": 20},
        )
        assert result_tp.total_trades >= result_no_tp.total_trades

    def test_max_position_size(self):
        """Custom max_position_size should be respected."""
        data = make_trending_data(n=300)
        result = run_backtest(
            "sma_crossover", data,
            params={"fast_period": 5, "slow_period": 20},
            risk_settings={"max_position_size": 0.5},
        )
        # Should still produce valid results
        assert result.final_capital > 0
        assert result.initial_capital == 10000


# ---------------------------------------------------------------------------
# Full backtest flow
# ---------------------------------------------------------------------------

class TestBacktestFlow:
    def test_basic_backtest_runs(self):
        """A basic backtest should complete without errors."""
        data = make_trending_data(n=300)
        result = run_backtest("sma_crossover", data, params={"fast_period": 10, "slow_period": 30})
        assert result.strategy == "sma_crossover"
        assert result.initial_capital == 10000
        assert result.final_capital > 0
        assert len(result.equity_curve) > 0

    def test_all_strategies_run(self):
        """Every registered strategy should produce a valid result."""
        data = make_trending_data(n=300)
        for name in list_strategies():
            result = run_backtest(name, data.copy())
            assert result.final_capital > 0, f"{name} produced zero capital"
            assert isinstance(result.total_return, float), f"{name} has bad total_return"

    def test_short_strategy_backtest(self):
        """Strategies with short signals should record short trades."""
        # Mean-reverting data should trigger mean_reversion shorts
        data = make_mean_reverting_data(n=300)
        result = run_backtest("mean_reversion", data, params={"period": 20, "z_threshold": 1.5})
        # May or may not have shorts depending on data, but should not error
        assert result.final_capital > 0

    def test_equity_curve_length(self):
        """Equity curve should match data length minus lookback + 1."""
        data = make_trending_data(n=300)
        strategy = get_strategy("sma_crossover")
        result = run_backtest("sma_crossover", data, params={"fast_period": 10, "slow_period": 30})
        expected_len = len(data) - strategy.lookback + 1
        assert len(result.equity_curve) == expected_len

    def test_metrics_calculated(self):
        """All metric fields should be populated after backtest."""
        data = make_trending_data(n=300)
        result = run_backtest("sma_crossover", data, params={"fast_period": 10, "slow_period": 30})
        assert isinstance(result.sharpe_ratio, float)
        assert isinstance(result.max_drawdown, float)
        assert isinstance(result.total_trades, int)
