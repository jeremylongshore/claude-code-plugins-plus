---
name: intercom-sdk-patterns
description: 'Apply production-ready intercom-client SDK patterns for TypeScript.

  Use when implementing Intercom integrations, refactoring SDK usage,

  or establishing team coding standards for Intercom API calls.

  Trigger with phrases like "intercom SDK patterns", "intercom best practices",

  "intercom code patterns", "idiomatic intercom", "intercom typescript".

  '
allowed-tools: Read, Write, Edit
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
# Intercom SDK Patterns

## Overview

Production-ready patterns for the `intercom-client` TypeScript SDK covering
client initialization, cursor-based pagination, error handling, retry with
backoff, compound search, and multi-tenant client factories. Use this skill to
Read existing Intercom code, then Write or Edit it to match these patterns —
type-safe singletons, memory-efficient pagination, and resilient error handling.

The SKILL.md body carries the essential skeletons (client wrapper, pagination,
error-handling shape). Deep implementations and worked examples live in
`references/` so you can drill in only when you need them:

- [Full implementation patterns](references/implementation.md) — error handling,
  retry/backoff, multi-tenant factory, search-operator table.
- [Worked examples](references/examples.md) — pagination, compound search,
  combined retry + safe-call.

## Prerequisites

- `intercom-client` package installed (`npm install intercom-client`).
- TypeScript 5.0+ project with `strict` mode enabled.
- Familiarity with `async`/`await` and async generators.
- An Intercom access token available at runtime (see Authentication below).

## Authentication

The SDK authenticates with a workspace **access token** passed to the
`IntercomClient` constructor. Store it in the `INTERCOM_ACCESS_TOKEN` environment
variable — never hardcode it. Generate the token from Intercom's Developer Hub
(Settings → Authentication). For multi-workspace apps, each workspace has its own
token; see the multi-tenant factory in
[references/implementation.md](references/implementation.md).

## Instructions

### Step 1: Type-Safe Client Wrapper

Create one lazily-initialized singleton client plus thin, typed helpers. This
keeps a single connection pool and gives every call-site full SDK types.

```typescript
// src/intercom/client.ts
import { IntercomClient } from "intercom-client";
import { Intercom } from "intercom-client";

let instance: IntercomClient | null = null;

export function getClient(): IntercomClient {
  if (!instance) {
    instance = new IntercomClient({
      token: process.env.INTERCOM_ACCESS_TOKEN!,
    });
  }
  return instance;
}

// Type-safe contact creation helper
export async function createContact(
  params: Intercom.CreateContactRequest
): Promise<Intercom.Contact> {
  return getClient().contacts.create(params);
}
```

### Step 2: Cursor-Based Pagination

Intercom lists are cursor-paginated — `starting_after` points to the next page.
Prefer the SDK's built-in async iteration, which manages the cursor for you:

```typescript
const response = await client.articles.list();
for await (const article of response) {
  console.log(article.title);
}
```

When explicit control is needed, an alternative option is a custom generator
that yields each item and advances `startingAfter` until the cursor is
exhausted. Choose auto-iteration for simplicity, or the manual generator when a
custom `perPage`, early exit, or per-page side effects are required. Both
variants: [references/examples.md](references/examples.md).

### Step 3: Error Handling and Retry

Wrap every call so a thrown `IntercomError` becomes a normalized
`{ data, error }` result, then layer retry/backoff on transient failures (429,
5xx). Skeleton:

```typescript
import { IntercomError } from "intercom-client";

try {
  const data = await client.contacts.find({ contactId: "abc123" });
  // use data
} catch (err) {
  if (err instanceof IntercomError) {
    // inspect err.statusCode (401/404/409/422/429), err.body?.errors
  }
  throw err; // re-throw non-Intercom errors
}
```

Full `safeIntercomCall` wrapper, `withRetry` exponential-backoff helper (with
`Retry-After` support), and compound search live in
[references/implementation.md](references/implementation.md).

## Output

Applying this skill produces TypeScript source that follows these patterns:

- A singleton client module (e.g. `src/intercom/client.ts`) exporting `getClient`
  and typed helpers.
- Pagination code that streams items via async iteration instead of buffering
  full result sets.
- API calls wrapped in `safeIntercomCall` returning `{ data, error }`, with
  `withRetry` applied to rate-limited and server-error responses.
- No hardcoded tokens — all auth reads `INTERCOM_ACCESS_TOKEN` (or a per-workspace
  token via the factory).

## Error Handling

| Pattern | Use Case | Benefit |
|---------|----------|---------|
| `safeIntercomCall` wrapper | All API calls | Prevents uncaught exceptions |
| `withRetry` | Transient failures (429, 5xx) | Automatic recovery |
| Cursor pagination generator | Large data sets | Memory-efficient streaming |
| Client factory | Multi-tenant apps | Workspace isolation |

Status codes to handle explicitly: `401` (bad/expired token), `404` (missing
resource), `409` (conflict/duplicate), `422` (validation — check
`err.body?.errors`), `429` (rate limited — back off). Full switch-based handler:
[references/implementation.md](references/implementation.md).

## Examples

- **Pagination** — manual generator plus SDK auto-iteration:
  [references/examples.md](references/examples.md).
- **Compound search** — AND/OR conditions with sort and pagination:
  [references/examples.md](references/examples.md).
- **Resilient call** — `withRetry` composed with `safeIntercomCall`:
  [references/examples.md](references/examples.md).

Minimal end-to-end shape:

```typescript
import { getClient } from "./intercom/client";

const client = getClient();
const contact = await client.contacts.create({
  role: "user",
  email: "new@acme.com",
});
console.log(contact.id);
```

## Resources

- [intercom-client npm](https://www.npmjs.com/package/intercom-client)
- [Intercom API Reference](https://developers.intercom.com/docs/references/rest-api/api.intercom.io)
- [Search Contacts](https://developers.intercom.com/docs/references/rest-api/api.intercom.io/contacts/searchcontacts)

## Next Steps

Apply these patterns alongside `intercom-core-workflow-a` for contact management
workflows. For the full implementation catalog and worked examples, open
[references/implementation.md](references/implementation.md) and
[references/examples.md](references/examples.md).
