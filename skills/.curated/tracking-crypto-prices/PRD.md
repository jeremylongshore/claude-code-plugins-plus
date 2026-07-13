# PRD: Market Price Tracker

**Version**: 2.0.0
**Author**: Jeremy Longshore <jeremy@intentsolutions.io>
**Status**: In Development
**Last Updated**: 2025-01-14

---

## Document Control

| Field | Value |
|-------|-------|
| **Skill Name** | tracking-crypto-prices |
| **Skill Type** | Utility Skill |
| **Domain** | Cryptocurrency / Market Data |
| **Target Users** | Traders, Investors, Developers, Analysts |
| **Priority** | Critical (Foundation Skill) |
| **Status** | In Development |
| **Owner** | Jeremy Longshore |

---

## 1. Executive Summary

**One-sentence description**: Track real-time cryptocurrency prices across multiple exchanges with historical data, price alerts, and multi-currency support.

**Value Proposition**: This is the **foundation skill** for the entire crypto plugin ecosystem. It provides the price data infrastructure that 10+ other skills depend on for their functionality. Without reliable price tracking, portfolio management, tax calculation, DeFi optimization, and arbitrage detection are impossible.

**Key Metrics**:

- Activation accuracy: 95%+
- Price data freshness: < 30 seconds
- API reliability: 99.5%+ uptime
- Supported assets: 10,000+ cryptocurrencies

**Dependent Skills** (skills that require this one):

- market-movers-scanner
- crypto-portfolio-tracker
- crypto-tax-calculator
- defi-yield-optimizer
- liquidity-pool-analyzer
- staking-rewards-optimizer
- crypto-derivatives-tracker
- dex-aggregator-router
- options-flow-analyzer
- arbitrage-opportunity-finder

---

## 2. Problem Statement

### Current State (Without This Skill)

**Pain Points**:

1. **Fragmented Data Sources**: Traders must manually check multiple exchanges and websites for price information, wasting time and risking decisions on stale data
2. **No Standardized Format**: Price data comes in different formats from different sources, making programmatic analysis difficult
3. **Missing Historical Context**: Point-in-time prices without historical trends lead to poor trading decisions
4. **Alert Fatigue**: Without intelligent alerting, users miss important price movements or get overwhelmed by noise
5. **Currency Confusion**: Prices in USD only ignore users who think in EUR, GBP, or other currencies

**Current Workarounds**:

- Manually refreshing CoinGecko/CoinMarketCap tabs
- Using spreadsheets with manual data entry
- Writing one-off scripts for each data source
- Subscribing to expensive third-party services

**Impact of Problem**:

- Time wasted: 30+ minutes daily checking prices across sources
- Error rate: 15% of decisions based on stale/incorrect data
- Missed opportunities: Significant due to delayed information
- User frustration: High

### Desired State (With This Skill)

**Transformation**:

- From: Manual, fragmented, time-consuming price checking
- To: Instant, unified, automated price intelligence with historical context

**Expected Benefits**:

1. **Time Savings**: Reduce price checking from 30+ minutes to < 30 seconds
2. **Accuracy**: 99.9%+ data accuracy with source verification
3. **Intelligence**: Historical trends and price alerts reduce missed opportunities by 80%
4. **Foundation**: Enable 10+ dependent skills to function reliably

---

## 3. Target Users

### Primary Users

**User Persona 1**: Active Cryptocurrency Trader

- **Background**: Trades crypto daily, uses multiple exchanges, technically competent
- **Goals**: Get real-time prices quickly, set price alerts, compare across exchanges
- **Pain Points**: Switching between apps/tabs, missing price movements, stale data
- **Use Frequency**: 10-50 times daily

**User Persona 2**: Crypto Investor (HODLer)

- **Background**: Long-term holder, checks portfolio weekly, moderate technical skills
- **Goals**: Monitor portfolio value, track historical performance, set major price alerts
- **Pain Points**: No simple way to see current holdings value, missing major moves
- **Use Frequency**: 2-5 times weekly

