# ARD: Analyzing Market Sentiment

> Part of [Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)

## Document Control

| Field | Value |
|-------|-------|
| **Skill Name** | analyzing-market-sentiment |
| **Architecture Pattern** | Multi-Source Aggregation + Scoring |
| **Version** | 2.0.0 |
| **Author** | Jeremy Longshore <jeremy@intentsolutions.io> |

---

## Architectural Overview

### Pattern: Composite Scoring Pipeline

This skill implements a multi-source data aggregation pattern with weighted composite scoring.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     MARKET SENTIMENT ANALYZER ARCHITECTURE                   │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  Fear & Greed    │     │  News Articles   │     │  Market Data     │
│     Index        │     │  (RSS/Aggregator)│     │  (CoinGecko)     │
└────────┬─────────┘     └────────┬─────────┘     └────────┬─────────┘
         │                        │                        │
         ▼                        ▼                        ▼
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  F&G FETCHER     │     │  NEWS FETCHER    │     │  MARKET FETCHER  │
│  - API call      │     │  - RSS parsing   │     │  - Price data    │
│  - Caching       │     │  - Deduplication │     │  - Volume data   │
└────────┬─────────┘     └────────┬─────────┘     └────────┬─────────┘
         │                        │                        │
         │                        ▼                        │
         │               ┌──────────────────┐              │
         │               │  NEWS SCORER     │              │
         │               │  - Keyword match │              │
         │               │  - Sentiment     │              │
         │               │  - Aggregation   │              │
         │               └────────┬─────────┘              │
         │                        │                        │
         └────────────────────────┼────────────────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │  COMPOSITE CALCULATOR   │
                    │  - Weight application   │
                    │  - Score normalization  │
                    │  - Classification       │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │  FORMATTER              │
                    │  - Dashboard view       │
                    │  - JSON export          │
                    │  - CSV export           │
                    └─────────────────────────┘
```

### Workflow

1. **Fetch**: Parallel data retrieval from multiple sources
2. **Score**: Analyze news sentiment using keyword matching
3. **Calculate**: Compute weighted composite score
4. **Classify**: Map score to sentiment classification
5. **Format**: Output in requested format

---

## Progressive Disclosure Strategy

### Level 1: Quick Sentiment Check (Default)

```bash
python sentiment_analyzer.py
```

Returns overall sentiment score and classification.

### Level 2: Coin-Specific Analysis

```bash
python sentiment_analyzer.py --coin BTC
```

Adds coin-specific sentiment breakdown.

### Level 3: Detailed Analysis

```bash
python sentiment_analyzer.py --detailed --period 24h
```

Full breakdown with news article scores.

### Level 4: Export with Custom Weights

```bash
python sentiment_analyzer.py --format json --weights "news:0.5,fng:0.3,momentum:0.2"
```

Custom weighting and JSON export.

---

## Tool Permission Strategy

### Allowed Tools (Scoped)

```yaml
allowed-tools: Read, Bash(crypto:sentiment-*)
```

| Tool | Scope | Purpose |
|------|-------|---------|
| Read | Unrestricted | Read config, cached data |
| Bash | `crypto:sentiment-*` | Execute sentiment analysis scripts |

### Why These Tools

- **Read**: Load configuration and cached sentiment data
- **Bash(crypto:sentiment-*)**: Execute Python scripts for analysis
- **No Write**: Analysis is read-only; exports use script file output

---

## Directory Structure

```
plugins/crypto/market-sentiment-analyzer/
└── skills/
    └── analyzing-market-sentiment/
        ├── PRD.md                    # Product requirements
        ├── ARD.md                    # This file
        ├── SKILL.md                  # Core instructions
        ├── scripts/
        │   ├── sentiment_analyzer.py # Main CLI entry point
        │   ├── fear_greed.py         # Fear & Greed Index fetcher
        │   ├── news_sentiment.py     # News sentiment scoring
        │   ├── market_momentum.py    # Market momentum calculation
        │   └── formatters.py         # Output formatting
        ├── references/
        │   ├── errors.md             # Error handling guide
        │   └── examples.md           # Usage examples
        └── config/
            └── settings.yaml         # Configuration options
```

---

## Data Flow Architecture

### Input

- User request with optional filters (--coin, --period, --detailed)
- External API data (Fear & Greed, news, market)

### Processing Pipeline

```
Input Request
     │
     ├──► Fetch Fear & Greed Index
     │         │
     │         ▼
     │    Score: 0-100, Classification
     │
     ├──► Fetch News (RSS or aggregator)
     │         │
     │         ▼
     │    Score each article (-1 to +1)
     │         │
     │         ▼
     │    Aggregate: weighted average
     │         │
     │         ▼
     │    Normalize to 0-100
     │
     ├──► Fetch Market Data
     │         │
     │         ▼
     │    Calculate momentum (price change, volume)
     │         │
     │         ▼
     │    Normalize to 0-100
     │
     └──► Calculate Composite Score
               │
               ▼
          Weighted Sum:
          - News: 40%
          - Fear & Greed: 40%
          - Momentum: 20%
               │
               ▼
          Classify:
          - 0-20: Extreme Fear
          - 21-40: Fear
          - 41-60: Neutral
          - 61-80: Greed
          - 81-100: Extreme Greed
```

### Output Schema

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
      "volume_ratio": 1.2,
      "weight": 0.20,
      "contribution": 13.3
    }
  },
  "meta": {
    "timestamp": "2026-01-14T15:30:00Z",
    "period": "24h",
    "coin_filter": null,
    "data_freshness": {
      "fear_greed": "5 min",
      "news": "2 min",
      "market": "1 min"
    }
  }
}
```

