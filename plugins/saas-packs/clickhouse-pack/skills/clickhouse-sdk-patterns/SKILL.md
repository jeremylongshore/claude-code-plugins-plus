---
name: clickhouse-sdk-patterns
description: |
  Apply production-ready ClickHouse SDK patterns for TypeScript and Python.
  Use when implementing ClickHouse integrations, refactoring SDK usage,
  or establishing team coding standards for ClickHouse.
  Trigger with phrases like "clickhouse SDK patterns", "clickhouse best practices",
  "clickhouse code patterns", "idiomatic clickhouse".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, clickhouse]
---

# ClickHouse SDK Patterns

## Overview
Production-ready patterns for ClickHouse SDK usage in TypeScript and Python.

## Prerequisites
- Completed `clickhouse-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/clickhouse/client.ts
import { ClickHouseClient } from '@clickhouse/sdk';

let instance: ClickHouseClient | null = null;

export function getClickHouseClient(): ClickHouseClient {
  if (!instance) {
    instance = new ClickHouseClient({
      apiKey: process.env.CLICKHOUSE_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { ClickHouseError } from '@clickhouse/sdk';

async function safeClickHouseCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof ClickHouseError) {
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
const clients = new Map<string, ClickHouseClient>();

export function getClientForTenant(tenantId: string): ClickHouseClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new ClickHouseClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from clickhouse import ClickHouseClient

@asynccontextmanager
async def get_clickhouse_client():
    client = ClickHouseClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const clickhouseResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [ClickHouse SDK Reference](https://docs.clickhouse.com/sdk)
- [ClickHouse API Types](https://docs.clickhouse.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `clickhouse-core-workflow-a` for real-world usage.