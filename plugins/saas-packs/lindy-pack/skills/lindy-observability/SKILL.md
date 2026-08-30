---
name: lindy-observability
description: 'Monitor Lindy AI agent health, task success rates, and credit consumption.

  Use when setting up monitoring, building dashboards, configuring alerts,

  or tracking agent performance over time.

  Trigger with phrases like "lindy monitoring", "lindy observability",

  "lindy metrics", "lindy logging", "lindy dashboard".

  '
allowed-tools: Read, Write, Edit
version: 1.18.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- lindy
- monitoring
- observability
- dashboard
compatibility: Compatible with AI coding agents that can read Markdown and review monitoring configurations
---
# Lindy Observability

## Overview

Monitor workflow health from Lindy's documented task surfaces. Start with **Tasks**
for manual inspection, then use an **Agent Task Change** trigger followed by **Get
Task Details** for workflow-based monitoring and send only bounded operational fields
to an external collector; task inputs, outputs, customer content, and secrets do not
belong in metrics or logs.

## Prerequisites

- Lindy workspace with active custom agents
- Access to each monitored agent's Tasks view
- For external monitoring: an HTTPS receiver and a metrics stack
- A distinct, nonempty callback secret stored as `LINDY_CALLBACK_SECRET` by the
  receiver and as a protected value in the Lindy HTTP Request action

## Authentication and Data Boundary

Authenticate Lindy's outbound HTTP Request with a dedicated bearer value generated
for the metrics receiver. Store it only in Lindy's protected action configuration and
the receiver's secret manager, require at least 32 characters, compare it in constant
time, and rotate it independently. Never reuse an inbound Lindy webhook secret or a
metrics-scrape credential. Export only the three schema fields defined below.

## Instructions

### Step 1: Establish the Built-In View

1. Open the custom agent and select **Tasks**.
2. Review task status and open representative runs.
3. Inspect chronological steps, timestamps, conditions, and the error location.
4. Record a workspace-specific baseline by agent and workflow class. Do not copy
   task inputs or outputs into the baseline.

The documented sources for operational signals are:

| Signal | Source | Handling |
|---|---|---|
| Task outcome and frequency | Tasks / Agent Task Change | Aggregate by configured agent key |
| Duration and failing block | Get Task Details | Retain duration; keep block content in Lindy |
| Workspace spend | Lindy billing view | Keep billing data at its documented source |

### Step 2: Build the Monitoring Workflow

Create a separate monitoring agent using documented Lindy utilities:

1. Add **Agent Task Change** as the trigger.
2. Select the agent and actionable events: **Task succeeded**, **Task failed**, and
   **Task was canceled**. Add created/working only when lifecycle telemetry is needed.
3. Add **Get Task Details** after the trigger. Leave Agent and Sub Task on Auto so
   Lindy associates the triggering task; set Max Number of Blocks high enough to
   cover the measured workflow.
4. Map the result into the small telemetry schema in Step 3.
5. Route human-readable failure alerts inside Lindy. Include an agent key, status,
   task link, and failing block name; omit block inputs and outputs.

### Step 3: Collect Bounded Metrics

Use Lindy's **HTTP Request** action to POST the sanitized result. This TypeScript
receiver rejects unknown agents, statuses, fields, oversized bodies, invalid
durations, and empty secrets:

```typescript
import { timingSafeEqual } from 'node:crypto';
import express from 'express';
import { Counter, Histogram, Registry } from 'prom-client';

const app = express();
app.use(express.json({ limit: '4kb', strict: true }));

const callbackSecret = process.env.LINDY_CALLBACK_SECRET;
if (!callbackSecret || callbackSecret.trim().length < 32) {
  throw new Error('LINDY_CALLBACK_SECRET must contain at least 32 characters');
}

const agentKeys = new Set(
  (process.env.LINDY_MONITORED_AGENTS ?? '')
    .split(',')
    .map((value) => value.trim())
    .filter(Boolean),
);
if (agentKeys.size === 0) throw new Error('LINDY_MONITORED_AGENTS is empty');

type TaskStatus = 'succeeded' | 'failed' | 'canceled';
type MetricInput = { agent: string; status: TaskStatus; durationSeconds: number };
const statuses = new Set<TaskStatus>(['succeeded', 'failed', 'canceled']);

function authorized(header: string | undefined): boolean {
  if (!header?.startsWith('Bearer ')) return false;
  const actual = Buffer.from(header.slice('Bearer '.length));
  const expected = Buffer.from(callbackSecret);
  return actual.length === expected.length && timingSafeEqual(actual, expected);
}

function parseMetricInput(value: unknown): MetricInput | null {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return null;
  const input = value as Record<string, unknown>;
  const allowed = new Set(['agent', 'status', 'durationSeconds']);
  if (Object.keys(input).some((key) => !allowed.has(key))) return null;
  if (typeof input.agent !== 'string' || !agentKeys.has(input.agent)) return null;
  if (typeof input.status !== 'string' || !statuses.has(input.status as TaskStatus)) return null;
  if (
    typeof input.durationSeconds !== 'number' ||
    !Number.isFinite(input.durationSeconds) ||
    input.durationSeconds < 0 ||
    input.durationSeconds > 86_400
  ) return null;
  return input as MetricInput;
}

const registry = new Registry();
const taskCounter = new Counter<'agent' | 'status'>({
  name: 'lindy_tasks_total',
  help: 'Total Lindy agent tasks',
  labelNames: ['agent', 'status'],
  registers: [registry],
});
const taskDuration = new Histogram<'agent'>({
  name: 'lindy_task_duration_seconds',
  help: 'Lindy task execution duration',
  labelNames: ['agent'],
  buckets: [1, 2, 5, 10, 30, 60, 120],
  registers: [registry],
});

app.post('/lindy/metrics', (req, res) => {
  if (!authorized(req.headers.authorization)) return res.sendStatus(401);
  const input = parseMetricInput(req.body);
  if (!input) return res.status(400).json({ error: 'invalid_metrics_schema' });

  taskCounter.inc({ agent: input.agent, status: input.status });
  taskDuration.observe({ agent: input.agent }, input.durationSeconds);
  // Do not log req.body or task details.
  return res.json({ recorded: true });
});

app.get('/metrics', async (_req, res) => {
  res.set('Content-Type', registry.contentType);
  res.send(await registry.metrics());
});
```

