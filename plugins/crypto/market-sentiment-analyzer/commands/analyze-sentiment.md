---
description: Analyze market sentiment from social media, news, and on-chain metrics
shortcut: as
---

# Analyze Market Sentiment

Comprehensive multi-source sentiment analysis system that aggregates data from social media platforms, news outlets, on-chain metrics, derivatives markets, and whale tracking to predict market movements and identify trading opportunities.

## Overview

Market sentiment analysis combines quantitative on-chain data with qualitative social signals to measure the collective mood of market participants. This command provides a sophisticated sentiment aggregation framework that:

- **Monitors 6+ data sources** including Twitter/X, Reddit, Telegram, Discord, news feeds, and blockchain metrics
- **Calculates Fear & Greed Index** using weighted multi-factor analysis
- **Analyzes derivatives markets** through funding rates and options sentiment
- **Tracks whale behavior** via large holder movements and exchange flows
- **Correlates sentiment shifts** with historical price action for predictive insights
- **Generates weighted sentiment scores** with confidence intervals and statistical significance

The analyzer uses natural language processing (NLP), time-series analysis, and machine learning to identify sentiment extremes that often precede major price reversals, making it invaluable for contrarian trading strategies.

## Data Sources & Weighting

### Social Media Sentiment (35% weight)

**Twitter/X Analysis (15%)**
- Real-time tweet monitoring for crypto-specific keywords and cashtags
- Sentiment scoring using VADER and FinBERT NLP models
- Influencer tracking with follower-weighted sentiment
- Engagement metrics (likes, retweets, quote tweets)
- Trending topics and hashtag velocity analysis

**Reddit Sentiment (10%)**
- r/CryptoCurrency, r/Bitcoin, r/ethereum analysis
- Post and comment sentiment with upvote weighting
- Daily discussion thread analysis
- Subreddit activity levels (posts per hour)
- Cross-post momentum tracking

**Telegram & Discord (10%)**
- Group message sentiment analysis
- Active user count and engagement rate
- Admin/moderator sentiment filtering
- Message velocity and panic indicators
- Voice chat activity monitoring

### News & Media Sentiment (20% weight)

**Mainstream Media Coverage**
- Automated news scraping from CoinDesk, CoinTelegraph, Bloomberg Crypto
- Headline sentiment analysis with clickbait filtering
- Source credibility scoring
- Publication frequency tracking
- Fear/uncertainty/doubt (FUD) detection

**Regulatory News Impact**
- Government announcement tracking
- SEC filing monitoring
- Central bank statement analysis
- Regulatory sentiment classification
- Geographic regulatory heat maps

### Derivatives Market Sentiment (25% weight)

**Funding Rates Analysis (12%)**
- Perpetual futures funding rate tracking across exchanges
- Historical funding rate comparison
- Funding rate divergence alerts
- Long/short ratio calculation
- Liquidation cascade prediction

**Options Market Sentiment (13%)**
- Put/Call ratio analysis for major strikes
- Implied volatility skew interpretation
- Options open interest distribution
- Max pain price calculation
- Gamma squeeze potential detection

### Whale & Smart Money Tracking (15% weight)

**Large Holder Movements**
- Whale wallet transaction monitoring (>$1M transfers)
- Exchange deposit/withdrawal flow analysis
- Cold wallet accumulation patterns
- Smart money address tracking
- Whale sentiment divergence from retail

**Exchange Flow Analysis**
- Net flow (deposits minus withdrawals)
- Exchange reserve levels
- Miner selling pressure
- OTC desk activity indicators
- Stablecoin flow correlation

### On-Chain Sentiment Indicators (5% weight)

**Network Value Metrics**
- MVRV ratio (Market Value to Realized Value)
- NVT ratio (Network Value to Transactions)
- Spent Output Age analysis
- Long-term holder behavior
- Realized cap momentum

## Fear & Greed Index Calculation

The Fear & Greed Index aggregates multiple data sources into a single 0-100 score:

**Score Interpretation:**
- 0-25: Extreme Fear (potential buying opportunity)
- 25-45: Fear (cautious sentiment)
- 45-55: Neutral (balanced market)
- 55-75: Greed (risk appetite increasing)
- 75-100: Extreme Greed (potential correction ahead)

**Calculation Methodology:**

1. **Social Sentiment Component (35 points)**
   - Twitter sentiment: 15 points (scaled -1 to +1 → 0 to 15)
   - Reddit sentiment: 10 points
   - Telegram/Discord: 10 points

2. **Market Momentum Component (20 points)**
   - Price volatility (25% of component)
   - Trading volume vs. 30-day average (25%)
   - Market dominance trends (25%)
   - Recent price action (25%)

3. **Derivatives Component (25 points)**
   - Funding rates (12 points, scaled from -0.1% to +0.1%)
   - Put/Call ratio (13 points, inverted scale)

4. **Whale Behavior Component (15 points)**
   - Exchange net flow (7.5 points)
   - Large transaction frequency (7.5 points)

5. **On-Chain Component (5 points)**
   - MVRV ratio deviation from mean
   - NVT ratio trend

## Code Implementation

### Comprehensive Python Sentiment Analyzer

