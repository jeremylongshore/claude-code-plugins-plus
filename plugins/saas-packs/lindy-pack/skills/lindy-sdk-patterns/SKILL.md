---
name: lindy-sdk-patterns
description: |
  Apply production-ready Lindy SDK patterns for TypeScript and Python.
  Use when implementing Lindy integrations, refactoring SDK usage,
  or establishing team coding standards for Lindy.
  Trigger with phrases like "lindy SDK patterns", "lindy best practices",
  "lindy code patterns", "idiomatic lindy".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, lindy]
---

# Lindy SDK Patterns

## Overview
Production-ready patterns for Lindy SDK usage in TypeScript and Python.

## Prerequisites
- Completed `lindy-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/lindy/client.ts
import { LindyClient } from '@lindy/sdk';

let instance: LindyClient | null = null;

export function getLindyClient(): LindyClient {
  if (!instance) {
    instance = new LindyClient({
      apiKey: process.env.LINDY_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { LindyError } from '@lindy/sdk';

async function safeLindyCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof LindyError) {
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
const clients = new Map<string, LindyClient>();

export function getClientForTenant(tenantId: string): LindyClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new LindyClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from lindy import LindyClient

@asynccontextmanager
async def get_lindy_client():
    client = LindyClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const lindyResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [Lindy SDK Reference](https://docs.lindy.com/sdk)
- [Lindy API Types](https://docs.lindy.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `lindy-core-workflow-a` for real-world usage.