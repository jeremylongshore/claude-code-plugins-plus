# Budget Tracking

## Budget Tracking

### Real-Time Cost Tracking

```python
import json
from pathlib import Path
from datetime import datetime, date

class CostTracker:
    def __init__(self, storage_path: str = "cost_tracking.json"):
        self.storage_path = Path(storage_path)
        self.data = self._load()

    def _load(self) -> dict:
        if self.storage_path.exists():
            return json.loads(self.storage_path.read_text())
        return {"daily": {}, "monthly": {}, "requests": []}

    def _save(self):
        self.storage_path.write_text(json.dumps(self.data, indent=2))

    def record(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost: float
    ):
        today = date.today().isoformat()
        month = today[:7]  # YYYY-MM

        # Daily
        if today not in self.data["daily"]:
            self.data["daily"][today] = 0.0
        self.data["daily"][today] += cost

        # Monthly
        if month not in self.data["monthly"]:
            self.data["monthly"][month] = 0.0
        self.data["monthly"][month] += cost

        # Detailed log
        self.data["requests"].append({
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "cost": cost
        })

        # Keep last 1000 requests
        self.data["requests"] = self.data["requests"][-1000:]

        self._save()

    def get_daily_cost(self, date_str: str = None) -> float:
        date_str = date_str or date.today().isoformat()
        return self.data["daily"].get(date_str, 0.0)

    def get_monthly_cost(self, month_str: str = None) -> float:
        month_str = month_str or date.today().isoformat()[:7]
        return self.data["monthly"].get(month_str, 0.0)

tracker = CostTracker()

def tracked_chat(prompt: str, model: str = "openai/gpt-4-turbo"):
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )

    cost = calculate_cost(model, response.usage)
    tracker.record(
        model=model,
        prompt_tokens=response.usage.prompt_tokens,
        completion_tokens=response.usage.completion_tokens,
        cost=cost
    )

    return response

def calculate_cost(model: str, usage) -> float:
    prices = {
        "openai/gpt-4-turbo": (10.0, 30.0),
        "anthropic/claude-3.5-sonnet": (3.0, 15.0),
        "anthropic/claude-3-haiku": (0.25, 1.25),
        "openai/gpt-3.5-turbo": (0.5, 1.5),
    }
    prompt_price, completion_price = prices.get(model, (10.0, 30.0))
    return (
        usage.prompt_tokens * prompt_price / 1_000_000 +
        usage.completion_tokens * completion_price / 1_000_000
    )
```
