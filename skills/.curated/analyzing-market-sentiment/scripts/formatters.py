#!/usr/bin/env python3
"""
Sentiment Output Formatters

Formats sentiment analysis results in various output formats:
- Table (default): Terminal-friendly dashboard
- JSON: Machine-readable export
- CSV: Spreadsheet-compatible

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 2.0.0
License: MIT
"""

import csv
import io
import json
from datetime import datetime
from typing import Dict, Any


class SentimentFormatter:
    """Formats sentiment analysis results."""

    # Sentiment classification colors (ANSI)
    COLORS = {
        "Extreme Fear": "\033[91m",  # Red
        "Fear": "\033[93m",  # Yellow
        "Neutral": "\033[0m",  # Default
        "Greed": "\033[92m",  # Green
        "Extreme Greed": "\033[96m",  # Cyan
        "reset": "\033[0m",
    }

    def format(self, data: Dict[str, Any], format_type: str = "table", detailed: bool = False) -> str:
        """Format sentiment data for output.

        Args:
            data: Sentiment analysis result dict
            format_type: Output format ("table", "json", "csv")
            detailed: Include component breakdown

        Returns:
            Formatted string output
        """
        if format_type == "json":
            return self._format_json(data)
        elif format_type == "csv":
            return self._format_csv(data, detailed)
        else:
            return self._format_table(data, detailed)

    def _format_table(self, data: Dict[str, Any], detailed: bool) -> str:
        """Format as terminal table/dashboard."""
        lines = []
        w = 78  # Width

        # Header
        timestamp = data.get("meta", {}).get("timestamp", "")
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                time_str = dt.strftime("%Y-%m-%d %H:%M UTC")
            except ValueError:
                time_str = timestamp[:19]
        else:
            time_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

        lines.append("=" * w)
        lines.append(f"  MARKET SENTIMENT ANALYZER{' ' * (w - 42)}{time_str}")
        lines.append("=" * w)
        lines.append("")

        # Composite Score
        score = data.get("composite_score", 50)
        classification = data.get("classification", "Neutral")
        color = self.COLORS.get(classification, "")
        reset = self.COLORS["reset"]

        lines.append("  COMPOSITE SENTIMENT")
        lines.append("-" * w)
        lines.append(
            f"  Score: {color}{score:.1f}{reset} / 100{' ' * 30}Classification: {color}{classification.upper()}{reset}"
        )
        lines.append("")

        # Sentiment gauge
        gauge = self._create_gauge(score)
        lines.append(f"  {gauge}")
        lines.append("  0 -------- 25 -------- 50 -------- 75 -------- 100")
        lines.append("  FEAR                  NEUTRAL                 GREED")
        lines.append("")

        # Component breakdown (always show basic, detailed shows more)
        components = data.get("components", {})
        if components:
            lines.append("  COMPONENTS")
            lines.append("-" * w)

            # Fear & Greed
            fg = components.get("fear_greed", {})
            fg_score = fg.get("score", 50)
            fg_weight = fg.get("weight", 0.4) * 100
            fg_contrib = fg.get("contribution", 20)
            fg_class = fg.get("classification", "Neutral")
            lines.append(
                f"  Fear & Greed Index:   {fg_score:5.1f}  (weight: {fg_weight:.0f}%)  → {fg_contrib:5.1f} pts  [{fg_class}]"
            )

            # News Sentiment
            ns = components.get("news_sentiment", {})
            ns_score = ns.get("score", 50)
            ns_weight = ns.get("weight", 0.4) * 100
            ns_contrib = ns.get("contribution", 20)
            ns_articles = ns.get("articles_analyzed", 0)
            lines.append(
                f"  News Sentiment:       {ns_score:5.1f}  (weight: {ns_weight:.0f}%)  → {ns_contrib:5.1f} pts  [{ns_articles} articles]"
            )

            # Market Momentum
            mm = components.get("market_momentum", {})
            mm_score = mm.get("score", 50)
            mm_weight = mm.get("weight", 0.2) * 100
            mm_contrib = mm.get("contribution", 10)
            btc_change = mm.get("btc_change_24h")
            btc_str = f"{btc_change:+.1f}%" if btc_change is not None else "N/A"
            lines.append(
                f"  Market Momentum:      {mm_score:5.1f}  (weight: {mm_weight:.0f}%)  → {mm_contrib:5.1f} pts  [BTC: {btc_str}]"
            )

            lines.append("")

        # Detailed breakdown
        if detailed:
            lines.append("  DETAILED BREAKDOWN")
            lines.append("-" * w)

            # News details
            ns = components.get("news_sentiment", {})
            if ns.get("articles_analyzed", 0) > 0:
                pos = ns.get("positive", 0)
                neg = ns.get("negative", 0)
                neu = ns.get("neutral", 0)
                lines.append("  News Analysis:")
                lines.append(f"    Positive: {pos}  |  Negative: {neg}  |  Neutral: {neu}")

                top_pos = ns.get("top_positive", [])
                if top_pos:
                    lines.append("    Top Positive Headlines:")
                    for headline in top_pos[:2]:
                        lines.append(f"      + {headline[:60]}...")

                top_neg = ns.get("top_negative", [])
                if top_neg:
                    lines.append("    Top Negative Headlines:")
                    for headline in top_neg[:2]:
                        lines.append(f"      - {headline[:60]}...")

                lines.append("")

            # Market details
            mm = components.get("market_momentum", {})
            eth_change = mm.get("eth_change_24h")
            vol_ratio = mm.get("volume_ratio")
            if eth_change is not None or vol_ratio is not None:
                lines.append("  Market Data:")
                if eth_change is not None:
                    lines.append(f"    ETH 24h: {eth_change:+.1f}%")
                if vol_ratio is not None:
                    vol_desc = "high" if vol_ratio > 1.2 else "normal" if vol_ratio > 0.8 else "low"
                    lines.append(f"    Volume Ratio: {vol_ratio:.2f}x ({vol_desc})")
                lines.append("")

        # Interpretation
        interpretation = data.get("interpretation", "")
        if interpretation:
            lines.append("  INTERPRETATION")
            lines.append("-" * w)
            # Word wrap interpretation
            words = interpretation.split()
            line = "  "
            for word in words:
                if len(line) + len(word) + 1 > w - 2:
                    lines.append(line)
                    line = "  " + word
                else:
                    line += " " + word if line.strip() else word
            if line.strip():
                lines.append(line)
            lines.append("")

        # Errors
        errors = data.get("meta", {}).get("errors")
        if errors:
            lines.append("  WARNINGS")
            lines.append("-" * w)
            for error in errors:
                lines.append(f"  ⚠ {error}")
            lines.append("")

        # Footer
        lines.append("=" * w)
        coin_filter = data.get("meta", {}).get("coin_filter")
        period = data.get("meta", {}).get("period", "24h")
        filter_str = f"Coin: {coin_filter}  |  " if coin_filter else ""
        lines.append(f"  {filter_str}Period: {period}  |  Sources: Fear & Greed, News, Market Data")
        lines.append("=" * w)

        return "\n".join(lines)

    def _format_json(self, data: Dict[str, Any]) -> str:
        """Format as JSON."""
        return json.dumps(data, indent=2, default=str)

    def _format_csv(self, data: Dict[str, Any], detailed: bool) -> str:
        """Format as CSV."""
        output = io.StringIO()
        writer = csv.writer(output)

        # Header row
        headers = [
            "timestamp",
            "composite_score",
            "classification",
            "fear_greed_score",
            "fear_greed_weight",
            "news_score",
            "news_weight",
            "news_articles",
            "momentum_score",
            "momentum_weight",
            "btc_change_24h",
            "period",
            "coin_filter",
        ]

        if detailed:
            headers.extend(["news_positive", "news_negative", "news_neutral", "eth_change_24h", "volume_ratio"])

        writer.writerow(headers)

        # Data row
        components = data.get("components", {})
        fg = components.get("fear_greed", {})
        ns = components.get("news_sentiment", {})
        mm = components.get("market_momentum", {})
        meta = data.get("meta", {})

        row = [
            meta.get("timestamp", ""),
            data.get("composite_score", 50),
            data.get("classification", "Neutral"),
            fg.get("score", 50),
            fg.get("weight", 0.4),
            ns.get("score", 50),
            ns.get("weight", 0.4),
            ns.get("articles_analyzed", 0),
            mm.get("score", 50),
            mm.get("weight", 0.2),
            mm.get("btc_change_24h", ""),
            meta.get("period", "24h"),
            meta.get("coin_filter", ""),
        ]

        if detailed:
            row.extend(
                [
                    ns.get("positive", 0),
                    ns.get("negative", 0),
                    ns.get("neutral", 0),
                    mm.get("eth_change_24h", ""),
                    mm.get("volume_ratio", ""),
                ]
            )

        writer.writerow(row)

        return output.getvalue()

    def _create_gauge(self, score: float) -> str:
        """Create ASCII gauge for sentiment score."""
        # 50 character gauge
        width = 50
        position = int((score / 100) * width)
        position = max(0, min(width - 1, position))

        gauge = ["-"] * width
        gauge[position] = "█"

        # Add markers
        if position > 0:
            gauge[0] = "|"
        if position < width - 1:
            gauge[width - 1] = "|"

        return "[" + "".join(gauge) + "]"


