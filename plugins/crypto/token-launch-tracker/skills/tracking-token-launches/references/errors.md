# Error Handling Reference

## RPC Connection Errors

### Connection Timeout
```
Error: RPC connection timeout after 30s
```
**Cause:** RPC endpoint is overloaded or unreachable.
**Solution:**
1. Try a different RPC URL with `--rpc-url`
2. Use a backup RPC provider (Alchemy, Chainstack, Infura, or QuickNode)
3. Reduce request frequency

### RPC Rate Limited
```
Error: 429 Too Many Requests
```
**Cause:** Exceeded RPC provider rate limits.
**Solution:**
1. Add delay between requests
2. Upgrade to paid RPC tier
3. Use multiple RPC endpoints with round-robin

### Invalid Chain
```
Error: Unsupported chain: xyz
```
**Cause:** Chain not in supported list.
**Solution:**
1. Use `python launch_tracker.py chains` to see supported chains
2. Check spelling (lowercase required)
3. Add custom chain config if needed

## Event Parsing Errors

### No Pairs Found
```
No new pairs found in the specified timeframe.
```
**Cause:** No PairCreated events in time window.
**Solution:**
1. Extend the time window with `--hours`
2. Check if correct chain is selected
3. Verify DEX is active on that chain

### Log Parsing Failed
```
Error parsing log: list index out of range
```
**Cause:** Unexpected event format (V3 vs V2).
**Solution:**
1. Check DEX version compatibility
2. Verify factory address is correct
3. Enable `--verbose` for debugging

## Contract Analysis Errors

### Bytecode Not Found
```
Error: Contract has no bytecode
```
**Cause:** Address is not a contract (EOA) or wrong network.
**Solution:**
1. Verify address is a contract
2. Check correct chain is selected
3. Confirm address checksum

### ABI Decoding Failed
```
Error decoding string: Unknown
```
**Cause:** Non-standard ERC20 implementation.
**Solution:**
1. Use `--verbose` to see raw data
2. Token may use bytes32 for name/symbol
3. Some tokens have non-standard decimals

### Verification Check Failed
```
Verification check error: API key invalid
```
**Cause:** Etherscan API key issues.
**Solution:**
1. Set `ETHERSCAN_API_KEY` environment variable
2. Use `--etherscan-key` flag
3. Check API key is valid for that chain

## Token Analysis Errors

### Risk Analysis Incomplete
```
Warning: Some risk indicators could not be checked
```
**Cause:** Limited bytecode or API access.
**Solution:**
1. Check if contract is verified
2. Provide Etherscan API key
3. Some indicators require source code

### Proxy Detection Failed
```
Warning: Could not determine if contract is proxy
```
**Cause:** Storage slot access issue.
**Solution:**
1. Some RPCs don't support eth_getStorageAt
2. Use a full node RPC
3. Proxy detection is best-effort

## Environment Errors

### Missing Dependencies
```
ImportError: requests library required
```
**Cause:** Python requests not installed.
**Solution:**
```bash
pip install requests
```

### Environment Variable Missing
```
Error: No RPC URL configured
```
**Cause:** Chain RPC URL not found.
**Solution:**
1. Set `{CHAIN}_RPC_URL` environment variable
2. Use `--rpc-url` flag
3. Check config/settings.yaml

## Common Error Patterns

| Error | Likely Cause | Quick Fix |
|-------|--------------|-----------|
| Connection timeout | RPC overloaded | Use backup RPC |
| 429 Too Many Requests | Rate limited | Add delay |
| No pairs found | Wrong timeframe | Increase --hours |
| Bytecode not found | Wrong address/chain | Verify address |
| Unknown token | Non-standard ERC20 | Use --verbose |
| API key invalid | Wrong chain API | Match key to chain |

## Fallback Chain

The system uses this fallback chain for RPC failures:

1. **Primary RPC** - Configured URL
2. **Environment Variable** - `{CHAIN}_RPC_URL`
3. **Default Public RPC** - From settings.yaml
4. **Error** - If all fail

## Debug Mode

Enable verbose output for troubleshooting:
```bash
python launch_tracker.py --verbose recent --chain ethereum
```

This shows:
- RPC requests being made
- Raw response data
- Parsing steps
- Analysis progress
