# SDK Code Patterns

## Singleton Pattern (Recommended)

```typescript
// src/retellai/client.ts
import { RetellAIClient } from '@retellai/sdk';

let instance: RetellAIClient | null = null;

export function getRetellAIClient(): RetellAIClient {
  if (!instance) {
    instance = new RetellAIClient({
      apiKey: process.env.RETELLAI_API_KEY!,
    });
  }
  return instance;
}
```

## Error Handling Wrapper

```typescript
import { RetellAIError } from '@retellai/sdk';

async function safeRetellAICall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof RetellAIError) {
      console.error({
        code: err.code,
        message: err.message,
      });
    }
    return { data: null, error: err as Error };
  }
}
```

## Retry Logic with Backoff

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

## Factory Pattern (Multi-tenant)

```typescript
const clients = new Map<string, RetellAIClient>();

export function getClientForTenant(tenantId: string): RetellAIClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new RetellAIClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

## Python Context Manager

```python
from contextlib import asynccontextmanager
from retellai import RetellAIClient

@asynccontextmanager
async def get_retellai_client():
    client = RetellAIClient()
    try:
        yield client
    finally:
        await client.close()
```

## Zod Response Validation

```typescript
import { z } from 'zod';

const retellaiResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```
