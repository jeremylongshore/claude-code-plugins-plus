---
name: analyzing-market-sentiment
description: |
  Analyze cryptocurrency market sentiment using Fear & Greed Index, news analysis, and market momentum.
  Use when gauging overall market mood, checking if markets are fearful or greedy, or analyzing sentiment for specific coins.
  Trigger with phrases like "analyze crypto sentiment", "check market mood", "is the market fearful", "sentiment for Bitcoin", or "Fear and Greed index".

allowed-tools: Read, Bash(crypto:sentiment-*)
version: 2.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---

# Analyzing Market Sentiment

## Overview

This skill provides comprehensive cryptocurrency market sentiment analysis by combining multiple data sources:

- **Fear & Greed Index**: Market-wide sentiment from Alternative.me
- **News Sentiment**: Keyword-based analysis of recent crypto news
- **Market Momentum**: Price and volume trends from CoinGecko

**Key Capabilities:**
- Composite sentiment score (0-100) with classification
- Coin-specific sentiment analysis
- Detailed breakdown of sentiment components
- Multiple output formats (table, JSON, CSV)

## Prerequisites

Before using this skill, ensure:

1. **Python 3.8+** is installed
2. **requests** library is available: `pip install requests`
3. Internet connectivity for API access (Alternative.me, CoinGecko)
4. Optional: `crypto-news-aggregator` skill for enhanced news analysis

## Instructions

### Step 1: Assess User Intent

Determine what sentiment analysis the user needs:
- **Overall market**: No specific coin, general sentiment
- **Coin-specific**: Extract coin symbol (BTC, ETH, etc.)
- **Quick vs detailed**: Quick score or full breakdown

### Step 2: Execute Sentiment Analysis

Run the sentiment analyzer with appropriate options:

```bash
# Quick sentiment check (default)
python ${CLAUDE_SKILL_DIR}/scripts/sentiment_analyzer.py

# Coin-specific sentiment
python ${CLAUDE_SKILL_DIR}/scripts/sentiment_analyzer.py --coin BTC

# Detailed analysis with component breakdown
python ${CLAUDE_SKILL_DIR}/scripts/sentiment_analyzer.py --detailed

# Export to JSON
python ${CLAUDE_SKILL_DIR}/scripts/sentiment_analyzer.py --format json --output sentiment.json

# Custom time period
python ${CLAUDE_SKILL_DIR}/scripts/sentiment_analyzer.py --period 7d --detailed
```

### Step 3: Present Results

Format and present the sentiment analysis:
- Show composite score and classification
- Explain what the sentiment means
- Highlight any extreme readings
- For detailed mode, show component breakdown

### Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--coin` | Analyze specific coin (BTC, ETH, etc.) | All market |
| `--period` | Time period (1h, 4h, 24h, 7d) | 24h |
| `--detailed` | Show full component breakdown | false |
| `--format` | Output format (table, json, csv) | table |
| `--output` | Output file path | stdout |
| `--weights` | Custom weights (e.g., "news:0.5,fng:0.3,momentum:0.2") | Default |
| `--verbose` | Enable verbose output | false |

### Sentiment Classifications

| Score Range | Classification | Description |
|-------------|----------------|-------------|
| 0-20 | Extreme Fear | Market panic, potential bottom |
| 21-40 | Fear | Cautious sentiment, bearish |
| 41-60 | Neutral | Balanced, no strong bias |
| 61-80 | Greed | Optimistic, bullish sentiment |
| 81-100 | Extreme Greed | Euphoria, potential top |

## Output

### Table Format (Default)
```
==============================================================================
  MARKET SENTIMENT ANALYZER                         Updated: 2026-01-14 15:30
==============================================================================

  COMPOSITE SENTIMENT
------------------------------------------------------------------------------
  Score: 65.5 / 100                         Classification: GREED

  Component Breakdown:
  - Fear & Greed Index:  72.0  (weight: 40%)  → 28.8 pts
  - News Sentiment:      58.5  (weight: 40%)  → 23.4 pts
  - Market Momentum:     66.5  (weight: 20%)  → 13.3 pts

  Interpretation: Market is moderately greedy. Consider taking profits or
  reducing position sizes. Watch for reversal signals.

==============================================================================
```

### JSON Format
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

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

| Error | Cause | Solution |
|-------|-------|----------|
| Fear & Greed unavailable | API down | Uses cached value with warning |
| News fetch failed | Network issue | Reduces weight of news component |
| Invalid coin | Unknown symbol | Proceeds with market-wide analysis |

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

### Quick Examples

```bash
# Quick market sentiment check
python ${CLAUDE_SKILL_DIR}/scripts/sentiment_analyzer.py

# Bitcoin-specific sentiment
python ${CLAUDE_SKILL_DIR}/scripts/sentiment_analyzer.py --coin BTC

# Detailed analysis
python ${CLAUDE_SKILL_DIR}/scripts/sentiment_analyzer.py --detailed

# Export for trading model
python ${CLAUDE_SKILL_DIR}/scripts/sentiment_analyzer.py --format json --output sentiment.json

# Custom weights (emphasize news)
python ${CLAUDE_SKILL_DIR}/scripts/sentiment_analyzer.py --weights "news:0.5,fng:0.3,momentum:0.2"

# Weekly sentiment comparison
python ${CLAUDE_SKILL_DIR}/scripts/sentiment_analyzer.py --period 7d --detailed
```

## Resources

- **Alternative.me Fear & Greed Index**: https://alternative.me/crypto/fear-and-greed-index/
- **CoinGecko API**: https://www.coingecko.com/en/api
- **Sentiment Analysis Theory**: Contrarian indicator - extreme readings often precede reversals
- See `${CLAUDE_SKILL_DIR}/config/settings.yaml` for configuration options
