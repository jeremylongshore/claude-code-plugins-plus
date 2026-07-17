---
name: notion-reference-architecture
description: |
  Design and implement a production-ready Notion integration architecture with
  proper layering, caching, error handling, and testing strategies.
  Use when designing a new Notion integration, reviewing existing project
  structure, establishing architecture standards for a Notion application, or
  migrating from ad-hoc API calls to a layered architecture.
  Trigger with "notion architecture", "notion project structure", "notion
  reference architecture", "notion integration design", "notion layered
  architecture", or "notion service pattern".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*)
version: 1.38.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- productivity
- notion
- architecture
compatibility: Designed for Claude Code
---
# Notion Reference Architecture

## Overview

Production-grade architecture for Notion integrations using `@notionhq/client`.
This skill defines a four-layer architecture — client singleton, repository
pattern, service layer, and caching — that scales from simple scripts to
enterprise applications, with multi-integration setups, event-driven
processing, and testing strategies.

**Notion API version:** `2022-06-28` | **Rate limit:** 3 requests/second per integration | **Max page size:** 100

## Prerequisites

- Node.js 18+ with TypeScript strict mode enabled
- `@notionhq/client` v2.x installed (`npm install @notionhq/client`)
- A Notion internal integration created at <https://www.notion.so/my-integrations>
- `NOTION_TOKEN` environment variable set with the integration token
- Target databases/pages shared with the integration via "Add connections"

## Instructions

Build the architecture in four layers, bottom-up. Each layer depends only on
the ones below it, so wire them in order. The full copy-ready code for every
layer lives in [the implementation reference](references/implementation.md) —
scaffold the [project layout](references/implementation.md) first, then follow
the steps below.

### Step 1: Client singleton with retry and rate limiting

Wrap `@notionhq/client` in a singleton with explicit rate limiting (Notion caps
at 3 req/s per integration) and exponential-backoff retry. Expose separate
reader and writer clients so a read-heavy and a write-scoped integration can run
side by side and double effective throughput.

```typescript
// src/notion/client.ts — skeleton (full code in the implementation reference)
export function getReaderClient(): Client { /* singleton, NOTION_READER_TOKEN ?? NOTION_TOKEN */ }
export function getWriterClient(): Client { /* singleton, NOTION_WRITER_TOKEN ?? NOTION_TOKEN */ }
export async function rateLimitedCall<T>(fn: () => Promise<T>): Promise<T> { /* 3 req/s window */ }
export async function withRetry<T>(fn: () => Promise<T>, maxRetries = 3): Promise<T> { /* backoff */ }
```

See the full singleton, rate limiter, and retry wrapper in
[the implementation reference](references/implementation.md) (Step 1).

### Step 2: Repository and service layers

The repository layer wraps raw Notion API calls with pagination (Notion caps at
100 results per request), type extraction, and error handling. The service layer
sits above it with business logic, schema validation, and cache-aware
operations. Keep API shape in the repository and domain rules in the service so
each is independently testable.

```typescript
// Layer boundary — full classes in the implementation reference
class NotionDatabaseRepo { queryAll(); getRecords(); create(); getSchema(); }  // API shape
class NotionService { getActiveTasks(); createTask(); validateSchema(); }       // domain rules
```

See `NotionDatabaseRepo`, `NotionService`, and the TTL cache in
[the implementation reference](references/implementation.md) (Steps 2 and 3).

### Step 3: Event-driven processing and testing

Add the event queue, polling-based change detection, and the test suite last.
See [event-driven processing and testing patterns](references/event-driven-and-testing.md)
for the event queue, unit tests with a mocked `@notionhq/client`, live
integration tests, the headless CMS pattern, the project tracker example, and
the multi-integration architecture.

## Output

Applying this architecture produces:

- **Client singleton** with separate reader/writer integrations, rate limiting (3 req/s), and exponential-backoff retry
- **Repository layer** (`NotionDatabaseRepo`) encapsulating all Notion API calls with automatic pagination
- **Service layer** (`NotionService`) with business logic, schema validation, and cache-aware operations
- **TTL cache** between the application and the Notion API, reducing redundant reads
- **Event-driven processing** with polling-based change detection and typed event handlers
- **Test suite** with a mocked `@notionhq/client` for fast unit tests and conditional live integration tests

## Error Handling

| Issue | Cause | Solution |
| ------- | ------- | ---------- |
| `401 Unauthorized` | Invalid or expired integration token | Verify `NOTION_TOKEN` at <https://www.notion.so/my-integrations>; tokens do not expire but can be regenerated |
| `404 object_not_found` | Page/database not shared with integration | In Notion, click "..." on the page, select "Add connections", and add the integration |
| `400 validation_error: property not found` | Property name mismatch (case-sensitive) | Call `databases.retrieve()` first to get exact property names; use schema validation before bulk ops |
| `429 rate_limited` | Exceeded 3 req/s per integration | The `withRetry` wrapper handles this automatically; for sustained throughput, use separate reader/writer integrations to double capacity |
| `502/503 server errors` | Notion service degradation | Check <https://status.notion.so>; the retry wrapper auto-recovers with backoff |
| Stale cache data | Cache TTL too long for write-heavy workloads | Invalidate on writes (shown in `NotionService.createTask`); reduce TTL for volatile databases |
| Polling misses changes | Poll interval too wide or clock skew | Use 10s intervals; store `last_edited_time` from the most recent page, not the system clock |

## Safety Justification

This skill scaffolds a multi-file TypeScript project, so it needs `Write`/`Edit`
alongside shell access — a combination that warrants explicit scoping:

- **Bash is scoped, not blanket.** Only `Bash(npm:*)` (install `@notionhq/client`, run `npm test`) and `Bash(npx:*)` (run TypeScript tooling like `npx tsc`/`npx vitest`) are granted — no arbitrary subprocesses, no `curl`-pipe-shell surface.
- **Write/Edit scope is the project source tree.** The skill creates files only under the layout shown in the implementation reference (`src/notion/`, `src/repositories/`, `src/services/`, `src/cache/`, `tests/`); it never writes credentials or touches files outside the project.
- **No secret handling.** `NOTION_TOKEN` is read from the environment by the generated code at runtime; the skill never echoes, fabricates, or persists token values.

## Examples

See [the event-driven and testing reference](references/event-driven-and-testing.md)
for full examples including Notion as Headless CMS, Project/Task Tracker, and
Multi-Integration Architecture patterns.

## Resources

- [Notion API Reference](https://developers.notion.com/reference/intro) — complete endpoint documentation
- [@notionhq/client SDK](https://github.com/makenotion/notion-sdk-js) — official TypeScript/JavaScript SDK
- [Working with Databases](https://developers.notion.com/docs/working-with-databases) — filtering, sorting, pagination
- [Block Types Reference](https://developers.notion.com/reference/block) — all supported content block types
- [Authorization Guide](https://developers.notion.com/docs/authorization) — internal integrations and OAuth
- [Status Page](https://status.notion.so) — check for Notion service degradation

## Next Steps

- For environment-specific configuration, see `notion-multi-env-setup`
- For webhook and polling patterns in depth, see `notion-webhooks-events`
- For performance optimization, see `notion-performance-tuning`
- For error troubleshooting, see `notion-common-errors` and `notion-advanced-troubleshooting`
