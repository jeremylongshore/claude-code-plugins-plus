# Provider Health Monitoring

## Provider Health Monitoring

### Track Provider Status

```python
class ProviderHealthMonitor:
    """Monitor health across providers."""

    def __init__(self):
        self.status = {}
        self.latencies = {}

    def record_success(self, model: str, latency_ms: float):
        provider = model.split("/")[0]

        if provider not in self.status:
            self.status[provider] = {"success": 0, "failure": 0}
            self.latencies[provider] = []

        self.status[provider]["success"] += 1
        self.latencies[provider].append(latency_ms)
        self.latencies[provider] = self.latencies[provider][-100:]

    def record_failure(self, model: str):
        provider = model.split("/")[0]
        if provider not in self.status:
            self.status[provider] = {"success": 0, "failure": 0}
        self.status[provider]["failure"] += 1

    def get_health_report(self) -> dict:
        """Get health report for all providers."""
        report = {}
        for provider, stats in self.status.items():
            total = stats["success"] + stats["failure"]
            latencies = self.latencies.get(provider, [])

            report[provider] = {
                "success_rate": stats["success"] / total if total else 0,
                "total_requests": total,
                "avg_latency_ms": sum(latencies) / len(latencies) if latencies else 0
            }
        return report

monitor = ProviderHealthMonitor()
```
