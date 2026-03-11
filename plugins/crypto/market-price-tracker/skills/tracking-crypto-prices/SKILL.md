---
name: tracking-crypto-prices
description: |
  Track real-time cryptocurrency prices across exchanges with historical data and alerts.
  Provides price data infrastructure for dependent skills (portfolio, tax, DeFi, arbitrage).
  Use when checking crypto prices, monitoring markets, or fetching historical price data.
  Trigger with phrases like "check price", "BTC price", "crypto prices", "price history",
  "get quote for", "what's ETH trading at", "show me top coins", or "track my watchlist".
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(python:*)
version: 2.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---

# Tracking Crypto Prices

## Overview

Foundation skill providing real-time and historical cryptocurrency price data. This skill is the data layer for the crypto plugin ecosystem - 10+ other skills depend on it for price information.

**Key Capabilities:**
- Real-time prices for 10,000+ cryptocurrencies
- Historical OHLCV data (1 day to all-time)
- Multi-currency support (USD, EUR, GBP, 30+ currencies)
- Intelligent caching to minimize API calls
- Predefined and custom watchlists
- Export to CSV/JSON for analysis

**Dependent Skills:**
This skill provides price data to: market-movers-scanner, crypto-portfolio-tracker, crypto-tax-calculator, defi-yield-optimizer, liquidity-pool-analyzer, staking-rewards-optimizer, crypto-derivatives-tracker, dex-aggregator-router, options-flow-analyzer, arbitrage-opportunity-finder.

## Prerequisites

Install required dependencies:

```bash
pip install requests pandas yfinance
```

Optional for advanced features:
```bash
pip install python-dotenv  # For API key management
```

**API Setup** (optional, for higher rate limits):
1. Get free API key from https://www.coingecko.com/en/api
2. Add to `${CLAUDE_SKILL_DIR}/config/settings.yaml` or set environment variable `COINGECKO_API_KEY`

## Instructions

### Step 1: Quick Price Check

Get current price for any cryptocurrency:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/price_tracker.py --symbol BTC
```

Check multiple assets:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/price_tracker.py --symbols BTC,ETH,SOL
```

### Step 2: Use Watchlists

Scan predefined watchlists:

```bash
# Top 10 by market cap
python ${CLAUDE_SKILL_DIR}/scripts/price_tracker.py --watchlist top10

# DeFi tokens
python ${CLAUDE_SKILL_DIR}/scripts/price_tracker.py --watchlist defi

# Layer 2 tokens
python ${CLAUDE_SKILL_DIR}/scripts/price_tracker.py --watchlist layer2
```

Available watchlists: `top10`, `defi`, `layer2`, `stablecoins`, `memecoins`

### Step 3: Fetch Historical Data

Get OHLCV (Open, High, Low, Close, Volume) history:

```bash
# Last 30 days
python ${CLAUDE_SKILL_DIR}/scripts/price_tracker.py --symbol BTC --period 30d

# Last 90 days with CSV export
python ${CLAUDE_SKILL_DIR}/scripts/price_tracker.py --symbol BTC --period 90d --output csv

# Custom date range
python ${CLAUDE_SKILL_DIR}/scripts/price_tracker.py --symbol ETH --start 2024-01-01 --end 2024-12-31
```

### Step 4: Configure Settings

Edit `${CLAUDE_SKILL_DIR}/config/settings.yaml` to customize:

```yaml
cache:
  spot_ttl: 30          # Seconds to cache spot prices
  historical_ttl: 3600  # Seconds to cache historical data

currency:
  default: usd          # Default fiat currency

watchlists:
  custom:               # Add your own watchlist
    - BTC
    - ETH
    - SOL
```

## Output

### Price Table (Default)

```
================================================================================
  CRYPTO PRICES                                           Updated: [timestamp]
================================================================================

  Symbol     Price (USD)      24h Change     Volume (24h)      Market Cap
--------------------------------------------------------------------------------
  BTC       $97,234.56          +2.34%      $28.5B            $1.92T
  ETH        $3,456.78          +1.87%      $12.3B            $415.2B
  SOL          $142.34          +5.12%       $2.1B             $61.4B
--------------------------------------------------------------------------------

  Total 24h Change: +2.44% (weighted)

================================================================================
```

### JSON Output (--format json)

