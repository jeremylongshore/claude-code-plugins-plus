#!/usr/bin/env python3
"""
Output formatters for DEX router results.

Supports table, JSON, and CSV output formats with rich terminal styling.
"""

import csv
import io
import json
from datetime import datetime
from decimal import Decimal
from typing import List

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from quote_fetcher import NormalizedQuote
from route_optimizer import RouteComparison
from split_calculator import SplitRecommendation
from mev_assessor import MEVAssessment, MEVRiskLevel


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder that handles Decimal types."""

    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        if hasattr(obj, "__dict__"):
            return obj.__dict__
        return super().default(obj)


class OutputFormatter:
    """
    Formats DEX router output in various formats.

    Supports:
    - Rich terminal tables (with fallback to plain text)
    - JSON output
    - CSV output
    """

    def __init__(self, use_color: bool = True):
        """
        Initialize formatter.

        Args:
            use_color: Enable colored output (if rich is available)
        """
        self.use_color = use_color and RICH_AVAILABLE
        if self.use_color:
            self.console = Console()

    def format_quote(self, quote: NormalizedQuote, output_format: str = "table") -> str:
        """Format a single quote."""
        if output_format == "json":
            return self._quote_to_json(quote)
        elif output_format == "csv":
            return self._quote_to_csv([quote])
        else:
            return self._quote_to_table(quote)

    def format_comparison(self, comparison: RouteComparison, output_format: str = "table") -> str:
        """Format route comparison results."""
        if output_format == "json":
            return self._comparison_to_json(comparison)
        elif output_format == "csv":
            return self._comparison_to_csv(comparison)
        else:
            return self._comparison_to_table(comparison)

    def format_split(self, split: SplitRecommendation, output_format: str = "table") -> str:
        """Format split order recommendation."""
        if output_format == "json":
            return self._split_to_json(split)
        elif output_format == "csv":
            return self._split_to_csv(split)
        else:
            return self._split_to_table(split)

    def format_mev(self, assessment: MEVAssessment, output_format: str = "table") -> str:
        """Format MEV risk assessment."""
        if output_format == "json":
            return self._mev_to_json(assessment)
        else:
            return self._mev_to_table(assessment)

    # --- Table Formatters ---

    def _quote_to_table(self, quote: NormalizedQuote) -> str:
        """Format quote as rich table."""
        if self.use_color:
            table = Table(title=f"Quote from {quote.source}", show_header=False)
            table.add_column("Field", style="cyan")
            table.add_column("Value", style="green")

            table.add_row("Input", f"{quote.input_amount} {quote.input_token}")
            table.add_row("Output", f"{quote.output_amount:.2f} {quote.output_token}")
            table.add_row("Rate", f"{quote.price:.4f} {quote.output_token}/{quote.input_token}")
            table.add_row("Price Impact", f"{quote.price_impact:.2f}%")
            table.add_row("Gas Cost", f"${quote.gas_cost_usd:.2f}")
            table.add_row("Effective Rate", f"{quote.effective_rate:.4f}")
            table.add_row("Protocols", ", ".join(quote.protocols))

            output = io.StringIO()
            console = Console(file=output, force_terminal=True)
            console.print(table)
            return output.getvalue()
        else:
            return self._quote_to_plain(quote)

    def _quote_to_plain(self, quote: NormalizedQuote) -> str:
        """Format quote as plain text."""
        lines = [
            f"Quote from {quote.source}",
            "=" * 40,
            f"Input:          {quote.input_amount} {quote.input_token}",
            f"Output:         {quote.output_amount:.2f} {quote.output_token}",
            f"Rate:           {quote.price:.4f} {quote.output_token}/{quote.input_token}",
            f"Price Impact:   {quote.price_impact:.2f}%",
            f"Gas Cost:       ${quote.gas_cost_usd:.2f}",
            f"Effective Rate: {quote.effective_rate:.4f}",
            f"Protocols:      {', '.join(quote.protocols)}",
        ]
        return "\n".join(lines)

    def _comparison_to_table(self, comparison: RouteComparison) -> str:
        """Format route comparison as rich table."""
        if self.use_color:
            table = Table(title="DEX Route Comparison")
            table.add_column("Rank", style="bold")
            table.add_column("Source", style="cyan")
            table.add_column("Output", justify="right")
            table.add_column("Rate", justify="right")
            table.add_column("Gas", justify="right")
            table.add_column("Score", justify="right")
            table.add_column("Savings", justify="right", style="green")

            for analysis in comparison.all_routes:
                rank_style = "bold green" if analysis.rank == 1 else ""
                table.add_row(
                    f"#{analysis.rank}",
                    analysis.quote.source,
                    f"{analysis.quote.output_amount:.2f}",
                    f"{analysis.quote.effective_rate:.2f}",
                    f"${analysis.quote.gas_cost_usd:.2f}",
                    f"{analysis.score:.0f}",
                    f"+{analysis.savings_pct:.2f}%",
                    style=rank_style,
                )

            output = io.StringIO()
            console = Console(file=output, force_terminal=True)
            console.print(table)
            console.print(f"\n[bold]Spread:[/bold] {comparison.price_spread:.2f}%")
            console.print(f"[bold]Recommendation:[/bold] {comparison.recommendation}")
            return output.getvalue()
        else:
            return self._comparison_to_plain(comparison)

    def _comparison_to_plain(self, comparison: RouteComparison) -> str:
        """Format comparison as plain text."""
        lines = [
            "DEX Route Comparison",
            "=" * 70,
            f"{'Rank':<6} {'Source':<12} {'Output':>14} {'Rate':>12} {'Gas':>8} {'Score':>6}",
            "-" * 70,
        ]

        for analysis in comparison.all_routes:
            lines.append(
                f"#{analysis.rank:<5} {analysis.quote.source:<12} "
                f"{analysis.quote.output_amount:>14.2f} "
                f"{float(analysis.quote.effective_rate):>12.2f} "
                f"${analysis.quote.gas_cost_usd:>6.2f} "
                f"{analysis.score:>6.0f}"
            )

        lines.extend(
            [
                "-" * 70,
                f"Spread: {comparison.price_spread:.2f}%",
                f"Recommendation: {comparison.recommendation}",
            ]
        )

        return "\n".join(lines)

    def _split_to_table(self, split: SplitRecommendation) -> str:
        """Format split recommendation as table."""
        if self.use_color:
            table = Table(title="Split Order Recommendation")
            table.add_column("Venue", style="cyan")
            table.add_column("Allocation", justify="right")
            table.add_column("Amount", justify="right")
            table.add_column("Expected", justify="right")
            table.add_column("Gas", justify="right")

            for alloc in split.allocations:
                table.add_row(
                    alloc.source,
                    f"{alloc.percentage:.1f}%",
                    f"{alloc.input_amount}",
                    f"{alloc.expected_output:.2f}",
                    f"${alloc.gas_cost_usd:.2f}",
                )

            output = io.StringIO()
            console = Console(file=output, force_terminal=True)
            console.print(table)

            # Summary
            console.print(f"\n[bold]Total Output:[/bold] {split.total_output:.2f}")
            console.print(f"[bold]Single Venue:[/bold] {split.single_venue_output:.2f}")

            if split.is_split_beneficial:
                console.print(
                    f"[bold green]Improvement:[/bold green] +{split.improvement_pct:.2f}% "
                    f"(${float(split.net_benefit):.2f} saved)"
                )
            else:
                console.print("[yellow]Split not beneficial for this trade size[/yellow]")

            console.print(f"\n{split.recommendation}")
            return output.getvalue()
        else:
            return self._split_to_plain(split)

    def _split_to_plain(self, split: SplitRecommendation) -> str:
        """Format split as plain text."""
        lines = [
            "Split Order Recommendation",
            "=" * 60,
            f"{'Venue':<15} {'Alloc':>8} {'Amount':>12} {'Expected':>14} {'Gas':>8}",
            "-" * 60,
        ]

        for alloc in split.allocations:
            lines.append(
                f"{alloc.source:<15} {alloc.percentage:>7.1f}% "
                f"{float(alloc.input_amount):>12.4f} "
                f"{float(alloc.expected_output):>14.2f} "
                f"${alloc.gas_cost_usd:>6.2f}"
            )

        lines.extend(
            [
                "-" * 60,
                f"Total Output:  {split.total_output:.2f}",
                f"Single Venue:  {split.single_venue_output:.2f}",
                f"Improvement:   +{split.improvement_pct:.2f}%",
                f"Net Benefit:   ${float(split.net_benefit):.2f}",
                "",
                split.recommendation,
            ]
        )

        return "\n".join(lines)

    def _mev_to_table(self, assessment: MEVAssessment) -> str:
        """Format MEV assessment as table."""
        risk_colors = {
            MEVRiskLevel.LOW: "green",
            MEVRiskLevel.MEDIUM: "yellow",
            MEVRiskLevel.HIGH: "red",
            MEVRiskLevel.CRITICAL: "bold red",
        }

        if self.use_color:
            output = io.StringIO()
            console = Console(file=output, force_terminal=True)

            # Risk level panel
            color = risk_colors.get(assessment.risk_level, "white")
            console.print(
                Panel(
                    f"[{color}]{assessment.risk_level.value}[/{color}] (Score: {assessment.risk_score:.0f}/100)",
                    title="MEV Risk Level",
                )
            )

            console.print(f"Estimated Exposure: [bold]${assessment.estimated_mev_exposure_usd:.2f}[/bold]\n")

            # Risk factors table
            table = Table(title="Risk Factors")
            table.add_column("Factor", style="cyan")
            table.add_column("Score", justify="right")
            table.add_column("Weight", justify="right")
            table.add_column("Description")

            for factor in assessment.risk_factors:
                table.add_row(
                    factor.name,
                    f"{factor.score:.0f}",
                    f"{factor.weight:.0%}",
                    factor.description,
                )

            console.print(table)

            # Protection options
            console.print("\n[bold]Protection Options:[/bold]")
            for option in assessment.protection_options:
                console.print(f"  • {option.name} ({option.effectiveness:.0f}% effective)")
                console.print(f"    {option.description}")

            console.print(f"\n[bold]Recommendation:[/bold] {assessment.recommendation}")

            return output.getvalue()
        else:
            return self._mev_to_plain(assessment)

    def _mev_to_plain(self, assessment: MEVAssessment) -> str:
        """Format MEV assessment as plain text."""
        lines = [
            "MEV Risk Assessment",
            "=" * 60,
            f"Risk Level: {assessment.risk_level.value}",
            f"Risk Score: {assessment.risk_score:.0f}/100",
            f"Estimated Exposure: ${assessment.estimated_mev_exposure_usd:.2f}",
            "",
            "Risk Factors:",
            "-" * 40,
        ]

        for factor in assessment.risk_factors:
            lines.append(f"  {factor.name}: {factor.score:.0f}/100 ({factor.weight:.0%})")

        lines.extend(["", "Protection Options:"])
        for option in assessment.protection_options:
            lines.append(f"  • {option.name} ({option.effectiveness:.0f}%)")

        lines.extend(["", f"Recommendation: {assessment.recommendation}"])

        return "\n".join(lines)

    # --- JSON Formatters ---

    def _quote_to_json(self, quote: NormalizedQuote) -> str:
        """Convert quote to JSON string."""
        data = {
            "source": quote.source,
            "input_token": quote.input_token,
            "output_token": quote.output_token,
            "input_amount": float(quote.input_amount),
            "output_amount": float(quote.output_amount),
            "price": float(quote.price),
            "price_impact": quote.price_impact,
            "gas_estimate": quote.gas_estimate,
            "gas_cost_usd": quote.gas_cost_usd,
            "effective_rate": float(quote.effective_rate),
            "protocols": quote.protocols,
            "timestamp": quote.timestamp.isoformat(),
        }
        return json.dumps(data, indent=2)

    def _comparison_to_json(self, comparison: RouteComparison) -> str:
        """Convert comparison to JSON string."""
        data = {
            "best_route": {
                "source": comparison.best_route.quote.source,
                "output": float(comparison.best_route.quote.output_amount),
                "score": comparison.best_route.score,
            },
            "all_routes": [
                {
                    "rank": a.rank,
                    "source": a.quote.source,
                    "output": float(a.quote.output_amount),
                    "effective_rate": float(a.quote.effective_rate),
                    "gas_cost_usd": a.quote.gas_cost_usd,
                    "score": a.score,
                    "savings_pct": a.savings_pct,
                }
                for a in comparison.all_routes
            ],
            "price_spread": comparison.price_spread,
            "recommendation": comparison.recommendation,
        }
        return json.dumps(data, indent=2)

    def _split_to_json(self, split: SplitRecommendation) -> str:
        """Convert split recommendation to JSON string."""
        data = {
            "allocations": [
                {
                    "source": a.source,
                    "percentage": a.percentage,
                    "input_amount": float(a.input_amount),
                    "expected_output": float(a.expected_output),
                    "gas_cost_usd": a.gas_cost_usd,
                }
                for a in split.allocations
            ],
            "total_input": float(split.total_input),
            "total_output": float(split.total_output),
            "single_venue_output": float(split.single_venue_output),
            "improvement_pct": split.improvement_pct,
            "net_benefit": float(split.net_benefit),
            "is_split_beneficial": split.is_split_beneficial,
            "recommendation": split.recommendation,
        }
        return json.dumps(data, indent=2)

    def _mev_to_json(self, assessment: MEVAssessment) -> str:
        """Convert MEV assessment to JSON string."""
        data = {
            "risk_level": assessment.risk_level.value,
            "risk_score": assessment.risk_score,
            "estimated_mev_exposure_usd": assessment.estimated_mev_exposure_usd,
            "risk_factors": [
                {
                    "name": f.name,
                    "score": f.score,
                    "weight": f.weight,
                    "description": f.description,
                }
                for f in assessment.risk_factors
            ],
            "protection_options": [
                {
                    "name": o.name,
                    "effectiveness": o.effectiveness,
                    "trade_off": o.trade_off,
                }
                for o in assessment.protection_options
            ],
            "recommendation": assessment.recommendation,
        }
        return json.dumps(data, indent=2)

    # --- CSV Formatters ---

    def _quote_to_csv(self, quotes: List[NormalizedQuote]) -> str:
        """Convert quotes to CSV string."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "source",
                "input_token",
                "output_token",
                "input_amount",
                "output_amount",
                "price",
                "price_impact",
                "gas_cost_usd",
                "effective_rate",
                "protocols",
            ]
        )

        for q in quotes:
            writer.writerow(
                [
                    q.source,
                    q.input_token,
                    q.output_token,
                    float(q.input_amount),
                    float(q.output_amount),
                    float(q.price),
                    q.price_impact,
                    q.gas_cost_usd,
                    float(q.effective_rate),
                    ";".join(q.protocols),
                ]
            )

        return output.getvalue()

    def _comparison_to_csv(self, comparison: RouteComparison) -> str:
        """Convert comparison to CSV string."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "rank",
                "source",
                "output_amount",
                "effective_rate",
                "gas_cost_usd",
                "score",
                "savings_pct",
            ]
        )

        for a in comparison.all_routes:
            writer.writerow(
                [
                    a.rank,
                    a.quote.source,
                    float(a.quote.output_amount),
                    float(a.quote.effective_rate),
                    a.quote.gas_cost_usd,
                    a.score,
                    a.savings_pct,
                ]
            )

        return output.getvalue()

    def _split_to_csv(self, split: SplitRecommendation) -> str:
        """Convert split recommendation to CSV string."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "source",
                "percentage",
                "input_amount",
                "expected_output",
                "gas_cost_usd",
            ]
        )

        for a in split.allocations:
            writer.writerow(
                [
                    a.source,
                    a.percentage,
                    float(a.input_amount),
                    float(a.expected_output),
                    a.gas_cost_usd,
                ]
            )

        return output.getvalue()
