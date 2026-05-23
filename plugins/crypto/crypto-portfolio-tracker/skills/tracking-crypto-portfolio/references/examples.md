# Usage Examples

Comprehensive examples for the Crypto Portfolio Tracker.

---

## Quick Start Examples

### 1. Basic Portfolio Check

```bash
python portfolio_tracker.py --portfolio holdings.json
```

Output:

```
==============================================================================
  CRYPTO PORTFOLIO TRACKER                          2026-01-14 15:30 UTC
==============================================================================

  PORTFOLIO SUMMARY: My Portfolio
------------------------------------------------------------------------------
  Total Value:    $125,450.00 USD
  24h Change:     +$2,540.50 (+2.07%)
  7d Change:      +$8,125.00 (+6.92%)
  Holdings:       8 assets

  TOP HOLDINGS
------------------------------------------------------------------------------
  Coin     Quantity      Price         Value      Alloc     24h
  BTC      0.5000    $95,000.00   $47,500.00    37.9%   +2.5%
  ETH     10.0000     $3,200.00   $32,000.00    25.5%   +1.8%
  SOL    100.0000       $180.00   $18,000.00    14.4%   +4.2%
  ... and 5 more holdings

==============================================================================
```

---

### 2. Show All Holdings

```bash
python portfolio_tracker.py --portfolio holdings.json --holdings
```

Displays complete breakdown of all positions instead of just top 5.

---

### 3. Detailed Analysis with P&L

```bash
python portfolio_tracker.py --portfolio holdings.json --detailed
```

Shows full analysis including:

- Unrealized P&L per position
- Total portfolio P&L
- Category allocation breakdown
- All concentration warnings

---

## Sorting Options

### 4. Sort by Allocation

```bash
python portfolio_tracker.py --portfolio holdings.json --holdings --sort allocation
```

Shows holdings sorted by allocation percentage (highest first).

### 5. Sort by 24h Change

```bash
python portfolio_tracker.py --portfolio holdings.json --holdings --sort change
```

Shows holdings sorted by 24h price change (best performers first).

### 6. Sort Alphabetically

```bash
python portfolio_tracker.py --portfolio holdings.json --holdings --sort name
```

Shows holdings sorted alphabetically by coin symbol.

---

## Export Examples

### 7. JSON Export

```bash
python portfolio_tracker.py --portfolio holdings.json --format json
```

Output:

```json
{
  "portfolio_name": "My Portfolio",
  "total_value_usd": 125450.00,
  "change_24h": {
    "amount": 2540.50,
    "percent": 2.07
  },
  "holdings": [
    {
      "coin": "BTC",
      "quantity": 0.5,
      "price_usd": 95000,
      "value_usd": 47500,
      "allocation_pct": 37.9,
      "change_24h_pct": 2.5
    }
  ],
  "meta": {
    "timestamp": "2026-01-14T15:30:00Z"
  }
}
```

---

### 8. CSV Export

```bash
python portfolio_tracker.py --portfolio holdings.json --format csv --output portfolio.csv
```

Creates spreadsheet-compatible file with columns:

- coin, quantity, price_usd, value_usd, allocation_pct, change_24h_pct, etc.

---

### 9. JSON Export to File

```bash
python portfolio_tracker.py --portfolio holdings.json --format json --output portfolio_data.json
```

Saves JSON output to file for programmatic use.

---

## Threshold Configuration

### 10. Custom Concentration Threshold

```bash
python portfolio_tracker.py --portfolio holdings.json --threshold 15
```

Flags any position > 15% allocation (default is 25%).

### 11. Strict Threshold

```bash
python portfolio_tracker.py --portfolio holdings.json --threshold 10 --holdings
```

Shows concentration warnings for positions > 10%.

---

## Portfolio File Examples

### 12. Minimal Portfolio

```json
{
  "holdings": [
    {"coin": "BTC", "quantity": 0.5},
    {"coin": "ETH", "quantity": 10},
    {"coin": "SOL", "quantity": 100}
  ]
}
```

### 13. Portfolio with Cost Basis

```json
{
  "name": "Main Portfolio",
  "holdings": [
    {"coin": "BTC", "quantity": 0.5, "cost_basis": 50000},
    {"coin": "ETH", "quantity": 10, "cost_basis": 2500},
    {"coin": "SOL", "quantity": 100, "cost_basis": 100}
  ]
}
```

