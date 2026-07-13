# Error Handling Guide

## API Errors

### No API Key Configured

```
Error: No API key configured, using mock data
```

**Cause**: WHALE_ALERT_API_KEY environment variable not set
**Solution**:

1. Get API key from https://whale-alert.io
2. Set environment variable: `export WHALE_ALERT_API_KEY=your_key`
3. Or add to config file

### Rate Limit Exceeded

```
Error: Rate limit exceeded. Please wait before making more requests.
```

**Cause**: Too many API requests in short time
**Solution**:

- Free tier: 10 requests/minute
- Wait 60 seconds and retry
- Upgrade to paid tier for higher limits

### Invalid API Key

```
Error: Invalid API key
```

**Cause**: API key is incorrect or expired
**Solution**: Verify key at

### Network Timeout

```
Error: Connection timed out
```

**Cause**: Network issues or API unavailable
**Solution**:

- Check internet connection
- Retry after a few seconds
- Check https://status.whale-alert.io

## Wallet Label Errors

### Watchlist File Permissions

```
Error: Cannot write to watchlist file
```

**Cause**: No write permission to ~/.whale_watchlist.json
**Solution**: Check file permissions or specify different path

### Invalid Address Format

```
Error: Invalid wallet address format
```

**Cause**: Malformed blockchain address
**Solution**:

- Ethereum: Should start with 0x and be 42 characters
- Bitcoin: Should start with 1, 3, or bc1
- Verify address on block explorer

## Price Service Errors

### Price Not Available

```
Warning: Price unavailable for TOKEN
```

**Cause**: Token not listed on CoinGecko or API error
**Solution**:

- USD value will show as N/A
- Verify token symbol is correct
- Check if token is listed on CoinGecko

### Stale Price Data

```
Warning: Using cached price data (may be stale)
```

**Cause**: API unavailable, using cached data
**Solution**: Data is still usable but may not be current

## Common Workflow Errors

### No Transactions Found

```
No whale transactions found.
```

**Cause**: No transactions matching filters
**Solution**:

- Lower --min-value threshold
- Remove --chain filter
- Try different time range

### Empty Watchlist

```
Watchlist is empty. Add wallets with: --watch <address> --name <name>
```

**Cause**: No wallets added to watchlist
**Solution**: Add wallets using the watch command

## Debugging

### Enable Verbose Mode

```bash
python whale_monitor.py recent -v
```

Shows API calls and detailed error information.

### Check API Status

```bash
python whale_monitor.py status
```

Shows current API status and rate limits.

### Test Individual Components

```bash
python whale_api.py        # Test API client
python wallet_labels.py    # Test label database
python price_service.py    # Test price lookups
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
