---
name: grammarly-rate-limits
description: |
  Implement Grammarly rate limiting, backoff, and idempotency patterns.
  Use when handling rate limit errors, implementing retry logic,
  or optimizing API request throughput for Grammarly.
  Trigger with phrases like "grammarly rate limit", "grammarly throttling",
  "grammarly 429", "grammarly retry", "grammarly backoff".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, grammarly, writing]
compatible-with: claude-code
---

# Grammarly Rate Limits

## Rate Limits

| API | Limit | Notes |
|-----|-------|-------|
| Writing Score | Plan-dependent | Per minute |
| AI Detection | Plan-dependent | Per minute |
| Plagiarism | Plan-dependent | Async, poll for results |
| Token endpoint | ~10/hour | Client credentials |

## Instructions

### Exponential Backoff

```typescript
async function grammarlyWithBackoff<T>(fn: () => Promise<T>, maxRetries = 3): Promise<T> {
  for (let i = 0; i <= maxRetries; i++) {
    try { return await fn(); }
    catch (err: any) {
      if (err.status !== 429 || i === maxRetries) throw err;
      const delay = 1000 * Math.pow(2, i) + Math.random() * 1000;
      await new Promise(r => setTimeout(r, delay));
    }
  }
  throw new Error('Unreachable');
}
```

### Queue-Based Processing

```typescript
import PQueue from 'p-queue';
const grammarlyQueue = new PQueue({ concurrency: 2, interval: 1000, intervalCap: 5 });

async function queuedScore(text: string, token: string) {
  return grammarlyQueue.add(() =>
    fetch('https://api.grammarly.com/ecosystem/api/v2/scores', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    }).then(r => r.json())
  );
}
```

## Resources

- [Grammarly API](https://developer.grammarly.com/)

## Next Steps

For security, see `grammarly-security-basics`.
