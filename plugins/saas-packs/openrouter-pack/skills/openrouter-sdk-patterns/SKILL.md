---
name: openrouter-sdk-patterns
description: |
  Apply production-ready OpenRouter SDK patterns for TypeScript and Python.
  Use when implementing OpenRouter integrations, refactoring SDK usage,
  or establishing team coding standards for OpenRouter.
  Trigger with phrases like "openrouter SDK patterns", "openrouter best practices",
  "openrouter code patterns", "idiomatic openrouter".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, openrouter]
---

# OpenRouter SDK Patterns

## Overview
Production-ready patterns for OpenRouter SDK usage in TypeScript and Python.

## Prerequisites
- Completed `openrouter-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/openrouter/client.ts
import { OpenRouterClient } from '@openrouter/sdk';

let instance: OpenRouterClient | null = null;

export function getOpenRouterClient(): OpenRouterClient {
  if (!instance) {
    instance = new OpenRouterClient({
      apiKey: process.env.OPENROUTER_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { OpenRouterError } from '@openrouter/sdk';

async function safeOpenRouterCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof OpenRouterError) {
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
const clients = new Map<string, OpenRouterClient>();

export function getClientForTenant(tenantId: string): OpenRouterClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new OpenRouterClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from openrouter import OpenRouterClient

@asynccontextmanager
async def get_openrouter_client():
    client = OpenRouterClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const openrouterResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [OpenRouter SDK Reference](https://docs.openrouter.com/sdk)
- [OpenRouter API Types](https://docs.openrouter.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `openrouter-core-workflow-a` for real-world usage.