# PRD: Finding Arbitrage Opportunities

## Summary

**One-liner**: Real-time detection and analysis of arbitrage opportunities across CEX, DEX, and cross-chain markets.

**Domain**: Cryptocurrency / Trading / DeFi

**Users**: Arbitrage Traders, Quantitative Researchers, DeFi Developers

## Problem Statement

Cryptocurrency markets are fragmented across hundreds of centralized exchanges (CEX) and decentralized exchanges (DEX), creating price discrepancies that represent arbitrage opportunities. However, manually monitoring these spreads across multiple venues is impractical due to:

- **Volume**: Thousands of trading pairs across hundreds of exchanges
- **Speed**: Opportunities exist for seconds to minutes
- **Complexity**: Multi-hop paths (triangular arbitrage) require graph analysis
- **Costs**: Fees, slippage, and gas must be accurately calculated

Traders need automated tools to scan markets, identify profitable opportunities, and calculate net profit after all costs.

## Target Users

### Persona 1: Arbitrage Trader (Alex)

- **Role**: Professional crypto trader specializing in arbitrage strategies
- **Goals**: Find consistent low-risk profits from market inefficiencies
- **Pain Points**: Missing opportunities due to manual monitoring; executing unprofitable trades due to hidden costs
- **Technical Level**: High (understands order books, APIs, gas costs)

### Persona 2: Quantitative Researcher (Quinn)

- **Role**: Researcher analyzing market microstructure and efficiency
- **Goals**: Study arbitrage dynamics, measure market integration, backtest strategies
- **Pain Points**: Lack of historical spread data; difficulty aggregating prices across venues
- **Technical Level**: Very High (builds custom models and systems)

### Persona 3: DeFi Bot Developer (Dana)

- **Role**: Developer building automated trading bots and MEV strategies
- **Goals**: Integrate opportunity detection into automated execution systems
- **Pain Points**: Need reliable APIs and data formats; require accurate profit calculations
- **Technical Level**: Expert (writes smart contracts, understands MEV)

## User Stories

### US-1: CEX Spread Scanning (Critical)

**As** an arbitrage trader,
**I want** to scan price spreads across centralized exchanges for a token pair,
**So that** I can identify exchange-to-exchange arbitrage opportunities.

**Acceptance Criteria:**

- Fetch bid/ask prices from at least 5 major CEXs
- Calculate spread after trading fees (maker/taker)
- Display opportunities above a configurable profit threshold
- Show estimated profit in USD and percentage

### US-2: DEX Price Comparison (Critical)

**As** a DeFi developer,
**I want** to compare token prices across decentralized exchanges,
**So that** I can find DEX-to-DEX arbitrage without CEX dependency.

**Acceptance Criteria:**

- Query prices from Uniswap, SushiSwap, Curve, Balancer
- Account for DEX swap fees (0.01% - 1%)
- Estimate gas costs for swap transactions
- Support multiple chains (Ethereum, Polygon, Arbitrum)

### US-3: Triangular Arbitrage Detection (High)

**As** a quantitative researcher,
**I want** to discover triangular arbitrage paths within a single exchange,
**So that** I can exploit multi-hop inefficiencies.

**Acceptance Criteria:**

- Build price graph from available trading pairs
- Find profitable circular paths (A→B→C→A)
- Calculate net profit after all hop fees
- Rank paths by profit and execution complexity

### US-4: Cross-Chain Opportunities (Medium)

**As** a DeFi bot developer,
**I want** to identify cross-chain price differences,
**So that** I can build bridge arbitrage strategies.

**Acceptance Criteria:**

- Compare same-token prices across L1/L2 chains
- Factor in bridge fees and transfer times
- Estimate total gas costs (both chains)
- Flag opportunities with acceptable delay risk

### US-5: Real-Time Monitoring (High)

**As** an arbitrage trader,
**I want** to continuously monitor spreads with alerts,
**So that** I don't miss time-sensitive opportunities.

**Acceptance Criteria:**

- Configurable polling interval (default: 5 seconds)
- Alert when spread exceeds threshold
- Rate-limit handling for API calls
- Graceful degradation if exchange is unavailable

### US-6: Profit Calculator (Critical)

**As** any user,
**I want** accurate profit calculations after all costs,
**So that** I only pursue genuinely profitable opportunities.

**Acceptance Criteria:**

- Include exchange trading fees (maker/taker)
- Include DEX swap fees
- Include network gas costs
- Include slippage estimates based on trade size
- Show breakeven prices

## Functional Requirements

- **REQ-1**: Multi-exchange price aggregation (CEX and DEX)
- **REQ-2**: Spread calculation with fee deduction
- **REQ-3**: Triangular arbitrage path finding
- **REQ-4**: Cross-chain price comparison
- **REQ-5**: Configurable profit threshold filtering
- **REQ-6**: Real-time monitoring mode with alerts
- **REQ-7**: JSON export for bot integration
- **REQ-8**: Historical spread tracking (optional)

## API Integrations

| API | Purpose | Auth Required |
|-----|---------|---------------|
| CoinGecko | Price aggregation, exchange list | No (free tier) |
| CCXT | Unified CEX API access | Per-exchange |
| Uniswap Subgraph | DEX pool prices | No |
| SushiSwap Subgraph | DEX pool prices | No |
| Etherscan | Gas price oracle | Optional |
| Chainlink | Price feeds (on-chain) | No |

## Non-Goals

- **Trade Execution**: This skill finds opportunities; it does not execute trades
- **Wallet Management**: No private key handling or transaction signing
- **MEV Protection**: Flashbots integration is out of scope
- **Historical Backtesting**: Focus is real-time detection, not historical analysis
- **Portfolio Tracking**: Separate from position management

## Success Metrics

- Opportunities identified match real market spreads (±0.1%)
- Profit calculations accurate within 5% of actual execution
- Latency from price update to opportunity detection < 2 seconds
- False positive rate (unprofitable opportunities shown as profitable) < 5%

## Constraints & Assumptions

**Constraints:**

- Free API tiers have rate limits (e.g., CoinGecko: 10-30 calls/min)
- DEX prices require blockchain queries (latency ~1-3s)
- Cross-chain bridge times vary (minutes to hours)

**Assumptions:**

- Users have basic understanding of arbitrage concepts
- Users can obtain exchange API keys if needed
- Network connectivity is stable

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Stale prices | Execute at wrong price | Show data freshness; require < 5s staleness |
| Rate limiting | Miss opportunities | Implement backoff; use multiple API sources |
| Slippage miscalculation | Negative profit | Conservative slippage estimates; size warnings |
| Exchange downtime | Incomplete data | Mark unavailable exchanges; use alternatives |

## Educational Disclaimer

**FOR EDUCATIONAL PURPOSES ONLY**

Arbitrage trading involves significant risks:

- Opportunities may disappear before execution
- Price data may be delayed or inaccurate
- Transaction fees can exceed expected profits
- Market manipulation can create false opportunities
- Automated trading requires careful risk management

This tool provides analysis only. Users are responsible for their own trading decisions.
