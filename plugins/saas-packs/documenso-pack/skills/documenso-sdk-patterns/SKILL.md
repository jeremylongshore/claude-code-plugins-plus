---
name: documenso-sdk-patterns
description: |
  Apply production-ready Documenso SDK patterns for TypeScript and Python.
  Use when implementing Documenso integrations, refactoring SDK usage,
  or establishing team coding standards for Documenso.
  Trigger with phrases like "documenso SDK patterns", "documenso best practices",
  "documenso code patterns", "idiomatic documenso".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, documenso]
---

# Documenso SDK Patterns

## Overview
Production-ready patterns for Documenso SDK usage in TypeScript and Python.

## Prerequisites
- Completed `documenso-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/documenso/client.ts
import { DocumensoClient } from '@documenso/sdk';

let instance: DocumensoClient | null = null;

export function getDocumensoClient(): DocumensoClient {
  if (!instance) {
    instance = new DocumensoClient({
      apiKey: process.env.DOCUMENSO_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { DocumensoError } from '@documenso/sdk';

async function safeDocumensoCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof DocumensoError) {
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
const clients = new Map<string, DocumensoClient>();

export function getClientForTenant(tenantId: string): DocumensoClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new DocumensoClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from documenso import DocumensoClient

@asynccontextmanager
async def get_documenso_client():
    client = DocumensoClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const documensoResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [Documenso SDK Reference](https://docs.documenso.com/sdk)
- [Documenso API Types](https://docs.documenso.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `documenso-core-workflow-a` for real-world usage.