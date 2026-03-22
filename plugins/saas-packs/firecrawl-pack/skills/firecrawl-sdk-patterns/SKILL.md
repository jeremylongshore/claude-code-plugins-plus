---
name: firecrawl-sdk-patterns
description: |
  Apply production-ready Firecrawl SDK patterns for TypeScript and Python.
  Use when implementing Firecrawl integrations, building reusable scraping services,
  or establishing team coding standards for Firecrawl.
  Trigger with phrases like "firecrawl SDK patterns", "firecrawl best practices",
  "firecrawl code patterns", "idiomatic firecrawl", "firecrawl wrapper".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, firecrawl, python, typescript]

---
# Firecrawl SDK Patterns

## Overview
Production-ready patterns for Firecrawl SDK (`@mendable/firecrawl-js` / `firecrawl-py`). Covers singleton client, typed wrappers, retry with backoff, response validation, and reusable scraping service patterns.

## Prerequisites
- `@mendable/firecrawl-js` installed
- Understanding of async/await patterns
- TypeScript strict mode recommended

## Instructions

### Step 1: Singleton Client with Configuration
```typescript
// src/firecrawl/client.ts
import FirecrawlApp from "@mendable/firecrawl-js";

let instance: FirecrawlApp | null = null;

export function getFirecrawl(): FirecrawlApp {
  if (!instance) {
    if (!process.env.FIRECRAWL_API_KEY) {
      throw new Error("FIRECRAWL_API_KEY environment variable is required");
    }
    instance = new FirecrawlApp({
      apiKey: process.env.FIRECRAWL_API_KEY,
      ...(process.env.FIRECRAWL_API_URL
        ? { apiUrl: process.env.FIRECRAWL_API_URL }
        : {}),
    });
  }
  return instance;
}
```

### Step 2: Typed Scrape Wrapper
```typescript
// src/firecrawl/scrape.ts
import { getFirecrawl } from "./client";

interface ScrapeResult {
  url: string;
  title: string;
  markdown: string;
  links: string[];
  scrapedAt: string;
}

export async function scrapePage(
  url: string,
  options?: { waitFor?: number; includeLinks?: boolean }
): Promise<ScrapeResult> {
  const firecrawl = getFirecrawl();
  const formats: string[] = ["markdown"];
  if (options?.includeLinks) formats.push("links");

  const result = await firecrawl.scrapeUrl(url, {
    formats,
    onlyMainContent: true,
    ...(options?.waitFor ? { waitFor: options.waitFor } : {}),
  });

  if (!result.success) {
    throw new Error(`Scrape failed for ${url}: ${result.error}`);
  }

  return {
    url: result.metadata?.sourceURL || url,
    title: result.metadata?.title || "",
    markdown: result.markdown || "",
    links: result.links || [],
    scrapedAt: new Date().toISOString(),
  };
}
```

### Step 3: Retry with Exponential Backoff
```typescript
// src/firecrawl/retry.ts
export async function withRetry<T>(
  operation: () => Promise<T>,
  config = { maxRetries: 3, baseDelayMs: 1000, maxDelayMs: 30000 }
): Promise<T> {
  for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error: any) {
      if (attempt === config.maxRetries) throw error;

      const status = error.statusCode || error.status;
      // Only retry on rate limits (429) and server errors (5xx)
      if (status && status !== 429 && status < 500) throw error;

      const delay = Math.min(
        config.baseDelayMs * Math.pow(2, attempt) + Math.random() * 500,
        config.maxDelayMs
      );
      console.warn(`Firecrawl retry ${attempt + 1}/${config.maxRetries} in ${delay.toFixed(0)}ms`);
      await new Promise(r => setTimeout(r, delay));
    }
  }
  throw new Error("Unreachable");
}

// Usage: await withRetry(() => scrapePage("https://example.com"))
```

### Step 4: Scraping Service with Queue
```typescript
// src/firecrawl/service.ts
import PQueue from "p-queue";
import { scrapePage, type ScrapeResult } from "./scrape";
import { withRetry } from "./retry";

export class FirecrawlService {
  private queue: PQueue;

  constructor(concurrency = 3) {
    this.queue = new PQueue({
      concurrency,
      interval: 1000,
      intervalCap: 5,  // max 5 requests per second
    });
  }

  async scrape(url: string): Promise<ScrapeResult> {
    return this.queue.add(() => withRetry(() => scrapePage(url)));
  }

  async scrapeMany(urls: string[]): Promise<ScrapeResult[]> {
    return Promise.all(urls.map(url => this.scrape(url)));
  }

  get pending(): number {
    return this.queue.pending;
  }
}
```

### Step 5: Response Validation with Zod
```typescript
import { z } from "zod";

const FirecrawlScrapeResponse = z.object({
  success: z.literal(true),
  markdown: z.string().min(1),
  metadata: z.object({
    title: z.string().optional(),
    sourceURL: z.string().url(),
    statusCode: z.number().optional(),
  }),
});

export function validateScrapeResponse(result: unknown) {
  const parsed = FirecrawlScrapeResponse.safeParse(result);
  if (!parsed.success) {
    console.error("Invalid Firecrawl response:", parsed.error.issues);
    return null;
  }
  return parsed.data;
}
```

### Step 6: Python Patterns
```python
# firecrawl_service.py
import os
from firecrawl import FirecrawlApp
from functools import lru_cache
import time

@lru_cache(maxsize=1)
def get_firecrawl() -> FirecrawlApp:
    """Singleton Firecrawl client."""
    return FirecrawlApp(api_key=os.environ["FIRECRAWL_API_KEY"])

def scrape_with_retry(url: str, max_retries: int = 3) -> dict:
    """Scrape with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return get_firecrawl().scrape_url(url, params={
                "formats": ["markdown"],
                "onlyMainContent": True,
            })
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            delay = (2 ** attempt) + (time.time() % 1)
            print(f"Retry {attempt + 1}/{max_retries} in {delay:.1f}s: {e}")
            time.sleep(delay)
```

## Output
- Singleton client with env-based configuration
- Typed wrappers returning clean domain objects
- Automatic retry with exponential backoff + jitter
- Queue-based concurrency control
- Zod validation for response safety

## Error Handling
| Pattern | Use Case | Benefit |
|---------|----------|---------|
| Singleton client | All SDK usage | One instance, consistent config |
| Typed wrapper | Business logic | Compile-time safety |
| Retry + backoff | 429 / 5xx errors | Automatic recovery |
| Queue | Multiple URLs | Respect rate limits |
| Zod validation | Any API response | Catch API changes early |

## Examples

### Factory Pattern (Multi-Tenant)
```typescript
const clients = new Map<string, FirecrawlApp>();

export function getClientForTenant(tenantId: string): FirecrawlApp {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId);
    clients.set(tenantId, new FirecrawlApp({ apiKey }));
  }
  return clients.get(tenantId)!;
}
```

## Resources
- [Node SDK](https://docs.firecrawl.dev/sdks/node)
- [Python SDK](https://docs.firecrawl.dev/sdks/python)
- [p-queue](https://github.com/sindresorhus/p-queue)
- [Zod](https://zod.dev/)

## Next Steps
Apply patterns in `firecrawl-core-workflow-a` for real-world usage.
