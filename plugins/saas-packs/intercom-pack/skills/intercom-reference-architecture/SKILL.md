---
name: intercom-reference-architecture
description: 'Implement Intercom reference architecture with layered project structure.

  Use when designing new Intercom integrations, reviewing project structure,

  or establishing architecture standards for Intercom applications.

  Trigger with phrases like "intercom architecture", "intercom project structure",

  "how to organize intercom", "intercom layout", "intercom design patterns".

  '
allowed-tools: Read, Grep
version: 1.6.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- support
- messaging
- intercom
compatibility: Designed for Claude Code
---
# Intercom Reference Architecture

## Overview

A production-ready reference architecture for Intercom integrations built on
four layers — API/webhook, service, Intercom client, and infrastructure — with
type-safe SDK usage, webhook processing, contact sync, and Help Center
management. Use it to scaffold a new integration or to review an existing one
against a known-good structure.

The layers (top to bottom): the **API / Webhook layer** (Express routes, webhook
endpoints) calls into the **service layer** (contacts, conversations, articles —
business logic and orchestration), which calls the **Intercom client layer** (a
singleton `intercom-client` SDK wrapper with typed errors, caching, and rate
limit handling), all resting on **infrastructure** (Redis cache, job queue,
monitoring). Keeping dependencies flowing strictly downward is what prevents the
circular imports and test-isolation problems listed under Error Handling.

## Prerequisites

- Node.js project with TypeScript and the `intercom-client` npm package
  installed.
- An **Intercom access token** — the SDK authenticates every request with a
  Bearer token read from the `INTERCOM_ACCESS_TOKEN` environment variable (see
  Step 1). Create one under Intercom → Developer Hub → your app →
  Authentication. Never commit it; load it from the environment.
- For webhook verification, your app's **client secret** to validate the
  `X-Hub-Signature` header on inbound webhook POSTs.
- Redis (optional) if you enable the caching layer.

## Instructions

Use `Read`/`Grep` to inspect the current project layout, then build each layer
in order — the client layer is the dependency root for every service.

1. **Client layer** (`src/intercom/client.ts`) — a lazy singleton
   `getClient()` that reads `INTERCOM_ACCESS_TOKEN` once, plus an
   `IntercomServiceError` that wraps raw SDK errors into a typed, retry-aware
   shape. Skeleton:

   ```typescript
   let instance: IntercomClient | null = null;
   export function getClient(): IntercomClient {
     if (!instance) {
       const token = process.env.INTERCOM_ACCESS_TOKEN;
       if (!token) throw new Error("INTERCOM_ACCESS_TOKEN required");
       instance = new IntercomClient({ token });
     }
     return instance;
   }
   ```

2. **Contacts service** (`src/services/contacts.service.ts`) —
   `findOrCreate` (search-before-create to avoid 409s), `syncFromCRM`,
   `mergeLead`, and a `searchAll` async generator for cursor pagination.
3. **Conversations service** (`src/services/conversations.service.ts`) —
   `replyAsAdmin`, `addNote`, `closeWithMessage`, and a scoped open-queue
   search.
4. **Articles service** (`src/services/articles.service.ts`) — Help Center
   article create/list, defaulting new articles to `draft`.
5. **Wire the data flow** — Intercom pushes events to your webhook router; the
   service layer makes API calls back and persists to your database + cache.

The full project tree, every service method, and the layer/data-flow diagrams
are in [the full implementation walkthrough](references/implementation.md); the
complete directory layout is in
[project-structure.md](references/project-structure.md).

## Output

Applying this skill produces a layered Intercom integration:

- A `src/intercom/` client layer (singleton SDK wrapper + typed errors).
- A `src/services/` layer with contacts, conversations, and articles services.
- `src/webhooks/`, `src/sync/`, `src/api/`, and `src/cache/` directories wired
  to the layers above.
- Per-environment `config/` files and a `tests/` tree with unit + integration
  suites.

When used to review an existing project, the output is a gap report: which
layers exist, which are missing, and where dependency direction is violated.

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Circular dependencies | Service A imports B imports A | Use dependency injection |
| Client initialization race | Async token fetch | Lazy singleton pattern |
| Cache inconsistency | Stale data after update | Webhook-driven invalidation |
| Test isolation | Shared SDK state | `resetClient()` in beforeEach |
| `401 Unauthorized` | Missing/invalid `INTERCOM_ACCESS_TOKEN` | Verify the env var is loaded before `getClient()` |
| `429 Too Many Requests` | Rate limit exceeded | Retry with backoff — `IntercomServiceError.retryable` is `true` here |

## Examples

Once the client and service layers exist, wiring them together is a few lines —
sync a CRM user, reply to and close a conversation, page through contacts, or
publish an article:

```typescript
const contacts = new ContactsService();
const contact = await contacts.syncFromCRM({
  id: "crm_8842", email: "ada@example.com", name: "Ada Lovelace",
  plan: "enterprise", company: "Analytical Engines Ltd",
});
```

See [examples.md](references/examples.md) for the full set of runnable usage
snippets (conversation reply/close, paginated search, Help Center publish).

## Resources

- [Full implementation walkthrough](references/implementation.md) — every layer, method, and diagram
- [Project structure reference](references/project-structure.md) — complete directory tree
- [Usage examples](references/examples.md) — runnable wiring snippets
- [Intercom API Reference](https://developers.intercom.com/docs/references/rest-api/api.intercom.io)
- [Articles API](https://developers.intercom.com/docs/references/rest-api/api.intercom.io/articles)
- [Help Center API](https://developers.intercom.com/docs/references/rest-api/api.intercom.io/help-center)
- [intercom-client npm](https://www.npmjs.com/package/intercom-client)

## Next Steps

For multi-environment configuration and deployment, see the
`intercom-multi-env-setup` skill, which extends the `config/` layer described
above into per-environment credential and rate-limit management.
