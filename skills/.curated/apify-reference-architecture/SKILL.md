---
name: apify-reference-architecture
description: |
  Production-grade architecture patterns for Apify-powered applications.
  Use when designing scraping infrastructure, building multi-Actor pipelines,
  or integrating Apify into a larger system architecture.
  Trigger with "apify architecture", "apify best practices",
  "apify project structure", "scraping architecture", "apify system design".
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
# Apify Reference Architecture

## Overview

Production-ready architecture patterns for applications built on Apify. Three patterns
scale from a single scraper to a full-stack integration:

1. **Standalone Actor** — one scraper deployed to the Apify platform.
2. **Multi-Actor Pipeline** — a discover → scrape → transform chain of Actors.
3. **Full-Stack Integration** — an application using Apify as a data source behind a service layer.

This skill helps you choose the right pattern, lay out the directory structure, and wire
the skeleton code. Full directory trees, diagrams, and code for every pattern live in
[references/architecture-patterns.md](references/architecture-patterns.md); the service
layer, configuration loader, and health check live in
[references/implementation.md](references/implementation.md).

## Prerequisites

- **Runtime:** Node.js `>=18`, TypeScript, and the Apify CLI (`npm i -g apify-cli`).
- **Packages:** `apify` + `crawlee` (inside an Actor), `apify-client` (calling Actors from an app), `zod` (input validation).
- **Auth:** an Apify API token. Set `APIFY_TOKEN` in the environment; the Apify SDK and
  `apify-client` read it automatically (or pass it explicitly to `new ApifyClient({ token })`).
  Never hardcode the token — inject it via env var and validate at startup.
- **Access:** `Read` and `Grep` the target repository so you can match the recommended
  layout against the code already on disk before proposing changes.

## Instructions

1. **Pick the pattern.** One scraper → Pattern 1. A staged workflow that discovers,
   scrapes, then cleans → Pattern 2. An app that consumes scraped data → Pattern 3.
2. **`Grep` the existing repo** for `apify`, `apify-client`, and `Actor.main` to see what
   is already wired, so you extend rather than duplicate structure.
3. **Lay out the directory** from the pattern's tree in
   [references/architecture-patterns.md](references/architecture-patterns.md). Keep
   routing, extraction, and validation in separate modules.
4. **Add typed input validation** with `zod` (see `src/types.ts` in the reference) so bad
   input fails fast at the Actor boundary instead of mid-crawl.
5. **Isolate every Apify call behind a service layer** (Pattern 3) using the `ApifyService`
   class in [references/implementation.md](references/implementation.md) — the rest of the
   app never imports `apify-client` directly.
6. **Load configuration once at startup** via `loadConfig()` and layer per-environment
   overrides on a single base object; validate required env vars before serving traffic.
7. **Expose an Apify health check** so a bad token or platform outage surfaces before a
   user-facing scrape fails.

## Output

Applying this skill produces an architecture, not a running command. Expect:

- A recommended directory layout for the chosen pattern.
- Skeleton TypeScript modules (`main.ts`, `types.ts`, service layer, config loader, health check).
- A per-environment configuration strategy and an Apify health signal.
- For pipelines, an orchestrator that reports per-stage item counts and total USD cost, e.g.:

```
=== Pipeline Summary ===
Discovered: 320 URLs
Scraped:    298 items
Clean:      271 items
Total cost: $0.4120
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Circular dependencies | Service imports service | Use dependency injection |
| Missing config | Env var not set | Validate at startup with `loadConfig()` |
| Pipeline stage failure | Actor crash mid-pipeline | Add retry logic per stage |
| State management | Tracking run status | Use webhook handler + database |
| `Run not ready` error | Fetching results before `SUCCEEDED` | Poll `getRunStatus` or use a completion webhook |

## Examples

**Standalone Actor entry point** — the minimal skeleton; full file in
[references/architecture-patterns.md](references/architecture-patterns.md):

```typescript
// src/main.ts
import { Actor } from 'apify';
import { CheerioCrawler } from 'crawlee';
import { router } from './routes/listing';
import { validateInput, ScraperInput } from './types';

await Actor.main(async () => {
  const input = validateInput(await Actor.getInput<ScraperInput>());
  const crawler = new CheerioCrawler({
    requestHandler: router,
    maxRequestsPerCrawl: input.maxItems ?? 100,
    maxConcurrency: input.concurrency ?? 10,
  });
  await crawler.run(input.startUrls.map(s => s.url));
});
```

**Calling an Actor from an app** — via the service layer:

```typescript
const apify = new ApifyService(process.env.APIFY_TOKEN!);
const { runId } = await apify.startScrape(['https://example.com']);
const results = await apify.getResults<ProductOutput>(runId);
```

More: the multi-stage pipeline orchestrator and the full `ApifyService` class are in
[references/architecture-patterns.md](references/architecture-patterns.md) and
[references/implementation.md](references/implementation.md). For multi-environment
setup, see the companion `apify-deploy-integration` skill.

## Resources

- [references/architecture-patterns.md](references/architecture-patterns.md) — full trees, diagrams, and code for all three patterns
- [references/implementation.md](references/implementation.md) — service layer, config loader, health check
- [Apify Platform Architecture](https://docs.apify.com/platform)
- [API Client Reference](https://docs.apify.com/api/client/js/reference)
- [Actor Development Best Practices](https://docs.apify.com/platform/actors/development)
