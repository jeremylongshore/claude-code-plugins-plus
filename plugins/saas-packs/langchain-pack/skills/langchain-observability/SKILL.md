---
name: langchain-observability
description: |
  Set up comprehensive observability for LangChain integrations.
  Use when implementing monitoring, setting up dashboards,
  or configuring alerting for LangChain application health.
  Trigger with phrases like "langchain monitoring", "langchain metrics",
  "langchain observability", "langchain tracing", "langchain alerts".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# LangChain Observability

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Set up comprehensive observability for LangChain applications with LangSmith, OpenTelemetry, Prometheus, and structured logging.

## Prerequisites
- LangChain application in staging/production
- LangSmith account (optional but recommended)
- Prometheus/Grafana infrastructure
- OpenTelemetry collector (optional)

## Instructions

### Step 1: Enable LangSmith Tracing
Set `LANGCHAIN_TRACING_V2=true` and configure `LANGCHAIN_API_KEY` and `LANGCHAIN_PROJECT` environment variables. All chains are automatically traced.

### Step 2: Add Prometheus Metrics
Create a `PrometheusCallback` handler that tracks `langchain_llm_requests_total`, `langchain_llm_latency_seconds`, and `langchain_llm_tokens_total` counters/histograms.

### Step 3: Integrate OpenTelemetry
Use `OTLPSpanExporter` with a custom `OpenTelemetryCallback` to add spans for chain and LLM operations with parent-child relationships.

### Step 4: Configure Structured Logging
Use `structlog` with a `StructuredLoggingCallback` to emit JSON logs for all LLM start/end/error events.

### Step 5: Set Up Grafana Dashboard
Create panels for request rate, P95 latency, token usage, and error rate using Prometheus queries.

### Step 6: Configure Alerting Rules
Define Prometheus alerts for high error rate (>5%), high latency (P95 >5s), and token budget exceeded.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for complete callback code, dashboard JSON, and alert rules.

## Output
- LangSmith tracing enabled
- Prometheus metrics exported
- OpenTelemetry spans
- Structured logging
- Grafana dashboard and alerts

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Missing metrics | Callback not attached | Pass callback to LLM constructor |
| Trace gaps | Missing context propagation | Check parent span handling |
| Alert storms | Thresholds too sensitive | Tune `for` duration and thresholds |

## Examples
```python
# Quick setup with all callbacks
tracker = PrometheusCallback()
llm = ChatOpenAI(model="gpt-4o-mini", callbacks=[tracker])
response = llm.invoke("Hello!")
print(tracker.report())
```

## Resources
- [LangSmith Documentation](https://docs.smith.langchain.com/)
- [OpenTelemetry Python](https://opentelemetry.io/docs/languages/python/)
- [Prometheus Python Client](https://prometheus.io/docs/instrumenting/clientlibs/)

## Next Steps
Use `langchain-incident-runbook` for incident response procedures.
