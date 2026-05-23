# PRD: Tracking Crypto Portfolio

## Document Control

| Field | Value |
|-------|-------|
| **Skill Name** | tracking-crypto-portfolio |
| **Type** | Portfolio Management & Analytics |
| **Domain** | Cryptocurrency Portfolio Tracking |
| **Target Users** | Traders, Investors, Portfolio Managers |
| **Priority** | P1 - Core Analytics Skill |
| **Version** | 2.0.0 |
| **Author** | Jeremy Longshore <jeremy@intentsolutions.io> |

---

## Executive Summary

The tracking-crypto-portfolio skill provides comprehensive cryptocurrency portfolio management with real-time valuations, performance analytics, and allocation insights. It enables users to track holdings across multiple wallets, exchanges, and chains with unified reporting.

**Value Proposition**: Consolidate multi-chain, multi-exchange crypto holdings into a single view with real-time valuations, P&L tracking, and allocation analysis.

---

## Problem Statement

### Current Pain Points

1. **Fragmented Holdings**: Assets spread across exchanges, wallets, and chains
2. **Manual Tracking**: Spreadsheets can't keep up with real-time prices
3. **No Cost Basis**: Hard to track acquisition costs and realize P&L
4. **Allocation Drift**: No visibility into portfolio concentration risks
5. **Performance Blind Spots**: Can't compare performance across assets

### Impact of Not Solving

- Missed rebalancing opportunities
- Tax reporting nightmares
- Overexposure to single assets
- No clear view of actual returns
- Emotional decisions from lack of data

---

## Target Users

### Persona 1: Active Trader

- **Name**: Marcus
- **Role**: Day/swing trader
- **Goals**: Track positions across exchanges, monitor P&L in real-time
- **Pain Points**: Holdings on 5 exchanges, needs quick portfolio snapshot
- **Usage**: Multiple times daily, JSON export for trading bot integration

### Persona 2: Long-Term Investor

- **Name**: Sarah
- **Role**: HODLer with diverse portfolio
- **Goals**: Track overall portfolio value, monitor allocation percentages
- **Pain Points**: Assets in cold wallets and exchanges, no unified view
- **Usage**: Weekly check-ins, detailed allocation reports

### Persona 3: DeFi User

- **Name**: Alex
- **Role**: DeFi yield farmer
- **Goals**: Track LP positions, staking rewards, multi-chain holdings
- **Pain Points**: Assets across Ethereum, Arbitrum, Polygon, etc.
- **Usage**: Daily monitoring, export for yield calculations

---

## User Stories

### US-1: Portfolio Overview (Critical)

**As a** crypto investor
**I want to** see my total portfolio value across all holdings
**So that** I know my current net worth in crypto

**Acceptance Criteria:**

- Display total portfolio value in USD
- Show 24h and 7d change (absolute and percentage)
- List top holdings by value
- Complete in under 10 seconds

### US-2: Holdings Breakdown (Critical)

**As a** portfolio manager
**I want to** see each asset with quantity, value, and allocation
**So that** I can monitor concentration risk

**Acceptance Criteria:**

- List all holdings with current prices
- Show allocation percentage per asset
- Highlight overweighted positions (>25% allocation)
- Sort by value, alphabetical, or allocation

### US-3: Performance Tracking (Important)

**As a** trader
**I want to** track P&L for each position
**So that** I know which trades are profitable

**Acceptance Criteria:**

- Calculate unrealized P&L per holding
- Show cost basis vs current value
- Display percentage gain/loss
- Support FIFO/LIFO/average cost methods

### US-4: Multi-Format Export (Important)

**As a** quant
**I want to** export portfolio data in JSON format
**So that** I can feed it into my analysis tools

**Acceptance Criteria:**

- JSON export with all holdings and metadata
- CSV export for spreadsheet analysis
- Include timestamps for time-series tracking
- Support custom field selection

### US-5: Allocation Analysis (Nice-to-Have)

**As an** investor
**I want to** see portfolio allocation by category
**So that** I can ensure proper diversification

**Acceptance Criteria:**

