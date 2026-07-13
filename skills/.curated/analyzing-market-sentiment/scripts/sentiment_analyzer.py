#!/usr/bin/env python3
"""
Market Sentiment Analyzer - Main CLI Entry Point

Analyze cryptocurrency market sentiment using Fear & Greed Index,
news sentiment, and market momentum.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 2.0.0
License: MIT
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict

# Add scripts directory to path for local imports
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from fear_greed import FearGreedFetcher
from news_sentiment import NewsSentimentAnalyzer
from market_momentum import MarketMomentumAnalyzer
from formatters import SentimentFormatter


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Analyze cryptocurrency market sentiment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                # Quick sentiment check
  %(prog)s --coin BTC                     # Bitcoin-specific sentiment
  %(prog)s --detailed                     # Full component breakdown
  %(prog)s --format json --output s.json  # Export to JSON
        """,
    )

    # Analysis options
    parser.add_argument("--coin", type=str, help="Analyze specific coin (e.g., BTC, ETH)")
    parser.add_argument(
        "--period",
        type=str,
        choices=["1h", "4h", "24h", "7d"],
        default="24h",
        help="Time period for analysis (default: 24h)",
    )
    parser.add_argument("--detailed", action="store_true", help="Show detailed component breakdown")

    # Weight customization
    parser.add_argument("--weights", type=str, help="Custom weights (e.g., 'news:0.5,fng:0.3,momentum:0.2')")

    # Output options
    parser.add_argument(
        "--format",
        "-f",
        type=str,
        choices=["table", "json", "csv"],
        default="table",
        help="Output format (default: table)",
    )
    parser.add_argument("--output", "-o", type=str, help="Output file path (default: stdout)")

    # Debug options
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--version", action="version", version="%(prog)s 2.0.0")

    return parser.parse_args()


def parse_weights(weights_str: Optional[str]) -> Dict[str, float]:
    """Parse custom weights string."""
    default_weights = {"fear_greed": 0.40, "news": 0.40, "momentum": 0.20}

    if not weights_str:
        return default_weights

    try:
        weights = {}
        for part in weights_str.split(","):
            key, value = part.strip().split(":")
            key = key.strip().lower()
            # Map shorthand names
            if key == "fng":
                key = "fear_greed"
            weights[key] = float(value.strip())

        # Fill in missing weights with defaults
        for key in default_weights:
            if key not in weights:
                weights[key] = default_weights[key]

        # Normalize to sum to 1.0
        total = sum(weights.values())
        if total > 0:
            weights = {k: v / total for k, v in weights.items()}

        return weights

    except Exception:
        return default_weights


def classify_sentiment(score: float) -> str:
    """Classify sentiment score into category."""
    if score <= 20:
        return "Extreme Fear"
    elif score <= 40:
        return "Fear"
    elif score <= 60:
        return "Neutral"
    elif score <= 80:
        return "Greed"
    else:
        return "Extreme Greed"


def get_interpretation(score: float, classification: str) -> str:
    """Generate interpretation text for sentiment score."""
    interpretations = {
        "Extreme Fear": (
            "Market is in extreme fear. Historically, this has been a good "
            "buying opportunity for long-term investors. However, prices may "
            "continue falling in the short term."
        ),
        "Fear": (
            "Market sentiment is fearful. Caution is advised, but oversold "
            "conditions may present opportunities for those with higher risk "
            "tolerance."
        ),
        "Neutral": (
            "Market sentiment is balanced with no strong directional bias. "
            "Wait for clearer signals before making major decisions."
        ),
        "Greed": (
            "Market is moderately greedy. Consider taking some profits or "
            "reducing position sizes. Watch for reversal signals."
        ),
        "Extreme Greed": (
            "Market is in extreme greed territory. Exercise caution - this "
            "level often precedes corrections. Consider defensive positioning."
        ),
    }
    return interpretations.get(classification, "")


