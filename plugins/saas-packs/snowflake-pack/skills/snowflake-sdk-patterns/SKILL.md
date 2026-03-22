---
name: snowflake-sdk-patterns
description: |
  Apply production-ready Snowflake SDK patterns for TypeScript and Python.
  Use when implementing Snowflake integrations, refactoring SDK usage,
  or establishing team coding standards for Snowflake.
  Trigger with phrases like "snowflake SDK patterns", "snowflake best practices",
  "snowflake code patterns", "idiomatic snowflake".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, snowflake]
---

# Snowflake SDK Patterns

## Overview
Production-ready patterns for Snowflake SDK usage in TypeScript and Python.

## Prerequisites
- Completed `snowflake-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/snowflake/client.ts
import { SnowflakeClient } from '@snowflake/sdk';

let instance: SnowflakeClient | null = null;

export function getSnowflakeClient(): SnowflakeClient {
  if (!instance) {
    instance = new SnowflakeClient({
      apiKey: process.env.SNOWFLAKE_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { SnowflakeError } from '@snowflake/sdk';

async function safeSnowflakeCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof SnowflakeError) {
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
const clients = new Map<string, SnowflakeClient>();

export function getClientForTenant(tenantId: string): SnowflakeClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new SnowflakeClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from snowflake import SnowflakeClient

@asynccontextmanager
async def get_snowflake_client():
    client = SnowflakeClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const snowflakeResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [Snowflake SDK Reference](https://docs.snowflake.com/sdk)
- [Snowflake API Types](https://docs.snowflake.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `snowflake-core-workflow-a` for real-world usage.