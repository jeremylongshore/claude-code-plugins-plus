# Error Handling Reference

## Data Fetching Errors

### No Data Returned

```
Error: No data returned for {symbol}
```

**Causes:**

- Invalid symbol format (use `BTC-USD` not `BTC/USD`)
- Symbol not available on data provider
- Date range has no trading data

**Solutions:**

```bash
# Check valid symbol format for Yahoo Finance
python -c "import yfinance as yf; print(yf.Ticker('BTC-USD').info.get('symbol'))"

# Try CoinGecko for crypto
python scripts/fetch_data.py --symbol BTC --source coingecko
```

### Insufficient Data

```
Error: Insufficient data. Got {n} bars, need at least 50.
```

**Cause:** Date range too short or strategy lookback period exceeds data length.

**Solution:** Extend the period or reduce strategy lookback:

```bash
python scripts/backtest.py --strategy sma_crossover --period 1y  # More data
```

### yfinance Not Installed

```
yfinance not installed. Install with: pip install yfinance pandas
```

**Solution:**

```bash
pip install yfinance pandas numpy matplotlib
```

## Strategy Errors

### Unknown Strategy

```
ValueError: Unknown strategy: {name}. Available: [...]
```

**Solution:** Use `--list` to see available strategies:

```bash
python scripts/backtest.py --list
```

### Invalid Parameters JSON

```
json.decoder.JSONDecodeError: ...
```

**Cause:** Malformed JSON in `--params` argument.

**Solution:** Ensure proper JSON format:

```bash
# Correct
--params '{"fast_period": 20, "slow_period": 50}'

# Wrong (single quotes inside)
--params "{'fast_period': 20}"
```

### Strategy Lookback Exceeded

```
Signal generation failed: insufficient data for lookback period
```

**Cause:** Strategy needs more historical bars than available.

**Solution:** Fetch more data or use shorter lookback:

```bash
python scripts/fetch_data.py --symbol BTC-USD --period 2y
```

## Calculation Errors

### Division by Zero in Metrics

```
RuntimeWarning: divide by zero encountered
```

**Cause:** No trades generated, or all trades were losses.

**Solution:** This is informational. Check if strategy generates signals:

- Too few signals = parameters may be too restrictive
- No winning trades = strategy may not suit the asset/timeframe

### NaN in Results

```
Sharpe Ratio: nan
```

**Cause:** Zero variance in returns (e.g., all flat periods).

**Solution:** Use longer test period or more volatile asset.

## File/Directory Errors

### Permission Denied

```
PermissionError: [Errno 13] Permission denied: 'reports/...'
```

**Solution:**

```bash
chmod -R u+w /path/to/backtester/reports/
```

### Missing Directory

```
FileNotFoundError: [Errno 2] No such file or directory: 'data/...'
```

**Solution:** Directories are auto-created, but ensure write permissions:

```bash
mkdir -p data reports
```

## Optimization Errors

### Memory Error During Grid Search

```
MemoryError: Unable to allocate array
```

**Cause:** Too many parameter combinations.

**Solution:** Reduce parameter grid:

```bash
# Instead of testing 10x10x10 = 1000 combinations
--param-grid '{"p1": [10,20,30], "p2": [50,100]}'  # 6 combinations
```

### Optimization Takes Too Long

**Cause:** Large grid + large dataset.

**Solutions:**

1. Reduce parameter grid
2. Use shorter test period for initial optimization
3. Parallelize (not implemented in basic version)

## Performance Warnings

### Unrealistic Results

**Symptoms:**

- Sharpe ratio > 5
- Win rate > 80%
- No losing periods

**Cause:** Likely overfitting or look-ahead bias.

**Solution:**

- Test on out-of-sample data
- Add realistic commission/slippage
- Verify signal generation doesn't use future data

### All Trades Are Losses

**Cause:**

- Commission/slippage too high
- Strategy not suited for asset
- Wrong direction (buying when should sell)

**Solution:**

- Reduce costs: `--commission 0.0005 --slippage 0.0002`
- Try different strategy
- Check strategy logic

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
