---
name: miro-sdk-patterns
description: |
  Apply production-ready Miro SDK patterns for TypeScript and Python.
  Use when implementing Miro integrations, refactoring SDK usage,
  or establishing team coding standards for Miro.
  Trigger with phrases like "miro SDK patterns", "miro best practices",
  "miro code patterns", "idiomatic miro".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, miro]
---

# Miro SDK Patterns

## Overview
Production-ready patterns for Miro SDK usage in TypeScript and Python.

## Prerequisites
- Completed `miro-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/miro/client.ts
import { MiroClient } from '@miro/sdk';

let instance: MiroClient | null = null;

export function getMiroClient(): MiroClient {
  if (!instance) {
    instance = new MiroClient({
      apiKey: process.env.MIRO_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { MiroError } from '@miro/sdk';

async function safeMiroCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof MiroError) {
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
const clients = new Map<string, MiroClient>();

export function getClientForTenant(tenantId: string): MiroClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new MiroClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from miro import MiroClient

@asynccontextmanager
async def get_miro_client():
    client = MiroClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const miroResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [Miro SDK Reference](https://docs.miro.com/sdk)
- [Miro API Types](https://docs.miro.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `miro-core-workflow-a` for real-world usage.