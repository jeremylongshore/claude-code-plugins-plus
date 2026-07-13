# Error Handling Reference

Comprehensive error handling guide for the Market Sentiment Analyzer.

---

## API Errors

### Fear & Greed Index Unavailable

**Error**: Cannot fetch Fear & Greed Index from Alternative.me API

**Symptoms**:

```
Fear & Greed Index unavailable
Using cached/fallback value
```

**Causes**:

- API rate limiting (>10 requests/minute)
- API server downtime
- Network connectivity issues

**Solutions**:

1. **Automatic**: Uses cached value with "stale" warning
2. **Manual**: Wait 1-2 minutes and retry
3. **Persistent**: Check https://alternative.me/crypto/fear-and-greed-index/ status

**Impact**: Composite score uses cached or neutral (50) value

---

### CoinGecko API Rate Limit

**Error**: Market momentum data unavailable

**Symptoms**:

```
API request failed: 429 Too Many Requests
Market data unavailable
```

**Causes**:

- Exceeded free tier limit (~10-30 calls/minute)
- Too many concurrent requests

**Solutions**:

1. **Automatic**: Falls back to cached data
2. **Manual**: Wait 60 seconds before retry
3. **Upgrade**: CoinGecko Pro API for higher limits

**Impact**: Momentum component uses neutral (50) value

---

### News Feed Unavailable

**Error**: Cannot fetch news from RSS feeds

**Symptoms**:

```
Failed to fetch [feed_url]: Connection timed out
No articles available
```

**Causes**:

- RSS feed URL changed
- Feed server downtime
- Network firewall blocking

**Solutions**:

1. **Automatic**: Skips unavailable feeds, uses others
2. **Check**: Verify feed URLs in settings
3. **Network**: Test connectivity to feed domains

**Impact**: News sentiment based on fewer articles; score may be less representative

---

## Data Parsing Errors

### Invalid JSON Response

**Error**: Failed to parse API response

**Symptoms**:

```
json.JSONDecodeError: Expecting value
Failed to parse response: [error details]
```

**Causes**:

- API returning HTML error page instead of JSON
- Malformed API response
- Incomplete response due to timeout

**Solutions**:

1. Check API status pages
2. Verify API endpoint URLs
3. Increase timeout in settings

---

### Missing Data Fields

**Error**: Expected field not in response

**Symptoms**:

```
KeyError: 'price_change_percentage_24h'
```

**Causes**:

- API schema changed
- New coin not fully supported
- Delisted coin

**Solutions**:

1. Update to latest script version
2. Use market-wide analysis instead of coin-specific
3. Report issue if persistent

---

## Configuration Errors

### Invalid Weights

**Error**: Custom weights don't sum to 1.0

**Note**: This is auto-corrected, not a fatal error

**Causes**:

- User-provided weights like "news:0.5,fng:0.5,momentum:0.5" (sum > 1)

**Solutions**:

1. **Automatic**: Weights are normalized
2. **Manual**: Ensure weights sum to 1.0

---

### Unknown Coin Symbol

**Error**: Coin not found in known mappings

**Symptoms**:

```
No data for [COIN], using market analysis
```

**Causes**:

- Coin symbol not in known mappings
- New coin not yet added
- Typo in symbol

**Solutions**:

1. Use common symbols (BTC, ETH, SOL, etc.)
2. Try full CoinGecko ID instead of symbol
3. Fall back to market-wide analysis

---

## Graceful Degradation

The analyzer implements graceful degradation:

```
Full Analysis (all 3 components)
     │
     ├─► Fear & Greed fails → Use cached/neutral (50)
     │
     ├─► News fails → Use remaining components with adjusted weights
     │
     ├─► Momentum fails → Use remaining components with adjusted weights
     │
     └─► All fail → Return neutral (50) with error warnings
```

### Component Failure Handling

| Component | Fallback | Score Used |
|-----------|----------|------------|
| Fear & Greed | Cached → Neutral | Cached value or 50 |
| News Sentiment | Skip | 50 (neutral) |
| Market Momentum | Cached → Neutral | Cached value or 50 |

---

## Diagnostic Commands

### Test Individual Components

```bash
# Test Fear & Greed
python fear_greed.py -v

# Test News Sentiment
python news_sentiment.py -v

# Test Market Momentum
python market_momentum.py -v

# Full analysis with verbose
python sentiment_analyzer.py -v
```

### Check Cache Files

```bash
# List cache files
ls -la scripts/.*.json

# View cached data
cat scripts/.fng_cache.json | python -m json.tool
```

### Clear Caches

```bash
rm scripts/.fng_cache.json
rm scripts/.news_cache.json
rm scripts/.momentum_cache.json
```

---

## Common Issues

### Issue: Score Always Neutral (50)

**Causes**:

- All APIs unavailable
- Network connectivity issues
- VPN blocking API access

**Diagnosis**:

```bash
# Run with verbose
python sentiment_analyzer.py -v

# Check network
curl -I https://api.alternative.me/fng/
curl -I https://api.coingecko.com/api/v3/ping
```

### Issue: News Sentiment Skewed

**Causes**:

- Only one RSS feed responding
- Feed returns old articles
- Keyword bias in recent news

**Diagnosis**:

```bash
python news_sentiment.py -v
# Check "articles_analyzed" count
# Should be 15-50 for balanced sentiment
```

### Issue: Slow Response Time

**Causes**:

- Cache expired, fetching fresh data
- Network latency to APIs
- API rate limiting delays

**Solutions**:

1. Increase cache TTL in settings
2. Use `--verbose` to see timing
3. Consider local caching proxy

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
