# Market Sentiment Analyzer Plugin

Analyze market sentiment from social media, news, and on-chain data to gauge market mood and identify trading opportunities.

## Features

###  Multi-Source Analysis
- **Social Media**: Twitter, Reddit, Telegram sentiment
- **News**: Headlines, article sentiment, media coverage
- **On-Chain**: Whale movements, exchange flows, network activity
- **Technical**: Fear & Greed Index, momentum indicators

###  Sentiment Metrics
- Overall sentiment score (0-100)
- Fear & Greed Index calculation
- Trend detection and momentum
- Contrarian signals
- Correlation with price

## Installation

```bash
/plugin install market-sentiment-analyzer@claude-code-plugins-plus
```

## Usage

```
/analyze-sentiment BTC

Analyzing Bitcoin sentiment:
- Social media mentions: 15,420
- News sentiment: 72% positive
- On-chain: Accumulation phase
- Fear & Greed: 65 (Greed)
```

## Commands

| Command | Description | Shortcut |
|---------|-------------|----------|
| `/analyze-sentiment` | Full sentiment analysis | `as` |
| `/social-pulse` | Social media sentiment | `sp` |
| `/news-sentiment` | News analysis | `ns` |
| `/fear-greed` | Fear & Greed Index | `fg` |

## Sentiment Indicators

### Fear & Greed Index
- 0-25: Extreme Fear
- 25-45: Fear
- 45-55: Neutral
- 55-75: Greed
- 75-100: Extreme Greed

### Social Sentiment
- Mention volume trends
- Sentiment polarity
- Influential account activity
- Viral content detection

### On-Chain Sentiment
- Exchange inflows/outflows
- Whale accumulation
- Long-term holder behavior
- Network growth metrics

## Data Sources
- Twitter API
- Reddit API
- CryptoQuant
- Glassnode
- News aggregators

## License

MIT License

---

*Built for sentiment traders by Intent Solutions IO*