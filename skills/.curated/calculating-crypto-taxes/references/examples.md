# Usage Examples

Comprehensive examples for the Crypto Tax Calculator.

---

## Quick Start Examples

### 1. Basic Tax Report

```bash
python tax_calculator.py --transactions trades.csv --year 2025
```

Output:

```
============================================================
  CRYPTO TAX REPORT - 2025
  Method: FIFO  |  Generated: 2026-01-14 15:30
============================================================

  SHORT-TERM CAPITAL GAINS/LOSSES (< 1 year)
------------------------------------------------------------
  Description    Acquired     Sold         Proceeds       Cost    Gain/Loss
  0.5000 BTC     06/15/24     01/20/25    $47,500.00  $32,500.00   $15,000.00
  2.0000 ETH     08/01/24     12/15/24     $7,200.00   $6,400.00      $800.00
------------------------------------------------------------
  Short-term Total:                                              $15,800.00

  LONG-TERM CAPITAL GAINS/LOSSES (>= 1 year)
------------------------------------------------------------
  Description    Acquired     Sold         Proceeds       Cost    Gain/Loss
  0.7500 BTC     01/15/24     01/20/25    $71,250.00  $30,000.00   $41,250.00
------------------------------------------------------------
  Long-term Total:                                               $41,250.00

============================================================
  SUMMARY
------------------------------------------------------------
  Total Proceeds:           $125,950.00
  Total Cost Basis:          $68,900.00
  Net Capital Gain/Loss:     $57,050.00

  Short-term Gains:          $15,800.00
  Short-term Losses:              $0.00
  Long-term Gains:           $41,250.00
  Long-term Losses:               $0.00
============================================================
```

---

### 2. Compare Cost Basis Methods

```bash
python tax_calculator.py --transactions trades.csv --compare-methods
```

Output:

```
======================================================================
  COST BASIS METHOD COMPARISON
======================================================================

Method     Net Gain/Loss     ST Gain      LT Gain
----------------------------------------------------------------------
FIFO           $57,050.00   $15,800.00   $41,250.00
LIFO           $52,050.00   $20,800.00   $31,250.00
HIFO           $47,050.00   $10,800.00   $36,250.00

======================================================================
  Lowest tax liability: HIFO

  Note: FIFO is the IRS default. Other methods may require
  consistent application and adequate records.
======================================================================
```

---

### 3. Generate Form 8949 CSV

```bash
python tax_calculator.py --transactions trades.csv --year 2025 --format csv --output form_8949.csv
```

Creates:

```csv
Description of Property,Date Acquired,Date Sold or Disposed,Proceeds (Sales Price),Cost or Other Basis,Gain or (Loss),Short/Long Term,Holding Period (Days)
0.75000000 BTC,01/15/2024,01/20/2025,71250.00,30000.00,41250.00,Long-term,371
0.50000000 BTC,06/15/2024,01/20/2025,47500.00,32500.00,15000.00,Short-term,219
2.00000000 ETH,08/01/2024,12/15/2024,7200.00,6400.00,800.00,Short-term,136

SUMMARY
Total Proceeds,125950.00
Total Cost Basis,68900.00
Net Gain/Loss,57050.00
Short-term Gain,15800.00
Short-term Loss,0.00
Long-term Gain,41250.00
Long-term Loss,0.00
Method,FIFO
Tax Year,2025
```

---

## Cost Basis Method Examples

### 4. FIFO (First In First Out)

```bash
python tax_calculator.py --transactions trades.csv --method fifo
```

Sells oldest lots first. IRS default method.

**Example**: You bought:

- Lot 1: 1 BTC @ $40,000 (Jan 2024)
- Lot 2: 0.5 BTC @ $65,000 (Jun 2024)

When you sell 0.75 BTC, FIFO sells from Lot 1 first.

---

### 5. LIFO (Last In First Out)

```bash
python tax_calculator.py --transactions trades.csv --method lifo
```

Sells newest lots first. May result in more short-term gains.

**Same example**: LIFO would sell:

- 0.5 BTC from Lot 2 (Jun 2024)
- 0.25 BTC from Lot 1 (Jan 2024)

---

### 6. HIFO (Highest In First Out)

```bash
python tax_calculator.py --transactions trades.csv --method hifo
```

Sells highest cost lots first. Minimizes gains but requires tracking.

**Same example**: HIFO would sell:

- 0.5 BTC from Lot 2 ($65,000 basis - higher)
- 0.25 BTC from Lot 1 ($40,000 basis - lower)

---

## Income Report Examples

### 7. Staking and Airdrop Income

```bash
python tax_calculator.py --transactions all_events.csv --income-report
```

Output:

```
======================================================================
  CRYPTO INCOME REPORT
======================================================================

Type         Date         Asset    Quantity     FMV (USD)
----------------------------------------------------------------------
staking      2024-01-15   ETH        0.0500       $160.00
staking      2024-02-15   ETH        0.0500       $175.00
staking      2024-03-15   ETH        0.0500       $180.00
airdrop      2024-03-01   ARB      100.0000       $150.00
mining       2024-04-01   BTC        0.0010        $65.00
----------------------------------------------------------------------

  SUMMARY BY TYPE
----------------------------------------------------------------------
  Staking          3 events         $515.00
  Airdrop          1 events         $150.00
  Mining           1 events          $65.00
----------------------------------------------------------------------
  TOTAL            5 events         $730.00

======================================================================
  Income is taxed as ordinary income at receipt fair market value.
======================================================================
```

---

## Multi-Exchange Examples

