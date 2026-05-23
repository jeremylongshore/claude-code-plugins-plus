# Model Health Monitoring

## Model Health Monitoring

### Health Check Function

```python
import time
from typing import Optional

def check_model_health(
    model_id: str,
    timeout: float = 10.0
) -> dict:
    """Check if model responds correctly."""
    start = time.time()

    try:
        response = client.chat.completions.create(
            model=model_id,
            messages=[{"role": "user", "content": "Say 'ok'"}],
            max_tokens=5,
            timeout=timeout
        )

        latency = time.time() - start
        return {
            "model": model_id,
            "status": "healthy",
            "latency_ms": latency * 1000,
            "response": response.choices[0].message.content
        }

    except Exception as e:
        latency = time.time() - start
        return {
            "model": model_id,
            "status": "unhealthy",
            "latency_ms": latency * 1000,
            "error": str(e)
        }

# Check multiple models
models_to_check = [
    "openai/gpt-4-turbo",
    "anthropic/claude-3.5-sonnet",
    "meta-llama/llama-3.1-70b-instruct"
]

for model in models_to_check:
    health = check_model_health(model)
    print(f"{model}: {health['status']} ({health['latency_ms']:.0f}ms)")
```

### Continuous Monitoring

```python
import asyncio
from datetime import datetime

class ModelMonitor:
    def __init__(self, models: list, check_interval: int = 60):
        self.models = models
        self.check_interval = check_interval
        self.status_history = {m: [] for m in models}

    async def check_all(self):
        """Check all models once."""
        results = {}
        for model in self.models:
            health = check_model_health(model)
            results[model] = health

            self.status_history[model].append({
                "timestamp": datetime.now().isoformat(),
                "status": health["status"],
                "latency": health.get("latency_ms", 0)
            })

            # Keep last 100 entries
            self.status_history[model] = self.status_history[model][-100:]

        return results

    def get_uptime(self, model: str) -> float:
        """Calculate uptime percentage for model."""
        history = self.status_history.get(model, [])
        if not history:
            return 0.0
        healthy = sum(1 for h in history if h["status"] == "healthy")
        return healthy / len(history) * 100

    async def run(self):
        """Continuous monitoring loop."""
        while True:
            results = await self.check_all()
            print(f"\n[{datetime.now().isoformat()}] Model Status:")
            for model, health in results.items():
                uptime = self.get_uptime(model)
                print(f"  {model}: {health['status']} (uptime: {uptime:.1f}%)")
            await asyncio.sleep(self.check_interval)

# Usage
monitor = ModelMonitor([
    "openai/gpt-4-turbo",
    "anthropic/claude-3.5-sonnet"
])
# asyncio.run(monitor.run())
```
