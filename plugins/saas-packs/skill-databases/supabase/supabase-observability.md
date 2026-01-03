# supabase-observability

## File Scaffold

```
supabase-observability/
-- SKILL.md
```

## File Descriptions

### 1. SKILL.md
**Purpose:** Set up comprehensive observability for Supabase integrations with Prometheus metrics, OpenTelemetry tracing, structured logging, and AlertManager alerts.
**Workflow:** Observability skill for production monitoring. Essential for maintaining production visibility.
**Relates to:** Follows supabase-multi-env-setup; enables supabase-incident-runbook with monitoring data.

## Summary

This skill provides a complete observability stack for Supabase integrations. It covers Prometheus metrics collection (counters, histograms, gauges), instrumented client wrapper, OpenTelemetry distributed tracing, structured logging with Pino, AlertManager alert rules for error rates and latency, and Grafana dashboard queries. Use this skill when implementing production monitoring or setting up alerting for Supabase operations.
