---
name: hex-core-workflow-b
description: |
  Execute Hex secondary workflow: Core Workflow B.
  Use when implementing secondary use case,
  or complementing primary workflow.
  Trigger with phrases like "hex secondary workflow",
  "secondary task with hex".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, hex, data, scheduling]
compatible-with: claude-code
---

# Hex Scheduled Runs & Admin API

## Overview

Configure scheduled runs and manage workspace resources via the Hex Admin API. Scheduled runs execute projects on cron-based intervals. The Admin API manages users, groups, and data connections.

## Instructions

### Step 1: List Project Runs

```typescript
const TOKEN = process.env.HEX_API_TOKEN!;
const BASE = 'https://app.hex.tech/api/v1';

async function getProjectRuns(projectId: string) {
  const response = await fetch(`${BASE}/project/${projectId}/runs`, {
    headers: { 'Authorization': `Bearer ${TOKEN}` },
  });
  const runs = await response.json();
  for (const run of runs) {
    console.log(`${run.runId}: ${run.status} (${run.startTime} → ${run.endTime || 'running'})`);
  }
  return runs;
}
```

### Step 2: Scheduled Runs (via Hex UI + API Trigger)

Schedules are configured in the Hex UI. For API-based scheduling, use external cron:

```typescript
// cron-trigger.ts — run via cron job or CI
import cron from 'node-cron';

// Daily at 6 AM UTC
cron.schedule('0 6 * * *', async () => {
  console.log('Triggering daily report...');
  await triggerRun({
    projectId: 'daily-report-project-id',
    inputParams: { date: new Date().toISOString().split('T')[0] },
    updateCache: true,
  });
});

// Weekly on Monday at 9 AM
cron.schedule('0 9 * * 1', async () => {
  await triggerRun({ projectId: 'weekly-summary-project-id' });
});
```

### Step 3: User Management (Admin API)

```typescript
// List workspace users
async function listUsers() {
  const response = await fetch(`${BASE}/workspace/users`, {
    headers: { 'Authorization': `Bearer ${TOKEN}` },
  });
  return response.json();
}

// List groups
async function listGroups() {
  const response = await fetch(`${BASE}/workspace/groups`, {
    headers: { 'Authorization': `Bearer ${TOKEN}` },
  });
  return response.json();
}
```

### Step 4: Data Connection Management

```typescript
// List configured data connections
async function listConnections() {
  const response = await fetch(`${BASE}/workspace/connections`, {
    headers: { 'Authorization': `Bearer ${TOKEN}` },
  });
  return response.json();
}
```

## Scheduling Options

| Method | Intervals | Plan Required |
|--------|-----------|---------------|
| Hex UI | Hourly, daily, weekly, monthly | Team+ |
| Hex UI (cron) | Any cron expression | Team+ |
| API trigger + external cron | Any schedule | Team+ |
| Airflow/Dagster integration | Any schedule | Team+ |

## Resources

- [Scheduled Runs](https://learn.hex.tech/docs/share-insights/scheduled-runs)
- [API Reference](https://learn.hex.tech/docs/api/api-reference)

## Next Steps

For common errors, see `hex-common-errors`.