---

## Sentiment Scoring Algorithm

### News Sentiment Scoring

```python
# Per-article scoring
def score_article(title: str, summary: str) -> float:
    """Score article from -1 (bearish) to +1 (bullish)."""
    text = f"{title} {summary}".lower()
    score = 0.0

    # Positive keywords
    positive = ["bullish", "surge", "rally", "breakout", "adoption",
                "partnership", "approval", "milestone", "record"]
    for kw in positive:
        if kw in text:
            score += 0.2

    # Negative keywords
    negative = ["bearish", "crash", "dump", "hack", "exploit",
                "ban", "lawsuit", "fraud", "bankruptcy"]
    for kw in negative:
        if kw in text:
            score -= 0.2

    return max(-1, min(1, score))

# Aggregate scoring
def aggregate_news_sentiment(articles: List[dict]) -> float:
    """Aggregate article scores to 0-100 scale."""
    if not articles:
        return 50  # Neutral

    # Weight by recency
    weighted_sum = 0
    weight_total = 0

    for article in articles:
        age_hours = article.get("age_hours", 24)
        weight = 1 / (1 + age_hours / 12)  # Decay over 12 hours
        weighted_sum += article["score"] * weight
        weight_total += weight

    avg_score = weighted_sum / weight_total  # -1 to +1
    return (avg_score + 1) * 50  # Convert to 0-100
```

### Composite Score Calculation

```python
def calculate_composite(
    fear_greed: float,      # 0-100
    news_sentiment: float,  # 0-100
    momentum: float,        # 0-100
    weights: dict = None
) -> float:
    """Calculate weighted composite sentiment score."""
    weights = weights or {
        "fear_greed": 0.40,
        "news": 0.40,
        "momentum": 0.20
    }

    return (
        fear_greed * weights["fear_greed"] +
        news_sentiment * weights["news"] +
        momentum * weights["momentum"]
    )
```

---

## Error Handling Strategy

### Error Categories

| Category | Examples | Strategy |
|----------|----------|----------|
| API Error | Fear & Greed API down | Use cached value with stale warning |
| Network | Timeout, DNS failure | Skip component, partial analysis |
| Parse | Invalid JSON response | Log warning, use default |
| Data | No news found | Reduce weight, increase other components |

### Graceful Degradation

```
Full Analysis (all components)
     │
     ▼
Partial Analysis (some components failed)
     │ → Recalculate weights for available data
     │ → Warn user about missing components
     │
     ▼
Cached Fallback (API failures)
     │ → Use recent cached values
     │ → Show "stale data" warning
     │
     ▼
Minimal Analysis (only Fear & Greed)
     │ → Single source analysis
     │ → Clear limitations disclosure
```

---

## Composability & Stacking

### Optional Dependencies

- **crypto-news-aggregator**: Enhanced news analysis
  - If available: Uses aggregator's scored news
  - If unavailable: Falls back to direct RSS fetch

### As Data Provider

Skills that can consume sentiment data:

- **crypto-signal-generator**: Sentiment as signal input
- **trading-strategy-backtester**: Historical sentiment data

### Integration Pattern

```python
# Check for news aggregator
NEWS_AGGREGATOR = None
try:
    from pathlib import Path
    aggregator_path = Path(__file__).parent.parent.parent.parent / \
                      "crypto-news-aggregator/skills/aggregating-crypto-news/scripts"
    if (aggregator_path / "news_aggregator.py").exists():
        NEWS_AGGREGATOR = aggregator_path
except Exception:
    pass

def get_news_for_sentiment(coin: str = None, period: str = "24h"):
    """Fetch news using aggregator if available, else direct RSS."""
    if NEWS_AGGREGATOR:
        # Use aggregator
        return fetch_via_aggregator(coin, period)
    else:
        # Direct RSS fallback
        return fetch_direct_rss(coin, period)
```

---

## Performance & Scalability

### Performance Targets

| Metric | Target | Approach |
|--------|--------|----------|
| Full analysis | < 15s | Parallel API calls |
| Quick check | < 5s | Cached Fear & Greed only |
| News scoring | < 2s per 100 articles | Efficient keyword matching |

### Optimization Strategies

1. **Parallel Fetching**: Concurrent API calls with asyncio/threading
2. **Caching**: Cache Fear & Greed (5 min TTL), news (2 min TTL)
3. **Lazy Loading**: Only fetch detailed data if --detailed flag
4. **Early Exit**: Return cached data for repeated calls

---

## Testing Strategy

### Unit Tests

| Component | Test Cases |
|-----------|------------|
| FearGreedFetcher | API response parsing, caching, classification |
| NewsSentiment | Keyword matching, aggregation, normalization |
| CompositeCalculator | Weight application, edge cases |
| Formatters | All output formats, empty data handling |

### Integration Tests

- End-to-end with mock APIs
- Real API tests (daily CI)
- Export format validation

### Manual Testing

```bash
# Quick check
python sentiment_analyzer.py

# Coin-specific
python sentiment_analyzer.py --coin BTC

# Detailed with export
python sentiment_analyzer.py --detailed --format json --output sentiment.json
```

---

## Security & Compliance

### Security Considerations

- **No Authentication**: All APIs used are public
- **No User Data**: No personal information collected
- **Output Only**: Read-only analysis, no state modification

### Rate Limiting

- Alternative.me: Respect 10 req/min limit
- CoinGecko: Respect free tier limits
- Caching reduces API calls significantly
