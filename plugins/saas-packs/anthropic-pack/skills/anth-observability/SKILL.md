---
name: anth-observability
description: |
  Set up observability for Claude API integrations with metrics, logging,
  and alerting for latency, cost, errors, and token usage.
  Trigger with phrases like "anthropic monitoring", "claude observability",
  "anthropic metrics", "track claude usage", "claude dashboard".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, anthropic]
compatible-with: claude-code
---

# Anthropic Observability

## Overview

Instrument Claude API calls with structured logging, Prometheus metrics, and cost tracking. Every API response includes `usage` data and rate limit headers — capture these for dashboards and alerting.

## Structured Logging

```python
import anthropic
import logging
import time
import json

logger = logging.getLogger("claude")

def create_with_logging(client: anthropic.Anthropic, **kwargs) -> anthropic.types.Message:
    start = time.monotonic()
    request_meta = {
        "model": kwargs.get("model"),
        "max_tokens": kwargs.get("max_tokens"),
        "tool_count": len(kwargs.get("tools", [])),
        "stream": kwargs.get("stream", False),
    }

    try:
        response = client.messages.create(**kwargs)
        duration_ms = int((time.monotonic() - start) * 1000)

        logger.info(json.dumps({
            "event": "claude.request",
            "request_id": response._request_id,
            "model": response.model,
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "cache_read_tokens": getattr(response.usage, "cache_read_input_tokens", 0),
            "stop_reason": response.stop_reason,
            "duration_ms": duration_ms,
            "content_blocks": len(response.content),
        }))
        return response

    except anthropic.APIStatusError as e:
        duration_ms = int((time.monotonic() - start) * 1000)
        logger.error(json.dumps({
            "event": "claude.error",
            "status": e.status_code,
            "error_type": getattr(e, "type", "unknown"),
            "duration_ms": duration_ms,
            "request_id": e.response.headers.get("request-id", "unknown"),
        }))
        raise
```

## Prometheus Metrics

```python
from prometheus_client import Counter, Histogram, Gauge

claude_requests = Counter(
    "claude_requests_total", "Total Claude API requests",
    ["model", "stop_reason", "status"]
)
claude_latency = Histogram(
    "claude_latency_seconds", "Claude API latency",
    ["model"], buckets=[0.5, 1, 2, 5, 10, 30, 60]
)
claude_tokens = Counter(
    "claude_tokens_total", "Token usage",
    ["model", "direction"]  # direction: input|output|cache_read
)
claude_cost = Counter(
    "claude_cost_usd", "Estimated cost in USD",
    ["model"]
)
claude_rate_limit_remaining = Gauge(
    "claude_rate_limit_remaining", "Remaining rate limit",
    ["dimension"]  # dimension: requests|tokens
)

def track_metrics(response, duration: float):
    model = response.model
    claude_requests.labels(model=model, stop_reason=response.stop_reason, status="ok").inc()
    claude_latency.labels(model=model).observe(duration)
    claude_tokens.labels(model=model, direction="input").inc(response.usage.input_tokens)
    claude_tokens.labels(model=model, direction="output").inc(response.usage.output_tokens)

    # Cost estimation
    pricing = {"claude-haiku-4-20250514": (0.80, 4.0), "claude-sonnet-4-20250514": (3.0, 15.0)}
    rates = pricing.get(model, (3.0, 15.0))
    cost = (response.usage.input_tokens * rates[0] + response.usage.output_tokens * rates[1]) / 1e6
    claude_cost.labels(model=model).inc(cost)
```

## Key Metrics Dashboard

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `claude_requests_total{status="error"}` | Error count | > 5% of total |
| `claude_latency_seconds` p99 | Tail latency | > 10s |
| `claude_cost_usd` daily | Daily spend | > 80% budget |
| `claude_rate_limit_remaining{dimension="requests"}` | RPM headroom | < 10% remaining |
| `claude_tokens_total{direction="output"}` rate | Output throughput | Spike detection |

## Usage API (Server-Side)

```python
# Anthropic's Usage & Cost API for billing reconciliation
# GET https://api.anthropic.com/v1/usage
# Returns daily token usage and cost per model
```

## Error Handling

| Observability Gap | Risk | Fix |
|-------------------|------|-----|
| No request_id logged | Can't debug with support | Capture `response._request_id` |
| Missing cost tracking | Budget surprise | Track per-request cost |
| No latency histogram | Can't spot slow queries | Add Prometheus/Datadog histograms |

## Resources

- [Usage & Cost API](https://docs.anthropic.com/en/api/usage-cost-api)
- [Rate Limits](https://docs.anthropic.com/en/api/rate-limits)
- [API Status](https://status.anthropic.com)

## Next Steps

For incident response, see `anth-incident-runbook`.
