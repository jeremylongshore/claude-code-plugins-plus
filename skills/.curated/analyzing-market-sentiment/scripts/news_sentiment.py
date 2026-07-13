#!/usr/bin/env python3
"""
News Sentiment Analyzer

Analyzes cryptocurrency news sentiment using keyword-based scoring.
Optionally integrates with crypto-news-aggregator skill.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 2.0.0
License: MIT
"""

import json
import re
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List

try:
    import requests
except ImportError:
    print("Error: requests library required. Install with: pip install requests", file=sys.stderr)
    sys.exit(1)


# Sentiment keywords with weights
POSITIVE_KEYWORDS = {
    # Strong positive (0.3)
    "bullish": 0.3,
    "surge": 0.3,
    "soar": 0.3,
    "rally": 0.3,
    "breakout": 0.3,
    "record high": 0.3,
    "all-time high": 0.3,
    "ath": 0.3,
    "moon": 0.3,
    # Medium positive (0.2)
    "adoption": 0.2,
    "partnership": 0.2,
    "approval": 0.2,
    "milestone": 0.2,
    "upgrade": 0.2,
    "launch": 0.2,
    "integration": 0.2,
    "institutional": 0.2,
    "etf": 0.2,
    "accumulation": 0.2,
    "inflow": 0.2,
    "buy": 0.2,
    # Mild positive (0.1)
    "gain": 0.1,
    "rise": 0.1,
    "up": 0.1,
    "growth": 0.1,
    "positive": 0.1,
    "optimistic": 0.1,
    "recovery": 0.1,
    "support": 0.1,
    "bullrun": 0.1,
}

NEGATIVE_KEYWORDS = {
    # Strong negative (-0.3)
    "bearish": -0.3,
    "crash": -0.3,
    "dump": -0.3,
    "collapse": -0.3,
    "hack": -0.3,
    "exploit": -0.3,
    "scam": -0.3,
    "fraud": -0.3,
    "bankruptcy": -0.3,
    "insolvent": -0.3,
    "rug pull": -0.3,
    "rugpull": -0.3,
    # Medium negative (-0.2)
    "ban": -0.2,
    "lawsuit": -0.2,
    "investigation": -0.2,
    "sec": -0.2,
    "regulation": -0.2,
    "crackdown": -0.2,
    "sell-off": -0.2,
    "selloff": -0.2,
    "outflow": -0.2,
    "withdrawal": -0.2,
    "liquidation": -0.2,
    # Mild negative (-0.1)
    "decline": -0.1,
    "drop": -0.1,
    "fall": -0.1,
    "down": -0.1,
    "loss": -0.1,
    "concern": -0.1,
    "risk": -0.1,
    "uncertain": -0.1,
    "volatility": -0.1,
    "correction": -0.1,
    "dip": -0.1,
    "fear": -0.1,
    "weak": -0.1,
}

# Coin-specific keywords
COIN_ALIASES = {
    "BTC": ["bitcoin", "btc", "satoshi"],
    "ETH": ["ethereum", "eth", "ether"],
    "SOL": ["solana", "sol"],
    "XRP": ["ripple", "xrp"],
    "ADA": ["cardano", "ada"],
    "DOGE": ["dogecoin", "doge"],
    "DOT": ["polkadot", "dot"],
    "LINK": ["chainlink", "link"],
    "AVAX": ["avalanche", "avax"],
    "MATIC": ["polygon", "matic"],
}


