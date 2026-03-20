---
name: evernote-performance-tuning
description: |
  Optimize Evernote integration performance.
  Use when improving response times, reducing API calls,
  or scaling Evernote integrations.
  Trigger with phrases like "evernote performance", "optimize evernote",
  "evernote speed", "evernote caching".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Evernote Performance Tuning

## Overview
Optimize Evernote API integration performance through response caching, efficient data retrieval, request batching, connection management, and performance monitoring.

## Prerequisites
- Working Evernote integration
- Understanding of API rate limits
- Caching infrastructure (Redis recommended, in-memory for simpler setups)

## Instructions

### Step 1: Response Caching

Cache frequently accessed data (notebook lists, tag lists, note metadata) with TTL-based expiration. Notebook and tag lists change rarely -- cache for 5-15 minutes. Note metadata can be cached for 1-5 minutes.

```javascript
class EvernoteCache {
  constructor(redis) {
    this.redis = redis;
  }

  async getOrFetch(key, fetcher, ttlSeconds = 300) {
    const cached = await this.redis.get(key);
    if (cached) return JSON.parse(cached);

    const data = await fetcher();
    await this.redis.setex(key, ttlSeconds, JSON.stringify(data));
    return data;
  }

  async listNotebooks(noteStore) {
    return this.getOrFetch('notebooks', () => noteStore.listNotebooks(), 600);
  }

  async listTags(noteStore) {
    return this.getOrFetch('tags', () => noteStore.listTags(), 600);
  }
}
```

### Step 2: Efficient Data Retrieval

Use `findNotesMetadata()` instead of `findNotes()` to avoid transferring full note content. Only request needed fields in `NotesMetadataResultSpec`. Fetch full content only when the user explicitly opens a note.

```javascript
// BAD: Fetches full content for all notes
const notes = await noteStore.findNotes(filter, 0, 100);

// GOOD: Fetches only metadata (title, dates, tags)
const metadata = await noteStore.findNotesMetadata(filter, 0, 100, spec);
// Fetch content only for the specific note user opens
const fullNote = await noteStore.getNote(guid, true, false, false, false);
```

### Step 3: Request Batching

Batch multiple operations using sync chunks instead of individual API calls. Use `getSyncChunk()` to fetch up to 100 changed notes in a single call instead of 100 `getNote()` calls.

### Step 4: Connection Optimization

Reuse the Evernote client instance across requests. The NoteStore maintains an HTTP connection that benefits from keep-alive. Create one client per user session, not per request.

### Step 5: Performance Monitoring

Track API call counts, response times (p50, p95, p99), cache hit rates, and rate limit occurrences. Alert on degradation.

For the complete caching layer, batching strategies, monitoring setup, and benchmark examples, see [Implementation Guide](references/implementation-guide.md).

## Output
- Redis-based response caching with TTL management
- Metadata-only query patterns (avoid unnecessary content transfer)
- Sync chunk batching for bulk operations
- Client instance reuse for connection optimization
- Performance monitoring with latency percentiles and cache hit rates

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `RATE_LIMIT_REACHED` | Too many API calls | Increase cache TTL, batch operations |
| Stale cache data | Cache not invalidated on update | Invalidate cache on webhook notification |
| Redis connection failure | Cache infrastructure down | Fall through to direct API call |
| Slow responses | Large note content in response | Use `findNotesMetadata()` for listings |

## Resources
- [Rate Limits](https://dev.evernote.com/doc/articles/rate_limits.php)
- [Synchronization (bulk fetch)](https://dev.evernote.com/doc/articles/synchronization.php)
- [API Reference](https://dev.evernote.com/doc/reference/)
- [Redis Documentation](https://redis.io/documentation)

## Next Steps
For cost optimization, see `evernote-cost-tuning`.

## Examples

**Cache notebook lookups**: Cache `listNotebooks()` for 10 minutes. On 100 requests/minute, this reduces API calls from 100 to 1 per 10-minute window (99% reduction).

**Lazy content loading**: Show note titles from cached metadata. Fetch full ENML content only when user clicks to read. Reduces average response time from 500ms to 50ms for list views.
