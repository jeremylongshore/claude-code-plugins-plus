# Usage Examples

## Basic Pool Analysis

### Analyze Pool by Address

```bash
python pool_analyzer.py --pool 0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640

# Output:
# ==============================================================================
#   LIQUIDITY POOL ANALYZER                              2025-01-14 15:30 UTC
# ==============================================================================
#
#   POOL: USDC-WETH (uniswap-v3 - 0.05%)
# ------------------------------------------------------------------------------
#   Chain:          Ethereum
#   TVL:            $500.00M
#   24h Volume:     $125.00M
#   Fee Tier:       0.05%
#
#   FEE METRICS
# ------------------------------------------------------------------------------
#   24h Fees:       $62,500.00
#   Fee APR:        4.56%
#   Volume/TVL:     0.2500
```

### Search by Token Pair

```bash
python pool_analyzer.py --pair ETH/USDC --protocol uniswap-v3

# Shows all ETH/USDC pools on Uniswap V3
```

### Filter by Chain

```bash
python pool_analyzer.py --pair ETH/USDC --chain arbitrum

# Shows ETH/USDC pools on Arbitrum only
```

## Impermanent Loss Calculation

### Calculate IL for Price Change

```bash
python pool_analyzer.py --il-calc --entry-price 2000 --current-price 3000

# Output:
# ==============================================================================
#   IMPERMANENT LOSS CALCULATION                        2025-01-14 15:30 UTC
# ==============================================================================
#
# ------------------------------------------------------------------------------
#   Entry Price:    $2,000.00
#   Current Price:  $3,000.00
#   Price Change:   +50.0%
#
#   IL (%):         2.02%
# ==============================================================================
```

### IL with Position Value

```bash
python pool_analyzer.py --il-calc --entry-price 2000 --current-price 3000 --position 10000

# Output includes:
#   IL (USD):       $202.00
#   Value if HODL:  $12,500.00
#   Value in LP:    $12,247.45
```

### IL Scenarios Table

```bash
python pool_analyzer.py --il-scenarios

# Output:
# ==============================================================================
#   IMPERMANENT LOSS SCENARIOS
# ==============================================================================
#
# ------------------------------------------------------------------------------
#     Price Change     Price Ratio              IL
# ------------------------------------------------------------------------------
#            -90%           0.10x         42.54%
#            -75%           0.25x         20.00%
#            -50%           0.50x          5.72%
#            -25%           0.75x          1.03%
#              0%           1.00x          0.00%
#            +25%           1.25x          0.62%
#            +50%           1.50x          2.02%
#           +100%           2.00x          5.72%
#           +200%           3.00x         13.40%
#           +400%           5.00x         25.46%
# ------------------------------------------------------------------------------
# ==============================================================================
```

## Pool Comparison

### Compare Pools Across Protocols

```bash
python pool_analyzer.py --compare --pair ETH/USDC --protocols uniswap-v3,curve,balancer

# Output:
# ==============================================================================
#   POOL COMPARISON
# ------------------------------------------------------------------------------
#   Protocol        Pair            Chain        TVL     Fee APR
# ------------------------------------------------------------------------------
#   uniswap-v3      USDC-WETH       Ethereum     $500M      4.56%
#   curve           USDC-ETH        Ethereum      $50M      3.21%
#   balancer        WETH-USDC       Ethereum      $25M      2.89%
# ------------------------------------------------------------------------------
#   Total: 3 pools
# ==============================================================================
```

### Compare Fee Tiers

```bash
python pool_analyzer.py --pair ETH/USDC --protocol uniswap-v3 --fee-tiers 0.01,0.05,0.30

# Shows pools at different fee tiers for comparison
```

## Position Analysis

### Project Returns for Position

```bash
python pool_analyzer.py --pool 0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640 --position 10000

# Adds position metrics:
#   Position Share: 0.0020%
#   Daily Fees:     $1.25
#   Weekly Fees:    $8.75
#   Monthly Fees:   $37.50
#   Annual Fees:    $456.25
```

## Filtering Options

### Filter by Minimum TVL

```bash
python pool_analyzer.py --protocol uniswap-v3 --min-tvl 10000000

# Shows only pools with TVL >= $10M
```

### Limit Results

```bash
python pool_analyzer.py --protocol uniswap-v3 --top 5

# Shows only top 5 pools
```

## Output Formats

### JSON Output

```bash
python pool_analyzer.py --pool 0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640 --format json

# Output:
# {
#   "timestamp": "2025-01-14 15:30 UTC",
#   "data": [
#     {
#       "pool": "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640",
#       "project": "uniswap-v3",
#       "chain": "Ethereum",
#       "symbol": "USDC-WETH",
#       "metrics": {
#         "tvl": 500000000,
#         "volume_24h": 125000000,
#         "fee_apr": 4.56,
#         "health_score": 90
#       }
#     }
#   ]
# }
```

### CSV Output

```bash
python pool_analyzer.py --protocol uniswap-v3 --top 10 --format csv --output pools.csv

# Creates CSV file with headers:
# Protocol,Symbol,Chain,Pool Address,TVL (USD),Volume 24h,Fee Tier (%),Fee APR (%),Volume/TVL,Health Score
```

### Save to File

```bash
python pool_analyzer.py --pool 0x88e6... --format json --output analysis.json
python pool_analyzer.py --pair ETH/USDC --format csv --output comparison.csv
```

## Verbose Mode

### Debug Output

```bash
python pool_analyzer.py --pair ETH/USDC --verbose

# Shows:
# Fetching pool data...
# Querying Uniswap V3 subgraph...
# Falling back to DeFiLlama...
# Found 15 pools for ETH/USDC
# Calculated metrics for USDC-WETH
# ...
```

## Real-World Workflows

### Find Best Pool for LP Position

```bash
# 1. Search pools for your pair
python pool_analyzer.py --pair ETH/USDC --protocol uniswap-v3 --min-tvl 1000000

# 2. Analyze specific pool
python pool_analyzer.py --pool 0x88e6... --detailed

# 3. Calculate IL risk at target price
python pool_analyzer.py --il-calc --entry-price 2000 --current-price 2500 --position 10000
```

### Monitor Position Profitability

```bash
# Check current pool metrics
python pool_analyzer.py --pool 0x88e6... --position 10000

# Calculate IL if price drops 20%
python pool_analyzer.py --il-calc --entry-price 2000 --current-price 1600 --position 10000
```

### Research DeFi Yields

```bash
# Compare pools across protocols
python pool_analyzer.py --pair ETH/USDC --compare --protocols uniswap-v3,curve,balancer --format csv --output research.csv

# View IL scenarios
python pool_analyzer.py --il-scenarios --format json --output il_table.json
```

## Integration Examples

### Pipe to jq

```bash
python pool_analyzer.py --protocol uniswap-v3 --top 5 --format json | jq '.data[].metrics.fee_apr'
```

### Use in Shell Scripts

```bash
#!/bin/bash
# Get top APR pool
BEST_POOL=$(python pool_analyzer.py --pair ETH/USDC --format json | jq -r '.data[0].pool')
echo "Best pool: $BEST_POOL"
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
