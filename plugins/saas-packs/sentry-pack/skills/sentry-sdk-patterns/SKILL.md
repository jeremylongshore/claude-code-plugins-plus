---
name: sentry-sdk-patterns
description: |
  Apply production-ready Sentry SDK patterns for TypeScript and Python.
  Use when implementing Sentry integrations, refactoring SDK usage,
  or establishing team coding standards for Sentry.
  Trigger with phrases like "sentry SDK patterns", "sentry best practices",
  "sentry code patterns", "idiomatic sentry".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, sentry]
---

# Sentry SDK Patterns

## Overview
Production-ready patterns for Sentry SDK usage in TypeScript and Python.

## Prerequisites
- Completed `sentry-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/sentry/client.ts
import { SentryClient } from '@sentry/sdk';

let instance: SentryClient | null = null;

export function getSentryClient(): SentryClient {
  if (!instance) {
    instance = new SentryClient({
      apiKey: process.env.SENTRY_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { SentryError } from '@sentry/sdk';

async function safeSentryCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof SentryError) {
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
const clients = new Map<string, SentryClient>();

export function getClientForTenant(tenantId: string): SentryClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new SentryClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from sentry import SentryClient

@asynccontextmanager
async def get_sentry_client():
    client = SentryClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const sentryResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [Sentry SDK Reference](https://docs.sentry.com/sdk)
- [Sentry API Types](https://docs.sentry.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `sentry-core-workflow-a` for real-world usage.