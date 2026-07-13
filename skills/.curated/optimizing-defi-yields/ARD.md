# ARD: DeFi Yield Optimizer

> Part of [Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)

## Architecture Pattern

**Pattern**: Data Aggregation Pipeline
**Type**: Multi-Source Fetch → Normalize → Score → Rank

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────────┐
│  DeFiLlama  │───▶│  Normalizer  │───▶│ Risk Scorer │───▶│   Ranker     │
│   + APIs    │    │  (Calculate) │    │  (Assess)   │    │  (Output)    │
└─────────────┘    └──────────────┘    └─────────────┘    └──────────────┘
       │                  │                   │                   │
       ▼                  ▼                   ▼                   ▼
  Protocol Data      Normalized APY      Risk Scores       Ranked Results
  TVL, Rewards       Base + Rewards      Audit/TVL/Age     Table/JSON
```

## Workflow

### Step 1: Fetch Protocol Data

Query DeFiLlama and other APIs for yield opportunities.

### Step 2: Normalize Yields

- Convert APR to APY where needed
- Calculate total yield (base + rewards)
- Factor in reward token prices

### Step 3: Assess Risks

- Check audit status
- Analyze TVL trends
- Score protocol maturity
- Flag anomalies

### Step 4: Rank and Output

- Sort by user preference (APY, risk, TVL)
- Apply filters
- Format for display

## Data Flow

```
Input:                     Processing:                  Output:
┌─────────────────┐       ┌─────────────────┐         ┌─────────────────┐
│ User Criteria   │       │ API Aggregator  │         │ Yield Table     │
│ - Chain filter  │──────▶│ - DeFiLlama     │         │ - Protocol name │
│ - Min TVL       │       │ - CoinGecko     │         │ - APY breakdown │
│ - Risk level    │       │ - Cache layer   │         │ - Risk score    │
│ - Asset filter  │       └────────┬────────┘         │ - TVL           │
└─────────────────┘                │                  │                 │
                          ┌────────▼────────┐         │ JSON Export     │
                          │ Yield Calculator│         │ - Full data     │
                          │ - APR to APY    │────────▶│ - Metadata      │
                          │ - Reward value  │         │                 │
                          │ - IL estimate   │         │ Recommendations │
                          └────────┬────────┘         │ - Top picks     │
                          ┌────────▼────────┐         │ - Diversified   │
                          │ Risk Assessor   │         └─────────────────┘
                          │ - Audit check   │
                          │ - TVL analysis  │
                          │ - Age score     │
                          └─────────────────┘
```

## Directory Structure

```
plugins/crypto/defi-yield-optimizer/skills/optimizing-defi-yields/
├── PRD.md                          # Product requirements
├── ARD.md                          # This file
├── SKILL.md                        # Core instructions
├── scripts/
│   ├── yield_optimizer.py          # Main CLI entry point
│   ├── protocol_fetcher.py         # API data fetching
│   ├── yield_calculator.py         # APY/APR calculations
│   ├── risk_assessor.py            # Risk scoring
│   └── formatters.py               # Output formatting
├── references/
│   ├── errors.md                   # Error handling guide
│   ├── examples.md                 # Usage examples
│   └── protocols.md                # Supported protocols
└── config/
    └── settings.yaml               # API endpoints, risk weights
```

## Component Design

### 1. Protocol Fetcher (`protocol_fetcher.py`)

**Purpose**: Aggregate yield data from multiple APIs.

**Data Sources**:

| Source | Data | Rate Limit |
|--------|------|------------|
| DeFiLlama | Yields, TVL, protocols | Generous |
| CoinGecko | Token prices | 10-30/min |

**Caching Strategy**:

- Cache TTL: 5 minutes for yields, 1 hour for protocol metadata
- Local file cache: `~/.defi_yield_cache.json`
- Fallback to cache on API failure

### 2. Yield Calculator (`yield_calculator.py`)

**Purpose**: Normalize and calculate true yields.

**Calculations**:

```python
# APR to APY conversion
APY = (1 + APR / n) ** n - 1  # n = compounding periods

# Total yield
total_apy = base_apy + reward_apy

# Reward APY calculation
reward_apy = (reward_tokens_per_year * token_price) / tvl_usd

