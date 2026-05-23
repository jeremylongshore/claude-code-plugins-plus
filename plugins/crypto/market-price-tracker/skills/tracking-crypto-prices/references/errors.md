# Error Handling Reference

Comprehensive guide to errors, causes, and solutions for the tracking-crypto-prices skill.

## Error Categories

### 1. API Errors

#### RateLimitError

**Message:** `Rate limit exceeded. Retry after Xs`

**Cause:** CoinGecko API rate limit reached (10-50 calls/minute for free tier).

**Solution:**

1. Wait for the indicated retry period
2. Enable caching to reduce API calls
3. Consider getting a CoinGecko API key for higher limits

**Prevention:**

```yaml
# In config/settings.yaml
cache:
  enabled: true
  spot_ttl: 30  # Cache spot prices for 30 seconds
```

---

#### NetworkError

**Message:** `Connection failed: [details]` or `Request timed out`

**Cause:** No internet connection or CoinGecko API unreachable.

**Solution:**

1. Check internet connection
2. Cached data will be used automatically if available
3. yfinance fallback will be attempted if configured

**Fallback Behavior:**

```
Primary: CoinGecko API
   ↓ (fails)
Fallback: yfinance (if installed)
   ↓ (fails)
Last Resort: Stale cache (if --allow-stale)
```

---

#### SymbolNotFoundError

**Message:** `Unknown symbol: XYZ`

**Cause:** The cryptocurrency ticker or CoinGecko ID doesn't exist.

**Solution:**

1. Check spelling (symbols are case-insensitive)
2. Use `--list` to search for valid symbols:

   ```bash
   python price_tracker.py --list --query bitcoin
   ```

3. Use CoinGecko ID instead of ticker (e.g., `avalanche-2` not `AVAX`)

**Common Mapping Issues:**

| Ticker | CoinGecko ID | Notes |
|--------|--------------|-------|
| AVAX | avalanche-2 | Not "avalanche" |
| MATIC | matic-network | Polygon network |
| COMP | compound-governance-token | Full name |
| CRV | curve-dao-token | Full name |

---

### 2. Cache Errors

#### Cache Stale Warning

**Message:** `Warning: Using stale cache for XYZ`

**Cause:** Fresh data unavailable, returning expired cache entry.

**Solution:**

- Not a critical error; stale data is returned with `_stale: true` flag
- Use `--no-cache` to force fresh fetch
- Clear cache with `--clear-cache` if data seems corrupted

---

#### Cache Write Failed

**Message:** Silent failure (logged in verbose mode)

**Cause:** Cannot write to cache directory (permissions or disk space).

**Solution:**

1. Check cache directory permissions:

   ```bash
   ls -la ./data/
   ```

2. Ensure disk space available
3. Configure alternate cache directory in settings.yaml

---

### 3. Configuration Errors

#### Missing Dependencies

**Message:** `ImportError: No module named 'requests'`

**Cause:** Required Python packages not installed.

**Solution:**

```bash
pip install requests pandas yfinance
```

Optional packages:

```bash
pip install pyyaml python-dotenv
```

---

#### Invalid Configuration

**Message:** Various YAML parsing errors

**Cause:** Malformed settings.yaml file.

**Solution:**

1. Validate YAML syntax
2. Check indentation (use spaces, not tabs)
3. Delete settings.yaml to use defaults

**Validation:**

```bash
python -c "import yaml; yaml.safe_load(open('config/settings.yaml'))"
```

---

#### Unknown Watchlist

**Message:** `Error: Unknown watchlist 'xyz'`

**Cause:** Requested watchlist not defined in configuration.

**Solution:**

1. Use a predefined watchlist: `top10`, `defi`, `layer2`, `stablecoins`, `memecoins`
2. Define custom watchlist in settings.yaml:

   ```yaml
   watchlists:
     custom:
       - bitcoin
       - ethereum
       - solana
   ```

---

### 4. Output Errors

#### File Write Error

**Message:** `Error writing to output file`

**Cause:** Cannot write to specified output path.

**Solution:**

1. Check directory exists
2. Check file permissions
3. Ensure path is valid

---

## Error Handling Strategy

### Automatic Fallback Chain

```
1. CoinGecko API (primary)
   ↓ RateLimitError or NetworkError
2. yfinance (fallback)
   ↓ ImportError or APIError
3. Stale Cache (last resort)
   ↓ No cache available
4. Error reported to user
```

### Graceful Degradation

| Scenario | Behavior |
|----------|----------|
| Rate limited | Auto-retry with exponential backoff |
| Network error | Use fallback source or cache |
| Partial failure | Return successful results with warnings |
| Total failure | Clear error message with suggestions |

### Retry Logic

```python
# Built-in retry with exponential backoff
Attempt 1: Immediate
Attempt 2: Wait 2 seconds
Attempt 3: Wait 4 seconds
(Give up and try fallback)
```

---

## Debugging

### Enable Verbose Output

```bash
python price_tracker.py --symbol BTC --verbose
```

Shows:

- API calls being made
- Cache hits/misses
- Fallback attempts
- Timing information

### Check Cache Status

```python
# In Python
from cache_manager import CacheManager
cache = CacheManager()
print(cache.get_stats())
```

### Force Fresh Data

```bash
# Bypass cache entirely
python price_tracker.py --symbol BTC --no-cache

# Clear all cached data
python price_tracker.py --clear-cache
```

---

## Error Codes

| Code | Category | Meaning |
|------|----------|---------|
| 1 | General | Command-line argument error |
| 2 | Network | API connection failed |
| 3 | API | Rate limit or server error |
| 4 | Data | Symbol not found |
| 5 | Config | Configuration error |
| 6 | Output | File write error |

---

## Reporting Issues

When reporting issues, include:

1. **Command executed:**

   ```bash
   python price_tracker.py --symbol XYZ --verbose
   ```

2. **Full error output** (with `--verbose` flag)

3. **Python version:**

   ```bash
   python --version
   ```

4. **Package versions:**

   ```bash
   pip show requests yfinance pandas
   ```

5. **Configuration** (redact API keys):

   ```bash
   cat config/settings.yaml
   ```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
