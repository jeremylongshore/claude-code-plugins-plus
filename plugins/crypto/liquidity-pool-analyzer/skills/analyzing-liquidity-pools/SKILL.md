---
name: analyzing-liquidity-pools
description: |
  Analyze DEX liquidity pools for TVL, volume, fees, impermanent loss, and LP profitability.
  Use when analyzing liquidity pools, calculating impermanent loss, or comparing DEX pools.
  Trigger with phrases like "analyze liquidity pool", "calculate impermanent loss", "LP returns", "pool TVL", "DEX pool metrics", or "compare pools".

allowed-tools: Read, Write, Bash(crypto:liquidity-*)
version: 2.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---

# Analyzing Liquidity Pools

## Overview

Analyze DEX liquidity pools to understand TVL, trading volume, fee income, and impermanent loss risk. Compare pools across protocols (Uniswap, Curve, Balancer) and chains to identify optimal LP opportunities.

## Prerequisites

Before using this skill, ensure you have:

- Python 3.8+ installed
- Internet access for subgraph/API queries
- Understanding of liquidity providing concepts (IL, fee tiers, TVL)

## Instructions

### Step 1: Analyze a Specific Pool

Analyze pool by address:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/pool_analyzer.py --pool 0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640
```

Analyze by token pair:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/pool_analyzer.py --pair ETH/USDC --protocol uniswap-v3
```

### Step 2: Calculate Impermanent Loss

Calculate IL for a price change:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/pool_analyzer.py --il-calc --entry-price 2000 --current-price 3000
```

Project IL for various scenarios:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/pool_analyzer.py --il-scenarios --token-pair ETH/USDC
```

### Step 3: Estimate LP Returns

Calculate fee APR:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/pool_analyzer.py --pool [address] --detailed
```

Project returns for position size:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/pool_analyzer.py --pool [address] --position 10000
```

### Step 4: Compare Pools

Compare same pair across protocols:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/pool_analyzer.py --compare --pair ETH/USDC --protocols uniswap-v3,curve,balancer
```

Compare fee tiers:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/pool_analyzer.py --compare --pair ETH/USDC --fee-tiers 0.05,0.30,1.00
```

### Step 5: Export Results

Export to JSON:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/pool_analyzer.py --pool [address] --format json --output pool_analysis.json
```

Export comparison to CSV:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/pool_analyzer.py --compare --pair ETH/USDC --format csv --output pools.csv
```

## Output

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

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

Common issues:
- **Pool not found**: Verify address and chain
- **Subgraph timeout**: Uses cached data with warning
- **Invalid pair**: Check supported protocols

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed usage examples.

### Quick Examples

**Analyze top ETH/USDC pool**:
```bash
python pool_analyzer.py --pair ETH/USDC --protocol uniswap-v3 --chain ethereum
```

**Calculate IL for 2x price increase**:
```bash
python pool_analyzer.py --il-calc --entry-price 100 --current-price 200
```

**Compare Uniswap fee tiers**:
```bash
python pool_analyzer.py --compare --pair ETH/USDC --fee-tiers 0.05,0.30,1.00
```

**Export all ETH pairs**:
```bash
python pool_analyzer.py --token ETH --format json --output eth_pools.json
```

## Configuration

Settings in `${CLAUDE_SKILL_DIR}/config/settings.yaml`:

- **Default chain**: Primary chain to query
- **Cache TTL**: How long to cache subgraph data
- **Subgraph endpoints**: URLs for each protocol
- **Fee tier defaults**: Common fee tier options

## Resources

- The Graph: https://thegraph.com/ - Subgraph queries
- Uniswap Info: https://info.uniswap.org/ - Pool explorer
- DeFiLlama: https://defillama.com/ - TVL data
- Impermanent Loss Calculator: https://dailydefi.org/tools/impermanent-loss-calculator/
