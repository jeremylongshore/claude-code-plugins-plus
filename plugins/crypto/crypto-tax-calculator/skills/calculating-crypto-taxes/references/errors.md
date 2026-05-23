# Error Handling Reference

Comprehensive error handling guide for the Crypto Tax Calculator.

---

## File Errors

### CSV File Not Found

**Error**: Cannot find transaction CSV file

**Symptoms**:

```
Error: Transaction file not found: /path/to/trades.csv
```

**Causes**:

- Incorrect file path
- File moved or deleted
- Typo in filename

**Solutions**:

1. Verify the file path is correct
2. Use absolute path or path relative to current directory
3. Check file exists: `ls -la /path/to/trades.csv`

---

### Invalid CSV Format

**Error**: Cannot parse CSV file

**Symptoms**:

```
Error: No headers found in trades.csv
Warning: Row 15 skipped: Cannot parse date
```

**Causes**:

- Missing header row
- Inconsistent delimiters
- Encoding issues

**Solutions**:

1. Verify CSV has header row
2. Check delimiter (comma, semicolon, tab)
3. Convert to UTF-8 encoding if needed
4. Open in spreadsheet app and re-export

---

### Unknown Exchange Format

**Error**: Cannot auto-detect exchange format

**Symptoms**:

```
Warning: Unknown exchange format, using generic parser
```

**Causes**:

- Non-standard CSV column names
- Custom export format

**Solutions**:

1. Specify exchange format: `--exchange coinbase`
2. Use generic format with mapped columns
3. Check `references/exchange_formats.md` for column requirements

---

## Data Validation Errors

### Missing Required Columns

**Error**: CSV missing required fields

**Symptoms**:

```
Error: Missing required column: date
Error: Missing required column: quantity
```

**Causes**:

- Incomplete export from exchange
- Wrong export type selected

**Solutions**:

1. Re-export from exchange with all fields
2. Select "Transaction History" not "Account Statement"
3. Manually add missing columns if data available

---

### Invalid Date Format

**Error**: Cannot parse transaction date

**Symptoms**:

```
Warning: Row 15 skipped: Cannot parse date: 15/01/2025
```

**Causes**:

- Unexpected date format
- Regional date format (DD/MM vs MM/DD)

**Solutions**:

1. Tool tries multiple formats automatically
2. Standardize to ISO format: YYYY-MM-DD
3. Check locale settings in export

**Supported Formats**:

- `2025-01-15` (ISO)
- `2025-01-15T10:30:00Z` (ISO with time)
- `01/15/2025` (US)
- `15/01/2025` (EU - attempted)

---

### Invalid Quantity or Price

**Error**: Cannot parse numeric values

**Symptoms**:

```
Warning: Row 20 skipped: Invalid quantity value
```

**Causes**:

- Text in numeric field
- Currency symbols not stripped
- Thousands separator issues

**Solutions**:

1. Remove currency symbols ($, €)
2. Use period for decimal separator
3. Remove thousands separators or use consistent format

---

## Cost Basis Errors

### Insufficient Lots for Disposal

**Error**: Trying to sell more than available

**Symptoms**:

```
Error: Cannot dispose 1.5 BTC - only 1.0 available
```

**Causes**:

- Missing buy transactions
- Transactions not in chronological order
- Transfer not recorded as acquisition

**Solutions**:

1. Check for missing buy transactions
2. Verify all exchange imports included
3. Add transfer-in as manual acquisition
4. Record cost basis for transferred coins

---

### Missing Price for Transaction

**Error**: Cannot calculate cost basis without price

**Symptoms**:

```
Warning: Missing price for buy on 2024-03-15, skipping lot creation
Warning: Missing price for sell on 2024-06-20, skipping disposal
```

**Causes**:

- Exchange didn't include price in export
- Historical price lookup not available

**Solutions**:

1. Add price column manually
2. Look up historical price on CoinGecko/CoinMarketCap
3. Use `--verbose` to see which transactions need prices

---

## Report Generation Errors

### Output File Permission Denied

**Error**: Cannot write output file

**Symptoms**:

```
Error: Permission denied: /path/to/report.csv
```

**Causes**:

- Directory doesn't exist
- No write permission
- File locked by another program

**Solutions**:

1. Create output directory first
2. Check directory permissions
3. Close any programs using the file

---

## Graceful Degradation

The calculator implements graceful degradation:

```
Full Calculation (all transactions)
     │
     ├─► Missing price → Skip lot/disposal with warning
     │         │
     │         ▼
     │    Continue with available data
     │
     ├─► Unknown type → Categorize as "other"
     │         │
     │         ▼
     │    Show warning, skip tax calculation
     │
     └─► Insufficient lots → Dispose available amount
               │
               ▼
          Show warning with discrepancy
```

---

## Diagnostic Commands

### Validate CSV File

```bash
# Check CSV structure
head -5 trades.csv

# Count rows
wc -l trades.csv

# Check for encoding issues
file trades.csv
```

### Test Transaction Parsing

```bash
# Parse and show first 10 transactions
python transaction_parser.py trades.csv -v
```

### Test Cost Basis Engine

```bash
# Run with verbose output
python tax_calculator.py --transactions trades.csv --verbose
```

---

## Common Issues

### Issue: No Transactions Found

**Causes**:

- Empty CSV file
- All rows failed validation
- Year filter excluded all transactions

**Diagnosis**:

```bash
python tax_calculator.py --transactions trades.csv --verbose
# Check for validation warnings
```

### Issue: All Gains Are Short-Term

**Causes**:

- Missing acquisition dates
- Transactions all within 1 year

**Diagnosis**:

```bash
python tax_calculator.py --transactions trades.csv --show-lots
# Verify lot acquisition dates
```

### Issue: Method Comparison Shows Same Results

**Causes**:

- Only one lot per asset
- All lots have same cost basis

**Explanation**:
Different methods only produce different results when multiple lots exist with different cost bases.

---

## Exchange Format Troubleshooting

### Coinbase

**Export**: Reports → Tax documents → Transaction history CSV

**Common Issues**:

- "Coinbase Pro" vs "Coinbase" different formats
- "Advanced Trade" transactions need separate export

### Binance

**Export**: Orders → Trade History → Export

**Common Issues**:

- No price column (requires manual price lookup)
- "Dust" conversions may be missing

### Kraken

**Export**: History → Export

**Common Issues**:

- Asset symbols like "XXBT" (map to BTC)
- Multiple currencies may be included

---

## Tax Disclaimer

**IMPORTANT**: This tool provides informational calculations only. It is not tax advice.

- Tax laws vary by jurisdiction
- Consult a qualified tax professional
- Keep original records for audit
- Rules change - verify current regulations

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
