---
name: fireflies-sdk-patterns
description: |
  Apply production-ready Fireflies.ai SDK patterns for TypeScript and Python.
  Use when implementing Fireflies.ai integrations, refactoring SDK usage,
  or establishing team coding standards for Fireflies.ai.
  Trigger with phrases like "fireflies SDK patterns", "fireflies best practices",
  "fireflies code patterns", "idiomatic fireflies".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Fireflies.ai SDK Patterns

## Overview
Production-ready patterns for Fireflies.ai SDK usage in TypeScript and Python.

## Prerequisites
- Completed `fireflies-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/fireflies/client.ts
import { Fireflies.aiClient } from '@fireflies/sdk';

let instance: Fireflies.aiClient | null = null;

export function getFireflies.aiClient(): Fireflies.aiClient {
  if (!instance) {
    instance = new Fireflies.aiClient({
      apiKey: process.env.FIREFLIES_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { Fireflies.aiError } from '@fireflies/sdk';

async function safeFireflies.aiCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof Fireflies.aiError) {
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
const clients = new Map<string, Fireflies.aiClient>();

export function getClientForTenant(tenantId: string): Fireflies.aiClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new Fireflies.aiClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from fireflies import Fireflies.aiClient

@asynccontextmanager
async def get_fireflies_client():
    client = Fireflies.aiClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const firefliesResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [Fireflies.ai SDK Reference](https://docs.fireflies.com/sdk)
- [Fireflies.ai API Types](https://docs.fireflies.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `fireflies-core-workflow-a` for real-world usage.