---
name: evernote-sdk-patterns
description: |
  Apply production-ready Evernote SDK patterns for TypeScript and Python.
  Use when implementing Evernote integrations, refactoring SDK usage,
  or establishing team coding standards for Evernote.
  Trigger with phrases like "evernote SDK patterns", "evernote best practices",
  "evernote code patterns", "idiomatic evernote".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, evernote]
---

# Evernote SDK Patterns

## Overview
Production-ready patterns for Evernote SDK usage in TypeScript and Python.

## Prerequisites
- Completed `evernote-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/evernote/client.ts
import { EvernoteClient } from '@evernote/sdk';

let instance: EvernoteClient | null = null;

export function getEvernoteClient(): EvernoteClient {
  if (!instance) {
    instance = new EvernoteClient({
      apiKey: process.env.EVERNOTE_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { EvernoteError } from '@evernote/sdk';

async function safeEvernoteCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof EvernoteError) {
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
const clients = new Map<string, EvernoteClient>();

export function getClientForTenant(tenantId: string): EvernoteClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new EvernoteClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from evernote import EvernoteClient

@asynccontextmanager
async def get_evernote_client():
    client = EvernoteClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const evernoteResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [Evernote SDK Reference](https://docs.evernote.com/sdk)
- [Evernote API Types](https://docs.evernote.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `evernote-core-workflow-a` for real-world usage.