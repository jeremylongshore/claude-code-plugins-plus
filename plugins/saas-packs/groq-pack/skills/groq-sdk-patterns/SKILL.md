---
name: groq-sdk-patterns
description: |
  Apply production-ready Groq SDK patterns for TypeScript and Python.
  Use when implementing Groq integrations, refactoring SDK usage,
  or establishing team coding standards for Groq.
  Trigger with phrases like "groq SDK patterns", "groq best practices",
  "groq code patterns", "idiomatic groq".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Groq SDK Patterns

## Overview
Production-ready patterns for Groq SDK usage in TypeScript and Python.

## Prerequisites
- Completed `groq-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/groq/client.ts
import { GroqClient } from '@groq/sdk';

let instance: GroqClient | null = null;

export function getGroqClient(): GroqClient {
  if (!instance) {
    instance = new GroqClient({
      apiKey: process.env.GROQ_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { GroqError } from '@groq/sdk';

async function safeGroqCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof GroqError) {
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
const clients = new Map<string, GroqClient>();

export function getClientForTenant(tenantId: string): GroqClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new GroqClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from groq import GroqClient

@asynccontextmanager
async def get_groq_client():
    client = GroqClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const groqResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [Groq SDK Reference](https://docs.groq.com/sdk)
- [Groq API Types](https://docs.groq.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `groq-core-workflow-a` for real-world usage.