# Implementation Details

## Output Formats

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

## Full Configuration Reference

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
  supported: [usd, eur, gbp, jpy, cad, aud]

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

## Rate Limit Handling

The skill automatically manages rate limits through a multi-tier fallback:
1. Uses cached data when available (spot: 30s TTL, historical: 1h TTL)
2. Applies exponential backoff on rate limits (1s, 2s, 4s, max 3 retries)
3. Falls back to yfinance if CoinGecko fails
4. Shows stale cache data with warning as last resort

## Integration with Other Skills

This skill provides the price data foundation for 10+ other crypto skills.

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
