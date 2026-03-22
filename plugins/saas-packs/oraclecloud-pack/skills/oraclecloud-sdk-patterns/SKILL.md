---
name: oraclecloud-sdk-patterns
description: |
  Apply production-ready Oracle Cloud SDK patterns for TypeScript and Python.
  Use when implementing Oracle Cloud integrations, refactoring SDK usage,
  or establishing team coding standards for Oracle Cloud.
  Trigger with phrases like "oraclecloud SDK patterns", "oraclecloud best practices",
  "oraclecloud code patterns", "idiomatic oraclecloud".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, oraclecloud]
---

# Oracle Cloud SDK Patterns

## Overview
Production-ready patterns for Oracle Cloud SDK usage in TypeScript and Python.

## Prerequisites
- Completed `oraclecloud-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/oraclecloud/client.ts
import { OracleCloudClient } from '@oraclecloud/sdk';

let instance: OracleCloudClient | null = null;

export function getOracle CloudClient(): OracleCloudClient {
  if (!instance) {
    instance = new OracleCloudClient({
      apiKey: process.env.ORACLECLOUD_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { Oracle CloudError } from '@oraclecloud/sdk';

async function safeOracle CloudCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof Oracle CloudError) {
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
const clients = new Map<string, OracleCloudClient>();

export function getClientForTenant(tenantId: string): OracleCloudClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new OracleCloudClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from oraclecloud import OracleCloudClient

@asynccontextmanager
async def get_oraclecloud_client():
    client = OracleCloudClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const oraclecloudResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [Oracle Cloud SDK Reference](https://docs.oraclecloud.com/sdk)
- [Oracle Cloud API Types](https://docs.oraclecloud.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `oraclecloud-core-workflow-a` for real-world usage.