def main():
    """CLI entry point for testing."""
    # Test with sample data
    sample_data = {
        "composite_score": 65.5,
        "classification": "Greed",
        "interpretation": "Market is moderately greedy. Consider taking some profits or reducing position sizes. Watch for reversal signals.",
        "components": {
            "fear_greed": {"score": 72, "classification": "Greed", "weight": 0.40, "contribution": 28.8},
            "news_sentiment": {
                "score": 58.5,
                "articles_analyzed": 25,
                "positive": 12,
                "negative": 5,
                "neutral": 8,
                "weight": 0.40,
                "contribution": 23.4,
                "top_positive": ["Bitcoin breaks $50k resistance", "Institutional adoption surges"],
                "top_negative": ["SEC delays ETF decision"],
            },
            "market_momentum": {
                "score": 66.5,
                "btc_change_24h": 3.5,
                "eth_change_24h": 2.1,
                "volume_ratio": 1.2,
                "weight": 0.20,
                "contribution": 13.3,
            },
        },
        "meta": {"timestamp": "2026-01-14T15:30:00Z", "period": "24h", "coin_filter": None},
    }

    formatter = SentimentFormatter()

    print("=== TABLE FORMAT ===")
    print(formatter.format(sample_data, "table", detailed=True))
    print()
    print("=== JSON FORMAT ===")
    print(formatter.format(sample_data, "json"))
    print()
    print("=== CSV FORMAT ===")
    print(formatter.format(sample_data, "csv", detailed=True))


if __name__ == "__main__":
    main()
