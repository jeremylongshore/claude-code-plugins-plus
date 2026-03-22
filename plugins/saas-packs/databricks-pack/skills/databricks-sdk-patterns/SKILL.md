---
name: databricks-sdk-patterns
description: |
  Apply production-ready Databricks SDK patterns for TypeScript and Python.
  Use when implementing Databricks integrations, refactoring SDK usage,
  or establishing team coding standards for Databricks.
  Trigger with phrases like "databricks SDK patterns", "databricks best practices",
  "databricks code patterns", "idiomatic databricks".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, databricks]
---

# Databricks SDK Patterns

## Overview
Production-ready patterns for Databricks SDK usage in TypeScript and Python.

## Prerequisites
- Completed `databricks-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/databricks/client.ts
import { DatabricksClient } from '@databricks/sdk';

let instance: DatabricksClient | null = null;

export function getDatabricksClient(): DatabricksClient {
  if (!instance) {
    instance = new DatabricksClient({
      apiKey: process.env.DATABRICKS_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { DatabricksError } from '@databricks/sdk';

async function safeDatabricksCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof DatabricksError) {
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
const clients = new Map<string, DatabricksClient>();

export function getClientForTenant(tenantId: string): DatabricksClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new DatabricksClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from databricks import DatabricksClient

@asynccontextmanager
async def get_databricks_client():
    client = DatabricksClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const databricksResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [Databricks SDK Reference](https://docs.databricks.com/sdk)
- [Databricks API Types](https://docs.databricks.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `databricks-core-workflow-a` for real-world usage.