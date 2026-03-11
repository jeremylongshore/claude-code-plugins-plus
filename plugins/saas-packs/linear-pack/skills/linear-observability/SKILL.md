---
name: linear-observability
description: |
  Implement monitoring, logging, and alerting for Linear integrations.
  Use when setting up metrics collection, creating dashboards,
  or configuring alerts for Linear API usage.
  Trigger with phrases like "linear monitoring", "linear observability",
  "linear metrics", "linear logging", "monitor linear integration".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Linear Observability

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Comprehensive monitoring, logging, and alerting for Linear integrations using Prometheus metrics, structured logging, and health checks.

## Prerequisites
- Linear integration deployed
- Metrics infrastructure (Prometheus, Datadog, etc.)
- Logging infrastructure (ELK, CloudWatch, etc.)
- Alerting system configured

## Instructions

### Step 1: Define Key Metrics
| Metric | Type | Purpose |
|--------|------|---------|
| `linear_api_requests_total` | Counter | Track request volume by operation/status |
| `linear_api_request_duration_seconds` | Histogram | Measure API latency |
| `linear_rate_limit_remaining` | Gauge | Monitor rate limit headroom |
| `linear_webhooks_received_total` | Counter | Track webhook volume |
| `linear_cache_hits_total` | Counter | Measure cache effectiveness |

### Step 2: Instrument the Client
Wrap the Linear SDK's fetch layer to capture metrics on every API call including operation name, duration, status, and rate limit headers.

### Step 3: Add Structured Logging
Use pino/winston with JSON output, component tags, and correlation IDs for API calls, webhooks, and errors.

### Step 4: Create Health Check Endpoint
Verify API connectivity, cache status, and rate limit headroom. Return `healthy`, `degraded`, or `unhealthy` status.

### Step 5: Configure Alerting Rules
- High error rate (>5% over 5 min)
- Rate limit low (<100 remaining)
- Slow responses (p95 > 2s)
- Webhook processing errors

### Step 6: Build Grafana Dashboard
Panels for request rate, latency p95, rate limit remaining, and webhook distribution.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for full Prometheus metrics, instrumented client, logger, health check, alert rules, and Grafana dashboard JSON.

## Output
- Prometheus metrics collecting on all Linear API calls
- Structured JSON logging for API calls and webhooks
- Health check endpoint returning system status
- Alerting rules for error rate, rate limits, and latency

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Metrics not collecting | Missing instrumentation | Wrap client with instrumented fetch |
| Alerts not firing | Wrong threshold | Adjust alert thresholds to match traffic |
| Missing labels | Logger misconfigured | Check logger base config and child loggers |

## Examples

### Quick Health Check
```bash
curl http://localhost:3000/health/linear | jq
# { "status": "healthy", "checks": { "linear_api": { "status": "healthy", "latency_ms": 150 } } }
```

## Resources
- [Prometheus Client Library](https://github.com/siimon/prom-client)
- [Grafana Dashboards](https://grafana.com/docs/grafana/latest/dashboards/)
- [Pino Logger](https://getpino.io/)

## Next Steps
Create incident runbooks with `linear-incident-runbook`.
