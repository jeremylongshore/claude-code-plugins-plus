---
name: figma-sdk-patterns
description: |
  Apply production-ready Figma SDK patterns for TypeScript and Python.
  Use when implementing Figma integrations, refactoring SDK usage,
  or establishing team coding standards for Figma.
  Trigger with phrases like "figma SDK patterns", "figma best practices",
  "figma code patterns", "idiomatic figma".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, figma]
---

# Figma SDK Patterns

## Overview
Production-ready patterns for Figma SDK usage in TypeScript and Python.

## Prerequisites
- Completed `figma-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/figma/client.ts
import { FigmaClient } from '@figma/sdk';

let instance: FigmaClient | null = null;

export function getFigmaClient(): FigmaClient {
  if (!instance) {
    instance = new FigmaClient({
      apiKey: process.env.FIGMA_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { FigmaError } from '@figma/sdk';

async function safeFigmaCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof FigmaError) {
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
const clients = new Map<string, FigmaClient>();

export function getClientForTenant(tenantId: string): FigmaClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new FigmaClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from figma import FigmaClient

@asynccontextmanager
async def get_figma_client():
    client = FigmaClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const figmaResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [Figma SDK Reference](https://docs.figma.com/sdk)
- [Figma API Types](https://docs.figma.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `figma-core-workflow-a` for real-world usage.