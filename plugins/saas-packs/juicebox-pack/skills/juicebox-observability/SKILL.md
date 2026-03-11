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
1. Step 1: Structured Logging
2. Step 2: Metrics Collection
3. Step 3: Distributed Tracing
4. Step 4: Health Checks
5. Step 5: Alerting Rules

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

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Authentication failure | Invalid or expired credentials | Refresh tokens or re-authenticate with monitoring |
| Configuration conflict | Incompatible settings detected | Review and resolve conflicting parameters |
| Resource not found | Referenced resource missing | Verify resource exists and permissions are correct |

## Examples

**Basic usage**: Apply juicebox observability to a standard project setup with default configuration options.

**Advanced scenario**: Customize juicebox observability for production environments with multiple constraints and team-specific requirements.