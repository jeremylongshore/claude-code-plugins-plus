---
name: lindy-observability
description: |
  Implement observability for Lindy AI integrations.
  Use when setting up monitoring, logging, tracing,
  or building dashboards for Lindy operations.
  Trigger with phrases like "lindy monitoring", "lindy observability",
  "lindy metrics", "lindy logging", "lindy tracing".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Lindy AI Observability

## Overview
Monitor Lindy AI agent execution health, automation success rates, and response latency. Key observability signals for Lindy include agent run duration, step-level success/failure within multi-step automations, trigger frequency (how often agents are invoked), and per-agent cost tracking based on Lindy's per-agent pricing model where each active agent incurs a fixed monthly cost.

## Prerequisites
- Lindy Team or Enterprise workspace
- API access with a valid `LINDY_API_KEY`
- External monitoring stack (Prometheus/Grafana, Datadog, or similar)

## Instructions

### Step 1: Poll Agent Run Status via API

### Step 2: Emit Metrics from Run Data

### Step 3: Set Up Webhook-Based Real-Time Monitoring
Configure Lindy webhooks to push events on agent run completion:

### Step 4: Alert on Agent Failures

### Step 5: Build a Dashboard
Key panels: agent run success/failure rate (stacked bar), run duration p50/p95 by agent, step failure heatmap (which steps fail most), trigger frequency (runs/hour), and active agent count vs billing (since Lindy charges per active agent).


For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Webhook not delivering | Endpoint returning non-2xx | Fix endpoint, check Lindy webhook logs |
| Run duration spike | Downstream API slow in agent step | Check step-level timing in run details |
| Agent marked inactive | No triggers firing | Verify trigger configuration (schedule, webhook, email) |
| Metrics exporter missing data | API rate limit on `/runs` | Reduce polling frequency, use webhooks instead |

## Examples


**Basic usage**: Apply lindy observability to a standard project setup with default configuration options.

**Advanced scenario**: Customize lindy observability for production environments with multiple constraints and team-specific requirements.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

See [monitoring implementation details](${CLAUDE_SKILL_DIR}/references/implementation.md) for output format specifications.

## Resources

- Official monitoring documentation
- Community best practices and patterns
- Related skills in this plugin pack