---
name: maintainx-observability
description: |
  Implement comprehensive observability for MaintainX integrations.
  Use when setting up monitoring, logging, tracing, and alerting
  for MaintainX API integrations.
  Trigger with phrases like "maintainx monitoring", "maintainx logging",
  "maintainx metrics", "maintainx observability", "maintainx alerts".
allowed-tools: Read, Write, Edit, Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# MaintainX Observability

## Overview
Implement comprehensive observability (metrics, logging, tracing) for MaintainX integrations to ensure reliability and quick issue resolution.

## Prerequisites
- MaintainX integration deployed
- Monitoring platform (Datadog, Prometheus, CloudWatch)
- Log aggregation solution

## Instructions
Follow these high-level steps to implement maintainx-observability:

1. Review the prerequisites and ensure your environment is configured
2. Follow the detailed implementation guide for step-by-step code examples
3. Validate your implementation against the output checklist below

For full implementation details, load: `Read(plugins/saas-packs/maintainx-pack/skills/maintainx-observability/references/implementation-guide.md)`

## Output
- Prometheus metrics collection
- Structured JSON logging
- Distributed tracing setup
- Health check endpoints
- Alerting rules configured
- Dashboard definition

## Error Handling
| Issue | Solution |
|-------|----------|
| 401 Unauthorized | Verify API key in environment variables |
| 429 Rate Limited | Implement exponential backoff, reduce request frequency |
| 500 Server Error | Retry with backoff, check MaintainX status page |

## Resources
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)
- [MaintainX API Documentation](https://maintainx.dev/)

## Next Steps
For incident response, see `maintainx-incident-runbook`.
