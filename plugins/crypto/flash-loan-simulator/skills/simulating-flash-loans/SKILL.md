---
name: simulating-flash-loans
description: |
  Simulate flash loan strategies with profitability calculations and risk assessment across Aave, dYdX, and Balancer.
  Use when simulating flash loans, analyzing arbitrage profitability, evaluating liquidation opportunities, or comparing flash loan providers.
  Trigger with phrases like "simulate flash loan", "flash loan arbitrage", "liquidation profit", "compare Aave dYdX", "flash loan strategy", or "DeFi arbitrage simulation".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(crypto:flashloan-*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---

# Simulating Flash Loans

## Overview

This skill simulates flash loan strategies across major DeFi protocols (Aave V3, dYdX, Balancer) with profitability calculations, gas cost estimation, and risk assessment. It enables developers and researchers to evaluate flash loan opportunities without executing real transactions.

## Prerequisites

Before using this skill, ensure you have:
- Python 3.9+ with `web3`, `httpx`, and `rich` packages
- RPC endpoint access (free public RPCs work fine)
- Understanding of flash loan mechanics and DeFi protocols
- Optional: Etherscan API key for better gas estimates

## Instructions

### Step 1: Configure RPC Endpoint

Configure your RPC in `${CLAUDE_SKILL_DIR}/config/settings.yaml`:

```yaml
# Free public RPCs (no signup required)
rpc_endpoints:
  ethereum: "https://rpc.ankr.com/eth"
  polygon: "https://rpc.ankr.com/polygon"
  arbitrum: "https://rpc.ankr.com/arbitrum"
```

Or use environment variable:
```bash
export ETH_RPC_URL="https://rpc.ankr.com/eth"
```

### Step 2: Simple Arbitrage Simulation

Simulate a basic two-DEX arbitrage:
```bash
python ${CLAUDE_SKILL_DIR}/scripts/flash_simulator.py arbitrage ETH USDC 100 \
  --dex-buy uniswap --dex-sell sushiswap
```

This calculates:
- Gross profit from price difference
- Flash loan fee (provider-specific)
- Gas costs
- Net profit/loss

### Step 3: Compare Flash Loan Providers

Find the cheapest provider for your strategy:
```bash
python ${CLAUDE_SKILL_DIR}/scripts/flash_simulator.py arbitrage ETH USDC 100 --compare-providers
```

Output shows:
| Provider | Fee | Net Profit |
|----------|-----|------------|
| dYdX | 0% | $245.30 |
| Balancer | 0.01% | $242.80 |
| Aave V3 | 0.09% | $225.50 |

### Step 4: Liquidation Profitability

Analyze liquidation opportunities:
```bash
python ${CLAUDE_SKILL_DIR}/scripts/flash_simulator.py liquidation \
  --protocol aave --health-factor 0.95
```

Shows positions below health factor threshold with:
- Collateral value
- Debt value
- Liquidation bonus
- Net profit after costs

### Step 5: Triangular Arbitrage

Simulate multi-hop circular arbitrage:
```bash
python ${CLAUDE_SKILL_DIR}/scripts/flash_simulator.py triangular \
  ETH USDC WBTC ETH --amount 50
```

Analyzes path profitability:
```
Path: ETH → USDC → WBTC → ETH
Gross: +0.15 ETH
Fees:  -0.045 ETH (3 swaps)
Loan:  -0.045 ETH (Aave fee)
Gas:   -0.02 ETH
─────────────────────
Net:   +0.04 ETH ($101.73)
```

### Step 6: Risk Assessment

Add risk analysis to any simulation:
```bash
python ${CLAUDE_SKILL_DIR}/scripts/flash_simulator.py arbitrage ETH USDC 100 --risk-analysis
```

Risk factors scored:
- **MEV Competition**: Bot activity on this pair
- **Execution Risk**: Slippage and timing sensitivity
- **Protocol Risk**: Smart contract and oracle risks
- **Liquidity Risk**: Depth available for trade size

### Step 7: Full Analysis

Run complete analysis with all features:
```bash
python ${CLAUDE_SKILL_DIR}/scripts/flash_simulator.py arbitrage ETH USDC 100 \
  --full --output json > simulation.json
```

## Output

The simulator provides:

**Quick Mode:**
- Net profit/loss
- Provider recommendation
- Go/No-Go verdict

**Breakdown Mode:**
- Step-by-step transaction flow
- Individual cost components
- Slippage estimates

**Comparison Mode:**
- All providers ranked
- Fee differences
- Liquidity availability

**Risk Analysis:**
- Competition score (0-100)
- Execution probability
- Protocol safety rating
- Overall viability grade

## Flash Loan Providers

| Provider | Fee | Best For | Chains |
|----------|-----|----------|--------|
| dYdX | 0% | Maximum profit | Ethereum |
| Balancer | 0.01% | Pool tokens | ETH, Polygon, Arbitrum |
| Aave V3 | 0.09% | Any token | ETH, Polygon, Arbitrum, Optimism |
| Uniswap V3 | ~0.3% | Specific pairs | ETH, Polygon, Arbitrum |

## Supported Strategies

1. **Simple Arbitrage**: Buy on DEX A, sell on DEX B
2. **Triangular Arbitrage**: A→B→C→A circular path
3. **Liquidation**: Repay debt, claim collateral bonus
4. **Collateral Swap**: Replace collateral without closing
5. **Self-Liquidation**: Efficiently close own position
6. **Debt Refinancing**: Move debt to better rates

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

Common issues:
- **RPC Rate Limit**: Switch to backup endpoint or wait
- **Stale Prices**: Data older than 30s triggers warning
- **No Profitable Route**: All routes lose money after costs
- **Insufficient Liquidity**: Trade size exceeds pool depth

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples including:
- ETH/USDC arbitrage simulation
- Aave liquidation analysis
- Multi-provider comparison
- Historical backtesting

## Educational Disclaimer

**FOR EDUCATIONAL PURPOSES ONLY**

Flash loan strategies involve significant risks:
- Smart contract bugs can cause total loss
- MEV bots compete for same opportunities
- Gas costs can exceed profits
- Protocol exploits may have legal implications

Never deploy unaudited code. Start with testnets. Consult legal counsel.

## Resources

- [Aave V3 Flash Loans](https://docs.aave.com/developers/guides/flash-loans)
- [dYdX Flash Loans](https://docs.dydx.exchange/developers/guides/flash-loans)
- [Balancer Flash Loans](https://docs.balancer.fi/concepts/advanced/flash-loans.html)
- [Flashbots Protect](https://docs.flashbots.net/flashbots-protect/overview)
- [Free RPC Providers](https://chainlist.org)
