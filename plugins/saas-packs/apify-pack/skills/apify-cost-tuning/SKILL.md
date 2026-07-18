---
name: apify-cost-tuning
description: 'Optimize Apify platform costs through memory tuning, compute unit
  management, and proxy budgeting. Use when analyzing Apify billing, reducing Actor
  run costs, or implementing usage monitoring and budget alerts. Trigger with "apify
  cost", "apify billing", "reduce apify costs", "apify pricing", "apify expensive",
  "apify budget", "compute units".'
allowed-tools: Read, Grep
version: 1.5.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- scraping
- automation
- apify
compatibility: Designed for Claude Code
---
# Apify Cost Tuning

## Overview

Apify charges on three axes: compute units (CU), proxy traffic (GB), and storage.
One CU = 1 GB of memory running for 1 hour, so cost scales with both memory
allocation and run duration. This skill walks the investigate → tune → guard loop
that finds where spend is going, cuts it at the biggest lever (memory), and installs
guardrails so it stays down.

Full pricing tables (plan CU prices, proxy rates, storage rules) live in
[pricing-model.md](references/pricing-model.md).

## Prerequisites

- An Apify account with API access and `APIFY_TOKEN` set in the environment.
- The `apify-client` package installed (`npm install apify-client`).
- At least one Actor with run history to analyze.

## Instructions

The workflow is six steps. Each is summarized here with its core lever; the full,
runnable code for every step is in
[implementation.md](references/implementation.md).

1. **Analyze current costs** — roll up the last N days of runs into total CU, USD, and
   duration, and surface the single most expensive run:

   ```typescript
   import { ApifyClient } from 'apify-client';
   const client = new ApifyClient({ token: process.env.APIFY_TOKEN });

   const { items: runs } = await client.actor(actorId).runs().list({ limit: 1000, desc: true });
   const totalUsd = runs.reduce((s, r) => s + (r.usageTotalUsd ?? 0), 0);
   ```

2. **Reduce memory allocation** (biggest lever) — sweep memory from 4096 MB down to
   256 MB and stop at the first failure to find the sweet spot. Most CheerioCrawler
   Actors are over-provisioned. Sweet spots: simple Cheerio 256-512 MB, complex
   512-1024 MB, Playwright 2048-4096 MB.

3. **Optimize crawl duration** — higher `maxConcurrency`, tighter
   `requestHandlerTimeoutSecs`, a `maxRequestsPerCrawl` cap, fewer retries, and
   selective `enqueueLinks`. Faster crawls consume fewer CUs.

4. **Minimize proxy costs** — prefer datacenter (free with plan), only reach for
   residential when a site blocks it, block images/fonts/CSS to save residential GB,
   and reuse proxy sessions with `useSessionPool`.

5. **Cost guard for runaway Actors** — start the run, poll `usageTotalUsd` every 30s,
   and `.abort()` once spend crosses a hard cap.

6. **Monitor monthly usage** — iterate every Actor's runs since the 1st of the month
   and print a cost-descending report so the top spenders are obvious.

See [full walkthrough](references/implementation.md) for the complete code of each
step, including the memory sweep, proxy hooks, budget guard, and monthly report.

## Output

Running this skill produces:

- A **per-Actor cost analysis** (runs, total CU, total USD, avg CU/run, avg cost/run,
  most expensive run) for a chosen lookback window.
- A **memory profile** table mapping memory settings to status, duration, CU, and USD
  so you can pick the cheapest allocation that still succeeds.
- A **monthly cost report** ranking every Actor by spend, with a grand total.
- Tuned Actor configuration (reduced memory, capped crawls, proxy resource blocking)
  and an optional budget guard that aborts runs exceeding a USD ceiling.

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

## Examples

Three worked scenarios chain the steps against concrete symptoms — a CheerioCrawler
bill that tripled, runaway residential-proxy GB, and guarding a brand-new Actor. Each
shows the full investigate → tune → verify loop. See
[examples.md](references/examples.md).

Quick guard example — abort any run that exceeds $0.50:

```typescript
// runWithBudget polls usageTotalUsd every 30s and aborts past the cap
const run = await runWithBudget('user/scraper', input, 0.50);
```

## Resources

- [Apify Pricing](https://apify.com/pricing)
- [Usage & Resources](https://docs.apify.com/platform/actors/running/usage-and-resources)
- [Compute Unit Calculator](https://help.apify.com/en/articles/3490384-what-is-a-compute-unit)
- [pricing-model.md](references/pricing-model.md) — full pricing tables (local)
- [implementation.md](references/implementation.md) — complete step-by-step code (local)
- [examples.md](references/examples.md) — worked cost-tuning scenarios (local)

## Next Steps

For architecture patterns, see `apify-reference-architecture`.
