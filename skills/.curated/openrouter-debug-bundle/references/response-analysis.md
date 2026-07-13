# Response Analysis

## Response Analysis

### Token Usage Tracking

```python
class UsageTracker:
    def __init__(self):
        self.requests = []

    def track(self, response, model: str, estimated_cost: float):
        self.requests.append({
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
            "estimated_cost": estimated_cost
        })

    def summary(self):
        total_tokens = sum(r["total_tokens"] for r in self.requests)
        total_cost = sum(r["estimated_cost"] for r in self.requests)
        return {
            "total_requests": len(self.requests),
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "by_model": self._group_by_model()
        }

    def _group_by_model(self):
        models = {}
        for r in self.requests:
            model = r["model"]
            if model not in models:
                models[model] = {"requests": 0, "tokens": 0, "cost": 0}
            models[model]["requests"] += 1
            models[model]["tokens"] += r["total_tokens"]
            models[model]["cost"] += r["estimated_cost"]
        return models

tracker = UsageTracker()
```

### Latency Monitoring

```python
import statistics

class LatencyMonitor:
    def __init__(self):
        self.latencies = {}

    def record(self, model: str, latency_ms: float):
        if model not in self.latencies:
            self.latencies[model] = []
        self.latencies[model].append(latency_ms)

    def stats(self, model: str):
        if model not in self.latencies:
            return None
        data = self.latencies[model]
        return {
            "count": len(data),
            "mean": statistics.mean(data),
            "median": statistics.median(data),
            "stdev": statistics.stdev(data) if len(data) > 1 else 0,
            "min": min(data),
            "max": max(data),
            "p95": sorted(data)[int(len(data) * 0.95)] if len(data) > 20 else max(data)
        }
```
