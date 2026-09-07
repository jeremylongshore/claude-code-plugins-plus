# Apify Cost Tuning — Full Implementation

The six-step cost-tuning workflow with complete, runnable code. SKILL.md summarizes
each step and links here for the full detail.

## Step 1: Analyze Current Costs

Pull the last N days of runs for an Actor and roll up compute units, USD spend, and
duration — plus the single most expensive run so you know where to look first.

```typescript
import { ApifyClient } from 'apify-client';

const client = new ApifyClient({ token: process.env.APIFY_TOKEN });

async function analyzeActorCosts(actorId: string, days = 30) {
  const { items: runs } = await client.actor(actorId).runs().list({
    limit: 1000,
    desc: true,
  });

  const cutoff = new Date(Date.now() - days * 86400_000);
  const recentRuns = runs.filter(r => new Date(r.startedAt) > cutoff);

  let totalCu = 0;
  let totalUsd = 0;
  let totalDurationSecs = 0;

  for (const run of recentRuns) {
    totalCu += run.usage?.ACTOR_COMPUTE_UNITS ?? 0;
    totalUsd += run.usageTotalUsd ?? 0;
    totalDurationSecs += run.stats?.runTimeSecs ?? 0;
  }

  const avgCuPerRun = recentRuns.length > 0 ? totalCu / recentRuns.length : 0;
  const avgCostPerRun = recentRuns.length > 0 ? totalUsd / recentRuns.length : 0;

  console.log(`=== Cost Analysis: ${actorId} (last ${days} days) ===`);
  console.log(`Runs:              ${recentRuns.length}`);
  console.log(`Total CU:          ${totalCu.toFixed(4)}`);
  console.log(`Total cost:        $${totalUsd.toFixed(4)}`);
  console.log(`Avg CU/run:        ${avgCuPerRun.toFixed(4)}`);
  console.log(`Avg cost/run:      $${avgCostPerRun.toFixed(4)}`);
  console.log(`Total duration:    ${(totalDurationSecs / 3600).toFixed(2)} hours`);

  // Find the most expensive run
  const mostExpensive = recentRuns.reduce(
    (max, r) => ((r.usageTotalUsd ?? 0) > (max.usageTotalUsd ?? 0) ? r : max),
    recentRuns[0],
  );
  if (mostExpensive) {
    console.log(`Most expensive:    $${mostExpensive.usageTotalUsd?.toFixed(4)} (${mostExpensive.id})`);
  }

  return { totalCu, totalUsd, avgCuPerRun, avgCostPerRun, runs: recentRuns.length };
}
```

## Step 2: Reduce Memory Allocation

Memory is the biggest cost lever. Most CheerioCrawler Actors are over-provisioned.

```typescript
// Test with progressively lower memory to find the sweet spot.
// Start high (4096 MB) and halve down to 256 MB — the floor where a
// simple Cheerio crawler still succeeds — stopping at the first failure.
for (const memory of [4096, 2048, 1024, 512, 256]) {
  try {
    const run = await client.actor('user/actor').call(testInput, {
      memory,
      timeout: 600,
    });

    console.log(
      `${memory}MB: ${run.status} | ` +
      `${run.stats?.runTimeSecs}s | ` +
      `${run.usage?.ACTOR_COMPUTE_UNITS?.toFixed(4)} CU | ` +
      `$${run.usageTotalUsd?.toFixed(4)}`
    );

    if (run.status !== 'SUCCEEDED') break;
  } catch (error) {
    console.log(`${memory}MB: FAILED — ${(error as Error).message}`);
    break;
  }
}
```

Typical memory sweet spots:

| Actor Type | Start At | Sweet Spot |
|-----------|----------|-----------|
| CheerioCrawler (simple) | 256 MB | 256-512 MB |
| CheerioCrawler (complex) | 512 MB | 512-1024 MB |
| PlaywrightCrawler | 2048 MB | 2048-4096 MB |
| Data processing | 1024 MB | 1024-2048 MB |

## Step 3: Optimize Crawl Duration

Faster crawls = fewer CUs consumed:

