# ARD: Staking Rewards Optimizer

> Part of [Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)

## Architectural Overview

### Pattern

**Multi-Source Data Aggregation with Optimization Engine**

The skill aggregates staking data from multiple sources, calculates normalized metrics, runs optimization algorithms, and produces actionable recommendations.

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                     STAKING REWARDS OPTIMIZER                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐          │
│  │  DeFiLlama   │    │StakingRewards│    │  CoinGecko   │          │
│  │   Pools API  │    │     API      │    │  Prices API  │          │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘          │
│         │                   │                   │                   │
│         └─────────────┬─────┴───────────────────┘                   │
│                       │                                             │
│                       ▼                                             │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    DATA AGGREGATOR                           │   │
│  │  - Fetch staking pools by protocol/chain                    │   │
│  │  - Normalize APY/APR across sources                         │   │
│  │  - Cache with TTL for rate limiting                         │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                       │                                             │
│         ┌─────────────┼─────────────┐                              │
│         ▼             ▼             ▼                              │
│  ┌───────────┐ ┌───────────┐ ┌───────────────┐                    │
│  │  Metrics  │ │   Risk    │ │  Optimizer    │                    │
│  │Calculator │ │ Assessor  │ │   Engine      │                    │
│  └───────────┘ └───────────┘ └───────────────┘                    │
│         │             │             │                              │
│         └─────────────┼─────────────┘                              │
│                       ▼                                             │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                     FORMATTER                                │   │
│  │  - Table format with rankings                               │   │
│  │  - JSON for programmatic use                                │   │
│  │  - Detailed recommendations report                          │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Workflow

```
1. Parse Request
   ├── Extract target assets (ETH, ATOM, DOT, etc.)
   ├── Parse current positions if provided
   └── Identify risk tolerance and constraints

2. Fetch Data
   ├── Query DeFiLlama for liquid staking pools
   ├── Query StakingRewards for native staking
   ├── Get current prices for USD calculations
   └── Apply rate limiting and caching

3. Calculate Metrics
   ├── Normalize APY/APR across protocols
   ├── Calculate net yield after fees
   ├── Project returns for time horizons
   └── Generate risk scores

4. Optimize (if positions provided)
   ├── Run allocation algorithm
   ├── Apply user constraints
   └── Generate rebalancing recommendations

5. Format Output
   ├── Generate comparison tables
   ├── Create risk assessments
   └── Produce actionable recommendations
```

## Progressive Disclosure Strategy

### Level 1: Quick Summary

```
Top Staking Opportunities for ETH:
1. Rocket Pool (rETH): 4.2% APY - Low Risk
2. Lido (stETH): 4.0% APY - Low Risk
3. Frax (sfrxETH): 5.1% APY - Medium Risk
```

### Level 2: Comparison Table

Full table with all metrics: APY, fees, lock-up, risk score, TVL

### Level 3: Detailed Analysis

- Risk breakdown per protocol
- Fee structure analysis
- Implementation guide
- Position projections

## Tool Permission Strategy

### Allowed Tools

```yaml
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(crypto:staking-*)
```

### Scoped Access

- `Read`: Config files, reference documentation
- `Write`: Output reports, cache files
- `Edit`: Update local configurations
- `Bash(crypto:staking-*)`: Run staking analysis scripts only

### Rationale

- No network tools needed - scripts handle API calls
- Scoped Bash prevents arbitrary command execution
- File access limited to plugin directory context

## Directory Structure

```
skills/optimizing-staking-rewards/
├── PRD.md                          # Product requirements
├── ARD.md                          # This document
├── SKILL.md                        # Core instructions
├── scripts/
│   ├── staking_optimizer.py        # Main CLI entry point
│   ├── staking_fetcher.py          # API data fetching
│   ├── metrics_calculator.py       # Yield and cost calculations
│   ├── risk_assessor.py            # Protocol risk scoring
│   ├── optimizer_engine.py         # Allocation optimization
│   └── formatters.py               # Output formatting
├── references/
│   ├── errors.md                   # Error handling guide
│   ├── examples.md                 # Usage examples
│   └── implementation.md           # Implementation details
└── config/
    └── settings.yaml               # Configuration options
```

## API Integration Architecture

### DeFiLlama Pools API

```python
# Endpoint: https://yields.llama.fi/pools
# Filter for staking pools

def fetch_staking_pools():
    response = requests.get("https://yields.llama.fi/pools")
    pools = response.json()["data"]

    # Filter for staking-related pools
    staking_keywords = ["staking", "liquid staking", "lsd", "stake"]
    staking_pools = [
        p for p in pools
        if any(kw in p.get("project", "").lower() or
               kw in p.get("symbol", "").lower()
               for kw in staking_keywords)
        or p.get("project") in KNOWN_STAKING_PROTOCOLS
    ]

    return staking_pools
```

