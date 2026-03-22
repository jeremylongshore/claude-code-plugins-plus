---
name: veeva-sdk-patterns
description: |
  Apply production-ready Veeva SDK patterns for TypeScript and Python.
  Use when implementing Veeva integrations, refactoring SDK usage,
  or establishing team coding standards for Veeva.
  Trigger with phrases like "veeva SDK patterns", "veeva best practices",
  "veeva code patterns", "idiomatic veeva".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, veeva]
---

# Veeva SDK Patterns

## Overview
Production-ready patterns for Veeva SDK usage in TypeScript and Python.

## Prerequisites
- Completed `veeva-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/veeva/client.ts
import { VeevaClient } from '@veeva/sdk';

let instance: VeevaClient | null = null;

export function getVeevaClient(): VeevaClient {
  if (!instance) {
    instance = new VeevaClient({
      apiKey: process.env.VEEVA_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { VeevaError } from '@veeva/sdk';

async function safeVeevaCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof VeevaError) {
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
const clients = new Map<string, VeevaClient>();

export function getClientForTenant(tenantId: string): VeevaClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new VeevaClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from veeva import VeevaClient

@asynccontextmanager
async def get_veeva_client():
    client = VeevaClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const veevaResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [Veeva SDK Reference](https://docs.veeva.com/sdk)
- [Veeva API Types](https://docs.veeva.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `veeva-core-workflow-a` for real-world usage.