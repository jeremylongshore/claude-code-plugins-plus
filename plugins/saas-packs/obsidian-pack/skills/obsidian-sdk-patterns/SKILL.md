---
name: obsidian-sdk-patterns
description: |
  Apply production-ready Obsidian SDK patterns for TypeScript and Python.
  Use when implementing Obsidian integrations, refactoring SDK usage,
  or establishing team coding standards for Obsidian.
  Trigger with phrases like "obsidian SDK patterns", "obsidian best practices",
  "obsidian code patterns", "idiomatic obsidian".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, obsidian]
---

# Obsidian SDK Patterns

## Overview
Production-ready patterns for Obsidian SDK usage in TypeScript and Python.

## Prerequisites
- Completed `obsidian-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/obsidian/client.ts
import { ObsidianClient } from '@obsidian/sdk';

let instance: ObsidianClient | null = null;

export function getObsidianClient(): ObsidianClient {
  if (!instance) {
    instance = new ObsidianClient({
      apiKey: process.env.OBSIDIAN_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { ObsidianError } from '@obsidian/sdk';

async function safeObsidianCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof ObsidianError) {
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
const clients = new Map<string, ObsidianClient>();

export function getClientForTenant(tenantId: string): ObsidianClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new ObsidianClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from obsidian import ObsidianClient

@asynccontextmanager
async def get_obsidian_client():
    client = ObsidianClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const obsidianResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [Obsidian SDK Reference](https://docs.obsidian.com/sdk)
- [Obsidian API Types](https://docs.obsidian.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `obsidian-core-workflow-a` for real-world usage.