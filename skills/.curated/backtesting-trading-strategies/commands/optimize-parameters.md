---
name: optimize-parameters
description: Grid search to find optimal strategy parameters
allowed-tools: Read, Write, Edit, Bash(python:*)
---

# /optimize-parameters

Find optimal strategy parameters via grid search over historical data.

## Usage

```
/optimize-parameters <strategy_name> <symbol> <param_grid> [options]
```

## How It Works

The optimizer in `${CLAUDE_SKILL_DIR}/scripts/optimize.py` runs a full backtest for every combination of parameters in your grid, ranks results by a target metric (default: Sharpe ratio), and reports the top performers.

## Examples

Optimize SMA crossover periods:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/optimize.py \
  --strategy sma_crossover --symbol BTC-USD --period 2y \
  --param-grid '{"fast_period": [10, 15, 20, 30], "slow_period": [50, 100, 150, 200]}'
```

Optimize RSI thresholds targeting win rate:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/optimize.py \
  --strategy rsi_reversal --symbol ETH-USD --period 1y \
  --param-grid '{"period": [7, 14, 21], "overbought": [65, 70, 75], "oversold": [25, 30, 35]}' \
  --metric win_rate
```

Optimize with custom capital and output:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/optimize.py \
  --strategy macd --symbol SOL-USD --period 1y \
  --param-grid '{"fast": [8, 12, 16], "slow": [20, 26, 32], "signal": [7, 9, 11]}' \
  --capital 50000 --output ./my-reports
```

## Options

| Flag | Description | Default |
|------|-------------|---------|
| `--strategy` | Strategy name | Required |
| `--symbol` | Trading symbol | Required |
| `--param-grid` | JSON dict of param lists | Required |
| `--period` | Lookback period | `1y` |
| `--start/--end` | Explicit date range | -- |
| `--capital` | Starting capital | `10000` |
| `--metric` | Sort/rank metric | `sharpe_ratio` |
| `--output` | Output directory | `${CLAUDE_SKILL_DIR}/reports` |

## Available Metrics

`total_return`, `sharpe_ratio`, `sortino_ratio`, `max_drawdown`, `win_rate`, `profit_factor`, `calmar_ratio`, `total_trades`

## Output

- Console table of top 10 parameter combinations
- `optimization_<strategy>_<timestamp>.csv` -- Full results grid
- `optimization_<strategy>_<timestamp>.txt` -- Formatted summary

## Tips

- Start with coarse grids, then narrow around promising values
- Use at least 1-2 years of data to avoid overfitting
- Watch for parameter sets that have very few trades (unreliable statistics)
- Compare in-sample optimization with out-of-sample validation (see `/walk-forward`)
