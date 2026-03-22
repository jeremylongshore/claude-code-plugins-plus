---
name: maintainx-sdk-patterns
description: |
  Apply production-ready MaintainX SDK patterns for TypeScript and Python.
  Use when implementing MaintainX integrations, refactoring SDK usage,
  or establishing team coding standards for MaintainX.
  Trigger with phrases like "maintainx SDK patterns", "maintainx best practices",
  "maintainx code patterns", "idiomatic maintainx".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, maintainx]
---

# MaintainX SDK Patterns

## Overview
Production-ready patterns for MaintainX SDK usage in TypeScript and Python.

## Prerequisites
- Completed `maintainx-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/maintainx/client.ts
import { MaintainXClient } from '@maintainx/sdk';

let instance: MaintainXClient | null = null;

export function getMaintainXClient(): MaintainXClient {
  if (!instance) {
    instance = new MaintainXClient({
      apiKey: process.env.MAINTAINX_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { MaintainXError } from '@maintainx/sdk';

async function safeMaintainXCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof MaintainXError) {
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
const clients = new Map<string, MaintainXClient>();

export function getClientForTenant(tenantId: string): MaintainXClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new MaintainXClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from maintainx import MaintainXClient

@asynccontextmanager
async def get_maintainx_client():
    client = MaintainXClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const maintainxResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [MaintainX SDK Reference](https://docs.maintainx.com/sdk)
- [MaintainX API Types](https://docs.maintainx.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `maintainx-core-workflow-a` for real-world usage.