---
name: ramp-sdk-patterns
description: |
  Apply production-ready Ramp SDK patterns for TypeScript and Python.
  Use when implementing Ramp integrations, refactoring SDK usage,
  or establishing team coding standards for Ramp.
  Trigger with phrases like "ramp SDK patterns", "ramp best practices",
  "ramp code patterns", "idiomatic ramp".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, ramp]
---

# Ramp SDK Patterns

## Overview
Production-ready patterns for Ramp SDK usage in TypeScript and Python.

## Prerequisites
- Completed `ramp-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/ramp/client.ts
import { RampClient } from '@ramp/sdk';

let instance: RampClient | null = null;

export function getRampClient(): RampClient {
  if (!instance) {
    instance = new RampClient({
      apiKey: process.env.RAMP_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { RampError } from '@ramp/sdk';

async function safeRampCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof RampError) {
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
const clients = new Map<string, RampClient>();

export function getClientForTenant(tenantId: string): RampClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new RampClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from ramp import RampClient

@asynccontextmanager
async def get_ramp_client():
    client = RampClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const rampResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [Ramp SDK Reference](https://docs.ramp.com/sdk)
- [Ramp API Types](https://docs.ramp.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `ramp-core-workflow-a` for real-world usage.