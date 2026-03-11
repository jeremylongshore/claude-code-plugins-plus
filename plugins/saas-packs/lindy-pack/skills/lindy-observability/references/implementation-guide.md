# Lindy Observability - Implementation Guide

# Lindy AI Observability

## Overview
Monitor Lindy AI agent execution health, automation success rates, and response latency. Key observability signals for Lindy include agent run duration, step-level success/failure within multi-step automations, trigger frequency (how often agents are invoked), and per-agent cost tracking based on Lindy's per-agent pricing model where each active agent incurs a fixed monthly cost.

## Prerequisites
- Lindy Team or Enterprise workspace
- API access with a valid `LINDY_API_KEY`
- External monitoring stack (Prometheus/Grafana, Datadog, or similar)

## Instructions

### Step 1: Poll Agent Run Status via API
```bash
# List recent runs for all agents, sorted by recency
curl "https://api.lindy.ai/v1/runs?limit=50&sort=-created_at" \
  -H "Authorization: Bearer $LINDY_API_KEY" | \
  jq '.runs[] | {agent_name, run_id, status, duration_ms, steps_completed, steps_failed, created_at}'
```

### Step 2: Emit Metrics from Run Data
```typescript
// lindy-metrics-exporter.ts
async function exportLindyMetrics() {
  const res = await fetch('https://api.lindy.ai/v1/runs?limit=100&since=1h', {
    headers: { Authorization: `Bearer ${process.env.LINDY_API_KEY}` },
  });
  const { runs } = await res.json();

  for (const run of runs) {
    emitCounter('lindy_runs_total', 1, { agent: run.agent_name, status: run.status });
    emitHistogram('lindy_run_duration_ms', run.duration_ms, { agent: run.agent_name });
    if (run.steps_failed > 0) {
      emitCounter('lindy_step_failures_total', run.steps_failed, { agent: run.agent_name });
    }
  }
}

// Run every 60 seconds
setInterval(exportLindyMetrics, 60_000);
```

### Step 3: Set Up Webhook-Based Real-Time Monitoring
Configure Lindy webhooks to push events on agent run completion:
```bash
curl -X POST https://api.lindy.ai/v1/webhooks \
  -H "Authorization: Bearer $LINDY_API_KEY" \
  -d '{
    "url": "https://hooks.company.com/lindy",
    "events": ["run.completed", "run.failed", "agent.error"],
    "secret": "whsec_your_signing_secret"
  }'
```

### Step 4: Alert on Agent Failures
```yaml
groups:
  - name: lindy
    rules:
      - alert: LindyAgentFailureRate
        expr: rate(lindy_runs_total{status="failed"}[15m]) / rate(lindy_runs_total[15m]) > 0.1
        for: 10m
        annotations: { summary: "Lindy agent failure rate exceeds 10%" }
      - alert: LindyAgentSlow
        expr: histogram_quantile(0.95, rate(lindy_run_duration_ms_bucket[15m])) > 30000
        annotations: { summary: "Lindy agent P95 latency exceeds 30 seconds" }
      - alert: LindyAgentInactive
        expr: lindy_runs_total == 0 and time() - lindy_last_run_timestamp > 3600
        annotations: { summary: "No Lindy agent runs in the last hour (expected continuous)" }
```

### Step 5: Build a Dashboard
Key panels: agent run success/failure rate (stacked bar), run duration p50/p95 by agent, step failure heatmap (which steps fail most), trigger frequency (runs/hour), and active agent count vs billing (since Lindy charges per active agent).

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Webhook not delivering | Endpoint returning non-2xx | Fix endpoint, check Lindy webhook logs |
| Run duration spike | Downstream API slow in agent step | Check step-level timing in run details |
| Agent marked inactive | No triggers firing | Verify trigger configuration (schedule, webhook, email) |
| Metrics exporter missing data | API rate limit on `/runs` | Reduce polling frequency, use webhooks instead |

## Examples
```bash
# Quick health check: agent success rate over last 24h
curl -s "https://api.lindy.ai/v1/runs?since=24h" \
  -H "Authorization: Bearer $LINDY_API_KEY" | \
  jq '{total: (.runs | length), failed: ([.runs[] | select(.status=="failed")] | length)}' | \
  jq '{total, failed, success_rate: (1 - .failed/.total) * 100}'
```
