---
name: exa-sdk-patterns
description: |
  Apply production-ready Exa SDK patterns for TypeScript and Python.
  Use when implementing Exa integrations, refactoring SDK usage,
  or establishing team coding standards for Exa.
  Trigger with phrases like "exa SDK patterns", "exa best practices",
  "exa code patterns", "idiomatic exa".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Exa SDK Patterns

## Overview
Production-ready patterns for Exa SDK usage in TypeScript and Python.

## Prerequisites
- Completed `exa-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/exa/client.ts
import { ExaClient } from '@exa/sdk';

let instance: ExaClient | null = null;

export function getExaClient(): ExaClient {
  if (!instance) {
    instance = new ExaClient({
      apiKey: process.env.EXA_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { ExaError } from '@exa/sdk';

async function safeExaCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof ExaError) {
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
const clients = new Map<string, ExaClient>();

export function getClientForTenant(tenantId: string): ExaClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new ExaClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from exa import ExaClient

@asynccontextmanager
async def get_exa_client():
    client = ExaClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const exaResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [Exa SDK Reference](https://docs.exa.com/sdk)
- [Exa API Types](https://docs.exa.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `exa-core-workflow-a` for real-world usage.