# Client, Retry, and Project Configuration

The Notion API enforces a hard limit of **3 requests per second** across all pricing tiers. Build
retry logic into your client from day one, expose it as a singleton so every module shares one
instance, and wire the npm scripts for hot reload + tests.

## Singleton client with retry and rate-limit handling

```typescript
// src/notion/client.ts
import { Client, LogLevel, isNotionClientError, APIResponseError } from '@notionhq/client';

let instance: Client | null = null;

export function getNotionClient(): Client {
  if (!instance) {
    instance = new Client({
      auth: process.env.NOTION_TOKEN,   // SDK reads NOTION_TOKEN automatically if omitted
      logLevel: process.env.NODE_ENV === 'development' ? LogLevel.DEBUG : LogLevel.WARN,
      // baseUrl can be overridden for proxy/mock servers:
      // baseUrl: process.env.NOTION_BASE_URL || 'https://api.notion.com',
    });
  }
  return instance;
}

// Retry wrapper with exponential backoff for rate limits
export async function withRetry<T>(
  fn: () => Promise<T>,
  maxRetries = 3
): Promise<T> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      if (
        isNotionClientError(error) &&
        error instanceof APIResponseError &&
        error.status === 429 &&
        attempt < maxRetries
      ) {
        const retryAfter = parseInt(error.headers?.get('retry-after') || '1', 10);
        const delay = retryAfter * 1000 * Math.pow(2, attempt);
        console.warn(`Rate limited. Retrying in ${delay}ms (attempt ${attempt + 1}/${maxRetries})`);
        await new Promise(resolve => setTimeout(resolve, delay));
        continue;
      }
      throw error;
    }
  }
  throw new Error('Unreachable');
}
```

## package.json — scripts and dependencies

```json
{
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "dev:debug": "NOTION_LOG_LEVEL=debug tsx watch src/index.ts",
    "test": "vitest",
    "test:watch": "vitest --watch",
    "test:integration": "INTEGRATION=true vitest run tests/integration/",
    "typecheck": "tsc --noEmit"
  },
  "dependencies": {
    "@notionhq/client": "^2.2.0"
  },
  "devDependencies": {
    "tsx": "^4.0.0",
    "typescript": "^5.0.0",
    "vitest": "^2.0.0",
    "dotenv": "^16.0.0"
  }
}
```
