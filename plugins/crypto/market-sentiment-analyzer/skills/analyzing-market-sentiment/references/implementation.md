# Analyzing Market Sentiment - Implementation Reference

## Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--coin` | Analyze specific coin (BTC, ETH, etc.) | All market |
| `--period` | Time period (1h, 4h, 24h, 7d) | 24h |
| `--detailed` | Show full component breakdown | false |
| `--format` | Output format (table, json, csv) | table |
| `--output` | Output file path | stdout |
| `--weights` | Custom weights (e.g., "news:0.5,fng:0.3,momentum:0.2") | Default |
| `--verbose` | Enable verbose output | false |

## Sentiment Classifications

| Score Range | Classification | Description |
|-------------|----------------|-------------|
| 0-20 | Extreme Fear | Market panic, potential bottom |
| 21-40 | Fear | Cautious sentiment, bearish |
| 41-60 | Neutral | Balanced, no strong bias |
| 61-80 | Greed | Optimistic, bullish sentiment |
| 81-100 | Extreme Greed | Euphoria, potential top |

## JSON Output Format

```json
{
  "composite_score": 65.5,
  "classification": "Greed",
  "components": {
    "fear_greed": {
      "score": 72,
      "classification": "Greed",
      "weight": 0.40,
      "contribution": 28.8
    },
    "news_sentiment": {
      "score": 58.5,
      "articles_analyzed": 25,
      "positive": 12,
      "negative": 5,
      "neutral": 8,
      "weight": 0.40,
      "contribution": 23.4
    },
    "market_momentum": {
      "score": 66.5,
      "btc_change_24h": 3.5,
      "weight": 0.20,
      "contribution": 13.3
    }
  },
  "meta": {
    "timestamp": "2026-01-14T15:30:00Z",
    "period": "24h"
  }
}
```

## Advanced Examples

```bash
# Custom weights (emphasize news)
python ${CLAUDE_SKILL_DIR}/scripts/sentiment_analyzer.py --weights "news:0.5,fng:0.3,momentum:0.2"

# Weekly sentiment comparison
python ${CLAUDE_SKILL_DIR}/scripts/sentiment_analyzer.py --period 7d --detailed

# Export for trading model
python ${CLAUDE_SKILL_DIR}/scripts/sentiment_analyzer.py --format json --output sentiment.json

# Bitcoin-specific detailed analysis
python ${CLAUDE_SKILL_DIR}/scripts/sentiment_analyzer.py --coin BTC --detailed
```

## Contrarian Indicator Theory

Sentiment is often used as a contrarian indicator:
- **Extreme Fear** readings historically correlate with market bottoms and buying opportunities
- **Extreme Greed** readings historically correlate with market tops and selling opportunities
- The Fear & Greed Index has shown predictive value when combined with technical analysis
- Best used in conjunction with other analysis tools rather than as a sole decision driver
