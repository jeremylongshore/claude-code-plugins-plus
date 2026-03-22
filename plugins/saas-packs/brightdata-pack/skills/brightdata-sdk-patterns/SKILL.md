---
name: brightdata-sdk-patterns
description: |
  Apply production-ready Bright Data SDK patterns for TypeScript and Python.
  Use when implementing Bright Data integrations, refactoring SDK usage,
  or establishing team coding standards for Bright Data.
  Trigger with phrases like "brightdata SDK patterns", "brightdata best practices",
  "brightdata code patterns", "idiomatic brightdata".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, brightdata]
---

# Bright Data SDK Patterns

## Overview
Production-ready patterns for Bright Data SDK usage in TypeScript and Python.

## Prerequisites
- Completed `brightdata-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/brightdata/client.ts
import { BrightDataClient } from '@brightdata/sdk';

let instance: BrightDataClient | null = null;

export function getBright DataClient(): BrightDataClient {
  if (!instance) {
    instance = new BrightDataClient({
      apiKey: process.env.BRIGHTDATA_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { Bright DataError } from '@brightdata/sdk';

async function safeBright DataCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof Bright DataError) {
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
const clients = new Map<string, BrightDataClient>();

export function getClientForTenant(tenantId: string): BrightDataClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new BrightDataClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from brightdata import BrightDataClient

@asynccontextmanager
async def get_brightdata_client():
    client = BrightDataClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const brightdataResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [Bright Data SDK Reference](https://docs.brightdata.com/sdk)
- [Bright Data API Types](https://docs.brightdata.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `brightdata-core-workflow-a` for real-world usage.