---
name: openrouter-usage-analytics
description: |
  Analyze OpenRouter usage patterns. Triggers on "openrouter analytics",
  "openrouter usage", "openrouter statistics", "openrouter metrics".
allowed-tools: Read, Write, Edit, Bash
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# OpenRouter Usage Analytics

## Dashboard Activity

### Access OpenRouter Dashboard
```
openrouter.ai/activity shows:
- Request history
- Token usage
- Cost breakdown
- Model distribution
- Daily/weekly/monthly views
```

### API Usage Information
```bash
# Check current key stats
curl https://openrouter.ai/api/v1/auth/key \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"
```

## Custom Analytics Implementation

### Usage Logger
```python
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict
import json

@dataclass
class UsageRecord:
    timestamp: datetime
    model: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: float
    cost: float
    user_id: str = None
    tags: list = None

class UsageAnalytics:
    def __init__(self):
        self.records: list[UsageRecord] = []

    def record(
        self,
        response,
        model: str,
        latency_ms: float,
        user_id: str = None,
        tags: list = None
    ):
        cost = self._calculate_cost(
            model,
            response.usage.prompt_tokens,
            response.usage.completion_tokens
        )

        record = UsageRecord(
            timestamp=datetime.now(),
            model=model,
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            latency_ms=latency_ms,
            cost=cost,
            user_id=user_id,
            tags=tags or []
        )

        self.records.append(record)
        return record

    def _calculate_cost(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> float:
        prices = {
            "openai/gpt-4-turbo": (10.0, 30.0),
            "anthropic/claude-3.5-sonnet": (3.0, 15.0),
            "anthropic/claude-3-haiku": (0.25, 1.25),
        }
        p_price, c_price = prices.get(model, (10.0, 30.0))
        return (
            prompt_tokens * p_price / 1_000_000 +
            completion_tokens * c_price / 1_000_000
        )

    def get_summary(
        self,
        start: datetime = None,
        end: datetime = None
    ) -> dict:
        """Get usage summary for time period."""
        filtered = self._filter_by_time(start, end)

        if not filtered:
            return {"total_requests": 0}

        total_cost = sum(r.cost for r in filtered)
        total_tokens = sum(r.prompt_tokens + r.completion_tokens for r in filtered)

        return {
            "total_requests": len(filtered),
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "avg_latency_ms": sum(r.latency_ms for r in filtered) / len(filtered),
            "avg_cost_per_request": total_cost / len(filtered),
        }

    def _filter_by_time(
        self,
        start: datetime = None,
        end: datetime = None
    ) -> list[UsageRecord]:
        filtered = self.records
        if start:
            filtered = [r for r in filtered if r.timestamp >= start]
        if end:
            filtered = [r for r in filtered if r.timestamp <= end]
        return filtered

analytics = UsageAnalytics()
```

### Model Analytics
```python
def get_model_breakdown(self) -> dict:
    """Analyze usage by model."""
    by_model = defaultdict(lambda: {
        "requests": 0,
        "tokens": 0,
        "cost": 0.0,
        "avg_latency": []
    })

    for record in self.records:
        by_model[record.model]["requests"] += 1
        by_model[record.model]["tokens"] += (
            record.prompt_tokens + record.completion_tokens
        )
        by_model[record.model]["cost"] += record.cost
        by_model[record.model]["avg_latency"].append(record.latency_ms)

    # Calculate averages
    result = {}
    for model, data in by_model.items():
        result[model] = {
            "requests": data["requests"],
            "tokens": data["tokens"],
            "cost": data["cost"],
            "avg_latency_ms": (
                sum(data["avg_latency"]) / len(data["avg_latency"])
                if data["avg_latency"] else 0
            ),
            "cost_per_request": data["cost"] / data["requests"]
        }

    return result
```

### Time Series Analytics
```python
def get_daily_stats(self, days: int = 30) -> list[dict]:
    """Get daily statistics."""
    end = datetime.now()
    start = end - timedelta(days=days)

    daily = defaultdict(lambda: {
        "requests": 0,
        "tokens": 0,
        "cost": 0.0
    })

    for record in self._filter_by_time(start, end):
        day = record.timestamp.date().isoformat()
        daily[day]["requests"] += 1
        daily[day]["tokens"] += record.prompt_tokens + record.completion_tokens
        daily[day]["cost"] += record.cost

    # Fill in missing days
    result = []
    current = start.date()
    while current <= end.date():
        day_str = current.isoformat()
        result.append({
            "date": day_str,
            **daily.get(day_str, {"requests": 0, "tokens": 0, "cost": 0.0})
        })
        current += timedelta(days=1)

    return result

def get_hourly_distribution(self) -> dict:
    """Get request distribution by hour."""
    hourly = defaultdict(int)

    for record in self.records:
        hour = record.timestamp.hour
        hourly[hour] += 1

    return {str(h).zfill(2): hourly.get(h, 0) for h in range(24)}
```

