---
name: exa-sdk-patterns
description: |
  Apply production-ready exa-js SDK patterns with type safety, singletons, and wrappers.
  Use when implementing Exa integrations, refactoring SDK usage,
  or establishing team coding standards for Exa.
  Trigger with phrases like "exa SDK patterns", "exa best practices",
  "exa code patterns", "idiomatic exa", "exa wrapper".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, exa, typescript, patterns]

---
# Exa SDK Patterns

## Overview
Production-ready patterns for the `exa-js` SDK. Covers client singletons, typed wrappers, error handling, retry logic, and response validation for real Exa API methods.

## Prerequisites
- `exa-js` installed and `EXA_API_KEY` configured
- TypeScript project with strict mode
- Familiarity with async/await and error handling

## Instructions

### Step 1: Client Singleton
```typescript
// src/exa/client.ts
import Exa from "exa-js";

let instance: Exa | null = null;

export function getExa(): Exa {
  if (!instance) {
    const apiKey = process.env.EXA_API_KEY;
    if (!apiKey) {
      throw new Error("EXA_API_KEY not set. Get one at https://dashboard.exa.ai");
    }
    instance = new Exa(apiKey);
  }
  return instance;
}
```

### Step 2: Typed Search Wrapper
```typescript
// src/exa/search.ts
import Exa from "exa-js";
import { getExa } from "./client";

interface ExaSearchOptions {
  type?: "auto" | "neural" | "keyword" | "fast" | "instant" | "deep" | "deep-reasoning";
  numResults?: number;
  includeDomains?: string[];
  excludeDomains?: string[];
  startPublishedDate?: string;
  endPublishedDate?: string;
  category?: "company" | "research paper" | "news" | "tweet" | "personal site" | "financial report" | "people";
  includeText?: string[];
  excludeText?: string[];
}

interface ExaContentsOptions {
  text?: boolean | { maxCharacters?: number; includeHtmlTags?: boolean };
  highlights?: boolean | { maxCharacters?: number; query?: string };
  summary?: boolean | { query?: string };
  livecrawl?: "always" | "preferred" | "fallback" | "never";
  livecrawlTimeout?: number;
  subpages?: number;
  subpageTarget?: string | string[];
}

export async function exaSearch(query: string, opts: ExaSearchOptions = {}) {
  const exa = getExa();
  return exa.search(query, {
    type: opts.type ?? "auto",
    numResults: opts.numResults ?? 10,
    ...opts,
  });
}

export async function exaSearchWithContents(
  query: string,
  searchOpts: ExaSearchOptions = {},
  contentOpts: ExaContentsOptions = {}
) {
  const exa = getExa();
  return exa.searchAndContents(query, {
    type: searchOpts.type ?? "auto",
    numResults: searchOpts.numResults ?? 10,
    ...searchOpts,
    ...contentOpts,
  });
}
```

### Step 3: Error Handling Wrapper
```typescript
// src/exa/safe.ts
interface ExaResult<T> {
  data: T | null;
  error: ExaError | null;
}

interface ExaError {
  status: number;
  message: string;
  tag?: string;
  requestId?: string;
  retryable: boolean;
}

function classifyError(err: any): ExaError {
  const status = err.status || err.response?.status || 500;
  const retryable = status === 429 || status >= 500;
  return {
    status,
    message: err.message || "Unknown error",
    tag: err.error_tag || err.tag,
    requestId: err.requestId || err.request_id,
    retryable,
  };
}

export async function safeExaCall<T>(
  operation: () => Promise<T>
): Promise<ExaResult<T>> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err: any) {
    const error = classifyError(err);
    console.error(`[Exa Error] ${error.status}: ${error.message}`, {
      tag: error.tag,
      requestId: error.requestId,
      retryable: error.retryable,
    });
    return { data: null, error };
  }
}

// Usage:
// const { data, error } = await safeExaCall(() =>
//   exa.searchAndContents("query", { numResults: 5, text: true })
// );
```

### Step 4: Retry with Exponential Backoff
```typescript
// src/exa/retry.ts
export async function withRetry<T>(
  operation: () => Promise<T>,
  config = { maxRetries: 3, baseDelayMs: 1000, maxDelayMs: 30000 }
): Promise<T> {
  for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
    try {
      return await operation();
    } catch (err: any) {
      const status = err.status || err.response?.status || 0;

      // Only retry on rate limits (429) and server errors (5xx)
      if (status !== 429 && (status < 500 || status >= 600)) throw err;
      if (attempt === config.maxRetries) throw err;

      const delay = Math.min(
        config.baseDelayMs * Math.pow(2, attempt) + Math.random() * 500,
        config.maxDelayMs
      );
      console.log(`[Exa] Retry ${attempt + 1}/${config.maxRetries} in ${delay.toFixed(0)}ms`);
      await new Promise(r => setTimeout(r, delay));
    }
  }
  throw new Error("Unreachable");
}

// Usage:
// const results = await withRetry(() =>
//   exa.searchAndContents("query", { numResults: 5, text: true })
// );
```

### Step 5: Response Validation with Zod
```typescript
// src/exa/validate.ts
import { z } from "zod";

const ExaResultSchema = z.object({
  url: z.string().url(),
  title: z.string().nullable(),
  score: z.number(),
  publishedDate: z.string().nullable().optional(),
  text: z.string().optional(),
  highlights: z.array(z.string()).optional(),
  summary: z.string().optional(),
});

const ExaSearchResponseSchema = z.object({
  results: z.array(ExaResultSchema),
  autopromptString: z.string().optional(),
});

export function validateSearchResponse(response: unknown) {
  return ExaSearchResponseSchema.parse(response);
}
```

## Error Handling
| Pattern | Use Case | Benefit |
|---------|----------|---------|
| Singleton | All API calls | Single client instance, consistent config |
| Safe wrapper | Non-critical searches | Prevents uncaught exceptions |
| Retry logic | Rate limits and 5xx | Automatic recovery from transient failures |
| Zod validation | Response processing | Catches unexpected API response changes |
| Typed options | IDE support | Autocomplete and compile-time checks |

## Examples

### Factory Pattern (Multi-tenant)
```typescript
const clients = new Map<string, Exa>();

export function getExaForTenant(tenantId: string): Exa {
  if (!clients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId); // from your config/vault
    clients.set(tenantId, new Exa(apiKey));
  }
  return clients.get(tenantId)!;
}
```

### Combined: Safe + Retry + Typed
```typescript
async function resilientSearch(query: string) {
  return safeExaCall(() =>
    withRetry(() =>
      exaSearchWithContents(
        query,
        { type: "neural", numResults: 5 },
        { text: { maxCharacters: 2000 }, highlights: true }
      )
    )
  );
}
```

## Resources
- [exa-js TypeScript SDK](https://docs.exa.ai/sdks/typescript-sdk-specification)
- [Exa Error Codes](https://docs.exa.ai/reference/error-codes)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `exa-core-workflow-a` for real-world search usage.
