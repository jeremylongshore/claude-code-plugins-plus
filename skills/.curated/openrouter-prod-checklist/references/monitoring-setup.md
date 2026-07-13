# Monitoring Setup

## Monitoring Setup

### Basic Metrics

```python
import time
from dataclasses import dataclass
from typing import Optional

@dataclass
class RequestMetrics:
    model: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: float
    success: bool
    error: Optional[str] = None

class MetricsCollector:
    def __init__(self):
        self.metrics = []

    def record(self, metrics: RequestMetrics):
        self.metrics.append(metrics)
        # Send to your monitoring system
        self._send_to_monitoring(metrics)

    def _send_to_monitoring(self, metrics: RequestMetrics):
        # Example: Send to StatsD/Datadog
        # statsd.gauge('openrouter.latency', metrics.latency_ms)
        # statsd.increment('openrouter.requests')
        pass

collector = MetricsCollector()

def monitored_chat(prompt: str, model: str):
    start = time.time()
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )

        collector.record(RequestMetrics(
            model=model,
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            latency_ms=(time.time() - start) * 1000,
            success=True
        ))

        return response

    except Exception as e:
        collector.record(RequestMetrics(
            model=model,
            prompt_tokens=0,
            completion_tokens=0,
            latency_ms=(time.time() - start) * 1000,
            success=False,
            error=str(e)
        ))
        raise
```

### Health Check Endpoint

```python
from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/health/openrouter")
def openrouter_health():
    try:
        # Quick health check
        response = client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=5,
            timeout=5.0
        )

        return jsonify({
            "status": "healthy",
            "model": "openai/gpt-3.5-turbo",
            "response_received": True
        })

    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 503
```
