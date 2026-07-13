# Error Handling Reference

## API Errors

### DefiLlama API Unavailable

```
Error: Connection refused / timeout
```

**Cause:** DefiLlama bridges API is down or rate limited.
**Solution:**

1. Wait and retry with exponential backoff
2. Use cached data if available
3. Check DefiLlama status page

### Bridge API Unavailable

```
Error: Protocol API not responding
```

**Cause:** Specific bridge API (Wormhole, LayerZero, etc.) is down.
**Solution:**

1. Try alternative tracking method (on-chain verification)
2. Wait and retry
3. Check bridge status page

### Rate Limited

```
Error: 429 Too Many Requests
```

**Cause:** Exceeded API rate limits.
**Solution:**

1. Reduce request frequency
2. Use caching more aggressively
3. Spread requests over time

## Transaction Tracking Errors

### Transaction Not Found

```
Transaction not found in any bridge
```

**Cause:** TX hash doesn't match any known bridge.
**Solution:**

1. Verify the transaction hash is correct
2. Specify the bridge with `--bridge`
3. Specify source chain with `--chain`
4. Transaction may be too old

### Wrong Bridge Specified

```
Bridge not found: xyz
```

**Cause:** Bridge name not recognized.
**Solution:**

1. Use `python bridge_monitor.py protocols` to see supported bridges
2. Check spelling (case-insensitive)
3. Use bridge ID instead of name

### Pending Too Long

```
Transaction still pending after 60 minutes
```

**Cause:** Bridge congestion, low gas, or failure.
**Solution:**

1. Check source chain for confirmation
2. Verify transaction wasn't reverted
3. Contact bridge support if stuck

## Chain Errors

### Unsupported Chain

```
Error: No RPC URL for chain: xyz
```

**Cause:** Chain not in supported list.
**Solution:**

1. Use `python bridge_monitor.py chains` to see supported chains
2. Set custom RPC via environment variable: `{CHAIN}_RPC_URL`
3. Check chain name spelling

### RPC Connection Failed

```
Error: RPC connection timeout
```

**Cause:** RPC endpoint is overloaded or down.
**Solution:**

1. Set custom RPC URL via environment variable
2. Try a different RPC provider
3. Check if chain is experiencing issues

## Comparison Errors

### Route Not Supported

```
No bridges support ethereum → xyz
```

**Cause:** Destination chain not supported by any bridge.
**Solution:**

1. Verify destination chain exists
2. Check individual bridge support with `python bridge_monitor.py detail --bridge`
3. Consider multi-hop route

### No Fee Estimates

```
No fee estimates available
```

**Cause:** Couldn't get fee data from any bridge.
**Solution:**

1. Check if bridges are operational
2. Verify chains are supported
3. Try with a different token

## Common Error Patterns

| Error | Likely Cause | Quick Fix |
|-------|--------------|-----------|
| Connection timeout | API overload | Retry with backoff |
| 429 Too Many Requests | Rate limited | Wait and retry |
| Bridge not found | Wrong name | Check `protocols` command |
| TX not found | Wrong hash/bridge | Verify hash, try all bridges |
| Chain not supported | Typo or unsupported | Check `chains` command |
| No estimates | Route not supported | Check bridge details |

## Fallback Behavior

The system uses this fallback chain:

1. **Protocol API** - Bridge-specific API
2. **DefiLlama API** - Aggregated data
3. **On-Chain RPC** - Direct blockchain verification
4. **Cached Data** - Last known good data
5. **Error** - If all fail

## Debug Mode

Enable verbose output for troubleshooting:

```bash
python bridge_monitor.py --verbose tvl
```

This shows:

- API requests being made
- Response times
- Cache hits/misses
- Error details

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
