# Error Handling Reference

## API Errors

### DeFiLlama Timeout

```
Error: requests.exceptions.Timeout: Request timed out after 30s
```

**Cause**: DeFiLlama API is slow or unavailable.
**Solution**:

- Script automatically uses cached data if available
- Wait and retry if fresh data is needed
- Check DeFiLlama status for outages

### DeFiLlama Rate Limit

```
Error: 429 Too Many Requests
```

**Cause**: Too many API requests in a short period.
**Solution**:

- DeFiLlama has generous rate limits
- Cache is used by default to reduce requests
- Wait 60 seconds before retrying

### Network Error

```
Error: requests.exceptions.ConnectionError: Failed to connect
```

**Cause**: No network connection or DNS issues.
**Solution**:

- Check network connectivity
- Falls back to cached data if available
- Uses static fallback data as last resort

## Asset Errors

### Invalid Asset

```
Error: Asset 'XYZ' not supported
```

**Cause**: Requested asset is not in the supported list.
**Solution**: Use supported assets:

- ETH, SOL, ATOM, DOT, AVAX
- MATIC, NEAR, ADA, BNB

### No Staking Options Found

```
Warning: No staking options found for BTC
```

**Cause**: Asset doesn't have staking options (e.g., BTC is not PoS).
**Solution**:

- Verify asset is proof-of-stake
- Check asset symbol is correct

## Position Errors

### Invalid Position Format

```
Error: Could not parse position '10 ETH lido'
```

**Cause**: Position string format is incorrect.
**Solution**: Use correct format:

- `"10 ETH @ lido 4.0%"`
- `"100 ATOM @ native 18%"`
- Multiple: `"10 ETH @ lido 4.0%, 100 ATOM @ native 18%"`

### Invalid Amount

```
Error: Amount must be positive
```

**Cause**: Negative or zero amount provided.
**Solution**:

- Provide a positive number for --amount
- Use decimal notation (10.5, not "10.5 ETH")

## Calculation Errors

### Division by Zero

```
Error: Cannot calculate metrics for zero position
```

**Cause**: Position value is zero or TVL is zero.
**Solution**:

- Provide valid position amount
- Check if protocol has valid TVL data

### Invalid APY

```
Warning: APY 1500% seems unusually high
```

**Cause**: Reported APY is likely incorrect or unsustainable.
**Solution**:

- Verify data from protocol's official source
- High APY often indicates high risk
- May be short-term promotional rate

## Output Errors

### File Write Permission Denied

```
PermissionError: [Errno 13] Permission denied: 'output.json'
```

**Cause**: Cannot write to output file location.
**Solution**:

- Check file/directory permissions
- Try different output path
- Use stdout (no --output flag)

### Invalid Output Format

```
Error: Invalid format 'xml'
```

**Cause**: Unsupported output format.
**Solution**: Use supported formats:

- `table` (default)
- `json`
- `csv`

## Cache Errors

### Cache Read Error

```
Warning: Could not read cache file
```

**Cause**: Cache file corrupted or permissions issue.
**Solution**:

- Delete cache: `rm ~/.staking_optimizer_cache.json`
- Script will fetch fresh data

### Stale Cache Warning

```
Using cached data (10 min old)
```

**Cause**: Cache TTL exceeded but API unavailable.
**Solution**:

- Not critical - data is still usable
- Use `--no-cache` to force refresh when API is back

## Import Errors

### Missing requests Library

```
Warning: requests library not available
```

**Cause**: Python `requests` package not installed.
**Solution**:

```bash
pip install requests
```

### Module Not Found

```
ModuleNotFoundError: No module named 'staking_fetcher'
```

**Cause**: Running script from wrong directory.
**Solution**:

```bash
# Run from scripts directory or use full path
python /path/to/scripts/staking_optimizer.py --help
```

## Risk Assessment Errors

### Unknown Protocol

```
Warning: No risk data for protocol 'new-protocol'
```

**Cause**: Protocol not in risk database.
**Solution**:

- Default risk score (5/10) is assigned
- Exercise caution with unknown protocols
- Research protocol manually

### Missing TVL Data

```
Warning: No TVL data for risk calculation
```

**Cause**: TVL data not available from API.
**Solution**:

- TVL component of risk score uses default
- Other risk factors still calculated
- Check protocol's official TVL on DeFiLlama

## Recovery Commands

### Reset Cache

```bash
rm ~/.staking_optimizer_cache.json
```

### Test API Connectivity

```bash
curl -s "https://yields.llama.fi/pools" | head -c 100
```

### Verbose Mode for Debugging

```bash
python staking_optimizer.py --asset ETH --verbose
```

### Test with Known Asset

```bash
python staking_optimizer.py --asset ETH --detailed
```

## Common Workflows

### If Data Seems Outdated

```bash
# Force fresh data
python staking_optimizer.py --asset ETH --no-cache
```

### If Errors Persist

```bash
# 1. Clear cache
rm ~/.staking_optimizer_cache.json

# 2. Test with verbose
python staking_optimizer.py --asset ETH --verbose

# 3. Check network
curl -I https://yields.llama.fi/pools
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
