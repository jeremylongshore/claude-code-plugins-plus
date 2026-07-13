# Error Handling Reference

## Exchange API Errors

### Authentication Failures

**API Key Invalid**

- Error: `Invalid API key` or `Signature mismatch`
- Causes: Expired key, wrong permissions, clock drift
- Solution:
  1. Regenerate API keys on exchange
  2. Ensure read-only permissions enabled
  3. Sync system clock: `sudo ntpdate pool.ntp.org`
  4. Check key has futures/derivatives permissions

**IP Whitelist Rejected**

- Error: `IP not in whitelist`
- Solution: Add current IP to exchange API settings or remove whitelist restriction

### Rate Limiting

**Too Many Requests**

- Error: `429 Too Many Requests` or `Rate limit exceeded`
- Threshold varies by exchange:
  - Binance: 1200 requests/minute (weighted)
  - Bybit: 120 requests/minute
  - OKX: 60 requests/2 seconds
  - Deribit: 100 requests/second
- Solution:
  1. Implement exponential backoff
  2. Use WebSocket for real-time data
  3. Cache static data (max pain, OI levels)
  4. Batch requests where possible

**Weight Exceeded**

- Error: `Request weight exceeded`
- Solution: Some endpoints cost more weight; use lightweight endpoints or wait

## Data Quality Errors

### Missing or Stale Data

**No Data Available**

- Error: `No funding data available for {symbol}`
- Causes: Symbol not listed, exchange down, maintenance
- Solution:
  1. Verify symbol exists on exchange
  2. Check exchange status page
  3. Fall back to alternative exchange
  4. Use mock data for testing

**Stale Timestamp**

- Error: Data timestamp older than expected
- Solution:
  1. Check WebSocket connection alive
  2. Verify exchange API operational
  3. Increase polling frequency
  4. Implement freshness checks

### Invalid Values

**Negative Funding Rate**

- Not an error - negative funding is valid (shorts pay longs)
- Just ensure your calculations handle negative correctly

**Zero Open Interest**

- May indicate:
  - New symbol with no positions
  - Data not yet populated
  - Exchange maintenance
- Solution: Filter out or flag as incomplete

**Implausible Values**

- Funding rate > 10% per 8h → likely data error
- IV > 500% → verify or exclude
- Solution: Implement sanity checks and outlier filtering

## Calculation Errors

### Division by Zero

**Empty Exchange List**

- Error: `Division by zero` in weighted average
- Cause: No exchanges returned data
- Solution:

```python
if not exchanges:
    raise ValueError("No exchange data available")
total = sum(oi.value for oi in exchanges)
if total == 0:
    raise ValueError("Total OI is zero")
```

### Decimal Precision

**Precision Loss**

- Error: Incorrect basis calculations due to floating point
- Solution: Use `Decimal` for all price/rate calculations

```python
from decimal import Decimal, ROUND_HALF_UP
basis = (futures - spot) / spot
basis_pct = float(basis.quantize(Decimal('0.0001')))
```

### Date Handling

**Invalid Expiry Format**

- Error: `strptime` fails on expiry string
- Cause: Different exchange formats (YYYYMMDD vs YYYY-MM-DD)
- Solution:

```python
formats = ['%Y-%m-%d', '%Y%m%d', '%d%b%y']
for fmt in formats:
    try:
        return datetime.strptime(expiry, fmt)
    except ValueError:
        continue
raise ValueError(f"Unknown expiry format: {expiry}")
```

**Expiry Already Passed**

- Warning: Analyzing expired contract
- Solution: Filter to active expiries only

## Network Errors

### Connection Failures

**Connection Timeout**

- Error: `Connection timed out`
- Solution:
  1. Increase timeout: `timeout=30`
  2. Use retry with backoff
  3. Switch to backup endpoint
  4. Check network connectivity

**SSL Certificate Error**

- Error: `SSL: CERTIFICATE_VERIFY_FAILED`
- Solution:
  1. Update CA certificates
  2. For testing only: `verify=False` (not recommended for production)

### WebSocket Issues

**Disconnected**

- Error: WebSocket connection closed unexpectedly
- Solution:
  1. Implement reconnection logic
  2. Use heartbeat/ping-pong
  3. Handle partial messages

## Recovery Strategies

### Graceful Degradation

1. **Exchange Fallback**: If primary exchange fails, try alternatives
2. **Cached Data**: Use last known good value with timestamp warning
3. **Partial Results**: Return available data, flag missing exchanges

### Retry Logic

```python
import time

def fetch_with_retry(func, max_retries=3, base_delay=1):
    for attempt in range(max_retries):
        try:
            return func()
        except RateLimitError:
            delay = base_delay * (2 ** attempt)
            time.sleep(delay)
        except ConnectionError:
            if attempt < max_retries - 1:
                time.sleep(base_delay)
            else:
                raise
    raise RetryExhaustedError()
```

### Circuit Breaker

Track failures per exchange and temporarily disable problematic sources:

```python
failures = defaultdict(int)
disabled_until = {}

def check_exchange_health(exchange):
    if exchange in disabled_until:
        if datetime.now() < disabled_until[exchange]:
            return False
        del disabled_until[exchange]
    return True

def record_failure(exchange):
    failures[exchange] += 1
    if failures[exchange] >= 3:
        disabled_until[exchange] = datetime.now() + timedelta(minutes=5)
```

## Common Issues by Exchange

### Binance

- Issue: Weight limits are complex (different endpoints cost different)
- Solution: Track weight counter from response headers

### Bybit

- Issue: V5 API has different structure than V3
- Solution: Use unified V5 endpoints consistently

### OKX

- Issue: Requires specific headers for authentication
- Solution: Include `OK-ACCESS-*` headers correctly

### Deribit

- Issue: Options data requires authentication
- Solution: Use API key even for read-only data

### BitMEX

- Issue: Rate limits are very strict
- Solution: Aggressive caching, minimal polling

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
