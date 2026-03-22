---
name: flyio-sdk-patterns
description: |
  Apply production-ready Fly.io SDK patterns for TypeScript and Python.
  Use when implementing Fly.io integrations, refactoring SDK usage,
  or establishing team coding standards for Fly.io.
  Trigger with phrases like "flyio SDK patterns", "flyio best practices",
  "flyio code patterns", "idiomatic flyio".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, flyio]
---

# Fly.io SDK Patterns

## Overview
Production-ready patterns for Fly.io SDK usage in TypeScript and Python.

## Prerequisites
- Completed `flyio-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/flyio/client.ts
import { Fly.ioClient } from '@flyio/sdk';

let instance: Fly.ioClient | null = null;

export function getFly.ioClient(): Fly.ioClient {
  if (!instance) {
    instance = new Fly.ioClient({
      apiKey: process.env.FLYIO_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { Fly.ioError } from '@flyio/sdk';

async function safeFly.ioCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof Fly.ioError) {
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
const clients = new Map<string, Fly.ioClient>();

export function getClientForTenant(tenantId: string): Fly.ioClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new Fly.ioClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from flyio import Fly.ioClient

@asynccontextmanager
async def get_flyio_client():
    client = Fly.ioClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const flyioResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [Fly.io SDK Reference](https://docs.flyio.com/sdk)
- [Fly.io API Types](https://docs.flyio.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `flyio-core-workflow-a` for real-world usage.