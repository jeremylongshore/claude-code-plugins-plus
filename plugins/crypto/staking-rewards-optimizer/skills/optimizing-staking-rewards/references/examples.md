# Usage Examples

## Basic Staking Comparison

### Compare ETH Staking Options

```bash
python staking_optimizer.py --asset ETH

# Output:
# ==============================================================================
#   STAKING REWARDS OPTIMIZER                              2025-01-15 15:30 UTC
# ==============================================================================
#
#   STAKING OPTIONS FOR ETH
# ------------------------------------------------------------------------------
#   Protocol             Type       Net APY   Risk          TVL
# ------------------------------------------------------------------------------
#   frax-ether           liquid       4.59%   7/10        $450M
#   lido (stETH)         liquid       3.60%   9/10         $15B
#   rocket-pool (rETH)   liquid       3.61%   8/10          $3B
#   coinbase (cbETH)     liquid       3.42%   9/10          $2B
#   ETH Native           native       4.00%  10/10         $50B
# ------------------------------------------------------------------------------
#   Total: 5 options | Ranked by risk-adjusted return
# ==============================================================================
```

### Compare SOL Staking Options

```bash
python staking_optimizer.py --asset SOL

# Shows Marinade, native SOL staking, and other liquid options
```

### Compare Multiple Assets

```bash
python staking_optimizer.py --assets ETH,SOL,ATOM

# Shows staking options for all three assets
```

## Position Analysis

### Analyze with Position Size

```bash
python staking_optimizer.py --asset ETH --amount 10

# Calculates gas-adjusted effective APY for 10 ETH position
# Shows projected returns accounting for gas costs
```

### Analyze with USD Value

```bash
python staking_optimizer.py --asset ETH --amount-usd 25000

# Analyzes for a $25,000 position
```

### Detailed Single Protocol Analysis

```bash
python staking_optimizer.py --protocol lido --detailed

# Output:
# ==============================================================================
#   PROTOCOL: Lido (stETH)
# ------------------------------------------------------------------------------
#   Chain:          Ethereum
#   Type:           Liquid
#
#   YIELD METRICS
# ------------------------------------------------------------------------------
#   Gross APY:      4.00%
#   Protocol Fee:   10.0%
#   Net APY:        3.60%
#
#   RISK ASSESSMENT
# ------------------------------------------------------------------------------
#   Overall Score:  9/10 (Low Risk)
#
#   Score Breakdown:
#     Audit Status:       10/10
#     Time in Production: 10/10
#     TVL Size:           10/10
#     Reputation:         10/10
#     Validator Diversity: 8/10
#
#   Positive Factors:
#     + Multiple audits, latest 6 months ago
#     + 3+ years in production
#     + Has slashing insurance or protocol backing
#     + Diversified across 30+ validators
#
#   Considerations:
#     - Largest LSD by market share - potential centralization concerns
#     - stETH occasionally trades at slight discount to ETH
#     - 10% fee on staking rewards
# ==============================================================================
```

## Portfolio Optimization

### Optimize Existing Portfolio

```bash
python staking_optimizer.py --optimize \
  --positions "10 ETH @ lido 4.0%, 100 ATOM @ native 18%, 50 DOT @ native 14%"

# Output:
# ==============================================================================
#   PORTFOLIO OPTIMIZATION                              2025-01-15 15:30 UTC
# ==============================================================================
#
#   CURRENT PORTFOLIO
# ------------------------------------------------------------------------------
#   Position                  APY      Annual Return
#   10 ETH @ lido           3.60%           $720.00
#   100 ATOM @ native      18.00%         $3,600.00
#   50 DOT @ native        14.00%         $1,400.00
# ------------------------------------------------------------------------------
#   Total: $25,000            22.88%         $5,720.00
#
#   OPTIMIZED ALLOCATION
# ------------------------------------------------------------------------------
#   Recommendation            APY       Annual       Change
#   10 ETH → frax-ether     4.59%      $918.00     +$198.00
#   100 ATOM → Keep        18.00%    $3,600.00          $0
#   50 DOT → Keep          14.00%    $1,400.00          $0
# ------------------------------------------------------------------------------
#   Optimized Annual: $5,918.00      Improvement: +$198.00 (+3.5%)
#
#   IMPLEMENTATION
#   1. Move 10 ETH from lido to frax-ether
# ==============================================================================
```

