---
name: fondo-sdk-patterns
description: |
  Apply production-ready Fondo SDK patterns for TypeScript and Python.
  Use when implementing Fondo integrations, refactoring SDK usage,
  or establishing team coding standards for Fondo.
  Trigger with phrases like "fondo SDK patterns", "fondo best practices",
  "fondo code patterns", "idiomatic fondo".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, fondo]
---

# Fondo SDK Patterns

## Overview
Production-ready patterns for Fondo SDK usage in TypeScript and Python.

## Prerequisites
- Completed `fondo-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/fondo/client.ts
import { FondoClient } from '@fondo/sdk';

let instance: FondoClient | null = null;

export function getFondoClient(): FondoClient {
  if (!instance) {
    instance = new FondoClient({
      apiKey: process.env.FONDO_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { FondoError } from '@fondo/sdk';

async function safeFondoCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof FondoError) {
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
const clients = new Map<string, FondoClient>();

export function getClientForTenant(tenantId: string): FondoClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new FondoClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from fondo import FondoClient

@asynccontextmanager
async def get_fondo_client():
    client = FondoClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const fondoResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [Fondo SDK Reference](https://docs.fondo.com/sdk)
- [Fondo API Types](https://docs.fondo.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `fondo-core-workflow-a` for real-world usage.