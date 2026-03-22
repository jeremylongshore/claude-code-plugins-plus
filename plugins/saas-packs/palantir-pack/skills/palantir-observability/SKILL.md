---
name: palantir-observability
description: |
  Set up observability for Palantir Foundry integrations with metrics, logging, and alerts.
  Use when implementing monitoring for Foundry API calls, setting up dashboards,
  or configuring alerting for Foundry integration health.
  Trigger with phrases like "palantir monitoring", "foundry metrics",
  "palantir observability", "monitor foundry", "foundry alerts".
allowed-tools: Read, Write, Edit
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, palantir, foundry, observability, monitoring]
compatible-with: claude-code, codex, openclaw
---

# Palantir Observability

## Overview
Set up comprehensive observability for Foundry integrations: structured logging with request IDs, Prometheus metrics for API latency/errors, health check endpoints, and alert rules.

## Prerequisites
- Working Foundry integration
- Prometheus + Grafana (or equivalent monitoring stack)
- Familiarity with `palantir-prod-checklist`

## Instructions

### Step 1: Structured Logging
```python
import logging, json, time, uuid

class FoundryLogger:
    def __init__(self):
        self.logger = logging.getLogger("foundry")
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def log_api_call(self, method: str, endpoint: str, status: int, duration_ms: float):
        self.logger.info(json.dumps({
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "request_id": str(uuid.uuid4())[:8],
            "service": "foundry",
            "method": method,
            "endpoint": endpoint,
            "status": status,
            "duration_ms": round(duration_ms, 2),
            "level": "error" if status >= 400 else "info",
        }))
```

### Step 2: Prometheus Metrics
```python
from prometheus_client import Counter, Histogram, Gauge

foundry_requests = Counter(
    "foundry_api_requests_total",
    "Total Foundry API requests",
    ["method", "endpoint", "status"],
)
foundry_latency = Histogram(
    "foundry_api_latency_seconds",
    "Foundry API request latency",
    ["endpoint"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)
foundry_health = Gauge(
    "foundry_api_healthy",
    "1 if Foundry API is reachable, 0 otherwise",
)

def instrumented_call(client, method, *args, **kwargs):
    endpoint = method.__qualname__
    start = time.monotonic()
    try:
        result = method(*args, **kwargs)
        status = 200
        return result
    except foundry.ApiError as e:
        status = e.status_code
        raise
    finally:
        duration = time.monotonic() - start
        foundry_requests.labels(method="API", endpoint=endpoint, status=str(status)).inc()
        foundry_latency.labels(endpoint=endpoint).observe(duration)
```

### Step 3: Health Check with Metrics
```python
import time

async def foundry_health_check():
    start = time.monotonic()
    try:
        list(client.ontologies.Ontology.list())
        latency = (time.monotonic() - start) * 1000
        foundry_health.set(1)
        return {"status": "healthy", "latency_ms": round(latency, 1)}
    except Exception as e:
        foundry_health.set(0)
        return {"status": "unhealthy", "error": str(e)}
```

### Step 4: Alert Rules (Prometheus)
```yaml
groups:
  - name: foundry
    rules:
      - alert: FoundryAPIDown
        expr: foundry_api_healthy == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Foundry API unreachable for 2+ minutes"

      - alert: FoundryHighErrorRate
        expr: rate(foundry_api_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: warning

      - alert: FoundryHighLatency
        expr: histogram_quantile(0.99, foundry_api_latency_seconds_bucket) > 10
        for: 10m
        labels:
          severity: warning
```

### Step 5: Dashboard Queries (Grafana)
```
# Request rate by status
rate(foundry_api_requests_total[5m])

# P99 latency
histogram_quantile(0.99, rate(foundry_api_latency_seconds_bucket[5m]))

# Error ratio
sum(rate(foundry_api_requests_total{status=~"[45].."}[5m]))
/ sum(rate(foundry_api_requests_total[5m]))
```

## Output
- Structured JSON logging with request IDs
- Prometheus metrics for requests, latency, and health
- Alert rules for API downtime, error rate, and latency
- Grafana dashboard queries

## Error Handling
| Alert | Threshold | Action |
|-------|-----------|--------|
| API Down | Health check fails 2min | Page on-call, check `palantir-incident-runbook` |
| High Error Rate | 5xx > 5% for 5min | Check Foundry status, review logs |
| High Latency | p99 > 10s for 10min | Review query complexity, check Foundry load |
| Rate Limited | 429 count spike | Tune rate limiter settings |

## Resources
- [Prometheus Python Client](https://github.com/prometheus/client_python)
- [Foundry API Reference](https://www.palantir.com/docs/foundry/api/general/overview/introduction)

## Next Steps
For multi-environment setup, see `palantir-multi-env-setup`.
