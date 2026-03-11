---
name: tracking-crypto-derivatives
description: |
  Track cryptocurrency futures, options, and perpetual swaps with funding rates, open interest, liquidations, and comprehensive derivatives market analysis.
  Use when monitoring derivatives markets, analyzing funding rates, tracking open interest, finding liquidation levels, or researching options flow.
  Trigger with phrases like "funding rate", "open interest", "perpetual swap", "futures basis", "liquidation levels", "options flow", "put call ratio", "derivatives analysis", or "BTC perps".
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(crypto:derivatives-*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# Tracking Crypto Derivatives

## Overview

Comprehensive derivatives market analysis across centralized and decentralized exchanges. This skill aggregates funding rates, open interest, liquidations, and options data to provide actionable trading insights.

**Supported Markets**:
- **Perpetual Swaps**: Binance, Bybit, OKX, Deribit, BitMEX
- **Futures**: Quarterly and monthly contracts
- **Options**: Deribit (primary), OKX, Bybit
- **DEX Perpetuals**: dYdX, GMX, Drift Protocol

## Prerequisites

Before using this skill, ensure you have:
- Python 3.8+ installed
- Network access to exchange APIs
- Optional: API keys for higher rate limits
- Understanding of derivatives concepts (funding, OI, basis)

## Instructions

### Step 1: Check Funding Rates

Monitor funding rates across exchanges to identify sentiment and arbitrage opportunities.

```bash
# Check BTC funding rates across all exchanges
python derivatives_tracker.py funding BTC

# Check multiple assets
python derivatives_tracker.py funding BTC ETH SOL

# Show historical average
python derivatives_tracker.py funding BTC --history 7d
```

**Interpret Results**:
- **Positive funding** (>0.01%): Longs pay shorts, bullish sentiment
- **Negative funding** (<-0.01%): Shorts pay longs, bearish sentiment
- **Extreme funding** (>0.1%): Potential contrarian opportunity

### Step 2: Analyze Open Interest

Track open interest to gauge market positioning and trend strength.

```bash
# Get BTC open interest across exchanges
python derivatives_tracker.py oi BTC

# Show OI changes over time
python derivatives_tracker.py oi BTC --changes

# Compare OI vs price
python derivatives_tracker.py oi BTC --divergence
```

**OI Interpretation**:
- **Rising OI + Rising Price**: Strong bullish trend
- **Rising OI + Falling Price**: Strong bearish trend
- **Falling OI + Rising Price**: Short covering rally
- **Falling OI + Falling Price**: Long liquidations

### Step 3: Monitor Liquidations

Track liquidation levels and recent liquidation events.

```bash
# Get liquidation heatmap
python derivatives_tracker.py liquidations BTC

# Show recent large liquidations
python derivatives_tracker.py liquidations BTC --recent

# Set minimum size filter
python derivatives_tracker.py liquidations BTC --min-size 100000  # 100000 = configured value
```

**Liquidation Signals**:
- Large liquidation clusters indicate support/resistance
- Cascading liquidations can accelerate price moves
- Long/short liquidation ratio indicates market direction

### Step 4: Analyze Options Market

Research options flow and implied volatility.

```bash
# Get options overview
python derivatives_tracker.py options BTC

# Show put/call ratio
python derivatives_tracker.py options BTC --pcr

# Find max pain for expiry
python derivatives_tracker.py options BTC --expiry 2025-01-31  # 2025 year

# Track large options trades
python derivatives_tracker.py options BTC --flow
```

**Options Insights**:
- **High IV rank** (>80): Options expensive, consider selling
- **Low IV rank** (<20): Options cheap, consider buying
- **Max pain**: Price where most options expire worthless

### Step 5: Calculate Basis

Find basis trading and arbitrage opportunities.

```bash
# Get spot-perp basis
python derivatives_tracker.py basis BTC

# Get quarterly futures basis
python derivatives_tracker.py basis BTC --quarterly

# Show all basis opportunities
python derivatives_tracker.py basis --all
```

**Basis Trading**:
- **Positive basis**: Futures > Spot (contango, normal)
- **Negative basis**: Futures < Spot (backwardation)
- **Cash-and-carry**: Buy spot + sell futures when basis high

### Step 6: Full Dashboard

Get comprehensive derivatives overview.

```bash
# Full derivatives dashboard for BTC
python derivatives_tracker.py dashboard BTC

# Multi-asset dashboard
python derivatives_tracker.py dashboard BTC ETH SOL

# Export to JSON
python derivatives_tracker.py dashboard BTC --output json
```

See `${CLAUDE_SKILL_DIR}/references/implementation.md` for detailed implementation guide.

## Output

The skill provides structured reports including:

### Funding Rate Report
```
BTC PERPETUAL FUNDING RATES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Exchange    Current    24h Avg    7d Avg    Next Payment
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Binance     +0.0150%   +0.0120%   +0.0080%  2h 15m
Bybit       +0.0180%   +0.0140%   +0.0100%  2h 15m
OKX         +0.0130%   +0.0110%   +0.0090%  2h 15m
Deribit     +0.0200%   +0.0150%   +0.0120%  2h 15m
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Weighted Avg: +0.0158%  |  Annualized: +17.29%
Sentiment: Moderately Bullish
```

### Open Interest Report
```
BTC OPEN INTEREST ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Exchange    OI (USD)      24h Chg    7d Chg    Share
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Binance     $8.2B         +2.5%      +8.1%     44.3%
Bybit       $4.5B         +1.8%      +5.2%     24.3%
OKX         $3.1B         +3.2%      +12.5%    16.8%
BitMEX      $1.5B         -0.5%      -2.1%     8.1%
Deribit     $1.2B         +0.8%      +3.4%     6.5%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total OI: $18.5B (+2.3% 24h)
Long/Short Ratio: 1.15 (53.5% long)
```

### Liquidation Heatmap
```
BTC LIQUIDATION LEVELS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Current Price: $67,500  # HTTP 500 Internal Server Error

LONG LIQUIDATIONS (below):
  $65,000 ████████████ $125M (HIGH DENSITY)
  $62,500 ███████      $85M  # HTTP 500 Internal Server Error
  $60,000 ████████████████████ $210M (CRITICAL)

SHORT LIQUIDATIONS (above):
  $70,000 █████████    $95M
  $72,500 █████████████ $145M (HIGH DENSITY)  # HTTP 500 Internal Server Error
  $75,000 █████████████████ $180M
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
24h Liquidations: Longs $45.2M | Shorts $32.8M
```

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

Common issues:
- **ERR_RATE_LIMIT**: Reduce request frequency or add API key
- **ERR_EXCHANGE_DOWN**: Exchange API unavailable, try alternative
- **ERR_SYMBOL_INVALID**: Check symbol format (BTC, ETH, not BTCUSDT)

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

Quick examples:

```bash
# Morning derivatives check
python derivatives_tracker.py dashboard BTC ETH SOL

# Monitor funding for arbitrage
python derivatives_tracker.py funding BTC --alert-threshold 0.08

# Pre-expiry options analysis
python derivatives_tracker.py options BTC --expiry friday

# Find basis trading opportunities
python derivatives_tracker.py basis --all --min-yield 5
```

## Resources

### Data Sources
- **Coinglass**: Aggregated derivatives data
- **Exchange APIs**: Binance, Bybit, OKX, Deribit
- **The Graph**: DEX perpetuals data

### Key Concepts
- **Funding Rate**: Payment between longs/shorts every 8h
- **Open Interest**: Total outstanding contracts
- **Basis**: Difference between futures and spot price
- **Max Pain**: Strike where most options expire worthless
- **IV Rank**: Current IV percentile vs historical

### Risk Warning
Derivatives are leveraged instruments with high risk of loss.
- Funding costs accumulate over time
- Liquidations can happen rapidly
- Options can expire worthless
- This tool provides analysis only, not financial advice