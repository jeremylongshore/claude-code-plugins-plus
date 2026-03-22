---
name: algolia-rate-limits
description: |
  Handle Algolia rate limits and throttling: per-key limits, indexing queue limits,
  429 responses, and backoff strategies.
  Trigger: "algolia rate limit", "algolia throttling", "algolia 429",
  "algolia retry", "algolia backoff", "algolia too many requests".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, search, algolia]
compatible-with: claude-code
---

# Algolia Rate Limits

## Overview

Algolia has two distinct rate limiting mechanisms: **per-API-key limits** (configurable, returns HTTP 429) and **server-side indexing limits** (protects cluster stability, returns HTTP 429 with specific messages). The `algoliasearch` v5 client has built-in retry with backoff, but you need to handle sustained rate limiting yourself.

## How Algolia Rate Limiting Works

### Per-API-Key Rate Limits

| Setting | Default | Where to Change |
|---------|---------|-----------------|
| `maxQueriesPerIPPerHour` | 0 (unlimited) | Dashboard > API Keys > Edit |
| `maxHitsPerQuery` | 1000 | Dashboard > API Keys > Edit |
| Search requests | Plan-dependent | Upgrade plan |

### Server-Side Indexing Limits

When the indexing queue is overloaded, Algolia returns 429 with these messages:

| Message | Meaning | Action |
|---------|---------|--------|
| `Too many jobs` | Queue full | Reduce batch frequency |
| `Job queue too large` | Too much pending work | Wait for queue to drain |
| `Old jobs on the queue` | Stuck tasks | Check dashboard > Indices > Operations |
| `Disk almost full` | Record quota near limit | Delete unused records or upgrade |

## Instructions

### Step 1: Configure Per-Key Rate Limits

```typescript
import { algoliasearch } from 'algoliasearch';

const client = algoliasearch(process.env.ALGOLIA_APP_ID!, process.env.ALGOLIA_ADMIN_KEY!);

// Create a rate-limited API key for frontend use
const { key } = await client.addApiKey({
  apiKey: {
    acl: ['search'],
    description: 'Frontend search key — rate limited',
    maxQueriesPerIPPerHour: 1000,  // Per user IP
    maxHitsPerQuery: 20,
    indexes: ['products'],          // Restrict to specific indices
    validity: 0,                    // 0 = never expires
  },
});
console.log(`Created rate-limited key: ${key}`);
```

### Step 2: Implement Backoff for Sustained 429s

```typescript
import { ApiError } from 'algoliasearch';

async function withBackoff<T>(
  operation: () => Promise<T>,
  config = { maxRetries: 5, baseDelayMs: 1000, maxDelayMs: 30000 }
): Promise<T> {
  for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error) {
      if (attempt === config.maxRetries) throw error;

      // Only retry on 429 or 5xx
      if (error instanceof ApiError) {
        if (error.status !== 429 && error.status < 500) throw error;
      }

      // Exponential backoff with jitter
      const delay = Math.min(
        config.baseDelayMs * Math.pow(2, attempt) + Math.random() * 500,
        config.maxDelayMs
      );
      console.warn(`Rate limited (attempt ${attempt + 1}). Retrying in ${delay.toFixed(0)}ms`);
      await new Promise(r => setTimeout(r, delay));
    }
  }
  throw new Error('Unreachable');
}

// Usage
const { hits } = await withBackoff(() =>
  client.searchSingleIndex({ indexName: 'products', searchParams: { query: 'laptop' } })
);
```

### Step 3: Throttled Batch Indexing

```typescript
import PQueue from 'p-queue';

// Limit concurrent indexing operations to avoid overloading the queue
const indexingQueue = new PQueue({
  concurrency: 1,       // One batch at a time
  interval: 1000,       // Per second
  intervalCap: 2,       // Max 2 operations per second
});

async function throttledBulkIndex(records: Record<string, any>[]) {
  const BATCH_SIZE = 500;
  const chunks: Record<string, any>[][] = [];
  for (let i = 0; i < records.length; i += BATCH_SIZE) {
    chunks.push(records.slice(i, i + BATCH_SIZE));
  }

  let indexed = 0;
  await Promise.all(
    chunks.map(chunk =>
      indexingQueue.add(async () => {
        const { taskID } = await client.saveObjects({
          indexName: 'products',
          objects: chunk,
        });
        await client.waitForTask({ indexName: 'products', taskID });
        indexed += chunk.length;
        console.log(`Indexed ${indexed}/${records.length}`);
      })
    )
  );
}
```

### Step 4: Monitor Usage Approaching Limits

```typescript
// Check current API key usage via the dashboard or programmatically
async function checkKeyUsage(apiKey: string) {
  const keyInfo = await client.getApiKey({ key: apiKey });

  console.log({
    description: keyInfo.description,
    maxQueriesPerIPPerHour: keyInfo.maxQueriesPerIPPerHour,
    acl: keyInfo.acl,
    indexes: keyInfo.indexes,
  });
}

// Check record count vs plan limit
async function checkRecordUsage() {
  const { items } = await client.listIndices();
  const totalRecords = items.reduce((sum, idx) => sum + (idx.entries || 0), 0);
  console.log(`Total records across all indices: ${totalRecords.toLocaleString()}`);
}
```

## Error Handling

| Scenario | Detection | Response |
|----------|-----------|----------|
| Burst spike (429) | `ApiError` with status 429 | Built-in retry handles it; add backoff for persistence |
| Sustained overload | Repeated 429s across minutes | Reduce batch size and frequency |
| Indexing queue full | 429 with "Too many jobs" | Pause indexing, wait for queue drain |
| Plan limit reached | 429 with quota message | Upgrade plan or reduce record count |

## Resources

- [API Key Rate Limiting](https://support.algolia.com/hc/en-us/articles/4905140190353)
- [Indexing Rate Limits](https://support.algolia.com/hc/en-us/articles/4406975251089)
- [p-queue](https://github.com/sindresorhus/p-queue)

## Next Steps

For security configuration, see `algolia-security-basics`.
