---
name: calculating-crypto-taxes
description: |
  Calculate cryptocurrency tax obligations with cost basis tracking, capital gains computation, and Form 8949 generation.
  Use when calculating crypto taxes, generating tax reports, comparing cost basis methods, or identifying taxable events.
  Trigger with phrases like "calculate crypto taxes", "generate tax report", "cost basis FIFO", "capital gains", "Form 8949", or "crypto taxable events".

allowed-tools: Read, Write, Bash(crypto:tax-*)
version: 2.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---

# Calculating Crypto Taxes

## Overview

Calculate cryptocurrency tax obligations from transaction history. Supports multiple cost basis methods (FIFO, LIFO, HIFO), identifies taxable events (trades, staking, airdrops), and generates Form 8949 compatible reports.

**DISCLAIMER**: This tool provides informational calculations only, not tax advice. Consult a qualified tax professional for your specific situation.

## Prerequisites

Before using this skill, ensure you have:

- Transaction history exported as CSV from your exchanges (Coinbase, Binance, Kraken, etc.)
- Python 3.8+ installed
- Understanding of your tax jurisdiction's crypto rules

## Instructions

### Step 1: Prepare Transaction Data

Export your transaction history from each exchange as CSV. Supported formats:

| Exchange | Export Location |
|----------|-----------------|
| Coinbase | Reports → Tax documents → Transaction history CSV |
| Binance | Orders → Trade History → Export |
| Kraken | History → Export |
| Generic | See `${CLAUDE_SKILL_DIR}/references/exchange_formats.md` for column mapping |

### Step 2: Run Basic Tax Calculation

Execute the tax calculator with your transaction file:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/tax_calculator.py --transactions your_trades.csv --year 2025
```

This uses FIFO (IRS default) and outputs:
- Total capital gains/losses
- Short-term vs long-term breakdown
- Summary of taxable events

### Step 3: Choose Cost Basis Method

Compare different methods to understand tax implications:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/tax_calculator.py --transactions trades.csv --compare-methods
```

Or specify a method:

| Method | Flag | Description |
|--------|------|-------------|
| FIFO | `--method fifo` | First In First Out (IRS default) |
| LIFO | `--method lifo` | Last In First Out |
| HIFO | `--method hifo` | Highest In First Out (minimize gains) |

### Step 4: Generate Tax Report

Create Form 8949 compatible CSV:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/tax_calculator.py --transactions trades.csv --method fifo --year 2025 --output form_8949.csv --format csv
```

Output includes:
- Description of property
- Date acquired
- Date sold
- Proceeds
- Cost basis
- Gain or loss

### Step 5: Handle Income Events (Optional)

For staking, airdrops, or mining income:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/tax_calculator.py --transactions all_events.csv --income-report
```

This identifies:
- Staking rewards (valued at receipt)
- Airdrops (valued at receipt)
- Mining income
- DeFi yield

### Step 6: Multi-Exchange Consolidation

Combine multiple exchange exports:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/tax_calculator.py --transactions coinbase.csv binance.csv kraken.csv --year 2025
```

The tool:
- Merges all transactions
- Sorts by date
- Calculates unified cost basis
- Handles transfers between exchanges

## Output

### Tax Report (Form 8949)
```
============================================================
  CRYPTO TAX REPORT - 2025
============================================================

SHORT-TERM CAPITAL GAINS/LOSSES (< 1 year)
------------------------------------------------------------
Description      Acquired    Sold        Proceeds    Cost      Gain/Loss
0.5 BTC          03/15/25    06/20/25    $52,500     $47,500   $5,000
2.0 ETH          04/01/25    08/15/25    $7,200      $6,400    $800
------------------------------------------------------------
Short-term Total:                                              $5,800

LONG-TERM CAPITAL GAINS/LOSSES (>= 1 year)
------------------------------------------------------------
Description      Acquired    Sold        Proceeds    Cost      Gain/Loss
1.0 BTC          01/10/24    02/15/25    $95,000     $42,000   $53,000
------------------------------------------------------------
Long-term Total:                                               $53,000

============================================================
SUMMARY
------------------------------------------------------------
Total Proceeds:           $154,700
Total Cost Basis:         $95,900
Net Capital Gain:         $58,800

Short-term Gains:         $5,800
Long-term Gains:          $53,000
============================================================
```

### Income Report
```
CRYPTO INCOME - 2025
------------------------------------------------------------
Type            Date        Asset    Quantity    FMV (USD)
Staking         01/15/25    ETH      0.05        $160.00
Staking         02/15/25    ETH      0.05        $175.00
Airdrop         03/01/25    ARB      100         $150.00
------------------------------------------------------------
Total Income:                                     $485.00
```

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

Common issues:
- **Missing columns**: Verify CSV format matches exchange template
- **Unknown transaction type**: Review and manually categorize
- **Insufficient lots**: Check for missing buy transactions

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed usage examples.

### Quick Examples

**Basic tax calculation**:
```bash
python tax_calculator.py --transactions trades.csv --year 2025
```

**HIFO to minimize gains**:
```bash
python tax_calculator.py --transactions trades.csv --method hifo --year 2025
```

**JSON output for processing**:
```bash
python tax_calculator.py --transactions trades.csv --format json --output tax_data.json
```

**Verbose with lot details**:
```bash
python tax_calculator.py --transactions trades.csv --verbose --show-lots
```

## Configuration

Settings in `${CLAUDE_SKILL_DIR}/config/settings.yaml`:

- **Default method**: Cost basis method (fifo, lifo, hifo)
- **Tax year start**: January 1 (US) or fiscal year
- **Exchange formats**: Column mappings for CSV parsing
- **Holding period**: Days for long-term (default: 365)

## Resources

- IRS Virtual Currency Guidance: https://www.irs.gov/businesses/small-businesses-self-employed/virtual-currencies
- Form 8949 Instructions: https://www.irs.gov/instructions/i8949
- CoinGecko API for historical prices
