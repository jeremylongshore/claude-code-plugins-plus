# Apify Production Deployment — Full Implementation

The six-step deploy-to-production walkthrough. SKILL.md carries the lean summary;
this file has every command and code block verbatim.

## Step 1: Deploy Actor

```bash
# Build and push to Apify platform
apify push

# Verify the build succeeded
apify builds ls

# Test on platform with production-like input
apify actors call username/my-actor \
  --input='{"startUrls":[{"url":"https://target.com"}],"maxItems":10}'
```

## Step 2: Configure Scheduling

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

## Step 3: Set Up Webhooks for Monitoring

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

## Step 4: Monitor Runs

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

## Step 5: Implement Rollback

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

## Step 6: Cost Guard

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
