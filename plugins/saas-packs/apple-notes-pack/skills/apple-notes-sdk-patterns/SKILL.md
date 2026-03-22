---
name: apple-notes-sdk-patterns
description: |
  Apply production-ready Apple Notes SDK patterns for TypeScript and Python.
  Use when implementing Apple Notes integrations, refactoring SDK usage,
  or establishing team coding standards for Apple Notes.
  Trigger with phrases like "apple-notes SDK patterns", "apple-notes best practices",
  "apple-notes code patterns", "idiomatic apple-notes".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, apple-notes]
---

# Apple Notes SDK Patterns

## Overview
Production-ready patterns for Apple Notes SDK usage in TypeScript and Python.

## Prerequisites
- Completed `apple-notes-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/apple-notes/client.ts
import { AppleNotesClient } from '@apple-notes/sdk';

let instance: AppleNotesClient | null = null;

export function getApple NotesClient(): AppleNotesClient {
  if (!instance) {
    instance = new AppleNotesClient({
      apiKey: process.env.APPLE-NOTES_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { Apple NotesError } from '@apple-notes/sdk';

async function safeApple NotesCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof Apple NotesError) {
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
const clients = new Map<string, AppleNotesClient>();

export function getClientForTenant(tenantId: string): AppleNotesClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new AppleNotesClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from apple-notes import AppleNotesClient

@asynccontextmanager
async def get_apple-notes_client():
    client = AppleNotesClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const apple-notesResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [Apple Notes SDK Reference](https://docs.apple-notes.com/sdk)
- [Apple Notes API Types](https://docs.apple-notes.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `apple-notes-core-workflow-a` for real-world usage.