**User Persona 3**: Developer Building Crypto Tools

- **Background**: Software developer integrating price data into applications
- **Goals**: Reliable price API, consistent data format, historical data access
- **Pain Points**: Inconsistent API responses, rate limits, data normalization
- **Use Frequency**: Continuous (via other skills)

### Secondary Users

- **Analysts**: Need historical price data for research and modeling
- **Content Creators**: Need current prices for articles and videos
- **Compliance Officers**: Need price data for regulatory reporting

---

## 4. User Stories

### Critical User Stories (Must Have)

1. **As a** trader,
   **I want** to get the current price of any cryptocurrency instantly,
   **So that** I can make informed trading decisions without delay.

   **Acceptance Criteria**:
   - [ ] Price returned in < 3 seconds
   - [ ] Price includes 24h change percentage
   - [ ] Price includes volume data
   - [ ] Works for top 10,000 cryptocurrencies by market cap

2. **As a** investor,
   **I want** to see price history for any cryptocurrency,
   **So that** I can understand trends before making buy/sell decisions.

   **Acceptance Criteria**:
   - [ ] Historical data available for 1d, 7d, 30d, 90d, 1y, all-time
   - [ ] Data includes OHLCV (Open, High, Low, Close, Volume)
   - [ ] Data exportable to CSV for analysis
   - [ ] Charts/visualizations available

3. **As a** multi-currency user,
   **I want** prices displayed in my preferred currency (EUR, GBP, JPY, etc.),
   **So that** I don't have to mentally convert from USD.

   **Acceptance Criteria**:
   - [ ] Support for 30+ fiat currencies
   - [ ] Currency preference can be set and remembered
   - [ ] Conversion rates are current (< 1 hour old)

4. **As a** developer using other crypto skills,
   **I want** a reliable price data interface,
   **So that** dependent skills (portfolio tracker, tax calculator, etc.) work correctly.

   **Acceptance Criteria**:
   - [ ] Standardized JSON output format
   - [ ] Consistent error handling
   - [ ] Cached data for rate limit management
   - [ ] Clear documentation for integration

### High-Priority User Stories (Should Have)

1. **As a** trader, **I want** to compare prices across exchanges to find arbitrage opportunities
2. **As a** investor, **I want** price alerts when assets hit target prices
3. **As a** analyst, **I want** batch price queries for multiple assets simultaneously

### Nice-to-Have User Stories (Could Have)

1. **As a** user, **I want** price predictions based on historical patterns
2. **As a** user, **I want** social sentiment integration with price data

---

## 5. Functional Requirements

### Core Capabilities (Must Have)

**REQ-1**: Real-Time Price Fetching

- **Description**: Fetch current price for any cryptocurrency by symbol or name
- **Rationale**: Core functionality - everything else depends on this
- **Acceptance Criteria**:
  - [ ] Support symbol lookup (BTC, ETH, SOL)
  - [ ] Support name lookup (Bitcoin, Ethereum, Solana)
  - [ ] Return price, 24h change, volume, market cap
  - [ ] Response time < 3 seconds
- **Dependencies**: CoinGecko API or equivalent

**REQ-2**: Historical Price Data

- **Description**: Fetch OHLCV data for specified time ranges
- **Rationale**: Trend analysis requires historical context
- **Acceptance Criteria**:
  - [ ] Configurable time ranges (1d to all-time)
  - [ ] Configurable intervals (1m, 5m, 1h, 1d)
  - [ ] OHLCV format output
  - [ ] Export to CSV/JSON
- **Dependencies**: Yahoo Finance, CoinGecko, or exchange APIs

**REQ-3**: Multi-Currency Support

- **Description**: Display prices in user's preferred fiat currency
- **Rationale**: Global user base thinks in different currencies
- **Acceptance Criteria**:
  - [ ] Support 30+ fiat currencies
  - [ ] Automatic conversion using current rates
  - [ ] Configurable default currency
- **Dependencies**: Exchange rate API

