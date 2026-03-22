---
name: lokalise-sdk-patterns
description: |
  Apply production-ready Lokalise SDK patterns for TypeScript and Python.
  Use when implementing Lokalise integrations, refactoring SDK usage,
  or establishing team coding standards for Lokalise.
  Trigger with phrases like "lokalise SDK patterns", "lokalise best practices",
  "lokalise code patterns", "idiomatic lokalise".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, lokalise]
---

# Lokalise SDK Patterns

## Overview
Production-ready patterns for Lokalise SDK usage in TypeScript and Python.

## Prerequisites
- Completed `lokalise-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/lokalise/client.ts
import { LokaliseClient } from '@lokalise/sdk';

let instance: LokaliseClient | null = null;

export function getLokaliseClient(): LokaliseClient {
  if (!instance) {
    instance = new LokaliseClient({
      apiKey: process.env.LOKALISE_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { LokaliseError } from '@lokalise/sdk';

async function safeLokaliseCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof LokaliseError) {
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
const clients = new Map<string, LokaliseClient>();

export function getClientForTenant(tenantId: string): LokaliseClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new LokaliseClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from lokalise import LokaliseClient

@asynccontextmanager
async def get_lokalise_client():
    client = LokaliseClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const lokaliseResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [Lokalise SDK Reference](https://docs.lokalise.com/sdk)
- [Lokalise API Types](https://docs.lokalise.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `lokalise-core-workflow-a` for real-world usage.