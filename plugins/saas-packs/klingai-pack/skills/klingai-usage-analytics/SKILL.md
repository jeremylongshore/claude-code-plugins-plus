---
name: klingai-usage-analytics
description: |
  Build usage analytics and reporting for Kling AI. Use when tracking generation patterns,
  analyzing costs, or creating dashboards. Trigger with phrases like 'klingai analytics',
  'kling ai usage report', 'klingai metrics', 'video generation stats'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Kling AI Usage Analytics

## Overview

This skill shows how to build comprehensive usage analytics including generation metrics, cost analysis, trend reporting, and visualization dashboards for Kling AI.

## Prerequisites

- Kling AI API key configured
- Usage data collection in place
- Python 3.8+ with pandas/matplotlib (optional)

## Instructions

Follow these steps for analytics:

1. **Collect Data**: Capture usage events
2. **Aggregate Metrics**: Calculate key metrics
3. **Generate Reports**: Create usage reports
4. **Visualize Data**: Build dashboards
5. **Set Up Alerts**: Anomaly detection

## Analytics Engine

```python
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from collections import defaultdict
import json

@dataclass
class GenerationEvent:
    timestamp: datetime
    job_id: str
    user_id: str
    project_id: str
    prompt: str
    model: str
    duration: int
    status: str  # completed, failed
    credits_used: int
    generation_time_seconds: float
    video_url: Optional[str] = None
    error: Optional[str] = None

class UsageAnalytics:
    """Analytics engine for Kling AI usage."""

    def __init__(self):
        self.events: List[GenerationEvent] = []

    def record_event(self, event: GenerationEvent):
        """Record a generation event."""
        self.events.append(event)

    def get_summary(
        self,
        start: datetime = None,
        end: datetime = None,
        user_id: str = None,
        project_id: str = None
    ) -> Dict:
        """Get usage summary for period."""
        filtered = self._filter_events(start, end, user_id, project_id)

        if not filtered:
            return {"total_generations": 0}

        completed = [e for e in filtered if e.status == "completed"]
        failed = [e for e in filtered if e.status == "failed"]

        total_credits = sum(e.credits_used for e in filtered)
        total_time = sum(e.generation_time_seconds for e in completed)

        return {
            "period": {
                "start": (start or filtered[0].timestamp).isoformat(),
                "end": (end or filtered[-1].timestamp).isoformat()
            },
            "total_generations": len(filtered),
            "completed": len(completed),
            "failed": len(failed),
            "success_rate": len(completed) / len(filtered) * 100 if filtered else 0,
            "total_credits": total_credits,
            "avg_credits_per_video": total_credits / len(filtered) if filtered else 0,
            "total_generation_time": total_time,
            "avg_generation_time": total_time / len(completed) if completed else 0,
            "by_model": self._group_by_model(filtered),
            "by_duration": self._group_by_duration(filtered),
            "by_user": self._group_by_user(filtered),
            "by_project": self._group_by_project(filtered)
        }

    def get_daily_breakdown(
        self,
        days: int = 30,
        user_id: str = None,
        project_id: str = None
    ) -> List[Dict]:
        """Get day-by-day breakdown."""
        end = datetime.utcnow()
        start = end - timedelta(days=days)

        daily = []
        current = start

        while current < end:
            next_day = current + timedelta(days=1)

            day_events = self._filter_events(current, next_day, user_id, project_id)

            daily.append({
                "date": current.strftime("%Y-%m-%d"),
                "generations": len(day_events),
                "credits": sum(e.credits_used for e in day_events),
                "completed": len([e for e in day_events if e.status == "completed"]),
                "failed": len([e for e in day_events if e.status == "failed"])
            })

            current = next_day

        return daily

    def get_top_users(self, limit: int = 10, days: int = 30) -> List[Dict]:
        """Get top users by usage."""
        start = datetime.utcnow() - timedelta(days=days)
        filtered = self._filter_events(start=start)

        user_stats = defaultdict(lambda: {"generations": 0, "credits": 0})

        for event in filtered:
            user_stats[event.user_id]["generations"] += 1
            user_stats[event.user_id]["credits"] += event.credits_used

        sorted_users = sorted(
            user_stats.items(),
            key=lambda x: x[1]["credits"],
            reverse=True
        )

        return [
            {"user_id": user_id, **stats}
            for user_id, stats in sorted_users[:limit]
        ]

    def get_popular_prompts(self, limit: int = 10, days: int = 30) -> List[Dict]:
        """Analyze popular prompt patterns."""
        start = datetime.utcnow() - timedelta(days=days)
        filtered = self._filter_events(start=start)

        # Simple word frequency analysis
        word_freq = defaultdict(int)
        for event in filtered:
            words = event.prompt.lower().split()
            for word in words:
                if len(word) > 3:  # Skip short words
                    word_freq[word] += 1

        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)

        return [
            {"term": word, "count": count}
            for word, count in sorted_words[:limit]
        ]

    def get_performance_metrics(self, days: int = 30) -> Dict:
        """Get performance metrics."""
        start = datetime.utcnow() - timedelta(days=days)
        filtered = self._filter_events(start=start)

        completed = [e for e in filtered if e.status == "completed"]

        if not completed:
            return {"no_data": True}

        gen_times = [e.generation_time_seconds for e in completed]
        gen_times.sort()

        return {
            "total_videos": len(completed),
            "generation_time": {
                "min": min(gen_times),
                "max": max(gen_times),
                "avg": sum(gen_times) / len(gen_times),
                "p50": gen_times[len(gen_times) // 2],
                "p95": gen_times[int(len(gen_times) * 0.95)],
                "p99": gen_times[int(len(gen_times) * 0.99)]
            },
            "failure_rate": len([e for e in filtered if e.status == "failed"]) / len(filtered) * 100,
            "avg_retries": 0  # Would need retry tracking
        }

    def detect_anomalies(self, days: int = 7) -> List[Dict]:
        """Detect usage anomalies."""
        daily = self.get_daily_breakdown(days=days * 2)

        if len(daily) < days:
            return []

        # Calculate baseline (first half)
        baseline = daily[:len(daily)//2]
        recent = daily[len(daily)//2:]

        avg_baseline = sum(d["generations"] for d in baseline) / len(baseline)
        std_baseline = (
            sum((d["generations"] - avg_baseline) ** 2 for d in baseline) / len(baseline)
        ) ** 0.5

        anomalies = []
        for day in recent:
            if std_baseline > 0:
                z_score = (day["generations"] - avg_baseline) / std_baseline
                if abs(z_score) > 2:
                    anomalies.append({
                        "date": day["date"],
                        "generations": day["generations"],
                        "expected": round(avg_baseline),
                        "z_score": round(z_score, 2),
                        "type": "spike" if z_score > 0 else "drop"
                    })

        return anomalies

    def _filter_events(
        self,
        start: datetime = None,
        end: datetime = None,
        user_id: str = None,
        project_id: str = None
    ) -> List[GenerationEvent]:
        """Filter events by criteria."""
        filtered = self.events

        if start:
            filtered = [e for e in filtered if e.timestamp >= start]
        if end:
            filtered = [e for e in filtered if e.timestamp < end]
        if user_id:
            filtered = [e for e in filtered if e.user_id == user_id]
        if project_id:
            filtered = [e for e in filtered if e.project_id == project_id]

        return filtered

    def _group_by_model(self, events: List[GenerationEvent]) -> Dict:
        """Group by model."""
        by_model = defaultdict(lambda: {"count": 0, "credits": 0})
        for e in events:
            by_model[e.model]["count"] += 1
            by_model[e.model]["credits"] += e.credits_used
        return dict(by_model)

    def _group_by_duration(self, events: List[GenerationEvent]) -> Dict:
        """Group by duration."""
        by_duration = defaultdict(lambda: {"count": 0, "credits": 0})
        for e in events:
            key = f"{e.duration}s"
            by_duration[key]["count"] += 1
            by_duration[key]["credits"] += e.credits_used
        return dict(by_duration)

    def _group_by_user(self, events: List[GenerationEvent]) -> Dict:
        """Group by user."""
        by_user = defaultdict(lambda: {"count": 0, "credits": 0})
        for e in events:
            by_user[e.user_id]["count"] += 1
            by_user[e.user_id]["credits"] += e.credits_used
        return dict(by_user)

    def _group_by_project(self, events: List[GenerationEvent]) -> Dict:
        """Group by project."""
        by_project = defaultdict(lambda: {"count": 0, "credits": 0})
        for e in events:
            by_project[e.project_id]["count"] += 1
            by_project[e.project_id]["credits"] += e.credits_used
        return dict(by_project)
```

