---
name: intercom-sdk-patterns
description: |
  Apply production-ready Intercom SDK patterns for TypeScript and Python.
  Use when implementing Intercom integrations, refactoring SDK usage,
  or establishing team coding standards for Intercom.
  Trigger with phrases like "intercom SDK patterns", "intercom best practices",
  "intercom code patterns", "idiomatic intercom".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, intercom]
---

# Intercom SDK Patterns

## Overview
Production-ready patterns for Intercom SDK usage in TypeScript and Python.

## Prerequisites
- Completed `intercom-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/intercom/client.ts
import { IntercomClient } from '@intercom/sdk';

let instance: IntercomClient | null = null;

export function getIntercomClient(): IntercomClient {
  if (!instance) {
    instance = new IntercomClient({
      apiKey: process.env.INTERCOM_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { IntercomError } from '@intercom/sdk';

async function safeIntercomCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof IntercomError) {
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
const clients = new Map<string, IntercomClient>();

export function getClientForTenant(tenantId: string): IntercomClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new IntercomClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from intercom import IntercomClient

@asynccontextmanager
async def get_intercom_client():
    client = IntercomClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const intercomResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [Intercom SDK Reference](https://docs.intercom.com/sdk)
- [Intercom API Types](https://docs.intercom.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `intercom-core-workflow-a` for real-world usage.