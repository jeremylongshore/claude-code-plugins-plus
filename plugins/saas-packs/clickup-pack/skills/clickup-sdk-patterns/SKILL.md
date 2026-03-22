---
name: clickup-sdk-patterns
description: |
  Apply production-ready ClickUp SDK patterns for TypeScript and Python.
  Use when implementing ClickUp integrations, refactoring SDK usage,
  or establishing team coding standards for ClickUp.
  Trigger with phrases like "clickup SDK patterns", "clickup best practices",
  "clickup code patterns", "idiomatic clickup".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, clickup]
---

# ClickUp SDK Patterns

## Overview
Production-ready patterns for ClickUp SDK usage in TypeScript and Python.

## Prerequisites
- Completed `clickup-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/clickup/client.ts
import { ClickUpClient } from '@clickup/sdk';

let instance: ClickUpClient | null = null;

export function getClickUpClient(): ClickUpClient {
  if (!instance) {
    instance = new ClickUpClient({
      apiKey: process.env.CLICKUP_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { ClickUpError } from '@clickup/sdk';

async function safeClickUpCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof ClickUpError) {
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
const clients = new Map<string, ClickUpClient>();

export function getClientForTenant(tenantId: string): ClickUpClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new ClickUpClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from clickup import ClickUpClient

@asynccontextmanager
async def get_clickup_client():
    client = ClickUpClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const clickupResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [ClickUp SDK Reference](https://docs.clickup.com/sdk)
- [ClickUp API Types](https://docs.clickup.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `clickup-core-workflow-a` for real-world usage.