class NewsSentimentAnalyzer:
    """Analyzes news sentiment for cryptocurrency markets."""

    RSS_FEEDS = [
        "https://cointelegraph.com/rss",
        "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "https://decrypt.co/feed",
    ]

    CACHE_FILE = Path(__file__).parent / ".news_cache.json"
    CACHE_TTL = 120  # 2 minutes

    def __init__(self, verbose: bool = False):
        """Initialize analyzer.

        Args:
            verbose: Enable verbose output
        """
        self.verbose = verbose
        self._cache: Dict[str, Any] = {}
        self._cache_time: float = 0

    def analyze(self, coin: Optional[str] = None, period: str = "24h") -> Optional[Dict[str, Any]]:
        """Analyze news sentiment.

        Args:
            coin: Filter by specific coin (e.g., "BTC", "ETH")
            period: Time period ("1h", "4h", "24h", "7d")

        Returns:
            Dict with score (0-100), articles_analyzed, positive, negative, neutral
        """
        # Check cache
        cache_key = f"{coin or 'all'}:{period}"
        if self._is_cache_valid(cache_key):
            if self.verbose:
                print(f"Using cached news sentiment for {cache_key}", file=sys.stderr)
            return self._cache.get(cache_key)

        # Try news aggregator skill first
        aggregator_result = self._try_news_aggregator(coin, period)
        if aggregator_result:
            self._cache[cache_key] = aggregator_result
            self._cache_time = time.time()
            return aggregator_result

        # Fallback to direct RSS fetch
        articles = self._fetch_rss_articles(period)
        if not articles:
            if self.verbose:
                print("No articles fetched, returning neutral sentiment", file=sys.stderr)
            return {
                "score": 50,
                "articles_analyzed": 0,
                "positive": 0,
                "negative": 0,
                "neutral": 0,
                "error": "No articles available",
            }

        # Filter by coin if specified
        if coin:
            articles = self._filter_by_coin(articles, coin.upper())

        # Score articles
        scored = self._score_articles(articles)

        # Calculate aggregate score
        result = self._aggregate_scores(scored)
        result["source"] = "rss"

        self._cache[cache_key] = result
        self._cache_time = time.time()

        return result

    def _try_news_aggregator(self, coin: Optional[str], period: str) -> Optional[Dict[str, Any]]:
        """Try to use crypto-news-aggregator skill if available."""
        # Check for news aggregator in sibling plugin
        aggregator_path = (
            Path(__file__).parent.parent.parent.parent.parent
            / "crypto-news-aggregator"
            / "skills"
            / "aggregating-crypto-news"
            / "scripts"
        )

        if not aggregator_path.exists():
            if self.verbose:
                print("News aggregator skill not found", file=sys.stderr)
            return None

        try:
            sys.path.insert(0, str(aggregator_path))
            from news_aggregator import NewsAggregator

            sys.path.pop(0)

            if self.verbose:
                print("Using news aggregator skill", file=sys.stderr)

            aggregator = NewsAggregator(verbose=self.verbose)
            news_data = aggregator.fetch(coin=coin, period=period, limit=50)

            if not news_data or not news_data.get("articles"):
                return None

            # Score the aggregated articles
            articles = [
                {"title": a.get("title", ""), "summary": a.get("summary", "")} for a in news_data.get("articles", [])
            ]

            scored = self._score_articles(articles)
            result = self._aggregate_scores(scored)
            result["source"] = "aggregator"

            return result

        except Exception as e:
            if self.verbose:
                print(f"News aggregator failed: {e}", file=sys.stderr)
            return None

    def _fetch_rss_articles(self, period: str) -> List[Dict[str, Any]]:
        """Fetch articles from RSS feeds."""
        articles = []
        cutoff = self._get_cutoff_time(period)

        for feed_url in self.RSS_FEEDS:
            try:
                if self.verbose:
                    print(f"Fetching RSS: {feed_url}", file=sys.stderr)

                response = requests.get(feed_url, timeout=10)
                response.raise_for_status()

                # Simple XML parsing for RSS
                parsed = self._parse_rss_xml(response.text, cutoff)
                articles.extend(parsed)

            except Exception as e:
                if self.verbose:
                    print(f"Failed to fetch {feed_url}: {e}", file=sys.stderr)
                continue

        # Deduplicate by title
        seen = set()
        unique = []
        for article in articles:
            title_key = article.get("title", "").lower()[:50]
            if title_key and title_key not in seen:
                seen.add(title_key)
                unique.append(article)

        return unique

    def _parse_rss_xml(self, xml_content: str, cutoff: datetime) -> List[Dict[str, Any]]:
        """Parse RSS XML content."""
        articles = []

        # Extract items using regex (simple approach)
        items = re.findall(r"<item>(.*?)</item>", xml_content, re.DOTALL)

        for item in items:
            # Extract title
            title_match = re.search(r"<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>", item, re.DOTALL)
            title = title_match.group(1).strip() if title_match else ""

            # Extract description
            desc_match = re.search(r"<description>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</description>", item, re.DOTALL)
            description = desc_match.group(1).strip() if desc_match else ""

            # Clean HTML
            title = re.sub(r"<[^>]+>", "", title)
            description = re.sub(r"<[^>]+>", "", description)

            if title:
                articles.append({"title": title, "summary": description[:500]})

        return articles[:30]  # Limit per feed

    def _filter_by_coin(self, articles: List[Dict[str, Any]], coin: str) -> List[Dict[str, Any]]:
        """Filter articles mentioning specific coin."""
        keywords = COIN_ALIASES.get(coin, [coin.lower()])

        filtered = []
        for article in articles:
            text = f"{article.get('title', '')} {article.get('summary', '')}".lower()
            if any(kw in text for kw in keywords):
                filtered.append(article)

        return filtered if filtered else articles  # Return all if no matches

    def _score_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Score each article for sentiment."""
        scored = []

        for article in articles:
            text = f"{article.get('title', '')} {article.get('summary', '')}".lower()
            score = 0.0

            # Check positive keywords
            for keyword, weight in POSITIVE_KEYWORDS.items():
                if keyword in text:
                    score += weight

            # Check negative keywords
            for keyword, weight in NEGATIVE_KEYWORDS.items():
                if keyword in text:
                    score += weight  # weight is already negative

            # Clamp to [-1, 1]
            score = max(-1, min(1, score))

            # Classify
            if score > 0.1:
                sentiment = "positive"
            elif score < -0.1:
                sentiment = "negative"
            else:
                sentiment = "neutral"

            scored.append({**article, "score": score, "sentiment": sentiment})

        return scored

    def _aggregate_scores(self, scored: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate article scores to overall sentiment."""
        if not scored:
            return {"score": 50, "articles_analyzed": 0, "positive": 0, "negative": 0, "neutral": 0}

        positive = sum(1 for a in scored if a["sentiment"] == "positive")
        negative = sum(1 for a in scored if a["sentiment"] == "negative")
        neutral = sum(1 for a in scored if a["sentiment"] == "neutral")

        # Calculate weighted average score
        total_score = sum(a["score"] for a in scored)
        avg_score = total_score / len(scored)  # -1 to +1

        # Convert to 0-100 scale
        normalized_score = (avg_score + 1) * 50

        return {
            "score": round(normalized_score, 1),
            "articles_analyzed": len(scored),
            "positive": positive,
            "negative": negative,
            "neutral": neutral,
            "top_positive": [
                a["title"]
                for a in sorted(scored, key=lambda x: x["score"], reverse=True)[:3]
                if a["sentiment"] == "positive"
            ],
            "top_negative": [
                a["title"] for a in sorted(scored, key=lambda x: x["score"])[:3] if a["sentiment"] == "negative"
            ],
        }

    def _get_cutoff_time(self, period: str) -> datetime:
        """Get cutoff datetime for period."""
        now = datetime.utcnow()
        deltas = {
            "1h": timedelta(hours=1),
            "4h": timedelta(hours=4),
            "24h": timedelta(days=1),
            "7d": timedelta(days=7),
        }
        return now - deltas.get(period, timedelta(days=1))

    def _is_cache_valid(self, key: str) -> bool:
        """Check if cache entry is valid."""
        if key not in self._cache:
            return False
        return (time.time() - self._cache_time) < self.CACHE_TTL


def main():
    """CLI entry point for testing."""
    import argparse

    parser = argparse.ArgumentParser(description="Analyze crypto news sentiment")
    parser.add_argument("--coin", type=str, help="Filter by coin (BTC, ETH, etc.)")
    parser.add_argument("--period", type=str, default="24h", help="Time period")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    analyzer = NewsSentimentAnalyzer(verbose=args.verbose)
    result = analyzer.analyze(coin=args.coin, period=args.period)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
