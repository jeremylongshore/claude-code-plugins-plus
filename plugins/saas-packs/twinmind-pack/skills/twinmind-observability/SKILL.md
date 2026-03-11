---
name: twinmind-observability
description: |
  Set up comprehensive observability for TwinMind integrations with metrics, traces, and alerts.
  Use when implementing monitoring for TwinMind operations, setting up dashboards,
  or configuring alerting for meeting AI integration health.
  Trigger with phrases like "twinmind monitoring", "twinmind metrics",
  "twinmind observability", "monitor twinmind", "twinmind alerts", "twinmind tracing".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# TwinMind Observability

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Set up comprehensive observability for TwinMind integrations including Prometheus metrics, OpenTelemetry distributed tracing, structured logging, AlertManager rules, and Grafana dashboards.

## Prerequisites
- Prometheus or compatible metrics backend
- OpenTelemetry SDK installed
- Grafana or similar dashboarding tool
- AlertManager configured

## Instructions

### Step 1: Define Key Metrics
Register Prometheus counters (transcriptions_total, errors_total, api_requests_total, ai_tokens_used), histograms (transcription_duration_seconds, api_latency_seconds), and gauges (rate_limit_remaining).

### Step 2: Instrument the TwinMind Client
Wrap all API calls in an `InstrumentedTwinMindClient` that records metrics on every request: increment counters, observe latency histograms, update rate limit gauges from response headers.

### Step 3: Add Distributed Tracing
Configure OpenTelemetry SDK with OTLP exporter. Create a `TracedTwinMindClient` that wraps operations in spans with attributes like `twinmind.model`, `twinmind.audio_url`, `twinmind.transcript_id`.

### Step 4: Implement Structured Logging
Use Pino with automatic redaction of sensitive fields (apiKey, authorization, password). Log operation name, duration, and context for all TwinMind calls.

### Step 5: Configure Alert Rules
Create AlertManager rules for: high error rate (>5%), high latency (P95 >5s), transcription failures, rate limit approaching/exceeded, API down, and high token usage.

### Step 6: Build Grafana Dashboard
Configure panels for transcription rate by status, API latency percentiles (P50/P95/P99), error rate by type, rate limit gauge, audio hours processed, and AI tokens used.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for complete Prometheus metrics, OpenTelemetry setup, alert rules YAML, and Grafana dashboard JSON.

## Output
- Prometheus metrics implementation
- Distributed tracing with OpenTelemetry
- Structured logging with Pino
- AlertManager rules
- Grafana dashboard configuration
- Metrics endpoint

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Missing metrics | No instrumentation | Wrap client calls |
| Trace gaps | Missing propagation | Check context headers |
| Alert storms | Wrong thresholds | Tune alert rules |
| High cardinality | Too many labels | Reduce label values |

## Examples
```typescript
// Instrumented transcription
const result = await instrumentedClient.transcribe(audioUrl, { model: 'ear-3' });
// Automatically records: transcription counter, duration histogram, audio hours

// Traced operation
const transcript = await tracedOperation('transcribe',
  () => client.transcribe(audioUrl),
  { 'twinmind.model': 'ear-3' }
);
```

## Resources
- [Prometheus Best Practices](https://prometheus.io/docs/practices/naming/)
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Grafana Dashboard Examples](https://grafana.com/grafana/dashboards/)

## Next Steps
For incident response, see `twinmind-incident-runbook`.