# Impermanent loss estimation (for LPs)
IL = 2 * sqrt(price_ratio) / (1 + price_ratio) - 1
```

**Output**:

```python
{
    "protocol": "Curve",
    "pool": "3pool",
    "base_apy": 2.5,
    "reward_apy": 8.3,
    "total_apy": 10.8,
    "il_risk": "low",  # stablecoin pool
}
```

### 3. Risk Assessor (`risk_assessor.py`)

**Purpose**: Score protocol and pool risks.

**Risk Factors**:

| Factor | Weight | Scoring |
|--------|--------|---------|
| Audit Status | 30% | Audited=10, Partial=5, None=0 |
| TVL | 20% | >$100M=10, >$10M=7, >$1M=4, <$1M=1 |
| Protocol Age | 20% | >2yr=10, >1yr=7, >6mo=4, <6mo=1 |
| TVL Trend | 15% | Growing=10, Stable=7, Declining=3 |
| Token Concentration | 15% | Distributed=10, Concentrated=3 |

**Risk Levels**:

| Score | Level | Description |
|-------|-------|-------------|
| 8-10 | Low | Blue-chip, battle-tested |
| 5-7.9 | Medium | Established, some risk |
| 3-4.9 | High | Newer, less tested |
| 0-2.9 | Very High | Unaudited, low TVL |

### 4. Formatters (`formatters.py`)

**Purpose**: Format output for display.

**Formats**:

- Table: Terminal-friendly yield comparison
- JSON: Full data for programmatic use
- Summary: Quick overview of top opportunities

## API Integration

### DeFiLlama API

**Endpoints**:

```
GET /pools              # All yield pools
GET /pools/{chain}      # Chain-specific pools
GET /protocol/{name}    # Protocol details
```

**Response Structure**:

```json
{
  "data": [
    {
      "chain": "Ethereum",
      "project": "aave-v3",
      "symbol": "USDC",
      "tvlUsd": 1234567890,
      "apyBase": 2.5,
      "apyReward": 0,
      "apy": 2.5,
      "pool": "0x..."
    }
  ]
}
```

### CoinGecko API

**Endpoints**:

```
GET /simple/price?ids={tokens}&vs_currencies=usd
```

Used for reward token price lookups.

## Error Handling Strategy

| Error Type | Handling | User Message |
|------------|----------|--------------|
| API timeout | Retry 2x, use cache | "Using cached data (X min old)" |
| Rate limit | Use cache, wait | "Rate limited, showing cached data" |
| Invalid protocol | Skip, warn | "Protocol X not found" |
| No data for chain | Empty result | "No yields found for [chain]" |

## Caching Architecture

```
Cache Layer:
┌─────────────────────────────────────────┐
│              Memory Cache               │
│  (current session, 5 min TTL)           │
├─────────────────────────────────────────┤
│              File Cache                 │
│  (~/.defi_yield_cache.json, 1 hr TTL)   │
├─────────────────────────────────────────┤
│              API Fallback               │
│  (fresh data when cache miss/stale)     │
└─────────────────────────────────────────┘
```

## Performance

| Operation | Target | Constraint |
|-----------|--------|------------|
| API fetch | < 5 seconds | Network/rate limits |
| Calculate yields | < 1 second | In-memory |
| Risk scoring | < 500ms | Lookup tables |
| Total response | < 10 seconds | Full pipeline |

## Security Considerations

- No wallet connections or private keys
- No transaction signing
- Read-only API access
- No storage of sensitive data
- Cache contains only public market data

## Testing Strategy

### Unit Tests

- Yield calculations (APR to APY, rewards)
- Risk scoring logic
- Filter application

### Integration Tests

- API response handling
- Cache fallback scenarios
- Multi-chain queries

### Test Data

```json
{
  "pools": [
    {
      "protocol": "test-aave",
      "chain": "ethereum",
      "tvl": 100000000,
      "apy_base": 3.5,
      "apy_reward": 1.2,
      "audited": true,
      "age_days": 730
    }
  ]
}
```

## Dependencies

**Required**:

- `requests` - HTTP client for APIs
- `json` - Data handling
- `datetime` - Cache timestamps

**Optional**:

- `tabulate` - Pretty table output (fallback to manual)

## Supported Protocols

### Lending

- Aave (v2, v3)
- Compound (v2, v3)
- Spark
- Radiant

### DEX/AMM

- Curve
- Convex
- Balancer
- Uniswap v3

### Yield Aggregators

- Yearn
- Beefy
- Harvest

### Liquid Staking

- Lido
- Rocket Pool
- Frax ETH
