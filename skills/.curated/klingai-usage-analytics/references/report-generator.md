# Report Generator

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
