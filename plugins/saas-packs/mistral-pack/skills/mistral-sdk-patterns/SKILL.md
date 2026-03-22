---
name: mistral-sdk-patterns
description: |
  Apply production-ready Mistral AI SDK patterns for TypeScript and Python.
  Use when implementing Mistral AI integrations, refactoring SDK usage,
  or establishing team coding standards for Mistral AI.
  Trigger with phrases like "mistral SDK patterns", "mistral best practices",
  "mistral code patterns", "idiomatic mistral".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, mistral]
---

# Mistral AI SDK Patterns

## Overview
Production-ready patterns for Mistral AI SDK usage in TypeScript and Python.

## Prerequisites
- Completed `mistral-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/mistral/client.ts
import { MistralAIClient } from '@mistral/sdk';

let instance: MistralAIClient | null = null;

export function getMistral AIClient(): MistralAIClient {
  if (!instance) {
    instance = new MistralAIClient({
      apiKey: process.env.MISTRAL_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { Mistral AIError } from '@mistral/sdk';

async function safeMistral AICall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof Mistral AIError) {
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
const clients = new Map<string, MistralAIClient>();

export function getClientForTenant(tenantId: string): MistralAIClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new MistralAIClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from mistral import MistralAIClient

@asynccontextmanager
async def get_mistral_client():
    client = MistralAIClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const mistralResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [Mistral AI SDK Reference](https://docs.mistral.com/sdk)
- [Mistral AI API Types](https://docs.mistral.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `mistral-core-workflow-a` for real-world usage.