# Usage Examples

Comprehensive examples for the aggregating-crypto-news skill.

## Quick Start Examples

### Example 1: Default News Scan

The simplest use case - get the latest crypto news:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/news_aggregator.py
```

**Output:**
```
==============================================================================
  CRYPTO NEWS AGGREGATOR                            Updated: 2026-01-14 15:30
==============================================================================

  TOP CRYPTO NEWS (24h)
------------------------------------------------------------------------------
  Rank  Source          Title                                       Age     Score
------------------------------------------------------------------------------
    1   CoinDesk        Bitcoin Breaks $100K, Sets New ATH          2h      95.0
    2   The Block       SEC Approves Spot ETH ETF Applications      4h      92.5
    3   Decrypt         Solana DeFi TVL Surges Past $15 Billion     6h      78.3
    4   CoinTelegraph   Binance Announces Major Listing Event       8h      75.0
    5   Blockworks      Arbitrum DAO Passes $50M Grant Proposal     12h     68.5
------------------------------------------------------------------------------

  Summary: 20 articles shown | Scanned: 12 sources | Matched: 156
==============================================================================
```

---

### Example 2: Bitcoin-Specific News

Filter for Bitcoin-related news only:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/news_aggregator.py --coin BTC
```

Only shows articles mentioning Bitcoin, BTC, or related terms.

---

### Example 3: Multiple Coins

Track news for your portfolio:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/news_aggregator.py --coins BTC,ETH,SOL
```

Shows articles mentioning any of the specified coins.

---

### Example 4: Recent Breaking News

Get news from the past hour only:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/news_aggregator.py --period 1h --top 10
```

Perfect for catching breaking news during active trading.

---

## Category Filtering

### Example 5: DeFi News

```bash
python ${CLAUDE_SKILL_DIR}/scripts/news_aggregator.py --category defi
```

Shows DeFi protocol news, yield farming updates, DEX announcements.

---

### Example 6: Regulatory News

```bash
python ${CLAUDE_SKILL_DIR}/scripts/news_aggregator.py --category regulatory
```

SEC, CFTC, congressional hearings, legal developments.

---

### Example 7: Security Alerts

```bash
python ${CLAUDE_SKILL_DIR}/scripts/news_aggregator.py --category security --period 4h
```

Hacks, exploits, vulnerabilities - time-sensitive security news.

---

### Example 8: Exchange News

```bash
python ${CLAUDE_SKILL_DIR}/scripts/news_aggregator.py --category exchange
```

Listings, delistings, exchange announcements.

---

### Example 9: Layer 2 Updates

```bash
python ${CLAUDE_SKILL_DIR}/scripts/news_aggregator.py --category layer2
```

Arbitrum, Optimism, Base, zkSync news.

---

## Export Options

### Example 10: JSON Export

For programmatic processing:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/news_aggregator.py --format json --output crypto_news.json
```

**Output (crypto_news.json):**
```json
{
  "articles": [
    {
      "rank": 1,
      "title": "Bitcoin Breaks $100K, Sets New ATH",
      "url": "https://coindesk.com/markets/2026/01/14/bitcoin-100k",
      "source": "CoinDesk",
      "published": "2026-01-14T13:30:00Z",
      "age": "2h ago",
      "category": "market",
      "relevance_score": 95.0,
      "coins_mentioned": ["BTC"],
      "summary": "Bitcoin surpassed $100,000 for the first time..."
    }
  ],
  "meta": {
    "period": "24h",
    "sources_checked": 12,
    "total_fetched": 500,
    "after_dedup": 380,
    "after_filter": 156,
    "shown": 20,
    "generated_at": "2026-01-14T15:30:00Z"
  }
}
```

---

### Example 11: CSV Export

For spreadsheet analysis:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/news_aggregator.py --format csv --output crypto_news.csv
```

**Output (crypto_news.csv):**
```csv
rank,title,url,source,published,age,category,relevance_score,coins_mentioned
1,Bitcoin Breaks $100K Sets New ATH,https://coindesk.com/...,CoinDesk,2026-01-14T13:30:00,2h ago,market,95.0,BTC
2,SEC Approves Spot ETH ETF,https://theblock.co/...,The Block,2026-01-14T11:30:00,4h ago,regulatory,92.5,ETH
```

---

## Sorting Options

### Example 12: Sort by Recency

```bash
python ${CLAUDE_SKILL_DIR}/scripts/news_aggregator.py --sort-by recency
```

Newest articles first, regardless of relevance score.

---

### Example 13: High-Score News Only

```bash
python ${CLAUDE_SKILL_DIR}/scripts/news_aggregator.py --min-score 70
```

Only shows articles with relevance score >= 70.

---

## Combined Filters

### Example 14: DeFi Breaking News