**REQ-4**: Watchlist Management

- **Description**: Track a personalized list of cryptocurrencies
- **Rationale**: Users care about specific assets, not all 10,000+
- **Acceptance Criteria**:
  - [ ] Create/edit/delete watchlists
  - [ ] Predefined watchlists (top 10, DeFi, Layer 2, etc.)
  - [ ] Batch price fetch for watchlist
- **Dependencies**: Local storage for watchlist data

**REQ-5**: Caching Layer

- **Description**: Cache price data to reduce API calls and improve speed
- **Rationale**: Rate limits and latency require intelligent caching
- **Acceptance Criteria**:
  - [ ] Configurable cache duration (default: 30 seconds for spot prices)
  - [ ] Cache invalidation on demand
  - [ ] Disk-based cache for persistence
- **Dependencies**: Local file system

### Integration Requirements

**REQ-API-1**: CoinGecko API

- **Purpose**: Primary source for price data (10,000+ assets, free tier available)
- **Endpoints**:
  - `/simple/price` - Current prices
  - `/coins/{id}/market_chart` - Historical data
  - `/coins/markets` - Market data with sorting
- **Authentication**: API key (optional for higher limits)
- **Rate Limits**: 10-50 calls/minute (free), 500/minute (Pro)
- **Error Handling**: Exponential backoff on 429, fallback to cache

**REQ-API-2**: Yahoo Finance (yfinance)

- **Purpose**: Backup source, especially for historical OHLCV data
- **Endpoints**: Via yfinance Python library
- **Authentication**: None required
- **Rate Limits**: Implicit (be respectful)
- **Error Handling**: Fallback to CoinGecko

### Data Requirements

**REQ-DATA-1**: Input Data Format

- **Format**: Command-line arguments or JSON config
- **Required Fields**: `symbol` or `symbols` (list)
- **Optional Fields**: `currency`, `period`, `interval`
- **Validation Rules**: Symbol must be valid crypto ticker

**REQ-DATA-2**: Output Data Format

- **Format**: JSON (programmatic) or formatted table (human-readable)
- **Fields**: `symbol`, `name`, `price`, `change_24h`, `volume_24h`, `market_cap`, `last_updated`
- **Quality Standards**: Prices accurate to 8 decimal places for small-cap assets

### Performance Requirements

**REQ-PERF-1**: Response Time

- **Target**: < 3 seconds for single asset
- **Max Acceptable**: < 10 seconds for watchlist of 20 assets

**REQ-PERF-2**: Token Budget

- **Description Size**: < 250 characters
- **SKILL.md Size**: < 500 lines
- **Total Skill Size**: < 5,000 tokens

### Quality Requirements

**REQ-QUAL-1**: Description Quality

- **Target Score**: 80%+ on quality formula
- **Must Include**:
  - [ ] Action-oriented verbs
  - [ ] "Use when [scenarios]" clause
  - [ ] "Trigger with '[phrases]'" examples
  - [ ] Domain keywords (price, crypto, exchange, market)

**REQ-QUAL-2**: Data Accuracy

- **Price Accuracy**: Match exchange prices within 0.5%
- **Data Freshness**: < 30 seconds for spot prices
- **Error Rate**: < 1% failed requests after retries

---

## 6. Non-Goals (Out of Scope)

**What This Skill Does NOT Do**:

1. **Execute Trades**
   - **Rationale**: Trading requires exchange authentication and carries financial risk
   - **Alternative**: Use exchange-specific trading bots or manual trading

2. **Provide Price Predictions**
   - **Rationale**: Prediction is speculative and outside data-fetching scope
   - **Alternative**: May be added in future version (v3.0)

3. **Track NFT Prices**
   - **Rationale**: NFTs require different data sources and valuation methods
   - **Alternative**: Use nft-rarity-analyzer skill (separate)

4. **Aggregate DEX Prices**
   - **Rationale**: DEX prices require on-chain queries (different architecture)
   - **Alternative**: Use dex-aggregator-router skill (depends on this skill)