## Report Generator

```python
def generate_usage_report(analytics: UsageAnalytics, days: int = 30) -> str:
    """Generate a formatted usage report."""
    summary = analytics.get_summary(
        start=datetime.utcnow() - timedelta(days=days)
    )
    performance = analytics.get_performance_metrics(days)
    top_users = analytics.get_top_users(limit=5, days=days)
    anomalies = analytics.detect_anomalies(days=7)

    report = f"""
================================================================================
                     KLING AI USAGE REPORT ({days} DAYS)
================================================================================

SUMMARY
-------
Total Generations: {summary['total_generations']}
Completed: {summary['completed']} ({summary['success_rate']:.1f}% success rate)
Failed: {summary['failed']}
Total Credits Used: {summary['total_credits']}
Average Credits/Video: {summary['avg_credits_per_video']:.1f}

PERFORMANCE
-----------
Average Generation Time: {performance['generation_time']['avg']:.1f}s
P95 Generation Time: {performance['generation_time']['p95']:.1f}s
Failure Rate: {performance['failure_rate']:.2f}%

BY MODEL
--------
"""
    for model, stats in summary['by_model'].items():
        report += f"  {model}: {stats['count']} videos, {stats['credits']} credits\n"

    report += """
BY DURATION
-----------
"""
    for duration, stats in summary['by_duration'].items():
        report += f"  {duration}: {stats['count']} videos, {stats['credits']} credits\n"

    report += """
TOP USERS
---------
"""
    for i, user in enumerate(top_users, 1):
        report += f"  {i}. {user['user_id']}: {user['generations']} videos, {user['credits']} credits\n"

    if anomalies:
        report += """
ANOMALIES DETECTED
------------------
"""
        for a in anomalies:
            report += f"  {a['date']}: {a['type'].upper()} - {a['generations']} generations (expected ~{a['expected']})\n"

    report += """
================================================================================
"""

    return report

# Usage
analytics = UsageAnalytics()

# Record events (in production, this would come from your tracking system)
# analytics.record_event(...)

# Generate report
print(generate_usage_report(analytics, days=30))
```

