---
name: finding-arbitrage-opportunities
description: |
  Detect profitable arbitrage opportunities across CEX, DEX, and cross-chain markets in real-time.
  Use when scanning for price spreads, finding arbitrage paths, comparing exchange prices, or analyzing triangular arbitrage opportunities.
  Trigger with phrases like "find arbitrage", "scan for arb", "price spread", "exchange arbitrage", "triangular arb", "DEX price difference", or "cross-exchange opportunity".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(crypto:arbitrage-*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# Finding Arbitrage Opportunities

## Overview

This skill detects and analyzes arbitrage opportunities across cryptocurrency exchanges and DeFi protocols. It aggregates prices from multiple sources, calculates net profit after fees and costs, and identifies both direct and triangular arbitrage paths.

## Prerequisites

Before using this skill, ensure you have:
- Python 3.9+ with `httpx`, `rich`, and `networkx` packages
- Internet access for API calls (no API keys required for basic use)
- Optional: Exchange API keys for real-time order book access
- Understanding of arbitrage concepts and trading fees

## Instructions

### Step 1: Configure Data Sources

Configure your price sources in `${CLAUDE_SKILL_DIR}/config/settings.yaml`:

```yaml
# Primary data sources
data_sources:
  coingecko:
    enabled: true
    base_url: "https://api.coingecko.com/api/v3"
    rate_limit: 10  # calls per minute (free tier)

exchanges:
  - binance
  - coinbase
  - kraken
  - kucoin
  - okx
```

Or use environment variables for API keys:
```bash
export BINANCE_API_KEY="your-key"
export COINBASE_API_KEY="your-key"
```

### Step 2: Quick Spread Scan

Scan for arbitrage opportunities on a specific pair:
```bash
python ${CLAUDE_SKILL_DIR}/scripts/arb_finder.py scan ETH USDC
```

This shows:
- Current prices on each exchange
- Spread percentage
- Estimated profit after fees
- Recommended action

### Step 3: Multi-Exchange Comparison

Compare prices across specific exchanges:
```bash
python ${CLAUDE_SKILL_DIR}/scripts/arb_finder.py scan ETH USDC \
  --exchanges binance,coinbase,kraken,kucoin,okx
```

Output includes:
| Exchange | Bid | Ask | Spread | Net Profit |
|----------|-----|-----|--------|------------|
| Binance | 2541.20 | 2541.50 | 0.01% | - |
| Coinbase | 2543.80 | 2544.10 | 0.01% | +$2.30 |

### Step 4: DEX Price Comparison

Scan decentralized exchanges for arbitrage:
```bash
python ${CLAUDE_SKILL_DIR}/scripts/arb_finder.py scan ETH USDC --dex-only
```

Compares:
- Uniswap V3
- SushiSwap
- Curve
- Balancer

Includes gas cost estimates for on-chain execution.

### Step 5: Triangular Arbitrage Discovery

Find profitable circular paths within an exchange:
```bash
python ${CLAUDE_SKILL_DIR}/scripts/arb_finder.py triangular binance --min-profit 0.5
```

Example output:
```
Path: ETH → BTC → USDT → ETH
Gross: +0.82%
Fees:  -0.30% (3 × 0.10%)
─────────────────────────────
Net:   +0.52%
```

### Step 6: Cross-Chain Opportunities

Compare prices across different blockchains:
```bash
python ${CLAUDE_SKILL_DIR}/scripts/arb_finder.py cross-chain USDC \
  --chains ethereum,polygon,arbitrum
```

Shows:
- Price on each chain
- Bridge fees and times
- Net profit after bridging

### Step 7: Real-Time Monitoring

Continuously monitor for opportunities:
```bash
python ${CLAUDE_SKILL_DIR}/scripts/arb_finder.py monitor ETH USDC \
  --threshold 0.5 \
  --interval 5
```

Alerts when spread exceeds threshold:
```
[ALERT] ETH/USDC spread 0.62% (Binance → Coinbase)
        Buy: $2,541.20 | Sell: $2,556.98
        Net Profit: +$12.34 (after fees)
```

### Step 8: Profit Calculator

Calculate exact profit for a trade:
```bash
python ${CLAUDE_SKILL_DIR}/scripts/arb_finder.py calc \
  --buy-exchange binance \
  --sell-exchange coinbase \
  --pair ETH/USDC \
  --amount 10
```

Shows detailed breakdown:
- Gross profit
- Trading fees (both exchanges)
- Withdrawal fees
- Net profit
- Breakeven spread

### Step 9: JSON Export

Export opportunities for bot integration:
```bash
python ${CLAUDE_SKILL_DIR}/scripts/arb_finder.py scan ETH USDC --output json > opportunities.json
```

## Output

The scanner provides:

**Quick Mode (default):**
- Best opportunity with profit estimate
- Buy/sell recommendation
- Risk level indicator

**Detailed Mode (`--detailed`):**
- All exchange prices
- Fee breakdown
- Slippage estimates
- Historical spread context

**Monitor Mode:**
- Real-time updates
- Threshold alerts
- Trend indicators

## Supported Exchanges

### Centralized Exchanges (CEX)
| Exchange | Maker Fee | Taker Fee | Withdrawal |
|----------|-----------|-----------|------------|
| Binance | 0.10% | 0.10% | Variable |
| Coinbase | 0.40% | 0.60% | Variable |
| Kraken | 0.16% | 0.26% | Variable |
| KuCoin | 0.10% | 0.10% | Variable |
| OKX | 0.08% | 0.10% | Variable |

### Decentralized Exchanges (DEX)
| DEX | Fee Range | Gas (ETH) | Chains |
|-----|-----------|-----------|--------|
| Uniswap V3 | 0.01-1% | ~150k | ETH, Polygon, Arbitrum |
| SushiSwap | 0.30% | ~150k | Multi-chain |
| Curve | 0.04% | ~200k | ETH, Polygon, Arbitrum |
| Balancer | 0.01-10% | ~180k | ETH, Polygon, Arbitrum |

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

Common issues:
- **Rate Limited**: Reduce polling frequency or use API key
- **Stale Prices**: Data older than 10s flagged with warning
- **No Spread**: All exchanges at similar prices (efficient market)
- **Insufficient Liquidity**: Trade size exceeds order book depth

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples including:
- ETH/USDC CEX arbitrage scan
- DEX triangular arbitrage discovery
- Cross-chain USDC opportunity
- Automated monitoring setup

## Educational Disclaimer

**FOR EDUCATIONAL PURPOSES ONLY**

Arbitrage trading involves significant risks:
- Opportunities may disappear before execution
- Price data may be delayed or inaccurate
- Fees can exceed profits on small trades
- Market conditions change rapidly

This tool provides analysis only. Do not trade without understanding the risks.

## Resources

- [CoinGecko API](https://www.coingecko.com/en/api) - Free price data
- [CCXT Library](https://github.com/ccxt/ccxt) - Unified exchange API
- [Uniswap Subgraph](https://thegraph.com/hosted-service/subgraph/uniswap/uniswap-v3) - DEX data
- [Gas Tracker](https://etherscan.io/gastracker) - Ethereum gas prices