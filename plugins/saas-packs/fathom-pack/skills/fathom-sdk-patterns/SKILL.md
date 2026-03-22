---
name: fathom-sdk-patterns
description: |
  Apply production-ready Fathom SDK patterns for TypeScript and Python.
  Use when implementing Fathom integrations, refactoring SDK usage,
  or establishing team coding standards for Fathom.
  Trigger with phrases like "fathom SDK patterns", "fathom best practices",
  "fathom code patterns", "idiomatic fathom".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, fathom]
---

# Fathom SDK Patterns

## Overview
Production-ready patterns for Fathom SDK usage in TypeScript and Python.

## Prerequisites
- Completed `fathom-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/fathom/client.ts
import { FathomClient } from '@fathom/sdk';

let instance: FathomClient | null = null;

export function getFathomClient(): FathomClient {
  if (!instance) {
    instance = new FathomClient({
      apiKey: process.env.FATHOM_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { FathomError } from '@fathom/sdk';

async function safeFathomCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof FathomError) {
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
const clients = new Map<string, FathomClient>();

export function getClientForTenant(tenantId: string): FathomClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new FathomClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from fathom import FathomClient

@asynccontextmanager
async def get_fathom_client():
    client = FathomClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const fathomResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [Fathom SDK Reference](https://docs.fathom.com/sdk)
- [Fathom API Types](https://docs.fathom.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `fathom-core-workflow-a` for real-world usage.