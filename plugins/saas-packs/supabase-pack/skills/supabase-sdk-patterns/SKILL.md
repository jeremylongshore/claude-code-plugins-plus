---
name: supabase-sdk-patterns
description: |
  Apply Supabase SDK patterns for TypeScript and Python with best practices.
  Use when implementing production-ready Supabase integrations.
  Trigger with phrases like "supabase SDK patterns", "supabase best practices",
  "supabase code patterns", "idiomatic supabase".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Supabase SDK Patterns

## Overview
Production-ready patterns for Supabase SDK usage in TypeScript and Python.

## Prerequisites
- Completed `supabase-install-auth` setup
- Understanding of async/await patterns
- TypeScript 5.0+ or Python 3.10+

## Instructions

### Step 1: Implement Singleton Pattern
```typescript
// src/supabase/client.ts
import { SupabaseClient } from '@supabase/supabase-js';

let instance: SupabaseClient | null = null;

export function getSupabaseClient(): SupabaseClient {
  if (!instance) {
    instance = new SupabaseClient({
      apiKey: process.env.SUPABASE_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling
```typescript
import { SupabaseError } from '@supabase/supabase-js';

async function safeSupabaseCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof SupabaseError) {
      console.error({ code: err.code, message: err.message });
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
- Singleton client instance for efficient resource usage
- Consistent error handling across all API calls
- Automatic retry with exponential backoff
- Type-safe API responses

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Multiple instances | Not using singleton | Use `getSupabaseClient()` |
| Unhandled rejection | Missing try-catch | Wrap in `safeSupabaseCall` |
| Rate limit exceeded | Too many retries | Increase backoff delay |
| Type errors | Schema mismatch | Update Zod schema |

## Examples

### Factory Pattern (Multi-tenant)
```typescript
const clients = new Map<string, SupabaseClient>();

export function getClientForTenant(tenantId: string): SupabaseClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new SupabaseClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from supabase import SupabaseClient

@asynccontextmanager
async def get_supabase_client():
    client = SupabaseClient()
    try:
        yield client
    finally:
        await client.close()
```

### Type Safety with Zod
```typescript
import { z } from 'zod';

const supabaseResponseSchema = z.object({
  id: z.string(),
  data: z.unknown()
});

type SupabaseResponse = z.infer<typeof supabaseResponseSchema>;
```

## Resources
- [Supabase SDK Documentation](https://docs.supabase.com/sdk)
- [TypeScript Best Practices](https://supabase.com/docs/typescript)
- [Python Best Practices](https://supabase.com/docs/python)

## Next Steps
Apply patterns in `supabase-core-workflow-a` for real-world usage.