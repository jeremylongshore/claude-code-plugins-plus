# Error Handling Reference

Comprehensive error handling guide for the Crypto Portfolio Tracker.

---

## File Errors

### Portfolio File Not Found

**Error**: Cannot find portfolio file at specified path

**Symptoms**:

```
Error: Portfolio file not found: /path/to/holdings.json
```

**Causes**:

- Incorrect file path
- File moved or deleted
- Typo in filename

**Solutions**:

1. Verify the file path is correct
2. Use absolute path or path relative to current directory
3. Check file exists: `ls -la /path/to/holdings.json`

---

### Invalid JSON Format

**Error**: Portfolio file contains invalid JSON

**Symptoms**:

```
Error: Invalid JSON in portfolio file: Expecting ',' delimiter
```

**Causes**:

- Missing commas between array items
- Unquoted strings
- Trailing commas (not allowed in JSON)
- UTF-8 encoding issues

**Solutions**:

1. Validate JSON: `python -m json.tool holdings.json`
2. Use a JSON linter or formatter
3. Check for common errors: trailing commas, missing quotes

---

### Missing Required Fields

**Error**: Holdings missing required coin or quantity

**Symptoms**:

```
Warning: Holding 2 missing coin symbol, skipping
Warning: Holding 3 (ETH) missing quantity, skipping
```

**Causes**:

- Incomplete portfolio entry
- Wrong field names

**Solutions**:

1. Ensure each holding has `coin` and `quantity` fields
2. Check for typos in field names
3. Valid example:

   ```json
   {"coin": "BTC", "quantity": 0.5}
   ```

---

## API Errors

### CoinGecko Rate Limit

**Error**: Too many API requests

**Symptoms**:

```
API request failed: 429 Too Many Requests
Using stale cached prices as fallback
```

**Causes**:

- Exceeded free tier limit (~10-30 calls/minute)
- Running multiple queries too quickly

**Solutions**:

1. **Automatic**: Uses cached prices with warning
2. **Manual**: Wait 60 seconds before retry
3. Cache persists between runs for resilience

---

### Unknown Coin Symbol

**Error**: Coin not found in CoinGecko

**Symptoms**:

```
Warning: Unknown symbols, trying lowercase: ['MYCOIN']
```

**Causes**:

- Coin not listed on CoinGecko
- Non-standard symbol
- New coin not yet indexed

**Solutions**:

1. Use standard symbols (BTC, ETH, SOL, etc.)
2. Check CoinGecko for correct ID
3. Holding will show with $0 price if not found

---

### Network Timeout

**Error**: Cannot connect to price API

**Symptoms**:

```
API request failed: Connection timed out
```

**Causes**:

- Network connectivity issues
- API server downtime
- Firewall blocking requests

**Solutions**:

1. Check internet connectivity
2. Test API: `curl https://api.coingecko.com/api/v3/ping`
3. Uses cached prices as fallback

---

## Validation Errors

### Invalid Quantity

**Error**: Holding has invalid quantity value

**Symptoms**:

```
Warning: Holding 1 (BTC) has non-positive quantity, skipping
```

**Causes**:

- Quantity is zero or negative
- Non-numeric value
- Empty string

**Solutions**:

1. Ensure quantity is a positive number
2. Remove or fix the invalid entry
3. Valid example: `"quantity": 0.5` (not `"quantity": "0.5"`)

---

### Invalid Cost Basis

**Note**: Cost basis is optional, invalid values are ignored silently

**Causes**:

- Negative cost basis
- Non-numeric value

**Solutions**:

1. Remove the field or set to valid positive number
2. Cost basis should be per-coin price, not total cost

---

## Graceful Degradation

The tracker implements graceful degradation:

```
Full Analysis (all prices + P&L)
     │
     ├─► API unavailable → Use cached prices
     │         │
     │         ▼
     │    Show "stale prices" warning
     │
     ├─► Unknown coin → Skip in valuation
     │         │
     │         ▼
     │    Show "coin not found" warning
     │
     └─► No cost basis → Skip P&L calculation
               │
               ▼
          Show allocations only
```

---

## Diagnostic Commands

### Validate Portfolio File

```bash
# Check JSON syntax
python -m json.tool holdings.json

# Test portfolio loading
python portfolio_loader.py holdings.json -v
```

### Test Price Fetching

```bash
# Fetch prices for specific coins
python price_fetcher.py BTC ETH SOL -v

# Check cache
cat scripts/.price_cache.json | python -m json.tool
```

### Clear Cache

```bash
rm scripts/.price_cache.json
```

---

## Common Issues

### Issue: All Values Show $0

**Causes**:

- API failed and no cache available
- All coin symbols unknown

**Diagnosis**:

```bash
python portfolio_tracker.py --portfolio holdings.json -v
# Check for API errors in output
```

### Issue: Missing Coins in Output

**Causes**:

- Invalid quantity (zero or negative)
- Missing required fields
- Duplicate coins aggregated

**Diagnosis**:

```bash
python portfolio_loader.py holdings.json -v
# Check warnings for skipped holdings
```

### Issue: P&L Not Showing

**Causes**:

- No cost_basis field in holdings
- Invalid cost_basis values
- Not using --detailed flag

**Solutions**:

1. Add cost_basis to holdings
2. Use `--detailed` flag
3. Example: `{"coin": "BTC", "quantity": 0.5, "cost_basis": 50000}`

---

## Portfolio File Troubleshooting

### Minimal Valid Portfolio

```json
{
  "holdings": [
    {"coin": "BTC", "quantity": 0.5}
  ]
}
```

### Full Valid Portfolio

```json
{
  "name": "My Portfolio",
  "holdings": [
    {
      "coin": "BTC",
      "quantity": 0.5,
      "cost_basis": 50000,
      "acquired": "2024-01-15",
      "wallet": "Ledger"
    }
  ],
  "categories": {
    "BTC": "Layer 1"
  }
}
```

### Common JSON Errors

```json
// WRONG: Trailing comma
{"holdings": [{"coin": "BTC", "quantity": 0.5},]}

// WRONG: Unquoted key
{holdings: [{"coin": "BTC", "quantity": 0.5}]}

// WRONG: Single quotes
{'holdings': [{'coin': 'BTC', 'quantity': 0.5}]}

// CORRECT
{"holdings": [{"coin": "BTC", "quantity": 0.5}]}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
