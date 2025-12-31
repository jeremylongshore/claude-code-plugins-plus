# vercel-observability

## Skill Scaffold

```
vercel-observability/
  SKILL.md
```

## File Descriptions

### 1. SKILL.md
**Purpose:** Set up comprehensive observability with Prometheus metrics, OpenTelemetry traces, structured logging, and alerting rules.
**Workflow:** Implemented during production setup; dashboards and alerts monitored continuously.
**Relates to:** Builds on vercel-multi-env-setup; integrates with vercel-incident-runbook for response

## Summary

This skill establishes full observability for Vercel integrations. It covers Prometheus metrics (counters for requests/errors, histograms for latency, gauges for rate limits), OpenTelemetry distributed tracing with span management, structured logging with Pino, Prometheus AlertManager rules for error rate and latency thresholds, and Grafana dashboard panel queries. The goal is sub-5-minute detection time for any Vercel-related incidents.