---

## 7. Success Metrics

### Skill Activation Metrics

**Metric 1**: Activation Accuracy

- **Definition**: % of times skill activates when user intends to check prices
- **Target**: 95%+
- **Measurement**: Manual testing with 50+ trigger phrase variations

**Metric 2**: False Positive Rate

- **Definition**: % of times skill activates when user meant something else
- **Target**: < 2%
- **Measurement**: User feedback and log analysis

### Quality Metrics

**Metric 3**: Description Quality Score

- **Formula**: 6-criterion weighted scoring
- **Target**: 85%+
- **Components**:
  - Action-oriented: 20%
  - Clear triggers: 25%
  - Comprehensive: 15%
  - Natural language: 20%
  - Specificity: 10%
  - Technical terms: 10%

### Usage Metrics

**Metric 4**: Daily Active Use

- **Target**: Used 5+ times daily by active users
- **Measurement**: Skill invocation logs

### Performance Metrics

**Metric 5**: Data Freshness

- **Definition**: Time since last price update
- **Target**: < 30 seconds for cached data
- **Measurement**: Timestamp comparison

---

## 8. User Experience Flow

### Typical Usage Flow

1. **User Intent**: User wants to know current Bitcoin price
2. **Trigger**: User says "What's the Bitcoin price?" or "check BTC"
3. **Skill Activation**: Claude recognizes price query intent
4. **Skill Execution**:
   - Check cache for recent BTC price
   - If stale, fetch from CoinGecko API
   - Format response with price, change, volume
5. **Output Delivered**: Formatted price card with key metrics
6. **User Action**: User uses information for trading decision

### Example Scenario

**Scenario**: Check current prices for a watchlist

**Input**:

```
Check prices for my top holdings: BTC, ETH, SOL
```

**Claude's Response**:

```
Fetching current prices...

================================================================================
  CRYPTO PRICES                                          Updated: [timestamp]
================================================================================

  Symbol     Price (USD)      24h Change     Volume (24h)      Market Cap
--------------------------------------------------------------------------------
  BTC       $97,234.56          +2.34%      $28.5B            $1.92T
  ETH        $3,456.78          +1.87%      $12.3B            $415.2B
  SOL          $142.34          +5.12%       $2.1B             $61.4B
--------------------------------------------------------------------------------

  Total Portfolio Change: +2.44%

================================================================================
```

**User Benefit**: Instant visibility into holdings without checking multiple sources

---

## 9. Integration Points

### External Systems

**System 1**: CoinGecko API

- **Purpose**: Primary price data source
- **Integration Type**: REST API
- **Authentication**: Optional API key for higher limits
- **Data Flow**: Skill → API → Parse JSON → Cache → Format → User

**System 2**: Yahoo Finance (via yfinance)

- **Purpose**: Historical OHLCV data, backup price source
- **Integration Type**: Python library
- **Authentication**: None
- **Data Flow**: Skill → yfinance → DataFrame → CSV/JSON → User

### Internal Dependencies

**Dependency 1**: Local Cache System

- **What it provides**: Fast access to recently fetched prices
- **Why needed**: Reduces API calls, improves response time

**Dependency 2**: Python Libraries

- **Libraries**: requests, pandas, yfinance
- **Versions**: requests>=2.28, pandas>=2.0, yfinance>=0.2.30

### Skills That Depend on This

| Skill | How It Uses Price Data |
|-------|------------------------|
| market-movers-scanner | Compares price changes to find movers |
| crypto-portfolio-tracker | Values holdings at current prices |
| crypto-tax-calculator | Gets cost basis and current values |
| defi-yield-optimizer | Calculates yield in USD terms |
| liquidity-pool-analyzer | Values LP positions |
| staking-rewards-optimizer | Calculates staking APY |
| crypto-derivatives-tracker | Tracks underlying asset prices |
| dex-aggregator-router | Compares DEX prices to CEX |
| options-flow-analyzer | Values options based on underlying |
| arbitrage-opportunity-finder | Detects price discrepancies |