- Group by asset type (L1, L2, DeFi, stables, etc.)
- Show pie chart or percentage breakdown
- Flag concentration risks
- Compare to target allocation

---

## Functional Requirements

### REQ-1: Holdings Management

- Add holdings manually (coin, quantity, cost basis)
- Import from JSON portfolio file
- Support for multiple portfolio files
- Track acquisition date for tax purposes

### REQ-2: Real-Time Valuations

- Fetch current prices from CoinGecko API
- Calculate total value per holding
- Sum to portfolio total value
- Cache prices with configurable TTL

### REQ-3: Performance Metrics

- Calculate 24h, 7d, 30d price changes
- Track unrealized P&L per position
- Support multiple cost basis methods
- Historical performance tracking (if data available)

### REQ-4: Allocation Analysis

- Calculate allocation percentages
- Group by configurable categories
- Flag overweight positions
- Compare to benchmark allocations

### REQ-5: Output Formatting

- Table format for terminal display
- JSON format for programmatic use
- CSV format for spreadsheet import
- Summary format for quick checks

---

## Non-Goals

- **Exchange Integration**: No direct API connections to exchanges (manual entry only)
- **Trading**: No buy/sell execution capabilities
- **Wallet Monitoring**: No on-chain wallet tracking (use dedicated tools)
- **Tax Calculations**: Basic P&L only, not full tax reporting
- **Historical Charts**: Current snapshot only, not time-series visualization

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Load time | < 10s | Script execution time |
| Price accuracy | Real-time within 5 min | API freshness check |
| Export completeness | All holdings included | Field validation |
| User activation | Triggered by portfolio phrases | Plugin analytics |

---

## UX Flow

```
User: "show my crypto portfolio"
  │
  ├─► Load portfolio file (JSON)
  │
  ├─► Fetch current prices (CoinGecko)
  │
  ├─► Calculate valuations
  │
  ├─► Calculate allocations
  │
  ├─► Calculate P&L (if cost basis provided)
  │
  └─► Display formatted output
```

---

## Integration Points

### Dependencies

- **market-price-tracker**: For real-time price data (can work standalone)
- CoinGecko API for price fetching

### Consumers

- **crypto-tax-calculator**: Portfolio data for tax reporting
- **trading-strategy-backtester**: Portfolio composition input

### Data Sources

- CoinGecko API (free tier)
- User-provided portfolio JSON file

---

## Constraints & Assumptions

### Constraints

- CoinGecko free tier rate limits (~10-30 calls/minute)
- Manual portfolio entry (no exchange API sync)
- Single currency display (USD)

### Assumptions

- User maintains portfolio file with accurate holdings
- Cost basis data optional but beneficial
- Network connectivity for price fetching

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| CoinGecko rate limiting | Medium | Medium | Caching, batch requests |
| Coin not found | Low | Low | Map common symbols, warn user |
| Stale prices | Low | Medium | Show last updated timestamp |
| Portfolio file format errors | Medium | Medium | Validation with clear errors |

---

## Examples

### Example 1: Quick Portfolio Check

```bash
python portfolio_tracker.py --portfolio holdings.json
```

Shows portfolio summary with total value and top holdings.

### Example 2: Detailed Holdings

```bash
python portfolio_tracker.py --portfolio holdings.json --detailed
```

Full breakdown with allocation percentages and P&L.

### Example 3: JSON Export

```bash
python portfolio_tracker.py --portfolio holdings.json --format json --output portfolio.json
```

Export for analysis tools.

---

## Portfolio File Format

```json
{
  "name": "Main Portfolio",
  "holdings": [
    {
      "coin": "BTC",
      "quantity": 0.5,
      "cost_basis": 25000,
      "acquired": "2024-01-15"
    },
    {
      "coin": "ETH",
      "quantity": 10,
      "cost_basis": 2000,
      "acquired": "2024-02-01"
    }
  ]
}
```

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-10-16 | Jeremy Longshore | Initial stub |
| 2.0.0 | 2026-01-14 | Jeremy Longshore | Full PRD, implementation |
