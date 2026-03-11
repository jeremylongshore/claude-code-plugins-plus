---
name: apollo-observability
description: |
  Set up Apollo.io monitoring and observability.
  Use when implementing logging, metrics, tracing, and alerting
  for Apollo integrations.
  Trigger with phrases like "apollo monitoring", "apollo metrics",
  "apollo observability", "apollo logging", "apollo alerts".
allowed-tools: Read, Write, Edit, Bash(kubectl:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Apollo Observability

## Overview
Comprehensive observability setup for Apollo.io integrations including metrics, logging, tracing, and alerting.

## Prerequisites
- Valid Apollo.io API credentials
- Node.js 18+ or Python 3.10+
- Completed `apollo-install-auth` setup

## Instructions
Follow these high-level steps to implement apollo-observability:

1. Review the prerequisites and ensure your environment is configured
2. Follow the detailed implementation guide for step-by-step code examples
3. Validate your implementation against the output checklist below

For full implementation details, load: `Read(plugins/saas-packs/apollo-pack/skills/apollo-observability/references/implementation-guide.md)`

## Output
- Prometheus metrics for all Apollo operations
- Structured JSON logging with PII redaction
- OpenTelemetry distributed tracing
- Alerting rules for errors, rate limits, latency
- Grafana dashboard configuration
- Health check endpoints

## Error Handling
| Issue | Resolution |
|-------|------------|
| Missing metrics | Verify instrumentation |
| Alert noise | Tune thresholds |
| Log volume | Adjust log levels |
| Trace gaps | Check propagation |

## Resources
- [Prometheus Documentation](https://prometheus.io/docs/)
- [OpenTelemetry](https://opentelemetry.io/)
- [Grafana Dashboards](https://grafana.com/grafana/dashboards/)
- [Pino Logger](https://getpino.io/)

## Next Steps
Proceed to `apollo-incident-runbook` for incident response.

## Examples

**Basic usage**: Apply apollo observability to a standard project setup with default configuration options.

**Advanced scenario**: Customize apollo observability for production environments with multiple constraints and team-specific requirements.