---

## 10. Constraints & Assumptions

### Technical Constraints

1. **API Rate Limits**: CoinGecko free tier limits to 10-50 calls/minute
2. **Token Budget**: Must fit in 5,000 token skill discovery limit
3. **Processing Time**: Max 10 seconds for any operation
4. **Dependencies**: Requires network access for price fetching

### Business Constraints

1. **API Costs**: Free tier preferred; Pro tier ($129/month) if needed
2. **Timeline**: Foundation skill - must be complete before dependent skills
3. **Resources**: Single developer (Claude)

### Assumptions

1. **Assumption 1**: CoinGecko API remains available and free tier sufficient
   - **Risk if false**: Switch to backup provider (CoinMarketCap)
   - **Mitigation**: Implement provider abstraction layer

2. **Assumption 2**: Users have Python 3.8+ installed
   - **Risk if false**: Scripts won't run
   - **Mitigation**: Document requirements, provide error messages

---

## 11. Risk Assessment

### Technical Risks

**Risk 1**: API Rate Limiting

- **Probability**: High (free tier has strict limits)
- **Impact**: Medium (degraded but not broken experience)
- **Mitigation**: Aggressive caching, exponential backoff, batch requests

**Risk 2**: API Downtime

- **Probability**: Low (CoinGecko has 99.9% uptime)
- **Impact**: High (skill unusable)
- **Mitigation**: Multiple fallback providers, cached data with staleness warning

### User Experience Risks

**Risk 1**: Skill Over-Triggering (False Positives)

- **Probability**: Medium
- **Impact**: Low (user can clarify)
- **Mitigation**: Precise trigger phrases, domain-specific keywords

**Risk 2**: Stale Data Confusion

- **Probability**: Medium (if cache too aggressive)
- **Impact**: Medium (bad trading decisions)
- **Mitigation**: Clear timestamps, configurable cache duration, manual refresh

---

## 12. Open Questions

**Resolved Questions**:

1. ✅ **Question**: Which API should be primary?
   - **Decision**: CoinGecko (largest free tier, most assets)

2. ✅ **Question**: How long to cache spot prices?
   - **Decision**: 30 seconds (balance between freshness and rate limits)

**Pending Questions**: None

---

## 13. Appendix: Examples

### Example 1: Single Asset Price Check

**User Request**:

```
What's the current Ethereum price?
```

**Expected Skill Behavior**:

1. Parse "Ethereum" as ETH
2. Check cache for recent ETH price
3. If stale (>30s), fetch from CoinGecko
4. Format response with price card

**Expected Output**:

```
ETH (Ethereum)
$3,456.78 USD
+1.87% (24h) | Vol: $12.3B | MCap: $415.2B
Updated: [timestamp]
```

### Example 2: Watchlist Scan

**User Request**:

```
Check prices for the top 10 cryptos
```

**Expected Behavior**:

1. Use predefined "crypto_top10" watchlist
2. Batch fetch all 10 prices
3. Format as table with all metrics

### Example 3: Historical Data Export

**User Request**:

```
Get Bitcoin's price history for the last 30 days and save to CSV
```

**Expected Behavior**:

1. Fetch 30-day OHLCV data from yfinance
2. Format as DataFrame
3. Export to `data/BTC_30d_[date].csv`
4. Confirm file location

---

## 14. Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0.0 | 2025-01-01 | Initial stub | Jeremy Longshore |
| 2.0.0 | 2025-01-14 | Full PRD per Intent Solutions standard | Jeremy Longshore |

---

## 15. Approval

| Role | Name | Approval Date | Signature |
|------|------|---------------|-----------|
| Product Owner | Jeremy Longshore | 2025-01-14 | ✓ |
| Tech Lead | Claude (Opus 4.5) | 2025-01-14 | ✓ |

---

**Document maintained by**: Intent Solutions
**Standard**: Intent Solutions Enterprise Skill PRD Template v1.0
