---
name: apify-prod-checklist
description: |
  Production readiness checklist for Apify Actor deployments.
  Use when deploying Actors to production, preparing for launch,
  or validating Actor configuration before going live.
  Trigger: "apify production", "deploy actor to prod",
  "apify go-live", "apify launch checklist", "actor production ready".
allowed-tools: Read, Bash(apify:*), Bash(curl:*), Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, scraping, automation, apify]
compatible-with: claude-code
---

# Apify Production Checklist

## Overview

Complete checklist for deploying Actors to the Apify platform and integrating them into production applications. Covers Actor configuration, scheduling, monitoring, alerting, and rollback.

## Prerequisites

- Actor tested locally with `apify run`
- `apify login` configured with production token
- Familiarity with `apify-core-workflow-a` and `apify-deploy-integration`

## Pre-Deployment Checklist

### Actor Configuration
- [ ] `.actor/actor.json` has correct `name`, `title`, `description`
- [ ] `INPUT_SCHEMA.json` validates all required inputs
- [ ] `Dockerfile` uses pinned base image version (`apify/actor-node:20`, not `latest`)
- [ ] `package-lock.json` committed (deterministic installs)
- [ ] Memory set appropriately (start at 1024MB, tune after profiling)
- [ ] Timeout set with buffer (2x expected runtime)

### Code Quality
- [ ] `Actor.main()` wraps entry point (handles init/exit/errors)
- [ ] `failedRequestHandler` logs failures without crashing Actor
- [ ] Input validation at Actor start (`if (!input?.startUrls) throw ...`)
- [ ] No hardcoded URLs, credentials, or magic numbers
- [ ] Proxy configured for target sites that block datacenter IPs
- [ ] `maxRequestsPerCrawl` set to prevent runaway costs

### Data Output
- [ ] Dataset schema documented (consistent field names)
- [ ] `SUMMARY` key-value store record saved with run stats
- [ ] Large payloads chunked (9MB dataset push limit)
- [ ] PII sanitized before storage

## Instructions

### Step 1: Deploy Actor

```bash
# Build and push to Apify platform
apify push

# Verify the build succeeded
apify builds ls

# Test on platform with production-like input
apify actors call username/my-actor \
  --input='{"startUrls":[{"url":"https://target.com"}],"maxItems":10}'
```

### Step 2: Configure Scheduling

```typescript
import { ApifyClient } from 'apify-client';

const client = new ApifyClient({ token: process.env.APIFY_TOKEN });

// Create a scheduled task (cron)
const schedule = await client.schedules().create({
  name: 'daily-product-scrape',
  cronExpression: '0 6 * * *',  // Daily at 6 AM UTC
  isEnabled: true,
  actions: [{
    type: 'RUN_ACTOR',
    actorId: 'username/my-actor',
    runInput: {
      body: JSON.stringify({
        startUrls: [{ url: 'https://target.com/products' }],
        maxItems: 5000,
      }),
      contentType: 'application/json',
    },
    runOptions: {
      memory: 2048,
      timeout: 3600,
      build: 'latest',
    },
  }],
});

console.log(`Schedule created: ${schedule.id}`);
```

Or configure in Apify Console: Actors > Your Actor > Schedules.

### Step 3: Set Up Webhooks for Monitoring

```typescript
// Create webhook for run completion alerts
const webhook = await client.webhooks().create({
  eventTypes: ['ACTOR.RUN.SUCCEEDED', 'ACTOR.RUN.FAILED', 'ACTOR.RUN.TIMED_OUT'],
  condition: { actorId: 'ACTOR_ID' },
  requestUrl: 'https://your-server.com/api/apify-webhook',
  payloadTemplate: JSON.stringify({
    eventType: '{{eventType}}',
    actorId: '{{actorId}}',
    runId: '{{actorRunId}}',
    status: '{{resource.status}}',
    datasetId: '{{resource.defaultDatasetId}}',
    startedAt: '{{resource.startedAt}}',
    finishedAt: '{{resource.finishedAt}}',
  }),
});
```

