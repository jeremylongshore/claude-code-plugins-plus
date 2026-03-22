---
name: podium-sdk-patterns
description: |
  Apply production-ready Podium SDK patterns for TypeScript and Python.
  Use when implementing Podium integrations, refactoring SDK usage,
  or establishing team coding standards for Podium.
  Trigger with phrases like "podium SDK patterns", "podium best practices",
  "podium code patterns", "idiomatic podium".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, podium]
---

# Podium SDK Patterns

## Overview
Production-ready patterns for Podium SDK usage in TypeScript and Python.

## Prerequisites
- Completed `podium-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/podium/client.ts
import { PodiumClient } from '@podium/sdk';

let instance: PodiumClient | null = null;

export function getPodiumClient(): PodiumClient {
  if (!instance) {
    instance = new PodiumClient({
      apiKey: process.env.PODIUM_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { PodiumError } from '@podium/sdk';

async function safePodiumCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof PodiumError) {
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
const clients = new Map<string, PodiumClient>();

export function getClientForTenant(tenantId: string): PodiumClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new PodiumClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from podium import PodiumClient

@asynccontextmanager
async def get_podium_client():
    client = PodiumClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const podiumResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [Podium SDK Reference](https://docs.podium.com/sdk)
- [Podium API Types](https://docs.podium.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `podium-core-workflow-a` for real-world usage.