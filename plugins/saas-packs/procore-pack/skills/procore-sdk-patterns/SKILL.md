---
name: procore-sdk-patterns
description: |
  Apply production-ready Procore SDK patterns for TypeScript and Python.
  Use when implementing Procore integrations, refactoring SDK usage,
  or establishing team coding standards for Procore.
  Trigger with phrases like "procore SDK patterns", "procore best practices",
  "procore code patterns", "idiomatic procore".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, procore]
---

# Procore SDK Patterns

## Overview
Production-ready patterns for Procore SDK usage in TypeScript and Python.

## Prerequisites
- Completed `procore-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/procore/client.ts
import { ProcoreClient } from '@procore/sdk';

let instance: ProcoreClient | null = null;

export function getProcoreClient(): ProcoreClient {
  if (!instance) {
    instance = new ProcoreClient({
      apiKey: process.env.PROCORE_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { ProcoreError } from '@procore/sdk';

async function safeProcoreCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof ProcoreError) {
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
const clients = new Map<string, ProcoreClient>();

export function getClientForTenant(tenantId: string): ProcoreClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new ProcoreClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from procore import ProcoreClient

@asynccontextmanager
async def get_procore_client():
    client = ProcoreClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const procoreResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [Procore SDK Reference](https://docs.procore.com/sdk)
- [Procore API Types](https://docs.procore.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `procore-core-workflow-a` for real-world usage.