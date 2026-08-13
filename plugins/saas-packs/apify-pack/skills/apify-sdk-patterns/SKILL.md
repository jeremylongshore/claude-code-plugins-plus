---
name: apify-sdk-patterns
description: 'Production-ready patterns for Apify SDK and apify-client in TypeScript.

  Use when building Actors with Crawlee, managing datasets/KV stores,
  or implementing robust client wrappers with retry and validation.

  Trigger with "apify SDK patterns", "apify best practices",
  "apify client wrapper", "crawlee patterns", "idiomatic apify".

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
# Apify SDK Patterns

## Overview

Production patterns for both the `apify` SDK (building Actors) and `apify-client` (calling Actors remotely). Covers Crawlee crawler selection, data storage, proxy configuration, and typed client wrappers. This skill gives you the essential skeletons inline; the full eight-pattern catalog and two worked scenarios live in `references/` for progressive drill-down.

## Prerequisites

- Install what you need: `apify-client` for calling Actors remotely, or `apify` + `crawlee` for building Actors. Both can coexist in one project.
- Set `APIFY_TOKEN` in the environment — read it via `process.env.APIFY_TOKEN`, never hard-code it. This is the only credential these patterns require (Apify uses a personal API token, not OAuth).
- TypeScript is recommended; every snippet here is typed and runs under `ts-node` or a compiled build.

## Instructions

Use the two skeletons below to start, then reach into the reference catalog for the pattern that matches your task.

### Pattern 1: Typed Client Singleton

Create one lazily-initialized, token-validated `ApifyClient` and reuse it everywhere. A `resetClient()` hook keeps it testable.

```typescript
// src/apify/client.ts
import { ApifyClient } from 'apify-client';

let instance: ApifyClient | null = null;

export function getApifyClient(): ApifyClient {
  if (!instance) {
    const token = process.env.APIFY_TOKEN;
    if (!token) throw new Error('APIFY_TOKEN is required');
    instance = new ApifyClient({ token });
  }
  return instance;
}

// Reset for testing
export function resetClient(): void {
  instance = null;
}
```

### Pattern 2: Crawlee Crawler Selection

Choose the crawler that matches the page, not the other way around:

```typescript
import { CheerioCrawler, PlaywrightCrawler, PuppeteerCrawler } from 'crawlee';

// CHEERIO — Fast, lightweight, no JavaScript rendering
// Use for: static HTML, server-rendered pages, APIs
// PLAYWRIGHT — Full browser, all engines, modern API
// Use for: SPAs, JavaScript-heavy pages, complex interactions
// PUPPETEER — Chromium-only browser automation
// Use for: when you need Chromium specifically or legacy Puppeteer code
```

### Patterns 3–8: Full catalog

The remaining six patterns are moved verbatim into [patterns.md](references/patterns.md) so this file stays scannable. Pick the one you need:

- **Pattern 3 — Actor lifecycle with error handling:** `Actor.main()` wrapping input validation, conditional proxy, and a `failedRequestHandler`.
- **Pattern 4 — Dataset operations:** push from inside an Actor; list/create/download from an external app.
- **Pattern 5 — Key-value store operations:** JSON config and binary artifacts by content type.
- **Pattern 6 — Proxy configuration:** datacenter vs residential vs SERP tiers.
- **Pattern 7 — Router for multi-page Actors:** labeled listing/detail handlers.
- **Pattern 8 — Safe result wrapper:** discriminated-union `Result<T>` around remote calls.

See [patterns.md](references/patterns.md) for the complete code of all six.

## Output

Applying these patterns yields:

- A single reusable `ApifyClient` instance with fail-fast token validation.
- Actors that store structured records in the default dataset (downloadable as CSV/JSON) and named config/artifacts in key-value stores.
- Remote Actor calls that resolve to a typed `Result<T>` — callers branch on `error` instead of catching exceptions.
- Failed requests captured as `{ url, error, '#isFailed': true }` rows rather than aborting the crawl.

## Error Handling

| Pattern | Use Case | Benefit |
|---------|----------|---------|
| `Actor.main()` | Actor entry point | Auto init/exit + error reporting |
| `failedRequestHandler` | Per-request failures | Log failures without stopping crawl |
| Safe wrapper | External calls | Prevents uncaught exceptions |
| Router | Multi-page scrapes | Clean separation of page types |
| Proxy rotation | Anti-bot sites | Higher success rate |

## Examples

Two runnable end-to-end scenarios live in [examples.md](references/examples.md):

- **Example A — Call a remote Actor safely from an app:** composes the client singleton (Pattern 1) with the safe result wrapper (Pattern 8) to run `apify/web-scraper` and read its dataset without ever throwing.
- **Example B — A two-tier product scraper Actor:** composes crawler selection (Pattern 2), the router (Pattern 7), and dataset writes (Pattern 4) into a listing → detail → structured-record flow.

## Resources

- [Full pattern catalog](references/patterns.md) — Patterns 3–8 with complete code
- [Worked examples](references/examples.md) — two end-to-end scenarios
- [Apify SDK Reference](https://docs.apify.com/sdk/js/reference)
- [Crawlee Documentation](https://crawlee.dev/js/docs/quick-start)
- [Apify JS Client Reference](https://docs.apify.com/api/client/js/reference)
- [Proxy Management Guide](https://docs.apify.com/sdk/js/docs/guides/proxy-management)

## Next Steps

Apply these patterns in `apify-core-workflow-a` for a complete build-and-deploy web scraping workflow, or pair them with `apify-common-errors` when hardening an Actor for production.
