---
name: elevenlabs-sdk-patterns
description: |
  Apply production-ready ElevenLabs SDK patterns for TypeScript and Python.
  Use when implementing ElevenLabs integrations, refactoring SDK usage,
  or establishing team coding standards for ElevenLabs.
  Trigger with phrases like "elevenlabs SDK patterns", "elevenlabs best practices",
  "elevenlabs code patterns", "idiomatic elevenlabs".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, elevenlabs]
---

# ElevenLabs SDK Patterns

## Overview
Production-ready patterns for ElevenLabs SDK usage in TypeScript and Python.

## Prerequisites
- Completed `elevenlabs-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/elevenlabs/client.ts
import { ElevenLabsClient } from '@elevenlabs/sdk';

let instance: ElevenLabsClient | null = null;

export function getElevenLabsClient(): ElevenLabsClient {
  if (!instance) {
    instance = new ElevenLabsClient({
      apiKey: process.env.ELEVENLABS_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { ElevenLabsError } from '@elevenlabs/sdk';

async function safeElevenLabsCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof ElevenLabsError) {
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
const clients = new Map<string, ElevenLabsClient>();

export function getClientForTenant(tenantId: string): ElevenLabsClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new ElevenLabsClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from elevenlabs import ElevenLabsClient

@asynccontextmanager
async def get_elevenlabs_client():
    client = ElevenLabsClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const elevenlabsResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [ElevenLabs SDK Reference](https://docs.elevenlabs.com/sdk)
- [ElevenLabs API Types](https://docs.elevenlabs.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `elevenlabs-core-workflow-a` for real-world usage.