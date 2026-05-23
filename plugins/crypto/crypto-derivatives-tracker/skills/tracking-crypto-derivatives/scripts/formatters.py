#!/usr/bin/env python3
"""
Output formatters for derivatives tracker.

Provides consistent formatting for:
- Console output (tables, charts)
- JSON export
- Report generation
"""

import json
from dataclasses import asdict
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder that handles Decimal types."""

    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def format_currency(value: Union[float, Decimal], decimals: int = 0) -> str:
    """Format value as currency."""
    val = float(value)
    if abs(val) >= 1e9:
        return f"${val / 1e9:.1f}B"
    elif abs(val) >= 1e6:
        return f"${val / 1e6:.1f}M"
    elif abs(val) >= 1e3:
        return f"${val / 1e3:.1f}K"
    else:
        return f"${val:,.{decimals}f}"


def format_percent(value: float, decimals: int = 2, sign: bool = True) -> str:
    """Format value as percentage."""
    if sign:
        return f"{value:+.{decimals}f}%"
    else:
        return f"{value:.{decimals}f}%"


def format_time_ago(dt: datetime) -> str:
    """Format datetime as time ago string."""
    delta = datetime.now() - dt
    minutes = int(delta.total_seconds() / 60)

    if minutes < 1:
        return "just now"
    elif minutes < 60:
        return f"{minutes}m ago"
    elif minutes < 1440:
        hours = minutes // 60
        return f"{hours}h ago"
    else:
        days = minutes // 1440
        return f"{days}d ago"


class ConsoleFormatter:
    """
    Formats data for console output.

    Features:
    - ASCII tables
    - Bar charts
    - Color indicators
    - Consistent widths
    """

    # Box drawing characters
    H_LINE = "─"
    V_LINE = "│"
    CROSS = "┼"
    TOP_LEFT = "┌"
    TOP_RIGHT = "┐"
    BOT_LEFT = "└"
    BOT_RIGHT = "┘"

    # Sentiment indicators
    BULLISH = "🟢"
    BEARISH = "🔴"
    NEUTRAL = "🟡"
    MIXED = "⚪"

    # Risk indicators
    RISK_CRITICAL = "🔴"
    RISK_HIGH = "🟠"
    RISK_MEDIUM = "🟡"
    RISK_LOW = "🟢"

    def __init__(self, width: int = 70):
        """Initialize formatter with terminal width."""
        self.width = width

    def header(self, title: str, char: str = "=") -> str:
        """Create a centered header."""
        return f"{char * self.width}\n{title.center(self.width)}\n{char * self.width}"

    def subheader(self, title: str, char: str = "-") -> str:
        """Create a subheader."""
        return f"{char * self.width}\n{title}\n{char * self.width}"

    def section(self, title: str) -> str:
        """Create a section divider."""
        return f"\n{self.H_LINE * self.width}\n{title}\n{self.H_LINE * self.width}"

    def sentiment_icon(self, sentiment: str) -> str:
        """Get icon for sentiment."""
        icons = {
            "bullish": self.BULLISH,
            "bearish": self.BEARISH,
            "neutral": self.NEUTRAL,
            "mixed": self.MIXED,
        }
        return icons.get(sentiment.lower(), self.NEUTRAL)

    def risk_icon(self, risk: str) -> str:
        """Get icon for risk level."""
        icons = {
            "critical": self.RISK_CRITICAL,
            "high": self.RISK_HIGH,
            "medium": self.RISK_MEDIUM,
            "low": self.RISK_LOW,
        }
        return icons.get(risk.lower(), self.RISK_LOW)

    def bar(
        self,
        value: float,
        max_value: float,
        width: int = 20,
        char: str = "█",
    ) -> str:
        """Create a horizontal bar."""
        if max_value <= 0:
            return ""
        fill = min(int(value / max_value * width), width)
        return char * fill

    def format_funding_table(
        self,
        rates: List[Dict],
    ) -> str:
        """Format funding rates as table."""
        lines = []
        lines.append(f"{'Exchange':<12} {'Current':>10} {'Annualized':>12} {'Next Payment':>14}")
        lines.append("-" * 50)

        for rate in sorted(rates, key=lambda r: r.get("rate", 0), reverse=True):
            lines.append(
                f"{rate['exchange']:<12} "
                f"{rate['rate']:>+9.4%} "
                f"{rate['annualized']:>+11.1f}% "
                f"{rate.get('next_payment', 'N/A'):>14}"
            )

        return "\n".join(lines)

    def format_oi_table(
        self,
        exchanges: List[Dict],
        total: float,
    ) -> str:
        """Format open interest as table."""
        lines = []
        lines.append(f"{'Exchange':<12} {'OI (USD)':>14} {'24h Chg':>10} {'7d Chg':>10} {'Share':>8}")
        lines.append("-" * 60)

        for ex in sorted(exchanges, key=lambda x: x.get("oi_usd", 0), reverse=True):
            share = ex.get("oi_usd", 0) / total * 100 if total > 0 else 0
            lines.append(
                f"{ex['exchange']:<12} "
                f"{format_currency(ex.get('oi_usd', 0)):>14} "
                f"{ex.get('change_24h', 0):>+9.1f}% "
                f"{ex.get('change_7d', 0):>+9.1f}% "
                f"{share:>7.1f}%"
            )

        return "\n".join(lines)

    def format_liquidation_heatmap(
        self,
        levels: List[Dict],
        side: str,
        max_value: float,
    ) -> str:
        """Format liquidation levels as visual heatmap."""
        lines = []

        for level in levels:
            bar_len = min(int(level.get("value_usd", 0) / 10_000_000), 20)
            bar = "█" * bar_len
            density = level.get("density", "low")
            marker = "⚠️ " if density in ["high", "critical"] else ""

            lines.append(
                f"  ${float(level.get('price', 0)):>10,.0f} {bar} "
                f"{format_currency(level.get('value_usd', 0))} "
                f"{marker}{density.upper()}"
            )

        return "\n".join(lines)

    def format_options_summary(
        self,
        analysis: Dict,
    ) -> str:
        """Format options analysis summary."""
        lines = []

        lines.append("Implied Volatility:")
        lines.append(f"   ATM IV: {analysis.get('atm_iv', 0):.1f}%")
        lines.append(f"   Interpretation: {analysis.get('iv_interpretation', 'unknown').upper()}")
        lines.append(f"   IV Rank: {analysis.get('iv_percentile', 50):.0f}th percentile")

        lines.append("\nPut/Call Analysis:")
        lines.append(f"   PCR (Volume): {analysis.get('pcr_volume', 0):.2f}")
        lines.append(f"   PCR (OI): {analysis.get('pcr_oi', 0):.2f}")
        lines.append(f"   Sentiment: {analysis.get('pcr_sentiment', 'neutral').upper()}")

        lines.append("\nMax Pain:")
        lines.append(f"   Price: ${analysis.get('max_pain', 0):,.0f}")
        lines.append(f"   Distance: {analysis.get('max_pain_distance', 0):+.1f}% from current")

        return "\n".join(lines)

    def format_basis_term_structure(
        self,
        structure: List[Dict],
    ) -> str:
        """Format term structure as visual chart."""
        lines = []

        for point in structure:
            annual = point.get("annualized_pct", 0)
            bar = "+" * min(int(abs(annual) / 2), 20)
            direction = "▲" if annual > 0 else "▼"
            lines.append(f"{point.get('expiry', 'N/A'):<12} {direction} {bar} {annual:+.1f}%")

        return "\n".join(lines)


class JSONFormatter:
    """
    Formats data for JSON export.

    Features:
    - Clean JSON structure
    - Decimal handling
    - Datetime serialization
    - Nested object support
    """

    def __init__(self, indent: int = 2):
        """Initialize formatter."""
        self.indent = indent

    def format(self, data: Any) -> str:
        """Format any data as JSON string."""
        return json.dumps(
            self._prepare(data),
            cls=DecimalEncoder,
            indent=self.indent,
        )

    def _prepare(self, obj: Any) -> Any:
        """Prepare object for JSON serialization."""
        if hasattr(obj, "__dataclass_fields__"):
            # Dataclass - convert to dict
            return {k: self._prepare(v) for k, v in asdict(obj).items()}
        elif isinstance(obj, dict):
            return {k: self._prepare(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._prepare(item) for item in obj]
        elif isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        else:
            return obj

    def funding_report(
        self,
        symbol: str,
        analysis: Dict,
    ) -> str:
        """Generate funding rate JSON report."""
        report = {
            "report_type": "funding_rates",
            "symbol": symbol,
            "generated_at": datetime.now().isoformat(),
            "data": self._prepare(analysis),
        }
        return self.format(report)

    def oi_report(
        self,
        symbol: str,
        analysis: Dict,
    ) -> str:
        """Generate open interest JSON report."""
        report = {
            "report_type": "open_interest",
            "symbol": symbol,
            "generated_at": datetime.now().isoformat(),
            "data": self._prepare(analysis),
        }
        return self.format(report)

    def derivatives_dashboard(
        self,
        symbol: str,
        funding: Dict,
        oi: Dict,
        liquidations: Dict,
        options: Optional[Dict] = None,
        basis: Optional[Dict] = None,
    ) -> str:
        """Generate complete derivatives dashboard JSON."""
        report = {
            "report_type": "derivatives_dashboard",
            "symbol": symbol,
            "generated_at": datetime.now().isoformat(),
            "funding": self._prepare(funding),
            "open_interest": self._prepare(oi),
            "liquidations": self._prepare(liquidations),
        }

        if options:
            report["options"] = self._prepare(options)
        if basis:
            report["basis"] = self._prepare(basis)

        return self.format(report)


class ReportGenerator:
    """
    Generates formatted reports combining multiple data sources.
    """

    def __init__(self):
        """Initialize report generator."""
        self.console = ConsoleFormatter()
        self.json_fmt = JSONFormatter()

    def derivatives_summary(
        self,
        symbol: str,
        funding: Dict,
        oi: Dict,
        liquidations: Dict,
        format: str = "console",
    ) -> str:
        """
        Generate derivatives market summary.

        Args:
            symbol: Trading symbol
            funding: Funding rate analysis
            oi: Open interest analysis
            liquidations: Liquidation summary
            format: Output format ("console" or "json")

        Returns:
            Formatted summary string
        """
        if format == "json":
            return self.json_fmt.derivatives_dashboard(symbol, funding, oi, liquidations)

        # Console format
        lines = []
        lines.append(self.console.header(f"{symbol} DERIVATIVES SUMMARY"))

        # Funding section
        lines.append("\n📊 FUNDING RATES")
        lines.append(f"   Weighted Average: {format_percent(funding.get('weighted_avg', 0) * 100, 4)}")
        lines.append(f"   Annualized: {format_percent(funding.get('annualized_avg', 0), 1)}")
        lines.append(f"   Sentiment: {funding.get('sentiment', 'unknown').upper()}")

        # OI section
        lines.append("\n📈 OPEN INTEREST")
        lines.append(f"   Total: {format_currency(oi.get('total_oi_usd', 0))}")
        lines.append(f"   24h Change: {format_percent(oi.get('avg_change_24h', 0), 1)}")
        lines.append(f"   Trend: {oi.get('trend', 'unknown').title()}")

        # Liquidations section
        lines.append("\n💥 LIQUIDATIONS")
        lines.append(f"   24h Total: {format_currency(liquidations.get('total_24h_usd', 0))}")
        lines.append(f"   Longs: {format_currency(liquidations.get('long_liquidations_usd', 0))}")
        lines.append(f"   Shorts: {format_currency(liquidations.get('short_liquidations_usd', 0))}")
        risk = liquidations.get("cascade_risk", "low")
        lines.append(f"   Cascade Risk: {self.console.risk_icon(risk)} {risk.upper()}")

        lines.append(f"\n{self.console.H_LINE * self.console.width}")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        return "\n".join(lines)


def demo():
    """Demonstrate formatters."""
    console = ConsoleFormatter()
    json_fmt = JSONFormatter()

    print(console.header("FORMATTER DEMO"))

    # Currency formatting
    print("\nCurrency Formatting:")
    print(f"  $1,234,567,890 → {format_currency(1234567890)}")
    print(f"  $12,345,678    → {format_currency(12345678)}")
    print(f"  $123,456       → {format_currency(123456)}")

    # Percent formatting
    print("\nPercent Formatting:")
    print(f"  5.5   → {format_percent(5.5)}")
    print(f"  -3.25 → {format_percent(-3.25)}")
    print(f"  0.02  → {format_percent(0.02, 4)}")

    # Bars
    print("\nBar Charts:")
    print(f"  100/100: {console.bar(100, 100)}")
    print(f"   50/100: {console.bar(50, 100)}")
    print(f"   25/100: {console.bar(25, 100)}")

    # Sentiment icons
    print("\nSentiment Icons:")
    for sent in ["bullish", "bearish", "neutral", "mixed"]:
        print(f"  {sent}: {console.sentiment_icon(sent)}")

    # JSON export
    print("\n" + console.section("JSON EXPORT"))
    sample_data = {
        "symbol": "BTC",
        "price": Decimal("67500.50"),
        "timestamp": datetime.now(),
        "metrics": {
            "funding": 0.01,
            "oi": Decimal("15000000000"),
        },
    }
    print(json_fmt.format(sample_data))


if __name__ == "__main__":
    demo()
