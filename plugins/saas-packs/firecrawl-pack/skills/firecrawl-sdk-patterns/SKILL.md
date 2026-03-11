---
name: firecrawl-sdk-patterns
description: |
  Apply production-ready FireCrawl SDK patterns for TypeScript and Python.
  Use when implementing FireCrawl integrations, refactoring SDK usage,
  or establishing team coding standards for FireCrawl.
  Trigger with phrases like "firecrawl SDK patterns", "firecrawl best practices",
  "firecrawl code patterns", "idiomatic firecrawl".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# FireCrawl SDK Patterns

## Overview
Production-ready patterns for FireCrawl SDK usage in TypeScript and Python.

## Prerequisites
- Completed `firecrawl-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/firecrawl/client.ts
import { FireCrawlClient } from '@firecrawl/sdk';

let instance: FireCrawlClient | null = null;

export function getFireCrawlClient(): FireCrawlClient {
  if (!instance) {
    instance = new FireCrawlClient({
      apiKey: process.env.FIRECRAWL_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { FireCrawlError } from '@firecrawl/sdk';

async function safeFireCrawlCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof FireCrawlError) {
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
const clients = new Map<string, FireCrawlClient>();

export function getClientForTenant(tenantId: string): FireCrawlClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new FireCrawlClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from firecrawl import FireCrawlClient

@asynccontextmanager
async def get_firecrawl_client():
    client = FireCrawlClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const firecrawlResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [FireCrawl SDK Reference](https://docs.firecrawl.com/sdk)
- [FireCrawl API Types](https://docs.firecrawl.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `firecrawl-core-workflow-a` for real-world usage.