---
name: walk-forward
description: Rolling window optimization with out-of-sample validation
allowed-tools: Read, Write, Edit, Bash(python:*)
---

# /walk-forward

Perform walk-forward analysis: optimize parameters on rolling in-sample windows, then validate on out-of-sample data to detect overfitting.

## Usage

```
/walk-forward <strategy> <symbol> <param_grid> [options]
```

## How It Works

1. Divide historical data into rolling windows (e.g., 12-month in-sample + 3-month out-of-sample)
2. For each window: optimize parameters on in-sample data
3. Apply best parameters to the out-of-sample period
4. Stitch out-of-sample results together for a realistic performance estimate

## Example Script

```python
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path("${CLAUDE_SKILL_DIR}/scripts")))

from backtest import load_data, run_backtest
from optimize import grid_search
from fetch_data import parse_period

# Configuration
symbol = "BTC-USD"
strategy = "sma_crossover"
param_grid = {"fast_period": [10, 20, 30], "slow_period": [50, 100, 200]}
in_sample_months = 12
out_of_sample_months = 3
total_years = 3

# Load full dataset
end = datetime.now()
start = end - parse_period(f"{total_years}y")
data_dir = Path("${CLAUDE_SKILL_DIR}/data")
full_data = load_data(symbol, start, end, data_dir)
full_data.attrs["symbol"] = symbol

# Walk-forward loop
window_start = start
oos_results = []

while window_start + timedelta(days=(in_sample_months + out_of_sample_months) * 30) <= end:
    is_end = window_start + timedelta(days=in_sample_months * 30)
    oos_end = is_end + timedelta(days=out_of_sample_months * 30)

    # In-sample data
    is_data = full_data[(full_data.index >= str(window_start.date())) &
                        (full_data.index < str(is_end.date()))].copy()
    is_data.attrs["symbol"] = symbol

    # Optimize on in-sample
    opt_df = grid_search(strategy, is_data, param_grid)
    if len(opt_df) == 0:
        window_start = is_end
        continue

    best_params = {col: opt_df.iloc[0][col]
                   for col in param_grid.keys()}

    # Out-of-sample data
    oos_data = full_data[(full_data.index >= str(is_end.date())) &
                         (full_data.index < str(oos_end.date()))].copy()
    oos_data.attrs["symbol"] = symbol

    if len(oos_data) < 20:
        window_start = is_end
        continue

    # Test on out-of-sample
    oos_result = run_backtest(strategy, oos_data, params=best_params)
    oos_results.append({
        "window": f"{window_start.date()} to {oos_end.date()}",
        "best_params": best_params,
        "is_sharpe": opt_df.iloc[0].get("sharpe_ratio", 0),
        "oos_return": oos_result.total_return,
        "oos_sharpe": oos_result.sharpe_ratio,
        "oos_max_dd": oos_result.max_drawdown,
    })
    print(f"Window {window_start.date()}-{oos_end.date()}: "
          f"IS Sharpe={opt_df.iloc[0].get('sharpe_ratio', 0):.2f}  "
          f"OOS Return={oos_result.total_return:+.2f}%  "
          f"OOS Sharpe={oos_result.sharpe_ratio:.2f}")

    window_start = is_end

# Summary
if oos_results:
    avg_oos_return = sum(r["oos_return"] for r in oos_results) / len(oos_results)
    avg_oos_sharpe = sum(r["oos_sharpe"] for r in oos_results) / len(oos_results)
    print(f"\nWalk-Forward Summary ({len(oos_results)} windows):")
    print(f"  Avg OOS Return: {avg_oos_return:+.2f}%")
    print(f"  Avg OOS Sharpe: {avg_oos_sharpe:.2f}")
```

## Interpreting Results

| Signal | Meaning |
|--------|---------|
| IS Sharpe >> OOS Sharpe | Overfitting -- parameters don't generalize |
| IS Sharpe ~ OOS Sharpe | Robust -- strategy is stable |
| OOS returns consistently negative | Strategy doesn't work in live conditions |
| Optimal params change every window | Unstable strategy, avoid |

## Tips

- Use at least 3-5 out-of-sample windows for statistical significance
- In-sample should be 3-4x longer than out-of-sample
- If walk-forward degrades badly vs. single-period optimization, the strategy is overfit
- Combine with `/compare-strategies` to find the most robust strategy first
