# Error Handling Reference

## RPC Errors

**eth_feeHistory Not Supported**

- Error: `RPC error: Method not found`
- Cause: Chain doesn't support EIP-1559 fee history
- Solution: Falls back to `eth_gasPrice` automatically

**RPC Connection Timeout**

- Error: `Connection timed out` or `ETIMEDOUT`
- Cause: RPC node unresponsive or network issues
- Solution: Falls back to explorer API; check network; try alternate RPC

**Rate Limited by RPC**

- Error: `429 Too Many Requests`
- Cause: Exceeded RPC rate limits
- Solution: Uses cached data; wait before retry; use private RPC

## Explorer API Errors

**Etherscan API Key Missing**

- Error: `Max rate limit reached` for free tier
- Cause: No API key, limited to 1 req/5s
- Solution: Set `ETHERSCAN_API_KEY` environment variable

**Invalid API Response**

- Error: `status: 0` in response
- Cause: API error or invalid request
- Solution: Check API key; verify chain support; use RPC fallback

## Price Feed Errors

**CoinGecko Rate Limit**

- Error: `429` response from price API
- Cause: Exceeded free tier (10-50 req/min)
- Solution: Uses cached price; default to $3000 ETH / $1 MATIC

**Price Not Available**

- Error: Token not found in price feed
- Cause: New/obscure token not tracked
- Solution: Uses default price estimate

## Pattern Analysis Errors

**No Historical Data**

- Error: Empty patterns or "Using defaults"
- Cause: New installation, no recorded history
- Solution: Uses default patterns; collects data over time

**Corrupted History File**

- Error: `JSONDecodeError` on history load
- Cause: File corruption or incomplete write
- Solution: Resets to empty history; starts fresh

## Chain-Specific Errors

**Unsupported Chain**

- Error: `Chain 'xyz' not supported`
- Cause: Chain not in configuration
- Solution: Use supported chains: ethereum, polygon, arbitrum, optimism, base

**L2 Gas Estimation**

- Error: Unexpected gas values on L2
- Cause: L2s have different fee structures
- Solution: L2 gas is typically much lower; estimates still accurate

## Fallback Chain

The system uses a fallback chain for resilience:

```
1. eth_feeHistory (EIP-1559) → Best data
   ↓ fails
2. eth_gasPrice (legacy) → Estimates tiers
   ↓ fails
3. Explorer API (Etherscan) → External oracle
   ↓ fails
4. Default values → 30 gwei baseline
```

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `ETHERSCAN_API_KEY` | Explorer API auth | None (rate limited) |
| `ETHEREUM_RPC_URL` | Custom Ethereum RPC | Public endpoints |
| `POLYGON_RPC_URL` | Custom Polygon RPC | Public endpoints |
| `ARBITRUM_RPC_URL` | Custom Arbitrum RPC | Public endpoints |

## Common Fixes

1. **Slow response**: Enable caching, check network
2. **Inaccurate estimates**: Verify chain selection, check RPC sync
3. **Missing patterns**: Wait for data collection, use defaults
4. **High variance**: Normal during network congestion

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
