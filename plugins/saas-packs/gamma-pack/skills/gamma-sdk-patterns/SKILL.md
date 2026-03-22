---
name: gamma-sdk-patterns
description: |
  Apply production-ready Gamma SDK patterns for TypeScript and Python.
  Use when implementing Gamma integrations, refactoring SDK usage,
  or establishing team coding standards for Gamma.
  Trigger with phrases like "gamma SDK patterns", "gamma best practices",
  "gamma code patterns", "idiomatic gamma".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, gamma]
---

# Gamma SDK Patterns

## Overview
Production-ready patterns for Gamma SDK usage in TypeScript and Python.

## Prerequisites
- Completed `gamma-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/gamma/client.ts
import { GammaClient } from '@gamma/sdk';

let instance: GammaClient | null = null;

export function getGammaClient(): GammaClient {
  if (!instance) {
    instance = new GammaClient({
      apiKey: process.env.GAMMA_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { GammaError } from '@gamma/sdk';

async function safeGammaCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof GammaError) {
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
const clients = new Map<string, GammaClient>();

export function getClientForTenant(tenantId: string): GammaClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new GammaClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from gamma import GammaClient

@asynccontextmanager
async def get_gamma_client():
    client = GammaClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const gammaResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [Gamma SDK Reference](https://docs.gamma.com/sdk)
- [Gamma API Types](https://docs.gamma.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `gamma-core-workflow-a` for real-world usage.