### Known Staking Protocols (DeFiLlama)

| Protocol | Project Key | Assets |
|----------|-------------|--------|
| Lido | lido | stETH, stSOL, stMATIC |
| Rocket Pool | rocket-pool | rETH |
| Frax | frax-ether | sfrxETH |
| Marinade | marinade-finance | mSOL |
| Ankr | ankr | ankrETH |
| Coinbase | coinbase-wrapped-staked-eth | cbETH |
| Benqi | benqi-staked-avax | sAVAX |

### StakingRewards API (Alternative Source)

```python
# For native staking rates
# https://www.stakingrewards.com/api/

NATIVE_STAKING = {
    "ethereum": {"apr": 4.0, "unbonding": "variable"},
    "cosmos": {"apr": 19.0, "unbonding": "21 days"},
    "polkadot": {"apr": 15.0, "unbonding": "28 days"},
    "solana": {"apr": 7.0, "unbonding": "~2 days"},
    "avalanche": {"apr": 8.0, "unbonding": "2 weeks"},
    "near": {"apr": 9.5, "unbonding": "36-48 hours"},
}
```

## Data Flow Architecture

### Input Processing

```
User Request: "Compare staking for 10 ETH"
                    │
                    ▼
            ┌───────────────┐
            │ Parse Request │
            └───────────────┘
                    │
    ┌───────────────┼───────────────┐
    ▼               ▼               ▼
┌────────┐    ┌──────────┐    ┌─────────┐
│ Asset  │    │ Amount   │    │ Options │
│ "ETH"  │    │ 10       │    │ {}      │
└────────┘    └──────────┘    └─────────┘
```

### Data Aggregation

```python
def aggregate_staking_data(asset: str) -> List[StakingOption]:
    """
    Aggregate staking options from multiple sources.
    """
    options = []

    # 1. Liquid staking from DeFiLlama
    liquid_pools = fetch_defillama_pools(asset)
    for pool in liquid_pools:
        options.append(StakingOption(
            protocol=pool["project"],
            type="liquid",
            apy=pool["apy"],
            tvl=pool["tvlUsd"],
            source="defillama"
        ))

    # 2. Native staking rates
    if asset.upper() in NATIVE_STAKING:
        native = NATIVE_STAKING[asset.upper()]
        options.append(StakingOption(
            protocol=f"{asset} Native Staking",
            type="native",
            apy=native["apr"],
            unbonding=native["unbonding"],
            source="native"
        ))

    # 3. Sort by APY descending
    options.sort(key=lambda x: x.apy, reverse=True)

    return options
```

### Metrics Calculation

```python
@dataclass
class StakingMetrics:
    gross_apy: float          # Advertised APY
    protocol_fee: float       # Protocol's cut
    net_apy: float            # After protocol fees
    gas_cost_usd: float       # Estimated staking gas
    effective_apy: float      # Net APY minus gas amortized

    risk_score: int           # 1-10 (10 = safest)
    tvl_usd: float            # Total value locked
    unbonding_days: int       # Lock-up period

    projected_1y: float       # Value after 1 year

def calculate_metrics(option, amount_usd, gas_price_gwei=30):
    """Calculate comprehensive metrics for a staking option."""

    # Protocol fees (varies by protocol)
    PROTOCOL_FEES = {
        "lido": 0.10,        # 10% of rewards
        "rocket-pool": 0.14, # 14% of rewards
        "frax-ether": 0.10,  # 10% of rewards
        "native": 0.0,       # No protocol fee
    }

    fee_rate = PROTOCOL_FEES.get(option.protocol_key, 0.10)
    net_apy = option.apy * (1 - fee_rate)

    # Gas cost for staking transaction (~100k gas for liquid staking)
    gas_cost_eth = (100_000 * gas_price_gwei) / 1e9
    gas_cost_usd = gas_cost_eth * get_eth_price()

    # Effective APY accounting for gas (amortized over 1 year)
    if amount_usd > 0:
        gas_drag = (gas_cost_usd / amount_usd) * 100
        effective_apy = net_apy - gas_drag
    else:
        effective_apy = net_apy

    return StakingMetrics(
        gross_apy=option.apy,
        protocol_fee=fee_rate,
        net_apy=net_apy,
        gas_cost_usd=gas_cost_usd,
        effective_apy=max(0, effective_apy),
        risk_score=calculate_risk_score(option),
        tvl_usd=option.tvl,
        unbonding_days=option.unbonding_days,
        projected_1y=amount_usd * (1 + net_apy / 100)
    )
```

### Risk Scoring

