---
name: alchemy-sdk-patterns
description: |
  Apply production-ready Alchemy SDK patterns for TypeScript and Python.
  Use when implementing Alchemy integrations, refactoring SDK usage,
  or establishing team coding standards for Alchemy.
  Trigger with phrases like "alchemy SDK patterns", "alchemy best practices",
  "alchemy code patterns", "idiomatic alchemy".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, alchemy]
---

# Alchemy SDK Patterns

## Overview
Production-ready patterns for Alchemy SDK usage in TypeScript and Python.

## Prerequisites
- Completed `alchemy-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/alchemy/client.ts
import { AlchemyClient } from '@alchemy/sdk';

let instance: AlchemyClient | null = null;

export function getAlchemyClient(): AlchemyClient {
  if (!instance) {
    instance = new AlchemyClient({
      apiKey: process.env.ALCHEMY_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { AlchemyError } from '@alchemy/sdk';

async function safeAlchemyCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof AlchemyError) {
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
const clients = new Map<string, AlchemyClient>();

export function getClientForTenant(tenantId: string): AlchemyClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new AlchemyClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from alchemy import AlchemyClient

@asynccontextmanager
async def get_alchemy_client():
    client = AlchemyClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const alchemyResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [Alchemy SDK Reference](https://docs.alchemy.com/sdk)
- [Alchemy API Types](https://docs.alchemy.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `alchemy-core-workflow-a` for real-world usage.