# Error Handling Reference

## API Errors

### DeFiLlama API Timeout

```
Error: Request timeout
```

**Cause:** DeFiLlama API slow or unreachable
**Solution:**

1. Wait and retry (service usually recovers quickly)
2. Check  for outages
3. Use cached data if available

### Invalid Protocol Name

```
Error: Protocol not found: invalid-name
```

**Cause:** Protocol slug doesn't match DeFiLlama database
**Solution:**

1. Check protocol list: `python onchain_analytics.py protocols`
2. Use exact slug from DeFiLlama (case-sensitive)
3. Search by partial name in protocol list

### Empty Response

```
Error: No data returned for query
```

**Cause:** Filter too restrictive or data unavailable
**Solution:**

1. Remove filters and retry
2. Check if category/chain exists
3. Try broader time range

## Data Quality Issues

### Missing TVL Data

```
Warning: TVL data unavailable for some protocols
```

**Cause:** New protocols or data collection gaps
**Solution:**

1. Check DeFiLlama directly for protocol
2. Data usually available within 24h of listing

### Stale Data

```
Warning: Data may be stale (last updated: X hours ago)
```

**Cause:** Cache not refreshed
**Solution:**

1. Clear cache: `rm ~/.onchain_analytics_cache.json`
2. Use `--verbose` to see cache status

## Output Issues

### Large Output Truncated

```
[Showing top 50 of 1000+ protocols]
```

**Solution:** Use `--limit` flag or `--format json` for full data

### Encoding Errors

```
UnicodeEncodeError: ...
```

**Solution:**

1. Use `--format json`
2. Set `LANG=en_US.UTF-8`

## Recovery Strategies

### Clear Cache

```bash
rm ~/.onchain_analytics_cache.json
```

### Verbose Mode for Debugging

```bash
python onchain_analytics.py protocols --verbose
```

### Fallback to JSON

If table output fails:

```bash
python onchain_analytics.py protocols --format json > output.json
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
