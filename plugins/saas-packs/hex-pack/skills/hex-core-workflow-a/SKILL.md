---
name: hex-core-workflow-a
description: |
  Execute Hex primary workflow: Core Workflow A.
  Use when implementing primary use case,
  building main features, or core integration tasks.
  Trigger with phrases like "hex main workflow",
  "primary task with hex".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, hex, data, orchestration]
compatible-with: claude-code
---

# Hex Project Orchestration

## Overview

Trigger Hex project runs from external orchestration tools (Airflow, Dagster, cron) with input parameters, status polling, and error handling. This is the primary integration pattern for embedding Hex in data pipelines.

## Instructions

### Step 1: Parameterized Project Runs

```typescript
import 'dotenv/config';
const TOKEN = process.env.HEX_API_TOKEN!;
const BASE = 'https://app.hex.tech/api/v1';

interface RunConfig {
  projectId: string;
  inputParams?: Record<string, any>;
  updateCache?: boolean;
  killRunning?: boolean;
}

async function triggerRun(config: RunConfig) {
  const response = await fetch(`${BASE}/project/${config.projectId}/run`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${TOKEN}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({
      inputParams: config.inputParams || {},
      updateCacheResult: config.updateCache ?? true,
      killRunningExecution: config.killRunning ?? false,
    }),
  });
  if (!response.ok) throw new Error(`Trigger failed: ${response.status} ${await response.text()}`);
  return response.json();
}
```

### Step 2: Synchronous Run Helper

```typescript
async function runAndWait(config: RunConfig, timeoutMs = 600000): Promise<any> {
  const { runId, projectId } = await triggerRun(config);
  const startTime = Date.now();

  while (Date.now() - startTime < timeoutMs) {
    const res = await fetch(`${BASE}/project/${projectId}/run/${runId}`, {
      headers: { 'Authorization': `Bearer ${TOKEN}` },
    });
    const status = await res.json();

    switch (status.status) {
      case 'COMPLETED': return { success: true, runId, duration: Date.now() - startTime };
      case 'ERRORED': throw new Error(`Run ${runId} errored: ${status.statusMessage || 'unknown'}`);
      case 'KILLED': throw new Error(`Run ${runId} was killed`);
      default: await new Promise(r => setTimeout(r, 5000));
    }
  }
  throw new Error(`Run ${runId} timed out after ${timeoutMs}ms`);
}
```

### Step 3: Pipeline Orchestration

```typescript
// Run multiple Hex projects in sequence (data pipeline)
async function runPipeline(steps: RunConfig[]) {
  const results = [];
  for (const step of steps) {
    console.log(`Running: ${step.projectId}`);
    const result = await runAndWait(step);
    console.log(`Completed in ${result.duration}ms`);
    results.push(result);
  }
  return results;
}

// Example: ETL pipeline
await runPipeline([
  { projectId: 'extract-project-id', inputParams: { date: '2025-01-01' } },
  { projectId: 'transform-project-id' },
  { projectId: 'load-project-id', updateCache: true },
]);
```

### Step 4: Cancel Long-Running Projects

```typescript
async function cancelRun(projectId: string, runId: string) {
  const response = await fetch(`${BASE}/project/${projectId}/run/${runId}`, {
    method: 'DELETE',
    headers: { 'Authorization': `Bearer ${TOKEN}` },
  });
  console.log(`Cancelled run ${runId}: ${response.status}`);
}
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `429 Too Many Requests` | Rate limit (20/min, 60/hr) | Queue runs with delays |
| Run ERRORED | Project code failed | Check project logs in Hex UI |
| Run KILLED | Timeout or manual cancel | Increase timeout or fix slow queries |
| `404` | Project not published | Publish project before triggering runs |

## Resources

- [Run Project API](https://learn.hex.tech/docs/api/api-reference#run-project)
- [Orchestration Blog](https://hex.tech/blog/announcing-orchestration-public-api/)

## Next Steps

For scheduled runs, see `hex-core-workflow-b`.
