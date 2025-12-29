---
name: supabase-sdk-patterns
description: |
  Supabase SDK patterns for TypeScript and Python with best practices.
  Trigger phrases: "supabase SDK patterns", "supabase best practices",
  "supabase code patterns", "idiomatic supabase".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Supabase SDK Patterns

## Overview
Production-ready patterns for Supabase SDK usage in TypeScript and Python.

## Client Initialization Patterns

### Singleton Pattern (Recommended)
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

## Error Handling Pattern

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
      // Log structured error
      console.error({
        code: err.code,
        message: err.message,
        // Additional error fields
      });
    }
    return { data: null, error: err as Error };
  }
}
```

## Retry Pattern

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

## Type Safety Patterns

```typescript
// Strict typing for API responses
interface SupabaseResponse<T> {
  data: T;
  meta: {
    requestId: string;
    timestamp: string;
  };
}

// Zod validation for runtime safety
import { z } from 'zod';

const supabaseResponseSchema = z.object({
  // Define schema fields
});
```

## Python Patterns

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

## Next Steps
Apply patterns in `supabase-core-workflow-a` for real-world usage.