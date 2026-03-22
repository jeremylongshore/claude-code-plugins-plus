---
name: wispr-sdk-patterns
description: |
  Apply production-ready Wispr SDK patterns for TypeScript and Python.
  Use when implementing Wispr integrations, refactoring SDK usage,
  or establishing team coding standards for Wispr.
  Trigger with phrases like "wispr SDK patterns", "wispr best practices",
  "wispr code patterns", "idiomatic wispr".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, wispr]
---

# Wispr SDK Patterns

## Overview
Production-ready patterns for Wispr SDK usage in TypeScript and Python.

## Prerequisites
- Completed `wispr-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/wispr/client.ts
import { WisprClient } from '@wispr/sdk';

let instance: WisprClient | null = null;

export function getWisprClient(): WisprClient {
  if (!instance) {
    instance = new WisprClient({
      apiKey: process.env.WISPR_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { WisprError } from '@wispr/sdk';

async function safeWisprCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof WisprError) {
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
const clients = new Map<string, WisprClient>();

export function getClientForTenant(tenantId: string): WisprClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new WisprClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from wispr import WisprClient

@asynccontextmanager
async def get_wispr_client():
    client = WisprClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const wisprResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [Wispr SDK Reference](https://docs.wispr.com/sdk)
- [Wispr API Types](https://docs.wispr.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `wispr-core-workflow-a` for real-world usage.