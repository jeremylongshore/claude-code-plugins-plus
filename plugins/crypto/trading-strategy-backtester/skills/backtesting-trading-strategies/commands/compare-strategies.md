---
name: compare-strategies
description: Compare multiple strategy backtests side by side
allowed-tools: Read, Write, Edit, Bash(python:*)
---

# /compare-strategies

Run multiple strategies on the same data and compare performance side by side.

## Usage

```
/compare-strategies <symbol> [strategies...] [options]
```

## Workflow

1. Fetch data once for the symbol and period
2. Run each strategy with its default (or specified) parameters
3. Collect results into a comparison table
4. Rank by chosen metric

## Example Script

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path("${CLAUDE_SKILL_DIR}/scripts")))

from backtest import load_data, run_backtest
from fetch_data import parse_period
from datetime import datetime

# Configuration
symbol = "BTC-USD"
strategies = ["sma_crossover", "ema_crossover", "rsi_reversal", "macd",
              "bollinger_bands", "breakout", "mean_reversion", "momentum"]
end = datetime.now()
start = end - parse_period("1y")

# Load data once
data_dir = Path("${CLAUDE_SKILL_DIR}/data")
data = load_data(symbol, start, end, data_dir)
data.attrs["symbol"] = symbol

# Run all strategies
results = []
for name in strategies:
    try:
        result = run_backtest(strategy_name=name, data=data.copy())
        results.append(result)
        print(f"{name:20s}  Return: {result.total_return:+8.2f}%  "
              f"Sharpe: {result.sharpe_ratio:6.2f}  "
              f"MaxDD: {result.max_drawdown:+8.2f}%  "
              f"Trades: {result.total_trades}")
    except Exception as e:
        print(f"{name:20s}  ERROR: {e}")

# Sort by Sharpe ratio
results.sort(key=lambda r: r.sharpe_ratio, reverse=True)
print(f"\nBest strategy: {results[0].strategy} (Sharpe: {results[0].sharpe_ratio:.2f})")
```

## CLI Approach

Run individual backtests and compare the summary files:

```bash
for strategy in sma_crossover ema_crossover rsi_reversal macd bollinger_bands; do
  python ${CLAUDE_SKILL_DIR}/scripts/backtest.py \
    --strategy $strategy --symbol BTC-USD --period 1y --quiet
done
```

## What to Compare

| Metric | What It Tells You |
|--------|-------------------|
| Sharpe Ratio | Best risk-adjusted return |
| Total Return | Raw profitability |
| Max Drawdown | Worst-case pain |
| Win Rate | Consistency |
| Profit Factor | Reward-to-risk per trade |
| Total Trades | Activity level / costs |

## Tips

- Always compare on the same data range and capital
- A strategy with fewer trades but higher Sharpe may be preferable to one with high return but deep drawdowns
- Consider combining uncorrelated strategies for portfolio diversification
- Use `/optimize-parameters` on the top 2-3 strategies for fine-tuning
