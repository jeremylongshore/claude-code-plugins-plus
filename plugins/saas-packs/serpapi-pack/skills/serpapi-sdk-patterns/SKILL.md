---
name: serpapi-sdk-patterns
description: |
  Apply production-ready SerpApi SDK patterns for TypeScript and Python.
  Use when implementing SerpApi integrations, refactoring SDK usage,
  or establishing team coding standards for SerpApi.
  Trigger with phrases like "serpapi SDK patterns", "serpapi best practices",
  "serpapi code patterns", "idiomatic serpapi".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, serpapi]
---

# SerpApi SDK Patterns

## Overview
Production-ready patterns for SerpApi SDK usage in TypeScript and Python.

## Prerequisites
- Completed `serpapi-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/serpapi/client.ts
import { SerpApiClient } from '@serpapi/sdk';

let instance: SerpApiClient | null = null;

export function getSerpApiClient(): SerpApiClient {
  if (!instance) {
    instance = new SerpApiClient({
      apiKey: process.env.SERPAPI_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { SerpApiError } from '@serpapi/sdk';

async function safeSerpApiCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof SerpApiError) {
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
const clients = new Map<string, SerpApiClient>();

export function getClientForTenant(tenantId: string): SerpApiClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new SerpApiClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from serpapi import SerpApiClient

@asynccontextmanager
async def get_serpapi_client():
    client = SerpApiClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const serpapiResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [SerpApi SDK Reference](https://docs.serpapi.com/sdk)
- [SerpApi API Types](https://docs.serpapi.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `serpapi-core-workflow-a` for real-world usage.