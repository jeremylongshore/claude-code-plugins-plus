---
name: lokalise-sdk-patterns
description: |
  Apply production-ready Lokalise SDK patterns for TypeScript and Node.js.
  Use when implementing Lokalise integrations, refactoring SDK usage,
  or establishing team coding standards for Lokalise.
  Trigger with phrases like "lokalise SDK patterns", "lokalise best practices",
  "lokalise code patterns", "idiomatic lokalise".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Lokalise SDK Patterns

## Overview

Production-grade patterns for `@lokalise/node-api`: client singleton, cursor pagination, typed error handling, batch operations, upload monitoring, and retry with rate limiting.

## Prerequisites

- `@lokalise/node-api` v12+ installed
- TypeScript 5+ with `strict` mode

## Instructions

1. Create a client singleton to centralize configuration and support branch-based project IDs.

```typescript
// src/lib/lokalise-client.ts
import { LokaliseApi } from "@lokalise/node-api";

let instance: LokaliseApi | null = null;

export function getClient(apiKey?: string): LokaliseApi {
  if (instance) return instance;
  const key = apiKey ?? process.env.LOKALISE_API_TOKEN;
  if (!key) throw new Error("Set LOKALISE_API_TOKEN or pass apiKey");
  instance = new LokaliseApi({ apiKey: key, enableCompression: true });
  return instance;
}

export function resetClient(): void { instance = null; }

/** Lokalise branch syntax: "projectId:branchName" */
export function projectId(id: string, branch?: string): string {
  return branch ? `${id}:${branch}` : id;
}
```

2. Build a cursor-based pagination helper that works with any paginated endpoint.

```typescript
// src/lib/paginate.ts
interface PaginatedResult<T> {
  items: T[];
  hasNextCursor(): boolean;
  nextCursor(): string;
}

type Fetcher<T> = (params: Record<string, unknown>) => Promise<PaginatedResult<T>>;

/** Async generator yielding all items across pages with rate-limit spacing. */
export async function* paginate<T>(
  fetcher: Fetcher<T>,
  baseParams: Record<string, unknown>,
  pageSize = 500
): AsyncGenerator<T, void, undefined> {
  let cursor: string | undefined;
  let n = 0;
  do {
    const params = { ...baseParams, limit: pageSize, ...(cursor ? { cursor } : {}) };
    if (n++ > 0) await new Promise((r) => setTimeout(r, 170)); // 6 req/sec
    const page = await fetcher(params);
    for (const item of page.items) yield item;
    cursor = page.hasNextCursor() ? page.nextCursor() : undefined;
  } while (cursor);
}

/** Collect all pages into an array (use only when dataset fits in memory). */
export async function paginateAll<T>(fetcher: Fetcher<T>, params: Record<string, unknown>): Promise<T[]> {
  const out: T[] = [];
  for await (const item of paginate(fetcher, params)) out.push(item);
  return out;
}
```

Usage:

```typescript
const allKeys = await paginateAll(
  (p) => client.keys().list(p),
  { project_id: "123456.abcdef", include_translations: 1 }
);
```

3. Wrap API calls with structured error handling that classifies retryable errors.

```typescript
// src/lib/lokalise-api.ts
export class LokaliseError extends Error {
  constructor(
    message: string,
    public readonly statusCode: number,
    public readonly isRetryable: boolean
  ) {
    super(message);
    this.name = "LokaliseError";
  }
}

export async function apiCall<T>(fn: () => Promise<T>): Promise<T> {
  try {
    return await fn();
  } catch (err: unknown) {
    if (err && typeof err === "object" && "code" in err) {
      const e = err as { code: number; message: string };
      throw new LokaliseError(e.message, e.code, e.code === 429 || e.code >= 500);
    }
    throw err;
  }
}

// Usage
try {
  const keys = await apiCall(() => client.keys().list({ project_id: pid, limit: 500 }));
} catch (err) {
  if (err instanceof LokaliseError && err.isRetryable) {
    console.log("Transient failure, safe to retry");
  }
}
```

4. Batch key operations that chunk requests to respect the 500-key-per-request limit.

