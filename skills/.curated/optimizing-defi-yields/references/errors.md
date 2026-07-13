# Error Handling Reference

## API Errors

### DeFiLlama API Timeout

```
Error: requests.exceptions.Timeout: Request timed out after 30s
```

**Cause**: DeFiLlama API is slow or unavailable.
**Solution**:

- Script automatically falls back to cached data
- If cache is also unavailable, uses mock data for basic functionality
- Wait a few minutes and retry with `--no-cache` flag

### DeFiLlama Rate Limit

```
Error: 429 Too Many Requests
```

**Cause**: Too many API requests in short period.
**Solution**:

- DeFiLlama has generous limits, this is rare
- Cache is used by default (5 minute TTL)
- Wait 1 minute before retrying

### Network Connection Error

```
Error: requests.exceptions.ConnectionError: Failed to establish connection
```

**Cause**: No internet connection or DNS issues.
**Solution**:

- Check network connectivity
- Script falls back to cached data automatically
- Use `--verbose` to see cache status

## Data Errors

### No Pools Found

```
No pools match your criteria. Try broadening filters.
```

**Cause**: Filters are too restrictive.
**Solution**:

- Remove some filters (e.g., remove `--audited-only`)
- Lower `--min-tvl` threshold
- Try fewer chains or protocols
- Use `--top 50` to see more results

### Invalid Chain Name

```
Warning: No pools found for chain 'eth'
```

**Cause**: Chain name doesn't match DeFiLlama format.
**Solution**: Use correct chain names:

- `ethereum` (not `eth` or `mainnet`)
- `arbitrum` (not `arb`)
- `polygon` (not `matic`)
- `optimism` (not `op`)
- `bsc` (for Binance Smart Chain)

### Invalid Protocol Name

```
Warning: No pools found for protocol 'aave'
```

**Cause**: Protocol slug doesn't match exactly.
**Solution**: Use exact slugs:

- `aave-v3` or `aave-v2` (not just `aave`)
- `compound-v3` (not `compound`)
- `curve-dex` (not `curve`)
- `convex-finance` (not `convex`)
- `yearn-finance` (not `yearn`)

## Cache Errors

### Cache Read Error

```
Warning: Could not read cache file
```

**Cause**: Cache file corrupted or permissions issue.
**Solution**:

- Delete cache file: `rm ~/.defi_yield_cache.json`
- Script will fetch fresh data on next run

### Stale Cache Warning

```
Using stale cache (15 min old)
```

**Cause**: Cache TTL exceeded but API unavailable.
**Solution**:

- Not a critical error - data is still usable
- Retry later for fresh data
- Use `--no-cache` to force refresh when API is back

## Import Errors

### Missing requests Library

```
Warning: requests library not available, using mock data
```

**Cause**: Python `requests` package not installed.
**Solution**:

```bash
pip install requests
```

### Module Not Found

```
ModuleNotFoundError: No module named 'protocol_fetcher'
```

**Cause**: Running script from wrong directory.
**Solution**:

```bash
# Run from scripts directory or use full path
cd /path/to/skills/optimizing-defi-yields/scripts
python yield_optimizer.py --help
```

## Output Errors

### File Write Permission Denied

```
PermissionError: [Errno 13] Permission denied: 'yields.json'
```

**Cause**: Cannot write to output file location.
**Solution**:

- Check file/directory permissions
- Try a different output path
- Use stdout (no `--output` flag) and redirect

### Invalid Output Format

```
Error: Invalid format 'xml'
```

**Cause**: Unsupported output format specified.
**Solution**: Use supported formats:

- `table` (default)
- `json`
- `csv`

## Risk Assessment Warnings

### Unknown Protocol Risk

```
Risk Score: 5.0/10 (default - protocol not in database)
```

**Cause**: Protocol not in known audited protocols list.
**Solution**:

- Not an error - default medium risk applied
- Manually verify protocol's audit status
- Consider additional due diligence for unknown protocols

### High APY Warning

```
Risk Factor: Very high APY (150.0%) - verify sustainability
```

**Cause**: APY exceeds expected sustainable levels.
**Solution**:

- High APY often indicates:
  - Temporary incentive programs
  - High-risk opportunities
  - Possible scams (if extremely high)
- Research the protocol thoroughly before investing

## Recovery Commands

### Reset Cache

```bash
rm ~/.defi_yield_cache.json
```

### Test API Connectivity

```bash
curl -s "https://yields.llama.fi/pools" | head -c 100
```

### Verbose Mode for Debugging

```bash
python yield_optimizer.py --verbose --top 5
```

### Check Specific Protocol

```bash
python yield_optimizer.py --protocol aave-v3 --verbose
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
