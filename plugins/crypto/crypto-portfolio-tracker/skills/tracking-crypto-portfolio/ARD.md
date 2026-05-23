# ARD: Tracking Crypto Portfolio

> Part of [Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)

## Document Control

| Field | Value |
|-------|-------|
| **Skill Name** | tracking-crypto-portfolio |
| **Architecture Pattern** | Data Aggregation + Valuation Engine |
| **Version** | 2.0.0 |
| **Author** | Jeremy Longshore <jeremy@intentsolutions.io> |

---

## Architectural Overview

### Pattern: Portfolio Valuation Pipeline

This skill implements a data aggregation pattern with real-time price enrichment and valuation calculation.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     CRYPTO PORTFOLIO TRACKER ARCHITECTURE                    │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  Portfolio JSON  │     │  CoinGecko API   │     │  User Config     │
│    (Holdings)    │     │  (Prices)        │     │  (Settings)      │
└────────┬─────────┘     └────────┬─────────┘     └────────┬─────────┘
         │                        │                        │
         ▼                        ▼                        ▼
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  PORTFOLIO       │     │  PRICE FETCHER   │     │  CONFIG LOADER   │
│  LOADER          │     │  - Batch fetch   │     │  - Categories    │
│  - Validation    │     │  - Caching       │     │  - Thresholds    │
│  - Normalization │     │  - Fallbacks     │     │  - Display opts  │
└────────┬─────────┘     └────────┬─────────┘     └────────┬─────────┘
         │                        │                        │
         └────────────────────────┼────────────────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │  VALUATION ENGINE       │
                    │  - Price × Quantity     │
                    │  - Allocation calc      │
                    │  - P&L calculation      │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │  ANALYTICS ENGINE       │
                    │  - Allocation analysis  │
                    │  - Risk flags           │
                    │  - Performance metrics  │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │  FORMATTER              │
                    │  - Table view           │
                    │  - JSON export          │
                    │  - CSV export           │
                    └─────────────────────────┘
```

### Workflow

1. **Load**: Parse portfolio JSON file and validate holdings
2. **Fetch**: Batch fetch prices from CoinGecko API
3. **Calculate**: Compute valuations and allocations
4. **Analyze**: Generate performance metrics and risk flags
5. **Format**: Output in requested format

---

## Progressive Disclosure Strategy

### Level 1: Portfolio Summary (Default)

```bash
python portfolio_tracker.py --portfolio holdings.json
```

Returns total value, 24h change, top 5 holdings.

### Level 2: Full Holdings List

```bash
python portfolio_tracker.py --portfolio holdings.json --holdings
```

Lists all holdings with prices and allocations.

### Level 3: Detailed Analysis

```bash
python portfolio_tracker.py --portfolio holdings.json --detailed
```

Full breakdown with P&L, risk flags, category allocation.

### Level 4: Export

```bash
python portfolio_tracker.py --portfolio holdings.json --format json --output portfolio.json
```

Machine-readable export for integration.

---

## Tool Permission Strategy

### Allowed Tools (Scoped)

```yaml
allowed-tools: Read, Write, Bash(crypto:portfolio-*)
```

| Tool | Scope | Purpose |
|------|-------|---------|
| Read | Unrestricted | Read portfolio files, config |
| Write | Unrestricted | Write export files |
| Bash | `crypto:portfolio-*` | Execute portfolio tracker scripts |

### Why These Tools

- **Read**: Load portfolio JSON and configuration
- **Write**: Save exported portfolio data
- **Bash(crypto:portfolio-*)**: Execute Python scripts for tracking

---

## Directory Structure

```
plugins/crypto/crypto-portfolio-tracker/
└── skills/
    └── tracking-crypto-portfolio/
        ├── PRD.md                    # Product requirements
        ├── ARD.md                    # This file
        ├── SKILL.md                  # Core instructions
        ├── scripts/
        │   ├── portfolio_tracker.py  # Main CLI entry point
        │   ├── portfolio_loader.py   # Portfolio file parsing
        │   ├── price_fetcher.py      # CoinGecko price fetching
        │   ├── valuation_engine.py   # Value calculations
        │   └── formatters.py         # Output formatting
        ├── references/
        │   ├── errors.md             # Error handling guide
        │   └── examples.md           # Usage examples
        └── config/
            └── settings.yaml         # Configuration options