```typescript
// src/lib/batch.ts
function chunk<T>(arr: T[], size: number): T[][] {
  const out: T[][] = [];
  for (let i = 0; i < arr.length; i += size) out.push(arr.slice(i, i + size));
  return out;
}

/** Create keys in batches of 500 with rate-limit spacing. */
export async function batchCreateKeys(
  client: LokaliseApi, projectId: string,
  keys: Array<{ key_name: { web: string }; platforms: string[]; tags?: string[];
    translations?: Array<{ language_iso: string; translation: string }> }>
): Promise<{ created: number; errors: Error[] }> {
  const batches = chunk(keys, 500);
  let created = 0;
  const errors: Error[] = [];
  for (let i = 0; i < batches.length; i++) {
    try {
      const r = await client.keys().create({ project_id: projectId, keys: batches[i] });
      created += r.items.length;
    } catch (err) { errors.push(err as Error); }
    if (i < batches.length - 1) await new Promise((r) => setTimeout(r, 500));
  }
  return { created, errors };
}

/** Delete keys in batches of 500. */
export async function batchDeleteKeys(
  client: LokaliseApi, projectId: string, keyIds: number[]
): Promise<number> {
  const batches = chunk(keyIds, 500);
  let deleted = 0;
  for (let i = 0; i < batches.length; i++) {
    const r = await client.keys().bulk_delete(batches[i], { project_id: projectId });
    deleted += r.keys_removed;
    if (i < batches.length - 1) await new Promise((r) => setTimeout(r, 500));
  }
  return deleted;
}
```

5. Upload files with async process monitoring and progress callbacks.

```typescript
// src/lib/upload.ts
import { readFileSync } from "node:fs";

export async function uploadWithProgress(
  client: LokaliseApi, projectId: string,
  opts: { filePath: string; langIso: string; tags?: string[];
    replaceModified?: boolean; cleanupMode?: boolean },
  onProgress?: (status: string, elapsedMs: number) => void
): Promise<{ processId: string; status: string; durationMs: number }> {
  const data = readFileSync(opts.filePath).toString("base64");
  const start = Date.now();

  const proc = await client.files().upload(projectId, {
    data,
    filename: opts.filePath.split("/").pop()!,
    lang_iso: opts.langIso,
    replace_modified: opts.replaceModified ?? true,
    cleanup_mode: opts.cleanupMode ?? false,
    detect_icu_plurals: true,
    tags: opts.tags,
  });
  onProgress?.("queued", Date.now() - start);

  // Poll process status until terminal state
  const maxWait = 120_000; // 2 minutes
  let last = proc.status;
  while (Date.now() - start < maxWait) {
    await new Promise((r) => setTimeout(r, 1500));
    const check = await client.queuedProcesses().get(proc.process_id, { project_id: projectId });
    if (check.status !== last) { last = check.status; onProgress?.(last, Date.now() - start); }
    if (check.status === "finished") return { processId: proc.process_id, status: "finished", durationMs: Date.now() - start };
    if (check.status === "cancelled" || check.status === "failed") throw new Error(`Upload ${check.status}: ${JSON.stringify(check.details)}`);
  }
  throw new Error(`Upload timed out after ${maxWait}ms`);
}
```

Usage:

```typescript
await uploadWithProgress(client, "123456.abcdef", {
  filePath: "./src/locales/en.json",
  langIso: "en",
  tags: ["ci"],
  replaceModified: true,
}, (status, ms) => console.log(`[${(ms / 1000).toFixed(1)}s] ${status}`));
```

6. Add a retry decorator with exponential backoff and a rate limiter for sequential calls.

