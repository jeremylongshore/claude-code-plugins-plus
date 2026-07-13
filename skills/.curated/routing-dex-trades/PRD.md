# PRD: DEX Aggregator Router

## Summary

**One-liner**: Route trades across multiple DEXs to find optimal prices with minimal slippage and gas costs
**Domain**: Cryptocurrency / DeFi Trading
**Users**: DeFi Traders, Arbitrage Bots, Portfolio Managers, MEV-Aware Users

## Problem Statement

DeFi traders face fragmented liquidity across dozens of decentralized exchanges. A single trade on one DEX may have 5% price impact, while splitting across multiple venues could reduce it to 0.5%. Without aggregation tools, traders:

1. Overpay due to poor price discovery across DEXs
2. Suffer unnecessary slippage from suboptimal routing
3. Miss multi-hop opportunities (ETH→USDC→TOKEN cheaper than ETH→TOKEN)
4. Waste gas on inefficient transaction paths
5. Fall victim to MEV extraction (sandwich attacks, frontrunning)

## Target Users

### Persona 1: Active DeFi Trader

- **Profile**: Trades $1K-$50K weekly across multiple tokens
- **Pain Points**: Manually checking 5+ DEXs is time-consuming; misses optimal routes
- **Goals**: Best execution price with minimal effort; understand true cost of trades
- **Usage Pattern**: Multiple trades daily, needs quick comparisons

### Persona 2: Arbitrage Bot Operator

- **Profile**: Runs automated trading strategies exploiting price differences
- **Pain Points**: Needs real-time route optimization; gas efficiency is critical
- **Goals**: Programmatic access to optimal routes; sub-second decisions
- **Usage Pattern**: High frequency, API-first, cost-sensitive

### Persona 3: Whale / Treasury Manager

- **Profile**: Executes large trades ($100K+) for DAOs or personal portfolios
- **Pain Points**: Large trades create massive price impact; MEV exposure
- **Goals**: Minimize market impact; protect against sandwich attacks
- **Usage Pattern**: Infrequent but high-value trades requiring careful execution

## User Stories

### Critical (P0)

1. **As a DeFi trader**, I want to compare prices across multiple DEXs for a token pair, so that I can execute at the best available rate.
   - **Acceptance Criteria**:
     - Query returns prices from at least 5 major DEXs (Uniswap V2/V3, SushiSwap, Curve, Balancer)
     - Response includes price, liquidity depth, and estimated gas cost per venue
     - Results sorted by effective rate (price after gas)

2. **As a trader**, I want to see optimal route recommendations including multi-hop paths, so that I can minimize price impact on larger trades.
   - **Acceptance Criteria**:
     - System identifies multi-hop routes (e.g., ETH→USDC→TOKEN)
     - Compares direct vs. multi-hop with total cost analysis
     - Shows price impact at each hop

3. **As a large trader**, I want split-order recommendations across multiple DEXs, so that I can reduce market impact on whale-sized trades.
   - **Acceptance Criteria**:
     - For trades >$10K, analyze split order strategies
     - Show percentage allocation per DEX to minimize total slippage
     - Calculate aggregate vs. single-venue price improvement

### Important (P1)

1. **As a MEV-aware user**, I want to see MEV protection recommendations, so that I can avoid sandwich attacks.
   - **Acceptance Criteria**:
     - Flag high-MEV-risk routes (low liquidity, pending large orders)
     - Recommend private transaction options (Flashbots, CoW Swap)
     - Show estimated MEV exposure per route

2. **As a gas-conscious trader**, I want gas-optimized route selection, so that I don't waste ETH on complex routes for small trades.
   - **Acceptance Criteria**:
     - Calculate break-even point for multi-hop vs. direct routes
     - Factor current gas prices into recommendations
     - Warn when gas cost exceeds 2% of trade value

### Nice-to-Have (P2)

1. **As a trader**, I want historical route performance data, so that I can trust the recommendations.
   - **Acceptance Criteria**:
     - Show average slippage vs. quoted for each DEX
     - Display route success rates
     - Track execution vs. quoted price variance

