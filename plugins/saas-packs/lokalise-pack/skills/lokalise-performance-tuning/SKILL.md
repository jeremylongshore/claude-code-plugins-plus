---
name: lokalise-performance-tuning
description: |
  Optimize Lokalise API performance with caching, pagination, and bulk operations.
  Use when experiencing slow API responses, implementing caching strategies,
  or optimizing request throughput for Lokalise integrations.
  Trigger with phrases like "lokalise performance", "optimize lokalise",
  "lokalise latency", "lokalise caching", "lokalise slow", "lokalise batch".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*), Bash(curl:*), Bash(jq:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Lokalise Performance Tuning

## Overview

Optimize Lokalise API throughput for translation pipelines by implementing cursor pagination, local caching, batch key operations (500/request), request throttling under the 6 req/s rate limit, and selective language downloads.

## Prerequisites

- `@lokalise/node-api` SDK v9+ (ESM) or REST API access
- `LOKALISE_API_TOKEN` environment variable set
- Understanding of project size (key count, language count) to calibrate batch sizes
- Optional: Redis or LRU cache library for persistent caching

## Instructions

### Step 1: Use Cursor Pagination for Large Datasets

Cursor pagination is significantly faster than offset pagination for projects with 5K+ keys. Offset pagination degrades as page numbers increase because the server must skip rows; cursor pagination uses a pointer.

```typescript
import { LokaliseApi } from '@lokalise/node-api';
const lok = new LokaliseApi({ apiKey: process.env.LOKALISE_API_TOKEN! });

// Generator that yields all keys using cursor pagination
async function* getAllKeys(projectId: string) {
  let cursor: string | undefined;
  do {
    const result = await lok.keys().list({
      project_id: projectId,
      limit: 500,              // Maximum allowed per request
      pagination: 'cursor',
      cursor,
    });
    for (const key of result.items) yield key;
    cursor = result.hasNextCursor() ? result.nextCursor : undefined;
  } while (cursor);
}

// Usage: 10,000 keys = 20 API calls (vs 100 with default limit=100)
let count = 0;
for await (const key of getAllKeys('PROJECT_ID')) {
  count++;
}
console.log(`Fetched ${count} keys`);
```

**Offset pagination comparison (avoid for large projects):**

| Keys | Offset (limit=100) | Cursor (limit=500) | Time saved |
|------|--------------------|--------------------|-----------|
| 1,000 | 10 requests | 2 requests | 80% |
| 10,000 | 100 requests | 20 requests | 80% |
| 50,000 | 500 requests (~84s) | 100 requests (~17s) | 80% |

### Step 2: Cache Translation Downloads Locally

Translation file downloads are the most expensive Lokalise operation. Cache them locally and use project `last_activity` timestamps to invalidate.

```typescript
import { LokaliseApi } from '@lokalise/node-api';
import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'fs';

const lok = new LokaliseApi({ apiKey: process.env.LOKALISE_API_TOKEN! });
const CACHE_DIR = '.lokalise-cache';

interface CacheEntry {
  url: string;
  timestamp: string;
  languages: string[];
}

function getCachePath(projectId: string, langIso: string): string {
  return `${CACHE_DIR}/${projectId}/${langIso}.json`;
}

function getMetaPath(projectId: string): string {
  return `${CACHE_DIR}/${projectId}/meta.json`;
}

async function downloadWithCache(projectId: string, langIso: string, format = 'json') {
  mkdirSync(`${CACHE_DIR}/${projectId}`, { recursive: true });
  const cachePath = getCachePath(projectId, langIso);
  const metaPath = getMetaPath(projectId);

  // Check if project was modified since last cache
  const project = await lok.projects().get(projectId);
  const lastActivity = project.statistics?.last_activity ?? project.created_at;

  if (existsSync(metaPath)) {
    const meta: CacheEntry = JSON.parse(readFileSync(metaPath, 'utf8'));
    if (meta.timestamp === lastActivity && existsSync(cachePath)) {
      console.log(`Cache hit: ${langIso} (unchanged since ${lastActivity})`);
      return JSON.parse(readFileSync(cachePath, 'utf8'));
    }
  }

  // Cache miss — download fresh
  const bundle = await lok.files().download(projectId, {
    format,
    filter_langs: [langIso],
    original_filenames: false,
  });

  // bundle.bundle_url contains a temporary download URL
  const response = await fetch(bundle.bundle_url);
  const data = await response.arrayBuffer();

  writeFileSync(cachePath, Buffer.from(data));
  writeFileSync(metaPath, JSON.stringify({
    url: bundle.bundle_url,
    timestamp: lastActivity,
    languages: [langIso],
  }));

  console.log(`Cache miss: downloaded ${langIso} (${data.byteLength} bytes)`);
  return data;
}
```

### Step 3: Batch Key Operations

Lokalise supports creating, updating, and deleting up to 500 keys per request. Always batch instead of making individual requests.

```typescript
// Bulk create keys — 500 per batch with rate limit awareness
async function createKeysBatched(projectId: string, keys: any[]) {
  const BATCH_SIZE = 500;
  const results = [];

  for (let i = 0; i < keys.length; i += BATCH_SIZE) {
    const batch = keys.slice(i, i + BATCH_SIZE);
    const result = await lok.keys().create({
      project_id: projectId,
      keys: batch,
    });
    results.push(...result.items);
    console.log(`Batch ${Math.floor(i / BATCH_SIZE) + 1}: created ${result.items.length} keys`);
    await new Promise(r => setTimeout(r, 200)); // Stay under 6 req/s
  }

  return results;
}

// Bulk update keys — same 500-key batch limit
async function updateKeysBatched(projectId: string, updates: Array<{key_id: number; [k: string]: any}>) {
  const BATCH_SIZE = 500;
  for (let i = 0; i < updates.length; i += BATCH_SIZE) {
    const batch = updates.slice(i, i + BATCH_SIZE);
    await lok.keys().bulk_update({
      project_id: projectId,
      keys: batch,
    });
    await new Promise(r => setTimeout(r, 200));
  }
}

// Bulk delete — up to 500 key IDs per request
async function deleteKeysBatched(projectId: string, keyIds: number[]) {
  const BATCH_SIZE = 500;
  for (let i = 0; i < keyIds.length; i += BATCH_SIZE) {
    const batch = keyIds.slice(i, i + BATCH_SIZE);
    await lok.keys().bulk_delete({
      project_id: projectId,
      keys: batch,
    });
    await new Promise(r => setTimeout(r, 200));
  }
}

// 2,000 keys: 4 batched requests instead of 2,000 individual ones
```

### Step 4: Implement Request Throttling

A proper request queue prevents `429 Too Many Requests` errors and makes your integration resilient under load.

```typescript
import PQueue from 'p-queue';

// Lokalise rate limit: 6 requests/second
// Use 5 concurrent with 1s interval for safety margin
const queue = new PQueue({
  concurrency: 5,
  interval: 1000,
  intervalCap: 5,
});

async function throttledRequest<T>(fn: () => Promise<T>): Promise<T> {
  return queue.add(fn) as Promise<T>;
}

// All API calls go through the queue automatically
const project = await throttledRequest(() => lok.projects().get(projectId));
const keys = await throttledRequest(() => lok.keys().list({
  project_id: projectId,
  limit: 500,
  pagination: 'cursor',
}));

// Works for parallel operations too — queue enforces the rate limit
const projectIds = ['PROJ_1', 'PROJ_2', 'PROJ_3', 'PROJ_4', 'PROJ_5'];
const allProjects = await Promise.all(
  projectIds.map(id => throttledRequest(() => lok.projects().get(id)))
);
```

### Step 5: Async File Operations with Webhooks

File uploads and downloads are processed asynchronously by Lokalise. Instead of polling the process status endpoint, use webhooks to get notified when processing completes.

```bash
set -euo pipefail
# Set up a webhook for file operation events
curl -s -X POST "https://api.lokalise.com/api2/projects/${PROJECT_ID}/webhooks" \
  -H "X-Api-Token: ${LOKALISE_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://hooks.company.com/lokalise",
    "events": [
      "project.imported",
      "project.exported",
      "project.keys_added"
    ]
  }' | jq '{webhook_id: .webhook.webhook_id, url: .webhook.url, events: .webhook.events}'
```

**If you must poll (no webhook endpoint available):**

```typescript
async function waitForProcess(projectId: string, processId: string, timeoutMs = 120_000) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    const proc = await throttledRequest(() =>
      lok.queuedProcesses().get(projectId, processId)
    );
    if (proc.status === 'finished') return proc;
    if (proc.status === 'cancelled' || proc.status === 'failed') {
      throw new Error(`Process ${processId} ${proc.status}: ${proc.message}`);
    }
    await new Promise(r => setTimeout(r, 2000)); // Poll every 2s
  }
  throw new Error(`Process ${processId} timed out after ${timeoutMs}ms`);
}
```

### Step 6: Selective Language Downloads (Delta Exports)

Downloading all languages when you only need one wastes bandwidth and API time. Always filter by language and, when possible, by modification timestamp.

```typescript
// Download only changed translations since last sync
async function downloadDelta(projectId: string, langIso: string, sinceTimestamp: string) {
  // Filter keys modified after the given timestamp
  const keys = await lok.keys().list({
    project_id: projectId,
    limit: 500,
    pagination: 'cursor',
    filter_translation_lang_ids: langIso,
    // Unfortunately, Lokalise doesn't support filter_modified_after on keys endpoint.
    // Workaround: download full file and diff locally, or use webhooks for real-time sync.
  });

  return keys.items;
}

// Download a single language file instead of all languages
async function downloadSingleLanguage(projectId: string, langIso: string) {
  const result = await lok.files().download(projectId, {
    format: 'json',
    filter_langs: [langIso],        // Only this language
    original_filenames: false,       // Flat structure
    bundle_structure: '%LANG_ISO%.%FORMAT%', // e.g., fr.json
    export_empty_as: 'base',         // Fall back to base language for untranslated
    include_tags: ['production'],    // Only production-tagged keys
  });
  return result.bundle_url;
}
```

### Step 7: Measure and Benchmark

```bash
set -euo pipefail
# Benchmark API response times across endpoints
echo "=== Lokalise API Benchmarks ==="

echo -n "Projects list: "
curl -s -o /dev/null -w "%{time_total}s" \
  -H "X-Api-Token: ${LOKALISE_API_TOKEN}" \
  "https://api.lokalise.com/api2/projects?limit=10"
echo ""

echo -n "Keys list (limit=500): "
curl -s -o /dev/null -w "%{time_total}s" \
  -H "X-Api-Token: ${LOKALISE_API_TOKEN}" \
  "https://api.lokalise.com/api2/projects/${PROJECT_ID}/keys?limit=500"
echo ""

echo -n "File download trigger: "
curl -s -o /dev/null -w "%{time_total}s" \
  -X POST -H "X-Api-Token: ${LOKALISE_API_TOKEN}" \
  -H "Content-Type: application/json" \
  "https://api.lokalise.com/api2/projects/${PROJECT_ID}/files/download" \
  -d '{"format":"json","filter_langs":["en"],"original_filenames":false}'
echo ""

echo -n "Rate limit headers: "
curl -s -D - -o /dev/null \
  -H "X-Api-Token: ${LOKALISE_API_TOKEN}" \
  "https://api.lokalise.com/api2/projects?limit=1" \
  | grep -i x-ratelimit
```

## Output

- Cursor pagination implemented for all list operations (80% fewer API calls)
- Translation download cache with timestamp-based invalidation
- Batch key operations (create/update/delete) using 500-key batches
- Request queue with PQueue throttling at 5 req/s (safety margin under 6 req/s limit)
- Webhooks configured for async file operations (replacing polling)
- Selective language downloads reducing bandwidth and processing time
- Benchmark results for baseline performance measurement

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `429 Too Many Requests` | Exceeded 6 req/s global rate limit | Use PQueue throttling (Step 4), retry with exponential backoff |
| Slow file downloads | Large project with 50+ languages | Filter by `filter_langs` to download one language at a time |
| Pagination timeout | Offset pagination on 50K+ key projects | Switch to cursor pagination (Step 1) |
| Bulk create partial failure | Network timeout on large batch | Reduce batch size from 500 to 200 and add retry logic per batch |
| Cache stale after team edits | `last_activity` not granular enough | Reduce cache TTL or use webhooks to invalidate on `project.translation_updated` |
| `bundle_url` expired | Download URL only valid for ~30 minutes | Fetch the URL and download immediately; do not store URLs for later |

## Examples

### Quick Rate Limit Check

```bash
set -euo pipefail
# See how much rate limit headroom you have right now
curl -s -D - -o /dev/null \
  -H "X-Api-Token: ${LOKALISE_API_TOKEN}" \
  "https://api.lokalise.com/api2/system/languages?limit=1" 2>/dev/null \
  | grep -iE 'x-ratelimit' | while read -r line; do echo "  $line"; done
```

## Resources

- [Lokalise Rate Limits](https://developers.lokalise.com/docs/api-rate-limits)
- [Cursor Pagination Docs](https://developers.lokalise.com/docs/cursor-pagination)
- [File Download API](https://developers.lokalise.com/reference/download-files)
- [Bulk Key Operations](https://developers.lokalise.com/reference/create-keys)
- [Webhook Events](https://developers.lokalise.com/reference/webhook-events)
- [p-queue (npm)](https://www.npmjs.com/package/p-queue)

## Next Steps

- For debugging performance issues, collect diagnostics with `lokalise-debug-bundle`.
- For SDK upgrade to get latest pagination improvements, see `lokalise-upgrade-migration`.
- For setting up CI pipelines with optimized API usage, see `lokalise-ci-integration`.
