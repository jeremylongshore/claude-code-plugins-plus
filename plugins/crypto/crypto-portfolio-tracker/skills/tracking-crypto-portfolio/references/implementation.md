# Tracking Crypto Portfolio - Implementation Reference

## Portfolio File Format

Create a portfolio file (e.g., `holdings.json`):

```json
{
  "name": "My Portfolio",
  "holdings": [
    {"coin": "BTC", "quantity": 0.5, "cost_basis": 25000},
    {"coin": "ETH", "quantity": 10, "cost_basis": 2000},
    {"coin": "SOL", "quantity": 100}
  ]
}
```

Fields:
- `coin`: Symbol (BTC, ETH, etc.) - **required**
- `quantity`: Amount held - **required**
- `cost_basis`: Average purchase price per coin (optional, for P&L)
- `acquired`: Date acquired (optional, for records)

## Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--portfolio` | Path to portfolio JSON file | Required |
| `--holdings` | Show all holdings breakdown | false |
| `--detailed` | Full analysis with P&L | false |
| `--sort` | Sort by: value, allocation, name, change | value |
| `--format` | Output format (table, json, csv) | table |
| `--output` | Output file path | stdout |
| `--threshold` | Allocation warning threshold | 25% |
| `--verbose` | Enable verbose output | false |

## Allocation Thresholds

By default, positions > 25% allocation are flagged:

| Allocation | Risk Level | Action |
|------------|------------|--------|
| < 10% | Low | Normal position |
| 10-25% | Medium | Monitor closely |
| 25-50% | High | Consider rebalancing |
| > 50% | Very High | Significant concentration risk |

## JSON Output Format

```json
{
  "portfolio_name": "My Portfolio",
  "total_value_usd": 125450.00,
  "change_24h": {"amount": 2540.50, "percent": 2.07},
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
    "timestamp": "2026-01-14T15:30:00Z",
    "holdings_count": 8
  }
}
```

## Advanced Examples

```bash
# Show all holdings sorted by allocation
python ${CLAUDE_SKILL_DIR}/scripts/portfolio_tracker.py --portfolio holdings.json --holdings --sort allocation

# Detailed analysis with 15% threshold
python ${CLAUDE_SKILL_DIR}/scripts/portfolio_tracker.py --portfolio holdings.json --detailed --threshold 15

# Export for tax software
python ${CLAUDE_SKILL_DIR}/scripts/portfolio_tracker.py --portfolio holdings.json --format csv --output tax_export.csv

# JSON export for trading bot
python ${CLAUDE_SKILL_DIR}/scripts/portfolio_tracker.py --portfolio holdings.json --format json --output portfolio_data.json
```
