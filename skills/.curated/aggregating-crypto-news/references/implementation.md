# Aggregating Crypto News - Implementation Reference

## Command-Line Options

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

## Categories Available

- `market`: General market news, price movements
- `defi`: DeFi protocols, yield farming, DEXes
- `nft`: NFT projects, marketplaces, collections
- `regulatory`: Government, SEC, legal developments
- `layer1`: L1 blockchain news (Ethereum, Solana, etc.)
- `layer2`: L2 scaling solutions (Arbitrum, Optimism, etc.)
- `exchange`: Exchange news, listings, delistings
- `security`: Hacks, exploits, vulnerabilities

## JSON Output Format

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

## Advanced Filtering Examples

```bash
# Multiple filters combined
python ${CLAUDE_SKILL_DIR}/scripts/news_aggregator.py --coin ETH --category defi --period 24h --top 15

# High-relevance news only
python ${CLAUDE_SKILL_DIR}/scripts/news_aggregator.py --min-score 70 --top 10

# Multiple coins
python ${CLAUDE_SKILL_DIR}/scripts/news_aggregator.py --coins BTC,ETH,SOL

# Export to JSON file
python ${CLAUDE_SKILL_DIR}/scripts/news_aggregator.py --format json --output crypto_news.json
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
