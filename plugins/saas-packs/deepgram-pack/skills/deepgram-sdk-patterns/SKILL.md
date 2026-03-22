---
name: deepgram-sdk-patterns
description: |
  Apply production-ready Deepgram SDK patterns for TypeScript and Python.
  Use when implementing Deepgram integrations, refactoring SDK usage,
  or establishing team coding standards for Deepgram.
  Trigger with phrases like "deepgram SDK patterns", "deepgram best practices",
  "deepgram code patterns", "idiomatic deepgram".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, deepgram]
---

# Deepgram SDK Patterns

## Overview
Production-ready patterns for Deepgram SDK usage in TypeScript and Python.

## Prerequisites
- Completed `deepgram-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/deepgram/client.ts
import { DeepgramClient } from '@deepgram/sdk';

let instance: DeepgramClient | null = null;

export function getDeepgramClient(): DeepgramClient {
  if (!instance) {
    instance = new DeepgramClient({
      apiKey: process.env.DEEPGRAM_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { DeepgramError } from '@deepgram/sdk';

async function safeDeepgramCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof DeepgramError) {
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
const clients = new Map<string, DeepgramClient>();

export function getClientForTenant(tenantId: string): DeepgramClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new DeepgramClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from deepgram import DeepgramClient

@asynccontextmanager
async def get_deepgram_client():
    client = DeepgramClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const deepgramResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [Deepgram SDK Reference](https://docs.deepgram.com/sdk)
- [Deepgram API Types](https://docs.deepgram.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `deepgram-core-workflow-a` for real-world usage.