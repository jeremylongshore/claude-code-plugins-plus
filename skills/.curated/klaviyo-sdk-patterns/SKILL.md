---
name: klaviyo-sdk-patterns
description: 'Apply production-ready Klaviyo SDK patterns for the klaviyo-api package.

  Use when implementing Klaviyo integrations, refactoring SDK usage,

  or establishing team coding standards for Klaviyo API calls.

  Trigger with phrases like "klaviyo SDK patterns", "klaviyo best practices",

  "klaviyo code patterns", "idiomatic klaviyo", "klaviyo wrapper".

  '
allowed-tools: Read, Write, Edit
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
# Klaviyo SDK Patterns

## Overview

Production-ready patterns for the `klaviyo-api` Node.js SDK: singleton
sessions, type-safe wrappers, retry logic, cursor pagination, and multi-tenant
support. Read the target project's Klaviyo files, then Write or Edit the
`src/klaviyo/` modules below into place so every call goes through one
consistent, retry-aware layer instead of ad-hoc `new ApiKeySession(...)` calls
scattered across the codebase.

The six patterns are summarized here with the essential skeleton; the full,
copy-paste implementation for all of them lives in
[references/implementation.md](references/implementation.md), and combined
worked examples with expected output are in
[references/examples.md](references/examples.md).

## Prerequisites

- `klaviyo-api` package installed in the target project.
- The `klaviyo-install-auth` setup completed, so `KLAVIYO_PRIVATE_KEY` is
  available in the environment.
- A TypeScript project with `strict` mode enabled — every pattern is typed.

## Instructions

### Step 1: Singleton session (the foundation)

Create one lazily-initialized `ApiKeySession` and reuse it everywhere. Read the
key from the environment, fail fast if it is missing, and expose a reset hook
for tests.

```typescript
// src/klaviyo/session.ts
import { ApiKeySession } from 'klaviyo-api';

let _session: ApiKeySession | null = null;

export function getSession(apiKey?: string): ApiKeySession {
  if (!_session) {
    const key = apiKey || process.env.KLAVIYO_PRIVATE_KEY;
    if (!key) throw new Error('KLAVIYO_PRIVATE_KEY is required');
    _session = new ApiKeySession(key);
  }
  return _session;
}
export function resetSession(): void { _session = null; }
```

### Steps 2-6: the rest of the layer

Each builds on the session singleton. Write the corresponding file from
[references/implementation.md](references/implementation.md):

- **Step 2 — Type-safe API wrapper** (`api.ts`): lazy getters for all 11 API
  clients (Profiles, Events, Lists, …) so unused clients are never constructed.
- **Step 3 — Error wrapper** (`errors.ts`): `parseKlaviyoError` normalizes the
  raw error and `safeCall` returns `{ data, error }` instead of throwing.
- **Step 4 — Retry** (`retry.ts`): `withRetry` retries only on `429`/`5xx`,
  honoring Klaviyo's `Retry-After` header, else exponential backoff with jitter.
- **Step 5 — Pagination** (`pagination.ts`): `paginate` turns any cursor-based
  list endpoint into an `AsyncGenerator`, extracting `page[cursor]` for you.
- **Step 6 — Multi-tenant factory** (`multi-tenant.ts`): `getApisForTenant`
  caches one client set per tenant id, isolating each customer's API key.

## Output

Applying this skill produces a `src/klaviyo/` module set:

| File | Exports | Purpose |
|------|---------|---------|
| `session.ts` | `getSession`, `resetSession` | One shared authenticated session |
| `api.ts` | default `apis` | Lazy, type-safe access to every API client |
| `errors.ts` | `parseKlaviyoError`, `safeCall` | Non-throwing typed error results |
| `retry.ts` | `withRetry` | Rate-limit/5xx retry honoring `Retry-After` |
| `pagination.ts` | `paginate` | Async iteration over cursor pages |
| `multi-tenant.ts` | `getApisForTenant` | Per-tenant client isolation |

Callers then read as `const { data, error } = await safeCall(() => apis.profiles.getProfiles(...))`
instead of managing sessions and try/catch by hand.

## SDK Conventions

| Convention | Example |
|-----------|---------|
| Property casing | `firstName` (not `first_name`) |
| Response access | `response.body.data` (not `response.data`) |
| Payload structure | `{ data: { type: 'profile', attributes: { ... } } }` |
| Filter syntax | `equals(email,"user@example.com")` |
| Sort syntax | `'-datetime'` (descending), `'datetime'` (ascending) |
| Include relations | `{ include: ['lists'] }` |

## Error Handling

| Error | Status | Retryable | Solution |
|-------|--------|-----------|----------|
| Invalid API key | 401 | No | Check KLAVIYO_PRIVATE_KEY |
| Missing scope | 403 | No | Add required scope to API key |
| Validation error | 400 | No | Fix request payload |
| Rate limited | 429 | Yes | Honor Retry-After header |
| Server error | 500/503 | Yes | Retry with backoff |
| Conflict | 409 | No | Resource already exists; use update |

## Examples

A quick taste — wrap any call so a failure returns a typed error instead of
throwing:

```typescript
import apis from './klaviyo/api';
import { safeCall } from './klaviyo/errors';

const { data, error } = await safeCall(
  () => apis.profiles.getProfiles({ pageSize: 20 }),
  'list profiles',
);
if (error) console.error(`Failed (${error.status}):`, error.errors[0].detail);
else console.log(`Fetched ${data!.body.data.length} profiles`);
```

Full worked examples — retrying a rate-limited write, paginating every profile,
and serving two tenants from one process, each with expected output — are in
[references/examples.md](references/examples.md).

## Resources

- [klaviyo-api-node README](https://github.com/klaviyo/klaviyo-api-node/blob/main/README.md)
- [API Overview](https://developers.klaviyo.com/en/reference/api_overview)
- [API Versioning](https://developers.klaviyo.com/en/docs/api_versioning_and_deprecation_policy)

## Next Steps

Once the `src/klaviyo/` layer is in place, apply the patterns in
`klaviyo-core-workflow-a` for profile and list management — those workflows
assume `apis`, `safeCall`, `withRetry`, and `paginate` already exist.