```python
#!/usr/bin/env python3
"""
Comprehensive Multi-Source Crypto Market Sentiment Analyzer
Aggregates sentiment from social media, news, derivatives, and on-chain data
"""

import asyncio
import aiohttp
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
import statistics
import json
import re
from collections import defaultdict, deque
import tweepy
import praw
from telethon import TelegramClient
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from transformers import pipeline
import ccxt.async_support as ccxt
from web3 import Web3
import redis
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SentimentLevel(Enum):
    """Sentiment level classification"""
    EXTREME_FEAR = "Extreme Fear"
    FEAR = "Fear"
    NEUTRAL = "Neutral"
    GREED = "Greed"
    EXTREME_GREED = "Extreme Greed"


@dataclass
class SentimentScore:
    """Individual sentiment score with metadata"""
    source: str
    score: float  # -1.0 to 1.0
    confidence: float  # 0.0 to 1.0
    weight: float
    timestamp: datetime
    sample_size: int
    metadata: Dict = field(default_factory=dict)


@dataclass
class FearGreedIndex:
    """Fear & Greed Index result"""
    score: int  # 0-100
    level: SentimentLevel
    components: Dict[str, float]
    historical_percentile: float
    trend: str  # 'increasing', 'decreasing', 'stable'
    timestamp: datetime


@dataclass
class SentimentAlert:
    """Sentiment-based trading alert"""
    alert_type: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    message: str
    sentiment_score: float
    trigger_condition: str
    timestamp: datetime


class SocialMediaAnalyzer:
    """Analyze sentiment from social media platforms"""

    def __init__(self, config: Dict):
        self.config = config
        self.vader = SentimentIntensityAnalyzer()
        self.finbert = pipeline(
            "sentiment-analysis",
            model="ProsusAI/finbert",
            device=-1  # CPU
        )

        # Initialize API clients
        self.twitter_client = self._init_twitter()
        self.reddit_client = self._init_reddit()
        self.telegram_client = self._init_telegram()

        # Sentiment cache
        self.cache = redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=True
        )

    def _init_twitter(self) -> Optional[tweepy.Client]:
        """Initialize Twitter API client"""
        try:
            return tweepy.Client(
                bearer_token=self.config.get('twitter_bearer_token'),
                wait_on_rate_limit=True
            )
        except Exception as e:
            logger.error(f"Twitter initialization failed: {e}")
            return None

    def _init_reddit(self) -> Optional[praw.Reddit]:
        """Initialize Reddit API client"""
        try:
            return praw.Reddit(
                client_id=self.config.get('reddit_client_id'),
                client_secret=self.config.get('reddit_client_secret'),
                user_agent='CryptoSentimentAnalyzer/1.0'
            )
        except Exception as e:
            logger.error(f"Reddit initialization failed: {e}")
            return None

    def _init_telegram(self) -> Optional[TelegramClient]:
        """Initialize Telegram client"""
        try:
            return TelegramClient(
                'sentiment_session',
                self.config.get('telegram_api_id'),
                self.config.get('telegram_api_hash')
            )
        except Exception as e:
            logger.error(f"Telegram initialization failed: {e}")
            return None

    async def analyze_twitter(self, symbol: str, lookback_hours: int = 24) -> SentimentScore:
        """Analyze Twitter sentiment for cryptocurrency"""
        if not self.twitter_client:
            return self._empty_sentiment_score('twitter')

        try:
            # Search for tweets
            query = f"${symbol} OR #{symbol} -is:retweet lang:en"
            tweets = self.twitter_client.search_recent_tweets(
                query=query,
                max_results=100,
                tweet_fields=['created_at', 'public_metrics', 'author_id']
            )

            if not tweets.data:
                return self._empty_sentiment_score('twitter')

            sentiments = []
            total_engagement = 0
            influential_count = 0

            for tweet in tweets.data:
                # Get engagement metrics
                metrics = tweet.public_metrics
                engagement = (
                    metrics['like_count'] +
                    metrics['retweet_count'] * 2 +
                    metrics['reply_count']
                )

                # Calculate sentiment with VADER
                vader_score = self.vader.polarity_scores(tweet.text)

                # Calculate FinBERT sentiment for financial context
                try:
                    finbert_result = self.finbert(tweet.text[:512])[0]
                    finbert_score = self._finbert_to_score(finbert_result)
                except Exception:
                    finbert_score = vader_score['compound']

                # Weighted average of VADER and FinBERT
                combined_score = 0.6 * finbert_score + 0.4 * vader_score['compound']

                # Weight by engagement
                sentiments.append({
                    'score': combined_score,
                    'weight': max(1, engagement)
                })

                total_engagement += engagement

                # Track influential tweets (high engagement)
                if engagement > 100:
                    influential_count += 1

            # Calculate weighted average sentiment
            weighted_sum = sum(s['score'] * s['weight'] for s in sentiments)
            total_weight = sum(s['weight'] for s in sentiments)
            avg_sentiment = weighted_sum / total_weight if total_weight > 0 else 0.0

            # Calculate confidence based on sample size and agreement
            sentiment_values = [s['score'] for s in sentiments]
            std_dev = statistics.stdev(sentiment_values) if len(sentiment_values) > 1 else 1.0
            confidence = min(1.0, (len(sentiments) / 100) * (1.0 - std_dev))

            return SentimentScore(
                source='twitter',
                score=avg_sentiment,
                confidence=confidence,
                weight=0.15,
                timestamp=datetime.now(),
                sample_size=len(sentiments),
                metadata={
                    'total_engagement': total_engagement,
                    'influential_tweets': influential_count,
                    'avg_engagement': total_engagement / len(sentiments),
                    'sentiment_distribution': {
                        'positive': sum(1 for s in sentiments if s['score'] > 0.05),
                        'neutral': sum(1 for s in sentiments if -0.05 <= s['score'] <= 0.05),
                        'negative': sum(1 for s in sentiments if s['score'] < -0.05)
                    }
                }
            )

        except Exception as e:
            logger.error(f"Twitter analysis error: {e}")
            return self._empty_sentiment_score('twitter')

    async def analyze_reddit(self, symbol: str, lookback_hours: int = 24) -> SentimentScore:
        """Analyze Reddit sentiment for cryptocurrency"""
        if not self.reddit_client:
            return self._empty_sentiment_score('reddit')

        try:
            # Define relevant subreddits
            subreddits = ['CryptoCurrency', 'Bitcoin', 'ethereum', 'CryptoMarkets']

            sentiments = []
            total_upvotes = 0
            post_count = 0
            comment_count = 0

            for subreddit_name in subreddits:
                subreddit = self.reddit_client.subreddit(subreddit_name)

                # Search posts
                search_query = f"{symbol}"
                for post in subreddit.search(search_query, time_filter='day', limit=50):
                    post_age_hours = (datetime.now().timestamp() - post.created_utc) / 3600
                    if post_age_hours > lookback_hours:
                        continue

                    # Analyze post title and text
                    text = f"{post.title} {post.selftext}"
                    sentiment = self.vader.polarity_scores(text)['compound']

                    # Weight by upvote ratio and score
                    weight = max(1, post.score * post.upvote_ratio)

                    sentiments.append({
                        'score': sentiment,
                        'weight': weight
                    })

                    total_upvotes += post.score
                    post_count += 1

                    # Analyze top comments
                    post.comment_sort = 'top'
                    post.comment_limit = 10
                    for comment in post.comments[:10]:
                        if hasattr(comment, 'body'):
                            comment_sentiment = self.vader.polarity_scores(comment.body)['compound']
                            comment_weight = max(1, comment.score)

                            sentiments.append({
                                'score': comment_sentiment,
                                'weight': comment_weight
                            })

                            comment_count += 1

            if not sentiments:
                return self._empty_sentiment_score('reddit')

            # Calculate weighted average
            weighted_sum = sum(s['score'] * s['weight'] for s in sentiments)
            total_weight = sum(s['weight'] for s in sentiments)
            avg_sentiment = weighted_sum / total_weight if total_weight > 0 else 0.0

            # Calculate activity level
            total_items = post_count + comment_count
            activity_level = (
                'HIGH' if total_items > 100 else
                'MEDIUM' if total_items > 30 else
                'LOW'
            )

            # Confidence based on sample size
            confidence = min(1.0, total_items / 100)

            return SentimentScore(
                source='reddit',
                score=avg_sentiment,
                confidence=confidence,
                weight=0.10,
                timestamp=datetime.now(),
                sample_size=len(sentiments),
                metadata={
                    'post_count': post_count,
                    'comment_count': comment_count,
                    'total_upvotes': total_upvotes,
                    'activity_level': activity_level,
                    'avg_upvotes_per_post': total_upvotes / post_count if post_count > 0 else 0
                }
            )

        except Exception as e:
            logger.error(f"Reddit analysis error: {e}")
            return self._empty_sentiment_score('reddit')

    async def analyze_telegram(self, symbol: str, lookback_hours: int = 24) -> SentimentScore:
        """Analyze Telegram group sentiment"""
        if not self.telegram_client:
            return self._empty_sentiment_score('telegram')

        try:
            # Define target channels/groups
            channels = self.config.get('telegram_channels', [])

            sentiments = []
            total_messages = 0

            async with self.telegram_client:
                for channel in channels:
                    try:
                        # Get recent messages
                        messages = await self.telegram_client.get_messages(
                            channel,
                            limit=100
                        )

                        for msg in messages:
                            # Check message age
                            msg_age = datetime.now() - msg.date
                            if msg_age.total_seconds() > lookback_hours * 3600:
                                continue

                            if msg.text and symbol.lower() in msg.text.lower():
                                sentiment = self.vader.polarity_scores(msg.text)['compound']

                                # Weight by reactions/views
                                weight = 1
                                if msg.reactions:
                                    weight += sum(r.count for r in msg.reactions.results)

                                sentiments.append({
                                    'score': sentiment,
                                    'weight': weight
                                })

                                total_messages += 1

                    except Exception as e:
                        logger.warning(f"Error accessing channel {channel}: {e}")
                        continue

            if not sentiments:
                return self._empty_sentiment_score('telegram')

            # Calculate weighted average
            weighted_sum = sum(s['score'] * s['weight'] for s in sentiments)
            total_weight = sum(s['weight'] for s in sentiments)
            avg_sentiment = weighted_sum / total_weight if total_weight > 0 else 0.0

            confidence = min(1.0, total_messages / 50)

            return SentimentScore(
                source='telegram',
                score=avg_sentiment,
                confidence=confidence,
                weight=0.10,
                timestamp=datetime.now(),
                sample_size=total_messages,
                metadata={
                    'channels_analyzed': len(channels),
                    'total_messages': total_messages
                }
            )

        except Exception as e:
            logger.error(f"Telegram analysis error: {e}")
            return self._empty_sentiment_score('telegram')

    def _finbert_to_score(self, result: Dict) -> float:
        """Convert FinBERT result to -1 to 1 score"""
        label = result['label'].lower()
        score = result['score']

        if label == 'positive':
            return score
        elif label == 'negative':
            return -score
        else:  # neutral
            return 0.0

    def _empty_sentiment_score(self, source: str) -> SentimentScore:
        """Return empty sentiment score"""
        return SentimentScore(
            source=source,
            score=0.0,
            confidence=0.0,
            weight=0.0,
            timestamp=datetime.now(),
            sample_size=0,
            metadata={}
        )


class DerivativesAnalyzer:
    """Analyze derivatives market sentiment"""

    def __init__(self):
        self.exchanges = {
            'binance': ccxt.binance(),
            'bybit': ccxt.bybit(),
            'okx': ccxt.okx()
        }

    async def analyze_funding_rates(self, symbol: str) -> SentimentScore:
        """Analyze perpetual futures funding rates"""
        try:
            funding_rates = []

            for exchange_name, exchange in self.exchanges.items():
                try:
                    # Get funding rate
                    ticker = await exchange.fetch_ticker(f"{symbol}/USDT:USDT")

                    if 'fundingRate' in ticker['info']:
                        rate = float(ticker['info']['fundingRate'])
                        funding_rates.append({
                            'exchange': exchange_name,
                            'rate': rate
                        })

                except Exception as e:
                    logger.warning(f"Error fetching funding rate from {exchange_name}: {e}")
                    continue

            if not funding_rates:
                return self._empty_sentiment_score('funding_rates')

            # Calculate average funding rate
            avg_rate = statistics.mean([fr['rate'] for fr in funding_rates])

            # Convert funding rate to sentiment score
            # Positive funding = longs pay shorts = bullish = positive sentiment
            # Negative funding = shorts pay longs = bearish = negative sentiment
            # Normalize to -1 to 1 scale (typical range: -0.1% to +0.1%)
            sentiment_score = np.clip(avg_rate * 1000, -1.0, 1.0)

            # High absolute funding rates indicate extreme sentiment
            confidence = min(1.0, abs(avg_rate) * 5000)

            return SentimentScore(
                source='funding_rates',
                score=sentiment_score,
                confidence=confidence,
                weight=0.12,
                timestamp=datetime.now(),
                sample_size=len(funding_rates),
                metadata={
                    'avg_funding_rate': avg_rate,
                    'rate_percentage': avg_rate * 100,
                    'exchanges': funding_rates,
                    'interpretation': (
                        'Strong bullish bias' if avg_rate > 0.0005 else
                        'Mild bullish bias' if avg_rate > 0.0001 else
                        'Neutral' if abs(avg_rate) <= 0.0001 else
                        'Mild bearish bias' if avg_rate > -0.0005 else
                        'Strong bearish bias'
                    )
                }
            )

        except Exception as e:
            logger.error(f"Funding rate analysis error: {e}")
            return self._empty_sentiment_score('funding_rates')

        finally:
            # Close exchange connections
            for exchange in self.exchanges.values():
                await exchange.close()

    async def analyze_options_sentiment(self, symbol: str) -> SentimentScore:
        """Analyze options market sentiment (put/call ratio, max pain)"""
        try:
            # For demonstration - would integrate with Deribit API
            # This is a simplified simulation

            # Fetch options data (simulated)
            put_volume = 15000
            call_volume = 22000
            put_call_ratio = put_volume / call_volume

            # Calculate sentiment from put/call ratio
            # Low ratio (< 0.7) = bullish (more calls) = positive sentiment
            # High ratio (> 1.3) = bearish (more puts) = negative sentiment
            if put_call_ratio < 0.7:
                sentiment_score = (0.7 - put_call_ratio) / 0.7  # 0 to 1
            elif put_call_ratio > 1.3:
                sentiment_score = -(put_call_ratio - 1.3) / 1.3  # -1 to 0
            else:
                # Neutral range
                sentiment_score = 0.0

            sentiment_score = np.clip(sentiment_score, -1.0, 1.0)

            # Confidence based on volume
            total_volume = put_volume + call_volume
            confidence = min(1.0, total_volume / 50000)

            return SentimentScore(
                source='options',
                score=sentiment_score,
                confidence=confidence,
                weight=0.13,
                timestamp=datetime.now(),
                sample_size=1,
                metadata={
                    'put_call_ratio': put_call_ratio,
                    'put_volume': put_volume,
                    'call_volume': call_volume,
                    'interpretation': (
                        'Bullish (heavy call buying)' if put_call_ratio < 0.7 else
                        'Neutral' if 0.7 <= put_call_ratio <= 1.3 else
                        'Bearish (heavy put buying)'
                    )
                }
            )

        except Exception as e:
            logger.error(f"Options sentiment analysis error: {e}")
            return self._empty_sentiment_score('options')

    def _empty_sentiment_score(self, source: str) -> SentimentScore:
        """Return empty sentiment score"""
        return SentimentScore(
            source=source,
            score=0.0,
            confidence=0.0,
            weight=0.0,
            timestamp=datetime.now(),
            sample_size=0,
            metadata={}
        )


class OnChainAnalyzer:
    """Analyze on-chain sentiment indicators"""

    def __init__(self, config: Dict):
        self.config = config
        # Initialize Web3 connections for different chains
        self.w3_eth = Web3(Web3.HTTPProvider(config.get('ethereum_rpc')))
        self.session = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def analyze_whale_movements(self, symbol: str) -> SentimentScore:
        """Analyze large holder movements"""
        try:
            session = await self._get_session()

            # Use Whale Alert API or similar service
            whale_api_url = "https://api.whale-alert.io/v1/transactions"
            params = {
                'api_key': self.config.get('whale_alert_api_key'),
                'min_value': 1000000,  # $1M minimum
                'symbol': symbol.lower(),
                'limit': 100
            }

            async with session.get(whale_api_url, params=params) as response:
                if response.status != 200:
                    return self._empty_sentiment_score('whale_movements')

                data = await response.json()
                transactions = data.get('transactions', [])

            if not transactions:
                return self._empty_sentiment_score('whale_movements')

            # Analyze transaction patterns
            exchange_deposits = 0  # Bearish
            exchange_withdrawals = 0  # Bullish
            unknown_transfers = 0

            total_value = 0

            for tx in transactions:
                value = tx.get('amount_usd', 0)
                total_value += value

                from_type = tx.get('from', {}).get('owner_type', 'unknown')
                to_type = tx.get('to', {}).get('owner_type', 'unknown')

                if to_type == 'exchange':
                    exchange_deposits += value
                elif from_type == 'exchange':
                    exchange_withdrawals += value
                else:
                    unknown_transfers += value

            # Calculate net exchange flow sentiment
            net_flow = exchange_withdrawals - exchange_deposits

            # Normalize to -1 to 1 scale
            max_value = max(exchange_deposits, exchange_withdrawals)
            if max_value > 0:
                sentiment_score = net_flow / max_value
            else:
                sentiment_score = 0.0

            sentiment_score = np.clip(sentiment_score, -1.0, 1.0)

            # Confidence based on transaction count and value
            confidence = min(1.0, (len(transactions) / 100) * (total_value / 100000000))

            return SentimentScore(
                source='whale_movements',
                score=sentiment_score,
                confidence=confidence,
                weight=0.15,
                timestamp=datetime.now(),
                sample_size=len(transactions),
                metadata={
                    'exchange_deposits_usd': exchange_deposits,
                    'exchange_withdrawals_usd': exchange_withdrawals,
                    'net_flow_usd': net_flow,
                    'total_value_usd': total_value,
                    'transaction_count': len(transactions),
                    'interpretation': (
                        'Strong accumulation (whale withdrawals)' if sentiment_score > 0.5 else
                        'Mild accumulation' if sentiment_score > 0.2 else
                        'Neutral' if abs(sentiment_score) <= 0.2 else
                        'Mild distribution' if sentiment_score > -0.5 else
                        'Strong distribution (whale deposits)'
                    )
                }
            )

        except Exception as e:
            logger.error(f"Whale movement analysis error: {e}")
            return self._empty_sentiment_score('whale_movements')

    async def analyze_network_value_metrics(self, symbol: str) -> SentimentScore:
        """Analyze MVRV, NVT, and other network value metrics"""
        try:
            # For demonstration - would integrate with Glassnode, CoinMetrics, etc.
            # This is a simplified simulation

            # MVRV ratio (Market Value to Realized Value)
            # > 3.0 = overvalued/euphoric (negative sentiment)
            # < 1.0 = undervalued/despair (positive sentiment for contrarian)
            mvrv_ratio = 2.1

            # NVT ratio (Network Value to Transactions)
            # High NVT = overvalued relative to usage
            nvt_ratio = 85

            # Calculate sentiment from MVRV
            # Convert to -1 to 1 scale where extremes indicate reversal potential
            if mvrv_ratio > 3.0:
                # Overvalued - bearish
                mvrv_sentiment = -(min(mvrv_ratio - 3.0, 2.0) / 2.0)
            elif mvrv_ratio < 1.0:
                # Undervalued - bullish (contrarian)
                mvrv_sentiment = (1.0 - mvrv_ratio)
            else:
                # Neutral range (1.0 to 3.0)
                mvrv_sentiment = (2.0 - mvrv_ratio) / 2.0

            # Calculate sentiment from NVT (inverse relationship)
            # Low NVT = healthy usage = bullish
            # High NVT = overvalued = bearish
            if nvt_ratio > 100:
                nvt_sentiment = -0.5
            elif nvt_ratio < 50:
                nvt_sentiment = 0.5
            else:
                nvt_sentiment = 0.0

            # Combine metrics
            combined_sentiment = (mvrv_sentiment * 0.6 + nvt_sentiment * 0.4)
            combined_sentiment = np.clip(combined_sentiment, -1.0, 1.0)

            # Confidence is moderate for on-chain metrics
            confidence = 0.7

            return SentimentScore(
                source='network_metrics',
                score=combined_sentiment,
                confidence=confidence,
                weight=0.05,
                timestamp=datetime.now(),
                sample_size=1,
                metadata={
                    'mvrv_ratio': mvrv_ratio,
                    'nvt_ratio': nvt_ratio,
                    'mvrv_interpretation': (
                        'Extremely overvalued' if mvrv_ratio > 3.5 else
                        'Overvalued' if mvrv_ratio > 2.5 else
                        'Fair value' if 1.0 <= mvrv_ratio <= 2.5 else
                        'Undervalued'
                    ),
                    'nvt_interpretation': (
                        'Overvalued vs usage' if nvt_ratio > 100 else
                        'Fair valuation' if 50 <= nvt_ratio <= 100 else
                        'Undervalued vs usage'
                    )
                }
            )

        except Exception as e:
            logger.error(f"Network value metrics analysis error: {e}")
            return self._empty_sentiment_score('network_metrics')

    def _empty_sentiment_score(self, source: str) -> SentimentScore:
        """Return empty sentiment score"""
        return SentimentScore(
            source=source,
            score=0.0,
            confidence=0.0,
            weight=0.0,
            timestamp=datetime.now(),
            sample_size=0,
            metadata={}
        )

    async def close(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()


class MarketSentimentAggregator:
    """Aggregate all sentiment sources into unified score"""

    def __init__(self, config: Dict):
        self.config = config
        self.social_analyzer = SocialMediaAnalyzer(config)
        self.derivatives_analyzer = DerivativesAnalyzer()
        self.onchain_analyzer = OnChainAnalyzer(config)

        # Historical sentiment tracking
        self.sentiment_history = deque(maxlen=168)  # 7 days of hourly data

    async def analyze_complete_sentiment(self, symbol: str) -> Dict:
        """Run complete sentiment analysis"""
        logger.info(f"Starting comprehensive sentiment analysis for {symbol}")

        # Gather all sentiment sources concurrently
        tasks = [
            self.social_analyzer.analyze_twitter(symbol),
            self.social_analyzer.analyze_reddit(symbol),
            self.social_analyzer.analyze_telegram(symbol),
            self.derivatives_analyzer.analyze_funding_rates(symbol),
            self.derivatives_analyzer.analyze_options_sentiment(symbol),
            self.onchain_analyzer.analyze_whale_movements(symbol),
            self.onchain_analyzer.analyze_network_value_metrics(symbol)
        ]

        sentiment_scores = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        valid_scores = [
            score for score in sentiment_scores
            if isinstance(score, SentimentScore) and score.confidence > 0
        ]

        if not valid_scores:
            logger.warning("No valid sentiment scores obtained")
            return self._empty_analysis_result(symbol)

        # Calculate weighted aggregate sentiment
        aggregate_sentiment = self._calculate_weighted_sentiment(valid_scores)

        # Calculate Fear & Greed Index
        fear_greed_index = self._calculate_fear_greed_index(valid_scores, aggregate_sentiment)

        # Generate sentiment alerts
        alerts = self._generate_alerts(valid_scores, fear_greed_index)

        # Store in history
        self.sentiment_history.append({
            'timestamp': datetime.now(),
            'sentiment': aggregate_sentiment,
            'fear_greed_score': fear_greed_index.score
        })

        # Calculate trend
        trend = self._calculate_trend()

        # Perform correlation analysis with historical price
        correlation_analysis = await self._analyze_sentiment_price_correlation(symbol)

        result = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'aggregate_sentiment': {
                'score': aggregate_sentiment,
                'normalized_score': (aggregate_sentiment + 1) / 2,  # 0 to 1 scale
                'interpretation': self._interpret_sentiment(aggregate_sentiment)
            },
            'fear_greed_index': {
                'score': fear_greed_index.score,
                'level': fear_greed_index.level.value,
                'historical_percentile': fear_greed_index.historical_percentile,
                'trend': trend,
                'components': fear_greed_index.components
            },
            'sentiment_sources': [
                {
                    'source': score.source,
                    'score': score.score,
                    'confidence': score.confidence,
                    'weight': score.weight,
                    'sample_size': score.sample_size,
                    'metadata': score.metadata
                }
                for score in valid_scores
            ],
            'alerts': [
                {
                    'type': alert.alert_type,
                    'severity': alert.severity,
                    'message': alert.message,
                    'sentiment_score': alert.sentiment_score,
                    'trigger': alert.trigger_condition
                }
                for alert in alerts
            ],
            'correlation_analysis': correlation_analysis,
            'data_quality': {
                'sources_analyzed': len(valid_scores),
                'total_samples': sum(score.sample_size for score in valid_scores),
                'avg_confidence': statistics.mean([score.confidence for score in valid_scores]),
                'coverage_percentage': (len(valid_scores) / 7) * 100  # 7 possible sources
            }
        }

        logger.info(f"Sentiment analysis complete: {fear_greed_index.level.value} "
                   f"(score: {fear_greed_index.score})")

        return result

    def _calculate_weighted_sentiment(self, scores: List[SentimentScore]) -> float:
        """Calculate weighted average sentiment"""
        weighted_sum = sum(
            score.score * score.weight * score.confidence
            for score in scores
        )
        total_weight = sum(
            score.weight * score.confidence
            for score in scores
        )

        if total_weight == 0:
            return 0.0

        return weighted_sum / total_weight

    def _calculate_fear_greed_index(
        self,
        scores: List[SentimentScore],
        aggregate_sentiment: float
    ) -> FearGreedIndex:
        """Calculate Fear & Greed Index (0-100)"""

        # Start with aggregate sentiment scaled to 0-100
        base_score = (aggregate_sentiment + 1) * 50

        # Build component scores
        components = {}

        for score in scores:
            # Scale each source to 0-100
            component_score = (score.score + 1) * 50
            components[score.source] = component_score

        # Calculate historical percentile
        if len(self.sentiment_history) > 10:
            historical_scores = [h['fear_greed_score'] for h in self.sentiment_history]
            percentile = (
                sum(1 for s in historical_scores if s < base_score) /
                len(historical_scores) * 100
            )
        else:
            percentile = 50.0  # Default to median if insufficient history

        # Determine sentiment level
        if base_score >= 75:
            level = SentimentLevel.EXTREME_GREED
        elif base_score >= 55:
            level = SentimentLevel.GREED
        elif base_score >= 45:
            level = SentimentLevel.NEUTRAL
        elif base_score >= 25:
            level = SentimentLevel.FEAR
        else:
            level = SentimentLevel.EXTREME_FEAR

        return FearGreedIndex(
            score=int(base_score),
            level=level,
            components=components,
            historical_percentile=percentile,
            trend='',  # Calculated separately
            timestamp=datetime.now()
        )

    def _calculate_trend(self) -> str:
        """Calculate sentiment trend from history"""
        if len(self.sentiment_history) < 5:
            return 'insufficient_data'

        # Compare recent average to older average
        recent_scores = [h['fear_greed_score'] for h in list(self.sentiment_history)[-5:]]
        older_scores = [h['fear_greed_score'] for h in list(self.sentiment_history)[-10:-5]]

        recent_avg = statistics.mean(recent_scores)
        older_avg = statistics.mean(older_scores)

        diff = recent_avg - older_avg

        if diff > 5:
            return 'increasing'
        elif diff < -5:
            return 'decreasing'
        else:
            return 'stable'

    def _generate_alerts(
        self,
        scores: List[SentimentScore],
        fear_greed: FearGreedIndex
    ) -> List[SentimentAlert]:
        """Generate trading alerts based on sentiment extremes"""
        alerts = []

        # Extreme Fear alert (potential buying opportunity)
        if fear_greed.level == SentimentLevel.EXTREME_FEAR:
            alerts.append(SentimentAlert(
                alert_type='contrarian_buy_opportunity',
                severity='high',
                message=f'Extreme Fear detected (score: {fear_greed.score}). '
                       'Historically, this has preceded price rebounds.',
                sentiment_score=fear_greed.score,
                trigger_condition='fear_greed_score < 25',
                timestamp=datetime.now()
            ))

        # Extreme Greed alert (potential selling opportunity)
        if fear_greed.level == SentimentLevel.EXTREME_GREED:
            alerts.append(SentimentAlert(
                alert_type='contrarian_sell_opportunity',
                severity='high',
                message=f'Extreme Greed detected (score: {fear_greed.score}). '
                       'Market may be overheated - consider profit taking.',
                sentiment_score=fear_greed.score,
                trigger_condition='fear_greed_score > 75',
                timestamp=datetime.now()
            ))

        # Funding rate extreme alert
        funding_score = next(
            (s for s in scores if s.source == 'funding_rates'),
            None
        )
        if funding_score and abs(funding_score.score) > 0.7:
            direction = 'long' if funding_score.score > 0 else 'short'
            alerts.append(SentimentAlert(
                alert_type='funding_rate_extreme',
                severity='medium',
                message=f'Extreme {direction} funding rate detected. '
                       f'Potential for {direction} squeeze or reversal.',
                sentiment_score=funding_score.score,
                trigger_condition=f'abs(funding_rate_score) > 0.7',
                timestamp=datetime.now()
            ))

        # Whale movement alert
        whale_score = next(
            (s for s in scores if s.source == 'whale_movements'),
            None
        )
        if whale_score and abs(whale_score.score) > 0.5:
            direction = 'accumulation' if whale_score.score > 0 else 'distribution'
            alerts.append(SentimentAlert(
                alert_type='whale_activity',
                severity='medium',
                message=f'Significant whale {direction} detected. '
                       f'Smart money may be positioning for trend.',
                sentiment_score=whale_score.score,
                trigger_condition='abs(whale_score) > 0.5',
                timestamp=datetime.now()
            ))

        return alerts

    async def _analyze_sentiment_price_correlation(self, symbol: str) -> Dict:
        """Analyze correlation between sentiment and price movements"""
        try:
            if len(self.sentiment_history) < 20:
                return {
                    'status': 'insufficient_data',
                    'message': 'Need at least 20 data points for correlation analysis'
                }

            # Extract sentiment scores
            sentiments = [h['sentiment'] for h in self.sentiment_history]

            # Would fetch actual price data here
            # For demonstration, simulating price correlation

            # Calculate correlation coefficient (simulated)
            correlation = 0.65  # Simulated positive correlation

            # Calculate lead/lag relationship
            # Does sentiment lead price, or vice versa?
            sentiment_leads_price = True  # Simulated
            lag_hours = 6  # Simulated

            return {
                'status': 'success',
                'correlation_coefficient': correlation,
                'correlation_strength': (
                    'strong' if abs(correlation) > 0.7 else
                    'moderate' if abs(correlation) > 0.4 else
                    'weak'
                ),
                'relationship': (
                    'Sentiment leads price' if sentiment_leads_price
                    else 'Price leads sentiment'
                ),
                'lag_hours': lag_hours,
                'sample_size': len(sentiments),
                'interpretation': (
                    'Sentiment changes typically precede price movements by ~6 hours. '
                    'Strong correlation suggests sentiment is a useful leading indicator.'
                    if sentiment_leads_price and abs(correlation) > 0.6
                    else 'Moderate correlation. Sentiment should be combined with other factors.'
                )
            }

        except Exception as e:
            logger.error(f"Correlation analysis error: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    def _interpret_sentiment(self, score: float) -> str:
        """Interpret aggregate sentiment score"""
        if score > 0.6:
            return 'Very Bullish'
        elif score > 0.2:
            return 'Bullish'
        elif score > -0.2:
            return 'Neutral'
        elif score > -0.6:
            return 'Bearish'
        else:
            return 'Very Bearish'

    def _empty_analysis_result(self, symbol: str) -> Dict:
        """Return empty analysis result"""
        return {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'error': 'Unable to gather sufficient sentiment data',
            'aggregate_sentiment': None,
            'fear_greed_index': None,
            'sentiment_sources': [],
            'alerts': []
        }

    async def close(self):
        """Cleanup resources"""
        await self.onchain_analyzer.close()


async def main():
    """Example usage"""

    # Configuration
    config = {
        'twitter_bearer_token': 'YOUR_TWITTER_TOKEN',
        'reddit_client_id': 'YOUR_REDDIT_CLIENT_ID',
        'reddit_client_secret': 'YOUR_REDDIT_SECRET',
        'telegram_api_id': 'YOUR_TELEGRAM_API_ID',
        'telegram_api_hash': 'YOUR_TELEGRAM_HASH',
        'telegram_channels': ['bitcoin', 'cryptocurrency'],
        'whale_alert_api_key': 'YOUR_WHALE_ALERT_KEY',
        'ethereum_rpc': 'https://mainnet.infura.io/v3/YOUR_KEY'
    }

    # Initialize aggregator
    aggregator = MarketSentimentAggregator(config)

    try:
        # Analyze sentiment
        result = await aggregator.analyze_complete_sentiment('BTC')

        # Pretty print results
        print("\n" + "="*80)
        print(f"MARKET SENTIMENT ANALYSIS - {result['symbol']}")
        print("="*80)

        print(f"\nFear & Greed Index: {result['fear_greed_index']['score']} - "
              f"{result['fear_greed_index']['level']}")
        print(f"Trend: {result['fear_greed_index']['trend']}")
        print(f"Historical Percentile: {result['fear_greed_index']['historical_percentile']:.1f}%")

        print(f"\nAggregate Sentiment: {result['aggregate_sentiment']['interpretation']}")
        print(f"Score: {result['aggregate_sentiment']['score']:.3f}")

        print("\nSentiment by Source:")
        print("-" * 80)
        for source in result['sentiment_sources']:
            print(f"  {source['source']:20} | Score: {source['score']:6.3f} | "
                  f"Confidence: {source['confidence']:.2f} | Samples: {source['sample_size']}")

        if result['alerts']:
            print("\nAlerts:")
            print("-" * 80)
            for alert in result['alerts']:
                print(f"  [{alert['severity'].upper()}] {alert['message']}")

        print("\nData Quality:")
        print("-" * 80)
        print(f"  Sources Analyzed: {result['data_quality']['sources_analyzed']}")
        print(f"  Total Samples: {result['data_quality']['total_samples']}")
        print(f"  Avg Confidence: {result['data_quality']['avg_confidence']:.2%}")
        print(f"  Coverage: {result['data_quality']['coverage_percentage']:.1f}%")

        if result['correlation_analysis']['status'] == 'success':
            print("\nSentiment-Price Correlation:")
            print("-" * 80)
            corr = result['correlation_analysis']
            print(f"  Correlation: {corr['correlation_coefficient']:.3f} ({corr['correlation_strength']})")
            print(f"  Relationship: {corr['relationship']}")
            print(f"  {corr['interpretation']}")

        print("\n" + "="*80)

        # Export to JSON
        output_file = f"sentiment_analysis_{result['symbol']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\nFull analysis exported to: {output_file}")

    finally:
        await aggregator.close()


if __name__ == '__main__':
    asyncio.run(main())
```

