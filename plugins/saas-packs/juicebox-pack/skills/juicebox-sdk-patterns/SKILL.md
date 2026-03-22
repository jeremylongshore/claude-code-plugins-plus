---
name: juicebox-sdk-patterns
description: |
  Apply production-ready Juicebox SDK patterns for TypeScript and Python.
  Use when implementing Juicebox integrations, refactoring SDK usage,
  or establishing team coding standards for Juicebox.
  Trigger with phrases like "juicebox SDK patterns", "juicebox best practices",
  "juicebox code patterns", "idiomatic juicebox".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, juicebox]
---

# Juicebox SDK Patterns

## Overview
Production-ready patterns for Juicebox SDK usage in TypeScript and Python.

## Prerequisites
- Completed `juicebox-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/juicebox/client.ts
import { JuiceboxClient } from '@juicebox/sdk';

let instance: JuiceboxClient | null = null;

export function getJuiceboxClient(): JuiceboxClient {
  if (!instance) {
    instance = new JuiceboxClient({
      apiKey: process.env.JUICEBOX_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { JuiceboxError } from '@juicebox/sdk';

async function safeJuiceboxCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof JuiceboxError) {
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
const clients = new Map<string, JuiceboxClient>();

export function getClientForTenant(tenantId: string): JuiceboxClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new JuiceboxClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from juicebox import JuiceboxClient

@asynccontextmanager
async def get_juicebox_client():
    client = JuiceboxClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const juiceboxResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [Juicebox SDK Reference](https://docs.juicebox.com/sdk)
- [Juicebox API Types](https://docs.juicebox.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `juicebox-core-workflow-a` for real-world usage.