### Step 4: Monitor Runs

```typescript
// Check recent runs for failures
async function checkActorHealth(actorId: string, lookbackHours = 24) {
  const { items: runs } = await client.actor(actorId).runs().list({
    limit: 50,
    desc: true,
  });

  const cutoff = new Date(Date.now() - lookbackHours * 3600_000);
  const recentRuns = runs.filter(r => new Date(r.startedAt) > cutoff);

  const stats = {
    total: recentRuns.length,
    succeeded: recentRuns.filter(r => r.status === 'SUCCEEDED').length,
    failed: recentRuns.filter(r => r.status === 'FAILED').length,
    timedOut: recentRuns.filter(r => r.status === 'TIMED-OUT').length,
    totalCostUsd: recentRuns.reduce((sum, r) => sum + (r.usageTotalUsd ?? 0), 0),
  };

  const successRate = stats.total > 0
    ? ((stats.succeeded / stats.total) * 100).toFixed(1)
    : 'N/A';

  console.log(`Actor: ${actorId}`);
  console.log(`Last ${lookbackHours}h: ${stats.total} runs, ${successRate}% success`);
  console.log(`Failed: ${stats.failed}, Timed out: ${stats.timedOut}`);
  console.log(`Total cost: $${stats.totalCostUsd.toFixed(4)}`);

  if (stats.failed > 0) {
    console.warn('ALERT: Failed runs detected!');
  }

  return stats;
}
```

### Step 5: Implement Rollback

```bash
# List available builds
apify builds ls

# Roll back to a previous build
curl -X POST \
  -H "Authorization: Bearer $APIFY_TOKEN" \
  "https://api.apify.com/v2/acts/ACTOR_ID?build=BUILD_NUMBER"

# Or redeploy from a git tag
git checkout v1.2.3
apify push
```

### Step 6: Cost Guard

```typescript
// Set up a cost guard that aborts runs exceeding budget
async function runWithCostGuard(
  actorId: string,
  input: Record<string, unknown>,
  maxCostUsd: number,
) {
  const run = await client.actor(actorId).start(input);

  // Poll every 30 seconds
  const pollInterval = setInterval(async () => {
    const status = await client.run(run.id).get();
    const cost = status.usageTotalUsd ?? 0;

    if (cost > maxCostUsd) {
      console.error(`Cost guard: $${cost.toFixed(4)} exceeds $${maxCostUsd}. Aborting.`);
      await client.run(run.id).abort();
      clearInterval(pollInterval);
    }
  }, 30_000);

  const finished = await client.run(run.id).waitForFinish();
  clearInterval(pollInterval);
  return finished;
}
```

## Production Alert Conditions

| Alert | Condition | Severity |
|-------|-----------|----------|
| Run failed | `status === 'FAILED'` | P1 |
| Run timed out | `status === 'TIMED-OUT'` | P2 |
| Low yield | Dataset items < expected threshold | P2 |
| High cost | `usageTotalUsd > budget` | P2 |
| Consecutive failures | 3+ failures in a row | P1 |
| No runs in window | Schedule didn't trigger | P1 |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Build fails on platform | Local deps differ | Commit `package-lock.json` |
| Schedule not firing | Cron syntax error | Validate at crontab.guru |
| Webhook not received | URL not reachable | Use ngrok for testing; check HTTPS |
| Memory exceeded | Workload too large | Increase memory or reduce concurrency |
| Unexpected cost spike | No `maxRequestsPerCrawl` | Always set an upper bound |

## Resources

- [Actor Deployment Guide](https://docs.apify.com/platform/actors/development/deployment)
- [Schedules Documentation](https://docs.apify.com/platform/schedules)
- [Webhook Event Types](https://docs.apify.com/platform/integrations/webhooks/events)
- [Usage & Billing](https://docs.apify.com/platform/actors/running/usage-and-resources)

## Next Steps

For version upgrades, see `apify-upgrade-migration`.
