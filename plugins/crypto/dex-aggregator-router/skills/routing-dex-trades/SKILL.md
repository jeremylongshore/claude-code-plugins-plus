---
name: routing-dex-trades
description: |
  Route trades across multiple DEXs to find optimal prices with minimal slippage and gas costs.
  Use when comparing DEX prices, finding optimal swap routes, analyzing price impact, splitting large orders, or assessing MEV risk.
  Trigger with phrases like "find best swap", "compare DEX prices", "route trade", "optimal swap route", "split order", "DEX aggregator", "check slippage", or "MEV protection".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(crypto:dex-*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---

# Routing DEX Trades

## Overview

This skill provides optimal trade routing across decentralized exchanges by aggregating quotes from multiple sources (1inch, Paraswap, 0x), discovering multi-hop routes, calculating split orders for large trades, and assessing MEV risk. It helps traders execute at the best prices while minimizing slippage and gas costs.

## Prerequisites

Before using this skill, ensure you have:
- Python 3.9+ with `httpx`, `pydantic`, and `rich` packages
- Network access to aggregator APIs (1inch, Paraswap, 0x)
- Optional: API keys for 1inch and 0x (higher rate limits)
- Environment variables configured in `${CLAUDE_SKILL_DIR}/config/settings.yaml`
- Understanding of DeFi trading concepts (slippage, price impact, MEV)

## Instructions

### Step 1: Configure API Access

1. Copy settings template: `cp ${CLAUDE_SKILL_DIR}/config/settings.yaml.example ${CLAUDE_SKILL_DIR}/config/settings.yaml`
2. Add optional API keys:
   ```yaml
   api_keys:
     oneinch: "your-1inch-api-key"  # Optional, increases rate limits
     zerox: "your-0x-api-key"       # Optional
   ```
3. Set preferred chain: `ethereum`, `arbitrum`, `polygon`, or `optimism`

### Step 2: Quick Quote (Single Best Price)

Use Bash(crypto:dex-router) to get the best price across aggregators:
```bash
python ${CLAUDE_SKILL_DIR}/scripts/dex_router.py ETH USDC 1.0
```

This returns the single best route with price, gas cost, and effective rate.

### Step 3: Compare All DEXs

For detailed comparison across all sources:
```bash
python ${CLAUDE_SKILL_DIR}/scripts/dex_router.py ETH USDC 5.0 --compare
```

Output includes quotes from each aggregator with:
- Output amount and rate
- Price impact percentage
- Gas cost in USD
- Effective rate (after gas)

### Step 4: Analyze Routes (Multi-Hop Discovery)

For trades where multi-hop might be cheaper:
```bash
python ${CLAUDE_SKILL_DIR}/scripts/dex_router.py ETH USDC 10.0 --routes
```

Discovers and compares:
- Direct routes (single pool)
- Multi-hop routes (2-3 pools)
- Shows hop-by-hop breakdown with cumulative impact

### Step 5: Split Large Orders

For whale-sized trades ($10K+), optimize across multiple DEXs:
```bash
python ${CLAUDE_SKILL_DIR}/scripts/dex_router.py ETH USDC 100.0 --split
```

Calculates optimal allocation:
```
Split Recommendation:
  60% via Uniswap V3  (60 ETH → 152,589 USDC)
  40% via Curve       (40 ETH → 101,843 USDC)
  ─────────────────────────────────────────────
  Total: 254,432 USDC (vs. 251,200 single-venue)
  Improvement: +1.28% ($3,232 saved)
```

### Step 6: MEV Risk Assessment

Check sandwich attack risk before executing:
```bash
python ${CLAUDE_SKILL_DIR}/scripts/dex_router.py ETH USDC 50.0 --mev-check
```

Returns risk score and recommendations:
- LOW: Safe to execute via public mempool
- MEDIUM: Consider private transaction
- HIGH: Use Flashbots Protect or CoW Swap

### Step 7: Full Analysis

Combine all features for comprehensive analysis:
```bash
python ${CLAUDE_SKILL_DIR}/scripts/dex_router.py ETH USDC 25.0 --full --output json
```

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed output examples.

## Output

The router provides:

**Quick Quote Mode:**
- Best price across aggregators
- Output amount and effective rate
- Gas cost estimate
- Recommended venue

**Comparison Mode:**
- All venues ranked by effective rate
- Price impact per venue
- Gas costs compared
- Liquidity depth indicators

**Route Analysis:**
- Direct vs. multi-hop comparison
- Hop-by-hop breakdown
- Cumulative price impact
- Gas cost per route type

**Split Mode:**
- Optimal allocation percentages
- Per-venue amounts
- Total vs. single-venue comparison
- Dollar savings estimate

**MEV Assessment:**
- Risk score (LOW/MEDIUM/HIGH)
- Exposure estimate
- Protection recommendations
- Alternative venues (CoW Swap, etc.)

## Trade Size Recommendations

| Trade Size | Strategy | Notes |
|------------|----------|-------|
| < $1K | Direct quote | Gas may exceed savings from optimization |
| $1K - $10K | Compare + routes | Multi-hop can save 0.1-0.5% |
| $10K - $100K | Split analysis | 2-3 way splits reduce impact |
| > $100K | Full + MEV + private TX | Consider OTC or algorithmic execution |

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

Common issues:
- **API Rate Limited**: Wait 60s or use API key for higher limits
- **Quote Expired**: Refresh before execution; quotes valid ~30s
- **No Route Found**: Token may have low liquidity; try larger DEXs
- **Network Timeout**: Retry or check aggregator status

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples including:
- Basic ETH→USDC swap comparison
- Multi-hop route discovery
- Large order splitting
- MEV-protected execution paths

## Resources

- [1inch API Documentation](https://docs.1inch.io/)
- [Paraswap API](https://developers.paraswap.network/)
- [0x API](https://0x.org/docs/api)
- [Flashbots Protect](https://docs.flashbots.net/flashbots-protect/overview)
- [CoW Swap](https://docs.cow.fi/)
