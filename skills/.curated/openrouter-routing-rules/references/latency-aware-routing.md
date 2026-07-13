# Latency-Aware Routing

## Latency-Aware Routing

### Fast Response Router

```python
import time
from statistics import mean

class LatencyRouter:
    def __init__(self, models: list):
        self.models = models
        self.latency_history: dict[str, list[float]] = {m: [] for m in models}
        self.latency_budget: float = 5.0  # seconds

    def record_latency(self, model: str, latency: float):
        self.latency_history[model].append(latency)
        # Keep last 10
        self.latency_history[model] = self.latency_history[model][-10:]

    def get_avg_latency(self, model: str) -> float:
        history = self.latency_history[model]
        if not history:
            return 2.0  # Default assumption
        return mean(history)

    def route_for_speed(self) -> str:
        """Return fastest model that fits latency budget."""
        candidates = []
        for model in self.models:
            avg_latency = self.get_avg_latency(model)
            if avg_latency <= self.latency_budget:
                candidates.append((model, avg_latency))

        if not candidates:
            # Return fastest regardless
            return min(self.models, key=lambda m: self.get_avg_latency(m))

        # Sort by latency, return fastest
        candidates.sort(key=lambda x: x[1])
        return candidates[0][0]

    def chat(self, prompt: str, **kwargs):
        model = self.route_for_speed()
        start = time.time()

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )
            self.record_latency(model, time.time() - start)
            return response
        except Exception as e:
            self.record_latency(model, 30.0)  # Record as slow on error
            raise
```
