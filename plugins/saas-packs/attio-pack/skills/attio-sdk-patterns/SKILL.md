---
name: attio-sdk-patterns
description: |
  Apply production-ready Attio SDK patterns for TypeScript and Python.
  Use when implementing Attio integrations, refactoring SDK usage,
  or establishing team coding standards for Attio.
  Trigger with phrases like "attio SDK patterns", "attio best practices",
  "attio code patterns", "idiomatic attio".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, attio]
---

# Attio SDK Patterns

## Overview
Production-ready patterns for Attio SDK usage in TypeScript and Python.

## Prerequisites
- Completed `attio-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/attio/client.ts
import { AttioClient } from '@attio/sdk';

let instance: AttioClient | null = null;

export function getAttioClient(): AttioClient {
  if (!instance) {
    instance = new AttioClient({
      apiKey: process.env.ATTIO_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { AttioError } from '@attio/sdk';

async function safeAttioCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof AttioError) {
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
const clients = new Map<string, AttioClient>();

export function getClientForTenant(tenantId: string): AttioClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new AttioClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from attio import AttioClient

@asynccontextmanager
async def get_attio_client():
    client = AttioClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const attioResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [Attio SDK Reference](https://docs.attio.com/sdk)
- [Attio API Types](https://docs.attio.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `attio-core-workflow-a` for real-world usage.