# Exchange CSV Format Reference

Documentation for supported exchange CSV formats.

---

## Supported Exchanges

| Exchange | Auto-Detect | Price Included | Notes |
|----------|-------------|----------------|-------|
| Coinbase | Yes | Yes | Standard transaction history |
| Binance | Yes | No | Requires price lookup |
| Kraken | Yes | No | Symbol normalization needed |
| Gemini | Yes | Yes | Standard format |
| Generic | Fallback | Optional | Configurable columns |

---

## Coinbase

### Export Location

Reports → Tax documents → Transaction history CSV

### Expected Columns

| Column | Description | Required |
|--------|-------------|----------|
| Timestamp | ISO 8601 format | Yes |
| Transaction Type | buy, sell, send, receive, etc. | Yes |
| Asset | BTC, ETH, etc. | Yes |
| Quantity Transacted | Amount | Yes |
| Spot Price at Transaction | USD price | Yes |
| Fees and/or Spread | Transaction fees | No |
| Total (inclusive of fees) | Total cost/proceeds | No |

### Sample CSV

```csv
Timestamp,Transaction Type,Asset,Quantity Transacted,Spot Price at Transaction,Fees and/or Spread,Total (inclusive of fees and/or spread)
2024-01-15T10:30:00Z,Buy,BTC,0.5,40000,10,20010
2024-06-15T14:22:00Z,Sell,BTC,0.25,65000,5,16245
```

### Transaction Types

- Buy
- Sell
- Send
- Receive
- Advanced Trade Buy
- Advanced Trade Sell
- Rewards Income
- Staking Income
- Coinbase Earn
- Learning Reward
- Convert

---

## Binance

### Export Location

Orders → Trade History → Export

### Expected Columns

| Column | Description | Required |
|--------|-------------|----------|
| Date(UTC) | DateTime format | Yes |
| Operation | Transaction type | Yes |
| Coin | Asset symbol | Yes |
| Change | Amount (positive/negative) | Yes |

### Sample CSV

```csv
Date(UTC),Operation,Coin,Change
2024-01-15 10:30:00,Buy,BTC,0.5
2024-06-15 14:22:00,Sell,BTC,-0.25
```

### Notes

- **No price column**: Requires manual price lookup
- **Change column**: Positive for buys, negative for sells
- **Multiple operations**: May include deposits, withdrawals, dust

---

## Kraken

### Export Location

History → Export

### Expected Columns

| Column | Description | Required |
|--------|-------------|----------|
| time | DateTime with microseconds | Yes |
| type | Transaction type | Yes |
| asset | Asset symbol (may need mapping) | Yes |
| amount | Quantity | Yes |
| fee | Transaction fee | No |

### Sample CSV

```csv
time,type,asset,amount,fee
2024-01-15 10:30:00.000000,buy,XXBT,0.5,0.001
2024-06-15 14:22:00.000000,sell,XXBT,0.25,0.0005
```

### Symbol Mappings

| Kraken | Standard |
|--------|----------|
| XXBT | BTC |
| XBT | BTC |
| XETH | ETH |
| ZUSD | USD |
| ZEUR | EUR |

---

## Gemini

### Export Location

Account → Transaction History → Download CSV

### Expected Columns

| Column | Description | Required |
|--------|-------------|----------|
| Date | DateTime format | Yes |
| Type | Transaction type | Yes |
| Symbol | Asset pair or symbol | Yes |
| Amount | Quantity | Yes |
| Price | USD price | Yes |
| Fee | Transaction fee | No |

### Sample CSV

```csv
Date,Type,Symbol,Amount,Price,Fee
2024-01-15 10:30:00,Buy,BTCUSD,0.5,40000,10
2024-06-15 14:22:00,Sell,BTCUSD,0.25,65000,5
```

---

## Generic Format

Use this format for custom CSV files or unsupported exchanges.

### Required Columns

| Column | Description | Example |
|--------|-------------|---------|
| date | Transaction date | 2024-01-15 |
| type | Transaction type | buy, sell, staking |
| asset | Asset symbol | BTC, ETH |
| quantity | Amount | 0.5 |

### Optional Columns

| Column | Description | Example |
|--------|-------------|---------|
| price | USD price per unit | 40000 |
| fee | Transaction fee | 10 |
| total | Total cost/proceeds | 20010 |
| notes | Description | DCA purchase |

### Sample CSV

```csv
date,type,asset,quantity,price,fee
2024-01-15,buy,BTC,0.5,40000,10
2024-06-15,sell,BTC,0.25,65000,5
2024-08-01,staking,ETH,0.05,3200,0
```

### Supported Date Formats

- `2024-01-15` (ISO)
- `2024-01-15T10:30:00Z` (ISO with time)
- `01/15/2024` (US format)
- `15/01/2024` (EU format - attempted)
- `2024-01-15 10:30:00` (DateTime)

### Supported Transaction Types

**Acquisitions**: buy, receive, deposit
**Disposals**: sell, send, withdrawal, trade, swap, convert
**Income**: staking, airdrop, mining, interest, reward
**Non-taxable**: transfer, transfer_in, transfer_out

---

## Creating Custom Format

If your exchange isn't supported, create a generic CSV:

1. Export transaction history from your exchange
2. Rename columns to match generic format:
   - Date column → `date`
   - Type column → `type`
   - Asset column → `asset`
   - Amount column → `quantity`
   - Price column → `price` (if available)
   - Fee column → `fee` (if available)

3. Ensure date is in parseable format
4. Use lowercase transaction types
5. Run with `--verbose` to check parsing

### Example Transformation

**Original (Custom Exchange)**:

```csv
Trade Date,Action,Currency,Units,Rate,Commission
15-Jan-2024,PURCHASE,Bitcoin,0.5,40000,10
```

**Transformed (Generic)**:

```csv
date,type,asset,quantity,price,fee
2024-01-15,buy,BTC,0.5,40000,10
```

---

## Troubleshooting

### Common Issues

**Wrong delimiter**:

- Check if CSV uses comma, semicolon, or tab
- Re-export with comma delimiter if needed

**Encoding issues**:

- Save as UTF-8
- Remove BOM if present

**Missing prices**:

- Add price column manually
- Look up historical prices on CoinGecko

**Unknown transaction types**:

- Check mapping in `config/settings.yaml`
- Manually map to standard types

### Validation

Test parsing with verbose mode:

```bash
python transaction_parser.py your_export.csv --verbose
```

This shows:

- Detected exchange format
- Parsed transaction count
- Any skipped rows with reasons