### 8. Combine Multiple Exchanges

```bash
python tax_calculator.py --transactions coinbase.csv binance.csv kraken.csv --year 2025
```

Merges all transactions, sorts chronologically, and calculates unified cost basis.

---

### 9. Specify Exchange Format

```bash
python tax_calculator.py --transactions trades.csv --exchange coinbase
```

Use when auto-detection fails or for non-standard exports.

---

## Output Format Examples

### 10. JSON Output

```bash
python tax_calculator.py --transactions trades.csv --format json
```

Output:

```json
{
  "disposals": [
    {
      "date_acquired": "2024-01-15T00:00:00",
      "date_sold": "2025-01-20T00:00:00",
      "asset": "BTC",
      "quantity": 0.75,
      "proceeds": 71250.0,
      "cost_basis": 30000.0,
      "gain_loss": 41250.0,
      "is_long_term": true,
      "holding_days": 371,
      "lot_id": 1
    }
  ],
  "summary": {
    "total_proceeds": 71250.0,
    "total_cost_basis": 30000.0,
    "net_gain_loss": 41250.0,
    "short_term_gain": 0.0,
    "short_term_loss": 0.0,
    "long_term_gain": 41250.0,
    "long_term_loss": 0.0
  },
  "method": "fifo"
}
```

---

### 11. Show Lot Details

```bash
python tax_calculator.py --transactions trades.csv --show-lots
```

Adds remaining lot inventory to output:

```
  REMAINING LOT INVENTORY
------------------------------------------------------------
  BTC:
    Lot #1: 0.2500 @ $40,000.00 (acquired 2024-01-15)
    Lot #2: 0.5000 @ $65,000.00 (acquired 2024-06-15)
  ETH:
    Lot #3: 8.0000 @ $3,200.00 (acquired 2024-08-01)
```

---

## Year Filtering Examples

### 12. Specific Tax Year

```bash
python tax_calculator.py --transactions trades.csv --year 2024
```

Only includes transactions with sale dates in 2024.

---

### 13. All Years

```bash
python tax_calculator.py --transactions trades.csv
```

Processes all transactions regardless of date.

---

## Portfolio File Examples

### 14. Minimal CSV Format

```csv
date,type,asset,quantity,price
2024-01-15,buy,BTC,1.0,40000
2024-06-15,buy,BTC,0.5,65000
2025-01-20,sell,BTC,0.75,95000
```

---

### 15. Full CSV with All Fields

```csv
date,type,asset,quantity,price,fee,notes
2024-01-15T10:30:00Z,buy,BTC,1.0,40000,10,Coinbase purchase
2024-06-15T14:22:00Z,buy,BTC,0.5,65000,5,DCA buy
2024-08-01T09:00:00Z,buy,ETH,10,3200,8,Ledger transfer in
2024-12-15T16:45:00Z,sell,ETH,2,3600,4,Partial profit take
2025-01-20T11:00:00Z,sell,BTC,0.75,95000,15,Year-end sale
```

---

### 16. With Income Events

```csv
date,type,asset,quantity,price
2024-01-15,staking,ETH,0.05,3200
2024-02-15,staking,ETH,0.05,3500
2024-03-01,airdrop,ARB,100,1.50
2024-06-15,buy,BTC,0.5,65000
2024-12-15,sell,BTC,0.25,95000
```

---

## Integration Examples

### 17. Automated Tax Snapshot

```bash
# Save annual tax report
YEAR=$(date +%Y)
python tax_calculator.py \
  --transactions ~/crypto/trades_${YEAR}.csv \
  --year ${YEAR} \
  --format csv \
  --output ~/taxes/crypto_${YEAR}_form8949.csv
```

---

### 18. Extract Summary for Scripts

```bash
# Get net gain/loss for shell script
NET_GAIN=$(python tax_calculator.py \
  --transactions trades.csv \
  --format json | jq -r '.summary.net_gain_loss')
echo "Net capital gain: $${NET_GAIN}"
```

---

### 19. Tax Optimization Analysis

```bash
# Compare methods and save analysis
python tax_calculator.py \
  --transactions trades.csv \
  --compare-methods \
  --format json \
  --output tax_optimization.json
```

---

## Debugging Examples

### 20. Verbose Mode

```bash
python tax_calculator.py --transactions trades.csv --verbose
```

Shows:

- File loading progress
- Detected exchange format
- Lot creation/disposal details
- Skipped transactions with reasons

---

### 21. Test Transaction Parsing

```bash
python transaction_parser.py trades.csv coinbase
```

Parses and displays transactions without calculating taxes.

---

### 22. Test Cost Basis Engine

```bash
python cost_basis_engine.py
```

Runs internal tests on lot tracking and disposal calculations.

---

## Output Interpretation

### Reading the Tax Report

| Field | Meaning |
|-------|---------|
| Description | Quantity and asset sold |
| Date Acquired | When the asset was purchased |
| Date Sold | When the asset was disposed |
| Proceeds | Sale price minus fees |
| Cost Basis | Purchase price plus fees |
| Gain/Loss | Proceeds minus Cost Basis |

### Short-term vs Long-term

| Holding Period | Classification | Tax Rate |
|----------------|----------------|----------|
| < 1 year | Short-term | Ordinary income rates |
| >= 1 year | Long-term | Preferential capital gains rates |

### Cost Basis Methods

| Method | Best For | Risk |
|--------|----------|------|
| FIFO | Simplicity, compliance | May have higher gains |
| LIFO | Rising markets | More short-term gains |
| HIFO | Tax minimization | Requires detailed records |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
