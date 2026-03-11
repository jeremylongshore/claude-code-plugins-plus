# Generating Trading Signals - Implementation Reference

## Detailed Output Formats

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

## Signal Types Reference

| Signal | Score | Meaning |
|--------|-------|---------|
| STRONG_BUY | +2 | Multiple strong buy signals aligned |
| BUY | +1 | Moderate buy signals |
| NEUTRAL | 0 | No clear direction |
| SELL | -1 | Moderate sell signals |
| STRONG_SELL | -2 | Multiple strong sell signals aligned |

## Confidence Interpretation

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