### User Analytics
```python
def get_user_stats(self) -> dict:
    """Analyze usage by user."""
    by_user = defaultdict(lambda: {
        "requests": 0,
        "tokens": 0,
        "cost": 0.0,
        "models_used": set()
    })

    for record in self.records:
        user_id = record.user_id or "anonymous"
        by_user[user_id]["requests"] += 1
        by_user[user_id]["tokens"] += (
            record.prompt_tokens + record.completion_tokens
        )
        by_user[user_id]["cost"] += record.cost
        by_user[user_id]["models_used"].add(record.model)

    # Convert sets to lists for JSON serialization
    return {
        user_id: {
            "requests": data["requests"],
            "tokens": data["tokens"],
            "cost": data["cost"],
            "models_used": list(data["models_used"])
        }
        for user_id, data in by_user.items()
    }

def get_top_users(self, limit: int = 10) -> list[dict]:
    """Get top users by cost."""
    user_stats = self.get_user_stats()
    sorted_users = sorted(
        user_stats.items(),
        key=lambda x: x[1]["cost"],
        reverse=True
    )
    return [
        {"user_id": uid, **stats}
        for uid, stats in sorted_users[:limit]
    ]
```

## Performance Analytics

### Latency Analysis
```python
import statistics

def get_latency_stats(self, model: str = None) -> dict:
    """Get latency statistics."""
    if model:
        latencies = [r.latency_ms for r in self.records if r.model == model]
    else:
        latencies = [r.latency_ms for r in self.records]

    if not latencies:
        return {"error": "No data"}

    return {
        "count": len(latencies),
        "mean": statistics.mean(latencies),
        "median": statistics.median(latencies),
        "stdev": statistics.stdev(latencies) if len(latencies) > 1 else 0,
        "min": min(latencies),
        "max": max(latencies),
        "p50": statistics.quantiles(latencies, n=100)[49] if len(latencies) >= 2 else latencies[0],
        "p95": statistics.quantiles(latencies, n=100)[94] if len(latencies) >= 2 else latencies[0],
        "p99": statistics.quantiles(latencies, n=100)[98] if len(latencies) >= 2 else latencies[0],
    }

def get_latency_by_model(self) -> dict:
    """Compare latency across models."""
    models = set(r.model for r in self.records)
    return {model: self.get_latency_stats(model) for model in models}
```

### Error Rate Tracking
```python
class ErrorTracker:
    def __init__(self):
        self.errors = []
        self.successes = 0

    def record_success(self, model: str):
        self.successes += 1

    def record_error(self, model: str, error_type: str, error_message: str):
        self.errors.append({
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "error_type": error_type,
            "error_message": error_message
        })

    def get_error_rate(self) -> float:
        total = self.successes + len(self.errors)
        if total == 0:
            return 0.0
        return len(self.errors) / total

    def get_errors_by_type(self) -> dict:
        by_type = defaultdict(int)
        for error in self.errors:
            by_type[error["error_type"]] += 1
        return dict(by_type)

    def get_errors_by_model(self) -> dict:
        by_model = defaultdict(int)
        for error in self.errors:
            by_model[error["model"]] += 1
        return dict(by_model)

error_tracker = ErrorTracker()
```

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

## Visualization

### Terminal Dashboard
```python
def print_dashboard(analytics: UsageAnalytics):
    """Print simple terminal dashboard."""
    summary = analytics.get_summary()
    models = analytics.get_model_breakdown()

    print("=" * 60)
    print("OpenRouter Usage Dashboard")
    print("=" * 60)

    print(f"\nTotal Requests: {summary['total_requests']}")
    print(f"Total Tokens: {summary['total_tokens']:,}")
    print(f"Total Cost: ${summary['total_cost']:.4f}")
    print(f"Avg Latency: {summary['avg_latency_ms']:.0f}ms")

    print("\nBy Model:")
    print("-" * 60)
    for model, stats in sorted(models.items(), key=lambda x: -x[1]["cost"]):
        print(f"  {model}")
        print(f"    Requests: {stats['requests']}, "
              f"Cost: ${stats['cost']:.4f}, "
              f"Latency: {stats['avg_latency_ms']:.0f}ms")

print_dashboard(analytics)
```
