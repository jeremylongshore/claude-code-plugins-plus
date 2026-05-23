# PRD: Crypto Derivatives Tracker

## Summary

**One-liner**: Track cryptocurrency futures, options, and perpetual swaps with comprehensive market analysis
**Domain**: Cryptocurrency / Derivatives Trading
**Users**: Derivatives Traders, Arbitrage Specialists, Risk Managers

---

## Problem Statement

Crypto derivatives markets generate massive amounts of data across multiple exchanges - funding rates, open interest, liquidations, options flow, and basis spreads. Traders need to:

1. Monitor funding rates across 5+ exchanges simultaneously
2. Track open interest changes to gauge market positioning
3. Identify liquidation clusters and cascade risks
4. Analyze options flow for smart money signals
5. Find basis trading and funding arbitrage opportunities

Manual monitoring is impractical given the 24/7 nature of crypto markets and the speed at which conditions change. A unified tool that aggregates derivatives data and generates actionable insights is essential.

---

## Target Users

### Persona 1: Derivatives Day Trader

- **Background**: Full-time crypto trader focusing on perpetual swaps
- **Goals**: Profit from funding rate extremes, OI divergences, and liquidation cascades
- **Pain Points**: Data fragmented across exchanges, misses funding changes
- **Success Criteria**: Consistent funding capture, early entry before liquidation cascades

### Persona 2: Basis Arbitrageur

- **Background**: Market-neutral trader running cash-and-carry strategies
- **Goals**: Lock in risk-free returns via spot-futures basis trades
- **Pain Points**: Manual basis calculations, timing entry/exit around funding
- **Success Criteria**: Captures basis premium with minimal directional risk

### Persona 3: Options Flow Analyst

- **Background**: Institutional researcher tracking smart money via options
- **Goals**: Identify unusual options activity and positioning before moves
- **Pain Points**: Options data scattered, hard to interpret Greeks at scale
- **Success Criteria**: Detects smart money positioning ahead of price moves

---

## User Stories

### US-1: Funding Rate Monitoring (Critical)

**As a** derivatives trader
**I want to** see funding rates across all major exchanges in one view
**So that** I can identify arbitrage opportunities and sentiment extremes

**Acceptance Criteria**:

- Display funding rates for BTC, ETH, SOL across Binance, Bybit, OKX, Deribit
- Show current, 24h average, and 7d average rates
- Calculate annualized funding yield
- Alert when funding exceeds configurable threshold (default: 0.1%)

### US-2: Open Interest Analysis (Critical)

**As a** derivatives trader
**I want to** track open interest changes by exchange and contract type
**So that** I can gauge market positioning and trend strength

**Acceptance Criteria**:

- Show total OI in USD and BTC/ETH equivalent
- Display 24h, 7d, 30d OI changes
- Compare OI across exchanges (market share)
- Analyze OI vs price divergences

### US-3: Liquidation Monitoring (Critical)

**As a** derivatives trader
**I want to** see liquidation levels and recent liquidation events
**So that** I can avoid cascade zones and position for liquidation-driven moves

**Acceptance Criteria**:

- Display liquidation heatmap with price levels
- Show recent large liquidations (>$100K)
- Calculate long/short liquidation zones
- Estimate cascade risk at key levels

### US-4: Basis Tracking (High)

**As a** basis arbitrageur
**I want to** see spot-futures basis across all expiries
**So that** I can identify cash-and-carry opportunities

**Acceptance Criteria**:

- Calculate perpetual-spot basis (real-time)
- Calculate quarterly-spot basis with annualized yield
- Compare basis across exchanges
- Signal when basis exceeds profitability threshold

### US-5: Options Flow Analysis (High)

**As an** options analyst
**I want to** track unusual options activity and positioning
**So that** I can identify smart money moves

**Acceptance Criteria**:

- Show large options trades (premium > $100K)
- Display put/call ratio by volume and OI
- Calculate max pain for upcoming expiries
- Analyze implied volatility levels and skew

### US-6: Multi-Asset Dashboard (Medium)

**As a** portfolio manager
**I want to** see derivatives metrics for multiple assets
**So that** I can monitor my entire derivatives exposure

