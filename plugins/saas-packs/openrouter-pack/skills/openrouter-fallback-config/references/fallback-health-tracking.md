# Fallback Health Tracking

## Fallback Health Tracking

### Track Model Health

```python
from collections import defaultdict
from datetime import datetime, timedelta

class HealthTracker:
    def __init__(self, window_minutes: int = 10):
        self.window = timedelta(minutes=window_minutes)
        self.successes = defaultdict(list)
        self.failures = defaultdict(list)

    def record_success(self, model: str):
        now = datetime.now()
        self._cleanup(model, now)
        self.successes[model].append(now)

    def record_failure(self, model: str):
        now = datetime.now()
        self._cleanup(model, now)
        self.failures[model].append(now)

    def _cleanup(self, model: str, now: datetime):
        cutoff = now - self.window
        self.successes[model] = [t for t in self.successes[model] if t > cutoff]
        self.failures[model] = [t for t in self.failures[model] if t > cutoff]

    def get_success_rate(self, model: str) -> float:
        total = len(self.successes[model]) + len(self.failures[model])
        if total == 0:
            return 1.0  # Assume healthy if no data
        return len(self.successes[model]) / total

    def should_skip(self, model: str, threshold: float = 0.3) -> bool:
        return self.get_success_rate(model) < threshold

tracker = HealthTracker()

def health_aware_fallback(prompt: str, models: list):
    # Sort by current health
    sorted_models = sorted(
        models,
        key=lambda m: tracker.get_success_rate(m),
        reverse=True
    )

    for model in sorted_models:
        if tracker.should_skip(model):
            continue

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            tracker.record_success(model)
            return response
        except Exception:
            tracker.record_failure(model)
            continue

    raise Exception("All healthy models failed")
```
