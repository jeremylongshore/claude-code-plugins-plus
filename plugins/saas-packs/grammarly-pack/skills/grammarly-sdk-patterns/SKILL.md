---
name: grammarly-sdk-patterns
description: |
  Apply production-ready Grammarly SDK patterns for TypeScript and Python.
  Use when implementing Grammarly integrations, refactoring SDK usage,
  or establishing team coding standards for Grammarly.
  Trigger with phrases like "grammarly SDK patterns", "grammarly best practices",
  "grammarly code patterns", "idiomatic grammarly".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, grammarly]
---

# Grammarly SDK Patterns

## Overview
Production-ready patterns for Grammarly SDK usage in TypeScript and Python.

## Prerequisites
- Completed `grammarly-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/grammarly/client.ts
import { GrammarlyClient } from '@grammarly/sdk';

let instance: GrammarlyClient | null = null;

export function getGrammarlyClient(): GrammarlyClient {
  if (!instance) {
    instance = new GrammarlyClient({
      apiKey: process.env.GRAMMARLY_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { GrammarlyError } from '@grammarly/sdk';

async function safeGrammarlyCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof GrammarlyError) {
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
const clients = new Map<string, GrammarlyClient>();

export function getClientForTenant(tenantId: string): GrammarlyClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new GrammarlyClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from grammarly import GrammarlyClient

@asynccontextmanager
async def get_grammarly_client():
    client = GrammarlyClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const grammarlyResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [Grammarly SDK Reference](https://docs.grammarly.com/sdk)
- [Grammarly API Types](https://docs.grammarly.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `grammarly-core-workflow-a` for real-world usage.