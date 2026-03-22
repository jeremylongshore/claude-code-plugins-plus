---
name: granola-sdk-patterns
description: |
  Apply production-ready Granola SDK patterns for TypeScript and Python.
  Use when implementing Granola integrations, refactoring SDK usage,
  or establishing team coding standards for Granola.
  Trigger with phrases like "granola SDK patterns", "granola best practices",
  "granola code patterns", "idiomatic granola".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, granola]
---

# Granola SDK Patterns

## Overview
Production-ready patterns for Granola SDK usage in TypeScript and Python.

## Prerequisites
- Completed `granola-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/granola/client.ts
import { GranolaClient } from '@granola/sdk';

let instance: GranolaClient | null = null;

export function getGranolaClient(): GranolaClient {
  if (!instance) {
    instance = new GranolaClient({
      apiKey: process.env.GRANOLA_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { GranolaError } from '@granola/sdk';

async function safeGranolaCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof GranolaError) {
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
const clients = new Map<string, GranolaClient>();

export function getClientForTenant(tenantId: string): GranolaClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new GranolaClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from granola import GranolaClient

@asynccontextmanager
async def get_granola_client():
    client = GranolaClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const granolaResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [Granola SDK Reference](https://docs.granola.com/sdk)
- [Granola API Types](https://docs.granola.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `granola-core-workflow-a` for real-world usage.