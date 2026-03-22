---
name: canva-sdk-patterns
description: |
  Apply production-ready Canva SDK patterns for TypeScript and Python.
  Use when implementing Canva integrations, refactoring SDK usage,
  or establishing team coding standards for Canva.
  Trigger with phrases like "canva SDK patterns", "canva best practices",
  "canva code patterns", "idiomatic canva".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, canva]
---

# Canva SDK Patterns

## Overview
Production-ready patterns for Canva SDK usage in TypeScript and Python.

## Prerequisites
- Completed `canva-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/canva/client.ts
import { CanvaClient } from '@canva/sdk';

let instance: CanvaClient | null = null;

export function getCanvaClient(): CanvaClient {
  if (!instance) {
    instance = new CanvaClient({
      apiKey: process.env.CANVA_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { CanvaError } from '@canva/sdk';

async function safeCanvaCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof CanvaError) {
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
const clients = new Map<string, CanvaClient>();

export function getClientForTenant(tenantId: string): CanvaClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new CanvaClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from canva import CanvaClient

@asynccontextmanager
async def get_canva_client():
    client = CanvaClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const canvaResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [Canva SDK Reference](https://docs.canva.com/sdk)
- [Canva API Types](https://docs.canva.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `canva-core-workflow-a` for real-world usage.