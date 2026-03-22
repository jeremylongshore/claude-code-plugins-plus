---
name: hootsuite-rate-limits
description: |
  Implement Hootsuite rate limiting, backoff, and idempotency patterns.
  Use when handling rate limit errors, implementing retry logic,
  or optimizing API request throughput for Hootsuite.
  Trigger with phrases like "hootsuite rate limit", "hootsuite throttling",
  "hootsuite 429", "hootsuite retry", "hootsuite backoff".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, hootsuite, social-media]
compatible-with: claude-code
---

# Hootsuite Rate Limits

## Overview

Handle Hootsuite API rate limits. The API returns `429 Too Many Requests` with `Retry-After` headers when limits are exceeded.

## Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| General API | Varies by plan | Per minute |
| Message scheduling | ~100/hour | Per hour |
| Media upload | ~50/hour | Per hour |
| Token refresh | ~10/hour | Per hour |

## Instructions

### Step 1: Respect Retry-After Header

```typescript
async function rateLimitedRequest(url: string, options: RequestInit = {}) {
  const response = await fetch(url, {
    ...options,
    headers: { 'Authorization': `Bearer ${process.env.HOOTSUITE_ACCESS_TOKEN}`, ...options.headers },
  });

  if (response.status === 429) {
    const retryAfter = parseInt(response.headers.get('Retry-After') || '60');
    console.log(`Rate limited. Retrying in ${retryAfter}s`);
    await new Promise(r => setTimeout(r, retryAfter * 1000));
    return rateLimitedRequest(url, options); // Retry
  }

  return response;
}
```

### Step 2: Queue-Based Scheduling

```typescript
import PQueue from 'p-queue';

const hootsuiteQueue = new PQueue({
  concurrency: 1,
  interval: 1000,
  intervalCap: 2, // 2 requests per second
});

async function queuedSchedule(profileId: string, text: string, time: Date) {
  return hootsuiteQueue.add(() =>
    fetch('https://platform.hootsuite.com/v1/messages', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${process.env.HOOTSUITE_ACCESS_TOKEN}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, socialProfileIds: [profileId], scheduledSendTime: time.toISOString() }),
    })
  );
}
```

## Resources

- [Hootsuite API FAQ](https://developer.hootsuite.com/docs/rest-api-faq)

## Next Steps

For security, see `hootsuite-security-basics`.
