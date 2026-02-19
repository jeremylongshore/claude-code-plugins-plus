---
name: optimizing-gas-fees
description: |
  Optimize blockchain gas costs by analyzing prices, patterns, and timing.
  Use when checking gas prices, estimating costs, or finding optimal windows.
  Trigger with phrases like "gas prices", "optimize gas", "transaction cost", "when to transact".
allowed-tools: Read, Bash(python3:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
---

# Optimizing Gas Fees

## Overview

Gas fee optimization skill that:
- Fetches real-time gas prices from multiple sources
- Estimates transaction costs in ETH and USD
- Analyzes historical patterns to find optimal timing
- Predicts future gas prices
- Compares gas across multiple chains

## Prerequisites

- Python 3.8+ with requests library
- Network access to RPC endpoints
- Optional: `ETHERSCAN_API_KEY` for higher rate limits
- Optional: Custom RPC URLs via environment variables

## Instructions

### 1. Check Current Gas Prices

```bash
cd {baseDir}/scripts && python3 gas_optimizer.py current
```

For specific chain:
```bash
cd {baseDir}/scripts && python3 gas_optimizer.py current --chain polygon
```

### 2. Estimate Transaction Cost

For known operations:
```bash
cd {baseDir}/scripts && python3 gas_optimizer.py estimate --operation uniswap_v2_swap --all-tiers
```

For custom gas limit:
```bash
cd {baseDir}/scripts && python3 gas_optimizer.py estimate --gas-limit 150000 --tier fast
```

Available operations: `eth_transfer`, `erc20_transfer`, `erc20_approve`, `uniswap_v2_swap`, `uniswap_v3_swap`, `sushiswap_swap`, `curve_swap`, `nft_mint`, `nft_transfer`, `opensea_listing`, `aave_deposit`, `aave_withdraw`, `compound_supply`, `compound_borrow`, `bridge_deposit`

### 3. Find Optimal Transaction Window

```bash
cd {baseDir}/scripts && python3 gas_optimizer.py optimal
```

### 4. View Gas Patterns

Hourly patterns:
```bash
cd {baseDir}/scripts && python3 gas_optimizer.py patterns
```

Daily patterns:
```bash
cd {baseDir}/scripts && python3 gas_optimizer.py patterns --daily
```

### 5. Predict Future Gas

```bash
cd {baseDir}/scripts && python3 gas_optimizer.py predict --time 14
```

### 6. Compare Chains

```bash
cd {baseDir}/scripts && python3 gas_optimizer.py compare
```

### 7. View Base Fee History

```bash
cd {baseDir}/scripts && python3 gas_optimizer.py history --blocks 50
```

## Output

- **Current**: Base fee, priority fee, and tier prices (slow/standard/fast/instant)
- **Estimate**: Gas cost in native token and USD for each tier
- **Patterns**: Historical hourly/daily patterns with low-gas markers
- **Optimal**: Recommended transaction window with expected savings
- **Predict**: Gas forecast for specific time with confidence
- **Compare**: Side-by-side gas prices across chains

## Supported Chains

| Chain | Native Token | Block Time |
|-------|--------------|------------|
| Ethereum | ETH | ~12 sec |
| Polygon | MATIC | ~2 sec |
| Arbitrum | ETH | ~0.25 sec |
| Optimism | ETH | ~2 sec |
| Base | ETH | ~2 sec |

## Price Tiers

| Tier | Percentile | Confirmation Time |
|------|------------|-------------------|
| Slow | 10th | 10+ blocks (~2+ min) |
| Standard | 50th | 3-5 blocks (~1 min) |
| Fast | 75th | 1-2 blocks (~30 sec) |
| Instant | 90th | Next block (~12 sec) |

## Error Handling

See `{baseDir}/references/errors.md` for:
- RPC connection issues
- API rate limiting
- Price feed errors
- Pattern analysis errors

## Examples

See `{baseDir}/references/examples.md` for:
- Quick start commands
- Cost estimation scenarios
- Multi-chain comparison
- Practical workflows

## Resources

- [EIP-1559](https://eips.ethereum.org/EIPS/eip-1559) - Fee market specification
- [Etherscan Gas Tracker](https://etherscan.io/gastracker) - Reference oracle
- [L2Fees](https://l2fees.info/) - L2 cost comparison
