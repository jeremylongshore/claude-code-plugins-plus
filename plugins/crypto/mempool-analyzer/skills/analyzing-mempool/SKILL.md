---
name: analyzing-mempool
description: |
  Monitor blockchain mempools for pending transactions, gas analysis, and MEV opportunities.
  Use when analyzing pending transactions, optimizing gas prices, or researching MEV.
  Trigger with phrases like "check mempool", "scan pending txs", "find MEV", "gas price analysis", or "pending swaps".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(python:*mempool*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
---

# Analyzing Mempool

## Overview

Monitor Ethereum mempool for pending transactions, analyze gas prices, detect DEX swaps, and identify potential MEV opportunities. Useful for traders, MEV researchers, and protocol developers.

## Prerequisites

Before using this skill, ensure you have:
- Python 3.8+ with requests library
- Ethereum RPC URL (default: public endpoint, or set ETH_RPC_URL)
- Internet access for RPC calls

## Instructions

### Step 1: Navigate to Scripts Directory

```bash
cd {baseDir}/scripts
```

### Step 2: Choose Your Command

**View Pending Transactions:**
```bash
python mempool_analyzer.py pending
python mempool_analyzer.py pending --limit 100
```

**Gas Price Analysis:**
```bash
python mempool_analyzer.py gas
# Shows distribution, recommendations for slow/standard/fast/instant
```

**Pending DEX Swaps:**
```bash
python mempool_analyzer.py swaps
# Detects Uniswap, SushiSwap, 1inch pending swaps
```

**MEV Opportunity Scan:**
```bash
python mempool_analyzer.py mev
# Detects sandwich, arbitrage, liquidation opportunities
```

**Mempool Summary:**
```bash
python mempool_analyzer.py summary
# Quick overview of pending count, gas, opportunities
```

**Watch Specific Contract:**
```bash
python mempool_analyzer.py watch 0x7a250d...
# Monitor pending transactions to specific contract
```

### Step 3: Interpret Results

**Gas Recommendations:**
- Slow (10th percentile): May take 10+ blocks
- Standard (50th percentile): 2-5 blocks
- Fast (75th percentile): 1-2 blocks
- Instant (90th percentile): Next block likely

**MEV Warnings:**
- MEV detection is for educational purposes
- Real MEV extraction requires specialized infrastructure
- Use this for research and understanding mempool dynamics

## Output

- Pending transaction lists with gas prices and types
- Gas price distribution and recommendations
- Detected DEX swaps with amounts and DEX identification
- MEV opportunity analysis with estimated profits
- JSON output for programmatic use

## Error Handling

See `{baseDir}/references/errors.md` for:
- RPC connection issues
- Mempool access limitations
- Transaction decoding errors
- Gas analysis fallbacks

## Examples

**Check gas before sending transaction:**
```bash
python mempool_analyzer.py gas
# Use "Fast" for quick confirmation
```

**Monitor for large pending swaps:**
```bash
python mempool_analyzer.py swaps --limit 200
```

**Research MEV opportunities:**
```bash
python mempool_analyzer.py mev -v
```

**Use different chain:**
```bash
python mempool_analyzer.py --chain polygon gas
python mempool_analyzer.py --chain arbitrum pending
```

See `{baseDir}/references/examples.md` for more usage patterns.

## Resources

- [Ethereum JSON-RPC](https://ethereum.org/en/developers/docs/apis/json-rpc/) - RPC specification
- [Flashbots](https://flashbots.net) - MEV research and infrastructure
- [DEX Subgraphs](https://thegraph.com) - Pool and swap data
- Supports: Ethereum, Polygon, Arbitrum, Optimism, Base
