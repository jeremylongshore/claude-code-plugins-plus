---
name: intercom-sdk-patterns
description: |
  Apply production-ready intercom-client SDK patterns for TypeScript.
  Use when implementing Intercom integrations, refactoring SDK usage,
  or establishing team coding standards for Intercom API calls.
  Trigger with phrases like "intercom SDK patterns", "intercom best practices",
  "intercom code patterns", "idiomatic intercom", "intercom typescript".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, support, messaging, intercom]
compatible-with: claude-code
---

# Intercom SDK Patterns

## Overview

Production-ready patterns for the `intercom-client` TypeScript SDK covering client initialization, pagination, error handling, and type safety.

## Prerequisites

- `intercom-client` package installed
- TypeScript 5.0+ project
- Familiarity with async/await and generators

## Instructions

### Step 1: Type-Safe Client Wrapper

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

// Type-safe search helper
export async function searchContacts(
  query: Intercom.SearchRequest
): Promise<Intercom.ContactList> {
  return getClient().contacts.search(query);
}
```

### Step 2: Cursor-Based Pagination

Intercom uses cursor-based pagination. The `starting_after` parameter points to the next page.

```typescript
// Generic paginator for any list endpoint
async function* paginateContacts(
  client: IntercomClient,
  perPage = 50
): AsyncGenerator<Intercom.Contact> {
  let startingAfter: string | undefined;

  do {
    const page = await client.contacts.list({
      perPage,
      startingAfter,
    });

    for (const contact of page.data) {
      yield contact;
    }

    // Cursor for next page
    startingAfter = page.pages?.next?.startingAfter ?? undefined;
  } while (startingAfter);
}

// Usage
const client = getClient();
for await (const contact of paginateContacts(client)) {
  console.log(contact.email);
}
```

The SDK also supports built-in iteration:

```typescript
// SDK auto-pagination (articles, contacts, etc.)
const response = await client.articles.list();
for await (const article of response) {
  console.log(article.title);
}
```

### Step 3: Error Handling with IntercomError

```typescript
import { IntercomError } from "intercom-client";

async function safeIntercomCall<T>(
  operation: () => Promise<T>,
  context: string
): Promise<{ data: T | null; error: IntercomError | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof IntercomError) {
      console.error(`[Intercom:${context}] ${err.statusCode}: ${err.message}`, {
        requestId: err.body?.request_id,
        errors: err.body?.errors,
      });

      // Specific error handling
      switch (err.statusCode) {
        case 401:
          console.error("Token invalid or expired. Regenerate access token.");
          break;
        case 404:
          console.error("Resource not found. Verify the ID.");
          break;
        case 409:
          console.error("Conflict: resource already exists.");
          break;
        case 422:
          console.error("Validation failed:", err.body?.errors);
          break;
        case 429:
          console.error("Rate limited. Back off and retry.");
          break;
      }

      return { data: null, error: err };
    }
    throw err; // Re-throw non-Intercom errors
  }
}

// Usage
const { data: contact, error } = await safeIntercomCall(
  () => client.contacts.find({ contactId: "abc123" }),
  "findContact"
);
```

### Step 4: Retry with Exponential Backoff

```typescript
async function withRetry<T>(
  operation: () => Promise<T>,
  config = { maxRetries: 3, baseDelayMs: 1000 }
): Promise<T> {
  for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
    try {
      return await operation();
    } catch (err) {
      if (err instanceof IntercomError) {
        // Only retry on rate limits and server errors
        if (err.statusCode !== 429 && (err.statusCode ?? 0) < 500) {
          throw err;
        }

        if (attempt === config.maxRetries) throw err;

        // Use Retry-After header if available, otherwise exponential backoff
        const retryAfter = err.headers?.["retry-after"];
        const delay = retryAfter
          ? parseInt(retryAfter) * 1000
          : config.baseDelayMs * Math.pow(2, attempt) + Math.random() * 500;

        console.log(`Retry ${attempt + 1}/${config.maxRetries} in ${delay}ms`);
        await new Promise((r) => setTimeout(r, delay));
      } else {
        throw err;
      }
    }
  }
  throw new Error("Unreachable");
}
```

### Step 5: Contact Search with Compound Queries

```typescript
// Search with multiple conditions (AND/OR)
const results = await client.contacts.search({
  query: {
    operator: "AND",
    value: [
      { field: "role", operator: "=", value: "user" },
      { field: "custom_attributes.plan", operator: "=", value: "pro" },
      {
        operator: "OR",
        value: [
          { field: "email", operator: "~", value: "@acme.com" },
          { field: "email", operator: "~", value: "@bigcorp.com" },
        ],
      },
    ],
  },
  pagination: { per_page: 25 },
  sort: { field: "created_at", order: "descending" },
});
```

### Step 6: Multi-Tenant Client Factory

```typescript
const clientCache = new Map<string, IntercomClient>();

export function getClientForWorkspace(
  workspaceToken: string
): IntercomClient {
  if (!clientCache.has(workspaceToken)) {
    clientCache.set(
      workspaceToken,
      new IntercomClient({ token: workspaceToken })
    );
  }
  return clientCache.get(workspaceToken)!;
}
```

## Intercom Search Operators

| Operator | Meaning | Example |
|----------|---------|---------|
| `=` | Equals | `email = "test@example.com"` |
| `!=` | Not equals | `role != "lead"` |
| `~` | Contains | `email ~ "@acme.com"` |
| `!~` | Not contains | `name !~ "test"` |
| `>` | Greater than | `created_at > 1700000000` |
| `<` | Less than | `last_seen_at < 1700000000` |
| `IN` | In list | `tag_id IN ["tag1", "tag2"]` |
| `NIN` | Not in list | `segment_id NIN ["seg1"]` |

## Error Handling

| Pattern | Use Case | Benefit |
|---------|----------|---------|
| `safeIntercomCall` wrapper | All API calls | Prevents uncaught exceptions |
| `withRetry` | Transient failures (429, 5xx) | Automatic recovery |
| Cursor pagination generator | Large data sets | Memory-efficient streaming |
| Client factory | Multi-tenant apps | Workspace isolation |

## Resources

- [intercom-client npm](https://www.npmjs.com/package/intercom-client)
- [Intercom API Reference](https://developers.intercom.com/docs/references/rest-api/api.intercom.io)
- [Search Contacts](https://developers.intercom.com/docs/references/rest-api/api.intercom.io/contacts/searchcontacts)

## Next Steps

Apply patterns in `intercom-core-workflow-a` for contact management workflows.
