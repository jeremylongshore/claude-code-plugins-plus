# Error Handling Reference

Common issues and solutions for the DEX Aggregator Router.

## API Errors

### Rate Limit Exceeded

**Error**: `429 Too Many Requests` or `Rate limit exceeded`

**Cause**: Exceeded aggregator API rate limits

**Solution**:

- Wait 60 seconds before retrying
- Set up API keys for higher limits:

  ```bash
  export ONEINCH_API_KEY=your-key  # 5 req/sec vs 1 req/sec
  export ZEROX_API_KEY=your-key    # 10 req/sec vs 3 req/sec
  ```

- The router automatically uses fallback aggregators when one is rate-limited

### Quote Not Found

**Error**: `No quotes available` or empty response

**Cause**: Token pair not supported or insufficient liquidity

**Solution**:

- Verify token symbols are correct (ETH, USDC, not eth, usdc)
- Check if tokens exist on the selected chain
- Try major pairs first (ETH/USDC, ETH/WBTC)
- For exotic tokens, try smaller amounts first

### Authentication Failed

**Error**: `401 Unauthorized` or `Invalid API key`

**Cause**: Invalid or expired API key

**Solution**:

- Regenerate API key from provider dashboard
- Verify environment variable is set correctly:

  ```bash
  echo $ONEINCH_API_KEY  # Should show your key
  ```

- Check API key hasn't been revoked

## Network Errors

### Connection Timeout

**Error**: `Connection timed out` or `ETIMEDOUT`

**Cause**: Network issues or aggregator service down

**Solution**:

- Check your internet connection
- Verify aggregator status pages:
  - 1inch: https://status.1inch.io/
  - 0x: https://status.0x.org/
- Router will automatically fallback to other aggregators

### SSL Certificate Error

**Error**: `SSL: CERTIFICATE_VERIFY_FAILED`

**Cause**: System SSL certificates outdated

**Solution**:

- Update SSL certificates:

  ```bash
  # Ubuntu/Debian
  sudo apt-get update && sudo apt-get install ca-certificates

  # macOS
  /Applications/Python\ 3.x/Install\ Certificates.command
  ```

## Quote Errors

### Quote Expired

**Error**: `Quote expired` or stale data warning

**Cause**: Quote validity window (30s) exceeded

**Solution**:

- Re-fetch quote immediately before execution
- Don't cache quotes for more than 30 seconds
- Use `--no-cache` flag for fresh quotes

### Invalid Token Address

**Error**: `Invalid token address` or `Token not found`

**Cause**: Token symbol not in our mapping

**Solution**:

- Use contract address instead of symbol:

  ```bash
  python dex_router.py 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2 \
                       0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48 1.0
  ```

- Verify token contract on Etherscan

### Insufficient Liquidity

**Error**: `Insufficient liquidity for this trade`

**Cause**: Trade size exceeds available liquidity

**Solution**:

- Reduce trade amount
- Use `--split` to distribute across multiple DEXs
- Try a different token pair with more liquidity
- Check liquidity on DeFiLlama: https://defillama.com/

## Calculation Errors

### Invalid Amount

**Error**: `Invalid amount` or `Cannot parse amount`

**Cause**: Non-numeric or negative amount provided

**Solution**:

- Use decimal format: `1.5` not `1,5`
- Avoid scientific notation
- Ensure positive values only

### Gas Price Error

**Error**: `Could not estimate gas` or `Gas estimation failed`

**Cause**: Complex route or congested network

**Solution**:

- Use `--gas-price` to set manually:

  ```bash
  python dex_router.py ETH USDC 1.0 --gas-price 50
  ```

- Check current gas at https://etherscan.io/gastracker

## Chain Errors

### Unsupported Chain

**Error**: `Chain not supported`

**Cause**: Selected chain not available for aggregator

**Solution**:

- Verify chain is supported:
  - 1inch: Ethereum, Arbitrum, Polygon, Optimism
  - Paraswap: Ethereum, Arbitrum, Polygon, Optimism
  - 0x: Ethereum, Polygon, Arbitrum
- Use `--chain ethereum` for maximum compatibility

### Chain Mismatch

**Error**: `Token not found on chain`

**Cause**: Token address is for different chain

**Solution**:

- Use chain-specific token addresses
- ETH is native on Ethereum, but needs WETH contract on L2s
- Check token addresses per chain on CoinGecko

## Debugging Tips

### Enable Verbose Output

```bash
# See raw API responses
python dex_router.py ETH USDC 1.0 --output json 2>&1 | tee output.json
```

### Test API Connectivity

```bash
# Test 1inch
curl "https://api.1inch.dev/swap/v6.0/1/healthcheck"

# Test Paraswap
curl "https://apiv5.paraswap.io/prices?network=1"

# Test 0x
curl "https://api.0x.org/swap/v1/sources"
```

### Check Environment

```bash
# Verify Python version (3.9+ required)
python --version

# Verify dependencies
pip list | grep -E "httpx|pydantic|rich"

# Check API keys are set
env | grep -E "ONEINCH|ZEROX"
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
