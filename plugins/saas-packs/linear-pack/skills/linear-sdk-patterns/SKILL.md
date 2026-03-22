---
name: linear-sdk-patterns
description: |
  Apply production-ready Linear SDK patterns for TypeScript and Python.
  Use when implementing Linear integrations, refactoring SDK usage,
  or establishing team coding standards for Linear.
  Trigger with phrases like "linear SDK patterns", "linear best practices",
  "linear code patterns", "idiomatic linear".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, linear]
---

# Linear SDK Patterns

## Overview
Production-ready patterns for Linear SDK usage in TypeScript and Python.

## Prerequisites
- Completed `linear-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/linear/client.ts
import { LinearClient } from '@linear/sdk';

let instance: LinearClient | null = null;

export function getLinearClient(): LinearClient {
  if (!instance) {
    instance = new LinearClient({
      apiKey: process.env.LINEAR_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { LinearError } from '@linear/sdk';

async function safeLinearCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof LinearError) {
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
const clients = new Map<string, LinearClient>();

export function getClientForTenant(tenantId: string): LinearClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new LinearClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from linear import LinearClient

@asynccontextmanager
async def get_linear_client():
    client = LinearClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const linearResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [Linear SDK Reference](https://docs.linear.com/sdk)
- [Linear API Types](https://docs.linear.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `linear-core-workflow-a` for real-world usage.