# Error Handling Reference

## API Errors

### Subgraph Query Timeout

```
Error: requests.exceptions.Timeout: Request timed out after 15s
```

**Cause**: The Graph subgraph is slow or unavailable.
**Solution**:

- Script automatically falls back to DeFiLlama data
- Wait and retry if fresh subgraph data is needed
- Check The Graph status page for outages

### Subgraph Rate Limit

```
Error: 429 Too Many Requests
```

**Cause**: Too many subgraph queries in short period.
**Solution**:

- The Graph allows ~100 queries/minute on free tier
- Cache is used by default to reduce queries
- Wait 60 seconds before retrying

### DeFiLlama API Error

```
Error: Failed to fetch from DeFiLlama
```

**Cause**: DeFiLlama API unavailable.
**Solution**:

- Falls back to cached data if available
- Uses mock data for testing if needed
- Retry after a few minutes

## Pool Errors

### Pool Not Found

```
Error: Pool not found on ethereum
```

**Cause**: Pool address doesn't exist or wrong chain.
**Solution**:

- Verify pool address is correct
- Check you're using the right chain flag (--chain)
- Address must be lowercase for subgraphs

### Invalid Pool Address

```
Error: Invalid pool address format
```

**Cause**: Address format is incorrect.
**Solution**:

- Ensure address starts with 0x
- Address should be 42 characters (0x + 40 hex chars)
- Use lowercase for consistency

### Token Pair Not Found

```
Warning: No pools found for ETH/BTC
```

**Cause**: No pools exist for this pair on the selected protocol.
**Solution**:

- Try different protocol (--protocol)
- Check token symbols are correct
- Some pairs only exist on certain chains

## Calculation Errors

### Invalid Price Values

```
Error: Entry price must be greater than 0
```

**Cause**: Invalid price input for IL calculation.
**Solution**:

- Entry and current prices must be positive numbers
- Don't include currency symbols ($)
- Use decimal notation (2000, not 2,000)

### IL Calculation Error

```
Error: Cannot calculate IL for negative price ratio
```

**Cause**: Current price is 0 or negative.
**Solution**:

- Verify price inputs are correct
- Current price cannot be 0

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

- Delete cache: `rm ~/.lp_analyzer_cache.json`
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
ModuleNotFoundError: No module named 'pool_fetcher'
```

**Cause**: Running script from wrong directory.
**Solution**:

```bash
# Run from scripts directory or use full path
python /path/to/scripts/pool_analyzer.py --help
```

## Recovery Commands

### Reset Cache

```bash
rm ~/.lp_analyzer_cache.json
```

### Test Subgraph Connectivity

```bash
curl -X POST https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3 \
  -H "Content-Type: application/json" \
  -d '{"query": "{ pools(first: 1) { id } }"}'
```

### Verbose Mode for Debugging

```bash
python pool_analyzer.py --verbose --pair ETH/USDC
```

### Test with Known Pool

```bash
# Uniswap V3 ETH/USDC 0.05% pool
python pool_analyzer.py --pool 0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640 --verbose
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
