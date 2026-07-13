# Error Handling Reference

Comprehensive error codes and solutions for arbitrage opportunity detection.

---

## Price Data Errors

### ERR_PRICE_STALE

**Error**: Price data exceeds maximum staleness threshold
**Cause**: Exchange API returned outdated data or connection issues
**Solution**:

- Check `max_staleness` setting in config (default: 30 seconds)
- Verify exchange API connectivity
- Switch to alternative data source
- Exclude stale quotes from analysis

### ERR_PRICE_UNAVAILABLE

**Error**: Could not fetch price for trading pair
**Cause**: Exchange doesn't list the pair or API timeout
**Solution**:

- Verify trading pair exists on target exchange
- Check exchange API status page
- Use alternative exchange for that pair
- Implement fallback data sources

### ERR_BID_ASK_INVERTED

**Error**: Bid price exceeds ask price
**Cause**: Data corruption, API error, or extreme volatility
**Solution**:

- Skip the quote and log warning
- Fetch fresh data
- This indicates unreliable data source

---

## Rate Limiting Errors

### ERR_RATE_LIMIT_CEX

**Error**: Exchange API rate limit exceeded
**Cause**: Too many requests in rate limit window
**Solution**:

- Implement exponential backoff (config: `backoff_multiplier`)
- Add delay between requests (config: `request_delay_ms`)
- Use API key for higher limits
- Batch requests where possible

### ERR_RATE_LIMIT_DEX

**Error**: DEX subgraph rate limit exceeded
**Cause**: Too many GraphQL queries
**Solution**:

- Reduce query frequency
- Cache pool data locally
- Use batch queries
- Consider self-hosted subgraph

### ERR_API_QUOTA_EXHAUSTED

**Error**: Daily/monthly API quota reached
**Cause**: Free tier limits exceeded
**Solution**:

- Upgrade API subscription tier
- Switch to alternative provider
- Implement data caching
- Reduce polling frequency

---

## Triangular Arbitrage Errors

### ERR_NO_PATH_FOUND

**Error**: No triangular path exists between tokens
**Cause**: Missing trading pairs for complete cycle
**Solution**:

- Verify all three pairs exist on exchange
- Check pair liquidity (may be delisted)
- Try different token combinations
- Use alternative exchange

### ERR_INSUFFICIENT_LIQUIDITY

**Error**: Pool/order book liquidity below minimum threshold
**Cause**: Trading pair has low volume
**Solution**:

- Adjust `min_liquidity` threshold
- Skip low-liquidity pairs
- Use larger, more liquid markets
- Factor in higher slippage estimate

### ERR_PATH_NEGATIVE_PROFIT

**Error**: All triangular paths result in losses after fees
**Cause**: Markets are efficient, no arbitrage exists
**Solution**:

- This is normal - markets are usually efficient
- Continue monitoring for opportunities
- Adjust `min_profit_pct` threshold
- Check fee calculations are accurate

---

## Exchange Connectivity Errors

### ERR_EXCHANGE_UNAVAILABLE

**Error**: Cannot connect to exchange API
**Cause**: Exchange maintenance, network issues, or API changes
**Solution**:

- Check exchange status page
- Retry with exponential backoff
- Use alternative exchange
- Verify API base URL is correct

### ERR_AUTH_FAILED

**Error**: API key authentication failed
**Cause**: Invalid/expired API key or incorrect signature
**Solution**:

- Regenerate API keys
- Check key permissions (read access required)
- Verify system clock sync (for signature)
- Ensure API key hasn't expired

### ERR_EXCHANGE_NOT_SUPPORTED

**Error**: Exchange not configured in system
**Cause**: Attempting to use unconfigured exchange
**Solution**:

- Add exchange to `config/settings.yaml`
- Verify exchange name spelling
- Check supported exchanges list
- Configure fee structure

---

## DEX-Specific Errors

### ERR_GAS_ESTIMATE_FAILED

**Error**: Could not estimate gas for DEX swap
**Cause**: RPC node issues or invalid transaction
**Solution**:

- Use default gas estimates from config
- Switch to alternative RPC endpoint
- Verify pool contract address
- Check for contract upgrades

### ERR_SUBGRAPH_SYNC

**Error**: DEX subgraph is behind blockchain
**Cause**: Subgraph indexing delay
**Solution**:

- Use on-chain RPC calls instead
- Wait for subgraph to catch up
- Factor in data delay in analysis
- Use alternative subgraph endpoint

### ERR_POOL_DEPRECATED

**Error**: Liquidity pool no longer active
**Cause**: V2→V3 migration or pool closure
**Solution**:

- Update pool addresses in config
- Switch to newer protocol version
- Remove deprecated pool from scan

---

## Calculation Errors

### ERR_INVALID_AMOUNT

**Error**: Trade amount is invalid
**Cause**: Non-numeric input or negative value
**Solution**:

- Validate amount before calculation
- Ensure positive numeric value
- Use Decimal for precision

### ERR_FEE_EXCEEDS_PROFIT

**Error**: Total fees exceed gross profit
**Cause**: Spread too small for trade size
**Solution**:

- Increase trade amount (larger size = better fee ratio)
- Use exchanges with lower fees
- Wait for larger spread opportunities
- Skip unprofitable opportunities

### ERR_SLIPPAGE_OVERFLOW

**Error**: Estimated slippage exceeds safe threshold
**Cause**: Trade size too large for liquidity
**Solution**:

- Reduce trade amount
- Split into smaller trades
- Use limit orders
- Target higher liquidity pools

---

## Risk Assessment Errors

### WARN_HIGH_RISK_OPPORTUNITY

**Warning**: Opportunity flagged as high/extreme risk
**Cause**: Multiple risk factors present
**Solution**:

- Review risk factors in output
- Verify data freshness
- Consider smaller position size
- Skip if outside risk tolerance

### WARN_DATA_STALENESS

**Warning**: Some quotes exceed staleness threshold
**Cause**: Delayed data from one or more sources
**Solution**:

- Refresh stale data before execution
- Factor staleness into risk assessment
- Use only fresh data for decisions

---

## Recovery Procedures

### General Recovery

1. Check exchange/API status pages
2. Verify network connectivity
3. Review config settings
4. Check API key validity
5. Restart with fresh data

### Data Recovery

1. Clear cached price data
2. Refetch from all sources
3. Validate data consistency
4. Resume normal operation

### Emergency Stop

If encountering repeated errors:

1. Stop monitoring loop
2. Review error logs
3. Fix configuration issues
4. Test with single request
5. Resume monitoring gradually

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
