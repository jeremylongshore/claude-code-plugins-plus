---
name: stackblitz-sdk-patterns
description: |
  Apply production-ready StackBlitz SDK patterns for TypeScript and Python.
  Use when implementing StackBlitz integrations, refactoring SDK usage,
  or establishing team coding standards for StackBlitz.
  Trigger with phrases like "stackblitz SDK patterns", "stackblitz best practices",
  "stackblitz code patterns", "idiomatic stackblitz".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, stackblitz]
---

# StackBlitz SDK Patterns

## Overview
Production-ready patterns for StackBlitz SDK usage in TypeScript and Python.

## Prerequisites
- Completed `stackblitz-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/stackblitz/client.ts
import { StackBlitzClient } from '@stackblitz/sdk';

let instance: StackBlitzClient | null = null;

export function getStackBlitzClient(): StackBlitzClient {
  if (!instance) {
    instance = new StackBlitzClient({
      apiKey: process.env.STACKBLITZ_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { StackBlitzError } from '@stackblitz/sdk';

async function safeStackBlitzCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof StackBlitzError) {
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
const clients = new Map<string, StackBlitzClient>();

export function getClientForTenant(tenantId: string): StackBlitzClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new StackBlitzClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from stackblitz import StackBlitzClient

@asynccontextmanager
async def get_stackblitz_client():
    client = StackBlitzClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const stackblitzResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [StackBlitz SDK Reference](https://docs.stackblitz.com/sdk)
- [StackBlitz API Types](https://docs.stackblitz.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `stackblitz-core-workflow-a` for real-world usage.