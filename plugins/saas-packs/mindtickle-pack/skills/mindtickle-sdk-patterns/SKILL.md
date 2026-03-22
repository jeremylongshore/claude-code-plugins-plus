---
name: mindtickle-sdk-patterns
description: |
  Apply production-ready Mindtickle SDK patterns for TypeScript and Python.
  Use when implementing Mindtickle integrations, refactoring SDK usage,
  or establishing team coding standards for Mindtickle.
  Trigger with phrases like "mindtickle SDK patterns", "mindtickle best practices",
  "mindtickle code patterns", "idiomatic mindtickle".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, mindtickle]
---

# Mindtickle SDK Patterns

## Overview
Production-ready patterns for Mindtickle SDK usage in TypeScript and Python.

## Prerequisites
- Completed `mindtickle-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/mindtickle/client.ts
import { MindtickleClient } from '@mindtickle/sdk';

let instance: MindtickleClient | null = null;

export function getMindtickleClient(): MindtickleClient {
  if (!instance) {
    instance = new MindtickleClient({
      apiKey: process.env.MINDTICKLE_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { MindtickleError } from '@mindtickle/sdk';

async function safeMindtickleCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof MindtickleError) {
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
const clients = new Map<string, MindtickleClient>();

export function getClientForTenant(tenantId: string): MindtickleClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new MindtickleClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from mindtickle import MindtickleClient

@asynccontextmanager
async def get_mindtickle_client():
    client = MindtickleClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const mindtickleResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [Mindtickle SDK Reference](https://docs.mindtickle.com/sdk)
- [Mindtickle API Types](https://docs.mindtickle.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `mindtickle-core-workflow-a` for real-world usage.