---
name: documenso-observability
description: |
  Implement monitoring, logging, and tracing for Documenso integrations.
  Use when setting up observability, implementing metrics collection,
  or debugging production issues.
  Trigger with phrases like "documenso monitoring", "documenso metrics",
  "documenso logging", "documenso tracing", "documenso observability".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Documenso Observability

## Overview
Implement comprehensive observability for Documenso integrations including metrics, logging, and distributed tracing.

## Prerequisites
- Working Documenso integration
- Monitoring platform (Datadog, Prometheus, etc.)
- Logging infrastructure (ELK, CloudWatch, etc.)
- Tracing system (Jaeger, Zipkin, etc.)

## Instructions

### Step 1: Metrics Collection
// src/observability/metrics.ts
### Step 2: Structured Logging
// src/observability/logger.ts
### Step 3: Distributed Tracing
// src/observability/tracing.ts
### Step 4: Health Check Endpoint
// src/api/health.ts
### Step 5: Alerting Rules
groups:
### Step 6: Grafana Dashboard
{

For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Metrics Collection
- Structured Logging
- Distributed Tracing
- Health Check Endpoint
- Alerting Rules
- Grafana Dashboard

## Error Handling
| Observability Issue | Cause | Solution |
|--------------------|-------|----------|
| Metrics not showing | Wrong scrape config | Check Prometheus config |
| Logs not appearing | Log level too high | Set LOG_LEVEL=debug |
| Traces missing | OTEL not initialized | Call initTracing() |
| High cardinality | Too many labels | Reduce label values |

## Resources
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Structured Logging](https://www.structlog.org/)

## Next Steps
For incident response, see `documenso-incident-runbook`.

## Examples

**Basic usage**: Apply documenso observability to a standard project setup with default configuration options.

**Advanced scenario**: Customize documenso observability for production environments with multiple constraints and team-specific requirements.