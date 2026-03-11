---
name: replit-sdk-patterns
description: |
  Apply production-ready Replit SDK patterns for TypeScript and Python.
  Use when implementing Replit integrations, refactoring SDK usage,
  or establishing team coding standards for Replit.
  Trigger with phrases like "replit SDK patterns", "replit best practices",
  "replit code patterns", "idiomatic replit".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Replit SDK Patterns

## Overview
Production-ready patterns for Replit SDK usage in TypeScript and Python.

## Prerequisites
- Completed `replit-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/replit/client.ts
import { ReplitClient } from '@replit/sdk';

let instance: ReplitClient | null = null;

export function getReplitClient(): ReplitClient {
  if (!instance) {
    instance = new ReplitClient({
      apiKey: process.env.REPLIT_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { ReplitError } from '@replit/sdk';

async function safeReplitCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof ReplitError) {
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
const clients = new Map<string, ReplitClient>();

export function getClientForTenant(tenantId: string): ReplitClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new ReplitClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from replit import ReplitClient

@asynccontextmanager
async def get_replit_client():
    client = ReplitClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const replitResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [Replit SDK Reference](https://docs.replit.com/sdk)
- [Replit API Types](https://docs.replit.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `replit-core-workflow-a` for real-world usage.