### Optimize with Constraints

```bash
# Only consider protocols with risk score >= 8
python staking_optimizer.py --optimize \
  --positions "50 ETH @ lido 3.6%" \
  --min-risk 8
```

## Protocol Comparison

### Compare Specific Protocols

```bash
python staking_optimizer.py --compare --protocols lido,rocket-pool,frax-ether

# Head-to-head comparison table
```

### Protocol Deep Dive

```bash
python staking_optimizer.py --protocol rocket-pool --detailed

# Shows full risk assessment, validator metrics, and considerations
```

## Output Formats

### JSON Output

```bash
python staking_optimizer.py --asset ETH --format json

# Output:
# {
#   "timestamp": "2025-01-15 15:30 UTC",
#   "data": [
#     {
#       "project": "lido",
#       "symbol": "stETH",
#       "chain": "Ethereum",
#       "staking_type": "liquid",
#       "metrics": {
#         "gross_apy": 4.0,
#         "net_apy": 3.6,
#         "protocol_fee_rate": 0.1,
#         "tvl_usd": 15000000000
#       },
#       "risk_assessment": {
#         "overall_score": 9,
#         "risk_level": "low"
#       }
#     }
#   ]
# }
```

### CSV Output

```bash
python staking_optimizer.py --asset ETH --format csv --output eth_staking.csv

# Creates CSV file:
# Protocol,Symbol,Chain,Type,Gross APY,Net APY,Protocol Fee,TVL (USD),Risk Score,Risk Level,Unbonding
# lido,stETH,Ethereum,liquid,4.0,3.6,0.1,15000000000,9,low,instant
```

### Save to File

```bash
python staking_optimizer.py --asset ETH --format json --output analysis.json
python staking_optimizer.py --asset SOL --format csv --output sol_staking.csv
```

## Advanced Usage

### Custom Gas Price

```bash
python staking_optimizer.py --asset ETH --amount 10 --gas-price 50

# Calculates with 50 gwei gas price instead of default 30
```

### Custom ETH Price

```bash
python staking_optimizer.py --asset ETH --amount 10 --eth-price 3000

# Uses $3000 ETH price for USD calculations
```

### Bypass Cache

```bash
python staking_optimizer.py --asset ETH --no-cache

# Forces fresh API fetch, ignores cached data
```

### Verbose Mode

```bash
python staking_optimizer.py --asset ETH --verbose

# Shows:
# Fetching staking data...
# Found 15 staking pools for ETH
# Calculating metrics for lido...
# ...
```

## Real-World Workflows

### Research Best Staking Option

```bash
# 1. Quick overview of all options
python staking_optimizer.py --asset ETH

# 2. Detailed analysis of top picks
python staking_optimizer.py --protocol lido --detailed
python staking_optimizer.py --protocol rocket-pool --detailed

# 3. Calculate for your position size
python staking_optimizer.py --asset ETH --amount 32 --detailed
```

### Monthly Portfolio Review

```bash
# Export current state for tracking
python staking_optimizer.py --assets ETH,SOL,ATOM --format csv --output $(date +%Y%m)_staking.csv

# Check for optimization opportunities
python staking_optimizer.py --optimize \
  --positions "32 ETH @ lido 3.6%, 500 SOL @ marinade 7.5%, 1000 ATOM @ native 18%"
```

### Compare Liquid vs Native Staking

```bash
# Get both options for comparison
python staking_optimizer.py --asset ETH --detailed

# Look at:
# - Net APY (liquid has protocol fee, native doesn't)
# - Risk score (native = 10/10, liquid varies)
# - Unbonding (liquid = instant, native = variable)
```

## Integration Examples

### Pipe to jq

```bash
python staking_optimizer.py --asset ETH --format json | jq '.data[].metrics.net_apy'
```

### Use in Shell Scripts

```bash
#!/bin/bash
# Get best APY for ETH
BEST=$(python staking_optimizer.py --asset ETH --format json | \
  jq -r '.data | sort_by(-.metrics.net_apy) | .[0].project')
echo "Best ETH staking: $BEST"
```

### Scheduled Analysis

```bash
# Add to crontab for daily report
0 9 * * * python /path/to/staking_optimizer.py --assets ETH,SOL,ATOM --format json --output /reports/staking_$(date +\%Y\%m\%d).json
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
