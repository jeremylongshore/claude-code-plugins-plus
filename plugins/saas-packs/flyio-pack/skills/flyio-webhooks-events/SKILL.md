---
name: flyio-webhooks-events
description: |
  Implement Fly.io machine events, health check monitoring, and log-based
  event processing for deployment automation and alerting.
  Trigger: "fly.io events", "fly.io machine status", "fly.io health monitoring".
allowed-tools: Read, Write, Edit, Bash(fly:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, edge-compute, flyio]
compatible-with: claude-code
---

# Fly.io Events & Monitoring

## Overview

Fly.io does not have traditional webhooks. Instead, monitor machine state changes via the Machines API, process structured logs via `fly logs`, and use health check endpoints for automated responses.

## Instructions

### Step 1: Poll Machine State Changes

```typescript
// Monitor machine state transitions via Machines API
async function watchMachines(appName: string, callback: (event: MachineEvent) => void) {
  const client = new FlyClient(appName, process.env.FLY_API_TOKEN!);
  const stateCache = new Map<string, string>();

  setInterval(async () => {
    const machines = await client.listMachines();
    for (const m of machines) {
      const prev = stateCache.get(m.id);
      if (prev && prev !== m.state) {
        callback({
          machineId: m.id,
          region: m.region,
          previousState: prev,
          currentState: m.state,
          timestamp: new Date(),
        });
      }
      stateCache.set(m.id, m.state);
    }
  }, 10_000);  // Check every 10 seconds
}

interface MachineEvent {
  machineId: string;
  region: string;
  previousState: string;
  currentState: string;
  timestamp: Date;
}
```

### Step 2: Health Check Event Handler

```typescript
// Implement health check that reports machine health
// Fly.io uses this to auto-restart unhealthy machines

import express from 'express';
const app = express();

app.get('/health', async (req, res) => {
  const checks = {
    database: await checkPostgres(),
    redis: await checkRedis(),
    memory: process.memoryUsage().heapUsed < 500 * 1024 * 1024,  // < 500MB
  };

  const healthy = Object.values(checks).every(Boolean);
  res.status(healthy ? 200 : 503).json({
    status: healthy ? 'healthy' : 'unhealthy',
    region: process.env.FLY_REGION,
    machine: process.env.FLY_MACHINE_ID,
    checks,
  });
});
```

### Step 3: Structured Log Processing

```bash
# Stream logs and process with jq
fly logs -a my-app --json | jq -c 'select(.level == "error")' | while read -r line; do
  echo "$line" >> errors.jsonl
  # Send to Slack, PagerDuty, etc.
done

# Search recent logs for specific patterns
fly logs -a my-app --no-tail | grep -i "error\|crash\|oom"
```

### Step 4: Deployment Event Notifications

```bash
# Post-deploy notification in CI
fly deploy -a my-app && \
curl -X POST "$SLACK_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d "{\"text\": \"Deployed my-app to Fly.io. Status: $(fly status -a my-app --json | jq -r '.Status')\"}"
```

## Resources

- [Machines API](https://fly.io/docs/machines/api/machines-resource/)
- [Health Checks](https://fly.io/docs/reference/configuration/#http_service-checks)
- [Fly Logs](https://fly.io/docs/flyctl/logs/)

## Next Steps

For performance optimization, see `flyio-performance-tuning`.
