---
name: apify-performance-tuning
description: 'Optimize Apify Actor performance: crawl speed, memory usage, concurrency,
  and proxy rotation.

  Use when Actors are slow, consuming too much memory, or being blocked by target
  sites, or when a crawl is too expensive per run.

  Trigger with "apify performance", "optimize apify actor", "apify slow", "crawlee
  concurrency", "apify memory tuning", "scraper performance".

  '
allowed-tools: Read, Write, Edit
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
# Apify Performance Tuning

## Overview

Optimize Apify Actors for speed, cost, and reliability. Covers Crawlee concurrency settings, memory profiling, proxy rotation strategies, request batching, and crawler selection for different workloads.

The workflow is a repeatable loop: measure a baseline, apply one lever, re-measure. The single highest-impact lever is usually crawler choice — swapping a browser crawler for `CheerioCrawler` on non-JS pages is a 5-10x speedup on its own. The full six-step walkthrough, with every code block, lives in [references/implementation.md](references/implementation.md).

## Prerequisites

- Existing Actor with measurable baseline performance
- Understanding of `apify-sdk-patterns`
- Access to Actor run stats in Apify Console
- `APIFY_TOKEN` in the environment for reading run stats via `ApifyClient`

## Instructions

Work the levers in order. Each step is expanded — with copy-paste code — in the reference file linked below.

1. **Measure a baseline.** Pull `runTimeSecs`, `requestsFinished`, `memAvgBytes`, and `usageTotalUsd` from the run stats before changing anything. You cannot judge an optimization without a before number.
2. **Choose the right crawler.** `HttpCrawler`/`CheerioCrawler` for static HTML or JSON (low memory, fast); `PlaywrightCrawler`/`PuppeteerCrawler` only when the page genuinely needs JavaScript rendering.
3. **Tune concurrency.** Raise `maxConcurrency` for Cheerio (up to ~50); keep it low (~3-5) for browser crawlers because each page costs ~200MB. Let `autoscaledPoolOptions` adjust within the band.
4. **Optimize memory.** Push data immediately instead of accumulating arrays; for browser crawlers, block images/CSS/fonts in `preNavigationHooks` and cap concurrent browsers.
5. **Right-size the memory allocation.** Compute units bill on `memory x duration` — start low (512 MB for Cheerio) and only raise it if the Actor is memory-starved.
6. **Rotate proxies and tune requests.** Start on datacenter proxies, fall back to residential on 403/blocked; use a session pool for IP rotation and ban detection.

Full step-by-step walkthrough with all code: [references/implementation.md](references/implementation.md).

The minimal starting skeleton — swap a browser crawler for Cheerio and push immediately:

```typescript
import { CheerioCrawler } from 'crawlee';
import { Actor } from 'apify';

const crawler = new CheerioCrawler({
  maxConcurrency: 50,             // Cheerio is cheap — parallelize hard
  maxRequestsPerMinute: 300,      // But cap the rate to protect the target
  requestHandler: async ({ $, request }) => {
    await Actor.pushData({ url: request.url, title: $('title').text().trim() });
  },
});
```

## Output

Applying this skill produces:

- A **baseline vs. tuned metrics** comparison (pages/min, avg/max memory, compute units, cost/run) drawn from the run stats.
- A **crawler and concurrency recommendation** matched to whether the target pages need JS rendering.
- A **memory allocation** value sized to the workload, with the compute-unit cost tradeoff made explicit.
- A **proxy and session strategy** (datacenter-first with residential fallback) for reliability under anti-bot blocking.

Instrument the running crawl to confirm the gains in real time — see [references/monitoring.md](references/monitoring.md) for the throughput logger and a before/after impact table.

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Out of memory crash | Too many concurrent browsers | Reduce `maxConcurrency` |
| Slow crawl speed | Low concurrency | Increase `maxConcurrency` |
| High failure rate | Anti-bot blocking | Add proxy, reduce concurrency |
| Expensive runs | Over-provisioned memory | Profile and reduce allocation |
| Stalled crawl | Request handler timeout | Set `requestHandlerTimeoutSecs` |

## Examples

**Slow Playwright crawl on static pages.** The Actor renders every page in a browser at 3 pages/min. The pages are server-rendered HTML, so switch to `CheerioCrawler` and raise `maxConcurrency` — ~30 pages/min (10x). Code: [references/implementation.md](references/implementation.md) Steps 1-2.

**Out-of-memory crashes under load.** A `PlaywrightCrawler` at `maxConcurrency: 20` OOMs. Drop concurrency to 3, block images/CSS/fonts in `preNavigationHooks`, and call `window.stop()` post-navigation. Code: [references/implementation.md](references/implementation.md) Step 3.

**Getting blocked (403s) mid-crawl.** Start on datacenter proxies, and on a 403 re-enqueue the request with a residential proxy and retire the session to force a new IP. Code: [references/implementation.md](references/implementation.md) Step 5.

**Runs cost too much.** A 4GB allocation bills 8x more than needed for HTML parsing. Right-size to 512 MB and re-measure cost/run. Code: [references/implementation.md](references/implementation.md) Step 4; impact table in [references/monitoring.md](references/monitoring.md).

## Resources

- [references/implementation.md](references/implementation.md) — full six-step walkthrough with all code blocks
- [references/monitoring.md](references/monitoring.md) — in-crawl throughput logger + before/after impact table
- [Crawlee Performance Guide](https://crawlee.dev/js/docs/guides/configuration)
- [Actor Memory & Performance](https://docs.apify.com/platform/actors/running/usage-and-resources)
- [Proxy Management](https://docs.apify.com/sdk/js/docs/guides/proxy-management)

## Next Steps

For cost optimization beyond performance tuning, see the `apify-cost-tuning` skill in this pack — it covers compute-unit budgeting, storage costs, and scheduling strategies that this skill's memory right-sizing feeds into.
