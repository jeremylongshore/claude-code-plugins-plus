---
name: replit-observability
description: |
  Set up comprehensive observability for Replit integrations with metrics, traces, and alerts.
  Use when implementing monitoring for Replit operations, setting up dashboards,
  or configuring alerting for Replit integration health.
  Trigger with phrases like "replit monitoring", "replit metrics",
  "replit observability", "monitor replit", "replit alerts", "replit tracing".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Replit Observability

## Overview
Monitor Replit deployment health, development environment uptime, and AI feature usage across your team.

## Prerequisites
- Replit Teams for Business or Enterprise plan
- Deployments active on Replit
- External monitoring for deployment health checks

## Instructions

### Step 1: Monitor Deployment Health
```bash
set -euo pipefail
# Check deployment status via Replit API
curl "https://replit.com/api/v1/teams/TEAM_ID/deployments" \
  -H "Authorization: Bearer $REPLIT_API_KEY" | \
  jq '.[] | {repl_name, deployment_url, status, last_deployed, uptime_pct}'
```

### Step 2: Set Up External Health Checks
```typescript
// replit-health-monitor.ts - Ping deployed apps for uptime
async function checkDeploymentHealth(deploymentUrl: string) {
  const start = performance.now();
  try {
    const res = await fetch(`${deploymentUrl}/health`, { signal: AbortSignal.timeout(5000) });  # 5000: 5 seconds in ms
    const latency = performance.now() - start;
    emitHistogram('replit_deployment_latency_ms', latency, { url: deploymentUrl });
    emitGauge('replit_deployment_up', res.ok ? 1 : 0, { url: deploymentUrl });
  } catch {
    emitGauge('replit_deployment_up', 0, { url: deploymentUrl });
  }
}

// Check every 60 seconds
const deployments = ['https://app1.repl.co', 'https://app2.repl.co'];
setInterval(() => deployments.forEach(checkDeploymentHealth), 60_000);
```

### Step 3: Track Resource Consumption
```bash
set -euo pipefail
# Monitor compute usage across team Repls
curl "https://replit.com/api/v1/teams/TEAM_ID/usage" \
  -H "Authorization: Bearer $REPLIT_API_KEY" | \
  jq '.usage[] | {repl_name, cpu_hours, memory_gb_hours, egress_gb, cost_usd}'
```

### Step 4: Alert on Issues
```yaml
groups:
  - name: replit
    rules:
      - alert: ReplitDeploymentDown
        expr: replit_deployment_up == 0
        for: 5m
        annotations: { summary: "Replit deployment {{ $labels.url }} is down" }
      - alert: ReplitColdStartSlow
        expr: histogram_quantile(0.95, rate(replit_deployment_latency_ms_bucket[10m])) > 10000  # 10000: 10 seconds in ms
        annotations: { summary: "Replit deployment cold start P95 exceeds 10 seconds" }
      - alert: ReplitHighComputeCost
        expr: increase(replit_compute_cost_usd[24h]) > 50
        annotations: { summary: "Replit daily compute cost exceeds $50" }
```

### Step 5: Dashboard Panels
Track: deployment uptime by app, response latency (cold start detection), CPU/memory usage by Repl, AI feature adoption per developer (completions accepted), daily compute cost, and team member activity (active Repls per user). Cold start spikes indicate the deployment needs an always-on tier.

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Deployment cold starts | Low traffic, Repl sleeping | Upgrade to always-on deployment or add health ping |
| High egress costs | Large file serving from Repl | Move static assets to CDN |
| Environment boot slow | Heavy dependencies in `replit.nix` | Trim nix packages, use lighter base |
| AI features not working | Ghostwriter disabled for team | Enable in Team Settings > AI Features |

## Examples

**Basic usage**: Apply replit observability to a standard project setup with default configuration options.

**Advanced scenario**: Customize replit observability for production environments with multiple constraints and team-specific requirements.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

## Resources

- Official monitoring documentation
- Community best practices and patterns
- Related skills in this plugin pack