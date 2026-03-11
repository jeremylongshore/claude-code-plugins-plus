---
name: posthog-sdk-patterns
description: |
  Apply production-ready PostHog SDK patterns for TypeScript and Python.
  Use when implementing PostHog integrations, refactoring SDK usage,
  or establishing team coding standards for PostHog.
  Trigger with phrases like "posthog SDK patterns", "posthog best practices",
  "posthog code patterns", "idiomatic posthog".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# PostHog SDK Patterns

## Overview
Production-ready patterns for PostHog SDK usage in TypeScript and Python.

## Prerequisites
- Completed `posthog-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/posthog/client.ts
import { PostHogClient } from '@posthog/sdk';

let instance: PostHogClient | null = null;

export function getPostHogClient(): PostHogClient {
  if (!instance) {
    instance = new PostHogClient({
      apiKey: process.env.POSTHOG_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { PostHogError } from '@posthog/sdk';

async function safePostHogCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof PostHogError) {
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
const clients = new Map<string, PostHogClient>();

export function getClientForTenant(tenantId: string): PostHogClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new PostHogClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from posthog import PostHogClient

@asynccontextmanager
async def get_posthog_client():
    client = PostHogClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const posthogResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [PostHog SDK Reference](https://docs.posthog.com/sdk)
- [PostHog API Types](https://docs.posthog.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `posthog-core-workflow-a` for real-world usage.