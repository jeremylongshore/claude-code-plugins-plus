#!/usr/bin/env python3
"""
Gas Optimizer Formatters

Format gas data for various outputs.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 1.0.0
License: MIT
"""

import json
from typing import Any, List


def format_gwei(value: float) -> str:
    """Format gwei value."""
    return f"{value:.1f} gwei"


def format_usd(value: float) -> str:
    """Format USD value."""
    if value >= 100:
        return f"${value:.0f}"
    elif value >= 1:
        return f"${value:.2f}"
    else:
        return f"${value:.4f}"


def format_native(value: float, symbol: str = "ETH") -> str:
    """Format native token amount."""
    if value >= 1:
        return f"{value:.4f} {symbol}"
    else:
        return f"{value:.6f} {symbol}"


def format_current_gas(gas_data: Any, native_symbol: str = "ETH") -> str:
    """Format current gas prices.

    Args:
        gas_data: GasData object
        native_symbol: Native token symbol

    Returns:
        Formatted gas price display
    """
    lines = [
        "",
        f"CURRENT GAS PRICES ({gas_data.chain.upper()})",
        "=" * 60,
        f"Base Fee:     {gas_data.base_fee / 10**9:.2f} gwei",
        f"Priority Fee: {gas_data.priority_fee / 10**9:.2f} gwei",
        f"Source:       {gas_data.source}",
        "",
        "PRICE TIERS",
        "-" * 60,
        f"{'Tier':<12} {'Gas Price':<15} {'Confirmation':<20}",
        "-" * 60,
        f"{'Slow':<12} {format_gwei(gas_data.slow / 10**9):<15} {'10+ blocks (~2+ min)':<20}",
        f"{'Standard':<12} {format_gwei(gas_data.standard / 10**9):<15} {'3-5 blocks (~1 min)':<20}",
        f"{'Fast':<12} {format_gwei(gas_data.fast / 10**9):<15} {'1-2 blocks (~30 sec)':<20}",
        f"{'Instant':<12} {format_gwei(gas_data.instant / 10**9):<15} {'Next block (~12 sec)':<20}",
        "=" * 60,
    ]

    return "\n".join(lines)


def format_cost_estimate(estimate: Any, native_symbol: str = "ETH") -> str:
    """Format single cost estimate.

    Args:
        estimate: CostEstimate object
        native_symbol: Native token symbol

    Returns:
        Formatted estimate
    """
    lines = [
        "",
        f"COST ESTIMATE: {estimate.operation.upper()}",
        "=" * 50,
        f"Gas Limit:  {estimate.gas_limit:,}",
        f"Gas Price:  {format_gwei(estimate.gas_price_gwei)}",
        f"Tier:       {estimate.tier}",
        "",
        f"Cost:       {format_native(estimate.gas_cost_native, native_symbol)}",
        f"            {format_usd(estimate.gas_cost_usd)}",
        "=" * 50,
    ]

    return "\n".join(lines)


def format_multi_tier_estimate(multi: Any, native_symbol: str = "ETH") -> str:
    """Format multi-tier cost estimate.

    Args:
        multi: MultiTierEstimate object
        native_symbol: Native token symbol

    Returns:
        Formatted estimate table
    """
    lines = [
        "",
        f"COST ESTIMATE: {multi.operation.upper()}",
        f"Gas Limit: {multi.gas_limit:,}",
        "=" * 70,
        f"{'Tier':<12} {'Gas Price':<15} {'Cost ' + native_symbol:<18} {'Cost USD':<12} {'Time':<15}",
        "-" * 70,
    ]

    tiers = [
        (multi.slow, "10+ blocks"),
        (multi.standard, "3-5 blocks"),
        (multi.fast, "1-2 blocks"),
        (multi.instant, "Next block"),
    ]

    for est, time_str in tiers:
        gas_str = format_gwei(est.gas_price_gwei)
        native_str = f"{est.gas_cost_native:.6f}"
        usd_str = format_usd(est.gas_cost_usd)
        lines.append(f"{est.tier.capitalize():<12} {gas_str:<15} {native_str:<18} {usd_str:<12} {time_str:<15}")

    lines.append("-" * 70)

    # Add savings info
    savings_usd = multi.instant.gas_cost_usd - multi.slow.gas_cost_usd
    savings_pct = (savings_usd / multi.instant.gas_cost_usd * 100) if multi.instant.gas_cost_usd > 0 else 0
    lines.append(f"Potential savings (Instant → Slow): {format_usd(savings_usd)} ({savings_pct:.0f}%)")

    return "\n".join(lines)