```python
def calculate_risk_score(option) -> int:
    """
    Calculate risk score from 1-10 (10 = safest).

    Factors:
    - Audit status (30%)
    - Time in production (25%)
    - TVL size (20%)
    - Protocol reputation (15%)
    - Validator diversity (10%)
    """

    score = 10.0

    # Audit status
    if not option.audited:
        score -= 3.0
    elif option.audit_age_months > 12:
        score -= 1.0

    # Time in production
    if option.age_months < 3:
        score -= 3.0
    elif option.age_months < 12:
        score -= 1.5

    # TVL size (larger = safer)
    if option.tvl_usd < 10_000_000:
        score -= 2.0
    elif option.tvl_usd < 100_000_000:
        score -= 1.0

    # Protocol reputation
    REPUTABLE_PROTOCOLS = {"lido", "rocket-pool", "coinbase", "frax-ether"}
    if option.protocol_key in REPUTABLE_PROTOCOLS:
        score += 0.5

    # Validator diversity (for liquid staking)
    if option.validator_count and option.validator_count < 10:
        score -= 1.0

    return max(1, min(10, round(score)))
```

## Error Handling Strategy

### Error Categories

| Category | Examples | Recovery Strategy |
|----------|----------|-------------------|
| API Errors | Timeout, rate limit | Retry with backoff, use cache |
| Data Errors | Invalid APY, missing fields | Skip record, log warning |
| User Input | Invalid asset, bad format | Clear error message |
| Calculation | Division by zero, overflow | Return safe default |

### Implementation

```python
class StakingError(Exception):
    """Base exception for staking optimizer."""
    pass

class DataFetchError(StakingError):
    """Failed to fetch data from source."""
    pass

class InvalidAssetError(StakingError):
    """Asset not supported."""
    pass

def safe_fetch_with_retry(url, max_retries=3, timeout=15):
    """Fetch with exponential backoff."""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            if attempt == max_retries - 1:
                raise DataFetchError(f"Failed after {max_retries} attempts: {e}")
            time.sleep(2 ** attempt)  # 1, 2, 4 seconds
```

## Composability & Stacking

### Works With

- **market-price-tracker**: Get current asset prices for USD calculations
- **gas-fee-optimizer**: Optimize staking transaction timing
- **crypto-portfolio-tracker**: Track staking positions over time
- **defi-yield-optimizer**: Compare staking vs other DeFi yields

### Integration Pattern

```python
# Example: Combined staking + yield analysis
def comprehensive_yield_analysis(asset, amount):
    # Get staking options
    staking = staking_optimizer.analyze(asset, amount)

    # Get LP/farming options (from yield optimizer)
    farming = yield_optimizer.analyze(asset, amount)

    # Combine and rank
    all_options = staking + farming
    all_options.sort(key=lambda x: x.risk_adjusted_return, reverse=True)

    return all_options
```

## Performance Considerations

### Caching Strategy

```python
CACHE_TTL = {
    "staking_pools": 300,      # 5 minutes (APYs change slowly)
    "prices": 60,              # 1 minute (prices change fast)
    "gas_prices": 30,          # 30 seconds (gas is volatile)
    "protocol_metadata": 3600, # 1 hour (rarely changes)
}

@lru_cache(maxsize=100)
def get_cached_pools(cache_key: str) -> List[dict]:
    """Memory-cached pool data."""
    pass
```

### Rate Limiting

| Source | Limit | Strategy |
|--------|-------|----------|
| DeFiLlama | ~100/min | Batch requests, cache aggressively |
| CoinGecko | 30/min | Cache prices for 1 minute |
| StakingRewards | Varies | Use fallback static data |

## Testing Strategy

### Unit Tests

```python
def test_apy_conversion():
    """Test APR to APY conversion."""
    assert apr_to_apy(10, 365) == pytest.approx(10.52, rel=0.01)
    assert apy_to_apr(10.52, 365) == pytest.approx(10, rel=0.01)

def test_risk_score_boundaries():
    """Risk score should be 1-10."""
    for option in MOCK_OPTIONS:
        score = calculate_risk_score(option)
        assert 1 <= score <= 10

def test_metrics_calculation():
    """Test comprehensive metrics calculation."""
    metrics = calculate_metrics(MOCK_LIDO_OPTION, 10000)
    assert metrics.net_apy < metrics.gross_apy  # Fees reduce yield
    assert metrics.effective_apy <= metrics.net_apy  # Gas reduces further
```

### Integration Tests

```python
def test_defillama_integration():
    """Test real DeFiLlama API."""
    pools = fetch_defillama_pools("ETH")
    assert len(pools) > 0
    assert all("apy" in p for p in pools)

def test_end_to_end():
    """Test full analysis flow."""
    result = analyze_staking("ETH", amount=10)
    assert "recommendations" in result
    assert len(result["options"]) > 0
```

## Security Considerations

### Data Validation

- Validate APY ranges (0-1000%)
- Sanitize protocol names
- Verify TVL is positive

### No Private Data

- No wallet connections
- No private key handling
- No transaction signing

### Output Safety

- Escape special characters in output
- Validate file paths for writing
- No arbitrary code execution
