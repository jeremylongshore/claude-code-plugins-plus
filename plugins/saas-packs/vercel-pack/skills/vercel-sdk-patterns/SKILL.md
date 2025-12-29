---
name: vercel-sdk-patterns
description: |
  Apply production-ready Vercel SDK patterns for TypeScript and Python.
  Use when implementing Vercel integrations, refactoring SDK usage,
  or establishing team coding standards for Vercel.
  Trigger with phrases like "vercel SDK patterns", "vercel best practices",
  "vercel code patterns", "idiomatic vercel".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Vercel SDK Patterns

## Overview
Production-ready patterns for Vercel SDK usage in TypeScript and Python.

## Prerequisites
- Completed `vercel-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/vercel/client.ts
import { VercelClient } from 'vercel';

let instance: VercelClient | null = null;

export function getVercelClient(): VercelClient {
  if (!instance) {
    instance = new VercelClient({
      apiKey: process.env.VERCEL_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { VercelError } from 'vercel';

async function safeVercelCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof VercelError) {
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
const clients = new Map<string, VercelClient>();

export function getClientForTenant(tenantId: string): VercelClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new VercelClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from None import VercelClient

@asynccontextmanager
async def get_vercel_client():
    client = VercelClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const vercelResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [Vercel SDK Reference](https://vercel.com/docs/sdk)
- [Vercel API Types](https://vercel.com/docs/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `vercel-core-workflow-a` for real-world usage.