# Monitoring & Profiling

## Monitoring & Profiling

### Latency Tracking

```python
import time
from dataclasses import dataclass
from statistics import mean, median, stdev

@dataclass
class LatencyMetrics:
    model: str
    latencies: list
    tokens: list

class PerformanceMonitor:
    """Track performance metrics."""

    def __init__(self):
        self.metrics = {}

    def record(
        self,
        model: str,
        latency_ms: float,
        tokens: int
    ):
        if model not in self.metrics:
            self.metrics[model] = LatencyMetrics(model, [], [])

        self.metrics[model].latencies.append(latency_ms)
        self.metrics[model].tokens.append(tokens)

        # Keep last 1000
        self.metrics[model].latencies = self.metrics[model].latencies[-1000:]
        self.metrics[model].tokens = self.metrics[model].tokens[-1000:]

    def get_stats(self, model: str) -> dict:
        if model not in self.metrics:
            return {}

        m = self.metrics[model]
        return {
            "count": len(m.latencies),
            "latency": {
                "mean": mean(m.latencies),
                "median": median(m.latencies),
                "p95": sorted(m.latencies)[int(len(m.latencies) * 0.95)],
                "stdev": stdev(m.latencies) if len(m.latencies) > 1 else 0
            },
            "tokens_per_request": mean(m.tokens),
            "tokens_per_second": sum(m.tokens) / (sum(m.latencies) / 1000)
        }

monitor = PerformanceMonitor()

def monitored_chat(prompt: str, model: str):
    """Chat with monitoring."""
    start = time.time()

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )

    latency = (time.time() - start) * 1000
    tokens = response.usage.total_tokens

    monitor.record(model, latency, tokens)

    return response
```
