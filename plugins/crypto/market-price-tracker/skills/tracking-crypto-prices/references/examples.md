# Usage Examples

Comprehensive examples for the tracking-crypto-prices skill.

## Quick Start Examples

### Example 1: Get Single Price

The simplest use case - check the current price of Bitcoin:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/price_tracker.py --symbol BTC
```

**Output:**
```
BTC (Bitcoin)
$97,234.56 USD
+2.34% (24h) | Vol: $28.5B | MCap: $1.92T
```

---

### Example 2: Check Multiple Prices

Get prices for a portfolio of assets:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/price_tracker.py --symbols BTC,ETH,SOL,AVAX,DOT
```

**Output:**
```
================================================================================
  CRYPTO PRICES                                           Updated: 2025-01-14 15:30:00
================================================================================

  Symbol     Price (USD)      24h Change     Volume (24h)      Market Cap
--------------------------------------------------------------------------------
  BTC       $97,234.56          +2.34%      $28.5B            $1.92T
  ETH        $3,456.78          +1.87%      $12.3B            $415.2B
  SOL          $142.34          +5.12%       $2.1B             $61.4B
  AVAX         $38.92          -0.45%       $425.6M            $14.2B
  DOT           $7.23          +3.21%       $198.3M             $9.8B
--------------------------------------------------------------------------------

  Total 24h Change: +2.44% (weighted)

================================================================================
```

---

### Example 3: Use a Watchlist

Scan predefined watchlists for quick market overview:

```bash
# Top 10 by market cap
python ${CLAUDE_SKILL_DIR}/scripts/price_tracker.py --watchlist top10

# DeFi tokens
python ${CLAUDE_SKILL_DIR}/scripts/price_tracker.py --watchlist defi

# Layer 2 solutions
python ${CLAUDE_SKILL_DIR}/scripts/price_tracker.py --watchlist layer2

# Stablecoins
python ${CLAUDE_SKILL_DIR}/scripts/price_tracker.py --watchlist stablecoins
```

---

## Output Format Examples

### Example 4: JSON Output

Machine-readable output for scripting:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/price_tracker.py --symbol ETH --format json
```

**Output:**
```json
{
  "prices": [
    {
      "symbol": "ETH",
      "name": "Ethereum",
      "price": 3456.78,
      "currency": "USD",
      "change_24h": 1.87,
      "change_7d": 5.42,
      "volume_24h": 12300000000,
      "market_cap": 415200000000,
      "timestamp": "2025-01-14T15:30:00.000000",
      "source": "coingecko"
    }
  ],
  "meta": {
    "count": 1,
    "currency": "USD",
    "timestamp": "2025-01-14T15:30:00.000000"
  }
}
```

---

### Example 5: CSV Export

Export prices for spreadsheet analysis:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/price_tracker.py --symbols BTC,ETH,SOL --format csv --output prices.csv
```

**Output (prices.csv):**
```csv
symbol,name,price,currency,change_24h,change_7d,volume_24h,market_cap,timestamp,source
BTC,Bitcoin,97234.56,USD,2.34,8.21,28500000000,1920000000000,2025-01-14T15:30:00.000000,coingecko
ETH,Ethereum,3456.78,USD,1.87,5.42,12300000000,415200000000,2025-01-14T15:30:00.000000,coingecko
SOL,Solana,142.34,USD,5.12,12.8,2100000000,61400000000,2025-01-14T15:30:00.000000,coingecko
```

---

### Example 6: Minimal Output

Single-line output for shell scripts:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/price_tracker.py --symbols BTC,ETH --format minimal
```

**Output:**
```
BTC:$97,234.56(+2.34%) | ETH:$3,456.78(+1.87%)
```

Use in shell scripts:
```bash
#!/bin/bash
PRICES=$(python ${CLAUDE_SKILL_DIR}/scripts/price_tracker.py --symbols BTC,ETH --format minimal)
echo "Current prices: $PRICES"
```

---

## Historical Data Examples

### Example 7: 30-Day History

Get price history for the last 30 days:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/price_tracker.py --symbol BTC --period 30d
```

**Output:**
```
================================================================================
  HISTORICAL PRICES: BTC
  Period: 2024-12-15 to 2025-01-14
================================================================================

  Date         Price            Volume
--------------------------------------------------------------------------------
  2024-12-15   $95,123.45       $24.3B
  2024-12-16   $94,567.89       $22.1B
  ...
  2025-01-13   $96,789.01       $26.8B
  2025-01-14   $97,234.56       $28.5B
--------------------------------------------------------------------------------
  Total data points: 30
================================================================================
```

---

### Example 8: Custom Date Range

Fetch history for a specific period:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/price_tracker.py --symbol ETH --start 2024-01-01 --end 2024-12-31
```

---

### Example 9: Export Historical Data to CSV

Export OHLCV data for analysis:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/price_tracker.py --symbol BTC --period 90d --format csv --output btc_90d.csv
```

**Output (btc_90d.csv):**
```csv
date,price,volume
2024-10-16,68234.56,18500000000
2024-10-17,69123.45,19200000000
...
```

---

## Currency Examples

### Example 10: Different Fiat Currencies

Get prices in alternative currencies:

