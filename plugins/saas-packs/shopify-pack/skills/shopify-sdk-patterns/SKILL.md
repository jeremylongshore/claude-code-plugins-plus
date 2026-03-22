---
name: shopify-sdk-patterns
description: |
  Apply production-ready Shopify SDK patterns for TypeScript and Python.
  Use when implementing Shopify integrations, refactoring SDK usage,
  or establishing team coding standards for Shopify.
  Trigger with phrases like "shopify SDK patterns", "shopify best practices",
  "shopify code patterns", "idiomatic shopify".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, shopify]
---

# Shopify SDK Patterns

## Overview
Production-ready patterns for Shopify SDK usage in TypeScript and Python.

## Prerequisites
- Completed `shopify-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/shopify/client.ts
import { ShopifyClient } from '@shopify/sdk';

let instance: ShopifyClient | null = null;

export function getShopifyClient(): ShopifyClient {
  if (!instance) {
    instance = new ShopifyClient({
      apiKey: process.env.SHOPIFY_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { ShopifyError } from '@shopify/sdk';

async function safeShopifyCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof ShopifyError) {
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
const clients = new Map<string, ShopifyClient>();

export function getClientForTenant(tenantId: string): ShopifyClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new ShopifyClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from shopify import ShopifyClient

@asynccontextmanager
async def get_shopify_client():
    client = ShopifyClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const shopifyResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [Shopify SDK Reference](https://docs.shopify.com/sdk)
- [Shopify API Types](https://docs.shopify.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `shopify-core-workflow-a` for real-world usage.