## Functional Requirements

### Core Features

- **REQ-1**: Multi-DEX Price Fetching
  - Query Uniswap V2, Uniswap V3, SushiSwap, Curve, Balancer
  - Integrate aggregator APIs (1inch, Paraswap, 0x)
  - Support major chains: Ethereum, Arbitrum, Polygon, Optimism

- **REQ-2**: Route Discovery Engine
  - Direct swap path identification
  - Multi-hop route construction (up to 3 hops)
  - Split order optimization (2-5 venue splits)

- **REQ-3**: Price Impact Analysis
  - Calculate slippage at various trade sizes
  - Identify liquidity depth per venue
  - Show impact curves for trade sizing decisions

- **REQ-4**: Gas Cost Optimization
  - Estimate gas per route (simple vs. complex)
  - Calculate effective rate including gas
  - Dynamic gas price integration

- **REQ-5**: MEV Protection Assessment
  - Risk scoring for sandwich attack exposure
  - Private transaction recommendations
  - CoW Swap / Flashbots integration guidance

### Trade Size Recommendations

| Trade Size | Recommended Strategy |
|------------|---------------------|
| < $1K | Direct swap on highest liquidity DEX |
| $1K - $10K | Compare direct vs. multi-hop; single venue |
| $10K - $100K | Multi-hop + potential 2-3 way split |
| > $100K | Algorithmic splitting; private transactions; OTC consideration |

## Non-Goals

- **NOT** executing trades (read-only analysis and recommendations)
- **NOT** providing financial advice or trade signals
- **NOT** supporting centralized exchanges
- **NOT** real-time order book streaming (snapshot-based)
- **NOT** building trading bots (analysis only)

## API Integrations

| API | Purpose | Auth | Rate Limits |
|-----|---------|------|-------------|
| 1inch API | Aggregated quotes, optimal routes | API Key (optional) | 1 req/sec (free) |
| Paraswap API | Alternative aggregator quotes | None | 10 req/sec |
| 0x API | Swap quotes with affiliate fees | API Key | 3 req/sec |
| The Graph | DEX subgraph queries | None | Varies by hosted/decentralized |
| DeFiLlama | TVL and liquidity data | None | Generous |
| Etherscan | Gas price oracle | API Key | 5 req/sec |

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Route Accuracy | Quoted vs. executed within 0.5% | Backtesting against historical |
| Coverage | 90%+ of trade volume covered | DEX market share analysis |
| Response Time | <3 seconds for full analysis | Performance monitoring |
| User Satisfaction | Recommendations followed >70% | Usage analytics |

## UX Flow

```
1. User Input
   ├── Token pair (ETH/USDC)
   ├── Trade amount ($5,000)
   ├── Chain (Ethereum mainnet)
   └── Preferences (gas sensitivity, MEV protection)

2. Data Collection (parallel)
   ├── Query 1inch API
   ├── Query Paraswap API
   ├── Query DEX subgraphs
   └── Fetch gas prices

3. Route Analysis
   ├── Direct routes ranked
   ├── Multi-hop routes discovered
   ├── Split strategies calculated
   └── MEV risk assessed

4. Results Presentation
   ├── Best route highlighted
   ├── Alternative options shown
   ├── Cost breakdown (price + gas + slippage)
   └── MEV protection recommendations
```

## Constraints & Assumptions

### Constraints

- API rate limits require caching and request optimization
- Gas prices volatile; recommendations valid for ~30 seconds
- Some DEXs have different liquidity on different chains

### Assumptions

- User has basic understanding of DEX trading
- User can execute recommended trades manually or via preferred interface
- Real-time prices acceptable (not tick-by-tick precision)

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| API rate limiting | Medium | High | Multi-source fallback; caching |
| Stale price data | Medium | Medium | Timestamp warnings; refresh prompts |
| Route becomes suboptimal | High | Low | Clear validity window; refresh before execution |
| MEV exposure on recommended route | Low | High | Conservative recommendations; private TX options |

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-01-15 | Claude | Initial PRD |
