# Calculating Crypto Taxes - Implementation Reference

## Detailed Output Formats

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

## Configuration

Settings in `${CLAUDE_SKILL_DIR}/config/settings.yaml`:

- **Default method**: Cost basis method (fifo, lifo, hifo)
- **Tax year start**: January 1 (US) or fiscal year
- **Exchange formats**: Column mappings for CSV parsing
- **Holding period**: Days for long-term (default: 365)

## Advanced Usage

### Verbose with Lot Details
```bash
python tax_calculator.py --transactions trades.csv --verbose --show-lots
```

### JSON Output for Processing
```bash
python tax_calculator.py --transactions trades.csv --format json --output tax_data.json
```

### Multi-Exchange Consolidation Details

When combining multiple exchange exports, the tool:
- Merges all transactions chronologically
- Calculates unified cost basis across exchanges
- Handles transfers between exchanges (matching withdrawals to deposits)
- Identifies orphaned transfers for manual review

## IRS Guidance Reference

- IRS Virtual Currency Guidance: https://www.irs.gov/businesses/small-businesses-self-employed/virtual-currencies
- Form 8949 Instructions: https://www.irs.gov/instructions/i8949
- CoinGecko API for historical prices
