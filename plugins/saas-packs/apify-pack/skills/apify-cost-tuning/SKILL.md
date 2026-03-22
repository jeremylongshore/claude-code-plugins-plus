---
name: apify-cost-tuning
description: |
  Optimize Apify platform costs through memory tuning, compute unit management, and proxy budgeting.
  Use when analyzing Apify billing, reducing Actor run costs,
  or implementing usage monitoring and budget alerts.
  Trigger: "apify cost", "apify billing", "reduce apify costs",
  "apify pricing", "apify expensive", "apify budget", "compute units".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, scraping, automation, apify]
compatible-with: claude-code
---

# Apify Cost Tuning

## Overview

Apify charges based on compute units (CU), proxy traffic (GB), and storage. One CU = 1 GB memory running for 1 hour. This skill covers how to analyze, reduce, and monitor costs across all three dimensions.

## Pricing Model

### Compute Units (CU)

```
CU = (Memory in GB) x (Duration in hours)

Example: 2048 MB (2 GB) running for 30 minutes = 2 x 0.5 = 1 CU
```

| Plan | CU Price | Included CUs |
|------|----------|-------------|
| Free | N/A | Limited trial |
| Starter | $0.30/CU | Varies by plan |
| Scale | $0.25/CU | Volume discounts |
| Enterprise | Custom | Negotiated |

### Proxy Costs

| Proxy Type | Cost | Use Case |
|-----------|------|----------|
| Datacenter | Included in plan | Non-blocking sites |
| Residential | ~$12/GB | Sites that block datacenters |
| Google SERP | ~$3.50/1000 queries | Google search results |

### Storage

Named datasets and KV stores persist indefinitely but count against storage quota. Unnamed (default run) storage expires after 7 days.

## Instructions

### Step 1: Analyze Current Costs

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

### Step 2: Reduce Memory Allocation

Memory is the biggest cost lever. Most CheerioCrawler Actors are over-provisioned.

```typescript
// Test with progressively lower memory to find the sweet spot
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

### Step 3: Optimize Crawl Duration

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

### Step 4: Minimize Proxy Costs

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

### Step 5: Cost Guard for Runaway Actors

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

### Step 6: Monitor Monthly Usage

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

## Cost Optimization Checklist

- [ ] Memory profiled (start low: 256-512MB for Cheerio)
- [ ] `maxRequestsPerCrawl` set to prevent runaway crawls
- [ ] Datacenter proxy used when possible (free with plan)
- [ ] Residential proxy: images/CSS/fonts blocked to save bandwidth
- [ ] `maxConcurrency` tuned (higher = faster = fewer CUs)
- [ ] Scheduled runs have appropriate frequency (don't over-scrape)
- [ ] Cost guard implemented for expensive runs
- [ ] Monthly usage reviewed

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Unexpected cost spike | No `maxRequestsPerCrawl` | Always set an upper bound |
| High residential proxy cost | Scraping images/fonts | Block non-essential resources |
| Over-provisioned memory | Default 1024MB | Profile and reduce to minimum |
| Too many scheduled runs | Aggressive cron | Reduce frequency if data freshness allows |

## Resources

- [Apify Pricing](https://apify.com/pricing)
- [Usage & Resources](https://docs.apify.com/platform/actors/running/usage-and-resources)
- [Compute Unit Calculator](https://help.apify.com/en/articles/3490384-what-is-a-compute-unit)

## Next Steps

For architecture patterns, see `apify-reference-architecture`.
