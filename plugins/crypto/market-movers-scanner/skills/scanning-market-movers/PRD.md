# PRD: Scanning Market Movers

## Document Control

| Field | Value |
|-------|-------|
| Skill Name | scanning-market-movers |
| Type | Data Analysis / Market Intelligence |
| Domain | Cryptocurrency Trading |
| Target Users | Day Traders, Swing Traders, Market Analysts |
| Priority | High (P1) |
| Version | 2.0.0 |
| Author | Jeremy Longshore <jeremy@intentsolutions.io> |
| Created | 2025-01-14 |
| Updated | 2025-01-14 |

---

## Executive Summary

The scanning-market-movers skill provides real-time detection and analysis of significant price movements and unusual volume patterns across cryptocurrency markets. By continuously monitoring thousands of assets, this skill identifies emerging opportunities (gainers, losers, volume spikes) before they become widely recognized, giving traders a time advantage in fast-moving markets.

**Key Value Proposition:**
- Detect market moves as they happen, not after
- Filter noise with configurable thresholds
- Correlate price action with volume confirmation
- Rank movers by significance for prioritization

**Dependencies:**
This skill depends on the `tracking-crypto-prices` skill from `market-price-tracker` plugin for underlying price data infrastructure.

---

## Problem Statement

### Pain Points

1. **Information Overload**: With 10,000+ cryptocurrencies, manually tracking significant moves is impossible
2. **Delayed Reaction**: Traditional watchlists only show assets you're already tracking
3. **False Signals**: Raw price changes without volume context lead to poor decisions
4. **Scattered Data**: Price, volume, and market cap data spread across multiple sources
5. **Alert Fatigue**: Most scanners trigger too many low-quality alerts

### Desired State

Traders receive timely, filtered notifications of significant market moves with:
- Configurable thresholds (% change, volume multiplier, market cap filters)
- Volume-confirmed price action
- Ranked results by significance score
- Historical context (was this move expected based on recent patterns?)

---

## Target Users

### Persona 1: Day Trader (Primary)

**Profile:**
- Trades daily, often multiple times per day
- Focuses on momentum and volatility plays
- Needs real-time or near-real-time data
- Makes decisions in minutes, not hours

**Goals:**
- Find assets breaking out before the crowd
- Identify dip-buying opportunities
- Avoid low-liquidity traps
- Time entries and exits precisely

**Pain Points:**
- Misses moves while analyzing other assets
- Gets caught in pump-and-dumps
- Spends too much time switching between tools

### Persona 2: Swing Trader

**Profile:**
- Holds positions for days to weeks
- Focuses on trend shifts and reversals
- Values comprehensive analysis over speed
- Monitors broader market context

**Goals:**
- Identify trend changes early
- Find oversold assets with recovery potential
- Avoid catching falling knives
- Build positions during accumulation phases

**Pain Points:**
- Entry timing in volatile markets
- Distinguishing dead cat bounces from real reversals
- Managing watchlist of hundreds of assets

### Persona 3: Market Analyst

**Profile:**
- Researches market structure and dynamics
- Produces reports and insights for others
- Values historical patterns and context
- Requires exportable data for further analysis

**Goals:**
- Identify sector rotations and themes
- Track whale and institutional activity
- Generate data-driven market summaries
- Backtest scanner effectiveness

**Pain Points:**
- Manual data collection is time-consuming
- Difficulty correlating moves across assets
- Need to process large datasets efficiently

---

## User Stories

### Critical (Must Have)

#### US-1: Basic Market Scan

**As a** day trader
**I want to** scan the market for top gainers and losers
**So that** I can identify trading opportunities quickly

**Acceptance Criteria:**
- Scan returns top 20 gainers and top 20 losers by 24h change
- Results include: symbol, price, 24h change %, volume, market cap
- Scan completes within 5 seconds
- Results sortable by change %, volume, or market cap

#### US-2: Volume Spike Detection

**As a** trader
**I want to** detect assets with unusual volume
**So that** I can find price moves with strong conviction

**Acceptance Criteria:**
- Identify assets where current volume > 2x average daily volume
- Filter by minimum volume threshold (e.g., > $1M/day)
- Show volume ratio (current vs average)
- Correlate with price direction (up/down on high volume)

#### US-3: Customizable Thresholds

**As a** swing trader
**I want to** set my own thresholds for what constitutes a "mover"
**So that** I only see moves that match my trading style

**Acceptance Criteria:**
- Configure minimum % change threshold (e.g., 5%, 10%, 20%)
- Configure volume multiplier threshold (e.g., 2x, 5x, 10x)
- Configure market cap filters (e.g., > $100M, $1B-$10B)
- Save configurations as named presets

### Important (Should Have)

#### US-4: Sector/Category Scanning

**As a** market analyst
**I want to** scan specific sectors (DeFi, L2, NFT, etc.)
**So that** I can identify sector-specific themes

**Acceptance Criteria:**
- Filter by predefined categories (DeFi, Layer 2, NFT, Gaming, etc.)
- Show sector aggregate statistics (avg change, total volume)
- Identify sector leaders and laggards

#### US-5: Timeframe Selection

**As a** trader
**I want to** scan across different timeframes
**So that** I can identify moves at different scales

**Acceptance Criteria:**
- Support 1h, 4h, 24h, 7d timeframes
- Show change and volume metrics for selected timeframe
- Allow multiple timeframe comparison

