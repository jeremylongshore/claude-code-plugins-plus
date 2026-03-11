---
name: evernote-observability
description: |
  Implement observability for Evernote integrations.
  Use when setting up monitoring, logging, tracing,
  or alerting for Evernote applications.
  Trigger with phrases like "evernote monitoring", "evernote logging",
  "evernote metrics", "evernote observability".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Evernote Observability

## Overview
Comprehensive observability setup for Evernote integrations including metrics, logging, tracing, and alerting.

## Prerequisites
- Monitoring infrastructure (Prometheus, Datadog, etc.)
- Log aggregation (ELK, CloudWatch, etc.)
- Alerting system

## Instructions

### Step 1: Metrics Collection

### Step 2: Instrumented Client

### Step 3: Structured Logging

### Step 4: Distributed Tracing

### Step 5: Health and Readiness Endpoints

### Step 6: Alert Rules

### Step 7: Grafana Dashboard

For full implementation details and code examples, load:
`references/implementation-guide.md`

## Output
- Prometheus metrics collection
- Instrumented Evernote client
- Structured JSON logging
- Distributed tracing with OpenTelemetry
- Health check endpoints
- Prometheus alert rules

## Resources
- [Prometheus](https://prometheus.io/docs/)
- [OpenTelemetry](https://opentelemetry.io/docs/)
- [Grafana](https://grafana.com/docs/)

## Next Steps
For incident handling, see `evernote-incident-runbook`.

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Authentication failure | Invalid or expired credentials | Refresh tokens or re-authenticate with monitoring |
| Configuration conflict | Incompatible settings detected | Review and resolve conflicting parameters |
| Resource not found | Referenced resource missing | Verify resource exists and permissions are correct |

## Examples

**Basic usage**: Apply evernote observability to a standard project setup with default configuration options.

**Advanced scenario**: Customize evernote observability for production environments with multiple constraints and team-specific requirements.