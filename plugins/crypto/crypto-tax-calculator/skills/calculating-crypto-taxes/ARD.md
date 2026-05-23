# ARD: Crypto Tax Calculator

> Part of [Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)

## Architecture Pattern

**Pattern**: Tax Calculation Pipeline
**Type**: Batch Processing with Lot Tracking

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────────┐
│  CSV Import │───▶│  Normalizer  │───▶│ Tax Engine  │───▶│    Report    │
│   (Parser)  │    │   (Clean)    │    │ (Calculate) │    │  (Generate)  │
└─────────────┘    └──────────────┘    └─────────────┘    └──────────────┘
       │                  │                   │                   │
       ▼                  ▼                   ▼                   ▼
  Exchange CSVs      Normalized         Lot Tracking        Form 8949
  Generic CSV        Transactions       Cost Basis          CSV Export
                                        Gains/Losses        JSON Export
```

## Workflow

### Step 1: Import Transactions

Load CSV files from exchange exports or generic format.

### Step 2: Normalize Data

- Parse dates to ISO format
- Normalize asset symbols (BTC, ETH)
- Categorize transaction types
- Validate required fields

### Step 3: Calculate Tax Events

- Build lot inventory from acquisitions
- Match disposals to lots using selected method
- Calculate gains/losses per disposal
- Track holding periods

### Step 4: Generate Report

- Format for Form 8949 compatibility
- Separate short-term and long-term
- Calculate summary totals
- Export to selected format

## Data Flow

```
Input:                     Processing:                  Output:
┌─────────────────┐       ┌─────────────────┐         ┌─────────────────┐
│ Exchange CSVs   │       │ Transaction     │         │ Tax Report CSV  │
│ - Coinbase      │──────▶│ Normalizer      │         │ - Form 8949     │
│ - Binance       │       │ - Date parsing  │         │ - Short/Long    │
│ - Kraken        │       │ - Type mapping  │         │                 │
│ - Generic       │       │ - Validation    │         │ Summary JSON    │
└─────────────────┘       └────────┬────────┘         │ - Totals        │
                                   │                  │ - By category   │
                          ┌────────▼────────┐         │                 │
                          │ Cost Basis      │         │ Income Report   │
                          │ Engine          │         │ - Staking       │
                          │ - Lot tracking  │────────▶│ - Airdrops      │
                          │ - FIFO/LIFO/HIFO│         │ - Yield         │
                          │ - Gain calc     │         └─────────────────┘
                          └─────────────────┘
```

## Directory Structure

```
plugins/crypto/crypto-tax-calculator/skills/calculating-crypto-taxes/
├── PRD.md                          # Product requirements
├── ARD.md                          # This file
├── SKILL.md                        # Core instructions
├── scripts/
│   ├── tax_calculator.py           # Main CLI entry point
│   ├── transaction_parser.py       # CSV parsing and normalization
│   ├── cost_basis_engine.py        # Lot tracking and cost basis
│   ├── tax_engine.py               # Gains/losses calculation
│   └── report_generator.py         # Output formatting
├── references/
│   ├── errors.md                   # Error handling guide
│   ├── examples.md                 # Usage examples
│   └── exchange_formats.md         # CSV format documentation
└── config/
    └── settings.yaml               # Exchange mappings, tax rules
```

## Component Design

### 1. Transaction Parser (`transaction_parser.py`)

**Purpose**: Parse and normalize CSV files from various exchanges.

**Exchange Format Handlers**:

```python
EXCHANGE_FORMATS = {
    "coinbase": {
        "date_col": "Timestamp",
        "type_col": "Transaction Type",
        "asset_col": "Asset",
        "quantity_col": "Quantity Transacted",
        "price_col": "Spot Price at Transaction",
        "fee_col": "Fees and/or Spread",
    },
    "binance": {
        "date_col": "Date(UTC)",
        "type_col": "Operation",
        "asset_col": "Coin",
        "quantity_col": "Change",
        "price_col": None,  # Requires price lookup
    },
    # ... more exchanges
}
```

**Output**: Normalized transaction list with consistent schema.

### 2. Cost Basis Engine (`cost_basis_engine.py`)

**Purpose**: Track lots and calculate cost basis using selected method.

**Lot Structure**:

```python
@dataclass
class Lot:
    asset: str
    quantity: Decimal
    cost_per_unit: Decimal
    acquired_date: datetime
    remaining: Decimal
    fees: Decimal = Decimal("0")
