# ARD: Liquidity Pool Analyzer

> Part of [Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)

## Architecture Pattern

**Pattern**: Multi-Source Data Aggregation + Analysis Pipeline
**Type**: Fetch → Normalize → Calculate → Analyze → Output

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────────┐
│  Subgraphs  │───▶│  Normalizer  │───▶│ IL Calculator│───▶│   Analyzer   │
│  + APIs     │    │  (Pool Data) │    │  (Math)      │    │  (Output)    │
└─────────────┘    └──────────────┘    └─────────────┘    └──────────────┘
       │                  │                   │                   │
       ▼                  ▼                   ▼                   ▼
  Raw Pool Data     Normalized Pools     IL Scenarios      Pool Report
  (reserves, vol)   (TVL, APR, fees)     (loss, breakeven) (table/JSON)
```

## Workflow

### Step 1: Fetch Pool Data

Query subgraphs and APIs for pool information.

### Step 2: Normalize Metrics

- Convert reserves to USD TVL
- Calculate fee APR from volume
- Standardize across protocols

### Step 3: Calculate IL/Returns

- Impermanent loss for price changes
- Fee income projections
- Net APY estimates

### Step 4: Analyze and Output

- Pool health metrics
- Comparison tables
- Risk warnings

## Data Flow

```
Input:                     Processing:                  Output:
┌─────────────────┐       ┌─────────────────┐         ┌─────────────────┐
│ User Criteria   │       │ Data Aggregator │         │ Pool Report     │
│ - Pool address  │──────▶│ - The Graph     │         │ - TVL/Volume    │
│ - Token pair    │       │ - DeFiLlama     │         │ - Fee APR       │
│ - Chain         │       │ - CoinGecko     │         │ - IL scenarios  │
│ - Protocol      │       └────────┬────────┘         │ - Risk metrics  │
└─────────────────┘                │                  │                 │
                          ┌────────▼────────┐         │ IL Calculator   │
                          │ Pool Normalizer │         │ - Entry/exit IL │
                          │ - TVL calc      │────────▶│ - Breakeven     │
                          │ - Fee rates     │         │ - Projections   │
                          │ - Token ratios  │         │                 │
                          └────────┬────────┘         │ Comparison      │
                          ┌────────▼────────┐         │ - Cross-pool    │
                          │ IL Calculator   │         │ - Cross-protocol│
                          │ - Price change  │         └─────────────────┘
                          │ - Fee offset    │
                          │ - Net returns   │
                          └─────────────────┘
```

## Directory Structure

```
plugins/crypto/liquidity-pool-analyzer/skills/analyzing-liquidity-pools/
├── PRD.md                          # Product requirements
├── ARD.md                          # This file
├── SKILL.md                        # Core instructions
├── scripts/
│   ├── pool_analyzer.py            # Main CLI entry point
│   ├── pool_fetcher.py             # Subgraph/API data fetching
│   ├── il_calculator.py            # Impermanent loss math
│   ├── pool_metrics.py             # TVL, fees, APR calculations
│   └── formatters.py               # Output formatting
├── references/
│   ├── errors.md                   # Error handling guide
│   ├── examples.md                 # Usage examples
│   └── protocols.md                # Supported DEX protocols
└── config/
    └── settings.yaml               # API endpoints, protocol configs
```

## Component Design

### 1. Pool Fetcher (`pool_fetcher.py`)

**Purpose**: Fetch pool data from subgraphs and APIs.

**Data Sources**:

| Source | Data | Rate Limit |
|--------|------|------------|
| The Graph | Pool reserves, swaps, ticks | 100/min |
| DeFiLlama | TVL, volume | Generous |
| CoinGecko | Token prices | 10-30/min |

**Subgraph Queries**:

```graphql
# Uniswap V3 Pool Query
query Pool($id: ID!) {
  pool(id: $id) {
    token0 { symbol, decimals }
    token1 { symbol, decimals }
    feeTier
    liquidity
    sqrtPrice
    tick
    totalValueLockedUSD
    volumeUSD
  }
}
```

**Caching Strategy**:

- Memory cache: 30 seconds for hot pools
- File cache: 5 minutes for historical data

### 2. IL Calculator (`il_calculator.py`)

**Purpose**: Calculate impermanent loss and breakeven metrics.

**Core Formulas**:

```python
# Impermanent Loss Formula
# price_ratio = new_price / original_price
IL = 2 * sqrt(price_ratio) / (1 + price_ratio) - 1

# Value if held (no LP)
value_held = (amount0 * price0_new) + (amount1 * price1_new)

# Value in LP
value_lp = value_held * (1 + IL)  # IL is negative

