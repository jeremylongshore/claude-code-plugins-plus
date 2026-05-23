# PRD: Analyzing Market Sentiment

## Document Control

| Field | Value |
|-------|-------|
| **Skill Name** | analyzing-market-sentiment |
| **Type** | Analysis & Intelligence |
| **Domain** | Cryptocurrency Sentiment Analysis |
| **Target Users** | Traders, Analysts, Portfolio Managers |
| **Priority** | P1 - Core Analytics Skill |
| **Version** | 2.0.0 |
| **Author** | Jeremy Longshore <jeremy@intentsolutions.io> |

---

## Executive Summary

The analyzing-market-sentiment skill provides comprehensive cryptocurrency market sentiment analysis by combining news sentiment scoring, Fear & Greed index integration, and keyword-based sentiment detection. It enables traders and analysts to gauge market mood before making trading decisions.

**Value Proposition**: Quantify market sentiment with a 0-100 score combining news analysis, social indicators, and market metrics into actionable intelligence.

---

## Problem Statement

### Current Pain Points

1. **Subjective Assessment**: "Feeling bullish" is not quantifiable; traders need measurable sentiment
2. **Information Fragmentation**: Sentiment signals scattered across news, social media, and market data
3. **Delayed Reaction**: Manual sentiment assessment is slow; markets move fast
4. **No Historical Context**: Hard to compare current sentiment to historical norms

### Impact of Not Solving

- Traders enter positions against prevailing sentiment
- Missed contrarian opportunities at sentiment extremes
- Emotional decisions override data-driven analysis
- No systematic approach to sentiment tracking

---

## Target Users

### Persona 1: Swing Trader

- **Name**: Alex
- **Role**: Part-time crypto trader
- **Goals**: Time entries/exits with sentiment extremes
- **Pain Points**: Doesn't have time to read all news; needs quick sentiment check
- **Usage**: Daily sentiment scan before placing trades

### Persona 2: Quantitative Analyst

- **Name**: Rachel
- **Role**: Quant at crypto hedge fund
- **Goals**: Incorporate sentiment into trading models
- **Pain Points**: Needs structured, exportable sentiment data
- **Usage**: Hourly sentiment data in JSON format for model input

### Persona 3: Research Analyst

- **Name**: Kevin
- **Role**: Crypto research analyst
- **Goals**: Include sentiment analysis in reports
- **Pain Points**: Needs both aggregate and coin-specific sentiment
- **Usage**: Weekly sentiment reports with historical comparison

---

## User Stories

### US-1: Overall Market Sentiment (Critical)

**As a** trader
**I want to** see a single sentiment score for the crypto market
**So that** I can quickly gauge if the market is fearful or greedy

**Acceptance Criteria:**

- Display composite sentiment score (0-100)
- Show Fear & Greed classification (Extreme Fear, Fear, Neutral, Greed, Extreme Greed)
- Include component breakdown (news, market metrics)
- Complete analysis in under 15 seconds

### US-2: Coin-Specific Sentiment (Critical)

**As a** trader
**I want to** analyze sentiment for a specific coin
**So that** I can make informed decisions on that asset

**Acceptance Criteria:**

- Filter sentiment analysis by coin symbol
- Show news sentiment specific to that coin
- Include social mention volume if available
- Compare to overall market sentiment

### US-3: News Sentiment Analysis (Important)

**As a** analyst
**I want to** see sentiment scores for recent news articles
**So that** I can understand what's driving market mood

**Acceptance Criteria:**

- Score each article as positive, negative, or neutral
- Show aggregate news sentiment
- Highlight most positive and negative articles
- Support time window filtering (1h, 4h, 24h, 7d)

### US-4: Export Sentiment Data (Important)

**As a** quant
**I want to** export sentiment data in JSON format
**So that** I can feed it into my trading models

**Acceptance Criteria:**

- JSON output with all sentiment components
- Include timestamps for time-series analysis
- Support multiple export formats (JSON, CSV)
- Include metadata (sources, confidence)

### US-5: Historical Comparison (Nice-to-Have)

