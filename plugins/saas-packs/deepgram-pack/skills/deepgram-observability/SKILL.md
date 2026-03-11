---
name: deepgram-observability
description: |
  Set up comprehensive observability for Deepgram integrations with metrics, traces, and alerts.
  Use when implementing monitoring for Deepgram operations, setting up dashboards,
  or configuring alerting for Deepgram integration health.
  Trigger with phrases like "deepgram monitoring", "deepgram metrics",
  "deepgram observability", "monitor deepgram", "deepgram alerts", "deepgram tracing".
allowed-tools: Read, Write, Edit, Bash(kubectl:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Deepgram Observability

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Implement comprehensive observability for Deepgram integrations with Prometheus metrics, OpenTelemetry distributed tracing, structured JSON logging, Grafana dashboards, and AlertManager rules.

## Prerequisites
- Prometheus or compatible metrics backend
- OpenTelemetry SDK installed
- Grafana or similar dashboarding tool
- AlertManager configured

## Instructions

### Step 1: Set Up Prometheus Metrics
Define counters for requests (by status/model/type), audio processed, rate limit hits, and estimated cost. Add histograms for transcription latency. Add gauges for active connections.

### Step 2: Build Instrumented Client
Wrap Deepgram client to auto-record metrics on every transcription. Track success/error counts, latency, audio duration, and cost per model. Add OpenTelemetry span attributes.

### Step 3: Configure OpenTelemetry Tracing
Initialize NodeSDK with OTLP exporter. Set service name, version, and environment as resource attributes. Auto-instrument HTTP (excluding /health and /metrics paths).

### Step 4: Implement Structured Logging
Use Pino with JSON output, ISO timestamps, and component-specific child loggers (transcription, metrics, alerts). Include service metadata in every log line.

### Step 5: Create Grafana Dashboard
Build panels for request rate, P95 latency, audio processed per hour, error rate gauge, estimated daily cost, and active connections.

### Step 6: Configure Alert Rules
Alert on: error rate >5% (critical), P95 latency >30s (warning), rate limit hits >10/hr (warning), cost spike >2x yesterday (warning), zero requests for 15min (warning).

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for advanced patterns.

## Output
- Prometheus metrics for all Deepgram operations
- Instrumented client with auto-tracking
- OpenTelemetry distributed tracing
- Structured JSON logging
- Grafana dashboard configuration
- AlertManager rules for key thresholds

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Missing metrics | No instrumentation | Use instrumented client wrapper |
| High cardinality | Too many labels | Limit label values to known set |
| Alert storms | Wrong thresholds | Tune alert rules, add `for` duration |
| Metric gaps | Scrape failures | Check Prometheus targets |

## Examples

### Observability Pillars
| Pillar | Tool | Purpose |
|--------|------|---------|
| Metrics | Prometheus | Performance and usage tracking |
| Traces | OpenTelemetry | Request flow visibility |
| Logs | Pino (JSON) | Debugging and audit |
| Alerts | AlertManager | Incident notification |

### Key Metrics
| Metric | Type | Purpose |
|--------|------|---------|
| `deepgram_transcription_requests_total` | Counter | Request throughput |
| `deepgram_transcription_latency_seconds` | Histogram | Latency tracking |
| `deepgram_audio_processed_seconds_total` | Counter | Usage tracking |
| `deepgram_estimated_cost_dollars` | Counter | Budget monitoring |
| `deepgram_rate_limit_hits_total` | Counter | Throttling detection |

## Resources
- [Prometheus Best Practices](https://prometheus.io/docs/practices/naming/)
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Grafana Dashboard Examples](https://grafana.com/grafana/dashboards/)