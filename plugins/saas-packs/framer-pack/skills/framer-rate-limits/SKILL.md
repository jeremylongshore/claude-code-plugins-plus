---
name: framer-rate-limits
description: |
  Implement Framer rate limiting, backoff, and idempotency patterns.
  Use when handling rate limit errors, implementing retry logic,
  or optimizing API request throughput for Framer.
  Trigger with phrases like "framer rate limit", "framer throttling",
  "framer 429", "framer retry", "framer backoff".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, framer]
compatible-with: claude-code
---

# Framer Rate Limits

## Overview

Handle Framer API rate limits for Server API and plugin operations. The Server API uses WebSocket, so rate limits apply per-connection. CMS operations are limited by collection size and concurrent writes.

## Rate Limit Reference

| Operation | Limit | Notes |
|-----------|-------|-------|
| Server API connections | 1 per site | WebSocket, persistent |
| CMS setItems | ~100 items/call | Batch larger sets |
| CMS getItems | No hard limit | Returns all items |
| Plugin API calls | Debounced | Framer throttles internally |
| Publish | ~1/minute | Site publishing |
| Image upload | Concurrent limit | Via CMS image fields |

## Instructions

### Step 1: Batch CMS Writes

```typescript
async function batchSetItems(collection: any, items: any[], batchSize = 100) {
  for (let i = 0; i < items.length; i += batchSize) {
    const batch = items.slice(i, i + batchSize);
    await collection.setItems(batch);
    console.log(`Synced ${Math.min(i + batchSize, items.length)}/${items.length}`);
    if (i + batchSize < items.length) {
      await new Promise(r => setTimeout(r, 1000)); // 1s between batches
    }
  }
}
```

### Step 2: Debounced Plugin Operations

```typescript
// Debounce rapid plugin UI interactions
function debounce<T extends (...args: any[]) => any>(fn: T, ms = 300) {
  let timer: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), ms);
  };
}

const debouncedSync = debounce(async () => {
  await syncCollection();
}, 500);
```

### Step 3: Retry for Server API

```typescript
async function withRetry<T>(fn: () => Promise<T>, maxRetries = 3): Promise<T> {
  for (let i = 0; i <= maxRetries; i++) {
    try {
      return await fn();
    } catch (err: any) {
      if (i === maxRetries) throw err;
      const delay = 1000 * Math.pow(2, i);
      console.log(`Retry ${i + 1} in ${delay}ms`);
      await new Promise(r => setTimeout(r, delay));
    }
  }
  throw new Error('Unreachable');
}
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| WebSocket disconnected | Connection timeout | Reconnect with backoff |
| setItems slow | Large batch | Split into chunks of 100 |
| Publish rate limited | Too frequent | Wait 60s between publishes |

## Resources

- [Framer Server API](https://www.framer.com/developers/server-api-introduction)
- [Framer API Reference](https://www.framer.com/developers/reference)

## Next Steps

For security, see `framer-security-basics`.