### 14. Full Portfolio with Categories

```json
{
  "name": "Diversified Portfolio",
  "holdings": [
    {"coin": "BTC", "quantity": 0.5, "cost_basis": 50000, "wallet": "Ledger"},
    {"coin": "ETH", "quantity": 10, "cost_basis": 2500, "wallet": "Ledger"},
    {"coin": "SOL", "quantity": 100, "cost_basis": 100, "wallet": "Phantom"},
    {"coin": "LINK", "quantity": 500, "cost_basis": 15, "wallet": "MetaMask"},
    {"coin": "USDC", "quantity": 10000, "wallet": "Coinbase"}
  ],
  "categories": {
    "BTC": "Layer 1",
    "ETH": "Layer 1",
    "SOL": "Layer 1",
    "LINK": "DeFi",
    "USDC": "Stablecoin"
  }
}
```

---

## Integration Examples

### 15. Daily Portfolio Snapshot

```bash
# Save daily snapshot with timestamp
DATE=$(date +%Y-%m-%d)
python portfolio_tracker.py --portfolio holdings.json --format json --output "snapshots/${DATE}.json"
```

### 16. Cron Job for Hourly Tracking

```bash
# Add to crontab
0 * * * * cd /path/to/skill && python portfolio_tracker.py --portfolio ~/holdings.json --format json --output ~/snapshots/$(date +\%Y\%m\%d_\%H).json
```

### 17. Extract Total Value for Scripts

```bash
# Get total value for shell script
TOTAL=$(python portfolio_tracker.py --portfolio holdings.json --format json | jq -r '.total_value_usd')
echo "Portfolio value: $${TOTAL}"
```

### 18. Check for Rebalancing

```bash
# Flag if any position > 30%
python portfolio_tracker.py --portfolio holdings.json --threshold 30 --format json | jq '.risk_flags'
```

---

## Multiple Portfolios

### 19. Compare Portfolios

```bash
# Run for each portfolio
python portfolio_tracker.py --portfolio main.json --format json > main_value.json
python portfolio_tracker.py --portfolio trading.json --format json > trading_value.json

# Compare totals
jq -s '.[0].total_value_usd + .[1].total_value_usd' main_value.json trading_value.json
```

### 20. Aggregate Multiple Wallets

Create a single portfolio file with wallet tracking:

```json
{
  "name": "All Wallets",
  "holdings": [
    {"coin": "BTC", "quantity": 0.3, "wallet": "Ledger"},
    {"coin": "BTC", "quantity": 0.2, "wallet": "Coinbase"},
    {"coin": "ETH", "quantity": 5, "wallet": "Ledger"},
    {"coin": "ETH", "quantity": 5, "wallet": "MetaMask"}
  ]
}
```

The tracker automatically aggregates holdings for the same coin.

---

## Debugging

### 21. Verbose Mode

```bash
python portfolio_tracker.py --portfolio holdings.json -v
```

Shows detailed progress:

- Loading portfolio file
- Fetching prices for X coins
- API responses and cache status
- Any warnings or errors

### 22. Test Price Fetching

```bash
python price_fetcher.py BTC ETH SOL -v
```

Tests price API independently.

### 23. Test Portfolio Loading

```bash
python portfolio_loader.py holdings.json -v
```

Validates portfolio file and shows any skipped entries.

---

## Output Interpretation

### Reading the Summary

| Field | Meaning |
|-------|---------|
| Total Value | Sum of all holdings at current prices |
| 24h Change | Portfolio value change in last 24 hours |
| 7d Change | Portfolio value change in last 7 days |
| Holdings | Number of unique assets |

### Reading Holdings Table

| Column | Meaning |
|--------|---------|
| Coin | Asset symbol |
| Quantity | Amount held |
| Price | Current USD price |
| Value | Quantity × Price |
| Alloc | Percentage of total portfolio |
| 24h | Price change in last 24 hours |
| P&L | Unrealized gain/loss (with --detailed) |

### Risk Flags

- **Exceeds X% threshold**: Single asset concentration risk
- **Majority of portfolio**: One asset > 50%
- **Limited diversification**: < 3 assets

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
