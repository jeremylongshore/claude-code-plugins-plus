---
name: tracking-crypto-portfolio
description: |
  Track cryptocurrency portfolio with real-time valuations, allocation analysis, and P&L tracking.
  Use when checking portfolio value, viewing holdings breakdown, analyzing allocations, or exporting portfolio data.
  Trigger with phrases like "show my portfolio", "check crypto holdings", "portfolio allocation", "track my crypto", or "export portfolio".

allowed-tools: Read, Write, Bash(crypto:portfolio-*)
version: 2.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---

# Tracking Crypto Portfolio

## Overview

This skill provides comprehensive cryptocurrency portfolio tracking with:

- **Real-Time Valuations**: Current prices from CoinGecko
- **Holdings Breakdown**: Quantity, value, and allocation per asset
- **P&L Tracking**: Unrealized gains/losses with cost basis
- **Allocation Analysis**: Category breakdown and concentration flags
- **Multiple Export Formats**: Table, JSON, CSV

**Key Capabilities:**
- Track holdings across multiple assets
- Calculate portfolio total value in USD
- Identify overweight positions (concentration risk)
- Export for analysis tools and tax reporting

## Prerequisites

Before using this skill, ensure:

1. **Python 3.8+** is installed
2. **requests** library is available: `pip install requests`
3. Internet connectivity for CoinGecko API access
4. A portfolio JSON file with your holdings

### Portfolio File Format

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

## Instructions

### Step 1: Assess User Intent

Determine what portfolio information the user needs:
- **Quick check**: Total value and top holdings
- **Holdings list**: Full breakdown of all positions
- **Detailed analysis**: Allocations, P&L, risk flags
- **Export**: JSON or CSV for external tools

### Step 2: Execute Portfolio Tracking

Run the tracker with appropriate options:

```bash
# Quick portfolio summary
python ${CLAUDE_SKILL_DIR}/scripts/portfolio_tracker.py --portfolio holdings.json

# Full holdings breakdown
python ${CLAUDE_SKILL_DIR}/scripts/portfolio_tracker.py --portfolio holdings.json --holdings

# Detailed analysis with P&L and allocations
python ${CLAUDE_SKILL_DIR}/scripts/portfolio_tracker.py --portfolio holdings.json --detailed

# Export to JSON
python ${CLAUDE_SKILL_DIR}/scripts/portfolio_tracker.py --portfolio holdings.json --format json --output portfolio_export.json

# Export to CSV
python ${CLAUDE_SKILL_DIR}/scripts/portfolio_tracker.py --portfolio holdings.json --format csv --output portfolio.csv
```

### Step 3: Present Results

Format and explain the portfolio data:
- Show total portfolio value prominently
- Highlight 24h and 7d changes
- Explain allocation percentages
- Flag any concentration risks
- For detailed mode, explain P&L calculations

### Command-Line Options

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

### Allocation Thresholds

By default, positions > 25% allocation are flagged:

| Allocation | Risk Level | Action |
|------------|------------|--------|
| < 10% | Low | Normal position |
| 10-25% | Medium | Monitor closely |
| 25-50% | High | Consider rebalancing |
| > 50% | Very High | Significant concentration risk |

## Output

### Table Format (Default)
```
==============================================================================
  CRYPTO PORTFOLIO TRACKER                          Updated: 2026-01-14 15:30
==============================================================================

  PORTFOLIO SUMMARY: My Portfolio
------------------------------------------------------------------------------
  Total Value:    $125,450.00 USD
  24h Change:     +$2,540.50 (+2.07%)
  7d Change:      +$8,125.00 (+6.92%)
  Holdings:       8 assets

  TOP HOLDINGS
------------------------------------------------------------------------------
  Coin     Quantity      Price         Value      Alloc   24h
  BTC      0.500     $95,000.00   $47,500.00    37.9%   +2.5%
  ETH      10.000     $3,200.00   $32,000.00    25.5%   +1.8%
  SOL      100.000      $180.00   $18,000.00    14.4%   +4.2%

  ⚠ CONCENTRATION WARNING: BTC (37.9%) exceeds 25% threshold

==============================================================================
```

### JSON Format
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

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

| Error | Cause | Solution |
|-------|-------|----------|
| Portfolio file not found | Invalid path | Check file path exists |
| Invalid JSON | Malformed file | Validate JSON syntax |
| Coin not found | Unknown symbol | Check symbol spelling, use standard symbols |
| API rate limited | Too many requests | Wait and retry, use caching |

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

### Quick Examples

```bash
# Basic portfolio check
python ${CLAUDE_SKILL_DIR}/scripts/portfolio_tracker.py --portfolio ~/crypto/holdings.json

# Show all holdings sorted by allocation
python ${CLAUDE_SKILL_DIR}/scripts/portfolio_tracker.py --portfolio holdings.json --holdings --sort allocation

# Detailed analysis with 15% threshold
python ${CLAUDE_SKILL_DIR}/scripts/portfolio_tracker.py --portfolio holdings.json --detailed --threshold 15

# Export for tax software
python ${CLAUDE_SKILL_DIR}/scripts/portfolio_tracker.py --portfolio holdings.json --format csv --output tax_export.csv

# JSON export for trading bot
python ${CLAUDE_SKILL_DIR}/scripts/portfolio_tracker.py --portfolio holdings.json --format json --output portfolio_data.json
```

## Resources

- **CoinGecko API**: https://www.coingecko.com/en/api - Free crypto market data
- **Portfolio Schema**: See PRD.md for complete portfolio file format
- **Configuration**: See `${CLAUDE_SKILL_DIR}/config/settings.yaml` for options
- See `${CLAUDE_SKILL_DIR}/references/examples.md` for integration examples
