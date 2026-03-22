---
name: runway-sdk-patterns
description: |
  Apply production-ready Runway SDK patterns for TypeScript and Python.
  Use when implementing Runway integrations, refactoring SDK usage,
  or establishing team coding standards for Runway.
  Trigger with phrases like "runway SDK patterns", "runway best practices",
  "runway code patterns", "idiomatic runway".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, runway]
---

# Runway SDK Patterns

## Overview
Production-ready patterns for Runway SDK usage in TypeScript and Python.

## Prerequisites
- Completed `runway-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/runway/client.ts
import { RunwayClient } from '@runway/sdk';

let instance: RunwayClient | null = null;

export function getRunwayClient(): RunwayClient {
  if (!instance) {
    instance = new RunwayClient({
      apiKey: process.env.RUNWAY_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { RunwayError } from '@runway/sdk';

async function safeRunwayCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof RunwayError) {
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
const clients = new Map<string, RunwayClient>();

export function getClientForTenant(tenantId: string): RunwayClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new RunwayClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from runway import RunwayClient

@asynccontextmanager
async def get_runway_client():
    client = RunwayClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const runwayResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [Runway SDK Reference](https://docs.runway.com/sdk)
- [Runway API Types](https://docs.runway.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `runway-core-workflow-a` for real-world usage.