```

**Methods**:

- `add_lot(lot)`: Record acquisition
- `dispose(asset, quantity, date, method)`: Match lots and return cost basis
- `get_inventory()`: Current holdings by lot

**Cost Basis Methods**:

| Method | Description | Use Case |
|--------|-------------|----------|
| FIFO | First In First Out | IRS default, required in some cases |
| LIFO | Last In First Out | Higher basis if prices rising |
| HIFO | Highest In First Out | Minimize gains (audit risk) |
| Specific ID | Manual lot selection | Maximum control |

### 3. Tax Engine (`tax_engine.py`)

**Purpose**: Calculate gains/losses and categorize taxable events.

**Taxable Event Types**:

| Event | Tax Treatment |
|-------|---------------|
| Sell | Capital gain/loss |
| Trade (crypto-to-crypto) | Capital gain/loss |
| Spend (purchase goods) | Capital gain/loss |
| Staking Reward | Ordinary income at FMV |
| Airdrop | Ordinary income at FMV |
| Mining | Ordinary income at FMV |
| Transfer | Non-taxable (same owner) |

**Holding Period**:

- Short-term: < 1 year (ordinary income rates)
- Long-term: >= 1 year (preferential rates)

### 4. Report Generator (`report_generator.py`)

**Purpose**: Format results for tax filing.

**Form 8949 Columns**:

| Column | Description |
|--------|-------------|
| Description | "X.XX BTC" |
| Date Acquired | MM/DD/YYYY |
| Date Sold | MM/DD/YYYY |
| Proceeds | Sale amount |
| Cost Basis | Acquisition cost + fees |
| Gain or Loss | Proceeds - Cost Basis |

**Output Formats**:

- CSV (Form 8949 compatible)
- JSON (programmatic use)
- Summary text (terminal display)

## Error Handling Strategy

| Error Type | Handling | User Message |
|------------|----------|--------------|
| Missing required column | Fail with details | "Column 'Date' not found in CSV" |
| Invalid date format | Attempt parse, warn | "Warning: Could not parse date on row 15" |
| Unknown transaction type | Categorize as "other" | "Unknown type 'MARGIN_CALL' treated as other" |
| Insufficient lots | Fail calculation | "Cannot dispose 1.5 BTC - only 1.0 available" |
| Missing price data | Request manual entry | "Price needed for BTC on 2025-03-15" |

## Historical Price Integration

**Primary**: CoinGecko Historical API (free tier)

```
GET /coins/{id}/history?date={dd-mm-yyyy}
```

**Fallback**: Manual price entry via CSV column or prompt.

**Caching**: Store fetched prices in `~/.crypto_tax_prices.json` to reduce API calls.

## Testing Strategy

### Unit Tests

- Transaction parser: Each exchange format
- Cost basis: FIFO/LIFO/HIFO scenarios
- Holding period: Edge cases (exactly 1 year)

### Integration Tests

- End-to-end with sample exchange exports
- Multi-year scenarios
- Mixed transaction types

### Test Data

```json
{
  "transactions": [
    {"date": "2024-01-15", "type": "buy", "asset": "BTC", "quantity": 1.0, "price": 40000},
    {"date": "2024-06-15", "type": "buy", "asset": "BTC", "quantity": 0.5, "price": 65000},
    {"date": "2025-01-20", "type": "sell", "asset": "BTC", "quantity": 0.75, "price": 95000}
  ]
}
```

Expected FIFO result:

- Dispose 0.75 BTC from first lot (acquired 2024-01-15)
- Proceeds: $71,250
- Cost basis: $30,000
- Long-term gain: $41,250

## Security Considerations

- No exchange API credentials stored or requested
- Transaction data stays local (CSV files)
- Historical price cache contains no PII
- Output reports may contain sensitive financial data (warn user)

## Performance

| Operation | Target | Constraint |
|-----------|--------|------------|
| Parse 10K transactions | < 5 seconds | CSV parsing |
| Calculate tax events | < 2 seconds | Lot matching |
| Generate report | < 1 second | Formatting |
| Price lookup (cached) | < 100ms | Local cache |
| Price lookup (API) | < 2 seconds | Rate limited |

## Dependencies

**Required** (Python stdlib):

- `csv` - CSV parsing
- `json` - JSON handling
- `datetime` - Date/time operations
- `decimal` - Precise financial math
- `dataclasses` - Lot structures
- `argparse` - CLI arguments

**Optional**:

- `requests` - Historical price API (graceful fallback if missing)

## Tax Disclaimer

**IMPORTANT**: This tool provides informational calculations only. It is not tax advice. Users should:

- Consult a qualified tax professional
- Verify calculations independently
- Understand their jurisdiction's specific rules
- Keep records for audit purposes

The tool follows general US IRS guidelines but tax laws vary by jurisdiction and change over time.
