# Usage Examples

Comprehensive examples for the scanning-market-movers skill.

## Quick Start Examples

### Example 1: Default Market Scan

The simplest use case - scan for significant movers:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/scanner.py
```

**Output:**
```
================================================================================
  MARKET MOVERS                                    Updated: 2025-01-14 15:30:00
================================================================================

  TOP GAINERS (24h)
--------------------------------------------------------------------------------
  Rank  Symbol      Price         Change    Vol Ratio   Market Cap    Score
--------------------------------------------------------------------------------
    1   ABC       $1.234        +45.67%        5.2x      $123.4M      89.3
    2   DEF       $0.567        +32.10%        3.8x       $45.6M      76.5
    3   GHI       $2.890        +28.45%        2.9x      $234.5M      71.2
--------------------------------------------------------------------------------

  TOP LOSERS (24h)
--------------------------------------------------------------------------------
  Rank  Symbol      Price         Change    Vol Ratio   Market Cap    Score
--------------------------------------------------------------------------------
    1   JKL       $3.456        -28.90%        4.1x       $89.1M      72.1
    2   MNO       $0.123        -22.34%        2.5x       $12.3M      58.9
--------------------------------------------------------------------------------

  Summary: 40 movers shown | Scanned: 1000 assets | Matched: 127
================================================================================
```

---

### Example 2: High-Volume Spikes Only

Find assets with extreme volume spikes:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/scanner.py --volume-spike 5 --min-volume 1000000
```

This finds assets with:
- Volume at least 5x normal
- Minimum $1M daily volume

---

### Example 3: Large Cap Movers

Focus on established assets only:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/scanner.py --min-cap 1000000000
```

Only shows assets with > $1B market cap.

---

## Threshold Customization

### Example 4: Aggressive Settings

Find even small moves:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/scanner.py --min-change 3 --volume-spike 1.5 --top 50
```

Lower thresholds = more results.

### Example 5: Conservative Settings

Only significant moves:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/scanner.py --min-change 15 --volume-spike 4 --min-cap 500000000
```

Higher thresholds = fewer, higher-quality results.

### Example 6: Mid-Cap Focus

Find mid-cap opportunities:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/scanner.py --min-cap 50000000 --max-cap 500000000
```

Market cap between $50M and $500M.

---

## Category Filtering

### Example 7: DeFi Movers

```bash
python ${CLAUDE_SKILL_DIR}/scripts/scanner.py --category defi
```

Only DeFi protocol tokens.

### Example 8: Layer 2 Movers

```bash
python ${CLAUDE_SKILL_DIR}/scripts/scanner.py --category layer2
```

Arbitrum, Optimism, Polygon ecosystem tokens.

### Example 9: Meme Coins

```bash
python ${CLAUDE_SKILL_DIR}/scripts/scanner.py --category meme --min-change 20
```

Meme tokens with significant moves (warning: high risk).

---

## Timeframe Options

### Example 10: Hourly Movers

```bash
python ${CLAUDE_SKILL_DIR}/scripts/scanner.py --timeframe 1h
```

Changes in the last hour.

### Example 11: Weekly Movers

```bash
python ${CLAUDE_SKILL_DIR}/scripts/scanner.py --timeframe 7d
```

Weekly change perspective.

---

## Output Formats

### Example 12: JSON Export

For programmatic processing:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/scanner.py --format json --output movers.json
```

**Output (movers.json):**
```json
{
  "gainers": [
    {
      "rank": 1,
      "symbol": "ABC",
      "name": "ABC Token",
      "price": 1.234,
      "change": 45.67,
      "volume_ratio": 5.2,
      "market_cap": 123400000,
      "significance_score": 89.3
    }
  ],
  "losers": [...],
  "meta": {
    "timeframe": "24h",
    "thresholds": {
      "min_change": 5,
      "volume_spike": 2.0,
      "min_market_cap": 10000000
    },
    "total_scanned": 1000,
    "matches": 127
  }
}
```

### Example 13: CSV Export

For spreadsheet analysis:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/scanner.py --format csv --output movers.csv
```

