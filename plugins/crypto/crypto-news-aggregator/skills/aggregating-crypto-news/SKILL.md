---
name: aggregating-crypto-news
description: |
  Aggregate breaking cryptocurrency news from 50+ sources including CoinDesk, CoinTelegraph, The Block, and Decrypt.
  Use when needing to monitor crypto market news, track announcements, or find coin-specific updates.
  Trigger with phrases like "get crypto news", "latest Bitcoin headlines", "DeFi announcements", "scan for breaking news", or "check crypto updates".

allowed-tools: Read, Bash(crypto:news-*)
version: 2.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---

# Aggregating Crypto News

## Overview

This skill aggregates cryptocurrency news from 50+ authoritative sources using RSS feeds. It provides real-time news scanning with filtering by coin, category, time window, and relevance scoring.

**Key Capabilities:**
- Multi-source aggregation from top crypto news sites
- Coin-specific filtering (BTC, ETH, SOL, etc.)
- Category filtering (DeFi, NFT, regulatory, exchange, etc.)
- Relevance scoring with market-moving keyword detection
- Multiple output formats (table, JSON, CSV)

## Prerequisites

Before using this skill, ensure:

1. **Python 3.8+** is installed
2. **feedparser** library is available: `pip install feedparser`
3. **requests** library is available: `pip install requests`
4. Internet connectivity for RSS feed access

## Instructions

### Step 1: Assess User Intent

Determine what the user is looking for:
- **General news**: No specific filters, use defaults
- **Coin-specific**: Extract coin symbol (BTC, ETH, etc.)
- **Category-specific**: Extract category (defi, nft, regulatory, etc.)
- **Time-specific**: Extract time window (1h, 4h, 24h, 7d)

### Step 2: Execute News Aggregation

Run the news aggregator with appropriate filters:

```bash
# Default scan (top 20, past 24h, relevance sorted)
python ${CLAUDE_SKILL_DIR}/scripts/news_aggregator.py

# Coin-specific scan
python ${CLAUDE_SKILL_DIR}/scripts/news_aggregator.py --coin BTC --period 4h

# Category filter
python ${CLAUDE_SKILL_DIR}/scripts/news_aggregator.py --category defi --top 30

# Export to JSON
python ${CLAUDE_SKILL_DIR}/scripts/news_aggregator.py --format json --output news.json

# Multiple filters
python ${CLAUDE_SKILL_DIR}/scripts/news_aggregator.py --coin ETH --category defi --period 24h --top 15
```

### Step 3: Present Results

Format and present the news to the user:
- Show source, title, age, and relevance score
- Highlight market-moving keywords if present
- Provide links for full articles
- Summarize meta information (sources checked, articles found)

### Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--coin` | Filter by coin symbol (BTC, ETH, etc.) | None |
| `--coins` | Filter by multiple coins (comma-separated) | None |
| `--category` | Filter by category | None |
| `--period` | Time window (1h, 4h, 24h, 7d) | 24h |
| `--top` | Number of results to return | 20 |
| `--min-score` | Minimum relevance score | 0 |
| `--format` | Output format (table, json, csv) | table |
| `--output` | Output file path | stdout |
| `--sort-by` | Sort by (relevance, recency) | relevance |
| `--verbose` | Enable verbose output | false |

### Categories Available

- `market`: General market news, price movements
- `defi`: DeFi protocols, yield farming, DEXes
- `nft`: NFT projects, marketplaces, collections
- `regulatory`: Government, SEC, legal developments
- `layer1`: L1 blockchain news (Ethereum, Solana, etc.)
- `layer2`: L2 scaling solutions (Arbitrum, Optimism, etc.)
- `exchange`: Exchange news, listings, delistings
- `security`: Hacks, exploits, vulnerabilities

## Output

### Table Format (Default)
```
==============================================================================
  CRYPTO NEWS AGGREGATOR                            Updated: 2026-01-14 15:30
==============================================================================

  TOP CRYPTO NEWS (24h)
------------------------------------------------------------------------------
  Rank  Source          Title                           Age     Score
------------------------------------------------------------------------------
    1   CoinDesk        Bitcoin Breaks $100K ATH        2h      95.0
    2   The Block       SEC Approves ETH ETF            4h      92.5
    3   Decrypt         Solana DeFi TVL Surges          6h      78.3
------------------------------------------------------------------------------

  Summary: 20 articles shown | Scanned: 50 sources | Matched: 187
==============================================================================
```

### JSON Format
```json
{
  "articles": [
    {
      "rank": 1,
      "title": "Bitcoin Breaks $100K ATH",
      "url": "https://coindesk.com/...",
      "source": "CoinDesk",
      "published": "2026-01-14T13:30:00Z",
      "age": "2h ago",
      "category": "market",
      "relevance_score": 95.0,
      "coins_mentioned": ["BTC"]
    }
  ],
  "meta": {
    "period": "24h",
    "sources_checked": 50,
    "total_articles": 187,
    "shown": 20
  }
}
```

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

| Error | Cause | Solution |
|-------|-------|----------|
| Network timeout | RSS feed unreachable | Uses cached data; skips unavailable sources |
| Parse error | Malformed RSS | Skips entry; continues with valid articles |
| No results | Filters too strict | Suggest relaxing filters |
| Invalid coin | Unknown symbol | List similar valid symbols |

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

### Quick Examples

```bash
# Get latest crypto news (default)
python ${CLAUDE_SKILL_DIR}/scripts/news_aggregator.py

# Bitcoin news from past 4 hours
python ${CLAUDE_SKILL_DIR}/scripts/news_aggregator.py --coin BTC --period 4h

# DeFi category news
python ${CLAUDE_SKILL_DIR}/scripts/news_aggregator.py --category defi

# Export to JSON file
python ${CLAUDE_SKILL_DIR}/scripts/news_aggregator.py --format json --output crypto_news.json

# High-relevance news only
python ${CLAUDE_SKILL_DIR}/scripts/news_aggregator.py --min-score 70 --top 10

# Multiple coins
python ${CLAUDE_SKILL_DIR}/scripts/news_aggregator.py --coins BTC,ETH,SOL
```

## Resources

- **CoinDesk**: https://www.coindesk.com/arc/outboundfeeds/rss/
- **CoinTelegraph**: https://cointelegraph.com/rss
- **The Block**: https://www.theblock.co/rss.xml
- **Decrypt**: https://decrypt.co/feed
- **feedparser docs**: https://feedparser.readthedocs.io/
- See `${CLAUDE_SKILL_DIR}/config/sources.yaml` for full source registry