```bash
# Euro
python ${CLAUDE_SKILL_DIR}/scripts/price_tracker.py --symbol BTC --currency EUR

# British Pound
python ${CLAUDE_SKILL_DIR}/scripts/price_tracker.py --symbol BTC --currency GBP

# Japanese Yen
python ${CLAUDE_SKILL_DIR}/scripts/price_tracker.py --symbol BTC --currency JPY
```

---

## Search Examples

### Example 11: Search for Coins

Find available cryptocurrencies:

```bash
# Search by name
python ${CLAUDE_SKILL_DIR}/scripts/price_tracker.py --list --query ethereum

# Search by partial name
python ${CLAUDE_SKILL_DIR}/scripts/price_tracker.py --list --query layer
```

**Output:**
```
================================================================================
  SEARCH RESULTS: 'ethereum'
================================================================================
  Symbol     ID                        Name
--------------------------------------------------------------------------------
  ETH        ethereum                  Ethereum
  ETC        ethereum-classic          Ethereum Classic
  ETHW       ethereum-pow              Ethereum PoW
  ...
--------------------------------------------------------------------------------
  Total: 15 coins
================================================================================
```

---

## Cache Management Examples

### Example 12: Bypass Cache

Force fresh data fetch:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/price_tracker.py --symbol BTC --no-cache
```

---

### Example 13: Clear Cache

Remove all cached data:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/price_tracker.py --clear-cache
```

---

## Integration Examples

### Example 14: Portfolio Value Calculation

Use with other skills for portfolio tracking:

```python
# In crypto-portfolio-tracker skill
from price_tracker import get_current_prices

# Get current prices
prices = get_current_prices(["BTC", "ETH", "SOL"])

# Calculate portfolio value
holdings = {"BTC": 0.5, "ETH": 10, "SOL": 100}
total_value = sum(
    prices[symbol]["price"] * amount
    for symbol, amount in holdings.items()
)
print(f"Portfolio Value: ${total_value:,.2f}")
```

---

### Example 15: Shell Script Integration

Use in automated scripts:

```bash
#!/bin/bash

# Get BTC price as JSON and extract value
BTC_PRICE=$(python ${CLAUDE_SKILL_DIR}/scripts/price_tracker.py --symbol BTC --format json | jq '.prices[0].price')

# Alert if price drops below threshold
if (( $(echo "$BTC_PRICE < 90000" | bc -l) )); then
    echo "ALERT: Bitcoin below $90,000!"
fi
```

---

### Example 16: Cron Job for Price Logging

Automated price logging:

```bash
# Add to crontab (crontab -e)
# Log prices every 5 minutes
*/5 * * * * python ${CLAUDE_SKILL_DIR}/scripts/price_tracker.py --watchlist top10 --format csv >> /var/log/crypto_prices.csv
```

---

## Advanced Examples

### Example 17: Multi-Timeframe Analysis

Combine spot and historical data:

```bash
# Current price
python ${CLAUDE_SKILL_DIR}/scripts/price_tracker.py --symbol BTC

# 7-day trend
python ${CLAUDE_SKILL_DIR}/scripts/price_tracker.py --symbol BTC --period 7d

# 30-day trend
python ${CLAUDE_SKILL_DIR}/scripts/price_tracker.py --symbol BTC --period 30d

# Year-to-date
python ${CLAUDE_SKILL_DIR}/scripts/price_tracker.py --symbol BTC --start 2025-01-01 --end $(date +%Y-%m-%d)
```

---

### Example 18: Verbose Debugging

Debug API and cache behavior:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/price_tracker.py --symbol BTC --verbose
```

**Output:**
```
[DEBUG] Checking cache for spot:btc:usd
[DEBUG] Cache miss
[DEBUG] Fetching from CoinGecko API
[DEBUG] API call: /coins/bitcoin
[DEBUG] Response received in 0.234s
[DEBUG] Caching result (TTL: 30s)

BTC (Bitcoin)
$97,234.56 USD
+2.34% (24h) | Vol: $28.5B | MCap: $1.92T

Cache: 0/1 hits
```

---

### Example 19: Custom Watchlist

Create and use a custom watchlist:

1. Edit `config/settings.yaml`:
```yaml
watchlists:
  custom:
    - bitcoin
    - ethereum
    - solana
    - chainlink
    - uniswap
```

2. Use it:
```bash
python ${CLAUDE_SKILL_DIR}/scripts/price_tracker.py --watchlist custom
```

---

## Error Recovery Examples

### Example 20: Handling Rate Limits

When rate limited, the skill automatically:
1. Uses cached data if available
2. Falls back to yfinance if installed
3. Shows stale data with warning

```bash
# Force yfinance fallback (for testing)
# Temporarily disable CoinGecko by rate limiting
python ${CLAUDE_SKILL_DIR}/scripts/price_tracker.py --symbol BTC --verbose
```

**Output with fallback:**
```
[DEBUG] CoinGecko rate limited
[DEBUG] Falling back to yfinance
[DEBUG] yfinance: BTC-USD

BTC (Bitcoin)
$97,234.56 USD (source: yfinance)
```

---

## Best Practices

1. **Use caching**: Default 30-second cache reduces API calls
2. **Batch requests**: Use `--symbols` instead of multiple single requests
3. **Use watchlists**: Predefined lists are optimized for common use cases
4. **Export for analysis**: Use `--format csv` for spreadsheet work
5. **Script with JSON**: Use `--format json` for programmatic access
