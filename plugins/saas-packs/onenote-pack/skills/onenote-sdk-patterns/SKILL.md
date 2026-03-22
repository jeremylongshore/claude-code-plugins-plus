---
name: onenote-sdk-patterns
description: |
  Apply production-ready OneNote SDK patterns for TypeScript and Python.
  Use when implementing OneNote integrations, refactoring SDK usage,
  or establishing team coding standards for OneNote.
  Trigger with phrases like "onenote SDK patterns", "onenote best practices",
  "onenote code patterns", "idiomatic onenote".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, onenote]
---

# OneNote SDK Patterns

## Overview
Production-ready patterns for OneNote SDK usage in TypeScript and Python.

## Prerequisites
- Completed `onenote-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/onenote/client.ts
import { OneNoteClient } from '@onenote/sdk';

let instance: OneNoteClient | null = null;

export function getOneNoteClient(): OneNoteClient {
  if (!instance) {
    instance = new OneNoteClient({
      apiKey: process.env.ONENOTE_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { OneNoteError } from '@onenote/sdk';

async function safeOneNoteCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof OneNoteError) {
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
const clients = new Map<string, OneNoteClient>();

export function getClientForTenant(tenantId: string): OneNoteClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new OneNoteClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from onenote import OneNoteClient

@asynccontextmanager
async def get_onenote_client():
    client = OneNoteClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const onenoteResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [OneNote SDK Reference](https://docs.onenote.com/sdk)
- [OneNote API Types](https://docs.onenote.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `onenote-core-workflow-a` for real-world usage.