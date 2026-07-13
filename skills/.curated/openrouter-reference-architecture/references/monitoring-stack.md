# Monitoring Stack

## Monitoring Stack

### Prometheus Metrics

```python
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Metrics
REQUEST_COUNT = Counter(
    'openrouter_requests_total',
    'Total requests to OpenRouter',
    ['model', 'status']
)

REQUEST_LATENCY = Histogram(
    'openrouter_request_latency_seconds',
    'Request latency in seconds',
    ['model']
)

TOKENS_USED = Counter(
    'openrouter_tokens_total',
    'Total tokens used',
    ['model', 'type']
)

ACTIVE_REQUESTS = Gauge(
    'openrouter_active_requests',
    'Currently active requests'
)

def instrumented_chat(service: OpenRouterService, prompt: str, model: str):
    ACTIVE_REQUESTS.inc()
    start = time.time()

    try:
        response = service.chat(prompt, model=model)
        REQUEST_COUNT.labels(model=model, status="success").inc()
        return response

    except Exception as e:
        REQUEST_COUNT.labels(model=model, status="error").inc()
        raise

    finally:
        latency = time.time() - start
        REQUEST_LATENCY.labels(model=model).observe(latency)
        ACTIVE_REQUESTS.dec()

# Start metrics server
start_http_server(9090)
```

### Grafana Dashboard JSON

```json
{
  "title": "OpenRouter Service",
  "panels": [
    {
      "title": "Request Rate",
      "type": "graph",
      "targets": [
        {
          "expr": "rate(openrouter_requests_total[5m])",
          "legendFormat": "{{model}} - {{status}}"
        }
      ]
    },
    {
      "title": "Latency P95",
      "type": "graph",
      "targets": [
        {
          "expr": "histogram_quantile(0.95, rate(openrouter_request_latency_seconds_bucket[5m]))",
          "legendFormat": "{{model}}"
        }
      ]
    },
    {
      "title": "Error Rate",
      "type": "singlestat",
      "targets": [
        {
          "expr": "sum(rate(openrouter_requests_total{status='error'}[5m])) / sum(rate(openrouter_requests_total[5m]))"
        }
      ]
    }
  ]
}
```
