# Export To Csv

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