**As a** analyst
**I want to** see how current sentiment compares to historical averages
**So that** I can identify sentiment extremes

**Acceptance Criteria:**

- Show current vs 7-day average
- Flag extreme readings (top/bottom 10%)
- Visual indicators for sentiment trends

---

## Functional Requirements

### REQ-1: Fear & Greed Index Integration

- Fetch Alternative.me Fear & Greed Index
- Parse historical values for comparison
- Map to 0-100 score with classification

### REQ-2: News Sentiment Analysis

- Integrate with crypto-news-aggregator skill (optional dependency)
- Perform keyword-based sentiment scoring
- Aggregate across multiple articles
- Weight by source quality and recency

### REQ-3: Sentiment Scoring Algorithm

- Composite score combining multiple indicators:
  - News sentiment (40% weight)
  - Fear & Greed Index (40% weight)
  - Market momentum (20% weight)
- Configurable weights via settings

### REQ-4: Coin-Specific Analysis

- Filter news by coin symbol
- Calculate coin-specific sentiment
- Compare to market-wide sentiment

### REQ-5: Output Formatting

- Table format for terminal display
- JSON format for programmatic use
- CSV format for spreadsheet analysis
- Summary format for quick reads

---

## Non-Goals

- **Social Media Scraping**: No Twitter/Discord/Telegram scraping (API access required)
- **Real-time Streaming**: Polling model, not push notifications
- **Machine Learning**: Keyword-based only, no ML sentiment models
- **Order Flow Analysis**: Pure sentiment, no trade flow data
- **Portfolio Integration**: Analysis only, no trading recommendations

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Analysis time | < 15s | Script execution time |
| Sentiment accuracy | Correlates with price direction > 60% | Backtest validation |
| Data freshness | < 5 min old | Timestamp comparison |
| User activation | Triggered by sentiment phrases | Plugin analytics |
| Export completeness | All components included | Schema validation |

---

## UX Flow

```
User: "analyze crypto sentiment"
  │
  ├─► Fetch Fear & Greed Index
  │
  ├─► Fetch news (via aggregator or direct)
  │
  ├─► Score news articles
  │
  ├─► Fetch market momentum data
  │
  ├─► Calculate composite score
  │
  ├─► Format output
  │
  └─► Display sentiment dashboard
```

---

## Integration Points

### Optional Dependencies

- **crypto-news-aggregator**: For news feed (can work standalone)
- **tracking-crypto-prices**: For market momentum data (can use CoinGecko directly)

### External APIs

- **Alternative.me**: Fear & Greed Index (free, no API key)
- **CoinGecko**: Market data for momentum calculation (free tier)

### Consumers (Skills that can use this)

- **crypto-signal-generator**: Sentiment as signal input
- **trading-strategy-backtester**: Historical sentiment for backtesting

---

## Constraints & Assumptions

### Constraints

- Alternative.me API availability (single source for F&G)
- No social media access without API keys
- Keyword-based sentiment is less accurate than ML

### Assumptions

- Fear & Greed Index is representative of market sentiment
- News sentiment correlates with market direction
- Users want quick, actionable sentiment scores

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Fear & Greed API down | Low | High | Cache recent values; show stale warning |
| News aggregator unavailable | Medium | Medium | Direct RSS fallback; reduced accuracy |
| Sentiment accuracy issues | Medium | Medium | Clear methodology disclosure |
| API rate limiting | Low | Low | Caching; respect rate limits |

---

## Examples

### Example 1: Quick Sentiment Check

```bash
python sentiment_analyzer.py
```

Returns overall market sentiment with Fear & Greed classification.

### Example 2: Bitcoin-Specific Sentiment

```bash
python sentiment_analyzer.py --coin BTC
```

Returns Bitcoin-specific sentiment with news analysis.

### Example 3: Detailed Analysis with Export

```bash
python sentiment_analyzer.py --detailed --format json --output sentiment.json
```

Full sentiment breakdown exported to JSON.

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-10-16 | Jeremy Longshore | Initial stub |
| 2.0.0 | 2026-01-14 | Jeremy Longshore | Full PRD, implementation |
