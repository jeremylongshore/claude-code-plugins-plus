---
name: vastai-sdk-patterns
description: |
  Apply production-ready Vast.ai SDK patterns for TypeScript and Python.
  Use when implementing Vast.ai integrations, refactoring SDK usage,
  or establishing team coding standards for Vast.ai.
  Trigger with phrases like "vastai SDK patterns", "vastai best practices",
  "vastai code patterns", "idiomatic vastai".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Vast.ai SDK Patterns

## Overview
Production-ready patterns for Vast.ai SDK usage in TypeScript and Python.

## Prerequisites
- Completed `vastai-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/vastai/client.ts
import { Vast.aiClient } from '@vastai/sdk';

let instance: Vast.aiClient | null = null;

export function getVast.aiClient(): Vast.aiClient {
  if (!instance) {
    instance = new Vast.aiClient({
      apiKey: process.env.VASTAI_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { Vast.aiError } from '@vastai/sdk';

async function safeVast.aiCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof Vast.aiError) {
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
const clients = new Map<string, Vast.aiClient>();

export function getClientForTenant(tenantId: string): Vast.aiClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new Vast.aiClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from vastai import Vast.aiClient

@asynccontextmanager
async def get_vastai_client():
    client = Vast.aiClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const vastaiResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [Vast.ai SDK Reference](https://docs.vastai.com/sdk)
- [Vast.ai API Types](https://docs.vastai.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `vastai-core-workflow-a` for real-world usage.