# Error Handling Reference

## RPC and Network Errors

### Connection Timeout

```
Error: RPC request timed out
Cause: Node unresponsive or network issues
```

**Solutions:**

- Switch to backup RPC endpoint (see `config/settings.yaml`)
- Increase timeout in requests (default 30s)
- Verify network connectivity
- Check if public RPC is rate-limited

### Invalid Response

```
Error: RPC error: {'code': -32000, 'message': 'execution reverted'}
Cause: Contract call failed or invalid parameters
```

**Solutions:**

- Verify address is a valid contract
- Check if contract is deployed on the specified chain
- Ensure correct chain is selected

### Rate Limiting

```
Error: 429 Too Many Requests
Cause: Exceeded API rate limits
```

**Solutions:**

- Add ETHERSCAN_API_KEY for higher limits
- Implement request throttling (200ms delay)
- Use caching for token info
- Batch requests where possible

## Address Validation Errors

### Invalid Address Format

```
Error: Address must start with 0x
Error: Address must be 42 characters
Error: Address contains invalid hex characters
```

**Solutions:**

- Verify address starts with `0x`
- Check address is exactly 42 characters
- Ensure only valid hex characters (0-9, a-f)

### ENS Not Supported

```
Error: ENS resolution not yet supported
Cause: .eth domain provided instead of hex address
```

**Solutions:**

- Use hex address (0x...) instead of ENS name
- Resolve ENS externally and provide result
- Feature planned for future release

### Invalid Checksum

```
Error: Address checksum validation failed
Cause: Mixed case address with incorrect checksum
```

**Solutions:**

- Use all lowercase address
- Verify address via block explorer
- Copy address directly from wallet

## Block Explorer API Errors

### Authentication Failed

```
Error: Invalid API key
Cause: ETHERSCAN_API_KEY invalid or missing
```

**Solutions:**

- Register at etherscan.io for free API key
- Set ETHERSCAN_API_KEY environment variable
- Verify key is for correct chain (etherscan vs bscscan)

### No Data Found

```
Error: No transactions found
Result: Empty approval list
```

**Not an error** - wallet may have:

- No token approvals
- No transactions in the specified period
- Only native token transfers (no ERC20)

### Contract Not Verified

```
Warning: Contract source code not verified
Cause: Spender contract not verified on explorer
```

**Implications:**

- Cannot determine contract name
- Flagged as potential risk
- Manual verification recommended

## Token Parsing Errors

### Invalid Token Data

```
Error: Error parsing log: ...
Cause: Malformed approval event data
```

**Solutions:**

- Skip problematic tokens (handled automatically)
- Token may be non-standard ERC20
- Verbose mode shows details

### Decimal Overflow

```
Error: Could not parse allowance
Cause: Invalid decimal value in approval
```

**Solutions:**

- Handled as raw integer
- Display as "Unknown" allowance
- Check token contract directly

## Risk Scoring Errors

### Missing Data

```
Warning: No approval data for scoring
Cause: Scanner returned empty results
```

**Solutions:**

- Returns neutral score (100)
- Check address is correct
- Verify chain selection

### API Integration Errors

```
Error: GoPlus API unavailable
Error: TokenSniffer timeout
```

**Solutions:**

- Security APIs are optional
- Falls back to basic analysis
- Enable/disable in config

## Common Issues by Command

### approvals

| Issue | Cause | Solution |
|-------|-------|----------|
| No approvals | Never approved tokens | Normal - wallet is clean |
| Many unknown spenders | Contracts not verified | Review manually |
| Rate limit | Too many tokens | Add API key |

### scan

| Issue | Cause | Solution |
|-------|-------|----------|
| Slow scan | Many transactions | Reduce --days |
| Partial results | API timeouts | Retry or split scan |
| High score but flagged | Edge cases | Review factors |

### history

| Issue | Cause | Solution |
|-------|-------|----------|
| No transactions | Inactive wallet | Increase --days |
| Missing contracts | Cache cold | Re-run command |
| Slow analysis | 1000+ txs | Use smaller window |

### report

| Issue | Cause | Solution |
|-------|-------|----------|
| File not created | Permission denied | Check write access |
| Truncated output | Very large wallet | Use --json |
| Missing sections | API errors | Check verbose output |

## Environment Variable Issues

### Missing API Keys

```
Warning: ETHERSCAN_API_KEY not set
Result: Lower rate limits, some features limited
```

**Solutions:**

- Register at explorer APIs for free keys
- Set in environment: `export ETHERSCAN_API_KEY=...`
- Add to `.env` file in project root

### Custom RPC Not Working

```
Error: Custom RPC connection failed
Cause: ETHEREUM_RPC_URL invalid
```

**Solutions:**

- Verify RPC URL is reachable
- Check if URL requires authentication
- Test with: `curl -X POST <url> -d '{"jsonrpc":"2.0","method":"net_version","params":[],"id":1}'`

## Recovery Strategies

### Partial Failures

If scan partially completes:

1. Check which component failed (approvals, history, score)
2. Run individual commands for debugging
3. Use `--verbose` for detailed error info

### Data Consistency

If results seem incorrect:

1. Verify address on block explorer
2. Check chain selection matches asset location
3. Clear token cache (restart script)

### Performance Issues

If scans are slow:

1. Add block explorer API key
2. Reduce analysis window (--days)
3. Use JSON output for large wallets
4. Consider running during off-peak hours

## Debugging Tips

### Enable Verbose Mode

```bash
wallet_auditor.py scan 0x... --verbose
```

Shows:

- API requests being made
- Token info lookups
- Error details

### Check Raw Data

```bash
wallet_auditor.py report 0x... --json
```

Returns structured data for manual inspection.

### Test Connectivity

```bash
# Test RPC
curl -X POST https://eth.llamarpc.com -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'

# Test Explorer API
curl "https://api.etherscan.io/api?module=stats&action=ethsupply"
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
