#!/usr/bin/env python3
"""
Gas Pattern Analyzer

Analyze historical gas patterns and predict optimal timing.

Author: Jeremy Longshore <jeremy@intentsolutions.io>
Version: 1.0.0
License: MIT
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import statistics


@dataclass
class HourlyPattern:
    """Hourly gas pattern."""

    hour: int  # 0-23 UTC
    avg_gas_gwei: float
    min_gas_gwei: float
    max_gas_gwei: float
    sample_count: int
    is_low: bool  # Below average


@dataclass
class DailyPattern:
    """Daily gas pattern."""

    day: int  # 0=Monday, 6=Sunday
    day_name: str
    avg_gas_gwei: float
    min_gas_gwei: float
    max_gas_gwei: float
    sample_count: int
    is_low: bool


@dataclass
class TimeWindow:
    """Optimal time window for transactions."""

    start_hour: int
    end_hour: int
    day_of_week: Optional[int]
    expected_gas_gwei: float
    savings_percent: float
    description: str


@dataclass
class GasPrediction:
    """Gas price prediction."""

    target_time: datetime
    predicted_gwei: float
    confidence: float
    reasoning: str


# Default patterns based on historical Ethereum data
# These serve as fallback when no local history is available
DEFAULT_HOURLY_PATTERNS = {
    0: 28,
    1: 25,
    2: 22,
    3: 20,
    4: 19,
    5: 18,  # Night (lowest)
    6: 20,
    7: 25,
    8: 32,
    9: 38,
    10: 42,
    11: 45,  # Morning (rising)
    12: 48,
    13: 50,
    14: 52,
    15: 55,
    16: 58,
    17: 55,  # Afternoon (peak)
    18: 50,
    19: 45,
    20: 40,
    21: 35,
    22: 32,
    23: 30,  # Evening (declining)
}

DEFAULT_DAILY_PATTERNS = {
    0: 45,  # Monday
    1: 48,  # Tuesday
    2: 50,  # Wednesday
    3: 52,  # Thursday (peak)
    4: 48,  # Friday
    5: 35,  # Saturday (low)
    6: 32,  # Sunday (lowest)
}


class PatternAnalyzer:
    """Analyze gas price patterns."""

    def __init__(self, history_file: str = None, verbose: bool = False):
        """Initialize pattern analyzer.

        Args:
            history_file: Path to local history file
            verbose: Enable verbose output
        """
        self.history_file = history_file or Path.home() / ".gas_history.json"
        self.verbose = verbose
        self._history = self._load_history()

    def _load_history(self) -> List[Dict[str, Any]]:
        """Load historical data from file."""
        try:
            if Path(self.history_file).exists():
                with open(self.history_file) as f:
                    return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass  # History file corrupted or missing - start with empty history
        return []

    def _save_history(self, entry: Dict[str, Any]) -> None:
        """Save new entry to history."""
        self._history.append(entry)
        # Keep last 7 days of data
        cutoff = (datetime.now() - timedelta(days=7)).timestamp()
        self._history = [e for e in self._history if e.get("timestamp", 0) > cutoff]

        try:
            with open(self.history_file, "w") as f:
                json.dump(self._history, f)
        except IOError:
            pass  # Non-critical - history save failed, will try again on next record

    def record_gas_data(self, gas_gwei: float) -> None:
        """Record current gas data for pattern analysis.

        Args:
            gas_gwei: Current gas price in gwei
        """
        now = datetime.now()
        self._save_history(
            {
                "timestamp": now.timestamp(),
                "hour": now.hour,
                "day": now.weekday(),
                "gas_gwei": gas_gwei,
            }
        )

    def analyze_hourly_pattern(self) -> List[HourlyPattern]:
        """Analyze hourly gas patterns.

        Returns:
            List of HourlyPattern for each hour
        """
        # Group data by hour
        hourly_data: Dict[int, List[float]] = {h: [] for h in range(24)}

        for entry in self._history:
            hour = entry.get("hour", 0)
            gas = entry.get("gas_gwei", 0)
            if 0 <= hour < 24 and gas > 0:
                hourly_data[hour].append(gas)

        # Calculate patterns
        patterns = []
        all_averages = []

        for hour in range(24):
            data = hourly_data[hour]
            if data:
                avg = statistics.mean(data)
                all_averages.append(avg)
                patterns.append(
                    HourlyPattern(
                        hour=hour,
                        avg_gas_gwei=avg,
                        min_gas_gwei=min(data),
                        max_gas_gwei=max(data),
                        sample_count=len(data),
                        is_low=False,  # Set later
                    )
                )
            else:
                # Use default pattern
                default_gas = DEFAULT_HOURLY_PATTERNS[hour]
                patterns.append(
                    HourlyPattern(
                        hour=hour,
                        avg_gas_gwei=default_gas,
                        min_gas_gwei=default_gas * 0.7,
                        max_gas_gwei=default_gas * 1.5,
                        sample_count=0,
                        is_low=False,
                    )
                )
                all_averages.append(default_gas)

        # Mark low-gas hours (below overall average)
        overall_avg = statistics.mean(all_averages)
        for pattern in patterns:
            pattern.is_low = pattern.avg_gas_gwei < overall_avg * 0.9

        return patterns

    def analyze_daily_pattern(self) -> List[DailyPattern]:
        """Analyze daily gas patterns.

        Returns:
            List of DailyPattern for each day
        """
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        # Group data by day
        daily_data: Dict[int, List[float]] = {d: [] for d in range(7)}

        for entry in self._history:
            day = entry.get("day", 0)
            gas = entry.get("gas_gwei", 0)
            if 0 <= day < 7 and gas > 0:
                daily_data[day].append(gas)

        # Calculate patterns
        patterns = []
        all_averages = []

        for day in range(7):
            data = daily_data[day]
            if data:
                avg = statistics.mean(data)
                all_averages.append(avg)
                patterns.append(
                    DailyPattern(
                        day=day,
                        day_name=day_names[day],
                        avg_gas_gwei=avg,
                        min_gas_gwei=min(data),
                        max_gas_gwei=max(data),
                        sample_count=len(data),
                        is_low=False,
                    )
                )
            else:
                default_gas = DEFAULT_DAILY_PATTERNS[day]
                patterns.append(
                    DailyPattern(
                        day=day,
                        day_name=day_names[day],
                        avg_gas_gwei=default_gas,
                        min_gas_gwei=default_gas * 0.7,
                        max_gas_gwei=default_gas * 1.5,
                        sample_count=0,
                        is_low=False,
                    )
                )
                all_averages.append(default_gas)

        # Mark low-gas days
        overall_avg = statistics.mean(all_averages)
        for pattern in patterns:
            pattern.is_low = pattern.avg_gas_gwei < overall_avg * 0.9

        return patterns

    def find_optimal_window(self, current_gas_gwei: float = None) -> TimeWindow:
        """Find optimal time window for transactions.

        Args:
            current_gas_gwei: Current gas for comparison

        Returns:
            TimeWindow with optimal timing recommendation
        """
        hourly = self.analyze_hourly_pattern()
        daily = self.analyze_daily_pattern()

        # Find lowest gas hours
        sorted_hours = sorted(hourly, key=lambda x: x.avg_gas_gwei)
        best_hours = sorted_hours[:4]  # Top 4 lowest hours

        # Find lowest gas days
        sorted_days = sorted(daily, key=lambda x: x.avg_gas_gwei)
        best_day = sorted_days[0]

        # Calculate expected gas in optimal window
        expected_gas = min(h.avg_gas_gwei for h in best_hours)

        # Calculate savings
        avg_gas = statistics.mean(h.avg_gas_gwei for h in hourly)
        savings = ((avg_gas - expected_gas) / avg_gas) * 100 if avg_gas > 0 else 0

        # Build description
        hours_str = ", ".join(f"{h.hour}:00" for h in best_hours[:3])

        return TimeWindow(
            start_hour=best_hours[0].hour,
            end_hour=best_hours[-1].hour,
            day_of_week=best_day.day,
            expected_gas_gwei=expected_gas,
            savings_percent=savings,
            description=f"Best times: {hours_str} UTC on {best_day.day_name}",
        )

    def predict_gas(self, target_time: datetime) -> GasPrediction:
        """Predict gas price for a specific time.

        Args:
            target_time: When you want to transact

        Returns:
            GasPrediction with expected gas
        """
        hourly = self.analyze_hourly_pattern()
        daily = self.analyze_daily_pattern()

        hour = target_time.hour
        day = target_time.weekday()

        # Get patterns for target time
        hour_pattern = hourly[hour]
        day_pattern = daily[day]

        # Weighted prediction
        predicted = hour_pattern.avg_gas_gwei * 0.7 + day_pattern.avg_gas_gwei * 0.3

        # Calculate confidence based on sample count
        samples = hour_pattern.sample_count + day_pattern.sample_count
        confidence = min(samples / 100, 1.0)

        # Determine reasoning
        if hour_pattern.is_low and day_pattern.is_low:
            reasoning = "Both hour and day are historically low-gas periods"
        elif hour_pattern.is_low:
            reasoning = "This hour is typically low-gas"
        elif day_pattern.is_low:
            reasoning = "This day is typically low-gas"
        else:
            reasoning = "Average gas expected for this time"

        return GasPrediction(
            target_time=target_time,
            predicted_gwei=predicted,
            confidence=confidence,
            reasoning=reasoning,
        )


def main():
    """CLI entry point for testing."""
    analyzer = PatternAnalyzer(verbose=True)

    print("=== Hourly Patterns ===")
    hourly = analyzer.analyze_hourly_pattern()
    for h in hourly:
        low_marker = "LOW" if h.is_low else ""
        print(f"  {h.hour:02d}:00 UTC: {h.avg_gas_gwei:.1f} gwei (n={h.sample_count}) {low_marker}")

    print("\n=== Daily Patterns ===")
    daily = analyzer.analyze_daily_pattern()
    for d in daily:
        low_marker = "LOW" if d.is_low else ""
        print(f"  {d.day_name:<10}: {d.avg_gas_gwei:.1f} gwei (n={d.sample_count}) {low_marker}")

    print("\n=== Optimal Window ===")
    window = analyzer.find_optimal_window()
    print(f"  {window.description}")
    print(f"  Expected: {window.expected_gas_gwei:.1f} gwei")
    print(f"  Savings: {window.savings_percent:.1f}%")

    print("\n=== Prediction for Now ===")
    prediction = analyzer.predict_gas(datetime.now())
    print(f"  Predicted: {prediction.predicted_gwei:.1f} gwei")
    print(f"  Confidence: {prediction.confidence:.0%}")
    print(f"  Reasoning: {prediction.reasoning}")


if __name__ == "__main__":
    main()