```json
{
  "prices": [
    {
      "symbol": "BTC",
      "name": "Bitcoin",
      "price": 97234.56,
      "currency": "USD",
      "change_24h": 2.34,
      "volume_24h": 28500000000,
      "market_cap": 1920000000000,
      "timestamp": "[timestamp]",
      "source": "coingecko"
    }
  ],
  "meta": {
    "count": 1,
    "currency": "USD",
    "cached": false
  }
}
```

### Historical CSV Export

```csv
date,open,high,low,close,volume
[date],95000.00,96500.00,94200.00,96100.00,25000000000
[date],96100.00,97800.00,95800.00,97500.00,27000000000
```

## Configuration

Edit `${CLAUDE_SKILL_DIR}/config/settings.yaml`:

```yaml
# API Configuration
api:
  coingecko:
    api_key: ${COINGECKO_API_KEY}  # Optional, from env
    use_pro: false
  yfinance:
    enabled: true                   # Fallback source

# Cache Configuration
cache:
  enabled: true
  spot_ttl: 30                      # Spot price TTL (seconds)
  historical_ttl: 3600              # Historical data TTL (seconds)
  directory: ./data

# Display Configuration
currency:
  default: usd
  supported:
    - usd
    - eur
    - gbp
    - jpy
    - cad
    - aud

# Predefined Watchlists
watchlists:
  top10:
    - bitcoin
    - ethereum
    - tether
    - binancecoin
    - solana
    - ripple
    - cardano
    - avalanche-2
    - dogecoin
    - polkadot

  defi:
    - uniswap
    - aave
    - chainlink
    - maker
    - compound-governance-token
    - curve-dao-token
    - sushi

  layer2:
    - matic-network
    - arbitrum
    - optimism
    - immutable-x
```

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `Unknown symbol: XYZ` | Invalid cryptocurrency ticker | Check spelling, use `--list` to search |
| `Rate limit exceeded` | Too many API calls | Wait 60s, or use API key for higher limits |
| `Network error` | No internet connection | Check connection, cached data will be used |
| `Cache stale` | Cached data older than TTL | Data still shown with warning, will refresh |

### Rate Limit Handling

The skill automatically:
1. Uses cached data when available
2. Applies exponential backoff on rate limits
3. Falls back to yfinance if CoinGecko fails
4. Shows stale cache data with warning as last resort

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples including:
- Multi-timeframe analysis
- Portfolio value calculation
- Price alert setup
- Integration with other skills

### Example 1: Quick Price Check

```bash
python ${CLAUDE_SKILL_DIR}/scripts/price_tracker.py --symbol BTC
```

Output:
```
BTC (Bitcoin)
$97,234.56 USD
+2.34% (24h) | Vol: $28.5B | MCap: $1.92T
```

### Example 2: Watchlist Scan

```bash
python ${CLAUDE_SKILL_DIR}/scripts/price_tracker.py --watchlist top10
```

### Example 3: Historical Export

```bash
python ${CLAUDE_SKILL_DIR}/scripts/price_tracker.py --symbol ETH --period 90d --output csv
```

Creates: `${CLAUDE_SKILL_DIR}/data/ETH_90d_[date].csv`

## Integration with Other Skills

This skill provides the price data foundation for other crypto skills.

**Direct Import** (recommended for Python skills):
```python
from price_tracker import get_current_prices, get_historical_prices

# Get prices for portfolio valuation
prices = get_current_prices(["BTC", "ETH", "SOL"])
```

**CLI Subprocess** (for non-Python or isolation):
```bash
PRICES=$(python ${CLAUDE_SKILL_DIR}/scripts/price_tracker.py --symbols BTC,ETH --format json)
```

**Shared Cache** (efficient for batch):
Multiple skills can read from `${CLAUDE_SKILL_DIR}/data/cache.json` to avoid redundant API calls.

## Files

| File | Purpose |
|------|---------|
| `scripts/price_tracker.py` | Main CLI entry point |
| `scripts/api_client.py` | CoinGecko/yfinance abstraction |
| `scripts/cache_manager.py` | Cache read/write/invalidation |
| `scripts/formatters.py` | Output formatting |
| `config/settings.yaml` | User configuration |
| `data/cache.json` | Price cache (auto-generated) |

## Resources

- [CoinGecko API](https://www.coingecko.com/en/api) - Primary data source
- [yfinance](https://github.com/ranaroussi/yfinance) - Fallback for historical data
- PRD.md - Product requirements
- ARD.md - Architecture documentation
