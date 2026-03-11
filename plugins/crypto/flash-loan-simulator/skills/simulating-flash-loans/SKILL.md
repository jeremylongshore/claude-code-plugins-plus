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

## Contents

[Overview](#overview) | [Prerequisites](#prerequisites) | [Instructions](#instructions) | [Output](#output) | [Error Handling](#error-handling) | [Examples](#examples) | [Resources](#resources)

## Overview

Simulate flash loan strategies across Aave V3, dYdX, and Balancer with profitability calculations, gas cost estimation, and risk assessment. Evaluate flash loan opportunities without executing real transactions.

## Prerequisites

1. Install Python 3.9+ with `web3`, `httpx`, and `rich` packages
2. Configure RPC endpoint access (free public RPCs via https://chainlist.org work fine)
3. Optionally add Etherscan API key for better gas estimates
4. Set RPC in `${CLAUDE_SKILL_DIR}/config/settings.yaml` or use `ETH_RPC_URL` env var

## Instructions

### Step 1: Simple Arbitrage Simulation

Simulate a two-DEX arbitrage with automatic fee and gas calculation:
```bash
python ${CLAUDE_SKILL_DIR}/scripts/flash_simulator.py arbitrage ETH USDC 100 \
  --dex-buy uniswap --dex-sell sushiswap
```

### Step 2: Compare Flash Loan Providers

Find the cheapest provider for your strategy:
```bash
python ${CLAUDE_SKILL_DIR}/scripts/flash_simulator.py arbitrage ETH USDC 100 --compare-providers
```

### Step 3: Liquidation Profitability

Analyze liquidation opportunities on lending protocols:
```bash
python ${CLAUDE_SKILL_DIR}/scripts/flash_simulator.py liquidation \
  --protocol aave --health-factor 0.95
```

### Step 4: Triangular Arbitrage

Simulate multi-hop circular arbitrage paths:
```bash
python ${CLAUDE_SKILL_DIR}/scripts/flash_simulator.py triangular \
  ETH USDC WBTC ETH --amount 50
```

### Step 5: Risk Assessment

Add risk analysis (MEV competition, execution, protocol, liquidity) to any simulation:
```bash
python ${CLAUDE_SKILL_DIR}/scripts/flash_simulator.py arbitrage ETH USDC 100 --risk-analysis
```

### Step 6: Full Analysis

Run complete analysis combining all features:
```bash
python ${CLAUDE_SKILL_DIR}/scripts/flash_simulator.py arbitrage ETH USDC 100 \
  --full --output json > simulation.json
```

## Output

- **Quick Mode**: Net profit/loss, provider recommendation, Go/No-Go verdict
- **Breakdown Mode**: Step-by-step transaction flow with individual cost components
- **Comparison Mode**: All providers ranked by net profit with fee differences
- **Risk Analysis**: Competition, execution, protocol, and liquidity scores (0-100) with viability grade (A-F)

See `${CLAUDE_SKILL_DIR}/references/implementation.md` for detailed output examples and risk scoring methodology.

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| RPC Rate Limit | Too many requests | Switch to backup endpoint or wait |
| Stale Prices | Data older than 30s | Auto-refreshes with warning |
| No Profitable Route | All routes lose after costs | Try different pairs or amounts |
| Insufficient Liquidity | Trade exceeds pool depth | Reduce amount or split across pools |

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

**Basic arbitrage simulation:**
```bash
python ${CLAUDE_SKILL_DIR}/scripts/flash_simulator.py arbitrage ETH USDC 100 \
  --dex-buy uniswap --dex-sell sushiswap
```

**Find cheapest provider:**
```bash
python ${CLAUDE_SKILL_DIR}/scripts/flash_simulator.py arbitrage ETH USDC 100 --compare-providers
```

**Liquidation opportunity scan:**
```bash
python ${CLAUDE_SKILL_DIR}/scripts/flash_simulator.py liquidation --protocol aave --health-factor 0.95
```

See `${CLAUDE_SKILL_DIR}/references/examples.md` for multi-provider comparison and backtesting examples.

## Resources

- `${CLAUDE_SKILL_DIR}/references/implementation.md` - Provider comparison, strategy details, risk scoring, output modes
- [Aave V3 Flash Loans](https://docs.aave.com/developers/guides/flash-loans)
- [dYdX Flash Loans](https://docs.dydx.exchange/developers/guides/flash-loans)
- [Balancer Flash Loans](https://docs.balancer.fi/concepts/advanced/flash-loans.html)
- [Flashbots Protect](https://docs.flashbots.net/flashbots-protect/overview)
