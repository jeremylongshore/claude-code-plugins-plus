---
name: framer-sdk-patterns
description: |
  Apply production-ready Framer SDK patterns for TypeScript and Python.
  Use when implementing Framer integrations, refactoring SDK usage,
  or establishing team coding standards for Framer.
  Trigger with phrases like "framer SDK patterns", "framer best practices",
  "framer code patterns", "idiomatic framer".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, framer]
---

# Framer SDK Patterns

## Overview
Production-ready patterns for Framer SDK usage in TypeScript and Python.

## Prerequisites
- Completed `framer-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/framer/client.ts
import { FramerClient } from '@framer/sdk';

let instance: FramerClient | null = null;

export function getFramerClient(): FramerClient {
  if (!instance) {
    instance = new FramerClient({
      apiKey: process.env.FRAMER_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { FramerError } from '@framer/sdk';

async function safeFramerCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof FramerError) {
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
const clients = new Map<string, FramerClient>();

export function getClientForTenant(tenantId: string): FramerClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new FramerClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from framer import FramerClient

@asynccontextmanager
async def get_framer_client():
    client = FramerClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const framerResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [Framer SDK Reference](https://docs.framer.com/sdk)
- [Framer API Types](https://docs.framer.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `framer-core-workflow-a` for real-world usage.