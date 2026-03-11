---
name: perplexity-sdk-patterns
description: |
  Apply production-ready Perplexity SDK patterns for TypeScript and Python.
  Use when implementing Perplexity integrations, refactoring SDK usage,
  or establishing team coding standards for Perplexity.
  Trigger with phrases like "perplexity SDK patterns", "perplexity best practices",
  "perplexity code patterns", "idiomatic perplexity".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Perplexity SDK Patterns

## Overview
Production-ready patterns for Perplexity SDK usage in TypeScript and Python.

## Prerequisites
- Completed `perplexity-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/perplexity/client.ts
import { PerplexityClient } from '@perplexity/sdk';

let instance: PerplexityClient | null = null;

export function getPerplexityClient(): PerplexityClient {
  if (!instance) {
    instance = new PerplexityClient({
      apiKey: process.env.PERPLEXITY_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { PerplexityError } from '@perplexity/sdk';

async function safePerplexityCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof PerplexityError) {
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
const clients = new Map<string, PerplexityClient>();

export function getClientForTenant(tenantId: string): PerplexityClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new PerplexityClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from perplexity import PerplexityClient

@asynccontextmanager
async def get_perplexity_client():
    client = PerplexityClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const perplexityResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [Perplexity SDK Reference](https://docs.perplexity.com/sdk)
- [Perplexity API Types](https://docs.perplexity.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `perplexity-core-workflow-a` for real-world usage.