**Acceptance Criteria**:

- Support BTC, ETH, SOL, and major altcoins
- Display comparative funding rates
- Show aggregate OI across assets
- Highlight assets with extreme metrics

---

## Functional Requirements

### REQ-1: Multi-Exchange Data Aggregation

- Fetch funding rates from Binance, Bybit, OKX, Deribit, BitMEX
- Aggregate open interest across exchanges
- Support both USDT-margined and coin-margined contracts

### REQ-2: Funding Rate Analysis

- Current funding rate with countdown to next payment
- Historical funding (24h, 7d, 30d averages)
- Funding arbitrage opportunities between exchanges
- Annualized funding yield calculation

### REQ-3: Open Interest Analytics

- Total OI by asset and exchange
- OI change tracking (1h, 24h, 7d)
- Long/short ratio by exchange
- OI vs price divergence detection

### REQ-4: Liquidation Intelligence

- Real-time liquidation tracking
- Liquidation heatmap generation
- Cascade risk estimation
- Historical liquidation analysis

### REQ-5: Options Market Data

- Implied volatility by strike and expiry
- Put/call ratio tracking
- Max pain calculation
- Options flow for large trades

### REQ-6: Basis Calculations

- Perpetual basis (funding-implied)
- Quarterly futures basis
- Annualized yield calculation
- Basis convergence alerts

---

## API Integrations

| Source | Data Provided | Rate Limits |
|--------|---------------|-------------|
| Binance Futures | Funding, OI, liquidations | 1200/min |
| Bybit | Funding, OI, positions | 120/min |
| OKX | Funding, OI, options | 60/min |
| Deribit | Options, funding, OI | 10K/day |
| Coinglass | Aggregated derivatives | API key required |

---

## Success Metrics

1. **Data Freshness**: All metrics updated within 5 seconds
2. **Exchange Coverage**: 5+ CEX, 3+ DEX protocols supported
3. **Alert Accuracy**: 90%+ of funding extremes detected
4. **User Satisfaction**: Clear, actionable output format

---

## Non-Goals

- **Not** executing trades or managing positions
- **Not** providing financial advice or guaranteed signals
- **Not** real-time order book depth analysis
- **Not** custom strategy backtesting
- **Not** portfolio accounting or tax reporting

---

## Risk Considerations

### Market Risks

- Funding rates can flip rapidly during volatility
- Liquidation cascades can gap through levels
- Options pricing models have limitations

### Data Risks

- Exchange API outages or rate limits
- Delayed or stale data during high volatility
- Inconsistent data formats between exchanges

### User Risks

- Over-reliance on signals without risk management
- Misinterpretation of complex derivatives metrics
- Leverage amplifies both gains and losses

---

## Examples

### Example 1: Funding Rate Alert

```
User: "What's the funding rate for BTC?"

Output:
BTC PERPETUAL FUNDING RATES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Exchange    Current    24h Avg    7d Avg    Next Payment
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Binance     +0.0150%   +0.0120%   +0.0080%  2h 15m
Bybit       +0.0180%   +0.0140%   +0.0100%  2h 15m
OKX         +0.0130%   +0.0110%   +0.0090%  2h 15m
Deribit     +0.0200%   +0.0150%   +0.0120%  2h 15m
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Annualized: +15.77% (based on current rates)
Sentiment: Moderately Bullish
Arbitrage: None (rates aligned)
```

### Example 2: Liquidation Analysis

```
User: "Where are the BTC liquidation levels?"

Output:
BTC LIQUIDATION HEATMAP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Current Price: $67,500

LONG LIQUIDATIONS (below current):
  $65,000: $125M at risk (HIGH DENSITY)
  $62,500: $85M at risk
  $60,000: $210M at risk (CRITICAL CLUSTER)

SHORT LIQUIDATIONS (above current):
  $70,000: $95M at risk
  $72,500: $145M at risk (HIGH DENSITY)
  $75,000: $180M at risk

Last 24h Liquidations:
  Longs: $45.2M | Shorts: $32.8M
  Largest: $5.2M long at $66,800
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-01-15 | Jeremy Longshore | Initial PRD |
