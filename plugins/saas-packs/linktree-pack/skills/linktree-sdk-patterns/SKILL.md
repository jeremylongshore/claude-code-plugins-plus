---
name: linktree-sdk-patterns
description: |
  Apply production-ready Linktree SDK patterns for TypeScript and Python.
  Use when implementing Linktree integrations, refactoring SDK usage,
  or establishing team coding standards for Linktree.
  Trigger with phrases like "linktree SDK patterns", "linktree best practices",
  "linktree code patterns", "idiomatic linktree".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, linktree]
---

# Linktree SDK Patterns

## Overview
Production-ready patterns for Linktree SDK usage in TypeScript and Python.

## Prerequisites
- Completed `linktree-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/linktree/client.ts
import { LinktreeClient } from '@linktree/sdk';

let instance: LinktreeClient | null = null;

export function getLinktreeClient(): LinktreeClient {
  if (!instance) {
    instance = new LinktreeClient({
      apiKey: process.env.LINKTREE_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { LinktreeError } from '@linktree/sdk';

async function safeLinktreeCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof LinktreeError) {
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
const clients = new Map<string, LinktreeClient>();

export function getClientForTenant(tenantId: string): LinktreeClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new LinktreeClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from linktree import LinktreeClient

@asynccontextmanager
async def get_linktree_client():
    client = LinktreeClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const linktreeResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [Linktree SDK Reference](https://docs.linktree.com/sdk)
- [Linktree API Types](https://docs.linktree.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `linktree-core-workflow-a` for real-world usage.