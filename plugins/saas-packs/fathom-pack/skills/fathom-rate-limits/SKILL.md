---
name: fathom-rate-limits
description: |
  Handle Fathom API rate limits (60 requests/minute per user).
  Trigger with phrases like "fathom rate limit", "fathom 429", "fathom throttle".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, meeting-intelligence, ai-notes, fathom]
compatible-with: claude-code
---

# Fathom Rate Limits

## Overview

Fathom's API enforces a strict 60 requests-per-minute cap per user across all API keys. Since meeting transcripts and action items are often fetched in bulk after a day of calls, this limit becomes a real constraint for teams processing large meeting backlogs. Transcript endpoints are especially heavy because they return full conversation text, making pagination and careful throttling essential for any integration that syncs meeting intelligence into CRMs or project trackers.

## Rate Limit Reference

| Endpoint | Limit | Window | Scope |
|----------|-------|--------|-------|
| List meetings | 60 req | 1 minute | Per user |
| Get transcript | 60 req | 1 minute | Per user |
| Action items | 60 req | 1 minute | Per user |
| Meeting summary | 60 req | 1 minute | Per user |
| Webhook management | 10 req | 1 minute | Per user |

## Rate Limiter Implementation

```typescript
class FathomRateLimiter {
  private tokens: number = 60;
  private lastRefill: number = Date.now();
  private queue: Array<{ resolve: () => void }> = [];

  async acquire(): Promise<void> {
    this.refill();
    if (this.tokens >= 1) { this.tokens -= 1; return; }
    return new Promise(resolve => this.queue.push({ resolve }));
  }

  private refill() {
    const now = Date.now();
    const elapsed = now - this.lastRefill;
    this.tokens = Math.min(60, this.tokens + (elapsed / 60_000) * 60);
    this.lastRefill = now;
    while (this.tokens >= 1 && this.queue.length) {
      this.tokens -= 1;
      this.queue.shift()!.resolve();
    }
  }
}

const limiter = new FathomRateLimiter();
```

## Retry Strategy

```typescript
async function fathomRetry<T>(fn: () => Promise<Response>, maxRetries = 3): Promise<T> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    await limiter.acquire();
    const res = await fn();
    if (res.ok) return res.json();
    if (res.status === 429) {
      const retryAfter = parseInt(res.headers.get("Retry-After") || "60", 10);
      const jitter = Math.random() * 3000;
      await new Promise(r => setTimeout(r, retryAfter * 1000 + jitter));
      continue;
    }
    if (res.status >= 500 && attempt < maxRetries) {
      await new Promise(r => setTimeout(r, Math.pow(2, attempt) * 2000));
      continue;
    }
    throw new Error(`Fathom API ${res.status}: ${await res.text()}`);
  }
  throw new Error("Max retries exceeded");
}
```

## Batch Processing

```typescript
async function syncAllTranscripts(meetingIds: string[], batchSize = 10) {
  const results: any[] = [];
  for (let i = 0; i < meetingIds.length; i += batchSize) {
    const batch = meetingIds.slice(i, i + batchSize);
    const batchResults = await Promise.all(
      batch.map(id => fathomRetry(() =>
        fetch(`${BASE}/api/v1/meetings/${id}/transcript`, { headers })
      ))
    );
    results.push(...batchResults);
    if (i + batchSize < meetingIds.length) await new Promise(r => setTimeout(r, 12_000));
  }
  return results;
}
```

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| 429 Too Many Requests | Exceeded 60 req/min user cap | Wait for Retry-After, then resume |
| Empty transcript | Meeting still processing | Poll with 30s interval until ready |
| 401 on refresh | Expired OAuth token | Rotate token before batch starts |
| Timeout on long meetings | Transcript > 2 hours of audio | Request with `Accept-Encoding: gzip` |
| Missing action items | AI extraction not yet complete | Retry after 5-minute delay |

## Resources

- [Fathom API Documentation](https://fathom.video/developers)

## Next Steps

See `fathom-performance-tuning`.
