---
name: klaviyo-reference-architecture
description: 'Implement Klaviyo reference architecture with best-practice project
  layout.

  Use when designing new Klaviyo integrations, reviewing project structure,

  or establishing architecture standards for email/SMS marketing applications.

  Trigger with phrases like "klaviyo architecture", "klaviyo project structure",

  "klaviyo design", "how to organize klaviyo", "klaviyo layout".

  '
allowed-tools: Read, Write, Edit, Grep
version: 1.7.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- klaviyo
- email-marketing
- cdp
compatibility: Designed for Claude Code
---
# Klaviyo Reference Architecture

## Overview

Production-ready architecture for Klaviyo integrations: a layered project structure, service patterns, event-driven sync, and the `klaviyo-api` SDK wired into a real application. SKILL.md gives you the four-layer contract and the skeleton you scaffold from; the deep material lives in `references/` so you pull code only when you reach that layer.

- **Layout & layering** (full directory tree, layer contract, data flow): [architecture.md](references/architecture.md)
- **Working code for every layer** (config, profile sync, event tracker): [implementation.md](references/implementation.md)

## Prerequisites

- TypeScript project with `klaviyo-api` installed
- Understanding of layered architecture
- Redis (for caching/queuing) and database (for audit/sync state)

## Instructions

Use **Write** to scaffold the directory tree, then fill each layer bottom-up. The four layers and their one-way call rule:

```
API / Webhook Layer   →  routes + webhook handlers (calls Service only)
Service Layer         →  profile-sync, event-tracker, campaigns (calls SDK + Infra)
Klaviyo SDK Layer     →  ApiKeySession, ProfilesApi, EventsApi (never calls upward)
Infrastructure Layer  →  Redis cache, BullMQ queue, Prisma DB, OTel monitoring
```

1. **Scaffold the tree.** Create the `src/{klaviyo,services,webhooks,jobs,middleware,config,health}` layout. Full annotated tree: [architecture.md](references/architecture.md).
2. **Config layer first.** A single `loadConfig()` returns environment-specific keys, rate limits, and cache TTLs — every other layer reads from it. Code: [implementation.md](references/implementation.md) Step 1.
3. **Service layer.** Build `ProfileSyncService` (bidirectional upsert) and `EventTracker` (server-side `Placed Order` / custom events). Both route Klaviyo calls through `withRateLimitRetry`. Code: [implementation.md](references/implementation.md) Steps 2–3.
4. **Wire the data flow.** Signup → `syncToKlaviyo()`, purchase → `trackPurchase()`, inbound `profile.updated` webhook → `WebhookRouter.routeEvent()` → local DB. Diagram: [architecture.md](references/architecture.md).

When reviewing an existing project, **Read** its `src/` tree and **Grep** for cross-layer imports that break the one-way rule (SDK importing a service, a route importing the SDK directly).

## Output

Applying this skill produces:

- A scaffolded `src/` tree matching the four-layer contract, with SDK, service, webhook, job, middleware, config, and health directories.
- A working `config/klaviyo.ts` plus `ProfileSyncService` and `EventTracker` service classes ready to call from routes and jobs.
- For a review pass: a list of layering violations (upward SDK calls, direct SDK use from routes) and sync-safety gaps to fix.

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Circular deps | Wrong layering | Services call SDK, never the reverse |
| Sync conflicts | Both sides update | Last-write-wins with sync timestamp |
| Queue backlog | Klaviyo slow/down | Circuit breaker + dead letter queue |
| Type mismatches | SDK version mismatch | Pin SDK version, run `tsc --noEmit` in CI |

## Examples

**Scaffold a new integration** — "Set up a Klaviyo integration for our Node app." Create the layered tree, drop in `loadConfig()`, then `ProfileSyncService` and `EventTracker`. Full code per step: [implementation.md](references/implementation.md).

**Track a purchase from your backend:**

```typescript
await new EventTracker().trackPurchase({
  email: order.email,
  orderId: order.id,
  total: order.total,
  items: order.lineItems,
});
```

**Review project structure** — "Is our Klaviyo code layered correctly?" Grep for imports that violate the one-way call rule and check webhook handlers verify HMAC signatures. Layer contract: [architecture.md](references/architecture.md).

## Resources

- [Klaviyo API Reference](https://developers.klaviyo.com/en/reference/api_overview)
- [Custom Integration Guide](https://developers.klaviyo.com/en/docs/guide_to_integrating_a_platform_without_a_pre_built_klaviyo_integration)
- [Ecommerce Integration Guide](https://developers.klaviyo.com/en/docs/guide_to_integrating_a_platform_without_a_pre_built_klaviyo_integration)

## Next Steps

For multi-environment configuration and per-stage key management, see the `klaviyo-multi-env-setup` skill in this pack.
