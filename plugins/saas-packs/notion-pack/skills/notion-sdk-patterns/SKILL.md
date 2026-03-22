---
name: notion-sdk-patterns
description: |
  Apply production-ready Notion SDK patterns for TypeScript and Python.
  Use when implementing Notion integrations, refactoring SDK usage,
  or establishing team coding standards for Notion.
  Trigger with phrases like "notion SDK patterns", "notion best practices",
  "notion code patterns", "idiomatic notion".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, notion]
---

# Notion SDK Patterns

## Overview
Production-ready patterns for Notion SDK usage in TypeScript and Python.

## Prerequisites
- Completed `notion-install-auth` setup
- Familiarity with async/await patterns
- Understanding of error handling best practices

## Instructions

### Step 1: Implement Singleton Pattern (Recommended)
```typescript
// src/notion/client.ts
import { NotionClient } from '@notion/sdk';

let instance: NotionClient | null = null;

export function getNotionClient(): NotionClient {
  if (!instance) {
    instance = new NotionClient({
      apiKey: process.env.NOTION_API_KEY!,
      // Additional options
    });
  }
  return instance;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
import { NotionError } from '@notion/sdk';

async function safeNotionCall<T>(
  operation: () => Promise<T>
): Promise<{ data: T | null; error: Error | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof NotionError) {
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
const clients = new Map<string, NotionClient>();

export function getClientForTenant(tenantId: string): NotionClient {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new NotionClient({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

### Python Context Manager
```python
from contextlib import asynccontextmanager
from notion import NotionClient

@asynccontextmanager
async def get_notion_client():
    client = NotionClient()
    try:
        yield client
    finally:
        await client.close()
```

### Zod Validation
```typescript
import { z } from 'zod';

const notionResponseSchema = z.object({
  id: z.string(),
  status: z.enum(['active', 'inactive']),
  createdAt: z.string().datetime(),
});
```

## Resources
- [Notion SDK Reference](https://docs.notion.com/sdk)
- [Notion API Types](https://docs.notion.com/types)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `notion-core-workflow-a` for real-world usage.