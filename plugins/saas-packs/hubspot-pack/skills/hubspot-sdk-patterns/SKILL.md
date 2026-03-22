---
name: hubspot-sdk-patterns
description: |
  Apply production-ready HubSpot SDK patterns for TypeScript and Python.
  Use when implementing HubSpot integrations, refactoring SDK usage,
  or establishing team coding standards for HubSpot.
  Trigger with phrases like "hubspot SDK patterns", "hubspot best practices",
  "hubspot code patterns", "idiomatic hubspot".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, hubspot]
---

# HubSpot SDK Patterns

## Overview
Production-ready patterns for HubSpot SDK usage in TypeScript and Python.

## Prerequisites
- Completed `hubspot-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/hubspot/client.ts
import { HubSpotClient } from '@hubspot/sdk';

let instance: HubSpotClient | null = null;

export function getHubSpotClient(): HubSpotClient {
  if (!instance) {
    instance = new HubSpotClient({
      apiKey: process.env.HUBSPOT_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { HubSpotError } from '@hubspot/sdk';

async function safeHubSpotCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof HubSpotError) {
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
const clients = new Map<string, HubSpotClient>();

export function getClientForTenant(tenantId: string): HubSpotClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new HubSpotClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from hubspot import HubSpotClient

@asynccontextmanager
async def get_hubspot_client():
    client = HubSpotClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const hubspotResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [HubSpot SDK Reference](https://docs.hubspot.com/sdk)
- [HubSpot API Types](https://docs.hubspot.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `hubspot-core-workflow-a` for real-world usage.