# Lokalise SDK Patterns - Implementation Guide

Detailed implementation reference for the lokalise-sdk-patterns skill.

## Instructions

### Step 1: Implement Singleton Client Pattern
```typescript
// src/lokalise/client.ts
import { LokaliseApi } from "@lokalise/node-api";

let instance: LokaliseApi | null = null;

export function getLokaliseClient(): LokaliseApi {
  if (!instance) {
    const apiKey = process.env.LOKALISE_API_TOKEN;
    if (!apiKey) {
      throw new Error("LOKALISE_API_TOKEN environment variable is required");
    }

    instance = new LokaliseApi({
      apiKey,
      enableCompression: true,  // Enable gzip for large responses
    });
  }
  return instance;
}

// Reset for testing
export function resetLokaliseClient(): void {
  instance = null;
}
```

### Step 2: Add Error Handling Wrapper
```typescript
// src/lokalise/errors.ts
import { ApiError } from "@lokalise/node-api";

interface LokaliseResult<T> {
  data: T | null;
  error: LokaliseError | null;
}

interface LokaliseError {
  code: number;
  message: string;
  retryable: boolean;
}

export async function safeLokaliseCall<T>(
  operation: () => Promise<T>
): Promise<LokaliseResult<T>> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    const error = parseLokaliseError(err);
    console.error("[Lokalise]", error);
    return { data: null, error };
  }
}

function parseLokaliseError(err: unknown): LokaliseError {
  if (err instanceof ApiError) {
    return {
      code: err.code,
      message: err.message,
      retryable: [429, 500, 502, 503, 504].includes(err.code),
    };
  }

  return {
    code: 0,
    message: err instanceof Error ? err.message : "Unknown error",
    retryable: false,
  };
}
```

### Step 3: Implement Rate-Limited Queue
```typescript
// src/lokalise/queue.ts
import PQueue from "p-queue";

// Lokalise: 6 requests/sec, 10 concurrent per project
const queue = new PQueue({
  concurrency: 5,  // Stay under concurrent limit
  interval: 1000,
  intervalCap: 5,  // Stay under rate limit
});

export async function queuedLokaliseCall<T>(
  operation: () => Promise<T>
): Promise<T> {
  return queue.add(operation) as Promise<T>;
}

// For batch operations
export async function batchLokaliseOperations<T, R>(
  items: T[],
  operation: (item: T) => Promise<R>
): Promise<R[]> {
  return Promise.all(
    items.map(item => queuedLokaliseCall(() => operation(item)))
  );
}
```

### Step 4: Add Retry Logic
```typescript
// src/lokalise/retry.ts
export async function withRetry<T>(
  operation: () => Promise<T>,
  maxRetries = 3,
  baseDelayMs = 1000
): Promise<T> {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await operation();
    } catch (err: any) {
      const isRetryable = err.code === 429 || (err.code >= 500 && err.code < 600);

      if (!isRetryable || attempt === maxRetries) {
        throw err;
      }

      // Exponential backoff with jitter
      const delay = baseDelayMs * Math.pow(2, attempt - 1);
      const jitter = Math.random() * 500;

      console.log(`[Lokalise] Retry ${attempt}/${maxRetries} in ${delay}ms...`);
      await new Promise(r => setTimeout(r, delay + jitter));
    }
  }
  throw new Error("Unreachable");
}
```

### Step 5: Implement Cursor Pagination Helper
```typescript
// src/lokalise/pagination.ts
import { LokaliseApi, PaginatedResult } from "@lokalise/node-api";

export async function* paginateKeys(
  client: LokaliseApi,
  projectId: string,
  options: { limit?: number } = {}
): AsyncGenerator<any> {
  const limit = options.limit || 500;  // Max 500 as of 2025
  let cursor: string | undefined;

  do {
    const result = await client.keys().list({
      project_id: projectId,
      limit,
      pagination: "cursor",
      cursor,
    });

    for (const key of result.items) {
      yield key;
    }

    cursor = result.hasNextCursor() ? result.nextCursor : undefined;
  } while (cursor);
}

// Usage
async function getAllKeys(projectId: string) {
  const client = getLokaliseClient();
  const keys: any[] = [];

  for await (const key of paginateKeys(client, projectId)) {
    keys.push(key);
  }

  return keys;
}
```


## Detailed Examples

### Factory Pattern (Multi-Project)
```typescript
const clients = new Map<string, LokaliseApi>();

export function getClientForProject(projectId: string): LokaliseApi {
  if (!clients.has(projectId)) {
    // Could use different tokens per project if needed
    clients.set(projectId, new LokaliseApi({
      apiKey: process.env.LOKALISE_API_TOKEN!,
      enableCompression: true,
    }));
  }
  return clients.get(projectId)!;
}
```

### Typed Response Wrapper
```typescript
import { Key, Translation, Project } from "@lokalise/node-api";

interface LokaliseService {
  getProject(id: string): Promise<Project>;
  listKeys(projectId: string): Promise<Key[]>;
  updateTranslation(projectId: string, translationId: number, text: string): Promise<Translation>;
}

export const lokaliseService: LokaliseService = {
  async getProject(id) {
    const client = getLokaliseClient();
    return client.projects().get(id);
  },

  async listKeys(projectId) {
    const client = getLokaliseClient();
    const result = await client.keys().list({ project_id: projectId });
    return result.items;
  },

  async updateTranslation(projectId, translationId, text) {
    const client = getLokaliseClient();
    return client.translations().update(translationId, {
      project_id: projectId,
      translation: text,
    });
  },
};
```

### Branch-Aware Client
```typescript
export function getProjectWithBranch(projectId: string, branch?: string): string {
  // Lokalise branch syntax: projectId:branchName
  return branch ? `${projectId}:${branch}` : projectId;
}

// Usage
const projectId = getProjectWithBranch("123456.abcdef", "feature/new-ui");
const keys = await client.keys().list({ project_id: projectId });
```

