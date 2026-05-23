# Usage Examples

## Basic Usage

### Find Top Yields Across All Chains

```bash
python yield_optimizer.py --top 20
```

Shows the 20 highest APY opportunities across all protocols and chains.

### Find Top Yields on Ethereum

```bash
python yield_optimizer.py --chain ethereum --top 10
```

Shows the 10 highest APY opportunities on Ethereum mainnet.

### Find Multi-Chain Opportunities

```bash
python yield_optimizer.py --chain ethereum,arbitrum,polygon --top 15
```

Compares yields across Ethereum, Arbitrum, and Polygon.

## Filtering by Asset

### Stablecoin Yields

```bash
python yield_optimizer.py --asset USDC --min-tvl 10000000
```

Shows USDC yield opportunities with at least $10M TVL.

### Multiple Stablecoins

```bash
python yield_optimizer.py --asset USDC,USDT,DAI --min-tvl 5000000
```

Shows yield opportunities for major stablecoins.

### ETH Yields

```bash
python yield_optimizer.py --asset ETH,WETH,stETH --chain ethereum
```

Shows ETH and liquid staking yield opportunities.

## Protocol-Specific Searches

### Compare Lending Protocols

```bash
python yield_optimizer.py --protocol aave-v3,compound-v3,spark --asset USDC
```

Compares USDC yields across major lending protocols.

### Curve/Convex Yields

```bash
python yield_optimizer.py --protocol curve-dex,convex-finance --top 10
```

Shows top yields from Curve and Convex ecosystems.

### Liquid Staking

```bash
python yield_optimizer.py --protocol lido,rocket-pool,frax-ether
```

Compares liquid staking options.

## Risk-Based Filtering

### Low-Risk Only

```bash
python yield_optimizer.py --risk low --min-apy 3
```

Shows only low-risk opportunities with at least 3% APY.

### Audited Protocols Only

```bash
python yield_optimizer.py --audited-only --min-tvl 50000000
```

Shows only yields from audited protocols with $50M+ TVL.

### Conservative Search

```bash
python yield_optimizer.py --risk low --audited-only --min-tvl 100000000 --min-apy 2
```

Most conservative search: audited, low-risk, high TVL, decent APY.

### Higher Risk for Higher Yield

```bash
python yield_optimizer.py --risk medium --min-apy 10 --max-apy 50
```

Medium-risk opportunities with 10-50% APY (filters outliers).

## Detailed Analysis

### Top Results with Breakdown

```bash
python yield_optimizer.py --top 5 --detailed
```

Shows top 5 with detailed APY breakdown for the highest yielding pool.

### Analyze Specific Pool

```bash
python yield_optimizer.py --pool "aave-v3-usdc-ethereum" --detailed
```

Shows full analysis for a specific pool.

### Compare Protocols Head-to-Head

```bash
python yield_optimizer.py --compare aave-v3,compound-v3,spark --asset USDC --chain ethereum
```

Side-by-side comparison of protocols for USDC on Ethereum.

## Export Options

### Export to JSON

```bash
python yield_optimizer.py --top 100 --format json --output all_yields.json
```

Exports top 100 yields to JSON for further analysis.

### Export to CSV

```bash
python yield_optimizer.py --chain ethereum --format csv --output eth_yields.csv
```

Exports Ethereum yields to CSV for spreadsheet analysis.

### Export Low-Risk Opportunities

```bash
python yield_optimizer.py --risk low --audited-only --format json --output safe_yields.json
```

Exports conservative opportunities to JSON.

## Sorting Options

### Sort by TVL (Safest First)

```bash
python yield_optimizer.py --sort tvl --top 20
```

Shows highest TVL protocols first (generally safest).

### Sort by Risk Score

```bash
python yield_optimizer.py --sort risk --top 20
```

Shows lowest risk protocols first.

### Sort by Protocol Name

```bash
python yield_optimizer.py --sort name --chain ethereum
```

Alphabetical listing for easy reference.

## Advanced Combinations

### DAO Treasury Strategy

```bash
python yield_optimizer.py --risk low --audited-only --min-tvl 500000000 --asset USDC,DAI --top 5
```

Ultra-conservative options suitable for DAO treasuries.

### Yield Farming Scout

```bash
python yield_optimizer.py --min-apy 15 --max-apy 100 --min-tvl 1000000 --top 20 --detailed
```

Higher yield opportunities with reasonable TVL (not dust pools).

### Arbitrum DeFi Yields

```bash
python yield_optimizer.py --chain arbitrum --min-tvl 5000000 --top 10 --format json --output arb_yields.json
```

L2 yield opportunities with export.

### Stablecoin Comparison Across L2s

```bash
python yield_optimizer.py --asset USDC --chain arbitrum,optimism,polygon --protocol aave-v3 --format csv
```

Compare Aave USDC yields across L2 networks.

## Workflow Examples

### Daily Yield Check

```bash
# Quick morning check of top opportunities
python yield_optimizer.py --top 10 --min-tvl 10000000

# Detailed analysis of anything interesting
python yield_optimizer.py --protocol [interesting-one] --detailed
```

### Research New Protocol

```bash
# See all pools for a protocol
python yield_optimizer.py --protocol [new-protocol] --verbose

# Check its risk profile
python yield_optimizer.py --protocol [new-protocol] --detailed
```

### Portfolio Rebalance Analysis

```bash
# Export current opportunities
python yield_optimizer.py --risk low --asset USDC,DAI,USDT --min-tvl 50000000 \
  --format json --output stablecoin_yields.json

# Compare to current positions and identify moves
```

## Output Examples

### Table Output (Default)

```
==============================================================================
  DEFI YIELD OPTIMIZER                              2026-01-15 15:30 UTC
==============================================================================

  TOP YIELD OPPORTUNITIES
------------------------------------------------------------------------------
  Protocol        Pool         Chain        TVL        APY      Risk  Score
  Convex         cvxCRV       Ethereum   $450M     12.50%      Low    9.2
  Aave v3        USDC         Ethereum   $2.1B      4.20%      Low    9.8
  Curve          3pool        Ethereum   $890M      3.80%      Low    9.5
------------------------------------------------------------------------------
```

### JSON Output Structure

```json
{
  "timestamp": "2026-01-15 15:30 UTC",
  "count": 3,
  "pools": [
    {
      "protocol": "convex-finance",
      "symbol": "cvxCRV",
      "chain": "Ethereum",
      "tvl_usd": 450000000,
      "apy": {
        "base": 4.5,
        "reward": 8.0,
        "total": 12.5
      },
      "risk": {
        "score": 9.2,
        "level": "Low",
        "factors": ["Reward token volatility"]
      }
    }
  ]
}
```

## Tips

1. **Start conservative**: Use `--risk low --audited-only` initially
2. **Watch TVL**: Higher TVL generally means better liquidity and lower risk
3. **Question high APY**: Anything over 50% APY deserves extra scrutiny
4. **Export for analysis**: Use JSON export for spreadsheet analysis
5. **Refresh data**: Use `--no-cache` when you need latest rates
6. **Verbose mode**: Use `--verbose` to understand data freshness

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
