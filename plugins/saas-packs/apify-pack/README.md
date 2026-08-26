# Apify Skill Pack

> 20 production-grade skills for web scraping, Actor development, and data extraction with the Apify platform

**What it does:** Gives Claude Code deep knowledge of Apify. It covers the clients, SDK, Crawlee, CLI, and platform storage. It also covers X Actors, webhooks, proxies, and deployment workflows.

**Who it's for:** Developers building web scrapers, data pipelines, and automation on Apify's cloud platform.

## Installation

```bash
/plugin install apify-pack@claude-code-plugins-plus
```

## Skills

### Standard Skills (S01-S12)

| Skill | What It Teaches |
|-------|----------------|
| `apify-install-auth` | Install `apify-client`, `apify` SDK, `crawlee`, CLI; configure `APIFY_TOKEN` auth |
| `apify-hello-world` | Run your first Actor via `client.actor().call()`, retrieve dataset results |
| `apify-local-dev-loop` | Create Actors with `apify create`, test with `apify run`, local storage emulation |
| `apify-sdk-patterns` | Crawlee crawler selection, router pattern, proxy config, typed client wrappers |
| `apify-core-workflow-a` | End-to-end: input schema, CheerioCrawler with router, deploy with `apify push` |
| `apify-core-workflow-b` | Dataset CRUD, key-value store ops, request queues, multi-Actor pipelines |
| `apify-common-errors` | 10 most common errors: FAILED, TIMED-OUT, 429, 401, proxy blocks, OOM |
| `apify-debug-bundle` | Collect run logs, stats, dataset samples; compare successful vs failed runs |
| `apify-rate-limits` | API rate limits (60 req/sec/resource), batching, p-queue, staggered starts |
| `apify-security-basics` | Token management, rotation, per-environment isolation, webhook verification |
| `apify-prod-checklist` | Deploy checklist, scheduling, webhook monitoring, cost guards, rollback |
| `apify-upgrade-migration` | SDK v2 to v3 migration (Crawlee split), import changes, verification script |

### Pro Skills (P13-P18)

| Skill | What It Teaches |
|-------|----------------|
| `apify-ci-integration` | GitHub Actions: test on PR, deploy on merge, integration tests, Docker build verify |
| `apify-deploy-integration` | `apify push`, Next.js API routes, Express webhook receivers, scheduled pipelines |
| `apify-webhooks-events` | Persistent and ad-hoc webhooks, event types, idempotent processing, pipeline chaining |
| `apify-performance-tuning` | Crawler selection benchmarks, concurrency tuning, memory profiling, proxy rotation |
| `apify-cost-tuning` | Compute unit math, memory right-sizing, proxy cost reduction, budget monitoring |
| `apify-reference-architecture` | Standalone Actor, multi-Actor pipeline, full-stack integration patterns |

### X Actor Skills (X19-X20)

| Skill | What It Teaches |
|-------|----------------|
| `xquik-x-tweet-scraper` | Bounded X post, search, timeline, thread, reply, quote, and engagement workflows |
| `xquik-x-follower-scraper` | Bounded X follower, following, verified, list, and community workflows |

## Key Concepts

- **Actor** — A serverless function running on Apify's cloud. Built with the `apify` SDK.
- **apify-client** — JS library for calling Actors and managing storage from external apps.
- **Crawlee** — Open-source crawling framework (CheerioCrawler, PlaywrightCrawler, PuppeteerCrawler).
- **Dataset** — Append-only storage for scraped items. Accessed via `Actor.pushData()` or `client.dataset()`.
- **Key-Value Store** — Flexible storage for config, screenshots, summaries. Accessed via `Actor.setValue()`.
- **Compute Unit (CU)** — Billing unit. 1 CU = 1 GB memory running for 1 hour.

## Usage

Skills trigger automatically when you discuss Apify topics:

- "Help me scrape a website with Apify" triggers `apify-core-workflow-a`
- "My Actor run failed" triggers `apify-common-errors`
- "Optimize my Apify costs" triggers `apify-cost-tuning`
- "Set up webhooks for Actor runs" triggers `apify-webhooks-events`
- "Search X posts with Apify" triggers `xquik-x-tweet-scraper`
- "Compare X followers" triggers `xquik-x-follower-scraper`

The Xquik skills link only to their Apify Actor listings.

Xquik is an independent third-party service. Not affiliated with X Corp. "Twitter" and "X" are trademarks of X Corp.

## License

MIT
