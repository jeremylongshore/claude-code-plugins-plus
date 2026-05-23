# Error Handling Reference

## Data Fetching Errors

### No Data Returned

```
Error: No data returned for {symbol}
```

**Causes:**

- Invalid symbol format
- Symbol not available on Yahoo Finance
- Network connectivity issues

**Solutions:**

```bash
# Verify symbol exists
python -c "import yfinance as yf; print(yf.Ticker('BTC-USD').info.get('symbol'))"

# Try alternative symbol format
# Yahoo uses: BTC-USD (not BTC/USD or BTCUSD)
```

### Insufficient Data

```
SKIP (insufficient data)
```

**Cause:** Less than 50 data points for reliable indicator calculation.

**Solutions:**

- Extend the period: `--period 1y`
- Reduce indicator lookback periods in config
- Check if asset is newly listed

### yfinance Import Error

```
ModuleNotFoundError: No module named 'yfinance'
```

**Solution:**

```bash
pip install yfinance pandas numpy
# or with uv
uv pip install yfinance pandas numpy
```

### Rate Limit Exceeded

```
HTTPError: Too Many Requests
```

**Cause:** Too many API calls to Yahoo Finance.

**Solutions:**

- Add delays between requests
- Use cached data: `--use-cache`
- Reduce watchlist size
- Wait and retry

## Indicator Calculation Errors

### NaN Values in Indicators

```
RuntimeWarning: invalid value encountered
```

**Cause:** Division by zero or insufficient data for calculation.

**Impact:** Affected indicators show as NEUTRAL in signals.

**Solutions:**

- Use longer period for more data
- Check if asset has low volume (causes NaN in some indicators)

### Timezone Mismatch

```
TypeError: Invalid comparison between dtype=datetime64[ns, UTC] and datetime
```

**Cause:** Cached data has timezone info, comparison doesn't.

**Solution:** The scanner handles this automatically. If persists, delete cached data:

```bash
rm -rf data/*.csv
```

## Configuration Errors

### Invalid YAML Syntax

```
yaml.scanner.ScannerError: ...
```

**Cause:** Syntax error in settings.yaml.

**Solution:**

```bash
# Validate YAML
python -c "import yaml; yaml.safe_load(open('config/settings.yaml'))"

# Common issues:
# - Incorrect indentation
# - Missing colons
# - Unquoted special characters
```

### Unknown Watchlist

```
Unknown watchlist: {name}
```

**Solution:**

```bash
# List available watchlists
python scanner.py --list-watchlists

# Available: crypto_top10, crypto_defi, crypto_layer2, stocks_tech, etfs_major
```

### Invalid Filter Option

```
error: argument --filter: invalid choice
```

**Solution:**

```bash
# Valid options: buy, sell, all
python scanner.py --filter buy
```

## Output Errors

### Permission Denied on Output

```
PermissionError: [Errno 13] Permission denied: 'output/...'
```

**Solution:**

```bash
# Check directory permissions
chmod -R u+w output/

# Or specify different output path
python scanner.py --output ~/signals.json
```

### JSON Output Invalid

```
json.decoder.JSONDecodeError: ...
```

**Cause:** Interrupted write or corrupted file.

**Solution:** Re-run the scanner to regenerate output.

## Signal Interpretation Warnings

### Low Confidence Signals

```
Confidence: 25.0%
```

**Meaning:** Indicators are mixed/conflicting. Not actionable.

**Recommendation:**

- Wait for clearer signals
- Use higher confidence threshold: `--min-confidence 60`

### All NEUTRAL Signals

```
Summary: 0 Buy | 10 Neutral | 0 Sell
```

**Causes:**

- Market in consolidation
- Indicators at neutral levels
- Insufficient volatility

**Not an error** - markets aren't always trending.

### Extreme Readings

```
RSI: STRONG_BUY | Oversold at 5.2 (< 30)
```

**Warning:** Extreme readings can indicate:

- True capitulation (good entry)
- Flash crash (may continue lower)
- Data error

**Recommendation:** Verify with multiple timeframes and on-chain data.

## Common Troubleshooting

### Script Won't Start

```bash
# Check Python version (need 3.8+)
python --version

# Check dependencies
pip list | grep -E "yfinance|pandas|numpy"

# Run from correct directory
cd /path/to/skills/generating-trading-signals/scripts
python scanner.py --help
```

### Slow Performance

**Causes:**

- Large watchlist
- No cached data
- Slow network

**Solutions:**

```bash
# Cache data first
python scanner.py --watchlist crypto_top10 --period 1y

# Use cached data on subsequent runs
# (automatic if files exist in data/)

# Reduce watchlist size
python scanner.py --symbols BTC-USD,ETH-USD
```

### Memory Issues

```
MemoryError: Unable to allocate array
```

**Cause:** Processing too many symbols with long history.

**Solutions:**

- Reduce period: `--period 3m`
- Process in batches
- Increase system memory

## Best Practices

1. **Always verify signals** with multiple sources before trading
2. **Use appropriate position sizing** based on confidence
3. **Set stop-losses** using the provided SL levels
4. **Backtest signals** before live trading
5. **Monitor for data quality** issues in cached data

## Getting Help

1. Check this error reference
2. Verify data source (yfinance) is working
3. Test with single symbol first
4. Check GitHub issues for known problems

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