```bash
python ${CLAUDE_SKILL_DIR}/scripts/news_aggregator.py \
  --category defi \
  --period 4h \
  --min-score 50 \
  --top 10
```

DeFi news from past 4 hours with decent relevance.

---

### Example 15: Bitcoin Regulatory Updates

```bash
python ${CLAUDE_SKILL_DIR}/scripts/news_aggregator.py \
  --coin BTC \
  --category regulatory \
  --period 7d \
  --format json \
  --output btc_regulatory.json
```

Bitcoin-related regulatory news from past week.

---

### Example 16: Exchange Security Alerts

```bash
python ${CLAUDE_SKILL_DIR}/scripts/news_aggregator.py \
  --category security \
  --period 1h \
  --sort-by recency
```

Recent security-related news, perfect for immediate alerts.

---

### Example 17: Solana Ecosystem News

```bash
python ${CLAUDE_SKILL_DIR}/scripts/news_aggregator.py \
  --coin SOL \
  --period 24h \
  --top 15
```

All Solana-related news from past day.

---

### Example 18: Multi-Coin DeFi

```bash
python ${CLAUDE_SKILL_DIR}/scripts/news_aggregator.py \
  --coins ETH,AAVE,UNI,MKR \
  --category defi \
  --period 24h
```

DeFi news mentioning major DeFi tokens.

---

## Verbose Mode

### Example 19: Debug with Verbose

```bash
python ${CLAUDE_SKILL_DIR}/scripts/news_aggregator.py --verbose
```

**Output:**
```
Loaded 12 sources
Fetching feeds...
  Fetching: CoinDesk
  Fetching: CoinTelegraph
  Fetching: The Block
  Cache hit: Decrypt
  ...
Fetched 11 feeds successfully
Parsed 487 total articles
After deduplication: 352 articles
After filtering: 156 articles
==============================================================================
...
```

---

## Shell Script Integration

### Example 20: Scheduled Scan

```bash
#!/bin/bash
# morning_scan.sh - Run at market open

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR=~/crypto_news

mkdir -p $OUTPUT_DIR

python ${CLAUDE_SKILL_DIR}/scripts/news_aggregator.py \
  --period 4h \
  --format json \
  --output "$OUTPUT_DIR/news_$TIMESTAMP.json"

echo "Scan complete: $OUTPUT_DIR/news_$TIMESTAMP.json"
```

---

### Example 21: Alert on Market-Moving News

```bash
#!/bin/bash
# Check for high-scoring news

RESULT=$(python ${CLAUDE_SKILL_DIR}/scripts/news_aggregator.py \
  --period 1h \
  --min-score 80 \
  --format json)

COUNT=$(echo "$RESULT" | jq '.meta.shown')

if [ "$COUNT" -gt 0 ]; then
  echo "ALERT: $COUNT high-importance articles found!"
  echo "$RESULT" | jq '.articles[0].title'
fi
```

---

### Example 22: Daily Digest Email

```bash
#!/bin/bash
# daily_digest.sh - Generate daily news digest

python ${CLAUDE_SKILL_DIR}/scripts/news_aggregator.py \
  --period 24h \
  --top 30 \
  --format json \
  --output /tmp/daily_digest.json

# Process with jq or send to email service
cat /tmp/daily_digest.json | jq '.articles[] | "\(.rank). \(.title) - \(.source)"'
```

---

## Practical Use Cases

### Example 23: Pre-Trading Research

```bash
# Morning routine before trading
python ${CLAUDE_SKILL_DIR}/scripts/news_aggregator.py \
  --period 12h \
  --min-score 60 \
  --top 15

# Check specific coins in watchlist
python ${CLAUDE_SKILL_DIR}/scripts/news_aggregator.py \
  --coins BTC,ETH,SOL,ARB \
  --period 12h
```

---

### Example 24: Security Monitoring

```bash
# Run every hour via cron
python ${CLAUDE_SKILL_DIR}/scripts/news_aggregator.py \
  --category security \
  --period 1h \
  --sort-by recency \
  --format json \
  --output /var/log/crypto_security.json
```

---

### Example 25: Research Report Data

```bash
# Generate data for weekly report
python ${CLAUDE_SKILL_DIR}/scripts/news_aggregator.py \
  --period 7d \
  --top 100 \
  --format csv \
  --output weekly_news.csv
```

---

## Best Practices

1. **Start with defaults**: Run without filters first to see what's available
2. **Use verbose mode**: Add `--verbose` when debugging or learning
3. **Cache is your friend**: Re-running within 5 minutes uses cached data
4. **Combine filters carefully**: Too many filters = no results
5. **Export for analysis**: JSON/CSV exports enable deeper processing
6. **Schedule regular scans**: Automate morning/evening news checks
7. **Monitor security category**: Set up alerts for security news
8. **Check multiple timeframes**: 1h for breaking, 24h for context
