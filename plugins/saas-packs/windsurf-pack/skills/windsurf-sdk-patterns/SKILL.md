---
name: windsurf-sdk-patterns
description: |
  Apply production-ready Windsurf SDK patterns for TypeScript and Python.
  Use when implementing Windsurf integrations, refactoring SDK usage,
  or establishing team coding standards for Windsurf.
  Trigger with phrases like "windsurf SDK patterns", "windsurf best practices",
  "windsurf code patterns", "idiomatic windsurf".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Windsurf SDK Patterns

## Overview
Production-ready patterns for Windsurf SDK usage in TypeScript and Python.

## Prerequisites
- Completed `windsurf-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/windsurf/client.ts
import { WindsurfClient } from '@windsurf/sdk';

let instance: WindsurfClient | null = null;

export function getWindsurfClient(): WindsurfClient {
  if (!instance) {
    instance = new WindsurfClient({
      apiKey: process.env.WINDSURF_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { WindsurfError } from '@windsurf/sdk';

async function safeWindsurfCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof WindsurfError) {
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
const clients = new Map<string, WindsurfClient>();

export function getClientForTenant(tenantId: string): WindsurfClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new WindsurfClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from windsurf import WindsurfClient

@asynccontextmanager
async def get_windsurf_client():
    client = WindsurfClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const windsurfResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [Windsurf SDK Reference](https://docs.windsurf.com/sdk)
- [Windsurf API Types](https://docs.windsurf.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `windsurf-core-workflow-a` for real-world usage.