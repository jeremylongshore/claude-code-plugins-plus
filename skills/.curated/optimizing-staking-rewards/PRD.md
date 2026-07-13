# PRD: Staking Rewards Optimizer

## Summary

**One-liner**: Compare and optimize staking rewards across validators, protocols, and blockchains to maximize yield while managing risk.

**Domain**: Cryptocurrency / Proof-of-Stake / DeFi
**Users**: Stakers, Yield Farmers, Portfolio Managers, DeFi Researchers

## Problem Statement

Proof-of-stake staking involves significant complexity:

- Dozens of chains with different staking mechanisms (native, liquid, restaking)
- Hundreds of validators per chain with varying performance and commission rates
- Multiple liquid staking protocols with different risk/reward profiles
- Dynamic APYs that change based on participation rates and tokenomics
- Hidden costs (gas, unstaking periods, slashing risk)
- No unified interface to compare opportunities across the ecosystem

Stakers need a tool that aggregates staking data, calculates true returns after costs, assesses risks, and recommends optimal allocation strategies.

## Target Users

### Persona 1: Yield-Seeking Staker

- **Profile**: Individual crypto holder looking to earn passive income
- **Goals**: Maximize staking returns with acceptable risk
- **Pain Points**: Overwhelmed by protocol choices, doesn't understand risk factors
- **Needs**: Simple comparison tables, risk ratings, clear recommendations

### Persona 2: DeFi Portfolio Manager

- **Profile**: Professional managing staked assets across multiple chains
- **Goals**: Optimal allocation across protocols, track performance over time
- **Pain Points**: Manual tracking across chains, calculating true yields
- **Needs**: Multi-chain view, position projections, rebalancing recommendations

### Persona 3: Liquid Staking Researcher

- **Profile**: Analyst evaluating liquid staking derivatives (LSDs)
- **Goals**: Compare stETH, rETH, frxETH, and other LSDs objectively
- **Pain Points**: Metrics scattered across protocols, hard to compare apples-to-apples
- **Needs**: Standardized comparisons, peg stability data, protocol risk scores

## User Stories

### US-1: Compare Staking Opportunities

**As a** yield-seeking staker
**I want to** compare staking yields across different chains and protocols
**So that** I can identify the best opportunities for my assets

**Acceptance Criteria**:

- Shows APY/APR for native staking on major chains (ETH, ATOM, DOT, SOL)
- Includes liquid staking options (Lido, Rocket Pool, Frax, Marinade)
- Displays lock-up periods and unbonding times
- Factors in estimated gas costs for each option

### US-2: Optimize Current Portfolio

**As a** DeFi portfolio manager
**I want to** input my current staking positions and get optimization recommendations
**So that** I can improve my overall yield

**Acceptance Criteria**:

- Accepts current positions (token, amount, current protocol, APY)
- Calculates total portfolio yield
- Suggests reallocation to higher-yield opportunities
- Shows projected improvement in annual returns
- Warns about switching costs and timing considerations

### US-3: Assess Protocol Risk

**As a** liquid staking researcher
**I want to** see risk assessments for each protocol
**So that** I can balance yield against safety

**Acceptance Criteria**:

- Risk score (1-10) for each protocol
- Factors: audit status, time in production, TVL, slashing history
- Validator concentration metrics
- Smart contract risk indicators
- Clearly explains risk factors

### US-4: Calculate True Returns

**As a** yield-seeking staker
**I want to** see true APY after all costs
**So that** I can make accurate comparisons

**Acceptance Criteria**:

- Shows gross APY (advertised rate)
- Deducts protocol fees and commissions
- Estimates gas costs for staking/unstaking
- Shows net APY after all fees
- Includes auto-compound benefits where applicable

### US-5: Compare Liquid Staking Tokens

**As a** liquid staking researcher
**I want to** compare LSDs on standardized metrics
**So that** I can recommend the best options

**Acceptance Criteria**:

- Shows exchange rate vs underlying (stETH/ETH ratio)
- Tracks 30-day peg stability
- Displays TVL and market share
- Shows secondary market liquidity (DEX depth)
- Includes protocol token rewards if any

## Functional Requirements

### REQ-1: Multi-Source Data Aggregation

- Fetch staking data from DeFiLlama pools API
- Query StakingRewards.com or similar for native staking rates
- Support major chains: Ethereum, Cosmos, Polkadot, Solana, Avalanche, Near
- Cache data with configurable TTL (default 5 minutes)

### REQ-2: Yield Calculations

- Convert between APY and APR
- Calculate effective APY with compounding frequency
- Estimate gas costs based on current network conditions
- Project returns for custom time horizons (1M, 3M, 6M, 1Y)

### REQ-3: Risk Assessment Engine

- Score protocols based on multiple factors
- Track validator performance and slashing events
- Monitor smart contract audit status
- Flag concentration risks (single validator dominance)

### REQ-4: Portfolio Optimization

- Accept current positions as input
- Run optimization algorithm for allocation
- Respect user constraints (max per protocol, excluded chains)
- Generate rebalancing recommendations

### REQ-5: Multiple Output Formats

- Table format for quick comparisons
- JSON for programmatic use
- CSV for spreadsheet analysis
- Detailed report with recommendations

## Non-Goals

- **Not providing financial advice**: Educational tool only
- **Not executing transactions**: Analysis only, no wallet integration
- **Not tracking real-time prices**: Focus on staking yields, not trading
- **Not supporting every chain**: Focus on major PoS chains

## Success Metrics

- Skill activates correctly on staking-related queries
- Returns accurate staking rates (within 1% of source data)
- Risk scores align with community consensus on protocol safety
- Users find optimization recommendations actionable

## Integration Points

### Input

- User's current staking positions (optional)
- Target assets (e.g., "ETH", "ATOM")
- Risk tolerance (conservative, moderate, aggressive)
- Investment timeframe

### Output

- Comparison tables of staking opportunities
- Optimization recommendations with projected returns
- Risk assessments for each option
- Step-by-step implementation guidance

### Data Sources

- **DeFiLlama Pools API**: `https://yields.llama.fi/pools` (liquid staking)
- **StakingRewards API**: Native staking rates and validator data
- **CoinGecko API**: Price data for USD calculations
- **Protocol APIs**: Direct queries to Lido, Rocket Pool, etc.

## UX Flow

```
User Input (asset/positions)
    ↓
Fetch Data (DeFiLlama, StakingRewards)
    ↓
Calculate Metrics (net APY, risk scores)
    ↓
Run Optimization (if positions provided)
    ↓
Format Output (table/JSON/report)
    ↓
Display Recommendations
```

## Constraints

- API rate limits on free tiers
- Some data sources may be incomplete or delayed
- Staking rates are point-in-time snapshots
- Risk scores are estimates, not guarantees

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Stale data | Medium | Cache with short TTL, show data age |
| Inaccurate APY | High | Cross-reference multiple sources |
| Missing protocols | Medium | Focus on major protocols first |
| API unavailability | Medium | Fallback to cached data |

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-01-15 | Jeremy Longshore | Initial PRD |
