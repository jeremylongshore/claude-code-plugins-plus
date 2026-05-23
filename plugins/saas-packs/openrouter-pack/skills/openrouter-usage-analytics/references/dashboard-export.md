# Dashboard Export

## Dashboard Export

### Generate Report

```python
def generate_analytics_report(analytics: UsageAnalytics) -> dict:
    """Generate comprehensive analytics report."""
    now = datetime.now()
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)
    last_30d = now - timedelta(days=30)

    return {
        "generated_at": now.isoformat(),
        "summary": {
            "last_24h": analytics.get_summary(start=last_24h),
            "last_7d": analytics.get_summary(start=last_7d),
            "last_30d": analytics.get_summary(start=last_30d),
            "all_time": analytics.get_summary(),
        },
        "model_breakdown": analytics.get_model_breakdown(),
        "daily_trend": analytics.get_daily_stats(30),
        "hourly_distribution": analytics.get_hourly_distribution(),
        "latency_stats": analytics.get_latency_by_model(),
        "top_users": analytics.get_top_users(10),
    }

def export_to_json(analytics: UsageAnalytics, filepath: str):
    """Export report to JSON file."""
    report = generate_analytics_report(analytics)
    with open(filepath, 'w') as f:
        json.dump(report, f, indent=2, default=str)
```

### CSV Export

```python
import csv

def export_to_csv(analytics: UsageAnalytics, filepath: str):
    """Export raw records to CSV."""
    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            "timestamp", "model", "prompt_tokens", "completion_tokens",
            "latency_ms", "cost", "user_id"
        ])

        for record in analytics.records:
            writer.writerow([
                record.timestamp.isoformat(),
                record.model,
                record.prompt_tokens,
                record.completion_tokens,
                record.latency_ms,
                record.cost,
                record.user_id or ""
            ])
```
