---
name: customerio-sdk-patterns
description: |
  Apply production-ready Customer.io SDK patterns for TypeScript and Python.
  Use when implementing Customer.io integrations, refactoring SDK usage,
  or establishing team coding standards for Customer.io.
  Trigger with phrases like "customerio SDK patterns", "customerio best practices",
  "customerio code patterns", "idiomatic customerio".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, customerio]
---

# Customer.io SDK Patterns

## Overview
Production-ready patterns for Customer.io SDK usage in TypeScript and Python.

## Prerequisites
- Completed `customerio-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/customerio/client.ts
import { Customer.ioClient } from '@customerio/sdk';

let instance: Customer.ioClient | null = null;

export function getCustomer.ioClient(): Customer.ioClient {
  if (!instance) {
    instance = new Customer.ioClient({
      apiKey: process.env.CUSTOMERIO_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { Customer.ioError } from '@customerio/sdk';

async function safeCustomer.ioCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof Customer.ioError) {
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
const clients = new Map<string, Customer.ioClient>();

export function getClientForTenant(tenantId: string): Customer.ioClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new Customer.ioClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from customerio import Customer.ioClient

@asynccontextmanager
async def get_customerio_client():
    client = Customer.ioClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const customerioResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [Customer.io SDK Reference](https://docs.customerio.com/sdk)
- [Customer.io API Types](https://docs.customerio.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `customerio-core-workflow-a` for real-world usage.