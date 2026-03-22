---
name: abridge-sdk-patterns
description: |
  Apply production-ready Abridge SDK patterns for TypeScript and Python.
  Use when implementing Abridge integrations, refactoring SDK usage,
  or establishing team coding standards for Abridge.
  Trigger with phrases like "abridge SDK patterns", "abridge best practices",
  "abridge code patterns", "idiomatic abridge".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, abridge]
---

# Abridge SDK Patterns

## Overview
Production-ready patterns for Abridge SDK usage in TypeScript and Python.

## Prerequisites
- Completed `abridge-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/abridge/client.ts
import { AbridgeClient } from '@abridge/sdk';

let instance: AbridgeClient | null = null;

export function getAbridgeClient(): AbridgeClient {
  if (!instance) {
    instance = new AbridgeClient({
      apiKey: process.env.ABRIDGE_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { AbridgeError } from '@abridge/sdk';

async function safeAbridgeCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof AbridgeError) {
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
const clients = new Map<string, AbridgeClient>();

export function getClientForTenant(tenantId: string): AbridgeClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new AbridgeClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from abridge import AbridgeClient

@asynccontextmanager
async def get_abridge_client():
    client = AbridgeClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const abridgeResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [Abridge SDK Reference](https://docs.abridge.com/sdk)
- [Abridge API Types](https://docs.abridge.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `abridge-core-workflow-a` for real-world usage.