#### US-6: Export Results

**As a** analyst
**I want to** export scan results
**So that** I can analyze data in external tools

**Acceptance Criteria:**
- Export to JSON with full metadata
- Export to CSV for spreadsheet analysis
- Include timestamp and scan parameters

### Nice to Have (Could Have)

#### US-7: Significance Scoring

**As a** trader
**I want to** see moves ranked by significance
**So that** I can prioritize the most important moves

**Acceptance Criteria:**
- Composite score based on % change, volume ratio, market cap
- Configurable scoring weights
- Explanation of why a move scored highly

#### US-8: Alert Integration

**As a** trader
**I want to** receive alerts when significant moves occur
**So that** I don't have to constantly watch the scanner

**Acceptance Criteria:**
- Threshold-based alerting
- Output suitable for piping to notification systems
- Rate limiting to prevent alert spam

---

## Functional Requirements

### REQ-1: Market Data Scanning

**Description:** Scan cryptocurrency markets for price and volume movements

**Specifications:**
- Fetch current prices and 24h changes for all tracked assets
- Calculate volume ratios vs historical averages
- Support filtering by market cap, volume, and category
- Return results sorted by configurable criteria

### REQ-2: Threshold-Based Filtering

**Description:** Apply user-defined thresholds to identify significant moves

**Specifications:**
- Price change thresholds: absolute % change cutoffs
- Volume thresholds: multiplier vs average, absolute minimums
- Market cap thresholds: min/max filters
- Combine filters with AND logic

### REQ-3: Significance Scoring

**Description:** Calculate composite significance score for ranking

**Specifications:**
- Score = weighted combination of change%, volume ratio, and market cap
- Default weights: change (40%), volume (40%), market cap (20%)
- Configurable weights via settings
- Normalize scores to 0-100 range

### REQ-4: Output Formatting

**Description:** Present results in human-readable and machine-readable formats

**Specifications:**
- Table format: aligned columns with headers
- JSON format: structured data with metadata
- CSV format: spreadsheet-compatible export
- Minimal format: one-line summary per mover

### REQ-5: Category Filtering

**Description:** Filter movers by asset category

**Specifications:**
- Predefined categories: DeFi, Layer2, NFT, Gaming, Meme, Stablecoins
- Custom category support via configuration
- Aggregate category statistics

---

## Non-Goals

This skill does NOT:
- Execute trades or manage positions
- Provide trading signals or recommendations
- Store historical scan results (ephemeral by design)
- Replace technical analysis tools
- Guarantee profitable trading outcomes

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Scan Latency | < 5 seconds | Time from command to results |
| Coverage | > 10,000 assets | Number of assets in scan universe |
| False Positive Rate | < 20% | Moves that reverse within 1 hour |
| User Activation | Daily use | Scanner used in active trading session |

---

## UX Flow

### Basic Scan Flow

```
1. User invokes scanner with default or custom thresholds
2. Skill fetches current market data via tracking-crypto-prices dependency
3. Skill calculates changes, volume ratios, and significance scores
4. Skill filters results against thresholds
5. Skill ranks and formats top movers
6. Results displayed in user-requested format
```

### Configuration Flow

```
1. User modifies settings.yaml with custom thresholds
2. User creates named presets (e.g., "aggressive", "conservative")
3. User selects preset when invoking scanner
4. Skill applies preset configuration to scan
```

---

## Integration Points

### Dependencies

| Dependency | Purpose |
|------------|---------|
| tracking-crypto-prices | Price data, historical prices, market cap |
| CoinGecko API | Category metadata, additional filtering |

### Dependent Skills

| Skill | How It Uses Market Movers |
|-------|--------------------------|
| crypto-signal-generator | Volume-confirmed signals |
| arbitrage-opportunity-finder | Price discrepancy detection |
| whale-alert-monitor | Correlation with large transactions |

---

## Constraints & Assumptions

### Constraints

- Rate limited by CoinGecko API (handled by price-tracker caching)
- Historical volume data limited to available timeframes
- Real-time data subject to exchange reporting delays

### Assumptions

- Users understand cryptocurrency market mechanics
- Users have internet connectivity
- tracking-crypto-prices skill is available and configured
- CoinGecko API remains accessible

---

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| API rate limits | Stale data | Medium | Leverage tracking-crypto-prices cache |
| Market manipulation | False signals | High | Volume confirmation, market cap filters |
| Flash crashes | Missed moves | Low | Configurable refresh intervals |
| Data quality issues | Incorrect rankings | Medium | Multi-source validation |

---

## Examples

### Example 1: Daily Scan

```bash
python ${CLAUDE_SKILL_DIR}/scripts/scanner.py --timeframe 24h --top 20
```

Output shows top 20 gainers and losers with volume confirmation.

### Example 2: High-Volume Movers

```bash
python ${CLAUDE_SKILL_DIR}/scripts/scanner.py --volume-spike 3x --min-volume 1000000
```

Output shows assets with 3x+ average volume and > $1M daily volume.

### Example 3: DeFi Sector Scan

```bash
python ${CLAUDE_SKILL_DIR}/scripts/scanner.py --category defi --min-change 5
```

Output shows DeFi tokens with > 5% change.

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2024-10-20 | Auto-generated | Initial stub |
| 2.0.0 | 2025-01-14 | Jeremy Longshore | Full PRD with requirements |
