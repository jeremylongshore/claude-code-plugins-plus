# Examples

## Example 1: Quick Market Scan

Scan top crypto for trading opportunities:

```bash
python scripts/scanner.py --watchlist crypto_top10
```

**Expected Output:**

```
Scanning BTC-USD... BUY (62%)
Scanning ETH-USD... NEUTRAL (45%)
Scanning BNB-USD... SELL (58%)
Scanning SOL-USD... STRONG_BUY (78%)
...

================================================================================
  SIGNAL SCANNER RESULTS
================================================================================

  Symbol       Signal         Confidence          Price    Stop Loss
--------------------------------------------------------------------------------
  BTC-USD      BUY                 62.3%     $67,234.00  $64,890.00
  ETH-USD      NEUTRAL             45.0%      $3,456.00         N/A
  BNB-USD      SELL                58.2%        $312.50     $328.00
  SOL-USD      STRONG_BUY          78.5%        $142.00     $132.50
--------------------------------------------------------------------------------

  Summary: 2 Buy | 1 Neutral | 1 Sell
  Scanned: 4 assets | 2024-01-15 14:30
================================================================================
```

## Example 2: Detailed Signal Breakdown

Get full indicator analysis for BTC:

```bash
python scripts/scanner.py --symbols BTC-USD --detail
```

**Expected Output:**

```
======================================================================
  BTC-USD - BUY
  Confidence: 62.3% | Price: $67,234.00
======================================================================

  Risk Management:
    Stop Loss:   $64,890.00
    Take Profit: $71,922.00
    Risk/Reward: 1:2.0

  Signal Components:
----------------------------------------------------------------------
    RSI              | BUY          | Approaching oversold at 38.2
    MACD             | BUY          | MACD above signal, positive momentum
    Bollinger Bands  | NEUTRAL      | Price in middle of bands (%B = 0.45)
    Trend            | BUY          | Uptrend: price above key moving averages
    Volume           | NEUTRAL      | Normal volume (1.1x average)
    Stochastic       | BUY          | Approaching oversold (%K=28.5)
    ADX              | NEUTRAL      | Weak/no trend (ADX=18.2)
----------------------------------------------------------------------
  Generated: 2024-01-15 14:30:00
```

## Example 3: Find Buy Opportunities

Filter for high-confidence buy signals:

```bash
python scripts/scanner.py \
  --watchlist crypto_top10 \
  --filter buy \
  --min-confidence 70 \
  --rank confidence
```

**Expected Output:**

```
================================================================================
  SIGNAL SCANNER RESULTS
================================================================================

  Symbol       Signal         Confidence          Price    Stop Loss
--------------------------------------------------------------------------------
  SOL-USD      STRONG_BUY          78.5%        $142.00     $132.50
  AVAX-USD     BUY                 72.1%         $38.50      $35.20
--------------------------------------------------------------------------------

  Summary: 2 Buy | 0 Neutral | 0 Sell
```

## Example 4: DeFi Token Scan

Scan DeFi tokens for opportunities:

```bash
python scripts/scanner.py --watchlist crypto_defi --period 3m
```

## Example 5: Export to JSON

Save results for further processing:

```bash
python scripts/scanner.py \
  --symbols BTC-USD,ETH-USD,SOL-USD \
  --output signals_$(date +%Y%m%d).json
```

**Output file (signals_20240115.json):**

```json
{
  "generated_at": "2024-01-15T14:30:00",
  "count": 3,
  "signals": [
    {
      "symbol": "BTC-USD",
      "timestamp": "2024-01-15",
      "signal": "BUY",
      "confidence": 62.3,
      "price": 67234.00,
      "stop_loss": 64890.00,
      "take_profit": 71922.00,
      "risk_reward": 2.0,
      "components": [
        {
          "name": "RSI",
          "signal": "BUY",
          "value": 38.2,
          "reasoning": "Approaching oversold at 38.2"
        }
      ]
    }
  ]
}
```

## Example 6: Custom Parameters

Use different indicator settings:

```bash
# More aggressive RSI thresholds
python scripts/scanner.py \
  --symbols BTC-USD \
  --detail
```

Then modify `config/settings.yaml`:

```yaml
indicators:
  rsi:
    oversold: 25    # More extreme for signals
    overbought: 75
```

## Example 7: Multi-Asset Comparison

Compare signals across asset classes:

```bash
# Crypto
python scripts/scanner.py --watchlist crypto_top10 --output crypto.json

# Tech stocks
python scripts/scanner.py --watchlist stocks_tech --output stocks.json

# Compare
cat crypto.json stocks.json | jq -s '.[].signals[] | {symbol, signal, confidence}'
```

## Example 8: Bearish Ranking

Find short opportunities:

```bash
python scripts/scanner.py \
  --watchlist crypto_top10 \
  --filter sell \
  --rank bearish
```

## Example 9: Integration with Backtester

Test a signal historically:

```bash
# 1. Get current signal for SOL
python scripts/scanner.py --symbols SOL-USD --detail

# Output shows: STRONG_BUY with RSI oversold

# 2. Backtest RSI strategy on SOL
cd ../trading-strategy-backtester/skills/backtesting-trading-strategies/scripts
python backtest.py --strategy rsi_reversal --symbol SOL-USD --period 1y
```

## Example 10: Watchlist Management

List available watchlists:

```bash
python scripts/scanner.py --list-watchlists
```

**Output:**

```
Available watchlists:
  crypto_top10: BTC-USD, ETH-USD, BNB-USD... (10 symbols)
  crypto_defi: UNI-USD, AAVE-USD, MKR-USD... (7 symbols)
  crypto_layer2: MATIC-USD, OP-USD, ARB-USD... (5 symbols)
  stocks_tech: AAPL, MSFT, GOOGL... (10 symbols)
  etfs_major: SPY, QQQ, IWM... (5 symbols)
```

## Example 11: Morning Scan Routine

Daily market analysis:

```bash
#!/bin/bash
# morning_scan.sh

DATE=$(date +%Y%m%d)
OUTDIR=~/trading/signals/$DATE

mkdir -p $OUTDIR

# Scan all watchlists
for list in crypto_top10 crypto_defi stocks_tech; do
  python scripts/scanner.py \
    --watchlist $list \
    --min-confidence 60 \
    --output $OUTDIR/${list}.json
done

# Summarize best opportunities
echo "=== TOP OPPORTUNITIES ==="
cat $OUTDIR/*.json | jq -s '
  [.[].signals[]] |
  sort_by(.confidence) |
  reverse |
  .[:5] |
  .[] |
  "\(.symbol): \(.signal) (\(.confidence)%)"
'
```

## Example 12: Quiet Mode for Scripts

Minimal output for automation:

```bash
python scripts/scanner.py \
  --watchlist crypto_top10 \
  --quiet \
  --output signals.json

# Check if any strong signals
STRONG=$(cat signals.json | jq '[.signals[] | select(.signal == "STRONG_BUY" or .signal == "STRONG_SELL")] | length')
echo "Found $STRONG strong signals"
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
