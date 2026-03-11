---
name: speak-observability
description: |
  Set up comprehensive observability for Speak integrations with metrics, traces, and alerts.
  Use when implementing monitoring for Speak operations, setting up dashboards,
  or configuring alerting for language learning feature health.
  Trigger with phrases like "speak monitoring", "speak metrics",
  "speak observability", "monitor speak", "speak alerts", "speak tracing".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Speak Observability

## Overview
Set up comprehensive observability for Speak language learning integrations.

## Prerequisites
- Prometheus or compatible metrics backend
- OpenTelemetry SDK installed
- Grafana or similar dashboarding tool
- AlertManager configured

## Instructions
1. **Key Metrics for Language Learning**
2. **Prometheus Metrics Implementation**
3. **Instrumented Speak Client**
4. **Distributed Tracing**
5. **Structured Logging**
6. **Alert Configuration**
7. **Grafana Dashboard**

For full implementation details, load: `Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Business and technical metrics
- Distributed tracing configured
- Structured logging implemented
- Alert rules deployed
- Grafana dashboard ready

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Missing metrics | No instrumentation | Wrap client calls |
| Trace gaps | Missing propagation | Check context headers |
| Alert storms | Wrong thresholds | Tune alert rules |
| High cardinality | Too many labels | Reduce label values |

## Examples
### Quick Metrics Endpoint
```typescript
app.get('/metrics', async (req, res) => {
  res.set('Content-Type', registry.contentType);
  res.send(await registry.metrics());
});
```

## Resources
- [Prometheus Best Practices](https://prometheus.io/docs/practices/naming/)
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Speak Observability Guide](https://developer.speak.com/docs/observability)

## Next Steps
For incident response, see `speak-incident-runbook`.