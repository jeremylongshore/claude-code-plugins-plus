---
name: coreweave-sdk-patterns
description: |
  Apply production-ready CoreWeave SDK patterns for TypeScript and Python.
  Use when implementing CoreWeave integrations, refactoring SDK usage,
  or establishing team coding standards for CoreWeave.
  Trigger with phrases like "coreweave SDK patterns", "coreweave best practices",
  "coreweave code patterns", "idiomatic coreweave".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, coreweave]
---

# CoreWeave SDK Patterns

## Overview
Production-ready patterns for CoreWeave SDK usage in TypeScript and Python.

## Prerequisites
- Completed `coreweave-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/coreweave/client.ts
import { CoreWeaveClient } from '@coreweave/sdk';

let instance: CoreWeaveClient | null = null;

export function getCoreWeaveClient(): CoreWeaveClient {
  if (!instance) {
    instance = new CoreWeaveClient({
      apiKey: process.env.COREWEAVE_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { CoreWeaveError } from '@coreweave/sdk';

async function safeCoreWeaveCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof CoreWeaveError) {
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
const clients = new Map<string, CoreWeaveClient>();

export function getClientForTenant(tenantId: string): CoreWeaveClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new CoreWeaveClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from coreweave import CoreWeaveClient

@asynccontextmanager
async def get_coreweave_client():
    client = CoreWeaveClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const coreweaveResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [CoreWeave SDK Reference](https://docs.coreweave.com/sdk)
- [CoreWeave API Types](https://docs.coreweave.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `coreweave-core-workflow-a` for real-world usage.