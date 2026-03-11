---
name: openevidence-observability
description: |
  Set up comprehensive observability for OpenEvidence integrations with metrics, traces, and alerts.
  Use when implementing monitoring for clinical AI operations, setting up dashboards,
  or configuring alerting for healthcare application health.
  Trigger with phrases like "openevidence monitoring", "openevidence metrics",
  "openevidence observability", "monitor openevidence", "openevidence alerts".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# OpenEvidence Observability

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Set up comprehensive observability for OpenEvidence clinical AI integrations with Prometheus metrics, OpenTelemetry tracing, structured logging with PHI redaction, and Grafana dashboards.

## Prerequisites
- Prometheus or compatible metrics backend
- OpenTelemetry SDK installed
- Grafana or similar dashboarding tool
- AlertManager or PagerDuty configured

## Key Metrics

| Metric | Type | Alert Threshold |
|--------|------|-----------------|
| `openevidence_requests_total` | Counter | N/A |
| `openevidence_request_duration_seconds` | Histogram | P95 > 15s |
| `openevidence_errors_total` | Counter | > 5% error rate |
| `openevidence_cache_hits_total` | Counter | < 50% hit rate |
| `openevidence_rate_limit_remaining` | Gauge | < 10% headroom |
| `openevidence_deepconsult_active` | Gauge | > 50 concurrent |

## Instructions

### Step 1: Set Up Prometheus Metrics
Register counters (requests, errors, cache hits/misses), histograms (request duration, DeepConsult duration), gauges (rate limit remaining), and summaries (confidence scores) with appropriate labels.

### Step 2: Instrument Client Wrapper
Wrap OpenEvidence client with metrics collection, cache hit/miss tracking, rate limit monitoring from response headers, and confidence score recording.

### Step 3: Configure Distributed Tracing
Initialize OpenTelemetry with Google Cloud Trace exporter, HTTP and Express instrumentations, and service metadata.

### Step 4: Set Up Structured Logging
Use pino with PHI redaction (patient.*, patientId, mrn, *.ssn) and OpenEvidence-specific child logger for clinical queries and DeepConsult events.

### Step 5: Define Alert Rules
Create Prometheus alerts for: high error rate (>5% warning, >20% critical), high P95 latency (>15s), low cache hit rate (<50%), rate limit warning (<10 remaining), service down.

### Step 6: Build Grafana Dashboard
Create panels for request rate, error rate gauge, latency heatmap, cache hit rate timeseries, rate limit gauge, and confidence score distribution.

## Output
- Prometheus metrics collection with `/metrics` endpoint
- Instrumented client wrapper with tracing
- Distributed tracing (OpenTelemetry + Cloud Trace)
- Structured logging with PHI redaction
- Alert rules for critical conditions
- Grafana dashboard JSON

## Error Handling
| Issue | Detection | Resolution |
|-------|-----------|------------|
| Metrics endpoint down | Prometheus scrape failure | Check `/metrics` route registration |
| Missing traces | No spans in Cloud Trace | Verify OpenTelemetry SDK initialization |
| PHI in logs | Audit review | Add patterns to pino redact config |
| Alert fatigue | Too many alerts | Adjust thresholds, add `for` durations |

## Examples

### Metrics Endpoint
```typescript
router.get('/metrics', async (req, res) => {
  res.set('Content-Type', registry.contentType);
  res.send(await registry.metrics());
});
```

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for advanced patterns.

## Resources
- [Prometheus Best Practices](https://prometheus.io/docs/practices/naming/)
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Grafana Dashboards](https://grafana.com/docs/grafana/latest/dashboards/)