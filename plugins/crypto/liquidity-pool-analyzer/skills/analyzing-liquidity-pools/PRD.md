# PRD: Liquidity Pool Analyzer

## Summary

**One-liner**: Analyze DEX liquidity pools for TVL, volume, fees, impermanent loss, and LP profitability.

**Domain**: Cryptocurrency / DeFi / Liquidity Providing
**Users**: Liquidity Providers, DeFi Traders, Protocol Analysts

## Problem Statement

Liquidity providing on DEXs involves complex trade-offs:

- Understanding TVL distribution and pool depth
- Calculating potential impermanent loss for different price scenarios
- Analyzing fee income vs. IL to determine profitability
- Comparing pools across protocols and chains
- Monitoring pool health and detecting risks (rug pulls, imbalanced pools)

Users need a tool that aggregates pool data, calculates IL scenarios, estimates LP returns, and identifies optimal pools based on their risk tolerance.

## User Personas

### Persona 1: Active Liquidity Provider (Marcus)

- **Profile**: Experienced DeFi user with $20K-$200K providing liquidity
- **Pain Points**: Manually tracking multiple positions, calculating IL, comparing fee APRs
- **Goals**: Maximize fee income while managing IL risk, find optimal entry/exit points

### Persona 2: DeFi Researcher (Luna)

- **Profile**: Analyst studying protocol health and pool dynamics
- **Pain Points**: Gathering data from multiple sources, analyzing pool composition trends
- **Goals**: Monitor protocol TVL, identify anomalies, track whale movements

### Persona 3: Arbitrage Bot Operator (Dev)

- **Profile**: Technical trader running automated strategies
- **Pain Points**: Need real-time pool reserves, slippage estimates, gas optimization
- **Goals**: Find pools with significant depth, minimize slippage, optimize trade routes

## User Stories

### US-1: Analyze Pool Metrics (Critical)

**As a** liquidity provider
**I want to** see comprehensive metrics for a specific pool
**So that** I can evaluate it before adding liquidity

**Acceptance Criteria**:

- Shows TVL, 24h volume, and fee tier
- Displays current token ratio and prices
- Shows historical volume/TVL ratio
- Includes pool contract address and creation date

### US-2: Calculate Impermanent Loss (Critical)

**As a** liquidity provider
**I want to** calculate IL for various price scenarios
**So that** I can understand my risk exposure

**Acceptance Criteria**:

- Calculate IL for specific price changes
- Show breakeven fee income needed
- Compare IL vs. holding both tokens
- Project IL over time periods

### US-3: Estimate LP Returns (High)

**As a** liquidity provider
**I want to** estimate my potential returns from fees
**So that** I can decide if the IL risk is worth it

**Acceptance Criteria**:

- Calculate fee APR from historical volume
- Show fee income projection for position size
- Factor in reward tokens if applicable
- Display net APY after estimated IL

### US-4: Compare Pools (High)

**As a** DeFi researcher
**I want to** compare similar pools across protocols
**So that** I can identify the best opportunities

**Acceptance Criteria**:

- Compare TVL, volume, and fees across pools
- Show fee tier differences (0.05%, 0.30%, 1%)
- Highlight volume/TVL efficiency
- Display historical performance

### US-5: Monitor Pool Health (Medium)

**As a** liquidity provider
**I want to** monitor my LP positions for risks
**So that** I can react to adverse conditions

**Acceptance Criteria**:

- Alert on significant TVL changes
- Warn on imbalanced token ratios
- Flag low liquidity or volume drop
- Track price divergence from oracles

## Functional Requirements

### REQ-1: Pool Data Aggregation

- Fetch pool data from DEX subgraphs (Uniswap, Curve, Balancer)
- Support multiple chains (Ethereum, Arbitrum, Polygon, BSC)
- Normalize pool metrics across protocols
- Cache data with appropriate TTL

### REQ-2: Impermanent Loss Calculator

- Calculate IL from entry price to current price
- Support various price change scenarios
- Compare IL across different fee tiers
- Estimate breakeven time based on volume

### REQ-3: Fee Analysis

- Calculate realized fees from swap volume
- Project fee income over time periods
- Factor in protocol fee splits
- Include reward token APY if applicable

### REQ-4: Pool Health Metrics

- Track TVL trends over time
- Monitor token ratio imbalances
- Detect unusual volume patterns
- Compare against oracle prices

### REQ-5: Output Formats

- Table format for terminal display
- JSON for programmatic use
- Detailed pool analysis report
- Comparison tables

## API Integrations

- **The Graph**: Uniswap V2/V3, Curve, Balancer subgraphs
- **DeFiLlama**: Pool TVL and volume data
- **CoinGecko**: Token prices for IL calculations
- **Dune Analytics**: Advanced on-chain queries (optional)

## Non-Goals

- Automated LP position management
- Trading execution or swaps
- Gas estimation for deposits/withdrawals
- Portfolio tracking across multiple wallets

## Success Metrics

- Skill activates on pool analysis phrases
- IL calculations match established formulas
- Pool data accuracy vs. protocol frontends
- Response time < 10 seconds for standard queries

## Technical Constraints

- Python 3.8+ with requests library
- No private key or wallet connection
- Subgraph rate limits (100 req/min)
- Data freshness: blocks may be ~15s behind

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Subgraph data delays | Medium | Medium | Multiple data sources, timestamp warnings |
| IL formula errors | Low | High | Test against known calculators |
| Pool not indexed | Medium | Low | Fallback to on-chain RPC calls |
| Price oracle divergence | Medium | Medium | Compare multiple price sources |

## Examples

### Example 1: Analyze Specific Pool

```bash
python pool_analyzer.py --pool 0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640 --chain ethereum
```

### Example 2: Calculate IL Scenario

```bash
python pool_analyzer.py --il-calc --entry-price 2000 --current-price 3000 --token-pair ETH/USDC
```

### Example 3: Compare Similar Pools

```bash
python pool_analyzer.py --compare --pair ETH/USDC --protocols uniswap-v3,curve,balancer
```

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-15 | Jeremy Longshore | Initial PRD |
