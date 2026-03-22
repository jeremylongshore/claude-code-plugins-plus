---
name: castai-sdk-patterns
description: |
  Apply production-ready Cast AI SDK patterns for TypeScript and Python.
  Use when implementing Cast AI integrations, refactoring SDK usage,
  or establishing team coding standards for Cast AI.
  Trigger with phrases like "castai SDK patterns", "castai best practices",
  "castai code patterns", "idiomatic castai".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, castai]
---

# Cast AI SDK Patterns

## Overview
Production-ready patterns for Cast AI SDK usage in TypeScript and Python.

## Prerequisites
- Completed `castai-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/castai/client.ts
import { CastAIClient } from '@castai/sdk';

let instance: CastAIClient | null = null;

export function getCast AIClient(): CastAIClient {
  if (!instance) {
    instance = new CastAIClient({
      apiKey: process.env.CASTAI_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { Cast AIError } from '@castai/sdk';

async function safeCast AICall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof Cast AIError) {
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
const clients = new Map<string, CastAIClient>();

export function getClientForTenant(tenantId: string): CastAIClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new CastAIClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from castai import CastAIClient

@asynccontextmanager
async def get_castai_client():
    client = CastAIClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const castaiResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [Cast AI SDK Reference](https://docs.castai.com/sdk)
- [Cast AI API Types](https://docs.castai.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `castai-core-workflow-a` for real-world usage.