```

---

## Data Flow Architecture

### Input

- Portfolio JSON file with holdings
- Optional: Configuration settings
- External: CoinGecko price API

### Processing Pipeline

```
Portfolio JSON
     │
     ├──► Parse and validate holdings
     │         │
     │         ▼
     │    Normalize coin symbols
     │    Calculate total quantity per coin
     │
     ├──► Fetch prices from CoinGecko
     │         │
     │         ▼
     │    Batch request (up to 250 coins)
     │    Cache results (60s TTL)
     │
     ├──► Calculate valuations
     │         │
     │         ▼
     │    Value = Quantity × Price
     │    Total = Sum(all values)
     │
     ├──► Calculate allocations
     │         │
     │         ▼
     │    Allocation = Value / Total × 100
     │    Flag if > threshold (default 25%)
     │
     ├──► Calculate P&L (if cost basis)
     │         │
     │         ▼
     │    Unrealized P&L = Value - (Quantity × Cost Basis)
     │    % Change = (Price - Cost Basis) / Cost Basis × 100
     │
     └──► Format and output
```

### Output Schema

```json
{
  "portfolio_name": "Main Portfolio",
  "total_value_usd": 125000.50,
  "change_24h": {
    "amount": 2500.25,
    "percent": 2.04
  },
  "holdings": [
    {
      "coin": "BTC",
      "coingecko_id": "bitcoin",
      "quantity": 0.5,
      "price_usd": 95000,
      "value_usd": 47500,
      "allocation_pct": 38.0,
      "change_24h_pct": 2.5,
      "cost_basis": 25000,
      "unrealized_pnl": 22500,
      "pnl_pct": 90.0
    }
  ],
  "allocation_by_category": {
    "Layer 1": 65.0,
    "DeFi": 20.0,
    "Stablecoins": 15.0
  },
  "risk_flags": [
    "BTC allocation > 25% threshold"
  ],
  "meta": {
    "timestamp": "2026-01-14T15:30:00Z",
    "prices_updated": "2026-01-14T15:29:45Z",
    "holdings_count": 12
  }
}
```

---

## API Integration Architecture

### CoinGecko API

```
Endpoint: https://api.coingecko.com/api/v3/coins/markets
Method: GET
Parameters:
  - vs_currency: usd
  - ids: bitcoin,ethereum,... (comma-separated)
  - order: market_cap_desc
  - sparkline: false
  - price_change_percentage: 24h,7d

Rate Limits:
  - Free tier: ~10-30 calls/minute
  - Batch up to 250 coins per request
```

### Request Strategy

```python
def fetch_prices(coin_ids: List[str]) -> Dict[str, Dict]:
    """Batch fetch prices with rate limiting."""
    # Split into batches of 250
    batches = [coin_ids[i:i+250] for i in range(0, len(coin_ids), 250)]

    results = {}
    for batch in batches:
        response = requests.get(
            f"{COINGECKO_API}/coins/markets",
            params={
                "vs_currency": "usd",
                "ids": ",".join(batch),
                "price_change_percentage": "24h,7d"
            }
        )
        for coin in response.json():
            results[coin["id"]] = {
                "price": coin["current_price"],
                "change_24h": coin["price_change_percentage_24h"],
                "change_7d": coin["price_change_percentage_7d"],
                "market_cap": coin["market_cap"]
            }
        time.sleep(0.5)  # Rate limit protection

    return results
