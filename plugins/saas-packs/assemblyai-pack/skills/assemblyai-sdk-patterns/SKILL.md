---
name: assemblyai-sdk-patterns
description: |
  Apply production-ready AssemblyAI SDK patterns for TypeScript and Python.
  Use when implementing AssemblyAI integrations, refactoring SDK usage,
  or establishing team coding standards for AssemblyAI.
  Trigger with phrases like "assemblyai SDK patterns", "assemblyai best practices",
  "assemblyai code patterns", "idiomatic assemblyai".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, assemblyai]
---

# AssemblyAI SDK Patterns

## Overview
Production-ready patterns for AssemblyAI SDK usage in TypeScript and Python.

## Prerequisites
- Completed `assemblyai-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/assemblyai/client.ts
import { AssemblyAIClient } from '@assemblyai/sdk';

let instance: AssemblyAIClient | null = null;

export function getAssemblyAIClient(): AssemblyAIClient {
  if (!instance) {
    instance = new AssemblyAIClient({
      apiKey: process.env.ASSEMBLYAI_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { AssemblyAIError } from '@assemblyai/sdk';

async function safeAssemblyAICall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof AssemblyAIError) {
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
const clients = new Map<string, AssemblyAIClient>();

export function getClientForTenant(tenantId: string): AssemblyAIClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new AssemblyAIClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from assemblyai import AssemblyAIClient

@asynccontextmanager
async def get_assemblyai_client():
    client = AssemblyAIClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const assemblyaiResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [AssemblyAI SDK Reference](https://docs.assemblyai.com/sdk)
- [AssemblyAI API Types](https://docs.assemblyai.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `assemblyai-core-workflow-a` for real-world usage.