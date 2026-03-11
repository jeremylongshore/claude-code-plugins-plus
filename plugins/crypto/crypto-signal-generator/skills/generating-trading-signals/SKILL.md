---
name: generating-trading-signals
description: |
  Generate trading signals using technical indicators (RSI, MACD, Bollinger Bands, etc.).
  Combines multiple indicators into composite signals with confidence scores.
  Use when analyzing assets for trading opportunities or checking technical indicators.
  Trigger with phrases like "get trading signals", "check indicators", "analyze for entry",
  "scan for opportunities", "generate buy/sell signals", or "technical analysis".
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(python:*)
version: 2.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# Generating Trading Signals

## Overview

Multi-indicator signal generation system that analyzes price action using 7 technical indicators and produces composite BUY/SELL signals with confidence scores and risk management levels.

**Indicators Used:**
- RSI (Relative Strength Index) - Overbought/oversold
- MACD (Moving Average Convergence Divergence) - Trend and momentum
- Bollinger Bands - Mean reversion and volatility
- Trend (SMA 20/50/200 crossovers) - Trend direction
- Volume - Confirmation of moves
- Stochastic Oscillator - Short-term momentum
- ADX (Average Directional Index) - Trend strength

## Prerequisites

Install required dependencies:

```bash
set -euo pipefail
pip install yfinance pandas numpy
```

Optional for visualization:
```bash
set -euo pipefail
pip install matplotlib
```

## Instructions

### Step 1: Quick Signal Scan

Scan multiple assets for trading opportunities:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/scanner.py --watchlist crypto_top10 --period 6m
```

Output shows signal type (STRONG_BUY/BUY/NEUTRAL/SELL/STRONG_SELL) and confidence for each asset.

### Step 2: Detailed Signal Analysis

Get full indicator breakdown for a specific symbol:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/scanner.py --symbols BTC-USD --detail
```

Shows each indicator's contribution:
- Individual signal (BUY/SELL/NEUTRAL)
- Indicator value
- Reasoning (e.g., "RSI oversold at 28.5")

### Step 3: Filter and Rank Signals

Find the best opportunities:

```bash
# Only buy signals with 70%+ confidence
python ${CLAUDE_SKILL_DIR}/scripts/scanner.py --filter buy --min-confidence 70 --rank confidence

# Rank by most bullish
python ${CLAUDE_SKILL_DIR}/scripts/scanner.py --rank bullish

# Save results to JSON
python ${CLAUDE_SKILL_DIR}/scripts/scanner.py --output signals.json
```

### Step 4: Use Custom Watchlists

Available predefined watchlists:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/scanner.py --list-watchlists
python ${CLAUDE_SKILL_DIR}/scripts/scanner.py --watchlist crypto_defi
```

Watchlists: `crypto_top10`, `crypto_defi`, `crypto_layer2`, `stocks_tech`, `etfs_major`

## Output

### Signal Summary Table

```
================================================================================
  SIGNAL SCANNER RESULTS
================================================================================

  Symbol       Signal         Confidence          Price    Stop Loss
--------------------------------------------------------------------------------
  BTC-USD      STRONG_BUY          78.5%     $67,234.00  $64,890.00
  ETH-USD      BUY                 62.3%      $3,456.00   $3,312.00
  SOL-USD      NEUTRAL             45.0%        $142.50         N/A
--------------------------------------------------------------------------------

  Summary: 2 Buy | 1 Neutral | 0 Sell
  Scanned: 3 assets | [timestamp]
================================================================================
```

### Detailed Signal Output

```
======================================================================
  BTC-USD - STRONG_BUY
  Confidence: 78.5% | Price: $67,234.00
======================================================================

  Risk Management:
    Stop Loss:   $64,890.00
    Take Profit: $71,922.00
    Risk/Reward: 1:2.0

  Signal Components:
----------------------------------------------------------------------
    RSI              | STRONG_BUY   | Oversold at 28.5 (< 30)
    MACD             | BUY          | MACD above signal, positive momentum
    Bollinger Bands  | BUY          | Price near lower band (%B = 0.15)
    Trend            | BUY          | Uptrend: price above key MAs
    Volume           | STRONG_BUY   | High volume (2.3x) on up move
    Stochastic       | STRONG_BUY   | Oversold (%K=18.2, %D=21.5)
    ADX              | BUY          | Strong uptrend (ADX=32.1)
----------------------------------------------------------------------
```

### Signal Types

| Signal | Score | Meaning |
|--------|-------|---------|
| STRONG_BUY | +2 | Multiple strong buy signals aligned |
| BUY | +1 | Moderate buy signals |
| NEUTRAL | 0 | No clear direction |
| SELL | -1 | Moderate sell signals |
| STRONG_SELL | -2 | Multiple strong sell signals aligned |

### Confidence Interpretation

| Confidence | Interpretation |
|------------|----------------|
| 70-100% | High conviction, strong signal |
| 50-70% | Moderate conviction |
| 30-50% | Weak signal, mixed indicators |
| 0-30% | No clear direction, avoid trading |

## Configuration

Edit `${CLAUDE_SKILL_DIR}/config/settings.yaml`:

```yaml
indicators:
  rsi:
    period: 14
    overbought: 70
    oversold: 30

signals:
  weights:
    rsi: 1.0
    macd: 1.0
    bollinger: 1.0
    trend: 1.0
    volume: 0.5
```

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for common issues:
- API rate limits
- Insufficient data handling
- Network errors

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples:
- Multi-timeframe analysis
- Custom indicator parameters
- Combining with backtester
- Automated scanning schedules

## Integration with Backtester

Test signals historically:

```bash
# Generate signal
python ${CLAUDE_SKILL_DIR}/scripts/scanner.py --symbols BTC-USD --detail

# Backtest the strategy that generated the signal
python ${CLAUDE_SKILL_DIR}/../trading-strategy-backtester/skills/backtesting-trading-strategies/scripts/backtest.py \
  --strategy rsi_reversal --symbol BTC-USD --period 1y
```

## Files

| File | Purpose |
|------|---------|
| `scripts/scanner.py` | Main signal scanner |
| `scripts/signals.py` | Signal generation logic |
| `scripts/indicators.py` | Technical indicator calculations |
| `config/settings.yaml` | Configuration |

## Resources

- yfinance for price data
- pandas/numpy for calculations
- Compatible with trading-strategy-backtester plugin