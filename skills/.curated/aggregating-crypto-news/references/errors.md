# Error Handling Reference

Comprehensive guide to errors, causes, and solutions for the aggregating-crypto-news skill.

## Error Categories

### 1. Network Errors

#### ConnectionError

**Message:** `Connection failed` or `Failed to establish connection`

**Cause:** No internet connectivity or DNS resolution failure.

**Solution:**

1. Check internet connection
2. Verify DNS settings
3. Try again after connection is restored
4. Cached data will be used if available

---

#### TimeoutError

**Message:** `Request timed out for [source]`

**Cause:** RSS feed server not responding within timeout window.

**Solution:**

1. Source is automatically skipped
2. Other sources continue to be fetched
3. Cached data used if available for that source
4. Check if source is down: visit URL in browser

**Mitigation:**

- Default timeout is 10 seconds per source
- Parallel fetching prevents one slow source from blocking others

---

#### HTTPError (4xx/5xx)

**Message:** `HTTP 403 Forbidden` or `HTTP 500 Server Error`

**Cause:** Source blocking requests or server issues.

**Solution:**

- 403: Source may be blocking automated access
- 404: RSS feed URL has changed
- 5xx: Server-side issue, try later

**Note:** Aggregator continues with available sources; failed sources are logged.

---

### 2. Parse Errors

#### FeedParseError

**Message:** `Failed to parse feed from [source]`

**Cause:** Malformed RSS/Atom XML that feedparser cannot process.

**Solution:**

1. Source is skipped
2. Check if source has valid RSS: validate at https://validator.w3.org/feed/
3. Report issue if feed URL has changed

---

#### MissingFieldError

**Message:** `Article missing required field: title`

**Cause:** Feed entry lacks required fields (title, link).

**Solution:**

1. Entry is skipped
2. Other entries from source continue to process
3. No user action needed

---

#### DateParseError

**Message:** `Failed to parse date for article`

**Cause:** Non-standard date format in feed entry.

**Solution:**

1. Article is included without date
2. Recency scoring disabled for that article
3. May appear out of order when sorted by recency

---

### 3. Filter Errors

#### InvalidCoinSymbol

**Message:** `Unknown coin symbol: [symbol]`

**Cause:** User provided unrecognized coin symbol.

**Solution:**

1. Check spelling (case-insensitive: btc, BTC, Btc all work)
2. Use common symbols: BTC, ETH, SOL, BNB, XRP, ADA, DOGE, etc.
3. Filter will attempt to match anyway against article text

**Note:** This is a warning, not a fatal error. Filter proceeds.

---

#### InvalidCategory

**Message:** `Invalid category: [category]`

**Cause:** User provided category not in allowed list.

**Solution:**
Use one of: `market`, `defi`, `nft`, `regulatory`, `layer1`, `layer2`, `exchange`, `security`

---

#### NoResultsFound

**Message:** `No articles found matching your criteria`

**Cause:** Filters are too restrictive for current news.

**Solution:**

1. Relax time window: `--period 24h` instead of `--period 1h`
2. Remove coin filter: drop `--coin` option
3. Lower score threshold: `--min-score 0`
4. Try different category or remove category filter

**Suggested Relaxations:**

```bash
# If no results with strict filters:
python news_aggregator.py --coin BTC --period 1h --min-score 50

# Try relaxing step by step:
python news_aggregator.py --coin BTC --period 4h    # Longer window
python news_aggregator.py --period 1h --min-score 0  # Lower threshold
python news_aggregator.py --period 4h               # Both relaxed
```

---

### 4. Export Errors

#### FileWriteError

**Message:** `Failed to write to output file: [path]`

**Cause:** Cannot write to specified path.

**Solution:**

1. Check directory exists
2. Check write permissions
3. Ensure disk space available
4. Use absolute path if relative fails

---

#### InvalidFormat

**Message:** `Invalid output format: [format]`

**Cause:** Unrecognized format option.

**Solution:**
Use one of: `table`, `json`, `csv`

---

### 5. Dependency Errors

#### ImportError: feedparser

**Message:** `Error: feedparser library required`

**Cause:** feedparser package not installed.

**Solution:**

```bash
pip install feedparser
```

---

#### ImportError: requests

**Message:** `Error: requests library required`

**Cause:** requests package not installed.

**Solution:**

```bash
pip install requests
```

---

## Error Handling Strategy

### Graceful Degradation

```
Full Success (all sources fetched)
     │
     ▼
Partial Success (some sources failed)
     │ → Continue with available data
     │ → Log warnings for failed sources
     │
     ▼
Cached Fallback (network issues)
     │ → Return cached data
     │ → Warn about stale data
     │
     ▼
Complete Failure (no data available)
     │ → Clear error message
     │ → Suggest remediation steps
```

### Behavior by Error Type

| Error Type | Behavior | User Impact |
|------------|----------|-------------|
| Network timeout | Skip source, continue | Partial results |
| Parse error | Skip entry, continue | Missing some articles |
| Invalid filter | Warn, proceed with partial filter | Approximate results |
| Export error | Fail with clear message | Must fix path/permissions |
| Missing dependency | Fail with install command | Must install package |

---

## Debugging

### Enable Verbose Mode

```bash
python news_aggregator.py --verbose
```

Shows:

- Which sources are being fetched
- Cache hits/misses
- Parse results per source
- Filter statistics
- Timing information

### Check Individual Source

```bash
# Validate RSS feed
curl -s "https://www.coindesk.com/arc/outboundfeeds/rss/" | head -50

# Or use a feed validator
# https://validator.w3.org/feed/check.cgi
```

### Test with Single Source

Edit `config/sources.yaml` to include only one source for testing.

---

## Error Codes

| Code | Category | Meaning |
|------|----------|---------|
| 0 | Success | Completed without errors |
| 1 | General | Unknown error or argument error |
| 2 | Dependency | Required library not installed |
| 3 | Network | All sources failed |
| 4 | Filter | No results after filtering |
| 5 | Export | File write error |

---

## Reporting Issues

When reporting issues, include:

1. **Command executed:**

   ```bash
   python news_aggregator.py --verbose [your options]
   ```

2. **Full error output** (with `--verbose`)

3. **Environment:**

   ```bash
   python --version
   pip list | grep -E "feedparser|requests"
   ```

4. **Network test:**

   ```bash
   curl -I https://www.coindesk.com/arc/outboundfeeds/rss/
   ```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
