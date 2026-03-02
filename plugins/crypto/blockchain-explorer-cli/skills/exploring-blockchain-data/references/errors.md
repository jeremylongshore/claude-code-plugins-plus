# Error Handling Reference

## API Errors

### Transaction Not Found
```
Error: Transaction not found
Hash: 0x1234...
```

**Causes:**
- Transaction not yet mined (pending in mempool)
- Wrong chain selected
- Invalid transaction hash

**Solutions:**
1. Wait and retry - transaction may be pending
2. Try other chains: `--chain polygon`, `--chain arbitrum`
3. Verify hash format (66 characters, starts with 0x)
4. Check mempool explorers for pending transactions

### Rate Limit Exceeded
```
Error: Explorer API error: Max rate limit reached
```

**Causes:**
- Too many requests in short period
- No API key configured (5/sec limit)
- API key quota exhausted

**Solutions:**
1. Wait 1-5 seconds and retry
2. Add API key for higher limits:
   ```bash
   export ETHERSCAN_API_KEY=your_key_here
   ```
3. Use caching to reduce requests
4. Upgrade to paid API tier

### RPC Connection Failed
```
Error: RPC error: {'code': -32000, 'message': 'execution timeout'}
```

**Causes:**
- RPC endpoint overloaded
- Network connectivity issues
- Complex query timeout

**Solutions:**
1. Retry with different RPC endpoint
2. Check internet connection
3. Use dedicated RPC (Alchemy, Chainstack, Infura, or Quicknode)
4. Simplify query or add timeout

### Invalid Address Format
```
Error: Invalid address: 0xinvalid
```

**Causes:**
- Missing or extra characters
- Invalid checksum (mixed case)
- Non-hex characters

**Solutions:**
1. Verify 42 characters (with 0x prefix)
2. Use checksummed address from explorer
3. Convert to lowercase if checksum fails

## Chain-Specific Errors

### Wrong Chain
```
Error: Transaction not found
```
When transaction exists on different chain.

**Solutions:**
1. Try common chains in order:
   ```bash
   python blockchain_explorer.py tx 0x... --chain ethereum
   python blockchain_explorer.py tx 0x... --chain polygon
   python blockchain_explorer.py tx 0x... --chain arbitrum
   ```
2. Check original source for chain info
3. Use multi-chain search tools

### Contract Not Verified
```
Error: Contract source code not verified
```

**Causes:**
- Contract source not published to explorer
- Proxy contract (implementation elsewhere)

**Solutions:**
1. Use known function signatures database
2. Check if proxy - find implementation address
3. Decode manually using known ABIs

## Token Resolution Errors

### Unknown Token
```
Token: ??? (Unknown Token)
```

**Causes:**
- New or obscure token
- CoinGecko doesn't track it
- Wrong contract address

**Solutions:**
1. Check token contract on explorer
2. Look up on DEX (Uniswap, SushiSwap)
3. Manually specify decimals if known

### Price Unavailable
```
Price: N/A
```

**Causes:**
- Token not on CoinGecko
- API rate limited
- Very low liquidity token

**Solutions:**
1. Check DEX for on-chain price
2. Use alternative price feed
3. Calculate from LP reserves

## Output Errors

### Encoding Issues
```
UnicodeEncodeError: 'ascii' codec can't encode character
```

**Solutions:**
1. Use `--format json` for safe output
2. Set terminal encoding: `export LANG=en_US.UTF-8`
3. Pipe to file: `> output.txt`

### Large Output Truncated
```
[Output truncated - use --format json for full data]
```

**Solutions:**
1. Use `--format json` and redirect to file
2. Reduce `--limit` parameter
3. Process in batches

## Environment Setup Errors

### Missing Dependencies
```
ImportError: No module named 'requests'
```

**Solutions:**
```bash
pip install requests
# Or for full setup:
pip install requests web3
```

### API Key Not Found
```
Warning: No API key found for ETHERSCAN_API_KEY
Using free tier (5 req/sec limit)
```

**Solutions:**
1. Get free API key from etherscan.io
2. Set environment variable:
   ```bash
   export ETHERSCAN_API_KEY=your_key
   ```
3. Add to shell profile for persistence

## Recovery Strategies

### Automatic Retry
The CLI implements exponential backoff:
- 1st retry: 1 second delay
- 2nd retry: 2 second delay
- 3rd retry: 4 second delay
- Max retries: 3

### Fallback Chain
When transaction not found, try:
1. ethereum
2. polygon
3. arbitrum
4. optimism
5. bsc

### Cache Recovery
Clear corrupted cache:
```bash
rm ~/.blockchain_explorer_cache.json
```

## Debug Mode

Enable verbose output for troubleshooting:
```bash
python blockchain_explorer.py tx 0x... --verbose
```

Shows:
- API requests being made
- Response times
- Cache hits/misses
- Rate limit status
