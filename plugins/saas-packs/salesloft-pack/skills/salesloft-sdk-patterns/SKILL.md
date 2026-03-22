---
name: salesloft-sdk-patterns
description: |
  Apply production-ready Salesloft SDK patterns for TypeScript and Python.
  Use when implementing Salesloft integrations, refactoring SDK usage,
  or establishing team coding standards for Salesloft.
  Trigger with phrases like "salesloft SDK patterns", "salesloft best practices",
  "salesloft code patterns", "idiomatic salesloft".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, salesloft]
---

# Salesloft SDK Patterns

## Overview
Production-ready patterns for Salesloft SDK usage in TypeScript and Python.

## Prerequisites
- Completed `salesloft-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/salesloft/client.ts
import { SalesloftClient } from '@salesloft/sdk';

let instance: SalesloftClient | null = null;

export function getSalesloftClient(): SalesloftClient {
  if (!instance) {
    instance = new SalesloftClient({
      apiKey: process.env.SALESLOFT_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { SalesloftError } from '@salesloft/sdk';

async function safeSalesloftCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof SalesloftError) {
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
const clients = new Map<string, SalesloftClient>();

export function getClientForTenant(tenantId: string): SalesloftClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new SalesloftClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from salesloft import SalesloftClient

@asynccontextmanager
async def get_salesloft_client():
    client = SalesloftClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const salesloftResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [Salesloft SDK Reference](https://docs.salesloft.com/sdk)
- [Salesloft API Types](https://docs.salesloft.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `salesloft-core-workflow-a` for real-world usage.