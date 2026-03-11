---
name: juicebox-observability
description: |
  Set up Juicebox monitoring and observability.
  Use when implementing logging, metrics, tracing,
  or alerting for Juicebox integrations.
  Trigger with phrases like "juicebox monitoring", "juicebox metrics",
  "juicebox logging", "juicebox observability".
allowed-tools: Read, Write, Edit, Bash(kubectl:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Juicebox Observability

## Overview
Implement comprehensive observability for Juicebox integrations including logging, metrics, tracing, and alerting.

## Prerequisites
- Observability platform (DataDog, Grafana, etc.)
- Juicebox integration running
- Access to deploy monitoring agents

## Instructions
- Step 1: Structured Logging
- Step 2: Metrics Collection
- Step 3: Distributed Tracing
- Step 4: Health Checks
- Step 5: Alerting Rules

For full implementation details and code examples, load:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Structured logging
- Prometheus metrics
- Distributed tracing
- Health checks
- Alerting rules

## Resources
- [Monitoring Guide](https://juicebox.ai/docs/monitoring)
- [OpenTelemetry](https://opentelemetry.io/)

## Next Steps
After observability, see `juicebox-incident-runbook` for incident response.
