---
name: lindy-observability
description: |
  Monitor Lindy AI agent health, task success rates, and credit consumption.
  Use when setting up monitoring, building dashboards, configuring alerts,
  or tracking agent performance over time.
  Trigger with phrases like "lindy monitoring", "lindy observability",
  "lindy metrics", "lindy logging", "lindy dashboard".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, lindy, monitoring, observability, dashboard]

---
# Lindy Observability

## Overview
Monitor Lindy AI agent execution health, task completion rates, step-level failures,
trigger frequency, and credit consumption. Lindy provides built-in task history in
the dashboard. External observability requires webhook callbacks, the Task Completed
trigger, and application-side metrics collection.

## Prerequisites
- Lindy workspace with active agents
- For external monitoring: webhook receiver + metrics stack (Prometheus/Grafana, Datadog)
- For alerts: Slack or email integration configured

## Key Observability Signals

| Signal | Source | Why It Matters |
|--------|--------|---------------|
| Task completion rate | Tasks tab / callback | Measures agent reliability |
| Task duration | Task detail view | Tracks performance over time |
| Step failure rate | Task detail (red steps) | Identifies broken actions |
| Credit consumption | Billing dashboard | Budget tracking |
| Trigger frequency | Task count over time | Detects trigger storms |
| Agent error rate | Failed tasks / total tasks | Overall health indicator |

## Instructions

### Step 1: Dashboard Monitoring (Built-In)
Lindy's Tasks tab provides per-agent monitoring:
1. Open agent > **Tasks** tab
2. Filter by status: **Completed**, **Failed**, **In Progress**
3. For failed tasks: click to see which step failed and why
4. Track patterns: same step failing? same time of day? same trigger type?

### Step 2: Task Completed Trigger (Agent-to-Agent Monitoring)
Use Lindy's built-in **Task Completed** trigger to build an observability agent:

```
Monitoring Agent:
  Trigger: Task Completed (from Production Support Agent)
  Condition: "Go down this path if the task failed"
    → Action: Slack Send Channel Message to #ops-alerts
      Message: "Support Agent task failed: {{task.error}}"
  Condition: "Go down this path if task duration > 30 seconds"
    → Action: Slack Send Channel Message to #ops-alerts
      Message: "Support Agent slow: {{task.duration}}s"
```

### Step 3: Webhook-Based Metrics Collection
Configure agents to call your metrics endpoint on task completion:

```typescript
// metrics-collector.ts — Receive agent metrics via HTTP Request action
import express from 'express';
import { Counter, Histogram, Gauge } from 'prom-client';

const app = express();
app.use(express.json());

// Prometheus metrics
const taskCounter = new Counter({
  name: 'lindy_tasks_total',
  help: 'Total Lindy agent tasks',
  labelNames: ['agent', 'status'],
});

const taskDuration = new Histogram({
  name: 'lindy_task_duration_seconds',
  help: 'Lindy task execution duration',
  labelNames: ['agent'],
  buckets: [1, 2, 5, 10, 30, 60, 120],
});

const creditGauge = new Gauge({
  name: 'lindy_credits_consumed',
  help: 'Credits consumed per task',
  labelNames: ['agent'],
});

// Receive metrics from Lindy HTTP Request action
app.post('/lindy/metrics', (req, res) => {
  const auth = req.headers.authorization;
  if (auth !== `Bearer ${process.env.LINDY_WEBHOOK_SECRET}`) {
    return res.status(401).json({ error: 'Unauthorized' });
  }

  const { agent, status, duration, credits } = req.body;

  taskCounter.inc({ agent, status });
  taskDuration.observe({ agent }, duration);
  creditGauge.set({ agent }, credits);

  res.json({ recorded: true });
});

// Prometheus scrape endpoint
app.get('/metrics', async (req, res) => {
  res.set('Content-Type', 'text/plain');
  res.send(await register.metrics());
});
```

**Lindy agent configuration**:
Add an HTTP Request action as the last step in each monitored agent:
- **URL**: `https://monitoring.yourapp.com/lindy/metrics`
- **Method**: POST
- **Body** (Set Manually):
  ```json
  {
    "agent": "support-bot",
    "status": "{{task.status}}",
    "duration": "{{task.duration}}",
    "credits": "{{task.credits}}"
  }
  ```

### Step 4: Grafana Dashboard Panels
Key panels for a Lindy monitoring dashboard:

| Panel | Metric | Type |
|-------|--------|------|
| Task Success Rate | `rate(lindy_tasks_total{status="completed"}[1h])` | Percentage gauge |
| Task Failures | `rate(lindy_tasks_total{status="failed"}[1h])` | Counter |
| Duration p50/p95 | `histogram_quantile(0.95, lindy_task_duration_seconds)` | Time series |
| Credit Burn Rate | `rate(lindy_credits_consumed[1h])` | Counter |
| Active Agents | Count of agents with tasks in last 24h | Stat panel |
| Trigger Frequency | Tasks per hour by agent | Bar chart |

### Step 5: Alert Rules
```yaml
# Prometheus alert rules
groups:
  - name: lindy
    rules:
      - alert: LindyAgentHighFailureRate
        expr: rate(lindy_tasks_total{status="failed"}[30m]) > 0.1
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Lindy agent {{ $labels.agent }} failure rate > 10%"

      - alert: LindyAgentDown
        expr: absent(lindy_tasks_total{agent="support-bot"}[1h])
        for: 30m
        labels:
          severity: critical
        annotations:
          summary: "No tasks from support-bot in 1 hour"

      - alert: LindyCreditsBurnRate
        expr: rate(lindy_credits_consumed[1h]) * 720 > 5000
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "Credit burn rate will exhaust monthly budget"
```

### Step 6: Evals (Built-In Quality Monitoring)
Use Lindy Evals to catch quality regressions:
1. Click the test tube icon below any agent step
2. Define scoring criteria (LLM-as-judge):
   ```
   Score 1 (pass) if the response is professional, accurate, and under 200 words.
   Score 0 (fail) if the response contains hallucinations or exceeds 200 words.
   ```
3. Run evals against historical task data
4. Track scores over time to detect quality drift

**Note**: Eval runs consume credits but do NOT execute real actions (safe simulation).

## Observability Maturity Levels

| Level | What You Monitor | How |
|-------|-----------------|-----|
| L0 | Nothing | Manual dashboard checks |
| L1 | Task failures | Task Completed trigger + Slack alerts |
| L2 | Success rate + duration | HTTP Request action + Prometheus |
| L3 | Credit burn + quality | Evals + Grafana dashboards |
| L4 | Automated remediation | Monitoring agent auto-restarts failed agents |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Metrics endpoint down | Monitoring server crashed | Alert on scrape failures |
| Task Completed not firing | Monitoring agent paused | Check monitoring agent is active |
| Credit burn alert false positive | Legitimate traffic spike | Tune alert threshold |
| Eval scores dropping | Prompt drift or model change | Review recent prompt/model changes |

## Resources
- [Lindy Evals](https://docs.lindy.ai/fundamentals/lindy-101/evals)
- [Lindy Tasks](https://docs.lindy.ai/fundamentals/lindy-101/tasks)
- [Lindy Documentation](https://docs.lindy.ai)

## Next Steps
Proceed to `lindy-incident-runbook` for incident response procedures.
