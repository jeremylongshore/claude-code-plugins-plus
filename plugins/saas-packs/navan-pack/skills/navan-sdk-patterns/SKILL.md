---
name: navan-sdk-patterns
description: |
  Apply production-ready Navan SDK patterns for TypeScript and Python.
  Use when implementing Navan integrations, refactoring SDK usage,
  or establishing team coding standards for Navan.
  Trigger with phrases like "navan SDK patterns", "navan best practices",
  "navan code patterns", "idiomatic navan".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, navan]
---

# Navan SDK Patterns

## Overview
Production-ready patterns for Navan SDK usage in TypeScript and Python.

## Prerequisites
- Completed `navan-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/navan/client.ts
import { NavanClient } from '@navan/sdk';

let instance: NavanClient | null = null;

export function getNavanClient(): NavanClient {
  if (!instance) {
    instance = new NavanClient({
      apiKey: process.env.NAVAN_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { NavanError } from '@navan/sdk';

async function safeNavanCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof NavanError) {
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
const clients = new Map<string, NavanClient>();

export function getClientForTenant(tenantId: string): NavanClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new NavanClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from navan import NavanClient

@asynccontextmanager
async def get_navan_client():
    client = NavanClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const navanResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [Navan SDK Reference](https://docs.navan.com/sdk)
- [Navan API Types](https://docs.navan.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `navan-core-workflow-a` for real-world usage.