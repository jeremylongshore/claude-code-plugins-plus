---
name: clay-sdk-patterns
description: |
  Apply production-ready Clay SDK patterns for TypeScript and Python.
  Use when implementing Clay integrations, refactoring SDK usage,
  or establishing team coding standards for Clay.
  Trigger with phrases like "clay SDK patterns", "clay best practices",
  "clay code patterns", "idiomatic clay".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Clay SDK Patterns

## Overview
Production-ready patterns for Clay SDK usage in TypeScript and Python.

## Prerequisites
- Completed `clay-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/clay/client.ts
import { ClayClient } from '@clay/sdk';

let instance: ClayClient | null = null;

export function getClayClient(): ClayClient {
  if (!instance) {
    instance = new ClayClient({
      apiKey: process.env.CLAY_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { ClayError } from '@clay/sdk';

async function safeClayCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof ClayError) {
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
  backoffMs = 1000  # 1000: 1 second in ms
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
const clients = new Map<string, ClayClient>();

export function getClientForTenant(tenantId: string): ClayClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new ClayClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from clay import ClayClient

@asynccontextmanager
async def get_clay_client():
    client = ClayClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const clayResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [Clay SDK Reference](https://docs.clay.com/sdk)
- [Clay API Types](https://docs.clay.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `clay-core-workflow-a` for real-world usage.