---
name: lucidchart-sdk-patterns
description: |
  Apply production-ready Lucidchart SDK patterns for TypeScript and Python.
  Use when implementing Lucidchart integrations, refactoring SDK usage,
  or establishing team coding standards for Lucidchart.
  Trigger with phrases like "lucidchart SDK patterns", "lucidchart best practices",
  "lucidchart code patterns", "idiomatic lucidchart".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, lucidchart]
---

# Lucidchart SDK Patterns

## Overview
Production-ready patterns for Lucidchart SDK usage in TypeScript and Python.

## Prerequisites
- Completed `lucidchart-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/lucidchart/client.ts
import { LucidchartClient } from '@lucidchart/sdk';

let instance: LucidchartClient | null = null;

export function getLucidchartClient(): LucidchartClient {
  if (!instance) {
    instance = new LucidchartClient({
      apiKey: process.env.LUCIDCHART_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { LucidchartError } from '@lucidchart/sdk';

async function safeLucidchartCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof LucidchartError) {
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
const clients = new Map<string, LucidchartClient>();

export function getClientForTenant(tenantId: string): LucidchartClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new LucidchartClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from lucidchart import LucidchartClient

@asynccontextmanager
async def get_lucidchart_client():
    client = LucidchartClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const lucidchartResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [Lucidchart SDK Reference](https://docs.lucidchart.com/sdk)
- [Lucidchart API Types](https://docs.lucidchart.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `lucidchart-core-workflow-a` for real-world usage.