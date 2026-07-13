# Monitoring Load Distribution

## Monitoring Load Distribution

### Request Tracking

```python
from collections import Counter
from datetime import datetime

class LoadMonitor:
    def __init__(self, balancer):
        self.balancer = balancer
        self.request_counts = Counter()
        self.latencies = {}
        self.errors = Counter()

    def record_request(self, key: str, latency: float, success: bool):
        self.request_counts[key] += 1
        if key not in self.latencies:
            self.latencies[key] = []
        self.latencies[key].append(latency)

        if not success:
            self.errors[key] += 1

    def stats(self) -> dict:
        return {
            "distribution": dict(self.request_counts),
            "avg_latency": {
                key: sum(lats) / len(lats)
                for key, lats in self.latencies.items()
            },
            "error_rate": {
                key: self.errors[key] / self.request_counts[key]
                for key in self.request_counts
            }
        }

monitor = LoadMonitor(lb_client)
```
