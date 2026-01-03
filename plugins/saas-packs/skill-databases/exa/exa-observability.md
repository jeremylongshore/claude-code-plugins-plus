# exa-observability

## Skill Scaffold

```
exa-observability/
  SKILL.md
```

## File Descriptions

### 1. SKILL.md
**Purpose:** Set up comprehensive observability with metrics, tracing, and alerting for Exa search operations.
**Workflow:** Production monitoring skill - enables proactive incident detection.
**Relates to:** Follows exa-prod-checklist; integrates with exa-incident-runbook

## Summary

This skill implements Exa observability: Prometheus/OpenMetrics for request metrics (latency, success rate, result counts), OpenTelemetry distributed tracing for request flows, structured logging with search context, alert rules (high error rate, latency degradation, rate limits), Grafana dashboard templates, custom metrics for search quality (relevance scores), and integration with PagerDuty/Opsgenie. Target: <5 minute detection time for Exa-related incidents.
