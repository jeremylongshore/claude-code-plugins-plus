---
name: langfuse-observability
description: |
  Set up comprehensive observability for Langfuse with metrics, dashboards, and alerts.
  Use when implementing monitoring for LLM operations, setting up dashboards,
  or configuring alerting for Langfuse integration health.
  Trigger with phrases like "langfuse monitoring", "langfuse metrics",
  "langfuse observability", "monitor langfuse", "langfuse alerts", "langfuse dashboard".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Langfuse Observability

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Set up comprehensive observability for Langfuse integrations with Prometheus metrics, an instrumented SDK wrapper, Grafana dashboards, and AlertManager rules.

## Prerequisites
- Prometheus or compatible metrics backend
- Grafana or similar dashboarding tool
- AlertManager or PagerDuty configured
- Langfuse SDK integrated

## Instructions

### Step 1: Implement Prometheus Metrics
Define counters (traces, generations, tokens, cost, errors), histograms (generation duration, flush latency), and gauges (pending events).

### Step 2: Create Instrumented Wrapper
Wrap the Langfuse client to automatically record metrics on trace creation, generation start/end, token usage, and cost calculation.

### Step 3: Expose Metrics Endpoint
Create `/metrics` endpoint returning Prometheus format from the shared registry.

### Step 4: Configure Prometheus Scraping
Add scrape job targeting your app's metrics endpoint at 15s intervals.

### Step 5: Create Grafana Dashboard
Build panels for request rate, latency percentiles, token usage, cost/hour, and error rate.

### Step 6: Configure Alerts
Set rules for high error rate (>5%), high latency (P95 >10s), projected daily cost (>$100), and flush backlog (>1000).

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for advanced patterns.

## Output
- Prometheus metrics for all Langfuse operations
- Instrumented Langfuse wrapper with auto-tracking
- Grafana dashboard configuration
- AlertManager rules for key thresholds

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Missing metrics | No instrumentation | Use wrapped client |
| High cardinality | Too many labels | Limit label values |
| Alert storms | Wrong thresholds | Tune alert rules |
| Metric gaps | Scrape failures | Check Prometheus targets |

## Examples

### Key Metrics Reference
| Metric | Type | Purpose |
|--------|------|---------|
| `langfuse_generations_total` | Counter | LLM throughput |
| `langfuse_generation_duration_seconds` | Histogram | Latency tracking |
| `langfuse_tokens_total` | Counter | Usage tracking |
| `langfuse_cost_usd_total` | Counter | Budget monitoring |
| `langfuse_errors_total` | Counter | Reliability |

## Resources
- [Prometheus Best Practices](https://prometheus.io/docs/practices/naming/)
- [Grafana Dashboards](https://grafana.com/docs/grafana/latest/dashboards/)
- [Langfuse Analytics](https://langfuse.com/docs/analytics)