# Analyzing Liquidity Pools - Implementation Reference

## Detailed Output Formats

### Pool Analysis Summary
```
==============================================================================
  LIQUIDITY POOL ANALYZER                           2026-01-15 15:30 UTC
==============================================================================

  POOL: USDC/WETH (Uniswap V3 - 0.05%)
------------------------------------------------------------------------------
  Chain:          Ethereum
  TVL:            $500.5M
  24h Volume:     $125.3M
  Fee Tier:       0.05%

  FEE METRICS
------------------------------------------------------------------------------
  24h Fees:       $62,650
  Fee APR:        4.57%
  Volume/TVL:     0.25

  TOKEN COMPOSITION
------------------------------------------------------------------------------
  USDC:           $252.1M (50.4%)
  WETH:           $248.4M (49.6%)
  Current Price:  $2,450/ETH
==============================================================================
```

### Impermanent Loss Report
```
  IMPERMANENT LOSS CALCULATION
------------------------------------------------------------------------------
  Entry Price:    $2,000/ETH
  Current Price:  $3,000/ETH
  Price Change:   +50%

  IL (%)          -5.72%
  IL ($1000 LP):  -$57.20

  Value if HODL:  $1,250.00
  Value in LP:    $1,192.80

  BREAKEVEN ANALYSIS (0.05% fee tier)
------------------------------------------------------------------------------
  Daily Fees:     $0.63 (at $500M TVL, $125M vol)
  Days to Break:  91 days
  Monthly Fees:   $18.90
==============================================================================
```

## Configuration

Settings in `${CLAUDE_SKILL_DIR}/config/settings.yaml`:

- **Default chain**: Primary chain to query
- **Cache TTL**: How long to cache subgraph data
- **Subgraph endpoints**: URLs for each protocol
- **Fee tier defaults**: Common fee tier options

## Advanced Comparisons

### Cross-Protocol Comparison
When comparing pools across protocols, the analyzer normalizes:
- Fee structures (fixed vs dynamic)
- TVL denominated in USD
- Volume-weighted fee APR
- Gas costs per trade

### Fee Tier Analysis
For Uniswap V3, compare fee tiers for the same pair:
- 0.01% - Stablecoin pairs
- 0.05% - Major pairs (ETH/USDC)
- 0.30% - Standard pairs
- 1.00% - Exotic pairs

## Data Sources

- The Graph: https://thegraph.com/ - Subgraph queries
- Uniswap Info: https://info.uniswap.org/ - Pool explorer
- DeFiLlama: https://defillama.com/ - TVL data
- Impermanent Loss Calculator: https://dailydefi.org/tools/impermanent-loss-calculator/
