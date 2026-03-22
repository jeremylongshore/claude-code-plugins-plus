---
name: klaviyo-sdk-patterns
description: |
  Apply production-ready Klaviyo SDK patterns for TypeScript and Python.
  Use when implementing Klaviyo integrations, refactoring SDK usage,
  or establishing team coding standards for Klaviyo.
  Trigger with phrases like "klaviyo SDK patterns", "klaviyo best practices",
  "klaviyo code patterns", "idiomatic klaviyo".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, klaviyo]
---

# Klaviyo SDK Patterns

## Overview
Production-ready patterns for Klaviyo SDK usage in TypeScript and Python.

## Prerequisites
- Completed `klaviyo-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/klaviyo/client.ts
import { KlaviyoClient } from '@klaviyo/sdk';

let instance: KlaviyoClient | null = null;

export function getKlaviyoClient(): KlaviyoClient {
  if (!instance) {
    instance = new KlaviyoClient({
      apiKey: process.env.KLAVIYO_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { KlaviyoError } from '@klaviyo/sdk';

async function safeKlaviyoCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof KlaviyoError) {
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
const clients = new Map<string, KlaviyoClient>();

export function getClientForTenant(tenantId: string): KlaviyoClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new KlaviyoClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from klaviyo import KlaviyoClient

@asynccontextmanager
async def get_klaviyo_client():
    client = KlaviyoClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const klaviyoResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [Klaviyo SDK Reference](https://docs.klaviyo.com/sdk)
- [Klaviyo API Types](https://docs.klaviyo.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `klaviyo-core-workflow-a` for real-world usage.