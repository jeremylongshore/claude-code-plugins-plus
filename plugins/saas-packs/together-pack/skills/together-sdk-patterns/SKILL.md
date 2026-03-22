---
name: together-sdk-patterns
description: |
  Apply production-ready Together AI SDK patterns for TypeScript and Python.
  Use when implementing Together AI integrations, refactoring SDK usage,
  or establishing team coding standards for Together AI.
  Trigger with phrases like "together SDK patterns", "together best practices",
  "together code patterns", "idiomatic together".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, together]
---

# Together AI SDK Patterns

## Overview
Production-ready patterns for Together AI SDK usage in TypeScript and Python.

## Prerequisites
- Completed `together-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/together/client.ts
import { TogetherAIClient } from '@together/sdk';

let instance: TogetherAIClient | null = null;

export function getTogether AIClient(): TogetherAIClient {
  if (!instance) {
    instance = new TogetherAIClient({
      apiKey: process.env.TOGETHER_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { Together AIError } from '@together/sdk';

async function safeTogether AICall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof Together AIError) {
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
const clients = new Map<string, TogetherAIClient>();

export function getClientForTenant(tenantId: string): TogetherAIClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new TogetherAIClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from together import TogetherAIClient

@asynccontextmanager
async def get_together_client():
    client = TogetherAIClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const togetherResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [Together AI SDK Reference](https://docs.together.com/sdk)
- [Together AI API Types](https://docs.together.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `together-core-workflow-a` for real-world usage.