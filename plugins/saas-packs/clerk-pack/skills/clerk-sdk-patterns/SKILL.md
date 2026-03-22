---
name: clerk-sdk-patterns
description: |
  Apply production-ready Clerk SDK patterns for TypeScript and Python.
  Use when implementing Clerk integrations, refactoring SDK usage,
  or establishing team coding standards for Clerk.
  Trigger with phrases like "clerk SDK patterns", "clerk best practices",
  "clerk code patterns", "idiomatic clerk".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, clerk]
---

# Clerk SDK Patterns

## Overview
Production-ready patterns for Clerk SDK usage in TypeScript and Python.

## Prerequisites
- Completed `clerk-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/clerk/client.ts
import { ClerkClient } from '@clerk/sdk';

let instance: ClerkClient | null = null;

export function getClerkClient(): ClerkClient {
  if (!instance) {
    instance = new ClerkClient({
      apiKey: process.env.CLERK_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { ClerkError } from '@clerk/sdk';

async function safeClerkCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof ClerkError) {
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
const clients = new Map<string, ClerkClient>();

export function getClientForTenant(tenantId: string): ClerkClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new ClerkClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from clerk import ClerkClient

@asynccontextmanager
async def get_clerk_client():
    client = ClerkClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const clerkResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [Clerk SDK Reference](https://docs.clerk.com/sdk)
- [Clerk API Types](https://docs.clerk.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `clerk-core-workflow-a` for real-world usage.