Configure the HTTP Request action with an allowlisted HTTPS URL, POST, JSON content
type, and `Authorization: Bearer <protected callback secret>`. Map only:

```json
{
  "agent": "support-bot",
  "status": "succeeded",
  "durationSeconds": 12.4
}
```

The agent value is a stable configured key, never a task/customer identifier. Do not
reuse a secret generated for an inbound **Webhook Received** trigger as the outbound
callback secret.

### Step 4: Query and Alert

Use correct counter/histogram aggregation:

| Panel | PromQL |
|---|---|
| Success ratio | `sum(rate(lindy_tasks_total{status="succeeded"}[1h])) / clamp_min(sum(rate(lindy_tasks_total[1h])), 1e-9)` |
| Failure rate | `sum by (agent) (rate(lindy_tasks_total{status="failed"}[15m]))` |
| Duration p95 | `histogram_quantile(0.95, sum by (le, agent) (rate(lindy_task_duration_seconds_bucket[15m])))` |
| Trigger frequency | `sum by (agent) (rate(lindy_tasks_total[15m]))` |

Set windows and thresholds from the measured workspace baseline and service
objectives. Alert text may link to the task but must not reproduce task content.

### Step 5: Add Quality Regression Checks

Lindy currently documents evals as offline evaluation of selected historical tasks.
Use them to compare quality after changes; do not describe them as live monitoring.
Keep operational alerts on Tasks/Agent Task Change and quality regression on evals.

## Error Handling

| Issue | Response |
|---|---|
| Agent Task Change is silent | Confirm the monitoring agent is active, selected agent is correct, and event is enabled |
| Collector returns 401 | Rotate and update the dedicated callback secret on both sides |
| Collector returns 400 | Reject the event; inspect only field names/types, not payload content |
| Cardinality spike | Restore the configured agent allowlist and remove dynamic labels |
| Dashboard has no samples | Verify HTTP status in the Lindy task and scrape the registry endpoint |

## Output

Return an observability plan containing:

- monitored agents and selected Agent Task Change events;
- the exact low-cardinality telemetry schema and agent allowlist;
- secret ownership and rotation notes for `LINDY_CALLBACK_SECRET`;
- baseline-derived dashboard queries and alert thresholds;
- a privacy review confirming that no task input, output, customer identifier, or
  credential leaves Lindy; and
- a verification receipt with a successful sample, a rejected bad secret, a rejected
  unknown field/agent, and a Prometheus scrape.

## Examples

For a support workflow, select success/failure/canceled events, retrieve task details,
and map only `{agent: "support-bot", status: "failed", durationSeconds: 12.4}`. The
receiver increments one bounded counter/histogram series. The alert links an operator
to the Lindy task for authorized investigation; it does not copy the customer message
or block output into Slack, logs, or Prometheus.

## Resources

- [Lindy Tasks](https://docs.lindy.ai/fundamentals/lindy-101/tasks)
- [Monitor Your Agents](https://docs.lindy.ai/testing/monitoring-your-agents)
- [Observability utilities](https://docs.lindy.ai/skills/lindy-utilities/observability)
- [HTTP Request](https://docs.lindy.ai/skills/by-lindy/http-request)
- [Lindy Evals](https://docs.lindy.ai/fundamentals/lindy-101/evals)

## Next Steps

Hand the verified alert contract and task-link policy to `lindy-incident-runbook` so
responders can investigate inside Lindy without expanding telemetry data exposure.