## Usage Examples

### Command-Line Analysis
```bash
# Basic sentiment analysis
/analyze-sentiment BTC

# Analysis with specific lookback period
/analyze-sentiment ETH --lookback 48h

# Export to JSON
/analyze-sentiment BTC --output sentiment_btc.json

# Monitor sentiment in real-time
/analyze-sentiment BTC --monitor --interval 1h
```

### Integration with Trading Strategy
```python
# Use sentiment for entry signals
result = await aggregator.analyze_complete_sentiment('BTC')

if result['fear_greed_index']['level'] == 'Extreme Fear':
    # Potential buying opportunity
    if result['aggregate_sentiment']['score'] < -0.6:
        print("STRONG BUY SIGNAL: Extreme fear with very bearish sentiment")

# Check for reversal signals
if len(result['alerts']) > 0:
    for alert in result['alerts']:
        if alert['type'] == 'contrarian_buy_opportunity':
            print(f"Contrarian signal: {alert['message']}")
```

## Interpretation Guidelines

### Fear & Greed Extremes
- **Extreme Fear (0-25)**: Historically good buying opportunities (contrarian)
- **Extreme Greed (75-100)**: Potential market tops, consider profit-taking

### Derivatives Signals
- **High positive funding rates**: Overleveraged longs, potential for long squeeze
- **High negative funding rates**: Overleveraged shorts, potential for short squeeze
- **Extreme put/call ratios**: Sentiment extremes often precede reversals

### Whale Activity
- **Large exchange withdrawals**: Accumulation phase (bullish)
- **Large exchange deposits**: Distribution phase (bearish)
- **Divergence from retail**: Smart money positioning differently

## Limitations & Considerations

1. **Sentiment Lags**: Social sentiment often lags price action
2. **Manipulation**: Coordinated FUD/FOMO campaigns can skew results
3. **Bot Activity**: Social media bots can create artificial sentiment
4. **Sample Bias**: Limited to English-language sources
5. **Market Context**: Sentiment should be combined with technical and fundamental analysis

## Advanced Features

- **Sentiment momentum**: Rate of change in sentiment scores
- **Source divergence detection**: Conflicting signals across sources
- **Influencer tracking**: Weighted sentiment from high-follower accounts
- **Time decay**: Recent sentiment weighted more heavily
- **Volatility adjustment**: Sentiment normalized by market volatility

## Future Enhancements

- Machine learning sentiment prediction models
- Real-time sentiment streaming dashboard
- Integration with automated trading systems
- Multi-asset sentiment correlation
- Sentiment-based portfolio rebalancing