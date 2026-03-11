---
name: ideogram-sdk-patterns
description: |
  Apply production-ready Ideogram SDK patterns for TypeScript and Python.
  Use when implementing Ideogram integrations, refactoring SDK usage,
  or establishing team coding standards for Ideogram.
  Trigger with phrases like "ideogram SDK patterns", "ideogram best practices",
  "ideogram code patterns", "idiomatic ideogram".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Ideogram SDK Patterns

## Overview
Production-ready patterns for Ideogram SDK usage in TypeScript and Python.

## Prerequisites
- Completed `ideogram-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/ideogram/client.ts
import { IdeogramClient } from '@ideogram/sdk';

let instance: IdeogramClient | null = null;

export function getIdeogramClient(): IdeogramClient {
  if (!instance) {
    instance = new IdeogramClient({
      apiKey: process.env.IDEOGRAM_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { IdeogramError } from '@ideogram/sdk';

async function safeIdeogramCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof IdeogramError) {
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
  backoffMs = 1000  # 1000: 1 second in ms
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
const clients = new Map<string, IdeogramClient>();

export function getClientForTenant(tenantId: string): IdeogramClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new IdeogramClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from ideogram import IdeogramClient

@asynccontextmanager
async def get_ideogram_client():
    client = IdeogramClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const ideogramResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [Ideogram SDK Reference](https://docs.ideogram.com/sdk)
- [Ideogram API Types](https://docs.ideogram.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `ideogram-core-workflow-a` for real-world usage.