def format_hourly_patterns(patterns: List[Any]) -> str:
    """Format hourly patterns.

    Args:
        patterns: List of HourlyPattern objects

    Returns:
        Formatted hourly pattern display
    """
    lines = [
        "",
        "HOURLY GAS PATTERNS (UTC)",
        "=" * 60,
        f"{'Hour':<8} {'Avg Gas':<12} {'Range':<20} {'Status':<10}",
        "-" * 60,
    ]

    for p in patterns:
        range_str = f"{p.min_gas_gwei:.0f} - {p.max_gas_gwei:.0f}"
        status = "LOW" if p.is_low else ""
        lines.append(f"{p.hour:02d}:00    {p.avg_gas_gwei:<12.1f} {range_str:<20} {status:<10}")

    lines.append("=" * 60)
    lines.append("LOW = Below average gas price")

    return "\n".join(lines)


def format_daily_patterns(patterns: List[Any]) -> str:
    """Format daily patterns.

    Args:
        patterns: List of DailyPattern objects

    Returns:
        Formatted daily pattern display
    """
    lines = [
        "",
        "DAILY GAS PATTERNS",
        "=" * 60,
        f"{'Day':<12} {'Avg Gas':<12} {'Range':<20} {'Status':<10}",
        "-" * 60,
    ]

    for p in patterns:
        range_str = f"{p.min_gas_gwei:.0f} - {p.max_gas_gwei:.0f}"
        status = "LOW" if p.is_low else ""
        lines.append(f"{p.day_name:<12} {p.avg_gas_gwei:<12.1f} {range_str:<20} {status:<10}")

    lines.append("=" * 60)

    return "\n".join(lines)


def format_optimal_window(window: Any) -> str:
    """Format optimal window recommendation.

    Args:
        window: TimeWindow object

    Returns:
        Formatted recommendation
    """
    lines = [
        "",
        "OPTIMAL TRANSACTION WINDOW",
        "=" * 60,
        f"Recommendation: {window.description}",
        "",
        f"Expected Gas:   {format_gwei(window.expected_gas_gwei)}",
        f"Potential Savings: {window.savings_percent:.1f}% vs average",
        "",
        "Timing:",
        f"  Best Hours: {window.start_hour:02d}:00 - {window.end_hour:02d}:00 UTC",
        "=" * 60,
    ]

    return "\n".join(lines)


def format_prediction(prediction: Any) -> str:
    """Format gas prediction.

    Args:
        prediction: GasPrediction object

    Returns:
        Formatted prediction
    """
    lines = [
        "",
        "GAS PREDICTION",
        "=" * 50,
        f"Target Time: {prediction.target_time.strftime('%Y-%m-%d %H:%M')} UTC",
        f"Predicted:   {format_gwei(prediction.predicted_gwei)}",
        f"Confidence:  {prediction.confidence:.0%}",
        f"Reasoning:   {prediction.reasoning}",
        "=" * 50,
    ]

    return "\n".join(lines)


def format_json(data: Any) -> str:
    """Format data as JSON."""
    if hasattr(data, "__dict__"):
        return json.dumps(vars(data), indent=2, default=str)
    elif isinstance(data, list):
        return json.dumps([vars(x) if hasattr(x, "__dict__") else x for x in data], indent=2, default=str)
    else:
        return json.dumps(data, indent=2, default=str)


def main():
    """CLI entry point for testing."""
    print("=== Format Tests ===")
    print(f"Gwei: {format_gwei(35.5)}")
    print(f"USD (high): {format_usd(125.50)}")
    print(f"USD (low): {format_usd(0.0045)}")
    print(f"Native: {format_native(0.00456789, 'ETH')}")


if __name__ == "__main__":
    main()