```typescript
// src/lib/retry.ts
/** Retry on 429 and 5xx with exponential backoff + jitter. */
export async function withRetry<T>(
  fn: () => Promise<T>,
  opts: { maxRetries?: number; baseDelayMs?: number; maxDelayMs?: number;
    onRetry?: (attempt: number, err: Error, delayMs: number) => void } = {}
): Promise<T> {
  const { maxRetries = 3, baseDelayMs = 1000, maxDelayMs = 10_000, onRetry } = opts;
  let lastErr: Error | undefined;
  for (let i = 0; i <= maxRetries; i++) {
    try { return await fn(); }
    catch (err: unknown) {
      lastErr = err as Error;
      const code = (err as { code?: number })?.code;
      if (!(code === 429 || (code && code >= 500)) || i === maxRetries) throw err;
      const delay = Math.min(baseDelayMs * 2 ** i + Math.random() * 200, maxDelayMs);
      onRetry?.(i + 1, lastErr, delay);
      await new Promise((r) => setTimeout(r, delay));
    }
  }
  throw lastErr;
}

/** Enforce minimum spacing between calls (default: 170ms = 6 req/sec). */
export function rateLimited<A extends unknown[], R>(
  fn: (...args: A) => Promise<R>, minMs = 170
): (...args: A) => Promise<R> {
  let last = 0;
  return async (...args) => {
    const wait = minMs - (Date.now() - last);
    if (wait > 0) await new Promise((r) => setTimeout(r, wait));
    last = Date.now();
    return fn(...args);
  };
}
```

Usage:

```typescript
// Single call with retry
const keys = await withRetry(
  () => client.keys().list({ project_id: pid, limit: 500 }),
  { onRetry: (n, e, ms) => console.warn(`Retry ${n}: ${e.message} (${ms}ms)`) }
);

// Rate-limited sequential calls
const listKeys = rateLimited((p: Record<string, unknown>) => client.keys().list(p));
const p1 = await listKeys({ project_id: pid, page: 1, limit: 100 });
const p2 = await listKeys({ project_id: pid, page: 2, limit: 100 });
```

## Output

- Singleton client with compression and branch support
- Async generator for memory-efficient cursor pagination
- Type-safe error wrapper with `isRetryable` classification
- Batch create/delete respecting 500-key API limit
- File upload with process polling and progress callbacks
- Retry with exponential backoff + rate limiter at 6 req/sec

## Error Handling

| Pattern | When to Use | Behavior |
|---------|------------|----------|
| `apiCall()` | Every SDK call | Converts to typed `LokaliseError` with `isRetryable` |
| `withRetry()` | Rate limits or transient failures | Exponential backoff, retries 429 and 5xx only |
| `rateLimited()` | Sequential bulk calls | Enforces 170ms minimum spacing |
| `paginate()` | Fetching all keys/translations | Built-in 170ms delay between pages |
| `batchCreateKeys()` | Creating > 500 keys | 500-key chunks with 500ms spacing |
| `uploadWithProgress()` | File uploads | Polls process status with 2-minute timeout |

## Examples

### Combining All Patterns

```typescript
import { getClient, projectId } from "./lib/lokalise-client";
import { paginateAll } from "./lib/paginate";
import { withRetry } from "./lib/retry";
import { batchCreateKeys } from "./lib/batch";
import { uploadWithProgress } from "./lib/upload";

const client = getClient();
const pid = projectId("123456.abcdef", "develop");

// Upload, paginate, batch create, download — all with rate limiting and retry
await uploadWithProgress(client, pid, { filePath: "./src/locales/en.json", langIso: "en" },
  (s, ms) => console.log(`[${ms}ms] ${s}`));

const allKeys = await paginateAll((p) => client.keys().list(p), { project_id: pid });
console.log(`${allKeys.length} keys`);

const result = await batchCreateKeys(client, pid,
  Array.from({ length: 1200 }, (_, i) => ({
    key_name: { web: `gen.key_${i}` }, platforms: ["web"],
    translations: [{ language_iso: "en", translation: `Val ${i}` }],
  })));
console.log(`Created ${result.created}, errors: ${result.errors.length}`);

const bundle = await withRetry(() => client.files().download(pid, {
  format: "json", original_filenames: false, bundle_structure: "%LANG_ISO%.json",
}));
console.log(`Download: ${bundle.bundle_url}`);
```

## Resources

- [Node SDK Documentation](https://lokalise.github.io/node-lokalise-api/)
- [Pagination Guide](https://lokalise.github.io/node-lokalise-api/api/getting-started.html)
- [API Rate Limits](https://developers.lokalise.com/reference/api-rate-limits)
- [API Error Codes](https://developers.lokalise.com/reference/api-errors)
- [Branching](https://docs.lokalise.com/en/articles/3049428-branching)

## Next Steps

Apply these patterns in `lokalise-core-workflow-a` and `lokalise-core-workflow-b` for real-world usage.