def main() -> None:
    """Main entry point."""
    args = parse_args()

    # Parse custom weights
    weights = parse_weights(args.weights)

    if args.verbose:
        print(f"Using weights: {weights}", file=sys.stderr)

    # Initialize analyzers
    fng_fetcher = FearGreedFetcher(verbose=args.verbose)
    news_analyzer = NewsSentimentAnalyzer(verbose=args.verbose)
    momentum_analyzer = MarketMomentumAnalyzer(verbose=args.verbose)
    formatter = SentimentFormatter()

    # Collect components
    components = {}
    errors = []

    # 1. Fear & Greed Index
    if args.verbose:
        print("Fetching Fear & Greed Index...", file=sys.stderr)

    fng_data = fng_fetcher.fetch()
    if fng_data:
        components["fear_greed"] = {
            "score": fng_data.get("value", 50),
            "classification": fng_data.get("classification", "Neutral"),
            "weight": weights.get("fear_greed", 0.4),
            "contribution": fng_data.get("value", 50) * weights.get("fear_greed", 0.4),
            "timestamp": fng_data.get("timestamp"),
        }
    else:
        errors.append("Fear & Greed Index unavailable")
        components["fear_greed"] = {
            "score": 50,
            "classification": "Unknown",
            "weight": weights.get("fear_greed", 0.4),
            "contribution": 50 * weights.get("fear_greed", 0.4),
            "error": "API unavailable",
        }

    # 2. News Sentiment
    if args.verbose:
        print("Analyzing news sentiment...", file=sys.stderr)

    news_data = news_analyzer.analyze(coin=args.coin, period=args.period)
    if news_data:
        components["news_sentiment"] = {
            "score": news_data.get("score", 50),
            "articles_analyzed": news_data.get("articles_analyzed", 0),
            "positive": news_data.get("positive", 0),
            "negative": news_data.get("negative", 0),
            "neutral": news_data.get("neutral", 0),
            "weight": weights.get("news", 0.4),
            "contribution": news_data.get("score", 50) * weights.get("news", 0.4),
        }
    else:
        errors.append("News sentiment analysis unavailable")
        components["news_sentiment"] = {
            "score": 50,
            "articles_analyzed": 0,
            "weight": weights.get("news", 0.4),
            "contribution": 50 * weights.get("news", 0.4),
            "error": "Analysis unavailable",
        }

    # 3. Market Momentum
    if args.verbose:
        print("Calculating market momentum...", file=sys.stderr)

    momentum_data = momentum_analyzer.analyze(coin=args.coin)
    if momentum_data:
        components["market_momentum"] = {
            "score": momentum_data.get("score", 50),
            "btc_change_24h": momentum_data.get("btc_change_24h"),
            "eth_change_24h": momentum_data.get("eth_change_24h"),
            "volume_ratio": momentum_data.get("volume_ratio"),
            "weight": weights.get("momentum", 0.2),
            "contribution": momentum_data.get("score", 50) * weights.get("momentum", 0.2),
        }
    else:
        errors.append("Market momentum unavailable")
        components["market_momentum"] = {
            "score": 50,
            "weight": weights.get("momentum", 0.2),
            "contribution": 50 * weights.get("momentum", 0.2),
            "error": "Data unavailable",
        }

    # Calculate composite score
    composite_score = sum(c.get("contribution", 0) for c in components.values())
    composite_score = round(composite_score, 1)

    classification = classify_sentiment(composite_score)
    interpretation = get_interpretation(composite_score, classification)

    # Prepare result
    result = {
        "composite_score": composite_score,
        "classification": classification,
        "interpretation": interpretation,
        "components": components,
        "meta": {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "period": args.period,
            "coin_filter": args.coin,
            "weights": weights,
            "errors": errors if errors else None,
        },
    }

    # Format output
    output = formatter.format(result, format_type=args.format, detailed=args.detailed)

    # Write output
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            f.write(output)
        print(f"Output written to {output_path}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
