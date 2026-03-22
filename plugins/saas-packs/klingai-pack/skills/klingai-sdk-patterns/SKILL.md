---
name: klingai-sdk-patterns
description: |
  Apply production-ready Kling AI SDK patterns for TypeScript and Python.
  Use when implementing Kling AI integrations, refactoring SDK usage,
  or establishing team coding standards for Kling AI.
  Trigger with phrases like "klingai SDK patterns", "klingai best practices",
  "klingai code patterns", "idiomatic klingai".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, klingai]
---

# Kling AI SDK Patterns

## Overview
Production-ready patterns for Kling AI SDK usage in TypeScript and Python.

## Prerequisites
- Completed `klingai-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/klingai/client.ts
import { KlingAIClient } from '@klingai/sdk';

let instance: KlingAIClient | null = null;

export function getKling AIClient(): KlingAIClient {
  if (!instance) {
    instance = new KlingAIClient({
      apiKey: process.env.KLINGAI_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { Kling AIError } from '@klingai/sdk';

async function safeKling AICall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof Kling AIError) {
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
const clients = new Map<string, KlingAIClient>();

export function getClientForTenant(tenantId: string): KlingAIClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new KlingAIClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from klingai import KlingAIClient

@asynccontextmanager
async def get_klingai_client():
    client = KlingAIClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const klingaiResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [Kling AI SDK Reference](https://docs.klingai.com/sdk)
- [Kling AI API Types](https://docs.klingai.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `klingai-core-workflow-a` for real-world usage.