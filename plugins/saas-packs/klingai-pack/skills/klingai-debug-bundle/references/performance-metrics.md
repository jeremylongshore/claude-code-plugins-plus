# Performance Metrics

## Performance Metrics

```python
from dataclasses import dataclass, field
from statistics import mean, median, stdev
from collections import defaultdict

@dataclass
class PerformanceMetrics:
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_duration_ms: float = 0
    durations: list = field(default_factory=list)
    errors_by_type: dict = field(default_factory=lambda: defaultdict(int))
    requests_by_endpoint: dict = field(default_factory=lambda: defaultdict(int))

    def record_request(self, duration_ms: float, endpoint: str, success: bool, error: str = None):
        self.total_requests += 1
        self.total_duration_ms += duration_ms
        self.durations.append(duration_ms)
        self.requests_by_endpoint[endpoint] += 1

        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
            if error:
                self.errors_by_type[error] += 1

    def get_stats(self) -> dict:
        if not self.durations:
            return {}

        return {
            "total_requests": self.total_requests,
            "success_rate": self.successful_requests / self.total_requests * 100,
            "avg_duration_ms": mean(self.durations),
            "median_duration_ms": median(self.durations),
            "p95_duration_ms": sorted(self.durations)[int(len(self.durations) * 0.95)],
            "min_duration_ms": min(self.durations),
            "max_duration_ms": max(self.durations),
            "stddev_duration_ms": stdev(self.durations) if len(self.durations) > 1 else 0,
            "errors_by_type": dict(self.errors_by_type),
            "requests_by_endpoint": dict(self.requests_by_endpoint)
        }

metrics = PerformanceMetrics()
```
