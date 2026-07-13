# PRD: DeFi Yield Optimizer

## Summary

**One-liner**: Find and compare DeFi yield opportunities across protocols with APY calculations, risk assessment, and optimization recommendations.

**Domain**: Cryptocurrency / DeFi / Yield Farming
**Users**: Yield Farmers, DeFi Investors, Treasury Managers

## Problem Statement

DeFi yield farming is complex due to:

- Hundreds of protocols across multiple chains offering varying APYs
- Constantly changing rates that require monitoring
- Hidden risks (impermanent loss, smart contract risk, rug pulls)
- Gas costs eating into yields on high-frequency strategies
- Difficulty comparing true yields across different reward structures

Users need a tool that aggregates yield opportunities, calculates real APY/APR, assesses risks, and recommends optimal strategies based on their risk tolerance.

## User Personas

### Persona 1: Yield Farmer (Maya)

- **Profile**: Active DeFi user with $50K-$500K seeking maximum yields
- **Pain Points**: Manually checking dozens of protocols, missing rate changes, unexpected impermanent loss
- **Goals**: Find highest yields adjusted for risk, automate monitoring, optimize gas costs

### Persona 2: Conservative DeFi Investor (Chen)

- **Profile**: Traditional investor exploring DeFi with $10K-$100K, risk-averse
- **Pain Points**: Uncertain about protocol safety, confused by APY vs APR, worried about rug pulls
- **Goals**: Find stable yields from audited protocols, understand risks clearly

### Persona 3: DAO Treasury Manager (Alex)

- **Profile**: Manages $1M+ treasury, accountable to governance
- **Pain Points**: Must balance yield with security, needs audit trail, limited to blue-chip protocols
- **Goals**: Generate yield on idle treasury, maintain liquidity, minimize governance risk

## User Stories

### US-1: Discover Yield Opportunities (Critical)

**As a** yield farmer
**I want to** see top yield opportunities across DeFi protocols
**So that** I can find the best places to deploy my capital

**Acceptance Criteria**:

- Shows top yields from major protocols (Aave, Compound, Curve, Convex, etc.)
- Displays APY/APR with breakdown (base + rewards)
- Filters by chain (Ethereum, Arbitrum, Polygon, etc.)
- Sorts by APY, TVL, or risk score

### US-2: Assess Protocol Risk (Critical)

**As a** conservative investor
**I want to** understand the risks of each yield opportunity
**So that** I can make informed decisions matching my risk tolerance

**Acceptance Criteria**:

- Shows audit status and auditor names
- Displays TVL and protocol age
- Calculates impermanent loss for LP positions
- Flags high-risk indicators (new protocols, unaudited, declining TVL)

### US-3: Calculate True Yield (High)

**As a** yield farmer
**I want to** see gas-adjusted net APY
**So that** I know my actual expected returns

**Acceptance Criteria**:

- Factors in gas costs for entry/exit
- Accounts for compounding frequency
- Shows net APY after all costs
- Compares across position sizes

### US-4: Track Yield Changes (High)

**As a** treasury manager
**I want to** monitor yield rate changes over time
**So that** I can rebalance when opportunities shift

**Acceptance Criteria**:

- Shows historical APY trends (7d, 30d)
- Alerts when yields drop below threshold
- Tracks protocol TVL changes
- Compares current vs historical averages

### US-5: Optimize Strategy (Medium)

**As a** yield farmer
**I want to** get optimization recommendations
**So that** I can maximize risk-adjusted returns

**Acceptance Criteria**:

- Suggests allocation across protocols
- Balances yield vs risk based on preference
- Considers gas costs in recommendations
- Provides diversification suggestions

## Functional Requirements

### REQ-1: Protocol Data Aggregation

- Fetch yields from major DeFi protocols via APIs
- Support multiple chains (Ethereum, Arbitrum, Polygon, Optimism, BSC)
- Normalize APY/APR calculations across protocols
- Cache data with appropriate TTL (5-15 minutes)

### REQ-2: Yield Calculation

- Calculate base APY from protocol rates
- Add reward token APY (e.g., CRV, CVX incentives)
- Estimate impermanent loss for LP positions
- Factor in compounding frequency

### REQ-3: Risk Assessment

- Protocol age and audit status
- TVL trends (growing, stable, declining)
- Smart contract risk indicators
- Centralization risk factors

### REQ-4: Output Formats

- Table format for terminal display
- JSON for programmatic use
- Detailed breakdown per opportunity
- Summary comparison view

## API Integrations

- **DeFiLlama API**: Protocol TVL and yield data (free, comprehensive)
- **CoinGecko API**: Token prices for reward valuation
- **DeBank API**: Protocol information (optional)

## Non-Goals

- Automated trading or position management (information only)
- Real-time price alerts (use dedicated monitoring tools)
- Cross-chain bridging recommendations
- Tax implications of strategies

## Success Metrics

- Skill activates on yield-related trigger phrases
- Returns accurate APY data matching protocol UIs
- Risk assessments align with community consensus
- Response time < 10 seconds for standard queries

## Technical Constraints

- Python 3.8+ with requests library
- No wallet connections or private keys
- API rate limits (DeFiLlama: generous, CoinGecko: 10-30/min free)
- Data freshness: 5-15 minute cache acceptable

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| API data inaccuracy | Medium | High | Cross-reference multiple sources |
| Protocol not listed | Medium | Medium | Manual addition capability |
| Rate changes rapidly | High | Low | Show data age, refresh option |
| Misleading APY claims | Medium | High | Show breakdown, warn on outliers |

## Examples

### Example 1: Find Top Yields

```bash
python yield_optimizer.py --chain ethereum --min-tvl 10000000 --sort apy
```

### Example 2: Risk-Adjusted Search

```bash
python yield_optimizer.py --risk-level low --min-apy 5 --audited-only
```

### Example 3: Compare Specific Protocols

```bash
python yield_optimizer.py --protocols aave,compound,curve --asset USDC
```

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-15 | Jeremy Longshore | Initial PRD |
