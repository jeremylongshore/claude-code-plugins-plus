# Usage Examples

Comprehensive examples for the Market Sentiment Analyzer.

---

## Quick Start Examples

### 1. Basic Sentiment Check

```bash
python sentiment_analyzer.py
```

Output:

```
==============================================================================
  MARKET SENTIMENT ANALYZER                         2026-01-14 15:30 UTC
==============================================================================

  COMPOSITE SENTIMENT
------------------------------------------------------------------------------
  Score: 58.5 / 100                         Classification: NEUTRAL

  [------------|----------------------█-----------------|------------------]
  0 -------- 25 -------- 50 -------- 75 -------- 100
  FEAR                  NEUTRAL                 GREED

  COMPONENTS
------------------------------------------------------------------------------
  Fear & Greed Index:    62.0  (weight: 40%)  →  24.8 pts  [Greed]
  News Sentiment:        55.0  (weight: 40%)  →  22.0 pts  [15 articles]
  Market Momentum:       58.5  (weight: 20%)  →  11.7 pts  [BTC: +1.2%]

  INTERPRETATION
------------------------------------------------------------------------------
  Market sentiment is balanced with no strong directional bias.
  Wait for clearer signals before making major decisions.

==============================================================================
```

---

### 2. Bitcoin-Specific Sentiment

```bash
python sentiment_analyzer.py --coin BTC
```

Filters news and momentum specifically for Bitcoin.

---

### 3. Detailed Analysis

```bash
python sentiment_analyzer.py --detailed
```

Shows full component breakdown including:

- News sentiment distribution (positive/negative/neutral)
- Top positive and negative headlines
- Volume ratio analysis
- ETH price change

---

### 4. Different Time Periods

```bash
# Last hour
python sentiment_analyzer.py --period 1h

# Last 4 hours
python sentiment_analyzer.py --period 4h

# Last 24 hours (default)
python sentiment_analyzer.py --period 24h

# Last 7 days
python sentiment_analyzer.py --period 7d
```

---

## Export Examples

### 5. JSON Export

```bash
python sentiment_analyzer.py --format json
```

Output:

```json
{
  "composite_score": 58.5,
  "classification": "Neutral",
  "interpretation": "Market sentiment is balanced...",
  "components": {
    "fear_greed": {
      "score": 62,
      "classification": "Greed",
      "weight": 0.40,
      "contribution": 24.8
    },
    "news_sentiment": {
      "score": 55.0,
      "articles_analyzed": 15,
      "positive": 6,
      "negative": 4,
      "neutral": 5,
      "weight": 0.40,
      "contribution": 22.0
    },
    "market_momentum": {
      "score": 58.5,
      "btc_change_24h": 1.2,
      "weight": 0.20,
      "contribution": 11.7
    }
  },
  "meta": {
    "timestamp": "2026-01-14T15:30:00Z",
    "period": "24h"
  }
}
```

---

### 6. CSV Export

```bash
python sentiment_analyzer.py --format csv --output sentiment.csv
```

Creates spreadsheet-compatible output for analysis.

---

### 7. Save to File

```bash
# JSON to file
python sentiment_analyzer.py --format json --output daily_sentiment.json

# Detailed CSV to file
python sentiment_analyzer.py --format csv --detailed --output sentiment_log.csv
```

---

## Advanced Examples

### 8. Custom Weights

Emphasize news over Fear & Greed:

```bash
python sentiment_analyzer.py --weights "news:0.5,fng:0.3,momentum:0.2"
```

Emphasize market momentum:

```bash
python sentiment_analyzer.py --weights "news:0.3,fng:0.3,momentum:0.4"
```

---

### 9. Verbose Mode (Debugging)

```bash
python sentiment_analyzer.py -v
```

Shows:

- Which APIs are being called
- Cache hits/misses
- Individual component fetch times
- Any errors or warnings

---

### 10. Ethereum Analysis with Export

```bash
python sentiment_analyzer.py --coin ETH --detailed --format json --output eth_sentiment.json
```

---

## Integration Examples

### 11. Cron Job (Hourly Tracking)

```bash
# Add to crontab
0 * * * * cd /path/to/skill && python sentiment_analyzer.py --format json --output /data/sentiment/$(date +\%Y\%m\%d_\%H).json
```

---

### 12. Combined with News Aggregator

When `crypto-news-aggregator` skill is installed:

```bash
# Aggregator provides enhanced news data
python sentiment_analyzer.py --detailed
# Will show "source: aggregator" in verbose mode
```

---

### 13. Trading Signal Input

```bash
# Get sentiment for trading bot
SENTIMENT=$(python sentiment_analyzer.py --format json | jq -r '.classification')
if [ "$SENTIMENT" = "Extreme Fear" ]; then
    echo "Potential buying opportunity"
fi
```

---

## Interpretation Guide

### Reading the Output

| Score Range | Classification | Trading Implication |
|-------------|----------------|---------------------|
| 0-20 | Extreme Fear | Potential bottom, accumulation zone |
| 21-40 | Fear | Cautious, wait for reversal signals |
| 41-60 | Neutral | No strong bias, follow other indicators |
| 61-80 | Greed | Consider taking profits |
| 81-100 | Extreme Greed | High risk, potential top |

### Component Weights

Default weights:

- Fear & Greed Index: 40%
- News Sentiment: 40%
- Market Momentum: 20%

These can be adjusted with `--weights` based on your trading style.

---

## Troubleshooting Examples

### Check Component Status

```bash
# Individual component tests
python fear_greed.py -v
python news_sentiment.py -v
python market_momentum.py -v
```

### Force Fresh Data

```bash
# Clear caches
rm scripts/.*.json
python sentiment_analyzer.py
```

### Debug Network Issues

```bash
python sentiment_analyzer.py -v 2>&1 | grep -E "(Fetching|failed|error)"
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