## Export to CSV

```python
import csv

def export_to_csv(analytics: UsageAnalytics, filepath: str, days: int = 30):
    """Export usage data to CSV."""
    start = datetime.utcnow() - timedelta(days=days)
    events = analytics._filter_events(start=start)

    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "timestamp", "job_id", "user_id", "project_id",
            "model", "duration", "status", "credits_used",
            "generation_time_seconds"
        ])
        writer.writeheader()

        for event in events:
            writer.writerow({
                "timestamp": event.timestamp.isoformat(),
                "job_id": event.job_id,
                "user_id": event.user_id,
                "project_id": event.project_id,
                "model": event.model,
                "duration": event.duration,
                "status": event.status,
                "credits_used": event.credits_used,
                "generation_time_seconds": event.generation_time_seconds
            })

    print(f"Exported {len(events)} events to {filepath}")
```

## Output

Successful execution produces:
- Usage summary statistics
- Daily breakdown reports
- Top user analysis
- Anomaly detection alerts
- Exportable CSV data

## Error Handling

Common errors and solutions:
1. **No Data**: Ensure events are being recorded
2. **Date Range Issues**: Verify timezone handling
3. **Memory Issues**: Implement pagination for large datasets

## Examples

See code examples above for complete, runnable implementations.

## Resources

- [Kling AI Dashboard](https://console.klingai.com/usage)
- [pandas Documentation](https://pandas.pydata.org/)
- [Data Visualization](https://matplotlib.org/)
