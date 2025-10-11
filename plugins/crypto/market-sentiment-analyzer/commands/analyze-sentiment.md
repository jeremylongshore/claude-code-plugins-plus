---
description: Analyze market sentiment from social media, news, and on-chain metrics
shortcut: as
---

# Analyze Market Sentiment

Comprehensive sentiment analysis from multiple data sources to gauge market mood and predict price movements.

## Implementation

```javascript
class MarketSentimentAnalyzer {
    async analyzeSentiment(symbol = 'BTC') {
        const sources = {
            social: await this.analyzeSocialMedia(symbol),
            news: await this.analyzeNews(symbol),
            onChain: await this.analyzeOnChain(symbol),
            technical: await this.analyzeTechnical(symbol)
        };

        return {
            overall: this.calculateOverallSentiment(sources),
            sources,
            signals: this.generateSignals(sources),
            fearGreedIndex: this.calculateFearGreed(sources)
        };
    }

    async analyzeSocialMedia(symbol) {
        // Twitter, Reddit, Telegram analysis
        return {
            twitter: {
                mentions: 15420,
                sentiment: 0.72,
                influential: 85
            },
            reddit: {
                posts: 342,
                sentiment: 0.65,
                activity: 'HIGH'
            }
        };
    }

    calculateFearGreed(sources) {
        let score = 50; // Neutral start

        // Social sentiment
        score += sources.social.twitter.sentiment * 20;

        // News sentiment
        score += sources.news.sentiment * 15;

        // On-chain metrics
        if (sources.onChain.netflow > 0) score += 10;

        // Technical indicators
        if (sources.technical.rsi > 70) score += 15;

        return {
            score: Math.min(100, Math.max(0, score)),
            label: score > 75 ? 'EXTREME_GREED' :
                   score > 55 ? 'GREED' :
                   score > 45 ? 'NEUTRAL' :
                   score > 25 ? 'FEAR' : 'EXTREME_FEAR'
        };
    }
}
```

Provides comprehensive sentiment analysis across multiple data sources.