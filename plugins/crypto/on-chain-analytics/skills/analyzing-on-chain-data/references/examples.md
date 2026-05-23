# Usage Examples

## Protocol Rankings

### Top Protocols by TVL

```bash
python onchain_analytics.py protocols
```

### Filter by Category

```bash
python onchain_analytics.py protocols --category lending
python onchain_analytics.py protocols --category "liquid staking"
python onchain_analytics.py protocols --category dex
```

### Filter by Chain

```bash
python onchain_analytics.py protocols --chain ethereum
python onchain_analytics.py protocols --chain arbitrum
```

### Sort by Different Metrics

```bash
python onchain_analytics.py protocols --sort tvl
python onchain_analytics.py protocols --sort market_share
python onchain_analytics.py protocols --sort tvl_to_mcap
```

## Chain Analysis

### Chain TVL Rankings

```bash
python onchain_analytics.py chains
```

## Fees and Revenue

### All Protocol Fees

```bash
python onchain_analytics.py fees
```

### Specific Protocol

```bash
python onchain_analytics.py fees --protocol aave
python onchain_analytics.py fees --protocol uniswap
```

## DEX Analysis

### DEX Volumes

```bash
python onchain_analytics.py dex
```

### DEX by Chain

```bash
python onchain_analytics.py dex --chain ethereum
python onchain_analytics.py dex --chain arbitrum
```

## Category Analysis

### Category Breakdown

```bash
python onchain_analytics.py categories
```

## Trending

### Trending Protocols

```bash
python onchain_analytics.py trends
```

### Custom Threshold

```bash
python onchain_analytics.py trends --threshold 5
python onchain_analytics.py trends --threshold 20
```

## Yield Analysis

### Top Yields

```bash
python onchain_analytics.py yields
```

### Filter by Chain

```bash
python onchain_analytics.py yields --chain ethereum
```

### Filter by Minimum TVL

```bash
python onchain_analytics.py yields --min-tvl 1000000
python onchain_analytics.py yields --min-tvl 10000000 --limit 50
```

## Stablecoins

### Stablecoin Market Caps

```bash
python onchain_analytics.py stables
```

## Output Formats

### JSON Output

```bash
python onchain_analytics.py protocols --format json
python onchain_analytics.py chains --format json > chains.json
```

### CSV Output

```bash
python onchain_analytics.py protocols --format csv > protocols.csv
python onchain_analytics.py fees --format csv > fees.csv
```

## Programmatic Usage

```python
from data_fetcher import DataFetcher
from metrics_calculator import MetricsCalculator

fetcher = DataFetcher()
calc = MetricsCalculator()

# Get top protocols
protocols = fetcher.fetch_protocols(limit=100)

# Calculate metrics
data = [vars(p) for p in protocols]
data = calc.calculate_market_share(data)
data = calc.calculate_tvl_to_mcap(data)

# Print top 10
for p in data[:10]:
    print(f"{p['name']}: ${p['tvl']/1e9:.2f}B ({p['market_share']:.1f}%)")
```

## Common Workflows

### Daily DeFi Overview

```bash
python onchain_analytics.py protocols --limit 20
python onchain_analytics.py chains
python onchain_analytics.py trends
```

### Research Protocol

```bash
python onchain_analytics.py protocols --category lending
python onchain_analytics.py fees --protocol aave
```

### Find Yield Opportunities

```bash
python onchain_analytics.py yields --min-tvl 5000000 --chain ethereum
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
