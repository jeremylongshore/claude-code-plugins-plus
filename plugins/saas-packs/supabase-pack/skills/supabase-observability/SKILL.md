---
name: supabase-observability
description: |
  Execute set up comprehensive observability for Supabase integrations with metrics, traces, and alerts.
  Use when implementing monitoring for Supabase operations, setting up dashboards,
  or configuring alerting for Supabase integration health.
  Trigger with phrases like "supabase monitoring", "supabase metrics",
  "supabase observability", "monitor supabase", "supabase alerts", "supabase tracing".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Supabase Observability

## Prerequisites
- Prometheus or compatible metrics backend
- OpenTelemetry SDK installed
- Grafana or similar dashboarding tool
- AlertManager configured

## Instructions

### Step 1: Set Up Metrics Collection
Implement Prometheus counters, histograms, and gauges for key operations.

### Step 2: Add Distributed Tracing
Integrate OpenTelemetry for end-to-end request tracing.

### Step 3: Configure Structured Logging
Set up JSON logging with consistent field names.

### Step 4: Create Alert Rules
Define Prometheus alerting rules for error rates and latency.

## Output
- Metrics collection enabled
- Distributed tracing configured
- Structured logging implemented
- Alert rules deployed

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources
- [Prometheus Best Practices](https://prometheus.io/docs/practices/naming/)
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Supabase Observability Guide](https://supabase.com/docs/observability)
