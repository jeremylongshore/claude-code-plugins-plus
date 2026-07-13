# Implementation Guide

## Architecture Overview

The DeFi Yield Optimizer follows a data aggregation pipeline pattern:

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────────┐
│  DeFiLlama  │───▶│   Normalize  │───▶│ Risk Scorer │───▶│   Formatter  │
│   + APIs    │    │  (Calculate) │    │  (Assess)   │    │   (Output)   │
└─────────────┘    └──────────────┘    └─────────────┘    └──────────────┘
```

## Component Responsibilities

### 1. Protocol Fetcher (`protocol_fetcher.py`)

**Purpose**: Aggregate yield data from DeFiLlama API.

**Key Methods**:

- `fetch_yields()` - Get all pool data
- `fetch_protocol_info()` - Get protocol details
- `_load_cache()` / `_save_cache()` - Cache management

**API Integration**:

```python
DEFILLAMA_YIELDS_URL = "https://yields.llama.fi/pools"
# Returns ~10,000+ pools across all chains
```

**Caching Strategy**:

- File cache at `~/.defi_yield_cache.json`
- TTL: 5 minutes for yield data
- Stale fallback on API failure
- Mock data fallback when requests unavailable

### 2. Yield Calculator (`yield_calculator.py`)

**Purpose**: Normalize and calculate yield metrics.

**Key Methods**:

- `calculate()` - Add calculated fields to pool
- `apr_to_apy()` / `apy_to_apr()` - Rate conversion
- `calculate_earnings()` - Project returns
- `calculate_il()` - Impermanent loss estimation

**APY Calculation**:

```python
# APR to APY (daily compounding)
APY = (1 + APR/365)^365 - 1

# Total yield
total_apy = base_apy + reward_apy
```

**Impermanent Loss Formula**:

```python
IL = 2 * sqrt(price_ratio) / (1 + price_ratio) - 1
```

### 3. Risk Assessor (`risk_assessor.py`)

**Purpose**: Score protocol and pool risks.

**Risk Factors**:

| Factor | Weight | Source |
|--------|--------|--------|
| Audit Status | 30% | Internal database |
| TVL | 20% | DeFiLlama API |
| Protocol Age | 20% | Internal database |
| TVL Trend | 15% | DeFiLlama API |
| Concentration | 15% | Estimated |

**Scoring Logic**:

```python
score = sum(factor_score * weight for all factors)
# Score 8-10: Low risk
# Score 5-7.9: Medium risk
# Score 3-4.9: High risk
# Score 0-2.9: Very High risk
```

### 4. Formatters (`formatters.py`)

**Purpose**: Format output for display.

**Supported Formats**:

- `table` - ASCII table for terminal
- `json` - Structured data for analysis
- `csv` - Spreadsheet-compatible

**Table Columns**:

```
Protocol | Pool | Chain | TVL | APY | Risk | Score
```

## Data Flow

### Input Processing

```
User Args → argparse → Filter Config
```

### API Fetch

```
Filter Config → ProtocolFetcher → Raw Pool Data
                      ↓
                  Cache Layer
```

### Data Enhancement

```
Raw Pool Data → YieldCalculator → Calculated Fields
                     ↓
             → RiskAssessor → Risk Scores
```

### Output Generation

```
Enhanced Data → Filter/Sort → Top N → Formatter → Output
```

## CLI Arguments Mapping

| Argument | Processing Step |
|----------|-----------------|
| `--chain` | Filter `pool["chain"]` |
| `--protocol` | Filter `pool["project"]` |
| `--asset` | Filter `pool["symbol"]` |
| `--min-tvl` | Filter `pool["tvlUsd"]` |
| `--min-apy` | Filter `pool["apy"]` |
| `--risk` | Filter `pool["risk_score"]` |
| `--audited-only` | Filter `pool["audited"]` |
| `--sort` | Sort key selection |
| `--top` | Limit results |
| `--format` | Output formatter |

## Adding New Features

### Adding a New Risk Factor

1. Add weight to `WEIGHTS` dict in `risk_assessor.py`
2. Create `_score_[factor]()` method
3. Include in `assess()` calculation
4. Update `_identify_risk_factors()` for warnings

### Adding a New Data Source

1. Add API endpoint to `settings.yaml`
2. Create fetch method in `protocol_fetcher.py`
3. Implement caching with appropriate TTL
4. Add fallback for API failures

### Adding a New Output Format

1. Add format to `output.formats` in `settings.yaml`
2. Create `_format_[type]()` method in `formatters.py`
3. Add to format selection in `format()` method

## Testing

### Unit Tests

```python
# Test yield calculations
calc = YieldCalculator()
assert calc.apr_to_apy(10) == pytest.approx(10.52, 0.01)

# Test risk scoring
assessor = RiskAssessor()
pool = {"project": "aave-v3", "tvlUsd": 1e9}
assessor.assess(pool)
assert pool["risk_score"] >= 8.0
```

### Integration Tests

```bash
# Test API connectivity
python protocol_fetcher.py

# Test full pipeline
python yield_optimizer.py --top 5 --verbose

# Test output formats
python yield_optimizer.py --format json
python yield_optimizer.py --format csv
```

## Performance Considerations

| Operation | Target Time | Optimization |
|-----------|-------------|--------------|
| API fetch | < 5s | Cache layer |
| Calculate | < 100ms | In-memory |
| Risk score | < 100ms | Lookup tables |
| Format | < 50ms | Pre-computed |
| Total | < 10s | Parallel ops |

## Error Handling Strategy

```python
try:
    pools = fetcher.fetch_yields()
except RequestException:
    # Try cache
    pools = fetcher._load_cache("yields", ignore_ttl=True)
    if not pools:
        # Use mock data
        pools = fetcher._get_mock_data()
```

## Security Notes

- No wallet connections
- No private key handling
- No transaction signing
- Read-only API access
- Cache contains public data only

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