**Output (movers.csv):**
```csv
type,rank,symbol,name,price,change,volume_ratio,market_cap,significance_score
gainer,1,ABC,ABC Token,1.234,45.67,5.2,123400000,89.3
gainer,2,DEF,DEF Protocol,0.567,32.10,3.8,45600000,76.5
loser,1,JKL,JKL Finance,3.456,-28.90,4.1,89100000,72.1
```

---

## Using Presets

### Example 14: Create Custom Preset

Create `config/presets/momentum.yaml`:
```yaml
min_change: 8
volume_spike: 2.5
min_market_cap: 25000000
top_n: 30
```

Use it:
```bash
python ${CLAUDE_SKILL_DIR}/scripts/scanner.py --preset momentum
```

### Example 15: Aggressive Day Trading

Create `config/presets/daytrader.yaml`:
```yaml
min_change: 3
volume_spike: 2
min_market_cap: 5000000
min_volume: 500000
top_n: 50
```

Use it:
```bash
python ${CLAUDE_SKILL_DIR}/scripts/scanner.py --preset daytrader --timeframe 1h
```

---

## Filtering Results

### Example 16: Gainers Only

```bash
python ${CLAUDE_SKILL_DIR}/scripts/scanner.py --gainers-only
```

Only shows positive movers.

### Example 17: Losers Only

```bash
python ${CLAUDE_SKILL_DIR}/scripts/scanner.py --losers-only
```

For dip buying or short opportunities.

---

## Sorting Options

### Example 18: Sort by Change

```bash
python ${CLAUDE_SKILL_DIR}/scripts/scanner.py --sort-by change
```

Highest % changes first.

### Example 19: Sort by Volume

```bash
python ${CLAUDE_SKILL_DIR}/scripts/scanner.py --sort-by volume
```

Highest volume ratios first.

### Example 20: Sort by Market Cap

```bash
python ${CLAUDE_SKILL_DIR}/scripts/scanner.py --sort-by market_cap
```

Largest caps first.

---

## Advanced Combinations

### Example 21: Morning Momentum Scan

```bash
python ${CLAUDE_SKILL_DIR}/scripts/scanner.py \
  --timeframe 1h \
  --min-change 5 \
  --volume-spike 3 \
  --min-cap 50000000 \
  --gainers-only \
  --top 10
```

Find fresh morning momentum plays.

### Example 22: Distressed Asset Hunt

```bash
python ${CLAUDE_SKILL_DIR}/scripts/scanner.py \
  --timeframe 24h \
  --min-change 20 \
  --losers-only \
  --min-cap 100000000 \
  --sort-by significance \
  --top 15
```

Find oversold large-cap assets.

### Example 23: DeFi Blue Chips

```bash
python ${CLAUDE_SKILL_DIR}/scripts/scanner.py \
  --category defi \
  --min-cap 500000000 \
  --min-change 3 \
  --format json
```

---

## Shell Script Integration

### Example 24: Scheduled Scan

```bash
#!/bin/bash
# morning_scan.sh - Run at market open

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR=~/crypto_scans

python ${CLAUDE_SKILL_DIR}/scripts/scanner.py \
  --format json \
  --output "$OUTPUT_DIR/movers_$TIMESTAMP.json"

echo "Scan complete: $OUTPUT_DIR/movers_$TIMESTAMP.json"
```

### Example 25: Alert on High Scores

```bash
#!/bin/bash
# Check for exceptional movers

RESULT=$(python ${CLAUDE_SKILL_DIR}/scripts/scanner.py --format json)
HIGH_SCORE=$(echo "$RESULT" | jq '.gainers[0].significance_score')

if (( $(echo "$HIGH_SCORE > 90" | bc -l) )); then
  echo "ALERT: Exceptional mover detected (Score: $HIGH_SCORE)"
fi
```

---

## Best Practices

1. **Start Conservative**: Begin with default thresholds, then adjust
2. **Use Volume Confirmation**: High volume = more reliable signals
3. **Consider Market Cap**: Very small caps are riskier
4. **Check Multiple Timeframes**: 1h, 24h, 7d give different perspectives
5. **Export for Analysis**: JSON/CSV exports enable deeper research
6. **Create Presets**: Save your preferred configurations
7. **Run Regularly**: Market conditions change; scan frequently
