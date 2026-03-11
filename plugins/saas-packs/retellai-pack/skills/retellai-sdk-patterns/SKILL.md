---
name: retellai-sdk-patterns
description: |
  Apply production-ready Retell AI SDK patterns for TypeScript and Python.
  Use when implementing Retell AI integrations, refactoring SDK usage,
  or establishing team coding standards for Retell AI.
  Trigger with phrases like "retellai SDK patterns", "retellai best practices",
  "retellai code patterns", "idiomatic retellai".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Retell AI SDK Patterns

## Overview
Production-ready patterns for Retell AI SDK usage in TypeScript and Python.

## Prerequisites
- Completed `retellai-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/retellai/client.ts
import { RetellAIClient } from '@retellai/sdk';

let instance: RetellAIClient | null = null;

export function getRetell AIClient(): RetellAIClient {
  if (!instance) {
    instance = new RetellAIClient({
      apiKey: process.env.RETELLAI_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { Retell AIError } from '@retellai/sdk';

async function safeRetell AICall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof Retell AIError) {
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
const clients = new Map<string, RetellAIClient>();

export function getClientForTenant(tenantId: string): RetellAIClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new RetellAIClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from retellai import RetellAIClient

@asynccontextmanager
async def get_retellai_client():
    client = RetellAIClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const retellaiResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [Retell AI SDK Reference](https://docs.retellai.com/sdk)
- [Retell AI API Types](https://docs.retellai.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `retellai-core-workflow-a` for real-world usage.