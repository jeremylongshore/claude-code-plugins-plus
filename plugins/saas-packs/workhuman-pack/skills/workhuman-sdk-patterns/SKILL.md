---
name: workhuman-sdk-patterns
description: |
  Apply production-ready Workhuman SDK patterns for TypeScript and Python.
  Use when implementing Workhuman integrations, refactoring SDK usage,
  or establishing team coding standards for Workhuman.
  Trigger with phrases like "workhuman SDK patterns", "workhuman best practices",
  "workhuman code patterns", "idiomatic workhuman".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, workhuman]
---

# Workhuman SDK Patterns

## Overview
Production-ready patterns for Workhuman SDK usage in TypeScript and Python.

## Prerequisites
- Completed `workhuman-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/workhuman/client.ts
import { WorkhumanClient } from '@workhuman/sdk';

let instance: WorkhumanClient | null = null;

export function getWorkhumanClient(): WorkhumanClient {
  if (!instance) {
    instance = new WorkhumanClient({
      apiKey: process.env.WORKHUMAN_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { WorkhumanError } from '@workhuman/sdk';

async function safeWorkhumanCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof WorkhumanError) {
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
const clients = new Map<string, WorkhumanClient>();

export function getClientForTenant(tenantId: string): WorkhumanClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new WorkhumanClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from workhuman import WorkhumanClient

@asynccontextmanager
async def get_workhuman_client():
    client = WorkhumanClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const workhumanResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [Workhuman SDK Reference](https://docs.workhuman.com/sdk)
- [Workhuman API Types](https://docs.workhuman.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `workhuman-core-workflow-a` for real-world usage.