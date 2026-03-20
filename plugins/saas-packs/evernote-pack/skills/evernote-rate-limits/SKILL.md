---
name: evernote-rate-limits
description: |
  Handle Evernote API rate limits effectively.
  Use when implementing rate limit handling, optimizing API usage,
  or troubleshooting rate limit errors.
  Trigger with phrases like "evernote rate limit", "evernote throttling",
  "api quota evernote", "rate limit exceeded".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Evernote Rate Limits

## Overview
Evernote enforces rate limits per API key, per user. When exceeded, the API throws `EDAMSystemException` with `errorCode: RATE_LIMIT_REACHED` and `rateLimitDuration` (seconds to wait). Production integrations must handle this gracefully.

## Prerequisites
- Evernote SDK setup
- Understanding of async/await patterns
- Error handling implementation

## Instructions

### Step 1: Rate Limit Handler

Catch `EDAMSystemException` and check for `rateLimitDuration`. Implement exponential backoff: wait the specified duration, then retry. Track retry attempts to avoid infinite loops.

```javascript
async function withRateLimitRetry(operation, maxRetries = 3) {
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error) {
      if (error.rateLimitDuration && attempt < maxRetries - 1) {
        const waitMs = error.rateLimitDuration * 1000;
        console.log(`Rate limited. Waiting ${error.rateLimitDuration}s...`);
        await new Promise(r => setTimeout(r, waitMs));
        continue;
      }
      throw error;
    }
  }
}
```

### Step 2: Rate-Limited Client Wrapper

Wrap the NoteStore with a class that adds configurable delays between API calls. Use a request queue to prevent bursts. Track request timestamps for monitoring.

```javascript
class RateLimitedClient {
  constructor(noteStore, minDelayMs = 100) {
    this.noteStore = noteStore;
    this.minDelayMs = minDelayMs;
    this.lastRequestTime = 0;
  }

  async call(method, ...args) {
    const elapsed = Date.now() - this.lastRequestTime;
    if (elapsed < this.minDelayMs) {
      await new Promise(r => setTimeout(r, this.minDelayMs - elapsed));
    }
    this.lastRequestTime = Date.now();
    return withRateLimitRetry(() => this.noteStore[method](...args));
  }
}
```

### Step 3: Batch Operations with Rate Limiting

Process items sequentially with delay between each operation. On rate limit, wait and retry the failed item. Report progress via callback. Collect successes and failures.

### Step 4: Avoiding Rate Limits

Strategies to minimize API calls: cache `listNotebooks()` and `listTags()` results, use `findNotesMetadata()` instead of `getNote()` for listings, request only needed fields in `NotesMetadataResultSpec`, batch reads with sync chunks instead of individual fetches.

### Step 5: Rate Limit Monitoring

Track request counts, rate limit hits, average response times, and wait times. Log statistics periodically to identify optimization opportunities.

For the complete rate limiter, batch processor, monitoring dashboard, and optimization examples, see [Implementation Guide](references/implementation-guide.md).

## Output
- Automatic retry with exponential backoff on rate limit errors
- Request queue with configurable minimum delay between calls
- Batch processor with progress tracking and failure collection
- Rate limit monitoring with request/error statistics
- API call optimization strategies (caching, metadata-only queries)

## Error Handling
| Scenario | Response |
|----------|----------|
| First rate limit hit | Wait `rateLimitDuration` seconds, retry |
| Repeated rate limits | Increase `minDelayMs`, reduce batch size |
| Rate limit during sync | Pause sync, wait, resume from last USN |
| Rate limit on initial setup | Request rate limit boost from Evernote support |

## Resources
- [Rate Limits Overview](https://dev.evernote.com/doc/articles/rate_limits.php)
- [API Best Practices](https://dev.evernote.com/doc/articles/rate_limits.php)
- [Webhooks (reduce polling)](https://dev.evernote.com/doc/articles/webhooks.php)

## Next Steps
For security considerations, see `evernote-security-basics`.

## Examples

**Batch note export**: Export 1,000 notes with 200ms delay between API calls and automatic retry on rate limits. Track progress and report failures at the end.

**High-throughput sync**: Use `getFilteredSyncChunk()` to fetch changes in bulk (100 entries per call) instead of individual `getNote()` calls, reducing API call count by 100x.
