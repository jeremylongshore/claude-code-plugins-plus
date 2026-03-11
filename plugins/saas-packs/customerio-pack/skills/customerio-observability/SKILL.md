---
name: customerio-observability
description: |
  Set up Customer.io monitoring and observability.
  Use when implementing metrics, logging, alerting,
  or dashboards for Customer.io integrations.
  Trigger with phrases like "customer.io monitoring", "customer.io metrics",
  "customer.io dashboard", "customer.io alerts".
allowed-tools: Read, Write, Edit, Bash(kubectl:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Customer.io Observability

## Overview
Implement comprehensive observability for Customer.io integrations including Prometheus metrics, structured logging, distributed tracing, and Grafana dashboards.

## Prerequisites
- Customer.io integration deployed
- Monitoring infrastructure (Prometheus, Grafana, etc.)
- Log aggregation system

## Key Metrics
| Metric | Type | Description |
|--------|------|-------------|
| `customerio_api_latency_ms` | Histogram | API call latency |
| `customerio_api_requests_total` | Counter | Total API requests |
| `customerio_api_errors_total` | Counter | API error count |
| `customerio_email_sent_total` | Counter | Emails sent |
| `customerio_email_bounced_total` | Counter | Email bounces |
| `customerio_webhook_received_total` | Counter | Webhooks received |

## Instructions

### Step 1: Set Up Metrics Collection
Register Prometheus counters and histograms for API latency, request counts, error counts, email delivery, and webhook events.

### Step 2: Create Instrumented Client
Wrap the Customer.io client to automatically record timing, success/error counters on every identify and track call.

### Step 3: Implement Structured Logging
Use pino for JSON structured logging with PII redaction. Log all Customer.io operations with operation type, user ID, result, and sanitized data.

### Step 4: Add Distributed Tracing
Use OpenTelemetry spans for all Customer.io operations with proper status codes and exception recording.

### Step 5: Build Grafana Dashboard
Create panels for API latency percentiles (p50/p95/p99), request rate by operation, error rate percentage, and email delivery funnel.

### Step 6: Configure Alerting Rules
Set up Prometheus alerts for high error rate (>5%), high p99 latency (>5s), high bounce rate (>5%), and webhook processing failures.

For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Error Handling
| Issue | Solution |
|-------|----------|
| Missing metrics | Check metric registration |
| High cardinality | Reduce label values |
| Log volume too high | Adjust log level |

## Resources
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)
- [OpenTelemetry Node.js](https://opentelemetry.io/docs/instrumentation/js/)

## Next Steps
After observability setup, proceed to `customerio-advanced-troubleshooting` for debugging.
