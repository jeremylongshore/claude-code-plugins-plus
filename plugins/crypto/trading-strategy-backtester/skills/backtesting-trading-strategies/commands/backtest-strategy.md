---
name: backtest-strategy
description: Run a trading strategy backtest against historical price data
allowed-tools: Read, Write, Edit, Bash(python:*)
---

# /backtest-strategy

Run a complete backtest of a trading strategy against historical data.

## Usage

```
/backtest-strategy <strategy_name> <symbol> [options]
```

## Core Architecture

The backtester uses three key types:

```python
from dataclasses import dataclass

@dataclass
class Signal:
    """Returned by every strategy on each bar."""
    entry: bool = False       # True to open a position
    exit: bool = False        # True to close a position
    direction: str = "long"   # "long" or "short"
    strength: float = 1.0     # 0-1 confidence

class Strategy(ABC):
    name: str
    lookback: int  # minimum bars needed

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame, params: dict) -> Signal:
        ...
```

The engine calls `run_backtest()`:

```python
def run_backtest(
    strategy_name: str,
    data: pd.DataFrame,
    initial_capital: float = 10000,
    params: dict = None,
    commission: float = 0.001,
    slippage: float = 0.0005,
    risk_settings: dict = None,  # stop_loss, take_profit, max_position_size
) -> BacktestResult:
```

## Examples

Basic SMA crossover backtest:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/backtest.py \
  --strategy sma_crossover --symbol BTC-USD --period 1y
```

RSI reversal with custom parameters and $50k capital:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/backtest.py \
  --strategy rsi_reversal --symbol ETH-USD --period 6m \
  --capital 50000 \
  --params '{"period": 14, "overbought": 75, "oversold": 25}'
```

Specific date range with low commission:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/backtest.py \
  --strategy macd --symbol SOL-USD \
  --start 2024-01-01 --end 2025-01-01 \
  --commission 0.0005 --slippage 0.0002
```

List all available strategies:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/backtest.py --list
```

## Available Strategies

| Strategy | Direction | Key Parameters |
|----------|-----------|----------------|
| `sma_crossover` | Long only | `fast_period`, `slow_period` |
| `ema_crossover` | Long only | `fast_period`, `slow_period` |
| `rsi_reversal` | Long + Short | `period`, `overbought`, `oversold` |
| `macd` | Long + Short | `fast`, `slow`, `signal` |
| `bollinger_bands` | Long + Short | `period`, `std_dev` |
| `breakout` | Long only | `lookback`, `threshold` |
| `mean_reversion` | Long + Short | `period`, `z_threshold` |
| `momentum` | Long only | `period`, `threshold` |

## Configuration

Settings are loaded from `${CLAUDE_SKILL_DIR}/config/settings.yaml` with this priority:

1. CLI arguments (highest)
2. `settings.yaml` values
3. Hardcoded defaults (lowest)

Risk management keys in `settings.yaml`:

```yaml
risk:
  max_position_size: 0.95   # fraction of cash per trade
  stop_loss: 0.05           # 5% stop loss (null to disable)
  take_profit: 0.15         # 15% take profit (null to disable)
```

## Output

Results are saved to `${CLAUDE_SKILL_DIR}/reports/`:
- `*_summary.txt` -- Performance metrics table
- `*_trades.csv` -- Trade log with entry/exit times, PnL
- `*_equity.csv` -- Equity curve data
- `*_chart.png` -- Equity curve + drawdown chart (requires matplotlib)