```typescript
const crawler = new CheerioCrawler({
  // Higher concurrency = faster completion
  maxConcurrency: 30,

  // Don't wait too long on slow pages
  requestHandlerTimeoutSecs: 20,

  // Stop early when you have enough data
  maxRequestsPerCrawl: 1000,

  // Avoid unnecessary retries
  maxRequestRetries: 2,  // Default: 3

  requestHandler: async ({ request, $, enqueueLinks }) => {
    // Only extract what you need
    await Actor.pushData({
      url: request.url,
      title: $('title').text().trim(),
      // Don't scrape entire page body if you don't need it
    });

    // Only enqueue relevant links (not every link on the page)
    await enqueueLinks({
      selector: 'a.product-link',  // Specific selector, not 'a'
      strategy: 'same-domain',
    });
  },
});
```

## Step 4: Minimize Proxy Costs

```typescript
// Strategy 1: Use datacenter proxy first (free with plan)
const dcProxy = await Actor.createProxyConfiguration({
  groups: ['BUYPROXIES94952'],
});

// Strategy 2: Only use residential proxy when needed
// Don't waste residential bandwidth on non-blocking sites

// Strategy 3: Minimize data transfer through residential proxy
const crawler = new PlaywrightCrawler({
  proxyConfiguration: resProxy,
  preNavigationHooks: [
    async ({ page }) => {
      // Block images, fonts, CSS (saves residential proxy GB)
      await page.route('**/*.{png,jpg,jpeg,gif,svg,webp,ico,woff,woff2,ttf,css}',
        route => route.abort()
      );
    },
  ],
});

// Strategy 4: Session stickiness (reduces new proxy connections)
const crawler = new CheerioCrawler({
  proxyConfiguration: resProxy,
  useSessionPool: true,
  sessionPoolOptions: {
    sessionOptions: {
      maxUsageCount: 100,  // More reuse = fewer new connections
    },
  },
});
```

## Step 5: Cost Guard for Runaway Actors

```typescript
async function runWithBudget(
  actorId: string,
  input: Record<string, unknown>,
  maxCostUsd: number,
) {
  const run = await client.actor(actorId).start(input, {
    memory: 512,
    timeout: 3600,
  });

  // Poll every 30 seconds
  const interval = setInterval(async () => {
    try {
      const status = await client.run(run.id).get();
      const cost = status.usageTotalUsd ?? 0;

      if (cost > maxCostUsd) {
        console.error(`Budget exceeded: $${cost.toFixed(4)} > $${maxCostUsd}. Aborting.`);
        await client.run(run.id).abort();
        clearInterval(interval);
      }
    } catch {
      // Ignore polling errors
    }
  }, 30_000);

  const finished = await client.run(run.id).waitForFinish();
  clearInterval(interval);
  return finished;
}

// Usage: max $0.50 per run
const run = await runWithBudget('user/scraper', input, 0.50);
```

## Step 6: Monitor Monthly Usage

```typescript
async function monthlyUsageReport() {
  // Get all Actors
  const { items: actors } = await client.actors().list();

  let grandTotalUsd = 0;
  const report: { actor: string; runs: number; cost: number }[] = [];

  for (const actor of actors) {
    const { items: runs } = await client.actor(actor.id).runs().list({
      limit: 1000,
      desc: true,
    });

    const thisMonth = new Date();
    thisMonth.setDate(1);
    thisMonth.setHours(0, 0, 0, 0);

    const monthlyRuns = runs.filter(r => new Date(r.startedAt) >= thisMonth);
    const monthlyCost = monthlyRuns.reduce(
      (sum, r) => sum + (r.usageTotalUsd ?? 0), 0,
    );

    if (monthlyRuns.length > 0) {
      report.push({
        actor: actor.name,
        runs: monthlyRuns.length,
        cost: monthlyCost,
      });
      grandTotalUsd += monthlyCost;
    }
  }

  // Sort by cost descending
  report.sort((a, b) => b.cost - a.cost);

  console.log('\n=== Monthly Cost Report ===');
  console.log(`${'Actor'.padEnd(30)} | ${'Runs'.padEnd(6)} | Cost`);
  console.log('-'.repeat(55));
  for (const r of report) {
    console.log(`${r.actor.padEnd(30)} | ${String(r.runs).padEnd(6)} | $${r.cost.toFixed(4)}`);
  }
  console.log('-'.repeat(55));
  console.log(`${'TOTAL'.padEnd(30)} | ${' '.padEnd(6)} | $${grandTotalUsd.toFixed(4)}`);
}
```
