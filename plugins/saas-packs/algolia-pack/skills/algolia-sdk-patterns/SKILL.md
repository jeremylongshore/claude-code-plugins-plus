---
name: algolia-sdk-patterns
description: |
  Apply production-ready Algolia SDK patterns for TypeScript and Python.
  Use when implementing Algolia integrations, refactoring SDK usage,
  or establishing team coding standards for Algolia.
  Trigger with phrases like "algolia SDK patterns", "algolia best practices",
  "algolia code patterns", "idiomatic algolia".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, algolia]
---

# Algolia SDK Patterns

## Overview
Production-ready patterns for Algolia SDK usage in TypeScript and Python.

## Prerequisites
- Completed `algolia-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/algolia/client.ts
import { AlgoliaClient } from '@algolia/sdk';

let instance: AlgoliaClient | null = null;

export function getAlgoliaClient(): AlgoliaClient {
  if (!instance) {
    instance = new AlgoliaClient({
      apiKey: process.env.ALGOLIA_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { AlgoliaError } from '@algolia/sdk';

async function safeAlgoliaCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof AlgoliaError) {
      console.error({
        code: err.code,
        message: err.message,
      });
    }
    return { data: null, error: err as Error };
  }
}
```

### Step 3: Implement Retry Logic
```typescript
async function withRetry<T>(
  operation: () => Promise<T>,
  maxRetries = 3,
  backoffMs = 1000
): Promise<T> {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await operation();
    } catch (err) {
      if (attempt === maxRetries) throw err;
      const delay = backoffMs * Math.pow(2, attempt - 1);
      await new Promise(r => setTimeout(r, delay));
    }
  }
  throw new Error('Unreachable');
}
```

## Output
- Type-safe client singleton
- Robust error handling with structured logging
- Automatic retry with exponential backoff
- Runtime validation for API responses

## Error Handling
| Pattern | Use Case | Benefit |
|---------|----------|---------|
| Safe wrapper | All API calls | Prevents uncaught exceptions |
| Retry logic | Transient failures | Improves reliability |
| Type guards | Response validation | Catches API changes |
| Logging | All operations | Debugging and monitoring |

## Examples

### Factory Pattern (Multi-tenant)
```typescript
const clients = new Map<string, AlgoliaClient>();

export function getClientForTenant(tenantId: string): AlgoliaClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new AlgoliaClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from algolia import AlgoliaClient

@asynccontextmanager
async def get_algolia_client():
    client = AlgoliaClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const algoliaResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [Algolia SDK Reference](https://docs.algolia.com/sdk)
- [Algolia API Types](https://docs.algolia.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `algolia-core-workflow-a` for real-world usage.