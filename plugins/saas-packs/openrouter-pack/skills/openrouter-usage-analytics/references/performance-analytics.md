# Performance Analytics

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