```

---

## Portfolio File Schema

### Minimal Format

```json
{
  "holdings": [
    {"coin": "BTC", "quantity": 0.5},
    {"coin": "ETH", "quantity": 10}
  ]
}
```

### Full Format

```json
{
  "name": "Main Portfolio",
  "currency": "USD",
  "holdings": [
    {
      "coin": "BTC",
      "quantity": 0.5,
      "cost_basis": 25000,
      "acquired": "2024-01-15",
      "wallet": "Ledger",
      "notes": "DCA purchase"
    }
  ],
  "categories": {
    "BTC": "Layer 1",
    "ETH": "Layer 1",
    "UNI": "DeFi",
    "USDC": "Stablecoin"
  }
}
```

---

## Error Handling Strategy

### Error Categories

| Category | Examples | Strategy |
|----------|----------|----------|
| File Error | Portfolio not found, invalid JSON | Exit with clear error |
| API Error | Rate limit, timeout | Retry with backoff, then cache fallback |
| Data Error | Unknown coin symbol | Warn, skip coin, continue |
| Validation | Negative quantity | Reject with explanation |

### Graceful Degradation

```
Full Analysis (prices + allocations + P&L)
     │
     ├─► API unavailable → Use cached prices (if available)
     │         │
     │         ▼
     │    Show "stale prices" warning
     │
     ├─► Unknown coin → Skip coin, warn user
     │         │
     │         ▼
     │    Show "X coins not found" message
     │
     └─► No cost basis → Skip P&L calculation
               │
               ▼
          Show allocations only
```

---

## Coin Symbol Mapping

```python
# Map common symbols to CoinGecko IDs
SYMBOL_TO_ID = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "XRP": "ripple",
    "ADA": "cardano",
    "DOGE": "dogecoin",
    "DOT": "polkadot",
    "LINK": "chainlink",
    "AVAX": "avalanche-2",
    "MATIC": "matic-network",
    "UNI": "uniswap",
    "AAVE": "aave",
    "USDC": "usd-coin",
    "USDT": "tether",
    "DAI": "dai",
    # ... more mappings
}
```

---

## Performance & Scalability

### Performance Targets

| Metric | Target | Approach |
|--------|--------|----------|
| Full analysis | < 10s | Batch API requests |
| Summary only | < 5s | Minimal API call |
| Large portfolio (100+ coins) | < 30s | Batching + caching |

### Optimization Strategies

1. **Batch Requests**: Fetch up to 250 coins per API call
2. **Caching**: Cache prices with 60s TTL
3. **Lazy Loading**: Only fetch what's needed for output level
4. **Symbol Pre-mapping**: Resolve symbols before API call

---

## Testing Strategy

### Unit Tests

| Component | Test Cases |
|-----------|------------|
| PortfolioLoader | Valid JSON, invalid JSON, missing fields, negative quantities |
| PriceFetcher | API success, rate limit, timeout, unknown coin |
| ValuationEngine | Basic calc, zero quantity, zero price |
| AllocationAnalyzer | Normal distribution, single coin, empty portfolio |
| Formatters | All output formats, empty data, special characters |

### Integration Tests

- End-to-end with mock API
- Real API tests (daily CI with sample portfolio)
- Export format validation

### Sample Test Portfolio

```json
{
  "name": "Test Portfolio",
  "holdings": [
    {"coin": "BTC", "quantity": 1.0, "cost_basis": 50000},
    {"coin": "ETH", "quantity": 10, "cost_basis": 2500},
    {"coin": "SOL", "quantity": 100, "cost_basis": 100},
    {"coin": "USDC", "quantity": 10000}
  ]
}
```

---

## Security & Compliance

### Security Considerations

- **No Private Keys**: Portfolio files contain quantities only
- **No Exchange APIs**: No authentication credentials stored
- **Local Data**: All portfolio data stays local
- **Public API Only**: CoinGecko is public, no secrets needed

### Data Privacy

- Portfolio files should not be committed to git
- Add `*.portfolio.json` to `.gitignore`
- No telemetry or data collection