# Breakeven Volume (for fee tier)
# days_to_breakeven = (IL_percent * TVL) / (daily_volume * fee_tier)
```

**Output**:

```python
{
    "entry_price": 2000,
    "current_price": 3000,
    "price_change": 50.0,  # percentage
    "il_percent": -5.72,   # negative = loss
    "value_if_held": 2500,
    "value_in_lp": 2357,
    "il_usd": -143,
    "breakeven_days": 45,
}
```

### 3. Pool Metrics (`pool_metrics.py`)

**Purpose**: Calculate derived metrics from raw pool data.

**Calculations**:

```python
# TVL from reserves
tvl_usd = reserve0 * price0 + reserve1 * price1

# Fee APR (annualized)
daily_fees = volume_24h * fee_tier
fee_apr = (daily_fees / tvl_usd) * 365 * 100

# Volume/TVL Ratio (efficiency)
volume_tvl_ratio = volume_24h / tvl_usd

# Token Weight (for imbalance detection)
weight_token0 = (reserve0 * price0) / tvl_usd
```

**Health Indicators**:

| Metric | Healthy | Warning | Critical |
|--------|---------|---------|----------|
| Volume/TVL | > 0.05 | 0.01-0.05 | < 0.01 |
| Token Balance | 40-60% | 30-40% or 60-70% | < 30% or > 70% |
| Fee APR | > 5% | 2-5% | < 2% |

### 4. Formatters (`formatters.py`)

**Purpose**: Format output for display.

**Formats**:

- Table: Pool metrics summary
- JSON: Structured data for analysis
- Report: Detailed pool analysis

## API Integration

### The Graph (Primary)

**Endpoints**:

```
Uniswap V3 Ethereum: https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3
Uniswap V3 Arbitrum: https://api.thegraph.com/subgraphs/name/ianlapham/uniswap-v3-arbitrum
Curve:              https://api.thegraph.com/subgraphs/name/curvefi/curve
Balancer V2:        https://api.thegraph.com/subgraphs/name/balancer-labs/balancer-v2
```

**Query Pattern**:

```python
query = """
{
  pools(where: {id: $pool_id}) {
    token0 { symbol }
    token1 { symbol }
    totalValueLockedUSD
    volumeUSD
  }
}
"""
```

### DeFiLlama Fallback

**Endpoints**:

```
GET /pools          # All DEX pools
GET /pool/{poolId}  # Specific pool
```

## Error Handling Strategy

| Error Type | Handling | User Message |
|------------|----------|--------------|
| Subgraph timeout | Retry 2x, use DeFiLlama | "Using cached/fallback data" |
| Pool not found | Check chain, validate address | "Pool not found on [chain]" |
| Price unavailable | Use pool ratio as backup | "Using pool price (oracle unavailable)" |
| Invalid address | Validate format | "Invalid pool address format" |

## Caching Architecture

```
Cache Layer:
┌─────────────────────────────────────────┐
│              Memory Cache               │
│  (current session, 30 sec TTL)          │
├─────────────────────────────────────────┤
│              File Cache                 │
│  (~/.lp_analyzer_cache.json, 5 min TTL) │
├─────────────────────────────────────────┤
│              Subgraph/API               │
│  (fresh data when cache miss/stale)     │
└─────────────────────────────────────────┘
```

## Performance

| Operation | Target | Constraint |
|-----------|--------|------------|
| Subgraph query | < 2 seconds | Network, rate limits |
| IL calculation | < 50ms | In-memory math |
| Pool metrics | < 100ms | Simple calculations |
| Total response | < 5 seconds | Full pipeline |

## Security Considerations

- No wallet connections
- No private key handling
- Read-only subgraph queries
- No smart contract interactions
- Cache contains only public pool data

## Testing Strategy

### Unit Tests

- IL formula validation
- Fee APR calculations
- TVL from reserves

### Integration Tests

- Subgraph query handling
- Multi-protocol normalization
- Error fallback scenarios

### Test Data

```json
{
  "pool": {
    "address": "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640",
    "token0": "USDC",
    "token1": "WETH",
    "fee_tier": 0.0005,
    "tvl": 500000000,
    "volume_24h": 100000000
  }
}
```

## Dependencies

**Required**:

- `requests` - HTTP client for APIs
- `json` - Data handling

**Optional**:

- `web3` - Direct RPC calls (fallback)

## Supported Protocols

### DEXs

- Uniswap V2, V3
- SushiSwap
- Curve
- Balancer V2

### Chains

- Ethereum
- Arbitrum
- Polygon
- Optimism
- BSC
