---
name: coderabbit-sdk-patterns
description: |
  Apply production-ready CodeRabbit SDK patterns for TypeScript and Python.
  Use when implementing CodeRabbit integrations, refactoring SDK usage,
  or establishing team coding standards for CodeRabbit.
  Trigger with phrases like "coderabbit SDK patterns", "coderabbit best practices",
  "coderabbit code patterns", "idiomatic coderabbit".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# CodeRabbit SDK Patterns

## Overview
Production-ready patterns for CodeRabbit SDK usage in TypeScript and Python.

## Prerequisites
- Completed `coderabbit-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/coderabbit/client.ts
import { CodeRabbitClient } from '@coderabbit/sdk';

let instance: CodeRabbitClient | null = null;

export function getCodeRabbitClient(): CodeRabbitClient {
  if (!instance) {
    instance = new CodeRabbitClient({
      apiKey: process.env.CODERABBIT_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { CodeRabbitError } from '@coderabbit/sdk';

async function safeCodeRabbitCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof CodeRabbitError) {
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
const clients = new Map<string, CodeRabbitClient>();

export function getClientForTenant(tenantId: string): CodeRabbitClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new CodeRabbitClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from coderabbit import CodeRabbitClient

@asynccontextmanager
async def get_coderabbit_client():
    client = CodeRabbitClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const coderabbitResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [CodeRabbit SDK Reference](https://docs.coderabbit.com/sdk)
- [CodeRabbit API Types](https://docs.coderabbit.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `coderabbit-core-workflow-a` for real-world usage.