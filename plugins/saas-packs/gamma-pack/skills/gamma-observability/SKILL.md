---
name: gamma-observability
description: |
  Implement comprehensive observability for Gamma integrations.
  Use when setting up monitoring, logging, tracing,
  or building dashboards for Gamma API usage.
  Trigger with phrases like "gamma monitoring", "gamma logging",
  "gamma metrics", "gamma observability", "gamma dashboard".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Gamma Observability

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Implement the three pillars of observability (metrics, logging, tracing) for Gamma integrations with alerting and dashboards.

## Prerequisites
- Observability stack (Prometheus, Grafana, or cloud equivalent)
- Log aggregation (ELK, CloudWatch, or similar)
- APM tool (Datadog, New Relic, or OpenTelemetry)

## Instructions

### Step 1: Instrument Metrics
Add Prometheus counters (request total, presentations created), histograms (request duration), and gauges (rate limit remaining) to the Gamma client via interceptors.

### Step 2: Add Structured Logging
Configure Winston with JSON format, timestamps, and service metadata. Log requests, responses, and errors with sanitized parameters (no API keys).

### Step 3: Enable Distributed Tracing
Use OpenTelemetry to create spans for Gamma API calls with operation name, success status, and error recording.

### Step 4: Build Dashboard
Create Grafana dashboard with request rate, latency p95, error rate, and rate limit remaining panels.

### Step 5: Configure Alerts
- High error rate (>5% for 5 min)
- Rate limit critically low (<10 remaining)
- High latency (p95 > 5s for 5 min)

### Step 6: Add Health Check
Endpoint that pings Gamma API and reports status (healthy/degraded/unhealthy) with latency and rate limit info.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for Prometheus metrics, Winston logger, OpenTelemetry tracing, Grafana dashboard JSON, alert rules, and health check endpoint.

## Output
- Prometheus metrics on all API calls
- Structured JSON logging with sanitized params
- Distributed tracing with OpenTelemetry spans
- Grafana dashboard with key metrics
- Alert rules for errors, rate limits, and latency

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Metrics not appearing | Registry not exposed | Add `/metrics` endpoint serving registry |
| Missing traces | Tracer not initialized | Initialize OpenTelemetry SDK at startup |
| Log volume too high | Debug level in prod | Set LOG_LEVEL to 'info' or 'warn' |
| False alerts | Thresholds too sensitive | Tune alert thresholds to traffic patterns |

## Examples

### Quick Health Check
```bash
curl http://localhost:3000/health/gamma | jq
# { "status": "healthy", "latency": 150, "rateLimit": { "remaining": 95, "limit": 100 } }
```

## Resources
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)
- [Grafana Dashboards](https://grafana.com/docs/grafana/latest/dashboards/)

## Next Steps
Proceed to `gamma-incident-runbook` for incident response.
