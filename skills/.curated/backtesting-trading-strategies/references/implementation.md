# Implementation Guide

## Overview

This guide covers implementing and extending the backtesting system.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   fetch_data    │────▶│    backtest     │────▶│    metrics      │
│   (data layer)  │     │   (engine)      │     │   (analysis)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │   strategies    │
                        │  (signal gen)   │
                        └─────────────────┘
```

## Step 1: Install Dependencies

```bash
pip install pandas numpy yfinance matplotlib

# Optional for advanced features:
pip install ta-lib scipy scikit-learn
```

## Step 2: Fetch Historical Data

```bash
# Fetch 2 years of daily BTC data
python scripts/fetch_data.py --symbol BTC-USD --period 2y --interval 1d

# Fetch specific date range
python scripts/fetch_data.py --symbol ETH-USD --start 2022-01-01 --end 2024-01-01

# Use CoinGecko for crypto (no Yahoo Finance ticker needed)
python scripts/fetch_data.py --symbol BTC --period 1y --source coingecko
```

Data is cached in `data/{symbol}_{interval}.csv`.

## Step 3: Run Backtest

```bash
# Basic backtest
python scripts/backtest.py --strategy sma_crossover --symbol BTC-USD --period 1y

# With custom parameters
python scripts/backtest.py \
  --strategy rsi_reversal \
  --symbol ETH-USD \
  --period 6m \
  --capital 25000 \
  --params '{"period": 14, "overbought": 75, "oversold": 25}'

# Custom commission and slippage
python scripts/backtest.py \
  --strategy macd \
  --symbol SOL-USD \
  --period 1y \
  --commission 0.002 \
  --slippage 0.001
```

## Step 4: Optimize Parameters

```bash
# Grid search for SMA crossover
python scripts/optimize.py \
  --strategy sma_crossover \
  --symbol BTC-USD \
  --period 1y \
  --param-grid '{"fast_period": [10, 20, 30, 50], "slow_period": [50, 100, 150, 200]}'

# Optimize RSI parameters
python scripts/optimize.py \
  --strategy rsi_reversal \
  --symbol ETH-USD \
  --param-grid '{"period": [7, 14, 21], "overbought": [70, 75, 80], "oversold": [20, 25, 30]}'
```

## Step 5: Analyze Results

Results are saved to `reports/` directory:

- `*_summary.txt` - Performance metrics table
- `*_trades.csv` - Trade log with entry/exit details
- `*_equity.csv` - Equity curve data
- `*_chart.png` - Visual equity curve and drawdown

## Adding Custom Strategies

Create a new strategy by extending the base class:

```python
# In scripts/strategies.py

class MyCustomStrategy(Strategy):
    """My custom trading strategy."""

    name = "my_strategy"
    lookback = 50  # Minimum bars needed

    def generate_signals(self, data: pd.DataFrame, params: Dict[str, Any]) -> Signal:
        # Your signal logic here
        threshold = params.get("threshold", 0.02)

        close = data["close"]
        returns = close.pct_change()

        # Example: buy after big drop, sell after big gain
        if returns.iloc[-1] < -threshold:
            return Signal(entry=True, direction="long")
        elif returns.iloc[-1] > threshold:
            return Signal(exit=True)

        return Signal()

# Register in STRATEGIES dict
STRATEGIES["my_strategy"] = MyCustomStrategy()
```

## Configuration Options

Create `config/settings.yaml`:

```yaml
data:
  provider: yfinance
  cache_dir: ./data
  default_interval: 1d

backtest:
  default_capital: 10000
  commission: 0.001      # 0.1% per trade
  slippage: 0.0005       # 0.05% slippage

risk:
  max_position_size: 0.95  # 95% of capital
  stop_loss: null          # Optional fixed stop loss
  take_profit: null        # Optional fixed take profit

reporting:
  output_dir: ./reports
  save_trades: true
  save_equity: true
  save_chart: true
```

## Performance Tips

1. **Cache data**: Fetch once, reuse for multiple backtests
2. **Use appropriate intervals**: Daily for swing trading, hourly for day trading
3. **Test on out-of-sample data**: Split data into train/test periods
4. **Watch for overfitting**: Simpler strategies often generalize better
5. **Account for costs**: Commission + slippage can erode profits significantly

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
