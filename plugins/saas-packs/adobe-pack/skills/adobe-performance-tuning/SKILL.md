---
name: adobe-performance-tuning
description: |
  Optimize Adobe API performance with token caching, async job batching,
  connection pooling, and response caching for Firefly, PDF Services,
  and Photoshop API workflows.
  Trigger with phrases like "adobe performance", "optimize adobe",
  "adobe latency", "adobe caching", "adobe slow", "adobe batch".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, adobe]
compatible-with: claude-code
---

# Adobe Performance Tuning

## Overview

Optimize Adobe API performance across Firefly Services, PDF Services, and Photoshop APIs. Key bottlenecks include IMS token generation, async job polling overhead, and cold-start latency on serverless platforms.

## Prerequisites

- Adobe SDK installed and functional
- Understanding of which APIs your app uses most
- Redis or in-memory cache available (optional)
- Performance monitoring in place

## Latency Benchmarks (Real-World)

| Operation | P50 | P95 | P99 |
|-----------|-----|-----|-----|
| IMS Token Generation | 200ms | 500ms | 1s |
| Firefly Text-to-Image (sync) | 5s | 12s | 20s |
| Firefly Text-to-Image (async poll) | 8s | 15s | 25s |
| PDF Extract (10-page doc) | 3s | 8s | 15s |
| PDF Create from HTML | 2s | 5s | 10s |
| Photoshop Remove Background | 4s | 10s | 18s |
| Lightroom Auto Tone | 3s | 8s | 15s |

## Instructions

### Optimization 1: Cache IMS Access Tokens (Biggest Win)

The IMS token endpoint returns tokens valid for 24 hours. Never re-generate per request:

```typescript
// WRONG: generates new token every call (adds 200-500ms each time)
async function makeRequest() {
  const token = await getAccessToken(); // hits IMS every time
}

// RIGHT: cache token and only refresh when expiring
let tokenCache: { token: string; expiresAt: number } | null = null;

async function getCachedToken(): Promise<string> {
  if (tokenCache && tokenCache.expiresAt > Date.now() + 300_000) {
    return tokenCache.token; // Cache hit — 0ms
  }
  const res = await fetch('https://ims-na1.adobelogin.com/ims/token/v3', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      client_id: process.env.ADOBE_CLIENT_ID!,
      client_secret: process.env.ADOBE_CLIENT_SECRET!,
      grant_type: 'client_credentials',
      scope: process.env.ADOBE_SCOPES!,
    }),
  });
  const data = await res.json();
  tokenCache = { token: data.access_token, expiresAt: Date.now() + data.expires_in * 1000 };
  return tokenCache.token;
}
```

### Optimization 2: Parallel Async Job Submission

Firefly and Photoshop APIs are async — submit all jobs first, then poll all:

```typescript
// SLOW: sequential (total = sum of all job times)
for (const prompt of prompts) {
  const result = await generateImageSync(prompt); // 5-20s each
}

// FAST: parallel submit + parallel poll (total = max job time)
async function batchFireflyGenerate(prompts: string[]) {
  const token = await getCachedToken();

  // 1. Submit all jobs simultaneously
  const jobSubmissions = await Promise.all(
    prompts.map(prompt =>
      fetch('https://firefly-api.adobe.io/v3/images/generate-async', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'x-api-key': process.env.ADOBE_CLIENT_ID!,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ prompt, n: 1, size: { width: 1024, height: 1024 } }),
      }).then(r => r.json())
    )
  );

  // 2. Poll all jobs in parallel
  const results = await Promise.all(
    jobSubmissions.map(job => pollUntilDone(job.statusUrl, token))
  );

  return results;
}
```

### Optimization 3: Response Caching for Repeated Operations

```typescript
import { LRUCache } from 'lru-cache';

// Cache PDF extraction results (same PDF = same output)
const extractionCache = new LRUCache<string, any>({
  max: 100,
  ttl: 3600_000, // 1 hour
});

async function cachedPdfExtract(pdfHash: string, pdfPath: string) {
  const cached = extractionCache.get(pdfHash);
  if (cached) {
    console.log('PDF extraction cache hit');
    return cached;
  }

  const result = await extractPdfContent(pdfPath);
  extractionCache.set(pdfHash, result);
  return result;
}
```

### Optimization 4: Connection Keep-Alive

```typescript
import { Agent } from 'https';

// Reuse TCP connections to Adobe endpoints
const adobeAgent = new Agent({
  keepAlive: true,
  maxSockets: 10,
  maxFreeSockets: 5,
  timeout: 60_000,
});

// Use with node-fetch or undici
const response = await fetch(url, {
  // @ts-ignore — agent option supported by node-fetch
  agent: adobeAgent,
  headers: { ... },
});
```

### Optimization 5: Smart Polling Intervals

```typescript
// Adaptive polling: start fast, slow down over time
async function adaptivePoll(statusUrl: string, token: string) {
  const intervals = [1000, 2000, 3000, 5000, 5000, 10000]; // ms
  let attempt = 0;

  while (true) {
    const res = await fetch(statusUrl, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'x-api-key': process.env.ADOBE_CLIENT_ID!,
      },
    });
    const status = await res.json();

    if (status.status === 'succeeded') return status;
    if (status.status === 'failed') throw new Error(status.error?.message);

    const delay = intervals[Math.min(attempt, intervals.length - 1)];
    await new Promise(r => setTimeout(r, delay));
    attempt++;
  }
}
```

## Output

- IMS token cached for 24h (eliminates 200-500ms per request)
- Parallel job submission for batch operations
- LRU response caching for repeated extractions
- Connection keep-alive reducing TLS handshake overhead
- Adaptive polling reducing unnecessary API calls

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Stale cached token | Token revoked mid-lifecycle | Catch 401, clear cache, retry once |
| Parallel rate limiting | Too many concurrent jobs | Add p-queue concurrency limit |
| Cache memory pressure | Too many cached results | Set LRU max size |
| Connection pool exhaustion | Too many parallel requests | Limit maxSockets to 10-20 |

## Resources

- [Firefly Async API Guide](https://developer.adobe.com/firefly-services/docs/firefly-api/guides/how-tos/using-async-apis)
- [PDF Services Quickstart](https://developer.adobe.com/document-services/docs/overview/pdf-services-api/quickstarts/nodejs/)
- [LRU Cache npm](https://github.com/isaacs/node-lru-cache)

## Next Steps

For cost optimization, see `adobe-cost-tuning`.
